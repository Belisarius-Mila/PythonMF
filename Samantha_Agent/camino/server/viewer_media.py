"""Small rebuildable Viewer derivatives. No original or metadata mutations."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from camino.domain.model import ContractError


RECIPE = "m1-v1"
OUTPUTS = {
    "photo": {"preview.jpg": "image/jpeg"},
    "video": {"clip.mp4": "video/mp4", "poster.jpg": "image/jpeg"},
    "audio": {"audio.m4a": "audio/mp4"},
}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class ViewerMedia:
    def __init__(self, root: Path, *, ffmpeg: str = "ffmpeg"):
        requested = Path(root).absolute()
        if requested.is_symlink() or requested.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
            raise ContractError("Viewer copies must stay outside source repository and symlinks")
        requested.mkdir(mode=0o700, parents=True, exist_ok=True)
        if requested.stat().st_mode & 0o077:
            raise ContractError("Viewer copies require a private directory")
        self.root = requested.resolve()
        self.ffmpeg = ffmpeg

    def directory(self, asset: dict) -> Path:
        # Identity comes from validated C03 manifests, never a request path.
        key = hashlib.sha256(
            f'{RECIPE}:{asset["id"]}:{asset["sha256"]}:{asset["media_kind"]}'.encode()
        ).hexdigest()
        return self.root / key

    def ready(self, asset: dict, *, verify: bool = True) -> dict[str, Path]:
        directory = self.directory(asset)
        if directory.is_symlink():
            return {}
        manifest = directory / "ready.json"
        if not manifest.is_file() or manifest.is_symlink():
            return {}
        try:
            data = json.loads(manifest.read_text())
            expected = OUTPUTS[asset["media_kind"]]
            if set(data) != set(expected):
                return {}
            paths = {name: directory / name for name in expected}
            for name, path in paths.items():
                if path.is_symlink() or not path.is_file() or path.stat().st_size != data[name]["bytes"]:
                    return {}
                if verify and sha256(path) != data[name]["sha256"]:
                    return {}
            return paths
        except (OSError, ValueError, KeyError, TypeError):
            return {}

    def build(self, asset: dict, source: Path, *, should_stop: Callable[[], bool] = lambda: False) -> bool:
        if should_stop():
            return False
        if self.ready(asset):
            return True
        if source.is_symlink() or not source.is_file():
            return False
        if source.stat().st_size != asset["byte_count"] or sha256(source) != asset["sha256"]:
            return False
        destination = self.directory(asset)
        # Do not overwrite a broken old cache or remove any original/file.
        if destination.exists() or destination.is_symlink():
            return False
        work = Path(tempfile.mkdtemp(prefix="pending-", dir=self.root))
        kind = asset["media_kind"]
        commands = []
        if kind == "photo":
            commands.append((source, ["-map", "0:v:0", "-frames:v", "1", "-vf",
                "scale=1600:1600:force_original_aspect_ratio=decrease", "-q:v", "3"], "preview.jpg"))
        elif kind == "video":
            commands.append((source, ["-map", "0:v:0", "-map", "0:a:0?", "-vf",
                "scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart"], "clip.mp4"))
            commands.append((work / "clip.mp4", ["-map", "0:v:0", "-frames:v", "1", "-q:v", "3"], "poster.jpg"))
        elif kind == "audio":
            commands.append((source, ["-map", "0:a:0", "-vn", "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart"], "audio.m4a"))
        else:
            return False
        try:
            for input_path, options, name in commands:
                if should_stop():
                    return False
                # Local files only; reject media that tries to resolve a remote input.
                subprocess.run([
                    self.ffmpeg, "-nostdin", "-v", "error", "-n", "-threads", "2",
                    "-protocol_whitelist", "file,pipe", "-format_whitelist",
                    "mov,mp4,m4a,3gp,3g2,mj2,caf,wav,aiff,mp3,image2,jpeg_pipe,png_pipe,heif",
                    "-i", str(input_path), *options,
                    "-map_metadata", "-1", "-map_chapters", "-1", str(work / name),
                ], check=True, timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            manifest = {}
            for name in OUTPUTS[kind]:
                path = work / name
                if not path.is_file() or not path.stat().st_size:
                    return False
                path.chmod(0o600)
                manifest[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
            (work / "ready.json").write_text(json.dumps(manifest))
            (work / "ready.json").chmod(0o600)
            os.rename(work, destination)  # completed directory published atomically
            return True
        except (OSError, subprocess.SubprocessError):
            # Incomplete outputs stay private and are never served.
            return False
