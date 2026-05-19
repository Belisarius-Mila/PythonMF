#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "VocabularyIT" / "VocabularyIT.csv"
JSON_PATH = REPO_ROOT / "docs" / "data" / "vocabulary-it.json"
EN_JSON_PATH = REPO_ROOT / "docs" / "data" / "vocabulary-en.json"
REPORT_MD_PATH = REPO_ROOT / "VocabularyIT" / "VocabularyIT_image_priority_report.md"
REPORT_CSV_PATH = REPO_ROOT / "VocabularyIT" / "VocabularyIT_image_priority_report.csv"

PRIORITY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
PRIORITY_LABEL = {
    "A": "A - konkretni obrazek ma vysokou hodnotu",
    "B": "B - konkretni obrazek by pomohl",
    "C": "C - fallback je prijatelny, konkretni obrazek jen volitelne",
    "D": "D - ponechat fallback, konkretni obrazek ma malou hodnotu",
}

PERSON_HINTS = {
    "doktor", "lékař", "sestra", "bratr", "matka", "otec", "dcera", "syn", "kamarád",
    "kamarádka", "přítel", "přítelkyně", "teta", "strýc", "soused", "sousedka", "kuchařka",
    "turista", "turistka", "cizinec", "učitel", "učitelka",
}
PLACE_HINTS = {
    "nádraží", "stanice", "trh", "obchod", "pekárna", "kancelář", "úřad", "nemocnice",
    "kostel", "hotel", "náměstí", "letiště", "koupelna", "východ", "město", "škola",
    "restaurace", "park", "kino",
}
TIME_HINTS = {
    "čas", "počasí", "rok", "měsíc", "léto", "zima", "ráno", "večer", "dnes", "zítra",
    "hodina", "pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle",
}
ABSTRACT_HINTS = {
    "historie", "příběh", "pomoc", "síla", "laskavost", "potěšení", "radost", "jistota",
    "zajímavý", "špatně", "možná", "vůbec", "také", "spolu", "vždycky", "každý", "velmi",
    "příliš", "moc", "teď", "nyní",
}
FUNCTION_WORDS = {
    "su", "o", "e", "ma", "per", "da", "di", "in", "con", "a", "io", "tu", "lui", "lei",
    "noi", "voi", "loro", "un", "una", "mio", "mia", "tuo", "tua", "ho", "hai", "sono",
    "sei", "sì", "ci", "come", "quanto", "quanti", "quante", "per favore", "e tu?",
}


def normalize_text(text: str) -> str:
    value = (text or "").strip().casefold().replace("’", "'")
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"\s+", " ", value)


def tokenize(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", (text or "").casefold())
    tokens: list[str] = []
    for token in raw:
        normalized = normalize_text(token)
        if normalized:
            tokens.append(normalized)
    return tokens


def build_exact_cz_suggestions() -> dict[str, str]:
    payload = json.loads(EN_JSON_PATH.read_text(encoding="utf-8"))
    suggestions: dict[str, str] = {}
    duplicates: set[str] = set()
    for item in payload["items"]:
        if item.get("imageSource") == "fallback":
            continue
        cz = normalize_text(item.get("cz", ""))
        stem = (item.get("imageStem") or "").strip()
        if not cz or not stem:
            continue
        if cz in suggestions and suggestions[cz] != stem:
            duplicates.add(cz)
            continue
        suggestions[cz] = stem
    for key in duplicates:
        suggestions.pop(key, None)
    return suggestions


def classify_priority(row: dict[str, str], image_stem: str) -> tuple[str, str, str]:
    it = (row.get("IT") or "").strip()
    cz = (row.get("CZ") or "").strip()
    gender = (row.get("gender_it") or "").strip().lower()
    it_norm = normalize_text(it)
    cz_tokens = set(tokenize(cz))
    is_phrase = (" " in it_norm) or any(ch in it for ch in "?!/;:")
    is_function = it_norm in FUNCTION_WORDS or image_stem in {"preposition", "conjuction"}
    is_person = bool(cz_tokens & PERSON_HINTS)
    is_place = bool(cz_tokens & PLACE_HINTS)
    is_time = bool(cz_tokens & TIME_HINTS)
    is_abstract = bool(cz_tokens & ABSTRACT_HINTS)
    is_verb = image_stem == "verb" or it_norm.endswith(("are", "ere", "ire"))

    if is_function:
        return "D", "gramatika_a_funkcni_slova", "Nechat fallback; konkretni obrazek ma maly prinos."

    if is_phrase:
        if is_person or is_place:
            return "B", "fraze_s_konkretnim_obsahem", "Pridat jen pokud najdeme zjevny vhodny asset."
        return "C", "fraze_a_vyrazy", "Fallback je prijatelny; konkretni obrazek jen volitelne."

    if is_place:
        return "A", "mista_a_lokace", "Hledat konkretni asset nebo pridat alias na existujici obrazek."

    if gender in {"m", "f"} and is_person:
        return "B", "osoby", "Pridat alias na vhodny person asset, pokud existuje."

    if gender in {"m", "f"} and is_time:
        return "B", "casove_pojmy", "Vhodny konkretni obrazek muze pomoct, ale fallback neni kriticky spatny."

    if gender in {"m", "f"} and not is_abstract:
        return "A", "konkretni_podstatna_jmena", "Hledat konkretni asset nebo vytvorit novy obrazek."

    if is_verb:
        return "B", "slovesa", "Pokud existuje vhodny akcni obrazek, pridat alias; jinak muze zustat verb."

    if is_time:
        return "B", "casove_a_merne_vyrazy", "Casove vyrazy maji smysl mapovat na jednoduche konkretni ikony."

    if is_abstract or image_stem in {"proverbs", "others", "man", "woman"}:
        return "C", "abstraktni_nebo_popisna_slova", "Doplnit jen pokud bude zjevny vhodny asset."

    return "C", "ostatni", "Doplnit jen pokud bude zjevny vhodny asset."


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig", newline="")))
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    fallback_items = [item for item in payload["items"] if item.get("imageSource") == "fallback"]
    rows_by_order = {int(row["Order"]): row for row in rows}
    exact_cz_suggestions = build_exact_cz_suggestions()

    report_rows: list[dict[str, str]] = []
    category_counter: Counter[tuple[str, str]] = Counter()

    for item in fallback_items:
        order = int(item["order"])
        row = rows_by_order[order]
        priority, category, note = classify_priority(row, item["imageStem"])
        exact_suggestion = exact_cz_suggestions.get(normalize_text(row.get("CZ", "")), "")
        category_counter[(priority, category)] += 1
        report_rows.append(
            {
                "Order": str(order),
                "IT": row.get("IT", ""),
                "CZ": row.get("CZ", ""),
                "Sentence": row.get("Sentence", ""),
                "CurrentFallbackStem": item["imageStem"],
                "Priority": priority,
                "Category": category,
                "SuggestedExistingStem": exact_suggestion,
                "Note": note,
            }
        )

    report_rows.sort(
        key=lambda row: (
            PRIORITY_ORDER[row["Priority"]],
            row["Category"],
            int(row["Order"]),
        )
    )

    with REPORT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Order",
                "IT",
                "CZ",
                "Sentence",
                "CurrentFallbackStem",
                "Priority",
                "Category",
                "SuggestedExistingStem",
                "Note",
            ],
        )
        writer.writeheader()
        writer.writerows(report_rows)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in report_rows:
        grouped[row["Priority"]].append(row)

    lines: list[str] = []
    lines.append("# VocabularyIT Image Priority Report")
    lines.append("")
    lines.append(f"- Celkem fallback polozek: `{len(report_rows)}`")
    lines.append(f"- Zdroj: `{JSON_PATH.relative_to(REPO_ROOT)}`")
    lines.append(f"- CSV report: `{REPORT_CSV_PATH.relative_to(REPO_ROOT)}`")
    lines.append("")
    lines.append("## Souhrn priorit")
    lines.append("")
    for priority in ("A", "B", "C", "D"):
        lines.append(f"- `{priority}`: `{len(grouped[priority])}`")
    lines.append("")
    lines.append("## Kategorie")
    lines.append("")
    for (priority, category), count in sorted(
        category_counter.items(),
        key=lambda item: (PRIORITY_ORDER[item[0][0]], item[0][1]),
    ):
        lines.append(f"- `{priority}` `{category}`: `{count}`")
    lines.append("")

    for priority in ("A", "B", "C", "D"):
        rows_for_priority = grouped[priority]
        lines.append(f"## {PRIORITY_LABEL[priority]}")
        lines.append("")
        if not rows_for_priority:
            lines.append("- Nic")
            lines.append("")
            continue
        lines.append("| Order | IT | CZ | Fallback | Doporučený stem | Kategorie |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in rows_for_priority[:60]:
            suggested = row["SuggestedExistingStem"] or ""
            lines.append(
                f"| {row['Order']} | {row['IT']} | {row['CZ']} | {row['CurrentFallbackStem']} | {suggested} | {row['Category']} |"
            )
        if len(rows_for_priority) > 60:
            lines.append(f"| ... | ... | ... | ... | ... | celkem {len(rows_for_priority)} položek |")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK  {REPORT_MD_PATH}")
    print(f"OK  {REPORT_CSV_PATH}")
    print(f"Fallback items: {len(report_rows)}")
    print(
        "Priority counts:",
        {priority: len(grouped[priority]) for priority in ("A", "B", "C", "D")},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
