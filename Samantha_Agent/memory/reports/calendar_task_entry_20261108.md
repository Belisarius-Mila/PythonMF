# Rychlé zadání kalendářového úkolu

Stav 2026-11-08 11:54 CET: lokální vývoj hotový, bez push/nasazení nové karty.
Proud project-cockpit; stávající kanonický handoff/TVBCP aktualizované.
Předchozí agenda je živě nasazená v 6d5b576b, nový vývoj se s ní nesměšuje.

## Přijaté ovládání

- Komunikace → Kalendář → Zadání úkolu; samostatná karta /calendar/task/.
- Jediné pole Název, popis, místo: celý text v názvu (do 400 znaků podle
  současné čtečky). Diktování řeší systémová klávesnice iPhonu. Bez AI.
- Den, měsíc, rok předvyplněné podle dne v Europe/Prague, samostatný
  viditelný Čas s výchozí hodnotou 09:00. Míla výslovně požadoval možnost
  hodinu změnit. Délka se nezadává; jde o termín úkolu, nikoli schůzku.
- Jedno Zapsat úkol potvrzuje aktuální data i zobrazený existující cíl.
  Alarmy 1440/60 minut. Po ověřeném výsledku se vyčistí text, datum/čas
  zůstanou pro další zadání; nové otevření nabízí 09:00.
- Manifest s oddělenou identitou/start_url přímo na kartě, vlastní SVG
  a apple-touch PNG 180×180. Žádný Service Worker ani offline fronta.
  Přidání ikony provede Míla jednou přes Safari; používá stávající síťový
  přístup ke Cockpitu, nová síť/klient/služba se nezřizuje.

## Zápis a obnova

CalendarTasks ukládá každé zadání do data/private/calendar_tasks/<ID>/state.json.
Před nativní akcí persistuje původní input, přesnou operation_id a event.
Stejný ID nelze přesměrovat na jiný obsah. Dvojklik, souběh či restart
nevytvoří druhý event. Uživatelův prohlížeč uchová rozpracované zadání
před odesláním; po ztrátě odpovědi/obnovení stránky čte pouze stav.
Neznámý výsledek uchovává text a zamyká změny; Ověřit zápis používá
pouze nativní recover. Nenalezený požadavek lze po ručním kliknutí odeslat
jen pod stejným ID a s přesně stejným obsahem.

Původní podepsaný CalendarWriter se nemění. Právě jeden create, event
s minutovým intervalem pro deadline, title obsahuje celý text, location
zůstává prázdné. Existenci cíle a skutečný write access hlídá EventKit.
Výběr je připnutý revizí/ID a zamčený po dobu nativního kroku. Úkoly
nevyžadují kolizní schválení schůzek. Jeden následující read-only recover
v rámci původního kliknutí řeší známé opožděné eventIdentifier; nevytvoří
další záznam a nerozběhne model. Vše nadále používá stejný OS grant.

Po ověření uložení se mimo zámky obnoví agenda, interně mimo 60s cooldown,
se zachováním single-flight. Duplicitní potvrzený request refresh neopakuje.
Typ task_deadline přebírá agenda z ověřené účtenky přes přesný obsahový klíč.
Starší neznámé události se nadále nehádají. Nedostupné/dvojznačné DST časy,
neplatné datum, minulost, změněný cíl či chybějící helper nevedou k zápisu.

## Důkazy a hranice

- 378 cílených testů PASS: logs/calendar_task_targeted_20261108.log.
- Poslední úpravy mobilních okrajů, chybových zpráv a prázdného textu:
  5 HTTP/UI testů PASS, logs/calendar_task_final_ui_20261108.log.
- Plná brána: 2923 testů OK (31 SKIP); logs/calendar_task_gate_20261108.log.
- Finální statická brána: logs/calendar_task_static_20261108.log.
- Skutečný pouze čtecí kontext: cíl připraven, 09:00, reader/writer build
  ověřený, žádné vytvoření task úložiště, žádný event/model/OS dialog.
  logs/calendar_task_live_read_20261108.log.
- HTTP testy mají izolované FakePilot/TaskWriter: skutečné Host/Origin
  ochrany a route, query rejection, ikonové PNG/manifest/start_url, jeden
  create a následný status. Node skutečného modulu ověřuje čas, datum,
  opakování/timeout/restart, uchování textu a obnovu původní identity.
- Vzhled ikony zkontrolovaný. Browser host unavailable a nativní Safari
  cgWindowNotFound znemožnily fyzickou Mac/iPhone přejímku. Syntetický
  QA server ukončený, žádná karta se nevytvořila, fixture zachované.
- Skutečný kalendářový zápis touto novou kartou nebyl proveden. Není to
  přejímka iPhone diktování, připomenutí na zařízení či ikony na ploše.

Další krok: samostatně schválit p+n, pak Mílův skutečný úkol a přidání
ikony v Safari. Nasazení není součástí nynějšího pokynu k vývoji.

Přesný lokální commit, počet čekajících commitů a zarovnání profilů jsou
v závěrečném logs/calendar_task_final_verified_20261108.log. Dřívější
měsíční přehled zůstává nasazený; nový vývoj zatím pouze lokálně.
