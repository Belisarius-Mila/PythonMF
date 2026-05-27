#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.email.config import EmailConfigError
from app.email.seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only vyhledani v Seznam Mail INBOX hlavickach."
    )
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--scan-limit", type=int, default=500)
    parser.add_argument("--year", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    safe_limit = min(max(1, args.limit), 100)
    safe_scan_limit = min(max(safe_limit, args.scan_limit), 1000)
    try:
        provider = SeznamReadOnlyEmailProvider()
        headers = provider.search_headers(
            query=args.query,
            limit=safe_scan_limit,
            scan_limit=safe_scan_limit,
        )
    except EmailConfigError:
        print("Chyba: chybi lokalni konfigurace pro Seznam Mail.", file=sys.stderr)
        return 1
    except SeznamEmailProviderError as exc:
        print(f"Chyba: read-only Seznam hledani selhalo: {exc}", file=sys.stderr)
        return 1

    if args.year:
        headers = [header for header in headers if args.year in header.date]
    headers = headers[:safe_limit]
    if not headers:
        print("Nenalezeny zadne odpovidajici Seznam e-mailove hlavicky.")
        return 0

    for index, header in enumerate(headers, start=1):
        print(f"{index}. UID: {header.internal_id}")
        print(f"   Datum: {header.date}")
        print(f"   Od: {header.sender}")
        print(f"   Predmet: {header.subject or '(bez predmetu)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
