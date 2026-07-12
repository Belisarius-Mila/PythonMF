"""Temporary, private working protocol for VoiceBridge brainstorming."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TVBCP_PATH = PROJECT_ROOT / "data" / "private" / "voice_bridge" / "TVBCP_current.txt"
MAX_TVBCP_CHARS = 120_000
MAX_FIELD_CHARS = 4_000


def _clean_field(value: str, *, limit: int = MAX_FIELD_CHARS) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(value or ""))
    return " ".join(text.split())[:limit].strip()


def _timestamp(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    return moment.replace(microsecond=0).astimezone().isoformat()


def start_tvbcp(
    *,
    title: str,
    path: Path = DEFAULT_TVBCP_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create today's protocol without overwriting an existing working file."""
    target = Path(path)
    safe_title = _clean_field(title, limit=300) or "VoiceBridge brainstorming"
    with exclusive_file_lock(target):
        if target.exists():
            return {"ok": True, "created": False, "active": True, "path": target}
        created_at = _timestamp(now)
        content = (
            "TVBCP – Temporary VoiceBridge Communication Protocol\n"
            "======================================================\n\n"
            "Stav: AKTIVNÍ – dočasný pracovní protokol\n"
            f"Založeno: {created_at}\n"
            f"Téma: {safe_title}\n\n"
            "Pravidla\n"
            "--------\n"
            "- Jen stručné myšlenky, návrhy, závěry a otevřené otázky.\n"
            "- Neukládat plné přepisy, tajemství, osobní údaje ani citlivé krizové příběhy.\n"
            "- Nic se automaticky nemaže ani nepřesouvá. O osudu protokolu rozhodne Míla.\n\n"
            "Průběžný záznam\n"
            "----------------\n"
        )
        atomic_replace_text_under_external_lock(target, content)
    return {"ok": True, "created": True, "active": True, "path": target}


def append_tvbcp_entry(
    *,
    discussed: str = "",
    conclusion: str = "",
    open_question: str = "",
    next_step: str = "",
    path: Path = DEFAULT_TVBCP_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append one bounded structured entry under a cross-process lock."""
    fields = (
        ("O čem jsme mluvili", _clean_field(discussed)),
        ("K čemu jsme došli", _clean_field(conclusion)),
        ("Otevřená otázka", _clean_field(open_question)),
        ("Další krok", _clean_field(next_step)),
    )
    populated = [(label, value) for label, value in fields if value]
    if not populated:
        raise ValueError("TVBCP záznam nemá žádný obsah.")

    target = Path(path)
    with exclusive_file_lock(target):
        if not target.exists():
            raise FileNotFoundError("TVBCP není aktivní. Nejdřív jej založ.")
        current = target.read_text(encoding="utf-8")
        entry_lines = ["", f"[{_timestamp(now)}]"]
        entry_lines.extend(f"{label}: {value}" for label, value in populated)
        updated = current.rstrip() + "\n" + "\n".join(entry_lines) + "\n"
        if len(updated) > MAX_TVBCP_CHARS:
            raise ValueError("TVBCP dosáhl bezpečnostního limitu velikosti; je čas jej uzavřít.")
        atomic_replace_text_under_external_lock(target, updated)
    return {"ok": True, "active": True, "chars": len(updated), "path": target}


def tvbcp_status(path: Path = DEFAULT_TVBCP_PATH) -> dict[str, Any]:
    """Return the one fixed private protocol file for read-only Cockpit display."""
    target = Path(path)
    if not target.exists():
        return {
            "ok": True,
            "active": False,
            "content": "TVBCP zatím není aktivní.",
            "updated_at": "",
            "chars": 0,
        }
    content = target.read_text(encoding="utf-8")[:MAX_TVBCP_CHARS]
    return {
        "ok": True,
        "active": True,
        "content": content,
        "updated_at": datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).astimezone().isoformat(),
        "chars": len(content),
    }


TVBCP_PAGE_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TVBCP – pracovní protokol</title>
  <style>
    :root { color-scheme: light dark; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f4f6f8; color: #1e2933; }
    main { max-width: 900px; margin: 0 auto; padding: 18px; }
    header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; }
    h1 { margin: 0; font-size: 22px; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; }
    button { border: 1px solid #aeb8c2; border-radius: 9px; padding: 9px 13px; background: #fff; color: #1e2933; font: inherit; }
    button.primary { background: #155eef; border-color: #155eef; color: white; }
    #status { margin: 12px 0; color: #52606d; }
    pre { margin: 0; min-height: 55vh; padding: 16px; border: 1px solid #d9e0e7; border-radius: 12px; background: white; color: #17212b; white-space: pre-wrap; overflow-wrap: anywhere; font: 15px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; }
    @media (prefers-color-scheme: dark) {
      body { background: #101418; color: #edf2f7; }
      button { background: #252c33; color: #edf2f7; border-color: #53606c; }
      pre { background: #171c21; color: #edf2f7; border-color: #35404a; }
      #status { color: #aeb8c2; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <h1>TVBCP – pracovní protokol</h1>
    <div class="actions">
      <button id="refreshBtn">Obnovit</button>
      <button class="primary" id="closeBtn">Zavřít a vrátit se</button>
    </div>
  </header>
  <div id="status">Načítám…</div>
  <pre id="content">Načítám protokol…</pre>
</main>
<script>
  const statusNode = document.getElementById("status");
  const contentNode = document.getElementById("content");
  async function refreshTvbcp() {
    try {
      const response = await fetch("/api/voice-bridge/tvbcp", {cache: "no-store"});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || `HTTP ${response.status}`);
      contentNode.textContent = data.content || "TVBCP je prázdný.";
      statusNode.textContent = data.active
        ? `Aktivní · naposledy změněno ${data.updated_at || "neznámo"} · ${data.chars || 0} znaků`
        : "TVBCP není aktivní.";
    } catch (error) {
      statusNode.textContent = `Protokol se nepodařilo načíst: ${error}`;
    }
  }
  document.getElementById("refreshBtn").addEventListener("click", refreshTvbcp);
  document.getElementById("closeBtn").addEventListener("click", () => {
    window.close();
    if (!window.closed) window.location.href = "/";
  });
  refreshTvbcp();
  window.setInterval(refreshTvbcp, 10000);
</script>
</body>
</html>
"""
