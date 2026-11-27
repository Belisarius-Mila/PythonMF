"""Optional exact-content media beside the portable dictionary; no generation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import unicodedata


def _text(value):
    return unicodedata.normalize("NFC", value.strip())


def _stamp(path):
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


class LocalMedia:
    def __init__(self, directory, *, kind, extensions):
        self.directory = Path(directory)
        self.kind = kind
        self.extensions = extensions
        self._manifest_stamp = None
        self._index = {}
        self._verified = {}

    def resolve(self, channel, text):
        """Unavailable, stale or invalid media falls back to existing speech."""
        try:
            manifest = self.directory / "manifest.json"
            stamp = _stamp(manifest)
            if manifest.is_symlink() or self.directory.is_symlink() or stamp[1] > 4_000_000:
                return None
            if stamp != self._manifest_stamp:
                # Discard the old index before parsing a new or damaged manifest.
                self._index = {}
                self._verified = {}
                self._manifest_stamp = None
                body = json.loads(manifest.read_text(encoding="utf-8"))
                if (body.get("schemaVersion") != 1
                        or body.get("kind") != self.kind
                        or not isinstance(body.get("items"), list)
                        or len(body["items"]) > 10000):
                    return None
                index = {}
                for item in body["items"]:
                    ch, content = item.get("channel"), item.get("text")
                    rel, digest = item.get("asset"), item.get("sha256")
                    if (ch not in ("fr", "cz") or not isinstance(content, str)
                            or not content.strip() or not isinstance(rel, str)
                            or not isinstance(digest, str)
                            or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                        return None
                    parts = rel.split("/")
                    if (PurePosixPath(rel).is_absolute() or "\\" in rel
                            or any(p in ("", ".", "..") for p in parts)
                            or not rel.endswith(self.extensions)):
                        return None
                    key = (ch, _text(content))
                    value = (rel, digest)
                    if key in index and index[key] != value:
                        return None
                    index[key] = value
                self._index, self._manifest_stamp = index, stamp
            record = self._index.get((channel, _text(text)))
            if record is None:
                return None
            relative, digest = record
            path = self.directory
            for part in relative.split("/"):
                path = path / part
                if path.is_symlink():
                    return None
            stamp = _stamp(path)
            if not path.is_file() or stamp[1] > 20_000_000:
                return None
            key = (relative, stamp)
            if key not in self._verified:
                if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    return None
                self._verified[key] = True
            return path
        except (OSError, ValueError, TypeError, AttributeError):
            self._index = {}
            self._manifest_stamp = None
            return None


class LocalAudio(LocalMedia):
    def __init__(self, directory):
        super().__init__(directory, kind="vocabulary-fr-local-audio", extensions=(".mp3",))

    def play(self, channel, text):
        path = self.resolve(channel, text)
        if path is None:
            return False
        try:
            result = subprocess.run(["/usr/bin/afplay", str(path)], check=False,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=120)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


class LocalPictures(LocalMedia):
    def __init__(self, directory):
        super().__init__(directory, kind="vocabulary-fr-local-pictures",
                         extensions=(".webp", ".png", ".jpg", ".jpeg"))

    def resolve(self, fr, cz):
        # A meaning pair disambiguates carte and bypasses English the for thé.
        pair = json.dumps([_text(fr), _text(cz)], ensure_ascii=False)
        return super().resolve("fr", pair)
