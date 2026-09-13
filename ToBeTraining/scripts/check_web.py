#!/usr/bin/env python3
"""Read-only content, image-budget, audio-codec and local HTTP verification."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

from PIL import Image
from build_web_data import build_data

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    data = json.loads((WEB / "data.json").read_text())
    assert data == build_data(), "Export differs from CSV or reviewed image map"
    paths = {"index.html", "styles.css", "app.mjs", "core.mjs", "data.json"}
    for row in [*data["sentences"], *data["verbs"]]:
        assert row["image"] in data["images"], row["id"]
        for field, key in row["audio"].items():
            assert data["audio"][key]["text"] == row[field], (row["id"], field)
    image_sizes = []
    for image in data["images"].values():
        path = WEB / image["src"]
        assert path.stat().st_size <= 262144, path.name
        image_sizes.append(path.stat().st_size)
        with Image.open(path) as im:
            assert im.format == "WEBP"
            im.load()
        paths.add(image["src"])

    def probe(clip):
        path = WEB / clip["src"]
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name:format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        assert metadata["streams"][0]["codec_name"] == "mp3", path.name
        assert 0.2 < float(metadata["format"]["duration"]) < 25, path.name
        assert path.stat().st_size > 1000, path.name
        return clip["src"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        paths.update(pool.map(probe, data["audio"].values()))
    if args.url:
        def http_check(relative):
            with urlopen(args.url.rstrip("/") + "/" + relative, timeout=10) as response:
                assert response.status == 200
                assert hashlib.sha256(response.read()).digest() == hashlib.sha256((WEB / relative).read_bytes()).digest()
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(http_check, sorted(paths)))
    print(json.dumps({"questions": len(data["sentences"]), "constructions": len(data["verbs"]),
        "mp3_verified": len(data["audio"]), "images_verified": len(image_sizes),
        "image_max_bytes": max(image_sizes), "image_total_bytes": sum(image_sizes),
        "http_verified": len(paths) if args.url else 0}, indent=2))


if __name__ == "__main__":
    main()
