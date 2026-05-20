# Lekarna PIL_Short workflow

Datum zalozeni: 2026-05-20

## Cil

Doplnovat do `data/lekarna/domaci_leky.csv` kratke, prakticke vytahy z pribalovych
informaci bez toho, aby se z domaci evidence stalo lekarske doporuceni.

Vystupem jsou sloupce:

- `PIL_Short`
- `PIL_Source`
- `PIL_Checked_Date`
- `PIL_Match_Status`

`data/lekarna/` je soukroma a ignorovana v gitu. Do gitu patri workflow, testy a
schema, ne plny osobni inventar leku.

## Zdrojovy postup

1. Vzit aktualni `data/lekarna/domaci_leky.csv`.
2. Stahnout maly SÚKL DLP export z `https://opendata.sukl.cz/`:
   - katalog: `Databaze lecivych pripravku DLP`,
   - soubor napr. `DLP20260427.zip`.
3. Z DLP ZIP cist hlavne:
   - `dlp_lecivepripravky.csv` - kody, nazvy, sila, forma, baleni, stav,
   - `dlp_nazvydokumentu.csv` - mapovani `KOD_SUKL` na `PIL` a datum PIL.
4. Nevyzadovat automaticky stazeni celeho mesicniho PIL ZIP archivu, protoze je
   velky radove GB. Staci DLP pro sparovani a konkretni verejne PIL/PDF odkazy,
   pokud jsou potreba pro text.
5. Pro kazdou polozku sparovat:
   - presny nazev,
   - ucinnou latku,
   - silu,
   - formu,
   - pripadne baleni.
6. Pokud je nazev nejisty nebo varianta neni jasna, nepovysovat polozku na
   overenou. Pouzit status nejistoty.

## Statusy

Doporucene hodnoty `PIL_Match_Status`:

- `overeno_sukl_dlp_pil` - presne nebo dostatecne jasne sparovano se SÚKL DLP a PIL.
- `overeno_sukl_dlp_ema_pil` - centralizovana registrace; SÚKL odkazuje na EMA PIL.
- `pravdepodobne_sparovano_sukl_pil` - velmi pravdepodobne sparovani, ale domaci
  nazev neni uplny nebo presny.
- `nejista_varianta_sukl` - existuje vice variant a evidence neobsahuje dost detailu.
- `nejisty_nazev_pravdepodobne_sukl` - domaci zapis je nejspis preklep nebo zkraceni.
- `nejisty_nazev` - nelze bezpecne urcit pripravek.
- `nenalezeno_sukl_overit_obal` - pripravek/sila nebyl nalezen v DLP; overit obal.
- `neni_lek_nebo_bez_sukl_pil` - doplnek, zdravotnicky prostredek nebo podobna polozka.
- `neni_lek` - zjevne neni lek.

## Jak psat PIL_Short

Text ma byt kratky, vecny a prakticky:

- na co lek obecne je,
- jak se obecne pouziva bez detailniho davkovani,
- hlavni kontraindikace,
- prakticka rizika a situace pro lekare/lekarnika.

Pravidla stylu:

- Neuvazet konkretni davkovaci schema, pokud neni opravdu potreba pro orientaci.
- Psat "podle PIL/lekare/lekarnika" tam, kde jde o leky na predpis nebo nejistou variantu.
- Nezvyraznovat raritni katastroficke nezadouci ucinky, pokud nejsou pro bezne
  rozhodovani zasadni.
- U antibiotik, opioidu, antidepresiv, kardiologickych leku a jinych osobnich leku
  zduraznit "pouze podle lekare / pro konkretni osobu".
- U deti, tehotenstvi, kojeni, alergii, chronickych nemoci, kombinaci leku a silnych
  nebo dlouhych potizi smerovat na lekare/lekarnika.
- U nejisteho nazvu radeji napsat, ze je nutne fyzicke overeni obalu, nez vyrabet
  falesne jistou informaci.

## Bezpecny zapis do CSV

Pred kazdym zapisem:

1. Udelat zalohu `domaci_leky.backup_before_pil_short_*.csv`.
2. Zkontrolovat, ze pocet radku zustal stejny.
3. Zkontrolovat pocty statusu a vytvorit report `pil_short_report_*.md`.
4. Spustit testy:
   - `.venv/bin/python -m unittest tests.test_lekarna_service`

## Stav k 2026-05-20

Byly doplneny `PIL_Short` nebo vysvetlujici status pro vsech 56 radku evidence.

Souhrn statusu:

- `overeno_sukl_dlp_pil`: 26
- `overeno_sukl_dlp_ema_pil`: 1
- `pravdepodobne_sparovano_sukl_pil`: 1
- `nejista_varianta_sukl`: 4
- `nejisty_nazev_pravdepodobne_sukl`: 3
- `nejisty_nazev`: 4
- `nenalezeno_sukl_overit_obal`: 7
- `neni_lek_nebo_bez_sukl_pil`: 8
- `neni_lek`: 2

Vytvorena lokalni soukroma zaloha:

- `data/lekarna/domaci_leky.backup_before_pil_short_all_20260520_152331.csv`

Vytvoren lokalni report:

- `data/lekarna/pil_short_report_20260520_152331.md`
