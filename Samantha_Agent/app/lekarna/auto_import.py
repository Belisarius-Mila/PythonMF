from __future__ import annotations

import csv
import os
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .download_intake import (
    DownloadPhotoCandidate,
    build_download_photo_intake,
    find_download_photos_by_names,
    find_recent_download_photos,
    match_existing_records,
    normalize_for_match,
    suggest_slug,
)
from .openai_vision import (
    DEFAULT_OPENAI_VISION_MODEL,
    analyze_lekarna_image_with_openai,
    openai_vision_label,
    openai_vision_to_inventory_suggestion,
)
from .photo_import import (
    APPLY_CONFIRMATION_PHRASE,
    DEFAULT_PHOTO_DIR,
    MANIFEST_FIELD_NAMES,
    SAFE_DEFAULTS,
    AppliedPhotoImportResult,
    apply_lekarna_photo_import_manifest,
)
from .service import DEFAULT_DOMACI_LEKY_CSV, FIELD_NAMES, load_domaci_leky
from .sukl_dlp import format_sukl_dlp_source, match_sukl_dlp
from .web_bundle import refresh_lekarna_web_bundle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_DIR = PROJECT_ROOT / "data" / "lekarna" / "photo_imports"
DEFAULT_VISION_OCR_SCRIPT = PROJECT_ROOT / "scripts" / "ocr_image_vision.swift"
DEFAULT_PHOTO_PREFIX = "Leky_v_Krabickach/"
OPENAI_DRAFT_CONFIRMATION_PHRASE = "Potvrzuji OpenAI vision draft lekarna"


@dataclass(frozen=True)
class ImageOcrResult:
    text: str
    lines: tuple[str, ...]
    method: str
    warning: str = ""
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class AutoImportDraftResult:
    manifest_path: Path
    report_path: Path
    photos: int
    new_candidates: int
    duplicate_existing: int
    needs_review: int


@dataclass(frozen=True)
class AutoImportApplyResult:
    csv_path: Path
    backup_path: Path
    report_path: Path
    copied_count: int
    renamed_count: int
    appended_count: int
    web_export_path: Path | None
    encrypted_bundle_path: Path | None
    warnings: tuple[str, ...]


def build_auto_import_draft(
    *,
    downloads_dir: Path,
    limit: int = 10,
    photo_names: list[str] | tuple[str, ...] | None = None,
    manifest_path: Path | None = None,
    report_path: Path | None = None,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    run_ocr: bool = True,
    ocr_backend: str = "macos",
    ocr_model: str = DEFAULT_OPENAI_VISION_MODEL,
    ocr_runner: Any | None = None,
    dlp_zip_path: Path | None = None,
) -> AutoImportDraftResult:
    if photo_names:
        photos = find_download_photos_by_names(downloads_dir=downloads_dir, names=photo_names, limit=limit)
    else:
        photos = find_recent_download_photos(downloads_dir=downloads_dir, limit=limit)
    records = load_domaci_leky(csv_path)
    ocr_by_name: dict[str, ImageOcrResult] = {}
    labels: dict[str, str] = {}
    for photo in photos:
        ocr = _run_ocr_backend(
            photo.path,
            run_ocr=run_ocr,
            ocr_backend=ocr_backend,
            ocr_model=ocr_model,
            ocr_runner=ocr_runner,
        )
        ocr_by_name[photo.path.name] = ocr
        suggestion = suggestion_from_ocr_result(ocr, fallback_name=photo.path.stem)
        if ocr.lines and suggestion["nazev"]:
            labels[photo.path.name] = _label_from_ocr_result(ocr, suggestion)

    intake = build_download_photo_intake(photos=photos, observed_labels=labels, csv_path=csv_path)
    manifest_rows: list[dict[str, str]] = []
    report_items: list[dict[str, Any]] = []
    for item in intake.get("items", []):
        photo_info = item.get("photo", {})
        photo_name = str(photo_info.get("name", ""))
        photo_path = Path(str(photo_info.get("path", "")))
        ocr = ocr_by_name.get(photo_name, ImageOcrResult("", (), "missing"))
        suggestion = suggestion_from_ocr_result(ocr, fallback_name=photo_path.stem)
        action = str(item.get("action", "needs_label"))
        risk = "review_required"
        if not ocr.lines:
            action = "needs_label"
        if action == "duplicate_existing":
            risk = "duplicate_skip"
        elif ocr.lines and suggestion["nazev"] and suggestion["new_file"]:
            risk = "draft_ready"

        if action == "new_candidate" and ocr.lines:
            manifest_rows.append(_manifest_row_from_suggestion(photo_name, suggestion, ocr, dlp_zip_path=dlp_zip_path))

        report_items.append(
            {
                "photo": photo_info,
                "action": action,
                "risk": risk,
                "suggestion": suggestion,
                "ocr_method": ocr.method,
                "ocr_warning": _short_warning(ocr.warning),
                "ocr_lines": list(ocr.lines[:12]),
                "metadata": ocr.metadata or {},
                "matches": item.get("matches", []),
            }
        )

    manifest_path = manifest_path or _default_manifest_path()
    report_path = report_path or _default_report_path()
    _write_manifest(manifest_path, manifest_rows)
    _write_report(report_path, intake, report_items, manifest_path)
    action_counts = _action_counts(report_items)
    return AutoImportDraftResult(
        manifest_path=manifest_path,
        report_path=report_path,
        photos=len(photos),
        new_candidates=int(action_counts.get("new_candidate", 0)),
        duplicate_existing=int(action_counts.get("duplicate_existing", 0)),
        needs_review=int(action_counts.get("needs_label", 0)),
    )


def apply_auto_import_manifest_from_downloads(
    *,
    manifest_path: Path,
    downloads_dir: Path,
    photo_dir: Path = DEFAULT_PHOTO_DIR,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    report_dir: Path | None = None,
    location: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    refresh_web: bool = True,
) -> AutoImportApplyResult:
    if not user_confirmed or APPLY_CONFIRMATION_PHRASE.casefold() not in confirmation_text.casefold():
        raise ValueError(
            "Prijeti leku na sklad zapisuje do CSV a kopiruje/prejmenovava fotku. "
            f"Vyzaduje potvrzeni: {APPLY_CONFIRMATION_PHRASE}"
        )

    manifest_path = _safe_auto_import_manifest_path(manifest_path)
    downloads_dir = downloads_dir.expanduser().resolve()
    photo_dir = photo_dir.resolve()
    if location.strip():
        _update_manifest_location(manifest_path=manifest_path, location=location)
    copied = _copy_auto_import_sources_from_downloads(
        manifest_path=manifest_path,
        downloads_dir=downloads_dir,
        photo_dir=photo_dir,
    )
    applied = apply_lekarna_photo_import_manifest(
        manifest_path=manifest_path,
        photo_dir=photo_dir,
        csv_path=csv_path,
        report_dir=report_dir or csv_path.parent,
        user_confirmed=True,
        confirmation_text=confirmation_text,
    )
    web_refresh = refresh_lekarna_web_bundle() if refresh_web else None
    return AutoImportApplyResult(
        csv_path=applied.csv_path,
        backup_path=applied.backup_path,
        report_path=applied.report_path,
        copied_count=copied,
        renamed_count=applied.renamed_count,
        appended_count=applied.appended_count,
        web_export_path=web_refresh.export_path if web_refresh else None,
        encrypted_bundle_path=web_refresh.encrypted_path if web_refresh else None,
        warnings=(*applied.warnings, *(web_refresh.warnings if web_refresh else ())),
    )


def _update_manifest_location(*, manifest_path: Path, location: str) -> None:
    clean_location = " ".join(str(location or "").strip().split())
    if not clean_location:
        return
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if "umisteni" not in fieldnames:
            raise ValueError("Manifest nema pole umisteni.")
        rows = [dict(row) for row in reader]
    for row in rows:
        if str(row.get("include", "")).strip().casefold() in {"ano", "yes", "true", "1"}:
            row["umisteni"] = clean_location
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _run_ocr_backend(
    image_path: Path,
    *,
    run_ocr: bool,
    ocr_backend: str,
    ocr_model: str,
    ocr_runner: Any | None,
) -> ImageOcrResult:
    if ocr_runner:
        return ocr_runner(image_path)
    if not run_ocr:
        return ImageOcrResult("", (), "disabled")
    normalized_backend = ocr_backend.strip().casefold()
    if normalized_backend == "openai":
        openai_result = analyze_image_with_openai_vision(image_path, model=ocr_model)
        if openai_result.lines or openai_result.method != "openai-vision-failed":
            return openai_result
        fallback = ocr_image_with_macos_vision(image_path)
        if not fallback.lines:
            return openai_result
        warning_parts = [
            f"OpenAI Vision selhalo: {_short_warning(openai_result.warning)}",
            "pouzit macOS Vision fallback",
        ]
        if fallback.warning:
            warning_parts.append(f"fallback upozorneni: {_short_warning(fallback.warning)}")
        return ImageOcrResult(
            text=fallback.text,
            lines=fallback.lines,
            method="macos-vision-fallback-after-openai-failed",
            warning="; ".join(part for part in warning_parts if part),
            metadata=fallback.metadata,
        )
    return ocr_image_with_macos_vision(image_path)


def _safe_auto_import_manifest_path(manifest_path: Path) -> Path:
    resolved_manifest = manifest_path.expanduser().resolve()
    resolved_dir = DEFAULT_MANIFEST_DIR.resolve()
    try:
        resolved_manifest.relative_to(resolved_dir)
    except ValueError as exc:
        raise ValueError("Manifest musi byt v lekarna photo_imports slozce.") from exc
    if not resolved_manifest.name.startswith("lekarna_auto_import_manifest_") or resolved_manifest.suffix != ".csv":
        raise ValueError("Manifest nevypada jako automaticky lekarna import manifest.")
    if not resolved_manifest.exists():
        raise ValueError(f"Manifest neexistuje: {resolved_manifest}")
    return resolved_manifest


def _copy_auto_import_sources_from_downloads(
    *,
    manifest_path: Path,
    downloads_dir: Path,
    photo_dir: Path,
) -> int:
    if not downloads_dir.exists():
        raise ValueError(f"Downloads slozka neexistuje: {downloads_dir}")
    photo_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_fields = sorted({"include", "source_file", "new_file"} - set(reader.fieldnames or []))
        if missing_fields:
            raise ValueError(f"Manifest nema povinna pole: {', '.join(missing_fields)}")
        for row in reader:
            if str(row.get("include", "")).strip().casefold() not in {"ano", "yes", "true", "1"}:
                continue
            source_name = _safe_manifest_filename(str(row.get("source_file", "")), "source_file")
            target_name = _safe_manifest_filename(str(row.get("new_file", "")), "new_file")
            staged_source = photo_dir / source_name
            staged_target = photo_dir / target_name
            if staged_source.exists() or staged_target.exists():
                continue
            downloads_source = (downloads_dir / source_name).resolve()
            try:
                downloads_source.relative_to(downloads_dir)
            except ValueError as exc:
                raise ValueError(f"Zdrojova fotka neni v Downloads: {source_name}") from exc
            if not downloads_source.is_file():
                raise ValueError(f"Chybi zdrojova fotka v Downloads: {source_name}")
            shutil.copy2(downloads_source, staged_source)
            copied += 1
    return copied


def _safe_manifest_filename(value: str, field: str) -> str:
    path = Path(value.strip())
    if not value.strip() or path.name != value.strip() or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} musi byt jen nazev souboru bez cesty: {value}")
    return value.strip()


def analyze_image_with_openai_vision(
    image_path: Path,
    *,
    model: str = DEFAULT_OPENAI_VISION_MODEL,
) -> ImageOcrResult:
    try:
        result = analyze_lekarna_image_with_openai(image_path=image_path, model=model)
    except Exception as exc:
        return ImageOcrResult("", (), "openai-vision-failed", str(exc))
    visible_text = tuple(str(line).strip() for line in result.get("visible_text", []) if str(line).strip())
    label = openai_vision_label(result)
    lines = visible_text or tuple(part for part in (label, result.get("strength", ""), result.get("quantity", "")) if str(part).strip())
    return ImageOcrResult(
        text="\n".join(str(line) for line in lines),
        lines=tuple(str(line) for line in lines),
        method="openai-vision",
        metadata=result,
    )


def suggestion_from_ocr_result(ocr: ImageOcrResult, *, fallback_name: str = "") -> dict[str, str]:
    if ocr.metadata:
        return openai_vision_to_inventory_suggestion(ocr.metadata)
    return suggest_metadata_from_ocr(ocr.lines, fallback_name=fallback_name)


def _label_from_ocr_result(ocr: ImageOcrResult, suggestion: dict[str, str]) -> str:
    if ocr.metadata:
        return openai_vision_label(ocr.metadata)
    return suggestion["nazev"]


def ocr_image_with_macos_vision(
    image_path: Path,
    *,
    script_path: Path = DEFAULT_VISION_OCR_SCRIPT,
    timeout_seconds: int = 30,
) -> ImageOcrResult:
    if not script_path.exists():
        return ImageOcrResult("", (), "macos-vision-unavailable", "OCR helper script missing.")
    try:
        env = os.environ.copy()
        env.setdefault("CLANG_MODULE_CACHE_PATH", "/private/tmp/samantha_swift_module_cache")
        completed = subprocess.run(
            ["/usr/bin/swift", str(script_path), str(image_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ImageOcrResult("", (), "macos-vision-failed", str(exc))
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return ImageOcrResult("", (), "macos-vision-failed", "OCR returned invalid JSON.")
    if completed.returncode != 0 or payload.get("error"):
        return ImageOcrResult("", (), "macos-vision-failed", str(payload.get("error") or completed.stderr).strip())
    lines = tuple(str(line).strip() for line in payload.get("lines", []) if str(line).strip())
    return ImageOcrResult(text="\n".join(lines), lines=lines, method="macos-vision")


def suggest_metadata_from_ocr(lines: tuple[str, ...], *, fallback_name: str = "") -> dict[str, str]:
    clean_lines = [_clean_ocr_line(line) for line in lines if _clean_ocr_line(line)]
    joined = " ".join(clean_lines)
    name = _guess_name(clean_lines) or fallback_name.replace("_", " ")
    strength = _guess_strength(joined)
    count = _guess_count(joined)
    form = _guess_form(joined)
    normalized_name = name.strip()
    slug_source = " ".join(value for value in (normalized_name, strength, form, count) if value)
    new_file = f"{suggest_slug(slug_source)}.jpg" if slug_source.strip() else ""
    category = _guess_category(joined)
    return {
        "nazev": normalized_name,
        "ucinna_latka": "",
        "forma": form,
        "sila": strength,
        "kategorie": category,
        "pouziti": "",
        "pro_koho": "",
        "nevhodne_pro_koho": "",
        "expirace": "nezjisteno",
        "mnozstvi": count,
        "umisteni": "leky v krabickach - umisteni nezadano",
        "new_file": new_file,
        "Search_Tags": "",
    }


def _manifest_row_from_suggestion(
    source_file: str,
    suggestion: dict[str, str],
    ocr: ImageOcrResult,
    *,
    dlp_zip_path: Path | None = None,
) -> dict[str, str]:
    row = {field: "" for field in MANIFEST_FIELD_NAMES}
    row.update(SAFE_DEFAULTS)
    row.update({field: suggestion.get(field, "") for field in FIELD_NAMES if field in suggestion})
    pil_defaults = _pil_defaults_from_suggestion(suggestion, ocr, dlp_zip_path=dlp_zip_path)
    for field, value in pil_defaults.items():
        if field in row and not row.get(field):
            row[field] = value
    row["include"] = "ano"
    row["source_file"] = source_file
    row["new_file"] = suggestion.get("new_file", "")
    row["zdroj"] = DEFAULT_PHOTO_PREFIX
    row["jistota_cteni"] = "stredni" if ocr.lines else "nizka"
    row["nutno_overit"] = "ano"
    row["PIL_Match_Status"] = row.get("PIL_Match_Status") or "nedohledano"
    row["poznamky"] = (
        "Automaticky navrh z fotografie krabicky; pred importem zkontrolovat OCR, "
        "nazev, silu, mnozstvi, umisteni a zdroj informaci."
    )
    if ocr.warning:
        row["poznamky"] = f"{row['poznamky']} OCR upozorneni: {_short_warning(ocr.warning)}"
    return row


def _pil_defaults_from_suggestion(
    suggestion: dict[str, str],
    ocr: ImageOcrResult,
    *,
    dlp_zip_path: Path | None = None,
) -> dict[str, str]:
    name = str(suggestion.get("nazev", "") or "").strip()
    normalized_name = normalize_for_match(name)
    dlp_match = match_sukl_dlp(suggestion, ocr_text=ocr.text, dlp_zip_path=dlp_zip_path)
    if "sinupret" in normalized_name:
        defaults = {
            "PIL_Short": (
                "Rostlinny lecivy pripravek pro dospele k lecbe akutnich nekomplikovanych zanetu "
                "vedlejsich nosnich dutin s priznaky jako ryma, ucpany nos, bolest hlavy, bolest "
                "tvare nebo tlak v obliceji. Neuzivat pri alergii na slozky pripravku nebo pri "
                "zaludecnim/dvanactnikovem vredu; pri tehotenstvi, kojeni, citlivem zaludku, "
                "zavaznych priznacich nebo potizich trvajicich ci horsicich se 7-14 dni overit "
                "lekare/lekarnika a ridit se pribalovou informaci."
            ),
            "PIL_Source": "PIL Sinupret akut obalene tablety, sp.zn. sukls158429/2025; overit aktualni pribalovou informaci.",
            "PIL_Checked_Date": datetime.now().strftime("%Y-%m-%d"),
            "PIL_Match_Status": "pravdepodobne_sparovano_pil_z_fotky",
        }
        if dlp_match:
            defaults["PIL_Source"] = format_sukl_dlp_source(dlp_match)
            defaults["PIL_Match_Status"] = dlp_match.match_status
        return defaults

    use = str(suggestion.get("pouziti", "") or "").strip()
    form = str(suggestion.get("forma", "") or "").strip()
    quantity = str(suggestion.get("mnozstvi", "") or "").strip()
    visible = ", ".join(value for value in (name, form, quantity) if value)
    if not visible:
        visible = "novy pripravek z fotografie"
    use_text = f" Viditelny/odhadnuty ucel: {use}." if use else ""
    defaults = {
        "PIL_Short": (
            f"Automaticky inventarni zaznam z fotografie: {visible}.{use_text} "
            "Nejde o plne overeny vytah z pribalove informace; pred pouzitim fyzicky overit "
            "obal, expiraci, slozeni, vhodnost a pribalovou informaci nebo lekarnika/lekare."
        ),
        "PIL_Source": f"Fotografie obalu ({ocr.method}); PIL zatim nedohledan.",
        "PIL_Checked_Date": datetime.now().strftime("%Y-%m-%d"),
        "PIL_Match_Status": "ceka_na_pil_overeni",
    }
    if dlp_match:
        defaults["PIL_Source"] = format_sukl_dlp_source(dlp_match)
        defaults["PIL_Match_Status"] = dlp_match.match_status
    return defaults


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, intake: dict[str, Any], items: list[dict[str, Any]], manifest_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Lékárna - automatický návrh importu",
        "",
        f"Vygenerováno: {datetime.now(timezone.utc).isoformat()}",
        f"Manifest: `{manifest_path}`",
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
            "## Bezpečnost",
            "",
            "- Report ani manifest nic nezapisují do hlavní evidence.",
            "- `duplicate_existing` neimportovat jako nový lék.",
            "- `new_candidate` je jen návrh; finální import vyžaduje ruční potvrzení.",
            "- U léků nepřebírat dávkování z OCR ani z neoficiálních webů.",
            "",
            "## Položky",
            "",
        ]
    )
    for item in items:
        photo = item["photo"]
        suggestion = item["suggestion"]
        lines.extend(
            [
                f"### {photo.get('name', '')}",
                "",
                f"- Akce: `{item['action']}`",
                f"- Riziko/stav: `{item['risk']}`",
                f"- Návrh názvu: {suggestion.get('nazev', '') or 'nezjištěno'}",
                f"- Návrh souboru: `{suggestion.get('new_file', '')}`",
                f"- Síla / forma / množství: {suggestion.get('sila', '')} | {suggestion.get('forma', '')} | {suggestion.get('mnozstvi', '')}",
                f"- OCR: {item['ocr_method']}{' - ' + item['ocr_warning'] if item['ocr_warning'] else ''}",
                "",
            ]
        )
        metadata = item.get("metadata", {})
        if metadata:
            lines.extend(
                [
                    f"- Typ podle vision: `{metadata.get('product_type', '')}`",
                    f"- Confidence: {metadata.get('confidence', '')}",
                ]
            )
            uncertainties = metadata.get("uncertainties", [])
            if uncertainties:
                lines.append("- Nejistoty: " + "; ".join(str(value) for value in uncertainties))
            lines.append("")
        if item["matches"]:
            lines.append("Shody v existující evidenci:")
            for match in item["matches"]:
                lines.append(f"- {match.get('nazev', '')} | {match.get('sila', '')} | `{match.get('zdroj', '')}`")
            lines.append("")
        if item["ocr_lines"]:
            lines.append("OCR ukázka:")
            for line in item["ocr_lines"]:
                lines.append(f"- {line}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _action_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        action = str(item.get("action", "needs_label"))
        counts[action] = counts.get(action, 0) + 1
    return counts


def _guess_name(lines: list[str]) -> str:
    ignored = {"tablety", "tablet", "capsules", "tobolky", "doplněk stravy", "doplnok stravy"}
    ignored_normalized = {normalize_for_match(value) for value in ignored}
    candidates: list[str] = []
    for line in lines[:10]:
        normalized = normalize_for_match(line)
        if not normalized or normalized in ignored_normalized:
            continue
        if re.fullmatch(r"[\d\s.,xX+-]+", line):
            continue
        if any(unit in normalized.split() for unit in ("mg", "mcg", "ug", "ml", "tbl")) and len(line.split()) <= 3:
            continue
        if _guess_count(line) and len(line.split()) <= 3:
            continue
        candidates.append(line)
    if not candidates:
        return ""
    return " ".join(candidates[:2])[:120].strip()


def _guess_strength(text: str) -> str:
    match = re.search(r"\b(\d+(?:[,.]\d+)?)\s*(mg|mcg|µg|ug|g|ml|iu|i\.u\.)\b", text, flags=re.IGNORECASE)
    if not match:
        return ""
    amount = match.group(1).replace(",", ".")
    unit = match.group(2).replace("µ", "u")
    return f"{amount} {unit}"


def _guess_count(text: str) -> str:
    match = re.search(r"\b(\d+)\s*(tablet|tablety|tbl|tobolek|tobolky|capsules|kapsli|pastilek|sáčků|sacku)\b", text, flags=re.IGNORECASE)
    if not match:
        return ""
    unit = match.group(2).casefold()
    if unit in {"tablet", "tablety", "tbl"}:
        unit = "tablet"
    return f"{match.group(1)} {unit}"


def _guess_form(text: str) -> str:
    normalized = normalize_for_match(text)
    for token, form in (
        ("tablety", "tablety"),
        ("tablet", "tablety"),
        ("tbl", "tablety"),
        ("capsules", "tobolky"),
        ("tobolky", "tobolky"),
        ("sirup", "sirup"),
        ("sprej", "sprej"),
        ("mast", "mast"),
        ("gel", "gel"),
        ("kapky", "kapky"),
    ):
        if token in normalized.split():
            return form
    return ""


def _guess_category(text: str) -> str:
    normalized = normalize_for_match(text)
    if any(token in normalized for token in ("vitamin", "zinek", "selen", "magnesium", "horcik")):
        return "vitaminy_mineraly_doplnky"
    return "nezarazeno"


def _clean_ocr_line(line: str) -> str:
    return re.sub(r"\s+", " ", str(line or "").strip())


def _short_warning(value: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _default_manifest_path() -> Path:
    return DEFAULT_MANIFEST_DIR / f"lekarna_auto_import_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


def _default_report_path() -> Path:
    return DEFAULT_MANIFEST_DIR / f"lekarna_auto_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
