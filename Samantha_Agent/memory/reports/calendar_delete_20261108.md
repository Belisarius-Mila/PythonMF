# Jednotlivé mazání události z Cockpitu — lokální vývoj

Proud `project-cockpit`; Míla 8. 11. schválil vývoj návrhu tlačítka Smazat
z kalendáře, přesného potvrzení a mazání jen jednoho výskytu. Tento pokyn
neobsahuje nové p+n ani povolení mazat skutečné testovací události.

## Chování

- Smazat z kalendáře u schůzek/termínů v měsíční agendě, v seznamu Kalendáře
  a po ověřeném zápisu rychlého úkolu nebo události z e-mailu.
- Nejprve nativní čtecí náhled konkrétní události, potom krátké potvrzení
  s názvem, kalendářem a začátkem. U opakování výslovně jen jeden výskyt.
- Po ověřeném smazání se přehled obnoví. Úspěch smazání se nepřeklápí na
  nejistotu kvůli následnému selhání refresh.
- Při změně nebo duplicitě se nemazá. Kalendář musí být vybraný pro čtení
  nebo být současným cílem zápisu a musí dovolovat změny. Revize výběru
  je připnutá; náhled platí pět minut.
- Pozvánky s účastníky nebo organizátorem jsou v této verzi odmítnuté;
  odkazují na aplikaci Kalendář. Neřeší se rozesílání zrušení/odmítnutí.

## Ochrany

Nový `CalendarDeleteHelper` je oddělená podepsaná aplikace. Původní reader,
create-only writer, jejich zdrojové i binární otisky a soukromé žurnály
nejsou změněné. Žádný nový model, placené posouzení, služba ani timer.

`CalendarDeletion` uchová serverový náhled a nativní identitu; klient
nedostává hash/ID z EventKit a při potvrzení předává pouze náhodné ID této
operace. Nativní část těsně před akcí porovná celý fingerprint včetně časů,
poznámek, alarmů, opakování a lastModified. Volá pouze `.thisEvent`.

Server i nativní helper mají trvalý marker před mutací. Nativní zámek/žurnál
je vázaný na kalendář, nativní identitu a výskyt, nikoli jen UI request nebo
proměnlivý fingerprint. Jiná karta/nový náhled proto nemohou zopakovat
nejistý pokus ani po změně provider metadat. Existující žurnál se pro další
remove nikdy neotevírá. Po úspěšném remove ověřuje nový store, že přesný
výskyt zmizel, a teprve potom ukládá verified.

Timeout, pád nebo chyba ukládání nechá unknown/pending. Opakované delete
nic nezapisuje; recover jen čte původní účtenku. Není-li nativní úspěšný
závěr trvale doložený, výsledek zůstává nejistý i při prázdném seznamu.
Nevzniká automatická opravná akce ani nové mazání po reloadu.

POST `/api/calendar/delete` je v registru akcí, za stejnou origin/host
ochranou jako ostatní kalendářové operace. Query, přebytečná pole, falešné
potvrzení a klientem dodaná nativní identita se odmítají. Stavové čtení
nezaloží nový záznam. Soukromé žurnály jsou mimo Git.

## Ověření

- 112 cílených testů PASS: backend, nativní protokol, HTTP/CSRF, frontend,
  agenda, dosavadní task/create writer a e-mailový dialog.
- Finální sada zahrnuje i starší browserový kontrakt přehledu a regresi ztráty
  přístupu při obnově nejasného výsledku: původní nejistota se neuzavírá
  a nevznikne nové mazání. Starší Node harness potřeboval doplnit window;
  oprava se týká pouze simulovaného browserového prostředí.
- Produkční Swift transakční logika proti in-memory EventKit: 15 scénářů
  PASS, včetně jednoho recurring výskytu, duplicit, skrytých změn, pozvánek,
  opakovaného požadavku a nejasné mutace s pozdější změnou fingerprintu.
- Skutečný EventKit build + ad-hoc podpis + strict codesign verify + sedm
  self-test kontrol PASS v izolované dočasné složce; bez otevření kalendáře.
- Existující instalované reader/writer sestavení se dál shodují se zdroji;
  nový mazací helper v provozní složce dosud není. Žádná reálná událost
  se během vývoje nevytvořila ani nesmazala.
- Důkazy: `logs/calendar_delete_targeted_20261108.log`,
  `logs/calendar_delete_native_build_20261108.log`,
  `logs/calendar_delete_existing_helpers_20261108.log`,
  `logs/calendar_delete_full_gate_20261108.log`.

První izolovaný podpis na synchronizované Ploše narazil na Finder metadata
(LL-037). Artefakt zůstal zachovaný a přesně lokálně ignorovaný; finální
sestavení proběhlo mimo Plochu. Žádné plošné čištění xattr ani mazání.

Finální plná brána: **3174 testů OK, 31 skipped**, včetně opraveného
staršího Node browserového prostředí. Předchozí selhání zůstalo v samostatném
logu; konečný log obsahuje celý úspěšný běh.

## Přejímka po samostatném p+n

Na řádku v kalendáři nebo po uložení zvol Smazat z kalendáře. Při prvním
použití se nabídne Povolit mazání na Macu: samostatné potvrzené sestavení
a systémový souhlas pro nový helper. Ten vývoj sám neudělil ani nevyvolal.
Potom stejný řádek zvol znovu, zkontroluj konkrétní potvrzení a teprve
potvrď smazání události, kterou opravdu chceš odstranit. Pro zkoušku storna
stačí potvrzovací okno zrušit; nemá žádnou kalendářovou mutaci.

Fyzická přejímka na Macu/iPhonu, skutečný nový OS grant a skutečné mazání
zůstávají otevřené. Vývoj ani unit testy neprokazují iCloud synchronizaci.
