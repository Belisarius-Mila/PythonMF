# VocabularyFR Web Trainer pro Janu

Zalozeno: 2026-06-04
Priorita: 2
Stav: webovy MVP prototyp funguje lokalne

## Cil

Preklopit francouzskou slovnikovou aplikaci `VocabularyFR/vocab_trainer_fr.py`
do formy, kterou Jana muze pouzivat bez instalovaneho Pythonu, idealne na Macu
a pozdeji i na iPhonu.

Zakladni datovy zdroj zustava:

```text
VocabularyFR/VocabularyFR.csv
```

CSV schema:

```text
FR,CZ,Order,Sentence,SentenceT,L,HT,gender_fr
```

## Aktualni webovy prototyp

Staticka webova aplikace je v:

```text
VocabularyFR/web/
```

Hlavni soubory:

```text
VocabularyFR/web/index.html
VocabularyFR/web/styles.css
VocabularyFR/web/app.js
VocabularyFR/web/audio/
VocabularyFR/web/pict/
```

Lokalni testovaci server:

```text
cd /Users/miloslavfalta/Desktop/PythonMF/VocabularyFR/web
python3 -m http.server 8788 --bind 127.0.0.1
```

URL:

```text
http://127.0.0.1:8788
```

## Hotove funkce

- Nacteni `VocabularyFR.csv`.
- Editace, pridani, vlozeni a smazani radku.
- Export aktualizovaneho CSV.
- Primy zapis do vybraneho CSV v prohlizecich s File System Access API
  (prakticky Chrome/Edge); Safari ma fallback export.
- Vyhledavani, razeni a filtry `vse`, `neumim`, `HT`, `nauceno`,
  `s vetou`.
- Treninkova karta FR/CZ s preklapenim.
- Lokalni audio cache pro FR slova a cast vet.
- Obrazky podle logiky puvodni desktopove aplikace: presny stem,
  `Pict/mapping.json`, fallback `man/woman`, `verb`, `preposition`,
  `proverbs`, `others`.
- Auto smycka: Start/Stop, nahodne/postupne, interval 2-30 s,
  cteni slovo nebo slovo + veta.

## Audio

Puvodni prohlizecovy Web Speech hlas byl prakticky nepouzitelny.
Lepsi smer je lokalni audio cache generovana na Milove Macu:

```text
VocabularyFR/generate_web_audio.py
```

Generator pouziva macOS:

```text
say -v Thomas
afconvert
```

Aktualni stav 2026-06-04:

- `web/audio/fr_words/`: 193 souboru, pokryva vsechna aktualni FR slovicka
  v CSV; nizsi pocet nez 206 radku je kvuli duplicitnim FR slovum.
- `web/audio/fr_sentences/`: 127 souboru.
- Web nejdriv hleda `.m4a`; kdyz chybi, spadne na nouzovy prohlizecovy hlas.

Pri novem slovu nebo nove vete audio automaticky nevznikne ve statickem webu.
Je nutne bud obcas spustit generator u Mily, nebo zvolit robustnejsi architekturu
s lokalnim/helper serverem.

## Obrazky

Priprava webovych obrazku:

```text
VocabularyFR/prepare_web_pict_assets.py
```

Generator bere:

```text
Pict/mapping.json
Pict/
VocabularyFR/MaleFox.PNG
VocabularyFR/FemaleFox.PNG
VocabularyFR/VocabularyFR.csv
```

A vytvori:

```text
VocabularyFR/web/pict/manifest.json
VocabularyFR/web/pict/images/
```

Aktualni stav 2026-06-04:

- `web/pict/images/`: 174 souboru.
- `missing_stems`: 0.
- `VocabularyFR/web/` ma celkem cca 39 MB.

Pro Janin Mac je prakticky nutne dodat celou slozku `VocabularyFR/web/`,
protoze obsahuje aplikaci, audio i obrazky.

## Otevrene architektonicke varianty

### Varianta A: staticky web + servis u Mily

Jana pouziva web a CSV. Pri novych slovech/vetach se obcas vezme aktualni CSV
a u Mily se spusti:

```text
python3 VocabularyFR/generate_web_audio.py
python3 VocabularyFR/prepare_web_pict_assets.py
```

Vyhoda: jednoduche.
Nevyhoda: pro denni praci v zahranici je servisni cyklus otravny.

### Varianta B: mala macOS aplikace bez Pythonu

Webove UI zustane, ale pribude lokalni helper nebo zabalena `.app`, ktera umi
volat macOS `say`/`afconvert` a generovat audio primo na Janine Macu.

Vyhoda: Jana muze denne pridavat slova a audio vznikne hned lokalne.
Nevyhoda: slozitejsi prvni build/deploy.

### Varianta C: Samantha server pres Tailscale

Jana by otevrela web pres zabezpeceny pristup k Milovu Macu/serveru.
Server by ukladal CSV, generoval audio a spravoval assets.

Vyhoda: vse se generuje automaticky.
Nevyhoda: Miluv Mac/server musi byt dostupny a musi se resit bezpecny pristup.

### Varianta D: iPhone / Pythonista 3

Pro iPhone je nejrealistictejsi Pythonista verze nad stejnym CSV.
Pythonista umi pracovat se svou iCloud slozkou `Pythonista 3`, ale je nutny
prakticky test s Janou:

1. Vytvorit v Pythonista iCloud maly `samantha_test.txt`.
2. Overit, ze je videt ve Files na iPhonu.
3. Overit, ze je videt na Janine Macu.
4. Pripadne slozku/soubor nasdilet Milovi.

Riziko: jeden CSV editovany z Mac webu i iPhonu muze mit iCloud konflikty.
Pred servisnim zasahem musi byt zaloha CSV.

## Dalsi doporuceny krok

1. Rucne otestovat prototyp na Milove Macu: CSV load, obrazky, audio, auto smycka,
   editace a export.
2. Rozhodnout, zda primarni cil je Janin Mac nebo iPhone.
3. Pokud Janin Mac: navrhnout malou `.app`/helper variantu pro lokalni generovani
   audia bez Pythonu.
4. Pokud iPhone: vikendovy test Pythonista iCloud slozky a konfliktniho chovani
   CSV.

## Bezpecnost

- Skutecne Janino aktualni CSV pred servisem zalohovat.
- Nepouzivat iCloud/Git jako soucasne editovane uloziste bez konfliktni kontroly.
- Pri commitech davat pozor, ze vedle VocabularyFR existuji nesouvisejici
  rozpracovane zmeny v Samantha memory (`Family Memory Films`).
