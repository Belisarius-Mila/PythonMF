from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VOICE_COMMAND_INBOX_DIR = PROJECT_ROOT / "data" / "private" / "voice_inbox"


@dataclass(frozen=True)
class VoiceCommandTriage:
    risk: str
    action: str
    reason: str
    requires_confirmation: bool


@dataclass(frozen=True)
class VoiceCommand:
    ok: bool
    path: str
    created_at: str
    status: str
    text: str
    triage: VoiceCommandTriage
    message: str


def load_latest_voice_command(*, inbox_dir: Path = VOICE_COMMAND_INBOX_DIR) -> VoiceCommand:
    latest_path = inbox_dir / "latest_voice_command.md"
    if not latest_path.exists():
        triage = VoiceCommandTriage(
            risk="none",
            action="wait",
            reason="Voice inbox zatím nemá latest_voice_command.md.",
            requires_confirmation=False,
        )
        return VoiceCommand(
            ok=False,
            path=str(latest_path),
            created_at="",
            status="missing",
            text="",
            triage=triage,
            message="Žádný hlasový pokyn zatím není uložený.",
        )
    return parse_voice_command_file(latest_path)


def parse_voice_command_file(path: Path) -> VoiceCommand:
    text = path.read_text(encoding="utf-8")
    created_at = extract_header_value(text, "Created at")
    status = extract_header_value(text, "Status") or "unknown"
    command_text = extract_text_section(text)
    triage = triage_voice_command(command_text)
    return VoiceCommand(
        ok=bool(command_text),
        path=str(path),
        created_at=created_at,
        status=status,
        text=command_text,
        triage=triage,
        message="Hlasový pokyn načtený a vyhodnocený." if command_text else "Hlasový pokyn nemá text.",
    )


def extract_header_value(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_text_section(text: str) -> str:
    match = re.search(r"^## Text\s*$\n+(.*)", text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def triage_voice_command(text: str) -> VoiceCommandTriage:
    folded = normalize_for_triage(text)
    if not folded:
        return VoiceCommandTriage(
            risk="none",
            action="wait",
            reason="Pokyn je prázdný.",
            requires_confirmation=False,
        )

    blocked_terms = (
        "zaplat",
        "platbu",
        "odesli platbu",
        "posli penize",
        "pošli peníze",
        "heslo",
        "token",
        "api key",
        "rodne cislo",
        "rodné číslo",
    )
    confirmation_terms = (
        "smaz",
        "smaž",
        "vymaz",
        "vymaž",
        "trvale smaz",
        "trvale smaž",
        "posli email",
        "pošli email",
        "posli e-mail",
        "pošli e-mail",
        "odesli email",
        "odešli email",
        "odesli e-mail",
        "odešli e-mail",
        "posli sms",
        "pošli sms",
        "odesli sms",
        "odešli sms",
        "vytiskni",
        "tisk",
        "archivuj",
        "presun",
        "přesuň",
        "commit",
        "push",
        "uloz do dokumentu",
        "ulož do dokumentu",
        "zmen metadata",
        "změň metadata",
    )
    draft_terms = (
        "navrhni",
        "napiš návrh",
        "napis navrh",
        "priprav",
        "připrav",
        "sepiš",
        "sepis",
        "vytvor checklist",
        "vytvoř checklist",
    )

    if any(term in folded for term in blocked_terms):
        return VoiceCommandTriage(
            risk="blocked",
            action="ask_user",
            reason="Pokyn může obsahovat platbu, tajemství nebo vysoce citlivou akci.",
            requires_confirmation=True,
        )
    if any(term in folded for term in confirmation_terms):
        return VoiceCommandTriage(
            risk="needs_confirmation",
            action="prepare_and_confirm",
            reason="Pokyn může měnit stav, odesílat, mazat, tisknout, archivovat nebo publikovat.",
            requires_confirmation=True,
        )
    if any(term in folded for term in draft_terms):
        return VoiceCommandTriage(
            risk="draft",
            action="draft_only",
            reason="Pokyn vypadá jako příprava textu nebo návrhu bez přímého zásahu do dat.",
            requires_confirmation=False,
        )
    return VoiceCommandTriage(
        risk="read_only",
        action="execute_read_only",
        reason="Pokyn nevypadá jako mazání, odesílání, platba, tisk, archivace ani změna dat.",
        requires_confirmation=False,
    )


def normalize_for_triage(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def voice_command_to_dict(command: VoiceCommand) -> dict[str, Any]:
    result = asdict(command)
    return result


def format_voice_command_for_adam(command: VoiceCommand) -> str:
    triage = command.triage
    lines = [
        "VOICE INBOX TRIAGE",
        f"- ok: {command.ok}",
        f"- path: {command.path}",
        f"- created_at: {command.created_at or 'neznámé'}",
        f"- status: {command.status}",
        f"- risk: {triage.risk}",
        f"- action: {triage.action}",
        f"- requires_confirmation: {triage.requires_confirmation}",
        f"- reason: {triage.reason}",
        "",
        "TEXT:",
        command.text or "(bez textu)",
    ]
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only triage of the latest Samantha Cockpit voice command.")
    parser.add_argument("--inbox-dir", type=Path, default=VOICE_COMMAND_INBOX_DIR)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    command = load_latest_voice_command(inbox_dir=args.inbox_dir)
    if args.json:
        print(json.dumps(voice_command_to_dict(command), ensure_ascii=False, indent=2))
    else:
        print(format_voice_command_for_adam(command))
    return 0 if command.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
