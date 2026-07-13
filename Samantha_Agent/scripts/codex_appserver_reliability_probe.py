#!/usr/bin/env python3
"""Isolated reliability probe using the production Codex app-server core."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.codex_appserver import AppServerError, CodexAppServerClient


class ProbeError(RuntimeError):
    """Raised when reliability evidence is incomplete."""


@dataclass(frozen=True)
class DeliveryEvidence:
    sequence: int
    client_message_id: str
    thread_id: str
    turn_id: str
    user_item_confirmed: bool
    turn_status: str
    exact_reply_confirmed: bool
    duplicate_user_items: int
    duration_ms: int

    @property
    def passed(self) -> bool:
        return (
            self.user_item_confirmed
            and self.turn_status == "completed"
            and self.exact_reply_confirmed
            and self.duplicate_user_items == 0
        )


def _item_from_notification(message: dict[str, object]) -> dict[str, object] | None:
    """Compatibility helper retained for focused historical unit tests."""
    params = message.get("params")
    if not isinstance(params, dict):
        return None
    item = params.get("item")
    return item if isinstance(item, dict) else None


def run_probe(
    *,
    count: int,
    timeout: float,
    codex_binary: str,
    workdir: Path,
    restart_after: int | None = None,
) -> list[DeliveryEvidence]:
    if count < 1:
        raise ProbeError("Count must be at least 1")
    if restart_after is not None and not 1 <= restart_after < count:
        raise ProbeError("restart-after must be at least 1 and lower than count")

    evidence: list[DeliveryEvidence] = []
    client = CodexAppServerClient(codex_binary=codex_binary, timeout=timeout)
    try:
        thread_id = client.start_thread(cwd=workdir, ephemeral=restart_after is None)
        for sequence in range(1, count + 1):
            if restart_after is not None and sequence == restart_after + 1:
                client.close()
                client = CodexAppServerClient(codex_binary=codex_binary, timeout=timeout)
                client.resume_thread(thread_id, cwd=workdir)

            nonce = uuid.uuid4().hex
            client_message_id = f"appserver-lab-{nonce}"
            expected_reply = f"VB_ACK_{sequence:03d}_{nonce}"
            receipt = client.send_text(
                thread_id=thread_id,
                client_message_id=client_message_id,
                text=f"Odpověz přesně tímto jediným řádkem: {expected_reply}",
            )
            item = DeliveryEvidence(
                sequence=sequence,
                client_message_id=client_message_id,
                thread_id=thread_id,
                turn_id=receipt.turn_id,
                user_item_confirmed=receipt.user_item_count == 1,
                turn_status=receipt.status,
                exact_reply_confirmed=receipt.answer == expected_reply,
                duplicate_user_items=max(0, receipt.user_item_count - 1),
                duration_ms=receipt.duration_ms,
            )
            evidence.append(item)
            if not item.passed:
                break
    finally:
        client.close()
    return evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--codex-binary", default="codex")
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--restart-after", type=int)
    parser.add_argument("--workdir", type=Path, default=Path(tempfile.gettempdir()))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = run_probe(
            count=args.count,
            timeout=args.timeout,
            codex_binary=args.codex_binary,
            workdir=args.workdir,
            restart_after=args.restart_after,
        )
    except (OSError, AppServerError, ProbeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    passed = len(results) == args.count and all(item.passed for item in results)
    output: dict[str, object] = {
        "passed": passed,
        "requested": args.count,
        "completed": len(results),
        "failures": sum(not item.passed for item in results),
    }
    if results:
        durations = [item.duration_ms for item in results]
        output["duration_ms"] = {
            "minimum": min(durations),
            "maximum": max(durations),
            "average": round(sum(durations) / len(durations)),
        }
    if not args.summary_only:
        output["results"] = [asdict(item) | {"passed": item.passed} for item in results]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
