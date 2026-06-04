Nazev: Document management - ranni akcni plan
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Po dokonceni sestibodove stabilizace Cockpitu se Mila ptal, co chybi u
  zpracovani dokumentu.
- Vysledek je prakticky akcni plan pro navazani rano: ne obecne ladeni
  Cockpitu, ale zamer na kvalitu a ergonomii dokumentoveho vaultu.

Co je hotove:
- Zakladni workflow dokumentu existuje:
  - `Downloads -> ScanDocu -> kontrola -> vault`,
  - e-mailove PDF prilohy jdou pres Email Work Queue do private document vaultu,
  - Cockpit umi dokumentovou frontu, hledani, detail, tisk, archiv a presun do
    kose,
  - ScanDocu umi revizi ulozenych dokumentu,
  - aktivni `pdf-encrypted` dokumenty byly vyresene; zustava znamy zero-text
    pripad bez textove vrstvy/OCR.
- Cockpit je po stabilizaci pouzitelny:
  - Recovery centrum,
  - lehci `/api/status`,
  - health stav tlacitek,
  - diagnostika,
  - akcni fronta `Co ted delat`,
  - bezpecny restart Cockpitu.

Co neni hotove:
1. Zero-text / OCR prehled
   - Chybi jasny seznam dokumentu bez textu nebo s prilis kratkym textem.
   - U kazdeho ma byt navrzena akce: OCR, rucni revize, nebo oznacit jako OK
     bez textu.

2. Jednotny intake dokumentu
   - Hlavni cesta je Downloads -> ScanDocu.
   - E-mail prilohy uz existuji pres Work Queue.
   - Mobilni sken/iPhone cesta existuje v historickych handoffech, ale neni
     sjednocena v jednom prehledu.
   - Chybi panel typu: `Nove dokumenty ze zdroju: Downloads / e-mail / mobilni
     sken`.

3. Re-review starsich dokumentu
   - ScanDocu umi `Revidovat ulozene`, ale chybi jasny seznam, co ma jeste
     smysl znovu projit.
   - Kandidati: `needs_review`, slaba metadata, zero-text, metadata-only nebo
     starsi dokumenty bez novejsi revize.

4. Vazby mezi dokumenty
   - Metadata a `related_asset` existuji, ale chybi pohodlne pripady/cases:
     auto pojisteni, najemni smlouva, kotel/servis, FVE, dane.
   - Cilem je otevrit jednu vec a videt smlouvu, dodatky, faktury, platby a
     reminders.

5. Ergonomie klasifikace
   - ScanDocu navrhuje metadata, ale kontrola by mela byt prehlednejsi:
     typ dokumentu, oblast, protistrana, souvisejici vec, castky, terminy,
     jistota navrhu.
   - Pomohl by rychly kontrolni formular misto dlouheho detailu.

6. Due dates -> Reminders
   - Kandidati na datumy existuji.
   - Chybi pohodlny potvrzovaci tok: `Z tohoto data udelat pripominku?`
   - Priorita jsou platby, konec platnosti, servis a revize.

Dalsi krok:
- Rano zacit nejmensim uzitecnym krokem: `zero-text/OCR + re-review seznam`.
- Nejdriv read-only zmapovat aktualni stav vaultu:
  - kolik dokumentu ma nulovy nebo velmi kratky text,
  - kolik dokumentu ma `needs_review`,
  - ktere dokumenty maji slaba metadata,
  - jestli pro tyto pocty uz existuji helper funkce/testy.
- Potom navrhnout maly Cockpit panel/report `Dokumenty k revizi`.

Navrhovane dalsi kroky:
- Okamzity:
  1. Precist `app/documents/vault.py`, `app/documents/scandocu.py` a existujici
     testy pro review status.
  2. Najit, jak se dnes pocita `stored_documents_review_status`.
  3. Pridat read-only status/report pro zero-text a re-review kandidaty.
  4. Zobrazit ho v Cockpitu bez nove rizikove akce.
- Navazujici:
  - sjednotit intake zdroje,
  - pridat cases/vazby,
  - zlepsit klasifikacni formular,
  - napojit potvrzovane due-date -> reminder.

Zmenene nebo relevantni soubory:
- `memory/handoffs/document_management_morning_action_plan_2026_06_04.md`
- `memory/projects/document_management_private_vault.md`
- `memory/technical/private_document_vault_workflow.md`
- `memory/handoffs/email_processing_cleanup_and_documents_next_2026_06_03.md`
- `memory/handoffs/document_management_scandocu_reimport_checkpoint_2026_05_28.md`
- `app/cockpit.py`
- `app/documents/vault.py`
- `app/documents/scandocu.py`
- `tests/test_cockpit.py`
- `tests/test_document_vault_tools.py`

Bezpecnost / neukladat:
- Neukladat do memory ani gitu obsah dokumentu, PDF, OCR texty, plne snippety,
  adresy, rodna cisla, platebni identifikatory, hesla ani tokeny.
- Ranni prvni krok ma byt read-only status/report.
- Zapisujici akce jako import, reminder, archiv, kos nebo tisk zustavaji
  potvrzovane samostatne.
