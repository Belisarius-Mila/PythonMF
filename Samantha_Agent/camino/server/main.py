"""Run the C05a owner API on loopback; private HTTPS terminates upstream."""

from __future__ import annotations

import argparse
import ipaddress
import math
import os
import shutil
from pathlib import Path

import uvicorn

from camino.api.v1 import CaminoV1Contract
from camino.domain.revision_store import RevisionStore
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore


def _viewer_options(parser, metadata, media, owner_tokens) -> dict:
    """Explicit opt-in only; no token creation and no trip/privacy mutation."""
    enabled = os.environ.get("CAMINO_VIEWER_ENABLED", "0")
    if enabled not in ("0", "1"):
        parser.error("CAMINO_VIEWER_ENABLED must be 0 or 1")
    if enabled == "0":
        return {}
    from camino.server.viewer import CaminoViewer
    from camino.server.viewer_media import ViewerMedia

    reader_path = _required_path(parser, "CAMINO_VIEWER_AUTH_DB")
    if reader_path.resolve() == owner_tokens.path or not reader_path.is_file():
        parser.error("Viewer requires an existing separate reader credential database")
    trip_id = os.environ.get("CAMINO_VIEWER_TRIP_ID", "")
    try:
        metadata._uuid(trip_id)
    except ValueError:
        parser.error("CAMINO_VIEWER_TRIP_ID must be a canonical UUID")
    interval = _nonnegative_number(parser, "CAMINO_VIEWER_INTERVAL_SECONDS", "60")
    if not 1 <= interval <= 3600:
        parser.error("Viewer interval must be between 1 and 3600 seconds")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("Viewer requires an installed ffmpeg executable")
    readers = RevocableTokenStore(reader_path)
    if readers.active_count() < 1:
        parser.error("at least one separate reader token must be provisioned offline")
    viewer = CaminoViewer(metadata, media, ViewerMedia(
        _required_path(parser, "CAMINO_VIEWER_MEDIA_ROOT"), ffmpeg=ffmpeg), readers, trip_id)
    return {"viewer": viewer, "viewer_interval_seconds": interval}


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
    parser.add_argument("--root-path", choices=("", "/camino-api"), default="")
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
            root_path=args.root_path,
            **_viewer_options(parser, metadata, media, tokens),
        ),
        host=args.host,
        port=args.port,
        access_log=False,
        server_header=False,
        date_header=False,
        workers=1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
