from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.case_service import build_email_case_draft, format_email_case_draft
from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider


DEFAULT_MAX_CHARS = 4_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only vytvoreni pracovniho e-mailoveho pripadu podle UID."
    )
    parser.add_argument("--uid", required=True, help="UID zpravy z vypisu hlavicek.")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Maximum znaku tela pro analyzu. Vychozi: {DEFAULT_MAX_CHARS}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(
        "Bezpecnost: skript cte jedno telo read-only podle UID, "
        "nic neodesila, nemaze, nepresouva, neotevira odkazy, "
        "nestahuje prilohy a nic neuklada do memory.",
        file=sys.stderr,
    )

    try:
        provider = ICloudReadOnlyEmailProvider()
        message = provider.read_message_by_uid(uid=args.uid, max_chars=args.max_chars)
    except EmailConfigError:
        print("Chyba: chybi lokalni konfigurace pro iCloud Mail.", file=sys.stderr)
        print("Dalsi krok: zkontroluj lokalni .env.", file=sys.stderr)
        return 1
    except EmailProviderError as exc:
        print(f"Chyba: vytvoreni e-mailoveho pripadu selhalo: {exc}", file=sys.stderr)
        return 1

    case = build_email_case_draft(message)
    print(format_email_case_draft(case))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
