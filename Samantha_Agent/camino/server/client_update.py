"""An explicitly staged, hash-checked IPA; caller must authenticate first."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from fastapi.responses import FileResponse, Response


def client_update_response(root: Path | None, headers: dict[str, str]):
    try:
        if root is None or not root.is_absolute() or root.resolve() != root:
            return Response(status_code=404, headers=headers)
        if not root.is_dir() or root.stat().st_mode & 0o077:
            return Response(status_code=404, headers=headers)
        manifest = root / "update.json"
        if manifest.is_symlink() or manifest.stat().st_mode & 0o077 or manifest.stat().st_size > 4096:
            return Response(status_code=404, headers=headers)
        proof = json.loads(manifest.read_text())
        name = proof.get("filename", "")
        if not isinstance(name, str) or not re.fullmatch(r"Camino-[A-Za-z0-9-]+\.ipa", name):
            return Response(status_code=404, headers=headers)
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
            return Response(status_code=404, headers=headers)
        size = path.stat().st_size
        if not 0 < size <= 32 * 1024 * 1024 or size != proof.get("bytes"):
            return Response(status_code=404, headers=headers)
        if proof.get("bundle_id") != "cz.pythonmf.camino.app":
            return Response(status_code=404, headers=headers)
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != proof.get("sha256"):
                return Response(status_code=404, headers=headers)
        return FileResponse(path, media_type="application/octet-stream", filename=name, headers=headers)
    except (OSError, ValueError, TypeError, AttributeError):
        return Response(status_code=404, headers=headers)
