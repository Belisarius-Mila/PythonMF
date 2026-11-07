# Kalendářový bod 2 — výběr a čtecí přehled

Datum: 2026-11-07, terminálový Will na main. Proud project-email-cases.

## Uživatelský výsledek

Cockpit → Kalendář, /calendar/. Soukromý výběr čtených kalendářů a odděleného
budoucího cíle zápisu; výchozí výběr je prázdný. Výběr se nezaměňuje za oprávnění
vytvářet události. Otevření stránky pouze čte uložený snímek; explicitní Obnovit
načte inventář a jen vybrané události na nejbližších 30 dní. Uložit výběr a načíst
uloží nastavení s kontrolou revize a načte nový snímek.

Zobrazuje název události, interval, celodenní rozsah, kalendář a čas posledního
načtení. Časy v Europe/Prague; celodenní data mají vlastní lokální datum a výlučný
konec. Názvy se vkládají přes textContent. Poznámky, účastníci, přílohy, těla,
lokace a odkazy se neexportují. Data ani soukromý snímek se neposílají modelu.

## Chybové stavy a persistence

Žádné vybrané ID znamená nula načtených událostí, nikdy EventKit calendars:nil.
Chybějící kalendář, neúplný limit 2000 událostí, odebrané oprávnění, chybná
odpověď či timeout nesmí tvrdit aktuálně ověřený přehled. Poslední známé události
smějí zůstat vidět jen pro přesně stejnou revizi výběru a s neaktuálním stavem.
Snímek po 15 minutách přestává být aktuální, také v již otevřené stránce.
Prázdný přehled není důkazem volného času. Kontrola konkrétních kolizí přijde
v další etapě. Kalendářové nastavení se ukládá atomicky pod vlastním zámkem,
starší revize nesmí přepsat novější výběr. Kalendář, který není zapisovatelný,
nelze zvolit jako budoucí cíl. Služba se trvale neinstaluje.

## Nativní přejímka a otevřená hranice

Rozšířený podepsaný EventKit helper se skutečně sestavil a prošel 4 nativními
syntetickými kontrolami. Nové ad-hoc sestavení má jiné cdhash. Skutečné spuštění
v jednorázové user launchd úloze s ověřeným rodičem PID 1 vrátilo
not_determined / authorization_required. Úloha byla odstraněna, žádný nový OS
dialog nebyl automaticky spuštěn. Starší sestavení i grant/request důkazy jsou
zachované ve vlastní aplikační složce. Grant se nikdy nedovozuje z původního
CLI kontextu ani z jiného binárního souboru. Nové GUI žádosti mají trvalou
identitu pro přesný binární otisk, nejistý start se automaticky neopakuje.
Původní CLI authorize/probe používá kompatibilně grant aktuálního sestavení.

Mílův další krok po nasazení: Kalendář → Povolit přístup na Macu, potvrdit OS
dialog na stejném Macu, Obnovit kalendáře, vybrat čtené kalendáře a případný
budoucí cíl, Uložit výběr a načíst. Potom porovnat několik skutečných událostí
s Kalendářem na Macu a iPhonu. Tato fyzická přejímka a skutečné čtení vybraných
událostí nejsou provedené. Nový grant si musí potvrdit Míla; jeho dřívější
souhlas se nepřenáší manipulací TCC nebo podpisu.

## Důkazy a vydání

87 cílených testů PASS: nativní kontrakt, soukromé nastavení, HTTP/origin,
souběžná revize, restart, stale snapshot, chybějící kalendář, timeout, odebrané
oprávnění, omezený výsledek a browserová ochrana obsahu. Browserový kontrakt
ověřuje také celodenní konec přes změnu letního času a zachování rozepsaného
výběru. Skutečná Safari přejímka proběhla nad izolovanými umělými daty, včetně
výběru a uložení; není to přejímka reálných kalendářů nebo iPhonu.

Vývojová plná brána: 2700 testů / 31 SKIP, bez selhání PASS (576,140 s unit část).
Poslední rozšíření nativního kontraktu a pevných časových posunů má cílené
ověření; finální zmrazený commit znovu celý ověří povinná publikační brána Terry.

Logy: calendar_overview_targeted_20261107.log, calendar_overview_build_20261107.log,
calendar_overview_native_20261107.log, calendar_overview_full_gate_20261107.log.
Míla autorizoval okamžité Terra p+n po dokončení. Přesný konečný stav určuje
logs/calendar_overview_release_20261107.log a calendar_overview_verified_20261107.log,
ne tento předběžný vývojový zápis. Samostatný nový TVBCP nebyl domluvený.
Hodinová e-mailová kopie, business stav, modelové role a Datův worktree se nemění.
Bez modelového posuzování, mikrofonu a placeného hlasového probe.

Registrované CLI: scripts/calendar_overview.py status / refresh --confirmed /
authorize --confirmed; vypisuje pouze agregáty. UI API je pod existujícími
Cockpit Host/Origin a no-store pravidly. /api/calendar/action má vlastní
COCKPIT_POST_ACTIONS registraci; schopnosti i shellová workflow jsou v registrech.

Primární API podklad: [Apple — EKEvent](https://developer.apple.com/documentation/eventkit/ekevent)
a [Apple — přístup ke kalendáři](https://developer.apple.com/documentation/eventkit/accessing-calendar-using-eventkit-and-eventkitui).
