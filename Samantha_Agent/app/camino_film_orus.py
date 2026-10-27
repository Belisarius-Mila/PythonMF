"""Explicitly consented Google narration; exact text, bounded cost and no synthesis retries."""
from __future__ import annotations

import base64
import binascii
import importlib.util
import json
import os
from pathlib import Path
import ssl
import stat
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import certifi

from camino.film.project import FilmError

VOICE = "cs-CZ-Chirp3-HD-Orus"
TEMPO = 0.9
MICROUSD_PER_CHARACTER = 30
MAX_TEXT_BYTES = 5000
MAX_AUDIO_BYTES = 32 * 1024**2
CREDENTIAL_FILE = Path(__file__).resolve().parents[1] / "data/private/camino/credentials/google-tts-service-account.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SYNTHESIS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


def _credential_stat():
    path = CREDENTIAL_FILE
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Unsafe credential path")
    info = path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
            or info.st_uid != os.getuid() or not 0 < info.st_size <= 65536
            or path.parent.stat().st_mode & 0o077):
        raise ValueError("Unsafe credential permissions")
    return info


def _credential_bytes():
    path = CREDENTIAL_FILE
    before = _credential_stat()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
                or info.st_uid != os.getuid() or not 0 < info.st_size <= 65536
                or info.st_ino != before.st_ino or info.st_dev != before.st_dev):
            raise ValueError("Unsafe credential permissions")
        return handle.read(65537)


def voice_profile():
    """Local availability only; never requests tokens or returns credential contents."""
    ready = False
    try:
        _credential_stat()
        ready = importlib.util.find_spec("google.auth") is not None
    except (OSError, ValueError, ModuleNotFoundError):
        pass
    return {"voice": VOICE, "label": "Orus · tempo −10 %", "tempo": TEMPO,
            "microusd_per_character": MICROUSD_PER_CHARACTER, "ready": ready,
            "reason": "" if ready else "Orus není připojený. Chybí bezpečný místní přístup ke Google Cloud."}


def consent_cost(text, consent):
    if (not isinstance(text, str) or not text.strip() or len(text) > 6000
            or not isinstance(consent, dict)
            or set(consent) != {"text", "max_cost_microusd", "voice", "tempo"}
            or consent["text"] != text or consent["voice"] != VOICE
            or type(consent["tempo"]) not in (int, float) or consent["tempo"] != TEMPO
            or type(consent["max_cost_microusd"]) is not int
            or consent["max_cost_microusd"] != len(text) * MICROUSD_PER_CHARACTER):
        raise FilmError("Potvrď odeslání tohoto uloženého textu Googlu a jeho zobrazenou cenu.")
    return consent["max_cost_microusd"]


def split_text(text):
    """Keep every code point and whitespace; prefer a sentence/word boundary."""
    chunks = []
    while text:
        size, end, boundary = 0, 0, 0
        for index, char in enumerate(text):
            size += len(char.encode("utf-8"))
            if size > MAX_TEXT_BYTES:
                break
            end = index + 1
            if char.isspace():
                boundary = end
        if end == len(text):
            chunks.append(text)
            break
        if not end:
            raise FilmError("Text nelze rozdělit pro český hlas.")
        cut = boundary if boundary >= end // 2 else end
        chunks.append(text[:cut])
        text = text[cut:]
    return chunks


def access_token():
    # Let the official library handle service-account authentication. The
    # returned token stays in memory; never log library errors or key material.
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as AuthRequest
        import requests

        info = json.loads(_credential_bytes())
        if (info.get("type") != "service_account" or info.get("project_id") != "camino-orus"
                or info.get("token_uri") != TOKEN_URL
                or info.get("universe_domain", "googleapis.com") != "googleapis.com"):
            raise ValueError("Unexpected credential identity")
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        with requests.Session() as session:
            session.trust_env = False
            transport = AuthRequest(session=session)

            def refresh_request(url, method="GET", body=None, headers=None, **kwargs):
                if url != TOKEN_URL:
                    raise ValueError("Unexpected authentication endpoint")
                return transport(url=url, method=method, body=body, headers=headers, timeout=20)

            credentials.refresh(refresh_request)
        if not isinstance(credentials.token, str) or not credentials.token:
            raise ValueError("Missing token")
        return credentials.token
    except Exception:
        raise FilmError("Přihlášení hlasu Orus selhalo. Text zůstal uložený; zkontroluj Google Cloud přístup.") from None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request_audio(text, token):
    """One POST only; a timeout or HTTP error is never retried here."""
    body = {"input": {"text": text}, "voice": {"languageCode": "cs-CZ", "name": VOICE},
            "audioConfig": {"audioEncoding": "LINEAR16"}}
    try:
        opener = build_opener(_NoRedirect(), HTTPSHandler(
            context=ssl.create_default_context(cafile=certifi.where())))
        request = Request(SYNTHESIS_URL, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method="POST")
        with opener.open(request, timeout=90) as response:
            content = response.read(44 * 1024**2 + 1)
        if len(content) > 44 * 1024**2:
            raise ValueError("Oversized response")
        audio = base64.b64decode(json.loads(content)["audioContent"], validate=True)
        if not 44 < len(audio) <= MAX_AUDIO_BYTES:
            raise ValueError("Invalid audio size")
        return audio
    except HTTPError as error:
        message = ("Google Orus požadavek odmítl (HTTP " + str(error.code) + "). "
                   "Text je uložený; požadavek se automaticky neopakuje.")
        error.close()
        raise FilmError(message) from None
    except (OSError, URLError, TimeoutError, ValueError, KeyError, TypeError, binascii.Error):
        raise FilmError("Výsledek Google Orus není potvrzený. Obnov seznam pokusů; požadavek neopakuj automaticky.") from None


def synthesize_orus(text, directory, consent, revalidate):
    consent_cost(text, consent)
    token = access_token()
    # PCM chunks are staging data, not another retained copy of every take.
    with tempfile.TemporaryDirectory(prefix=".orus-", dir=directory) as temporary:
        return _synthesize_parts(text, directory, revalidate, token, Path(temporary))


def _synthesize_parts(text, directory, revalidate, token, temporary):
    from app.camino_film_narration import media_binary
    from app.camino_film_render import ffmpeg
    from camino.film.media import duration_ms, probe
    from camino.film.project import write_json

    parts = split_text(text)
    # Privacy/current text can change while authentication or a previous part
    # is in flight. Check immediately before EVERY transmission.
    paths = []
    total_bytes = 0
    for index, part in enumerate(parts):
        revalidate()
        write_json(directory / f"cloud-part-{index:02d}-request.json", {
            "index": index, "characters": len(part), "state": "may_have_been_sent",
            "voice": VOICE, "automatic_retry": False})
        audio = request_audio(part, token)
        total_bytes += len(audio)
        if total_bytes > MAX_AUDIO_BYTES:
            raise FilmError("Orus vrátil příliš velkou nahrávku. Text zůstává uložený.")
        path = temporary / f"cloud-part-{index:02d}.wav"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(audio)
        info = probe(path, executable=media_binary("ffprobe"))
        if len(info["streams"]) != 1 or info["streams"][0].get("codec_name") != "pcm_s16le":
            raise FilmError("Orus nevrátil očekávaný zvuk. Požadavek se neopakuje.")
        paths.append(path)
    revalidate()
    args = []
    for path in paths:
        args.extend(["-protocol_whitelist", "file,pipe", "-i", str(path)])
    inputs = "".join(f"[{index}:a:0]" for index in range(len(paths)))
    graph = inputs + f"concat=n={len(paths)}:v=0:a=1,atempo={TEMPO}[speech]"
    target = directory / "speech.m4a"
    ffmpeg([*args, "-filter_complex", graph, "-map", "[speech]", "-vn", "-map_metadata", "-1",
            "-map_chapters", "-1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart", str(target)], executable=media_binary("ffmpeg"))
    info = probe(target, executable=media_binary("ffprobe"))
    length = duration_ms(info, "audio")
    if (len(info["streams"]) != 1 or not 1 <= length <= 3_600_000
            or not 0 < target.stat().st_size <= MAX_AUDIO_BYTES):
        raise FilmError("Orus nemá platný výsledný zvuk nebo délku.")
    ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(target), "-f", "null", "-"],
           executable=media_binary("ffmpeg"))
    return length
