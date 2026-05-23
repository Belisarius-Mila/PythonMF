Nazev: iCloud Mail - fulltextove hledani v telech e-mailu a dnesni read-only test
Priorita: 1
Stav: rozpracovane / ceka na commit a dalsi rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-05-21

## Co se resilo

Mila chtel najit e-maily z roku 2026, kde se v textu nebo tele zpravy vyskytuji
vyrazy:

- `Pojisteni`
- `pripojisteni`
- `vyrocni zprava`

Pozadavek nebyl jen hledani v hlavickach. Bylo potreba fulltextove read-only
hledani v obsahu zprav, ale bez vypisu tel, bez otevreni odkazu a bez jakychkoli
zmen ve schrance.

## Co je hotove

Byl doplnen novy bezpecny tool:

- `app/email/text_search_tools.py`
- `search_email_text_year`
- `search_email_text_year_text`
- `has_explicit_text_search_confirmation`

Byl rozsireny provider:

- `app/email/icloud_provider.py`
- nova metoda `search_text_headers(...)`
- IMAP `SEARCH CHARSET UTF-8 SINCE ... BEFORE ... TEXT ...`
- vystup jen UID + hlavicky + nalezene vyrazy, ne tela zprav.

Byl doplnen model:

- `EmailTextSearchHit` v `app/email/models.py`

Byl doplnen CLI skript:

- `scripts/email_search_text_year.py`

Tool byl napojen do:

- `app/email/__init__.py`
- `app/samantha_agent.py`

Bezpecnostni potvrzeni pro cteni konkretniho UID bylo drobne rozsirovano v:

- `app/email/safety.py`

Pridana testovaci sada:

- `tests/test_email_text_search_tools.py`

Otestovano:

- `.venv/bin/python -m unittest tests.test_email_text_search_tools`
- `.venv/bin/python -m unittest tests.test_email_text_search_tools tests.test_email_triage_tools tests.test_memory_store`
- predtim take navazujici e-mailove testy pro triage/case/archive query.

## Vysledek dnesniho read-only hledani

Po Milove potvrzeni probehlo read-only fulltextove hledani za rok 2026.
Nalezeny byly 4 e-maily, vsechny na vyraz `Pojisteni`.

Do pameti se neuklada obsah e-mailu, plne URL ani citlive detaily.

Po dalsim Milove potvrzeni byla read-only nactena tela dvou UID:

- `13007`
- `12925`

Do pameti se uklada jen fakt, ze byla ctena tato UID. Neuklada se telo e-mailu.

U `12925` provider nenasel textove telo. Muze jit o prilohu, obrazek nebo HTML
strukturu, kterou soucasny extractor neprevedl do textu.

## Co neni hotove

- Zmeny zatim nejsou commitnute.
- Neni jeste vyreseno, zda se ma novy fulltext tool povysit do dokumentace/project
  memory jako trvale hotovy stav.
- Neni vyresene lepsi cteni e-mailu bez textoveho tela, zejmena pripadne prilohy.
- Neni vyresene, zda dalsim krokem ma byt archivace konkretnich UID nebo cteni
  metadat/priloh.

## Dalsi krok

1. Zkontrolovat `git status`.
2. Rozhodnout, zda commitnout nove e-mailove zmeny.
3. Pri commitu pridat jen souvisejici e-mailove soubory, ne `git add .`.
4. Ignorovat nebo samostatne vyresit nesouvisejici untracked soubor
   `scripts/lekarna_apply_pil_short_updates.py`.
5. Pokud Mila bude chtit pokracovat s UID `12925`, nejdriv navrhnout bezpecny
   krok: vypsat metadata priloh nebo kompletni archivaci po samostatnem potvrzeni.

## Zmenene nebo relevantni soubory

- `app/email/__init__.py`
- `app/email/icloud_provider.py`
- `app/email/models.py`
- `app/email/safety.py`
- `app/email/text_search_tools.py`
- `app/samantha_agent.py`
- `scripts/email_search_text_year.py`
- `tests/test_email_text_search_tools.py`
- `memory/handoffs/email_fulltext_search_tool_2026_05_21.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

## Bezpecnost / neukladat

- Neukladat do memory cela tela e-mailu.
- Neukladat plne URL.
- Neukladat e-mailove adresy bez redakce.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- `data/email/`, archivy, cases a reminders jsou lokalni citliva data a nepatri
  do gitu.
- Pri dalsim cteni tela, odkazu, priloh nebo archivaci vzdy vyzadovat konkretni
  potvrzeni podle daneho toolu.
