from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .download_intake import normalize_for_match, token_set


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUKL_CACHE_DIR = PROJECT_ROOT / "data" / "lekarna" / "sukl_cache"


@dataclass(frozen=True)
class SuklDlpMatch:
    kod_sukl: str
    nazev: str
    sila: str
    forma: str
    baleni: str
    doplnek: str
    rc: str
    vydej: str
    typ_lp: str
    dodavky: str
    atc_code: str
    atc_name: str
    atc_group: str
    vydej_name: str
    active_substances: tuple[str, ...]
    pil: str
    dat_roz_pil: str
    spc: str
    dat_roz_spc: str
    score: int
    confidence: str
    source_zip: Path

    @property
    def match_status(self) -> str:
        if self.confidence in {"exact", "probable"} and self.pil:
            return "overeno_z_dlp"
        return "nejista_varianta_sukl"


def find_latest_dlp_zip(cache_dir: Path = DEFAULT_SUKL_CACHE_DIR) -> Path | None:
    cache_dir = cache_dir.expanduser()
    if not cache_dir.exists():
        return None
    candidates = sorted(cache_dir.glob("DLP*.zip"), key=lambda path: path.name, reverse=True)
    return candidates[0] if candidates else None


def match_sukl_dlp(
    suggestion: dict[str, str],
    *,
    ocr_text: str = "",
    dlp_zip_path: Path | None = None,
) -> SuklDlpMatch | None:
    source_zip = dlp_zip_path or find_latest_dlp_zip()
    if not source_zip or not source_zip.exists():
        return None

    products = _read_csv_from_zip(source_zip, "dlp_lecivepripravky.csv")
    documents = {
        str(row.get("KOD_SUKL", "")).strip(): row
        for row in _read_csv_from_zip(source_zip, "dlp_nazvydokumentu.csv")
        if str(row.get("KOD_SUKL", "")).strip()
    }
    substances_by_product = _substances_by_product(source_zip)
    atc_names = _atc_names(source_zip)
    vydej_names = _vydej_names(source_zip)

    query_text = " ".join(
        str(value or "")
        for value in (
            suggestion.get("nazev", ""),
            suggestion.get("sila", ""),
            suggestion.get("forma", ""),
            suggestion.get("mnozstvi", ""),
            ocr_text,
        )
    )
    query_norm = normalize_for_match(query_text)
    if not query_norm:
        return None
    query_tokens = _important_tokens(query_norm)
    quantity = _quantity_number(query_text)
    form_hint = _form_hint(query_text)
    wants_coated = "obalene" in query_norm or "obd" in query_norm

    scored: list[tuple[int, dict[str, str]]] = []
    for row in products:
        name_norm = normalize_for_match(row.get("NAZEV", ""))
        if not name_norm:
            continue
        name_tokens = _important_tokens(name_norm)
        if not name_tokens:
            continue
        overlap = query_tokens & name_tokens
        if not overlap:
            continue

        score = len(overlap) * 12
        if name_norm in query_norm:
            score += 42
        if name_tokens <= query_tokens:
            score += 24
        missing_name_tokens = name_tokens - query_tokens
        score -= len(missing_name_tokens) * 7

        if quantity and _same_quantity(quantity, row.get("BALENI", "")):
            score += 26
        if form_hint and _dlp_form_matches(form_hint, row.get("FORMA", ""), row.get("DOPLNEK", "")):
            score += 14
        if wants_coated and "obd" in normalize_for_match(" ".join([row.get("FORMA", ""), row.get("DOPLNEK", "")])):
            score += 8
        if str(row.get("DODAVKY", "")).strip() == "1":
            score += 4
        else:
            score -= 4
        if str(row.get("REG", "")).strip() == "R":
            score += 3
        if documents.get(str(row.get("KOD_SUKL", "")).strip(), {}).get("PIL", "").strip():
            score += 5

        if score >= 35:
            scored.append((score, row))

    if not scored:
        return None

    scored.sort(key=lambda item: (-item[0], _supply_sort_key(item[1]), item[1].get("KOD_SUKL", "")))
    best_score, best = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0
    if best_score < 55:
        return None
    if best_score >= 90 and best_score - second_score >= 18:
        confidence = "exact"
    elif best_score >= 65:
        confidence = "probable"
    else:
        confidence = "ambiguous"

    code = str(best.get("KOD_SUKL", "")).strip()
    doc = documents.get(code, {})
    return SuklDlpMatch(
        kod_sukl=code,
        nazev=str(best.get("NAZEV", "")).strip(),
        sila=str(best.get("SILA", "")).strip(),
        forma=str(best.get("FORMA", "")).strip(),
        baleni=str(best.get("BALENI", "")).strip(),
        doplnek=str(best.get("DOPLNEK", "")).strip(),
        rc=str(best.get("RC", "")).strip(),
        vydej=str(best.get("VYDEJ", "")).strip(),
        typ_lp=str(best.get("TYP_LP", "")).strip(),
        dodavky=str(best.get("DODAVKY", "")).strip(),
        atc_code=str(best.get("ATC_WHO", "")).strip(),
        atc_name=atc_names.get(str(best.get("ATC_WHO", "")).strip(), ""),
        atc_group=_best_atc_group(str(best.get("ATC_WHO", "")).strip(), atc_names),
        vydej_name=vydej_names.get(str(best.get("VYDEJ", "")).strip(), ""),
        active_substances=substances_by_product.get(code, ()),
        pil=str(doc.get("PIL", "")).strip(),
        dat_roz_pil=str(doc.get("DAT_ROZ_PIL", "")).strip(),
        spc=str(doc.get("SPC", "")).strip(),
        dat_roz_spc=str(doc.get("DAT_ROZ_SPC", "")).strip(),
        score=best_score,
        confidence=confidence,
        source_zip=source_zip,
    )


def format_sukl_dlp_source(match: SuklDlpMatch) -> str:
    date = _date_from_dlp_filename(match.source_zip)
    pieces = [
        f"SUKL DLP {date}" if date else f"SUKL DLP {match.source_zip.name}",
        f"kod {match.kod_sukl}",
        match.nazev,
    ]
    if match.doplnek:
        pieces.append(match.doplnek)
    elif match.forma or match.baleni:
        pieces.append(" ".join(value for value in (match.forma, match.baleni) if value))
    if match.pil:
        pil_piece = f"PIL {match.pil}"
        if match.dat_roz_pil:
            pil_piece += f" ({match.dat_roz_pil})"
        pieces.append(pil_piece)
    pieces.append("plny text PIL neni soucasti DLP; pro text je potreba PIL archiv/PDF")
    return "; ".join(piece for piece in pieces if piece)


def _read_csv_from_zip(zip_path: Path, member_name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        data = archive.read(member_name)
    text = _decode_sukl_csv(data)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return [dict(row) for row in reader]


def _read_csv_from_zip_optional(zip_path: Path, member_name: str) -> list[dict[str, str]]:
    try:
        return _read_csv_from_zip(zip_path, member_name)
    except KeyError:
        return []


def _substances_by_product(zip_path: Path) -> dict[str, tuple[str, ...]]:
    substances = {
        str(row.get("KOD_LATKY", "")).strip(): str(
            row.get("NAZEV") or row.get("NAZEV_INN") or row.get("NAZEV_EN") or ""
        ).strip()
        for row in _read_csv_from_zip_optional(zip_path, "dlp_latky.csv")
        if str(row.get("KOD_LATKY", "")).strip()
    }
    grouped: dict[str, list[tuple[int, str]]] = {}
    for row in _read_csv_from_zip_optional(zip_path, "dlp_slozeni.csv"):
        code = str(row.get("KOD_SUKL", "")).strip()
        substance_code = str(row.get("KOD_LATKY", "")).strip()
        if not code or not substance_code:
            continue
        name = substances.get(substance_code, "")
        if not name or name in {"OR:", "NEBO:"}:
            continue
        kind = str(row.get("S", "")).strip().upper()
        priority = 0 if kind == "O" else 1 if kind == "L" else 2
        grouped.setdefault(code, []).append((priority, name))

    result: dict[str, tuple[str, ...]] = {}
    for code, values in grouped.items():
        ordered: list[str] = []
        for _, name in sorted(values, key=lambda item: (item[0], item[1].casefold())):
            if name not in ordered:
                ordered.append(name)
        if any(priority == 0 for priority, _ in values):
            preferred = {
                name
                for priority, name in values
                if priority == 0
            }
            ordered = [name for name in ordered if name in preferred]
        result[code] = tuple(ordered[:4])
    return result


def _atc_names(zip_path: Path) -> dict[str, str]:
    return {
        str(row.get("ATC", "")).strip(): str(row.get("NAZEV", "") or row.get("NAZEV_EN", "")).strip()
        for row in _read_csv_from_zip_optional(zip_path, "dlp_atc.csv")
        if str(row.get("ATC", "")).strip()
    }


def _vydej_names(zip_path: Path) -> dict[str, str]:
    return {
        str(row.get("VYDEJ", "")).strip(): str(row.get("NAZEV", "")).strip()
        for row in _read_csv_from_zip_optional(zip_path, "dlp_vydej.csv")
        if str(row.get("VYDEJ", "")).strip()
    }


def _best_atc_group(atc_code: str, atc_names: dict[str, str]) -> str:
    code = str(atc_code or "").strip()
    for length in (5, 4, 3, 1):
        group_code = code[:length]
        if group_code in atc_names and group_code != code:
            return atc_names[group_code]
    return ""


def _decode_sukl_csv(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    for encoding in ("cp1250", "utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin2", errors="replace")


def _important_tokens(normalized_text: str) -> set[str]:
    stop = {
        "bionorica",
        "dr",
        "max",
        "akutni",
        "tablety",
        "tablet",
        "tbl",
        "obalene",
        "obalenych",
        "potahovane",
        "tobolky",
        "sirup",
        "mg",
        "ml",
    }
    return {token for token in token_set(normalized_text) if len(token) >= 3 and token not in stop}


def _quantity_number(text: str) -> str:
    match = re.search(r"\b(\d+)\s*(?:tablet|tablety|tbl|tobolek|tobolky|kapsli|pastilek|sacku|sacek)\b", text, re.I)
    return match.group(1) if match else ""


def _same_quantity(quantity: str, dlp_value: str) -> bool:
    return bool(quantity and re.fullmatch(rf"\s*{re.escape(quantity)}(?:[,.]0+)?\s*", str(dlp_value or "")))


def _form_hint(text: str) -> str:
    normalized = normalize_for_match(text)
    if any(token in normalized.split() for token in ("tablety", "tablet", "tbl")):
        return "tablety"
    if any(token in normalized.split() for token in ("tobolky", "kapsle", "kapsli")):
        return "tobolky"
    if "sirup" in normalized.split():
        return "sirup"
    if "kapky" in normalized.split():
        return "kapky"
    if "mast" in normalized.split():
        return "mast"
    if "gel" in normalized.split():
        return "gel"
    return ""


def _dlp_form_matches(form_hint: str, forma: str, doplnek: str) -> bool:
    haystack = normalize_for_match(" ".join([forma, doplnek]))
    if form_hint == "tablety":
        return "tbl" in haystack
    if form_hint == "tobolky":
        return "cps" in haystack or "tob" in haystack
    if form_hint == "sirup":
        return "sir" in haystack
    if form_hint == "kapky":
        return "gtt" in haystack or "kap" in haystack
    if form_hint == "mast":
        return "ung" in haystack or "mast" in haystack
    if form_hint == "gel":
        return "gel" in haystack
    return False


def _supply_sort_key(row: dict[str, str]) -> int:
    return 0 if str(row.get("DODAVKY", "")).strip() == "1" else 1


def _date_from_dlp_filename(path: Path) -> str:
    match = re.search(r"(\d{4})(\d{2})(\d{2})", path.name)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
