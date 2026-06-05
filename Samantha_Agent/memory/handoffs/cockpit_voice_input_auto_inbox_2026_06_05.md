Nazev: Cockpit hlasovy vstup - automaticky private inbox pro Codex
Priorita: dulezite
Pripomenout pri startu: ne
Stav: MVP hotove, ceka na dalsi rozhodnuti
Datum: 2026-06-05

## Kontext

Mila chtel, aby hlasovy vstup v Cockpitu po nahrani a prepisu nemusel mit dalsi
tlacitko `Ulozit pro Codex`. Prakticky cil: nahrat hlas na Macu, prepsat ho a
rovnou ulozit prepsany text tak, aby si ho mohl dalsi Codex/Samantha krok precist.

Predtim byl overen prvni hlasovy vstup:

- lokalni hlasovy vystup pres macOS hlas `Zuzana`,
- Cockpit endpoint `/api/speech/speak`,
- tlacitka `Precist stav` a `Precist vyber`,
- panel `Hlasovy pokyn`,
- endpoint `/api/speech/transcribe`,
- rychlost prepisu po snizeni bitrate je podle Milova testu dobra.

Test z iPhonu pres vzdaleny browser hlasil, ze prohlizec mikrofon nepodporuje.
Aktualni priorita je proto Mac hlasovy vstup.

## Aktualni stav

Po uspesnem prepisu Cockpit automaticky uklada text hlasoveho pokynu do:

```text
data/private/voice_inbox/
```

Vznika:

```text
data/private/voice_inbox/latest_voice_command.md
data/private/voice_inbox/voice_command_YYYYMMDD_HHMMSS.md
data/private/voice_inbox/index.jsonl
```

Soukromy inbox je pod `data/private/`, tedy ignorovany Gitem.

Kazdy ulozeny hlasovy pokyn ma stav:

```text
transcribed_only_not_executed
```

To znamena: prepis se ulozi pro pozdejsi prevzeti, ale sam od sebe nespousti
zadnou akci.

## Zmenene soubory

- `app/cockpit.py`
- `app/speech/__init__.py`
- `app/speech/local_tts.py`
- `app/speech/transcribe.py`
- `scripts/speak_text.py`
- `tests/test_cockpit.py`
- `tests/test_speech_local_tts.py`
- `tests/test_speech_transcribe.py`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/ACTIVE_PROJECTS.md`
- tento handoff

## Overeni

Proslo:

```text
.venv/bin/python -m unittest tests.test_cockpit tests.test_speech_transcribe
.venv/bin/python -m py_compile app/cockpit.py app/speech/transcribe.py
```

Vysledek testu:

```text
Ran 85 tests ... OK
```

Cockpit byl pres bezpecny endpoint restartovan:

```text
POST /api/cockpit/restart
```

Po restartu `/api/status` odpovidal a HTML obsahovalo aktualni hlasovy panel.

## Dalsi prakticky krok

Rozhodnout, jak ma Codex/Samantha prevzit ulozeny text:

1. prikazem typu `zpracuj posledni hlasovy vstup`,
2. jako read-only intent v Cockpitu,
3. nebo jako navazani na lokalni buffer posledni odpovedi.

Bezpecnostni hranice zustava:

- hlasovy pokyn muze pripravit nebo najit informace,
- rizikove akce jako mazani, posilani e-mailu/SMS, tisk, archivace a zmeny
  dokumentu musi zustat potvrzovane.

## Co necommitovat

- `data/private/voice_inbox/`
- zadne audio nahravky,
- zadne tokeny, API klice ani soukroma data z prepisu.
