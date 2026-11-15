"""Export curated IT web cards; legacy CSV, mappings and other web apps are read-only.

Assets are immutable and content addressed. The JSON is replaced last, so a
failed export leaves the previous dataset usable. Nothing is cleaned up.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

from PIL import Image, ImageOps

from vocabulary_it_catalog import (CATALOG, MANIFEST, ROOT, all_card_texts, audit,
                                   digest, load_catalog, load_rows)

IMAGE_MANIFEST = Path(__file__).with_name("vocabulary_it_image_manifest.json")
DATA_NAME = "vocabulary-it-v2.json"
ASSET_DIR = "assets/vocabulary-it-v2"


def candidate_files(directory: Path | None, pending: set[str]) -> dict:
    if directory is None:
        return {}
    report = json.loads((directory / "generation_report.json").read_text(encoding="utf-8"))
    if (report.get("schemaVersion") != 1 or report.get("project") != "VocabularyIT-candidates"
            or not isinstance(report.get("items"), list)):
        raise ValueError("Neplatný přehled kandidátních ilustrací.")
    result = {}
    for item in report["items"]:
        uid, name = item.get("uid"), item.get("file")
        if (uid not in pending or uid in result or not isinstance(name, str)
                or PurePosixPath(name).name != name or name in {".", ".."}
                or item.get("status") != "awaiting-visual-approval"):
            raise ValueError("Nepřesné nebo duplicitní přiřazení kandidáta.")
        path = directory / name
        if (not path.is_file() or not path.resolve().is_relative_to(directory.resolve())
                or path.stat().st_size != item.get("bytes") or digest(path) != item.get("sha256")):
            raise ValueError("Změněná kandidátní ilustrace.")
        result[uid] = (path, item["sha256"])
    return result


def webp(data: bytes, edge: int) -> bytes:
    with Image.open(io.BytesIO(data)) as source:
        im = ImageOps.exif_transpose(source)
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        im.save(output, format="WEBP", quality=84, method=4)
        return output.getvalue()


def prepare_export(root: Path, *, catalog_path: Path = CATALOG,
                   manifest_path: Path = MANIFEST, image_manifest_path: Path = IMAGE_MANIFEST,
                   preview: bool = False, candidates: Path | None = None) -> tuple[dict, dict[str, bytes]]:
    if candidates is not None and not preview:
        raise ValueError("Kandidátní obrázky jsou povolené jen v explicitním náhledu.")
    proof = audit(root, catalog_path, manifest_path, image_manifest_path,
                  require_complete_images=not preview)
    catalog = load_catalog(catalog_path)
    rows = load_rows(root / "VocabularyIT/VocabularyIT.csv")
    pending = set(proof["imageBindings"]["pendingUids"])
    drafts = candidate_files(candidates, pending)
    if pending - drafts.keys():
        raise ValueError("Náhledu chybí konkrétní ilustrace; žádný náhradní obrázek se nedoplní.")
    assets, converted, items = {}, {}, []
    for entry, text in all_card_texts(rows, catalog):
        reviewed = entry["imageStatus"] == "reviewed"
        source, expected_sha = ((root / entry["imageFile"], entry["imageSha256"])
                                if reviewed else drafts[entry["uid"]])
        source_data = source.read_bytes()
        source_sha = hashlib.sha256(source_data).hexdigest()
        if source_sha != expected_sha:
            raise ValueError("Ilustrace se během přípravy exportu změnila.")
        if source_sha not in converted:
            urls = []
            for kind, edge in (("images", 900), ("thumbs", 240)):
                data = webp(source_data, edge)
                name = f"{ASSET_DIR}/{kind}/{hashlib.sha256(data).hexdigest()}.webp"
                assets[name] = data
                urls.append(name)
            converted[source_sha] = urls
        full, thumb = converted[source_sha]
        items.append({"id": entry["id"], "uid": entry["uid"], **text,
                      "active": entry["active"], "image": full, "thumbnail": thumb,
                      "imageReviewed": reviewed, "imageRole": entry.get("imageRole", "candidate"),
                      "primaryGroup": entry["primaryGroup"], "topicIds": entry["topicIds"],
                      "partOfSpeech": entry["partOfSpeech"], "teachingType": entry["teachingType"],
                      "expressionType": entry["expressionType"], "difficultyBand": entry["difficultyBand"],
                      "difficultyStatus": entry["difficultyStatus"],
                      "addedAt": entry.get("addedAt"), "legacyAddedAt": entry.get("legacyAddedAt"),
                      "origin": entry.get("origin", "legacy"), "lemma": entry.get("lemma"),
                      "formOfUid": entry.get("formOfUid"), "related": entry.get("related", [])})
    if (digest(catalog_path) != proof["catalogSha256"]
            or digest(root / "VocabularyIT/VocabularyIT.csv") != proof["csvSha256"]):
        raise ValueError("Zdrojová data se během přípravy exportu změnila.")
    return {"schemaVersion": 2, "appName": "VocabularyIT", "language": "it", "translationLanguage": "cs",
            "mode": "preview" if preview else "release", "imageReviewComplete": not pending,
            "audioStatus": "not-generated", "itemCount": len(items), "sourceRowCount": len(rows),
            "parents": catalog["parents"], "groups": catalog["groups"], "items": items,
            "stats": {"active": sum(item["active"] for item in items),
                      "legacyCards": sum(item["origin"] == "legacy" for item in items),
                      "webCards": sum(item["origin"] == "web" for item in items),
                      "pendingImageReview": len(pending), "uniqueSourceImages": len(converted),
                      "teachingTypes": dict(Counter(item["teachingType"] for item in items))},
            "provenance": {"sourceCsvSha256": proof["csvSha256"], "catalogSha256": proof["catalogSha256"],
                           "imageManifestSha256": digest(image_manifest_path)}}, assets


def safe_target(root: Path, relative: str) -> Path:
    path = root / relative
    if (not path.resolve().is_relative_to(root.resolve()) or root.is_symlink()
            or any(parent.is_symlink() for parent in (path, *path.parents) if parent.is_relative_to(root))):
        raise ValueError("Výstup nesmí používat symlink nebo cestu mimo zvolený kořen.")
    return path


def audio_status(root: Path, payload: dict) -> str:
    """Do not reset a completed library to a stale migration placeholder."""
    items = {item["uid"]: item for item in payload["items"] if item["active"]}
    present = False
    for kind, name, namespace in (("words", "vocabulary-it-audio.json", "audio"),
                                  ("sentences", "vocabulary-it-sentence-audio.json", "sentences")):
        path = root / "data" / name
        if not path.is_file():
            return "partial" if present else "not-generated"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("status") != "complete":
            return "partial" if present else "not-generated"
        present = True
        if (manifest.get("language") != "it" or manifest.get("kind") != kind
                or not isinstance(manifest.get("items"), dict) or set(manifest["items"]) != set(items)):
            return "partial"
        for uid, item in items.items():
            record = manifest["items"][uid]
            expected = {"sourceIt": item["it"], "sourceCz": item["cz"]}
            if kind == "sentences":
                expected.update(sourceSentenceIt=item["sentenceIt"], sourceSentenceCz=item["sentenceCz"])
            if record.get("uid") != uid or any(record.get(k) != v for k, v in expected.items()):
                return "partial"
            for language in ("it", "cz"):
                relative = record.get(language)
                if not isinstance(relative, str) or not relative.startswith(f"assets/vocabulary-it-{namespace}/"):
                    return "partial"
                asset = safe_target(root, relative)
                if not asset.is_file() or digest(asset) != manifest.get("assetSha256", {}).get(relative):
                    return "partial"
    return "complete"


def write_export(output: Path, payload: dict, assets: dict[str, bytes]) -> dict:
    output = output.absolute()
    payload = {**payload, "audioStatus": audio_status(output, payload)}
    for relative, data in assets.items():
        if (not relative.startswith(ASSET_DIR + "/") or ".." in PurePosixPath(relative).parts
                or not relative.endswith(hashlib.sha256(data).hexdigest() + ".webp")):
            raise ValueError("Neplatný neměnný exportní asset.")
        path = safe_target(output, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError("Existující asset má odlišný obsah; nebude přepsaný.")
        else:
            with path.open("xb") as handle:
                handle.write(data)
    data_path = safe_target(output, "data/" + DATA_NAME)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if data_path.exists():
        previous = json.loads(data_path.read_text(encoding="utf-8"))
        if previous.get("appName") != "VocabularyIT" or previous.get("schemaVersion") != 2:
            raise ValueError("Cílové JSON patří jiné aplikaci; nebude přepsané.")
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    # Create a retained same-directory staging file. os.replace publishes only
    # complete JSON; retaining a failed stage is intentional (no cleanup/deletion).
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=data_path.parent,
                                     prefix=".vocabulary-it-", suffix=".stage", delete=False) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, data_path)
    if data_path.read_text(encoding="utf-8") != text:
        raise ValueError("Zpětné čtení exportu se neshoduje.")
    return {"cards": payload["itemCount"], "assets": len(assets), "data": str(data_path),
            "mode": payload["mode"], "imageReviewComplete": payload["imageReviewComplete"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Úplný zmrazený nebo kanonický zdroj.")
    parser.add_argument("--output", required=True, type=Path, help="Samostatný kořen webového exportu.")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--candidates", type=Path)
    args = parser.parse_args()
    try:
        payload, assets = prepare_export(args.root, preview=args.preview, candidates=args.candidates)
        # Input validation and image conversion finish before the first output write.
        print(json.dumps(write_export(args.output, payload, assets), ensure_ascii=False))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Export Vocabulary IT selhal: {exc}\n")


if __name__ == "__main__":
    main()
