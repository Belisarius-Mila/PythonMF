# Průběžný osobní agent — e-mailový provoz a Pushcut

Nazev: Průběžný osobní agent pro e-maily a Apple/iCloud kalendář
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-11-05

## Aktuální opravený provoz — 2026-11-05 10:47 CET

- První moje p+n už dokončené: 87d2d78c037c00d17b7251752ecdc1d0,
  target 3f3b5b25, 2473 testů (20 SDK SKIP), smoke 5/5, chráněné služby
  beze změny; CI 42006566022 success. Automatická 11. hodina začala v
  11:00:09 CET a zpracovala dvě čekající zprávy, oba zdroje OK, 0 chyb.
  Datův nový UI commit je nyní převzatý k druhému oddělenému p+n; na
  samostatné provozní kopii e-mailového agenta 167e629f nic nemění.


- Běžící e-mailová služba je řízeně přepnutá z b6375a33 na 167e629f.
  installed/owned/loaded/enabled=true, nový skutečný check již dokončený.
- Opravena příčina minutových retry: úspěšné prázdné iCloud SEARCH OK/[None]
  se nově uzavírá jako prázdná hodinová kontrola. Skutečné chyby zůstávají
  chybami. Test 10:00/10:19/11:00 potvrdil čekání nové zprávy na další hodinu.
- Celý business stav před/po skutečném upgrade má stejný otisk: karty,
  předvolby, UID kurzory i denní počítadla zachované. Nový check po reloadu
  already_completed, 0 modelových posouzení, 0 nových oznámení.
- Přímo nainstalovaná kopie v Application Support úspěšně prošla živou
  prázdnou IMAP sondou obou providerů. Dočasný diagnostický kurzor se neukládá.
  Stará kopie a záloha jejího plist/účtenky zůstávají pro obnovu.
- Ověření: 118 cílených PASS; plná brána 2473 testů, 2453 PASS a 20 SDK SKIP
  (504,5 s). Kódový commit 167e629f; model Terra/high a rozsah 07–22 beze změny.
- Míla nyní výslovně určil dvě vydání v pořadí: nejdřív můj dokončený krok,
  potom samostatně Datův nový commit 5363238b. Jeho UI změnu jsem zatím jen
  přečetl; po prvním dokončeném vydání je nyní převzatý k samostatnému druhému p+n. Před fyzickou iPhone přejímkou nebude označena
  za přijatou. Žádné nejisté uživatelské odeslání se nesmí opakovat.
- První moje p+n i automatická 11. hodina jsou potvrzené; další krok je
  druhé p+n převzaté Datovy UI opravy a konečné dočištění repozitáře.
- Provozní důkazy: logs/email_empty_search_upgrade_20261105.log,
  logs/email_empty_search_upgrade_verified_20261105.log; source_head služby
  je 167e629f i po případném pozdějším čistě paměťovém commitu. Karty ani
  zprávy nebyly při opravě smazané, neposílal se SMTP ani ruční Pushcut test.

## Předchozí lokální oprava hodinového režimu — 2026-11-05 10:37 CET

- Míla potvrdil, že provozní upozornění v 08:49 skutečně dorazilo, jen ho
  nezaznamenal. Další oznámení v 10:19 slyšel tiše a banner rychle zmizel;
  nastavil jeho trvalé zobrazení. Doručení na iPhone tím je potvrzené.
- Zpochybnil okamžitou reakci na novou zprávu mimo celou hodinu. Audit
  prokázal opakované incomplete a dokončení cyklu pro 10. hodinu až 10:19;
  zpráva měla v Date 10:18:38, Pushcut accepted v 10:19:18 CET.
- Přímý read-only IMAP audit: iCloud na prázdné UID SEARCH vrací OK/[None],
  Seznam OK/bytes s nulovým novým UID. Klient úspěšný iCloud výsledek chybně
  považoval za chybu. Nešlo o zamýšlený okamžitý režim, ale minutové retry.
- Lokální oprava přijímá pouze tento úspěšný prázdný výsledek, zachovává
  chyby NO/BAD a vadné odpovědi. Regrese FAIL→PASS ověřuje dokončení prázdné
  10:00 bez modelu a čekání zprávy z 10:19 do 11:00. Cíleně 118 PASS.
- Běžící b6375a33 je do řízené výměny pozastavený (enabled=false); karty,
  předvolby, denní počítadla i pozice schránek zůstávají zachované.
- Nový registrovaný continuous_email_service_upgrade přepíná pouze vlastní
  pozastavený job na kopii čistého commitu, se stejnou přesnou globální větou.
  Stará kopie a plist/účtenka zůstanou uložené; při chybě obnoví starý job
  pozastavený, neobnovuje starší obchodní data a nepřeruší aktivní posouzení.
- Plná brána 2473 testů: 2453 PASS, 20 SDK SKIP (504,5 s). Další krok: lokální checkpoint, prepare/upgrade,
  skutečné ověření prázdného vstupu a hodinové obnovy, provozní writeback
  a autorizované p+n do čistého repozitáře. Aktivní službu nevracet na starou
  chybnou verzi bez opravy. Nový TVBCP ani změna modelu nevznikly.
- Důkazy: email_service_hourly_timing_diagnosis_20261105.log,
  email_empty_search_{regression_before,targeted,live_fixed,full_gate,pause}_20261105.log.

## Předchozí provozní stav — 2026-11-05 08:55 CET

- Míla zadal přesnou větu globální brzdy. Registrovaný instalátor dokončil
  systémovou instalaci a aktivaci vlastního LaunchAgentu; installed/owned/
  loaded/enabled=true. Vlastní kód je z vydaného b6375a33 v Application
  Support, sdílený kanonický private stav a centrální role zůstaly zachované.
- První skutečný cyklus 08:48:53–08:49:38 CET dokončil 6 nových zpráv:
  3 důležité karty s těly a 3 nedůležité zprávy v jednom hodinovém řádku.
  Živé API potvrdilo všechny počty, těla karet a 0 chyb posouzení.
- Pushcut API accepted=1 pro nový důležitý hodinový souhrn. Nejde o tvrzení,
  že Míla fyzicky přijal toto konkrétní provozní oznámení; předchozí ruční
  test doručení a klepnutí už přijal. Žádný další ruční test se neposílal.
- iCloud kurzor se při aktivaci nezresetoval, Seznam začal od aktuálního
  konce. Oba zdroje jsou inicializované. Předchozí vyřazení/ignorování zůstala.
- V 08:52 CET ověřen unload/bootstrap vlastního jobu a nový skutečný check:
  already_completed, 0 nových návrhů/oznámení. Kurzory, počet položek a denní
  počet modelových posouzení byly před/po obnově shodné. Fyzický reboot Macu
  se neprováděl; ověřena byla obnova samotné služby.
- Terra/high, všechny nové celé zprávy, 07–22 Europe/Prague, bez výchozího
  denního početního limitu. Dokončená hodina se neopakuje, další minuty
  kontrolují stav a případně dokončují dávky. Per-user služba vyžaduje
  přihlášený účet a bdělý Mac; AC sleep=0 už bylo nastavené, neměnilo se.
- Odeslání odpovědí a uložení zůstávají potvrzované v Cockpitu. Tento krok
  žádný e-mail neodeslal, nearchivoval ani nesmazal ve schránce.
- Předchozí společné vydání Data + instalátor b6375a33 potvrzené:
  p+n 09e6c05f658a1ce16750dfd5cd15c514, push/deploy confirmed,
  2462 testů (20 SDK skipů), smoke 5/5, chráněné služby beze změny,
  GitHub CI 41938993126 success. SDK zůstává offline.
- Provozní důkazy: logs/email_service_activation_20261105_{install,
  first_cycle,restart,verification,api_check}.log; soukromá účtenka
  installation.json a service_health.json. Obsah e-mailů/přístupy do Gitu nepatří.
- Další krok: sledovat další automatickou hodinovou kontrolu; případné
  hodnocení důležitosti upravovat výslovnou preferencí. CalDAV a živá
  přejímka archivních metadat zůstávají samostatné kroky. Nový TVBCP nevznikl.

## Předchozí stav 2026-11-05 — instalátor před systémovým potvrzením

- Pushcut vydaný po b372355c: Terra p+n job
  `9f34b5d5fa3be12a0124646c4d353050`, push/deployment confirmed,
  2386 PASS, smoke 5/5, GitHub CI 41927780373 success. Míla přijal
  doručení na skutečný iPhone i otevření E-mailů k řešení klepnutím.
  Private webhook připojený/zapnutý, test accepted.
- Míla zadal dokončit řízenou instalaci a provoz. Nová role continuous_email
  je Terra/high, doložené dřívější živé e-mailové zkoušky a cenové posouzení;
  aktuální katalog model potvrdil bez fallbacku. Samotný instalátor nemění
  App Server; navazující noční pokyn autorizoval převzetí Datových změn.
- Výchozí provoz zahrnuje všechny nové celé zprávy, bez denního početního
  limitu. Dřívější 20/den byl návrh. Dávky navážou další minutu; dokončená
  hodina se neopakuje. Rozsah 07–22 Europe/Prague, přihlášený uživatel Macu.
- Nový instalátor připraví uvnitř projektu kopii čistého commitnutého main;
  po systémovém potvrzení vytvoří vlastní Application Support runtime
  a LaunchAgent, odmítne přepsat existující cíl/job. Private stav, přístupy
  a role sdílí přes odkazy, běžný vývoj nepřepisuje instalovaný kód.
- Registrované continuous_email_service_{status,prepare,install,pause,
  resume,verify-restart}. Instalace/obnova vyžadují přesnou globální větu.
  iCloud kurzor se zachová; Seznam při aktivaci začne od aktuálního konce.
  Změna UIDVALIDITY zastaví instalaci bez čtení historických těl.
- Samostatný malý heartbeat dokládá skutečný check bez přepisování těl.
  Selhání startu službu vypne a zachová data/runtime. Ověření obnovy odmítá
  přerušit aktivní posouzení; neprovádí fyzický reboot celého Macu.
- 67 cílených scénářů PASS, finální plná brána 2403 PASS (388,8 s), včetně opravy vnořeného archivu. Podrobnosti a logy:
  reports/continuous_email_service_installation_20261105.md.
- Čerstvá readiness: role/socket dostupné, iCloud inicializovaný,
  Seznam zatím ne, služba vypnutá, LaunchAgent neexistuje. Systémová
  instalace zatím neproběhla: přesná věta globální brzdy nebyla zadána.
  Nový placený modelový tah, SMTP, archivace ani ruční Pushcut test neběžel.
  Míla následně výslovně schválil převzetí Datových commitů a společné p+n včetně oprav do čistého repozitáře. Nový TVBCP nebyl domluvený ani založený.
- Čerstvý report zálohy: poslední úspěch 2026-10-30, starší než tři dny.
  Autosave běží a zapisuje; SSD upozornění při 25,2 GiB. Záloha neběžela.

- Následně Will převzal oba Datovy commity do main (1b6fd61e/ccece787):
  modernizovaný původní klient, SDK stále offline. Společně 192 cílených
  testů: 172 PASS a 20 volitelných SDK SKIP; živý handshake/katalog na
  serveru 0.163.0 úspěšné. Společná plná brána 2462 testů: 2442 PASS, 20 SDK SKIP. P+n je další
  autorizovaný krok; kanonický App Server handoff/TVBCP byly synchronně aktualizované.

## Předchozí stav 2026-11-04 23:24 CET

- Příprava hodinového vstupu je již vydaná po 77f7e12f: Terra p+n
  `742135a3ba9990edc0afe6734d125166`, 2368 PASS, smoke 5/5 a GitHub CI
  41922126605 success. Živý stamp i obsah stránky shodné, main/GitHub čisté.
- Míla upřednostnil dokončit notifikaci před hodinovou aktivací a zvolil
  Pushcut. Nový lokální kód sdružuje nové důležité karty do jednoho oznámení
  za kontrolní hodinu, s trvalým stavem pokusu a bez opakování po restartu.
- Karta a fronta vznikají atomicky. Vyřazené/ignorované karty, nízká
  důležitost a modelové chyby nezvoní. Zapnutí nezahrnuje staré karty zpětně.
- Plain POST spouští v aplikaci předdefinovaný text/zvuk/URL bez placeného
  dynamického obsahu. Kód ani tento krok nevytvořily placený tarif.
- V E-mailech k řešení přibylo nastavení Pushcutu a výslovný test s request
  ID i při vypnuté hodinové službě. Prázdné pole zachovává uložený webhook,
  přehled jej nevrací. Polling nepřepisuje rozepsané nastavení.
- 147 cílených scénářů PASS včetně HTTP, JS a celého frontend kontraktu.
  První plná brána měla jediný FAIL ve starém pevném otisku rozšířené
  stránky; fixture opraven, kontrola ponechaná. Nové plné ověření provede
  schválené registrované p+n podle LL-079 před publikací.
  Čtecí audit ověřil HTTPS Cockpit a připravil private odkaz s vypnutými
  oznámeními. Skutečný webhook zatím chybí; žádný živý Pushcut POST,
  placený model, archivace ani SMTP. Staré čtyři položky zachované.
- Míla během testů výslovně schválil p+n. Nový kód zatím není nasazený;
  po commitu jej převezme Terra bez dalšího dotazu.
  Podrobnosti: `reports/email_pushcut_20261104.md`.
  Následuje p+n, skutečné propojení a fyzický test zvuku/odkazu; potom
  řízená instalace a aktivace. Vlastní modelová role zůstává neaktivní.

## Předchozí stav 2026-11-04 22:40 CET

- Míla zadal pokračovat na e-mailech, zatímco druhý terminál Data samostatně
  ověřuje App Server SDK. Produkční App Server klient ani runtime se zde nemění.
- Příště nedůležité je už nasazené po 592d247b: Terra p+n
  `1f89c512868687f9d1828d14c9337dbd`, 2352 testů PASS, smoke 5/5;
  živý stamp a stránka ověřené, GitHub run 41908363646 success.
  Níže uvedené starší tvrzení „pouze lokálně“ je překonané.
- Nový lokální krok připravuje samostatný omezený provozní vstup `tick`,
  čtecí readiness a náhled macOS LaunchAgentu. Zatím bez instalace/p+n.
- Denní počítadlo rezervuje pokus před modelovým voláním, zahrnuje nejistý
  výsledek a přežije restart. Vypnutí či změna účtů zastaví další zprávu
  bez přeskočení její pozice. Vzorový limit 20/den je návrh, nikoli schválený
  finanční/provozní rozpočet. Celé zprávy se nezkracují.
- Rozpoznávaná samostatná role `continuous_email` zatím není aktivovaná
  v config/agent_roles.json. Chybějící schválení zastaví vstup před katalogem,
  není použita role p+n a neexistuje automatický modelový fallback.
- Opravené UIDVALIDITY: změna schránky zastaví zdroj před SEARCH/FETCH,
  zachová starý kurzor a vystaví konkrétní chybu. Původní chování by četlo
  historii od začátku. Reprodukce FAIL před opravou, regrese PASS.
- Čerstvá readiness: iCloud pozice existuje, Seznam potřebuje výchozí pozici;
  chybí povolená provozní konfigurace a schválená vlastní role. Žádný nový
  živý IMAP/model/SMTP pokus ani archivace; čtyři staré položky zachované.
- Podrobnosti a důkazy: `reports/continuous_email_service_preparation_20261104.md`.
  Finální cílená sada 112 PASS, nová servisní sada 15 PASS; plná Cockpit
  brána 2366 PASS (498,4 s) a finální statická brána PASS.
  Notifikace, CalDAV, fyzické QA preference a živé archivace dál čekají.

## Předchozí stav 2026-11-04 21:19 CET

- Míla osobně ověřil úpravu odpovědi, uložení a následné skutečné odeslání.
  Čtecí audit vybrané položky potvrzuje upravený návrh, `smtp_sent` a kopii
  do Odeslané pošty `saved`. Jde o přijatý živý SMTP/editor pilot, nikoli
  pouze syntetický test. Potvrzená archivace touto zkouškou ověřená není.
- Míla výslovně schválil a zadal implementaci „Příště nedůležité“.
  Lokální vývoj přidává tlačítko k důležitým kartám a sekci Předvolby
  důležitosti se zrušením preference. Aktuální karta se tím nevyřazuje.
- Preference jsou součástí existujícího soukromého atomického JSON
  repository; žádná nová databázová závislost ani služba. Rozsah je konkrétní
  účet, přesná adresa odesílatele a podobný předmět. Normalizují se běžné
  odpovědní/přeposílací prefixy, velikost písmen, interpunkce a číselné
  varianty; volnější podobnost platí jen u delších dostatečně shodných názvů.
  Krátké předměty vyžadují shodu, nejednoznačné adresy a prázdné/čistě
  číselné vzory pravidlo nevytvoří.
- Kliknutí výslovně uloží či obnoví preferenci, opakování je idempotentní;
  Zrušit preferenci ji deaktivuje. Ignorování, vyřazení či nečinnost žádná
  pravidla neučí. Staré návrhy, kurzory a potvrzení odpovědí se nemění.
- Nový cyklus předává odpovídající preference oběma adaptérům jako vodítko
  vedle celého textu a HTML. Model dál čte úplný obsah a může nový důležitý
  požadavek/termín/platbu vyhodnotit jako důležitý. Aplikace modelový verdikt
  nepřepisuje; shoda preference nevyřazuje zprávu před posouzením.
- Cíleně 78 e-mailových scénářů PASS a 290 Cockpit/frontend scénářů PASS,
  včetně restartu, izolace účtů/odesílatelů/témat, dvojkliku, zrušení,
  úplného těla, modelového přepsání vodítka, HTTP akcí a DOM chování.
  Plná brána persistence 2352 testů PASS; důkaz v
  `logs/continuous_email_importance_gate_20261104.log`.
- Nový kód je zatím lokální, bez p+n, placeného modelového pokusu nebo
  dalšího živého SMTP. Běžící Cockpit nemá tuto novou volbu dosud nasazenou.
  Fyzická přejímka preference a jejího zrušení čeká na vydání. Hodinová
  služba, notifikace a CalDAV zůstávají neaktivované.

## Předchozí milník 2026-11-04 21:02 CET

- Následné Terra p+n je uzavřené po `13b41716`, účtenka
  `bfdfc2299ef6712e615f68e1d3fed3ed`: místní plná brána 2339 PASS,
  smoke 5/5, push/deployment confirmed. Nový GitHub CI run 41898753725
  na přesném headu success: 2339 testů, 23 skip, žádná chyba.
  Důkaz `logs/camino_ci_media_release_verification_20261104.log`.
- Míla uvedl, že předchozí e-maily v testu byly v pořádku, a vybral konkrétní
  personální korespondenci pro koncept odpovědi. Adresa, předmět ani obsah
  se do Git zápisu nekopírují. Zdroj byl znovu úplně načtený a přesně ověřený.
- Třetí vzorek malého pilota: jeden potvrzený pokus Terry/high vytvořil
  důležitou kartu s upravitelným předmětem a krátkým poděkováním.
  Odpověď na toto oznámení je volitelná; její přípravu si Míla výslovně
  zadal pro pilot. Tento kontext se neposílá do běžného hodinového cyklu.
- Živé API ověřilo návrh i celé tělo: 1 karta s konceptem, 0 chyb,
  3 předchozí vyřazené/ignorované položky zachované a kurzor neposunutý.
  SMTP, archivace ani příprava potvrzení odeslání se nevolaly.
  Soukromý důkaz `representative_pilot_20261104/reply_selected_v1.json`,
  bezpečný souhrn `logs/continuous_email_selected_reply_pilot_20261104.log`.
- Spotřeba třetího vzorku: 25 854 input, 0 cached, 278 output tokenů,
  6 946 ms; odhad při dosavadních sazbách 0,6811 Standard kreditu.
  Celkový zamýšlený třízprávový pilot je tím zpracovaný; další vzorky
  ani zapnutí služby nebyly automaticky zahájené.
- Míla navrhl malou paměť odesílatelů/předmětů pro budoucí důležitost.
  Adam doporučil výslovnou volbu „Příště nedůležité“ jako modelové vodítko:
  nevyřízený e-mail zůstává důležitý, vyřazení karty samo neznamená
  nedůležitý obsah. Jde o návrh k diskusi, implementace nebyla schválená
  ani provedená; dosavadní akce žádná nová pravidla neučí.
- Další přejímka: Míla otevře Upravit odpověď, zkontroluje/upraví předmět
  a text a použije Uložit koncept. Skutečný SMTP test a archivace zůstávají
  samostatnými kroky. Hodinová služba, notifikace i CalDAV zatím vypnuté.

## Předchozí milník 2026-11-04 20:20 CET

- Míla výslovně předal Terře dokončení opravy zjištěných chyb CI před
  návratem k e-mailovému testu. Terra lokálně upravila pouze 2 testové
  soubory Camina; Adam převzal diff. Reprodukce bez binárek FAIL→PASS,
  37/37 běžných testů PASS, skutečná mediální integrace zachovaná.
  Kanonický vývojový zápis je v handoffu/TVBCP `project-camino` a v
  `projects/camino.md`. Nové p+n ani vzdálená CI opravy zatím neproběhly.
  E-mailový pilot a výběr zprávy pro koncept tím nebyly změněné.

## Předchozí milník 2026-11-04 20:13 CET

- Následné Terra p+n je dokončené po `d1e5e72c7f88`: 2 commity,
  účtenka `2be778ce2781fc3396856daf24ead8d6`, plná místní brána 2338 PASS,
  smoke 5/5. Vzdálený head, živý stamp `6eedb2457fff8304` a stránka
  nezávisle ověřené; důkazy jsou v
  `logs/continuous_email_schema_release_20261104.log` a navazujícím
  `continuous_email_schema_release_verification_20261104.log`.
- Míla na Macu osobně vyřadil první kartu a uvedl, že Cockpit funguje.
  Čerstvý stav potvrdil `dismissed`. Jde o dílčí Mac QA místního vyřazení,
  nikoli o přejímku archivace, SMTP, metadat nebo iPhonu; kartu neobnovovat
  automaticky. Originální zprávu místní vyřazení nemaže.
- Míla souhlasil s malým dalším pilotem. Dvě dosud neposuzované iCloud
  zprávy dostala Terra/high celé a každou posoudila jednou: hromadná nabídka
  → `hourly_summary`, technické upozornění → `awaiting_confirmation`.
  Obě bez návrhu odpovědi/archivace. Živé API ověřilo 1 kartu, 1 hodinový
  řádek a 0 chyb. Běžné kurzory i původní vyřazení zachované.
- Soukromá účtenka `representative_pilot_20261104/proof_v1.json` obsahuje
  oba potvrzené pokusy, otisky a usage. Celkem 65 777 input, 42 496 cached
  (podmnožina vstupu), 454 output tokenů: při dosavadních Standard sazbách
  odhad 0,691895 kreditu za oba pokusy. Úspora cache není zárukou dalšího
  provozu; profil/rozpočet zatím nejsou aktivované.
- Pro pilot konceptu chybí konkrétní aktuální zpráva, kterou Míla chce
  zodpovědět. Asynchronně byl požádán o odesílatele a předmět. Žádost
  nenahrazovat vymyšleným zájmem, souhlasem nebo odpovědí na oznámení.
  Celkový zamýšlený limit tohoto malého pilota je nejvýše 3 zprávy.
- Technický nález z pošty: GitHub Actions pro vydání `d1e5e72c` skončily
  chybou ve 2 mediálních testech Camina (`test_camino_film_photo_layers`,
  `test_camino_film_orus`), protože runner nenalezl ffmpeg/ffprobe.
  Vzdálená CI tedy neprošla, ačkoli místní publikační brána prošla.
  Potvrzený run 41890802397; log `logs/github_email_gate_failed_20261104.log`.
  Jde o samostatný otevřený nález, nikoli provedenou opravu CI.
- Nic se neodeslalo ani nearchivovalo. Hodinová služba a notifikace zůstaly
  vypnuté; kalendář se nečetl. Tento krok neměnil produkční kód ani role.

## Předchozí milník 2026-11-04 19:35 CET

- Po Mílově „jdi na to“ byl jedním syntetickým diagnostickým průchodem
  doložen skutečný důvod: HTTP 400 `invalid_json_schema`. Modelový výstup
  vyžaduje všechny vlastnosti v `required`; generované Pydantic schéma
  vynechávalo `important` a `reply_subject` kvůli místním výchozím hodnotám.
- `CodexEmailProposer` nyní pro výstup požaduje všechny kořenové vlastnosti.
  Lokální model a jeho výchozí hodnoty se nemění, staré návrhy zůstávají
  kompatibilní. Regresní test ověřil FAIL před úpravou a PASS po ní, včetně
  požadavků na vnořené objekty. Celkem 65 cílených scénářů PASS a rychlá
  statická Cockpit brána PASS (`logs/continuous_email_schema_static_20261104.log`).
- Následoval právě jeden nový živý pokus Terry/high nad stejnou úplnou
  iCloud zprávou se shodným otiskem. Modelový výsledek je potvrzený:
  důležitá zpráva, doporučené uložení, odpověď nenavržená. Karta je ve
  stavu `awaiting_confirmation`; živé API ověřilo 1 kartu, 0 hodinových
  řádků, 0 chyb a přesnou shodu návrhu i celého textu s výsledkem pilota.
- Původní selhání je zachované v `assessment_history` a první soukromé
  účtence. Nový pokus má samostatnou soukromou účtenku
  `pilot_20261104_2.json`; kurzor běžného zdroje nebyl posunutý.
  Nic se nearchivovalo ani neodeslalo a hodinová služba zůstala vypnutá.
- Potvrzená spotřeba tohoto nového pokusu: 28 463 vstupních tokenů,
  0 cached, 221 výstupních, 28 684 celkem; modelový tah 5 724 ms.
  Při ověřených Standard sazbách jde o 0,7392 kreditu, nikoli částku v Kč.
  Jeden vzorek není odhad celého provozu; před aktivací posoudit režii
  základních instrukcí/nástrojů, dávkování a další reálné zprávy.
- Oprava adaptéru je zatím pouze lokální. Nasazený Cockpit zůstává na
  `d9bf3a7c111a`; jeho již nasazené API a stránka čtou novou kartu ze
  společného soukromého stavu. V této navazující etapě se p+n neopakovalo.
- Skutečnou kvalitu důležitosti a metadat ještě musí přijmout Míla na kartě
  v Komunikace → E-maily k řešení. Živé odesílání/archivace ani fyzická
  browser/iPhone přejímka tím nejsou doložené. Trvalá role se neměnila.

## Předchozí milník 2026-11-04 19:27 CET

- Míla výslovně schválil pořadí „nejdříve terra p+n a pak řízený pilot
  Terry“. Původní odklad p+n níže je tím překonaný; trvalá aktivace schválená
  ani provedená není.
- Registrované p+n v proudu `project-email-cases` dokončila Terra/high:
  4 commity publikované a nasazené po `d9bf3a7c111a`. Účtenka
  `c3a38a12547115a5ed292a3826a9e70e`, plná brána 2337 PASS, smoke 5/5.
  Nezávisle ověřený vzdálený main, živý code stamp `deeec06862f3711e`
  a přesná shoda nasazené stránky E-maily k řešení se zdrojem.
  Bezpečný důkaz: `logs/continuous_email_release_20261104.log`.
- Následný jednorázový pilot načetl celý jeden nejnovější e-mail z iCloudu
  přes read-only IMAP a vyvolal právě jeden modelový pokus Terry/high přes
  nasazený adaptér. Žádný archiv, SMTP, notifikace ani běžící hodinová služba.
- Pilot neprošel: `CodexAppServerClient.send_text` skončil
  `AppServerContractError`: „Turn nebyl jednoznačně potvrzen jako doručený
  a dokončený.“ Není potvrzený návrh, klasifikace ani usage; nelze tvrdit,
  že model zprávu dokončil nebo že pokus nic nestál. Kořenová příčina není
  doložená; dostupné logy ji nerozlišily. Žádný automatický opakovaný pokus.
- Soukromý stav obsahuje právě jednu položku `analysis_failed`, žádnou
  kartu ani hodinový řádek; živé API ukazuje `assessment_errors=1`.
  Scheduler má `completed` pro dokončení vstupního průchodu, nikoli pro
  úspěch modelové analýzy. Jednorázový kurzor zůstal u vybrané zprávy;
  při další aktivaci jej nemazat ani nepřesouvat bez vědomého rozhodnutí.
- Soukromá účtenka a chyba jsou pod `data/private/continuous_agent/`;
  neobsahovat je v Git zápisech. Nová trvalá modelová role nevznikla:
  jednorázový pilot použil centrálně schválenou Terru/high, nikoli fallback.
- Oficiální Standard sazby byly znovu ověřené: 25 vstup / 1,25 cached /
  125 výstup kreditů za milion tokenů, https://learn.chatgpt.com/docs/pricing.
  Provozní odhad čeká na úspěšný pilot s doloženou spotřebou.
- Browser/iPhone přejímka zůstává otevřená. Důkazy HTTP a testy ji
  nenahrazují. Níže uvedené lokální milníky jsou historie před tímto vydáním.

## Co se řešilo

Po diskusi celkového návrhu Míla určil e-maily a kalendář jako první prioritu
a souhlasil se zahájením vývoje. Celé zprávy mají být průběžně čtené a
obsahově posouzené agentem. Agent připravuje návrhy odpovědi a uložení,
metadata volí podle obsahu a ukládá až po potvrzení. Nevracet předem
odsouhlasený rozsah čtení k potvrzování jednotlivých zpráv.

## Co je hotové lokálně

- Třetí vývojový krok 2026-11-04 18:55 CET: editor má Odeslat a druhé
  potvrzení přesného příjemce, účtu, předmětu a konečného textu. První
  tlačítko pouze připraví potvrzení; SMTP se volá až po druhém.
- Odpověď respektuje jednoznačné Reply-To (jinak From), přidává vlastní
  Message-ID a návaznost In-Reply-To/References. Použije zdrojový účet;
  změna účtu, příjemce nebo textu původní potvrzení zneplatní.
- Stav `sending` se persistuje před síťovým pokusem. Úspěšné SMTP přijetí
  zůstává platné i při chybě QUIT nebo ukládání kopie do Odeslané pošty.
  Nejistý/přerušený pokus se automaticky neposílá znovu. Opakované i souběžné
  potvrzení nevytvoří druhé odeslání; jiné karty lze mezitím vyřizovat.
- Karta se po archivaci zachová, pokud ještě čeká navržená odpověď. U již
  uložené zprávy lze měnit pouze koncept odpovědi, ne přepisovat archivní
  metadata. Uložené zprávy zůstanou v historii i po místním vyřazení karty.
- 64 cílených scénářů PASS včetně falešného SMTP, HTTP cest a JS editoru.
  Žádný živý SMTP/IMAP ani placený model se při této přejímce nevolal.
  Plná Cockpit brána 2337 testů PASS; důkaz v
  `logs/continuous_email_reply_gate_20261104.log`.

- Druhý vývojový krok 2026-11-04 18:29 CET: hodinový plánovač 7:00 až 22:00
  v Europe/Prague, včetně ranní návaznosti na večerní pozici, dočtení celé dávky
  po stránkách a pokračování po výpadku. Dokončená hodina se znovu neposuzuje.
- První aktivace hodinového plánovače vyžaduje explicitní výchozí pozici
  schránek. `initialize_from_now` načte pouze UIDVALIDITY/UIDNEXT, nikoli
  historii těl; zatím nebyl živě spuštěn. Produkční vstup má používat
  `HourlyEmailScheduler`, nikoli nízkoúrovňový intervalový testovací cyklus.
- `CodexEmailProposer` podporuje Mílou zvolenou Terru přes existující lokální
  App Server socket, oddělené dočasné vlákno a strukturovaný výsledek.
  Živý model se v této etapě nevolal a centrální role/config se neměnily.
- Lokální stránka `/emails-to-resolve/` má vstup v nabídce Komunikace:
  důležité zprávy jako jednotlivé karty se záhlavím, shrnutím, důvodem,
  celým tělem a agentními metadaty; ostatní jako jeden řádek za kontrolní
  hodinu s datem, časem, odesílateli a předměty.
- Akce Ignorovat / Smazat z Cockpitu mění jen místní stav. Ve schránce se nic
  nemaže a vyřazená identita se po restartu znovu nenabízí.
- Koncept odpovědi se otevírá ve vlastním editoru, lze upravit předmět a text
  a uložit novou verzi. Běžící kontrola ani automatická obnova stránky
  nepřepisují rozepsaný editor. Odesílání doplnil třetí lokální krok výše.
- Potvrzený místní archiv je napojený na kartu; před uložením se znovu načte
  očekávaný zdroj. Přerušené uložení má v kartě možnost opětovného ověření.
- 42 cílených scénářů PASS: hodinové hranice včetně letního času, noční
  návaznost, stránkování, chyby, místní vyřazení, HTTP a JS editor/obnova.
  Plná Cockpit brána 2315 testů PASS; důkaz v
  `logs/continuous_email_hourly_gate_20261104.log`. Starší důkaz 2293 níže
  patří prvnímu backendovému milníku.
- Vizuální browser QA je otevřená: ovládací host prohlížeče v této relaci
  hlásil nedostupnost. Izolovaný syntetický HTTP náhled byl korektně ukončen;
  živý Cockpit nebyl restartovaný ani nasazený.

- Průběžný Python cyklus nezávislý na otevřeném Cockpitu, s možností ukončení.
- iCloud a Seznam vstup používá `BODY.PEEK[]`, úplný MIME obsah a identitu
  účtu, složky, UIDVALIDITY a UID. Zprávy se netřídí starými heuristikami.
- Nová cesta neomezuje počet znaků textu ani HTML. Dosavadní náhledové cesty
  zůstaly beze změny. Původní EML zachovává i vložené přílohy.
- Trvalý stav návrhů, postup po dávkách, viditelné chyby zdroje a přerušené
  modelové pokusy bez automatického opakování placeného posouzení.
- Strukturovaný modelový návrh shrnutí, reakce a metadat; upravitelný návrh
  dostává nový otisk. Úplný zdroj se před potvrzeným uložením znovu ověřuje.
- Potvrzený lokální archiv zachovává EML a přesná agentní metadata.
  Zveřejnění připravené složky je atomické; hotový archiv lze po přerušení
  převzít podle účtenky bez další kopie.
- Registrované workflow `continuous_email_agent_status` a
  `continuous_email_agent_synthetic_test`. Status je čtecí, test používá
  dočasná umělá data a falešný model. CLI nemá živý aktivační vstup.
- První milestone: 20 cílených syntetických testů PASS, samostatná regrese dosavadních iCloud
  a Seznam providerů 17/17 PASS. Plná Cockpit brána 2293 testů PASS včetně
  nového modulu, syntaxe Python/JS/shell a whitespace; bez změn živých služeb.
- Míla osobně potvrdil iCloud synchronizaci kalendáře na Macu i iPhonu.

## Co není hotové

- Terra je Mílou zvolená a jeden skutečný modelový průchod je potvrzený.
  Zbývá provozní posouzení, centrální modelový profil a skutečná přejímka
  kvality odpovědí a metadat na reprezentativních zprávách.
- Potvrzená živá archivace a přejímka metadat; editor/SMTP už Míla osobně
  úspěšně otestoval a místní účtenka potvrzuje přijetí i Odeslanou kopii.
- Ruční audit nejistého odeslání podle původního Message-ID. Automatický
  retry není povolený; UI jej při nejistotě nenabízí.
- Ruční pokračování neúspěšného modelového posouzení a odložení karet.
- Import příloh do dokumentového vaultu a zobrazení nového archivu ve
  stávajícím archivním UI. První archiv je zatím samostatný lokální výsledek.
- Kalendářový adaptér, instalace `caldav`, připojovací a synchronizační test.
- Instalační/aktivační workflow, LaunchAgent a fyzická přejímka obnovy služby.
- Upozornění na iPhonu jen při nových důležitých zprávách. Text má být
  „Zkontroluj e-maily v Cockpitu“. Cockpit se otevře klepnutím na oznámení;
  samovolné otevření přes jinou aplikaci se neslibuje. Specifický tón a
  konkrétní notifikační cesta ještě vyžadují výběr a zkoušku na telefonu.
- Předchozí vydání je po 13b41716 ověřené. Nová paměť preferencí zatím
  vydaná není a hodinový provoz není zapnutý.
- Nový samostatný pracovní proud ani nový TVBCP nebyly domluvené či založené.
  Tento terminálový krok je zapsán u existující e-mailové oblasti; před
  převzetím do Human–Adam musí být určena schválená kanonická vazba.

## Další krok

Po lokálním checkpointu připravit plán z výsledného čistého commitu. Jeho
otisk/source_head jsou v private installation_plan.json. Potom vyžádat přesnou větu globální brzdy, nainstalovat vlastní LaunchAgent,
inicializovat Seznam a zachovat iCloud, ověřit čerstvý heartbeat a obnovu.
První ostrý průchod čeká na provozní okno 07–22; mimo ně se ověří pouze
funkční spouštění. Pushcut i editor/SMTP jsou přijaté. Živé QA preference,
archivace/metadat a CalDAV čekají. Instalace není p+n společného Cockpitu.

## Navrhované další kroky

- CalDAV připojení ke stejnému iCloud kalendáři, který už používá iPhone.
- Přejímka kvality metadat, ne pouze jejich syntaktické správnosti.
- Instalace nepřetržité služby až po funkčním průchodu a ověření po restartu.

## Rizika a důkazy

- Nízkoúrovňový scan bez kurzoru začíná nejstarší zprávou; hodinový vstup
  takovou neinitializovanou schránku odmítne. Budoucí aktivace musí vytvořit
  výchozí pozice bez nechtěného zpracování celé historie a stanovit rozpočet.
- Dlouhý e-mail se nezkracuje. Překročení kontextu modelu vede k viditelné
  chybě; dělené posouzení extrémně dlouhých zpráv zatím implementované není.
- Těla důležitých zpráv jsou zatím součástí místního JSON stavu karet.
  Před trvalým provozem ověřit odezvu přehledu na větší dávce; případné
  samostatné úložiště těl a stránkování odvodit z výsledku tohoto měření.
- Původní syntetická přejímka adaptéru neodhalila neplatné strict schéma.
  Nyní je doložená reprodukce, oprava a jeden potvrzený živý výsledek;
  Míla přijal dosavadní vzorky i editor/skutečné odeslání. Širší
  reprezentativnost návrhů, metadata a paměť preferencí ještě vyžadují přejímku.
  Kalendář se nečetl a žádný e-mail se při tomto vývoji nearchivoval.
  Publikování/nasazení doložené výše není aktivací hodinového agenta.
- Projektový Python je `3.12.0rc3`; stabilní prostředí služby je doporučená
  příprava před trvalým provozem. Současné závislosti prošly `pip check`.
- Předchozí kontrola zálohy: poslední úspěch 2026-10-30; nová záloha se v této
  etapě nespouštěla. Aktuální stav vždy znovu ověřit registrovaným reportem.

## Relevantní soubory

`continuous_agent.py`, `continuous_source.py`, `continuous_email_agent.py`,
`test_continuous_email_agent.py`, `icloud_provider.py`, `commands.py`,
`cockpit_quality_gate.py`, `email_readonly_oauth.md`, `hourly_agent.py`,
`codex_proposer.py`, `cockpit_email_agent.py`, `agent_reply.py`,
`test_agent_reply.py`, `frontend/email_agent/`.

## Bezpečnost / neukládat

Do Git zápisů patří pouze technický a redigovaný stav. Živý obsah a přístupy
nepatří do tohoto handoffu; provozní data jsou pod ignorovaným `data/private/`.
