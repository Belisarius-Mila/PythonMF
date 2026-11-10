#!/usr/bin/env python3
"""Audit novel Scene 6 vocabulary and build only missing fixed word audio."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_scene06_opening_audio as audio

DOCS, MIRROR = audio.DOCS, audio.MIRROR
INPUT, GENERATED, MANIFEST = "vocabulary.json", "dictionary_generated_audio.json", "dictionary_audio_manifest.json"
RECEIPT = audio.ROOT / "data/private/mmtx/scene06_dictionary_20261110/audio_receipt.json"
PRIOR = ["scene01_audio_manifest.js"] + [f"{name}/audio_manifest.js" for name in (
    "scene02_sunnys_lost_nuts", "scene03_journey_to_the_lake", "scene04_harry_guard_prototype", "scene05_log_bridge")]
SCRIPTS = ["script_intro_v2.js"] + [p.replace("audio_manifest.js", "script.js") for p in PRIOR[1:]]
INFLECTIONS = {"clouds": "cloud", "ears": "ear", "trees": "tree", "beavers": "beaver",
    "asked": "ask", "called": "call", "coming": "come", "practising": "practise", "practicing": "practise",
    "smaller": "small", "better": "good", "ones": "one", "wants": "want", "needs": "need",
    "friends": "friend", "logs": "log", "crossed": "cross", "is": "be", "are": "be", "am": "be",
    "was": "be", "were": "be", "has": "have", "does": "do", "did": "do", "going": "go",
    "helped": "help", "helps": "help", "jumps": "jump", "jumping": "jump", "looks": "look"}
NAMES = {"benji", "bunny", "bruno", "fiona", "sunny", "harry", "logan", "ollie", "freddie", "dotty"}


def words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace("’", "'"))


def phrase(text):
    return " ".join(INFLECTIONS.get(x, x) for x in words(text))


def manifest(path):
    raw = path.read_text()
    return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])


def prior_corpus(root):
    texts = []
    for name in PRIOR:
        texts.extend(key.split("::", 1)[-1] for key in manifest(root / name)["dialogue"]["en"])
    for name in SCRIPTS:
        source = (root / name).read_text()
        if name == "script_intro_v2.js":
            source = source[source.index("const clearingDictionary ="):source.index("const houseBunnyIntroAudio =")]
        patterns = [r'\b(?:en|textEn|cue):\s*("(?:[^"\\]|\\.)*")']
        if name.startswith("scene04"):
            patterns += [r'dialogue\("[^"]+",\s*("(?:[^"\\]|\\.)*")', r'prompt\(\s*("(?:[^"\\]|\\.)*")']
        if name.startswith("scene05"):
            patterns += [r'(?:dialogue|prompt)\("[^"]+",\s*("(?:[^"\\]|\\.)*")']
        for pattern in patterns:
            texts.extend(json.loads(x) for x in re.findall(pattern, source))
    return texts


def vocabulary(docs=DOCS):
    data = json.loads((docs / INPUT).read_text())
    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list) or not data["entries"]:
        raise RuntimeError("Neplatný slovníček.")
    prior = prior_corpus(docs.parent)
    old_words = {x for text in prior for x in phrase(text).split()}
    old_phrases = [" " + phrase(text) + " " for text in prior]
    current = [(p, row) for p in range(1, 11) for row in audio.dialogue(docs, p)["lines"]]
    seen = set()
    for n, item in enumerate(data["entries"], 1):
        lemma = phrase(item["lemma"])
        if (item["id"] != f"v{n:02d}" or lemma in seen or lemma in NAMES
                or not item["en"].strip() or not item["cz"].strip() or not item["emoji"]):
            raise RuntimeError("Neplatné nebo duplicitní heslo.")
        if (lemma in old_words if " " not in lemma else any(" " + lemma + " " in text for text in old_phrases)):
            raise RuntimeError(f"Heslo již bylo ve scénách 1–5: {item['en']}")
        if not any(" " + phrase(form) + " " in " " + phrase(row["text"]) + " "
                   for form in item["forms"] for _, row in current):
            raise RuntimeError(f"Heslo není doložené v šestce: {item['en']}")
        seen.add(lemma)
    return data


def assets(data):
    return [{"id": item["id"], "language": lang, "text": item["en" if lang == "en" else "cz"],
             "voice": "en-US-AndrewNeural" if lang == "en" else "cs-CZ-VlastaNeural",
             "audio": f"audio/vocabulary/{lang}/{item['id']}.mp3", "origin": item["origins"][lang]}
            for item in data["entries"] for lang in ("en", "cs")]


def reused_bytes(row, docs):
    origin = row["origin"]
    if not re.fullmatch(r"assets/vocabulary-en-audio/cs-cz-vlasta-neural/[0-9a-f]{20}\.mp3", origin["source"]):
        raise RuntimeError("Nepovolený zdroj převzatého audia.")
    identity = audio.digest(f"{row['voice']}\n-10%\n{row['text']}".encode())[:20]
    if row["language"] != "cs" or Path(origin["source"]).stem != identity:
        raise RuntimeError("Převzatý hlas, tempo nebo text nesouhlasí.")
    raw = (docs.parent / origin["source"]).read_bytes()
    if audio.digest(raw) != origin["sha256"]:
        raise RuntimeError("Převzaté audio má změněný otisk.")
    audio.validate_mp3(raw)
    return raw


def build(*, docs=DOCS, mirror=MIRROR, receipt=RECEIPT, limit=10000, env_path=audio.ENV_PATH,
          synthesizer=audio.synthesize_azure_tts_mp3_sync, validator=audio.validate_mp3):
    data = vocabulary(docs)
    if (docs / INPUT).read_bytes() != (mirror / INPUT).read_bytes():
        raise RuntimeError("Vstupní mirror slovníčku se liší.")
    rows = assets(data)
    pending = [r for r in rows if r["origin"]["type"] == "azure"]
    if any(r["origin"]["type"] not in ("azure", "reused") for r in rows):
        raise RuntimeError("Neznámý původ audia.")
    count = sum(audio.ssml_parts(r["text"], r["voice"])[1] for r in pending)
    if not 0 < limit <= 10000 or count > limit:
        raise RuntimeError("Celý slovníček překračuje rozpočet; žádný požadavek.")
    reused = [(r, reused_bytes(r, docs)) for r in rows if r["origin"]["type"] == "reused"]
    for row, raw in reused:
        for root in (docs, mirror): audio.write_new(root / row["audio"], raw)
    payload = {"schema_version": 1, "rate": "-10%", "input_sha256": audio.digest((docs / INPUT).read_bytes()), "lines": pending}
    result = audio.build_assets(payload, receipt=receipt, manifest_name=GENERATED, docs=docs, mirror=mirror,
                                limit=limit, env_path=env_path, synthesizer=synthesizer, validator=validator, picture="dictionary")
    records = [{**row, "sha256": audio.digest((docs / row["audio"]).read_bytes()), "bytes": (docs / row["audio"]).stat().st_size} for row in rows]
    for root in (docs, mirror): audio.atomic_write_json(root / MANIFEST, {"schema_version": 1, "rate": "-10%", "assets": records})
    return {**result, "reused": len(reused), "total_assets": len(rows)}


def check(docs=DOCS, mirror=MIRROR):
    rows = assets(vocabulary(docs)); saved = json.loads((docs / MANIFEST).read_text())
    if saved.get("rate") != "-10%" or len(saved.get("assets", [])) != len(rows): raise RuntimeError("Neúplný manifest slovníčku.")
    for row, item in zip(rows, saved["assets"]):
        raw = (docs / row["audio"]).read_bytes();audio.validate_mp3(raw)
        if (any(item.get(k) != v for k, v in row.items()) or audio.digest(raw) != item["sha256"]
                or (row["origin"]["type"] == "reused" and audio.digest(raw) != row["origin"]["sha256"])
                or len(raw) != item["bytes"] or (mirror / row["audio"]).read_bytes() != raw): raise RuntimeError("Neshoda audia slovníčku.")
    for name in (INPUT, GENERATED, MANIFEST):
        if (docs / name).read_bytes() != (mirror / name).read_bytes(): raise RuntimeError("Neshoda dat slovníčku.")
    return {"ok": True, "entries": len(rows) // 2, "audio_assets": len(rows)}


def main():
    p = argparse.ArgumentParser(description=__doc__);mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit",action="store_true");mode.add_argument("--check",action="store_true");mode.add_argument("--apply",action="store_true")
    p.add_argument("--provider",choices=("azure",));p.add_argument("--env-path",type=Path,default=audio.ENV_PATH);p.add_argument("--max-characters",type=int,default=10000)
    args=p.parse_args()
    if args.apply and args.provider!="azure":p.error("Generování vyžaduje výslovný Azure provider.")
    try:
        result=build(env_path=args.env_path,limit=args.max_characters) if args.apply else check() if args.check else {"ok":True,"entries":len(vocabulary()["entries"])}
    except Exception as exc: print(f"Zastaveno bez opakování: {exc}",file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__ == "__main__": raise SystemExit(main())
