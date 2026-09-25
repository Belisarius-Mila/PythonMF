"""FastAPI adapter joining the C03b metadata contract with C05a media truth."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from camino.api.v1 import CaminoV1Contract
from camino.domain.model import ContractError
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import DEFAULT_CHUNK_BYTES, MediaStore, MediaStoreError
from camino.server.viewer_worker import ViewerWorker

if TYPE_CHECKING:
    from camino.server.viewer import CaminoViewer


def _error(status: int | HTTPStatus, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=int(status),
        content={"contract_version": 1, "error": {"code": code, "message": message}},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def _json(status: int | HTTPStatus, body: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=int(status), content=body,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


def _authorization(request: Request) -> str:
    return request.headers.get("authorization", "")


def _exact_json(raw: bytes, expected: set[str]) -> dict[str, Any]:
    if not raw or len(raw) > 4096:
        raise ContractError("request body is empty or too large")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ContractError("duplicate JSON field")
            value[key] = item
        return value

    def reject_nonfinite(_value: str) -> None:
        raise ContractError("non-finite number is invalid")

    try:
        body = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("request body is not valid UTF-8 JSON") from error
    if not isinstance(body, dict) or set(body) != expected:
        raise ContractError("request body has missing or unknown fields")
    return body


def create_app(
    *,
    metadata_api: CaminoV1Contract,
    media_store: MediaStore,
    token_store: RevocableTokenStore,
    finalize_delay_seconds: float = 0,
    viewer: CaminoViewer | None = None,
    viewer_interval_seconds: float | None = None,
    root_path: str = "",
) -> FastAPI:
    if not 0 <= finalize_delay_seconds <= 15:
        raise ValueError("finalize delay must stay between 0 and 15 seconds")
    if root_path not in ("", "/camino-api"):
        raise ValueError("unsupported private proxy prefix")
    if viewer_interval_seconds is not None and viewer is None:
        raise ValueError("Viewer worker requires an explicitly configured Viewer")
    worker = ViewerWorker(viewer, interval=viewer_interval_seconds) if viewer_interval_seconds is not None else None

    @asynccontextmanager
    async def lifespan(_app):
        if worker is not None:
            worker.start()
        try:
            yield
        finally:
            if worker is not None:
                await asyncio.to_thread(worker.stop)

    app = FastAPI(
        title="Camino private owner API",
        version="1",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        root_path=root_path,
        lifespan=lifespan,
    )
    app.state.metadata_api = metadata_api
    app.state.media_store = media_store
    app.state.token_store = token_store
    app.state.viewer_worker = worker
    if viewer is not None:
        if viewer.tokens.path == token_store.path:
            raise ValueError("Viewer must have a separate read-only credential store")
        if viewer.metadata is not metadata_api.store or viewer.media is not media_store:
            raise ValueError("Viewer must use this API's authoritative stores")
        app.include_router(viewer.router())

    def authorized(request: Request) -> bool:
        return token_store.authenticate(_authorization(request))

    @app.get("/healthz", include_in_schema=True)
    async def health(request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        return _json(HTTPStatus.OK, {
            "contract_version": 1,
            "status": "ok",
            "scope": "c05a_private_owner",
        })

    @app.post("/api/v1/assets/{asset_id}/upload-session", include_in_schema=True)
    async def create_upload_session(asset_id: str, request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        if request.headers.get("content-type") != "application/json":
            return _error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "unsupported_media_type", "application/json is required")
        try:
            body = _exact_json(await request.body(), {"contract_version", "chunk_size"})
            if body["contract_version"] != 1:
                return _error(HTTPStatus.UPGRADE_REQUIRED, "unsupported_version", "API version is unsupported")
            status, created = media_store.create_session(asset_id, chunk_size=body["chunk_size"])
            status["created"] = created
            return _json(HTTPStatus.CREATED if created else HTTPStatus.OK, status)
        except (ContractError, TypeError, ValueError):
            return _error(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_request", "upload manifest request is invalid")
        except MediaStoreError as error:
            return _error(error.status, error.code, str(error))
        except sqlite3.DatabaseError:
            return _error(HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable", "server storage is unavailable")

    @app.get("/api/v1/assets/{asset_id}/upload-status", include_in_schema=True)
    async def upload_status(asset_id: str, request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        try:
            return _json(HTTPStatus.OK, media_store.status(asset_id))
        except MediaStoreError as error:
            return _error(error.status, error.code, str(error))
        except sqlite3.DatabaseError:
            return _error(HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable", "server storage is unavailable")

    @app.put("/api/v1/assets/{asset_id}/chunks/{chunk_index}", include_in_schema=True)
    async def put_chunk(asset_id: str, chunk_index: int, request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        if request.headers.get("content-type") != "application/octet-stream":
            return _error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "unsupported_media_type", "application/octet-stream is required"
            )
        raw_headers = request.scope.get("headers") or []
        lengths = [value for key, value in raw_headers if key.lower() == b"content-length"]
        if request.headers.get("transfer-encoding") is not None or len(lengths) != 1:
            return _error(HTTPStatus.LENGTH_REQUIRED, "content_length_required", "one Content-Length is required")
        try:
            raw_length = lengths[0].decode("ascii")
            if not raw_length.isdigit():
                raise ValueError
            content_length = int(raw_length)
            reservation = media_store.reserve_chunk(
                asset_id,
                chunk_index,
                content_length=content_length,
                expected_sha256=request.headers.get("x-camino-chunk-sha256", ""),
            )
            if reservation.already_stored:
                status = media_store.status(asset_id)
                status["chunk_created"] = False
                return _json(HTTPStatus.OK, status)
            staged = media_store.new_chunk_staging(reservation)
            received = 0
            try:
                with staged.open("wb") as output:
                    async for block in request.stream():
                        received += len(block)
                        if received > content_length:
                            raise MediaStoreError(
                                HTTPStatus.BAD_REQUEST, "invalid_chunk_length", "chunk body is longer than declared"
                            )
                        output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
                if received != content_length:
                    raise MediaStoreError(
                        HTTPStatus.BAD_REQUEST, "incomplete_chunk", "chunk body ended before Content-Length"
                    )
                status, created = media_store.commit_chunk(reservation, staged)
                status["chunk_created"] = created
                return _json(HTTPStatus.CREATED if created else HTTPStatus.OK, status)
            except Exception:
                if staged.exists():
                    media_store.preserve_staging(staged, "incomplete_http_chunk", asset_id)
                raise
        except (UnicodeDecodeError, ValueError):
            return _error(HTTPStatus.LENGTH_REQUIRED, "content_length_required", "one numeric Content-Length is required")
        except MediaStoreError as error:
            return _error(error.status, error.code, str(error))
        except (OSError, sqlite3.DatabaseError):
            return _error(HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable", "server storage is unavailable")

    @app.post("/api/v1/assets/{asset_id}/finalize", include_in_schema=True)
    async def finalize(asset_id: str, request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        try:
            if finalize_delay_seconds:
                await asyncio.sleep(finalize_delay_seconds)
            receipt, created = media_store.finalize(asset_id)
            body = dict(receipt)
            body["created"] = created
            return _json(HTTPStatus.CREATED if created else HTTPStatus.OK, body)
        except MediaStoreError as error:
            return _error(error.status, error.code, str(error))
        except sqlite3.DatabaseError:
            return _error(HTTPStatus.SERVICE_UNAVAILABLE, "storage_unavailable", "server storage is unavailable")

    @app.api_route("/api/v1/{path:path}", methods=["GET", "POST"], include_in_schema=False)
    async def metadata(path: str, request: Request):
        if not authorized(request):
            return _error(HTTPStatus.UNAUTHORIZED, "unauthorized", "private authorization required")
        raw = await request.body()
        target = "/api/v1/" + path
        if request.url.query:
            target += "?" + request.url.query
        response = metadata_api.handle(
            request.method,
            target,
            authorization=_authorization(request),
            body=raw,
            content_type=request.headers.get("content-type"),
        )
        return _json(response.status, response.body)

    return app
