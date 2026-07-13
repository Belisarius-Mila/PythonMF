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
- Nasazeny rucni retest opravene varianty z iPhonu vratil spravny kontrolni kod
  z capsule misto starsiho kontrolniho slova. Predani Context Capsule je timto
  funkcne potvrzene.
- Izolovany Cockpit LAB panel umi zobrazit registr, zalozit pojmenovanou relaci,
  explicitne prepnout relaci a upravit/ulozit capsule.
- Vyber relace pouziva app-server `threadId`; stale plati sandbox `read-only` a
  approval policy `never`.
- Automaticke testy overuji oddeleni dvou relaci, idempotenci, lifecycle,
  migraci stareho stavu, limity capsule, jeji revizi v odchozim turnu a prave
  jednu user polozku.
- Cockpit quality gate dokoncil 636 testu bez chyby. Samostatny Node syntax check
  overil vysledny JavaScript.
- HTTP smoke test na docasnem portu nacetl nove ovladaci prvky a stavajici
  private stav jako schema v2. Neodeslal zpravu, nevytvoril novy realny thread a
  nevypsal soukromy obsah.

Co neni hotove:
- Mila rucne overil z iPhonu zachovani puvodni historie, zalozeni druhe relace,
  navaznost, oddeleni relaci, pet casu, prepinani, disconnect a resume. Tyto
  casti prosly.
- Mila pri retestu hlasil pomaly start Cockpitu pres Tailscale, priblizne 40 s,
  a pomale otevreni LAB panelu. Mereni ukazalo, ze Tailscale transport byl rychly
  (spojeni radove 2 ms, hlavni HTML kolem 10 ms); zdrzeni bylo v lokalnim
  lifecycle/status kodu.
- Supervisor po ukonceni serveru testoval port bez `SO_REUSEADDR`, a proto mohl
  `TIME_WAIT` povazovat za zivy obsazeny port a cekat v 10s cyklech. Port probe
  v supervisoru i launcheru je opraveny, restart health limit zvysen z 12 na
  25 s a testy nove zahrnuji i restart modul.
- LAB status opakovane spoustel `codex --version`, coz stabilne stalo asi 0,33 s.
  Nemenna verze se nyni po prvnim uspesnem zjisteni cacheuje.
- Oprava je nasazena vcetne noveho launchd supervisoru. Cisty plny restart vratil
  Cockpit se spravnym code stampem za 2,58 s. Prvni LAB status po restartu trval
  0,356 s a druhy po naplneni cache 0,0016 s. Pres aktualni Tailscale listener
  trvalo nacteni hlavniho HTML 0,011 s, health 0,0031 s a zahraty LAB status
  0,0036 s. Porty 8771 a 8877 zustaly volne.
- Pro cestovni brainstorming vznikla oddelena private LAB relace s Context
  Capsule a TVBCP strukturou odpovedi. Kazda dokoncena vymena ma explicitni
  tlacitko `Ulozit do TVBCP`; server uklada otazku, odpoved a tema z vlastni LAB
  historie do stavajiciho private TXT. Opakovany klik je idempotentni a nic se
  neuklada automaticky. VoiceBridge ani watcher se tim nezapina.
- Hlavni `/api/status` stale trva priblizne 1,1-1,4 s; nejpomalejsi byla zmrazena
  VoiceBridge status vetev kolem 0,7 s. V teto davce nebyla menena, aby zustal
  dodrzeny freeze mimo novy LAB a presne ohranicenou lifecycle opravu.
- Zatim neni editace nazvu, archivace ani mazani relaci. Nic se nema mazat bez
  noveho vyslovneho rozhodnuti.
- LAB stale neni finalni plnohodnotny chat Janicky. Hlas a TVBCP zustavaji
  samostatne pozdejsi vrstvy.

Dalsi krok:
- Z iPhonu overit rychlost Cockpitu/LAB a u jedne vecne vymeny tlacitko
  `Ulozit do TVBCP`, nasledne otevrit TVBCP panel a potvrdit novy zaznam.

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
