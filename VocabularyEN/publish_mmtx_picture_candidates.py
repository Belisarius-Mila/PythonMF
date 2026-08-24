#!/usr/bin/env python3
"""Copy approved MMTX picture candidates without overwriting and preview mapping.

The mapping itself is never changed by this tool.  ``--apply-copy`` creates
only missing picture files in ``Pict`` using exclusive file creation and then
verifies every copied byte with SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PICT_DIR = REPO_ROOT / "Pict"
PICTNEW_DIR = REPO_ROOT / "PictNew"
PLAN_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_picture_plan_20260824.json"
MAPPING_PATH = PICT_DIR / "mapping.json"
COPY_RECEIPT_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_copy_receipt_20260824.json"
MAPPING_PREVIEW_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_mapping_preview_20260824.json"
MAPPING_PREVIEW_MD_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_mapping_preview_20260824.md"
MAPPING_BACKUP_DIR = PICTNEW_DIR / "backups"
MAPPING_APPLY_RECEIPT_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_mapping_apply_receipt_20260824.json"
WEB_SYNC_RECEIPT_PATH = PICTNEW_DIR / "VocabularyEN_MMTX_web_sync_receipt_20260824.json"
CSV_PATH = REPO_ROOT / "VocabularyEN" / "VocabularyEN.csv"
WEB_DATA_PATH = REPO_ROOT / "docs" / "data" / "vocabulary-en.json"
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
WEB_SYNC_GUARD_ADDITIONS = {"běhat": "race"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan() -> dict[str, object]:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def copy_candidates(plan: dict[str, object]) -> list[dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}
    for assignment in plan["assignments"]:
        action = assignment["action"]
        if action == "reuse_mmtx_forest_asset":
            source = REPO_ROOT / assignment["source"]
            target = PICT_DIR / f"{assignment['image_stem']}{source.suffix.lower()}"
        elif action == "generate":
            stem = assignment["image_stem"]
            matches = sorted(
                (PICTNEW_DIR / "generated").glob(
                    f"20260824_en_mmtx_batch*/{stem}.webp"
                )
            )
            if len(matches) != 1:
                raise SystemExit(
                    f"Expected one generated source for {stem}, found {len(matches)}"
                )
            source = matches[0]
            target = PICT_DIR / f"{stem}.webp"
        else:
            continue

        key = target.name.casefold()
        previous = candidates.get(key)
        candidate = {
            "action": action,
            "image_stem": assignment["image_stem"],
            "source": source,
            "target": target,
        }
        if previous and previous["source"] != source:
            raise SystemExit(f"Conflicting copy sources for {target.name}")
        candidates[key] = candidate

    result = []
    for candidate in sorted(candidates.values(), key=lambda item: item["target"].name.casefold()):
        source = candidate["source"]
        if not source.is_file():
            raise SystemExit(f"Missing source: {source}")
        candidate["bytes"] = source.stat().st_size
        candidate["sha256"] = sha256(source)
        result.append(candidate)
    if len(result) != 68:
        raise SystemExit(f"Expected 68 unique copy candidates, found {len(result)}")
    return result


def preflight_targets(candidates: list[dict[str, object]]) -> None:
    existing_names = {path.name.casefold(): path for path in PICT_DIR.iterdir() if path.is_file()}
    collisions = [
        str(existing_names[candidate["target"].name.casefold()])
        for candidate in candidates
        if candidate["target"].name.casefold() in existing_names
    ]
    if collisions:
        raise SystemExit("Refusing to overwrite existing targets: " + ", ".join(collisions))


def copy_exclusive(source: Path, target: Path) -> None:
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
        for chunk in iter(lambda: input_handle.read(1024 * 1024), b""):
            output_handle.write(chunk)
        output_handle.flush()
        os.fsync(output_handle.fileno())


def apply_copy(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    preflight_targets(candidates)
    receipt_items = []
    for candidate in candidates:
        source = candidate["source"]
        target = candidate["target"]
        copy_exclusive(source, target)
        copied_sha = sha256(target)
        if copied_sha != candidate["sha256"]:
            raise SystemExit(f"SHA-256 mismatch after copying {target}")
        receipt_items.append(
            {
                "action": candidate["action"],
                "image_stem": candidate["image_stem"],
                "source": source.relative_to(REPO_ROOT).as_posix(),
                "target": target.relative_to(REPO_ROOT).as_posix(),
                "bytes": candidate["bytes"],
                "sha256": copied_sha,
                "status": "created_without_overwrite",
            }
        )
    return receipt_items


def available_picture_stems() -> set[str]:
    return {
        path.stem
        for path in PICT_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    }


def load_sync_module():
    path = REPO_ROOT / "VocabularyEN" / "sync_vocabulary_en_to_docs.py"
    spec = importlib.util.spec_from_file_location("sync_vocabulary_en_to_docs", path)
    if not spec or not spec.loader:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_web_sync_preview(
    plan: dict[str, object], current_mapping: dict[str, str], additions: dict[str, str]
) -> dict[str, object]:
    sync = load_sync_module()
    rows = sync.load_rows(CSV_PATH)
    base_dirs = sync.build_picture_base_dirs(REPO_ROOT, CSV_PATH)
    picture_stems = sync.discover_picture_stems(base_dirs)
    proposed_raw = dict(current_mapping)
    proposed_raw.update(additions)
    proposed_mapping = {
        sync.normalize_word(str(key)): sync.normalize_word(str(value))
        for key, value in proposed_raw.items()
        if sync.normalize_word(str(key)) and sync.normalize_word(str(value))
    }
    payload, asset_map = sync.build_export_payload(
        rows=rows,
        base_dirs=base_dirs,
        synonym_image_map=proposed_mapping,
        picture_stems=picture_stems,
        output_root=REPO_ROOT / "docs",
        asset_dir_name="vocabulary-en",
        source_csv_label="VocabularyEN/VocabularyEN.csv",
    )
    assignments = {int(item["order"]): item for item in plan["assignments"]}
    mismatches = []
    imported_items = []
    for item in payload["items"]:
        order = int(item["order"])
        if order < 187:
            continue
        expected = str(assignments[order]["image_stem"])
        actual = str(item["imageStem"])
        if sync.normalize_word(expected) != sync.normalize_word(actual):
            mismatches.append(
                {"order": order, "en": item["en"], "expected": expected, "actual": actual}
            )
        imported_items.append(item)
    if mismatches:
        raise SystemExit(
            "Web preview does not match the approved picture plan: "
            + json.dumps(mismatches, ensure_ascii=False)
        )
    current_web_rows = None
    current_web_unique_images = None
    changed_existing_rows = []
    if WEB_DATA_PATH.is_file():
        current_web = json.loads(WEB_DATA_PATH.read_text(encoding="utf-8"))
        current_web_rows = current_web.get("itemCount")
        current_web_unique_images = current_web.get("stats", {}).get("uniqueImageFiles")
        for proposed_item in payload["items"][: int(current_web_rows or 0)]:
            current_item = current_web["items"][int(proposed_item["order"]) - 1]
            if current_item.get("imageStem") != proposed_item.get("imageStem"):
                changed_existing_rows.append(
                    {
                        "order": proposed_item["order"],
                        "en": proposed_item["en"],
                        "cz": proposed_item["cz"],
                        "current_image_stem": current_item.get("imageStem"),
                        "proposed_image_stem": proposed_item.get("imageStem"),
                    }
                )
    web_asset_dir = REPO_ROOT / "docs" / "assets" / "vocabulary-en"
    existing_assets = {
        path.name: path for path in web_asset_dir.iterdir() if path.is_file()
    } if web_asset_dir.is_dir() else {}
    proposed_assets = {dest_name: source for source, dest_name in asset_map.items()}
    new_assets = sorted(set(proposed_assets) - set(existing_assets))
    removed_assets = sorted(set(existing_assets) - set(proposed_assets))
    changed_assets = sorted(
        name
        for name in set(existing_assets) & set(proposed_assets)
        if sha256(existing_assets[name]) != sha256(proposed_assets[name])
    )
    unchanged_assets = sorted(
        set(existing_assets) & set(proposed_assets) - set(changed_assets)
    )
    return {
        "status": "preview_only_web_not_modified",
        "note": "Web VocabularyEN has no separate mapping.json; sync consumes Pict/mapping.json.",
        "current_web_row_count": current_web_rows,
        "proposed_web_row_count": payload["itemCount"],
        "current_web_unique_image_count": current_web_unique_images,
        "proposed_web_unique_image_count": payload["stats"]["uniqueImageFiles"],
        "proposed_web_asset_copy_count": len(asset_map),
        "new_web_asset_count": len(new_assets),
        "changed_existing_web_asset_count": len(changed_assets),
        "unchanged_existing_web_asset_count": len(unchanged_assets),
        "removed_web_asset_count": 0,
        "preserved_unreferenced_web_asset_count": len(removed_assets),
        "preserved_unreferenced_web_assets": removed_assets,
        "changed_existing_row_count": len(changed_existing_rows),
        "changed_existing_rows": changed_existing_rows,
        "proposed_web_missing_image_count": sum(
            bool(item["imageMissing"]) for item in payload["items"]
        ),
        "imported_row_count": len(imported_items),
        "imported_rows_matching_approved_picture_plan": len(imported_items),
        "output_data": "docs/data/vocabulary-en.json",
        "output_assets": "docs/assets/vocabulary-en/",
        "writes_separate_web_mapping_json": False,
        "planned_sync_flag": "--preserve-extra-assets",
    }


def mapping_preview(plan: dict[str, object]) -> dict[str, object]:
    current_bytes = MAPPING_PATH.read_bytes()
    current = json.loads(current_bytes.decode("utf-8"))
    mmtx_additions = dict(plan["mapping_preview"])
    additions = dict(mmtx_additions)
    for key, value in WEB_SYNC_GUARD_ADDITIONS.items():
        previous = additions.get(key)
        if previous is not None and previous != value:
            raise SystemExit(f"Conflicting web-sync guard mapping for {key}")
        additions[key] = value
    unexpected_existing = {
        key: {"current": current[key], "proposed": value}
        for key, value in additions.items()
        if key in current
    }
    if unexpected_existing:
        raise SystemExit(
            "Mapping changed since planning; preview must be rebuilt: "
            + json.dumps(unexpected_existing, ensure_ascii=False)
        )
    stems = available_picture_stems()
    missing_targets = sorted({value for value in additions.values() if value not in stems})
    if missing_targets:
        raise SystemExit("Mapping targets without pictures: " + ", ".join(missing_targets))
    preview = {
        "schema_version": 1,
        "created_at": "2026-08-24",
        "status": "preview_only_mapping_not_modified",
        "mapping_path": "Pict/mapping.json",
        "base_sha256": hashlib.sha256(current_bytes).hexdigest(),
        "current_entry_count": len(current),
        "addition_count": len(additions),
        "mmtx_addition_count": len(mmtx_additions),
        "web_sync_guard_addition_count": len(WEB_SYNC_GUARD_ADDITIONS),
        "web_sync_guard_additions": WEB_SYNC_GUARD_ADDITIONS,
        "proposed_entry_count": len(current) + len(additions),
        "all_target_images_present": True,
        "additions": additions,
        "preserved_existing_conflicts": plan["preserved_mapping_conflicts"],
    }
    preview["web_sync_preview"] = build_web_sync_preview(plan, current, additions)
    return preview


def escape_markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|")


def render_mapping_preview_markdown(preview: dict[str, object]) -> str:
    additions = "\n".join(
        f"| {escape_markdown_cell(key)} | `{value}` |"
        for key, value in preview["additions"].items()
    )
    conflicts = "\n".join(
        f"| {escape_markdown_cell(item['cz'])} | `{item['current']}` | "
        f"`{item['proposed']}` | zachovat současnou hodnotu |"
        for item in preview["preserved_existing_conflicts"]
    )
    web = preview["web_sync_preview"]
    return f"""# VocabularyEN + MMTX — mapping preview

**Stav:** pouze náhled, `Pict/mapping.json` nebyl změněn<br>
**Výchozí SHA-256:** `{preview['base_sha256']}`<br>
**Položek nyní:** {preview['current_entry_count']}<br>
**Nových položek:** {preview['addition_count']}<br>
**Z toho MMTX / ochranná oprava webu:** {preview['mmtx_addition_count']} / {preview['web_sync_guard_addition_count']}<br>
**Položek po případném schválení:** {preview['proposed_entry_count']}<br>
**Všechny cílové obrázky existují:** ano

## Dopad následného webového syncu

- Web nemá samostatný `mapping.json`; generátor načítá centrální `Pict/mapping.json`.
- Řádků nyní / po syncu: {web['current_web_row_count']} / {web['proposed_web_row_count']}
- Unikátních webových obrázků nyní / po syncu: {web['current_web_unique_image_count']} / {web['proposed_web_unique_image_count']}
- Nové / skutečně změněné / odstraněné webové obrázky: {web['new_web_asset_count']} / {web['changed_existing_web_asset_count']} / {web['removed_web_asset_count']}
- Staré nepoužívané obrázky bezpečně ponechané: {web['preserved_unreferenced_web_asset_count']}
- Chybějících obrázků po syncu: {web['proposed_web_missing_image_count']}
- Nových MMTX řádků odpovídajících schválenému obrazovému plánu: {web['imported_rows_matching_approved_picture_plan']} / {web['imported_row_count']}
- Budoucí výstupy: `docs/data/vocabulary-en.json` a `docs/assets/vocabulary-en/`
- Synchronizace bude spuštěna s `--preserve-extra-assets`, takže nic nesmaže.

## Nové položky

| Český klíč | Cílový image stem |
|---|---|
{additions}

## Existující konflikty ponechané beze změny

| Český klíč | Současná hodnota | Kandidát | Rozhodnutí |
|---|---|---|---|
{conflicts}
"""


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def append_mapping_bytes(current_bytes: bytes, additions: dict[str, str]) -> bytes:
    closing_index = current_bytes.rfind(b"\n}")
    if closing_index < 0 or current_bytes[closing_index:] != b"\n}\n":
        raise SystemExit("Unexpected Pict/mapping.json ending; refusing to rewrite it")
    lines = [
        f"  {json.dumps(key, ensure_ascii=False)}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in additions.items()
    ]
    return current_bytes[:closing_index] + b",\n" + ",\n".join(lines).encode("utf-8") + b"\n}\n"


def apply_mapping_from_approved_preview() -> dict[str, object]:
    preview = json.loads(MAPPING_PREVIEW_PATH.read_text(encoding="utf-8"))
    if preview.get("status") != "preview_only_mapping_not_modified":
        raise SystemExit("Mapping preview is not in an approved pre-apply state")
    additions = preview.get("additions")
    if not isinstance(additions, dict) or len(additions) != 86:
        raise SystemExit("Expected exactly 86 approved mapping additions")
    current_bytes = MAPPING_PATH.read_bytes()
    before_sha = hashlib.sha256(current_bytes).hexdigest()
    if before_sha != preview.get("base_sha256"):
        raise SystemExit("Pict/mapping.json changed after preview; refusing to apply")
    current = json.loads(current_bytes.decode("utf-8"))
    collisions = sorted(set(current) & set(additions))
    if collisions:
        raise SystemExit("Approved additions now collide with mapping keys: " + ", ".join(collisions))

    MAPPING_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = MAPPING_BACKUP_DIR / f"mapping_before_mmtx_20260824_{before_sha[:12]}.json"
    if backup_path.exists():
        if backup_path.read_bytes() != current_bytes:
            raise SystemExit(f"Existing backup has unexpected content: {backup_path}")
    else:
        write_exclusive(backup_path, current_bytes)

    updated_bytes = append_mapping_bytes(current_bytes, additions)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="mapping.mmtx.", suffix=".tmp", dir=MAPPING_PATH.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(updated_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, MAPPING_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)

    written_bytes = MAPPING_PATH.read_bytes()
    written = json.loads(written_bytes.decode("utf-8"))
    if len(written) != len(current) + len(additions):
        raise SystemExit("Unexpected mapping entry count after apply")
    if any(written.get(key) != value for key, value in current.items()):
        raise SystemExit("An existing mapping value changed during apply")
    if any(written.get(key) != value for key, value in additions.items()):
        raise SystemExit("An approved mapping addition is missing after apply")
    receipt = {
        "schema_version": 1,
        "created_at": "2026-08-24",
        "status": "mapping_applied_web_sync_pending",
        "mapping_path": "Pict/mapping.json",
        "backup_path": backup_path.relative_to(REPO_ROOT).as_posix(),
        "before_sha256": before_sha,
        "after_sha256": hashlib.sha256(written_bytes).hexdigest(),
        "entry_count_before": len(current),
        "addition_count": len(additions),
        "entry_count_after": len(written),
        "existing_values_preserved": True,
    }
    write_json(MAPPING_APPLY_RECEIPT_PATH, receipt)
    return receipt


def finalize_web_sync_receipt(plan: dict[str, object]) -> dict[str, object]:
    mapping_receipt = json.loads(MAPPING_APPLY_RECEIPT_PATH.read_text(encoding="utf-8"))
    mapping_bytes = MAPPING_PATH.read_bytes()
    if hashlib.sha256(mapping_bytes).hexdigest() != mapping_receipt["after_sha256"]:
        raise SystemExit("Pict/mapping.json no longer matches the applied mapping receipt")
    mapping = json.loads(mapping_bytes.decode("utf-8"))
    data_bytes = WEB_DATA_PATH.read_bytes()
    data = json.loads(data_bytes.decode("utf-8"))
    if data.get("itemCount") != 306 or len(data.get("items", [])) != 306:
        raise SystemExit("Expected 306 synchronized web vocabulary rows")
    assignments = {int(item["order"]): item for item in plan["assignments"]}
    imported = data["items"][186:]
    for item in imported:
        expected = str(assignments[int(item["order"])]["image_stem"]).casefold()
        if str(item.get("imageStem", "")).casefold() != expected:
            raise SystemExit(f"Web image mismatch for row {item['order']}: {item['en']}")
    missing_paths = [
        item.get("image")
        for item in data["items"]
        if not item.get("image") or not (REPO_ROOT / "docs" / item["image"]).is_file()
    ]
    if missing_paths:
        raise SystemExit(f"Web data contains missing image paths: {missing_paths}")
    preview = json.loads(MAPPING_PREVIEW_PATH.read_text(encoding="utf-8"))
    preserved = preview["web_sync_preview"]["preserved_unreferenced_web_assets"]
    asset_dir = REPO_ROOT / "docs" / "assets" / "vocabulary-en"
    for name in preserved:
        if not (asset_dir / name).is_file():
            raise SystemExit(f"Expected preserved web asset is missing: {name}")
    receipt = {
        "schema_version": 1,
        "created_at": "2026-08-24",
        "status": "mapping_and_web_sync_completed",
        "mapping_entry_count": len(mapping),
        "mapping_sha256": hashlib.sha256(mapping_bytes).hexdigest(),
        "web_data_path": "docs/data/vocabulary-en.json",
        "web_data_sha256": hashlib.sha256(data_bytes).hexdigest(),
        "web_row_count": data["itemCount"],
        "web_sentence_count": data["stats"]["withSentence"],
        "web_sentence_translation_count": data["stats"]["withSentenceTranslation"],
        "web_unique_referenced_image_count": data["stats"]["uniqueImageFiles"],
        "web_missing_image_count": 0,
        "approved_imported_rows_verified": len(imported),
        "preserved_unreferenced_assets": preserved,
        "asset_deletions": 0,
    }
    write_json(WEB_SYNC_RECEIPT_PATH, receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--apply-copy",
        action="store_true",
        help="Create approved image files in Pict without overwriting.",
    )
    group.add_argument(
        "--refresh-preview",
        action="store_true",
        help="Rebuild mapping and web-sync previews after the approved copy.",
    )
    group.add_argument(
        "--apply-mapping",
        action="store_true",
        help="Apply exactly the approved mapping preview after making a byte backup.",
    )
    group.add_argument(
        "--finalize-web-sync",
        action="store_true",
        help="Verify the synchronized web export and write its completion receipt.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = load_plan()
    candidates = copy_candidates(plan)
    print(f"Copy candidates: {len(candidates)}")
    print(f"Forest School PNG: {sum(item['action'] == 'reuse_mmtx_forest_asset' for item in candidates)}")
    print(f"Generated WebP: {sum(item['action'] == 'generate' for item in candidates)}")
    if (
        not args.apply_copy
        and not args.refresh_preview
        and not args.apply_mapping
        and not args.finalize_web_sync
    ):
        preflight_targets(candidates)
        print("Dry run only. No pictures or mapping changed.")
        return 0

    if args.apply_mapping:
        receipt = apply_mapping_from_approved_preview()
        print(
            f"Mapping applied: {receipt['entry_count_before']} + "
            f"{receipt['addition_count']} = {receipt['entry_count_after']}"
        )
        print(f"Mapping backup: {receipt['backup_path']}")
        print(f"Mapping receipt: {MAPPING_APPLY_RECEIPT_PATH}")
        return 0

    if args.finalize_web_sync:
        receipt = finalize_web_sync_receipt(plan)
        print(f"Web sync verified: {receipt['web_row_count']} rows")
        print(f"Referenced images: {receipt['web_unique_referenced_image_count']}")
        print(f"Asset deletions: {receipt['asset_deletions']}")
        print(f"Web sync receipt: {WEB_SYNC_RECEIPT_PATH}")
        return 0

    if args.apply_copy:
        receipt_items = apply_copy(candidates)
        receipt = {
            "schema_version": 1,
            "created_at": "2026-08-24",
            "status": "copy_completed_mapping_not_modified",
            "copied_count": len(receipt_items),
            "items": receipt_items,
        }
        write_json(COPY_RECEIPT_PATH, receipt)
        print(f"Copied and SHA-256 verified: {len(receipt_items)}")
        print(f"Copy receipt: {COPY_RECEIPT_PATH}")
    preview = mapping_preview(plan)
    write_json(MAPPING_PREVIEW_PATH, preview)
    MAPPING_PREVIEW_MD_PATH.write_text(
        render_mapping_preview_markdown(preview), encoding="utf-8"
    )
    print(f"Mapping preview additions: {preview['addition_count']}")
    print(f"Web rows after proposed sync: {preview['web_sync_preview']['proposed_web_row_count']}")
    print(f"Web missing images after proposed sync: {preview['web_sync_preview']['proposed_web_missing_image_count']}")
    print(f"Mapping remains unchanged: {MAPPING_PATH}")
    print(f"Mapping preview: {MAPPING_PREVIEW_MD_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
