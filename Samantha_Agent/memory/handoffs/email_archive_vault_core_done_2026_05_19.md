Nazev: EmailArchiveVault - cisty core hotovy
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Implementovala se prvni cista cast `EmailArchiveVault` pro kompletni lokalni zalohu dulezitych e-mailu.
- Rozsah byl zamerne omezeny na service nad fake daty, bez IMAPu, bez provideru a bez Samantha toolu.
- Archiv je citlivy lokalni archiv oddeleny od bezpecneho `EmailCaseVault`.

Co je hotove:
- Pridan `app/email/archive_models.py`.
- Pridan `app/email/archive_service.py`.
- Pridany exporty v `app/email/__init__.py`.
- Pridany testy `tests/test_email_archive_service.py`.
- Pridano `.gitignore` pravidlo pro `data/email/archive/` v `Samantha_Agent/.gitignore`.
- Doplneno odpovidajici pravidlo i do root `.gitignore`.
- Service uklada do explicitne predane slozky:
  - `metadata.json`,
  - `body.txt`,
  - `body.html`, pokud je predan,
  - `links.json` s plnymi URL,
  - `attachments/attachments.json` pouze s metadaty,
  - `original.eml`, pokud je predan.
- `EmailArchiveSource` umi nest cele telo, HTML, plne URL, metadata priloh a volitelny raw EML.
- Existuje helper `email_message_to_archive_source` pro prevod z existujiciho `EmailMessage` plus volitelne HTML/raw EML.
- Testy bezi jen nad temporary directory a nevytvari realne `data/email/archive/`.

Co neni hotove:
- Neni implementovana read-only provider metoda pro raw EML / HTML archivaci.
- Neni implementovan Samantha tool pro archivaci podle UID.
- Neni implementovan samostatny workflow pro stahovani souboru priloh.
- Neni implementovano cteni archivu zpet do chatu.
- Po realne archivaci se zatim automaticky neaktualizuje `last_archive_at`.

Dalsi krok:
- Doplnit do provideru konzervativni read-only metodu pro archivni nacteni jednoho UID:
  - `select("INBOX", readonly=True)`,
  - `BODY.PEEK[]`,
  - vratit text, HTML, odkazy, metadata priloh a raw EML,
  - bez `STORE`, `COPY`, `MOVE`, `EXPUNGE` a bez mark-read.
- Potom implementovat samostatne potvrzovany Samantha tool pro archivaci jednoho konkretniho UID.
- Po uspesne archivaci aktualizovat `last_archive_at` pres existujici activity state helper.

Zmenene nebo relevantni soubory:
- `app/email/archive_models.py`
- `app/email/archive_service.py`
- `app/email/__init__.py`
- `tests/test_email_archive_service.py`
- `.gitignore`
- `../.gitignore`
- `app/email/activity_state.py`
- `app/email/icloud_provider.py`
- `app/samantha_agent.py`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 93 testu OK.

Bezpecnost / neukladat:
- `EmailArchiveVault` je citlivy lokalni archiv, ne memory.
- Archiv se nikdy nema zapisovat do memory.
- Archiv se nikdy nema commitovat do gitu.
- Archivace nesmi byt automaticky napojena na triage.
- Archivace musi v dalsi fazi vyzadovat samostatne vyslovne potvrzeni s konkretnim UID.
- Tool v dalsi fazi nesmi otevirat odkazy.
- Tool v dalsi fazi nesmi spoustet ani automaticky stahovat prilohy.
- Tool v dalsi fazi nesmi nic odesilat, mazat, presouvat ani oznacovat jako prectene.
- Stahovani souboru priloh ma byt az dalsi samostatne potvrzovany krok.
- Cteni archivu zpet do chatu ma byt samostatny workflow s potvrzenim.
