"""Registered interior routes under the Cockpit's existing access/origin checks."""
from __future__ import annotations

from http import HTTPStatus
from urllib.parse import parse_qs

from app.cockpit_frontend import INTERIOR_HTML, INTERIOR_MASKS_HTML
from app.interior_mask_store import InteriorMaskStore
import sqlite3
from app.file_persistence import FilePersistenceError
from app.interior_atelier import AtelierConflict, AtelierError, InteriorAtelier
from app.interior_ai import INTERIOR_AI
from app.work_repository import WorkRepositoryError


def interior_atelier_action(payload, *, store=None):
    try:
        return (store or InteriorAtelier()).execute(payload)
    except AtelierConflict as exc:
        return {"ok": False, "error": "conflict", "message": str(exc)}
    except AtelierError as exc:
        return {"ok": False, "error": "invalid_request", "message": str(exc)}
    except (OSError, FilePersistenceError, WorkRepositoryError):
        return {"ok": False, "error": "storage_error", "message": "Stav se nepodařilo bezpečně uložit. Načti přehled a ověř výsledek."}


class InteriorRoutes:
    paths = ("/interior/", "/api/interior/state", "/api/interior/asset", "/api/interior/ai/status",
             "/api/interior/delete-preview")

    def __init__(self, store_factory=None):
        self.store_factory = store_factory or InteriorAtelier

    def dispatch(self, *, parsed, responder):
        if parsed.path in ("/interior/masks/", "/api/interior/masks/state", "/api/interior/masks/image"):
            try:
                params = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
                if parsed.path != "/api/interior/masks/image" and params:
                    raise ValueError("Neplatný výběr.")
                if set(params) - {"variant"} or any(len(values) != 1 for values in params.values()):
                    raise ValueError("Neplatný výběr.")
                if parsed.path == "/interior/masks/":
                    responder.respond_html(INTERIOR_MASKS_HTML)
                elif parsed.path.endswith("/state"):
                    responder.respond_json(InteriorMaskStore().state())
                else:
                    raw = InteriorMaskStore().image(params.get("variant", [None])[0])
                    responder.send_response(HTTPStatus.OK)
                    responder.send_header("Content-Type", "image/png")
                    responder.send_header("Content-Length", str(len(raw)))
                    responder.send_header("Cache-Control", "no-store")
                    responder.end_headers()
                    responder.wfile.write(raw)
            except (ValueError, OSError, sqlite3.Error):
                responder.respond_json({"ok": False, "message": "Zkušební místnost není dostupná."}, status=HTTPStatus.BAD_REQUEST)
            return True
        if parsed.path == "/interior/":
            responder.respond_html(INTERIOR_HTML)
            return True
        if parsed.path not in self.paths:
            return False
        try:
            params = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
            allowed = {"project_id", "room_id", "base_id"} if parsed.path.endswith(("/state", "/ai/status")) else {
                "project_id", "room_id", "asset_id"}
            if parsed.path.endswith("/asset"):
                allowed.add("view")
            if set(params) - allowed or any(len(v) != 1 for v in params.values()):
                raise AtelierError("Neplatný výběr místnosti nebo podkladu.")
            args = {k: v[0] for k, v in params.items()}
            if parsed.path == "/api/interior/ai/status":
                responder.respond_json(INTERIOR_AI.status(**args) if args else INTERIOR_AI.capabilities())
                return True
            store = self.store_factory()
            if parsed.path.endswith("/state"):
                responder.respond_json(store.state(**args))
            elif parsed.path.endswith("/delete-preview"):
                responder.respond_json(store.deletion_preview(**args))
            else:
                raw, mime = store.asset(**args)
                responder.send_response(HTTPStatus.OK)
                responder.send_header("Content-Type", mime)
                responder.send_header("Content-Length", str(len(raw)))
                responder.send_header("Cache-Control", "no-store, max-age=0")
                responder.send_header("Content-Disposition", "inline")
                responder.end_headers()
                responder.wfile.write(raw)
        except AtelierConflict as exc:
            responder.respond_json({"ok": False, "error": "conflict", "message": str(exc)},
                                   status=HTTPStatus.CONFLICT)
        except AtelierError as exc:
            message = str(exc) if parsed.path.endswith("/delete-preview") else "Požadovaná místnost nebo podklad nejsou dostupné."
            responder.respond_json({"ok": False, "message": message}, status=HTTPStatus.BAD_REQUEST)
        except (TypeError, ValueError):
            responder.respond_json({"ok": False, "message": "Požadovaná místnost nebo podklad nejsou dostupné."},
                                   status=HTTPStatus.BAD_REQUEST)
        except (OSError, FilePersistenceError, WorkRepositoryError):
            responder.respond_json({"ok": False, "message": "Soukromé úložiště není dostupné."},
                                   status=HTTPStatus.CONFLICT)
        return True
