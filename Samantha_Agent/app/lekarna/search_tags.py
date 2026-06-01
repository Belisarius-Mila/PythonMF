from __future__ import annotations

import csv
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .service import DEFAULT_DOMACI_LEKY_CSV, FIELD_NAMES


SEARCH_TAG_FIELD = "Search_Tags"


@dataclass(frozen=True)
class SearchTagsApplyResult:
    csv_path: Path
    backup_path: Path
    updated_rows: int
    total_rows: int


TAG_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("kasel", "vykasl", "hlen", "zahlen", "prudu"), ("kašel", "suchý kašel", "dráždivý kašel", "hlen", "zahlenění")),
    (("ryma", "nos", "dutin", "xylometazolin"), ("rýma", "ucpaný nos", "nos", "dutiny", "nachlazení")),
    (("nachlaz", "paralen grip"), ("nachlazení", "chřipka")),
    (("chrip",), ("chřipka", "nachlazení")),
    (("horeck", "teplot", "zimnic", "paracetamol"), ("horečka", "teplota", "zimnice", "chřipka")),
    (("bolest", "ibuprofen", "diclofenac", "diklofenak", "nimesil", "novalgin"), ("bolest", "bolest hlavy", "bolest zad", "bolest svalů", "bolest kloubů")),
    (("krk", "mandl", "pastilk", "vincentka", "lugol"), ("bolest v krku", "škrábání v krku", "dutina ústní")),
    (("alerg", "sved", "stip", "kopriv", "vyrazk", "fenistil"), ("alergie", "svědění", "štípnutí", "kopřivka", "vyrážka")),
    (("prujem", "streva", "traveni", "probiotik", "carbo", "imodium"), ("průjem", "trávení", "střeva", "žaludek")),
    (("zalud", "reflux", "zaha", "omeprazol"), ("žaludek", "pálení žáhy", "reflux", "trávení")),
    (("nadym", "febichol", "pancreolan", "sliniv"), ("nadýmání", "trávení", "žlučník", "slinivka")),
    (("modrin", "otok", "podlit", "heparin", "hirudoid"), ("modřina", "otok", "podlitina", "úraz")),
    (("kuze", "pokoz", "gel", "ekzem", "popalen"), ("kůže", "pokožka", "svědění", "drobné popálení")),
    (("rana", "riznut", "dezinfek"), ("rána", "říznutí", "dezinfekce")),
    (("nevolnost", "zvracen", "kinedryl", "cestov"), ("cestovní nevolnost", "nevolnost", "zvracení")),
    (("oko", "ocni", "ophthalm", "visine", "occusept"), ("oči", "oční kapky", "zarudlé oči")),
    (("ucho", "usni", "maz", "akustone"), ("uši", "ucho", "ušní maz")),
    (("spanek", "nespav", "nerv", "kozlik", "melatonin", "trezalka"), ("spánek", "nespavost", "uklidnění", "nervozita")),
    (("tlak", "srdce", "prestarum", "tonarssa", "atoris"), ("tlak", "vysoký tlak", "srdce", "osobní lék")),
    (("redeni krve", "krev", "godasal", "stacyl", "anopyrin"), ("ředění krve", "krev", "srdce", "osobní lék")),
    (("dna", "milurit", "mocov"), ("dna", "kyselina močová", "osobní lék")),
    (("jatra", "zluc", "ursosan", "silymarin", "ostropestrec"), ("játra", "žluč", "trávení")),
    (("antibiotik", "amoxiklav"), ("antibiotikum", "pouze podle lékaře", "osobní lék")),
    (("vitamin", "mineral", "horcik", "magnesium", "zinek", "selen"), ("vitamíny", "minerály", "doplněk stravy")),
)


def build_search_tags(row: Mapping[str, str]) -> str:
    haystack = normalize(
        " ".join(
            [
                row.get("nazev", ""),
                row.get("ucinna_latka", ""),
                row.get("forma", ""),
                row.get("kategorie", ""),
                row.get("pouziti", ""),
                row.get("poznamky", ""),
            ]
        )
    )
    tags: list[str] = []
    add_tags(tags, split_free_text(row.get("kategorie", "")))
    add_tags(tags, split_free_text(row.get("pouziti", "")))
    for needles, rule_tags in TAG_RULES:
        if any(matches_needle(haystack, needle) for needle in needles):
            add_tags(tags, rule_tags)
    if normalize(row.get("pro_koho", "")).strip():
        pro_koho = normalize(row.get("pro_koho", ""))
        if "mila" in pro_koho or "jana" in pro_koho:
            add_tags(tags, ("osobní lék",))
    return "; ".join(tags)


def apply_search_tags_to_csv(csv_path: Path = DEFAULT_DOMACI_LEKY_CSV) -> SearchTagsApplyResult:
    csv_path = csv_path.resolve()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{field: (row.get(field) or "").strip() for field in FIELD_NAMES} for row in reader]

    backup_path = backup_csv(csv_path)
    updated = 0
    for row in rows:
        tags = build_search_tags(row)
        if row.get(SEARCH_TAG_FIELD, "") != tags:
            row[SEARCH_TAG_FIELD] = tags
            updated += 1

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)

    return SearchTagsApplyResult(
        csv_path=csv_path,
        backup_path=backup_path,
        updated_rows=updated,
        total_rows=len(rows),
    )


def split_free_text(value: str) -> tuple[str, ...]:
    parts = re.split(r"[/;,|]+", value)
    return tuple(part.strip() for part in parts if len(part.strip()) >= 3)


def add_tags(tags: list[str], values: tuple[str, ...] | list[str]) -> None:
    existing = {normalize(tag) for tag in tags}
    for value in values:
        cleaned = " ".join(str(value).split())
        normalized = normalize(cleaned)
        if not cleaned or normalized in existing:
            continue
        tags.append(cleaned)
        existing.add(normalized)


def matches_needle(haystack: str, needle: str) -> bool:
    normalized = normalize(needle)
    if not normalized:
        return False
    if " " in normalized:
        return normalized in haystack
    return re.search(rf"\b{re.escape(normalized)}[a-z0-9]*\b", haystack) is not None


def backup_csv(csv_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"{csv_path.stem}.backup_before_search_tags_{stamp}{csv_path.suffix}")
    shutil.copy2(csv_path, backup_path)
    return backup_path


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", str(value).casefold())
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()
