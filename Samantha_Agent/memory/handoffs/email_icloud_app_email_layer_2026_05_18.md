# Handoff: iCloud Mail app/email read-only vrstva

Nazev: iCloud Mail read-only vrstva `app/email/`
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Mila schvalil navrh male bezpecne architektury pro read-only praci s iCloud Mail
hlavickami. Cilem bylo prevest logiku ze stareho overovaciho skriptu smerem k
normalizovane vrstve v `app/email/`.

## Co je hotove

Vznikly soubory:

- `app/email/__init__.py`
- `app/email/models.py`
- `app/email/config.py`
- `app/email/icloud_provider.py`
- `scripts/email_list_recent.py`

Prvni model je pouze:

- `internal_id`
- `date`
- `sender`
- `subject`

Provider pouziva read-only IMAP pristup:

- `imap.select("INBOX", readonly=True)`
- `UID SEARCH ALL`
- `UID FETCH` s `BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)]`

Stary overovaci skript zustal zachovany:

- `scripts/icloud_list_recent.py`

## Overeni

Probehlo:

```bash
.venv/bin/python -m py_compile app/email/__init__.py app/email/models.py app/email/config.py app/email/icloud_provider.py scripts/email_list_recent.py
.venv/bin/python scripts/email_list_recent.py --help
```

Oboji proslo.

Realny sitovy iCloud test z Codex sandboxu nebyl spusten.

## Bezpecnostni hranice

Nova vrstva nesmi:

- odesilat e-maily,
- mazat e-maily,
- presouvat e-maily,
- oznacovat zpravy jako prectene,
- cist telo e-mailu,
- ukladat obsah e-mailu do memory,
- vypisovat heslo nebo plnou konfiguraci.

Konfigurace se cte jen z lokalniho `.env`, ktery se necommituje.

## Dalsi krok

Mila muze v normalnim SSH terminalu mimo Codex sandbox spustit realny read-only test:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/email_list_recent.py --limit 10
```

Pokud projde, dalsi krok je napojit tuto vrstvu jako bezpecny nastroj pro Samanthu,
stale jen pro hlavicky a bez automatickeho ukladani obsahu do memory.
