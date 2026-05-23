#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "private" / "email_seznam" / "seznam_pojisteni_smlouvy_2011_2026.csv"

NOISE_DOMAINS = (
    "ods.cz",
    "alza.cz",
    "megaknihy.cz",
    "drmax.cz",
    "datart.cz",
    "momkids.cz",
    "milionchvilek.cz",
)
STRONG_WORDS = (
    "poji",
    "pojist",
    "smlouv",
    "zelen",
    "daňové potvrzení",
    "danove potvrzeni",
    "dokumentace",
    "předsmluv",
    "predsmluv",
    "výroční",
    "vyrocni",
    "zánik",
    "zanik",
    "výpově",
    "vypove",
)
STRONG_SENDERS = (
    "generali",
    "koop",
    "cpp",
    "čpp",
    "rixo",
    "kbps",
    "kb.cz",
    "kbinfo",
    "komercpoj",
    "metlife",
    "axa",
    "top-pojisteni",
    "porovnej24",
    "moneta",
    "rb.cz",
    "rsts",
    "generalipenze",
    "pojisteni",
    "pojišťovna",
    "pojistovna",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vytvori prioritni vyber ze Seznam e-mail search CSV.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-prefix", default="seznam_pojisteni_smlouvy_priority_2011_2026")
    parser.add_argument("--min-score", type=int, default=4)
    parser.add_argument("--markdown-limit", type=int, default=120)
    parser.add_argument(
        "--profile",
        choices=("broad", "insurance"),
        default="broad",
        help="broad = pojisteni/smlouvy, insurance = uzsi pojistovaci vyber",
    )
    return parser.parse_args()


def low(value: str | None) -> str:
    return (value or "").casefold()


def attachment_count(row: dict[str, str]) -> int:
    try:
        return int(row.get("attachment_count") or 0)
    except ValueError:
        return 0


def is_noise(row: dict[str, str]) -> bool:
    sender = low(row.get("sender"))
    subject = low(row.get("subject"))
    if not any(domain in sender for domain in NOISE_DOMAINS):
        return False
    return not any(word in subject for word in ("poji", "smlouv", "pojist"))


def score(row: dict[str, str]) -> int:
    sender = low(row.get("sender"))
    subject = low(row.get("subject"))
    names = low(row.get("attachment_names"))
    terms = low(row.get("matched_terms"))

    value = 0
    if attachment_count(row) > 0:
        value += 3
    if any(item in sender for item in STRONG_SENDERS):
        value += 4
    if any(item in subject for item in STRONG_WORDS):
        value += 4
    if any(item in names for item in ("sml", "poj", "zelen", "dan", "ipid", "memorandum", "podm")):
        value += 2
    if "pripojis" in terms and not any(item in subject + sender + names for item in ("poji", "pojist", "smlouv", "zelen")):
        value -= 5
    if is_noise(row):
        value -= 5
    return value


def insurance_match(row: dict[str, str]) -> bool:
    text = " ".join(
        (
            row.get("sender", ""),
            row.get("subject", ""),
            row.get("attachment_names", ""),
        )
    ).casefold()
    terms = (
        "poji",
        "pojist",
        "rixo",
        "generali",
        "koop",
        "cpp",
        "čpp",
        "metlife",
        "axa",
        "top-pojisteni",
        "porovnej24",
        "komercpoj",
        "generalipenze",
    )
    return any(term in text for term in terms)


def main() -> int:
    args = parse_args()
    rows = list(csv.DictReader(args.input.open(encoding="utf-8")))
    if not rows:
        raise SystemExit("Vstupni CSV je prazdne.")

    if args.profile == "insurance":
        filtered = [row for row in rows if insurance_match(row)]
    else:
        filtered = [row for row in rows if score(row) >= args.min_score]
    filtered.sort(key=lambda row: (attachment_count(row), row.get("date", "")), reverse=True)

    out_csv = args.input.parent / f"{args.out_prefix}.csv"
    out_md = args.input.parent / f"{args.out_prefix}.md"

    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(filtered)

    lines = [
        "# Prioritni vyber ze Seznam hledani",
        "",
        f"Zdroj: `{args.input.name}`",
        f"Puvodni vysledky: {len(rows)}",
        f"Prioritni kandidati: {len(filtered)}",
        "",
    ]
    for index, row in enumerate(filtered[: args.markdown_limit], start=1):
        lines.extend(
            [
                f"## {index}. {row.get('subject') or '(bez predmetu)'}",
                "",
                f"- Datum: {row.get('date', '')}",
                f"- Od: {row.get('sender', '')}",
                f"- Slozka/UID: `{row.get('folder', '')}` / `{row.get('uid', '')}`",
                f"- Prilohy: {row.get('attachment_count', '')} {row.get('attachment_names', '')}",
                f"- Nalezene vyrazy: {row.get('matched_terms', '')}",
                "",
            ]
        )
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Puvodni vysledky: {len(rows)}")
    print(f"Prioritni kandidati: {len(filtered)}")
    print(f"CSV: {out_csv}")
    print(f"Markdown: {out_md}")
    print("Top kandidati:")
    for row in filtered[:20]:
        print(
            f"- {row.get('date', '')} UID {row.get('uid', '')} "
            f"prilohy {row.get('attachment_count', '')}: {row.get('subject', '')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
