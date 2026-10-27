"""Private, immutable local narration derivatives bound to a photo and saved text."""
from __future__ import annotations

import fcntl
from datetime import datetime, timezone
import hashlib
import os
import shutil
import stat
import subprocess

from camino.film.closed_day import _private_directory, _store_lock
from camino.film.media import duration_ms, probe
from camino.film.project import FilmError, digest, fingerprint, write_json
from app.file_persistence import atomic_write_json
from camino.domain.project_lifecycle import shared


def _database(editor):
    return getattr(editor.store, 'metadata_db', None) or editor.store.metadata.path

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


def narration_paths(editor, manifest, draft, *, project_id, allow_deleted=True):
    result = {}
    for row in draft["shots"]:
        layer = row.get("photo_text", {})
        ref = layer.get("narration")
        if ref:
            receipt, path, _ = verify_record(editor, manifest, row["asset_id"], layer, ref["id"], project_id=project_id)
            if not allow_deleted and is_trashed(editor.store, path.parent):
                raise FilmError("Tento pokus je v koši. Před použitím jej obnov.")
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


@shared(_database)
def prepare_narration(editor, payload):
    from app.camino_film_editor import exact, identifier
    cloud = "cloud_consent" in payload
    exact(payload, "project_id revision asset_id request_id" + (" cloud_consent" if cloud else ""))
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
    if cloud:
        from app.camino_film_orus import consent_cost, synthesize_orus, VOICE, TEMPO
        cost = consent_cost(layer["text"], payload["cloud_consent"])

    def revalidate():
        _, current = editor.inputs(folder.name)
        latest = editor.revision(folder, current)
        current_row = next((r for r in latest["draft"]["shots"] if r["asset_id"] == sid), None)
        if fingerprint(current) != fingerprint(manifest) or not current_row or current_row.get("photo_text") != layer:
            raise FilmError("Text nebo povolení se během čtení změnilo. Nový komentář se nepřipojil.")
        editor.verify_texts(current, latest["draft"], project_id=folder.name)

    root = _private_directory(folder / "narrations")
    lock = os.open(root / ".generation", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise FilmError("Jiné místní čtení se právě vytváří. Počkej na jeho dokončení.") from error
        directory = root / nid
        if directory.exists():
            if is_trashed(editor.store, directory):
                raise FilmError("Pokus je v koši; nejprve jej obnov.")
            if not (directory / "receipt.json").exists():
                raise FilmError("Předchozí pokus není potvrzený. Obnov seznam pokusů; čtení se samo neopakuje.")
            receipt, _, _ = verify_record(editor, manifest, sid, layer, nid, project_id=folder.name)
            request = editor.store._read(directory / "request.json")
            if request != payload:
                raise FilmError("Stejný požadavek byl použitý pro jiné čtení.")
        else:
            if len(list(root.glob("*/request.json"))) >= 256:
                raise FilmError("Projekt má již 256 hlasových verzí; další čtení vyžaduje správu úložiště.")
            directory = _private_directory(directory)
            write_json(directory / "request.json", payload)
            length = (synthesize_orus(layer["text"], directory, payload["cloud_consent"], revalidate)
                      if cloud else synthesize(layer["text"], directory))
            # Recheck privacy and current exact text after the relatively slow speech operation.
            revalidate()
            path = directory / "speech.m4a"
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
            receipt = {"schema": 1, "scope": "camino-photo-narration", "project_id": folder.name,
                "asset_id": sid, "manifest_sha256": fingerprint(manifest), "text_sha256": text_hash(layer),
                "text_source": layer["text_source"], "duration_ms": length, "bytes": path.stat().st_size,
                "sha256": digest(path), "voice": VOICE if cloud else "Zuzana", "synthetic": True,
                "text": layer["text"], "created_at": datetime.now(timezone.utc).isoformat(),
                "label": "Orus · tempo −10 %" if cloud else "Místní čtení Zuzana"}
            if cloud:
                receipt.update(provider="google-cloud-tts", tempo=TEMPO, max_cost_microusd=cost)
            write_json(directory / "receipt.json", receipt)
            checked_audio(directory, receipt)
        return {"ok": True, "narration": {"id": nid, "duration_ms": receipt["duration_ms"],
            "sha256": receipt["sha256"], "included": False},
            "url": f"/api/camino/film/narration/{folder.name}/{nid}",
            "narrations": list_narrations(editor, folder, manifest)}
    finally:
        os.close(lock)


def is_trashed(store, directory):
    path = directory / "trash.json"
    return path.exists() and store._read(path).get("deleted") is True


def attempt_record(editor, folder, manifest, nid):
    """A previous take keeps its own script; current photo edits never rewrite it."""
    from app.camino_film_editor import identifier
    directory = folder / "narrations" / identifier(nid)
    if folder.is_symlink() or directory.parent.is_symlink() or directory.is_symlink():
        raise FilmError("Pokus nemá bezpečné umístění.")
    receipt = editor.store._read(directory / "receipt.json")
    sid = receipt.get("asset_id")
    if (receipt.get("project_id") != folder.name or receipt.get("scope") != "camino-photo-narration"
            or receipt.get("manifest_sha256") != fingerprint(manifest)
            or not any(s["asset_id"] == sid and s["media_kind"] == "photo" for s in manifest["sources"])):
        raise FilmError("Pokus nepatří k povolené fotografii tohoto filmu.")
    if "text" in receipt:
        text = receipt["text"]
    else:
        # Legacy takes already have an immutable source edit; recover without rewriting it.
        request = editor.store._read(directory / "request.json")
        edit = editor.revision(folder, manifest, request["revision"])
        row = next((r for r in edit["draft"]["shots"] if r["asset_id"] == sid), None)
        if not row or "photo_text" not in row:
            raise FilmError("Chybí uložený text tohoto pokusu.")
        text = row["photo_text"]["text"]
    if not isinstance(text, str) or len(text) > 6000 or text_hash({"text": text}) != receipt.get("text_sha256"):
        raise FilmError("Uložený text pokusu byl změněný.")
    original = ""
    if receipt.get("text_source") is not None:
        original = editor.store.text_choices(manifest, [receipt["text_source"]])[0]["text"]
    return {**receipt, "text": text, "original_text": original}, directory


def list_narrations(editor, folder, manifest):
    root = folder / "narrations"
    if not root.exists():
        return []
    if root.is_symlink():
        raise FilmError("Pokusy nemají bezpečný projekt.")
    result = []
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        if directory.is_symlink():
            raise FilmError("Pokus nemá bezpečné umístění.")
        if not (directory / "receipt.json").exists():
            continue  # Interrupted or currently generating attempts are never offered as playable.
        receipt, directory = attempt_record(editor, folder, manifest, directory.name)
        result.append({"id": directory.name, "asset_id": receipt["asset_id"],
            "duration_ms": receipt["duration_ms"], "sha256": receipt["sha256"],
            "text": receipt["text"], "original_text": receipt["original_text"], "text_source": receipt["text_source"],
            "synthetic": receipt.get("synthetic", True), "label": receipt.get("label", "Místní čtení Zuzana"),
            "created_at": receipt.get("created_at"), "deleted": is_trashed(editor.store, directory),
            "url": f"/api/camino/film/narration/{folder.name}/{directory.name}"})
    return sorted(result, key=lambda r: (r["created_at"] or "", r["id"]))


@shared(_database)
def trash_narration(editor, payload):
    from app.camino_film_editor import exact, identifier, integer
    exact(payload, "project_id asset_id narration_id revision deleted")
    integer(payload["revision"], 1, 999999)
    if type(payload["deleted"]) is not bool:
        raise FilmError("Vyber smazání do koše nebo obnovení pokusu.")
    folder, manifest = editor.inputs(identifier(payload["project_id"]))
    sid = identifier(payload["asset_id"])
    receipt, directory = attempt_record(editor, folder, manifest, payload["narration_id"])
    if receipt["asset_id"] != sid:
        raise FilmError("Pokus patří jiné fotografii.")
    # All changes are reversible metadata. Media, previous edits and exported films stay intact.
    with _store_lock(editor.store.root):
        _, current = editor.inputs(folder.name)
        latest = editor.revision(folder, current)
        if payload["revision"] != latest["revision"]:
            raise FilmError("Jiné okno změnilo střih. Obnov přehled pokusů.")
        if payload["deleted"] and any((r.get("photo_text", {}).get("narration") or {}).get("id") == directory.name for r in latest["draft"]["shots"]):
            raise FilmError("Nejprve odpoj pokus od fotografie a ulož střih.")
        attempt_record(editor, folder, current, directory.name)
        atomic_write_json(directory / "trash.json", {"schema": 1, "deleted": payload["deleted"]})
    return {"ok": True, "deleted": payload["deleted"], "narrations": list_narrations(editor, folder, current)}


def narration_bytes(editor, project_id, nid):
    from app.camino_film_editor import identifier
    folder, manifest = editor.inputs(identifier(project_id))
    receipt, directory = attempt_record(editor, folder, manifest, nid)
    if is_trashed(editor.store, directory):
        raise FilmError("Tento pokus je v koši.")
    data = checked_audio(directory, receipt)[1]
    # Recheck permission after reading so a changed privacy revision cannot release the take.
    _, current = editor.inputs(folder.name)
    attempt_record(editor, folder, current, nid)
    if is_trashed(editor.store, directory):
        raise FilmError("Tento pokus je v koši.")
    return data


MAX_IMPORT_BYTES = 64 * 1024**2


@shared(_database)
def import_narration(editor, payload, body):
    """Import one bounded MP3/WAV as a film derivative, never as an archive Asset."""
    from app.camino_film_editor import exact, identifier
    from app.camino_film_render import ffmpeg
    exact(payload, "project_id revision asset_id request_id")
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_IMPORT_BYTES:
        raise FilmError("Nahrávka musí mít 1 až 64 MiB.")
    if body[:4] == b"RIFF" and body[8:12] == b"WAVE":
        kind = "wav"
    elif body[:3] == b"ID3" or len(body) >= 2 and body[0] == 255 and body[1] & 224 == 224:
        kind = "mp3"
    else:
        raise FilmError("Vyber skutečný soubor MP3 nebo WAV.")
    folder, manifest = editor.inputs(identifier(payload["project_id"]))
    nid, sid = identifier(payload["request_id"]), identifier(payload["asset_id"])
    edit = editor.revision(folder, manifest, payload["revision"])
    if edit["revision"] != editor.revision(folder, manifest)["revision"]:
        raise FilmError("Nejprve načti a ulož poslední střih.")
    row = next((r for r in edit["draft"]["shots"] if r["asset_id"] == sid), None)
    if not row or not any(s["asset_id"] == sid and s["media_kind"] == "photo" for s in manifest["sources"]) or "photo_text" not in row:
        raise FilmError("Nejprve ulož textový panel vybrané fotografie.")
    layer = row["photo_text"]
    editor.verify_texts(manifest, edit["draft"], project_id=folder.name)
    root = _private_directory(folder / "narrations")
    lock = os.open(root / ".generation", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    spec = {**payload, "content_sha256": hashlib.sha256(body).hexdigest()}
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise FilmError("Jiná nahrávka se právě připravuje. Počkej na její dokončení.") from error
        directory = root / nid
        if directory.exists():
            if editor.store._read(directory / "request.json") != spec or is_trashed(editor.store, directory):
                raise FilmError("Požadavek už patří jinému nebo smazanému pokusu.")
            receipt, _, _ = verify_record(editor, manifest, sid, layer, nid, project_id=folder.name)
        else:
            if len(list(root.glob("*/request.json"))) >= 256:
                raise FilmError("Projekt již má 256 uložených pokusů. Je nutná správa archivu.")
            directory = _private_directory(directory)
            write_json(directory / "request.json", spec)
            source = directory / "source.bin"
            fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(body); handle.flush(); os.fsync(handle.fileno())
            # Force a single-file decoder. Never autodetect uploaded playlists or external references.
            path = directory / "speech.m4a"
            ffmpeg(["-protocol_whitelist", "file,pipe", "-f", kind, "-i", str(source), "-map", "0:a:0", "-vn",
                "-map_metadata", "-1", "-map_chapters", "-1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                "-movflags", "+faststart", str(path)], executable=media_binary("ffmpeg"))
            info = probe(path, executable=media_binary("ffprobe")); length = duration_ms(info, "audio")
            if len(info["streams"]) != 1 or not 1 <= length <= 300000:
                raise FilmError("Importovaná nahrávka musí být zvuk o délce nejvýše 300 sekund.")
            ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(path), "-f", "null", "-"], executable=media_binary("ffmpeg"))
            _, current = editor.inputs(folder.name); latest = editor.revision(folder, current)
            live_row = next((r for r in latest["draft"]["shots"] if r["asset_id"] == sid), None)
            if fingerprint(current) != fingerprint(manifest) or not live_row or live_row.get("photo_text") != layer:
                raise FilmError("Text nebo povolení se během importu změnilo. Nahrávka se nepřipojila.")
            editor.verify_texts(current, latest["draft"], project_id=folder.name)
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
            receipt = {"schema": 1, "scope": "camino-photo-narration", "project_id": folder.name,
                "asset_id": sid, "manifest_sha256": fingerprint(manifest), "text_sha256": text_hash(layer),
                "text_source": layer["text_source"], "text": layer["text"], "duration_ms": length,
                "bytes": path.stat().st_size, "sha256": digest(path), "synthetic": None,
                "label": "Importovaná nahrávka " + kind.upper(), "created_at": datetime.now(timezone.utc).isoformat()}
            write_json(directory / "receipt.json", receipt); checked_audio(directory, receipt)
        return {"ok": True, "narration": {"id": nid, "duration_ms": receipt["duration_ms"],
            "sha256": receipt["sha256"], "included": False}, "narrations": list_narrations(editor, folder, manifest)}
    finally:
        os.close(lock)
