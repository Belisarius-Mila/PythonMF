#!/usr/bin/env python3
"""Small wrapper for Matysek English F5-TTS Bunny voice experiments."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLI = REPO_ROOT / ".venv_f5tts2/bin/f5-tts_infer-cli"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/matysek_english/voice_references"
DEFAULT_REF_AUDIO = DEFAULT_OUTPUT_DIR / "bunny_long_gifts_scene_we_can_train_all_colors_20260602.mp3"
DEFAULT_REF_TEXT = "Yes. But we can train all colors in my house. Let's go."
MAX_REF_SECONDS = 12.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Bunny-style English MP3 via local F5-TTS CLI."
    )
    parser.add_argument("--cli", type=Path, default=DEFAULT_CLI)
    parser.add_argument("--model", default="F5TTS_v1_Base")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--ref-audio", type=Path, default=DEFAULT_REF_AUDIO)
    parser.add_argument("--ref-text", default=None)
    parser.add_argument("--ref-text-file", type=Path, default=None)
    parser.add_argument("--gen-text", default=None)
    parser.add_argument("--gen-text-file", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--nfe-step", type=int, default=None)
    parser.add_argument(
        "--allow-long-ref",
        action="store_true",
        help="Allow ref audio over 12s. F5 may clip it, so this is usually a bad idea.",
    )
    parser.add_argument("--print-command", action="store_true")
    return parser.parse_args()


def read_text_arg(value: str | None, file_path: Path | None, default: str | None = None) -> str:
    if value and file_path:
        raise SystemExit("Pouzij jen jednu variantu: text nebo textovy soubor.")
    if file_path:
        return file_path.read_text(encoding="utf-8").strip()
    if value:
        return value.strip()
    if default is not None:
        return default
    raise SystemExit("Chybi text.")


def mp3_duration_seconds(path: Path) -> float | None:
    afinfo = shutil.which("afinfo")
    if afinfo:
        result = subprocess.run(
            [afinfo, str(path)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        match = re.search(r"estimated duration:\s*([0-9.]+)\s*sec", result.stdout)
        if match:
            return float(match.group(1))

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            return float(result.stdout.strip())
        except ValueError:
            return None

    return None


def main() -> int:
    args = parse_args()

    ref_audio = args.ref_audio.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    cli = args.cli.expanduser().resolve()
    ref_text = read_text_arg(args.ref_text, args.ref_text_file, DEFAULT_REF_TEXT)
    gen_text = read_text_arg(args.gen_text, args.gen_text_file)

    if not cli.exists():
        raise SystemExit(f"F5 CLI neexistuje: {cli}")
    if not ref_audio.exists():
        raise SystemExit(f"Referencni audio neexistuje: {ref_audio}")

    duration = mp3_duration_seconds(ref_audio)
    if duration is not None and duration > MAX_REF_SECONDS and not args.allow_long_ref:
        raise SystemExit(
            f"Reference ma {duration:.2f} s. F5 lokalne klipuje nad ~12 s; "
            "zkrat ji, nebo pouzij --allow-long-ref vedome."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-f5tts")
    env.setdefault("XDG_CACHE_HOME", "/private/tmp/f5tts-cache")

    command = [
        str(cli),
        "--model",
        args.model,
        "--ref_audio",
        str(ref_audio),
        "--ref_text",
        ref_text,
        "--gen_text",
        gen_text,
        "--output_dir",
        str(output_dir),
        "--output_file",
        args.output_file,
        "--device",
        args.device,
    ]
    if args.nfe_step is not None:
        command.extend(["--nfe_step", str(args.nfe_step)])

    if args.print_command:
        print(" ".join(command))

    start = time.perf_counter()
    subprocess.run(command, check=True, env=env)
    elapsed = time.perf_counter() - start

    output_path = output_dir / args.output_file
    print(f"Hotovo: {output_path}")
    print(f"Cas: {elapsed:.2f} s")
    if duration is not None:
        print(f"Reference: {duration:.3f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
