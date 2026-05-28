from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.backup.activity_state import format_backup_activity_reminder
from app.documents.scandocu import DEFAULT_DOWNLOADS_DIR, reviewed_document_ids, scan_downloads_for_pdfs
from app.documents.vault import (
    DEFAULT_DOCUMENTS_DIR,
    build_snippet,
    document_vault_status_summary,
    append_jsonl,
    is_pdf_encrypted,
    next_available_path,
    prepare_document_print_job,
    read_jsonl,
    read_json_file,
    relative_to_project,
    run_document_print_job,
    safe_text,
    safe_slug,
    sanitize_output,
    tokenize,
    write_json,
    write_jsonl,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PORT = 8770
SCANDOCU_URL = "http://127.0.0.1:8766"
SCANDOCU_PORT = 8766
SCANDOCU_LOG_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "scandocu"
SCANDOCU_LOG_FILE = SCANDOCU_LOG_DIR / "server.log"
SCANDOCU_SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "scandocu_server.py"


def cockpit_status() -> dict[str, Any]:
    downloads = safe_downloads_status()
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "downloads": downloads,
        "document_work": document_work_status(downloads=downloads),
        "backup": format_backup_activity_reminder(),
        "vault": document_vault_status_summary(),
        "scandocu": probe_scandocu(),
    }


def safe_downloads_status(limit: int = 20) -> dict[str, Any]:
    try:
        items = scan_downloads_for_pdfs(
            downloads_dir=DEFAULT_DOWNLOADS_DIR,
            vault_dir=DEFAULT_DOCUMENTS_DIR,
            limit=limit,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "items": []}
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
        path_value = item.get("path")
        if isinstance(path_value, str) and path_value and is_pdf_encrypted(Path(path_value)):
            item["is_encrypted"] = True
            item["problem_kind"] = "encrypted"
            item["problem_label"] = "šifrované PDF"
    return {
        "ok": True,
        "folder": str(DEFAULT_DOWNLOADS_DIR),
        "counts": counts,
        "items": items,
    }


def document_work_status(
    downloads: dict[str, Any] | None = None,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
) -> dict[str, Any]:
    downloads = downloads if downloads is not None else safe_downloads_status(limit=50)
    items = [item for item in downloads.get("items", []) if isinstance(item, dict)]
    new_pdfs = [item for item in items if item.get("status") == "new"][:limit]
    problems = [with_problem_label(item) for item in items if download_problem_kind(item)][:limit]
    review = stored_documents_review_status(vault_dir=vault_dir, limit=limit)
    return {
        "new_pdfs": new_pdfs,
        "review": review,
        "problems": problems,
        "summary": {
            "new_pdf_count": sum(1 for item in items if item.get("status") == "new"),
            "problem_count": sum(1 for item in items if download_problem_kind(item)),
            "review_pending_count": review["pending_count"],
        },
    }


def stored_documents_review_status(vault_dir: Path = DEFAULT_DOCUMENTS_DIR, limit: int = 8) -> dict[str, Any]:
    reviewed = reviewed_document_ids(vault_dir)
    pending: list[dict[str, Any]] = []
    reviewed_count = 0
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        document_id = str(row.get("document_id", ""))
        if not document_id:
            continue
        if document_id in reviewed:
            reviewed_count += 1
            continue
        pending.append(
            {
                "document_id": document_id,
                "title": str(row.get("title") or row.get("original_filename") or document_id),
                "domain": str(row.get("domain", "")),
                "document_type": str(row.get("document_type", "")),
                "stored_path": str(row.get("stored_path", "")),
            }
        )
    return {
        "pending_count": len(pending),
        "reviewed_count": reviewed_count,
        "next_items": pending[:limit],
    }


def download_problem_kind(item: dict[str, Any]) -> str:
    if item.get("is_encrypted"):
        return "encrypted"
    status = str(item.get("status", ""))
    if status == "invalid":
        return "invalid"
    if status in {"already_in_vault", "duplicate"}:
        return "duplicate"
    if status == "skipped":
        return "skipped"
    return ""


def with_problem_label(item: dict[str, Any]) -> dict[str, Any]:
    kind = download_problem_kind(item)
    labels = {
        "encrypted": "šifrované PDF",
        "duplicate": "už uložené / duplicita",
        "skipped": "přeskočeno",
        "invalid": "neplatný soubor",
    }
    enriched = dict(item)
    enriched["problem_kind"] = kind
    enriched["problem_label"] = labels.get(kind, kind or "problém")
    return enriched


def search_document_index(
    query: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    limit: int = 8,
) -> dict[str, Any]:
    terms = [term.casefold() for term in tokenize(query) if len(term) >= 2]
    if not terms:
        return {"ok": False, "message": "Zadej konkrétnější dotaz.", "results": []}

    documents = {
        str(item.get("document_id", "")): item
        for item in read_jsonl(vault_dir / "index" / "documents_index.jsonl")
        if str(item.get("document_id", "")).strip()
    }
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    scored: list[tuple[int, dict[str, Any], str]] = []
    for document_id, metadata in documents.items():
        text = text_by_id.get(document_id, "")
        haystack = " ".join(
            [
                text,
                str(metadata.get("title", "")),
                str(metadata.get("original_filename", "")),
                str(metadata.get("document_id", "")),
                str(metadata.get("stored_path", "")),
                str(metadata.get("document_type", "")),
                str(metadata.get("domain", "")),
                str(metadata.get("counterparty", "")),
                str(metadata.get("related_asset", "")),
                " ".join(str(tag) for tag in metadata.get("tags", []) if isinstance(tag, str)),
            ]
        ).casefold()
        score = sum(haystack.count(term) for term in terms)
        if score <= 0:
            continue
        snippet = build_snippet(text, terms) if text else ""
        if not snippet.strip():
            snippet = "Text zatím není k dispozici; shoda je podle metadat."
        scored.append((score, metadata, snippet))

    results: list[dict[str, Any]] = []
    for score, metadata, snippet in sorted(scored, key=lambda row: row[0], reverse=True)[: max(1, min(limit, 20))]:
        results.append(
            {
                "score": score,
                "document_id": safe_text(str(metadata.get("document_id", ""))),
                "title": safe_text(str(metadata.get("title") or metadata.get("original_filename") or "")),
                "original_filename": safe_text(str(metadata.get("original_filename", ""))),
                "domain": safe_text(str(metadata.get("domain", ""))),
                "document_type": safe_text(str(metadata.get("document_type", ""))),
                "counterparty": safe_text(str(metadata.get("counterparty", ""))),
                "related_asset": safe_text(str(metadata.get("related_asset", ""))),
                "stored_path": safe_text(str(metadata.get("stored_path", ""))),
                "lifecycle_status": safe_text(str(metadata.get("lifecycle_status", "active") or "active")),
                "snippet": sanitize_output(snippet),
            }
        )
    return {
        "ok": True,
        "query": query,
        "count": len(results),
        "results": results,
        "message": "Nalezena shoda." if results else "V dokumentech jsem nenašla shodu.",
    }


def prepare_document_print_action(document_id: str, vault_dir: Path = DEFAULT_DOCUMENTS_DIR) -> dict[str, Any]:
    try:
        result = prepare_document_print_job(document_id=document_id, vault_dir=vault_dir)
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    return {
        "ok": True,
        "message": "Dokument je připraven k tisku. Originál ve vaultu zůstal beze změny.",
        "print_job_id": result.print_job_id,
        "document_id": result.document_id,
        "queue_path": str(relative_to_project(result.queue_path)),
    }


def run_document_print_action(
    print_job_id: str,
    confirmation_text: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_print_job_id = safe_slug(print_job_id, default="", limit=120)
    try:
        result = run_document_print_job(
            print_job_id=safe_print_job_id,
            user_confirmed=True,
            confirmation_text=confirmation_text,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}
    return {
        "ok": result.status == "printed",
        "status": result.status,
        "message": result.message,
        "print_job_id": result.print_job_id,
        "document_id": result.document_id,
    }


def move_document_lifecycle_action(
    document_id: str,
    target: str,
    confirmation_text: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    safe_document_id = safe_slug(document_id, default="", limit=140)
    if not safe_document_id:
        return {"ok": False, "message": "Chybí document_id."}
    if target not in {"archive", "trash"}:
        return {"ok": False, "message": "Neznámá akce nad dokumentem."}
    required = (
        f"Potvrzuji, archivuj dokument {safe_document_id}."
        if target == "archive"
        else f"Potvrzuji, přesuň dokument {safe_document_id} do koše."
    )
    if confirmation_text.strip() != required:
        return {"ok": False, "message": f"Chybí přesné potvrzení: {required}"}

    try:
        return move_document_to_archive_or_trash(
            document_id=safe_document_id,
            target=target,
            vault_dir=vault_dir,
        )
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}


def move_document_to_archive_or_trash(
    document_id: str,
    target: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> dict[str, Any]:
    documents_path = vault_dir / "index" / "documents_index.jsonl"
    documents = read_jsonl(documents_path)
    row_index = next((index for index, row in enumerate(documents) if str(row.get("document_id", "")) == document_id), None)
    if row_index is None:
        raise ValueError(f"Dokument {document_id} nebyl nalezen v indexu.")
    current = dict(documents[row_index])
    stored_path = PROJECT_ROOT / str(current.get("stored_path", ""))
    try:
        resolved_stored_path = stored_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("Dokument je v indexu, ale soubor ve vaultu nebyl nalezen.") from exc
    document_dir = resolved_stored_path.parent
    vault_root = vault_dir.resolve()
    if vault_root not in document_dir.parents:
        raise ValueError("Dokument není uvnitř povoleného document vaultu.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    domain = safe_slug(str(current.get("domain", "other")), default="other", limit=80)
    if target == "archive":
        target_dir = next_available_path(vault_dir / "archive" / domain / document_id)
        lifecycle_status = "archived"
        action = "archived"
        time_key = "archived_at"
        message = "Dokument byl přesunut do archivu."
    else:
        target_dir = next_available_path(vault_dir / "trash" / f"{stamp}_{document_id}")
        lifecycle_status = "trashed"
        action = "moved_to_trash"
        time_key = "trashed_at"
        message = "Dokument byl přesunut do koše. Nebyl trvale smazán."

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(document_dir), str(target_dir))
    new_stored_path = target_dir / resolved_stored_path.name
    now_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    updated = dict(current)
    updated["stored_path"] = str(relative_to_project(new_stored_path))
    updated["lifecycle_status"] = lifecycle_status
    updated[time_key] = now_value
    documents[row_index] = updated
    write_jsonl(documents_path, documents)

    manifest_path = target_dir / "manifest.json"
    if manifest_path.exists():
        manifest = read_json_file(manifest_path)
        manifest.update(updated)
        write_json(manifest_path, manifest)

    append_jsonl(
        vault_dir / "index" / "document_lifecycle_actions.jsonl",
        {
            "action": action,
            "document_id": document_id,
            "from_path": str(relative_to_project(document_dir)),
            "to_path": str(relative_to_project(target_dir)),
            "created_at": now_value,
            "do_not_commit": True,
        },
    )
    return {
        "ok": True,
        "status": lifecycle_status,
        "message": message,
        "document_id": document_id,
        "stored_path": str(relative_to_project(new_stored_path)),
    }


def probe_scandocu() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["/usr/bin/curl", "-fsS", f"{SCANDOCU_URL}/api/list"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"running": False, "url": SCANDOCU_URL, "message": str(exc)}
    return {
        "running": completed.returncode == 0,
        "url": SCANDOCU_URL,
        "message": "běží" if completed.returncode == 0 else "neběží",
    }


def start_scandocu() -> dict[str, Any]:
    if probe_scandocu().get("running"):
        return {"ok": True, "message": "ScanDocu už běží.", "url": SCANDOCU_URL}
    if not SCANDOCU_SERVER_SCRIPT.exists():
        return {"ok": False, "message": f"ScanDocu server neexistuje: {SCANDOCU_SERVER_SCRIPT}"}
    try:
        SCANDOCU_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with SCANDOCU_LOG_FILE.open("a", encoding="utf-8") as log_handle:
            subprocess.Popen(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(SCANDOCU_SERVER_SCRIPT),
                    "--port",
                    str(SCANDOCU_PORT),
                ],
                cwd=str(PROJECT_ROOT),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        return {"ok": False, "message": f"ScanDocu se nepodařilo spustit: {exc}"}
    for _ in range(10):
        if probe_scandocu().get("running"):
            return {"ok": True, "message": "ScanDocu spuštěno.", "url": SCANDOCU_URL}
        time.sleep(0.2)
    return {"ok": False, "message": f"ScanDocu se spustilo, ale zatím neodpovídá. Log: {SCANDOCU_LOG_FILE}"}


def open_project_terminal() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["/usr/bin/open", "-a", "Terminal", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": f"Terminál se nepodařilo otevřít: {exc}"}
    message = completed.stderr.strip() or completed.stdout.strip() or "Terminál otevřen v projektu."
    return {"ok": completed.returncode == 0, "message": message, "returncode": completed.returncode}


class CockpitServer:
    def __init__(self, host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
        self.host = host
        self.port = port

    def serve(self) -> None:
        server = ThreadingHTTPServer((self.host, self.port), self.make_handler())
        print(f"Samantha Cockpit běží na http://{self.host}:{self.port}", flush=True)
        server.serve_forever()

    def make_handler(self):
        class Handler(BaseHTTPRequestHandler):
            server_version = "SamanthaCockpit/0.1"

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self.respond_html(COCKPIT_HTML)
                    return
                if parsed.path == "/api/status":
                    self.respond_json(cockpit_status())
                    return
                if parsed.path == "/api/documents/search":
                    params = parse_qs(parsed.query)
                    query = params.get("q", [""])[0]
                    self.respond_json(search_document_index(query=query))
                    return
                self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/api/scandocu/open":
                    self.respond_json(start_scandocu())
                    return
                if parsed.path == "/api/terminal/open":
                    self.respond_json(open_project_terminal())
                    return
                if parsed.path == "/api/documents/print/prepare":
                    payload = self.read_json()
                    self.respond_json(prepare_document_print_action(document_id=str(payload.get("document_id", ""))))
                    return
                if parsed.path == "/api/documents/print/run":
                    payload = self.read_json()
                    self.respond_json(
                        run_document_print_action(
                            print_job_id=str(payload.get("print_job_id", "")),
                            confirmation_text=str(payload.get("confirmation_text", "")),
                        )
                    )
                    return
                if parsed.path == "/api/documents/lifecycle":
                    payload = self.read_json()
                    self.respond_json(
                        move_document_lifecycle_action(
                            document_id=str(payload.get("document_id", "")),
                            target=str(payload.get("target", "")),
                            confirmation_text=str(payload.get("confirmation_text", "")),
                        )
                    )
                    return
                self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

            def read_json(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length).decode("utf-8") if length else "{}"
                data = json.loads(raw or "{}")
                if not isinstance(data, dict):
                    raise ValueError("JSON payload musí být objekt.")
                return data

            def log_message(self, format: str, *args: Any) -> None:
                return

            def respond_html(self, html: str) -> None:
                data = html.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def respond_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
                data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        return Handler


COCKPIT_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Samantha Cockpit</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef1f4;
      --ink: #172033;
      --muted: #667085;
      --line: #d6dce5;
      --panel: #ffffff;
      --blue: #1f5fbf;
      --green: #18794e;
      --amber: #9a6700;
      --red: #b42318;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    header { height: 54px; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; background: #182230; color: white; }
    h1 { margin: 0; font-size: 19px; font-weight: 650; letter-spacing: 0; }
    main { padding: 18px 20px 24px; display: grid; gap: 16px; }
    .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    button { border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 650; cursor: pointer; background: #e4e9f0; color: #172033; }
    button.primary { background: var(--blue); color: white; }
    button.secondary { background: #dfe5ec; }
    button:disabled { opacity: .6; cursor: wait; }
    .grid { display: grid; grid-template-columns: minmax(320px, 1.15fr) minmax(320px, .85fr); gap: 16px; align-items: start; }
    .work-grid { display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; align-items: stretch; }
    .work-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfe; display: grid; gap: 10px; align-content: start; min-height: 170px; }
    .work-card h3 { margin: 0; font-size: 13px; color: #253047; }
    .work-count { font-size: 27px; font-weight: 750; line-height: 1; }
    .work-list { display: grid; gap: 7px; font-size: 12px; color: #344054; }
    .work-item { border-top: 1px solid #edf0f4; padding-top: 7px; overflow-wrap: anywhere; }
    .work-item:first-child { border-top: 0; padding-top: 0; }
    .work-meta { color: var(--muted); font-size: 11px; margin-top: 2px; }
    .search-controls { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 10px; align-items: center; }
    input[type="search"] { box-sizing: border-box; width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; font: inherit; background: white; color: var(--ink); }
    .search-results { display: grid; gap: 9px; margin-top: 12px; }
    .search-result { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; }
    .search-result-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
    .search-title { font-weight: 700; overflow-wrap: anywhere; }
    .search-meta { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .search-detail { display: grid; gap: 5px; margin-top: 6px; padding-top: 8px; border-top: 1px solid #edf0f4; }
    .search-snippet { font-size: 12px; line-height: 1.45; color: #263244; overflow-wrap: anywhere; }
    .danger-soft { background: #fee2e2; color: #991b1b; }
    .stack { display: grid; gap: 16px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    section h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; }
    .status-line { color: var(--muted); font-size: 13px; }
    .pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 12px; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 5px 8px; font-size: 12px; background: #f8fafc; color: #344054; }
    .ok { color: var(--green); }
    .warn { color: var(--amber); }
    .bad { color: var(--red); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; border-bottom: 1px solid #edf0f4; padding: 8px 6px; vertical-align: top; }
    th { color: #475467; font-size: 12px; font-weight: 650; background: #fbfcfe; }
    td.name { max-width: 360px; overflow-wrap: anywhere; }
    pre { margin: 0; white-space: pre-wrap; font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; line-height: 1.45; color: #263244; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .message { margin-top: 10px; padding: 9px 10px; border-radius: 6px; background: #eef4ff; color: #1d3b74; font-size: 13px; }
    .hidden { display: none; }
    @media (max-width: 1050px) { .work-grid { grid-template-columns: 1fr; } }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .search-controls { grid-template-columns: 1fr; } header { height: auto; padding: 12px 16px; align-items: flex-start; gap: 10px; flex-direction: column; } }
  </style>
</head>
<body>
  <header>
    <h1>Samantha Cockpit</h1>
    <div class="toolbar">
      <button class="secondary" id="refreshBtn">Obnovit</button>
      <button class="primary" id="scanDocuBtn">Otevřít ScanDocu</button>
      <button class="secondary" id="scanDocuReviewBtn">Revidovat uložené</button>
      <button class="secondary" id="terminalBtn">Terminál v projektu</button>
    </div>
  </header>
  <main>
    <div id="statusLine" class="status-line">Načítám stav...</div>
    <section>
      <h2>Práce s dokumenty</h2>
      <div class="body">
        <div class="work-grid">
          <div class="work-card">
            <h3>Nová PDF ve Downloads</h3>
            <div id="newPdfCount" class="work-count">0</div>
            <div class="actions">
              <button class="primary" id="processNextBtn">Zpracovat další dokument</button>
            </div>
            <div id="newPdfList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Uložené dokumenty k revizi</h3>
            <div id="reviewCount" class="work-count">0</div>
            <div class="actions">
              <button class="secondary" id="reviewNextBtn">Revidovat další uložený</button>
            </div>
            <div id="reviewList" class="work-list"></div>
          </div>
          <div class="work-card">
            <h3>Problémy</h3>
            <div id="problemCount" class="work-count">0</div>
            <div class="status-line">Šifrované / duplicitní / přeskočené</div>
            <div id="problemList" class="work-list"></div>
          </div>
        </div>
      </div>
    </section>
    <section>
      <h2>Najít dokument</h2>
      <div class="body">
        <div class="search-controls">
          <input id="documentSearchInput" type="search" placeholder="Hledat podle názvu, typu, protistrany, věci, tagu nebo textu">
          <button class="primary" id="documentSearchBtn">Hledat</button>
        </div>
        <div id="documentSearchStatus" class="status-line"></div>
        <div id="documentSearchResults" class="search-results"></div>
      </div>
    </section>
    <div class="grid">
      <section>
        <h2>PDF ve Downloads</h2>
        <div class="body">
          <div id="downloadPills" class="pills"></div>
          <table>
            <thead><tr><th>Soubor</th><th>Stav</th><th>Změněno</th></tr></thead>
            <tbody id="downloadsBody"></tbody>
          </table>
        </div>
      </section>
      <div class="stack">
        <section>
          <h2>ScanDocu</h2>
          <div class="body">
            <div id="scanDocuState" class="status-line"></div>
            <div id="actionMessage" class="message hidden"></div>
          </div>
        </section>
        <section>
          <h2>Záloha</h2>
          <div class="body"><pre id="backupText"></pre></div>
        </section>
      </div>
    </div>
    <section>
      <h2>Document Vault</h2>
      <div class="body"><pre id="vaultText"></pre></div>
    </section>
  </main>
  <script>
    const statusLine = document.getElementById("statusLine");
    const downloadsBody = document.getElementById("downloadsBody");
    const downloadPills = document.getElementById("downloadPills");
    const backupText = document.getElementById("backupText");
    const vaultText = document.getElementById("vaultText");
    const scanDocuState = document.getElementById("scanDocuState");
    const actionMessage = document.getElementById("actionMessage");
    const refreshBtn = document.getElementById("refreshBtn");
    const scanDocuBtn = document.getElementById("scanDocuBtn");
    const scanDocuReviewBtn = document.getElementById("scanDocuReviewBtn");
    const processNextBtn = document.getElementById("processNextBtn");
    const reviewNextBtn = document.getElementById("reviewNextBtn");
    const terminalBtn = document.getElementById("terminalBtn");
    const newPdfCount = document.getElementById("newPdfCount");
    const reviewCount = document.getElementById("reviewCount");
    const problemCount = document.getElementById("problemCount");
    const newPdfList = document.getElementById("newPdfList");
    const reviewList = document.getElementById("reviewList");
    const problemList = document.getElementById("problemList");
    const documentSearchInput = document.getElementById("documentSearchInput");
    const documentSearchBtn = document.getElementById("documentSearchBtn");
    const documentSearchStatus = document.getElementById("documentSearchStatus");
    const documentSearchResults = document.getElementById("documentSearchResults");

    function statusClass(value) {
      if (value === "new") return "ok";
      if (value === "already_in_vault" || value === "imported" || value === "skipped") return "warn";
      if (value === "invalid") return "bad";
      return "";
    }

    function showMessage(text) {
      actionMessage.textContent = text || "";
      actionMessage.classList.toggle("hidden", !text);
    }

    async function refresh() {
      refreshBtn.disabled = true;
      statusLine.textContent = "Načítám stav...";
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        statusLine.textContent = `Aktualizováno: ${data.generated_at || ""}`;
        scanDocuState.innerHTML = data.scandocu && data.scandocu.running
          ? `<span class="ok">ScanDocu běží</span> | ${data.scandocu.url}`
          : `<span class="warn">ScanDocu neběží</span> | ${data.scandocu ? data.scandocu.url : ""}`;
        backupText.textContent = data.backup || "";
        vaultText.textContent = data.vault || "";
        renderDocumentWork(data.document_work || {});
        renderDownloads(data.downloads || {});
      } catch (err) {
        statusLine.textContent = `Chyba načtení: ${err}`;
      } finally {
        refreshBtn.disabled = false;
      }
    }

    function renderDocumentWork(work) {
      const summary = work.summary || {};
      const review = work.review || {};
      const newItems = work.new_pdfs || [];
      const reviewItems = review.next_items || [];
      const problemItems = work.problems || [];
      newPdfCount.textContent = String(summary.new_pdf_count || 0);
      reviewCount.textContent = String(summary.review_pending_count || review.pending_count || 0);
      problemCount.textContent = String(summary.problem_count || 0);
      processNextBtn.disabled = newItems.length === 0;
      reviewNextBtn.disabled = reviewItems.length === 0;
      renderWorkList(newPdfList, newItems, (item) => ({
        title: item.name || "",
        meta: `${item.status || ""} | ${item.modified_at || ""}`
      }), "Žádné nové PDF.");
      renderWorkList(reviewList, reviewItems, (item) => ({
        title: item.title || item.document_id || "",
        meta: `${item.domain || "other"} / ${item.document_type || "document"}`
      }), "Žádný uložený dokument nečeká na revizi.");
      renderWorkList(problemList, problemItems, (item) => ({
        title: item.name || "",
        meta: `${item.problem_label || item.status || ""} | ${item.modified_at || ""}`
      }), "Žádné zjevné problémy ve frontě.");
    }

    function renderWorkList(target, items, mapItem, emptyText) {
      target.innerHTML = "";
      if (!items || items.length === 0) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = emptyText;
        target.appendChild(empty);
        return;
      }
      items.slice(0, 5).forEach((item) => {
        const mapped = mapItem(item);
        const row = document.createElement("div");
        row.className = "work-item";
        const title = document.createElement("div");
        title.textContent = mapped.title || "";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = mapped.meta || "";
        row.appendChild(title);
        row.appendChild(meta);
        target.appendChild(row);
      });
    }

    function renderDownloads(downloads) {
      downloadPills.innerHTML = "";
      const counts = downloads.counts || {};
      Object.keys(counts).sort().forEach((key) => {
        const pill = document.createElement("span");
        pill.className = `pill ${statusClass(key)}`;
        pill.textContent = `${key}: ${counts[key]}`;
        downloadPills.appendChild(pill);
      });
      downloadsBody.innerHTML = "";
      (downloads.items || []).slice(0, 20).forEach((item) => {
        const row = document.createElement("tr");
        row.innerHTML = `<td class="name"></td><td></td><td></td>`;
        row.children[0].textContent = item.name || "";
        row.children[1].textContent = item.status || "";
        row.children[1].className = statusClass(item.status || "");
        row.children[2].textContent = item.modified_at || "";
        downloadsBody.appendChild(row);
      });
      if (!downloads.items || downloads.items.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = `<td colspan="3">Žádné PDF nenalezeno.</td>`;
        downloadsBody.appendChild(row);
      }
    }

    async function postAction(url, button) {
      button.disabled = true;
      showMessage("Provádím akci...");
      try {
        const res = await fetch(url, {method: "POST"});
        const data = await res.json();
        showMessage(data.message || data.error || "Hotovo.");
        await refresh();
      } catch (err) {
        showMessage(`Chyba: ${err}`);
      } finally {
        button.disabled = false;
      }
    }

    async function searchDocuments() {
      const query = documentSearchInput.value.trim();
      documentSearchResults.innerHTML = "";
      if (query.length < 2) {
        documentSearchStatus.textContent = "Zadej aspoň dvě písmena nebo číslice.";
        return;
      }
      documentSearchBtn.disabled = true;
      documentSearchStatus.textContent = "Hledám v indexu dokumentů...";
      try {
        const res = await fetch(`/api/documents/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        documentSearchStatus.textContent = data.message || "";
        renderDocumentSearchResults(data.results || []);
      } catch (err) {
        documentSearchStatus.textContent = `Chyba hledání: ${err}`;
      } finally {
        documentSearchBtn.disabled = false;
      }
    }

    function renderDocumentSearchResults(results) {
      documentSearchResults.innerHTML = "";
      if (!results || results.length === 0) {
        return;
      }
      results.forEach((item) => {
        const card = document.createElement("div");
        card.className = "search-result";
        const head = document.createElement("div");
        head.className = "search-result-head";
        const summary = document.createElement("div");
        const title = document.createElement("div");
        title.className = "search-title";
        title.textContent = item.title || item.original_filename || item.document_id || "Dokument bez názvu";
        const meta = document.createElement("div");
        meta.className = "search-meta";
        meta.textContent = `${item.domain || "other"} / ${item.document_type || "document"} | ${item.counterparty || "protistrana nezjištěna"} | ${item.related_asset || "věc nezjištěna"}`;
        const toggle = document.createElement("button");
        toggle.className = "secondary";
        toggle.type = "button";
        toggle.textContent = "Rozbalit";
        const detail = document.createElement("div");
        detail.className = "search-detail hidden";
        const id = document.createElement("div");
        id.className = "search-meta";
        id.textContent = `ID: ${item.document_id || ""}`;
        const path = document.createElement("div");
        path.className = "search-meta";
        path.textContent = `Cesta: ${item.stored_path || ""}`;
        const lifecycle = document.createElement("div");
        lifecycle.className = "search-meta";
        lifecycle.textContent = `Stav: ${item.lifecycle_status || "active"}`;
        const snippet = document.createElement("div");
        snippet.className = "search-snippet";
        snippet.textContent = item.snippet || "";
        const actions = document.createElement("div");
        actions.className = "actions";
        const printBtn = document.createElement("button");
        printBtn.className = "secondary";
        printBtn.type = "button";
        printBtn.textContent = "Tisknout";
        const archiveBtn = document.createElement("button");
        archiveBtn.className = "secondary";
        archiveBtn.type = "button";
        archiveBtn.textContent = "Archivovat";
        const trashBtn = document.createElement("button");
        trashBtn.className = "danger-soft";
        trashBtn.type = "button";
        trashBtn.textContent = "Do koše";
        printBtn.addEventListener("click", () => printDocument(item.document_id));
        archiveBtn.addEventListener("click", () => moveDocumentLifecycle(item.document_id, "archive"));
        trashBtn.addEventListener("click", () => moveDocumentLifecycle(item.document_id, "trash"));
        actions.appendChild(printBtn);
        actions.appendChild(archiveBtn);
        actions.appendChild(trashBtn);
        summary.appendChild(title);
        summary.appendChild(meta);
        head.appendChild(summary);
        head.appendChild(toggle);
        detail.appendChild(id);
        detail.appendChild(path);
        detail.appendChild(lifecycle);
        detail.appendChild(snippet);
        detail.appendChild(actions);
        toggle.addEventListener("click", () => {
          const isHidden = detail.classList.toggle("hidden");
          toggle.textContent = isHidden ? "Rozbalit" : "Sbalit";
        });
        card.appendChild(head);
        card.appendChild(detail);
        documentSearchResults.appendChild(card);
      });
    }

    async function postJson(url, payload) {
      const res = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload || {})
      });
      return await res.json();
    }

    async function printDocument(documentId) {
      if (!documentId) return;
      documentSearchStatus.textContent = "Připravuji kopii k tisku...";
      const prepared = await postJson("/api/documents/print/prepare", {document_id: documentId});
      if (!prepared.ok) {
        documentSearchStatus.textContent = prepared.message || "Příprava tisku selhala.";
        return;
      }
      const confirmation = `Potvrzuji, vytiskni print job ${prepared.print_job_id}.`;
      const shouldPrint = window.confirm(`Dokument je připraven k tisku.\n\nPrint job: ${prepared.print_job_id}\n\nOdeslat na tiskárnu?`);
      if (!shouldPrint) {
        documentSearchStatus.textContent = "Tisk je připravený, ale nebyl odeslán na tiskárnu.";
        return;
      }
      documentSearchStatus.textContent = "Odesílám tisk na macOS tiskovou frontu...";
      const printed = await postJson("/api/documents/print/run", {
        print_job_id: prepared.print_job_id,
        confirmation_text: confirmation
      });
      documentSearchStatus.textContent = printed.message || "Tisk dokončen.";
    }

    async function moveDocumentLifecycle(documentId, target) {
      if (!documentId) return;
      const archive = target === "archive";
      const confirmation = archive
        ? `Potvrzuji, archivuj dokument ${documentId}.`
        : `Potvrzuji, přesuň dokument ${documentId} do koše.`;
      const label = archive ? "archivu" : "koše";
      const ok = window.confirm(`Přesunout dokument do ${label}?\n\n${documentId}\n\nSoubor nebude trvale smazán.`);
      if (!ok) return;
      documentSearchStatus.textContent = archive ? "Archivuji dokument..." : "Přesouvám dokument do koše...";
      const result = await postJson("/api/documents/lifecycle", {
        document_id: documentId,
        target,
        confirmation_text: confirmation
      });
      documentSearchStatus.textContent = result.message || "Akce dokončena.";
      if (result.ok && documentSearchInput.value.trim().length >= 2) {
        await searchDocuments();
        await refresh();
      }
    }

    async function openScanDocu(reviewMode = false) {
      const scanDocuWindow = window.open(
        "about:blank",
        reviewMode ? "SamanthaScanDocuReview" : "SamanthaScanDocu",
        "popup=yes,width=1380,height=920,left=80,top=60"
      );
      const activeButton = reviewMode ? scanDocuReviewBtn : scanDocuBtn;
      activeButton.disabled = true;
      showMessage(reviewMode ? "Spouštím ScanDocu Review..." : "Spouštím ScanDocu...");
      try {
        const res = await fetch("/api/scandocu/open", {method: "POST"});
        const data = await res.json();
        showMessage(data.message || data.error || "Hotovo.");
        if (data.ok && data.url) {
          const targetUrl = reviewMode ? `${data.url}/?mode=review` : data.url;
          if (scanDocuWindow) {
            scanDocuWindow.location.href = targetUrl;
            scanDocuWindow.focus();
          } else {
            showMessage(`${data.message || "ScanDocu běží."} Popup okno bylo blokováno, otevři ${targetUrl}`);
          }
        } else if (scanDocuWindow) {
          scanDocuWindow.close();
        }
        await refresh();
      } catch (err) {
        if (scanDocuWindow) {
          scanDocuWindow.close();
        }
        showMessage(`Chyba: ${err}`);
      } finally {
        activeButton.disabled = false;
      }
    }

    refreshBtn.addEventListener("click", refresh);
    scanDocuBtn.addEventListener("click", () => openScanDocu(false));
    scanDocuReviewBtn.addEventListener("click", () => openScanDocu(true));
    processNextBtn.addEventListener("click", () => openScanDocu(false));
    reviewNextBtn.addEventListener("click", () => openScanDocu(true));
    documentSearchBtn.addEventListener("click", searchDocuments);
    documentSearchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchDocuments();
      }
    });
    terminalBtn.addEventListener("click", () => postAction("/api/terminal/open", terminalBtn));
    refresh();
  </script>
</body>
</html>
"""


def run_cockpit_server(host: str = "127.0.0.1", port: int = COCKPIT_PORT) -> None:
    CockpitServer(host=host, port=port).serve()
