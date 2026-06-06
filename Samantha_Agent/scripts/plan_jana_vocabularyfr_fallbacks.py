#!/usr/bin/env python3
"""Create a curated review plan for Jana's VocabularyFR fallback picture rows."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import audit_jana_vocabularyfr_pict_mapping as audit


DEFAULT_CSV = audit.DEFAULT_CSV
DEFAULT_PICT = audit.DEFAULT_PICT
DEFAULT_CSV_REPORT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/PictNew/jana_vocabularyfr_fallback_review.csv"
)
DEFAULT_MD_REPORT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/PictNew/jana_vocabularyfr_fallback_review.md"
)


@dataclass(frozen=True)
class PlanItem:
    action: str
    stem: str
    note: str


PLAN: dict[int, PlanItem] = {
    5: PlanItem("use_existing", "cake", "dort lze zobrazit existujicim cake"),
    6: PlanItem("use_existing", "cake", "kolac lze zobrazit existujicim cake"),
    42: PlanItem("use_existing", "now", "ted ma existujici obrazek now"),
    79: PlanItem("use_existing", "already", "deja = uz/jiz, existuje already"),
    107: PlanItem("use_existing", "abit", "peu = trochu/malo, existuje abit"),
    110: PlanItem("use_existing", "funny", "drole/vtipne, existuje funny"),
    113: PlanItem("use_existing", "german", "Nemec, existuje german"),
    114: PlanItem("use_existing", "german", "Nemka, existuje obecny german"),
    115: PlanItem("use_existing", "end", "finir = skoncit/dodelat, existuje end"),
    117: PlanItem("generate", "tie", "kravata nema vhodny existujici obrazek"),
    123: PlanItem("use_existing", "ready", "preta/pripravene, existuje ready"),
    124: PlanItem("use_existing", "very", "beaucoup/hodne, existuje very"),
    125: PlanItem("generate", "suitcase", "kufr nema vhodny existujici obrazek"),
    126: PlanItem("use_existing", "iam", "suis/jsem, existuje iam"),
    127: PlanItem("generate", "late", "zpozdeni/pozde nema vhodny obrazek"),
    128: PlanItem("generate", "charger", "nabijecka chybi"),
    130: PlanItem("use_existing", "pocket", "kapsa, existuje pocket"),
    133: PlanItem("generate", "heavy", "tezka/lourde chybi"),
    134: PlanItem("generate", "fast", "rychly/rapide chybi"),
    135: PlanItem("generate", "mobilephone", "mobil/portable chybi"),
    136: PlanItem("generate", "kitchen", "kuchyne chybi"),
    137: PlanItem("generate", "livingroom", "obyvak/salon chybi"),
    138: PlanItem("use_existing", "beautiful", "joli/hezky, existuje beautiful"),
    139: PlanItem("use_existing", "reason", "protoze lze opatrne obrazkem reason"),
    143: PlanItem("use_existing", "satisfied", "spokojen, existuje satisfied"),
    146: PlanItem("generate", "sofa", "canape/gauc nema vhodny existujici obrazek"),
    149: PlanItem("use_existing", "beautiful", "jolie/pekna, existuje beautiful"),
    151: PlanItem("use_existing", "big", "grand/veliky, existuje big"),
    154: PlanItem("generate", "fast", "vite/rychle bude sdilet novy fast"),
    155: PlanItem("use_existing", "office", "bureau/kancelar, existuje office"),
    156: PlanItem("generate", "friend", "copain/pritel chybi"),
    158: PlanItem("use_existing", "how", "comment/jak, existuje how"),
    159: PlanItem("generate", "comfortable", "confortable/pohodlny chybi"),
    160: PlanItem("use_existing", "know", "connaitre/znat, existuje know"),
    163: PlanItem("generate", "moroccan", "marocain chybi"),
    164: PlanItem("use_existing", "also", "en plus/vice lze zobrazit also"),
    166: PlanItem("use_existing", "that", "C'est/To je, vhodnejsi that nez osoba"),
    168: PlanItem("use_existing", "clean", "propre/cisty bez spiny, existuje clean"),
    169: PlanItem("generate", "nolonger", "non plus/jiz ne neni dobre pokryte"),
    170: PlanItem("use_existing", "understand", "comprendre/porozumet, existuje understand"),
    172: PlanItem("generate", "calm", "calme/klidny chybi"),
    178: PlanItem("generate", "bank", "banque/banka chybi"),
    179: PlanItem("use_existing", "italian", "italien/italsky, existuje italian"),
    181: PlanItem("generate", "chinese", "chinois/cinsky chybi"),
    182: PlanItem("use_existing", "also", "en plus/vic, existuje also"),
    183: PlanItem("generate", "nolonger", "non plus/uz ne bude sdilet nolonger"),
    184: PlanItem("use_existing", "take", "prendre/brat, existuje take"),
    185: PlanItem("use_existing", "all", "tout/kazdy, jakykoliv, existuje all"),
    187: PlanItem("generate", "student", "student chybi"),
    188: PlanItem("use_existing", "teacher", "professeur lze pokryt teacher"),
    190: PlanItem("generate", "pen", "stylo/pero chybi"),
    191: PlanItem("use_existing", "school", "etudier/studovat, zatim school"),
    192: PlanItem("generate", "university", "universite chybi"),
    194: PlanItem("use_existing", "mynamecall", "jmenovat se, existuje mynamecall"),
    196: PlanItem("use_existing", "abit", "un petit peu/trosku, existuje abit"),
    198: PlanItem("use_existing", "magnificent", "super lze vyjadrit magnificent"),
    199: PlanItem("use_existing", "magnificent", "cool/super lze vyjadrit magnificent"),
    202: PlanItem("use_existing", "drink", "boire/pit, existuje drink"),
    204: PlanItem("use_existing", "drink", "boisson/napoj, existuje drink"),
    210: PlanItem("generate", "driver", "chauffeur/ridic chybi"),
    212: PlanItem("use_existing", "open", "ouverte/otevrena, existuje open"),
    214: PlanItem("generate", "bus", "autobus chybi jako samostatny obrazek"),
    217: PlanItem("use_existing", "store", "vendeuse/prodavacka, zatim store"),
    218: PlanItem("use_existing", "store", "vendeur/prodavac, zatim store"),
    220: PlanItem("use_existing", "closed", "ferme/zavreny, existuje closed"),
    221: PlanItem("use_existing", "inhurry", "presse/spechajici, existuje inhurry"),
    225: PlanItem("use_existing", "busstation", "station/stanice, existuje busstation"),
    226: PlanItem("use_existing", "entrance", "porte/dvere, nejblizsi entrance"),
    227: PlanItem("use_existing", "broken", "casse/rozbity, existuje broken"),
    229: PlanItem("generate", "infront", "devant/pred jako vztah chybi"),
    231: PlanItem("use_existing", "bring", "apporter/prinest, existuje bring"),
    232: PlanItem("generate", "delivery", "livrer/dodavat chybi"),
    233: PlanItem("generate", "surrender", "se livrer/vzdavat se chybi"),
    235: PlanItem("keep_fallback", "preposition", "chez/u,k je funkcni predlozka"),
    238: PlanItem("generate", "passport", "passeport chybi"),
    239: PlanItem("use_existing", "yourm", "votre/vase, existuje yourm jako nejblizsi"),
    241: PlanItem("use_existing", "airplane", "atterrir/pristat, existuje airplane"),
    242: PlanItem("use_existing", "red", "rouge/cervena, existuje red"),
    244: PlanItem("use_existing", "go", "aller/jet, existuje go"),
    245: PlanItem("use_existing", "pay", "payer/platit, existuje pay"),
    246: PlanItem("use_existing", "meal", "dejeuner/obedvat, zatim meal"),
    248: PlanItem("use_existing", "prepare", "preparer/pripravovat, existuje prepare"),
    251: PlanItem("use_existing", "restaurant", "cafeteria/jidelna, nejblizsi restaurant"),
    253: PlanItem("use_existing", "vegetable", "vegetarien, nejblizsi vegetable"),
    254: PlanItem("use_existing", "young", "enfant/dite, nejblizsi young"),
    260: PlanItem("generate", "fresh", "frais/cerstvy chybi"),
    261: PlanItem("generate", "butter", "beurre/maslo chybi"),
    263: PlanItem("use_existing", "lakepond", "lac/jezero, existuje lakepond"),
    266: PlanItem("generate", "european", "europeen/evropsky chybi"),
    268: PlanItem("use_existing", "cousin", "cousine/sestrenice, existuje cousin"),
    270: PlanItem("generate", "notebook", "cahier/sesit chybi presneji"),
    271: PlanItem("generate", "musicnotebook", "notovy sesit chybi"),
    272: PlanItem("generate", "notebook", "skolni sesit muze sdilet notebook"),
    274: PlanItem("generate", "glasses", "lunettes/bryle chybi"),
    275: PlanItem("generate", "matchstick", "allumette/sirka chybi"),
    276: PlanItem("use_existing", "cupboard", "armoire/skrin, existuje cupboard"),
    279: PlanItem("use_existing", "end", "enfin/nakonec, existuje end"),
    280: PlanItem("use_existing", "race", "courir/bezet, zatim race"),
    283: PlanItem("generate", "world", "monde/svet chybi"),
    286: PlanItem("use_existing", "when", "Quand/Kdy, existuje when"),
    287: PlanItem("use_existing", "sothenwell", "alors/tedy tak pak, existuje sothenwell"),
    289: PlanItem("use_existing", "understand", "comprendre/chapat, existuje understand"),
    292: PlanItem("use_existing", "money", "mince/mince lze brat jako mince/penize"),
    295: PlanItem("use_existing", "wash", "laver/umyt, existuje wash"),
    302: PlanItem("use_existing", "appetite", "Bon appetit, existuje appetite"),
    303: PlanItem("use_existing", "towelnapkin", "serviette/ubrousek, existuje towelnapkin"),
    305: PlanItem("use_existing", "magnificent", "excellent/vynikajici, existuje magnificent"),
    306: PlanItem("generate", "never", "jamais/nikdy chybi"),
    307: PlanItem("generate", "neveragain", "jamais plus/uz nikdy chybi"),
    310: PlanItem("generate", "sad", "triste/zarmouceny chybi"),
    313: PlanItem("use_existing", "nothing", "pas de/zadny, existuje nothing"),
    314: PlanItem("use_existing", "nothing", "aucun/ani jediny, existuje nothing"),
    316: PlanItem("use_existing", "do", "faire/udelat, existuje do"),
    318: PlanItem("generate", "idea", "idee/napad chybi"),
    322: PlanItem("use_existing", "new", "nouvelle/nova, existuje new"),
    323: PlanItem("use_existing", "some", "part/cast, kus, nejblizsi some"),
    324: PlanItem("generate", "lemonade", "limonade chybi presne"),
    329: PlanItem("use_existing", "thankyou", "merci pour/dekuji za, existuje thankyou"),
    330: PlanItem("use_existing", "niceevening", "soiree/vecer, existuje niceevening"),
    331: PlanItem("use_existing", "niceevening", "soir/vecer, existuje niceevening"),
    333: PlanItem("use_existing", "really", "vraiment/opravdu, existuje really"),
    336: PlanItem("use_existing", "just", "juste/presne zrovna, existuje just"),
    339: PlanItem("use_existing", "lost", "perdre/ztratit, existuje lost"),
    341: PlanItem("use_existing", "map", "plan/mapa mesta, existuje map"),
    343: PlanItem("use_existing", "eyes", "regarder/divat se, existuje eyes"),
    345: PlanItem("use_existing", "when", "quand/kdy, existuje when"),
    347: PlanItem("use_existing", "end", "enfin/konecne, existuje end"),
}


def markdown_row(cells: list[str]) -> str:
    return "| " + " | ".join(str(cell).replace("|", "\\|") for cell in cells) + " |"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--pict", type=Path, default=DEFAULT_PICT)
    parser.add_argument("--csv-report", type=Path, default=DEFAULT_CSV_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    files = audit.image_files(args.pict)
    _, mapping = audit.load_mapping(args.pict / "mapping.json")
    with args.csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    fallback_rows: list[tuple[dict[str, str], audit.ImageChoice]] = []
    for row in rows:
        choice = audit.choose_picture(row, files, mapping)
        if choice.source == "fallback":
            fallback_rows.append((row, choice))

    fallback_orders = {int(row["Order"]) for row, _ in fallback_rows}
    plan_orders = set(PLAN)
    missing_plan = sorted(fallback_orders - plan_orders)
    stale_plan = sorted(plan_orders - fallback_orders)
    if missing_plan or stale_plan:
        raise SystemExit(
            f"Plan nesedi s aktualnim fallback auditem. "
            f"Chybi v planu: {missing_plan}; uz nejsou fallback: {stale_plan}"
        )

    output_rows: list[dict[str, str]] = []
    missing_existing_files: list[str] = []
    for row, choice in fallback_rows:
        order = int(row["Order"])
        item = PLAN[order]
        file_name = files.get(audit.normalize_word(item.stem), "")
        if item.action == "use_existing" and not file_name:
            missing_existing_files.append(f"{order}: {item.stem}")
        output_rows.append(
            {
                "Order": row.get("Order", ""),
                "FR": row.get("FR", ""),
                "CZ": row.get("CZ", ""),
                "CurrentFallback": choice.stem,
                "CurrentReason": choice.key,
                "Decision": item.action,
                "ProposedStem": item.stem,
                "ExistingFile": file_name,
                "ProposedMappingKey": row.get("CZ", ""),
                "Note": item.note,
            }
        )

    if missing_existing_files:
        raise SystemExit(
            "Nektere use_existing navrhy nemaji fyzicky obrazek: "
            + ", ".join(missing_existing_files)
        )

    counts: dict[str, int] = {}
    for item in PLAN.values():
        counts[item.action] = counts.get(item.action, 0) + 1

    unique_generate = sorted({item.stem for item in PLAN.values() if item.action == "generate"})

    print(f"Fallback rows: {len(fallback_rows)}")
    for action in sorted(counts):
        print(f"{action}: {counts[action]}")
    print(f"Unique generated image stems: {len(unique_generate)}")
    for stem in unique_generate:
        print(f"- {stem}")

    if not args.write_report:
        print("DRY RUN: report jsem nezapsal.")
        return 0

    args.csv_report.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_report.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(output_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    md: list[str] = []
    md.append("# Jana VocabularyFR fallback review")
    md.append("")
    md.append(f"- Fallback radku: {len(fallback_rows)}")
    md.append(f"- Pouzit existujici obrazek: {counts.get('use_existing', 0)}")
    md.append(f"- Vytvorit novy obrazek: {counts.get('generate', 0)}")
    md.append(f"- Ponechat fallback: {counts.get('keep_fallback', 0)}")
    md.append(f"- Jedinecnych novych obrazku k vytvoreni: {len(unique_generate)}")
    md.append("")
    md.append("## Nove obrazky k vytvoreni")
    md.append("")
    for stem in unique_generate:
        orders = [
            row["Order"]
            for row in output_rows
            if row["Decision"] == "generate" and row["ProposedStem"] == stem
        ]
        md.append(f"- `{stem}`: radky {', '.join(orders)}")
    md.append("")
    md.append("## Detail")
    md.append("")
    md.append(markdown_row(list(output_rows[0])))
    md.append(markdown_row(["---"] * len(output_rows[0])))
    for row in output_rows:
        md.append(markdown_row([row[key] for key in output_rows[0]]))
    md.append("")
    args.md_report.write_text("\n".join(md), encoding="utf-8")

    print(f"CSV report: {args.csv_report}")
    print(f"MD report: {args.md_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
