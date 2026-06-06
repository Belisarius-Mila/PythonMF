#!/usr/bin/env python3
"""Prepare image generation request JSON for Jana's VocabularyFR missing images."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path


DEFAULT_REVIEW_CSV = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/PictNew/jana_vocabularyfr_fallback_review.csv"
)
DEFAULT_OUTPUT = Path(
    "/Users/miloslavfalta/Desktop/PythonMF/PictNew/"
    "JanaVocabularyFRRequest20260606.json"
)

STYLE_PROMPT = (
    "Warm vocabulary-card illustration for a child learner, but not babyish. "
    "Use a clear everyday scene with a simple background, natural details, soft shadows, "
    "and a little story or action. Vary people when they are useful: different children "
    "or adults, not always the same boy and girl; use at most one main boy or one main girl "
    "unless the meaning requires interaction. Keep the main idea instantly readable. "
    "Avoid random text, foreign words, decorative letters, and meaningless labels. "
    "A short Czech label or sign is allowed only when it makes the meaning clearer. "
    "No watermark, no signature."
)


VISUAL_DIRECTIONS = {
    "bank": "Show a small local bank building with a discreet money symbol and a person entering with a wallet; make it clearly a financial bank, not a river bank.",
    "bus": "Show a friendly city bus stopped at a bus stop with its door open, ready for passengers.",
    "butter": "Show a pat of butter on a small plate next to bread on a kitchen table.",
    "calm": "Show a quiet person sitting calmly by a window with a cup of tea, peaceful posture and no action rush.",
    "charger": "Show a phone connected to a wall charger on a bedside table, cable and plug clearly visible.",
    "chinese": "Show a respectful everyday hint of Chinese culture, such as a child holding a small Chinese flag beside a red lantern; avoid stereotypes.",
    "comfortable": "Show a person relaxed in a comfortable chair with a blanket, clearly feeling cozy.",
    "delivery": "Show a delivery courier handing a small package to a person at a front door.",
    "driver": "Show a car driver seated at the wheel, hands on steering wheel, seen through the windshield.",
    "european": "Show a simple map-like scene with Europe highlighted and small EU-style stars, not a political poster.",
    "fast": "Show a runner moving quickly with motion lines on a path, clearly fast but friendly.",
    "fresh": "Show fresh vegetables and fruit with water droplets on a market stall.",
    "friend": "Show two friends greeting each other warmly, simple everyday friendship.",
    "glasses": "Show a pair of eyeglasses on an open book, clearly glasses for seeing.",
    "heavy": "Show a person carefully lifting a heavy suitcase, effort visible but safe.",
    "idea": "Show a person having an idea, with a small glowing light bulb above a notebook.",
    "infront": "Show one object clearly in front of another, for example a red ball in front of a chair.",
    "kitchen": "Show a clean home kitchen with a stove, sink, and a pot on the counter.",
    "late": "Show a person rushing while looking at a clock, clearly late for an appointment.",
    "lemonade": "Show a glass pitcher and glass of lemonade with lemon slices on a table.",
    "livingroom": "Show a cozy living room with sofa, lamp, and small table.",
    "matchstick": "Show a single wooden matchstick and a small matchbox, unlit and safe.",
    "mobilephone": "Show a smartphone in a hand with a simple home screen, clearly a mobile phone.",
    "moroccan": "Show a respectful Moroccan context, such as a small Moroccan flag and warm market architecture; avoid caricature.",
    "musicnotebook": "Show a music notebook open on a stand with simple musical notes and a pencil.",
    "never": "Show a clear 'never' idea without text if possible: a child refusing a bad habit, with a crossed-out symbol above it.",
    "neveragain": "Show a small broken mistake being learned from, with a crossed-out repeat arrow to mean never again.",
    "nolonger": "Show something finished or no longer happening, such as an empty chair where activity has stopped, with a gentle crossed-out repeat sign.",
    "notebook": "Show a school notebook on a desk with a pencil, clearly a notebook for writing.",
    "passport": "Show a passport at an airport check desk with a boarding pass nearby; no real country data.",
    "pen": "Show a pen writing a simple line in a notebook.",
    "sad": "Show a person sitting sadly with soft expression, gentle and not dramatic.",
    "sofa": "Show a sofa in a living room, clearly the main object.",
    "student": "Show a student carrying books or sitting at a desk studying.",
    "suitcase": "Show a travel suitcase standing near a door, ready for a trip.",
    "surrender": "Show a gentle symbolic surrender: a person raising both hands calmly, no weapons or danger.",
    "tie": "Show a necktie laid neatly on a shirt, clearly a tie.",
    "university": "Show a university building with students walking outside and books in hand.",
    "world": "Show a globe on a desk, clearly representing the world.",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    with args.review_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("Decision") == "generate"]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["ProposedStem"]].append(row)

    missing_directions = sorted(set(grouped) - set(VISUAL_DIRECTIONS))
    if missing_directions:
        raise SystemExit(f"Chybi visual directions pro: {missing_directions}")

    requests = []
    for stem in sorted(grouped):
        source_rows = grouped[stem]
        words = sorted({row["FR"] for row in source_rows})
        meanings = sorted({row["CZ"] for row in source_rows})
        row_numbers = [int(row["Order"]) for row in source_rows]
        prompt = (
            "Create one square image for a vocabulary card. "
            f"The file name will be '{stem}', but do not illustrate the file name literally "
            "unless it matches the meaning. "
            f"The image must represent the French word(s) '{' / '.join(words)}' "
            f"with Czech meaning '{' / '.join(meanings)}'. "
            "Base the scene primarily on the Czech meaning, then use the French word only as context. "
            "If the concept is abstract, use a concrete everyday visual metaphor that a child can understand. "
            f"Specific visual direction: {VISUAL_DIRECTIONS[stem]} "
            f"{STYLE_PROMPT}"
        )
        requests.append(
            {
                "id": f"fr-jana-{stem}",
                "language": "fr",
                "image_name": stem,
                "target_filename": f"{stem}.webp",
                "row_numbers": row_numbers,
                "words": words,
                "czech_meanings": meanings,
                "source_entries": [
                    {
                        "row_number": int(row["Order"]),
                        "word": row["FR"],
                        "czech_meaning": row["CZ"],
                        "note": row["Note"],
                    }
                    for row in source_rows
                ],
                "prompt": prompt,
            }
        )

    payload = {
        "schema_version": 1,
        "created_at": date.today().isoformat(),
        "language": "fr_jana",
        "source_csv": str(args.review_csv),
        "output_dir": "PictNew/generated",
        "target_size_kb": 250,
        "max_size_kb": 300,
        "batch_size": args.batch_size,
        "total_source_rows": len(rows),
        "total_requests": len(requests),
        "total_unique_target_images": len(requests),
        "total_batches": (len(requests) + args.batch_size - 1) // args.batch_size,
        "style_prompt": STYLE_PROMPT,
        "requests": requests,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rows marked generate: {len(rows)}")
    print(f"Unique requests: {len(requests)}")
    print(f"Batch size: {args.batch_size}")
    print(f"Total batches: {payload['total_batches']}")
    print(f"Wrote: {args.output}")
    for request in requests:
        print(
            f"- {request['image_name']}: rows {request['row_numbers']} | "
            f"{' / '.join(request['words'])} | {' / '.join(request['czech_meanings'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
