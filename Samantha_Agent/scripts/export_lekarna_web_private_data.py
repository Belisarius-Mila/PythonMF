from __future__ import annotations

import csv
import json
import shutil
import subprocess
import unicodedata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = PROJECT_ROOT / "Samantha_Agent"
CSV_PATH = AGENT_ROOT / "data" / "lekarna" / "domaci_leky.csv"
PHOTO_ROOT = AGENT_ROOT / "data" / "lekarna"
WEB_PRIVATE_ROOT = PROJECT_ROOT / "docs" / "lekarna" / "private-data"
WEB_PHOTO_ROOT = WEB_PRIVATE_ROOT / "photos"
EXPORT_PATH = WEB_PRIVATE_ROOT / "lekarna.json"


def main() -> None:
    rows = _read_rows(CSV_PATH)
    WEB_PHOTO_ROOT.mkdir(parents=True, exist_ok=True)

    medicines: dict[str, dict[str, object]] = {}
    boxes = {
        "jana": _box("Pils Jana", "Osobní krabička", "Léky v osobní krabičce Jana."),
        "mila": _box("Pils Mila", "Osobní krabička", "Léky v osobní krabičce Míla."),
        "home": _box("Pils Home Store", "Domácí zásoba", "Společná domácí zásoba léků a přípravků."),
        "supplements": _box(
            "Vitamíny a přírodní přípravky",
            "Koupelna - nová dóza",
            "Vitamíny, minerály a přírodní přípravky na spánek, nervy a podobné potíže.",
        ),
    }

    for row in rows:
        name = (row.get("nazev") or "").strip()
        if not name:
            continue
        box_key = _box_key(row)
        boxes[box_key]["medicines"].append(name)
        medicines[name] = _medicine_payload(row, export_photo(row, name))

    payload = {
        "generatedBy": "scripts/export_lekarna_web_private_data.py",
        "warning": "Soukromy lokalni export. Nekomitovat a nepublikovat bez sifrovani nebo samostatneho souhlasu.",
        "boxes": boxes,
        "medicines": medicines,
    }

    WEB_PRIVATE_ROOT.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exportováno {len(medicines)} položek do {EXPORT_PATH}")
    print(f"Fotky: {WEB_PHOTO_ROOT}")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _box(title: str, kicker: str, text: str) -> dict[str, object]:
    return {"title": title, "kicker": kicker, "text": text, "medicines": []}


def _box_key(row: dict[str, str]) -> str:
    location = _normalize(row.get("umisteni") or "")
    if "jana" in location:
        return "jana"
    if "mila" in location:
        return "mila"
    if _is_supplement_row(row):
        return "supplements"
    return "home"


def _is_supplement_row(row: dict[str, str]) -> bool:
    searchable_haystack = _normalize(
        " ".join(
            [
                row.get("nazev", ""),
                row.get("kategorie", ""),
                row.get("pouziti", ""),
                row.get("umisteni", ""),
                row.get("poznamky", ""),
                row.get("PIL_Short", ""),
            ]
        )
    )
    exclusion_haystack = _normalize(
        " ".join(
            [
                row.get("nazev", ""),
                row.get("kategorie", ""),
                row.get("pouziti", ""),
            ]
        )
    )
    include_terms = (
        "vitamin",
        "mineral",
        "spanek",
        "nerv",
        "uklid",
        "doza",
        "kozlik",
        "ostropestrec",
        "silymarin",
        "vigant",
        "horcik",
        "magnesium",
        "zinek",
        "melatonin",
        "medunka",
        "levandul",
        "trezalka",
    )
    exclude_terms = (
        "antibiot",
        "redeni krve",
        "specialni lecba",
        "tlak srdce",
        "pouze dle lekare",
    )
    return any(term in searchable_haystack for term in include_terms) and not any(
        term in exclusion_haystack for term in exclude_terms
    )


def _medicine_payload(row: dict[str, str], photo: str | None) -> dict[str, object]:
    return {
        "name": row.get("nazev", ""),
        "category": row.get("kategorie", ""),
        "use": row.get("pouziti", ""),
        "form": row.get("forma", ""),
        "strength": row.get("sila", ""),
        "amount": row.get("mnozstvi", ""),
        "packageStatus": row.get("stav_obalu", ""),
        "readConfidence": row.get("jistota_cteni", ""),
        "mustVerify": row.get("nutno_overit", ""),
        "pilShort": row.get("PIL_Short", ""),
        "pilStatus": row.get("PIL_Match_Status", ""),
        "pilSource": row.get("PIL_Source", ""),
        "pilCheckedDate": row.get("PIL_Checked_Date", ""),
        "searchTags": row.get("Search_Tags", ""),
        "photo": photo,
    }


def export_photo(row: dict[str, str], name: str) -> str | None:
    source = (row.get("zdroj") or "").strip()
    if not source.startswith("Leky_v_Krabickach/"):
        return None

    source_path = PHOTO_ROOT / source
    if not source_path.exists() or not source_path.is_file():
        return None

    target_name = f"{_slug(name)}.jpg"
    target_path = WEB_PHOTO_ROOT / target_name

    suffix = source_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        shutil.copy2(source_path, target_path)
    else:
        subprocess.run(
            ["sips", "-s", "format", "jpeg", str(source_path), "--out", str(target_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    return f"./private-data/photos/{target_name}"


def _slug(value: str) -> str:
    normalized = _normalize(value)
    chars = []
    for char in normalized:
        if char.isalnum():
            chars.append(char)
        else:
            chars.append("-")
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "lek"


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


if __name__ == "__main__":
    main()
