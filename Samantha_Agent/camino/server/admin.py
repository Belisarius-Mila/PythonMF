"""Offline token administration; secrets never appear in command arguments."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from camino.server.auth import RevocableTokenStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth-db", required=True, type=Path)
    actions = parser.add_subparsers(dest="action", required=True)
    add = actions.add_parser("add-token")
    add.add_argument("--label", required=True)
    revoke = actions.add_parser("revoke-token")
    revoke.add_argument("--token-id", required=True)
    args = parser.parse_args(argv)
    store = RevocableTokenStore(args.auth_db)
    if args.action == "add-token":
        token = os.environ.get("CAMINO_C05A_TOKEN", "")
        if not token:
            parser.error("CAMINO_C05A_TOKEN is required for add-token")
        print(store.add(token, label=args.label))
        return 0
    if not store.revoke(args.token_id):
        parser.error("token ID does not exist")
    print("revoked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
