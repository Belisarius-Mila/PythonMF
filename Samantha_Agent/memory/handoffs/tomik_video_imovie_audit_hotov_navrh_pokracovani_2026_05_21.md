Nazev: Tomik video iMovie - audit hotov a navrh pokracovani
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Mila chce pripravit rodinny iMovie film z malych videi od dcery, tema vnuk
  Tomik druhy rok.
- Vstupni slozka z Uschovny byla nalezena jako `~/Downloads/Rok 2`.
- Kvuli opakovanym reconnectum bylo zavedeno pravidlo: dlouhe ukoly poustet jako
  navazovatelne skripty s logem/stavem, ne jako dlouhe interaktivni cekani v chatu.

Co je hotove:
- Videa jsou zkopirovana do soukrome ignorovane slozky:
  `data/private/tomik_rok_2/`.
- `data/private/` je v `.gitignore`, rodinna media nesmi do gitu.
- V `01_originaly/` je 217 videi, cca 3,82 GB, celkova delka cca 81 minut.
- V `02_nahledy/` je 651 JPG nahledu, tri ke kazdemu videu.
- V `02_nahledy/contact_sheets/` je 19 kontaktnich listu.
- V `03_audit/` vznikly:
  - `video_audit.csv`
  - `video_audit_described.csv`
  - `video_rename_mapping.csv`
  - `chronologicky_katalog.md`
- V `04_chronologicky_pojmenovane/` je 217 chronologicky serazenych a pracovnimi
  nazvy pojmenovanych videi.
- Pomocne skripty:
  - `scripts/tomik_video_audit.py`
  - `scripts/tomik_video_finalize.py`

Co neni hotove:
- Neni jeste vytvoren vyber pro iMovie.
- Neni jeste storyboard pro kratkou ani rodinnou variantu.
- Neni jeste vybrano, zda finalni cil bude kratky 3-5 minutovy sestřih, delsi
  rodinny film, nebo chronologicky archiv.

Dalsi krok po restartu:
- Nepoustet dlouhy interaktivni tool call.
- Vytvorit navazovatelny skript pro vyber videi do:
  - `data/private/tomik_rok_2/05_imovie_vyber_short/`
  - `data/private/tomik_rok_2/06_imovie_vyber_family/`
- Skript ma pouzit hardlinky/kopie bez mazani originalu.
- Vytvorit storyboardy:
  - `data/private/tomik_rok_2/03_audit/storyboard_short.md`
  - `data/private/tomik_rok_2/03_audit/storyboard_family.md`
- Navrzeny postup vyberu:
  - `short`: cca 25-35 reprezentativnich klipu, 4-6 minut.
  - `family`: cca 60-90 klipu, 12-18 minut.
  - Preferovat rozmanitost a kapitoly: jaro 2025, rodina/oslavy, leto/zahrada,
    cestovani/moře, podzim, Vanoce/zima, jaro 2026, zaver.
  - Slabsi, tmave, duplicitni nebo nejasne klipy ponechat v archivu, automaticky
    je nedavat do hlavniho filmu.

Zmenene nebo relevantni soubory:
- `data/private/tomik_rok_2/` - soukrome lokalni vystupy, necommitovat.
- `scripts/tomik_video_audit.py`
- `scripts/tomik_video_finalize.py`
- `memory/projects/tomik_video_imovie.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/technical/session_recovery_rules.md`
- `memory/infrastructure/codex_reconnect_recovery.md`
- `NETWORK_RECOVERY_CARD.txt`
- `../Samantha_NETWORK_RECOVERY_CARD.txt`

Bezpecnost / neukladat:
- Rodinna videa, detailni soukrome popisy, exporty a media neukladat do gitu ani
  dlouhodobe memory.
- Nemazat zadna videa bez vyslovneho souhlasu.
- Pri reconnectu Mila muze v normalnim Terminalu spustit:
  `source ~/.zshrc`
  `SAMANTHA_DISABLE_VPN=1 samantha`
