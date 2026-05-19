from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from app.email.redaction import redact_email_addresses


DEFAULT_MAX_CHARS = 2_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only nacteni jednoho iCloud e-mailu podle UID."
    )
    parser.add_argument(
        "--uid",
        required=True,
        help="UID zpravy z vypisu hlavicek.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Maximum znaku tela k vypsani. Vychozi: {DEFAULT_MAX_CHARS}.",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Vypise text bez redigovani e-mailovych adres. Pouzit jen vedome.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        provider = ICloudReadOnlyEmailProvider()
        message = provider.read_message_by_uid(
            uid=args.uid,
            max_chars=args.max_chars,
        )
    except EmailConfigError:
        print("Chyba: chybi lokalni konfigurace pro iCloud Mail.", file=sys.stderr)
        print("Dalsi krok: zkontroluj lokalni .env.", file=sys.stderr)
        return 1
    except EmailProviderError as exc:
        print(f"Chyba: read-only nacteni e-mailu selhalo: {exc}", file=sys.stderr)
        return 1

    print(f"UID: {message.header.internal_id}")
    print(f"Datum: {message.header.date}")
    print(f"Od: {message.header.sender}")
    print(f"Predmet: {message.header.subject or '(bez predmetu)'}")
    print()
    print("Text:")
    body_text = message.body_text or "(nenalezeno textove telo)"
    if not args.no_redact:
        body_text = redact_email_addresses(body_text)
    print(body_text)

    if message.truncated:
        print()
        print("[Zkraceno podle limitu --max-chars]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
