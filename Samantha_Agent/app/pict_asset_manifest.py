from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PICT_DIR = PROJECT_ROOT / "Pict"
DEFAULT_MAPPING_PATH = DEFAULT_PICT_DIR / "mapping.json"
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "Samantha_Agent" / "data" / "private" / "knowledge_inbox" / "processed"
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
LANGUAGE_COLUMNS = ("FR", "IT", "EN", "ES", "LA")
DEFAULT_VOCABULARY_PATHS = (
    PROJECT_ROOT / "VocabularyFR" / "VocabularyFR.csv",
    PROJECT_ROOT / "VocabularyIT" / "VocabularyIT.csv",
    PROJECT_ROOT / "VocabularyEN" / "VocabularyEN.csv",
    PROJECT_ROOT / "VocabularyES" / "VocabularyES.csv",
    PROJECT_ROOT / "VocabularyLA" / "VocabularyLA.csv",
)


@dataclass(frozen=True)
class VocabularyRow:
    language: str
    source_word: str
    cz: str
    path: str
    row_number: int


def normalize_czech_key(text: str) -> str:
    """Normalize a Czech vocabulary label for matching, not for display."""
    value = str(text or "").casefold().strip()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\[[^]]*\]", " ", value)
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def normalized_czech_aliases(text: str) -> list[str]:
    """Return normalized full key plus simple alternatives from multi-meaning cells."""
    raw = str(text or "").strip()
    without_notes = re.sub(r"\([^)]*\)", " ", raw)
    without_notes = re.sub(r"\[[^]]*\]", " ", without_notes)
    candidates = [raw]
    candidates.extend(re.split(r"\s*(?:[,;/|]|\bnebo\b)\s*", without_notes, flags=re.IGNORECASE))

    aliases: list[str] = []
    for candidate in candidates:
        normalized = normalize_czech_key(candidate)
        if normalized and normalized not in aliases:
            aliases.append(normalized)
    return aliases


def normalize_asset_stem(text: str) -> str:
    value = str(text or "").casefold().strip()
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def load_mapping(mapping_path: Path = DEFAULT_MAPPING_PATH) -> dict[str, str]:
    raw = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mapping must be a JSON object: {mapping_path}")
    return {str(key): str(value) for key, value in raw.items()}


def list_image_files(pict_dir: Path = DEFAULT_PICT_DIR) -> dict[str, list[str]]:
    files: dict[str, list[str]] = defaultdict(list)
    if not pict_dir.exists():
        return {}
    for path in sorted(pict_dir.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS:
            files[normalize_asset_stem(path.stem)].append(path.name)
    return dict(files)


def read_vocabulary_rows(paths: tuple[Path, ...] = DEFAULT_VOCABULARY_PATHS) -> list[VocabularyRow]:
    rows: list[VocabularyRow] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "CZ" not in reader.fieldnames:
                continue
            language = vocabulary_language(path, reader.fieldnames)
            source_column = language if language in reader.fieldnames else first_language_column(reader.fieldnames)
            for row_number, row in enumerate(reader, start=2):
                cz = (row.get("CZ") or "").strip()
                source_word = (row.get(source_column) or "").strip() if source_column else ""
                if cz:
                    rows.append(
                        VocabularyRow(
                            language=language.lower(),
                            source_word=source_word,
                            cz=cz,
                            path=display_path(path),
                            row_number=row_number,
                        )
                    )
    return rows


def vocabulary_language(path: Path, fieldnames: list[str]) -> str:
    for column in LANGUAGE_COLUMNS:
        if column in fieldnames:
            return column
    match = re.search(r"Vocabulary([A-Z]{2})", str(path))
    return match.group(1) if match else "unknown"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def first_language_column(fieldnames: list[str]) -> str:
    for column in LANGUAGE_COLUMNS:
        if column in fieldnames:
            return column
    return ""


def build_asset_manifest_preview(
    *,
    mapping_path: Path = DEFAULT_MAPPING_PATH,
    pict_dir: Path = DEFAULT_PICT_DIR,
    vocabulary_paths: tuple[Path, ...] = DEFAULT_VOCABULARY_PATHS,
) -> dict[str, Any]:
    mapping = load_mapping(mapping_path)
    image_files = list_image_files(pict_dir)
    vocabulary_rows = read_vocabulary_rows(vocabulary_paths)

    assets: dict[str, dict[str, Any]] = {}
    normalized_mapping: dict[str, set[str]] = defaultdict(set)
    mapping_values_by_stem: dict[str, set[str]] = defaultdict(set)

    for raw_key, raw_value in mapping.items():
        asset_id = normalize_asset_stem(raw_value)
        if not asset_id:
            continue
        for alias in normalized_czech_aliases(raw_key):
            normalized_mapping[alias].add(asset_id)
        mapping_values_by_stem[asset_id].add(raw_value)
        asset = assets.setdefault(
            asset_id,
            {
                "filename": choose_filename(asset_id, image_files),
                "status": "approved" if asset_id in image_files else "missing_file",
                "kind": "vocabulary_image",
                "canonical_label_en": raw_value,
                "canonical_label_cs": raw_key,
                "allowed_cs_keys": [],
                "normalized_cs_keys": [],
                "languages": [],
                "source": "existing_mapping",
                "style": "unknown_existing",
                "constraints": {
                    "no_text_in_image": True,
                    "max_size_kb": 300,
                    "preferred_format": "webp",
                },
                "usage_count": 0,
                "examples": [],
            },
        )
        append_unique(asset["allowed_cs_keys"], raw_key)
        for alias in normalized_czech_aliases(raw_key):
            append_unique(asset["normalized_cs_keys"], alias)

    unmatched_vocabulary: list[dict[str, Any]] = []
    duplicate_mapping_keys: list[dict[str, Any]] = []
    alias_matched_rows = 0
    for row in vocabulary_rows:
        normalized = normalize_czech_key(row.cz)
        aliases = normalized_czech_aliases(row.cz)
        matched_by_alias = {
            alias: sorted(normalized_mapping.get(alias, set()))
            for alias in aliases
            if normalized_mapping.get(alias)
        }
        asset_ids = sorted({asset_id for ids in matched_by_alias.values() for asset_id in ids})
        if not asset_ids:
            unmatched_vocabulary.append(vocabulary_row_dict(row, normalized, aliases=aliases))
            continue
        if normalized not in matched_by_alias:
            alias_matched_rows += 1
        if len(asset_ids) > 1:
            duplicate_mapping_keys.append(
                {
                    "normalized_cz_key": normalized,
                    "matched_aliases": matched_by_alias,
                    "asset_ids": asset_ids,
                    "example": vocabulary_row_dict(row, normalized, aliases=aliases),
                }
            )
        for asset_id in asset_ids:
            asset = assets.get(asset_id)
            if not asset:
                continue
            append_unique(asset["languages"], row.language)
            asset["usage_count"] += 1
            if len(asset["examples"]) < 8:
                asset["examples"].append(
                    {
                        "language": row.language,
                        "source_word": row.source_word,
                        "cz": row.cz,
                        "matched_aliases": sorted(
                            alias for alias, ids in matched_by_alias.items() if asset_id in ids
                        ),
                        "path": row.path,
                        "row_number": row.row_number,
                    }
                )

    for asset in assets.values():
        asset["allowed_cs_keys"].sort(key=str.casefold)
        asset["normalized_cs_keys"].sort()
        asset["languages"].sort()

    mapping_values_without_file = [
        {
            "asset_id": asset_id,
            "mapping_values": sorted(values, key=str.casefold),
            "allowed_cs_keys": assets[asset_id]["allowed_cs_keys"],
        }
        for asset_id, values in sorted(mapping_values_by_stem.items())
        if asset_id not in image_files
    ]
    image_files_without_mapping = [
        {"asset_id": asset_id, "filenames": filenames}
        for asset_id, filenames in sorted(image_files.items())
        if asset_id not in assets
    ]

    language_counter = Counter(row.language for row in vocabulary_rows)
    status_counter = Counter(asset["status"] for asset in assets.values())

    return {
        "schema": "pict_asset_manifest_preview_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "mapping_path": str(mapping_path),
            "pict_dir": str(pict_dir),
            "vocabulary_paths": [str(path) for path in vocabulary_paths if path.exists()],
        },
        "summary": {
            "mapping_entries": len(mapping),
            "asset_entries": len(assets),
            "image_file_stems": len(image_files),
            "image_files": sum(len(names) for names in image_files.values()),
            "vocabulary_rows": len(vocabulary_rows),
            "vocabulary_rows_by_language": dict(sorted(language_counter.items())),
            "asset_status_counts": dict(sorted(status_counter.items())),
            "mapping_values_without_file": len(mapping_values_without_file),
            "image_files_without_mapping": len(image_files_without_mapping),
            "unmatched_vocabulary_rows": len(unmatched_vocabulary),
            "alias_matched_vocabulary_rows": alias_matched_rows,
            "duplicate_normalized_mapping_keys": len(duplicate_mapping_keys),
        },
        "assets": dict(sorted(assets.items())),
        "issues": {
            "mapping_values_without_file": mapping_values_without_file,
            "image_files_without_mapping": image_files_without_mapping,
            "unmatched_vocabulary_rows_sample": unmatched_vocabulary[:200],
            "duplicate_normalized_mapping_keys_sample": duplicate_mapping_keys[:200],
        },
    }


def choose_filename(asset_id: str, image_files: dict[str, list[str]]) -> str:
    names = image_files.get(asset_id, [])
    if not names:
        return f"{asset_id}.webp"
    return sorted(names, key=filename_preference)[0]


def filename_preference(name: str) -> tuple[int, str]:
    suffix = Path(name).suffix.casefold()
    order = {".webp": 0, ".png": 1, ".jpg": 2, ".jpeg": 3, ".gif": 4}
    return (order.get(suffix, 9), name.casefold())


def append_unique(items: list[str], value: str) -> None:
    clean = str(value or "").strip()
    if clean and clean not in items:
        items.append(clean)


def vocabulary_row_dict(row: VocabularyRow, normalized: str, *, aliases: list[str] | None = None) -> dict[str, Any]:
    item = {
        "language": row.language,
        "source_word": row.source_word,
        "cz": row.cz,
        "normalized_cz_key": normalized,
        "path": row.path,
        "row_number": row.row_number,
    }
    if aliases is not None:
        item["normalized_aliases"] = aliases
    return item


def default_preview_output_path(processed_dir: Path = DEFAULT_PROCESSED_DIR) -> Path:
    stamp = datetime.now().strftime("%Y_%m_%d")
    return processed_dir / f"pict_asset_manifest_preview_{stamp}.json"


def default_review_output_path(processed_dir: Path = DEFAULT_PROCESSED_DIR) -> Path:
    stamp = datetime.now().strftime("%Y_%m_%d")
    return processed_dir / f"pict_asset_manifest_review_{stamp}.md"


def write_manifest_preview(preview: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_manifest_review(preview: dict[str, Any], output_path: Path, *, max_rows: int = 200) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_manifest_review_markdown(preview, max_rows=max_rows), encoding="utf-8")
    return output_path


def build_manifest_review_markdown(preview: dict[str, Any], *, max_rows: int = 200) -> str:
    summary = preview.get("summary", {})
    issues = preview.get("issues", {})
    source = preview.get("source", {})

    lines = [
        "# Pict asset manifest review",
        "",
        f"Vygenerováno: {preview.get('generated_at', '')}",
        "",
        "## Zdroj",
        "",
        f"- Mapping: `{source.get('mapping_path', '')}`",
        f"- Pict dir: `{source.get('pict_dir', '')}`",
        f"- Slovníkové soubory: {len(source.get('vocabulary_paths', []))}",
        "",
        "## Souhrn",
        "",
        markdown_table(
            ["Metrika", "Hodnota"],
            [
                ["Položky v mappingu", summary.get("mapping_entries", 0)],
                ["Asset položky", summary.get("asset_entries", 0)],
                ["Obrazové soubory", summary.get("image_files", 0)],
                ["Slovníkové řádky", summary.get("vocabulary_rows", 0)],
                ["Schválené assety", summary.get("asset_status_counts", {}).get("approved", 0)],
                ["Mapping ukazuje na chybějící soubor", summary.get("mapping_values_without_file", 0)],
                ["Obrázky bez mappingu", summary.get("image_files_without_mapping", 0)],
                ["Slovníkové řádky bez shody", summary.get("unmatched_vocabulary_rows", 0)],
                ["Řádky nalezené přes alias", summary.get("alias_matched_vocabulary_rows", 0)],
                ["Nejednoznačné řádky", summary.get("duplicate_normalized_mapping_keys", 0)],
            ],
        ),
        "",
        "## Doporučený postup",
        "",
        "1. Nejdřív opravit chybějící mapované soubory; to jsou přímé rozbité vazby z mappingu na obrázky.",
        "2. Nejednoznačné řádky projít ručně dřív, než se z aliasů udělají skutečné změny mappingu.",
        "3. Řádky bez shody brát jako kandidáty na novou mapping položku nebo nový obrázek.",
        "4. Tento report je jen read-only podklad; `Pict/mapping.json` neměnit bez samostatného potvrzeného apply kroku.",
        "",
    ]

    missing_files = issues.get("mapping_values_without_file", [])[:max_rows]
    lines.extend(
        [
            "## Chybějící mapované soubory",
            "",
            markdown_table(
                ["Asset ID", "Hodnoty v mappingu", "Povolené české klíče"],
                [
                    [
                        item.get("asset_id", ""),
                        ", ".join(item.get("mapping_values", [])),
                        ", ".join(item.get("allowed_cs_keys", [])),
                    ]
                    for item in missing_files
                ],
            )
            if missing_files
            else "Žádné chybějící mapované soubory.",
            "",
        ]
    )

    unused_files = issues.get("image_files_without_mapping", [])[:max_rows]
    lines.extend(
        [
            "## Obrázky bez mappingu",
            "",
            markdown_table(
                ["Asset ID", "Soubory"],
                [[item.get("asset_id", ""), ", ".join(item.get("filenames", []))] for item in unused_files],
            )
            if unused_files
            else "Žádné obrázky bez mappingu.",
            "",
        ]
    )

    unmatched = issues.get("unmatched_vocabulary_rows_sample", [])[:max_rows]
    lines.extend(
        [
            "## Slovníkové řádky bez shody",
            "",
            markdown_table(
                ["Jazyk", "Slovo", "CZ", "Alias klíče", "Soubor", "Řádek"],
                [
                    [
                        item.get("language", ""),
                        item.get("source_word", ""),
                        item.get("cz", ""),
                        ", ".join(item.get("normalized_aliases", [])),
                        item.get("path", ""),
                        item.get("row_number", ""),
                    ]
                    for item in unmatched
                ],
            )
            if unmatched
            else "Žádné slovníkové řádky bez shody.",
            "",
        ]
    )

    ambiguous = issues.get("duplicate_normalized_mapping_keys_sample", [])[:max_rows]
    lines.extend(
        [
            "## Nejednoznačné mapping řádky",
            "",
            markdown_table(
                ["Jazyk", "Slovo", "CZ", "Nalezené aliasy", "Kandidátní asset ID", "Soubor", "Řádek"],
                [
                    [
                        item.get("example", {}).get("language", ""),
                        item.get("example", {}).get("source_word", ""),
                        item.get("example", {}).get("cz", ""),
                        format_matched_aliases(item.get("matched_aliases", {})),
                        ", ".join(item.get("asset_ids", [])),
                        item.get("example", {}).get("path", ""),
                        item.get("example", {}).get("row_number", ""),
                    ]
                    for item in ambiguous
                ],
            )
            if ambiguous
            else "Žádné nejednoznačné mapping řádky.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def format_matched_aliases(matched_aliases: dict[str, list[str]]) -> str:
    parts = []
    for alias, asset_ids in sorted(matched_aliases.items()):
        parts.append(f"{alias} -> {', '.join(asset_ids)}")
    return "; ".join(parts)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    output = [
        "| " + " | ".join(markdown_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")
    return "\n".join(output)


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()
