# Sprava dokumentu - soukromy dokumentovy trezor

Zalozeno: 2026-05-21
Priorita: 1
Stav: MVP tooly implementovane a otestovane 2026-05-21

## Smysl

Mila potrebuje system pro dlouhodobe ulozeni, zařazeni a vyhledavani dulezitych
dokumentu mimo git:

- smlouvy ruzneho druhu,
- pojistne smlouvy a platebni dokumenty,
- dulezite faktury,
- protokoly o udrzbe kotle, fotovoltaiky a dalsich zarizeni,
- dokumenty s technickymi detaily zarizeni,
- potvrzeni, revize, zarucni listy, servisni zaznamy.

Cil neni jen "slozka PDF". Cil je soukromy dokumentovy trezor, ve kterem Samantha
umi bezpecne hledat podle vecneho dotazu, zarizeni, protistrany, data, due date,
typu dokumentu a souvisejiciho projektu.

## Bezpecnostni hranice

- Dokumenty a extrahovane texty patri do `data/private/documents/`.
- `data/private/` je mimo git.
- Do `memory/` patri jen pravidla, workflow a redigovane shrnuti projektu, ne
  obsah dokumentu.
- Do gitu nesmi prijit PDF, OCR texty, plne smlouvy, faktury, osobni udaje,
  rodna cisla, adresy, platebni symboly ani neredigovane kontakty.
- Samantha nesmi dokument smazat ani prepsat bez vyslovneho potvrzeni.
- Vyhledavani v dokumentech je read-only.

## Navrzena struktura soukromeho trezoru

```text
data/private/documents/
  inbox/
    incoming/
    processed/
    rejected/
  vault/
    insurance/
    energy/
    home/
    car/
    health/
    tax/
    warranty/
    other/
  index/
    documents_index.jsonl
    text_index.jsonl
    due_dates.jsonl
  cases/
    <case_id>/
      documents/
      manifest.json
```

Princip:

- `inbox/incoming/` je vstupni karantena pro nove soubory.
- Alternativni vstup ma byt podporen pres potvrzovany intake ze slozky
  Stazene/Downloads: Samantha nejdriv read-only najde kandidaty a ukaze nazev,
  cestu, cas a velikost, az po potvrzeni presune vybrany soubor do inboxu.
- `vault/<oblast>/` je finalni ulozeni po potvrzenem zařazeni.
- `index/` obsahuje strojove metadata a extrahovany text pro vyhledavani.
- `cases/` propojuje dokumenty do pripadu typu "uhrada pojistky", "servis kotle",
  "fotovoltaika - stridac", "smlouva dodavatel energie".

## Zakladni metadata dokumentu

Kazdy dokument ma mit minimalne:

```json
{
  "document_id": "doc-YYYYMMDD-kratky-slug",
  "original_filename": "...",
  "stored_path": "data/private/documents/vault/...",
  "sha256": "...",
  "document_type": "contract|invoice|service_protocol|warranty|manual|payment|other",
  "domain": "insurance|energy|home|car|tax|health|other",
  "counterparty": "...",
  "related_asset": "...",
  "issue_date": "YYYY-MM-DD nebo null",
  "valid_from": "YYYY-MM-DD nebo null",
  "valid_to": "YYYY-MM-DD nebo null",
  "due_dates": [],
  "amounts": [],
  "identifiers": [],
  "tags": [],
  "confidence": "low|medium|high",
  "needs_human_review": true
}
```

## Due date pravidlo

Samantha muze due dates automaticky navrhnout, ale nesmi je brat jako jistotu bez
kontextu:

- `splatnost`, `uhradit do`, `due date`, `payment due` -> kandidat platebniho
  terminu,
- `platnost do`, `valid until`, `konec smlouvy` -> kandidat konce platnosti,
- `servis do`, `revize do`, `kontrola do` -> kandidat servisniho terminu,
- `pocatek`, `platnost od`, `valid from` -> neni deadline, ale kontext.

Kazdy nalezeny datumovy kandidat musi mit:

- raw text kolem data,
- typ kandidata,
- confidence,
- doporucenou akci,
- informaci, zda ma vzniknout reminder.

Reminder se smi ulozit az samostatne potvrzenym krokem do
`data/reminders/reminders.json`.

## Prvni implementacni cil

Minimalni read-only/write-safe workflow je implementovany v `app/documents/`:

1. `prepare_document_import`
   - read-only nahled lokalniho souboru z `data/` nebo `/private/tmp`,
   - spocita hash,
   - zkusi textovou extrakci,
   - navrhne metadata a due date kandidaty,
   - nic nekopiruje ani nezapisuje.
2. `inspect_document_text`
   - extrahuje text z PDF nebo ulozi, ze OCR/text neni dostupny,
   - najde kandidaty na due dates,
   - nic neuklada jako fakt bez potvrzeni.
3. `apply_document_import`
   - po potvrzeni kopiruje dokument do `vault/<domain>/<document_id>/`,
   - zapise manifest a index,
   - neuklada do git.
4. `search_private_documents`
   - read-only hleda v indexu a vraci jen bezpecny vyrez, ne cely dokument.
5. `save_document_due_reminder`
   - po samostatnem potvrzeni ulozi konkretni deadline do reminders JSON.
6. `prepare_document_print_job`
   - podle `document_id` nebo jednoznacneho dotazu pripravi kopii dokumentu do
     `data/private/documents/print_queue/`,
   - samotny tisk nespousti.
7. `run_document_print_job`
   - po samostatnem potvrzeni vytiskne pripravenou ulohu,
   - po uspesnem predani tisku smaze jen kopii z `print_queue`,
   - pri chybe tisku kopii ponecha a ohlasi problem.

## Otevrene technicke rozhodnuti

- PDF text extraction: zacit bez nove zavislosti, zjistit dostupne lokalni nastroje
  (`pdftotext`, macOS `mdls`/Spotlight, pripadne Python knihovna pozdeji).
- OCR skenovanych PDF: az druha faze, pravdepodobne samostatny workflow.
- Vyhledavani: prvni verze muze byt JSONL + jednoduche fulltext hledani; pozdeji
  SQLite FTS nebo lokalni vektorovy index.
- Zaloha: soukromy trezor musi byt zahrnut v offline zalohovani, ale nikdy v gitu.

## Implementovano 2026-05-21

- `app/documents/vault.py` - core logika private vaultu, hash, text extraction,
  due date kandidati, JSONL index, search a potvrzeny reminder.
- `app/documents/tools.py` - Samantha tooly a testovatelne `_text` wrappery.
- `app/documents/__init__.py` - export toolu.
- `tests/test_document_vault_tools.py` - testy read-only prepare, potvrzeny import,
  duplicity, search redakce, inspekce podle document_id a potvrzeny reminder.
- `app/samantha_agent.py` - tooly napojene do agenta a popsana bezpecnostni pravidla.

Overeno:

- `.venv/bin/python -m unittest tests.test_document_vault_tools`
- `.venv/bin/python -m unittest tests.test_document_vault_tools tests.test_payment_case_documents tests.test_payment_sms_reminders tests.test_reminders_store tests.test_reminders_tools tests.test_reminders_query_tools`
- `.venv/bin/python -m py_compile app/documents/__init__.py app/documents/vault.py app/documents/tools.py app/samantha_agent.py tests/test_document_vault_tools.py`

## ScanDocu a cockpit 2026-05-27/28

Hlavni aktualni vstupni cesta pro nove skenovane dokumenty je:

1. Mila nafoti dokument a v GPT z nej pripravi PDF.
2. PDF stahne do `Downloads`.
3. `ScanDocu` vezme nejmladsi nezpracovane PDF, vytvori soukromou pracovni kopii,
   udela OCR/navrh metadat a ukaze lokalni webovou kontrolu.
4. Klik `Ulozit` ve ScanDocu je potvrzenim finalniho importu do private vaultu.

Implementovano:

- `app/documents/scandocu.py` - ScanDocu procesor, stav PDF v Downloads,
  priprava kandidata, pravdepodobne duplicity a potvrzeny import.
- `scripts/scandocu_server.py` a `scripts/start_scandocu.sh` - lokalni ScanDocu
  server a spousteci wrapper.
- `app/cockpit.py`, `scripts/cockpit_server.py`, `scripts/start_cockpit.sh` -
  prvni prototyp `Samantha Cockpit` na `http://127.0.0.1:8770`.

Rozhodnuti:

- Cockpit zatim neni samostatny projekt. Je to lokalni ovladaci vrstva k
  dokumentovemu workflow a dalsim rutinnim schopnostem Samanthy.
- Pokud se z cockpitu stane obecny ridici panel pro vice oblasti, muze se
  pozdeji presunout do samostatne infrastructure capability.

Overeno:

- ScanDocu bezi lokalne na `http://127.0.0.1:8766`.
- Cockpit bezi lokalne na `http://127.0.0.1:8770`.
- Oprava samostatneho okna ScanDocu byla Milou overena: zavreni ScanDocu uz
  nezavira cockpit.
- Testy dokumentoveho vaultu prosly s novymi ScanDocu scenari.

## Checkpoint 2026-05-28 - reimport a revize ulozenych priloh

Aktualni smer:

- Pokracovat dokument po dokumentu, ne hromadne bez kontroly.
- Pro nove nebo znovu pripravene PDF pouzivat `Downloads -> ScanDocu -> kontrola -> Ulozit`.
- Pro drive ulozene dokumenty pouzit ScanDocu review rezim a po lidskem potvrzeni
  aktualizovat jen metadata existujiciho dokumentu, ne vytvaret duplicitni novy
  zaznam.

Hotove zlepseni:

- ScanDocu review rezim `?mode=review` a cockpit tlacitko `Revidovat ulozene`.
- Lepsi nacteni a navrh metadat pro vozidla: druh vozidla, znacka/model a SPZ/RZ,
  pokud jsou v textu dostupne.
- Sifrovana PDF maji ve ScanDocu jasnou napovedu: odemknout lokalne v Preview a
  ulozit novou kopii do Downloads; hesla se nikam neukladaji.
- Po ulozeni odemcene varianty se podobna starsi sifrovana varianta ve fronte umi
  oznacit jako preskocena, aby se znovu nenabizela.
- Bez potvrzeni `Presto ulozit jako dalsi dokument` ScanDocu neulozi dokument,
  ktery vypada jako pravdepodobna duplicita nebo souvisejici dokument.

Dalsi krok priorita 1:

- Az Mila vlozi novou kopii najemni smlouvy do Downloads, otevrit ScanDocu,
  zkontrolovat kvalitu nacteni, metadata a duplicity a az potom potvrdit ulozeni.
- Pote pokracovat se znovuukladanim/revizi uz ulozenych priloh po jednom dokumentu.

## Checkpoint 2026-05-29 - Cockpit command inbox / hlasove ovladani

Novy koncept:

- iPhone muze slouzit jako jednoduchy hlasovy/textovy ovladac cockpitu.
- Zkratka na iPhonu by po diktovani ulozila kratky prikaz do iCloud inboxu.
- Cockpit na Macu by inbox periodicky kontroloval, prikaz naroutoval na bezpecnou
  schopnost a vysledek zobrazil v panelu.
- Prvni implementace ma byt textovy command inbox bez iPhonu: rucne vlozeny JSON
  prikaz do slozky, poller v cockpitu, intent router a result panel.

Bezpecnostni hranice:

- Automaticky lze spoustet jen read-only akce:
  - hledani dokumentu,
  - hledani e-mailovych hlavicek,
  - status e-mailove komunikace,
  - status PDF ve Downloads,
  - backup/status report.
- Zapisujici nebo rizikove akce se nesmi spoustet hlasem samostatne:
  - tisk,
  - archivace,
  - presun do kose / mazani,
  - odesilani e-mailu nebo SMS,
  - zmena metadat.
- U rizikovych akci smi hlasovy prikaz jen pripravit navrh; finalni krok musi
  potvrdit Mila v cockpitu kliknutim nebo presnou potvrzovaci vetou.

Navrzeny tok:

```text
iPhone Shortcut -> iCloud command inbox -> Cockpit poller -> intent router -> safe tool -> result panel
```

Navrzeny dalsi krok:

- Zalozit `SamanthaCockpitInbox` mimo git, definovat JSON schema prikazu a
  implementovat prvni read-only intent `document_search`.

## Omezena mista MVP

- OCR je implementovane pres Homebrew nastroje `poppler` + `tesseract`:
  `pdftoppm` vykresli stranky a Tesseract cte OCR jazykem `ces+eng`, pokud jsou
  dostupne.
- PDF extrakce zkusi `pdftotext`, potom `pypdf`, potom nouzove dekodovani bajtu,
  potom `pdftoppm + tesseract`, a nakonec experimentální macOS Vision fallback.
- Sifrovana/uzamcena PDF (`/Encrypt`) se nejdriv oznaci jako `pdf-encrypted`;
  bez odemcene kopie nebo hesla z nich OCR nevytahne text.
- Identifikatory, castky a protistrany jsou zatim jednoducha heuristika, ne
  robustni parser vsech dodavatelu.
- Search je JSONL fulltext se snippetem; SQLite FTS nebo embedding index je dalsi
  faze.
- Tiskovy workflow je implementovany jako dvoukrokovy: priprava kopie do
  `print_queue` a az potom potvrzeny systemovy tisk pres macOS `lp`.
- Fyzicky tisk byl dodatecne overen Milou na TXT dokumentu o zkratkach; neni uz
  potreba startovni pripominka k overeni tisku. Codex stale umi technicky
  potvrdit jen predani do macOS tiskove fronty.

## Realny PDF test 2026-05-21

Na tri realne pojistovaci PDF z lokalne stazenych Seznam priloh byl spusten
`prepare_document_import`. Vsechny tri soubory jsou validni PDF, ale jsou
sifrovane/uzamcene (`/Encrypt`). `pdfinfo` na jednom z nich vratilo
`Incorrect password` a Quick Look nahled ukazal jen zamkovou ikonu.

Po testu byla opravena logika extrakce: nouzove dekodovani bajtu uz nema
falesne oznacit obrazove PDF jako textove zpracovane a uzamcena PDF jsou
diagnostikovana jako `pdf-encrypted`.

Tri PDF byla nasledne ulozena metadata-only do
`data/private/documents/vault/insurance/` s document_id:

- `auto-pojisteni-smlouva-2024`
- `auto-pojisteni-navrh-2025`
- `auto-pojisteni-smlouva-3270612451`

`search_private_documents` je najde podle metadat/nazvu/cisla v nazvu. Snippet
u nich rika, ze text zatim neni dostupny a dokument potrebuje OCR.

OCR smoke test na umelem neuzamcenem obrazkovem PDF prosel:

- `Textova extrakce: tesseract-ocr`
- Tesseract nasel text a datum `2026-07-31`.

Dalsi krok pro realne pojistne smlouvy neni dalsi OCR, ale ziskat odemcenou kopii
PDF nebo heslo, pripadne exportovat dokument jako neuzamcene PDF/obrazek.

## Pojistovaci PDF batch 2026-05-21

V lokalnich Seznam priloh bylo mezi pojistovacimi PDF nalezeno:

- 43 kandidatu podle nazvu,
- 32 nezamcenych PDF,
- 11 zamcenych/sifrovanych PDF.

Novy OCR backend byl realne pouzit na:

- `metlife-akciove-fondy-ocr`
  - zdroj: `uid_137596/10_Akciov_fondy_MetLife.pdf`
  - metoda: `tesseract-ocr`
  - vysledek je dohledatelny pres `search_private_documents`
  - OCR rezim byl upraven z `--psm 6` na `--psm 3`, protoze tabulkove PDF davalo
    v psm 6 spatny vystup.

Do insurance vaultu byly navic importovany dve nezamcene textove pojistovaci PDF:

- `kooperativa-pojisteni-vozidla-6300720621-2023`
- `kooperativa-upomenuti-platby-6391193598-2025`

Tato dve PDF se zpracovala pres `pdftotext`, ne pres OCR, protoze uz mela
pouzitelnou textovou vrstvu. Search je najde podle Kooperativy, cisla smlouvy,
splatnosti a obsahu.

## Dalsi OCR doladeni 2026-05-21

Na dalsich trech nezamcenych PDF byla overena standardni cesta `inspect_document_text`:

- `uid_137596/09_Zhodnocen_investice_World_index_21-_akcie_sv_tov_.pdf`
  - nema textovou vrstvu a proslo pres `tesseract-ocr`;
  - jde o tabulkovy MetLife dokument, OCR je pouzitelne pro hledani, ale neni
    dokonale pro presne rozliseni tabulek a splatnosti.
- `uid_134468/05_Zelen_karta.pdf`
  - proslo pres `pdftotext`, OCR se spravne nespoustelo.
- `uid_110188/08_potvrzeni_odpovednosti.pdf`
  - proslo pres `pdftotext`, OCR se spravne nespoustelo.

Porovnani `pdftoppm` DPI 200/250/300 a Tesseract `--psm 3/4/6/11/12` na MetLife
obrazovem PDF ukazalo:

- `--psm 3` zustava nejlepsi vychozi kompromis;
- `--psm 6` je pro tabulkove dokumenty slabsi;
- render 200 DPI dava na testovanem PDF cistsi text nez 250 DPI a mensi docasne
  obrazky, proto byl default OCR render zmenen na 200 DPI.

Overeno po zmene:

- `.venv/bin/python -m unittest tests.test_document_vault_tools tests.test_payment_case_documents tests.test_payment_sms_reminders tests.test_reminders_store tests.test_reminders_tools tests.test_reminders_query_tools`
- `.venv/bin/python -m py_compile app/documents/__init__.py app/documents/vault.py app/documents/tools.py app/samantha_agent.py tests/test_document_vault_tools.py`

## OCR tabulkova PDF 2026-05-21

Na dalsich tabulkovych PDF bylo OCR vynuceno i tam, kde existovala textova vrstva:

- `uid_154544/21_Oce_ovac_tabulky.pdf`
  - 34 stran, OCR zpracovalo standardni limit prvnich 8 stran;
  - text je dobry pro hledani nazvu diagnoz, polozek a poctu dni;
  - rekonstrukce tabulek je jen radkova, ne spolehliva struktura sloupcu.
- `uid_154544/25_Kompletn_porovn_n_nab_dek.pdf`
  - 3 strany, OCR ma velmi vysoky token overlap proti `pdftotext`;
  - kvalita je dobra pro hledani i zakladni metadata, stale ale neni lepsi nez
    existujici textova vrstva.
- `uid_134158/06_Tabulka_asisten_n_ch_slu_eb.pdf`
  - obsahuje PDF znacku `/Encrypt`, ale text i OCR jsou citelne;
  - dosavadni logika byla moc prisna, protoze `/Encrypt` brala jako stopku.

Upravena extrakce PDF: nejdrive se zkusi `pdftotext`/`pypdf`/fallback/OCR a az
pokud vse selze a dokument ma `/Encrypt`, vrati se `pdf-encrypted`. Tim se
nevyhodi dokumenty s owner-encryption nebo omezenymi pravy, ktere jsou presto
citelne bez hesla.

Prakticky zaver: OCR je u tabulek spolehlive pro dohledani, zda dokument obsahuje
tema, smlouvu, vozidlo, polozku nebo castku. Neni spolehlive jako jediny zdroj
pravdy pro presne parovani radek-sloupec, rozhodne splatnosti a presne financni
hodnoty. Pro tyto pripady je treba preferovat textovou vrstvu, pripadne pozdeji
doplnit specializovany tabulkovy parser.

## pdfplumber tabulkovy parser 2026-05-21

Do dokumentoveho trezoru byl pridan volitelny `pdfplumber` backend:

- zavislost je doplnena do `requirements.txt` a nainstalovana v lokalnim `.venv`
  jako `pdfplumber 0.11.9`;
- `extract_text` po uspesnem `pdftotext` nebo `pypdf` zkusi najit tabulky pres
  `pdfplumber`;
- pokud tabulky najde, textova extrakce je oznacena jako
  `pdftotext+pdfplumber-tables` a tabulky se pripoji k indexovanemu textu jako
  radky oddelene `|`;
- pokud `pdfplumber` neni dostupny nebo tabulky nenajde, puvodni extrakce zustane
  beze zmeny.

Realne overeni:

- `21_Oce_ovac_tabulky.pdf`
  - `pdfplumber` nasel 8 tabulek na prvnich 8 z 34 stran;
  - vystup je vyrazne lepsi pro tabulky nez OCR plain text.
- `25_Kompletn_porovn_n_nab_dek.pdf`
  - `pdfplumber` nasel 6 tabulek na 3 stranach;
  - dobre zachytil vozidlo, cenu, RIXO kontakt i platnost kalkulace.
- `06_Tabulka_asisten_n_ch_slu_eb.pdf`
  - `pdfplumber` nasel 6 tabulek na 1 strane;
  - dobre zachytil sloupce asistenčních programu `ZAKLAD`, `IDEAL`, `MAX`, `MAX+`.

Prakticky zaver: pro PDF s textovou vrstvou je `pdfplumber` vhodnejsi nez OCR
pro tabulky. OCR zustava fallback pro skeny. Dalsi zlepseni by bylo pridat
samostatny inspect tool pro tabulky, ktery vrati jen nalezene tabulky a pripadne
zvysi `max_pages` po potvrzeni u dlouhych dokumentu.

## User-friendly intake 2026-05-22

Rucni predpoklad "Mila mi musi rict, ze dal dokument do inboxu" je spatny.
Doplnena vstupni kontrola:

- `scan_document_inbox` je read-only tool nad
  `data/private/documents/inbox/incoming/`;
- vypise cekajici soubory, velikost, cas zmeny a lokalni relativni cestu;
- nic nepresouva, nekopiruje ani neindexuje;
- startup kontext Samanthy obsahuje jen pocet cekajicich dokumentu, ne nazvy
  souboru, aby nebyly zbytecne vystavene citlive nazvy;
- kdyz je pocet vetsi nez nula, Samantha ma Milu pri startu upozornit a nabidnout
  read-only `scan_document_inbox`, potom `prepare_document_import`.

Realny stav pri testu: v inboxu byl nalezen jeden soubor
`potvrzeni_scan_zarovnany.pdf`. Nazev se ma ukazat az ve vystupu toolu, ne ve
startup memory.

Ostry test dokumentu 2026-05-22:

- soubor zustava v `data/private/documents/inbox/incoming/`;
- byl read-only precten pres `tesseract-ocr`;
- navrh zarazeni je `tax` / `tax_income_confirmation`;
- navrzeny `document_id`: `centrum-83-potvrzeni-prijmy-2025`;
- dokument zatim neni ulozeny do vaultu ani zaindexovany, protoze chybi
  samostatne potvrzeni importu;
- nevytvaret reminder: nalezene datum vypada jako datum vystaveni/podpisu, ne
  splatnost.

Bezpecnost: do memory neukladat plny text dokumentu, rodne cislo, adresu, castky
ani jina osobni/danova data. Do memory patri jen tento redigovany stav a dalsi
krok.

## Mobilni iPhone scan intake 2026-05-26

Prvni bezpecna faze mobilniho intake je rozpracovana a realne otestovana:

- iPhone zkratka `Skenovat dokument pro Samanthu v4.shortcut` uklada do iCloud
  slozky `SamanthaDocumentInbox`;
- zkratka umi vice stran pod jednim technickym identifikatorem batchu;
- lidsky nazev dokumentu se uklada do manifestu jako `document_title`;
- druha zkratka `Zpracovat dokumenty pro Samanthu.shortcut` vytvari
  `process_request.json`, ktery signalizuje, ze ma Samantha zpracovat inbox;
- `scan_mobile_document_inbox` je read-only tool, ktery najde process request,
  manifesty a stranky bez mazani nebo importu;
- `prepare_mobile_document_batch` kopiruje zdrojove fotky do pracovniho adresare,
  normalizuje stranky pres Pillow, vytvori PDF a ulozi pracovni manifest;
- zdrojove fotky v iCloud inboxu zustavaji beze zmeny.

Realny test:

- batch `scan_B`;
- lidsky nazev v manifestu: testovaci dokument;
- 2 nalezene stranky;
- pracovni adresar
  `data/private/documents/mobile_inbox/processing/scan_b/`;
- vytvoreno `scan_b.pdf`;
- nad PDF probehl `prepare_document_import`.

Poznamka ke klasifikaci: testovaci text byl o zkratce Najit auto, proto navrh
metadat mohl vypadat jako auto dokument. To neni chyba mobilniho intake, ale
signal, ze dalsi krok ma zlepsit klasifikaci testovacich/technickych dokumentu a
zavest `case_id` pro vecne souvisejici dokumenty.

Bezpecnost: pracovni PDF, fotky a extrahovany text zustavaji v `data/private/`
mimo git. Finalni import do vaultu musi zustat potvrzovany.

## Cockpit dokumentovy checkpoint 2026-06-04

Cockpit je prakticka lokalni ovladaci vrstva pro document management na
`http://127.0.0.1:8770`.

Hotove funkcni oblasti:

- `Dokumenty k revizi`: prehled zero-text/OCR, kratky text, slaba metadata a
  dokumenty cekajici na rucni kontrolu.
- `Vazby / cases`: ukazuje jen skutecne vazby s vice dokumenty; jedno-dokumentove
  samostatne vazby jsou schovane, aby UI nematlo.
- `Klasifikace`: ukazuje pokryti metadat a umoznuje doplnit oblast, typ,
  protistranu a souvisejici vec.
- `Terminy v dokumentech`: ukazuje due-date kandidaty a umi po potvrzeni vytvorit
  pripominku.
- Detail case v2: po rozbaleni case ukazuje dokumenty, otevrene pripominky,
  terminove kandidaty, platebni konflikty a kratke `case_health` doporuceni.

Bezpecnostni pravidla zustavaji:

- Cockpit vraci redigovane reference, ne raw `document_id` v detailu case.
- Plne dokumenty, PDF, OCR texty, cele e-maily a citlive identifikatory zustavaji
  mimo git v `data/private/`.
- Akce typu reminder, tisk, archivace nebo presun do kose zustavaji potvrzovane.

Dalsi prakticky krok:

- Rucne otestovat detail case v UI.
- Potom rozhodnout, zda pokracovat OCR/re-review pipeline pro zero-text dokumenty,
  nebo sjednocenym intake panelem Downloads / e-mail / mobilni sken.

## Vztah k existujicim projektum

- Platebni SMS/reminders: konkretni faktury/prilohy z platebnich pripadu se mohou
  ukladat jako dokumenty nebo case dokumenty.
- E-mail archive: e-mail muze byt zdroj dokumentu, ale cteni e-mailu vyzaduje
  samostatne potvrzeni podle e-mailoveho workflow.
- Lekarna/Tax/Technika domu: mohou byt domény dokumentu, ne samostatne kopie téhož
  PDF v gitu.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii, ale nepouzivat je jako aktivni
startovni stav projektu. Aktualni navazani je v `MEMORY_INDEX.md` pres projektovy
soubor, technicky workflow a posledni aktivni handoff.

- `handoffs/document_management_private_vault_start_2026_05_21.md` - start
  projektu a prvni MVP tooly; prekryto realnymi importy a pozdejsim stavem.
- `handoffs/document_management_private_vault_tax_import_2026_05_22.md` - prvni
  realny tax PDF import a presun zdrojove kopie do `processed`.
- `handoffs/document_management_private_vault_cleanup_done_2026_05_22.md` -
  cleanup workflow po importu, audit `inbox_actions.jsonl` a read-only status.
- `handoffs/document_management_private_vault_status_done_next_steps_2026_05_22.md` -
  kompaktni status po cleanupu; prekryto handoffem k fyzickemu tisku a Downloads
  intake.
- `handoffs/document_management_tax_generali_import_2026_05_22.md` - import
  Generali penzijnich PDF podkladu do oblasti `tax`.
- `handoffs/document_vault_print_workflow_2026_05_22.md` - implementace a test
  dvoukrokoveho print workflow; fyzicke overeni bylo pozdeji potvrzeno Milou na
  TXT dokumentu o zkratkach.
