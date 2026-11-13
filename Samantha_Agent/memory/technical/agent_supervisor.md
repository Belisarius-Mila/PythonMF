# Místní dohled nad agenty

Pracovní proud: `project-samantha-infrastructure`. První verze 2026-11-13.
Jde o deterministický dohled bez AI, nikoli o změnu architektury App Serveru.

## Rozsah a stav

Implementováno a 13.11. vydáno v fb062e34: pošta, Cockpit, sdílený App Server, autosave a SSD.
P+n potvrzuje účtenka f414b8d3c33e18033b65f00375a40559; živý panel a GET200 ověřené.
Aktuální provoz13.11.: vlastní služba je nainstalovaná, načtená a aktivní po
přesné globální větě. Dvě vlastní Pushcut oznámení jsou připojená a zapnutá;
první skutečné SSD varování09:32 UTC accepted1. Míla potvrdil doručení
varování na iPhone a přístup do přehledu Servis → Provoz. Zvuk a oznámení
obnovy zatím nejsou výslovně potvrzené; skutečná obnova dosud nenastala.
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
