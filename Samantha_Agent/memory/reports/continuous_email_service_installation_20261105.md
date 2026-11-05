# Řízená instalace hodinového e-mailového agenta

Stav 2026-11-05: systémová instalace, první ostrý průchod a obnova služby úspěšně ověřené.

## Aktuální provozní stav — 2026-11-05 08:55 CET

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

## Provedený postup

1. Registrované prepare uvnitř ignorovaných private dat vytvoří kopii
   čistého commitnutého main, manifest, otisk plánu a vypnutou konfiguraci.
   Ověří schválený model v katalogu a připojený otestovaný Pushcut.
2. Install po přesné větě globální brzdy znovu ověří zdroj, roli, nastavení
   a otisk kopie. IMAP metadata ověří UIDVALIDITY, zachová existující iCloud
   pozici; Seznam začne od aktuálního konce bez čtení starých těl.
3. Kopie kódu vznikne v uživatelském Application Support/SamanthaEmailAgent/
   releases/HEAD. .env, private data a centrální role jsou odkazy na kanonický
   projekt. Python zůstává projektový venv. Živý vývoj nemění kopii kódu.
4. Vytvoří nový uživatelský LaunchAgents plist
   com.miloslavfalta.samantha.continuous-email; existující cíl/job nepřepíše.
   RunAtLoad, začátek hodiny, minutová kontrola, Prague, explicitní child PATH.
5. Bootstrap/enable/kickstart jen vlastního jobu; čekání na čerstvý heartbeat.
   Při chybě instalace vypne konfiguraci, vyloží vlastní job a ponechá
   data/runtime k servisní kontrole. Nejisté modelové pokusy neopakuje.
6. Verify-restart znovu nahraje pouze vlastní nepracující job a ověří nový
   heartbeat. Aktivní posouzení nepřeruší. Fyzický reboot Macu neprovádí.

Terra/high, iCloud i Seznam, všechny nové celé zprávy, 07–22 Europe/Prague.
Výchozí denní početní limit null; explicitní limit zůstává možný. Nedokončené
dávky navazují další minutu, dokončená hodina se neopakuje. Per-user služba
vyžaduje přihlášený účet; uspaný/vypnutý Mac nepracuje. Po wake/přihlášení
má navázat. Odeslání odpovědí a ukládání zůstává potvrzované v Cockpitu.

## Důkazy

- 67 cílených testů PASS: skutečný izolovaný Git, falešný launchctl/IMAP/model,
  zachování kurzorů, ochrana cizí služby, změny zdroje, chyby startu/obnovy,
  zámek aktivního posouzení, redigovaný heartbeat, více než 20 zpráv,
  potvrzovací brány registru a dosavadní Pushcut/role.
- logs/email_service_install_targeted_20261105.log
- logs/email_service_model_catalog_20261105.log: Terra/high, fallback=false,
  jen katalog, žádný placený modelový tah.
- logs/email_service_install_gate_20261105.log: plná brána 2403 PASS (377,5 s).
- Následný reálný čtecí audit odhalil zdvojený prefix `git archive` ve
  vnořeném projektu. Opravené relativní cesty, instalační fixture nyní
  kopíruje skutečné vnoření; 13 instalačních regresí PASS. Viz LL-096,
  logs/email_service_install_nested_regression_20261105.log. Finální plná
  brána v logs/email_service_install_gate_final_20261105.log: 2403 PASS (388,8 s).
- Readiness: role/socket dostupné, iCloud inicializovaný, Seznam ne;
  installed/loaded/enabled=false. Pushcut configured/enabled=true, accepted.
- Předchozí vydání b372355c: p+n 9f34b5d5fa3be12a0124646c4d353050,
  push/deployment confirmed, 2386 PASS, smoke 5/5, CI 41927780373 success.
  Míla přijal skutečné doručení Pushcutu i otevření Cockpitu klepnutím.

## Původní otevřené kroky před instalací — překonané aktuálním stavem výše

Systémová věta dosud nezadaná. Po ní nainstalovat a ověřit check/obnovu,
v provozním okně první ostrý průchod. Registrace launchctl není tento důkaz.
Míla následně výslovně schválil převzetí Datových commitů a společné p+n včetně oprav do čistého repozitáře. Nový TVBCP nebyl domluvený ani založený.
Servisní příkazy jsou registrované lokálně pro terminál. Jejich dostupnost
v dříve nasazené kopii registru Cockpitu bez dalšího p+n není potvrzená;
stávající karty a Pushcut používají sdílený kanonický private stav.
Záloha 2026-10-30 je starší než tři dny; nová se nespouštěla.
Python 3.12.0rc3 zůstává; update není součástí tohoto kroku.
Na napájení už je automatické uspání vypnuté (pmset sleep=0); neměnilo se.
CalDAV a živá přejímka archivních metadat jsou další samostatné kroky.

## Společná přejímka s Datovými commity

Po převzetí Data (1b6fd61e/ccece787) 192 cílených testů: 172 PASS, 20 SDK
SKIP. Plná společná brána 2462 testů: 2442 PASS, 20 SDK SKIP (377,0 s),
logs/data_email_integration_gate_20261105.log. Upravený původní klient
ověřil živý server 0.163.0 a katalog. SDK zůstává offline. P+n je výslovně
autorizované, konečný stav je nutné číst z přesné účtenky a živého auditu.


## Aktuální oprava hodinového režimu — 2026-11-05 10:37 CET

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
