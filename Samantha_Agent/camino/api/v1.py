"""Versioned JSON v1 contract over the C03b persistent revision store.

The caller supplies an authentication check. This adapter never binds a socket;
C05 owns the private HTTPS server, token lifecycle, and media routes.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from camino.domain.codec import exact_object
from camino.domain.model import ContractError
from camino.domain.revision_store import RevisionStore, StoreConflict, StoreNotFound


MAX_REQUEST_BYTES = 1_048_576
KINDS = frozenset({
    "create_trip", "create_day", "create_moment", "create_asset",
    "update_metadata", "append_text",
})


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status: int
    body: dict[str, Any]


def _uuid(value: Any) -> str:
    if not isinstance(value, str):
        raise ContractError("ID must be a canonical UUID")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except ValueError as error:
        raise ContractError("ID must be a canonical UUID") from error
    return value


def _positive(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContractError(f"{label} must be a positive integer")
    return value


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ContractError("non-finite JSON number is invalid")


def _body(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_REQUEST_BYTES:
        raise ContractError("JSON request body is empty or too large")
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_unique,
                            parse_constant=_invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("request is not valid UTF-8 JSON") from error
    if not isinstance(parsed, dict):
        raise ContractError("request body must be a JSON object")
    return parsed


class CaminoV1Contract:
    def __init__(self, store: RevisionStore, authenticate: Callable[[str], bool]):
        if not callable(authenticate):
            raise TypeError("an explicit private authenticator is required")
        self.store = store
        self.authenticate = authenticate

    def handle(self, method: str, target: str, *, authorization: str | None,
               body: bytes = b"", content_type: str | None = None) -> ApiResponse:
        """Return HTTP semantics without opening a socket or logging private input."""
        try:
            if (not isinstance(authorization, str) or
                    not self.authenticate(authorization)):
                return self._error(401, "unauthorized", "private authorization required")
        except Exception:
            return self._error(401, "unauthorized", "private authorization required")
        try:
            if not isinstance(method, str) or not isinstance(target, str):
                raise ContractError("route is invalid")
            parsed_target = urlsplit(target)
            if parsed_target.scheme or parsed_target.netloc or parsed_target.fragment:
                raise ContractError("route must be a local path")
            path = parsed_target.path
            if not path.startswith("/api/v1/"):
                if path.startswith("/api/"):
                    return self._error(426, "unsupported_version", "API version is unsupported")
                return self._error(404, "not_found", "route is unknown")
            if method == "GET" and path == "/api/v1/state" and not parsed_target.query:
                return ApiResponse(200, self.store.state())
            if method == "GET" and path == "/api/v1/changes":
                query = parse_qs(parsed_target.query, strict_parsing=True)
                if set(query) != {"epoch", "cursor"} or any(len(values) != 1 for values in query.values()):
                    raise ContractError("changes requires one epoch and cursor")
                epoch = _uuid(query["epoch"][0])
                raw_cursor = query["cursor"][0]
                if re.fullmatch(r"0|[1-9][0-9]*", raw_cursor) is None:
                    raise ContractError("cursor must be a nonnegative integer")
                return ApiResponse(200, self.store.changes(epoch, int(raw_cursor)))
            match = re.fullmatch(r"/api/v1/moments/([0-9a-f-]{36})(/text)?", path)
            if method == "GET" and match and not parsed_target.query:
                moment_id = _uuid(match.group(1))
                if match.group(2):
                    return ApiResponse(200, {
                        "contract_version": 1, "moment_id": moment_id,
                        "revisions": list(self.store.text_history(moment_id)),
                    })
                return ApiResponse(200, {
                    "contract_version": 1, "epoch": self.store.state()["epoch"],
                    "moment": self.store.moment(moment_id),
                })
            if method == "POST" and path in {"/api/v1/operations", "/api/v1/reconcile"}:
                if content_type != "application/json":
                    return self._error(415, "unsupported_media_type", "application/json is required")
                data = _body(body)
                if path == "/api/v1/operations":
                    envelope = exact_object(data, {
                        "contract_version", "epoch", "operation_id", "device_sequence",
                        "device_id", "kind", "expected_revision", "payload",
                    })
                    self._version(envelope["contract_version"])
                    _uuid(envelope["epoch"])
                    _uuid(envelope["operation_id"])
                    _uuid(envelope["device_id"])
                    _positive(envelope["device_sequence"], "device sequence")
                    if not isinstance(envelope["kind"], str) or envelope["kind"] not in KINDS:
                        raise ContractError("operation kind is unknown")
                    if envelope["expected_revision"] is not None:
                        _positive(envelope["expected_revision"], "expected revision")
                    if not isinstance(envelope["payload"], dict):
                        raise ContractError("operation payload must be an object")
                    return ApiResponse(200, self.store.apply(envelope, body))
                reconciliation = exact_object(data, {
                    "contract_version", "last_known_epoch", "moments",
                })
                self._version(reconciliation["contract_version"])
                _uuid(reconciliation["last_known_epoch"])
                if not isinstance(reconciliation["moments"], list):
                    raise ContractError("inventory moments must be an array")
                return ApiResponse(200, self.store.compare_inventory(reconciliation["moments"]))
            return self._error(404, "not_found", "route is unknown")
        except StoreConflict as error:
            if error.code == "unsupported_version":
                return self._error(426, error.code, str(error))
            details = {"current_revision": error.current_revision} if error.current_revision else {}
            return self._error(409, error.code, str(error), **details)
        except StoreNotFound:
            return self._error(404, "not_found", "requested object is missing")
        except ContractError as error:
            return self._error(422, "invalid_request", str(error))
        except ValueError:
            return self._error(422, "invalid_request", "request parameter is invalid")
        except sqlite3.DatabaseError:
            return self._error(503, "storage_unavailable", "metadata store is unavailable")

    @staticmethod
    def _version(value: Any) -> None:
        if type(value) is not int or value != 1:
            raise StoreConflict("unsupported_version", "API contract version is unsupported")

    @staticmethod
    def _error(status: int, code: str, message: str, **details: Any) -> ApiResponse:
        return ApiResponse(status, {
            "contract_version": 1,
            "error": {"code": code, "message": message, **details},
        })
