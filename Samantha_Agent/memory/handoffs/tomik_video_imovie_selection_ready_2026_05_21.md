Nazev: Tomik video iMovie - vybery pro iMovie hotove
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Po sitovem/reconnect problemu se pokracovalo v projektu rodinneho videa Tomik
  druhy rok.
- Navazovalo se na hotovy audit 217 videi, nahledy, popisy a chronologicky
  pojmenovanou sadu v soukrome slozce `data/private/tomik_rok_2/`.
- Cilem bylo vytvorit prakticke iMovie vybery bez mazani nebo prepisovani
  originalu.

Co je hotove:
- Pridan navazovatelny skript `scripts/tomik_video_select_imovie.py`.
- Skript prosel dry-runem a potom byl spusten naostro.
- Vytvorena kratka iMovie sada:
  `data/private/tomik_rok_2/05_imovie_vyber_short/`
  - 35 MP4 klipu
  - manifest `selection_manifest_short.csv`
  - surova delka vybranych klipu cca 15:12, cil strihu 3-5 minut
- Vytvorena rodinna iMovie sada:
  `data/private/tomik_rok_2/06_imovie_vyber_family/`
  - 82 MP4 klipu
  - manifest `selection_manifest_family.csv`
  - surova delka vybranych klipu cca 32:11, cil strihu 12-18 minut
- Vytvoreny storyboardy:
  - `data/private/tomik_rok_2/03_audit/storyboard_short.md`
  - `data/private/tomik_rok_2/03_audit/storyboard_family.md`
- Vybery jsou chronologicky cislovane prefixem, aby se v iMovie daly radit podle
  nazvu souboru.

Co neni hotove:
- Neni jeste rucne zkontrolovana kvalita vybranych klipu.
- Neni jeste import do iMovie.
- Neni jeste rozhodnuto, jestli se bude strihat primarne kratka verze, rodinna
  verze, nebo obe.
- Neni jeste finalni hudba, titulky ani export.

Dalsi krok:
- Otevrit `05_imovie_vyber_short/` ve Finderu a rychle projit 35 klipu.
- Pokud kratky vyber sedi, importovat jej do iMovie a seradit podle nazvu.
- Pri strihu pouzit storyboard `storyboard_short.md`: vetsinu klipu zkratit na
  5-10 sekund, delsi rodinne momenty nechat jen pokud maji hodnotu.
- Pokud bude short moc chudy, navazat rodinnou sadou `06_imovie_vyber_family/`.

Zmenene nebo relevantni soubory:
- `scripts/tomik_video_select_imovie.py`
- `data/private/tomik_rok_2/05_imovie_vyber_short/`
- `data/private/tomik_rok_2/06_imovie_vyber_family/`
- `data/private/tomik_rok_2/03_audit/storyboard_short.md`
- `data/private/tomik_rok_2/03_audit/storyboard_family.md`
- `data/private/tomik_rok_2/03_audit/video_audit_described.csv`
- `data/private/tomik_rok_2/04_chronologicky_pojmenovane/`

Bezpecnost / neukladat:
- Rodinna videa a detailni soukrome vystupy jsou v `data/private/`, ktera je
  ignorovana gitem.
- Nic z rodinnych videi necommitovat.
- Originaly nemazat ani neupravovat bez vyslovneho souhlasu.
