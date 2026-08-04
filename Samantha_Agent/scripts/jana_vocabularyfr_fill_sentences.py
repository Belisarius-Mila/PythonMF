#!/usr/bin/env python3
"""Fill basic French example sentences in Jana's VocabularyFR CSV."""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_CSV = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/VocabularyFR/VocabularyFR.csv"
)

EXPECTED_HEADERS = ["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_fr"]


@dataclass(frozen=True)
class SentencePatch:
    sentence: str
    translation: str


FR_CORRECTIONS = {
    18: "Ça va ?",
    20: "Et toi ?",
    257: "Bonne journée !",
    285: "Quoi ?",
    286: "Quand ?",
    289: "comprendre",
    298: "De rien !",
    302: "Bon appétit !",
    332: "Bonne soirée !",
    337: "magasin",
    342: "je ne sais pas",
    387: "nouveau, nouvelle",
}


SENTENCE_PATCHES = {
    289: SentencePatch(
        "Je commence à comprendre cette règle.",
        "Začínám chápat toto pravidlo.",
    ),
    290: SentencePatch(
        "Il y a une pharmacie près de la gare.",
        "U nádraží je lékárna.",
    ),
    291: SentencePatch(
        "Je prends un verre d'eau avec le repas.",
        "K jídlu si dávám sklenici vody.",
    ),
    292: SentencePatch(
        "Mince, j'ai oublié mon téléphone à la maison !",
        "Sakra, zapomněl jsem telefon doma!",
    ),
    293: SentencePatch(
        "Cette table est sale après le déjeuner.",
        "Tento stůl je po obědě špinavý.",
    ),
    294: SentencePatch(
        "Je bois mon café dans une grande tasse.",
        "Piju kávu z velkého hrnku.",
    ),
    295: SentencePatch(
        "Je dois laver les verres avant le dîner.",
        "Musím umýt sklenice před večeří.",
    ),
    296: SentencePatch(
        "Attention, ce verre est fragile.",
        "Pozor, tato sklenice je křehká.",
    ),
    297: SentencePatch(
        "Je pose la fourchette à côté de l'assiette.",
        "Položím vidličku vedle talíře.",
    ),
    298: SentencePatch(
        "Merci pour ton aide. De rien !",
        "Děkuji za pomoc. Není zač!",
    ),
    299: SentencePatch(
        "Notre invité arrive pour le dîner.",
        "Náš pozvaný host přijde na večeři.",
    ),
    300: SentencePatch(
        "Le visiteur attend devant la porte.",
        "Návštěvník čeká přede dveřmi.",
    ),
    301: SentencePatch(
        "Le client demande l'addition au serveur.",
        "Host v restauraci žádá číšníka o účet.",
    ),
    302: SentencePatch(
        "Le repas est prêt, bon appétit !",
        "Jídlo je hotové, dobrou chuť!",
    ),
    303: SentencePatch(
        "Je prends une serviette avec mon repas.",
        "K jídlu si beru ubrousek.",
    ),
    304: SentencePatch(
        "Nous prenons un dessert après le dîner.",
        "Po večeři si dáme dezert.",
    ),
    305: SentencePatch(
        "Ce fromage est excellent avec du pain frais.",
        "Tento sýr je výborný s čerstvým chlebem.",
    ),
    306: SentencePatch(
        "Je ne bois jamais de café le soir.",
        "Nikdy večer nepiju kávu.",
    ),
    307: SentencePatch(
        "Je ne veux jamais plus arriver en retard.",
        "Už nikdy nechci přijít pozdě.",
    ),
    308: SentencePatch(
        "J'aime cuisiner une soupe simple le dimanche.",
        "Rád v neděli vařím jednoduchou polévku.",
    ),
    309: SentencePatch(
        "Le service est un peu lent aujourd'hui.",
        "Obsluha je dnes trochu pomalá.",
    ),
    310: SentencePatch(
        "Elle est triste parce que son ami part.",
        "Je smutná, protože její kamarád odjíždí.",
    ),
    311: SentencePatch(
        "Je garde un peu d'argent pour le marché.",
        "Nechávám si trochu peněz na trh.",
    ),
    312: SentencePatch(
        "Je peux venir demain matin.",
        "Můžu přijít zítra ráno.",
    ),
    313: SentencePatch(
        "Il n'y a pas de lait dans le frigo.",
        "V lednici není žádné mléko.",
    ),
    314: SentencePatch(
        "Je n'ai aucune idée pour le dîner.",
        "Nemám ani jediný nápad na večeři.",
    ),
    315: SentencePatch(
        "Je sais où est la gare.",
        "Vím, kde je nádraží.",
    ),
    316: SentencePatch(
        "Je vais faire une tarte ce soir.",
        "Dnes večer udělám koláč.",
    ),
    317: SentencePatch(
        "Peut-être que nous irons au cinéma demain.",
        "Možná půjdeme zítra do kina.",
    ),
    318: SentencePatch(
        "J'ai une bonne idée pour le repas.",
        "Mám dobrý nápad na jídlo.",
    ),
    319: SentencePatch(
        "C'est un beau jardin derrière la maison.",
        "Za domem je krásná zahrada.",
    ),
    320: SentencePatch(
        "La visite de Marie est une belle surprise.",
        "Mariina návštěva je milé překvapení.",
    ),
    321: SentencePatch(
        "Il achète un nouveau vélo pour l'été.",
        "Kupuje si nové kolo na léto.",
    ),
    322: SentencePatch(
        "J'ai une nouvelle adresse à Lyon.",
        "Mám novou adresu v Lyonu.",
    ),
    323: SentencePatch(
        "Je prends une petite part de gâteau.",
        "Dám si malý kousek dortu.",
    ),
    324: SentencePatch(
        "Les enfants boivent une limonade au jardin.",
        "Děti pijí limonádu na zahradě.",
    ),
    325: SentencePatch(
        "Cette soupe est bonne et très simple.",
        "Tato polévka je dobrá a velmi jednoduchá.",
    ),
    326: SentencePatch(
        "Elle va au travail à bicyclette.",
        "Jezdí do práce na kole.",
    ),
    327: SentencePatch(
        "Mon vélo est devant la maison.",
        "Moje kolo je před domem.",
    ),
    328: SentencePatch(
        "Je suis content de te voir aujourd'hui.",
        "Jsem rád, že tě dnes vidím.",
    ),
    329: SentencePatch(
        "Merci pour le café et le gâteau.",
        "Děkuji za kávu a dort.",
    ),
    330: SentencePatch(
        "Nous passons une soirée calme à la maison.",
        "Trávíme klidný večer doma.",
    ),
    331: SentencePatch(
        "Je rentre tard ce soir.",
        "Dnes večer se vracím pozdě.",
    ),
    332: SentencePatch(
        "Bonne soirée, à demain !",
        "Hezký večer, zítra na viděnou!",
    ),
    333: SentencePatch(
        "Ce dessert est vraiment excellent.",
        "Tento dezert je opravdu výborný.",
    ),
    334: SentencePatch(
        "La soupe est encore chaude.",
        "Polévka je ještě horká.",
    ),
    335: SentencePatch(
        "Ta réponse est juste.",
        "Tvoje odpověď je správná.",
    ),
    336: SentencePatch(
        "J'arrive juste après le déjeuner.",
        "Přijdu hned po obědě.",
    ),
    337: SentencePatch(
        "Le magasin ferme à six heures.",
        "Obchod zavírá v šest hodin.",
    ),
    338: SentencePatch(
        "La gare est au centre de la ville.",
        "Nádraží je v centru města.",
    ),
    339: SentencePatch(
        "Je ne veux pas perdre mes clés.",
        "Nechci ztratit klíče.",
    ),
    340: SentencePatch(
        "Je prends une glace à la vanille.",
        "Dám si vanilkovou zmrzlinu.",
    ),
    341: SentencePatch(
        "Nous regardons le plan de la ville.",
        "Díváme se na mapu města.",
    ),
    342: SentencePatch(
        "Je ne sais pas où est mon sac.",
        "Nevím, kde je moje taška.",
    ),
    343: SentencePatch(
        "Nous regardons les photos après le dîner.",
        "Po večeři se díváme na fotky.",
    ),
    344: SentencePatch(
        "Quelle heure est-il maintenant ?",
        "Kolik je teď hodin?",
    ),
    345: SentencePatch(
        "Quand pars-tu pour Paris ?",
        "Kdy odjíždíš do Paříže?",
    ),
    346: SentencePatch(
        "J'appelle quand j'arrive à la gare.",
        "Zavolám, když dorazím na nádraží.",
    ),
    347: SentencePatch(
        "Enfin, le train arrive à la gare.",
        "Konečně vlak přijíždí na nádraží.",
    ),
    384: SentencePatch(
        "J’ai neuf livres.",
        "Mám devět knih.",
    ),
    385: SentencePatch(
        "La leçon commence à neuf heures.",
        "Lekce začíná v devět hodin.",
    ),
    386: SentencePatch(
        "Les maths sont intéressantes.",
        "Matematika je zajímavá.",
    ),
    387: SentencePatch(
        "Il a un nouveau vélo et elle a une nouvelle robe.",
        "On má nové kolo a ona má nové šaty.",
    ),
    388: SentencePatch(
        "J’apprends le français chaque jour.",
        "Každý den se učím francouzsky.",
    ),
    389: SentencePatch(
        "Je comprends cette question.",
        "Rozumím této otázce.",
    ),
    390: SentencePatch(
        "Je suis un cours de français chaque semaine.",
        "Každý týden chodím na kurz francouzštiny.",
    ),
}


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise SystemExit(
                f"Neocekavana hlavicka CSV: {reader.fieldnames!r}; "
                f"cekam {EXPECTED_HEADERS!r}"
            )
        return list(reader)


def write_rows(csv_path: Path, rows: list[dict[str, str]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def order_of(row: dict[str, str]) -> int:
    try:
        return int(row["Order"])
    except ValueError as exc:
        raise SystemExit(f"Neplatne Order {row['Order']!r} pro radek {row!r}") from exc


def apply_patches(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    changes: list[str] = []
    warnings: list[str] = []
    seen_orders: set[int] = set()

    for row in rows:
        order = order_of(row)
        seen_orders.add(order)

        corrected_fr = FR_CORRECTIONS.get(order)
        if corrected_fr and row["FR"] != corrected_fr:
            changes.append(f"{order}: FR {row['FR']!r} -> {corrected_fr!r}")
            row["FR"] = corrected_fr

        sentence_patch = SENTENCE_PATCHES.get(order)
        if not sentence_patch:
            continue

        if not row["Sentence"].strip():
            changes.append(f"{order}: doplnen Sentence")
            row["Sentence"] = sentence_patch.sentence
        elif row["Sentence"] != sentence_patch.sentence:
            warnings.append(f"{order}: Sentence uz existuje, neprepisuji")

        if not row["SentenceT"].strip():
            changes.append(f"{order}: doplnen SentenceT")
            row["SentenceT"] = sentence_patch.translation
        elif row["SentenceT"] != sentence_patch.translation:
            warnings.append(f"{order}: SentenceT uz existuje, neprepisuji")

    missing_orders = sorted(set(SENTENCE_PATCHES) - seen_orders)
    if missing_orders:
        warnings.append(f"V CSV chybi Order: {missing_orders}")

    return changes, warnings


def validate(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []

    missing_sentence = [
        order_of(row)
        for row in rows
        if not row["Sentence"].strip() or not row["SentenceT"].strip()
    ]
    if missing_sentence:
        errors.append(f"Radky bez Sentence/SentenceT: {missing_sentence}")

    for order, expected_fr in FR_CORRECTIONS.items():
        matching = [row for row in rows if order_of(row) == order]
        if not matching:
            errors.append(f"Chybi radek Order {order}")
        elif matching[0]["FR"] != expected_fr:
            errors.append(
                f"Order {order}: FR je {matching[0]['FR']!r}, cekam {expected_fr!r}"
            )

    return errors


def make_backup(csv_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.with_name(f"{csv_path.stem}.before_sentences_{stamp}.csv")
    shutil.copy2(csv_path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Zapsat zmeny. Bez --apply se jen vypise preview.",
    )
    args = parser.parse_args()

    csv_path = args.csv.expanduser()
    if not csv_path.exists():
        raise SystemExit(f"CSV neexistuje: {csv_path}")

    rows = read_rows(csv_path)
    original_count = len(rows)
    changes, warnings = apply_patches(rows)
    errors = validate(rows)

    print(f"CSV: {csv_path}")
    print(f"Radku: {original_count}")
    print(f"Planovanych zmen: {len(changes)}")
    for change in changes:
        print(f"- {change}")
    if warnings:
        print("Varovani:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("Chyby validace:")
        for error in errors:
            print(f"- {error}")
        return 2

    if not args.apply:
        print("DRY RUN: nic jsem nezapsal.")
        return 0

    backup_path = make_backup(csv_path)
    write_rows(csv_path, rows)
    print(f"Zaloha: {backup_path}")
    print("Zapsano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
