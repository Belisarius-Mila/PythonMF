Nazev: Znalostni databaze - systemovy audit a textovy vstup
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-11

Co se resilo:
- Mila zadal podle posledni Quick Note #40 strukturovany audit projektu, toolu a vrstev.
- Vznikl report `memory/reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_11.txt`.
- Pri revizi bylo potvrzeno, ze `Knihovna clanku / web article archive` a `Knowledge inbox / ziva znalostni databaze` patri k sobe.
- Sloucena oblast je ted vedena jako `Znalostni databaze / Knihovna clanku / Knowledge inbox`.
- Mila navrhl budoucí import receptu z historicke Samanthy/ChatGPT bez URL.

Co je hotove:
- `ACTIVE_PROJECTS.md`, `MEMORY_INDEX.md` a `projects/vedecke_clanky.md` uz popisuji jednotnou znalostni databazi bez dvojakeho projektu.
- Cockpit `Knihovna` ma vedle `Ulozit URL` novy vstup `Ulozit text`.
- `app/article_archive.py` umi `archive_text_entry(...)` a uklada rucne vlozene texty jako `manual_text` se zdrojem, poznamkou, kategorii a tagy.
- `scripts/archive_text_entry.py` je CLI fallback pro ulozeni TXT souboru do stejneho soukromeho archivu.
- Recepty bez URL se maji znac kovymi metadaty, napr. `source_label = ChatGPT historický chat`.
- Lokalni i Tailscale Cockpit byly restartovane a smoke check pro `/`, `/api/status`, `/api/recovery/status` prosel.

Co neni hotove:
- Nebyl ulozen zadny realny receptovy obsah.
- Neni hotovy davkovy parser velkeho TXT baliku receptu na jednotlive karty.
- Neni hotovy Cockpit pohled pro tematicke knowledge karty mimo existujici seznam knihovny.
- Report zatim neni opakovatelny systemovy report, jen rucne vytvoreny textovy snapshot.

Dalsi krok:
- Az Mila doda TXT s recepty od historicke Samanthy/ChatGPT, nejdriv udelat read-only rozbor: pocet receptu, navrzene nazvy, kategorie a tagy.

Navrhovane dalsi kroky:
- Okamzite: rucne v Cockpitu ulozit jeden maly testovaci recept jako `Recepty` se zdrojem `ChatGPT historický chat`.
- Potom: pro vetsi TXT balicek pridat preview parser, ktery nic neuklada bez potvrzeni.
- Pozdeji: z reportu `systemovy_audit_projekty_tooly_vrstvy_2026_06_11.txt` udelat opakovatelny systemovy report.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `scripts/archive_text_entry.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/projects/vedecke_clanky.md`
- `memory/reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_11.txt`

Overeni:
- `.venv/bin/python -m unittest tests.test_article_archive tests.test_cockpit` -> 115 tests OK.
- `.venv/bin/python -m py_compile app/article_archive.py app/cockpit.py scripts/archive_text_entry.py tests/test_article_archive.py tests/test_cockpit.py` -> OK.
- `scripts/cockpit_smoke_check.py` pro lokalni i Tailscale Cockpit -> OK.

Bezpecnost / neukladat:
- Necommitovat realne recepty, chat exporty ani obsah `data/private/knowledge_inbox/`.
- Recepty z historicke Samanthy/ChatGPT bez URL oznacovat jako vlozeny nebo syntetizovany text, ne jako overeny webovy zdroj.
