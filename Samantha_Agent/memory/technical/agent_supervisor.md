# Místní dohled nad agenty

Pracovní proud: `project-samantha-infrastructure`. První verze 2026-11-13.
Jde o deterministický dohled bez AI, nikoli o změnu architektury App Serveru.

## Rozsah a stav

Implementováno a 13.11. vydáno v fb062e34: pošta, Cockpit, sdílený App Server, autosave a SSD.
P+n potvrzuje účtenka f414b8d3c33e18033b65f00375a40559; živý panel a GET200 ověřené.
Aktuální provoz13.11.: vlastní služba je nainstalovaná, načtená a aktivní po
přesné globální větě. Dvě vlastní Pushcut oznámení jsou připojená a zapnutá;
skutečné SSD varování09:32 UTC a automatická obnova10:32:58 UTC mají obě
API accepted a Míla potvrdil doručení na iPhone. Celý skutečný cyklus je
přijatý. Přehled i odkazy ověřené; další úklid Míla odložil. Vnější hlídač chybí.
Pravidelná služba i oznámení jsou výchozím stavem vypnuté. Vývoj nepovoluje
nasazení, instalaci LaunchAgentu, zapnutí oznámení ani externího hlídače.
Soví automatika, ScienceNews, recovery správce a ostatní služby se nemění.

Samostatný jednorázový proces má interval120 sekund a nepoužívá Cockpit jako
plánovač. `GET /api/agent-supervisor/status` a `status` čtou pouze vlastní
uložený snímek. Po300 sekundách bez čerstvé kontroly se řádky zobrazí jako
neověřené; stará zelená není provozní důkaz. Ruční snímek není doklad
pravidelně běžícího workeru.

## Signály

- Pošta: skutečné enabled/installed/owned/loaded a heartbeat do300 sekund;
  úplný scan všech vybraných účtů se stejnou UID epochou. Dokončený slot
  nenahrazuje zdrojový důkaz. Tolerance nového hodinového scanu15 minut,
  provoz07–22 Europe/Prague. Delší práce je `working` jen s doloženým PID
  poštovního workeru; po45 minutách `warning`. Noční okno ani vědomé vypnutí
  pošty se nevydávají za chybu scanu.
- Cockpit: pevný loopback `/api/server/health`, bounded GET bez proxy,
  přesměrování či obchodních dat.
- App Server: připojení na existující sdílený Unix socket a čtecí katalog
  modelů; bez startu procesu, thread/start, turn/start nebo modelového tahu.
- Autosave: právě jeden watcher, čerstvost metadat do20 minut, poslední chyba.
  Nečte obsah nouzových session logů.
- SSD: varování pod30 GiB, kritický stav pod15 GiB; žádný úklid.

Stavy: ok / working / warning / error / unknown / disabled / outside_hours.
Každý řádek uvádí důvod, čas kontroly, poslední doložený úspěch a další termín.
Výjimka jedné sondy nezastaví zbývající sondy; její text se nepersistuje.

## Registry a použití

- `agent_supervisor_status`: `.venv/bin/python scripts/agent_supervisor.py status`
- `agent_supervisor_check`: stejné CLI `check --confirmed`; ukládá vlastní
  redigovaný snímek, nikdy neposílá oznámení a nemění incidenty plánovače.
- `agent_supervisor_tick`: stejné CLI `tick`; bez opt-in končí před sondami
  i zápisem. Při aktivaci používá předem schválenou konfiguraci.
- `agent_supervisor_service_preview`: stejné CLI `service-preview`; neinstaluje.
- Pythonové konfigurace/instalace mají vlastní capability záznamy v registru.
- V Cockpitu Servis → Provoz → Dohled nad agenty. Obnovit přehled je pouze GET.
  Použitý existující minutový refresh; žádná nová browserová monitorovací smyčka.

## Persistence a oznámení

Vlastní soukromý kořen `data/private/agent_supervisor/`: config.json,
state.json, installation.json, zámky a scheduler logy. Do Gitu nepatří.
Konfigurace má verzi1; neznámá nebo poškozená verze se nepřepisuje výchozími daty.
GET ani veřejná účtenka neobsahují webhooky, raw výjimky, adresy, texty zpráv
nebo příkazové řádky procesů. Současný poštovní namespace je jen čtený.

Incident drží stabilní identitu od zjištění problému do skutečné obnovy.
Severity/reason aktualizace nevytváří další varování. Současně zjištěné
výpadky se sdruží do jednoho POST; totéž platí pro souběžné obnovy.
Před síťovým požadavkem je trvale uložené `sending`. Neznámý výsledek,
pád po odeslání či chyba zápisu dokončení znamenají `delivery_unknown`;
žádný automatický resend. Neodeslaný starý podnět po změně situace se potlačí.
Obnova se oznamuje jen po potvrzeném přijetí původního varování a skutečně
obnoveném úspěchu. Rozběhnutí workeru ani stav working incident neuzavírají.
Worker i změna konfigurace používají společný procesní zámek.

Pushcut potřebuje dvě vlastní předem připravená oznámení a dva různé webhooky:
„Dohlížitel hlásí problém. Otevři Servis.“ a „Dohlížitel zaznamenal obnovu.
Otevři Servis.“ Odkaz má vést do soukromého Cockpitu `/#servis`.
Text neříká, že všechny služby jsou zdravé, když se obnovila jen jedna.
Stávající poštovní webhook ani jeho pevný text se nepřebírají.

Samostatně potvrzené `AgentSupervisor.configure` přijímá enabled,
notifications_enabled, failure_url, recovery_url a confirmed=True. Webhooky
se předávají pouze z privátní konfigurace, nikdy v argv, chatu, reportu či Gitu.
Vypnutí konfigurace neukončuje ani neopakuje žádnou sledovanou práci.

## Instalace a aktivace — zvlášť po nasazení

`SupervisorService.preview()` zmrazí manifest čtyř provozních souborů a
LaunchAgent definici. První `install(approved_digest=..., confirmation=...)`
vyžaduje přesnou větu z global_safety_brake.md a shodný zdrojový digest.
Pouze vlastní nová definice, žádný přepis cizího plist. Trvalá instalační
účtenka existuje před bootstrapem; nejistý nebo předchozí bootstrap se
neodesílá znovu. Instalační aktivace ponechá oznámení vypnutá. Teprve pozdější
samostatný opt-in smí povolit dva konkrétní Pushcut webhooky.

Vývojové smoke podklady patří výhradně do oddělené privátní složky
agent_supervisor_devcheck_20261113, nikoli do produkčního namespace.

## Vnější hlídač — dosud nenastavený

Lokální proces nemůže sám ohlásit vypnutý Mac či úplný výpadek připojení.
Rozhraní proto tuto hranici viditelně přiznává (`external_watchdog=not_configured`).
Navazující samostatně schválená integrace má z jiného dostupného stroje či
služby hlídat pravidelný provozní signál z Macu, po vyhodnocení místních sond.
Posílat pouze technický stav/identitu a čas; žádné schránky, obsahy ani logy.
Nevytváříme účet, nevystavujeme privátní HTTP endpoint a neposíláme žádný ping.

## Přejímka

Izolované testy: starý heartbeat, starý/částečný scan, jiná epocha, noční
okno, živá dlouhá práce, budoucí čas, souběžné workery, restart incidentu,
nejisté odeslání, selhání persist po send, zastaralá obnova, vlastní/cizí plist,
nejistý bootstrap bez retry, redakce a pouze čtecí HTTP. Skutečný iPhone,
aktivovaný LaunchAgent, ostrý Pushcut a výpadek celého Macu zůstávají otevřené.

Názvy aktuálních oznámení: SamanthaDohledProblem a SamanthaDohledObnova.
Druhá URL může být při stejném účtu sestavená z již soukromě získané první
URL a přesného názvu podle dokumentace Pushcutu; nepřenášet secret do chatu
ani žádat znovu Copy URL kvůli rozdílným schránkám zařízení. Samotná syntaxe
URL neprokazuje HTTP přijetí nebo fyzické doručení obnoveného oznámení.

Skutečná automatická přejímka13.11.: SSD26,44 → přibližně30,12 GiB po
uživatelem provedeném uvolnění. Původní incident automaticky uzavřený,
jedna obnova přijatá API a uživatelem potvrzená na iPhonu. Žádná simulace,
změna prahu ani ruční recovery POST. Další úklid se nyní neprovádí.


## 2026-11-14 07:52 CET — Noční spánek a potvrzení trvajícího problému

Míla výslovně schválil opravu a bezprostřední Terra p+n v proudu
project-samantha-infrastructure. Předání používá centrální release_executor
a jediné app.communication.luna_release.submit_release(wait=True), bez
nativního pomocníka. Terra je schválená preferovaná role; při auditu musí
být vybraná právě gpt-6.1-terra/high, žádný tichý fallback na Lunu.

Příčina: Lokální LaunchAgent běží i při krátkých systémových DarkWake.
Před ranním otevřením Macu14.11. přijal Pushcut8 oznámení (10 agentových
událostí), hlavně starý heartbeat pošty a autosave. Záznam OS04:32:11
DarkWake a události04:32:14 dokazují časovou vazbu. Noční kontrola pošty
byla až za kontrolou stáří heartbeatu, takže záměrné neprovádění scanu
vytvářelo nové incidenty. Autosave má600s cyklus, který musí po spánku
dostat čas na skutečné obnovení. Vnější hlídač není nakonfigurovaný.

Oprava:
- Pošta23–07 Europe/Prague nejprve vyhodnotí outside_hours; starý/chybějící
  heartbeat ani nečerstvý scan samy v noci nevyhlásí závadu.
- Čtecí pmset -g systemstate rozliší plné probuzení (Graphics) od DarkWake;
  kern.waketime doplní čas probuzení. Žádná změna uspávání, sítě či víka.
  Při spánku/údržbě nebo neověřené power sondě neprobíhají síťové sondy
  a neodesílá se problém ani obnova. Panel stav viditelně označí Pozastaveno.
- Trvalá pěti­minutová ochrana po probuzení, prvním běhu nebo delší mezeře.
  Restart workeru ani opakovaný polling tuto lhůtu nezkrátí/neprodlužuje.
  Autosave má navíc až15 minut na svůj desetiminutový cyklus; skutečný
  čerstvý úspěch jej může vrátit dříve po společné pěti­minutové ochraně.
- Nové varování až po souvislém problému alespoň90s (při120s periodě dvě
  skutečné kontroly). Stejný čas/dvojí klik nestačí. Krátký výpadek nemá
  varování ani falešnou obnovu. Working/noční klid/spánek čítač přeruší.
- Otevřené incidenty se během spánku neuzavírají a nevytváří se obnova.
  Zachované identifikátory a accepted/delivery_unknown; neprovádí se resend.
  Pending před spánkem potřebuje čerstvé potvrzení po obnovení provozu.
- Nové pozastavené řádky se na disk zapisují jako dříve známé unknown/
  unavailable plus whitelisted pause_code. Starší běžící Cockpit je stále
  přečte; nový reader zobrazí přesný důvod. Žádná falešná zelená.

Ověření:71 cílených testů PASS, Node panel včetně Pozastaveno a redakce PASS.
Regrese zahrnují starý/noční/chybějící/budoucí heartbeat, DarkWake bez sond,
noční opakování, restart během grace, krátký spánek mezi dvěma tiky,
mezery, neověřený power stav, trvalý i krátký výpadek, ochranu autosave,
pending send a skutečnou obnovu. Živá nová OS sonda pouze čtecí: awake,
čas normálního otevření víka souhlasí s pmset logem. Testy používají vlastní
dočasné archivy a syntetického sendera; žádné ostré testovací Pushcut POST.
Konečná plná brána: 3876 testů/31 skip v izolaci (668.4s): pouze1 chyba nezměněného recovery CLI bootstrapu mimo kanonický projekt; stejný test v kanonickém prostředí PASS. Nové testy dohledu PASS; úplná kanonická publikační brána následuje u Terry.

Vývoj proběhl v samostatném vlastním worktree, Data se nemění. Při integraci
je použit existující worker zámek proti načtení neúplné sady souborů.
Definice LaunchAgentu ani nastavení Pushcutu se nemění; žádný bootstrap,
reinstalace, vypnutí sledovaných služeb či úprava soukromých incidentů ručně.
Všechny existující soubory a účtenky zůstávají zachované.

Další krok: Lokální commit a již schválené jediné Terra p+n; konečná provozní
účtenka je mimo Git v logs/agent_supervisor_sleep_release_20261114.log.
Po vydání ověřit GitHub SHA, health/nové UI, čerstvý scheduled tick a stejnou
vlastněnou službu/config. Další skutečná noc je fyzická přejímka; automaticky
Mac neuspávat. Bez samostatného pokynu nenastavovat žádný vnější dohled.

Technické zdroje: https://github.com/apple-oss-distributions/PowerManagement/blob/main/pmset/pmset.m
(System Capabilities) a https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/pwr_mgt/IOPM.h
(Graphics0x02). Provozní cesta je lokální Mac; GitHub uchovává kód a Pushcut
doručuje oznámení.

Doplňující QA: Skutečná noční OS časová osa64 Sleep/DarkWake/Wake přechodů
přehraná do syntetických zdravých služeb a desetiminutového autosave:266
kontrol,203 pozastavených,0 falešných oznámení. Produkční incidenty/config
se neměnily,0 skutečných Pushcut POST. Doklad
logs/agent_supervisor_sleep_replay_20261114.log (nenahrazuje další fyzickou noc).

Omezení izolované brány: Jediný nezměněný test recovery CLI bootstrapu
v oddělené kopii vrátil attention/ValueError. Tentýž test v kanonickém
projektu bez úpravy kódu prošel; neobchází se žádná aktivace a nekopírují
se privátní data. Doklad logs/agent_supervisor_sleep_canonical_environment_test_20261114.log.
Plnou kanonickou bránu nad přesným commitem musí před push/deploy dokončit
registrovaná Terra; konečná provozní účtenka zůstává mimo Git.
