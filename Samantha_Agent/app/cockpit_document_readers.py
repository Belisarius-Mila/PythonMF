"""HTML renderers for Cockpit document and purchase reader windows.

Only page generation lives here; file resolution and action endpoints remain
owned by the Cockpit server.
"""

from __future__ import annotations

import html
import json
from urllib.parse import quote


def document_reader_page_html(document_id: str, title: str, viewer_kind: str = "pdf") -> str:
    safe_title = html.escape(title or "Dokument")
    safe_document_id = html.escape(document_id)
    document_id_json = json.dumps(document_id, ensure_ascii=False)
    pdf_url = f"/documents/pdf?document_id={quote(document_id, safe='')}"
    safe_pdf_url = html.escape(pdf_url, quote=True)
    if viewer_kind == "image":
        viewer_html = (
            f'<main class="image-viewer"><img class="document-image" src="{safe_pdf_url}" '
            f'alt="Náhled dokumentu"></main>\n'
            f'  <noscript><div class="fallback"><a class="button primary" href="{safe_pdf_url}">'
            f"Otevřít obrázek</a></div></noscript>"
        )
    else:
        viewer_html = (
            f'<iframe class="viewer" src="{safe_pdf_url}" title="PDF dokument"></iframe>\n'
            f'  <noscript><div class="fallback"><a class="button primary" href="{safe_pdf_url}">'
            f"Otevřít PDF</a></div></noscript>"
        )
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Čtení dokumentu - {safe_title}</title>
  <style>
    :root {{ color-scheme: light; --blue: #2563eb; --ink: #172033; --muted: #667085; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: var(--ink); }}
    .bar {{ min-height: 58px; display: grid; grid-template-columns: minmax(0, 1fr) auto auto auto; gap: 10px; align-items: center; padding: 10px 14px; background: white; border-bottom: 1px solid #d7dee8; }}
    .title {{ min-width: 0; }}
    .title strong {{ display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .title span {{ color: var(--muted); font-size: 12px; }}
    button, a.button {{ border: 0; border-radius: 6px; padding: 9px 12px; font: inherit; font-weight: 700; cursor: pointer; background: #e4e9f0; color: #172033; text-decoration: none; white-space: nowrap; }}
    button.primary, a.button.primary {{ background: var(--blue); color: white; }}
    .status {{ grid-column: 1 / -1; color: var(--muted); font-size: 13px; min-height: 18px; }}
    .viewer {{ width: 100vw; height: calc(100vh - 82px); border: 0; display: block; background: white; }}
    .image-viewer {{ width: 100vw; min-height: calc(100vh - 82px); overflow: auto; display: grid; place-items: start center; padding: 16px; background: #0f172a; }}
    .document-image {{ max-width: 100%; height: auto; background: white; box-shadow: 0 18px 42px rgba(15, 23, 42, 0.28); }}
    .fallback {{ padding: 16px; }}
    @media (max-width: 720px) {{
      .bar {{ grid-template-columns: 1fr; align-items: stretch; }}
      button, a.button {{ width: 100%; text-align: center; }}
      .viewer {{ height: calc(100vh - 210px); }}
      .image-viewer {{ min-height: calc(100vh - 210px); padding: 10px; }}
    }}
  </style>
</head>
<body>
  <div class="bar">
    <div class="title">
      <strong>{safe_title}</strong>
      <span>{safe_document_id}</span>
    </div>
    <button type="button" class="primary" id="readerPrintBtn">Tisknout</button>
    <button type="button" id="readerBackBtn">Zpět do Cockpitu</button>
    <button type="button" id="readerCloseBtn">Zavřít okno</button>
    <div class="status" id="readerStatus">Dokument je otevřený ke čtení. Po kontrole ho můžeš rovnou vytisknout.</div>
  </div>
  {viewer_html}
  <script>
    const DOCUMENT_ID = {document_id_json};
    const readerStatus = document.getElementById("readerStatus");
    const readerPrintBtn = document.getElementById("readerPrintBtn");
    const readerBackBtn = document.getElementById("readerBackBtn");
    const readerCloseBtn = document.getElementById("readerCloseBtn");

    async function postJson(url, payload) {{
      const res = await fetch(url, {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(payload || {{}})
      }});
      return await res.json();
    }}

    function focusCockpit() {{
      if (window.opener && !window.opener.closed) {{
        try {{ window.opener.focus(); }} catch (_) {{ /* Opener may be inaccessible. */ }}
        readerStatus.textContent = "Vracím zpět původní Cockpit.";
        window.close();
        window.setTimeout(() => {{
          window.location.href = "/";
        }}, 350);
        return true;
      }}
      window.location.href = "/";
      return false;
    }}

    function closeReader() {{
      if (window.opener && !window.opener.closed) {{
        try {{ window.opener.focus(); }} catch (_) {{ /* Opener may be inaccessible. */ }}
      }}
      window.close();
      window.setTimeout(() => {{
        readerStatus.textContent = "Pokud se okno nezavřelo, použij Zpět do Cockpitu. Dokument můžeš vytisknout i odsud.";
      }}, 300);
    }}

    async function printFromReader() {{
      if (!DOCUMENT_ID) return;
      readerPrintBtn.disabled = true;
      readerStatus.textContent = "Připravuji dokument k tisku...";
      try {{
        const prepared = await postJson("/api/documents/print/prepare", {{document_id: DOCUMENT_ID}});
        if (!prepared.ok) {{
          readerStatus.textContent = prepared.message || "Příprava tisku selhala.";
          return;
        }}
        const confirmation = `Potvrzuji, vytiskni print job ${{prepared.print_job_id}}.`;
        const shouldPrint = window.confirm(`Dokument je připraven k tisku.\\n\\nPrint job: ${{prepared.print_job_id}}\\n\\nOdeslat na tiskárnu?`);
        if (!shouldPrint) {{
          readerStatus.textContent = "Tisk je připravený, ale nebyl odeslán na tiskárnu.";
          return;
        }}
        readerStatus.textContent = "Odesílám tisk na macOS tiskovou frontu...";
        const printed = await postJson("/api/documents/print/run", {{
          print_job_id: prepared.print_job_id,
          confirmation_text: confirmation
        }});
        readerStatus.textContent = printed.message || "Tisk dokončen.";
      }} catch (err) {{
        readerStatus.textContent = `Chyba tisku: ${{err}}`;
      }} finally {{
        readerPrintBtn.disabled = false;
      }}
    }}

    readerPrintBtn.addEventListener("click", printFromReader);
    readerBackBtn.addEventListener("click", focusCockpit);
    readerCloseBtn.addEventListener("click", closeReader);
  </script>
</body>
</html>"""


def purchase_reader_page_html(purchase_id: str, title: str) -> str:
    safe_title = html.escape(title or "Nákup / faktura")
    safe_purchase_id = html.escape(purchase_id)
    pdf_url = f"/purchases/pdf?purchase_id={quote(purchase_id, safe='')}"
    safe_pdf_url = html.escape(pdf_url, quote=True)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nákup / záruka - {safe_title}</title>
  <style>
    :root {{ color-scheme: light; --blue: #2563eb; --ink: #172033; --muted: #667085; }}
    body {{ height: 100vh; display: flex; flex-direction: column; margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #f6f7fb; }}
    header {{ flex: none; flex-wrap: wrap; display: flex; gap: 12px; align-items: center; justify-content: space-between; padding: 14px 18px; background: #fff; border-bottom: 1px solid #d8deea; }}
    header > div:first-child {{ min-width: 0; flex: 1 1 240px; overflow-wrap: anywhere; }}
    h1 {{ margin: 0; font-size: 18px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin-top: 3px; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button, a.button {{ border: 1px solid #b9c4d6; background: #fff; color: var(--ink); border-radius: 7px; padding: 8px 11px; font-size: 14px; text-decoration: none; cursor: pointer; }}
    a.primary {{ background: var(--blue); color: #fff; border-color: var(--blue); }}
    main {{ flex: 1; min-height: 0; }}
    .status {{ flex-basis: 100%; color: var(--muted); font-size: 13px; }}
    iframe {{ width: 100%; height: 100%; border: 0; background: #fff; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{safe_title}</h1>
      <div class="meta">Nákupní evidence: {safe_purchase_id}</div>
    </div>
    <div class="actions">
      <a class="button primary" href="{safe_pdf_url}" target="_blank" rel="noopener">Otevřít PDF</a>
      <button type="button" id="readerBackBtn">Zpět do Cockpitu</button>
      <button type="button" id="readerCloseBtn">Zavřít okno</button>
    </div>
    <div class="status" id="readerStatus" role="status"></div>
  </header>
  <main>
    <iframe title="PDF nákupní faktury" src="{safe_pdf_url}"></iframe>
  </main>
  <script>
    const readerStatus = document.getElementById("readerStatus");
    function focusCockpit() {{
      if (window.opener && !window.opener.closed) {{
        try {{ window.opener.focus(); }} catch (_) {{ /* Opener may be inaccessible. */ }}
        readerStatus.textContent = "Vracím zpět původní Cockpit.";
        window.close();
        window.setTimeout(() => {{
          window.location.href = "/";
        }}, 350);
        return true;
      }}
      window.location.href = "/";
      return false;
    }}

    function closeReader() {{
      if (window.opener && !window.opener.closed) {{
        try {{ window.opener.focus(); }} catch (_) {{ /* Opener may be inaccessible. */ }}
      }}
      window.close();
      window.setTimeout(() => {{
        readerStatus.textContent = "Pokud se okno nezavřelo, použij Zpět do Cockpitu.";
      }}, 300);
    }}

    document.getElementById("readerBackBtn").addEventListener("click", focusCockpit);
    document.getElementById("readerCloseBtn").addEventListener("click", closeReader);
  </script>
</body>
</html>"""
