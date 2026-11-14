"""Catalog classification, kept separate from legacy user tags.

Conspectus numbers come from the selected record's MARC 072, never from
search-wide facets (which may describe other editions).
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree


_TABLE = json.loads(Path(__file__).with_name("book_conspectus.json").read_text(encoding="utf-8"))
SUBJECTS = tuple(_TABLE["subjects"])
_GROUPS = _TABLE["groups"]


def labels(value, *, limit=30, length=120):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError("Neplatné třídění knihy.")
    result, seen = [], set()
    for text in value:
        if not isinstance(text, str) or len(text) > length:
            raise ValueError("Neplatný údaj třídění knihy.")
        clean = " ".join(text.split())
        if clean and clean.casefold() not in seen:
            seen.add(clean.casefold())
            result.append(clean)
    return result


def normalize_manual_subjects(value):
    result = labels(value, limit=26)
    if any(subject not in SUBJECTS for subject in result):
        raise ValueError("Vyber obor z nabídky Konspektu.")
    return result


def _isbn13(value):
    value = re.sub(r"[\s-]", "", str(value)).upper()
    if re.fullmatch(r"[0-9]{9}[0-9X]", value):
        stem = "978" + value[:9]
        return stem + str((-sum(int(c) * (1 if n % 2 == 0 else 3) for n, c in enumerate(stem))) % 10)
    return value


def normalize_classification(value, isbn):
    if not isinstance(value, dict) or set(value) != {"version", "isbn", "subjects", "genres", "topics", "languages", "source_url"} or type(value.get("version")) is not int or value["version"] != 1:
        raise ValueError("Neplatný formát třídění knihy.")
    if not isinstance(value["isbn"], str) or _isbn13(value["isbn"]) != _isbn13(isbn):
        raise ValueError("Třídění patří jinému ISBN. Znovu knihu dohledej.")
    source = value["source_url"]
    if not isinstance(source, str) or len(source) > 1500:
        raise ValueError("Neplatný zdroj třídění knihy.")
    parsed = urlsplit(source)
    if parsed.scheme != "https" or parsed.netloc != "www.knihovny.cz" or not parsed.path.startswith("/Record/") or not parsed.path[8:] or parsed.query or parsed.fragment:
        raise ValueError("Neplatný zdroj třídění knihy.")
    result = {"version": 1, "isbn": _isbn13(isbn), "source_url": source}
    for key in ("subjects", "genres", "topics", "languages"):
        result[key] = labels(value[key], limit=26 if key == "subjects" else 30)
    if any(subject not in SUBJECTS for subject in result["subjects"]):
        raise ValueError("Neznámý obor knihy.")
    return result


def record_classification(record, *, isbn, source_url):
    subjects, marc_languages = [], []
    xml = record.get("fullRecord")
    if isinstance(xml, str) and len(xml) <= 256 * 1024 and not re.search(r"<!\s*(?:DOCTYPE|ENTITY)", xml, re.I):
        try:
            root = ElementTree.fromstring(xml)
            records = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "record"]
            if len(records) == 1:
                for field in records[0]:
                    if field.get("tag") == "041":
                        marc_languages.extend((sub.text or "").strip() for sub in field if sub.get("code") == "a")
                if not marc_languages:
                    for field in records[0]:
                        if field.get("tag") == "008" and len(field.text or "") >= 38:
                            marc_languages.append(field.text[35:38])
                for field in records[0]:
                    if field.tag.rsplit("}", 1)[-1] != "datafield" or field.get("tag") != "072":
                        continue
                    subfields = [(sub.get("code"), (sub.text or "").strip()) for sub in field]
                    if not any(code == "2" and text.casefold() == "konspekt" for code, text in subfields):
                        continue
                    # Exact official group lookup; no prefix/keyword inference.
                    numbers = [int(text) for code, text in subfields if code == "9" and 1 <= len(text) <= 2 and text.isascii() and text.isdigit() and 1 <= int(text) <= 26]
                    if not numbers:
                        numbers = [_GROUPS[text] for code, text in subfields if code == "a" and text in _GROUPS]
                    for number in numbers:
                        label = SUBJECTS[number - 1]
                        if label not in subjects:
                            subjects.append(label)
        except ElementTree.ParseError:
            pass
    typed = {"genre/form": [], "topic": []}
    headings = record.get("subjectsExtended")
    for entry in headings if isinstance(headings, list) else []:
        if not isinstance(entry, dict) or entry.get("type") not in typed or not isinstance(entry.get("heading"), list):
            continue
        parts = [" ".join(part.split()) for part in entry["heading"] if isinstance(part, str) and part.strip()]
        # Keep the whole topical heading, so subdivisions retain their meaning.
        text = (parts[0] if entry["type"] == "genre/form" else " — ".join(parts)) if parts else ""
        if text and len(text) <= 120 and len(typed[entry["type"]]) < 30:
            typed[entry["type"]].append(text)
    languages = record.get("languages")
    languages = [text for text in languages if isinstance(text, str) and len(text) <= 120][:30] if isinstance(languages, list) else []
    if not languages:
        names = {"cze": "čeština", "ces": "čeština", "eng": "angličtina", "fre": "francouzština", "fra": "francouzština", "ger": "němčina", "deu": "němčina", "slo": "slovenština", "slk": "slovenština"}
        languages = [names.get(code, code) for code in marc_languages if re.fullmatch(r"[a-z]{3}", code) and code not in {"und", "zxx"}][:30]
    return normalize_classification({"version": 1, "isbn": isbn, "subjects": subjects,
        "genres": labels(typed["genre/form"]), "topics": labels(typed["topic"]),
        "languages": languages, "source_url": source_url}, isbn)
