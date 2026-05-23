Nazev: Seznam e-mail - pojisteni, smlouvy a prilohy
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Mila potrebuje rychle projit stary Seznam ucet za cca 15 let a najit e-maily k pojisteni, pripojisteni, smlouvam a souvisejicim dokumentum.
- Cilem je prakticky lokalni archiv/pracovni katalog pojistnych dokumentu, hlavne smlouvy, zelene karty, danova potvrzeni a relevantni prilohy.

Co je hotove:
- Vznikl skript `scripts/seznam_email_search.py` pro Seznam IMAP:
  - hledani pres IMAP,
  - vystup do CSV/Markdown,
  - samostatne stahovani priloh podle `folder` a `uid`.
- Prvni hledani v INBOXu za 2011-2026 naslo `INBOX: 1998 kandidatu`, ale ulozilo vychozich 500 vysledku.
- Vystupy hledani jsou lokalne v:
  - `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.csv`
  - `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.md`
- Vznikl prioritizacni/worklist vystup:
  - `data/private/email_seznam/seznam_email_worklist_500.md`
  - `data/private/email_seznam/next_attachment_download_commands.txt`
- Byly stazeny prilohy z puvodnich 4 RIXO/CPP UID a nasledne dalsich 30 doporucenych UID.
- Aktualni lokalni stav priloh:
  - 34 UID slozek v `data/private/email_seznam/attachments/INBOX/`
  - 129 souboru priloh mimo manifesty
  - cca 50 MB dat
- Vznikl katalog stazenych priloh:
  - `scripts/seznam_email_attachment_catalog.py`
  - `data/private/email_seznam/insurance_attachment_catalog.csv`
  - `data/private/email_seznam/insurance_attachment_catalog.md`
- Katalog klasifikuje podle metadat a nazvu priloh bez otevirani PDF:
  - 31 dulezitych dokumentu
  - 52 uzitecnych doplnku
  - 46 balast / obecne prilohy

Co mame v prilohach:
- RIXO/CPP auto smlouvy 2025 a 2026:
  - UID `143496`, `143498`, `154544`, `154546`
- Kooperativa auto smlouvy/nabidky/zelene karty/upominky:
  - napr. UID `134162`, `134158`, `153554`, `147630`, `145618`, `134468`, `134470`
- MetLife danova potvrzeni a zivotni/urazove dokumenty:
  - napr. UID `111208`, `111212`, `122512`, `122514`, `136610`, `136680`, `137596`
- Cestovni pojisteni AXA / Top-pojisteni:
  - UID `110188`
- KB / sluzba Bezpeci a bankovni dokumenty:
  - UID `140516`, `140514`

Co neni hotove:
- Neni jeste otevreny/zkontrolovany obsah PDF; zatim se pracovalo s nazvy priloh, UID a metadaty.
- Nebyl jeste spusten uspesny rozsirený beh s `--limit 2500`; predchozi pokusy se zalomily v shellu a zustalo u 500 vysledku.
- Neni jeste dohodnuto, ktere dokumenty jsou finalni "dulezite" a ktere jsou jen podminky/marketing/balast.

Dalsi krok:
- Otevrit `data/private/email_seznam/insurance_attachment_catalog.md` a projit sekci `Dulezite dokumenty`.
- Z katalogu vybrat finalni dokumenty k praktickemu archivovani:
  - smlouvy,
  - zelene karty,
  - navrhy smluv,
  - danova potvrzeni,
  - MetLife ukonceni / zivotni a urazove dokumenty.
- Pokud bude potreba opravdu celych 15 let, spustit jednoradkovy prikaz:

```bash
.venv/bin/python scripts/seznam_email_search.py search --since-year 2011 --before-year 2027 --folders all --limit 2500
```

Zmenene nebo relevantni soubory:
- `scripts/seznam_email_search.py`
- `scripts/seznam_email_prioritize_results.py`
- `scripts/seznam_email_worklist.py`
- `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.csv`
- `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.md`
- `data/private/email_seznam/seznam_email_worklist_500.md`
- `data/private/email_seznam/next_attachment_download_commands.txt`
- `data/private/email_seznam/attachments/INBOX/`
- `data/private/email_seznam/insurance_attachment_catalog.csv`
- `data/private/email_seznam/insurance_attachment_catalog.md`

Bezpecnost / neukladat:
- Do memory ani gitu neukladat heslo k Seznamu, app-specific password, tokeny ani plne obsahy e-mailu.
- `data/private/email_seznam/` je lokalni privatni pracovni slozka a necommitovat.
- Pri sumarizaci do memory pouzivat jen metadata a stav prace, ne opisovat obsah osobnich dokumentu.
