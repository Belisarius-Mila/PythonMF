"""Redacted, best-effort diagnostics for refused metadata operations only."""

from __future__ import annotations

import ast
import json
import logging
from functools import lru_cache
from pathlib import Path

from camino.api.v1 import KINDS, MAX_REQUEST_BYTES

LOGGER = logging.getLogger("camino.metadata")
_CODES = frozenset({
    "unauthorized", "unsupported_media_type", "unsupported_version", "not_found",
    "invalid_request", "storage_unavailable", "epoch_mismatch", "writer_mismatch",
    "sequence_gap", "reconciliation_required", "operation_id_conflict",
    "identity_conflict", "revision_conflict",
})


@lru_cache(maxsize=1)
def _public_reasons() -> frozenset[str]:
    """Only program-source literals may become a log message, never input text.

    Some validators format a fixed field name into a fixed error template.
    Expand those templates using public source literals, not request values.
    Missing/unparseable sources reduce diagnostics; they never affect the API.
    """
    root = Path(__file__).resolve().parents[1]
    literals: set[str] = set()
    templates: list[ast.JoinedStr] = []
    for path in (root / "api" / "v1.py", *sorted((root / "domain").glob("*.py"))):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if len(node.value) <= 160 and "\n" not in node.value and "\r" not in node.value:
                    literals.add(node.value)
            elif isinstance(node, ast.JoinedStr):
                placeholders = [v for v in node.values if isinstance(v, ast.FormattedValue)]
                if (len(placeholders) == 1 and placeholders[0].conversion == -1
                        and placeholders[0].format_spec is None
                        and isinstance(placeholders[0].value, ast.Name)
                        and placeholders[0].value.id in {"name", "label", "field", "key"}
                        and all(isinstance(v, ast.FormattedValue)
                                or (isinstance(v, ast.Constant) and isinstance(v.value, str))
                                for v in node.values)):
                    templates.append(node)
    result = set(literals)
    for template in templates:
        for label in literals:
            message = "".join(label if isinstance(v, ast.FormattedValue) else v.value
                              for v in template.values)
            if len(message) <= 160 and "\n" not in message and "\r" not in message:
                result.add(message)
    return frozenset(result)


def record_metadata_rejection(response, raw: bytes) -> None:
    """Observe an existing result without altering it or storing private inputs."""
    try:
        if type(response.status) is not int or not 400 <= response.status <= 599:
            return
        error = response.body.get("error", {})
        code = error.get("code")
        code = code if isinstance(code, str) and code in _CODES else "redacted"
        reason = error.get("message")
        reason = reason if isinstance(reason, str) and reason in _public_reasons() else "redacted"
        kind, sequence = "unknown", None
        if isinstance(raw, bytes) and len(raw) <= MAX_REQUEST_BYTES:
            try:
                envelope = json.loads(raw)
                if isinstance(envelope, dict):
                    candidate = envelope.get("kind")
                    if isinstance(candidate, str) and candidate in KINDS:
                        kind = candidate
                    candidate = envelope.get("device_sequence")
                    if type(candidate) is int and 1 <= candidate <= 2**63 - 1:
                        sequence = candidate
            except (ValueError, UnicodeError, RecursionError):
                pass
        LOGGER.warning("Camino metadata rejected status=%d code=%s reason=%s kind=%s sequence=%s",
                       response.status, code, reason, kind, sequence)
    except Exception:
        # Diagnostics must not change transaction, response or retry semantics.
        return
