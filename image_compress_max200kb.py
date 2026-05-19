#!/usr/bin/env python3
import argparse
import io
from pathlib import Path

from PIL import Image


SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def _save_jpeg(img: Image.Image, quality: int) -> bytes:
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def _save_webp(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()


def _save_png(img: Image.Image, colors: int) -> bytes:
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    qimg = img.quantize(colors=colors, method=Image.MEDIANCUT)
    buf = io.BytesIO()
    qimg.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def compress_to_limit(path: Path, target_bytes: int) -> tuple[bytes, str]:
    with Image.open(path) as img:
        original_fmt = (img.format or "").upper()

        if original_fmt in {"JPG", "JPEG"}:
            best = _save_jpeg(img, 95)
            if len(best) <= target_bytes:
                return best, "JPEG"
            lo, hi = 25, 95
            for _ in range(8):
                q = (lo + hi) // 2
                data = _save_jpeg(img, q)
                if len(data) <= target_bytes:
                    best = data
                    lo = q + 1
                else:
                    hi = q - 1
            return best, "JPEG"

        if original_fmt == "WEBP":
            best = _save_webp(img, 95)
            if len(best) <= target_bytes:
                return best, "WEBP"
            lo, hi = 20, 95
            for _ in range(8):
                q = (lo + hi) // 2
                data = _save_webp(img, q)
                if len(data) <= target_bytes:
                    best = data
                    lo = q + 1
                else:
                    hi = q - 1
            return best, "WEBP"

        # PNG or unknown: try palette reduction first.
        best = _save_png(img, 256)
        if len(best) <= target_bytes:
            return best, "PNG"
        for colors in (192, 128, 96, 64, 48, 32, 24, 16):
            data = _save_png(img, colors)
            if len(data) <= target_bytes:
                return data, "PNG"
            if len(data) < len(best):
                best = data

        # Fallback to JPEG for hard-to-compress PNGs.
        jpg_best = _save_jpeg(img, 90)
        if len(jpg_best) < len(best):
            best = jpg_best
            return best, "JPEG"
        return best, "PNG"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress images in a folder to max size (default 200 KB)."
    )
    parser.add_argument("input_dir", help="Source directory with images")
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory (default: overwrite originals)",
    )
    parser.add_argument(
        "--max-kb",
        type=int,
        default=200,
        help="Maximum file size in KB (default: 200)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    out_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else input_dir
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    target_bytes = args.max_kb * 1024

    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED])
    if not files:
        print("No supported image files found.")
        return

    for src in files:
        data, out_fmt = compress_to_limit(src, target_bytes)
        if out_fmt == "JPEG":
            ext = ".jpg"
        elif out_fmt == "WEBP":
            ext = ".webp"
        else:
            ext = ".png"

        dst = out_dir / (src.stem + ext)
        dst.write_bytes(data)
        print(
            f"{src.name} -> {dst.name}: {src.stat().st_size // 1024} KB -> {dst.stat().st_size // 1024} KB"
        )


if __name__ == "__main__":
    main()
