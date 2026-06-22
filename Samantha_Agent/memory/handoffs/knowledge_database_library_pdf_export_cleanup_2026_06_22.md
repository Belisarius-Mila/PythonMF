Nazev: Knihovna / PDF export clanku a cisteni balastu ve vedeckych clancich
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-22

Co se resilo:
- Do Cockpit Knihovny byl pridan export vybraneho clanku do PDF a potvrzovane odeslani e-mailem.
- Export je dvoukrokovy: nejdriv lokalne pripravi PDF a `.eml` draft v soukromem archivu, potom teprve po presne potvrzovaci vete odesle e-mail.
- E-mail exportu ma marker `X-Samantha-Library-Export: true` a subject prefix `[SamanthaLibraryExport]`, aby se nemel znovu nabizet k ulozeni/importu.
- Po realnem testu PDF exportu se ukazalo, ze jeden ulozeny vedecky clanek mel velke mnozstvi balastu z webu. Byla doplnena automaticka extrakce/cisteni textu pri URL importu a samostatny cleanup tool pro uz ulozene clanky.

Co je hotove:
- `app/article_archive.py`:
  - `prepare_article_pdf_export(...)` vytvari PDF a e-mailovy draft bez odeslani.
  - `send_article_pdf_export(...)` odesila az po potvrzeni.
  - extrakce clanku umi odstranit social/share bloky, vlozene doporucovaci bloky, tagy a dlouhy webovy tail.
  - `article_text_cleanup_report(...)` najde podezrele ulozene clanky.
  - `cleanup_article_text(...)` prepise `article.txt` cistou extrakci ze zachovaneho `source.html`, vytvori soukromou zalohu puvodniho textu a aktualizuje `metadata.json` i `registry.jsonl`.
- `scripts/clean_article_archive_texts.py`:
  - CLI dry-run/apply tool pro cisteni ulozenych clanku.
  - Pouzity prikaz pro dry-run: `.venv/bin/python scripts/clean_article_archive_texts.py --category science`.
  - Pouzity potvrzeny apply: `.venv/bin/python scripts/clean_article_archive_texts.py --category science --apply --confirm "Potvrzuji vyčištění článků knihovny"`.
- Cockpit:
  - v modalnim okne `Knihovna` pribyla tlacitka `Připravit PDF` a `Odeslat export`.
  - endpointy `/api/library/export/prepare` a `/api/library/export/send`.
  - lokalni i Tailscale Cockpit byly po zmenach restartovane a odpovidaly.
- Testy:
  - `.venv/bin/python -m unittest tests.test_article_archive tests.test_cockpit` proslo: 167 testu OK.
  - `.venv/bin/python -m py_compile app/article_archive.py app/cockpit.py scripts/clean_article_archive_texts.py` proslo; zustava starsi nesouvisejici `SyntaxWarning` v HTML stringu Cockpitu.
  - `git diff --check` pro upravene soubory proslo.

Co bylo vycisteno v soukromych datech:
- Kategorie `science`: zkontrolovano 10 ulozenych vedeckych clanku.
- Kandidat k cisteni byl jen jeden: clanek o bateriich elektromobilu z `vietnam.vn`.
- U nej byl `article.txt` zkracen z 16602 znaku na 2682 znaku.
- Odstranen byl webovy balast typu doporuceni, trendy, komentare a footer.
- Puvodni text zustal jako soukroma zaloha:
  `data/private/article_archive/articles/2026-06-13_prulom-ktery-ozivuje-baterie-elektromobilu_851c2f13/article_before_cleanup_20260621_223734.txt`
- Po cisteni dry-run ukazuje 0 kandidatu v kategorii `science`.

Co neni hotove:
- Zmeny nejsou commitnute ani pushnute.
- PDF export zatim vklada do PDF text a metadata vcetne seznamu priloh; nevklada obrazkove prilohy primo do PDF.
- E-mail intake jeste explicitne nefiltruje podle noveho export markeru ve vsech budoucich cestach; marker je pripraveny, navazujici filtr lze doplnit samostatne.
- Cleanup tool je zatim CLI/backend, neni jako samostatne tlacitko v Cockpitu.
- Nebyl delan plny audit vsech kategorii knihovny; cisteni bylo pouzito jen na `science`.

Dalsi krok:
- Pred dalsi praci udelat git safety kontrolu a tematicky commit kodovych zmen Knihovny bez soukromych dat.

Navrhovane dalsi kroky:
- Okamzite:
  - Spustit `git status --short` a zkontrolovat, ze do commitu nepujdou `data/private/` ani autosave.
  - Commitnout jen kod/testy: `app/article_archive.py`, `app/cockpit.py`, `tests/test_article_archive.py`, `tests/test_cockpit.py`, `scripts/clean_article_archive_texts.py`.
- Volitelne pozdeji:
  - Doplnit e-mail intake filtr na `X-Samantha-Library-Export: true` a `[SamanthaLibraryExport]`.
  - Pridat Cockpit akci/report pro cleanup kandidaty.
  - Otestovat PDF export na dalsim bezpecnem clanku.
  - Spustit dry-run cleanup pro dalsi kategorie (`recipes`, `ai_tools`, `other`) bez apply.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `scripts/clean_article_archive_texts.py`
- `data/private/article_archive/` - soukroma data, mimo git, necommitovat

Aktualni git stav k handoffu:
- Modifikovane: `app/article_archive.py`, `app/cockpit.py`, `tests/test_article_archive.py`, `tests/test_cockpit.py`
- Nove: `scripts/clean_article_archive_texts.py`
- Nesouvisejici untracked mimo Samantha oblast: `../MatysekANJ/web_mmtx_scene02_cursor_prototype/` - nesahat bez zvlastniho pokynu

Bezpecnost / neukladat:
- Do gitu nepatri PDF exporty, `.eml` drafty, soukrome texty clanku, `data/private/article_archive/`, ChatGPT export ani `data/session_autosave/`.
- V handoffu nejsou opsane texty clanku ani citlive obsahy.
- E-mailove odeslani je externi akce a zustava potvrzovane pres presnou vetu.
