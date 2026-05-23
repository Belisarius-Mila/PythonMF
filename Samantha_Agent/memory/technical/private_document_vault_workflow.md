Nazev: Workflow soukrome spravy dokumentu
Priorita: 1
Stav: MVP implementovano 2026-05-21
Datum: 2026-05-21

## Cil

Samantha ma umet bezpecne prijimat, tridit a prohledavat dulezite soukrome
dokumenty mimo git:

- smlouvy vseho druhu,
- pojistky,
- faktury a platebni predpisy,
- protokoly o servisu a revizich,
- dokumentaci ke kotli, fotovoltaice, autu, domu a zarizenim,
- zarucni listy a servisni historii.

Dokumenty ani extrahovane texty nepatri do gitu. Patri do `data/private/`.
Memory muze obsahovat jen pravidla, stav projektu a redigovane shrnuti.

## Uloziste

Navrzena lokalni struktura:

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
  cases/
    <case_id>/
      documents/
      manifest.json
  index/
    documents_index.jsonl
    text_index.jsonl
    due_dates.jsonl
    inbox_actions.jsonl
```

`data/private/` musi zustat mimo git. Pred implementaci MVP overit `.gitignore`.

## Workflow vlozeni dokumentu

1. Intake
   Uzivatel doda PDF nebo cestu k souboru. Samantha dokument nema mazat ani
   presouvat bez potvrzeni. Prvni bezpecny krok je pripravit import.
   Vedle rucniho vlozeni do `data/private/documents/inbox/incoming/` ma vzniknout
   i potvrzovany intake ze slozky Stazene/Downloads: uzivatel rekne, ze dokument
   je ve Stazenych, Samantha read-only najde kandidaty, ukaze nazev, cestu, cas
   ulozeni/zmeny a velikost, a teprve po samostatnem potvrzeni presune vybrany
   dokument do inboxu. Bez potvrzeni se ze Stazenych nic nepresouva ani nemaze.

2. Fingerprint
   Vypocitat `sha256`, velikost souboru, puvodni nazev, typ souboru a datum
   importu. Pokud stejny hash uz existuje, navrhnout propojeni se stavajicim
   dokumentem misto duplicitniho importu.

3. Extrakce textu
   U PDF nejprve zkusit textovou extrakci bez OCR. Pokud dokument nema textovou
   vrstvu nebo je text prilis kratky, oznacit `ocr_needed: true`.
   OCR je az druha faze projektu.

4. Navrh metadata
   Z textu a nazvu navrhnout `document_type`, `domain`, `counterparty`,
   `related_asset`, identifikatory, castky, datumy, due date kandidaty a tagy.

5. Kandidati na due date
   Kazde nalezene datum musi mit kontext:

   - raw text z okoli data,
   - typ kandidata,
   - confidence,
   - doporucenou akci,
   - zda je vhodne vytvorit reminder.

   Zakladni pravidla:

   - `splatnost`, `uhradit do`, `zaplatit do` = platebni deadline,
   - `platnost do`, `konec smlouvy`, `do kdy je smlouva platna` = konec
     platnosti,
   - `revize do`, `servis do`, `kontrola do` = servisni deadline,
   - `pocatek`, `platnost od`, `datum vystaveni` = kontext, ne automaticky
     deadline.

6. Lidske potvrzeni
   Pred definitivnim zarazenim Samantha ukaze navrzenou kategorii, metadata,
   kandidaty na due date a cilovou cestu. Bez potvrzeni se dokument nepresune
   do trezoru a nevznikne reminder.

7. Apply import
   Po potvrzeni zkopirovat dokument do `vault/<domain>/` nebo
   `cases/<case_id>/documents/`, ulozit manifest a indexy. Puvodni soubor jen
   oznacit jako zpracovany nebo ponechat, nemazat.

8. Reminder
   Reminder vznikne jen ze schvaleneho due date. Platebni a servisni pripominky
   se zapisuji pres existujici reminders system do `data/reminders/reminders.json`.
   Do reminderu neukladat cely dokument ani citlivy text.

## Vyhledavani

MVP vyhledavani:

- `documents_index.jsonl` pro metadata,
- `text_index.jsonl` pro extrahovany text a kratke snippety,
- `inbox_actions.jsonl` pro auditni stopu zdrojovych souboru z inboxu:
  presun do `processed`, smazani, SHA, `document_id`, puvodni a cilova cesta,
- vysledek dotazu vraci nazev, kategorii, datum, protistranu, cestu a kratky
  kontext.

Bez dalsiho potvrzeni nevracet cele texty smluv nebo faktur do chatu. Pro beznou
praci staci snippety a metadata. Pokud Mila vyslovne pozada o detail konkretniho
dokumentu, lze zobrazit vetsi cast textu.

Pokud k dokumentu existuje zaznam v `inbox_actions.jsonl`, vysledek hledani ma
ukazat i stav zdrojove kopie: cestu v `inbox/processed/`, nebo informaci, ze
byla z inboxu smazana po potvrzeni.

Pozdejsi faze:

- SQLite FTS index,
- lokalni embedding index,
- OCR pro skenovana PDF,
- vazby mezi dokumenty, platbami, emaily a pripominkami.

Poznamka z realneho testu 2026-05-21: prvni tri realne pojistovaci PDF ze
Seznam priloh jsou sifrovane/uzamcene (`/Encrypt`). Aktualni MVP je spravne
oznaci jako `pdf-encrypted`; OCR z nich bez odemceni nevytahne text, protoze
render dava jen zamkovou ikonu.

OCR vrstva 2026-05-21:

- nainstalovano `poppler`, `tesseract`, `tesseract-lang`,
- backend `pdftoppm + tesseract` funguje na neuzamcenem obrazkovem PDF,
- jazykovy rezim preferuje `ces+eng`,
- macOS Vision helper zustava experimentální fallback, ale v tomto prostredi
  nevracel spolehlive vysledky.

## Navrzene tooly

1. `prepare_document_import`
   Read-only kontrola souboru, fingerprint, detekce duplicity, prvni textova
   extrakce a navrh metadata. Nic netrvale nepresouva.

2. `inspect_document_text`
   Detailni read-only analyza uz pripraveneho dokumentu, vcetne due date
   kandidatu.

3. `apply_document_import`
   Write-safe tool. Vyzaduje potvrzeni cilove kategorie, `document_id` a cesty.
   Zkopiruje dokument do private vaultu a zapise index.

4. `search_private_documents`
   Read-only hledani v private indexu. Vraci metadata a snippety.

5. `save_document_due_reminder`
   Vytvori reminder jen z potvrzeneho due date kandidata.

6. `propose_document_inbox_cleanup`
   Read-only navrh po zpracovani/importu dokumentu. Pouziva se, kdyz zdrojova
   kopie zustava v `inbox/incoming/`. Samantha se ma zeptat: `Dokument xy
   zpracovan, presunout do slozky processed? 1. presunout, 2. smazat.`

7. `resolve_document_inbox_item`
   Write-safe tool pro potvrzeny presun do `inbox/processed/` nebo pro smazani
   z `inbox/incoming/`. Smi pracovat jen se souborem primo v inboxu. Kazdy
   presun nebo smazani musi zapsat auditni radek do
   `index/inbox_actions.jsonl`, aby slo za rok dohledat, co se stalo se
   zdrojovou kopii.

8. `document_vault_status`
   Read-only agregovany status vaultu. Vraci pocty dokumentu, oblasti, typy,
   stav inboxu, pocet zdrojovych kopii v `processed`, due date kandidaty a
   auditni akce. Nesmí vracet obsah dokumentu ani citlive identifikatory.
   Statusove pocty nejsou "od posledniho spusteni", ale celkove pocty v
   indexech. U inbox audit akci musi byt uvedene auditni obdobi od prvni do
   posledni akce a pocet za poslednich 30 dni. Presun do `processed` znamena,
   ze soubor byl odstranen z `inbox/incoming/`, ale zustal fyzicky ulozeny v
   `inbox/processed/`; trvale smazani je samostatna kategorie.

9. `prepare_document_print_job`
   Write-safe priprava tisku. Podle `document_id` nebo jednoznacneho dotazu
   najde jeden dokument ve vaultu a zkopiruje pracovni kopii do
   `data/private/documents/print_queue/`. Originál ve vaultu zustava beze zmeny.
   Pokud dotaz neni jednoznacny, musi vratit kandidaty a vyzadat vyber
   konkretniho `document_id`. Samotny tisk nespousti.

10. `run_document_print_job`
    Potvrzeny tisk pripravene ulohy. Vyzaduje samostatne potvrzeni s
    `print_job_id`, napr. `Potvrzuji, vytiskni print job <id>.` Po uspesnem
    predani tisku systemu smaze jen pracovni kopii z `print_queue`; original ve
    vaultu nikdy nemaze. Pokud tisk selze, kopii v `print_queue` ponecha a
    oznami, ze se tisk nedari.

11. Navrhovany budouci tool: `prepare_document_inbox_from_downloads`
    Read-only vyhledani dokumentu ve slozce Stazene/Downloads podle nazvu,
    pripony nebo casu. Vystup smi ukazat jen kandidaty: nazev, cestu, velikost a
    cas ulozeni/zmeny. Nesmí dokument kopirovat ani presouvat.

12. Navrhovany budouci tool: `move_document_from_downloads_to_inbox`
    Potvrzeny presun vybraneho lokalniho dokumentu ze Stazenych do
    `data/private/documents/inbox/incoming/`. Potvrzeni musi obsahovat presny
    nazev/cestu souboru a souhlas s presunem do inboxu. Tool ma zapsat auditni
    stopu intake akce; nesmi mazat dokument bez dalsiho potvrzeni.

## Bezpecnostni pravidla

- Nikdy neukladat dokumenty do `memory/`.
- Nikdy necommitovat obsah `data/private/documents/`.
- Nikdy neukladat hesla, tokeny, rodna cisla, cele smlouvy ani cele faktury do
  handoffu nebo memory.
- Pri nejistote mezi vice daty nevybrat deadline automaticky; ulozit kandidaty
  a vyzadat potvrzeni.
- Pri emailove priloze nejdrive ulozit dokument jako lokalni soubor, potom ho
  zarazovat workflowem.
- Kdyz `apply_document_import` potrebuje potvrzeni, pripravit Milovi presnou
  vetu k odeslani ve tvaru: `Potvrzuji, uloz dokument <soubor> do oblasti
  <oblast>.`
- Po uspesnem importu nabidnout uklid zdrojove kopie v inboxu:
  `Dokument <soubor> zpracovan, presunout do slozky processed? 1. presunout,
  2. smazat.`
- Pri volbe 1 pripravit vetu:
  `Potvrzuji, presunout dokument <soubor> do processed.`
- Pri volbe 2 se nejdriv samostatne zeptat:
  `Opravdu chcete dokument <soubor> smazat z inboxu?`
  Mazani provest az po druhem vyslovnem potvrzeni:
  `Ano, smazat dokument <soubor> z inboxu.`
- Bez potvrzeni nepresouvat ani nemazat. Nikdy nemazat nic mimo
  `data/private/documents/inbox/incoming/`.
- Tisk je samostatny dvoukrokovy workflow: nejdriv pripravit tiskovou kopii,
  potom tisknout az po potvrzeni. Automaticke mazani po tisku smi smazat pouze
  kopii v `data/private/documents/print_queue/` a jen po uspesnem predani tisku
  systemu.
- Intake ze slozky Stazene/Downloads musi byt dvoukrokovy: nejdrive read-only
  najit kandidaty a ukazat metadata, potom presunout do inboxu az po potvrzeni.
  Nikdy nebrat soubory ze Stazenych naslepo.

## Dalsi prakticky krok

MVP tooly jsou implementovane v `app/documents/` a napojene do Samanthy:

- `prepare_document_import`
- `inspect_document_text`
- `apply_document_import`
- `search_private_documents`
- `save_document_due_reminder`
- `propose_document_inbox_cleanup`
- `resolve_document_inbox_item`
- `document_vault_status`
- `prepare_document_print_job`
- `run_document_print_job`

Overit na prvnim realnem PDF:

1. dat soubor do `data/private/documents/inbox/incoming/` nebo dodat lokalni cestu,
2. spustit read-only `prepare_document_import`,
3. zkontrolovat navrzenou oblast, typ a due date kandidaty,
4. po potvrzeni spustit `apply_document_import`,
5. overit `search_private_documents`,
6. nabidnout `propose_document_inbox_cleanup` pro zdrojovou kopii v inboxu,
7. pokud Mila potvrdi presun, spustit `resolve_document_inbox_item` s akci
   `move`; pokud zvoli smazani, vyzadat druhe potvrzeni a az potom spustit
   `resolve_document_inbox_item` s akci `delete`,
8. pokud je due date spravne, samostatne potvrdit `save_document_due_reminder`.
9. pokud Mila chce dokument vytisknout, nejdriv pouzit
   `prepare_document_print_job`, potom tisknout az po samostatnem potvrzeni pres
   `run_document_print_job`.

Aktualni prakticky dalsi krok po realnem testu: pro uzamcene pojistovaci PDF
ziskat odemcenou kopii nebo heslo; pro neuzamcene skeny pouzit hotovy OCR backend.
