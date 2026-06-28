#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.adam_voice_mode import clear_codex_approval_request, save_codex_approval_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Zapíše nebo vyčistí runtime stav, že Codex čeká na potvrzení.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    set_parser = subparsers.add_parser("set", help="Zapsat čekající Codex approval stav.")
    set_parser.add_argument("--reason", required=True, help="Proč Codex čeká na potvrzení.")
    set_parser.add_argument("--command", dest="command_text", default="", help="Stručný bezpečný popis příkazu nebo akce.")
    set_parser.add_argument("--risk", default="", help="Stručné lidské shrnutí rizika, bez tajemství a dlouhých detailů.")
    set_parser.add_argument("--next-step", default="", help="Co má Míla udělat z iPhonu nebo u Macu.")
    set_parser.add_argument("--confirmation-text", default="", help="Přesná potvrzovací věta, kterou má Cockpit zobrazit a umět odeslat.")

    clear_parser = subparsers.add_parser("clear", help="Označit Codex approval stav jako vyřešený.")
    clear_parser.add_argument("--note", default="", help="Stručná poznámka k vyřešení.")

    parser.add_argument("--json", action="store_true", help="Vypsat celý runtime záznam jako JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "set":
        result = save_codex_approval_request(
            reason=args.reason,
            command=args.command_text,
            risk=args.risk,
            next_step=args.next_step,
            confirmation_text=args.confirmation_text,
        )
    else:
        result = clear_codex_approval_request(note=args.note)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("CODEX APPROVAL NOTICE")
        print(f"- active: {str(bool(result.get('active'))).lower()}")
        print(f"- status: {result.get('status') or 'unknown'}")
        print(f"- updated_at: {result.get('updated_at') or '-'}")
        detail = result.get("reason") or result.get("note") or ""
        if detail:
            print(f"- detail: {detail}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
