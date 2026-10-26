# Camino — odstranění P2-A a rychlejší procházení filmu

Stav: 2026-10-26 11:29 CET, výmaz P2-A dokončený; kód 11098612 místní, bez nového push/nasazení.
Pracovní proud: `project-camino`.

## Zadání a výsledek

Míla kladně hodnotí vzhled UI 2 („Vypadá to dobře, dobrá práce“), ale popisuje
načítání 1–2 minuty. Žádá odstranit dolní Testovací ukázku P2-A a její data.
Nový lokální frontend odstraňuje celý blok i jeho obsluhu a styl. Staré
`/local-apps/camino-p2a-review/…` vrací 404, i kdyby soubory stále existovaly.
Syntetické generátory a automatické regresní testy zůstávají pro další vývoj.

## Změřená příčina

Při každém obrázku se dvakrát kontroloval SHA-256 všech zdrojů celého projektu.
Miniatury navíc dostávaly stejný až 4096px PNG jako velká fotografie; v pracovní
ploše se vytvářel ještě skrytý duplicitní obrázek v panelu komentáře.

Měření stejného místního skutečného projektu: 45 záběrů, 29 fotografií,
48 zdrojů / 372 111 754 B. Čtena pouze technická metadata a nutné obrazové
podklady; soukromé texty ani obrázky nejsou v reportu. Originály, revize střihu
ani produkční render se neměnily.

| Operace | Před změnou | Po změně |
| --- | --- | --- |
| Stav editoru, 45 záběrů | 1,324 s, plné ověření | 0,039 s, již ověřené soubory |
| Kontrola vstupů | 1,308 s / 48 hashů / 372 MB | studená 1,241 s; opakovaná 0,068 s |
| Obrázek pro seznam | 5,287 s / 16 227 034 B | 0,192 s / 100 491 B |
| Obrázek pro hlavní náhled | původní stejný velký obrázek | 1,003 s / 3 471 580 B |

Původní požadavek na obrázek přečetl pro kontrolu ostatních zdrojů dohromady
744 223 508 B (96 hashů); nadto četl a ověřoval samotný originál fotografie.
Nové miniatury mají limit 256×256, hlavní náhled 1600×1600. PNG pro samostatné
otevření velké fotografie a filmové renderování si zachovávají původní postup.
Pro malé náhledy JPEG využívá menší dekódování a zmenšení před barevným převodem.

Jde o serverová/component měření, nikoli čas kompletní stránky přes Safari,
síť nebo iPhone. Zrychlení uživatelského načtení po nasazení dosud NEOVĚŘENO.
První kontrola po startu či expiraci nadále čte všechny zdrojové bajty.

## Zachované ochrany

- Pouze čtecí pohledy mohou použít omezené RAM ověření SHA-256: nejvýše
  1024 položek a 30 s od původní kontroly, bez prodlužování při použití.
- Pokaždé se znovu kontrolují aktuální metadata, soukromí, koš, příjem médií
  a manifest. U hashů musí souhlasit device/inode/size/mtime_ns/ctime_ns;
  symlink a změna během čtení se odmítnou.
- Zobrazený originál se vždy znovu celý přečte a ověří jeho SHA-256.
  Po dekódování se znovu kontroluje aktuální projekt/soukromí.
- Zavření vstupů, uložení střihu, render i výstup používají nadále úplné
  ověření zdrojových bajtů. Výchozí validace zůstává přísná.
- Obrázky nemají EXIF/GPS, HTTP zůstává no-store/private; žádné diskové
  kopie náhledů ani nová veřejná cesta. Ověření oprávnění se necachuje.

## Výmaz P2-A dokončený

Jediný kořen: `data/private/camino/p2a`, čtyři syntetické běhy:

| Běh | Souborů | Bajtů |
| --- | ---: | ---: |
| run-112rz9am | 27 | 17 080 578 |
| run-900plgpz | 27 | 19 284 351 |
| run-m4u5v6jh | 27 | 19 460 604 |
| run-xip7fnef | 28 | 16 570 641 |
| Celkem | 109 | 72 396 174 (69,04 MiB) |

Všechny čtyři experimenty a projekty jsou synthetic-p2a, zdroje synthetic=true;
validace projektů a hashů prošla. Bez symlinků a bez skutečných médií cest.
Přesný soukromý inventář včetně hashů a identity souborů je v ignorovaném
`data/private/cleanup_receipts/camino_p2a_20261026/plan.json`, režim 0600,
nadřazený adresář 0700. Původní plán zůstává nezměněný ve stavu před potvrzením;
aktuální výsledek drží soukromá `receipt.json` vedle plánu.
Otisk plánu: `b0bcf0c26c660467b7dbe3aabbd07a4262b37507d3a8359d93ea1e80b5859034`.

2026-10-26 11:29 CET: Míla dodal přesnou globální větu pro tento rozsah. Před výmazem
znovu ověřený otisk plánu, všechny názvy/metadata/identity a SHA-256, bez
symlinků a bez odkazů mimo plán. Před každým unlink další ověření souboru,
výmaz přes otevřené adresáře, průběžná soukromá účtenka. Odstraněno všech
109 souborů a 16 adresářů; kořen zůstal prázdný. Receipt state=completed,
remaining_entries=0; nezávislá závěrečná kontrola PASS. Účtenka má režim 0600.

Součet velikostí 72 396 174 B (69,04 MiB) zahrnoval interní hardlinky.
101 unikátních inode mělo před výmazem 43 364 352 B (41,36 MiB) alokovaných
bloků. Čistá změna volných bloků celého SSD se neměřila. Skutečné projekty,
originály a historické zálohy nebyly součástí výmazu.

## Ověření

- 45 cílených Python/HTTP/frontend/server kontrol PASS / 13,848 s; Node scénáře
  editoru a komentářů PASS. Dalších 6 kontrol nových GET/HEAD cest a jejich
  statické evidence PASS / 3,302 s.
- První plná brána: 2243 testů, jediné selhání evidence frontendových cest.
  AST kontrola nerozpoznala tuple ve startswith. Nové GET/HEAD větve jsou nyní
  explicitní, s pevným druhem náhledu; kontraktní test se neoslaboval.
- Finální kanonická plná brána PASS: 2243 testů / 458,763 s unit část; statické a Node kontroly PASS.
- Fyzický Safari/iPhone a celkový čas stránky po nasazení NEOVĚŘENO.

## Další krok

Výmaz dat je dokončený a ověřený. Nový lokální kód ještě vyžaduje
samostatně zadané p+n přes registrovanou Lunu;
poté přejímku stejného filmu na Macu a případně iPhonu. Zachovat otevřené
praktické nahrávky/import a výběr příjemnějšího českého hlasu.
