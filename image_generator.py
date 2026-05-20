#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_DIR / "image_generator_config.json"
DEFAULT_REQUEST_PATH = PROJECT_DIR / "PictNew" / "NewPicturesRequest20052026.json"
CONFIRMATION_PHRASE = "Potvrzuji generovani obrazku"


@dataclass(frozen=True)
class GenerationConfig:
    model: str
    size: str
    quality: str
    output_format: str
    output_compression: int
    target_size_kb: int
    max_size_kb: int
    batch_size: int
    output_root: Path
    style_prompt: str


@dataclass(frozen=True)
class PlannedItem:
    index: int
    request: dict[str, Any]
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a reviewed PictNew image batch.")
    parser.add_argument("--request-json", type=Path, default=DEFAULT_REQUEST_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--batch-index", type=int, default=1, help="One-based batch index.")
    parser.add_argument("--batch-size", type=int, default=0, help="Override config/request batch size.")
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--execute", action="store_true", help="Actually call the image API.")
    parser.add_argument(
        "--confirm",
        default="",
        help=f"Required with --execute. Must contain: {CONFIRMATION_PHRASE}",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    payload = load_json(args.request_json)
    batch_size = args.batch_size or int(payload.get("batch_size") or config.batch_size)
    if batch_size < 1:
        raise SystemExit("Batch size must be at least 1.")
    if args.batch_index < 1:
        raise SystemExit("--batch-index must be at least 1.")

    requests = payload.get("requests")
    if not isinstance(requests, list):
        raise SystemExit("Request JSON must contain a list field: requests")

    output_root = (args.output_root or config.output_root).resolve()
    ensure_within_project(output_root)
    planned = plan_batch(
        requests=requests,
        batch_index=args.batch_index,
        batch_size=batch_size,
        output_dir=output_root / batch_dir_name(payload=payload, batch_index=args.batch_index),
        output_format=config.output_format,
    )

    print_plan(
        payload=payload,
        config=config,
        request_path=args.request_json,
        batch_index=args.batch_index,
        batch_size=batch_size,
        planned=planned,
        execute=args.execute,
    )

    if not args.execute:
        print("")
        print("Dry run only. No API calls and no files written.")
        print(f"To generate, rerun with --execute --confirm \"{CONFIRMATION_PHRASE}\"")
        return 0

    if normalize(CONFIRMATION_PHRASE) not in normalize(args.confirm):
        raise SystemExit(f"Generation requires confirmation containing: {CONFIRMATION_PHRASE}")
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set in the environment.")
    if not planned:
        raise SystemExit("Selected batch is empty.")

    output_dir = planned[0].output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    results = generate_batch(planned=planned, config=config, overwrite=args.overwrite)
    report_path = output_dir / "generation_report.json"
    review_path = output_dir / "review.html"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_path.write_text(render_review_html(results=results, batch_index=args.batch_index), encoding="utf-8")

    print("")
    print(f"Wrote: {report_path}")
    print(f"Wrote: {review_path}")
    return 0


def load_config(path: Path) -> GenerationConfig:
    data = load_json(path)
    output_root = Path(str(data.get("output_root") or "PictNew/generated"))
    if not output_root.is_absolute():
        output_root = PROJECT_DIR / output_root
    output_format = str(data.get("output_format") or "webp").casefold()
    if output_format not in {"webp", "jpeg", "png"}:
        raise SystemExit("output_format must be one of: webp, jpeg, png")
    return GenerationConfig(
        model=str(data.get("model") or "gpt-image-2"),
        size=str(data.get("size") or "1024x1024"),
        quality=str(data.get("quality") or "low"),
        output_format=output_format,
        output_compression=int(data.get("output_compression") or 85),
        target_size_kb=int(data.get("target_size_kb") or 250),
        max_size_kb=int(data.get("max_size_kb") or 300),
        batch_size=int(data.get("batch_size") or 10),
        output_root=output_root,
        style_prompt=str(data.get("style_prompt") or ""),
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object: {path}")
    return data


def batch_dir_name(payload: dict[str, Any], batch_index: int) -> str:
    created = str(payload.get("created_at") or datetime.now().date().isoformat()).replace("-", "")
    language = str(payload.get("language") or "vocab")
    return f"{created}_{language}_batch{batch_index:03d}"


def plan_batch(
    requests: list[dict[str, Any]],
    batch_index: int,
    batch_size: int,
    output_dir: Path,
    output_format: str,
) -> list[PlannedItem]:
    start = (batch_index - 1) * batch_size
    end = start + batch_size
    selected = requests[start:end]
    suffix = ".jpg" if output_format == "jpeg" else f".{output_format}"
    planned = []
    for offset, request in enumerate(selected, start=start + 1):
        image_name = str(request.get("image_name") or "").strip()
        if not image_name:
            raise SystemExit(f"Missing image_name in request #{offset}")
        filename = f"{safe_stem(image_name)}{suffix}"
        planned.append(PlannedItem(index=offset, request=request, output_path=output_dir / filename))
    return planned


def print_plan(
    payload: dict[str, Any],
    config: GenerationConfig,
    request_path: Path,
    batch_index: int,
    batch_size: int,
    planned: list[PlannedItem],
    execute: bool,
) -> None:
    total = int(payload.get("total_unique_target_images") or payload.get("total_requests") or 0)
    total_batches = math.ceil(total / batch_size) if total else 0
    print(f"Request JSON: {request_path}")
    print(f"Model: {config.model}")
    print(f"Size/quality/format: {config.size} / {config.quality} / {config.output_format}")
    print(f"Target/max size: {config.target_size_kb} kB / {config.max_size_kb} kB")
    print(f"Batch: {batch_index} / {total_batches}")
    print(f"Items in batch: {len(planned)}")
    print(f"Mode: {'execute' if execute else 'dry-run'}")
    if planned:
        print("")
        print("Planned files:")
        for item in planned:
            words = " / ".join(str(value) for value in item.request.get("words", []))
            meanings = " / ".join(str(value) for value in item.request.get("czech_meanings", []))
            print(f"- #{item.index}: {item.output_path} | {words} | {meanings}")


def generate_batch(
    planned: list[PlannedItem],
    config: GenerationConfig,
    overwrite: bool,
) -> list[dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI()
    results = []
    for item in planned:
        print(
            f"Generating {len(results) + 1}/{len(planned)}: {item.output_path.name}",
            flush=True,
        )
        if item.output_path.exists() and not overwrite:
            results.append(build_result(item=item, status="skipped_exists"))
            print(f"Skipped existing: {item.output_path.name}", flush=True)
            continue

        prompt = str(item.request.get("prompt") or "")
        if config.style_prompt and config.style_prompt not in prompt:
            prompt = f"{prompt} {config.style_prompt}".strip()

        response = client.images.generate(
            model=config.model,
            prompt=prompt,
            n=1,
            size=config.size,
            quality=config.quality,
            output_format=config.output_format,
            output_compression=config.output_compression,
        )
        if not response.data or not response.data[0].b64_json:
            raise RuntimeError(f"No image data returned for {item.output_path.name}")

        raw = base64.b64decode(response.data[0].b64_json)
        image_bytes = compress_image_bytes(
            raw=raw,
            output_format=config.output_format,
            target_bytes=config.target_size_kb * 1024,
            max_bytes=config.max_size_kb * 1024,
        )
        item.output_path.parent.mkdir(parents=True, exist_ok=True)
        item.output_path.write_bytes(image_bytes)
        results.append(
            build_result(
                item=item,
                status="generated",
                original_bytes=len(raw),
                output_bytes=len(image_bytes),
            )
        )
        print(f"Wrote {item.output_path.name}: {len(image_bytes) / 1024:.1f} kB", flush=True)
    return results


def build_result(
    item: PlannedItem,
    status: str,
    original_bytes: int = 0,
    output_bytes: int = 0,
) -> dict[str, Any]:
    return {
        "status": status,
        "request_index": item.index,
        "output_path": str(item.output_path),
        "output_file": item.output_path.name,
        "original_bytes": original_bytes,
        "output_bytes": output_bytes or (item.output_path.stat().st_size if item.output_path.exists() else 0),
        "request": item.request,
    }


def compress_image_bytes(raw: bytes, output_format: str, target_bytes: int, max_bytes: int) -> bytes:
    from PIL import Image, ImageOps

    with Image.open(BytesIO(raw)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        encoded = encode_image(image, output_format=output_format, quality=88)
        if len(encoded) <= max_bytes:
            return encoded

        current = image
        best = encoded
        scale = 1.0
        for _attempt in range(8):
            for quality in (85, 78, 70, 62, 54, 46, 38):
                encoded = encode_image(current, output_format=output_format, quality=quality)
                if len(encoded) < len(best):
                    best = encoded
                if len(encoded) <= target_bytes:
                    return encoded
                if len(encoded) <= max_bytes:
                    return encoded

            width, height = current.size
            long_edge = max(width, height)
            if long_edge <= 800:
                return best
            ratio = math.sqrt(target_bytes / max(1, len(best))) * 0.94
            scale *= min(0.9, max(0.6, ratio))
            new_size = (max(1, int(image.size[0] * scale)), max(1, int(image.size[1] * scale)))
            current = image.resize(new_size, Image.Resampling.LANCZOS)
        return best


def encode_image(image: Any, output_format: str, quality: int) -> bytes:
    from PIL import Image as PILImage

    save_format = "JPEG" if output_format == "jpeg" else output_format.upper()
    output = BytesIO()
    save_args: dict[str, Any] = {"format": save_format, "optimize": True}
    if save_format in {"JPEG", "WEBP"}:
        save_args["quality"] = quality
    if save_format == "JPEG":
        if image.mode in {"RGBA", "LA", "P"}:
            background = PILImage.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        save_args["progressive"] = True
    image.save(output, **save_args)
    return output.getvalue()


def render_review_html(results: list[dict[str, Any]], batch_index: int) -> str:
    rows = "\n".join(render_review_row(result) for result in results)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>Generated image review batch {batch_index:03d}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; background: #f7f8fa; color: #1f2933; }}
    h1 {{ font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 10px; vertical-align: top; }}
    th {{ background: #edf2f7; text-align: left; }}
    img {{ width: 160px; height: 160px; object-fit: contain; background: #fff; }}
    code {{ white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>Generated image review batch {batch_index:03d}</h1>
  <table>
    <thead>
      <tr>
        <th>Preview</th>
        <th>File</th>
        <th>Size</th>
        <th>Words</th>
        <th>Czech meanings</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""


def render_review_row(result: dict[str, Any]) -> str:
    request = result["request"]
    output_file = result["output_file"]
    words = " / ".join(str(value) for value in request.get("words", []))
    meanings = " / ".join(str(value) for value in request.get("czech_meanings", []))
    size_kb = result.get("output_bytes", 0) / 1024
    return f"""      <tr>
        <td><img src="{html.escape(output_file)}" alt="{html.escape(output_file)}"></td>
        <td><code>{html.escape(output_file)}</code></td>
        <td>{size_kb:.1f} kB</td>
        <td>{html.escape(words)}</td>
        <td>{html.escape(meanings)}</td>
        <td>{html.escape(result["status"])}</td>
      </tr>"""


def safe_stem(value: str) -> str:
    stem = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip())
    while "__" in stem:
        stem = stem.replace("__", "_")
    stem = stem.strip("_")
    if not stem:
        raise SystemExit(f"Cannot build filename from image name: {value!r}")
    return stem


def ensure_within_project(path: Path) -> None:
    try:
        path.resolve().relative_to(PROJECT_DIR)
    except ValueError as exc:
        raise SystemExit(f"Path must stay inside project: {path}") from exc


def normalize(text: str) -> str:
    return text.casefold().strip()


if __name__ == "__main__":
    raise SystemExit(main())
