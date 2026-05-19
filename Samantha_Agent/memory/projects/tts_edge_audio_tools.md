# TTS: české audio nástroje přes edge-tts

## Stav

V projektu `PythonMF` byly vytvořeny nástroje pro generování českého MP3 audia pomocí knihovny `edge-tts`.

Vznikly soubory:

- `scripts/generate_tts.py`
- `scripts/tts_gui.py`

Byla nainstalována knihovna:

- `edge-tts`, ověřená verze `7.2.7`

## Cíl

Cílem je mít praktický způsob, jak vytvářet české hlasové MP3 soubory pro výukové aplikace, pohádky, slovíčka a další projekty.

Jsou podporované dva režimy:

1. dávkové generování z CSV,
2. jednoduché GUI okno pro ruční zadání jednoho textu.

## Důležité poznatky

### Dávkový skript

Soubor:

```text
scripts/generate_tts.py
```

Původní zadání:

- načíst CSV soubor `data/tts_phrases.csv`
- očekávané sloupce: `id,text_cs`
- pro každý řádek vytvořit MP3 soubor:
  - `assets/audio/cs/{id}.mp3`
- použít hlas:
  - `cs-CZ-AntoninNeural`
- použít rychlost:
  - `-10 %`
- pokud MP3 už existuje, přeskočit ho
- pokud je použit parametr `--force`, existující MP3 přepsat
- podporovat argumenty:
  - `--csv`
  - `--out`
  - `--voice`
  - `--force`
- kompatibilita s macOS i Windows

Použití:

```bash
python3 scripts/generate_tts.py
python3 scripts/generate_tts.py --force
python3 scripts/generate_tts.py --csv data/tts_phrases.csv --out assets/audio/cs --voice cs-CZ-AntoninNeural
```

### GUI skript

Soubor:

```text
scripts/tts_gui.py
```

GUI slouží pro praktické ruční vytvoření jednoho MP3 souboru.

Obsahuje:

- pole pro text k namluvení,
- pole pro název MP3 souboru,
- výběr cílové složky,
- volbu hlasu,
- tlačítko `Namluvit a uložit MP3`.

Výchozí hlas:

```text
cs-CZ-AntoninNeural
```

Výchozí rychlost:

```text
-10 %
```

GUI:

- automaticky přidá příponu `.mp3`,
- vytvoří cílový adresář, pokud neexistuje,
- pokud soubor už existuje, zeptá se na přepsání.

Spuštění z adresáře projektu:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF
python3 scripts/tts_gui.py
```

Nebo přes konkrétní Python:

```bash
/usr/local/bin/python3.12 /Users/miloslavfalta/Desktop/PythonMF/scripts/tts_gui.py
```

## Rozhodnutí

`generate_tts.py` je primárně pro dávkové generování z CSV.

`tts_gui.py` je primárně pro běžné ruční použití, když chce Míla zadat nový text, pojmenovat soubor a vybrat cílový adresář.

Proto pokud Míla chce "okno", má spouštět:

```bash
python3 scripts/tts_gui.py
```

Ne:

```bash
python3 scripts/generate_tts.py
```

Později byl `generate_tts.py` upraven tak, že pokud nenajde `data/tts_phrases.csv`, místo tvrdé chyby nabídne nebo otevře GUI režim pro ruční zadání textu.

## Otevřené otázky

- Zvážit, zda má vzniknout jednotné tlačítko v aplikacích pro generování audia.
- Zvážit, zda používat jeden společný audio adresář, nebo adresáře podle projektů.
- Zvážit podporu dalších hlasů, například ženský český hlas.
- Zvážit napojení na slovníkové CSV soubory pro automatické generování výslovnosti.

## Další kroky pro Codex

- Před úpravami TTS nástrojů přečíst:
  - `scripts/generate_tts.py`
  - `scripts/tts_gui.py`
  - tento memory soubor
- Neměnit chování dávkového skriptu bez ověření, že GUI režim zůstane funkční.
- Zachovat kompatibilitu s macOS i Windows.
- Nepřidávat API klíče ani citlivé údaje.
- Při přidávání TTS do dalších aplikací preferovat sdílenou funkci nebo sdílený skript, ne kopírování stejného kódu do více projektů.

## Zdroj

Souhrn ChatGPT/Codex konverzace z 28. 4. a 1. 5. k vytvoření nástroje `generate_tts.py`, GUI aplikace `tts_gui.py`, instalaci `edge-tts` a vysvětlení rozdílu mezi dávkovým CSV režimem a ručním GUI režimem.
