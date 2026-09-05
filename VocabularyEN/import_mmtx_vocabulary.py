#!/usr/bin/env python3
"""Audit and append MMTX glossary entries to VocabularyEN.csv.

The source JavaScript stays authoritative for English/Czech word pairs.  The
curated table below supplies only the example sentences and optional word set.
By default the command is read-only; ``--apply`` appends missing rows while
preserving every original byte of the existing CSV prefix, including CRLF.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import tempfile
import unicodedata
from collections import OrderedDict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "VocabularyEN" / "VocabularyEN.csv"
DIALOGUE_SUPPLEMENT_PATH = Path(__file__).with_name("mmtx_dialogue_supplement.csv")
SOURCE_FILES = (
    ("MMTX intro, Owl Garden and Forest School", REPO_ROOT / "MatysekANJ" / "web_mmtx" / "script_intro_v2.js"),
    ("MMTX scene 02", REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene02_sunnys_lost_nuts" / "script.js"),
    ("MMTX scene 03", REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene03_journey_to_the_lake" / "script.js"),
    ("MMTX scene 04 prototype", REPO_ROOT / "docs" / "scene04_harry_guard_prototype" / "script.js"),
)
EXCLUDED_REASONS = {
    "benji": "character_name",
    "bunny": "character_name",
    "metoo": "use_too_only",  # Mila: keep the standalone vocabulary entry "too".
}
EXCLUDED_NORMALIZED = set(EXCLUDED_REASONS)
IGNORED_DIALOGUE_TOKENS = set("benji bunny bruno fiona sunny harry logan kate jane caw hmm oh".split())
DIALOGUE_ALIASES = {
    "adventures": "adventure", "animals": "animal", "am": "I (am)", "are": "be",
    "carrots": "carrot", "cheering": "cheer", "chickens": "chicken",
    "closer": "come closer", "colors": "color", "crossed": "cross",
    "did": "do", "does": "do", "don't": "not", "dreams": "dream",
    "fences": "fence", "finished": "finish", "has": "have", "i": "I (am)",
    "is": "be", "isn't": "not", "jumping": "jump", "knows": "know",
    "let's": "let's go", "lives": "live", "logs": "log", "lots": "lots of",
    "needs": "need", "okay": "OK", "paths": "path", "pushing": "push",
    "questions": "question", "reasons": "reason", "stays": "stay",
    "strangers": "stranger", "thank": "thank you", "wants": "want",
}
FIELDS = ("EN", "CZ", "Order", "Sentence", "SentenceT", "WS", "L", "HT")

PAIR_RE = re.compile(
    r'\{\s*en:\s*"((?:\\.|[^"\\])*)",\s*cz:\s*"((?:\\.|[^"\\])*)"'
)
FOREST_RE = re.compile(
    r'\{\s*id:\s*"(?:\\.|[^"\\])*",\s*word:\s*"((?:\\.|[^"\\])*)",'
    r'\s*translation:\s*"((?:\\.|[^"\\])*)"'
)


def _row(sentence: str, sentence_t: str, word_set: str = "") -> tuple[str, str, str]:
    return sentence, sentence_t, word_set


CURATED = {
    "answer": _row("I know the answer to this question.", "Znám odpověď na tuto otázku."),
    "apples": _row("The apples are red and sweet.", "Jablka jsou červená a sladká.", "Food"),
    "bad": _row("This road is bad after the rain.", "Tato cesta je po dešti špatná."),
    "badger": _row("A badger comes out of its den at night.", "Jezevec vychází v noci ze svého doupěte.", "Animals"),
    "ball": _row("The child throws the ball to a friend.", "Dítě hází míč kamarádovi.", "Things"),
    "banana": _row("I peel a banana for my snack.", "Oloupu si banán ke svačině.", "Food"),
    "bears": _row("The bears walk slowly through the forest.", "Medvědi pomalu kráčejí lesem.", "Animals"),
    "bed": _row("The cat is sleeping under the bed.", "Kočka spí pod postelí.", "Things"),
    "believe": _row("I believe you because you tell the truth.", "Věřím ti, protože říkáš pravdu.", "Actions"),
    "block": _row("The child builds a tower with a blue block.", "Dítě staví věž z modré kostky.", "Things"),
    "boat": _row("A small boat sails across the lake.", "Malá loď pluje přes jezero.", "Things"),
    "boots": _row("I wear my boots when it rains.", "Když prší, nosím holinky.", "Things"),
    "bread": _row("We buy fresh bread in the morning.", "Ráno kupujeme čerstvý chleba.", "Food"),
    "bucket": _row("The bucket is full of clean water.", "Kbelík je plný čisté vody.", "Things"),
    "bus": _row("The yellow bus stops near the school.", "Žlutý autobus zastavuje u školy.", "Things"),
    "but": _row("I am tired, but I am happy.", "Jsem unavený, ale jsem šťastný."),
    "cake": _row("There is a birthday cake on the table.", "Na stole je narozeninový dort.", "Food"),
    "cap": _row("He wears a red cap in the sun.", "Na slunci nosí červenou čepici.", "Things"),
    "car": _row("Our car is parked in front of the house.", "Naše auto stojí před domem.", "Things"),
    "careful": _row("Be careful when you cross the road.", "Buď opatrný, když přecházíš silnici."),
    "carrot": _row("The rabbit eats a fresh carrot.", "Králík jí čerstvou mrkev.", "Food"),
    "catch": _row("Can you catch the red ball?", "Dokážeš chytit červený míč?", "Actions"),
    "chair": _row("The wooden chair stands beside the table.", "Dřevěná židle stojí vedle stolu.", "Things"),
    "chase": _row("The dog does not chase the sheep.", "Pes nehoní ovce.", "Actions"),
    "closed": _row("The shop is closed today.", "Obchod je dnes zavřený."),
    "cloud": _row("A dark cloud moves across the sky.", "Po obloze se pohybuje tmavý mrak."),
    "come": _row("Please come to the table.", "Prosím přijď ke stolu.", "Actions"),
    "comecloser": _row("Come closer so you can see the map.", "Přijď blíž, abys viděl mapu.", "Actions"),
    "cookie": _row("She puts one cookie on the plate.", "Položí jednu sušenku na talíř.", "Food"),
    "corn": _row("The farmer grows corn in this field.", "Farmář pěstuje na tomto poli kukuřici.", "Food"),
    "count": _row("Count the apples in the basket.", "Spočítej jablka v košíku.", "Actions"),
    "crow": _row("A black crow sits on the fence.", "Na plotě sedí černý havran.", "Animals"),
    "cup": _row("My blue cup is on the table.", "Můj modrý hrnek je na stole.", "Things"),
    "deep": _row("The water is deep near the bridge.", "Voda je u mostu hluboká."),
    "dig": _row("The badger can dig under the fence.", "Jezevec umí hrabat pod plotem.", "Actions"),
    "doyouhave": _row("Do you have a pencil?", "Máš tužku?"),
    "doeshehave": _row("Does he have the key?", "Má on ten klíč?"),
    "doll": _row("The little girl puts her doll to bed.", "Holčička ukládá panenku do postele.", "Things"),
    "door": _row("Please close the door behind you.", "Prosím zavři za sebou dveře.", "Things"),
    "eat": _row("We eat lunch together at noon.", "V poledne spolu jíme oběd.", "Actions"),
    "eight": _row("Eight ducks are swimming on the pond.", "Na rybníku plave osm kachen."),
    "empty": _row("The glass is empty now.", "Sklenice je teď prázdná."),
    "farm": _row("There are cows and chickens on the farm.", "Na farmě jsou krávy a slepice."),
    "fence": _row("The sheep stand behind the wooden fence.", "Ovce stojí za dřevěným plotem.", "Things"),
    "five": _row("Five stars shine in the dark sky.", "Na tmavé obloze svítí pět hvězd."),
    "flower": _row("A yellow flower grows by the path.", "U cesty roste žlutá kytka."),
    "forest": _row("We walk quietly through the green forest.", "Tiše procházíme zeleným lesem."),
    "fork": _row("I eat the salad with a fork.", "Jím salát vidličkou.", "Things"),
    "four": _row("Four children are playing in the garden.", "Na zahradě si hrají čtyři děti."),
    "friendly": _row("The horse is calm and friendly.", "Kůň je klidný a přátelský."),
    "friends": _row("We are good friends and help each other.", "Jsme dobří kamarádi a pomáháme si."),
    "gate": _row("The farmer opens the gate for us.", "Farmář nám otevírá branku.", "Things"),
    "get": _row("I get a present on my birthday.", "K narozeninám dostanu dárek.", "Actions"),
    "going": _row("We are going to the lake together.", "Jdeme společně k jezeru.", "Actions"),
    "grape": _row("One purple grape falls from the bunch.", "Z hroznu spadne jedna fialová kulička vína.", "Food"),
    "handle": _row("Push the handle down to pump the water.", "Stlač páku dolů, abys napumpoval vodu.", "Things"),
    "hat": _row("Her warm hat is on the chair.", "Její teplá čepice je na židli.", "Things"),
    "idonthave": _row("I don't have my bag with me.", "Nemám u sebe svou tašku."),
    "idontknow": _row("I don't know the answer yet.", "Ještě nevím odpověď."),
    "ihave": _row("I have a map in my bag.", "Mám v tašce mapu."),
    "key": _row("This small key opens the front door.", "Tento malý klíč otevírá přední dveře.", "Things"),
    "kite": _row("The colorful kite flies high in the wind.", "Barevný drak létá vysoko ve větru.", "Things"),
    "lamp": _row("The lamp gives us light in the evening.", "Lampa nám večer svítí.", "Things"),
    "leaf": _row("A red leaf falls from the tree.", "Ze stromu padá červený list."),
    "letsgo": _row("Let's go to the park now.", "Pojďme teď do parku."),
    "littleanimals": _row("The little animals hide under the tree.", "Malá zvířátka se schovávají pod stromem.", "Animals"),
    "look": _row("Look at the bird in the tree.", "Podívej se na ptáka na stromě.", "Actions"),
    "lookinside": _row("Look inside the box for the missing toy.", "Podívej se dovnitř krabice po ztracené hračce.", "Actions"),
    "map": _row("The map shows the way to the lake.", "Mapa ukazuje cestu k jezeru.", "Things"),
    "maybe": _row("Maybe we can go there tomorrow.", "Možná tam můžeme jít zítra."),
    "metoo": _row("I like apples, and my friend says, ‘Me too.’", "Mám rád jablka a kamarád říká: „Já také.“"),
    "moon": _row("The moon is bright above the forest.", "Měsíc jasně svítí nad lesem."),
    "nuts": _row("The squirrel keeps its nuts in a bag.", "Veverka má oříšky v brašně.", "Food"),
    "ok": _row("OK, I will wait by the gate.", "Dobře, počkám u branky.", "Greetings"),
    "one": _row("One bird is sitting on the roof.", "Na střeše sedí jeden pták."),
    "own": _row("The rabbit has its own carrots.", "Králík má vlastní mrkev."),
    "pants": _row("These blue pants are too long.", "Tyto modré kalhoty jsou příliš dlouhé.", "Things"),
    "path": _row("This path leads through the forest.", "Tato cesta vede lesem."),
    "pea": _row("A small green pea is on the plate.", "Na talíři je malý zelený hrášek.", "Food"),
    "pencil": _row("I write my name with a pencil.", "Píšu své jméno tužkou.", "Things"),
    "pigs": _row("The pigs are sleeping in the warm straw.", "Prasátka spí v teplé slámě.", "Animals"),
    "pillow": _row("My head rests on a soft pillow.", "Hlavu mám položenou na měkkém polštáři.", "Things"),
    "plane": _row("The plane flies above the clouds.", "Letadlo letí nad mraky.", "Things"),
    "plate": _row("Please put the bread on the plate.", "Prosím polož chleba na talíř.", "Things"),
    "pump": _row("The old pump brings water from the ground.", "Stará pumpa čerpá vodu ze země.", "Things"),
    "push": _row("Push the heavy door slowly.", "Pomalu zatlač na těžké dveře.", "Actions"),
    "question": _row("The teacher asks a simple question.", "Učitel pokládá jednoduchou otázku."),
    "robot": _row("The little robot waves its hand.", "Malý robot mává rukou.", "Things"),
    "rocket": _row("The rocket rises into the sky.", "Raketa stoupá k obloze.", "Things"),
    "scared": _row("The horse is scared of the loud noise.", "Kůň se bojí hlasitého zvuku."),
    "seven": _row("Seven sheep are standing in the field.", "Na poli stojí sedm ovcí."),
    "shoe": _row("I tie my shoe before we leave.", "Než odejdeme, zavážu si botu.", "Things"),
    "six": _row("Six oranges are in the basket.", "V košíku je šest pomerančů."),
    "soap": _row("Wash your hands with soap and water.", "Umyj si ruce mýdlem a vodou.", "Things"),
    "sock": _row("I found one sock under the bed.", "Našel jsem jednu ponožku pod postelí.", "Things"),
    "spoon": _row("She eats her soup with a spoon.", "Jí polévku lžičkou.", "Things"),
    "squirrel": _row("A squirrel jumps from tree to tree.", "Veverka skáče ze stromu na strom.", "Animals"),
    "star": _row("The first star appears in the evening sky.", "Na večerní obloze se objeví první hvězda."),
    "stick": _row("The dog carries a stick in its mouth.", "Pes nese v tlamě klacek.", "Things"),
    "stone": _row("A smooth stone lies beside the water.", "U vody leží hladký kámen.", "Things"),
    "stranger": _row("Do not open the gate for a stranger.", "Neotvírej branku cizinci."),
    "sun": _row("The sun warms the garden in the morning.", "Slunce ráno zahřívá zahradu."),
    "sunflowers": _row("The tall sunflowers turn toward the sun.", "Vysoké slunečnice se otáčejí ke slunci."),
    "three": _row("Three rabbits sit near the tree.", "U stromu sedí tři králíci."),
    "too": _row("I want to go to the lake too.", "Také chci jít k jezeru."),
    "toy": _row("The child puts the toy into the box.", "Dítě dává hračku do krabice.", "Things"),
    "train": _row("The train arrives at the station on time.", "Vlak přijíždí na nádraží včas.", "Things"),
    "tree": _row("A bird is building a nest in the tree.", "Pták si staví hnízdo na stromě."),
    "truck": _row("The truck carries boxes to the shop.", "Náklaďák veze krabice do obchodu.", "Things"),
    "trust": _row("The little animals trust their friend.", "Malá zvířátka důvěřují svému kamarádovi.", "Actions"),
    "two": _row("Two paths meet near the lake.", "U jezera se setkávají dvě cesty."),
    "under": _row("The key is under the book.", "Klíč je pod knihou."),
    "valley": _row("A river runs through the deep valley.", "Hlubokým údolím protéká řeka."),
    "wait": _row("Please wait for me by the door.", "Prosím počkej na mě u dveří.", "Actions"),
    "warning": _row("The warning tells us to stop.", "Varování nám říká, abychom zastavili."),
    "way": _row("This is the way to the farm.", "Tudy se jde k farmě."),
    "weare": _row("We are ready to start the lesson.", "Jsme připraveni začít lekci."),
    "wecan": _row("We can help the little animal.", "Můžeme pomoci malému zvířeti."),
    "window": _row("Open the window and let in fresh air.", "Otevři okno a pusť dovnitř čerstvý vzduch.", "Things"),
    "yard": _row("The chickens walk around the farm yard.", "Slepice chodí po dvorku farmy."),
}


def normalize_word(text: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", (text or "").strip().casefold())
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def merge_word_sets(value: str, *required: str) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    for candidate in re.split(r"[|,;]+", value or "") + list(required):
        label = re.sub(r"\s+", " ", str(candidate).strip())
        key = label.casefold()
        if label and key not in seen:
            seen.add(key)
            labels.append(label)
    return "|".join(labels)


def decode_js_string(value: str) -> str:
    return json.loads(f'"{value}"')


def load_dialogue_supplement() -> list[dict[str, str]]:
    with DIALOGUE_SUPPLEMENT_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["EN", "CZ", "Sentence", "SentenceT"]:
            raise ValueError("Unexpected MMTX dialogue supplement header")
        rows = list(reader)
    keys = [normalize_word(row["EN"]) for row in rows]
    if len(set(keys)) != len(keys) or any(not all(row.values()) for row in rows):
        raise ValueError("Duplicate or incomplete MMTX dialogue supplement row")
    return rows


def extract_dialogue_tokens() -> dict[str, list[str]]:
    """Audit spoken English, including scenes without a dictionary widget.

    Read data only: no JavaScript evaluation. Manifests hold the actual fixed
    speech keys; intro colors and birthday dialogue are declared in scripts.
    """
    docs = REPO_ROOT / "docs"
    texts: list[tuple[Path, str]] = []
    manifests = [docs / "scene01_audio_manifest.js", docs / "forest_school_audio_manifest.js"]
    manifests.extend(sorted(docs.glob("scene0*/audio_manifest.js")))
    for path in manifests:
        source = path.read_text(encoding="utf-8")
        payload = json.loads(source[source.index("{"):].rstrip().removesuffix(";"))
        for key in payload["dialogue"]["en"]:
            texts.append((path, key.split("::", 1)[-1]))
    scripts = [docs / "script_intro_v2.js", *sorted(docs.glob("scene_*birthday/script.js"))]
    for path in scripts:
        source = path.read_text(encoding="utf-8")
        for raw in re.findall(r'\b(?:en|textEn|word):\s*"((?:\\.|[^"\\])*)"', source):
            texts.append((path, decode_js_string(raw)))
    tokens: dict[str, list[str]] = {}
    for path, text in texts:
        for word in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", text):
            key = word.lower().replace("’", "'")
            source = path.relative_to(REPO_ROOT).as_posix()
            sources = tokens.setdefault(key, [])
            if source not in sources:
                sources.append(source)
    return dict(sorted(tokens.items()))


def dialogue_coverage(rows: list[dict[str, str]]) -> dict[str, object]:
    known = {normalize_word(row["EN"]) for row in rows}
    tokens = extract_dialogue_tokens()
    missing = sorted({DIALOGUE_ALIASES.get(token, token) for token in tokens
                      if token not in IGNORED_DIALOGUE_TOKENS
                      and normalize_word(DIALOGUE_ALIASES.get(token, token)) not in known})
    return {
        "unique_tokens": len(tokens), "missing_lemmas": missing,
        "ignored_tokens": sorted(set(tokens) & IGNORED_DIALOGUE_TOKENS),
        "aliases": {token: lemma for token, lemma in DIALOGUE_ALIASES.items() if token in tokens},
        "sources": sorted({source for sources in tokens.values() for source in sources}),
    }


def extract_source_entries() -> OrderedDict[str, dict[str, object]]:
    entries: OrderedDict[str, dict[str, object]] = OrderedDict()
    for source_label, source_path in SOURCE_FILES:
        text = source_path.read_text(encoding="utf-8")
        pairs = list(PAIR_RE.findall(text))
        if source_path.name == "script_intro_v2.js":
            pairs.extend(FOREST_RE.findall(text))
        for raw_en, raw_cz in pairs:
            en = decode_js_string(raw_en).strip()
            cz = decode_js_string(raw_cz).strip()
            key = normalize_word(en)
            if not key:
                continue
            entry = entries.setdefault(key, {"en": en, "cz": cz, "sources": []})
            sources = entry["sources"]
            assert isinstance(sources, list)
            if source_label not in sources:
                sources.append(source_label)
    tokens = extract_dialogue_tokens()
    for row in load_dialogue_supplement():
        key = normalize_word(row["EN"])
        sources = sorted({source for token, paths in tokens.items()
                          if normalize_word(DIALOGUE_ALIASES.get(token, token)) == key
                          for source in paths})
        if not sources:
            raise ValueError(f"Supplement entry is absent from MMTX speech: {row['EN']}")
        entries.setdefault(key, {"en": row["EN"], "cz": row["CZ"], "sources": sources})
    return entries


def load_csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise SystemExit(f"Unexpected CSV header: {reader.fieldnames}")
        return list(reader)


def build_plan() -> tuple[OrderedDict[str, dict[str, object]], list[dict[str, str]], list[dict[str, object]]]:
    entries = extract_source_entries()
    current_rows = load_csv_rows()
    current_keys = {normalize_word(row["EN"]) for row in current_rows}
    missing_keys = [
        key for key in entries
        if key not in current_keys and key not in EXCLUDED_NORMALIZED
    ]
    curated = dict(CURATED)
    for row in load_dialogue_supplement():
        curated[normalize_word(row["EN"])] = _row(row["Sentence"], row["SentenceT"])
    speech_missing = dialogue_coverage(current_rows)["missing_lemmas"]
    unreviewed = [word for word in speech_missing if normalize_word(word) not in entries]
    if unreviewed:
        raise SystemExit("Unreviewed MMTX dialogue words: " + ", ".join(unreviewed))
    uncovered = sorted(set(missing_keys) - set(curated))
    if uncovered:
        raise SystemExit("Missing curated sentences for: " + ", ".join(uncovered))

    next_order = max(int(row["Order"]) for row in current_rows) + 1
    planned: list[dict[str, object]] = []
    for offset, key in enumerate(missing_keys):
        source = entries[key]
        sentence, sentence_t, word_set = curated[key]
        planned.append(
            {
                "EN": str(source["en"]),
                "CZ": str(source["cz"]),
                "Order": str(next_order + offset),
                "Sentence": sentence,
                "SentenceT": sentence_t,
                "WS": merge_word_sets(word_set, "Benji"),
                "L": "ne",
                "HT": "ne",
                "sources": list(source["sources"]),
            }
        )
    return entries, current_rows, planned


def append_rows(planned: list[dict[str, object]]) -> None:
    if not planned:
        return
    original = CSV_PATH.read_bytes()
    if not original.endswith(b"\r\n"):
        raise SystemExit("VocabularyEN.csv must end with CRLF before append.")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\r\n")
    for row in planned:
        writer.writerow({field: row[field] for field in FIELDS})
    appended = buffer.getvalue().encode("utf-8")

    descriptor, temp_name = tempfile.mkstemp(prefix="VocabularyEN.", suffix=".tmp", dir=CSV_PATH.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(original)
            handle.write(appended)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, CSV_PATH)
    finally:
        temp_path.unlink(missing_ok=True)


def write_report(path: Path, entries: OrderedDict[str, dict[str, object]], current_rows: list[dict[str, str]], planned: list[dict[str, object]]) -> None:
    current_keys = {normalize_word(row["EN"]) for row in current_rows}
    planned_keys = {normalize_word(str(row["EN"])) for row in planned}
    items = []
    for key, entry in entries.items():
        if key in EXCLUDED_NORMALIZED:
            status = f"excluded_{EXCLUDED_REASONS[key]}"
        elif key in current_keys:
            status = "already_present"
        elif key in planned_keys:
            status = "planned_addition"
        else:
            status = "unresolved"
        items.append({"normalized": key, **entry, "status": status})
    payload = {
        "source_unique_count": len(entries),
        "already_present_count": sum(item["status"] == "already_present" for item in items),
        "planned_addition_count": len(planned),
        "excluded_count": sum(item["normalized"] in EXCLUDED_NORMALIZED for item in items),
        "planned_rows": planned,
        "source_items": items,
        "dialogue_coverage": dialogue_coverage(current_rows),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Append all currently missing curated rows.")
    parser.add_argument("--report-json", type=Path, help="Optional path for a durable audit manifest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries, current_rows, planned = build_plan()
    print(f"MMTX unique entries: {len(entries)}")
    print(f"VocabularyEN rows before: {len(current_rows)}")
    print(f"Already present: {len(entries) - len(planned) - len(EXCLUDED_NORMALIZED)}")
    print(f"Excluded entries: {len(EXCLUDED_NORMALIZED)}")
    print(f"Rows to append: {len(planned)}")
    for row in planned:
        print(f"- {row['Order']}: {row['EN']} | {row['CZ']}")

    if args.report_json:
        report_path = args.report_json.expanduser().resolve()
        write_report(report_path, entries, current_rows, planned)
        print(f"Wrote report: {report_path}")

    if args.apply:
        append_rows(planned)
        print(f"Applied: {len(planned)} row(s)")
    else:
        print("Dry run only. No CSV changes written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
