#!/usr/bin/env python3
"""Generate Czech MP3 files from a CSV phrase list using edge-tts."""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:  # pragma: no cover - depends on local environment
    edge_tts = None


DEFAULT_CSV = Path("data") / "tts_phrases.csv"
DEFAULT_OUT = Path("assets") / "audio" / "cs"
DEFAULT_VOICE = "cs-CZ-AntoninNeural"
DEFAULT_RATE = "-10%"
REQUIRED_COLUMNS = {"id", "text_cs"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Czech MP3 files from data/tts_phrases.csv."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"CSV file with id,text_cs columns (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory for MP3 files (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"edge-tts voice name (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate files even when the target MP3 already exists.",
    )
    return parser.parse_args()


def validate_edge_tts() -> None:
    if edge_tts is None:
        raise RuntimeError(
            "Missing dependency 'edge-tts'. Install it with: python -m pip install edge-tts"
        )


def read_phrases(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV file is missing required column(s): {missing}")

        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            phrase_id = (row.get("id") or "").strip()
            text = (row.get("text_cs") or "").strip()
            if not phrase_id:
                print(f"Skipping line {line_number}: empty id", file=sys.stderr)
                continue
            if not text:
                print(f"Skipping {phrase_id}: empty text_cs", file=sys.stderr)
                continue
            rows.append({"id": phrase_id, "text_cs": text})
        return rows


async def generate_phrase(
    phrase_id: str,
    text: str,
    out_dir: Path,
    voice: str,
    force: bool,
) -> str:
    output_path = out_dir / f"{phrase_id}.mp3"
    if output_path.exists() and not force:
        return f"skip {output_path}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=DEFAULT_RATE)
    await communicate.save(str(output_path))
    return f"done {output_path}"


async def generate_all(
    rows: list[dict[str, str]],
    out_dir: Path,
    voice: str,
    force: bool,
) -> None:
    for row in rows:
        status = await generate_phrase(
            phrase_id=row["id"],
            text=row["text_cs"],
            out_dir=out_dir,
            voice=voice,
            force=force,
        )
        print(status)


def main() -> int:
    args = parse_args()

    try:
        validate_edge_tts()
        rows = read_phrases(args.csv)
        if not rows:
            print(f"No valid rows found in {args.csv}")
            return 0
        asyncio.run(generate_all(rows, args.out, args.voice, args.force))
    except FileNotFoundError as exc:
        if args.csv == DEFAULT_CSV:
            print(
                "CSV soubor nebyl nalezen, otevírám okno pro ruční zadání textu..."
            )
            from tts_gui import main as gui_main

            gui_main()
            return 0

        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
