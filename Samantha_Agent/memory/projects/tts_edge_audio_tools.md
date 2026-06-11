# TTS: české audio nástroje přes edge-tts

## Stav

V projektu `PythonMF` byly vytvořeny nástroje pro generování českého MP3 audia pomocí knihovny `edge-tts`.

Vznikly soubory:

- `scripts/generate_tts.py`
- `scripts/tts_gui.py`

Byla nainstalována knihovna:

- `edge-tts`, ověřená verze `7.2.7`

Stav k 2026-06-05:

- Lokální hlasový výstup Samanthy má MVP přes macOS `say` + `afplay`.
- Modul `app/speech/local_tts.py` bezpečně přečte krátký text hlasem `Zuzana`, nejdřív vytvoří dočasný AIFF a potom ho přehraje.
- Skript `scripts/speak_text.py` slouží pro ruční smoke test z terminálu.
- Cockpit má endpoint `/api/speech/speak` a tlačítko `Přečíst stav`, které nahlas přečte aktuálně viditelný dashboard stav.
- Cockpit má také tlačítko `Přečíst výběr`: čte aktuálně označený text a kvůli iPhonu si pamatuje poslední textový výběr, pokud klepnutí na tlačítko výběr zruší.
- Hlasový vstup má MVP panel `Hlasový pokyn`: browser nahraje krátké audio přes mikrofon, endpoint `/api/speech/transcribe` ho přepíše přes OpenAI audio transcription a výsledek se pouze zobrazí v textarea. Přepis sám nespouští žádné akce.
- Po prvním ručním testu trval krátký přepis zhruba minutu, proto panel od 2026-06-05 nahrává s nižším audio bitrate a po přepisu ukazuje diagnostiku `celkem / server / OpenAI / audio kB`, aby šlo poznat, jestli je pomalé API volání, přenos nebo velikost nahrávky.
- Po dalším ručním testu 2026-06-05 Míla potvrdil, že přepis už je rychlý; původní problém s minutovým čekáním je po úpravě bitrate/diagnostiky považovaný za vyřešený pro aktuální MVP.
- Test z iPhonu přes vzdálený prohlížeč 2026-06-05 hlásil, že prohlížeč hlasový vstup nepodporuje. Priorita je proto praktický hlasový vstup z Macu; iPhone vstup řešit později jen pokud bude potřeba přes HTTPS/secure context nebo jinou mobilní cestu.
- Po úspěšném přepisu Cockpit automaticky ukládá text hlasového pokynu do soukromého ignorovaného inboxu `data/private/voice_inbox/`: timestampovaný `voice_command_YYYYMMDD_HHMMSS.md`, `latest_voice_command.md` a `index.jsonl`. Není potřeba další tlačítko `Uložit pro Codex`.
- Uložený hlasový pokyn má stav `transcribed_only_not_executed`: Codex/Samantha si ho může později přečíst, ale přepis sám nespouští žádnou akci.
- Důležitý technický poznatek: přehrávání z běžné sandbox relace může selhat na `AudioQueueStart failed (-66680)`, ale stejný výstup funguje mimo sandbox / z běžícího Cockpitu.

Stav k 2026-06-06:

- Adam Voice Mode má praktický terminálový bridge do Codexu, private TTY marker a TTS helper `scripts/speak_edge_open.py` pro přečtení stručného výsledku.
- Cockpit ukazuje běžící Codex relace a jasně označí, která relace je cílem voice bridge.
- Nová Codex/screen relace se ptá, zda má nastavit voice marker na sebe; ruční pokyn `Prosím převezmi voice marker` vyžaduje jednoduché potvrzení `Mám převzít voice marker? y/n`.
- iPhone text fallback `Odeslat přepis Adamovi` po úspěšném odeslání maže textarea, aby ve vzdáleném Cockpitu nezůstával starý pokyn.
- Bridge už při existujícím TTY markeru nepoužívá VS Code GUI fallback po neověřeném doručení, aby netvrdil falešný úspěch v jiné relaci.
- Hlavní nový směr je remote-first provoz: odpověď se nesmí přehrávat jen na Macu, ale má být dostupná a přehratelná v iPhone Cockpitu; potvrzovací žádosti pro rizikové kroky mají chodit do Cockpitu jako approval karty.
- Remote-first část má první funkční checkpoint: Cockpit umí zobrazit poslední Adamovu odpověď, přehrát ji přes browser audio a schválit/odmítnout čekající hlasový pokyn v approval kartě.
- `scripts/adam_voice_reply.py --latest-command` dovoluje Codexu po dokončení terminálového pokynu zapsat stručný finální výsledek zpět do Cockpitu, aby uživatel neviděl jen technickou hlášku bridge.
- Terminal bridge byl zpřesněn tak, aby preferoval označený TTY marker a read-only formulace typu `pošli odpověď` neblokoval jako rizikové, zatímco mazání, commit, push, platby, hesla a tokeny zůstávají ručně potvrzované.
- Priorita 1 pro další práci je Cockpit read-only capability registry: pevný allowlist bezpečných lokálních schopností, approval centrum a návrat výsledku do poslední Adamovy odpovědi v Cockpitu.

Stav k 2026-06-10:

- Voice bridge lépe zachází se starým TTY markerem: pokud marker ukazuje na neaktivní TTY a existuje právě jedna aktivní Codex TTY, bridge použije tuto jedinou aktivní relaci jako bezpečný efektivní cíl.
- Cockpit status vrací `effective_tty`, takže umí rozlišit starý marker od skutečného cíle bridge.
- V Cockpitu vznikl MVP přepínač `Voice bridge cíl`: zobrazuje aktivní Codex relace a dovolí nastavit marker jen na TTY, kterou backend opravdu vidí jako aktivní Codex relaci.
- Aktuální ověřený stav po restartu Cockpitu: marker i efektivní cíl jsou `ttys002`; varování zůstává jen kvůli tomu, že aktuální relace neběží přes `screen`.
- Relevantní commity: `88f160f Use active Codex TTY when voice marker is stale`, `db1ceeb Add Cockpit voice bridge TTY switcher`.

Stav k 2026-06-11:

- Mac TTY bridge byl ověřený bez `screen`: hlasový pokyn z Cockpitu dorazil přímo do aktivní Codex relace.
- `scripts/speak_edge_open.py` má kvůli rychlosti a sandboxu výchozí lokální režim přes macOS `say`, takže běžný hlasový výsledek nevyžaduje síť ani eskalaci mimo sandbox.
- Online Edge MP3 zůstává dostupné explicitně přes `--engine edge`; diagnostický režim `--engine edge-fallback` nejdřív zkusí Edge a při selhání použije lokální hlas.

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
