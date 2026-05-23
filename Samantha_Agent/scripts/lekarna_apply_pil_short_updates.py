from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "lekarna" / "domaci_leky.csv"
PIL_FIELDS = ["PIL_Short", "PIL_Source", "PIL_Checked_Date", "PIL_Match_Status"]
CHECKED_DATE = "2026-05-20"

PIL_UPDATES = {
    "Brufen": {
        "PIL_Short": (
            "Ibuprofen na horecku a mirnou az stredni bolest, napr. hlavy, zad, zubu, menstruacni "
            "bolest, bolesti svalu/kloubu a urazy mekych tkani; protizanetlivy ucinek. Uziva se "
            "kratkodobe podle PIL, zapit vodou; u citliveho zaludku spise s jidlem. Neuzivat pri "
            "alergii na ibuprofen/NSAID, aktivnim nebo opakovanem zaludecnim ci dvanactnikovem vredu "
            "nebo krvaceni, zavaznem selhani srdce/jater/ledvin, vyrazne dehydrataci a ve 3. trimestru "
            "tehotenstvi. Pozor pri astmatu, zaludecnich potizich, lecich na redeni krve, jinych NSAID, "
            "vysokem tlaku/srdci a pri zhorsujici se infekci."
        ),
        "PIL_Source": (
            "SUKL DLP 2026-04-27 kod 0234194; "
            "https://www.mojelekarna.cz/uploads/uploadedFiles/05/pribalovy-letak-sukl-brufen-400mg-tbl-flm-100-1.pdf?v4="
        ),
        "PIL_Match_Status": "overeno_sukl_dlp_pil",
    },
    "Panadol Novum": {
        "PIL_Short": (
            "Paracetamol na horecku a mirnou az stredni bolest, napr. hlavy, zubu, zad, kloubu/svalu, "
            "menstruacni bolest a bolesti pri chripce/nachlazeni. Uziva se kratkodobe podle PIL, s "
            "odstupy mezi davkami; neprekrocit doporucene davkovani. Neuzivat pri alergii na paracetamol, "
            "tezke poruse jater, akutni hepatitide nebo tezke hemolyticke anemii. Pozor na soubezne "
            "uzivani jinych pripravku s paracetamolem, onemocneni jater a pravidelny alkohol."
        ),
        "PIL_Source": (
            "SUKL DLP 2026-04-27 kod 0226670/0173187 dle baleni; "
            "https://www.pilulka.cz/panadol-novum-500-mg-24-tablet/pribalovy-letak"
        ),
        "PIL_Match_Status": "overeno_sukl_dlp_pil",
    },
    "ACC Long": {
        "PIL_Short": (
            "Acetylcystein na vlhky kasel a husty vazky hlen pri akutnich onemocnenich dychacich cest; "
            "u chronickych stavu jen podle lekare. Pro dospele a dospivajici od 14 let; sumiva tableta "
            "se rozpousti ve vode a uziva podle PIL, obvykle kratkodobe. Neuzivat pri alergii na "
            "acetylcystein nebo pri zaludecnim/dvanactnikovem vredu. Pozor pri astmatu, snizene schopnosti "
            "vykaslavani, predchozich vredovych potizich, tehotenstvi/kojeni a pri kombinaci s leky "
            "tlumicimi kasel nebo nekterymi antibiotiky."
        ),
        "PIL_Source": (
            "SUKL DLP 2026-04-27 kod 0057395, PIL PI226693.pdf; "
            "https://pilulka.s3-central.vshosting.cloud/pilulka-cz/files/images/2022-12/3338ec724ee7aa9d97bebe7c60bf5286.jpg"
        ),
        "PIL_Match_Status": "overeno_sukl_dlp_pil",
    },
    "Fenistil gel": {
        "PIL_Short": (
            "Dimetindenovy gel ke zmirneni svedeni kuze, koprivky, stipnuti hmyzem, spalenin od slunce "
            "a mirnych povrchovych popalenin; ma i mistni znecitlivujici efekt. Nanasi se zevne na "
            "svediva mista podle PIL. Nepouzivat pri alergii na slozky pripravku. V tehotenstvi a kojeni "
            "opatrne: hlavne nenanaset na rozsahle, porusene nebo zanicene plochy a pri kojeni ne na "
            "prsni dvorce. Rizika jsou hlavne lokalni paleni/suchost kuze nebo kozni alergicka reakce."
        ),
        "PIL_Source": (
            "SUKL DLP 2026-04-27 kod 0279626/0173497; "
            "https://www.pilulka.cz/fenistil-gel-1mg-g-pri-svedeni-pokozky-30-g/pribalovy-letak"
        ),
        "PIL_Match_Status": "overeno_sukl_dlp_pil",
    },
    "Omeprazol Teva Pharma": {
        "PIL_Short": (
            "Omeprazol snizuje tvorbu zaludecni kyseliny; u dospelych se bez lekare pouziva na priznaky "
            "refluxu, jako paleni zahy a navraceni kyseliny, dalsi indikace patri pod lekare. Tobolky se "
            "polykaji cele podle PIL, nekousat ani nedrtit. Neuzivat pri alergii na omeprazol nebo podobne "
            "leky; pri varovnych priznacich, dlouhodobych potizich, onemocneni jater, tehotenstvi/kojeni "
            "nebo pri lecich s moznymi interakcemi overit u lekare/lekarnika."
        ),
        "PIL_Source": (
            "SUKL DLP 2026-04-27 kod 0164972, PIL PI207295.pdf; "
            "https://www.medicinous.com/cs/Omeprazol-teva-pharma/spc128924"
        ),
        "PIL_Match_Status": "overeno_sukl_dlp_pil",
    },
}


def main() -> None:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        original_fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    if not original_fields:
        raise SystemExit("CSV nema hlavicku.")

    fieldnames = [*original_fields]
    for field in PIL_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)

    backup_path = _backup_csv(CSV_PATH)
    updated = 0
    for row in rows:
        name = (row.get("nazev") or "").strip()
        update = PIL_UPDATES.get(name)
        for field in PIL_FIELDS:
            row.setdefault(field, "")
        if not update:
            continue
        row.update(update)
        row["PIL_Checked_Date"] = CHECKED_DATE
        updated += 1

    if updated != len(PIL_UPDATES):
        raise SystemExit(f"Ocekavano {len(PIL_UPDATES)} aktualizaci, provedeno {updated}. Zaloha: {backup_path}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    print(f"Hotovo: pridany/aktualizovany PIL sloupce, pilotne doplneno {updated} radku.")
    print(f"Zaloha: {backup_path}")


def _backup_csv(csv_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"{csv_path.stem}.backup_before_pil_short_{stamp}{csv_path.suffix}")
    shutil.copy2(csv_path, backup_path)
    return backup_path


if __name__ == "__main__":
    main()
