"""Private, immutable local narration derivatives bound to a photo and saved text."""
from __future__ import annotations

import fcntl
import hashlib
import os
import shutil
import stat
import subprocess

from camino.film.closed_day import _private_directory
from camino.film.media import duration_ms, probe
from camino.film.project import FilmError, digest, fingerprint, write_json

MAX_AUDIO_BYTES = 32 * 1024**2


def media_binary(name):
    path = os.pathsep.join((os.environ.get("PATH") or os.defpath, "/opt/homebrew/bin", "/usr/local/bin"))
    executable = shutil.which(name, path=path)
    if not executable:
        raise FilmError("Chybí místní mediální nástroje pro čtení fotografie.")
    return executable


def text_hash(layer):
    return hashlib.sha256(layer["text"].encode("utf-8")).hexdigest()


def checked_audio(folder, receipt):
    path = folder / "speech.m4a"
    if folder.is_symlink() or path.is_symlink():
        raise FilmError("Komentář nemá bezpečné umístění.")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_AUDIO_BYTES:
            raise FilmError("Komentář nemá platný mediální soubor.")
        data = handle.read(MAX_AUDIO_BYTES + 1)
    if len(data) != receipt["bytes"] or hashlib.sha256(data).hexdigest() != receipt["sha256"]:
        raise FilmError("Uložený komentář byl poškozený.")
    return path, data


def verify_record(editor, manifest, sid, layer, nid, *, project_id):
    from app.camino_film_editor import identifier
    root = editor.store.root / identifier(project_id)
    directory = root / "narrations" / identifier(nid)
    if root.is_symlink() or directory.parent.is_symlink() or directory.is_symlink():
        raise FilmError("Komentář nemá bezpečný projekt.")
    receipt = editor.store._read(directory / "receipt.json")
    if (receipt.get("scope") != "camino-photo-narration" or receipt.get("project_id") != root.name
            or receipt.get("asset_id") != sid or receipt.get("manifest_sha256") != fingerprint(manifest)
            or receipt.get("text_sha256") != text_hash(layer)
            or receipt.get("text_source") != layer["text_source"]):
        raise FilmError("Komentář patří jiné fotografii nebo jiné verzi textu. Vytvoř čtení znovu.")
    path, data = checked_audio(directory, receipt)
    return receipt, path, data


def narration_paths(editor, manifest, draft, *, project_id):
    result = {}
    for row in draft["shots"]:
        layer = row.get("photo_text", {})
        ref = layer.get("narration")
        if ref:
            receipt, path, _ = verify_record(editor, manifest, row["asset_id"], layer, ref["id"], project_id=project_id)
            if receipt["sha256"] != ref["sha256"] or receipt["duration_ms"] != ref["duration_ms"]:
                raise FilmError("Vazba hlasového komentáře byla změněná.")
            result[ref["id"]] = path
    return result


def synthesize(text, directory):
    """Read every selected character through stdin; never use the truncating chat TTS helper."""
    from app.camino_film_render import ffmpeg
    raw = directory / "speech.aiff"
    try:
        result = subprocess.run(["/usr/bin/say", "-v", "Zuzana", "-o", str(raw), "-f", "-"],
            input=text.encode("utf-8"), capture_output=True, timeout=240, check=False, umask=0o077)
        if result.returncode:
            raise FilmError("Místní český hlas Zuzana není dostupný. Text i fotografie zůstaly uložené.")
        ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(raw), "-map", "0:a:0", "-vn",
                "-map_metadata", "-1", "-map_chapters", "-1", "-c:a", "aac", "-b:a", "128k",
                "-ar", "48000", "-movflags", "+faststart", str(directory / "speech.m4a")], executable=media_binary("ffmpeg"))
        path = directory / "speech.m4a"
        info = probe(path, executable=media_binary("ffprobe"))
        length = duration_ms(info, "audio")
        if (len(info["streams"]) != 1 or not 1 <= length <= 3_600_000
                or not 0 < path.stat().st_size <= MAX_AUDIO_BYTES):
            raise FilmError("Místní čtení nemá platný zvuk nebo délku.")
        ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(path), "-f", "null", "-"], executable=media_binary("ffmpeg"))
        return length
    except (OSError, subprocess.TimeoutExpired) as error:
        raise FilmError("Místní čtení se nedokončilo. Uložený text zůstává zachovaný.") from error


def prepare_narration(editor, payload):
    from app.camino_film_editor import exact, identifier
    exact(payload, "project_id revision asset_id request_id")
    folder, manifest = editor.inputs(identifier(payload["project_id"]))
    sid, nid = identifier(payload["asset_id"]), identifier(payload["request_id"])
    edit = editor.revision(folder, manifest, payload["revision"])
    if edit["revision"] != editor.revision(folder, manifest)["revision"]:
        raise FilmError("Načti poslední střih před vytvořením čtení.")
    row = next((r for r in edit["draft"]["shots"] if r["asset_id"] == sid), None)
    layer = row.get("photo_text") if row else None
    if not layer or not layer["text"].strip():
        raise FilmError("Nejprve ulož text u vybrané fotografie.")
    editor.verify_texts(manifest, edit["draft"], project_id=folder.name)
    root = _private_directory(folder / "narrations")
    lock = os.open(root / ".generation", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise FilmError("Jiné místní čtení se právě vytváří. Počkej na jeho dokončení.") from error
        directory = root / nid
        if directory.exists():
            receipt, _, _ = verify_record(editor, manifest, sid, layer, nid, project_id=folder.name)
            request = editor.store._read(directory / "request.json")
            if request != payload:
                raise FilmError("Stejný požadavek byl použitý pro jiné čtení.")
        else:
            if len(list(root.glob("*/request.json"))) >= 64:
                raise FilmError("Projekt má již 64 hlasových verzí; další čtení vyžaduje správu úložiště.")
            directory = _private_directory(directory)
            write_json(directory / "request.json", payload)
            length = synthesize(layer["text"], directory)
            # Recheck privacy and current exact text after the relatively slow speech operation.
            _, current = editor.inputs(folder.name)
            latest = editor.revision(folder, current)
            current_row = next((r for r in latest["draft"]["shots"] if r["asset_id"] == sid), None)
            if fingerprint(current) != fingerprint(manifest) or not current_row or current_row.get("photo_text") != layer:
                raise FilmError("Text nebo povolení se během čtení změnilo. Nový komentář se nepřipojil.")
            editor.verify_texts(current, latest["draft"], project_id=folder.name)
            path = directory / "speech.m4a"
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
            receipt = {"schema": 1, "scope": "camino-photo-narration", "project_id": folder.name,
                "asset_id": sid, "manifest_sha256": fingerprint(manifest), "text_sha256": text_hash(layer),
                "text_source": layer["text_source"], "duration_ms": length, "bytes": path.stat().st_size,
                "sha256": digest(path), "voice": "Zuzana", "synthetic": True}
            write_json(directory / "receipt.json", receipt)
            checked_audio(directory, receipt)
        return {"ok": True, "narration": {"id": nid, "duration_ms": receipt["duration_ms"],
            "sha256": receipt["sha256"], "included": False},
            "url": f"/api/camino/film/narration/{folder.name}/{nid}"}
    finally:
        os.close(lock)


def narration_bytes(editor, project_id, nid):
    from app.camino_film_editor import identifier
    folder, manifest = editor.inputs(identifier(project_id))
    edit = editor.revision(folder, manifest)
    editor.verify_texts(manifest, edit["draft"], project_id=folder.name)
    # Only a saved attachment may be served, and it must still match current text/privacy.
    for row in edit["draft"]["shots"]:
        layer = row.get("photo_text", {})
        if (layer.get("narration") or {}).get("id") == nid:
            return verify_record(editor, manifest, row["asset_id"], layer, nid, project_id=folder.name)[2]
    raise FilmError("Komentář není připojený k aktuální fotografii.")
