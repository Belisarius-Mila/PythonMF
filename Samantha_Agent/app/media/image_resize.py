from __future__ import annotations

import math
import shutil
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET_KB = 250
LEKARNA_TARGET_KB = 100
IMAGE_RESIZE_CONFIRMATION_PHRASE = "Potvrzuji zmenseni obrazku"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
DEFAULT_BACKUP_ROOT = PROJECT_ROOT / "data" / "media" / "image_resize_backups"
PROJECT_PRESETS = {
    "lekarna": (PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach", LEKARNA_TARGET_KB),
    "lekarny": (PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach", LEKARNA_TARGET_KB),
    "leky": (PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach", LEKARNA_TARGET_KB),
    "lékárna": (PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach", LEKARNA_TARGET_KB),
    "léky": (PROJECT_ROOT / "data" / "lekarna" / "Leky_v_Krabickach", LEKARNA_TARGET_KB),
}


@dataclass(frozen=True)
class ImageResizeCandidate:
    path: Path
    relative_path: Path
    original_bytes: int
    target_bytes: int
    should_resize: bool
    reason: str


@dataclass(frozen=True)
class ImageResizeSummary:
    source_path: Path
    target_kb: int
    target_bytes: int
    total_files: int
    resize_candidates: int
    original_bytes: int
    candidate_bytes: int
    recursive: bool
    candidates: tuple[ImageResizeCandidate, ...]


@dataclass(frozen=True)
class ImageResizeResult:
    summary: ImageResizeSummary
    backup_dir: Path
    resized_count: int
    skipped_count: int
    original_bytes: int
    resized_bytes: int
    warnings: tuple[str, ...]


def preview_image_resize(
    path: Path | str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
) -> ImageResizeSummary:
    source_path, resolved_target_kb = _resolve_request(path=path, project=project, target_kb=target_kb)
    candidates = _collect_candidates(source_path=source_path, target_kb=resolved_target_kb, recursive=recursive)
    return ImageResizeSummary(
        source_path=source_path,
        target_kb=resolved_target_kb,
        target_bytes=resolved_target_kb * 1024,
        total_files=len(candidates),
        resize_candidates=sum(1 for candidate in candidates if candidate.should_resize),
        original_bytes=sum(candidate.original_bytes for candidate in candidates),
        candidate_bytes=sum(candidate.original_bytes for candidate in candidates if candidate.should_resize),
        recursive=recursive,
        candidates=tuple(candidates),
    )


def apply_image_resize(
    path: Path | str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
    *,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    backup_root: Path = DEFAULT_BACKUP_ROOT,
) -> ImageResizeResult:
    if (
        not user_confirmed
        or _normalize_confirmation(IMAGE_RESIZE_CONFIRMATION_PHRASE)
        not in _normalize_confirmation(confirmation_text)
    ):
        raise ValueError(
            "Zmenseni obrazku prepisuje soubory a vyzaduje potvrzeni: "
            f"{IMAGE_RESIZE_CONFIRMATION_PHRASE}"
        )

    summary = preview_image_resize(path=path, project=project, target_kb=target_kb, recursive=recursive)
    backup_root = backup_root.resolve()
    _ensure_within_project(backup_root)
    backup_dir = backup_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=False)

    resized_count = 0
    skipped_count = 0
    original_bytes = 0
    resized_bytes = 0
    warnings: list[str] = []

    for candidate in summary.candidates:
        if not candidate.should_resize:
            skipped_count += 1
            continue

        try:
            output = _resize_image_bytes(candidate.path, candidate.target_bytes)
        except ImageResizeDependencyError as exc:
            warnings.append(f"{candidate.relative_path}: {exc}")
            skipped_count += 1
            continue
        except Exception as exc:  # pragma: no cover - defensive boundary for corrupted images
            warnings.append(f"{candidate.relative_path}: nepodarilo se zmensit ({exc})")
            skipped_count += 1
            continue

        if len(output) >= candidate.original_bytes:
            warnings.append(f"{candidate.relative_path}: zmensena verze neni mensi nez original")
            skipped_count += 1
            continue

        backup_path = backup_dir / candidate.relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate.path, backup_path)
        candidate.path.write_bytes(output)
        resized_count += 1
        original_bytes += candidate.original_bytes
        resized_bytes += len(output)

    return ImageResizeResult(
        summary=summary,
        backup_dir=backup_dir,
        resized_count=resized_count,
        skipped_count=skipped_count,
        original_bytes=original_bytes,
        resized_bytes=resized_bytes,
        warnings=tuple(warnings),
    )


def format_preview_image_resize(
    path: str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
) -> str:
    summary = preview_image_resize(path=path, project=project, target_kb=target_kb, recursive=recursive)
    lines = [
        "Zmenseni obrazku - nahled",
        "Nic zatim neprepisuji ani nemazu.",
        "",
        f"Slozka/soubor: {summary.source_path}",
        f"Cilova velikost: cca {summary.target_kb} kB na obrazek",
        f"Rekurzivne: {_yes_no(summary.recursive)}",
        f"Nalezeno obrazku: {summary.total_files}",
        f"Kandidatu ke zmenseni: {summary.resize_candidates}",
        f"Soucasna velikost celkem: {_format_bytes(summary.original_bytes)}",
        f"Velikost kandidatu: {_format_bytes(summary.candidate_bytes)}",
        "",
    ]

    if summary.candidates:
        lines.append("Ukazka souboru:")
        for candidate in summary.candidates[:20]:
            marker = "zmensit" if candidate.should_resize else "ponechat"
            lines.append(
                f"- {candidate.relative_path} | {_format_bytes(candidate.original_bytes)} | {marker}"
            )
        if len(summary.candidates) > 20:
            lines.append(f"- ... dalsich {len(summary.candidates) - 20} souboru")
        lines.append("")

    try:
        _load_pillow()
    except ImageResizeDependencyError as exc:
        lines.extend(
            [
                "Stav zavislosti:",
                f"- {exc}",
                "- Preview funguje, ale apply bude mozne az po instalaci Pillow.",
                "",
            ]
        )

    lines.extend(
        [
            "Po potvrzeni apply krok:",
            "- zalozi zalohu originalu do `data/media/image_resize_backups/`,",
            "- prepise jen obrazky v teto slozce/souboru, ktere jsou vetsi nez cil,",
            "- nebude mazat zadne zalohy ani jine soubory.",
            "",
            f"Pro zapis posli potvrzeni obsahujici: `{IMAGE_RESIZE_CONFIRMATION_PHRASE}`",
        ]
    )
    return "\n".join(lines)


def format_apply_image_resize(
    path: str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
    *,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    result = apply_image_resize(
        path=path,
        project=project,
        target_kb=target_kb,
        recursive=recursive,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )
    saved = result.original_bytes - result.resized_bytes
    lines = [
        "Zmenseni obrazku - hotovo",
        f"Slozka/soubor: {result.summary.source_path}",
        f"Cilova velikost: cca {result.summary.target_kb} kB na obrazek",
        f"Zmenseno: {result.resized_count}",
        f"Ponechano/preskoceno: {result.skipped_count}",
        f"Zaloha originalu: {result.backup_dir}",
        f"Velikost zmensovanych originalu: {_format_bytes(result.original_bytes)}",
        f"Velikost po zmenseni: {_format_bytes(result.resized_bytes)}",
        f"Uspora: {_format_bytes(max(0, saved))}",
    ]
    if result.warnings:
        lines.append("")
        lines.append("Upozorneni:")
        lines.extend(f"- {warning}" for warning in result.warnings[:20])
        if len(result.warnings) > 20:
            lines.append(f"- ... dalsich {len(result.warnings) - 20} upozorneni")
    return "\n".join(lines)


class ImageResizeDependencyError(RuntimeError):
    pass


def _resolve_request(path: Path | str, project: str, target_kb: int) -> tuple[Path, int]:
    normalized_project = project.strip().casefold()
    source_path: Path
    preset_target = 0
    if normalized_project:
        preset = PROJECT_PRESETS.get(normalized_project)
        if preset is None:
            if not path:
                raise ValueError(
                    "Pro neznamy projekt zadej cestu ke slozce nebo souboru. "
                    "Cilova velikost je volitelna, vychozi je 250 kB."
                )
            source_path = Path(path)
        else:
            source_path, preset_target = preset
    elif path:
        source_path = Path(path)
    else:
        raise ValueError("Zadej projekt, slozku nebo soubor s obrazky.")

    source_path = source_path.resolve()
    _ensure_within_project(source_path)
    if not source_path.exists():
        raise ValueError(f"Cesta neexistuje: {source_path}")
    resolved_target_kb = target_kb or preset_target or DEFAULT_TARGET_KB
    if resolved_target_kb < 20 or resolved_target_kb > 10_000:
        raise ValueError("Cilova velikost musi byt mezi 20 kB a 10000 kB.")
    return source_path, resolved_target_kb


def _collect_candidates(source_path: Path, target_kb: int, recursive: bool) -> list[ImageResizeCandidate]:
    paths = [source_path] if source_path.is_file() else _iter_images(source_path, recursive=recursive)
    target_bytes = target_kb * 1024
    base = source_path.parent if source_path.is_file() else source_path
    candidates: list[ImageResizeCandidate] = []
    for image_path in paths:
        original_bytes = image_path.stat().st_size
        candidates.append(
            ImageResizeCandidate(
                path=image_path,
                relative_path=image_path.relative_to(base),
                original_bytes=original_bytes,
                target_bytes=target_bytes,
                should_resize=original_bytes > target_bytes,
                reason="vetsi nez cil" if original_bytes > target_bytes else "uz je mensi nebo rovno cili",
            )
        )
    return candidates


def _iter_images(source_dir: Path, recursive: bool) -> list[Path]:
    iterator = source_dir.rglob("*") if recursive else source_dir.iterdir()
    return sorted(
        (
            path
            for path in iterator
            if path.is_file()
            and path.suffix.casefold() in SUPPORTED_EXTENSIONS
            and not path.name.startswith(".")
        ),
        key=lambda item: str(item.relative_to(source_dir)).casefold(),
    )


def _resize_image_bytes(path: Path, target_bytes: int) -> bytes:
    image_module, image_ops = _load_pillow()
    try:
        register_heif = _load_pillow_heif()
        register_heif()
    except ImageResizeDependencyError:
        if path.suffix.casefold() in {".heic", ".heif"}:
            raise ImageResizeDependencyError("HEIC/HEIF vyzaduje balik pillow-heif")

    with image_module.open(path) as image:
        image = image_ops.exif_transpose(image)
        output_format = _format_for_path(path)
        image = _prepare_image_for_format(image, output_format)
        return _compress_to_target(image, output_format=output_format, target_bytes=target_bytes)


def _compress_to_target(image: Any, output_format: str, target_bytes: int) -> bytes:
    scale = 1.0
    best = b""
    current = _initial_resize_for_target(image, target_bytes=target_bytes)
    min_long_edge = 800

    for _attempt in range(6):
        candidate = _best_quality_bytes(current, output_format=output_format, target_bytes=target_bytes)
        if not best or len(candidate) < len(best):
            best = candidate
        if len(candidate) <= target_bytes:
            return candidate

        width, height = current.size
        long_edge = max(width, height)
        if long_edge <= min_long_edge:
            return candidate
        ratio = math.sqrt(target_bytes / max(1, len(candidate))) * 0.92
        scale *= min(0.88, max(0.55, ratio))
        new_width = max(1, int(image.size[0] * scale))
        new_height = max(1, int(image.size[1] * scale))
        if max(new_width, new_height) < min_long_edge:
            factor = min_long_edge / max(new_width, new_height)
            new_width = max(1, int(new_width * factor))
            new_height = max(1, int(new_height * factor))
        current = image.resize((new_width, new_height), _resampling_lanczos())

    return best


def _initial_resize_for_target(image: Any, target_bytes: int) -> Any:
    width, height = image.size
    long_edge = max(width, height)
    if target_bytes <= 120 * 1024 and long_edge > 1400:
        ratio = 1400 / long_edge
    elif target_bytes <= 300 * 1024 and long_edge > 2200:
        ratio = 2200 / long_edge
    else:
        return image
    return image.resize((max(1, int(width * ratio)), max(1, int(height * ratio))), _resampling_lanczos())


def _best_quality_bytes(image: Any, output_format: str, target_bytes: int) -> bytes:
    if output_format == "PNG":
        buffer = BytesIO()
        image.save(buffer, format=output_format, optimize=True)
        return buffer.getvalue()

    low = 35
    high = 90
    best_under = b""
    smallest = b""
    while low <= high:
        quality = (low + high) // 2
        encoded = _encode_image(image, output_format=output_format, quality=quality)
        if not smallest or len(encoded) < len(smallest):
            smallest = encoded
        if len(encoded) <= target_bytes:
            best_under = encoded
            low = quality + 1
        else:
            high = quality - 1
    return best_under or smallest


def _encode_image(image: Any, output_format: str, quality: int) -> bytes:
    buffer = BytesIO()
    save_args: dict[str, Any] = {"format": output_format, "optimize": True}
    if output_format in {"JPEG", "WEBP", "HEIF"}:
        save_args["quality"] = quality
    if output_format == "JPEG":
        save_args["progressive"] = True
    image.save(buffer, **save_args)
    return buffer.getvalue()


def _prepare_image_for_format(image: Any, output_format: str) -> Any:
    if output_format in {"JPEG", "HEIF"} and image.mode in {"RGBA", "LA", "P"}:
        background = _new_white_background(image.size)
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
        return background
    if output_format in {"JPEG", "HEIF"} and image.mode != "RGB":
        return image.convert("RGB")
    return image


def _format_for_path(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix in {".jpg", ".jpeg"}:
        return "JPEG"
    if suffix == ".png":
        return "PNG"
    if suffix == ".webp":
        return "WEBP"
    if suffix in {".heic", ".heif"}:
        return "HEIF"
    raise ValueError(f"Nepodporovana pripona obrazku: {path.suffix}")


def _new_white_background(size: tuple[int, int]) -> Any:
    image_module, _image_ops = _load_pillow()
    return image_module.new("RGB", size, (255, 255, 255))


def _resampling_lanczos() -> Any:
    image_module, _image_ops = _load_pillow()
    return image_module.Resampling.LANCZOS


def _load_pillow() -> tuple[Any, Any]:
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as exc:
        raise ImageResizeDependencyError("chybi Python balik Pillow") from exc
    return Image, ImageOps


def _load_pillow_heif() -> Any:
    try:
        from pillow_heif import register_heif_opener
    except ModuleNotFoundError as exc:
        raise ImageResizeDependencyError("chybi Python balik pillow-heif") from exc
    return register_heif_opener


def _ensure_within_project(path: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Cesta musi zustat uvnitr Samantha_Agent: {path}") from exc


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} kB"
    return f"{value / (1024 * 1024):.2f} MB"


def _yes_no(value: bool) -> str:
    return "ano" if value else "ne"


def _normalize_confirmation(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "č": "c",
            "ď": "d",
            "é": "e",
            "ě": "e",
            "í": "i",
            "ň": "n",
            "ó": "o",
            "ř": "r",
            "š": "s",
            "ť": "t",
            "ú": "u",
            "ů": "u",
            "ý": "y",
            "ž": "z",
        }
    )
    return text.casefold().translate(replacements)
