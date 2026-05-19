#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPORT = REPO_ROOT / "VocabularyIT" / "VocabularyIT_image_priority_report.csv"
OUTPUT_MD = REPO_ROOT / "VocabularyIT" / "VocabularyIT_A_remaining_split.md"
OUTPUT_CSV = REPO_ROOT / "VocabularyIT" / "VocabularyIT_A_remaining_split.csv"

# Remaining group A items that can still use an existing Pict asset without adding a new image.
# Notes intentionally state when the match is only approximate.
EXISTING_ASSET_SUGGESTIONS: dict[str, tuple[str, str]] = {
    "forno": ("restaurant", "Stredni shoda: peceni/jidlo, ale neni to primo trouba."),
    "panificio": ("restaurant", "Stredni shoda: misto s pecivem, ale neni to primo pekarna."),
    "esercizio": ("document", "Vysoka shoda pro ukol/cviceni na papire."),
    "forza": ("strong", "Stredni shoda pro vyznam sila; mene pro citoslovce 'no tak'."),
    "parola": ("document", "Stredni shoda: psane slovo na dokumentu."),
    "vocabolo": ("document", "Stredni shoda: slovicko/vyraz na dokumentu."),
    "viale": ("garden", "Nizsi shoda: alej se stromy, nejblizsi je zahrada."),
    "vaniglia": ("icecream", "Stredni shoda podle aktualni vety o vanilkove zmrzline."),
    "calcio": ("field", "Stredni shoda podle fotbaloveho kontextu ve vete."),
    "gara": ("field", "Nizsi shoda: sportovni zavod, nejblizsi je hriste."),
    "ponte": ("lakepond", "Nizsi shoda: most pres vodu, nejblizsi je scena s vodou."),
    "mercato": ("restaurant", "Nizsi shoda: misto spojene s jidlem a nakupem."),
}


def main() -> int:
    rows = [r for r in csv.DictReader(SOURCE_REPORT.open(encoding="utf-8", newline="")) if r["Priority"] == "A"]
    rows.sort(key=lambda row: int(row["Order"]))

    existing_rows: list[dict[str, str]] = []
    new_image_rows: list[dict[str, str]] = []

    for row in rows:
        it = row["IT"]
        suggestion = EXISTING_ASSET_SUGGESTIONS.get(it)
        if suggestion:
            stem, note = suggestion
            row = dict(row)
            row["Decision"] = "existing_asset"
            row["SuggestedStem"] = stem
            row["DecisionNote"] = note
            existing_rows.append(row)
        else:
            row = dict(row)
            row["Decision"] = "new_image_needed"
            row["SuggestedStem"] = ""
            row["DecisionNote"] = "Bez rozumneho existujiciho assetu v Pict."
            new_image_rows.append(row)

    fieldnames = [
        "Order",
        "IT",
        "CZ",
        "CurrentFallbackStem",
        "Decision",
        "SuggestedStem",
        "DecisionNote",
        "Sentence",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows + new_image_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    lines: list[str] = []
    lines.append("# VocabularyIT Remaining A Split")
    lines.append("")
    lines.append(f"- Zdroj: `{SOURCE_REPORT.relative_to(REPO_ROOT)}`")
    lines.append(f"- Celkem zbyvajicich A polozek: `{len(rows)}`")
    lines.append(f"- Lze jeste mapovat na existujici asset: `{len(existing_rows)}`")
    lines.append(f"- Potrebuje novy obrazek: `{len(new_image_rows)}`")
    lines.append("")

    lines.append("## Lze jeste mapovat na existujici asset")
    lines.append("")
    lines.append("| Order | IT | CZ | Navrzeny stem | Poznamka |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in existing_rows:
        lines.append(
            f"| {row['Order']} | {row['IT']} | {row['CZ']} | {row['SuggestedStem']} | {row['DecisionNote']} |"
        )
    lines.append("")

    lines.append("## Potrebuje novy obrazek")
    lines.append("")
    lines.append("| Order | IT | CZ | Aktualni fallback |")
    lines.append("| --- | --- | --- | --- |")
    for row in new_image_rows:
        lines.append(
            f"| {row['Order']} | {row['IT']} | {row['CZ']} | {row['CurrentFallbackStem']} |"
        )
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OK  {OUTPUT_MD}")
    print(f"OK  {OUTPUT_CSV}")
    print(f"Existing asset candidates: {len(existing_rows)}")
    print(f"New image needed: {len(new_image_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
