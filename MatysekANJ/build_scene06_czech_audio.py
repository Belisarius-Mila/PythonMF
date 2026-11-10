#!/usr/bin/env python3
"""Build the approved Czech companion tracks without changing English assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_scene06_opening_audio as english

DOCS, MIRROR = english.DOCS, english.MIRROR
INPUT = "translations_cs.json"
MANIFEST = "audio_manifest_cs.json"
RECEIPT = english.ROOT / "data/private/mmtx/scene06_czech_20261110/audio_receipt_cs.json"


def translations(docs=DOCS):
    data = json.loads((docs / INPUT).read_text())
    if (data.get("schema_version") != 1 or data.get("language") != "cs"
            or data.get("rate") != "-10%" or not isinstance(data.get("lines"), list)):
        raise RuntimeError("Neplatná česká sada.")
    expected = []
    for picture in range(1, 11):
        for number, row in enumerate(english.dialogue(docs, picture)["lines"], 1):
            expected.append((picture, number, row))
    if len(data["lines"]) != len(expected):
        raise RuntimeError("Neúplné české překlady.")
    for item, (picture, number, row) in zip(data["lines"], expected):
        slug = row["speaker"].lower().replace(" ", "_")
        if (item.get("picture") != picture or item.get("number") != number
                or item.get("speaker") != row["speaker"] or item.get("english") != row["text"]
                or item.get("audio_en") != row["audio"] or item.get("voice") != "cs-CZ-VlastaNeural"
                or item.get("audio") != f"audio/cs/p{picture:02d}_{number:02d}_{slug}.mp3"
                or not isinstance(item.get("text"), str) or not item["text"].strip()):
            raise RuntimeError("Český překlad neodpovídá původní anglické větě.")
        english.ssml_parts(item["text"], item["voice"], data["rate"])
    return data


def build(*, docs=DOCS, mirror=MIRROR, receipt=RECEIPT, env_path=english.ENV_PATH,
          limit=6000, synthesizer=english.synthesize_azure_tts_mp3_sync, validator=english.validate_mp3):
    data = translations(docs)
    if (mirror / INPUT).read_bytes() != (docs / INPUT).read_bytes():
        raise RuntimeError("Český mirror se liší; žádná syntéza.")
    return english.build_assets(data, receipt=receipt, manifest_name=MANIFEST, env_path=env_path,
                                limit=limit, docs=docs, mirror=mirror, synthesizer=synthesizer,
                                validator=validator, picture="cs")


def check(docs=DOCS, mirror=MIRROR):
    data = translations(docs)
    manifest = json.loads((docs / MANIFEST).read_text())
    if (manifest.get("provider") != "azure" or manifest.get("rate") != data["rate"]
            or len(manifest.get("assets", [])) != len(data["lines"])):
        raise RuntimeError("Neplatný český audio manifest.")
    for line, asset in zip(data["lines"], manifest["assets"]):
        audio = (docs / line["audio"]).read_bytes()
        if (any(asset.get(k) != v for k, v in line.items())
                or english.digest(audio) != asset.get("sha256") or len(audio) != asset.get("bytes")
                or (mirror / line["audio"]).read_bytes() != audio):
            raise RuntimeError("České audio nebo jeho mirror neodpovídá schválenému textu.")
        english.validate_mp3(audio)
    for name in (INPUT, MANIFEST):
        if (docs / name).read_bytes() != (mirror / name).read_bytes():
            raise RuntimeError("Česká data mirroru se liší.")
    return {"ok": True, "czech_mp3": len(data["lines"]), "missing": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--provider", choices=("azure",))
    parser.add_argument("--env-path", type=Path, default=english.ENV_PATH)
    parser.add_argument("--max-characters", type=int, default=6000)
    args = parser.parse_args()
    if args.apply and args.provider != "azure":
        parser.error("Generování vyžaduje výslovné --provider azure.")
    try:
        result = build(env_path=args.env_path, limit=args.max_characters) if args.apply else check()
    except Exception as error:
        print(f"Zastaveno bez opakování: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
