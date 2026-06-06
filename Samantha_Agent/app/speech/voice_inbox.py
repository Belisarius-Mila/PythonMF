from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
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


def wait_for_latest_voice_command(
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    timeout_seconds: float = 180.0,
    poll_seconds: float = 1.0,
    since_mtime_ns: int | None = None,
    since_signature: str | None = None,
) -> VoiceCommand:
    latest_path = inbox_dir / "latest_voice_command.md"
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while True:
        if latest_path.exists():
            mtime_ns = latest_path.stat().st_mtime_ns
            signature = file_signature(latest_path)
            if since_signature is not None:
                if signature != since_signature:
                    return parse_voice_command_file(latest_path)
            elif since_mtime_ns is None or mtime_ns > since_mtime_ns:
                return parse_voice_command_file(latest_path)
        if time.monotonic() >= deadline:
            break
        time.sleep(max(0.1, poll_seconds))

    triage = VoiceCommandTriage(
        risk="none",
        action="wait",
        reason="Během čekání nepřišel nový hlasový pokyn.",
        requires_confirmation=False,
    )
    return VoiceCommand(
        ok=False,
        path=str(latest_path),
        created_at="",
        status="timeout",
        text="",
        triage=triage,
        message="Nový hlasový pokyn nebyl nalezen.",
    )


def latest_voice_command_mtime_ns(*, inbox_dir: Path = VOICE_COMMAND_INBOX_DIR) -> int | None:
    latest_path = inbox_dir / "latest_voice_command.md"
    if not latest_path.exists():
        return None
    return latest_path.stat().st_mtime_ns


def latest_voice_command_signature(*, inbox_dir: Path = VOICE_COMMAND_INBOX_DIR) -> str | None:
    latest_path = inbox_dir / "latest_voice_command.md"
    if not latest_path.exists():
        return None
    return file_signature(latest_path)


def file_signature(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    outbound_message_terms = (
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
        "posli zpravu",
        "pošli zprávu",
        "odesli zpravu",
        "odešli zprávu",
        "napiš sms",
        "napis sms",
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
    if any(term in folded for term in outbound_message_terms):
        return VoiceCommandTriage(
            risk="outbound_confirmation",
            action="prepare_outbound_and_confirm",
            reason="Pokyn chce odeslat SMS/e-mail nebo jinou zprávu navenek. To je povolené jen po samostatném potvrzení.",
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
    parser.add_argument("--wait", action="store_true", help="Wait for a latest voice command before printing triage.")
    parser.add_argument("--follow", action="store_true", help="Keep watching and print every new voice command triage.")
    parser.add_argument("--since-now", action="store_true", help="With --wait, ignore an existing latest command and wait for a newer one.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Maximum seconds to wait with --wait.")
    parser.add_argument("--poll", type=float, default=1.0, help="Polling interval in seconds with --wait.")
    parser.add_argument("--count", type=int, default=0, help="With --follow, stop after this many commands. 0 means no count limit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    since_mtime_ns = latest_voice_command_mtime_ns(inbox_dir=args.inbox_dir) if args.since_now else None
    since_signature = latest_voice_command_signature(inbox_dir=args.inbox_dir) if args.since_now else None
    if args.follow:
        return follow_voice_commands(
            inbox_dir=args.inbox_dir,
            timeout_seconds=args.timeout,
            poll_seconds=args.poll,
            since_mtime_ns=since_mtime_ns,
            since_signature=since_signature,
            json_output=args.json,
            count=args.count,
        )
    command = (
        wait_for_latest_voice_command(
            inbox_dir=args.inbox_dir,
            timeout_seconds=args.timeout,
            poll_seconds=args.poll,
            since_mtime_ns=since_mtime_ns,
            since_signature=since_signature,
        )
        if args.wait
        else load_latest_voice_command(inbox_dir=args.inbox_dir)
    )
    if args.json:
        print(json.dumps(voice_command_to_dict(command), ensure_ascii=False, indent=2))
    else:
        print(format_voice_command_for_adam(command))
    return 0 if command.ok else 1


def follow_voice_commands(
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    timeout_seconds: float = 180.0,
    poll_seconds: float = 1.0,
    since_mtime_ns: int | None = None,
    since_signature: str | None = None,
    json_output: bool = False,
    count: int = 0,
) -> int:
    processed = 0
    current_since = since_mtime_ns
    current_signature = since_signature
    while True:
        command = wait_for_latest_voice_command(
            inbox_dir=inbox_dir,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
            since_mtime_ns=current_since,
            since_signature=current_signature,
        )
        if not command.ok:
            print(json.dumps(voice_command_to_dict(command), ensure_ascii=False) if json_output else format_voice_command_for_adam(command), flush=True)
            return 0 if processed else 1

        print(json.dumps(voice_command_to_dict(command), ensure_ascii=False) if json_output else format_voice_command_for_adam(command), flush=True)
        processed += 1
        current_since = latest_voice_command_mtime_ns(inbox_dir=inbox_dir)
        current_signature = latest_voice_command_signature(inbox_dir=inbox_dir)
        if count > 0 and processed >= count:
            return 0
        if not json_output:
            print("\n--- čekám na další hlasový pokyn ---\n", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
