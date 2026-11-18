"""Read-only identity and source checks for the new Vocabulary IT web app.

The initial migration assigns IDs once. Resolution never uses CSV Order,
accent-insensitive image lookup, or a fallback UID for an unknown meaning.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("vocabulary_it_catalog.json")
MANIFEST = Path(__file__).with_name("vocabulary_it_input_manifest.json")
COLUMNS = ("IT", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_it")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
PARTS = {"noun", "verb", "adjective", "adverb", "pronoun", "number", "preposition",
         "conjunction", "article", "determiner", "particle", "interjection", "verb-modal"}


def identity(it: str, cz: str) -> tuple[str, str]:
    """Normalize Unicode composition and outer whitespace, preserving meaning."""
    if not isinstance(it, str) or not isinstance(cz, str) or not it.strip() or not cz.strip():
        raise ValueError("Identita vyžaduje neprázdné IT i CZ.")
    return tuple(unicodedata.normalize("NFC", value.strip()) for value in (it, cz))


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("CSV má jiné sloupce; nelze bezpečně převzít původní obsah.")
        rows = list(reader)
    orders = set()
    for row in rows:
        identity(row.get("IT"), row.get("CZ"))
        if (set(row) != set(COLUMNS) or any(value is None for value in row.values())
                or not row["Sentence"].strip() or not row["SentenceT"].strip()
                or row["L"] not in {"ano", "ne"} or row["HT"] not in {"ano", "ne"}
                or row["gender_it"] not in {"", "m", "f"}
                or not re.fullmatch(r"[1-9][0-9]*", row["Order"])):
            raise ValueError("Neúplný nebo neplatný zdrojový řádek CSV.")
        if row["Order"] in orders:
            raise ValueError("Duplicitní Order v CSV.")
        orders.add(row["Order"])
    return rows


def validate_catalog(catalog: dict) -> dict:
    if not isinstance(catalog, dict) or catalog.get("schemaVersion") != 1 or catalog.get("language") != "it":
        raise ValueError("Neznámý formát italského katalogu.")
    groups = catalog.get("groups", [])
    if not isinstance(groups, list) or any(not isinstance(group, dict) or "id" not in group for group in groups):
        raise ValueError("Neplatný seznam témat.")
    group_ids = {group["id"] for group in groups}
    if len(groups) != 18 or group_ids != {f"topic-{n:02d}" for n in range(1, 19)}:
        raise ValueError("Katalog musí mít osmnáct jednoznačných témat.")
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Katalog nemá identity karet.")
    uids, ids, keys = set(), set(), set()
    reasons = catalog.get("reviewCodes", {})
    if not isinstance(reasons, dict) or not isinstance(catalog.get("metadataStatus"), str):
        raise ValueError("Katalog nemá stav redakčních návrhů.")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Neplatný záznam katalogu.")
        number, uid = entry.get("id"), entry.get("uid")
        if (type(number) is not int or number < 1 or number in ids
                or uid != f"vit-{number:04d}" or uid in uids):
            raise ValueError("Neplatná nebo duplicitní trvalá identita.")
        if (entry.get("primaryGroup") not in group_ids
                or not isinstance(entry.get("topicIds"), list)
                or not set(entry["topicIds"]).issubset(group_ids)
                or entry["primaryGroup"] not in entry["topicIds"]
                or not isinstance(entry.get("partOfSpeech"), list)
                or not set(entry["partOfSpeech"]).issubset(PARTS)
                or entry.get("teachingType") not in {"word", "interaction", "idiom"}
                or entry.get("expressionType") not in {"word", "phrase"}
                or type(entry.get("active")) is not bool
                or type(entry.get("difficultyBand")) is not int or entry["difficultyBand"] not in {1, 2, 3}
                or entry.get("difficultyStatus") not in {"proposed", "reviewed"}
                or entry.get("editorialStatus") not in {"needs-review", "reviewed"}
                or entry.get("reviewPriority") not in {"normal", "high"}
                or not isinstance(entry.get("reviewReasons"), list)
                or not set(entry["reviewReasons"]).issubset(reasons)):
            raise ValueError(f"Neplatný tematický nebo redakční návrh {uid}.")
        matches = entry.get("matches")
        if not isinstance(matches, list) or not matches:
            raise ValueError(f"Chybí významová shoda {uid}.")
        for match in matches:
            if not isinstance(match, dict):
                raise ValueError(f"Neplatný alias {uid}.")
            key = identity(match.get("it"), match.get("cz"))
            if key in keys:
                raise ValueError("Nejednoznačný význam nebo alias v katalogu.")
            keys.add(key)
        if identity(entry.get("it"), entry.get("cz")) not in {
                identity(match["it"], match["cz"]) for match in matches}:
            raise ValueError(f"Hlavní význam není mezi aliasy {uid}.")
        origin = entry.get("origin", "legacy")
        if origin not in {"legacy", "web"}:
            raise ValueError(f"Neznámý původ karty {uid}.")
        if origin == "web":
            text = entry.get("webText")
            if (not isinstance(text, dict) or set(text) != {"sentenceIt", "sentenceCz", "genderIt"}
                    or not all(isinstance(text.get(key), str) and text[key].strip()
                               for key in ("sentenceIt", "sentenceCz"))
                    or text["genderIt"] not in {"", "m", "f"}
                    or not isinstance(entry.get("addedAt"), str)
                    or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["addedAt"])
                    or "sentenceOverride" in entry):
                raise ValueError(f"Neúplná samostatná webová karta {uid}.")
        image_status = entry.get("imageStatus")
        if image_status not in {"pending-review", "replacement-needed", "reviewed"}:
            raise ValueError(f"Neplatný stav obrazové revize {uid}.")
        image_file = entry.get("imageFile")
        if image_status == "reviewed":
            if (not isinstance(image_file, str)
                    or PurePosixPath(image_file).parent.as_posix() not in {"Pict", "VocabularyIT/Pict"}
                    or PurePosixPath(image_file).as_posix() != image_file
                    or PurePosixPath(image_file).suffix.lower() not in IMAGE_SUFFIXES
                    or not re.fullmatch(r"[0-9a-f]{64}", entry.get("imageSha256", ""))
                    or entry.get("imageRole") not in {"literal", "contextual", "mnemonic"}):
                raise ValueError(f"Neúplná připnutá ilustrace {uid}.")
        elif image_file is not None:
            raise ValueError(f"Nevyřešená ilustrace má schválenou cestu {uid}.")
        override = entry.get("sentenceOverride")
        if override is not None and (not isinstance(override, dict)
                or set(override) != {"sourceIt", "sourceCz", "it", "cz"}
                or not all(isinstance(value, str) and value.strip() for value in override.values())):
            raise ValueError(f"Neplatná oprava příkladové věty {uid}.")
        if "genderOverride" in entry and entry["genderOverride"] not in {"", "m", "f"}:
            raise ValueError(f"Neplatná webová oprava rodu {uid}.")
        uids.add(uid)
        ids.add(number)
    for entry in entries:
        related = entry.get("related", [])
        if (not isinstance(related, list) or any(not isinstance(link, dict)
                or link.get("kind") not in {"related", "same-spelling", "form"} for link in related)):
            raise ValueError(f"Neplatný vztah karty {entry['uid']}.")
        references = [link.get("uid") for link in related]
        if entry.get("formOfUid") is not None:
            references.append(entry["formOfUid"])
        if any(target not in uids or target == entry["uid"] for target in references):
            raise ValueError(f"Neexistující nebo vlastní související identita {entry['uid']}.")
    return catalog


def load_catalog(path: Path = CATALOG) -> dict:
    return validate_catalog(json.loads(path.read_text(encoding="utf-8")))


def resolve_catalog_rows(rows: list[dict], catalog: dict, *, require_all: bool = False) -> list[dict]:
    validate_catalog(catalog)
    lookup = {identity(match["it"], match["cz"]): entry
              for entry in catalog["entries"] for match in entry["matches"]}
    result, seen = [], set()
    for row in rows:
        key = identity(row.get("IT"), row.get("CZ"))
        entry = lookup.get(key)
        if entry is None:
            raise ValueError(f"Neznámý význam {key!r}; doplň katalog, nikdy nepřečísluj UID podle Order.")
        if entry["uid"] in seen:
            raise ValueError(f"Dva řádky by použily tutéž identitu {entry['uid']}.")
        seen.add(entry["uid"])
        result.append(entry)
    if require_all:
        legacy = {entry["uid"] for entry in catalog["entries"] if entry.get("origin", "legacy") == "legacy"}
        if seen != legacy:
            raise ValueError("Zdrojové CSV nepokrývá všechny původní katalogové identity.")
    return result


def effective_card_text(row: dict, entry: dict) -> dict:
    """Apply reviewed web text without rewriting the original desktop CSV."""
    if identity(row.get("IT"), row.get("CZ")) not in {
            identity(match["it"], match["cz"]) for match in entry["matches"]}:
        raise ValueError("Oprava textu patří jinému významu.")
    sentence_it, sentence_cz = row["Sentence"], row["SentenceT"]
    override = entry.get("sentenceOverride")
    if override:
        if (sentence_it, sentence_cz) != (override["sourceIt"], override["sourceCz"]):
            raise ValueError(f"Zdrojová věta se změnila; znovu posuď opravu {entry['uid']}.")
        sentence_it, sentence_cz = override["it"], override["cz"]
    return {"it": entry["it"], "cz": entry["cz"], "sentenceIt": sentence_it,
            "sentenceCz": sentence_cz, "genderIt": entry.get("genderOverride", row["gender_it"])}


def all_card_texts(rows: list[dict], catalog: dict) -> list[tuple[dict, dict]]:
    """Read legacy cards plus explicit web additions, with no synthetic CSV rows."""
    resolved = resolve_catalog_rows(rows, catalog, require_all=True)
    texts = {entry["uid"]: effective_card_text(row, entry) for row, entry in zip(rows, resolved)}
    return [(entry, {"it": entry["it"], "cz": entry["cz"], **entry["webText"]}
             if entry.get("origin", "legacy") == "web" else texts[entry["uid"]])
            for entry in catalog["entries"]]


def verify_image_bindings(root: Path, catalog: dict, manifest: dict, *, require_complete: bool = False) -> dict:
    """No heuristic or fallback may replace a reviewed, exact-case image pin."""
    validate_catalog(catalog)
    if manifest.get("schemaVersion") != 1 or manifest.get("project") != "VocabularyIT-images":
        raise ValueError("Neznámý manifest obrazové revize.")
    ready = [entry for entry in catalog["entries"] if entry["imageStatus"] == "reviewed"]
    pending = [entry["uid"] for entry in catalog["entries"] if entry["imageStatus"] != "reviewed"]
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != {entry["imageFile"] for entry in ready}:
        raise ValueError("Manifest nepokrývá přesně připnuté obrázky.")
    for relative, record in files.items():
        path = root / relative
        if (not isinstance(record, dict) or type(record.get("bytes")) is not int
                or record["bytes"] < 1 or not isinstance(record.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
                or PurePosixPath(relative).parent.as_posix() not in {"Pict", "VocabularyIT/Pict"}
                or PurePosixPath(relative).as_posix() != relative
                or not path.is_file() or path.is_symlink()
                or path.name not in {p.name for p in path.parent.iterdir()}
                or not path.resolve().is_relative_to(root.resolve())
                or path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]):
            raise ValueError(f"Změněná nebo nepřesná ilustrace {relative}.")
    for entry in ready:
        if files[entry["imageFile"]]["sha256"] != entry["imageSha256"]:
            raise ValueError(f"Ilustrace je svázaná s jiným obsahem {entry['uid']}.")
    if require_complete and pending:
        raise ValueError(f"Obrazová revize není dokončená: zbývá {len(pending)} karet.")
    return {"readyCards": len(ready), "verifiedImages": len(files), "pendingUids": pending,
            "complete": not pending, "exact": True}


def verify_input_manifest(root: Path, manifest: dict, *, extra_images: set[str] | None = None) -> dict:
    """Verify pinned bytes and exact case against canonical or frozen inputs."""
    root = root.resolve()
    if manifest.get("schemaVersion") != 1 or manifest.get("project") != "VocabularyIT":
        raise ValueError("Neznámý snímek vstupů.")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Prázdný snímek vstupů.")
    names = {}
    for relative, expected in files.items():
        parts = PurePosixPath(relative)
        if parts.is_absolute() or not parts.parts or any(part in {".", ".."} for part in parts.parts):
            raise ValueError("Neplatná cesta ve vstupním snímku.")
        folder = root
        for part in parts.parts:
            if folder not in names:
                names[folder] = {path.name for path in folder.iterdir()}
            if part not in names[folder]:
                raise ValueError(f"Chybí přesná cesta nebo velikost písmen: {relative}")
            folder = folder / part
        if (not folder.resolve().is_relative_to(root) or not folder.is_file()
                or folder.stat().st_size != expected["bytes"] or digest(folder) != expected["sha256"]):
            raise ValueError(f"Vstup se liší od zmrazeného snímku: {relative}")
    expected_images = {name for name, record in files.items() if record.get("kind") == "image"}
    actual_images = {path.relative_to(root).as_posix() for path in (root / "Pict").iterdir()
                     if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES}
    if expected_images | (extra_images or set()) != actual_images:
        raise ValueError("Změnil se úplný inventář obrazů Pict.")
    return {"verifiedFiles": len(files), "verifiedImages": len(expected_images), "exact": True}


def audit(root: Path, catalog_path: Path = CATALOG, manifest_path: Path = MANIFEST,
          image_manifest_path: Path | None = None, *, require_complete_images: bool = False) -> dict:
    catalog = load_catalog(catalog_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    image_manifest = None
    extra_images = set()
    if image_manifest_path is not None:
        image_manifest = json.loads(image_manifest_path.read_text(encoding="utf-8"))
        if (image_manifest.get("foundationManifestSha256") != digest(manifest_path)
                or not isinstance(image_manifest.get("files"), dict)):
            raise ValueError("Obrazová revize patří jinému vstupnímu snímku.")
        extra_images = set(image_manifest["files"]) - set(manifest["files"])
    proof = verify_input_manifest(root, manifest, extra_images={
        path for path in extra_images if PurePosixPath(path).parent.as_posix() == "Pict"})
    rows = load_rows(root / "VocabularyIT/VocabularyIT.csv")
    entries = resolve_catalog_rows(rows, catalog, require_all=True)
    cards = all_card_texts(rows, catalog)
    image_proof = {}
    if image_manifest is not None:
        image_proof = {"imageBindings": verify_image_bindings(
            root, catalog, image_manifest, require_complete=require_complete_images)}
    elif require_complete_images:
        raise ValueError("Úplnost obrazů vyžaduje obrazový manifest.")
    return {**proof, **image_proof, "additionalPinnedImages": len(extra_images),
            "cards": len(cards), "legacyCards": len(rows),
            "identities": len({entry["uid"] for entry, _ in cards}),
            "topics": len(catalog["groups"]), "allActive": all(entry["active"] for entry, _ in cards),
            "metadataStatus": catalog["metadataStatus"],
            "highPriorityReview": [{"uid": entry["uid"], "it": entry["it"], "cz": entry["cz"],
                                    "reasons": entry["reviewReasons"]} for entry in entries
                                   if entry["reviewPriority"] == "high"],
            "genderCounts": dict(Counter(row["gender_it"] or "unspecified" for row in rows)),
            "teachingTypes": dict(Counter(entry["teachingType"] for entry, _ in cards)),
            "topicCounts": dict(sorted(Counter(entry["primaryGroup"] for entry, _ in cards).items())),
            "csvSha256": digest(root / "VocabularyIT/VocabularyIT.csv"),
            "catalogSha256": digest(catalog_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Kanonický nebo zmrazený kořen vstupů.")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--image-manifest", type=Path)
    parser.add_argument("--require-complete-images", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.root, args.catalog, args.manifest, args.image_manifest,
                       require_complete_images=args.require_complete_images)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Kontrola Vocabulary IT selhala: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
