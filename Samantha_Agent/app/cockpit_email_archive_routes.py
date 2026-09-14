"""Read-only email archive HTTP routes behind the shared access check.

Resolvers retain file authorization and EML decoding. The HTTP handler owns
common responses, security headers, local-file delivery and exception handling.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib.parse import ParseResult, parse_qs

from app.documents.vault import safe_filename


@dataclass(frozen=True)
class EmailArchiveReadRoutes:
    page_html: Callable[[], str]
    list_archives: Callable[..., dict[str, Any]]
    archive_detail: Callable[..., dict[str, Any]]
    resolve_file: Callable[..., dict[str, Any]]
    resolve_incoming: Callable[..., dict[str, Any]]
    resolve_attachment: Callable[..., dict[str, Any]]

    def dispatch(self, *, parsed: ParseResult, responder: Any) -> bool:
        if parsed.path == "/email-archive/":
            responder.respond_html(self.page_html())
            return True
        if parsed.path == "/api/email-archive/list":
            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            try:
                limit = int(params.get("limit", ["120"])[0])
            except (TypeError, ValueError):
                limit = 120
            responder.respond_json(self.list_archives(query=query, limit=limit))
            return True
        if parsed.path == "/api/email-archive/detail":
            params = parse_qs(parsed.query)
            archive_id = params.get("archive_id", [""])[0]
            responder.respond_json(self.archive_detail(archive_id=archive_id))
            return True
        if parsed.path == "/email-archive/file":
            params = parse_qs(parsed.query)
            archive_id = params.get("archive_id", [""])[0]
            file_key = params.get("file", [""])[0]
            self._respond_email_archive_file(responder, archive_id=archive_id, file_key=file_key)
            return True
        if parsed.path == "/email-archive/attachment":
            params = parse_qs(parsed.query)
            archive_id = params.get("archive_id", [""])[0]
            attachment_ref = params.get("attachment", [""])[0]
            self._respond_email_archive_attachment(
                responder,
                archive_id=archive_id,
                attachment_ref=attachment_ref,
            )
            return True
        if parsed.path == "/email-archive/incoming":
            params = parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            self._respond_email_archive_incoming_file(responder, name=name)
            return True
        return False

    def _respond_email_archive_file(self, responder: Any, archive_id: str, file_key: str) -> None:
        resolved = self.resolve_file(archive_id=archive_id, file_key=file_key)
        if not resolved.get("ok"):
            responder.respond_json(
                {"error": "not_found", "message": resolved.get("message", "")},
                status=HTTPStatus.NOT_FOUND,
            )
            return
        responder.respond_local_file_bytes(
            target=resolved["path"],
            content_type=str(resolved.get("content_type") or "application/octet-stream"),
            filename=str(resolved.get("filename") or "email-archive"),
        )

    def _respond_email_archive_incoming_file(self, responder: Any, name: str) -> None:
        resolved = self.resolve_incoming(name=name)
        if not resolved.get("ok"):
            responder.respond_json(
                {"error": "not_found", "message": resolved.get("message", "")},
                status=HTTPStatus.NOT_FOUND,
            )
            return
        responder.respond_local_file_bytes(
            target=resolved["path"],
            content_type=str(resolved.get("content_type") or "application/octet-stream"),
            filename=str(resolved.get("filename") or "attachment"),
        )

    def _respond_email_archive_attachment(
        self,
        responder: Any,
        archive_id: str,
        attachment_ref: str,
    ) -> None:
        resolved = self.resolve_attachment(
            archive_id=archive_id,
            attachment_ref=attachment_ref,
        )
        if not resolved.get("ok"):
            responder.respond_json(
                {"error": "not_found", "message": resolved.get("message", "")},
                status=HTTPStatus.NOT_FOUND,
            )
            return
        data = resolved["data"]
        filename = safe_filename(
            str(resolved.get("filename") or "attachment")
        )
        content_type = str(
            resolved.get("content_type") or "application/octet-stream"
        )
        disposition = (
            "inline"
            if content_type == "application/pdf"
            or (
                content_type.startswith("image/")
                and content_type != "image/svg+xml"
            )
            or content_type.startswith("text/plain")
            else "attachment"
        )
        responder.send_response(HTTPStatus.OK)
        responder.send_header("Content-Type", content_type)
        responder.send_header(
            "Content-Disposition",
            f'{disposition}; filename="{filename}"',
        )
        responder.send_header("Cache-Control", "no-store, max-age=0")
        responder.send_header("Content-Length", str(len(data)))
        responder.end_headers()
        responder.wfile.write(data)
