#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PICT_NEW_DIR = PROJECT_DIR / "PictNew"

LANGUAGES = {
    "it": {
        "name": "VocabularyIT",
        "pict_path": PROJECT_DIR / "VocabularyIT" / "IT_Pict.csv",
        "word_col": "ITP",
    },
    "fr": {
        "name": "VocabularyFR",
        "pict_path": PROJECT_DIR / "VocabularyFR" / "FR_Pict.csv",
        "word_col": "FRP",
    },
}

DEFAULT_STYLE_PROMPT = (
    "Warm vocabulary-card illustration for a child learner, but not babyish. "
    "Use a clear everyday scene with a simple background, natural details, soft shadows, "
    "and a little story or action. Vary people when they are useful: different children or adults, "
    "not always the same boy and girl; use at most one main boy or one main girl unless the meaning "
    "requires interaction. Keep the main idea instantly readable. Avoid random text, foreign words, "
    "decorative letters, and meaningless labels. A short Czech label or sign is allowed only when it "
    "makes the meaning clearer. No watermark, no signature."
)

CONCEPT_HINTS = {
    "a": (
        "Do not draw the letter A and do not use an apple as a shortcut. "
        "Represent the idea of an indefinite article: one ordinary, unspecified object chosen "
        "from a small group, such as one cup on a kitchen table with a few other household objects "
        "softly in the background."
    ),
    "inorderto": (
        "Represent purpose: a person doing one action in order to achieve a clear result, "
        "for example a child carrying a watering can toward a dry plant."
    ),
    "sothenwell": (
        "Represent a transition in thought or time: a small everyday scene where someone has just "
        "understood what to do next."
    ),
    "often": (
        "Represent repetition without using written marks or numbers: the same everyday action shown "
        "through several visual echoes or repeated objects in the scene."
    ),
    "tolikepleasure": (
        "Represent liking and pleasure: one person enjoying something simple with a natural expression, "
        "not a generic heart icon."
    ),
    "painevil": (
        "Represent badness or pain gently and safely: a child with a small scraped knee being comforted, "
        "or a broken object causing frustration, without anything frightening."
    ),
    "usual": (
        "Represent usual or ordinary: a familiar daily routine in a lived-in room, with small realistic details."
    ),
}


@dataclass
class PictureRequest:
    id: str
    language: str
    image_name: str
    target_filename: str
    row_numbers: list[int]
    words: list[str]
    czech_meanings: list[str]
    source_entries: list[dict[str, str | int]]
    prompt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare vocabulary picture-generation request JSON and batch review HTML."
    )
    parser.add_argument("--language", choices=sorted(LANGUAGES), default="it")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date as YYYY-MM-DD.")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--batch-index", type=int, default=1, help="One-based batch index for HTML review.")
    parser.add_argument("--out-dir", type=Path, default=PICT_NEW_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_date = parse_date(args.date)
    date_stamp = run_date.strftime("%d%m%Y")

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    if args.batch_index < 1:
        raise SystemExit("--batch-index must be at least 1")

    config = LANGUAGES[args.language]
    rows = load_csv(config["pict_path"])
    requests = collect_picture_requests(
        rows=rows,
        language=args.language,
        word_col=config["word_col"],
    )
    batches = split_batches(requests, args.batch_size)
    selected_batch = batches[args.batch_index - 1] if args.batch_index <= len(batches) else []

    request_path = args.out_dir / f"NewPicturesRequest{date_stamp}.json"
    review_path = args.out_dir / f"NewPicturesReview{date_stamp}_batch{args.batch_index:03d}.html"

    payload = build_payload(
        language=args.language,
        source_csv=config["pict_path"],
        run_date=run_date,
        batch_size=args.batch_size,
        requests=requests,
    )

    print(f"Language: {args.language}")
    print(f"Source: {config['pict_path']}")
    source_rows = sum(len(item.row_numbers) for item in requests)
    duplicate_rows = source_rows - len(requests)
    print(f"Rows with PD containing add: {source_rows}")
    print(f"Unique target images: {len(requests)}")
    print(f"Rows sharing an image name: {duplicate_rows}")
    print(f"Batch size: {args.batch_size}")
    print(f"Batches: {len(batches)}")
    print(f"Selected batch: {args.batch_index} ({len(selected_batch)} items)")

    if args.dry_run:
        print("Dry run: no files written.")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    review_path.write_text(
        render_review_html(
            language=args.language,
            run_date=run_date,
            batch_index=args.batch_index,
            total_batches=len(batches),
            batch_size=args.batch_size,
            requests=selected_batch,
            request_path=request_path,
        ),
        encoding="utf-8",
    )

    print(f"Wrote: {request_path}")
    print(f"Wrote: {review_path}")
    return 0


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit("--date must use YYYY-MM-DD") from exc


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def collect_picture_requests(
    rows: list[dict[str, str]],
    language: str,
    word_col: str,
) -> list[PictureRequest]:
    grouped: dict[str, dict[str, object]] = {}
    for index, row in enumerate(rows, start=2):
        pd_value = (row.get("PD") or "").strip()
        if "add" not in pd_value.casefold():
            continue

        image_name = (row.get("ENP") or "").strip()
        if not image_name:
            continue

        word = (row.get(word_col) or "").strip()
        czech_meaning = (row.get("CZP") or "").strip()
        target_filename = f"{safe_stem(image_name)}.png"
        group_key = target_filename.casefold()
        if group_key not in grouped:
            grouped[group_key] = {
                "image_name": image_name,
                "target_filename": target_filename,
                "entries": [],
            }
        grouped[group_key]["entries"].append(
            {
                "row_number": index,
                "word": word,
                "czech_meaning": czech_meaning,
                "source_pd": pd_value,
                "source_pe": (row.get("PE") or "").strip(),
            }
        )

    requests = []
    for key, group in grouped.items():
        entries = group["entries"]
        assert isinstance(entries, list)
        words = [str(entry["word"]) for entry in entries]
        czech_meanings = [str(entry["czech_meaning"]) for entry in entries]
        image_name = str(group["image_name"])
        requests.append(
            PictureRequest(
                id=f"{language}-{safe_stem(image_name).casefold()}",
                language=language,
                image_name=image_name,
                target_filename=str(group["target_filename"]),
                row_numbers=[int(entry["row_number"]) for entry in entries],
                words=words,
                czech_meanings=czech_meanings,
                source_entries=entries,
                prompt=build_prompt(
                    words=words,
                    czech_meanings=czech_meanings,
                    image_name=image_name,
                ),
            )
        )
    return requests


def safe_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    stem = re.sub(r"_+", "_", stem).strip("_")
    if not stem:
        raise SystemExit(f"Cannot build filename from ENP value: {value!r}")
    return stem


def build_prompt(words: list[str], czech_meanings: list[str], image_name: str) -> str:
    word_text = join_unique(words)
    meaning_text = join_unique(czech_meanings)
    concept_hint = CONCEPT_HINTS.get(image_name.casefold(), "")
    hint_sentence = f" Specific visual direction: {concept_hint}" if concept_hint else ""
    return (
        "Create one square image for a vocabulary card. "
        f"The file name will be '{image_name}', but do not illustrate the file name literally unless it matches the meaning. "
        f"The image must represent the Italian/French word(s) '{word_text}' with Czech meaning '{meaning_text}'. "
        "Base the scene primarily on the Czech meaning, then use the foreign word only as context. "
        "If the concept is abstract or grammatical, use a concrete everyday visual metaphor that a child can understand."
        f"{hint_sentence} "
        f"{DEFAULT_STYLE_PROMPT}"
    )


def join_unique(values: list[str]) -> str:
    seen = set()
    result = []
    for value in values:
        normalized = value.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return " / ".join(result)


def split_batches(requests: list[PictureRequest], batch_size: int) -> list[list[PictureRequest]]:
    return [requests[i : i + batch_size] for i in range(0, len(requests), batch_size)]


def build_payload(
    language: str,
    source_csv: Path,
    run_date: date,
    batch_size: int,
    requests: list[PictureRequest],
) -> dict[str, object]:
    total_batches = math.ceil(len(requests) / batch_size) if requests else 0
    return {
        "schema_version": 1,
        "created_at": run_date.isoformat(),
        "language": language,
        "source_csv": str(source_csv),
        "output_dir": "PictNew",
        "target_size_kb": 250,
        "max_size_kb": 300,
        "batch_size": batch_size,
        "total_source_rows": sum(len(item.row_numbers) for item in requests),
        "total_requests": len(requests),
        "total_unique_target_images": len(requests),
        "duplicate_source_rows": sum(len(item.row_numbers) for item in requests) - len(requests),
        "total_batches": total_batches,
        "style_prompt": DEFAULT_STYLE_PROMPT,
        "requests": [asdict(item) for item in requests],
    }


def render_review_html(
    language: str,
    run_date: date,
    batch_index: int,
    total_batches: int,
    batch_size: int,
    requests: list[PictureRequest],
    request_path: Path,
) -> str:
    rows = "\n".join(render_review_row(item) for item in requests)
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>PictNew review {html.escape(language)} batch {batch_index:03d}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 24px;
      color: #1f2933;
      background: #f7f8fa;
    }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    .meta {{ margin: 0 0 18px; color: #52606d; line-height: 1.45; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 10px; vertical-align: top; }}
    th {{ background: #edf2f7; text-align: left; }}
    code {{ white-space: nowrap; }}
    .prompt {{ max-width: 760px; line-height: 1.35; }}
  </style>
</head>
<body>
  <h1>PictNew review: {html.escape(language.upper())} batch {batch_index:03d}</h1>
  <p class="meta">
    Date: {html.escape(run_date.isoformat())}<br>
    Batch size: {batch_size}<br>
    Batch: {batch_index} / {total_batches}<br>
    Request JSON: <code>{html.escape(str(request_path))}</code>
  </p>
  <table>
    <thead>
      <tr>
        <th>Row</th>
        <th>Words</th>
        <th>Czech meanings</th>
        <th>Image name</th>
        <th>Target file</th>
        <th>Prompt</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""


def render_review_row(item: PictureRequest) -> str:
    rows = ", ".join(str(row_number) for row_number in item.row_numbers)
    words = " / ".join(item.words)
    czech_meanings = " / ".join(item.czech_meanings)
    return f"""      <tr>
        <td>{html.escape(rows)}</td>
        <td>{html.escape(words)}</td>
        <td>{html.escape(czech_meanings)}</td>
        <td><code>{html.escape(item.image_name)}</code></td>
        <td><code>{html.escape(item.target_filename)}</code></td>
        <td class="prompt">{html.escape(item.prompt)}</td>
      </tr>"""


if __name__ == "__main__":
    raise SystemExit(main())
