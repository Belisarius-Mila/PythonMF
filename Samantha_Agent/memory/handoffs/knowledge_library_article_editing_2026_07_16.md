<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-12 22:44 CEST; pracovní proud `project-knowledge-library`.

### Hotovo
- Vývoj je pushnutý a nasazený: funkční commit `2f5cf1f9`, plná brána 1622 testů a smoke 5/5 prošly; Knihovna je připojená, oba profily čisté a zarovnané.
- Nové ilustrace mají společný rozpočet 305 KiB: hlavní JPEG nejvýše 285 KiB a náhled nejvýše 20 KiB. Původní/readable varianta odkazují na tentýž soubor; tři fotografie mají nejvýše 0,894 MiB.
- Limit vynucuje browser i backend, podporované jsou i starší camera JPEG/MPO. Text a fotografie se dál ukládají nezávisle na pozadí, retry zachovává identitu přílohy.
- Dočasné OCR/ISBN/rozpoznávání obálky používá oddělenou přípravu do 1 MiB / 2400 px. Ukládané ilustrace používají nejvýše 1600 px.
- Registrovaný převod existujících příloh má oddělenou přípravu, potvrzené použití a ověřenou obnovu. Nemění text článku, PDF, identifikátory, popisky ani poznámky.

### Rozhodnutí
- Míla schválil nový rozpočet i c+p+n. U ilustrací se neuchovává druhá velká obrazová kopie.
- Míla potvrdil přesnou větu globální brzdy pro připravených 22 obrázků; registrovaný převod byl proveden a ověřen.
- Jednorázová ověřená záloha starých příloh a metadat zůstává mimo aktivní archiv. Míla výslovně nařídil její pozdější smazání; pokyn platí pouze pro backup tohoto převodu, po uživatelské kontrole výsledku. Není to souhlas k mazání jiných záloh a není zaveden časovaný úklid.

### Otevřeno a rizika
- Převod 22 obrázků v 11 kartách je dokončený: 66 původních souborů → 44 kompaktních, 59,117 → 5,962 MiB. Ověřená záloha 59,350 MiB je zachovaná do pozdějšího odstranění; její prostor zatím není uvolněný.
- Případná obnova ze zálohy nesmí přepsat další uživatelskou práci; používá ověřené otisky a potvrzovanou registrovanou operaci.
- Rozpracovaný přenos nadále vyžaduje otevřenou stránku. Skutečné Safari na iPhonu má být ověřeno při běžném použití.

### Další krok
- Míla při běžném použití zkontroluje zmenšené obrázky; potom provést už nařízené odstranění konkrétní jednorázové zálohy a doložit výsledek.

### Navrhované další kroky
- Automatický úklid nezavádět; žádný další vývoj není pro tento převod potřeba.

### Technický důkaz
- Reálný převod: 61 988 739 → 6 251 688 B; největší fotografie s náhledem 310 875 B, všechny v limitu 305 KiB. 299 ostatních souborů beze změny podle SHA-256; mimo plánovaná obrazová pole nezměněná metadata a registr 121/121 konzistentní. Všech 44 JPEGů dekódováno, bez EXIF a v rozměrových limitech; záloha 62 233 053 B ověřena po souborech. Soukromý doklad `post_apply_verification.json` je u plánu odkazovaného přes `latest_prepared.json`.
- Nasazení funkční změny ověřeno 2026-09-12 22:33 CEST; code stamp `f57dfb8454ac938f`, smoke 5/5, přesná serverová stránka/worker a HTTP příprava obou rozpočtů. Navazující commit pouze uchovává tento doklad.
- 388 cílených testů prošlo; po doplnění konzistence registru a HTTP účelu přípravy prošlo dalších 26 testů. Plná Cockpit brána prošla: 1622 testů bez chyb, unit testy 491,112 s; syntaxe a whitespace OK.
- Browser na syntetickém archivu: PNG 12 980 174 B, HEIC, dvě karty, retry po ztrátě odpovědi, editor, kniha s obálkou; vše OK, 0 JS chyb. Uložení textu při pozastavené přípravě 0,153 s; každý skutečně uložený snímek má jen dva soubory a nejvýše 305 KiB.
- Oddělené rozpočty v browseru: stejný zkušební snímek ilustrace 279 826 B / rozpoznávání 994 293 B; bez spuštění AI.
- Všech 22 připravených JPEGů i náhledů prošlo dekódováním, rozměrovým/velikostním limitem a kontrolou odstranění EXIF. Vizuálně ověřeny tři receptové přílohy (včetně čitelnosti textu), vybraná obálka a největší cestovatelský snímek.
- Soukromý plán a vizuální doklad: `data/private/library_photo_compaction/latest_prepared.json`; integrační browserové důkazy: `data/private/library_compact_20260912/`.
<!-- SAMANTHA_CURRENT_STATUS_END -->

Nazev: Knihovna v Cockpitu – editace článku a příloh
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-16

Co se resilo:
- Human–Adam doplnil přímou editaci existující znalostní karty v Cockpitu.
- Součástí stejného celku je úprava popisku a poznámky přílohy a bezpečné
  odebrání přílohy do soukromého koše.
- Kanonický commit je `2597e14` (`Knihovna - editace`) z 2026-07-16.

Co je hotove:
- Editor načte celý text vybrané karty a umožní změnit název, text, kategorii,
  tagy, označení zdroje a poznámku ke zdroji.
- Uložení aktualizuje text, metadata i registr; při chybě vrací původní stav.
- Existující přílohy zůstanou při editaci článku zachované a obrazová karta si
  zachová technický tag `ma-obrazek`.
- U přílohy lze změnit pouze popisek a poznámku, bez přepisu obrazových souborů.
- Odebrání přílohy vyžaduje přesnou potvrzovací větu, přesune její soubory do
  soukromého koše s manifestem a upraví metadata i registr.
- Přílohy mimo recepty používají obecný popisek a tagy; nedostávají automaticky
  receptové nebo rukopisné značky.
- Změna je v `app/article_archive.py`, `app/cockpit.py`,
  `test_article_archive.py` a `test_cockpit.py`.

Co neni hotove:
- Terminálový Adam samostatně neopakoval ruční editaci skutečného soukromého
  článku v UI; soukromý obsah nebyl kvůli handoffu čten ani vypisován.
- Obnova jednotlivé přílohy přímo z koše nemá samostatné tlačítko v Cockpitu;
  odebrání je vratné technicky uloženými soubory a manifestem.

Dalsi krok:
- Bez okamžité vývojové akce. Při příští běžné editaci zkontrolovat, že se po
  uložení znovu otevře stejná karta se zachovanými přílohami.

Navrhovane dalsi kroky:
- Na necitlivé nebo testovací kartě lze samostatně ověřit změnu popisku přílohy
  a potvrzované odebrání do koše.
- Samostatné uživatelské obnovení přílohy z koše řešit pouze podle reálné potřeby.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `memory/projects/vedecke_clanky.md`

Overeni:
- Commit `2597e14` mění pouze čtyři kódové a testovací soubory; soukromý archiv
  článků není součástí commitu.
- Dne 2026-07-16 terminálově znovu prošlo 6 cílených regresních testů, Python
  kompilace obou aplikačních modulů a `git diff --check`.

Infrastrukturni registrace 2026-07-20:
- Knihovna je ve fazi 1.3 transformace Human–Adam zkušebne zaregistrovana jako
  `Project` `project-knowledge-library`.
- Vazba pouziva stavajici oddelene vlakno Knihovny, `knihovna_cockpit.txt`, tento
  handoff a existujici izolovany workspace; zadny soukromy identifikator vlakna
  se do Gitu neuklada.
- Neveřejny koordinator umi prechod Human–Adam -> Knihovna -> Human–Adam a pri
  aktivaci automaticky fast-forwarduje cisty cil z commitnuteho lokalniho
  `main`. API ani UI zatim nejsou prepnute.
- Cilena sada 38 testu, plna sada 870 testu a zivy Cockpit smoke 5/5 prosly.
- Faze 1.4 dne 2026-07-20 zachovala stejny vyber a jeho vzhled, ale zdroj polozek
  prepojila na koordinator. Knihovna se nyni v payloadu voli kanonickym ID
  `project-knowledge-library`; puvodni profilove ID zustava vratnym fallbackem.
- Automatizovana sada 93 cilenych a 871 plnych testu prosla. Zmena jeste neni
  nasazena ani rucne prokliknuta v zivem Cockpitu.
- Commit `6f17852` byl nasazen a Cockpit rizene restartovan na code stamp
  `7a4440b979d98690`. Zivy endpointovy prechod Human–Adam -> Knihovna ->
  Human–Adam prosel a oba workspaces skoncily ciste a zarovnane.
- Vizualni kliknuti pres menu zatim chybi pouze proto, ze vestaveny prohlizec
  nebyl v terminalove relaci dostupny; soukromy obsah Knihovny se necetl.

Bezpecnost / neukladat:
- Do Gitu ani handoffu nepatří texty soukromých článků, přílohy, metadata
  konkrétních osob ani obsah soukromého koše.
- Při odebrání přílohy neobcházet přesnou potvrzovací bránu a nikdy nemaž soubory
  archivu ručně bez samostatného potvrzení.

### 2026-07-20 11:01 CEST – Živý zapisovací test fáze 1.6

- Knihovna ověřila automatické dokončení jednoho zapisovacího tahu přímo do
  `main`.

### Automatický checkpoint 2026-07-20 11:06 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Živý zapisovací test Knihovny fáze 1.6 prošel
- Ověření: plná Cockpit brána: 880 testů, 265.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (1): `Samantha_Agent/memory/handoffs/knowledge_library_article_editing_2026_07_16.md`
- Commit: `Verify Knihovna automatic completion live`
- Další krok: Ověřit čistý main, synchronizaci obou profilů a uvolnit přechodný semafor.

### Automatický checkpoint 2026-07-23 10:57 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Import URL nyní respektuje HTTP charset včetně ISO-8859-2
- Ověření: plná Cockpit brána: 1123 testů, 216.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`
- Commit: `Fix URL article HTTP charset decoding`
- Další krok: Nasadit opravu a samostatně obnovit dnešní kartu z uloženého source.html.

### Automatický checkpoint 2026-07-23 13:12 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Read-only náhled nové extrakce ISO-8859-2 je připraven bez změny karty
- Ověření: plná Cockpit brána: 1132 testů, 234.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add read-only article re-extraction preview`
- Další krok: Nasadit změnu a spustit náhled nad dnešní kartou; samotnou opravu potvrdit samostatně.

### Automatický checkpoint 2026-07-23 22:11 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Import URL bezpečně rozbaluje gzip před dekódováním a regresní testy prošly
- Ověření: plná Cockpit brána: 1159 testů, 230.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`
- Commit: `Handle gzip-compressed article responses`
- Další krok: Nasadit změnu a samostatným výslovným pokynem opravit dnešní kartu z uloženého zdroje.

### Automatický checkpoint 2026-08-01 15:49 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Obrázky se otevírají v Knihovně s jasným tlačítkem pro návrat
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 9.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add in-app library attachment viewer`
- Další krok: Převzít a nasadit změnu, potom ověřit návrat z obrázku na iPhonu

### Automatický checkpoint 2026-08-01 16:50 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Zdravotní informace jsou znovu samostatnou kategorií Knihovny; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (10): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/scripts/archive_article_url.py`, `Samantha_Agent/scripts/archive_text_entry.py`, `Samantha_Agent/scripts/clean_article_archive_texts.py`, `Samantha_Agent/scripts/search_article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Restore health information library category`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit záložku Zdravotní informace

### Automatický checkpoint 2026-08-01 17:48 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: PDF export Knihovny nyní obsahuje čitelné obrazové přílohy na samostatných stránkách; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`
- Commit: `Embed library images in PDF exports`
- Další krok: Převzít a nasadit změnu, potom připravit PDF jedné karty s obrázkem a vizuálně je ověřit bez odeslání

### Automatický checkpoint 2026-08-02 19:07 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihovna i Human–Adam nyní rozpoznají jeden společný stav záloh bez lokálních kopií; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1272 testů, 293.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/backup/__init__.py`, `Samantha_Agent/app/backup/activity_state.py`, `Samantha_Agent/memory/LESSONS_LEARNED.md`, `Samantha_Agent/tests/test_backup_activity_state.py`
- Commit: `Share backup activity state across workspaces`
- Další krok: Převzít a nasadit změnu, potom ověřit stav zálohy v Knihovně i Human–Adamovi

### Automatický checkpoint 2026-08-02 19:39 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihovna má novou kategorii Knihy s autorem, umístěním, stručným obsahem, formulářem a vyhledáváním; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1273 testů, 294.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add structured books to Knowledge Library`
- Další krok: Převzít a nasadit změnu, potom na iPhonu uložit jednu syntetickou knihu a ověřit hledání podle autora a umístění

### Automatický checkpoint 2026-08-02 20:06 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Formulář Knihy bezpečně vytvoří upravitelný návrh obsahu z dodaných podkladů bez automatického uložení; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1275 testů, 295.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/app/book_summary.py`, `Samantha_Agent/tests/test_book_summary.py`
- Commit: `Add safe book summary drafts`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit generování ze syntetických podkladů a ruční úpravu návrhu

### Automatický checkpoint 2026-08-03 10:57 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihy umějí bezpečně rozpoznat údaje z obálky, uložit validované ISBN a připojit fotografii až při uložení karty; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1277 testů, 304.4 s, výsledek OK
- Změněné cesty před paměťovým zápisem (10): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/app/book_cover.py`, `Samantha_Agent/tests/test_book_cover.py`
- Commit: `Add safe book cover recognition`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit náhled obálky, rozpoznání, ruční opravu, uložení přílohy a hledání podle ISBN

### Automatický checkpoint 2026-08-03 13:00 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihy umějí bezpečně dohledat a předvyplnit katalogové údaje podle ISBN bez automatického uložení; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1279 testů, 299.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/tests/test_book_isbn_lookup.py`
- Commit: `Add safe ISBN catalog lookup`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit známé ISBN, neznámé ISBN a ruční úpravu před uložením

### Automatický checkpoint 2026-08-03 19:10 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Tlačítko Přidat knihu se zobrazuje výhradně v oddílu Knihy; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Show add book action only in Books`
- Další krok: Převzít a nasadit změnu, potom na iPhonu přepnout mezi Recepty a Knihami a ověřit viditelnost tlačítka

### Automatický checkpoint 2026-08-03 21:40 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Dohledání knih rozlišuje síťové chyby a u ISBN-10 současně zkouší odpovídající ISBN-13; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1279 testů, 367.4 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_book_isbn_lookup.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Improve ISBN lookup diagnostics and fallback`
- Další krok: Převzít a nasadit změnu, potom znovu vyzkoušet ISBN 80-204-1453-3 a zaznamenat novou bezpečnou hlášku

### Automatický checkpoint 2026-08-03 22:14 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Dohledání knih bezpečně rozliší DNS, certifikát a další TLS či síťové chyby; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1279 testů, 369.2 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_book_isbn_lookup.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add safe ISBN connection diagnostics`
- Další krok: Převzít a nasadit změnu, znovu vyhledat stejné ISBN a sdělit přesnou novou hlášku

### Automatický checkpoint 2026-08-03 22:23 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Dohledání knih používá ověřený certifi CA balík a zachovává plnou kontrolu TLS; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/tests/test_book_isbn_lookup.py`
- Commit: `Use certifi for ISBN catalog TLS`
- Další krok: Převzít a nasadit změnu, potom znovu dohledat stejné ISBN

### Automatický checkpoint 2026-08-04 14:02 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihy umějí načíst podklady z 1–3 dočasných fotografií a uložit pouze zmenšenou obálku
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1283 testů, 369.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (10): `Samantha_Agent/app/book_cover.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_book_cover.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/app/book_text_ocr.py`, `Samantha_Agent/tests/test_book_text_ocr.py`
- Commit: `Add temporary book photo OCR`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit OCR, práci s rozpoznaným textem a jedinou zmenšenou přílohu obálky

### Automatický checkpoint 2026-08-05 08:10 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihovna nabízí výchozí i vlastní umístění a kategorie knih při založení i editaci.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Aktivní relace má neuzavřenou nejistotu doručení.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1288 testů, 450.4 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add book location and category choices`
- Další krok: Po samostatně potvrzeném nasazení ručně ověřit založení a editaci knihy s umístěním a více kategoriemi.

### Automatický checkpoint 2026-08-05 09:54 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Formulář knih má přehlednější pořadí, barevně odlišené oddíly a samostatné finální uložení; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Improve mobile book form flow`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit pořadí prvků a čitelnost barevných oddílů

### Automatický checkpoint 2026-08-05 11:35 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihovna umí z dočasné fotografie načíst ověřené ISBN bez ukládání snímku.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1290 testů, 325.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add ISBN photo capture for books`
- Další krok: Po samostatném potvrzení nasadit checkpoint a živě ověřit načtení ISBN na mobilu.

### Automatický checkpoint 2026-08-05 12:15 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihovna nabízí úplný seznam knih s pohledy podle kategorií, autorů a umístění i kombinovatelnými filtry; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1290 testů, 406.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add grouped book overview`
- Další krok: Převzít a nasadit změnu, potom na iPhonu ověřit všechny čtyři pohledy, kombinované filtry a otevření karty

### Automatický checkpoint 2026-08-05 22:05 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Dohledání knih nyní po prázdné přesné odpovědi bezpečně zkusí také vyhledávací index Open Library; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 48.7 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/tests/test_book_isbn_lookup.py`
- Commit: `Add Open Library ISBN search fallback`
- Další krok: Převzít a nasadit změnu, potom znovu otestovat ISBN načtených knih na iPhonu

### Automatický checkpoint 2026-08-06 20:20 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Existující knihu lze při editaci doplnit o ISBN z fotografie a bezpečně dohledat její katalogové údaje; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 14.7 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add ISBN tools to book editing`
- Další krok: Nasadit změnu a na iPhonu ověřit celý postup u existující knihy

### Automatický checkpoint 2026-08-07 08:57 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihy nyní ukládají a zobrazují volitelný rok vydání
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1324 testů, 308.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add book publication year metadata`
- Další krok: Nasadit změnu a na iPhonu ověřit založení i editaci knihy s rokem vydání

### Automatický checkpoint 2026-08-07 09:27 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: ISBN dohledání nyní porovnává údaje z obálky a bezpečně doplňuje rok vydání; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1325 testů, 405.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/book_isbn_lookup.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_book_isbn_lookup.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add Czech ISBN catalog comparison`
- Další krok: Nasadit změnu a na iPhonu ověřit shodu, neshodu i obě volby porovnání

### Automatický checkpoint 2026-08-28 09:21 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Knihy mají nové kategorie učebnice a cizojazyčná literatura a vlastní kategorii lze přidat i při editaci; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 12.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add custom book categories in Cockpit`
- Další krok: Nasadit změnu a ověřit přidání i výběr kategorie na iPhonu


### 2026-09-12 21:35 CEST – Fotografie bez čekání a správná pole podle kategorie

Hotovo:
- Automatické zmenšení fotografií na nejvýše 1 MiB; výběr více snímků k textu, URL i existující kartě; obálka nové knihy se také připojuje na pozadí.
- Stav přípravy/přenosu s názvem cílové karty, opakování jednotlivé chyby bez duplicit a ukončení neúspěšného připojování. Úpravy karty se s fotografiemi nepřepisují.
- Oprava CSS specificity skrývá knižní pole mimo kategorii Knihy.

Rozhodnutí:
- Schválený rozsah Míly: vývoj, commit, push a nasazení. Příprava je lokální bez AI, běžně mimo hlavní vlákno UI; HEIC může přenést původní soubor na Mac k převodu.
- Fronta je navázaná na otevřenou stránku a neměnný identifikátor uložené karty. Limity: vstup 32 MiB / 64 Mpx, výstup JPEG 1 MiB / delší hrana 2400 px.

Další krok:
- Dokončit autorizované c+p+n; po nasazení ověřit běžný snímek na iPhonu.

Navrhované další kroky:
- Případné doladění čitelnosti pouze podle reálné fotografie.

Technický důkaz:
- 363 cílených testů + 20 po poslední úpravě prošlo. Plná Cockpit brána prošla: 1607 testů, bez chyb (330,648 s unit testů); syntaxe a whitespace OK.
- Browserové ověření syntetických dat: velké PNG a HEIC, uložení textu při pozastaveném workeru 0,162 s, správné cíle dvou karet, retry po ztrátě odpovědi bez duplicit, zachovaný editor, nová kniha s obálkou, chybná fotka neblokuje text, desktop/mobilní viditelnost polí; 0 JS chyb.
- Rizika: čekající fronta se neobnovuje po zavření stránky; skutečný iPhone ještě nebyl otestován. Soukromý archiv ani originály na zařízení se testem neměnily.


### 2026-09-12 21:42 CEST – Dokončené c+p+n a ověřený provoz fotografií

Hotovo:
- Funkční commit `832c3360` je na GitHubu a nasazený v Cockpitu. Fotografie se připravují na pozadí a knižní pole se zobrazují pouze u knih.
- Knihovna je připojená, oba profilové workspaces jsou čisté a zarovnané; živý audit potvrdil `current` / `verified_current`.

Rozhodnutí:
- Schválené c+p+n je dokončené; tento navazující záznam pouze uchovává doklad nasazení.

Další krok:
- Na iPhonu obnovit Cockpit, vybrat fotografii a během přípravy pokračovat v psaní. Před zavřením počkat na stav Připojeno.

Navrhované další kroky:
- Při prvním běžném použití posoudit čitelnost vlastní fotografie; skutečné Safari na iPhonu zůstává uživatelským retestem.

Technický důkaz:
- Plná brána: 1607 testů bez chyb, unit testy 330,648 s; kontrola syntaxe a whitespace OK. Browserové syntetické scénáře prošly bez JS chyb.
- Řízené nasazení: 2026-09-12 21:40 CEST, funkční commit `832c33609f02`, nový proces a code stamp `e1e1b0f2b9e7e865`, rychlá nasazovací brána 18,2 s, smoke 5/5.
- Serverová stránka i worker přesně odpovídají zdroji, syntetický PNG byl přes HTTP úspěšně převeden na JPEG bez zápisu do archivu.
- Soukromé technické doklady: `data/private/library_photos_20260912/`; žádné skutečné fotografie ani texty knihovny nebyly použity jako testovací data.
- Riziko zůstává pouze praktické: čekající přenos vyžaduje otevřenou stránku, fronta se neobnovuje po zavření.


### 2026-09-12 22:25 CEST – Ilustrační fotografie do 0,3 MiB včetně náhledu

Hotovo:
- Jedna uložená hlavní fotografie do 285 KiB a náhled do 20 KiB, společně nejvýše 305 KiB. Tři fotografie se vejdou do 0,894 MiB. Backend neuchovává druhou velkou kopii.
- Příprava na pozadí a opakování přenosu zachovány; dočasná příprava pro OCR/ISBN zůstává oddělená ve vyšší kvalitě.
- Registrované prepare/apply/restore pro existující fotografie: kontrola konzistence registru a otisků, ověřená záloha, automatický návrat při chybě a obnova i po přerušení procesu, ochrana pozdějších úprav.

Rozhodnutí:
- Schváleno Mílou: ilustrační rozpočet a c+p+n. Použití na stará soukromá data podléhá přesné potvrzovací větě globální brzdy.
- Do knihovny se ukládá kompaktní ilustrace; odkaz dříve nazvaný Originál se u obrázků jmenuje Uložený obrázek. Plné originály na telefonu se nemění.
- Jednorázová soukromá záloha zůstane zachovaná mimo aktivní archiv; úsporu aktivního archivu je nutné odlišit od celkově uvolněného disku.

Další krok:
- Dokončit commit, push a nasazení. Pak vyžádat přesnou větu pro již připravený převod 22 fotografií a po použití dopsat výsledek do této kanonické dvojice.

Navrhované další kroky:
- Po kontrole výsledku rozhodnout o retenci jednorázové zálohy.

Technický důkaz:
- 388 cílených testů + 26 po posledním doplnění prošlo. Plná Cockpit brána prošla: 1622 testů bez chyb, unit testy 491,112 s; syntaxe a whitespace OK.
- Browserové end-to-end scénáře prošly, 0 JS chyb, text při pozastavené přípravě uložen za 0,153 s; hlavní snímek + náhled na disku mají nejvýše 305 KiB.
- Příprava existujících dat: 22 obrázků / 11 karet, 66 → 44 souborů, 61 988 739 → 6 251 688 B (59,117 → 5,962 MiB). Zdrojový archiv se nezměnil. Všechny výstupy dekódovány; textová receptová příloha zůstala při vizuální kontrole čitelná.
- Riziko/otevřeno: skutečný archiv čeká na přesné potvrzení; záloha 62 233 053 B se vytvoří až při použití. Nesmí se tvrdit, že již byla uvolněna odpovídající kapacita disku.


### 2026-09-12 22:35 CEST – Nové ukládání nasazeno; převod původních dat čeká na potvrzení

Hotovo:
- Funkční commit `2f5cf1f9` je na GitHubu a nasazený v Cockpitu. Nové ilustrace se ukládají celkem do 305 KiB a tři mají nejvýše 0,894 MiB.
- Řízené nasazení a provozní testy prošly. Knihovna je připojená a oba pracovní profily jsou čisté a zarovnané.

Rozhodnutí:
- Autorizované c+p+n vývoje je dokončené. Převod stávajících soukromých dat zůstává samostatným potvrzovaným krokem.
- Původní archiv ani fotografie nebyly při testech změněny; jednorázová záloha zatím nevznikla.

Další krok:
- Pro konkrétní převod 22 obrázků vyžádat přesnou větu globální brzdy. Potom znovu ověřit otisky plánu, použít registrovaný převod a dopsat skutečný výsledek do handoffu i TVBCP.

Navrhované další kroky:
- Po uživatelské kontrole převedených obrázků případně rozhodnout o retenci zálohy.

Technický důkaz:
- Plná Cockpit brána: 1622 testů, bez chyb, unit testy 491,112 s; cílené testy a browser prošly.
- Nasazení 2026-09-12 22:33 CEST: `2f5cf1f968ce`, code stamp `f57dfb8454ac938f`, nový proces ověřen, rychlá brána 8,3 s, smoke 5/5.
- Živá stránka a worker odpovídají přesně zdroji; HTTP příprava zachovala oddělené rozpočty a rozměry (ilustrace 1600 × 1200, dočasné rozpoznávání 2400 × 1800) bez zápisu do archivu.
- Soukromé účtenky: `data/private/library_compact_20260912/`. Připravený převod 59,117 → 5,962 MiB zůstává pouze plánem; staré fotografie dosud zabírají původní prostor. Záloha přibližně 59,35 MiB se vytvoří až při použití.


### 2026-09-12 22:44 CEST – Potvrzený převod všech 22 existujících ilustrací

Hotovo:
- Připravený plán byl po opětovné kontrole otisků použit na 22 obrázků v 11 kartách: 66 starých aktivních souborů nahradilo 44 JPEGů, 59,117 → 5,962 MiB (přibližně o 90 % méně).
- Všechny obrázky i náhledy splňují rozpočet a dekódují se; ostatní soubory, text, PDF, identifikátory, popisky a poznámky jsou zachované.

Rozhodnutí:
- Míla poskytl přesnou potvrzovací větu globální brzdy a výslovný pokyn „Zálohu později smazat“. Pokyn se váže pouze na backup tohoto převodu; záloha nyní zůstává pro kontrolu výsledku, automatický úklid se nezavádí.
- Funkční kód zůstává beze změny; platí již úspěšná plná brána 1622 testů a nasazení 6139b35d.

Další krok:
- Po uživatelské kontrole zmenšených obrázků provést již nařízené pozdější odstranění konkrétní zálohy a ověřit rozsah. Žádné jiné zálohy se nemažou.

Navrhované další kroky:
- Bez dalšího vývoje; při běžném používání ověřit fotografie na iPhonu.

Technický důkaz:
- Registrované apply: applied, 22 obrázků, 61 988 739 → 6 251 688 B; největší obrázek včetně náhledu 310 875 B.
- 299 ostatních souborů má shodný SHA-256, všechna neobrazová pole metadat zachována, registr a metadata 121/121 konzistentní; přesně 66 starých obrazových souborů odstraněno z aktivního archivu.
- Backup 62 233 053 B ověřen proti původním otiskům. Diskový prostor této zálohy není uvolněný. Účtenka, autorizace a následné ověření jsou pouze v soukromém adresáři plánu přes `data/private/library_photo_compaction/latest_prepared.json`.
