Nazev: App-server LAB - Thread Registry a Context Capsule
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-13

Co se resilo:
- Navazalo se na overeny single-thread read-only LAB nad `codex app-server`.
- Cilem bylo umoznit dve a vice oddelenych textovych relaci bez prepisovani
  historie a pridat kratky rizeny kontext bez kopirovani chatoveho fulltextu.
- Zmrazeny VoiceBridge, watcher, Janicka, hlas, TVBCP a zbytek Cockpitu nebyly
  v teto davce meneny.

Co je hotove:
- Soukromy LAB state ma schema v2 s registrem nejvyse 12 nove zakladanych relaci,
  stabilnim lokalnim `registry_id`, app-server `thread_id`, lidskym nazvem/roli,
  poctem turnu, poslednim dokoncenym turnem a oddelenou historii/lifecycle.
- Puvodni single-thread state se pri dalsim ulozeni nedestruktivne prevede na
  prvni registrovanou relaci; dosavadni zpravy a lifecycle zustavaji zachovane.
- Context Capsule ma ohranicena pole `cil`, `aktualni stav`, `dalsi krok` a
  nejvyse sest kratkych omezeni. Skutecny obsah se uklada pouze do
  `data/private/appserver_lab/`, nikdy do gitu.
- Prvni implementace zkousela capsule predavat pres `developerInstructions` pri
  `thread/resume`. App-server parametr formalne prijal, ale rucni test dvakrat
  vratil udaj ze stare historie misto udaje z capsule; tento kontrakt tedy nebyl
  spolehlivy a byl nahrazen.
- Opravena varianta pridava aktualni capsule jako kompaktni aplikacni JSON kontext
  primo k jednomu textovemu user itemu kazdeho dalsiho `turn/start`. V lokalni
  historii a UI zustava jen puvodni Milova zprava; nepridava se druhy user item,
  skryty turn ani chatovy fulltext.
- Izolovany Cockpit LAB panel umi zobrazit registr, zalozit pojmenovanou relaci,
  explicitne prepnout relaci a upravit/ulozit capsule.
- Vyber relace pouziva app-server `threadId`; stale plati sandbox `read-only` a
  approval policy `never`.
- Automaticke testy overuji oddeleni dvou relaci, idempotenci, lifecycle,
  migraci stareho stavu, limity capsule, jeji revizi v odchozim turnu a prave
  jednu user polozku.
- Cockpit quality gate dokoncil 630 testu bez chyby. Samostatny Node syntax check
  overil vysledny JavaScript.
- HTTP smoke test na docasnem portu nacetl nove ovladaci prvky a stavajici
  private stav jako schema v2. Neodeslal zpravu, nevytvoril novy realny thread a
  nevypsal soukromy obsah.

Co neni hotove:
- Mila rucne overil z iPhonu zachovani puvodni historie, zalozeni druhe relace,
  navaznost, oddeleni relaci, pet casu, prepinani, disconnect a resume. Tyto
  casti prosly.
- Ceka se na jediny rucni retest opraveneho primeho predani capsule v dalsim
  turnu; restart LAB app-serveru uz k aplikaci capsule neni potreba.
- Pri kontrolovanem plnem restartu Cockpitu se stary proces bezpecne ukoncil,
  ale automaticky start se kvuli prechodne obsazenemu portu nedokoncil. Standardni
  start Cockpit obnovil. Toto male restart/port race riziko zustava k pozdejsi
  samostatne oprave; netyka se tlacitka `Restartovat LAB app-server`.
- Zatim neni editace nazvu, archivace ani mazani relaci. Nic se nema mazat bez
  noveho vyslovneho rozhodnuti.
- LAB stale neni finalni plnohodnotny chat Janicky. Hlas a TVBCP zustavaji
  samostatne pozdejsi vrstvy.

Dalsi krok:
- Po nasazeni opraveneho kodu v existujici `LAB B` polozit jednu jednoznacnou
  otazku na kontrolni kod z capsule. Karta zpravy ma ukazat revizi capsule a
  odpoved ma pouzit capsule, ne starsi kontrolni slovo z historie.

Navrhovane dalsi kroky:
- Po uspesnem rucnim testu doplnit maly restart-Mac/Cockpit recovery test.
- Teprve potom navrhnout prvni plnohodnotny textovy chat Janicky bez VS Code.
- Hlasove nahravani/prepis/prehrani a TVBCP pridavat oddelene nad timto
  overenym transportem.

Zmenene nebo relevantni soubory:
- `app/codex_appserver_lab.py`
- `app/cockpit.py`
- `tests/test_codex_appserver.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Necommitovat `data/private/`, LAB state, texty zprav a odpovedi, runtime
  thread/turn ID, autosave, `.env`, tokeny ani API klice.
- Capsule se technicky stava soucasti private app-server vstupu kazdeho turnu,
  ale neuklada se do gitove pameti ani se nezobrazuje jako Milova zprava v UI.
- Handoff zamerne neobsahuje text existujici soukrome LAB konverzace ani runtime
  identifikatory.
- Stary VoiceBridge zustava fail-closed a watcher vypnuty; tato davka ho znovu
  nezapina ani nemeni.
