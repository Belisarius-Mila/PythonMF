#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.adam_voice_mode import (
    ADAM_PENDING_COMMAND_PATH,
    ADAM_VOICE_HISTORY_PATH,
    append_manual_voice_history_turn,
    load_pending_for_adam,
    mark_pending_for_adam_processed,
)
from app.adam_service import record_adam_text_reply
from app.speech.voice_inbox import VOICE_COMMAND_INBOX_DIR, load_latest_voice_command


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zapíše odpověď Adama k čekajícímu hlasovému pokynu a označí ho jako vyřízený."
    )
    parser.add_argument("response", nargs="+", help="Odpověď, kterou Adam po zpracování v Codexu vrátil.")
    parser.add_argument("--path", type=Path, default=ADAM_PENDING_COMMAND_PATH)
    parser.add_argument("--history-path", type=Path, default=ADAM_VOICE_HISTORY_PATH)
    parser.add_argument("--inbox-dir", type=Path, default=VOICE_COMMAND_INBOX_DIR)
    parser.add_argument(
        "--latest-command",
        action="store_true",
        help="Zapsat odpověď k poslednímu hlasovému pokynu bez změny pending záznamu.",
    )
    parser.add_argument(
        "--user-text",
        default="",
        help="Explicitní text uživatelského dotazu, ke kterému se odpověď ukládá.",
    )
    parser.add_argument(
        "--request-id",
        default="",
        help="ID textového dotazu z managed Adam fronty.",
    )
    parser.add_argument(
        "--route",
        default="codex_terminal_final",
        help="Název kanálu odpovědi pro Cockpit.",
    )
    parser.add_argument("--json", action="store_true", help="Vypsat aktualizovaný pending záznam jako JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    response = " ".join(args.response).strip()
    if args.request_id.strip():
        request_result = record_adam_text_reply(
            request_id=args.request_id.strip(),
            response=response,
        )
        turn = append_manual_voice_history_turn(
            user_text=args.user_text.strip(),
            adam_response=response,
            route=args.route.strip() or "codex_terminal_final",
            path=args.history_path,
        )
        result = {
            "ok": bool(request_result.get("ok")),
            "status": "recorded_text_request_reply",
            "processed_at": turn.get("created_at"),
            "response": response,
            "user_text": args.user_text.strip(),
            "route": args.route.strip() or "codex_terminal_final",
            "request_id": args.request_id.strip(),
            "request": request_result,
        }
    elif args.user_text.strip():
        turn = append_manual_voice_history_turn(
            user_text=args.user_text.strip(),
            adam_response=response,
            route=args.route.strip() or "codex_terminal_final",
            path=args.history_path,
        )
        result = {
            "ok": True,
            "status": "recorded_explicit_user_text_reply",
            "processed_at": turn.get("created_at"),
            "response": response,
            "user_text": args.user_text.strip(),
            "route": args.route.strip() or "codex_terminal_final",
        }
    elif args.latest_command:
        command = load_latest_voice_command(inbox_dir=args.inbox_dir)
        turn = append_manual_voice_history_turn(
            user_text=command.text,
            adam_response=response,
            route=args.route.strip() or "codex_terminal_final",
            path=args.history_path,
        )
        result = {
            "ok": True,
            "status": "recorded_latest_command_reply",
            "processed_at": turn.get("created_at"),
            "response": response,
            "latest_command_path": str(command.path),
        }
    else:
        pending = load_pending_for_adam(path=args.path)
        if pending.get("pending"):
            result = mark_pending_for_adam_processed(
                adam_response=response,
                path=args.path,
                history_path=args.history_path,
            )
        else:
            command = load_latest_voice_command(inbox_dir=args.inbox_dir)
            turn = append_manual_voice_history_turn(
                user_text=command.text,
                adam_response=response,
                route=args.route.strip() or "codex_terminal_final",
                path=args.history_path,
            )
            result = {
                "ok": True,
                "status": "recorded_latest_command_reply",
                "processed_at": turn.get("created_at"),
                "response": response,
                "latest_command_path": str(command.path),
            }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("ADAM VOICE REPLY")
        print(f"- ok: {str(bool(result.get('ok'))).lower()}")
        print(f"- status: {result.get('status') or 'unknown'}")
        print(f"- processed_at: {result.get('processed_at') or '-'}")
        print("")
        print("RESPONSE:")
        print(result.get("response") or result.get("message") or response)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
