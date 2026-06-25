from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DomaciLek
from .service import DEFAULT_DOMACI_LEKY_CSV, load_domaci_leky


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOWNLOADS_DIR = Path.home() / "Downloads"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "data" / "lekarna" / "photo_imports"
PHOTO_EXTENSIONS = {".heic", ".heif", ".jpeg", ".jpg", ".png", ".webp"}


@dataclass(frozen=True)
class DownloadPhotoCandidate:
    path: Path
    bytes_size: int
    modified_at: str


@dataclass(frozen=True)
class DownloadPhotoIntakeItem:
    photo: DownloadPhotoCandidate
    observed_label: str
    suggested_slug: str
    action: str
    matches: tuple[DomaciLek, ...]


def find_recent_download_photos(
    *,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    limit: int = 5,
) -> tuple[DownloadPhotoCandidate, ...]:
    downloads_dir = downloads_dir.expanduser().resolve()
    if not downloads_dir.exists():
        return ()
    candidates = [
        DownloadPhotoCandidate(
            path=path,
            bytes_size=path.stat().st_size,
            modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        )
        for path in downloads_dir.iterdir()
        if path.is_file() and path.suffix.casefold() in PHOTO_EXTENSIONS
    ]
    candidates.sort(key=lambda item: item.path.stat().st_mtime, reverse=True)
    return tuple(candidates[: max(1, limit)])


def find_download_photos_by_names(
    *,
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    names: list[str] | tuple[str, ...],
    limit: int = 10,
) -> tuple[DownloadPhotoCandidate, ...]:
    downloads_dir = downloads_dir.expanduser().resolve()
    if not downloads_dir.exists():
        return ()
    selected_names = [Path(str(name)).name for name in names if str(name).strip()]
    candidates: list[DownloadPhotoCandidate] = []
    seen: set[str] = set()
    for name in selected_names[: max(1, limit)]:
        if name in seen:
            continue
        seen.add(name)
        path = (downloads_dir / name).resolve()
        try:
            path.relative_to(downloads_dir)
        except ValueError:
            continue
        if not path.is_file() or path.suffix.casefold() not in PHOTO_EXTENSIONS:
            continue
        candidates.append(
            DownloadPhotoCandidate(
                path=path,
                bytes_size=path.stat().st_size,
                modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            )
        )
    return tuple(candidates)


def build_download_photo_intake(
    *,
    photos: tuple[DownloadPhotoCandidate, ...],
    observed_labels: dict[str, str] | None = None,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
) -> dict[str, Any]:
    observed_labels = observed_labels or {}
    records = load_domaci_leky(csv_path)
    items: list[DownloadPhotoIntakeItem] = []
    for photo in photos:
        label = observed_labels.get(photo.path.name, "").strip()
        matches = tuple(match_existing_records(label, records)) if label else ()
        if not label:
            action = "needs_label"
        elif matches:
            action = "duplicate_existing"
        else:
            action = "new_candidate"
        items.append(
            DownloadPhotoIntakeItem(
                photo=photo,
                observed_label=label,
                suggested_slug=suggest_slug(label or photo.path.stem),
                action=action,
                matches=matches,
            )
        )

    action_counts: dict[str, int] = {}
    for item in items:
        action_counts[item.action] = action_counts.get(item.action, 0) + 1

    return {
        "schema": "lekarna_download_photo_intake_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "photos": len(items),
            "action_counts": action_counts,
        },
        "items": [intake_item_to_dict(item) for item in items],
    }


def match_existing_records(label: str, records: list[DomaciLek]) -> list[DomaciLek]:
    normalized_label = normalize_for_match(label)
    if not normalized_label:
        return []
    label_tokens = token_set(normalized_label)
    matches: list[tuple[int, DomaciLek]] = []
    for record in records:
        haystack = normalize_for_match(
            " ".join([record.nazev, record.ucinna_latka, record.sila, record.forma, record.pouziti])
        )
        score = 0
        if normalized_label and normalized_label in haystack:
            score += 10
        record_tokens = token_set(haystack)
        overlap = label_tokens & record_tokens
        score += len(overlap)
        important = {token for token in label_tokens if len(token) >= 3}
        if important and len(important & record_tokens) >= min(2, len(important)):
            score += 4
        if score >= 4:
            matches.append((score, record))
    matches.sort(key=lambda item: (-item[0], normalize_for_match(item[1].nazev)))
    return [record for _score, record in matches[:5]]


def normalize_for_match(value: str) -> str:
    text = str(value or "").casefold()
    text = text.replace("µ", "u")
    text = text.replace("μ", "u")
    text = text.replace("mcg", "ug")
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def token_set(normalized_text: str) -> set[str]:
    return {token for token in normalized_text.split() if token}


def suggest_slug(value: str) -> str:
    normalized = normalize_for_match(value)
    slug = "_".join(normalized.split())
    return slug or "lekarna_fotka"


def intake_item_to_dict(item: DownloadPhotoIntakeItem) -> dict[str, Any]:
    return {
        "photo": {
            "name": item.photo.path.name,
            "path": str(item.photo.path),
            "bytes": item.photo.bytes_size,
            "modified_at": item.photo.modified_at,
        },
        "observed_label": item.observed_label,
        "suggested_slug": item.suggested_slug,
        "action": item.action,
        "matches": [
            {
                "nazev": match.nazev,
                "sila": match.sila,
                "forma": match.forma,
                "mnozstvi": match.mnozstvi,
                "umisteni": match.umisteni,
                "zdroj": match.zdroj,
                "nutno_overit": match.nutno_overit,
                "pil_status": match.PIL_Match_Status,
            }
            for match in item.matches
        ],
    }


def build_download_photo_intake_markdown(intake: dict[str, Any]) -> str:
    lines = [
        "# Lékárna - Downloads photo intake",
        "",
        f"Vygenerováno: {intake.get('generated_at', '')}",
        "",
        "## Souhrn",
        "",
        f"- Fotky: {intake.get('summary', {}).get('photos', 0)}",
    ]
    for action, count in sorted(intake.get("summary", {}).get("action_counts", {}).items()):
        lines.append(f"- {action}: {count}")
    lines.extend(
        [
            "",
            "## Doporučený postup",
            "",
            "- `duplicate_existing`: neimportovat jako nový řádek; případně později řešit jen aktualizaci fotky nebo metadat.",
            "- `new_candidate`: připravit manifest pro nový import, ale apply až po potvrzení.",
            "- `needs_label`: nejdřív přečíst obal/OCR/vision a doplnit název.",
            "",
            "## Položky",
            "",
        ]
    )
    for item in intake.get("items", []):
        photo = item.get("photo", {})
        lines.extend(
            [
                f"### {photo.get('name', '')}",
                "",
                f"- Akce: `{item.get('action', '')}`",
                f"- Přečtený název: {item.get('observed_label') or 'nezadáno'}",
                f"- Navržený slug: `{item.get('suggested_slug', '')}`",
                f"- Cesta: `{photo.get('path', '')}`",
                f"- Velikost: {photo.get('bytes', 0)} B",
                "",
            ]
        )
        matches = item.get("matches", [])
        if matches:
            lines.append("Shody v existující evidenci:")
            for match in matches:
                lines.append(
                    "- "
                    f"{match.get('nazev', '')} | {match.get('sila', '')} | "
                    f"{match.get('mnozstvi', '')} | {match.get('umisteni', '')} | "
                    f"`{match.get('zdroj', '')}`"
                )
        else:
            lines.append("Shody v existující evidenci: žádné")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def default_download_intake_report_path(report_dir: Path = DEFAULT_REPORT_DIR) -> Path:
    return report_dir / f"lekarna_download_photo_intake_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"


def write_download_photo_intake_report(intake: dict[str, Any], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_download_photo_intake_markdown(intake), encoding="utf-8")
    return report_path
