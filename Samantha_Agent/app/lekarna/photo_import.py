from __future__ import annotations

import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .service import DEFAULT_DOMACI_LEKY_CSV, FIELD_NAMES


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHOTO_DIR = PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach"
DEFAULT_IMPORT_DIR = PROJECT_ROOT / "data" / "lekarna" / "photo_imports"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "data" / "lekarna"
MANIFEST_FIELD_NAMES = (
    "include",
    "source_file",
    "new_file",
    *FIELD_NAMES,
)
PHOTO_EXTENSIONS = {".heic", ".jpg", ".jpeg", ".png", ".webp"}
SAFE_DEFAULTS = {
    "expirace": "nezjisteno",
    "umisteni": "leky v krabickach - umisteni nezadano",
    "overeno_z_letaku": "ne",
    "stav_obalu": "KRABICKA_FOTO",
    "jistota_cteni": "stredni",
    "nutno_overit": "ano",
}
APPLY_CONFIRMATION_PHRASE = "Potvrzuji import fotek lekarna"


@dataclass(frozen=True)
class PhotoImportResult:
    manifest_path: Path
    rows: int
    message: str


@dataclass(frozen=True)
class AppliedPhotoImportResult:
    csv_path: Path
    backup_path: Path
    report_path: Path
    renamed_count: int
    appended_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _PhotoImportPlan:
    row: dict[str, str]
    source_name: str
    target_name: str
    source_path: Path
    target_path: Path
    csv_source: str


def prepare_lekarna_photo_import_manifest(
    photo_dir: Path = DEFAULT_PHOTO_DIR,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    manifest_path: Path | None = None,
) -> PhotoImportResult:
    """Create a CSV manifest template for newly photographed medicine boxes."""
    photo_dir = photo_dir.resolve()
    csv_path = csv_path.resolve()
    manifest_path = manifest_path or _default_manifest_path()
    manifest_path = manifest_path.resolve()

    _ensure_within_project(photo_dir)
    _ensure_within_project(csv_path)
    _ensure_within_project(manifest_path)

    existing_sources = _load_existing_sources(csv_path)
    candidates = [
        path
        for path in sorted(photo_dir.iterdir(), key=lambda item: item.name.casefold())
        if _is_candidate_photo(path)
        and f"{photo_dir.name}/{path.name}" not in existing_sources
    ]

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELD_NAMES)
        writer.writeheader()
        for photo in candidates:
            row = {field: "" for field in MANIFEST_FIELD_NAMES}
            row.update(SAFE_DEFAULTS)
            row["include"] = "ano"
            row["source_file"] = photo.name
            row["zdroj"] = f"{photo_dir.name}/"
            row["poznamky"] = (
                "Nacteno z fotografie krabicky; pred pouzitim overit expiraci, "
                "slozeni a vhodnost podle pribalove informace nebo lekarnika."
            )
            writer.writerow(row)

    if candidates:
        message = (
            f"Manifest pripraven: {manifest_path}. "
            f"Dopln nazvy souboru a pole leku pro {len(candidates)} fotek."
        )
    else:
        message = "Nenasla jsem zadne nove fotky k importu."
    return PhotoImportResult(manifest_path=manifest_path, rows=len(candidates), message=message)


def apply_lekarna_photo_import_manifest(
    manifest_path: Path,
    photo_dir: Path = DEFAULT_PHOTO_DIR,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    report_dir: Path = DEFAULT_REPORT_DIR,
    *,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> AppliedPhotoImportResult:
    """Apply a reviewed photo import manifest: backup CSV, rename photos, append rows."""
    if not user_confirmed or APPLY_CONFIRMATION_PHRASE.casefold() not in confirmation_text.casefold():
        raise ValueError(
            "Import fotek zapisuje do CSV a prejmenovava soubory. "
            f"Vyzaduje potvrzeni: {APPLY_CONFIRMATION_PHRASE}"
        )

    manifest_path = manifest_path.resolve()
    photo_dir = photo_dir.resolve()
    csv_path = csv_path.resolve()
    report_dir = report_dir.resolve()
    _ensure_within_project(manifest_path)
    _ensure_within_project(photo_dir)
    _ensure_within_project(csv_path)
    _ensure_within_project(report_dir)

    rows = _load_manifest_rows(manifest_path)
    plans = _plan_photo_import(rows, photo_dir)
    existing_sources = _load_existing_sources(csv_path)
    backup_path = _backup_csv(csv_path)
    warnings: list[str] = []
    renamed: list[tuple[str, str]] = []
    appended_rows: list[dict[str, str]] = []

    for plan in plans:
        if plan.source_path.exists():
            plan.source_path.rename(plan.target_path)
            renamed.append((plan.source_name, plan.target_name))
        elif plan.target_path.exists():
            warnings.append(f"Fotka uz byla prejmenovana: {plan.target_name}")
        else:
            raise ValueError(f"Chybi zdrojova fotka: {plan.source_name}")

        if plan.csv_source in existing_sources:
            warnings.append(f"CSV uz obsahuje zdroj: {plan.csv_source}")
            continue

        appended_rows.append(_manifest_row_to_csv_row(plan.row, plan.csv_source))
        existing_sources.add(plan.csv_source)

    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_NAMES)
        for row in appended_rows:
            writer.writerow(row)

    report_path = _write_report(
        report_dir=report_dir,
        manifest_path=manifest_path,
        renamed=renamed,
        appended_rows=appended_rows,
        warnings=warnings,
    )
    missing_sources = validate_lekarna_photo_sources(csv_path=csv_path, photo_dir=photo_dir)
    if missing_sources:
        warnings.extend(f"Chybi zdrojova fotka v CSV: {source}" for source in missing_sources)

    return AppliedPhotoImportResult(
        csv_path=csv_path,
        backup_path=backup_path,
        report_path=report_path,
        renamed_count=len(renamed),
        appended_count=len(appended_rows),
        warnings=tuple(warnings),
    )


def validate_lekarna_photo_sources(
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    photo_dir: Path = DEFAULT_PHOTO_DIR,
) -> list[str]:
    csv_path = csv_path.resolve()
    photo_dir = photo_dir.resolve()
    _ensure_within_project(csv_path)
    _ensure_within_project(photo_dir)

    missing: list[str] = []
    photo_prefix = f"{photo_dir.name}/"
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source = (row.get("zdroj") or "").strip()
            if source.startswith(photo_prefix) and not (photo_dir / source.removeprefix(photo_prefix)).exists():
                missing.append(source)
    return missing


def format_prepare_lekarna_photo_import_manifest() -> str:
    result = prepare_lekarna_photo_import_manifest()
    lines = [
        "Lekarna photo import - priprava manifestu",
        result.message,
        "",
        "Dalsi krok:",
        "- Do manifestu doplnit `new_file`, `nazev`, `ucinna_latka`, `forma`, `sila`, `kategorie`, `pouziti`, `mnozstvi` a `poznamky`.",
        "- Nejasne polozky nechat jako `neovereno`, `jistota_cteni=nizka` a `nutno_overit=ano`.",
        "- Samotny zapis provede az potvrzeny apply krok.",
    ]
    return "\n".join(lines)


def format_apply_lekarna_photo_import_manifest(
    manifest_path: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    result = apply_lekarna_photo_import_manifest(
        manifest_path=Path(manifest_path),
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )
    lines = [
        "Lekarna photo import - hotovo",
        f"Prejmenovano fotek: {result.renamed_count}",
        f"Pridano radku do CSV: {result.appended_count}",
        f"Zaloha CSV: {result.backup_path}",
        f"Report: {result.report_path}",
    ]
    if result.warnings:
        lines.extend(["", "Upozorneni:"])
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines)


def format_validate_lekarna_photo_sources() -> str:
    missing = validate_lekarna_photo_sources()
    if not missing:
        return "Lekarna photo import validace: vsechny foto zdroje z CSV existuji."
    lines = ["Lekarna photo import validace: chybi nektere foto zdroje:"]
    lines.extend(f"- {source}" for source in missing)
    return "\n".join(lines)


def _default_manifest_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_IMPORT_DIR / f"lekarna_photo_import_manifest_{stamp}.csv"


def _load_existing_sources(csv_path: Path) -> set[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row.get("zdroj") or "").strip()
            for row in csv.DictReader(handle)
            if (row.get("zdroj") or "").strip()
        }


def _load_manifest_rows(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_fields = sorted(set(MANIFEST_FIELD_NAMES) - set(reader.fieldnames or []))
        if missing_fields:
            raise ValueError(f"Manifest nema povinna pole: {', '.join(missing_fields)}")
        rows = [
            {field: (row.get(field) or "").strip() for field in MANIFEST_FIELD_NAMES}
            for row in reader
            if _is_included(row)
        ]
    if not rows:
        raise ValueError("Manifest neobsahuje zadne radky s include=ano.")
    for index, row in enumerate(rows, start=2):
        _validate_manifest_row(row, index)
    return rows


def _validate_manifest_row(row: dict[str, str], line_number: int) -> None:
    required = ("source_file", "new_file", "nazev")
    missing = [field for field in required if not row.get(field)]
    if missing:
        raise ValueError(f"Radek {line_number}: chybi {', '.join(missing)}")
    if Path(row["new_file"]).suffix.casefold() not in PHOTO_EXTENSIONS:
        raise ValueError(f"Radek {line_number}: new_file musi byt podporovana fotka")


def _plan_photo_import(rows: list[dict[str, str]], photo_dir: Path) -> list[_PhotoImportPlan]:
    plans: list[_PhotoImportPlan] = []
    seen_sources: set[str] = set()
    seen_targets: set[str] = set()

    for index, row in enumerate(rows, start=2):
        source_name = _safe_filename(row["source_file"], "source_file")
        target_name = _safe_filename(row["new_file"], "new_file")
        source_path = photo_dir / source_name
        target_path = photo_dir / target_name

        if source_name in seen_sources:
            raise ValueError(f"Radek {index}: duplicitni source_file: {source_name}")
        if target_name in seen_targets:
            raise ValueError(f"Radek {index}: duplicitni new_file: {target_name}")
        seen_sources.add(source_name)
        seen_targets.add(target_name)

        if source_path.exists() and target_path.exists():
            raise ValueError(f"Radek {index}: cilovy soubor uz existuje: {target_name}")
        if not source_path.exists() and not target_path.exists():
            raise ValueError(f"Radek {index}: chybi zdrojova fotka: {source_name}")

        plans.append(
            _PhotoImportPlan(
                row=row,
                source_name=source_name,
                target_name=target_name,
                source_path=source_path,
                target_path=target_path,
                csv_source=f"{photo_dir.name}/{target_name}",
            )
        )

    return plans


def _manifest_row_to_csv_row(row: dict[str, str], csv_source: str) -> dict[str, str]:
    data = {field: row.get(field, "") for field in FIELD_NAMES}
    for field, value in SAFE_DEFAULTS.items():
        if not data.get(field):
            data[field] = value
    data["zdroj"] = csv_source
    data["nutno_overit"] = "ano"
    data["overeno_z_letaku"] = "ne"
    data["stav_obalu"] = data["stav_obalu"] or "KRABICKA_FOTO"
    return data


def _backup_csv(csv_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"{csv_path.stem}.backup_before_photo_import_{stamp}{csv_path.suffix}")
    shutil.copy2(csv_path, backup_path)
    return backup_path


def _write_report(
    report_dir: Path,
    manifest_path: Path,
    renamed: list[tuple[str, str]],
    appended_rows: list[dict[str, str]],
    warnings: list[str],
) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"photo_import_{stamp}.md"
    lines = [
        f"# Import fotografii leku v krabickach - {stamp}",
        "",
        f"Manifest: `{manifest_path}`",
        "",
        "Bezpecnostni pravidlo: import je inventar, ne doporuceni lecby; nove polozky zustavaji `nutno_overit=ano`, `overeno_z_letaku=ne`.",
        "",
        "## Prejmenovani",
        "",
    ]
    lines.extend(f"- `{source}` -> `{target}`" for source, target in renamed)
    lines.extend(["", "## Polozky pridane do CSV", ""])
    lines.extend(
        f"- {row.get('nazev', '')} | {row.get('sila', '')} | {row.get('zdroj', '')}"
        for row in appended_rows
    )
    if warnings:
        lines.extend(["", "## Upozorneni", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _safe_filename(value: str, field: str) -> str:
    path = Path(value)
    if not value or path.name != value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} musi byt jen nazev souboru bez cesty: {value}")
    return value


def _is_candidate_photo(path: Path) -> bool:
    return (
        path.is_file()
        and not path.name.startswith(".")
        and path.suffix.casefold() in PHOTO_EXTENSIONS
    )


def _is_included(row: dict[str, str]) -> bool:
    return (row.get("include") or "").strip().casefold() in {"ano", "yes", "true", "1"}


def _ensure_within_project(path: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Cesta musi zustat uvnitr Samantha_Agent: {path}") from exc
