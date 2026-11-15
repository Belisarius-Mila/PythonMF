<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

### Cestování / místa — úplně ověřené, p+n čeká na servisní rozhodnutí

Priorita: 2; stav: ceka na prejimku/nasazeni; připomenout při startu: ano.

- Schválený přehled míst s fotografiemi/úvodem a samostatný detail. Správa
  i export pod Další možnosti, návrat drží hledání a pozici. Ostatní kategorie
  zachované.114 cílených PASS a izolovaný browser320/390/1280 PASS.
- Soukromá data se nemigrují, náhledy jen čtou existující text a ID fotografie.
- P+n výslovně schválené; první brána zastavila jedinou chybu, opravenou
  beze změny rozsahu. Aktuální výsledek podle přesného jobufff30ae477f38401ae8e582208e9a582
  a privátní travel_ui_20261115/release_v2/release_receipt.json + live_verification.json.
  V2 skončilo attention bez push/nasazení; následná celá diagnostická sada
  3922/0 chyb PASS. Čeká rozhodnutí o samostatné opravě900s limitu.
  Fyzický iPhone až po vydání; podrobně reports/travel_places_ui_20261115.md.


### Knihy — skupiny Konspektu nasazené

Priorita: 2; stav: rozpracovane; připomenout při startu: ano.

- Ruční obory a odstranění starých kategorií jsou vydané:24096145,
  Terra job cc7bb358f72b61b428a8f4fb09fa7c7b, push/deploy confirmed,
  publikační brána3908 PASS a smoke5/5. Nativní účtenka zkontrolovaná;
  portálový returned_to_adam není potvrzený.
- Následné jednorázové čištění je dokončené:3 knihy,11 položek slovníku,
  5 souborů; přesné původní zálohy ověřené, všech6 knih a jejich obrázky
  i zařazení zachované,0 starých kategorií. Historie operací beze změny.
  Apply ani původní p+n neopakovat. Důkazy zůstávají soukromě pod
  data/private/book_subject_edit_20261114/ (completion/release/live/cleanup).
- Skupiny Konspektu jsou nasazené v64e9897a: katalogové i samostatné ruční,
 606 pojmenovaných kódů, závislý filtr a seskupení.394 cílených PASS,
 plná3918 PASS/31 SKIP; po drobném UI zpřesnění browser a24 frontendových PASS.
 P+n potvrzené job3f40788ac09e6a1b24ada757ef6534c1, smoke5/5; fyzická přejímka zbývá. Katalogové MARC072:
  $a kód, $x název, $9 hlavní obor, $2 Konspekt. Nevymýšlet z názvu či faset.
  Staré snapshoty a pending fingerprints/replay musí zůstat kompatibilní;
  ruční původ samostatný, žádná hromadná migrace soukromých knih.
- Pořadí: knihovna → konkrétní UI na iPhonu → poštovní přejímka A+C.
  Podrobnosti mobilního UI zatím chybí; nevymýšlet celkový redesign.
  Nový ruční obor ještě čeká na fyzickou iPhone přejímku. Dosavadní sken
  Míla přijal. Vnější watchdog není objednaná implementace.
- Pošta: dnešní soukromý most uvádí configured/worker_recent=true,
  active=0/completed=4; to není budoucí provozní důkaz. Před testem znovu
  registrovaně ověřit běh a vazby. Historický stav12.11. není dnešní stav.
- Blokace main skončila: přesný cizí Vocabulary EN job
  4e5e18a70db086fa6eac083f0f9e2984 dokončený,2b17cbb4, Pages/push confirmed,
  3912 PASS, HTTP200. Pouze čekání a čtení téže účtenky, žádný nový submit.
  Dočasný soukromý most je tímto dorovnaný; nový TVBCP nevzniká.

Další krok: pokračovat UI poštovního agenta; místní oprava mobilních tlačítek
je v reports/email_mobile_actions_20261114.md. Knihovna64e9897a je již nasazená,
fyzická iPhone přejímka zbývá. Po UI poštovní A+C; nové aktivace ani hromadné
čištění nejsou zadané.

### ScienceNews — dosavadní doložený stav (nový živý audit se nyní neprováděl)

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

Předchozí doložené stavy (historie přípravy před aktivací):

- 2026-11-10 10:58 CET: Systémové potvrzení přijato a blokátor nové role je uzavřený: registrovaný upgrade pošty 617f3e0d→8c83e93b ověřen,95 položek i business digest/nastavení/role identické. Skutečný nový parser načítá live science binding.
- Teprve potom main převzal připravený 31a59e0c s Datovým aad367c7. Žádný další ScienceNews save, překlad nebo instalace plánovače se neprováděly.
- Míla následně prioritně nahlásil kalendářový bug. Původní editace byla dočtena bez druhého save; problém pořadí alarmů lokálně opraven a společná plná brána PASS: 3406 testů / 31 SKIP (620,186 s). Převzetí a nasazení pokračují jedním runtime balíčkem.
- Další krok: finální checkpoint a zadané Terra p+n; účtenka `logs/science_calendar_release_20261110.log`. Páteční ScienceNews služba/rozpočet zůstávají samostatné. Reporty `reports/email_science_role_upgrade_20261110.md` a `reports/calendar_edit_alarm_order_recovery_20261110.md`.

- 2026-11-10 10:09 CET: Datův `aad367c7` je převzatý a testovaný pouze na izolované větvi `will/science-news-20261110`; živý main/pošta/role zůstávají beze změny.
- 134 cílených testů PASS, plná izolovaná brána PASS: 3405 testů / 31 SKIP (641,430 s). UI i API vyžadují celý český překlad před uložením; žádný modelový tah nebo opakování již hotového save.
- Blokátor skutečně ověřen: vlastněná hodinová pošta 617f3e0d čte hlavní role přes symlink a kandidátní science_news_editor odmítá AgentRoleError. Nový binding se nesmí objevit na main dřív než kompatibilní runtime.
- Připravené pořadí: s přesnou globální brzdou upgrade pošty 617f3e0d→již publikovaný 8c83e93b, jeho živé ověření; potom fast-forward připraveného checkpointu a registrované Terra p+n. Mílovo zadání k nasazení platí, systémové přepnutí potřebuje vlastní přesnou větu.
- Páteční ScienceNews plánovač se tímto nezapíná a nový rozpočet se neschvaluje. Report `reports/science_news_aad367c7_integration_20261110.md`.

- Aktualizováno: 2026-11-10 09:20 CET; proud `project-knowledge-library`, Data / `data/parallel-20261104`.
- Míla výslovně požádal zapnout páteční zpravodaj a uložit CRISPR v češtině.
  Celý hotový český překlad byl jednou uložen do Vědeckých článků s původním odkazem;
  sledování zapnuté, živá fronta pilotů prázdná. Žádný nový placený tah.
- Zpětná kontrola skutečné archivní karty potvrdila celý český text; anglický plný zdroj
  se do těla karty neukládal. Jobs modelu beze změny. Private účtenka
  `data/private/science_news_activation/crispr_save_receipt_20261110.json`.
- Nové Uložit v UI i serverovém API čeká na hotový český překlad; samotný abstrakt
  nestačí. Jen prokazatelně nezahájená validace uvolní browser request_id; nejistý save ne.
- Páteční aktivace je připravená, nikoli zapnutá: první návrh 13. 11. 2026 v 09:00
  Europe/Prague, příprava od 08:00, max 5 novinek. Sol/medium Standard,
  návrh 15 kreditů/job a 100/měsíc. Rozpočet a instalace LaunchAgentu čekají potvrzení.
- Guard účtu ChatGPT zastaví API-key/unknown před vláknem. Měsíční evidence započte
  doložené dokončené náklady a drží rezervy neukončených/nejistých úloh.
- Modelová role je připravená jen ve vlastním config/agent_roles.json. Provozní role,
  systémové LaunchAgents a služby Data neměnil. Will musí převzít nový commit do main,
  zachovat jeho další role a samostatně nasadit i serverovou/UI ochranu českého uložení.
- Ověření: 112 cílených Python testů PASS, včetně 16 Node scénářů.
  Finální plná brána: 2964 testů OK (5 SKIP), 547,271 s, syntaxe a whitespace OK.
- Detail a konkrétní předání: `reports/science_news_activation_20261110.json`.
  Po nasazení znovu ověřit návrh, pak s výslovným rozpočtem a přesnou globální větou
  aktivovat jediný LaunchAgent. Žádný automatický druhý bootstrap ani modelový pokus.
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

## 2026-11-09 21:46 CET — Převzetí ScienceNews do společného Cockpitu

**Hotovo:** Datův ScienceNews je lokálně integrovaný se současným kalendářem a Archivem. Izolovaný skutečný browser prošel všemi třemi volbami a změnou poslední zelené na šedou, včetně obnovení stránky.

**Rozhodnutí:** Míla výslovně schválil převzetí fb708be9 a předání Terře pro p+n. Publikuje se kód/UI, bez aktivace placeného editoru, bez provozního importu karet a bez instalace plánovače. Datův worktree se nepřepíná ani nemigruje.

**Další krok:** Po úspěšné bráně dokončit merge checkpoint, zarovnat jen čisté profily a provést schválené p+n pro project-knowledge-library registrovaným submit_release(wait=True).

**Navrhované další kroky:** Přejímka skutečného UI/API; případný provozní UI import až po jeho samostatném schválení. Potom samostatná volba modelu/ceny a malá živá QA, kompatibilita všech runtime parserů, rozpočet a teprve povolená aktivace služby.

**Technický důkaz:** 161 cílených testů PASS; izolovaný headless Edge 390×844 PASS, bez modelu a bez produkční fronty/archivu. Plná integrační brána 3365 testů OK (31 SKIP). Bindingy rolí shodné s5ea9af40, šest konfliktů vyřešených zachováním obou funkcí a silnějších main kontrol. Rizika: zdroje mají omezené pokrytí; placený editor a jeho odborná QA nejsou aktivované. Report `reports/science_news_integration_20261109.md`.

## 2026-11-09 22:09 CET — Přerušené vydání a ochrana spouštěče

**Hotovo:** Datův commit je zachovaný v merge1395956d. Lokálně opravený spouštěč už při aktivním p+n neukončí starší běžící Cockpit; nejistý stav restart blokuje. Otevření existující verze zůstává možné, autorizovaný restart publikačního workeru se nemění.

**Rozhodnutí:** Nevydávat restartem načtený kód za potvrzený push/deploy. Původní účtenku nepřepisovat a po nejasném výsledku automaticky nespouštět nové předání. ScienceNews role/model/plánovač i provozní import zůstávají bez aktivace.

**Další krok:** Dokončit bránu/checkpoint ochrany a předložit Mílovi přesný nový balíček k novému potvrzení p+n.

**Navrhované další kroky:** Po potvrzeném vydání teprve samostatná provozní UI/modelová přejímka podle science_news.md.

**Technický důkaz:** Původní integrační brána 3365 OK/31 SKIP, 161 cílených a izolovaný mobilní browser PASS. Oprava spouštěče 77 cílených PASS; její plná brána PASS: 3370 testů / 31 SKIP (546,298 s). GitHub 5ea9af40, veřejný nový HTML/API i lokální 1395956d shodné, ScienceNews initialized=false/activated=false. Logy a přesná časová osa v reports/science_news_release_interruption_20261109.md. Riziko: původní vydání nemá dokončenou publikační/protection účtenku; žádný nový placený pokus nesmí vzniknout bez dalšího pokynu.


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


## 2026-11-09 23:38 CET — Willovo převzetí dvou překladových commitů

**Hotovo:** Oba Datovy commity jsou integrovány nad současné vydání, 116 cílených testů PASS. Zachovány kalendář, Archiv, role, ochrana restartu a obě historické větve dokumentace.

**Rozhodnutí:** Míla výslovně schválil převzetí a následné Terra p+n; jednorázový pilot již proběhl u Data a neopakuje se. Publikuje se kód/UI a bezpečný report, nikoli soukromý překlad nebo aktivace služby.

**Další krok:** Dokončit plnou bránu a merge checkpoint, zarovnat čisté profily a provést schválené submit_release(wait=True) pro project-knowledge-library. Přesný výsledek vydání číst z logs/science_news_two_commits_release_20261109.log, nepředjímat ho.

**Navrhované další kroky:** Mílova četba a fyzická přejímka; připojení hotového překladu ke kartě vlastní omezenou operací bez druhého modelového tahu, případná služba samostatně.

**Technický důkaz:** 116 cílených testů PASS; plná integrační brána PASS: 3381 testů / 31 SKIP (492,622 s). Žádný placený překlad ani zápis do živé fronty/archivu. Pět konfliktů vyřešeno v dokumentaci a snapshotu, LL-121 místo kolidujícího LL-114. Report reports/science_news_two_commits_integration_20261109.md; předchozí vydání 32c4ed20/účtenka 243f9c9c a CI 42705522900 potvrzené.

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


## 2026-11-10 10:09 CET — Izolované převzetí a kompatibilita hodinové pošty

**Hotovo:** Ochrana celého českého uložení a příprava páteční služby jsou integrované v oddělené kopii; 134 cílených testů PASS. Živá pošta i její dosavadní konfigurace zůstávají zachované.

**Rozhodnutí:** Míla požádal nasadit nový Datův commit. Nutný krok kompatibility nesmí zpřístupnit neznámou roli staršímu hodinovému parseru. Instalace páteční služby a její rozpočet zůstávají samostatné.

**Další krok:** Dokončit izolovanou plnou bránu/checkpoint a předložit přesný upgrade pošty 617f3e0d→vydaný 8c83e93b k potvrzení globální brzdou; poté lze dokončit již zadané p+n.

**Navrhované další kroky:** Po kompatibilním upgradu zpřístupnit nový binding a nasadit připravený balíček; páteční aktivaci řešit odděleně po dohodě rozpočtu.

**Technický důkaz:** Skutečný instalovaný parser odmítl dočasný kandidátní JSON (AgentRoleError, science_known=false), přímo ověřen sdílený symlink; main se nezměnil. 134 cílených testů PASS, plná izolovaná brána PASS: 3405 testů / 31 SKIP (641,430 s). Report reports/science_news_aad367c7_integration_20261110.md. Riziko přímého merge: opakovaný výpadek pošty.


## 2026-11-10 10:58 CET — Kompatibilita nové role potvrzena, navazuje společné vydání

**Hotovo:** Kompatibilní vlastní poštovní runtime je skutečně nainstalovaný a čte nový live binding. Všech95 položek, business digest, nastavení i původní modelové role byly při přepnutí zachované. Datův commit je teprve poté převzatý do main.

**Rozhodnutí:** Míla dodal přesnou globální větu a prioritně nahlásil kalendářový bug. Již zadané nasazení pokračuje se související opravou; žádný nový ScienceNews modelový pokus, save ani instalace páteční služby.

**Další krok:** Dokončit společný kalendářový checkpoint a zadané Terra p+n.

**Navrhované další kroky:** Páteční rozpočet/instalace a fyzická přejímka samostatně.

**Technický důkaz:** Registered pause/prepare/upgrade617f3e0d→8c83e93b, všechny checks true, health already_completed. Následný instalovaný parser načetl skutečný main config včetně nové role. Původní kalendářová transakce ověřena read-only bez druhého update. Reporty reports/email_science_role_upgrade_20261110.md a reports/calendar_edit_alarm_order_recovery_20261110.md; budoucí výsledek publikace v logs/science_calendar_release_20261110.log.


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


### 2026-11-12 08:02 CET — Dokumentační integrace hotové Datovy větve

Hotovo: Do main převzatý závěr Data3035fc14 a jeho dosud nesloučená historie; kód, testy, konfigurace, workflow, média a služby se proti main c22bc3af nemění. Doplněné dříve chybějící aktivační a publikační doklady ScienceNews/MMTX, zachované novější main zápisy včetně kompatibility pošty, e-mailového backendu a obnovy terminálu.

Důkaz: Report `data_repository_integration_20261112.md` popisuje rozsah a ověření. Původní účtenky jsou historické důkazy z10.–11.11., nikoli nový provozní audit. Žádná nová aktivace, modelový tah, push ani nasazení.

Rizika a další krok: Přejímky na zařízení a procesní nejistota původního Pages publisheru zůstávají otevřené. Hotové lokální commity čekají na samostatný pokyn k publikaci. Datův vlastní worktree a rozpracovaná UI větev se nemění.


## 2026-11-13 12:54 CET — Rychlé ISBN knihy lokálně připravené, plná brána probíhá

Hotovo: Telefonní sken/ruční ISBN, náhled, potvrzené základní uložení,
kontrola duplicity a další exemplář. Umístění se doplní až na Macu,
jednotlivě nebo pro vybrané knihy. Původní podrobný formulář zachovaný.

Rozhodnutí: Míla schválil plán a zahájení vývoje. Katalogovou část předala
registrovaná Luna; Adam převzal přesný ověřený diff a řešil kameru/persistenci/UI.
E-mailový test A+C odložený, nasazení Cockpitu ještě není schválené.

Další krok: Dokončit plnou bránu a místní checkpoint; potom samostatné p+n
a fyzická přejímka kamery a přibližně20 knih na iPhonu/Macu.
Navrhované další kroky: Podle pilotu doplnit české zdroje obálek. ScienceNews
přejímka zůstává samostatná; tato práce ji nepotvrzuje ani znovu neaktivuje.

Technický důkaz:368 cílených integračních PASS, Node ochrany ručních úprav,
trvalé identity a kamery; headless390/1280 bez přetékání, skutečný WASM EAN13,
ztracená HTTP odpověď a reload bez druhého zápisu v izolovaném archivu.
Podrobnosti reports/book_quick_inventory_20261113.md a
technical/book_quick_inventory.md. Plná brána zatím není doklad PASS.


## 2026-11-13 13:11 CET — Rychlé ISBN knihy lokálně dokončené

Hotovo: Schválená první verze je připravená k samostatnému vydání. Kamera,
lokální fotografie kódu a ruční ISBN vedou k náhledu a potvrzenému zápisu
do Mac archivu; umístění až později. Přehled a hromadné přiřazení umístění,
duplicity a výslovný další exemplář dokončené. Podrobný původní formulář zachovaný.

Rozhodnutí: Žádná změna schváleného rozsahu. Původní plná brána byla
překonaná opravou skutečných hlaviček; finální nový běh prošel. Kód je
lokální, p+n ani fyzická iPhone přejímka zatím nebyly provedené.

Další krok: Samostatně schválit p+n proudu project-knowledge-library;
potom fyzická iPhone/Mac přejímka podle TXT v Downloads.
Navrhované další kroky: Pilot přibližně20 knih a podle jeho výsledků další
české zdroje obálek. E-mailové A+C a ScienceNews zůstávají samostatné.

Technický důkaz: Finální plná brána3783 testů OK/31 skip,646,686s unit testy,
fáze654,3s, log library_isbn_full_gate_final_20261113.log. Všech21 finálních
zdrojových otisků beze změny.368 cílených a327 bezpečnostních/integračních
PASS, překrývající se sady. Plné COCKPIT_HTML se skutečnými hlavičkami,
headless390/1280, fake kamera pouze video + stop tracků, skutečný WASM,
disconnect/reload bez druhého zápisu PASS. Soukromý živý archiv se neměnil.
Zkouška není fyzický iPhone ani deployment. Kompletní scénář v Downloads:
Samantha_Knihovna_ISBN_testovaci_scenar_2026-11-13.txt.


## 2026-11-13 15:59 CET — Lokální oprava nereagujícího startu kamery

Hotovo: Připravené okamžité vyžádání kamery po klepnutí, bez předchozího
čekání na JS/WASM čtečku. Stav je u tlačítka před náhledem, opakované klepnutí
při startu blokované; chyba povolení či čtečky je viditelná. Načítání JS/WASM
má15s mez a při chybě ukončí stream. Pozdní starý start nezastaví novou kameru.

Rozhodnutí: Míla nahlásil první fyzický iPhone problém „Skenovat kamerou“
bez viditelné reakce. Konkrétní příčina na jeho zařízení ještě není potvrzená;
čeká informace Safari versus ikona a znění původního stavu. Oprava odstraňuje
prokázané čekání před žádostí a chybějící ohraničení chyb. Zápisy knih,
umístění, katalogy, oprávnění HTTP a modely se nemění.

Další krok: Samostatné p+n opraveného commitu a znovu fyzický iPhone sken.
Navrhované další kroky: Po úspěšném startu pilot přibližně20 knih, včetně
duplicity a chybějící obálky. E-mailový A+C zůstává odložený.

Technický důkaz: První verze je již vydaná v0ec447e7, runtime účtenka
1267634111aad32de7f188312d900770 confirmed; dnešní následný audit HTTP/HTTPS
potvrdil přesně shodné HTML, camera=(self) a obě čtecí asset URL HTTP200.
Regrese okamžité žádosti FAIL před opravou → PASS po ní; šest nových
Node průchodů (odmítnutí, timeout, chybějící API, chyba WASM, zavření, restart)
a původní životní cyklus/ukládání PASS.60 cílených Python testů PASS/13,294s,
rychlá statická brána PASS. Celé COCKPIT_HTML se skutečnými hlavičkami,
viewport390, falešná video-only kamera před uvolněním pozdrženého reader.js,
viditelný stav a následné načtení skutečného WASM PASS. Zablokovaný WASM
zobrazí chybu, ukončí stopy a znovu zpřístupní tlačítko.0 zápisů archivu.
Nová oprava je pouze lokální, bez p+n a bez potvrzené fyzické iPhone přejímky.
Logy library_camera_start_browser_20261113.log a library_camera_start_static_20261113.log;
privátní doklad camera_start_fix_browser_qa/result.json.


## 2026-11-13 17:35 CET — Doplnění roku z českého katalogu, obálka čeká na ISBN

Hotovo: Po otevření přes HTTPS Míla potvrdil načtení knihy na iPhonu.
Následně nahlásil chybějící rok a miniaturu. Rok je lokálně opravený:
českému API se výslovně vyžádají publicationDates/publishers a z odpovědi
se převezme jednoznačný rok, bez dalšího dotazu a čekání na Open Library.
Neplatné a víceznačné roky se neodhadují.

Rozhodnutí: Rozsah zůstává rychlá ISBN inventura. Obálky se nadále zkoušejí
přes Open Library; konkrétní případ zatím není ověřený, protože chybí ISBN.
Žádná registrace další služby ani její oprávnění se nepředpokládají.
HTTPS lze uložit jako novou ikonu z Safari; relativní PWA manifest zachová
HTTPS původ. Není potřeba další aplikace.

Další krok: Převzít ISBN od Míly a ověřit konkrétní chybějící obálku;
opravený rok vyžaduje samostatné schválené p+n.
Navrhované další kroky: Potom pilot přibližně20 knih a umístění na Macu.

Technický důkaz: Kamerová oprava4e7007ae je skutečně nasazená, účtenka
d4e292cadfbff224094fd22cb4614ccd, push/deploy confirmed, plná brána3823,
smoke5/5 a přesná HTTP/HTTPS shoda HTML. Nová oprava roku:36 cílených
PASS/1,462s, dva regresní FAIL před opravou → PASS po ní, statická brána
PASS. Veřejný příklad9788025229033 vrací2018, Egmont,0,384s; nejde
o ISBN nahlášené Mílou. Logy library_year_czech_catalog_*_20261113.log.
Výchozí API roku neposílalo; explicitní field[] jej poskytuje. Zdroj schématu:
https://github.com/vufind-org/vufind/blob/dev/config/vufind/SearchApiRecordFields.yaml .
Tato nová metadata změna je pouze lokální; soukromé knihy se nepřepisovaly.


## 2026-11-13 20:17 CET — Kategorie z katalogu a skutečné místní miniatury

Hotovo: Na výslovné upřesnění Míly je kategorie nepovinná; přebírá se pouze
žánr/formát označený katalogem jako genre/form, bez odhadu podle témat.
Při chybějícím údaji zůstávají tags prázdné a přehled ukáže Bez kategorie.
Rychlý formulář umožní převzaté kategorie opravit. Nová katalogová kategorie
zůstane vybraná i při následné podrobné editaci.

Rozhodnutí: Po potvrzení Uložit do knihovny se dostupná miniatura z pevné
Open Library URL skutečně uloží jako soukromý JPEG na Macu. Náhled ani sken
samy soubor nebo knihu neukládají. Limit vstupu2 MiB/8 Mpx, timeout3 s, JPEG
nejvýše240×320 a64 KiB, bez EXIF; přesměrování jen na tentýž HTTPS host.
V registru je stávající příloha book_cover; seznam i detail čtou místní API.
Nedostupná miniatura neblokuje knihu a UI výslovně oznámí uložení bez obálky.
Staré knihy se hromadně nemění a nejsou znovu stahované.

Technický důkaz:49 cílených testů ISBN/uložení/stahování PASS; dalších83
frontend/archive/photo/persistence PASS. Node ověřuje převzetí kategorií,
pozdní ruční editaci, skutečný nový payload a návrat na místní obrázek.
Mobilní/desktopový headless browser390/1280 PASS: místní příloha i obrázek
v seznamu mají naturalWidth>0 při zablokovaném covers.openlibrary.org;
ztracená odpověď a reload nezaloží duplikát. Lokální logy
library_thumbnail_browser_qa_20261113.log a library_thumbnail_live_catalog_20261113.log.
Plná brána: 3850 testů OK/31 skip, 642.1 s; statická i plná brána PASS.

Obnova: Nové volitelné categories/store_cover vstupují do otisku jen pokud
jsou ve vstupu. Staré čekající požadavky mají původní otisk i chování.
Zápis nejdřív rezervuje přesný JPEG a SHA-256, potom vytvoří výhradně nový
soubor, metadata a registr. Opakování používá původní bajty, nikoli síť;
cizí soubor nepřepíše. Po úspěchu rezervace obsahuje již jen otisk a metadata.
Změna ISBN ponechá všechny soubory, ale katalogový obrázek jiného vydání
přestane nabízet jako obálku. Vlastní fotografie má přednost.

Zdrojové vazby: Předchozí oprava roku bb05bf8f byla samostatně vydaná
účtenkou3fef2e2d678aeb969918e5f9902ac33c, push1/deploy confirmed,
3823 testů a smoke5/5. Tento nový krok zatím nemá p+n. Veřejný katalog
pro ISBN9788024932460 živě vrací2016 a dvě žánrové kategorie; Open Library
obálku nemá (404). Veřejný kontrolní vzorek9780385472579 vrací JPEG1459 B.
Živá knihovna se těmito testy neměnila.

Rizika: Fyzická přejímka nového formuláře na iPhonu zůstává po nasazení.
Obálkyknih.cz nejsou integrované. Jejich podmínky trvalé ukládání zakazují;
předchozí registrační dotaz trvalé stahování nepožadoval. Míla musí doplnit
dotaz výslovně i na malé soukromé trvalé miniatury a získat jejich souhlas.
Zdroj: https://www.obalkyknih.cz/about ; Open Library postup:
https://openlibrary.org/dev/docs/api/covers . Žádná zpráva se nyní neposílala.

Další krok: Samostatně schválené p+n této konkrétní změny; pak telefonní
pilot a umístění na Macu. Poskytovatele českých obálek doplnit až podle
odpovědi a dohodnutých podmínek. E-mailový A+C test zůstává odložený.

Ověřovací prostředí: První plná brána měla pouze7 chyb pomocného Git commitu
v email_service_control (Author identity unknown); žádná funkční chyba
nové změny. Bez změny skutečného Gitu prošla s procesní syntetickou Git
identitou celá dotčená sada30 testů a potom znovu i úplná brána.
Konečný log: library_thumbnail_full_gate_verified_20261113.log;
podrobná měření: library_thumbnail_unit_timings_20261113.log.


## 2026-11-14 14:38 CET — Online obálky z Obálkyknih.cz

Hotovo: Místně napojený rychlý ISBN náhled a seznam knih přes ověřený
cache3.obalkyknih.cz. Obrázek otevírá povinný odkaz na zdroj, název v seznamu
otvírá naši knihu. Chyba, prázdný1×1 obrázek a5s čekání v náhledu přejdou
na Open Library. Lazy obrázky v seznamu se nevyčerpají dřív, než jsou vidět.
Uložení knihy zachová online náhled; vlastní fotografie a místní miniatura
mají přednost. Nové vysvětlení rozlišuje online a místně uloženou obálku.

Rozhodnutí: Míla výslovně zadal napojení i při částečném rozšíření oprávnění
mezi servery. Používá se doložený cache3 a dosavadní náhrada Open Library.
Pouze pro tento obrázek odchází registrovaný origin, žádná cesta či parametry
našeho soukromého katalogu. Trvalé ukládání obálek Obálkyknih není schválené;
server je nestahuje. Původní ukládání Open Library, metadata, zápisové
identity, zdrojové vazby a ochrana při změně ISBN zůstávají zachované.

Další krok: Samostatné p+n proudu project-knowledge-library do runtime
Cockpitu a fyzická přejímka na iPhonu. Tato změna ještě není nasazená.

Navrhované další kroky: Schválená náhrada prozatímních kategorií26obory,
oddělené žánry/formy a témata; dynamické filtry jen ze skutečně uložených
knih s počty. Jde o další samostatný krok. Trvalé miniatury Obálkyknih
doplnit jen podle výslovné dohody s poskytovatelem.

Technický důkaz:88 cílených Python testů včetně Node regresí PASS. Finální
frontendový kontrakt znovu23 PASS. Skutečný headless prohlížeč na registrovaném
HTTPS originu načetl živou obálku170×240 a ověřil backlink, uložení bez
kopie Obálkyknih, chybový/1×1/timeout fallback, místní prioritu i lazy scroll.
Viewporty390/1280 bez přetékání;2 syntetické knihy v izolovaném archivu,
0 produkčních POST a0 neodchycených výjimek. Logy obalkyknih_*_20261114.log;
privátní podklady data/private/obalkyknih_integration_20261114/.
Statická brána logs/obalkyknih_static_gate_20261114.log.


## 2026-11-14 19:58 CET — Dorovnání soukromého mostu po vydání

Hotovo: Ruční knihovní obory jsou vydané a jednorázové čištění starých
kategorií dokončené. Přesné zálohy, všechny knihy, obrázky a zařazení zachované;
historie operací se neměnila. Kanonický stav nyní odpovídá dokončeným účtenkám.

Rozhodnutí: Míla zadal pořadí knihovna (jemnější skupiny Konspektu), potom
konkrétní iPhone UI a poštovní A+C. Vývoj skupin schválený; nové p+n ani
hromadná migrace tím nejsou povolené. Vnější watchdog zůstává pouze návrh.

Další krok: Zpětně kompatibilně doplnit skupiny z vybraného MARC072 a jejich UI.
Navrhované další kroky: Fyzická přejímka nového zařazení, konkrétní mobilní
průchod a poté poštovní scénář v Downloads. Skutečná noc dohledu čeká na Mílu.

Technický důkaz:24096145 / cc7bb358f72b61b428a8f4fb09fa7c7b,
push/deploy confirmed,3908 PASS/smoke5. cleanup_receipt:done,3 knihy,
11 položek,5 souborů, přesné původní zálohy a0 zbývajících kategorií.
completion_receipt/live_verification v data/private/book_subject_edit_20261114/.
Cizí Vocabulary EN4e5e18a70db086fa6eac083f0f9e2984 ověřené jedním programovým
čekáním:completed,3912 PASS,push+Pages confirmed,HTTP200. Nic se neopakovalo.
Dnešní health potvrzuje0f157594c8dba03b/PID77219; není to důkaz fyzického UI.


## 2026-11-14 20:05 CET — Jemnější skupiny Konspektu místně připravené

Hotovo: Knihy umí podrobnější katalogové i samostatné ruční skupiny pod oborem;
rychlé i úplné přidání, editace bez ISBN, filtr s počty a Podle skupin.

Rozhodnutí: Zůstávají26 hlavní obory, žánry a témata samostatně. Identitou
skupiny je kód; názvy pouze z vybraného MARC072$x nebo doložené mapy MZK.
606 ručních pojmenovaných kódů; nepojmenovaných10 pouze z konkrétního katalogu.
Staré v1 payloady bez groups zůstanou nezměněné; žádná hromadná migrace.

Další krok: Dokončit plnou bránu persistence a jeden místní commit.
Navrhované další kroky: Samostatně schválené p+n/fyzická přejímka, konkrétní
UI na iPhonu a potom poštovní A+C. Podrobnosti mobilního průchodu chybí.

Technický důkaz:394 cílených PASS, izolovaný skutečný browser390/1280,
včetně celého sestaveného Cockpitu a options API;0 produkčních POST/výjimek,
ruční skupina bez ISBN, clear a rychlé přidání ověřené. Plná brána probíhá.
Report reports/book_conspectus_groups_20261114.md, private důkazy ve stejnojmenné
složce data/private/. Zatím bez nového push/nasazení a fyzické iPhone přejímky.


## 2026-11-14 20:20 CET — Skupiny Konspektu místně dokončené

Hotovo: Podrobnější katalogové i ruční skupiny jsou v přidání, editaci,
kartách, závislém filtru a pohledu Podle skupin. Fungují i bez ISBN.
Kanonické předání dokončeného předchozího vydání/čištění je dorovnané.

Rozhodnutí: Žádné nové rozhodnutí; původ a kompatibilita zachované,
žádné nové p+n ani hromadné přepisování soukromých knih.

Další krok: Upřesnit konkrétní obrazovku/průchod iPhone UI; zatím chybí
Mílův popis. Pro nové knihovní skupiny je případné p+n samostatný krok.
Navrhované další kroky: Fyzická telefonní přejímka a po UI poštovní A+C;
před poštou nový čtecí audit, žádná automatická aktivace/send.

Technický důkaz:394 cílených PASS; plná brána3918 PASS/31 SKIP/767,493s.
Následné jednorádkové zpřesnění frontendového seskupení (backend beze změny)
prošlo browser390/1280 a24 frontendovými testy; finální statická brána před
commitem.0 produkčních POST/výjimek. Důkaz reports/book_conspectus_groups_20261114.md
+ privátní final_validation.json. Místní commit následuje; dosud bez nového
push/nasazení a bez fyzické iPhone přejímky. Stará data a Data worktrees zachované.


## 2026-11-14 20:48 CET — Skupiny Konspektu nasazené

Hotovo: Jemnější katalogové i ruční skupiny jsou dostupné v běžícím Cockpitu.
Rozhodnutí: Míla výslovně zadal nasazení knihovny a potom UI poštovního agenta.
Další krok: Fyzická přejímka skupin na iPhonu; vývoj pokračuje UI pošty.
Navrhované další kroky: Po UI poštovní přejímka A+C; původní čištění neopakovat.
Technický důkaz:64e9897a, jediný job3f40788ac09e6a1b24ada757ef6534c1,
Terra,3918 testů PASS/731,1s, push/deploy confirmed, smoke5/5,
chráněné služby shodné. Živý HTTPS přesně odpovídá zdroji,606 skupin přes API,
code_stamp42ad54202295bc7c/PID32060, GitHub zarovnaný. Native účtenka zkontrolovaná;
portálový returned_to_adam se nepotvrzuje. Private release_receipt.json a
release_live_verification.json v book_conspectus_groups_20261114/.
Fyzický iPhone zatím neověřený; žádná migrace knih ani změna pošty.


## 2026-11-15 08:05 CET — Cestování / místa: klidnější přehled a samostatný detail místně

Hotovo: Cestování / místa má přehled karet s fotografií a krátkým úvodem,
hledání, jeden přepínač kategorií a nabídku Přidat místo. Detail na telefonu
i desktopu ukáže místo, fotografie a poznámky; Další možnosti a údaje
obsahují původní správu, stav čtení a export. Správa fotografií je při editaci.
Zpět zachová hledání i pozici; stejný kontext zůstane po uložení úprav/stavu.
Rozhodnutí: Míla schválil navržené zjednodušení a zahájení vývoje, warp1.
Rozsah je pouze Cestování / místa; ostatní kategorie zachovávají původní UI.
Další krok: Samostatně schválené nasazení a potom fyzická přejímka na iPhonu.
Navrhované další kroky: Dříve otevřená přejímka knih a poštovní A+C zůstávají
oddělené. Další přestavba Knihovny ani nové cestovní funkce nejsou součástí.
Technický důkaz:114 cílených PASS /16,501s, sestavený celý Cockpit v izolovaném
Edge320/390/1280 bez přetékání a nechycených výjimek. Návrat, fotografie,
PDF, ochrana rozepsaného textu, uložení, chyba čtení a opožděná odpověď PASS.
Jen2 syntetické POST (stav/edit),0 produkčních POST; soukromé karty se
nepřepisovaly. Náhled čte nejvýše2048 znaků již uloženého textu a vrací
max241 znaků, kontroluje kořen archivu; fotka se odkazuje původním ID.
Žádná migrace, model, generování či aktivace. Report
reports/travel_places_ui_20261115.md; privátní důkazy travel_ui_20261115/.
Statická brána PASS; plná publikační brána až při schváleném p+n.
Tento výsledek je místní, bez push/nasazení a fyzické iPhone přejímky.


## 2026-11-15 08:10 CET — Schválené vlastní Terra p+n Cestování / místa

Hotovo: Vývojový checkpoint35b5402e je připravený k vydání,114 cílených,
statická brána i izolovaný browser320/390/1280 PASS.
Rozhodnutí: Míla výslovně zadal p+n via Terra pouze pro Willovu práci.
Balíček obsahuje35b5402e, Willův závěrečný dokumentační7d8c04e4 k minulému
vydání Vocabulary EN a tento bezpečný publikační zápis. Další Datovy větve
a nový Vocabulary obsah nejsou součástí. Cíl project-knowledge-library / cockpit.
Další krok: Jediné registrované submit_release(wait=True), potom převzetí
účtenky a čtecí kontrola živé Knihovny. Po potvrzeném vydání fyzický iPhone.
Navrhované další kroky: Původní přejímky knih a poštovní A+C zůstávají
oddělené; žádná aktivace nebo změna soukromých záznamů.
Technický důkaz:8/8 finálních zdrojů/testů stále shodných s místní přejímkou.
Request travel-places-ui-20261115-own-v1, deterministický job c67e607ca431ef10d7c0522dee0e2845.
Aktuální výsledek vydání určuje výhradně přesná privátní
data/private/travel_ui_20261115/release/release_receipt.json
a live_verification.json, nikoli tento předpublikační záznam.
Účtenka explicitně odděluje push, nasazení, ověření a fyzický telefon.
Při timeoutu či nejistotě ověřit stejný job; žádné automatické opakování.


## 2026-11-15 08:29 CET — Oprava oddělení rendereru a nové přesné vlastní vydání

Hotovo: Jediná podmínka v rendereru nejprve ověří kategorii travel_places,
a teprve potom sahá na cestovní controller. Samostatný původní test
knižních obálek tak dál funguje bez nové globální závislosti. Funkce
nového UI ani rozsah se nerozšiřují.64 knižních/frontendových testů
PASS/17,073s a znovu celý browser320/390/1280 včetně nového draftu PASS.
Rozhodnutí: Pokračování stejného Mílou schváleného p+n via Terra jen
Willova balíčku. Datovy další větve zůstávají mimo.
Další krok: Po statické bráně a lokálním checkpointu nové jediné registrované
vydání opraveného headu; potom ověřit živý Cockpit a fyzický iPhone.
Navrhované další kroky: Původní přejímky knih a poštovní A+C odděleně.
Technický důkaz: Původní jobc67e607ca431ef10d7c0522dee0e2845 skončil attention;
3922 testů/53 SKIP, jediný FAIL test_online_cover_sources_and_backlink_behavior
s ReferenceError libraryTravel v izolovaném Node rendereru. Plná brána
ukončená, žádný timeout. Čerstvý registrovaný GitHub audit doložil stále
e780fe98,3 vlastní pending commity; runtime PID72316/stamp42ad54202295bc7c
beze změny. Push tedy nebyl proveden a nasazení nezačalo; původní účtenka
a first_gate.log jsou zachované v privátním travel_ui_20261115/release/.
Nová oprava vyžaduje novou identitu: request travel-places-ui-20261115-own-v2,
jobfff30ae477f38401ae8e582208e9a582. Výsledek výhradně z privátní
travel_ui_20261115/release_v2/release_receipt.json + live_verification.json.
Žádný resubmit původního jobu, změna časových limitů nebo vynechání testů.


## 2026-11-15 09:04 CET — Úplná diagnostika zelená, p+n čeká na servisní rozhodnutí

Hotovo: Opravený zdrojda1ee2bc prošel celou nezměněnou kanonickou sadou
v témže profilu Knihovny:3922 testů,0 failures/errors,31 SKIP. Testová část
822,728s; import5,669s; příprava syntaxe9,3s a jednotkový krok829,2s.
Všech8 finálních zdrojů/testů odpovídá zmrazeným otiskům opravy.
Rozhodnutí: Žádné rozšíření schváleného rozsahu UI; čeká se na samostatné
rozhodnutí Míly o servisní opravě limitu900→1500s a řízeném načtení po plné
bráně. Návrh zatím není aplikovaný. Další publikační pokus se nespouští.
Další krok: Rozhodnutí o servisní opravě; teprve poté dokončit registrované
Terra p+n a ověřit živý Cockpit.
Navrhované další kroky: Po potvrzeném vydání fyzický iPhone; poštovní A+C
a přejímka knih odděleně.
Technický důkaz: v2 fff30ae477f38401ae8e582208e9a582 skončil attention
po přibližně15min, nový gate log se nezapsal. Spolu s pevným900s limitem
a jeho větví TimeoutExpired to odpovídá vypršení času, ne novému doloženému
FAIL. Úplná samostatná brána s --unit-test-timings následně PASS. První
FAIL knižního rendereru z v1 je opravou64 testů a touto úplnou sadou uzavřený.
Čerstvý registrovaný GitHub audit pořád e780fe98; runtime PID72316 a stamp
42ad54202295bc7c beze změny. Push ani nasazení tedy neproběhly.
Privátní důkazy: travel_ui_20261115/release_v2/diagnostic_gate.log,
diagnostic_timings.json, release_receipt.json, source_manifest.json.
Servisní proposal.patch je pouze návrh mimo Git; nezměněná publikační
brána se neobchází a testy se neškrtají.
