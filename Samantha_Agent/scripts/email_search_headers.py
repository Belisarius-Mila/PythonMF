from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.email.config import EmailConfigError
from app.email.icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider


DEFAULT_LIMIT = 10
DEFAULT_SCAN_LIMIT = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only vyhledani v iCloud e-mailovych hlavickach."
    )
    parser.add_argument(
        "--query",
        default="",
        help="Hledany text v datu, odesilateli nebo predmetu. Bez dotazu vypise posledni hlavicky.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum vysledku. Vychozi: {DEFAULT_LIMIT}.",
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=DEFAULT_SCAN_LIMIT,
        help=f"Kolik poslednich hlavicek prohledat. Vychozi: {DEFAULT_SCAN_LIMIT}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        provider = ICloudReadOnlyEmailProvider()
        headers = provider.search_headers(
            query=args.query,
            limit=args.limit,
            scan_limit=args.scan_limit,
        )
    except EmailConfigError:
        print("Chyba: chybi lokalni konfigurace pro iCloud Mail.", file=sys.stderr)
        print("Dalsi krok: zkontroluj lokalni .env.", file=sys.stderr)
        return 1
    except EmailProviderError:
        print("Chyba: read-only vyhledani v iCloud Mail hlavickach selhalo.", file=sys.stderr)
        print(
            "Dalsi krok: over pripojeni, app-specific password a IMAP pristup.",
            file=sys.stderr,
        )
        return 1

    if not headers:
        print("Nenalezeny zadne odpovidajici e-mailove hlavicky.")
        return 0

    for index, header in enumerate(headers, start=1):
        print(f"{index}. UID: {header.internal_id}")
        print(f"   Datum: {header.date}")
        print(f"   Od: {header.sender}")
        print(f"   Predmet: {header.subject or '(bez predmetu)'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
