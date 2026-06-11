# Cockpit UI content audit

Datum: 2026-06-11
Rozsah: read-only audit hlavni obrazovky Cockpitu, modalu a samostatnych oken podle `app/cockpit.py` a ziveho lokalniho API.

## Kratke shrnuti

Cockpit uz ma spravne jadro: `Dnes`, `Stav`, `Co ted delat`, dokumenty, vyhledani dokumentu, Knihovna, Janička, Reminders a Recovery. Problem neni chybejici funkce, ale hlasitost vseho najednou. Na hlavni obrazovce jsou vedle denni prace viditelne i servisni veci jako Git, frontend health, endpoint diagnostika, kvantitativni status, terminal, restart a raw souhrny.

Doporuceny smer: hlavni obrazovka ma byt ranni/denni rozhodovaci panel. Technicky provoz presunout do `Servis / Diagnostika`, historicke a sirsi prehledy do `Archiv / Projekty`.

## Co je opravdu denni

- `Dnes`: nova PDF, dokumenty k revizi, problemy.
- `Co ted delat`: ranni prioritni fronta; ma byt hlavni odpoved na otazku "co mam ted resit".
- `Dulezita pripomenuti`: pokud existuji, patri nahoru jako alert.
- `Najit dokument`: denni prakticka akce, hlavne pro Milu i Janu.
- `Knihovna`: denni/obcas podle aktualni prace; z hlavni listy ano, ale ne jako velky blok na hlavni strance.
- `Janička`: denni prakticky vstup pro Janu; ma zustat netechnicky.
- `Hlasovy pokyn`: denni jen pokud je zapnuty hlasovy rezim; jinak schovat do maleho stavu + tlacitko `Otevrit hlas`.

## Obcas

- `Prace s dokumenty`: dobry detail, ale na hlavni obrazovce je prilis rozsahla. Nechat jen souhrn a akce; detail pres modal nebo samostatnou obrazovku `Dokumenty`.
- `Email Processing`: obcasny pracovni rezim, ne denni status v hlavni liste pro Janu.
- `Webove aplikace`: rozcestnik, staci v liste nebo pod `Vice`.
- `Projekty a schopnosti`: obcasny planning/status, ne denni start.
- `QN prehled`: obcasny inbox, pokud nema aktivni polozky, nema byt hlasity.
- `Kvantitativni status`: obcasny audit rustu systemu, ne denni karta.
- `Consistency Audit`: obcasny/servisni audit; na hlavni obrazovce jen signal, detail pod diagnostikou nebo dokumenty.

## Servis / diagnostika

Schovat pod jedno tlacitko `Servis` nebo `Diagnostika`:

- `Frontend`, `Tlacitka`, `API`, `Posledni chyba`.
- `Diagnostika` endpointu.
- `Recovery centrum`.
- `Git` detail.
- `Restart Cockpitu`.
- `Terminal v projektu`.
- `Kvantitativni status`.
- `Consistency Audit` detail, pokud nejde o konkretni rozhodnuti pro uzivatele.
- Detail `Voice bridge cil`, TTY, screen, Codex relace.

Na hlavni obrazovce ma zustat jen lidska veta typu: `Samantha je vzhuru; zkontrolovat: zaloha.`

## Archiv

- Archivovane projekty.
- Historicke handoffy.
- Raw autosave metadata.
- Stare aplikace/prototypy, ktere nejsou aktualni denni prace.
- Dlouhe systemove reporty.

## Duplicity

1. Dokumenty jsou zobrazeny v mnoha vrstvach najednou:
   - `Dnes`
   - `Co ted delat`
   - `Prace s dokumenty`
   - `PDF ve Downloads za 7 dni`
   - `Souhrn vaultu`
   - `Consistency Audit`

   Navrh: hlavni obrazovka ukaze jen souhrn + top akci. Detail sloucit do jedne obrazovky `Dokumenty`, kde budou tabs: `Vstupy`, `K revizi`, `Hledat`, `Cases`, `Terminy`, `Klasifikace`.

2. Stav systemu je zobrazen duplicitne:
   - karta `Stav`
   - frontend health panel
   - diagnosticky modal
   - recovery modal
   - casti `Git`, `Zaloha`, `ScanDocu`

   Navrh: hlavni `Stav` ma byt lidsky semafor. Technicke rozklady presunout do `Diagnostika`.

3. Hlas/Adam ma dve ruzne tvare:
   - hlavni panel `Hlasovy pokyn`
   - `Janička -> Zeptat se Adama`

   Navrh: pro Milu ponechat `Hlasovy pokyn`, pro Janu ponechat `Zeptat se Adama`. Technicke bridge detaily schovat.

## Moc technicke nazvy

Prejmenovat nebo schovat:

- `Email Processing` -> `E-maily`
- `Reminders` -> `Pripomenuti`
- `QN prehled` -> `Rychle poznamky`
- `Kvantitativni status` -> `Systemovy souhrn` nebo schovat do servisu
- `Consistency Audit` -> `Kontrola nesrovnalosti`
- `Frontend / Tlacitka / API` -> jen v diagnostice
- `Voice bridge cil`, `TTY`, `screen`, `Codex relace` -> jen v diagnostice hlasu
- `Vazby / cases` -> `Souvisejici dokumenty`
- `Slaba metadata` -> `Doplnit udaje`

## Dokumentovy vault: lidske stavy

Existujici stavove nazvy jsou dobre zaklady:

- `OK` -> `V poradku`
- `k revizi` -> `Zkontrolovat`
- `necitelne` -> `Necitelne`
- `nahrazeno lepsi kopii` -> `Nahrazeno`

Pro Janu a denni UI doporucuji zobrazovat lidske labely:

- `V poradku`
- `Zkontrolovat`
- `Necitelne`
- `Nahrazeno lepsi kopii`
- `Doplnit udaje`
- `Ceka na OCR`

Technicke interni hodnoty (`ok`, `needs_review`, `unreadable`, `superseded`, `weak_metadata`, `zero_text`) neukazovat v hlavnim UI.

## Action queue rano

Poradi karet pro ranni Cockpit:

1. Dulezita pripomenuti z mobilu nebo rucniho vstupu.
2. Platebni konflikty a rizikove pripominky.
3. Dokumentove problemy.
4. Nova PDF / nove dokumentove vstupy.
5. Dokumenty k revizi.
6. Dnesni a brzké pripominky.
7. Zaloha, pokud je starsi nez limit.
8. Projekty jen pokud maji explicitni `ceká na me`, `blokovano` nebo `[PRIPOMENOUT]`.

Aktualni zivy stav pri auditu:

- Dokumenty: 0 novych PDF, 0 problemu, 0 dokumentu k revizi.
- Action queue: 1 polozka priority 1.
- Zaloha: posledni uspesna 2026-06-07, stara 4 dny, ma byt viditelna.
- Git: cisty.
- ScanDocu: bezi.
- Dokumentovy review report: 22 aktivnich dokumentu OK, 1 dokument potrebuje doplnit udaje.

## Navrh prvniho UI cleanupu

Minimalni dalsi implementacni krok:

1. Na hlavni obrazovce nechat jen:
   - `Dnes`
   - lidsky `Stav`
   - `Co ted delat`
   - `Najit dokument`
   - maly radek `Zaloha / Git / Adam` jen jako semafor
2. Presunout do modalu `Dokumenty`:
   - `Prace s dokumenty`
   - `PDF ve Downloads za 7 dni`
   - `Souhrn vaultu`
   - `Dokumenty k revizi`
   - `Cases`, `Klasifikace`, `Terminy`
3. Presunout do `Servis`:
   - health panel
   - diagnostika
   - recovery
   - terminal
   - restart
   - kvantitativni status
   - raw audit
4. Prejmenovat hlavni tlacitka do cestiny:
   - `Reminders` -> `Pripomenuti`
   - `Email Processing` -> `E-maily`
   - `Revidovat ulozene` -> `Revidovat dokumenty`
5. Technicke detaily hlasu ukazovat jen po rozbaleni `Pokrocile`.

Tento uklid by nemel menit backend ani workflow. Jde hlavne o preskupeni stavajicich prvku a prejmenovani viditelnych labelu.
