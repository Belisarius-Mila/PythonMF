import argparse
import csv
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PICT_DIR = PROJECT_DIR / "Pict"
PICT_NEW_DIR = PROJECT_DIR / "PictNew"
MAPPING_PATH = PICT_DIR / "mapping.json"

LANGUAGES = {
    "fr": {
        "name": "VocabularyFR",
        "vocab_path": PROJECT_DIR / "VocabularyFR" / "VocabularyFR.csv",
        "pict_path": PROJECT_DIR / "VocabularyFR" / "FR_Pict.csv",
        "word_col": "FR",
        "pict_word_col": "FRP",
    },
    "it": {
        "name": "VocabularyIT",
        "vocab_path": PROJECT_DIR / "VocabularyIT" / "VocabularyIT.csv",
        "pict_path": PROJECT_DIR / "VocabularyIT" / "IT_Pict.csv",
        "word_col": "IT",
        "pict_word_col": "ITP",
    },
}

PICT_FIELDS = {
    "fr": ["FRP", "CZP", "ENP", "PD", "PE"],
    "it": ["ITP", "CZP", "ENP", "PD", "PE"],
}

STOP_TOKENS = {
    "a",
    "aby",
    "co",
    "do",
    "i",
    "jak",
    "jaky",
    "je",
    "jsou",
    "k",
    "ke",
    "kde",
    "kdo",
    "kdy",
    "kdyz",
    "ktery",
    "mit",
    "na",
    "nebo",
    "o",
    "od",
    "po",
    "pro",
    "se",
    "si",
    "ta",
    "tak",
    "ten",
    "tento",
    "to",
    "u",
    "v",
    "ve",
    "z",
    "ze",
}


@dataclass
class MappingEntry:
    key: str
    value: str
    key_norm: str
    parts: list[str]
    part_norms: set[str]
    tokens: set[str]


def strip_accents(text):
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text or "")
        if unicodedata.category(ch) != "Mn"
    )


def normalize(text):
    text = strip_accents((text or "").strip().casefold())
    return re.sub(r"[^a-z0-9]+", "", text)


def tokenize(text):
    text = strip_accents((text or "").casefold())
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if len(token) > 1 and token not in STOP_TOKENS
    ]


def split_meaning_parts(text):
    raw = (text or "").strip()
    if not raw:
        return []

    without_parentheses = re.sub(r"\([^)]*\)", " ", raw)
    candidates = [raw, without_parentheses]
    candidates.extend(re.findall(r"\(([^)]*)\)", raw))

    parts = []
    seen = set()
    for candidate in candidates:
        for part in re.split(r"[,/;|]+|\bnebo\b", candidate, flags=re.IGNORECASE):
            part = part.strip(" .!?()[]")
            part_norm = normalize(part)
            if part_norm and part_norm not in seen:
                seen.add(part_norm)
                parts.append(part)
    return parts


def load_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_mapping_entries(mapping_path=MAPPING_PATH):
    with mapping_path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)

    entries = []
    for key, value in mapping.items():
        key = str(key).strip()
        value = str(value).strip()
        if not key or not value:
            continue
        parts = split_meaning_parts(key)
        part_norms = {normalize(part) for part in parts if normalize(part)}
        part_norms.add(normalize(key))
        entries.append(
            MappingEntry(
                key=key,
                value=value,
                key_norm=normalize(key),
                parts=parts,
                part_norms=part_norms,
                tokens=set(tokenize(key)),
            )
        )
    return entries


def discover_pict_stems(pict_dir=PICT_DIR):
    stems = {}
    if not pict_dir.is_dir():
        return stems
    for path in pict_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            continue
        stems[normalize(path.stem)] = path.stem
    return stems


def has_picture(stem, pict_stems):
    return normalize(stem) in pict_stems


def format_mapping(entry, pict_stems):
    status = "obrazek existuje" if has_picture(entry.value, pict_stems) else "obrazek chybi"
    return f"{entry.key} -> {entry.value} ({status})"


def find_exact_mapping(cz, entries):
    norms = {normalize(cz)}
    norms.update(normalize(part) for part in split_meaning_parts(cz))
    norms.discard("")
    return [entry for entry in entries if entry.key_norm in norms or entry.part_norms & norms]


def find_probable_mapping(cz, entries):
    cz_parts = split_meaning_parts(cz) + [cz]
    cz_norms = {normalize(part) for part in cz_parts if normalize(part)}
    cz_tokens = set(tokenize(cz))
    matches = []

    for entry in entries:
        score = 0
        reason = ""

        common_tokens = cz_tokens & entry.tokens
        if common_tokens and (len(common_tokens) >= 2 or max(len(t) for t in common_tokens) >= 4):
            score = 80 + len(common_tokens) * 8 + max(len(t) for t in common_tokens)
            reason = "token: " + ", ".join(sorted(common_tokens))

        for cz_norm in cz_norms:
            for entry_norm in entry.part_norms:
                if len(cz_norm) >= 5 and len(entry_norm) >= 5 and (
                    cz_norm in entry_norm or entry_norm in cz_norm
                ):
                    new_score = 75 + min(len(cz_norm), len(entry_norm))
                    if new_score > score:
                        score = new_score
                        reason = "cast textu"

        best_ratio = 0
        best_pair = None
        for cz_part in cz_parts:
            cz_norm = normalize(cz_part)
            if len(cz_norm) < 5:
                continue
            for entry_part in entry.parts + [entry.key]:
                entry_norm = normalize(entry_part)
                if len(entry_norm) < 5:
                    continue
                ratio = SequenceMatcher(None, cz_norm, entry_norm).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_pair = (cz_part, entry_part)
        if best_ratio >= 0.9:
            new_score = 70 + int(best_ratio * 20)
            if new_score > score:
                score = new_score
                reason = f"podobnost {best_ratio:.2f}: {best_pair[0]} ~ {best_pair[1]}"

        if score:
            matches.append((score, reason, entry))

    matches.sort(key=lambda item: (item[0], item[2].key), reverse=True)
    return matches[:5]


def row_key(row, word_col):
    return ((row.get(word_col) or "").strip(), (row.get("CZ") or "").strip())


def pict_row_key(row, pict_word_col):
    return ((row.get(pict_word_col) or "").strip(), (row.get("CZP") or "").strip())


def load_or_create_pict_rows(config, language):
    path = config["pict_path"]
    fields = PICT_FIELDS[language]
    if not path.exists():
        return []
    rows = load_csv(path)
    repaired = []
    for raw in rows:
        row = {field: (raw.get(field) or "").strip() for field in fields}
        if not any(row.values()):
            continue
        row["PE"] = "ano" if row["PE"].casefold() in {"ano", "yes", "true", "1", "☑"} else "ne"
        repaired.append(row)
    return repaired


def sync_pict_rows(vocab_rows, pict_rows, config, language):
    word_col = config["word_col"]
    pict_word_col = config["pict_word_col"]
    existing = {pict_row_key(row, pict_word_col) for row in pict_rows}
    added = []
    for vocab_row in vocab_rows:
        key = row_key(vocab_row, word_col)
        if key in existing:
            continue
        new_row = {
            pict_word_col: key[0],
            "CZP": key[1],
            "ENP": "",
            "PD": "",
            "PE": "ne",
        }
        pict_rows.append(new_row)
        existing.add(key)
        added.append(new_row)
    return added


def build_audit_for_language(language, entries, pict_stems, sync=False):
    config = LANGUAGES[language]
    word_col = config["word_col"]
    pict_word_col = config["pict_word_col"]
    vocab_rows = load_csv(config["vocab_path"])
    pict_rows = load_or_create_pict_rows(config, language)
    original_pict_count = len(pict_rows)
    added_rows = sync_pict_rows(vocab_rows, pict_rows, config, language)

    if sync and added_rows:
        write_csv(config["pict_path"], pict_rows, PICT_FIELDS[language])

    pict_by_key = {pict_row_key(row, pict_word_col): row for row in pict_rows}

    direct_mapping = []
    mapping_without_image = []
    direct_pict = []
    probable_mapping = []
    unresolved = []
    already_ok = []

    for vocab_row in vocab_rows:
        key = row_key(vocab_row, word_col)
        pict_row = pict_by_key.get(key)
        pict_data_missing = pict_row is None
        if pict_row is None:
            pict_row = {pict_word_col: key[0], "CZP": key[1], "ENP": "", "PD": "", "PE": "ne"}

        enp = (pict_row.get("ENP") or "").strip()
        pe = (pict_row.get("PE") or "").strip().casefold()
        cz = key[1]

        if pe == "ano" and (not enp or has_picture(enp, pict_stems)):
            already_ok.append((vocab_row, pict_row))
            continue

        exact = find_exact_mapping(cz, entries)
        exact_with_picture = [entry for entry in exact if has_picture(entry.value, pict_stems)]
        exact_without_picture = [entry for entry in exact if not has_picture(entry.value, pict_stems)]

        if enp and has_picture(enp, pict_stems):
            direct_pict.append((vocab_row, pict_row, [enp]))
        elif exact_with_picture:
            direct_mapping.append((vocab_row, pict_row, exact_with_picture))
        elif exact_without_picture:
            mapping_without_image.append((vocab_row, pict_row, exact_without_picture))
        else:
            probable = [
                item for item in find_probable_mapping(cz, entries)
                if has_picture(item[2].value, pict_stems)
            ]
            if probable:
                probable_mapping.append((vocab_row, pict_row, probable))
            else:
                unresolved.append((vocab_row, pict_row, pict_data_missing))

    return {
        "language": language,
        "config": config,
        "vocab_count": len(vocab_rows),
        "pict_count": original_pict_count,
        "audit_pict_count": len(pict_rows),
        "added_rows": added_rows,
        "already_ok": already_ok,
        "direct_pict": direct_pict,
        "direct_mapping": direct_mapping,
        "mapping_without_image": mapping_without_image,
        "probable_mapping": probable_mapping,
        "unresolved": unresolved,
    }


def format_vocab_row(vocab_row, pict_row, config):
    order = (vocab_row.get("Order") or "").strip()
    word = (vocab_row.get(config["word_col"]) or "").strip()
    cz = (vocab_row.get("CZ") or "").strip()
    enp = (pict_row.get("ENP") or "").strip()
    pd = (pict_row.get("PD") or "").strip()
    pe = (pict_row.get("PE") or "").strip()
    extras = []
    if enp:
        extras.append(f"ENP={enp}")
    if pe:
        extras.append(f"PE={pe}")
    if pd:
        extras.append(f"PD={pd}")
    suffix = " | " + " | ".join(extras) if extras else ""
    return f"{order}\t{word}\t{cz}{suffix}"


def write_section(lines, title, rows):
    lines.append("")
    lines.append(title)
    lines.append("-" * len(title))
    if not rows:
        lines.append("Nic nenalezeno.")
        return
    lines.extend(rows)


def build_report(audits, report_date, sync, pict_stems):
    date_label = report_date.strftime("%d.%m.%Y")
    lines = [
        f"NewVocabulary audit - {date_label}",
        "",
        f"mapping.json: {MAPPING_PATH}",
        f"Pict: {PICT_DIR}",
        f"Synchronizace Pict CSV: {'ano' if sync else 'ne'}",
    ]

    for audit in audits:
        config = audit["config"]
        lines.append("")
        lines.append("=" * 80)
        lines.append(config["name"])
        lines.append("=" * 80)
        lines.append(f"Vocabulary rows: {audit['vocab_count']}")
        lines.append(f"Aktualni Pict CSV rows: {audit['pict_count']}")
        lines.append(f"Pict CSV rows po navrzenem doplneni: {audit['audit_pict_count']}")
        lines.append(f"Nove radky k doplneni do Pict CSV: {len(audit['added_rows'])}")
        lines.append(f"Uz OK: {len(audit['already_ok'])}")
        lines.append(f"ENP ukazuje na existujici obrazek: {len(audit['direct_pict'])}")
        lines.append(f"Shoda v mapping.json + obrazek existuje: {len(audit['direct_mapping'])}")
        lines.append(f"Shoda v mapping.json, ale obrazek chybi: {len(audit['mapping_without_image'])}")
        lines.append(f"Pravdepodobna shoda v mapping.json + obrazek existuje: {len(audit['probable_mapping'])}")
        lines.append(f"Bez navrhu: {len(audit['unresolved'])}")

        write_section(
            lines,
            "Nove radky chybejici v Pict CSV",
            [
                f"{row.get(config['pict_word_col'], '')}\t{row.get('CZP', '')}"
                for row in audit["added_rows"]
            ],
        )

        write_section(
            lines,
            "ENP uz ukazuje na existujici obrazek v Pict",
            [
                f"{format_vocab_row(vocab, pict, config)} | Pict: {', '.join(stems)}"
                for vocab, pict, stems in audit["direct_pict"]
            ],
        )

        write_section(
            lines,
            "Prima shoda v mapping.json a obrazek existuje",
            [
                f"{format_vocab_row(vocab, pict, config)} | "
                + "; ".join(format_mapping(entry, pict_stems) for entry in matches)
                for vocab, pict, matches in audit["direct_mapping"]
            ],
        )

        write_section(
            lines,
            "Prima shoda v mapping.json, ale obrazek chybi",
            [
                f"{format_vocab_row(vocab, pict, config)} | "
                + "; ".join(format_mapping(entry, pict_stems) for entry in matches)
                for vocab, pict, matches in audit["mapping_without_image"]
            ],
        )

        write_section(
            lines,
            "Pravdepodobna shoda v mapping.json",
            [
                f"{format_vocab_row(vocab, pict, config)} | "
                + "; ".join(
                    f"{format_mapping(entry, pict_stems)}, {reason}, score={score}"
                    for score, reason, entry in matches
                )
                for vocab, pict, matches in audit["probable_mapping"]
            ],
        )

        write_section(
            lines,
            "Bez navrhu - kandidat pro novy obrazek",
            [
                format_vocab_row(vocab, pict, config)
                + (" | chybi radek v Pict CSV" if missing_pict_row else "")
                for vocab, pict, missing_pict_row in audit["unresolved"]
            ],
        )

    return "\n".join(lines) + "\n"


def run_audit(languages, sync=False, report_date=None):
    report_date = report_date or datetime.now()
    PICT_NEW_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_mapping_entries()
    pict_stems = discover_pict_stems()
    audits = [
        build_audit_for_language(language, entries, pict_stems, sync=sync)
        for language in languages
    ]
    report = build_report(audits, report_date, sync, pict_stems)
    report_path = PICT_NEW_DIR / f"NewVocabulary{report_date.strftime('%d%m%Y')}.txt"
    report_path.write_text(report, encoding="utf-8")
    return report_path, audits


def parse_args():
    parser = argparse.ArgumentParser(description="Audit VocabularyFR/IT picture mapping candidates.")
    parser.add_argument(
        "--language",
        choices=["fr", "it", "all"],
        default="all",
        help="Which vocabulary to audit.",
    )
    parser.add_argument(
        "--sync-pict-csv",
        action="store_true",
        help="Append missing vocabulary rows to FR_Pict.csv / IT_Pict.csv before auditing.",
    )
    parser.add_argument(
        "--date",
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    languages = ["fr", "it"] if args.language == "all" else [args.language]
    report_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    report_path, audits = run_audit(languages, sync=args.sync_pict_csv, report_date=report_date)

    print(f"Report: {report_path}")
    for audit in audits:
        review_matches = (
            len(audit["direct_pict"])
            + len(audit["direct_mapping"])
            + len(audit["mapping_without_image"])
            + len(audit["probable_mapping"])
        )
        print(
            f"{audit['config']['name']}: "
            f"added_rows={len(audit['added_rows'])}, "
            f"review_matches={review_matches}, "
            f"unresolved={len(audit['unresolved'])}"
        )


if __name__ == "__main__":
    main()
