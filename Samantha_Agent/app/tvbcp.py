"""Temporary, private working protocol for VoiceBridge brainstorming."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TVBCP_PATH = PROJECT_ROOT / "data" / "private" / "voice_bridge" / "TVBCP_current.txt"
MAX_TVBCP_CHARS = 240_000
MAX_FIELD_CHARS = 20_000

OLD_RULES = (
    "- Jen stručné myšlenky, návrhy, závěry a otevřené otázky.\n"
    "- Neukládat plné přepisy, tajemství, osobní údaje ani citlivé krizové příběhy.\n"
    "- Nic se automaticky nemaže ani nepřesouvá. O osudu protokolu rozhodne Míla."
)
CURRENT_RULES = (
    "- Zachovat plné věcné znění podstatných návrhů a myšlenek Míly i Adama.\n"
    "- Není to kopie VoiceBridge chatu: vynechat technické mezistavy, testy, příkazy a provozní hlášky.\n"
    "- Neukládat tajemství, osobní údaje ani identifikující citlivé krizové příběhy.\n"
    "- VoiceBridge vrací stručné shrnutí; detailní myšlenková práce patří sem.\n"
    "- Nic se automaticky nemaže ani nepřesouvá. O osudu protokolu rozhodne Míla."
)


def _clean_text(value: str, *, limit: int = MAX_FIELD_CHARS) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned[:limit].rstrip()


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
    safe_title = _clean_text(title, limit=300) or "VoiceBridge brainstorming"
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
            f"{CURRENT_RULES}\n\n"
            "Průběžný záznam\n"
            "----------------\n"
        )
        atomic_replace_text_under_external_lock(target, content)
    return {"ok": True, "created": True, "active": True, "path": target}


def update_tvbcp_contract(path: Path = DEFAULT_TVBCP_PATH) -> dict[str, Any]:
    """Upgrade the protocol rules in place without deleting existing entries."""
    target = Path(path)
    with exclusive_file_lock(target):
        if not target.exists():
            raise FileNotFoundError("TVBCP není aktivní. Nejdřív jej založ.")
        current = target.read_text(encoding="utf-8")
        if CURRENT_RULES in current:
            return {"ok": True, "changed": False, "active": True, "path": target}
        if OLD_RULES not in current:
            raise ValueError("TVBCP má neznámou hlavičku pravidel; automaticky ji nepřepisuji.")
        updated = current.replace(OLD_RULES, CURRENT_RULES, 1)
        atomic_replace_text_under_external_lock(target, updated)
    return {"ok": True, "changed": True, "active": True, "path": target}


def append_tvbcp_entry(
    *,
    mila: str = "",
    adam: str = "",
    discussed: str = "",
    conclusion: str = "",
    open_question: str = "",
    next_step: str = "",
    path: Path = DEFAULT_TVBCP_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append full substantive proposals plus optional structured conclusions."""
    fields = (
        ("Míla – plné znění návrhu / myšlenky", _clean_text(mila)),
        ("Adam – plné znění návrhu / myšlenky", _clean_text(adam)),
        ("Téma rozhovoru", _clean_text(discussed)),
        ("Dohodnutý závěr", _clean_text(conclusion)),
        ("Otevřená otázka", _clean_text(open_question)),
        ("Další věcný krok", _clean_text(next_step)),
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
        for label, value in populated:
            entry_lines.extend((f"{label}:", value, ""))
        updated = current.rstrip() + "\n" + "\n".join(entry_lines).rstrip() + "\n"
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
