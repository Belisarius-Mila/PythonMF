<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-11-10 11:32 CET; proud `project-knowledge-library`, Data / `data/parallel-20261104`.
- ScienceNews je skutečně aktivované: nasazený kód, role i servírovaná ochrana
  celého českého uložení byly před spuštěním ověřené. Míla výslovně zapnul službu
  přesnou globální větou pro předložený rozsah Sol/medium Standard, 15 kreditů/job,
  100/měsíc. Jde o přejímací/rezervační meze, nikoli tvrdý provider billing cap.
- Jediný LaunchAgent com.samantha.science-news byl instalován a bootstrap vrací 0.
  Stejná trvalá účtenka má active, launch_attempted=true. Žádný opakovaný bootstrap.
- První skutečný tick: ok=true, state=not_due, last exit code=0, stderr=0 B,
  production jobs=0; žádný placený modelový tah ani dohánění minulého pátku.
  Cockpit API activated=true, pending_count=0.
- První příprava pátek 13. 11. 2026 od 08:00 Europe/Prague, publikace od 09:00,
  nejvýše 5 novinek. Služba kontroluje čas po 60 sekundách; mezi tick běhy proces neběží.
- CRISPR je již uložený jako celý český překlad s odkazem a sledováním. Původní
  jednorázový překlad se neopakuje; nové Uložit v UI/API vyžaduje hotový český text.
- Aktivační provedení neměnilo kód, živý JSON modelových rolí, starší archiv ani
  jiné služby; vytvořilo pouze schválenou privátní aktivaci a jediný systémový plist.
- Důkaz `reports/science_news_activation_20261110.json`; private launch receipt
  a live_activation_check_20261110.json pod science_news_activation. Předchozí
  kódová brána 2964 OK (5 SKIP), 112 cílených a 16 Node scénářů PASS; kód beze změny.
- Další krok: přejímka prvního pátečního vydání a fyzická kontrola na Mílově zařízení.
  Nejistý běh ověřit podle stejné účtenky, nevytvářet druhý pokus.
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


### 2026-09-12 23:09 CEST – Jednorázová záloha převodu smazaná na výslovný pokyn

Hotovo:
- Odstraněno přesně 188 záložních souborů / 62 233 053 B (59,350 MiB) a prázdné adresáře této jediné zálohy. Aktivní kompaktní knihovna a doklady převodu zůstaly beze změny.
- Registrovaná operace `delete_library_photo_compaction_backup` ověřuje dokončený převod, příslušné aktivní karty/obrázky a úplný seznam i otisky záložních souborů; odmítá cizí soubory a symbolické odkazy. Přerušené mazání lze dokončit bezpečným opakováním.

Rozhodnutí:
- Míla už poskytl globální potvrzovací větu, nařídil pozdější smazání a nyní výslovně zadal smazání právě zálohy 59,35 MiB. Souhlas se nevyžadoval znovu.
- Změna jiné karty nebo přidání nové karty po převodu není důvod blokovat tento úklid. Kontrolují se převáděné karty a jejich položky v registru; další práce zůstává zachovaná.
- Z této zálohy již nelze vrátit původní velké obrázky. Samostatné připravené kompaktní JPEGy a účtenky se podle tohoto pokynu nemažou.

Další krok:
- Žádný další úklid tohoto backupu nezbývá; pokračovat běžným používáním Knihovny.

Navrhované další kroky:
- Běžné používání Knihovny; bez automatického mazání a bez dalšího vývoje.

Technický důkaz:
- Následný audit: backup neexistuje, 357 souborů aktivního archivu a 50 ostatních souborů přípravy/dokladů beze změny podle SHA-256. Odstraněný logický objem 62 233 053 B neudává změnu volných bloků APFS.
- 39 cílených testů prošlo včetně odmítnutí cizích souborů/odkazů, zachování pozdější jiné karty, kontroly převáděných karet a pokračování po přerušení. Plná sada dokončila 1629 testů (441,205 s); 1628 prošlo, jediná chyba byl zastaralý očekávaný počet rizikových registrací 18 místo 19. Upraven pouze tento testový údaj; následný retest všech dotčených modulů prošel: 40 testů / 6,584 s. Produkční kód se po plné sadě nezměnil; plná sada nebyla znovu opakována.
- Soukromé účtenky: `data/private/library_compact_20260912/backup_cleanup_before.json`, `backup_cleanup_verified.json`; dokončení je i v původním `receipt.json`.


## 2026-11-09 20:45 CET — ScienceNews / 03-K4, lokální implementace

Hotovo:
- Míla má připravené nové ovládání vědeckých novinek v Knihovně a ikonu ScienceNews
  v horní liště. Zelená/pulzující znamená nevyřízené zprávy, šedá znamená vyřízeno.
- Tři rozhodnutí jsou trvalá; Uložit současně sleduje. Překlad se otevře samostatně
  a nevyřizuje položku. Oprávněný plný text není nahrazován abstraktem.
- Páteční příprava od 08:00 / publikace od 09:00 používá přijatý filtr všech osmi oborů,
  nejvýše pět zpráv a osm konkrétních čtecích kanálů; prázdná/známá dávka model nevolá.

Rozhodnutí:
- Míla přijal všech 12 kalibračních verdiktů beze změny a přesné ovládání popsané
  v projektové paměti; zadal implementaci. Neudělil tím souhlas s placenou zkouškou,
  novým modelovým bindingem, aktivací služby, pushem nebo nasazením.
- Sdílené modelové role, e-mail, kalendář, App Server klient a živé služby se nemění.

Další krok:
- Will převezme konkrétní Datův commit a po samostatném p+n ověří UI/API s Mílou
  na Macu a iPhonu. Model/effort/cena a malá zkouška mají vlastní schválení před aktivací.

Navrhované další kroky:
- Po přejímce navázat novou centrální roli až v kompatibilním runtime a aktivovat
  schválenou soukromou konfiguraci a LaunchAgent v provozním checkoutu.
- Zpětnou vazbou doladit kvalitu výběru a pokrytí zdrojů; počáteční seznam je omezený
  a převažuje Nature. Automatické mazání ani notifikace mimo Cockpit nejsou zavedené.

Technický důkaz:
- 115 cílených testů PASS včetně skutečných syntetických HTTP tras a 10 Node případů.
  Plná brána 2929 testů OK (5 SKIP), syntaxe a whitespace OK; log `logs/science_news_full_gate_20261109.log`.
- Čtecí zkouška osmi RSS PASS; CERN staré adresy 404, NIH 403 se nepovažují za fungující
  kanály. Doklad `reports/science_news_sources_20261109.json`.
- Role JSON byte-identický s výchozím commitem; ScienceNews provozní adresář ani
  activation.json nevznikly. Neproběhl modelový tah, živá archivace, instalace ani restart.
- Skutečný browser host nebyl dostupný; vizuální a fyzická iPhone přejímka je otevřená.
  Detaily a seznam souborů v `reports/science_news_implementation_20261109.md`.


## 2026-11-09 23:10 CET — ScienceNews: neaktivní překlad a konkrétní podklady zkoušky

Hotovo:
- Lokálně je neaktivní překlad jasně vysvětlený a tlačítko vypnuté; již hotové překlady
  zůstávají dostupné. Uložit / Sledovat / Nezařazovat fungují dál samostatně.
- Připraven kandidátní `science_news_trial.preview/run`: otisky zdroje, vstupu, kódu
  a kritických závislostí; konkrétní souhlas, sdílený socket, jediný read-only tah
  Standard, trvalá účtenka před spojením, kontrola účtu ChatGPT (API-key/unknown stop),
  raw odpověď před přejímkou. Timeout,
  ztracená odpověď, chybějící usage i vadný výstup blokují další pokus. Výsledek
  čeká lidskou sémantickou kontrolu; nic nepřenáší do živé fronty ani archivu.
- Pro zbývající CRISPR zprávu připraveno celé vlastní sdělení NIH (2953 znaků),
  nadpis, datum, podtitulek, všech devět odstavců, grant a reference; bez institucionálního
  boilerplate, obrázků a navigace. Není nahrazeno abstraktem ani plným článkem Nature.

Rozhodnutí:
- Míla povolil pokračovat přípravou jediné placené zkoušky a opravy matoucího UI;
  dosud nepovolil samotný modelový tah, nový role binding ani aktivaci ScienceNews.
- Dříve výslovně schválený import tří pilotních zpráv proběhl jednou; dvě mezitím
  vyřízené zprávy se neobnovují. Mílovo potvrzení nasazení je odděleno od přejímky opravy.

Další krok:
- Předat lokální UI opravu Willovi; před placenou zkouškou schválit přesnou
  kartu kandidáta; jednorázový vstup je připraven bez změny centrální role.

Navrhované další kroky:
- Jediný tah gpt-6.1-sol / medium / Standard, návrh přijímací meze 5 kreditů;
  zmrazený vstup, trvalá účtenka před odesláním a žádné opakování nejistého výsledku.
- Po přijaté zkoušce samostatně řešit binding, rozpočet, provozní text a páteční aktivaci.

Technický důkaz:
- 74 cílených testů PASS / 3,070 s včetně 12 Node případů; finální plná brána 2940 testů OK (5 SKIP).
  Logy `logs/science_news_translation_targeted_20261109.log` a `logs/science_news_translation_final_full_gate_20261109.log`.
- NIH přímé HTTP 403, veřejný index oficiální stránky poskytl tělo zprávy; whitespace
  normalizován. NIH FAQ ověřeno 2026-11-09, public-domain posouzení jen pro tento
  redakční text, žádné automatické oprávnění pro celou doménu, cizí obrázky či studii.
- Zdroj a přesný paket jsou ignorované pod `data/private/science_news_preflight/`;
  veřejný report uvádí SHA-256, rozsah, provenance, cenu a zbývající exekuční bránu.
- 3507 vstupních UTF-8 bajtů v proxy + 16000 přijatelných výstupních tokenů při
  Standard 50/250 kreditů za milion = 4,17535 kreditu. Není to tokenizace, faktura ani
  upstream limit. Placené tahy 0; centrální role, provozní data a služby beze změny.

Doplnění dokončení 2026-11-09 23:25 CET:
- Finální plná brána nad konečným kódem: 2940 testů / 422,860 s OK (5 SKIP).
  Čtecí živé ověření 23:23 CET: účet ChatGPT a přesný kandidát Sol/medium dostupný;
  žádný thread/start ani turn/start. Živá fronta nadále ukazuje 1 CRISPR zprávu bez překladu.
- `origin/main` je před vytvořením nového commitu o 56 commitů napřed. Will má
  převzít pouze tento konkrétní nový commit do aktuálního main, zkontrolovat případné
  konflikty a cíleně ověřit integraci. Žádný merge/rebase/push/nasazení se neprovádí.
- Přijímací karta v reportu je hotová, včetně změněných souborů, ceny, otisků,
  read-only metadata proof a testů. K samotnému jedinému placenému pokusu chybí souhlas.


## 2026-11-09 23:32 CET — ScienceNews: schválený překladový pilot dokončen

Hotovo:
- Je připraven skutečný český překlad celého dodaného těla tiskové zprávy NIH o CRISPR,
  včetně nadpisu, data, podtitulku, všech devíti odstavců, grantu a reference.
- Jeden schválený pokus Sol/medium Standard prošel technickou i Datovou věcnou kontrolou.
  Cena podle vykázaných tokenů je 0,5995 kreditu, pod přijímací mezí 5 kreditů.
- Čtenářský soubor `crispr-preklad-cs.txt` a nezměněná raw účtenka jsou private;
  Git-safe výsledkový report `reports/science_news_translation_trial_20261109.json`.

Rozhodnutí:
- Mílovo „Schvaluji.“ se vztahuje na přesný jeden připravený placený překladový test.
  Je tím spotřebován tento jediný pokus; nejde o aktivaci role, týdenního editoru,
  zápis do živé fronty/archivu ani p+n. Neproběhl žádný další modelový tah.
- Přípravná karta i programová raw účtenka se nepřepisují; Datova následná kontrola
  má samostatný záznam. Datova věcná kontrola není Mílova čtenářská přejímka.

Další krok:
- Míla přečte hotový český text; Will může převzít konkrétní lokální commity
  a po samostatném oprávnění propojit hotový překlad s existující pilotní zprávou.

Navrhované další kroky:
- Pro tuto zprávu nepřekládat znovu; bezpečně připojit již ověřený výsledek bez modelu.
- Aktivaci centrální role/rozpočtu, úplné texty a páteční automatiku převzít samostatně;
  jedna tisková zpráva neprokazuje kvalitu týdenního výběru ani obecné získávání zdrojů.

Technický důkaz:
- Raw účtenka: state=review, attempts=1, účet ChatGPT, gpt-6.1-sol/medium Standard;
  6980 input, 1002 output, total 7982, 0 cached. Z ověřeného usage vychází 0,5995 kreditu;
  nejde o nezávisle ověřenou fakturu poskytovatele.
- Strict JSON complete=true, 2953 znaků zdroje / 3012 znaků překladu, oba mají 12 bloků;
  Datovo porovnání ověřilo všech devět obsahových odstavců, čísla a jejich nerovnosti,
  názvy Al3Cas12f/RKK, grant R35GM138348, DOI, buněčný experiment a budoucí plán AAV.
- SHA-256 zdroje, zmrazeného reportu/paketu, raw účtenky a překladu jsou ve výsledkovém
  reportu. Nezměněné zdroje a instrukce byly znovu ověřeny čtecím preview, nikoli run.
- Vstupních 6980 účtovaných tokenů ukazuje režii nad proxy 3507 UTF-8 bajtů; proxy není
  horní mez účtovaného vstupu. Plán 4,17535 využíval 16000 výstupních tokenů a nebyl fakturou.
- Žádné změny kódu, modelových rolí, živé fronty či archivu, služby, push nebo nasazení.
  Dříve prošlo 74 cílených testů a 12 Node scénářů, plná brána 2940 OK (5 SKIP).


## 2026-11-10 09:20 CET — ScienceNews: CRISPR uložen česky, páteční aktivace připravená

Hotovo:
- Míla má CRISPR uložený ve Vědeckých článcích jako celý český překlad s původním
  odkazem, sledování je zapnuté. Zpráva opustila frontu, ostatní vyřízené piloty
  se neobnovily. Přenos použil už schválený překlad za nula dalších modelových tahů.
- Uložit zprávu nově vyžaduje hotový český překlad, v UI i serverovém API.
  Před překladem zůstávají Sledovat a Nezařazovat použitelné. Po jednoznačné validaci
  bez zahájené operace může uživatel změnit volbu; nejistý výsledek stále drží request ID.
- Připraven testovaný installer jediné služby com.samantha.science-news, s otisky,
  kontrolou nasazené role/kódu i skutečně servírovaného UI. Spuštění má trvalou
  účtenku před bootstrap; ztracenou odpověď jen ověří, bootstrap podruhé neposílá.

Rozhodnutí:
- Míla výslovně zadal uložit tuto konkrétní zprávu a aktivovat páteční zpravodaj.
  Uložení již proběhlo. Navržené meze 15/job a 100/měsíc ještě samostatně nepotvrdil;
  nedal ani přesnou globální větu potřebnou k instalaci LaunchAgentu.
- Dřívější jednorázový modelový pilot se neopakuje. Jeho raw účtenka a přípravná
  karta zůstávají historicky zmrazené; přenos ověřuje uložené hashované výsledky.

Další krok:
- Will převezme nový lokální commit do aktuálního main, zachová všechny jeho modelové
  role a samostatně nasadí. Potom ověřit aktivační návrh a s rozpočtem/global potvrzením
  zapnout páteční službu. Konkrétní postup `technical/science_news.md`.

Navrhované další kroky:
- První připravený termín pátek 13. 11. 2026 v 09:00 Europe/Prague, příprava 08:00.
- Po instalaci ověřit stejnou launch účtenku a dnešní not_due/0 placených doháněcích tahů.
- První skutečné vydání hodnotit podle přijatého filtru; samostatně zůstává omezené
  pokrytí vydavatelů a ověřování dostupnosti/licence celých zdrojů.

Technický důkaz:
- 112 cílených Python testů PASS / 8,347 s, včetně 16 Node případů.
  Finální plná brána: 2964 testů OK (5 SKIP), 547,271 s, syntaxe a whitespace OK.
- Registrace: `science_news_cached_translation.attach_and_save` a
  `science_news_activation.prepare/activate`. Cíleně ověřeny hash/URL/rozhodnutí,
  ztracená save odpověď, cizí editace, nejistý placený job, účet API-key, skutečné
  měsíční náklady, chybějící deploy, cizí agent a nejistý/selhaný bootstrap bez retry.
- Živý Cockpit readback: pending_count=0, CRISPR follow active. Archivní tělo končí
  přesným celým českým překladem; source URL zachované, jobs modelu nezměněné.
- Sazby Sol Standard ověřeny v oficiální dokumentaci 2026-11-10: 50/2,5/250 kreditů
  za milion input/cached/output. 15/100 jsou přijímací/rezervační meze, ne provider cap.
- Návrh je pouze private JSON, žádný LaunchAgent ani aktivace služby nevznikly.
  Aktuální provoz zatím nesplňuje code_ready/role_ready/served_save_guard;
  je nutné převzetí nového commitu Willem, nikoli opakování původního pilotu.

Doplnění dokončení 2026-11-10 09:24 CET:
- Finální plná brána 2964 testů OK (5 SKIP), 547,271 s; žádný nový modelový tah.
- Čtecí live proof: účet ChatGPT, Sol/medium dostupný, bez thread/start nebo turn/start.
  Aktuální runtime parser navrženou novou roli přijal v odděleném souboru a politiky
  všech jeho stávajících rolí zachoval. Živá role konfigurace se tím nezměnila.
- Služba com.samantha.science-news ani její systémový plist zatím neexistují.
  Konečný neplacený návrh e6e8eb06770426631ba1f0c85caf6e083be0f6c1ef1fbf87f5e4cdea784d375b
  má první vydání 2026-11-13T09:00:00+01:00, 15/job a 100/měsíc. Code/role/served guard
  zůstávají false do nového nasazení; původní nasazení tuto doplňující ochranu neobsahuje.
- Will při převzetí doplní do provozního config/agent_roles.json pouze science_news_editor;
  celý Datův JSON nepřebírat, protože aktuální main má další role. Ostatní role zachovat.


## 2026-11-10 11:32 CET — ScienceNews: služba aktivována

Hotovo:
- Páteční zpravodaj je skutečně zapnutý. První příprava je plánovaná na pátek
  13. 11. od 08:00 a vydání od 09:00 Europe/Prague; nejvýše pět zpráv.
- Služba byla jednou nahrána do launchd, první tick úspěšně počkal na termín.
  Cockpit už hlásí aktivaci. Dnes nevznikl placený modelový tah ani nové vydání.

Rozhodnutí:
- Míla zadal „Zapni službu“ a dodal přesnou globální potvrzovací větu pro předložený
  balíček. Potvrzení zahrnuje Sol/medium Standard, 15 kreditů na úlohu a 100 za měsíc.
- Rozpočet zůstává kontrolou dokončené usage a rezerv nedokončených úloh, nikoli
  tvrdým provider limitem. Nejasné modelové výsledky ani bootstrap se neopakují.

Další krok:
- V pátek 13. 11. převzít první vydání a jeho kvalitu; Míla ověří UI na svém zařízení.

Navrhované další kroky:
- Pokrytí dalších primárních zdrojů nebo zpřesnění filtru řešit podle skutečné zpětné vazby.
- Případnou chybu ověřit nad stejným weekly job/launch receipt, ne novým pokusem.

Technický důkaz:
- Před zápisem všechny readiness true: code_ready, role_ready, served_save_guard;
  runtime soubory beze změny proti přesnému schválenému návrhu e6e8eb06770426631ba1f0c85caf6e083be0f6c1ef1fbf87f5e4cdea784d375b.
- activate vrací active, launch_attempted=true, launch_returncode=0. launchctl potvrdil
  1 run, last exit code=0; periodická služba mezi běhy správně hlásí not running.
- První stdout {"ok":true,"state":"not_due"}, stderr 0 B, production job_count=0,
  API activated=true, pending_count=0. Žádný restart ostatních služeb nebo změna rolí.
- Provedení vytvořilo pouze privátní activation.json a jeden LaunchAgent. Kód se neměnil;
  předchozí plná brána 2964 OK (5 SKIP) zůstává relevantní, nyní přibylo živé ověření.

- Doplňující neplacená kontrola v cestě PATH služby a minimálním servisním prostředí:
  codex-cli 0.167.0 dostupné, sdílený App Server účet ChatGPT a Sol/medium kompatibilní.
  Nula thread/start a turn/start; žádná změna prostředí nebo restart služby.
