"""Seal the approved La phrase éclair material into a private runtime bundle.

No synthesis, network, publication, or changes to the source content. The answer
key remains outside docs and is read exclusively by the existing game service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def build(source: Path, output: Path, *, expected_rounds: int = 372) -> dict:
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory; existing bundles are preserved")
    raw = json.loads((source / "rounds.json").read_text())
    bindings = {b["id"]: b for b in json.loads((source / "image-bindings.json").read_text())}
    rounds, media = [], {}

    def asset(relative, expected):
        path = source / relative
        if (path.is_symlink() or not path.resolve().is_relative_to(source)
                or not path.is_file() or not re.fullmatch(r"[a-f0-9]{64}", expected or "")):
            raise ValueError("Invalid approved media reference")
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Approved media changed")
        name = expected + path.suffix.lower()
        if path.suffix.lower() not in (".webp", ".png", ".mp3", ".svg"):
            raise ValueError("Unsupported media type")
        media[name] = body
        return name

    for row in raw["rounds"]:
        if row.get("recommendedForInitialRelease") is not True or row.get("editorialStatus") != "ready":
            raise ValueError("Only the accepted core set may be sealed")
        item = {key: row[key] for key in ("id", "infinitive", "promptCs", "sentenceFr", "canonicalPronoun",
                                         "acceptedPronouns", "acceptedVerb", "verbForms", "variants")}
        item["segments"] = []
        for segment in row["segments"]:
            value = {key: segment[key] for key in ("text", "type", "role") if key in segment}
            binding = bindings.get(segment.get("imageBindingId"), {})
            if binding.get("preparedAsset"):
                value["image"] = asset(binding["preparedAsset"], binding["preparedAssetSha256"])
            elif binding.get("kind") == "ui":
                value["visual"] = binding["id"].removeprefix("ui-")
            item["segments"].append(value)
        audio = row["audio"]
        if audio["text"] != row["sentenceFr"]:
            raise ValueError("Canonical audio does not match the approved sentence")
        item["audio"] = asset(audio["asset"], audio["sha256"])
        rounds.append(item)
    if len(rounds) != expected_rounds or len({r["id"] for r in rounds}) != expected_rounds:
        raise ValueError("Approved round count or identities differ")
    body = json.dumps({"schemaVersion": 1, "kind": "la-phrase-eclair-runtime-v1", "rounds": rounds},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    (output / "media").mkdir(mode=0o700)
    for name, content in media.items():
        (output / "media" / name).write_bytes(content)
    (output / "rounds.json").write_bytes(body)
    manifest = {"kind": "la-phrase-eclair-private-bundle-v1", "roundCount": len(rounds),
                "files": {"rounds.json": hashlib.sha256(body).hexdigest(),
                          **{"media/" + n: hashlib.sha256(v).hexdigest() for n, v in sorted(media.items())}}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for path in output.rglob("*"):
        if path.is_file():
            path.chmod(0o600)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.output)
    print(json.dumps({"roundCount": result["roundCount"], "mediaFiles": len(result["files"]) - 1,
                      "privateBundle": str(args.output)}))
