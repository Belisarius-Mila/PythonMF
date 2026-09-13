#!/usr/bin/env python3
"""Export the two read-only teaching CSVs and an explicit, reviewed image map."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
VOICE = "en-US-JennyNeural"
RATE = "-10%"
REVIEWED_SOURCES = {
    "tobevety.csv": "81216d8f1347882b2c9e35b480191ed3c116badd01238f3154fc3eb2845213fe",
    "verb_conjugation.csv": "fca7bdbafd844045d2bfec9a8812d903b82f13b6aa50cd27d330c1ec9b1bf9d6",
}

# Selected visually from Pict. Generated illustrations fix important attributes
# (a black dog must not be illustrated by the original golden dog).
PICT = {
    "happy": ("happy.webp", "A happy smiling boy"),
    "tired": ("tired.PNG", "Two tired children"),
    "friends": ("friend.webp", "Two friends talking together"),
    "home": ("home.jpg", "A welcoming home"),
    "house": ("house.png", "A house with a garden"),
    "mother": ("mother.webp", "A friendly mother"),
    "student": ("student.webp", "A student studying at a desk"),
    "school": ("school.PNG", "A colorful school building"),
    "sister": ("sister.png", "A smiling young woman"),
    "teacher": ("teacher.webp", "A teacher beside a classroom board"),
    "city": ("city.PNG", "A busy city with tall buildings"),
    "grey-sky": ("cloudy.webp", "Grey clouds in the sky"),
    "blue-sky": ("sky.webp", "A bright blue sky above a meadow"),
    "sun": ("sun.webp", "The sun shining over a meadow"),
    "window": ("window.webp", "An open window overlooking a garden"),
    "cake": ("cake.png", "A slice of fruit cake"),
    "father": ("father.PNG", "A friendly father"),
    "radio": ("radio.webp", "A woman listening to a radio"),
    "old": ("old.jpg", "An older woman"),
    "book": ("book.jpg", "A book"),
    "bike": ("bike.jpg", "A bicycle"),
    "car": ("car.PNG", "A red car"),
    "work": ("work.webp", "A person working at a desk"),
    "fast": ("fast.webp", "A runner moving fast"),
    "garden": ("garden.jpg", "A green garden"),
    "blue": ("blue.jpg", "A collection of blue objects"),
    "black": ("black.jpg", "A collection of black objects"),
    "green": ("green.webp", "A green toy brick"),
    "yellow": ("yellow.jpg", "A collection of yellow objects"),
    "pink": ("pink.png", "A collection of pink objects"),
    "red": ("red.webp", "A red toy brick"),
    "young": ("young.PNG", "A young person"),
    "cinema": ("cinema.png", "The entrance to a cinema"),
    "restaurant": ("restaurant.jpg", "The inside of a restaurant"),
    "shop": ("bookstore.webp", "A book shop"),
    "boy": ("boy.png", "A young boy"),
}
GENERATED = {
    "black-dog": "A black dog with four legs in a garden",
    "white-cat": "A white cat in a garden",
    "pink-dress": "A pink dress on a hanger",
    "black-bag": "A black school backpack",
    "green-eyes": "A person with green eyes",
    "siblings": "A tall brother and his small younger sister",
    "prague": "Prague, Charles Bridge and Prague Castle",
    "two-sisters": "Two sisters standing together in a garden",
    "male-teacher": "A male teacher beside a classroom board",
    "school-friends": "Four happy school friends outside their school",
    "tall-men": "Two tall men standing together in a park",
}

# One deliberate entry per original CSV row; never an unpredictable keyword fallback.
SENTENCE_IMAGES = """
happy boy friends tired home home mother student student siblings student teacher
school city boy friends grey-sky prague tired home school friends prague black
school garden home garden tired sister black-bag garden blue garden student school
white-cat school city tired prague green-eyes city yellow sun siblings teacher home
mother prague tired happy school home garden blue-sky city window friends friends
school black-dog siblings happy city garden siblings sister city green cake tired
teacher friends city red radio black-dog pink-dress happy home pink student student
white-cat boy boy old student boy prague
black-dog book bike white-cat black-dog school teacher car
school home work prague fast city garden school
""".split()
VERB_IMAGES = """
old young siblings siblings blue friends mother home
black-dog green-eyes siblings white-cat black house garden car
home school cinema friends fast friends restaurant shop
""".split()


def read_csv(name):
    if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != REVIEWED_SOURCES[name]:
        raise ValueError(f"{name} changed: review the per-row image mapping before rebuilding.")
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def audio_key(text):
    return hashlib.sha256(f"{VOICE}|{RATE}|{text}".encode()).hexdigest()[:20]


def build_data():
    audio = {}

    def clip(text):
        key = audio_key(text)
        audio[key] = {"text": text, "src": f"assets/audio/{key}.mp3"}
        return key

    sentences = read_csv("tobevety.csv")
    verbs = read_csv("verb_conjugation.csv")
    assert len(sentences) == len(SENTENCE_IMAGES) == 107
    assert len(verbs) == len(VERB_IMAGES) == 24
    lesson_counts = {"be": 0, "have": 0, "go": 0}
    exported_sentences = []
    for row, scene in zip(sentences, SENTENCE_IMAGES):
        lesson = row["Lekce"]
        lesson_counts[lesson] += 1
        question = row["Otázka"]
        age = next((f"{n} years old" for n in ("five", "seven", "eight", "ten") if f"{n} years old" in question), "")
        row_id = f"{lesson}-{lesson_counts[lesson]:03}"
        # Explicit corrections after reviewing the actual illustration contents.
        overrides = {
            "be-008": "school-friends", "be-009": "school-friends", "be-011": "school-friends",
            "be-012": "male-teacher", "be-016": "school-friends", "be-046": "tall-men",
            "be-047": "male-teacher", "be-064": "school-friends", "be-068": "two-sisters",
            "be-073": "male-teacher", "be-080": "school-friends", "be-083": "school-friends",
            "be-086": "school-friends", "be-089": "school-friends", "have-006": "school-friends",
            "have-007": "male-teacher", "go-005": "car",
        }
        scene = overrides.get(row_id, scene)
        exported_sentences.append({
            "id": f"{lesson}-{lesson_counts[lesson]:03}", "lesson": lesson,
            "question": question, "positive": row["Kladná odpověď"],
            "negative": row["Záporná odpověď"], "image": scene, "age": age,
            "audio": {"question": clip(question), "positive": clip(row["Kladná odpověď"]), "negative": clip(row["Záporná odpověď"])},
        })
    exported_verbs = []
    for index, (row, scene) in enumerate(zip(verbs, VERB_IMAGES), 1):
        if index == 11:
            scene = "two-sisters"
        if index == 20:
            scene = "school-friends"
        if index == 21:
            scene = "car"
        p, v, rest = row["Pronoun"], row["Verb"], row["Adverbial"]
        aux, base = row["QuestionAux"], row["QuestionVerb"]
        statement = f"{p} {v} {rest}."
        statement = statement[0].upper() + statement[1:]
        question = f"{aux} {p} {base} {rest}?" if aux else f"{base} {p} {rest}?"
        question = question[0].upper() + question[1:]
        lesson = "be" if not aux else ("have" if base == "have" else "go")
        exported_verbs.append({"id": f"verb-{index:03}", "lesson": lesson,
            "pronoun": p, "verb": v, "rest": rest, "aux": aux, "base": base,
            "statement": statement, "question": question, "translation": row["Translation"],
            "image": scene, "audio": {"statement": clip(statement), "question": clip(question)}})
    images = {k: {"src": f"assets/images/{k}.webp", "alt": alt, "origin": f"Pict/{name}"} for k, (name, alt) in PICT.items()}
    images.update({k: {"src": f"assets/images/{k}.webp", "alt": alt, "origin": "Generated for ToBeToHave"} for k, alt in GENERATED.items()})
    return {"version": 1, "voice": VOICE, "rate": RATE, "sentences": exported_sentences,
        "verbs": exported_verbs, "images": images, "audio": audio,
        "sourceHashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ("tobevety.csv", "verb_conjugation.csv")}}


if __name__ == "__main__":
    data = build_data()
    WEB.mkdir(exist_ok=True)
    (WEB / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported {len(data['sentences'])} questions, {len(data['verbs'])} constructions, {len(data['audio'])} unique MP3 references.")
