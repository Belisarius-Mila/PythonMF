"""Read-only document HTTP routes, called after the shared access check.

Backend lookups are injected; file authorization stays in the existing resolvers.
The HTTP handler owns common responses, security headers and exception handling.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib.parse import ParseResult, parse_qs

from app.cockpit_document_readers import document_reader_page_html, purchase_reader_page_html
from app.documents.search_service import MAX_DOCUMENT_SEARCH_PAGE_SIZE
from app.documents.vault import safe_filename, safe_text


@dataclass(frozen=True)
class DocumentReadRoutes:
    search_documents: Callable[..., dict[str, Any]]
    review_report: Callable[[], dict[str, Any]]
    case_detail: Callable[..., dict[str, Any]]
    resolve_document: Callable[[str], dict[str, Any]]
    resolve_purchase: Callable[[str], dict[str, Any]]

    def dispatch(self, *, parsed: ParseResult, responder: Any) -> bool:
        if parsed.path == "/documents/read":
            params = parse_qs(parsed.query)
            document_id = params.get("document_id", [""])[0]
            self._respond_document_reader(responder, document_id)
            return True
        if parsed.path == "/documents/pdf":
            params = parse_qs(parsed.query)
            document_id = params.get("document_id", [""])[0]
            self._respond_document_pdf(responder, document_id)
            return True
        if parsed.path == "/purchases/read":
            params = parse_qs(parsed.query)
            purchase_id = params.get("purchase_id", [""])[0]
            self._respond_purchase_reader(responder, purchase_id)
            return True
        if parsed.path == "/purchases/pdf":
            params = parse_qs(parsed.query)
            purchase_id = params.get("purchase_id", [""])[0]
            self._respond_purchase_pdf(responder, purchase_id)
            return True
        if parsed.path == "/api/documents/search":
            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            page_params = parse_qs(parsed.query, keep_blank_values=True)
            try:
                values = {}
                for name, default, minimum in (("limit", "8", 1), ("offset", "0", 0)):
                    raw = page_params.get(name, [default])
                    if len(raw) != 1 or not raw[0].isascii() or not raw[0].isdecimal():
                        raise ValueError(name)
                    values[name] = int(raw[0])
                    if values[name] < minimum:
                        raise ValueError(name)
            except ValueError:
                responder.respond_json(
                    {"ok": False, "error": "invalid_pagination", "message": "limit musí být kladné celé číslo a offset nezáporné celé číslo; každý parametr pouze jednou."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return True
            responder.respond_json(self.search_documents(
                query=query, limit=min(values["limit"], MAX_DOCUMENT_SEARCH_PAGE_SIZE), offset=values["offset"],
            ))
            return True
        if parsed.path == "/api/documents/review-report":
            responder.respond_json(self.review_report())
            return True
        if parsed.path == "/api/documents/case-detail":
            params = parse_qs(parsed.query)
            case_ref = params.get("case_ref", [""])[0]
            responder.respond_json(self.case_detail(case_ref=case_ref))
            return True
        return False

    def _respond_document_reader(self, responder: Any, document_id: str) -> None:
        resolved = self.resolve_document(document_id)
        if not resolved.get("ok"):
            responder.respond_html(
                document_reader_page_html(
                    document_id=safe_text(document_id)[:180],
                    title=str(resolved.get("message", "Dokument není dostupný.")),
                ),
                status=HTTPStatus.NOT_FOUND,
            )
            return
        responder.respond_html(
            document_reader_page_html(
                document_id=str(resolved["document_ref"]),
                title=str(resolved["title"]),
                viewer_kind=str(resolved.get("viewer_kind", "pdf")),
            )
        )

    def _respond_document_pdf(self, responder: Any, document_id: str) -> None:
        resolved = self.resolve_document(document_id)
        if not resolved.get("ok"):
            responder.respond_json({"error": "not_found", "message": resolved.get("message", "")}, status=HTTPStatus.NOT_FOUND)
            return
        target = resolved["path"]
        data = target.read_bytes()
        filename = safe_filename(str(target.name or "document.pdf"))
        responder.send_response(HTTPStatus.OK)
        responder.send_header("Content-Type", str(resolved.get("content_type") or "application/octet-stream"))
        responder.send_header("Content-Disposition", f'inline; filename="{filename}"')
        responder.send_header("Cache-Control", "no-store, max-age=0")
        responder.send_header("Content-Length", str(len(data)))
        responder.end_headers()
        responder.wfile.write(data)

    def _respond_purchase_reader(self, responder: Any, purchase_id: str) -> None:
        resolved = self.resolve_purchase(purchase_id)
        if not resolved.get("ok"):
            responder.respond_html(
                purchase_reader_page_html(
                    purchase_id=safe_text(purchase_id)[:180],
                    title=str(resolved.get("message", "Nákup není dostupný.")),
                ),
                status=HTTPStatus.NOT_FOUND,
            )
            return
        responder.respond_html(
            purchase_reader_page_html(
                purchase_id=str(resolved["purchase_ref"]),
                title=str(resolved["title"]),
            )
        )

    def _respond_purchase_pdf(self, responder: Any, purchase_id: str) -> None:
        resolved = self.resolve_purchase(purchase_id)
        if not resolved.get("ok"):
            responder.respond_json({"error": "not_found", "message": resolved.get("message", "")}, status=HTTPStatus.NOT_FOUND)
            return
        target = resolved["path"]
        data = target.read_bytes()
        filename = safe_filename(str(target.name or "purchase.pdf"))
        responder.send_response(HTTPStatus.OK)
        responder.send_header("Content-Type", "application/pdf")
        responder.send_header("Content-Disposition", f'inline; filename="{filename}"')
        responder.send_header("Cache-Control", "no-store, max-age=0")
        responder.send_header("Content-Length", str(len(data)))
        responder.end_headers()
        responder.wfile.write(data)
