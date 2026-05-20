from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path
from dataclasses import replace
from datetime import datetime

from .models import DomaciLek, DomaciLekMatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOMACI_LEKY_CSV = PROJECT_ROOT / "data" / "lekarna" / "domaci_leky.csv"
LOW_CONFIDENCE_WORDS = ("nizka", "stredni")
UNKNOWN_EXPIRATION_VALUES = ("", "nezjisteno", "neuvedeno", "nezadano", "neznamo")
UNKNOWN_LOCATION_VALUES = ("", "nezadano", "neuvedeno", "nezjisteno")
UNKNOWN_LOCATION_MARKERS = ("umisteni nezadano",)
FIELD_NAMES = tuple(DomaciLek.__dataclass_fields__.keys())
RETIRE_CONFIRMATION_PHRASE = "Potvrzuji vyrazeni leku"
QUERY_ALIASES = {
    "bolest": ("bolest", "bolesti", "zanet", "kloub", "klouby", "zad", "zada"),
    "horecka": ("horecka", "teplota", "nachlazeni", "chripka"),
    "kasel": ("kasel", "nachlazeni", "chripka"),
    "alergie": ("alergie", "alergicka"),
    "prujem": ("prujem", "traveni", "zaludek", "streva"),
    "nachlazeni": ("nachlazeni", "chripka", "ryma", "horecka", "kasel"),
    "traveni": ("traveni", "nadymani", "zaludek", "prujem", "probiotika"),
    "modriny": ("modriny", "otoky", "otok", "podlitiny", "uraz"),
}
AUDIT_SECTIONS = (
    ("missing_expiration", "Polozky s chybejici nebo nezjistenou expiraci"),
    ("unknown_location", "Polozky s neurcenym umistenim"),
    ("needs_verification", "Polozky `nutno_overit=ano`"),
    ("loose_without_box", "Polozky `ZBYTKY_BEZ_KRABICKY`"),
    ("low_confidence", "Polozky s nizkou/stredni jistotou cteni"),
    ("antibiotics", "Antibiotika"),
    ("blood_thinners", "Leciva souvisejici s redenim krve"),
)


def load_domaci_leky(csv_path: Path = DEFAULT_DOMACI_LEKY_CSV) -> list[DomaciLek]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            DomaciLek(**{field: (row.get(field) or "").strip() for field in FIELD_NAMES})
            for row in reader
        ]


def search_domaci_leky_records(
    query: str,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    limit: int = 10,
) -> list[DomaciLekMatch]:
    query_terms = _expand_query_terms(query)
    if not query_terms:
        return []

    matches: list[DomaciLekMatch] = []
    for lek in load_domaci_leky(csv_path):
        if _is_retired(lek):
            continue
        score, reasons = _score_record(lek, query_terms)
        if score <= 0:
            continue
        matches.append(
            DomaciLekMatch(
                lek=lek,
                score=score,
                reasons=tuple(reasons),
                warnings=tuple(_safety_warnings(lek)),
            )
        )

    matches.sort(key=lambda match: (-match.score, _normalize(match.lek.nazev)))
    return matches[: max(1, limit)]


def format_domaci_leky_search(
    query: str,
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    limit: int = 10,
) -> str:
    matches = search_domaci_leky_records(query=query, csv_path=csv_path, limit=limit)
    if not matches:
        return (
            f"V domaci lekarne jsem pro dotaz `{query}` nenasla zadnou evidovanou "
            "polozku. Evidence je jen inventar; pri zdravotnich potizich over lek "
            "podle pribalove informace nebo u lekarnika/lekare."
        )

    lines = [
        f"Domaci lekarna - vysledky pro dotaz: {query}",
        "Toto je jen read-only inventarni prehled, ne doporuceni lecby ani davkovani.",
        "",
    ]

    for index, match in enumerate(matches, start=1):
        lek = match.lek
        lines.extend(
            [
                f"{index}. {lek.nazev or 'Nazev neuveden'}",
                f"   Souvislost podle evidence: {_join_nonempty(lek.kategorie, lek.pouziti)}",
                f"   Ucinna latka / sila / forma: {_join_nonempty(lek.ucinna_latka, lek.sila, lek.forma)}",
                f"   Kde je: {lek.umisteni or 'umisteni neuvedeno'}",
                f"   Expirace: {lek.expirace or 'neuvedena'}",
                f"   Mnozstvi: {lek.mnozstvi or 'neuvedeno'}",
                f"   Proc se naslo: {', '.join(match.reasons)}",
            ]
        )
        if match.warnings:
            lines.append(f"   Nejistoty: {'; '.join(match.warnings)}")
        lines.append("")

    lines.extend(
        [
            "Bezpecnost:",
            "- Neuvadim davkovani. Over ho v pribalove informaci nebo u lekarnika/lekare.",
            "- U deti, tehotenstvi, chronickych nemoci, alergii, kombinaci leku, silnych nebo trvajicich potizi res lekare/lekarnika.",
            "- Polozky po expiraci, bez expirace, bez krabicky nebo s `nutno_overit=ano` nepouzivej bez overeni.",
        ]
    )
    return "\n".join(lines)


def audit_domaci_lekarna_records(
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
) -> dict[str, list[DomaciLek]]:
    audit = {key: [] for key, _label in AUDIT_SECTIONS}
    for lek in load_domaci_leky(csv_path):
        if _has_missing_expiration(lek):
            audit["missing_expiration"].append(lek)
        if _has_unknown_location(lek):
            audit["unknown_location"].append(lek)
        if _normalize(lek.nutno_overit) == "ano":
            audit["needs_verification"].append(lek)
        if _normalize(lek.stav_obalu) == "zbytky_bez_krabicky":
            audit["loose_without_box"].append(lek)
        if _has_low_or_medium_confidence(lek):
            audit["low_confidence"].append(lek)
        if _is_antibiotic(lek):
            audit["antibiotics"].append(lek)
        if _is_blood_thinner_related(lek):
            audit["blood_thinners"].append(lek)
    return audit


def format_domaci_lekarna_audit(
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
) -> str:
    records = load_domaci_leky(csv_path)
    audit = audit_domaci_lekarna_records(csv_path)
    lines = [
        "Audit domaci lekarny - read-only kontrolni checklist",
        f"Celkem evidovanych polozek: {len(records)}",
        "Toto je inventarni kontrola evidence, ne doporuceni lecby, vhodnosti ani davkovani.",
        "",
        "Doporuceny fyzicky postup:",
        "- Vzit krabicky/blistry do ruky a opsat expiraci, silu, formu a umisteni.",
        "- U polozek bez krabicky overit skutecny nazev podle blistru/lahvicky nebo je vyradit z aktivniho pouziti.",
        "- Antibiotika a leciva souvisejici s redenim krve drzet jako zvlast citlive polozky k overeni s lekarem/lekarnikem.",
        "",
    ]

    for key, label in AUDIT_SECTIONS:
        items = audit[key]
        lines.append(f"[ ] {label}: {len(items)}")
        if items:
            for lek in sorted(items, key=lambda item: _normalize(item.nazev)):
                lines.append(f"    - {_audit_item_line(lek)}")
        else:
            lines.append("    - Bez nalezu")
        lines.append("")

    lines.extend(
        [
            "Bezpecnost:",
            "- Audit nic nezapisuje do CSV ani do jinych dat.",
            "- Neuvadi davkovani a neposuzuje vhodnost pro konkretni osobu.",
            "- Davkovani, kontraindikace, kombinace leku a pouziti u deti over v pribalove informaci nebo u lekarnika/lekare.",
        ]
    )
    return "\n".join(lines)


def format_domaci_lek_retire_preview(
    query: str,
    reason: str = "",
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
) -> str:
    candidates = _find_retire_candidates(query=query, csv_path=csv_path)
    if not candidates:
        return (
            f"Vyrazeni leku - pro dotaz `{query}` jsem nenasla jednu aktivni polozku. "
            "Zkus presnejsi nazev, silu nebo cast nazvu."
        )
    if len(candidates) > 1:
        lines = [
            f"Vyrazeni leku - dotaz `{query}` je nejednoznacny.",
            "Upresni, kterou polozku chces vyradit:",
            "",
        ]
        lines.extend(_retire_candidate_line(index, lek) for index, lek in enumerate(candidates, start=1))
        return "\n".join(lines)

    lek = candidates[0]
    reason_text = reason.strip() or "duvod neuveden"
    return "\n".join(
        [
            "Vyrazeni leku - navrh zmeny",
            "Nic zatim nezapisuji do CSV.",
            "",
            _retire_candidate_line(1, lek),
            "",
            "Po potvrzeni se radek nesmaze, jen oznaci jako vyradeny:",
            f"- mnozstvi: `{lek.mnozstvi or 'neuvedeno'}` -> `vyradeno`",
            f"- umisteni: `{lek.umisteni or 'neuvedeno'}` -> `vyradeno`",
            f"- poznamky: prida se `Vyradeno YYYY-MM-DD: {reason_text}`",
            "",
            f"Pro zapis posli potvrzeni obsahujici: `{RETIRE_CONFIRMATION_PHRASE}`",
        ]
    )


def format_retire_domaci_lek(
    query: str,
    reason: str = "",
    csv_path: Path = DEFAULT_DOMACI_LEKY_CSV,
    *,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    if not user_confirmed or RETIRE_CONFIRMATION_PHRASE.casefold() not in confirmation_text.casefold():
        raise ValueError(
            "Vyrazeni leku zapisuje do CSV a vyzaduje potvrzeni: "
            f"{RETIRE_CONFIRMATION_PHRASE}"
        )

    csv_path = csv_path.resolve()
    _ensure_within_project(csv_path)
    candidates = _find_retire_candidates(query=query, csv_path=csv_path)
    if not candidates:
        raise ValueError(f"Pro dotaz `{query}` jsem nenasla jednu aktivni polozku k vyrazeni.")
    if len(candidates) > 1:
        names = ", ".join(lek.nazev for lek in candidates[:8])
        raise ValueError(f"Dotaz `{query}` je nejednoznacny. Upresni jednu polozku: {names}")

    target = candidates[0]
    rows = load_domaci_leky(csv_path)
    backup_path = _backup_csv_for_retire(csv_path)
    reason_text = reason.strip() or "duvod neuveden"
    stamp = datetime.now().strftime("%Y-%m-%d")
    changed = 0
    updated_rows: list[DomaciLek] = []

    for lek in rows:
        if _same_inventory_item(lek, target) and not _is_retired(lek):
            note = _append_note(lek.poznamky, f"Vyradeno {stamp}: {reason_text}")
            updated_rows.append(
                replace(
                    lek,
                    mnozstvi="vyradeno",
                    umisteni="vyradeno",
                    nutno_overit="ano",
                    poznamky=note,
                )
            )
            changed += 1
        else:
            updated_rows.append(lek)

    if changed != 1:
        raise ValueError(f"Ocekavala jsem zmenu 1 radku, ale zmeneno bylo: {changed}")

    _write_domaci_leky(csv_path, updated_rows)
    return "\n".join(
        [
            "Vyrazeni leku - hotovo",
            f"Polozka: {target.nazev}",
            f"Sila / forma: {_join_nonempty(target.sila, target.forma)}",
            f"Zaloha CSV: {backup_path}",
            "Radek nebyl smazan; je oznacen jako `vyradeno`.",
        ]
    )


def _score_record(lek: DomaciLek, query_terms: set[str]) -> tuple[int, list[str]]:
    fields = {
        "nazev": lek.nazev,
        "kategorie": lek.kategorie,
        "pouziti": lek.pouziti,
        "ucinna latka": lek.ucinna_latka,
        "poznamky": lek.poznamky,
    }
    weights = {
        "nazev": 4,
        "kategorie": 5,
        "pouziti": 5,
        "ucinna latka": 3,
        "poznamky": 1,
    }
    score = 0
    reasons: list[str] = []
    for label, value in fields.items():
        normalized_value = _normalize(value)
        matched_terms = sorted(term for term in query_terms if term and term in normalized_value)
        if not matched_terms:
            continue
        score += weights[label] * len(matched_terms)
        reasons.append(f"{label}: {', '.join(matched_terms[:4])}")
    return score, reasons


def _find_retire_candidates(query: str, csv_path: Path) -> list[DomaciLek]:
    query_terms = _expand_query_terms(query)
    normalized_query = _normalize(query)
    if not query_terms and not normalized_query:
        return []

    candidates: list[DomaciLek] = []
    for lek in load_domaci_leky(csv_path):
        if _is_retired(lek):
            continue
        haystack = _normalize(
            " ".join([lek.nazev, lek.ucinna_latka, lek.forma, lek.sila, lek.kategorie, lek.zdroj])
        )
        if normalized_query and normalized_query in haystack:
            candidates.append(lek)
            continue
        matched_terms = [term for term in query_terms if term in haystack]
        if matched_terms and len(matched_terms) >= min(2, len(query_terms)):
            candidates.append(lek)

    candidates.sort(key=lambda lek: (_normalize(lek.nazev), _normalize(lek.sila), _normalize(lek.forma)))
    return candidates[:10]


def _safety_warnings(lek: DomaciLek) -> list[str]:
    warnings: list[str] = []
    if _normalize(lek.nutno_overit) == "ano":
        warnings.append("nutno_overit=ano")
    if _normalize(lek.expirace) in UNKNOWN_EXPIRATION_VALUES:
        warnings.append("chybi nebo je nezjistena expirace")
    if _normalize(lek.stav_obalu) == "zbytky_bez_krabicky":
        warnings.append("ZBYTKY_BEZ_KRABICKY")
    if _looks_unverified_name(lek):
        warnings.append("neovereny nebo nejisty nazev")
    if any(word in _normalize(lek.jistota_cteni) for word in LOW_CONFIDENCE_WORDS):
        warnings.append(f"jistota cteni: {lek.jistota_cteni}")
    if _normalize(lek.overeno_z_letaku) != "ano":
        warnings.append("neovereno z pribaloveho letaku")
    return warnings


def _has_missing_expiration(lek: DomaciLek) -> bool:
    return _normalize(lek.expirace) in UNKNOWN_EXPIRATION_VALUES


def _has_unknown_location(lek: DomaciLek) -> bool:
    if _is_retired(lek):
        return False
    normalized_location = _normalize(lek.umisteni)
    return (
        normalized_location in UNKNOWN_LOCATION_VALUES
        or any(marker in normalized_location for marker in UNKNOWN_LOCATION_MARKERS)
    )


def _has_low_or_medium_confidence(lek: DomaciLek) -> bool:
    normalized_confidence = _normalize(lek.jistota_cteni)
    return any(word in normalized_confidence for word in LOW_CONFIDENCE_WORDS)


def _is_antibiotic(lek: DomaciLek) -> bool:
    text = _audit_search_text(lek)
    return "antibiotik" in text


def _is_blood_thinner_related(lek: DomaciLek) -> bool:
    text = _audit_search_text(lek)
    return (
        "redeni krve" in text
        or "redeni_krve" in text
        or "acetylsalicyl" in text
        or "godasal" in text
        or "stacyl" in text
    )


def _audit_search_text(lek: DomaciLek) -> str:
    return _normalize(
        " ".join(
            [
                lek.nazev,
                lek.ucinna_latka,
                lek.kategorie,
                lek.pouziti,
                lek.poznamky,
            ]
        )
    )


def _audit_item_line(lek: DomaciLek) -> str:
    details = [
        f"expirace: {lek.expirace or 'neuvedena'}",
        f"umisteni: {lek.umisteni or 'neuvedeno'}",
        f"obal: {lek.stav_obalu or 'neuvedeno'}",
        f"jistota: {lek.jistota_cteni or 'neuvedena'}",
        f"nutno_overit: {lek.nutno_overit or 'neuvedeno'}",
    ]
    if lek.kategorie:
        details.append(f"kategorie: {lek.kategorie}")
    return f"{lek.nazev or 'Nazev neuveden'} ({'; '.join(details)})"


def _looks_unverified_name(lek: DomaciLek) -> bool:
    text = _normalize(" ".join([lek.nazev, lek.kategorie, lek.poznamky]))
    return "/" in lek.nazev or "neoveren" in text or "nejist" in text


def _is_retired(lek: DomaciLek) -> bool:
    return (
        _normalize(lek.mnozstvi) == "vyradeno"
        or _normalize(lek.umisteni) == "vyradeno"
        or "vyradeno" in _normalize(lek.poznamky)
    )


def _retire_candidate_line(index: int, lek: DomaciLek) -> str:
    return (
        f"{index}. {lek.nazev or 'Nazev neuveden'} | "
        f"{_join_nonempty(lek.sila, lek.forma)} | "
        f"mnozstvi: {lek.mnozstvi or 'neuvedeno'} | "
        f"umisteni: {lek.umisteni or 'neuvedeno'}"
    )


def _same_inventory_item(left: DomaciLek, right: DomaciLek) -> bool:
    return all(
        getattr(left, field) == getattr(right, field)
        for field in ("nazev", "ucinna_latka", "forma", "sila", "zdroj")
    )


def _append_note(existing: str, note: str) -> str:
    existing = existing.strip()
    return f"{existing} {note}".strip() if existing else note


def _backup_csv_for_retire(csv_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"{csv_path.stem}.backup_before_retire_{stamp}{csv_path.suffix}")
    shutil.copy2(csv_path, backup_path)
    return backup_path


def _write_domaci_leky(csv_path: Path, records: list[DomaciLek]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_NAMES)
        writer.writeheader()
        for record in records:
            writer.writerow({field: getattr(record, field) for field in FIELD_NAMES})


def _expand_query_terms(query: str) -> set[str]:
    normalized_query = _normalize(query)
    base_terms = set(_tokens(normalized_query))
    expanded = set(base_terms)
    for key, aliases in QUERY_ALIASES.items():
        if key in base_terms or any(alias in normalized_query for alias in aliases):
            expanded.update(aliases)
    return {term for term in expanded if len(term) >= 3}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text)


def _normalize(text: str) -> str:
    normalized = text.casefold().translate(
        str.maketrans(
            {
                "á": "a",
                "č": "c",
                "ď": "d",
                "é": "e",
                "ě": "e",
                "í": "i",
                "ň": "n",
                "ó": "o",
                "ř": "r",
                "š": "s",
                "ť": "t",
                "ú": "u",
                "ů": "u",
                "ý": "y",
                "ž": "z",
            }
        )
    )
    return " ".join(_tokens(normalized))


def _join_nonempty(*values: str) -> str:
    parts = [value for value in values if value]
    return " | ".join(parts) if parts else "neuvedeno"


def _ensure_within_project(path: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Cesta musi zustat uvnitr Samantha_Agent: {path}") from exc
