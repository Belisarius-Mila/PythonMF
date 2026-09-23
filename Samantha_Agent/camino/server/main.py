"""Run the C05a owner API on loopback; private HTTPS terminates upstream."""

from __future__ import annotations

import argparse
import ipaddress
import math
import os
from pathlib import Path

import uvicorn

from camino.api.v1 import CaminoV1Contract
from camino.domain.revision_store import RevisionStore
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore


def _required_path(parser: argparse.ArgumentParser, name: str) -> Path:
    value = os.environ.get(name, "")
    if not value:
        parser.error(f"{name} is required")
    return Path(value)


def _nonnegative_number(parser: argparse.ArgumentParser, name: str, default: str) -> float:
    raw = os.environ.get(name, default)
    try:
        value = float(raw)
    except ValueError:
        parser.error(f"{name} must be a nonnegative number")
    if not math.isfinite(value) or value < 0:
        parser.error(f"{name} must be a nonnegative number")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8766, type=int)
    args = parser.parse_args(argv)
    try:
        if not ipaddress.ip_address(args.host).is_loopback:
            raise ValueError
    except ValueError:
        parser.error("C05a must bind to a loopback IP; use Tailscale Serve for private HTTPS")
    metadata = RevisionStore(_required_path(parser, "CAMINO_C05A_METADATA_DB"))
    tokens = RevocableTokenStore(_required_path(parser, "CAMINO_C05A_AUTH_DB"))
    if tokens.active_count() < 1:
        parser.error("at least one active owner token must be provisioned offline")
    media = MediaStore(
        _required_path(parser, "CAMINO_C05A_MEDIA_DB"),
        _required_path(parser, "CAMINO_C05A_MEDIA_ROOT"),
        asset_lookup=metadata.asset,
        reserve_bytes=int(_nonnegative_number(
            parser, "CAMINO_C05A_RESERVE_BYTES", str(512 * 1024 * 1024)
        )),
    )
    contract = CaminoV1Contract(metadata, authenticate=tokens.authenticate)
    uvicorn.run(
        create_app(
            metadata_api=contract,
            media_store=media,
            token_store=tokens,
            finalize_delay_seconds=_nonnegative_number(
                parser, "CAMINO_C05A_FINALIZE_DELAY_SECONDS", "0"
            ),
        ),
        host=args.host,
        port=args.port,
        access_log=False,
        server_header=False,
        date_header=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
