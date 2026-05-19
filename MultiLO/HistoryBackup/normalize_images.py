"""Normalize MultiLO images into a runtime-friendly asset tree.

Rules:
- Keep original source images untouched under `Foto/`.
- Write normalized copies to `Foto_normalized/`.
- `Months` keeps original resolution and format.
- Other folders are converted to 400x400 JPEG using contain+padding.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import csv
import shutil

from PIL import Image, ImageOps


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "Foto"
DST_DIR = BASE_DIR / "Foto_normalized"
REPORT_PATH = BASE_DIR / "normalization_report.csv"

MONTHS_DIR_NAME = "Months"
TARGET_SIZE = (400, 400)
CANVAS_COLOR = (238, 238, 238)  # neutral light gray
JPEG_QUALITY = 90


@dataclass(frozen=True)
class ReportRow:
    src_rel: str
    dst_rel: str
    action: str
    src_size: str
    dst_size: str


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _open_image(path: Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return img


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGB",):
        return img
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, CANVAS_COLOR)
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def _normalize_square(src: Path, dst: Path) -> tuple[tuple[int, int], tuple[int, int]]:
    with _open_image(src) as img:
        src_size = img.size
        img = _to_rgb(img)
        fitted = ImageOps.contain(img, TARGET_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", TARGET_SIZE, CANVAS_COLOR)
        x = (TARGET_SIZE[0] - fitted.size[0]) // 2
        y = (TARGET_SIZE[1] - fitted.size[1]) // 2
        canvas.paste(fitted, (x, y))
        dst.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(dst, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return src_size, canvas.size


def _copy_original(src: Path, dst: Path) -> tuple[tuple[int, int], tuple[int, int]]:
    with _open_image(src) as img:
        size = img.size
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return size, size


def main() -> int:
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Source folder not found: {SRC_DIR}")

    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)
    DST_DIR.mkdir(parents=True, exist_ok=True)

    report: list[ReportRow] = []

    for src in sorted(SRC_DIR.rglob("*")):
        if not src.is_file() or not _is_image(src):
            continue
        rel = src.relative_to(SRC_DIR)
        folder = rel.parts[0] if rel.parts else ""

        if folder == MONTHS_DIR_NAME:
            dst = DST_DIR / rel
            src_size, dst_size = _copy_original(src, dst)
            action = "copy_original_months"
        else:
            dst = (DST_DIR / rel).with_suffix(".jpg")
            dst = dst.with_name(dst.stem.lower() + ".jpg")
            src_size, dst_size = _normalize_square(src, dst)
            action = "normalize_400x400_jpg"

        report.append(
            ReportRow(
                src_rel=str(rel),
                dst_rel=str(dst.relative_to(DST_DIR)),
                action=action,
                src_size=f"{src_size[0]}x{src_size[1]}",
                dst_size=f"{dst_size[0]}x{dst_size[1]}",
            )
        )

    with REPORT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["src_rel", "dst_rel", "action", "src_size", "dst_size"])
        for row in report:
            writer.writerow([row.src_rel, row.dst_rel, row.action, row.src_size, row.dst_size])

    print(f"Processed images: {len(report)}")
    print(f"Output folder: {DST_DIR}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
