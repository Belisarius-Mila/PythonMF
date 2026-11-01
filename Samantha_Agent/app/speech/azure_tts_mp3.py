"""One Azure Neural MP3 request, with exact text and redacted failures."""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import dotenv_values

from app.communication.trusted_external_generation import trusted_external_generation_text_allowed

ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
MAX_AUDIO_BYTES = 8 * 1024 * 1024
VOICES = frozenset({'en-US-AndrewNeural', 'en-US-AnaNeural', 'en-US-JennyNeural',
                    'en-US-MichelleNeural', 'en-US-GuyNeural',
                    'en-US-ChristopherNeural', 'cs-CZ-VlastaNeural'})


class AzureTtsError(RuntimeError):
    pass


def ssml_parts(text: str, voice: str, rate: str = '-10%') -> tuple[str, int]:
    """Count the exact billable body; speak and voice wrappers are exempt."""
    if (voice not in VOICES or rate != '-10%' or not isinstance(text, str)
            or not trusted_external_generation_text_allowed(text)
            or len(text) > 1500
            or any(ord(c) < 32 and c not in '\t\r\n' for c in text)):
        raise AzureTtsError('Nepovolený text, hlas nebo tempo Azure Speech.')
    inner = '<prosody rate="-10%">' + escape(text) + '</prosody>'
    language = '-'.join(voice.split('-')[:2])
    ssml = ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xml:lang="' + language + '"><voice name="' + voice + '">'
            + inner + '</voice></speak>')
    return ssml, len(inner)


@dataclass
class CharacterBudget:
    limit: int = 10_000
    reserved: int = 0

    def __post_init__(self):
        if not 0 < self.limit <= 10_000:
            raise AzureTtsError('Limit musí být 1 až 10 000 znaků na běh.')

    def reserve(self, count: int):
        if count <= 0 or self.reserved + count > self.limit:
            raise AzureTtsError('Limit účtovaných znaků vyčerpán; požadavek neodeslán.')
        # Reserve before transport: a lost response must never refund usage.
        self.reserved += count


def synthesize_azure_tts_mp3_sync(text: str, *, voice: str, rate: str = '-10%',
                                  budget: CharacterBudget, env_path: Path = ENV_PATH,
                                  runner=None) -> bytes:
    ssml, count = ssml_parts(text, voice, rate)
    settings = {**dotenv_values(env_path), **os.environ}
    key = settings.get('AZURE_SPEECH_KEY') or ''
    region = settings.get('AZURE_SPEECH_REGION') or ''
    if not re.fullmatch(r'[A-Za-z0-9_+/=.-]{20,512}', key):
        raise AzureTtsError('Chybí platný místní AZURE_SPEECH_KEY.')
    if not re.fullmatch(r'[a-z0-9]{3,40}', region):
        raise AzureTtsError('Chybí platný místní AZURE_SPEECH_REGION.')
    config = '\n'.join(name + ' = ' + json.dumps(value, ensure_ascii=False) for name, value in (
        ('header', 'Ocp-Apim-Subscription-Key: ' + key),
        ('header', 'Content-Type: application/ssml+xml; charset=utf-8'),
        ('header', 'X-Microsoft-OutputFormat: audio-24khz-48kbitrate-mono-mp3'),
        ('header', 'User-Agent: Samantha-MMTX'),
        ('data-binary', ssml),
    )) + '\n'
    argv = ['/usr/bin/curl', '--silent', '--show-error', '--max-time', '45',
            '--max-filesize', str(MAX_AUDIO_BYTES), '--proto', '=https',
            '--request', 'POST', '--config', '-', '--write-out', '\n%{http_code}',
            f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1']
    budget.reserve(count)
    try:
        result = (runner or subprocess.run)(argv, input=config.encode('utf-8'),
                                            capture_output=True, timeout=50, check=False)
    except Exception:
        raise AzureTtsError('Spojení Azure selhalo; bez opakování, spotřeba rezervována.') from None
    if result.returncode:
        raise AzureTtsError('Přenos Azure selhal; bez opakování, spotřeba rezervována.')
    audio, separator, status = result.stdout.rpartition(b'\n')
    if not separator or status != b'200':
        code = status.decode('ascii', errors='ignore')
        code = code if re.fullmatch(r'\d{3}', code) else 'nezjištěno'
        raise AzureTtsError(f'Azure HTTP {code}; zastaveno bez opakování.')
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise AzureTtsError('Azure vrátil prázdný nebo příliš velký zvuk.')
    return audio
