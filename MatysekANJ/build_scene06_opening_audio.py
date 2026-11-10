#!/usr/bin/env python3
"""Build one picture's fixed English MP3 in the NEW Scene 6, without retries."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "Samantha_Agent"
sys.path.insert(0, str(ROOT))

from app.file_persistence import atomic_write_json
from app.speech.azure_tts_mp3 import (
    CharacterBudget, ENV_PATH, ssml_parts, synthesize_azure_tts_mp3_sync,
)

DOCS = REPO / "docs/scene06_lake_arrival"
MIRROR = REPO / "MatysekANJ/web_mmtx/scene06_lake_arrival"
RECEIPT = ROOT / "data/private/mmtx/scene06_opening_20261110/audio_receipt.json"
CAPABILITY_ID = "generate_project_azure_audio_asset"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError("Existující audio se liší; nic se nepřepisuje.")
        return
    with path.open("xb") as output:
        output.write(data)


def names(picture):
    if picture not in (1, 2, 3):
        raise RuntimeError("Nepovolený obraz nové šestky.")
    return ("dialogue.json", "audio_manifest.json") if picture == 1 else (f"dialogue_{picture:02d}.json", f"audio_manifest_{picture:02d}.json")


def dialogue(root=DOCS, picture=1):
    data = json.loads((root / names(picture)[0]).read_text(encoding="utf-8"))
    if (data.get("schema_version") != 1 or data.get("picture") != picture
            or len(data.get("lines", [])) != {1: 7, 2: 10, 3: 8}[picture]):
        raise RuntimeError("Neplatný dialog nové šestky.")
    for number, line in enumerate(data["lines"], 1):
        prefix = "" if picture == 1 else f"p{picture:02d}_"
        expected = f"audio/en/{prefix}{number:02d}_{line['speaker'].lower()}.mp3"
        if line.get("audio") != expected:
            raise RuntimeError("Neplatná cesta audia.")
        ssml_parts(line["text"], line["voice"], data["rate"])
    return data


def validate_mp3(data):
    if len(data) < 1000 or not (data.startswith(b"ID3") or data[0] == 255):
        raise RuntimeError("Výsledek není platné MP3.")
    # Explicit known locations also work under the launchd service PATH.
    decoder = next((str(p) for p in (Path("/usr/local/bin/ffmpeg"), Path("/opt/homebrew/bin/ffmpeg")) if p.is_file()), None)
    if not decoder:
        import shutil
        decoder = shutil.which("ffmpeg")
    if not decoder:
        raise RuntimeError("Chybí FFmpeg; generování se nespouští.")
    result = subprocess.run([decoder, "-v", "error", "-i", "pipe:0", "-f", "null", "-"],
                            input=data, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError("MP3 neprošlo dekódováním.")


@contextmanager
def receipt_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def build(*, env_path=ENV_PATH, receipt=None, limit=1000, docs=DOCS, picture=1,
          mirror=MIRROR, synthesizer=synthesize_azure_tts_mp3_sync, validator=validate_mp3):
    data = dialogue(docs, picture)
    receipt = receipt or (RECEIPT if picture == 1 else RECEIPT.with_name(f"audio_receipt_picture_{picture:02d}.json"))
    signature = digest(json.dumps(data, ensure_ascii=False, sort_keys=True).encode())
    with receipt_lock(receipt):
        state = json.loads(receipt.read_text()) if receipt.exists() else {
            "schema_version": 1, "input_sha256": signature, "provider": "azure", "assets": {},
        }
        if state.get("input_sha256") != signature or state.get("provider") != "azure":
            raise RuntimeError("Vstup neodpovídá původní účtence.")
        if any(item.get("state") != "complete" for item in state["assets"].values()):
            raise RuntimeError("Nejistý dřívější požadavek; žádné automatické opakování.")
        pending = [line for line in data["lines"] if line["audio"] not in state["assets"]]
        count = sum(ssml_parts(line["text"], line["voice"], data["rate"])[1] for line in pending)
        if not 0 < limit <= 10_000 or count > limit:
            raise RuntimeError("Celý plán překračuje znakový rozpočet; žádný požadavek odeslán.")
        # Preflight decoder before the first paid operation, independent of actual media.
        if validator is validate_mp3:
            import shutil
            if not any(p.is_file() for p in (Path("/usr/local/bin/ffmpeg"), Path("/opt/homebrew/bin/ffmpeg"))) and not shutil.which("ffmpeg"):
                raise RuntimeError("Chybí FFmpeg; žádný požadavek odeslán.")
        for line in pending:
            if (docs / line["audio"]).exists() or (mirror / line["audio"]).exists():
                raise RuntimeError("Audio bez odpovídající účtenky; nepřepisuje se ani negeneruje.")
        budget = CharacterBudget(limit=limit)
        assets = []
        for line in data["lines"]:
            path = docs / line["audio"]
            previous = state["assets"].get(line["audio"])
            if previous:
                audio = path.read_bytes()
                if digest(audio) != previous["sha256"]:
                    raise RuntimeError("Změněný hotový soubor; běh zastaven.")
            else:
                # Durable claim BEFORE transport: even invalid/lost responses cannot be retried.
                state["assets"][line["audio"]] = {
                    "state": "attempted", "text": line["text"], "voice": line["voice"],
                    "reserved_characters": ssml_parts(line["text"], line["voice"], data["rate"])[1],
                }
                atomic_write_json(receipt, state)
                audio = synthesizer(line["text"], voice=line["voice"], rate=data["rate"],
                                    budget=budget, env_path=env_path)
                validator(audio)
                write_new(path, audio)
                state["assets"][line["audio"]].update(state="complete", sha256=digest(audio), bytes=len(audio))
                atomic_write_json(receipt, state)
            write_new(mirror / line["audio"], audio)
            assets.append({**line, "sha256": digest(audio), "bytes": len(audio)})
        manifest = {"schema_version": 1, "provider": "azure", "rate": data["rate"], "assets": assets}
        for root in (docs, mirror):
            atomic_write_json(root / names(picture)[1], manifest)
        return {"ok": True, "picture": picture, "assets": len(assets), "new_requests": len(pending),
                "reserved_characters": budget.reserved}


def check(docs=DOCS, mirror=MIRROR, picture=1):
    data = dialogue(docs, picture)
    manifest = json.loads((docs / names(picture)[1]).read_text())
    if manifest.get("provider") != "azure" or manifest.get("rate") != data["rate"]:
        raise RuntimeError("Nesprávný provider nebo tempo.")
    if len(manifest.get("assets", [])) != len(data["lines"]):
        raise RuntimeError("Neúplný audio manifest.")
    for line, asset in zip(data["lines"], manifest["assets"]):
        if any(asset.get(key) != value for key, value in line.items()):
            raise RuntimeError("Text/hlas/cesta neodpovídá MP3 manifestu.")
        audio = (docs / line["audio"]).read_bytes()
        validate_mp3(audio)
        if digest(audio) != asset["sha256"] or len(audio) != asset["bytes"]:
            raise RuntimeError("MP3 neodpovídá ověřenému otisku.")
        if (mirror / line["audio"]).read_bytes() != audio:
            raise RuntimeError("Mirror se liší.")
    for name in names(picture):
        if (docs / name).read_bytes() != (mirror / name).read_bytes():
            raise RuntimeError("Data mirroru se liší.")
    return {"ok": True, "english_mp3": len(data["lines"]), "missing": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--provider", choices=("azure",))
    parser.add_argument("--picture", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--env-path", type=Path, default=ENV_PATH)
    parser.add_argument("--max-characters", type=int, default=1000)
    args = parser.parse_args()
    if args.apply and args.provider != "azure":
        parser.error("Generování vyžaduje výslovné --provider azure.")
    try:
        result = build(env_path=args.env_path, limit=args.max_characters, picture=args.picture) if args.apply else check(picture=args.picture)
    except Exception as error:
        # Registered transport exceptions are already secret-safe; never print settings.
        print(f"Zastaveno bez opakování: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
