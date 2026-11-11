# Průběžný osobní agent — e-mailový provoz a Pushcut

## Aktuální vývoj hlídání — 2026-11-11

Hlídání záležitostí — etapa 1 je lokálně implementovaná jako ruční backend.
Založení, čtení/detail, úprava, Hlídání/Vyřízeno a obnovení používají stejnou
identitu, revize, generaci a trvalou doménovou účtenku. Žádný automatický monitor
ani UI nejsou připojené; API výslovně vrací automatic_monitoring=false.
Zdrojové karty, kurzory, přílohy, modelové role a běžící služba zachované.
Ověření: 22 doménových + 5 HTTP scénářů; cílené běhy 89/51/54 testů PASS.
Plná povinná brána: 3514 testů OK (31 SKIP), 504,079 s. Důkazy mimo Git: data/private/email_followups_step1_20261111/.
Další krok: etapa 2 — formulář, přepínač a přehled nad tímto kontraktem.
Dokumentační blokátor uzavření celého proudu: samostatný e-mailový TVBCP není
výslovně dohodnutý. Nevznikl nový ani náhradní obecný TVBCP. P+n této etapy
ani aktivace sledování nebyly zadány. Datův worktree zůstává nedotčený.


- 2026-11-09 14:03 CET: Lokálně propojený Archiv s potvrzenými archivacemi hodinového agenta. Společný seznam/hledání, detail, text, originál a vložené PDF fungují bez přesunu nebo přepisu uložených zpráv. Původní odkazy stabilní; agent má oddělené reference, nejednoznačná ID a úniky přes symlinky se odmítají. 30 cílených testů PASS; plná brána 3296 testů OK (31 SKIP). Skutečné uložené vyúčtování nalezené, PDF čitelné, souborové otisky před/po shodné. Bez p+n; další krok samostatně schválit nasazení a ověřit Archiv na Macu/iPhonu. Report reports/email_archive_bridge_20261109.md.


Aktuální provozní stav 2026-11-09 11:30 CET: hodinová služba obnovena registrovaným
upgradem f2d6ef79→617f3e0d. První kontrola9.11.11:00 completed v11:28:47,
7 nových zpráv (3 karty+4 přehled); HTTP3+3 viditelné,1 skrytá platným pravidlem.
Při přepnutí business stav/nastavení/role zachované; všechny původní položky
po dočtení beze změny. Terra/high, calendar_suggestions=false. Příčina byla
starý instalovaný parser proti nové recovery roli ve sdíleném JSON.
P+n dokončovacího provozního záznamu výslovně schválené; konečná účtenka
v logs/email_role_compat_release_20261109.log. Samostatný e-mailový TVBCP
není domluvený a nevzniká. Report reports/email_hourly_role_compat_20261109.md.


- 2026-11-08 18:22 CET: Lokálně doplněné volitelné kalendářové návrhy v jednom e-mailovém posouzení. Výchozí calendar_suggestions=false, běžící služba se nemění. Připravený návrh přebírá stejné Do kalendáře bez dalšího modelu/IMAP; existující návrhy, revize, zápisy a e-mailové koncepty se nepřepisují. 214 cílených testů PASS; závěrečná plná Cockpit brána 3199 testů OK (31 SKIP). Bez p+n/aktivace. Report reports/calendar_hourly_suggestions_20261108.md.

Kalendář používá jednu kartu se čtyřmi poli: název, začátek,
typ a místo. Kliknutí Do kalendáře připraví návrh přes stávající Terra roli;
úpravy i kontrola kolizí probíhají automaticky. Výchozí pásmo Europe/Prague,
konec +1 hodina; výslovný konec/délka/pásmo mají přednost. Při posunu začátku
se zachová navržená délka, také vícedenní celodenní období. Dva alarmy 24 h/60 min.
Samostatný create-only EventKit writer zapisuje až po kliknutí Zapsat do
kalendáře. Nové kolize či změna cíle vyžadují další kliknutí na aktualizovanou
kartu. Ověřuje uložené údaje i alarmy; nejistý výsledek dovoluje pouze čtecí
obnovu původního zápisu, nikoli druhý create. Původní read-only Swift/bundle a
jeho OS souhlas zůstávají beze změny. Vlastní OS souhlas writeru již potvrzený
a první konkrétně schválená událost skutečně uložená a ověřená (jeden create,
čtecí recover, dva alarmy). Přehled Cockpitu obnovený; viz poslední záznam.
Jednoduchá karta, přesun do Komunikace a měsíční agenda již nasazené
v 6d5b576b (Terra a751897cb82760aa9704339547dd78f2, CI 42458143491 success).
Rychlá karta Zadání úkolu s jedním textem, datem a upravitelným časem
09:00 je nasazená v 6c610287 (CI 42474671842 success). Uživatel nahlásil
chybu před odesláním a zašedlý formulář. Lokální oprava reprodukovaného
HTTP profilu bez randomUUID používá silné getRandomValues, odemyká
text při známém neodeslání a při částečném uložení drží původní ID.
Server při prvním auditu neměl žádnou účtenku úkolu; schéma skutečné
Mílovy adresy zatím nepotvrzené. 26 cílených PASS, plná brána 2923 testů OK (31 SKIP).
Oprava zatím bez nového p+n. Report reports/calendar_task_storage_fix_20261108.md;
kanonický UI handoff/TVBCP workstreams/project-cockpit.md. Žádný
skutečný event tímto vývojem nevznikl. Samostatný e-mailový TVBCP není domluvený.

Aktuální stav 6. 11.: Terra p+n e82a5d47 dokončené, nový editor živě ověřený.
Potvrzený upgrade na f2d6ef79 aktivoval zdvořilostní pravidlo i v hodinovém
agentu; úplný business stav zachovaný, první check already_completed.
Podrobnosti v posledním časovaném záznamu.

## 2026-11-05 22:06 CET — kompatibilita s Datovou hlasovou rolí

Po Mílově výslovném rozšíření p+n i na Datův projekt proběhl druhý potřebný
registrovaný upgrade vlastní hodinové kopie 2fe0481e → 11b4ce64. Vztahuje se
na stejný dříve potvrzený kompatibilitní servis; jiné služby se neměnily.
Instalovaný parser skutečně načetl Email/Interior i novou read_only_voice roli.
Installed/owned/loaded/enabled, úplný business otisk a nastavení před/po shodné,
e-mailová politika nezměněná, stará kopie i záloha zachované. První check
already_completed, 0 návrhů a 0 oznámení. Žádná nová hlasová či e-mailová modelová
zkouška; příští hodinové kontroly zůstávají běžným dříve schváleným provozem.
Důkaz logs/data_voice_email_compat_upgrade_20261105.log a
logs/data_voice_role_activation_20261105.log. Samostatný e-mailový TVBCP stále
není domluvený; nový nevzniká. Další krok: běžný provoz a uživatelská přejímka.


## 2026-11-05 21:22 CET — kompatibilita s rolí architekta

Míla schválil potřebný servisní upgrade přesnou globální větou spolu s AI
Ateliérem. Registrované pause/prepare/upgrade přepnuly vlastní hodinovou kopii
ac9f3bed → 2fe0481e, aby starý KNOWN_ROLES neodmítal interior_architect.
Instalovaná kopie následně skutečně načetla novou centrální politiku.

Ověřeno: installed/owned/loaded/enabled; stejný úplný business otisk před/po,
stejná nastavení a e-mailová modelová politika. Stará kopie a servisní záloha
zachované. První check already_completed, 0 nových návrhů a 0 oznámení.
Karty, visibility/importance předvolby, koncepty, UID kurzory a denní počítadla
se nezměnily. Žádné další modelové posouzení ani odchozí e-mail se nespouštěly.
Důkaz: logs/interior_ai_email_compat_upgrade_20261105.log; soukromý před/po
snapshot je pouze v lokálním servisním úložišti, nikoli v Gitu.
Samostatný TVBCP e-mailového proudu se tímto nezakládá.

## 2026-11-05 — samostatné „Příště nezobrazovat“

Míla upřesnil význam obou voleb a schválil vývoj i okamžité Terra p+n.
U důležitých karet zůstává „Příště nedůležité“ jako vodítko pro plné modelové
posouzení. U ostatní pošty má jednotlivá zpráva „Příště nezobrazovat“.
Ukládá se oddělené vratné pravidlo: účet + přesná adresa + podobný předmět.
Přehled skryje odpovídající již posouzené nedůležité zprávy, včetně dosavadních
hodinových řádků. Důležitou zprávu pravidlo neskryje; celé modelové posouzení
zůstává zachované. Pravidlo lze zrušit v samostatném seznamu a přehled obnovit.

Staré importance_preferences se nekonvertují; data zpráv, koncepty, kurzory,
notifikace a schránka se filtrem nemění. Nové visibility_preferences jsou
transakční doplňující pole společného private stavu. Stávající hodinový
worker zachovává neznámá pole; jeho zdroje/roli/instalaci tento krok nemění.
Přepnutí samostatné služby ani další modelové posouzení není k nasazení
tohoto Cockpit filtru potřeba. Živě ověřeno installed/owned/loaded/enabled,
zdroj služby ac9f3bed. Datův vlastní worktree zůstává oddělený.

Ověření: 54 funkčních testů, 46 kontraktových kontrol a Node scénář PASS;
plná brána 2 528 testů, 2 497 PASS, 31 SKIP, bez selhání (511,548 s).
Report: memory/reports/email_visibility_20261105.md. Přesný konečný stav
vydání: logs/email_visibility_release_20261105.log a
logs/email_visibility_verified_20261105.log. Fyzické kliknutí Míly je další
uživatelská přejímka. Samostatný kanonický TVBCP e-mailového proudu stále
není domluvený ani založený; nejde o uzavření této dříve otevřené vazby.

## Řízené přepnutí a společné vydání s Datou — 2026-11-05 12:07 CET

- Míla výslovně zadal Terra p+n pro Willovy i Datovy commity. E-mailový
  kód c846775b a Data d50fccbd/c49da146 (v main 5ad99375/4a337100)
  jsou společně převzaté; integrační checkpoint ac9f3bed.
- Registrované pause/prepare/upgrade dokončily přepnutí vlastního hodinového
  agenta z 167e629f na ac9f3bed. Stará kopie a servisní záloha zůstaly.
  installed/owned/loaded/enabled=true, první skutečná kontrola
  already_completed, 0 modelových posouzení a 0 oznámení.
- Celý stav před/po má shodný SHA-256: karty, upravené koncepty, předvolby,
  zdrojové UID pozice, denní počítadla i doručovací fronta beze změny.
  Nainstalované moduly návrhu/podpisu se byte-for-byte shodují s ověřeným
  zdrojem. Podpis čte místní konfiguraci, model zůstává Terra/high.
- SDK pilot zůstává izolovaný. V main s Datovým interpretem 102 PASS +
  3 historické schema SKIP; všech 12 nových C případů skutečně PASS.
  Chybějící 3 schema testy zvlášť v původním prostředí s exporty PASS,
  jejich zdroj i syntetický peer shodný. Žádná instalace závislostí do produkce.
- Důkazy: logs/email_quality_upgrade_verified_20261105.log,
  logs/data_sdk_c_integration_20261105.log,
  logs/data_sdk_c_schema_verification_20261105.log. Uživatelské Mac/iPhone
  přejímky 1–3 Data zaznamenal jako PASS; bod 4 a skutečný technický reconnect
  jsou nadále otevřené, syntetické zkoušky je nenahrazují.
- Tento checkpoint zmrazí podklady pro registrované submit_release(wait=True)
  v project-email-cases; centrální vykonavatel a společný cíl se ověří auditem.
  Konečný stav publikace a její přesnou účtenku dokládá
  logs/email_data_quality_release_20261105.log a následné *_verified_*.log.
  Během vydání se Gitový snapshot nemění. Po vydání ověřit živé UI, CI,
  samostatnou službu a čistotu main i profilů; další plné posouzení nového
  e-mailu a fyzické kliknutí na novou volbu nejsou předem prohlášené za přijaté.

Nazev: Průběžný osobní agent pro e-maily a Apple/iCloud kalendář
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-11-05

## Lokální oprava kvality konceptů a předvolby ostatní pošty — 2026-11-05 11:46 CET

- Míla upozornil na chybějící předvolbu u nedůležité pošty a na věcně
  chybný koncept s nepodloženým tvrzením o příloze. Read-only načtení
  konkrétní zprávy ověřilo shodu původního EML digestu i celého uloženého
  těla (1801 znaků textu, 13908 znaků HTML). Oba úplné formáty předává
  adaptér modelu; zkrácení vstupu se nepotvrdilo. Původní koncept se po
  uživatelské úpravě nezachoval, jeho přesné znění není zpětně doložitelné.
- Ve zdrojích je doplněná volba jednotlivé zprávy uvnitř rozbalení
  Příště nedůležité… v hodinovém řádku. Ukládá se stejná výslovná
  preference účet + odesílatel + podobný předmět. Řádek, těla, UID kurzory
  a schránka zůstávají zachované; smazání se dál neučí automaticky.
- Oba modelové adaptéry sdílejí pravidla: rozlišit hotové úkony od
  požadavků, zachovat termín, podklady a alternativy doručení, nezaměňovat
  běžnou odpověď za úřední podání. Editor posílá pouze text bez příloh;
  koncept nemá tvrdit, že něco přikládá nebo že už byla žádost podána.
  Požadované oslovení vychází z From/podpisu, při neznámé osobě obecné.
- Podpis se doplní programově jen novému konceptu podle lokálního
  SAMANTHA_EMAIL_REPLY_NAME. Jméno bylo ověřeno v uživatelem uloženém
  konceptu a nastaveno pouze v místním .env; Git obsahuje jen prázdný vzor.
  Uživatelské úpravy a potvrzené odchozí zprávy se tím nepřepisují.
- Dvě skutečné jednorázové zkoušky Terra/high: syntetická žádost a
  původní zpráva. Obě správně oddělily odpověď od podání, zachovaly termín,
  oslovení a podpis, bez tvrzení o příloze či dokončeném úkonu. Původní
  karta a koncept beze změny. Jde o dva ověřené případy, nikoli záruku
  bezchybnosti všech dalších e-mailů. Žádný SMTP ani Pushcut test.
- Aktuální centrální role i skutečný App Server potvrzují Terra/high.
  Katalog podporuje také xhigh/max; vyšší úroveň by vyžadovala samostatné
  srovnání kvality, času a spotřeby. Model ani jeho úroveň se neměnily.
- Ověření: plná brána 2476 testů, 2456 PASS a 20 SDK SKIP (406,1 s).
  Po poslední úpravě rozložení a registrace nového policy modulu navíc
  55 cílených kontrol PASS; finální statická brána PASS. Dvě živé zkoušky
  Terra/high PASS. Otisk změněné stránky byl aktualizován bez oslabení kontraktu.
  Důkazy: logs/email_proposal_diagnosis_20261105.log,
  logs/email_quality_live_review_20261105.log,
  logs/email_quality_full_gate_20261105.log. Soukromý náhled leží pouze
  pod data/private/continuous_agent/quality_preview_20261105.json.
- Stav vydání: pouze lokální změna, bez nového p+n. Běžící hodinový agent
  zůstává na 167e629f; pro zapnutí opravy je nutné schválené p+n Cockpitu
  a řízený upgrade jeho samostatné kopie. Starý uživatelský koncept se
  automaticky nepřegeneruje. Nový TVBCP nebyl domluven ani založen;
  jde o terminálový vývoj stávajícího e-mailového proudu.
- Předchozí vydání obou kroků skončila úspěšně: moje 3f3b5b25 / CI
  42006566022 a Data 6972ea5c / CI 42009849549. Datův vývoj zde neměněn.
  Další krok po lokálním checkpointu: samostatné p+n project-email-cases
  a řízený pause/prepare/upgrade hodinové kopie se zachováním dat a pozic.
  Nový p+n v tomto kroku nebyl zadán. CalDAV a archivní metadata zvlášť.

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

## 2026-11-06 16:34 CET — Zdvořilostní odpovědi a prázdný editor (lokálně)

Hotovo: Společná politika obou modelových adaptérů vyžaduje návrh i při
zdvořilostním významu odpovědi, například poděkování za osobní/pracovní zprávu
nebo výsledek výběrového řízení. Odlišuje povinnou reakci od dobrovolné;
zprávu s navrženou odpovědí ponechá k lidskému posouzení jako important=true.
Reklama, newsletter ani zjevné no-reply samy o sobě zdvořilou reakci neodůvodňují.
Karta bez konceptu má Napsat odpověď s prázdným tělem a odvozeným Re: předmětem;
existující koncept dál nabízí Upravit odpověď. Otevření nic neukládá.

Rozhodnutí: Míla výslovně požaduje připravit odpověď vždy, pokud má i
zdvořilostní význam, a souhlasil s prázdným editorem. Vývoj je lokální;
push, nasazení Cockpitu ani upgrade samostatné hodinové služby nebyly zadané.
Model a role se nemění. Stávající živé návrhy se nepřegenerovávají.

Další krok: Samostatně schválit p+n a registrovaný upgrade vlastní hodinové
kopie; pouhý nový main její zmrazená pravidla nezmění. Lokální vývoj a plná
brána jsou dokončené; tento záznam je součástí lokálního checkpointu.

Navrhované další kroky: Podle původního pořadí Míly zvlášť analyzovat,
proč Human–Adam nedokázal diagnostiku konkrétního problému provést.

Technický důkaz: Regrese prázdného editoru před změnou FAIL, po změně PASS.
61 cílených Python testů včetně rozšířeného Node DOM scénáře PASS. Ověřené
ruční napsání/uložení/znovuotevření, ochrana rozepsaného textu, blokace
sending/delivery_unknown/smtp_sent a odmítnutí prázdného textu. Příprava bez
SMTP a odesílání až po samostatném potvrzení. Plná brána 2669 testů,
31 SKIP, bez selhání PASS (513,892 s unit část):
logs/email_courtesy_full_gate_20261106.log. Nové pravidlo nebylo zkoušené živým
modelem; fyzická Mac/iPhone přejímka je otevřená. Soukromý e-mail ani adresy
se do tohoto zápisu nekopírují. Nový e-mailový TVBCP se nezakládá.

## 2026-11-06 16:57 CET — Terra p+n editoru dokončené, hodinová pravidla čekají na servis

Hotovo: Cockpit má nové Napsat odpověď u karty bez konceptu. Terra p+n na
výslovný pokyn Míly dokončené pro e82a5d473198677c83deb805fd0b303ff8034671;
push i deployment confirmed, plná brána 2669 testů PASS / 482,1 s, smoke 5/5,
protected_services_unchanged=true. Živé HTML HTTP 200 se přesně shoduje se
zdrojem, SHA-256 de672549c799950265dba9bdb14e73755e1fb61a4c444cf34137528c32468247.
Fyzická přejímka otevření editoru na Macu/iPhonu zůstává samostatná.

Rozhodnutí: Míla schválil „ok terra p+n“. Samostatná hodinová služba dál
installed/owned/loaded/enabled na 11b4ce64; její proposal_policy je dosud
původní. P+n Cockpitu nepřepíná tento vlastní LaunchAgent. Žádný nový placený
modelový pokus ani přeposouzení staré karty se neprováděly.

Další krok: Pro aktivaci zdvořilostního pravidla v hodinovém agentu získat
přesnou globální potvrzovací větu podle global_safety_brake.md a service_control.py.
Potom registrované pause → prepare aktuálního čistého main → upgrade, se
zachováním karet, konceptů, předvoleb, UID pozic a modelové politiky; ověřit
business otisk a první check. Porovnání 11b4ce64..e82a5d47 v Python app kódu
mění pouze proposal_policy.py. Služba zatím nebyla pozastavená ani přepnutá.

Navrhované další kroky: Samostatná diagnostika dřívějšího selhání Human–Adam
podle Mílova původního pořadí.

Technický důkaz: Účtenka b3165b2afa348909c291ff989fd12207 completed,
logs/email_courtesy_release_20261106.log a email_courtesy_verified_20261106.log.
return_channel=caller; returned_to_adam=false není důvodem opakovat vydání.
Main/GitHub byly před tímto výsledkovým zápisem shodné, profily zarovnané,
Datův vlastní worktree čistý a zachovaný. Tento dokumentační checkpoint je
lokální pro příští balíček; neprovádí nové nasazení. Soukromý e-mail ani
přihlašovací údaje se do zápisu nekopírují. Nový TVBCP nevzniká.

## 2026-11-06 17:03 CET — Zdvořilostní pravidlo aktivní i v hodinové službě

Hotovo: Hodinový e-mailový agent nyní používá nové pravidlo zdvořilostních
odpovědí. Registrované pause → prepare → upgrade převedly vlastní LaunchAgent
z 11b4ce64 na f2d6ef79. Installed/owned/loaded/enabled=true; čerstvý import
z instalované kopie potvrdil nové pravidlo a byteovou shodu proposal_policy.py.
První dokončená kontrola already_completed, žádné nové placené posouzení.

Rozhodnutí: Míla po dokončeném Terra p+n výslovně poslal přesnou větu globální
brzdy pro tento servisní upgrade. Kód odpovídá již přijatému e82a5d47;
f2d6ef79 oproti němu přidává pouze dokumentační výsledek vydání.

Další krok: U dalších běžně posuzovaných zpráv ověřit praktickou kvalitu
zdvořilostních konceptů; původní již posouzená karta se nepřegenerovává.
Napsat odpověď je v nasazeném Cockpitu dostupné i bez původního konceptu.

Navrhované další kroky: Samostatně navázat na Mílův původní požadavek proč
Human–Adam nedokázal konkrétní e-mailový problém diagnostikovat.

Technický důkaz: Všech 12 servisních kontrol PASS. Úplný business stav před/po
shodný (karty, koncepty, předvolby, UID pozice, počítadla i doručovací fronty),
shodná nastavení a všechny role; předchozí release i nová servisní záloha
zachované. Otisk business stavu
338d2a91f2bb5402cda3848a2f383a76845e6d9c3012670b603b10783e5662a4.
Důkaz logs/email_courtesy_service_upgrade_20261106.log; úplný soukromý baseline
a redigovaný verified.json jen v ignorovaném service_audits/courtesy_policy_upgrade_20261106.
Bez SMTP, nového modelového probe či přeposouzení původní zprávy.
Předchozí p+n e82a5d47/b3165b2a a plná brána 2669 testů zůstávají platné;
servisní kód ani testy se v tomto kroku neměnily. Tento výsledkový zápis je
lokální pro příští balíček; nový TVBCP nevzniká.

## 2026-11-07 00:01 CET — Kalendářový agent, bod 1: čtecí přístup ověřený

Hotovo: Úplný sedmibodový návrh je připojený na konec zadaného soukromého TXT;
původní obsah zachovaný bajtově. V hlavním checkoutu je samostatný čtecí
EventKit pilot, registrované schopnosti a přesné CLI workflow. Míla povolil
nativní aplikaci přístup. Skutečná jednorázová launchd zkouška rozpoznala
8 kalendářů / 4 iCloud a ověřila sedmidenní okno; žádné události nezapsala.
Dočasný vlastní job už je odstraněný, trvalý LaunchAgent nevznikl.

Rozhodnutí: Míla schválil zahájení bodu 1, další body zůstávají návrhem.
Ověřená cesta používá samostatnou podepsanou aplikaci a soukromý request/result
kanál. Přímý kontext Codexu hlásí pouze write_only, samostatný launchd helper
full_access; nelze zaměňovat oprávnění různých exekučních kontextů.

Další krok: Bod 2 — vybrat čtené kalendáře a budoucí cílový kalendář, navrhnout
čtecí přehled. Bez implementace dalších etap a bez nového p+n v tomto kroku.

Navrhované další kroky: Samostatně zachované dřívější téma diagnostiky selhání
Human–Adam. Aktualizace nativního podpisu/TCC a fyzická iPhone přejímka mají
v dalších etapách vlastní ověření.

Technický důkaz: 44 cílených testů a 4 nativní kontroly PASS; reálná čtecí
launchd přejímka PASS. Plná brána 2683 testů / 31 SKIP, bez selhání PASS
(512,463 s unit část). Report
calendar_access_pilot_20261107.md a logs/calendar_access_*_20261106.log.
Osobní názvy kalendářů/ID zůstávají soukromě, texty událostí se neexportují.
Nový e-mailový TVBCP nevzniká. Hodinová služba a Cockpit se nepřepínaly.

## 2026-11-07 00:18 CET — Schválené společné Terra p+n s Datovým hlasovým panelem

Hotovo: Čtecí kalendářový bod 1 c0963d6b je připravený společně s Datovými
opravami E/F/G 4bf110fd, 73fdc08e, 975f0900. Obě historie a provozní výsledky
jsou zachované; střety byly pouze v dokumentaci.
Rozhodnutí: Míla zadal p+n Willových i Datových commitů přes Terru. Nevzniká
nové oprávnění k zápisům kalendáře, mikrofonu, placenému probe nebo upgradu
samostatné hodinové kopie; ta už má aktivní zdvořilostní pravidlo na f2d6ef79.
Další krok: Konečná účtenka logs/calendar_voice_release_20261107.log a živé
ověření calendar_voice_verified_20261107.log. Vydání není předběžným zápisem
potvrzené. Kalendářový bod 2 zůstává další etapa.
Navrhované další kroky: Mílova skutečná iPhone přejímka hlasového panelu.
Technický důkaz: Cílená integrace a statická brána dle příslušných logů;
plná publikační brána uvnitř Terry. Datův vlastní worktree se nemění.

## 2026-11-07 00:51 CET — Kalendářový bod 2: výběr a čtecí přehled

Hotovo: Cockpit má samostatnou cestu Kalendář (/calendar/). Soukromě ukládá
výběr čtených kalendářů a oddělený budoucí cíl. Přehled načítá 30 dní, ukazuje
poslední čas, celodenní i časové události a označí neúplné/zastaralé načtení.
Chybějící kalendář, odebrané oprávnění ani prázdný snímek nejsou důkazem volna.

Rozhodnutí: Míla autorizoval bod 2 a okamžité Terra p+n. Výběr je výchozí
prázdný; konkrétní kalendáře musí vybrat sám. Žádná událost, hodinová služba,
modelová role ani Datův worktree se nemění. Obsah přehledu se neposílá modelu.

Další krok: Po nasazení na Macu v Kalendář → Povolit přístup na Macu potvrdit
nové nativní sestavení, Obnovit kalendáře, zvolit výběr a Uložit výběr a načíst.
Následně porovnat skutečné události s Kalendářem na Macu a iPhonu. Bez této
přejímky není bod 2 uzavřený jako skutečný provozní přístup.

Navrhované další kroky: Bod 3, návrhy událostí z vybraných e-mailů, až jako
samostatný vývoj. Diagnostika dřívějšího selhání Human–Adam zůstává zachovaná.

Technický důkaz: 87 cílených testů a Safari QA nad izolovanými umělými daty
PASS; nativní sestavení a 4 syntetické kontroly PASS. Skutečné jednorázové
launchd čtení po změně cdhash hlásí not_determined / authorization_required,
nebyl automaticky spuštěn nový OS dialog. Staré binární sestavení, původní
oprávnění a žádosti jsou zachované. Plná brána: logs/calendar_overview_full_gate_20261107.log;
publikační autorita: calendar_overview_release_20261107.log a calendar_overview_verified_20261107.log.
Živé názvy, ID a události zůstávají soukromě; nový TVBCP nebyl domluvený.

## 2026-11-07 09:05 CET — Bod 3: návrhy událostí z vybraných e-mailů (lokálně)

Hotovo: Na vybrané důležité e-mailové kartě je v lokálním kódu Navrhnout událost.
Editor se otevře bez modelového tahu. Samostatné potvrzené tlačítko pošle jen
tuto zprávu schválenému e-mailovému modelu; odpověď obsahuje citace a navržené
položky. Uživatel může uložit i neúplný koncept, uvidí co chybí a co upravil.
Program kontroluje data, pásmo, délku, půlnoc, DST a nesoulad normalizace s
výslovným datem/časem v citaci. Termín úkolu není automaticky schůzka.
Formální ICS a rozpoznané opakování mají ruční zpracování bez placeného tahu.

Rozhodnutí: Míla zadal pokračování bodem 3. Will řeší jádro, validace a integraci;
vymezený editor připravila Luna registrovanou cestou, převzatý přesným digestem.
P+n bodu 3 není zadané. Žádné kalendářové zápisy, odesílání, zpětný průchod
pošty ani rozšíření hodinové služby. Modelové role a Datův worktree beze změny.

Další krok: Po lokálním dokončení samostatně rozhodnout o p+n a vybrat jeden
skutečný e-mail pro přejímku. Ranní OS souhlas bodu 2 stále není potvrzený;
přípravu návrhů neblokuje, budoucí kontrolu kolizí a zápis ano.

Navrhované další kroky: Bod 4 — kolize a konečné potvrzení, až po samostatném
zadání. Diagnostika dřívějšího selhání Human–Adam zůstává zachovaná.

Technický důkaz: Cílené testy viz calendar_draft_targeted_20261107.log, plná
brána calendar_draft_full_gate_20261107.log, finální stav calendar_draft_verified_20261107.log.
Jeden skutečný Terra tah nad umělým e-mailem PASS, 7171 vstupních / 214 výstupních
tokenů; správné datum, 10:00–11:00, Europe/Prague, místo a odkaz, žádný retry
a žádná skutečná pošta. Pojmenovaný omezený profil ověřen také prázdným vláknem
bez modelového tahu. Browserový kontrakt ověřuje rozepsané změny, opožděný GET,
revizi, nejistý POST a zákaz nového pokusu. Safari vrací cgWindowNotFound, takže
vizuální přejímka zůstává otevřená. Soukromé vstupy/účtenky nejsou v Gitu;
nový TVBCP nebyl domluvený a nevzniká.

## 2026-11-07 09:27 CET — Kalendářový vývoj ověřen a společné p+n schválené

Hotovo: Vývojová plná brána bodu 3 prošla: 2726 testů, 31 SKIP, bez selhání
(441,869 s unit část). Bodový čas termínu úkolu nevyžaduje konec ani délku
schůzky. Statická brána a cílené kontroly PASS.
Rozhodnutí: Míla nyní výslovně zadal p+n včetně Datova b4b72ab0, který ruší
placený hlasový pilot. Starší hlasové opravy A–G se samostatně nenasazují.
Další krok: Převzít přesný rušící commit a předat společný merge head Terře.
Navrhované další kroky: Vybraný skutečný e-mail a bod 4 kolizí samostatně.
Technický důkaz: logs/calendar_draft_full_gate_20261107.log; společné vydání
dle logs/calendar_draft_retirement_release_20261107.log a *_verified_*.log.
Tento zápis nepředstírá dokončené nasazení. Soukromé účtenky zůstávají private.

## 2026-11-07 — Will: společný balíček kalendáře 3 a zrušení hlasového pilotu

Míla výslovně schválil p+n včetně Datova rušícího `b4b72ab0`. Will jej
začlenil nad kalendářový `afb7c9cf`; starší hlasové opravy se samostatně
nenasazují. Bod 15/P2 je definitivně ukončen, historické přejímky E/F/G
ani iPhone Start již nejsou dalšími kroky. Data má dál vlastní worktree.

Při řešení konfliktů zůstaly všechny kalendářové a Ateliérové cesty i pět
ostatních rolí; odstraněná je pouze role read_only_voice a zapojení placeného
pilota. Na main se přebírá přesných 14 verzovaných odstranění; Datových deset
generovaných souborů se týkalo jen jeho worktree. Soukromé důkazy a audio se
nemažou. Běžné předčítání, nahrávání pokynů a audio Camina zůstávají zachované.
203 integračních testů PASS; po opravě zastaralého testu zakázané hlasové role
samostatně 10/10 PASS. Rychlá statická a plná publikační brána jsou podmínkou
vydání. Kalendářový vývoj před integrací: 2726 testů OK, 31 SKIP; jedno
syntetické živé modelové ověření PASS. Skutečný e-mail ani kalendář se neměnil.

P+n provede jediný registrovaný vykonavatel Terra pro project-email-cases
(společný Cockpit). Tento zápis vzniká před publikací; konečný provozní stav
určuje přesná účtenka a logs/calendar_draft_retirement_release_20261107.log,
čerstvé ověření logs/calendar_draft_retirement_verified_20261107.log.
Po dokončení ověřit 404 bývalého panelu/API, nové e-mailové UI a běžné audio.
Fyzická Mac/iPhone přejímka nového kalendářového editoru a oprávnění aktuálního
EventKit buildu zůstávají oddělené; bod 3 nevytváří kalendářové události.

## 2026-11-07 13:40 CET — bod 4, upozornění a odvozené časy

Hotovo: Editor doplňuje datum konce a počítá délku z časů v uvedeném pásmu,
včetně DST. Přes půlnoc se konec neposouvá bez pozdějšího data. Ručně zadaná
délka bez koncového času zachovává správné skutečné datum konce. Vícedenní
uživatelské datum se nepřepisuje. Původ výpočtu se odlišuje od citace modelu.
Upozornění jsou standardně 24 hodin a 60 minut před začátkem/termínem;
každé lze vypnout, volba se uchová. U celodenní schůzky se počítají od půlnoci
a koncové datum je výlučné. Celodenní termín bez hodiny vyžaduje pro náhled
upozornění upřesnit čas. Upozornění se zatím neplánují do OS: skutečný zápis
události a alarmů patří bodu 5.

Hotovo: Zkontrolovat kolize a zobrazit náhled načítá výhradně vybrané kalendáře
v přesném omezeném období návrhu, i mimo výchozích 30 dní přehledu. Konečný
náhled obsahuje celý interval, místo/odkaz, přesný cíl, čtené kalendáře, kolize
a konkrétní časy upozornění. Potvrzení vyžaduje kontrolu údajů/citací a zvlášť
přijetí kolizí, jsou-li přítomné. Znovu čte kalendáře; změněný obsah nebo
vypršení ukáže nový náhled bez přeneseného souhlasu. Revize, source digest,
výběr/cíl, upozornění, kolize a pětiminutová platnost brání použití starého
potvrzení. Chybějící oprávnění/cíl, neúplný výsledek či chyba čtení potvrzení
neumožní. Souběžné změny na jiném zařízení zamknout nelze. Potvrzení neprovádí
zápis kalendáře a není povolením obejít čerstvou kontrolu v budoucím bodu 5.

Rozhodnutí: Míla výslovně požádal o automatické datum/délku, obě výchozí
upozornění a pokračování vývoje. Pokračování znamená bod 4 podle přijatého
plánu, vykonavatel Will. Nové p+n tím nebylo zadáno.


Další krok: místní checkpoint po plné bráně; samostatně schválené p+n a fyzická
přejímka nového editoru. Navrhované další kroky: bod 5 — jediný skutečný zápis,
uložení obou alarmů do EventKitu a ověření výsledku; bod 6 — přejímka iPhonu.

Technický důkaz: 112 cílených testů PASS a dalších 45 finálních regresních
kontrol PASS včetně nových závodů/vypršení. Plná brána a finální checkpoint dle
logs/calendar_review_full_gate_20261107.log a calendar_review_verified_20261107.log.
Skutečné omezené čtení čtyř vybraných kalendářů PASS, cíl zapisovatelný,
build i uložený přehled beze změny; pouze agregáty v
logs/calendar_review_native_live_20261107.log. Žádný skutečný e-mail, nový
modelový tah, kalendářový zápis ani restart/službový upgrade. Hodinový agent,
role a Datův samostatný worktree beze změn. Nový e-mailový TVBCP nedohodnutý.

Doplnění ověření: skutečné Safari nad oddělenou syntetickou zprávou a kalendářem
prošlo změnou koncového času 11:00 → 11:01 (délka ihned 61), uložením, náhledem
obou konkrétních upozornění, kolizí a odděleným souhlasem k potvrzení. Screenshot
zkontrolovaný; původní panel obnovený a vlastněný QA server zastavený. Nejde o
přejímku skutečného e-mailu/iPhonu. Důkaz logs/calendar_review_safari_20261107.log.
Plná vývojová brána PASS: 2656 testů, skipped=31, 496,185 s unit část.
Poslední drobná CSS oprava skrytých souhlasových řádků ověřená následně
28 frontend/HTTP testy a znovu ve skutečném Safari; oba výchozí alarmy zaškrtnuté,
souhlasy před náhledem skryté. Změna persistence a potvrzování byla ověřená
plnou bránou; finální CSS pokrývají doplňkové kontroly a rychlá statická brána.

## 2026-11-07 14:04 CET — Will: společné schválené Terra p+n

Hotovo: Do hlavního checkoutu převzatý Datův commitovaný REC-01 až REC-04
rozsah 29de7f05, dc528b45, d8b3d066, e8bb4b12, d5651110 nad kalendářovým
9f7ce93e. Rozpracovaný REC-05 v Datově vlastním worktree zůstává zachovaný.
Konflikty zachovávají všechny současné role (Email/Ateliér) i přidaný parser
RECOVERY_ROLE, oba seznamy workflow a všechny testy. Centrální JSON beze změny:
recovery_document_maintainer není aktivovaný. Sdílený helper zachovává named
profile/disabled_features a doplňuje Datovo vypnutí plugins/skills. LL nového
REC proudu přeznačené na 106–108, aby nepřekryly existující záznamy.

Rozhodnutí: Míla výslovně zadal všechny hotové Willovy i Datovy commity pro
Terra p+n. Jde o společný runtime Cockpitu, předání project-email-cases; nový
plánovač, placený REC pilot, produkční TXT/iCloud publikace a nová role se
neaktivují. REC-04 writer zůstává jen pro izolované testovací kopie.

Další krok: jediný registrovaný submit_release(wait=True), zmrazený společný
merge head a Terra z centrálního auditu. Výsledek publikace se neodvozuje z
tohoto předběžného zápisu: autorita logs/calendar_recovery_release_20261107.log
a logs/calendar_recovery_verified_20261107.log a přesná runtime účtenka.

Navrhované další kroky: kalendářový bod 5 (jediný zápis včetně alarmů) až jako
další vývoj; REC-05/06 v Datově samostatném proudu, původní přejímky zachované.

Technický důkaz: 198 cílených integračních testů PASS. Plná společná brána,
smoke, přesné nasazení a CI jsou podmínkou vydání; zajišťuje registrovaný worker
a následná kontrola Willa. Žádná změna hodinové kopie, produkčního návodu,
iCloud cílů, služeb Camina či autosave mimo standardní chráněné vydání Cockpitu.

## 2026-11-07 14:18 CET — oprava přenositelnosti testu po publikační bráně

Hotovo: Test návrhu plist používá vlastní TemporaryDirectory s připraveným
interpretem a skriptem. Ověřuje pouze vytvoření specifikace bez změn fixture;
nový negativní scénář zachovává odmítnutí chybějícího Pythonu nebo skriptu.
Produkční launcher ani služby se nemění. 125 REC testů PASS.

Rozhodnutí: Původní přesná účtenka d525499100547f133a7214951cc661dd zůstává
zachovaná v attention/push_state=uncertain. Diagnostika doložila jedinou chybu
v plné bráně (2780 testů, 49 SKIP): lokální .venv chybí v izolovaném profilu.
GitHub živě stále 9730a662. V github_batch.py brána vyhazuje výjimku před
_push_exact_head, tedy tento pokus žádný Git push neprovedl; nasazení nezačalo.
Nejde o opakování nejasného síťového push. Po opravě vzniká nový commit a nový
přesný balíček podle stále platného Mílova p+n.

Další krok: nové registrované předání v2; autorita aktuálního vydání
logs/calendar_recovery_release_v2_20261107.log a calendar_recovery_verified_20261107.log.
Technický důkaz selhání: logs/calendar_recovery_gate_failed_fixture_20261107.log;
oprava: logs/calendar_recovery_fixture_fix_20261107.log. Produkční REC aktivace
zůstává vypnutá a Datův REC-05 ve vlastním worktree zachovaný.

## 2026-11-07 14:33 CET — Will: převzetí dodatečně dokončeného REC-05

Hotovo: První balíček 135f46e7 je potvrzeně pushnutý a nasazený (Terra job
10fcd19ea7f50889a1f1424679e70b9b, 2781 testů, smoke 5/5). Během jeho běhu
Data commitnul aa18a6e7. Will podle Mílova pokynu všechny commity přebírá i tento
REC-05 do navazujícího přesného vydání. Celý kalendář/REC-01 až REC-04 zůstává.
Nový plánovač má pouze sandboxové callbacky a produkční run/tick jsou stále
activation_required. Žádná role, služba, skutečný návod ani modelový pilot se
neaktivují. REC-06 má samostatné dosud otevřené předpoklady a oprávnění.

Hotovo: Zachovaná launcher X_OK kontrola. Fixture mají vlastní spustitelný
wrapper k aktuálnímu interpretu a odkaz na skutečný CLI pro minimal-PATH test;
žádná závislost na .venv izolovaného publikačního profilu. Validace produkce
není oslabená. 199 cílených testů PASS; skutečný read-only environment preview
v hlavním checkoutu PASS (bez launchd/auth přejímky, bez služby/modelu).
LL-100 z nového proudu přeznačen na LL-110, historické záznamy zachované.

Rozhodnutí: pokračuje původní výslovné p+n všech hotových commitů, nikoli
aktivace automatického běhu. Datův worktree zůstává oddělený.


Další krok: navazující Terra p+n, nová přesná účtenka a nejnovější GitHub CI.
Autorita výsledku logs/calendar_recovery_rec05_release_20261107.log a
logs/calendar_recovery_verified_20261107.log. Důkazy předání předchozího balíčku
zůstávají calendar_recovery_release_v2_20261107.log a *_verified_phase1_*.log.
Technický důkaz: logs/calendar_rec05_targeted_20261107.log a
calendar_rec05_environment_20261107.log. Plná brána posledního balíčku je
povinná u registrovaného workeru. Bez změny hodinové kopie, výběru kalendářů,
produkčních TXT/iCloud kopií nebo aktivace plánovače.

## 2026-11-07 19:26 CET — jednoduchý soukromý kalendář a potvrzený zápis

Hotovo: Jedna karta se čtyřmi poli, automatická příprava/ukládání/kontrola,
jedno tlačítko pro zápis a samostatný create-only helper s oběma alarmy.

Rozhodnutí: Míla schválil zjednodušení pro soukromé účely; výslovný konec
má přednost před hodinou. Bez nového p+n; poslední nasazení 2909ea5a.

Další krok: po samostatně schváleném p+n povolit přesný writer na Macu a
potvrdit jednu konkrétní skutečnou událost pro přejímku.

Navrhované další kroky: přejímka na iPhonu. Nový TVBCP nevzniká bez dohody.

Technický důkaz: report calendar_simple_20261107.md; úplná brána
logs/calendar_simple_gate_20261107.log a nativní build
logs/calendar_simple_native_20261107.log. Skutečný EventKit zápis ani nový
modelový tah nebyly spuštěny. Browser QA blokuje nedostupné okno/host; neprošla
fyzická přejímka. Hodinový e-mailový runtime, placený hlas a Data worktree se nemění.

## 2026-11-07 21:47 CET — první skutečný zápis do kalendáře macOS

Hotovo: Mílou konkrétně potvrzený test uložen do nastaveného cílového
kalendáře; začátek/konec, Praha i alarmy 24 h/60 min ověřené novým nativním
čtením. Jeden create, jeden čistě čtecí recover. Přehled Cockpitu obnovený,
obsahuje právě jednu odpovídající událost. Potvrzovací karta vyčištěná.

Rozhodnutí: Výslovné „ano“ potvrdilo dříve zobrazený test 8. 11. 2026
10–11. Událost zůstává uložená. Nejde o souhlas s dalším zápisem ani p+n.

Další krok: samostatně schválené p+n nové jednoduché karty; její kód je stále
pouze lokálně. Pro zobrazení uloženého testu stačí obnovit Kalendář v Cockpitu.

Navrhované další kroky: vizuální přejímka na Macu/iPhonu a kontrola přenosu
na druhé zařízení. Nový TVBCP není domluvený a nevzniká.

Technický důkaz: logs/calendar_writer_macos_acceptance_20261107.log.
GUI grant přesného writeru full_access; oba native požadavky parent_pid=1.
První read-back měl všechny potvrzené údaje i alarmy, ale prázdné event_id;
Python správně ponechal unknown. Původní identita následně dohledána čtecím
recover s neprázdným ID a stejnými údaji, bez druhého create. Privátní žádosti,
ID i kalendáře zůstávají mimo Git. Žádný modelový tah ani reálný e-mail,
změna hodinové kopie nebo Data worktree. Příčina přechodně prázdného ID nebyla
určena; samotné místní uložení není důkaz synchronizace na druhé zařízení.

## 2026-11-07 23:41 CET — Měsíční agenda pod připomenutími

Hotovo: Lokální Cockpit pod důležitými připomenutími ukazuje nejprve úkoly
a termíny z kalendářů, potom schůzky a další události na příštích 30 dní.
Poslední načtený přehled se zobrazí ihned a čerstvé čtení běží na pozadí;
obnovuje se při návratu a každé dvě minuty viditelné stránky. Nezpomaluje
hlavní status. Datum aktualizace, tlačítko Obnovit, šest položek a rozbalení
zbytku jsou součástí přehledu. Při chybě zůstanou starší údaje s upozorněním.

Rozhodnutí: Míla upřesnil kalendářové termíny a povolil samostatný vývoj.
Čteme pouze již vybrané kalendáře původním podepsaným helperem, bez změny
macOS oprávnění, bez modelového volání a bez zápisu událostí. Typ přebíráme
z ověřené účtenky Samanthy; starší událost lze přes Typ označit pouze pro
tento přehled. Neznámý typ se nehádá podle názvu ani délky, zůstává mezi
ostatními událostmi. Označení je vázané na přesný kalendář, název a čas;
po jejich změně může být potřeba zopakovat. Stejné duplicitní položky
nelze jednotlivě označit. Žádný nový TVBCP nevzniká.

Další krok: samostatně schválené p+n měsíční agendy. Lokální vývoj hotový,
běžící Cockpit tento nový panel ještě neobsahuje.

Navrhované další kroky: po nasazení Mílova přejímka na Macu/iPhonu.

Technický důkaz: plná brána 2896 testů OK (31 SKIP), finálních 347 cílených
PASS včetně skutečných HTTP ochranných scénářů a Node UI kontraktu. Živé
čtení čtyř vybraných kalendářů PASS, 7 událostí, žádný kalendářový zápis;
původní čtečka i writer beze změny. Safari na syntetických datech ověřilo
rozložení, změnu typu 1/8 → 2/7, zachování po obnově a rozbalení zbytku.
Fyzický iPhone nebyl ověřený. Report reports/calendar_agenda_20261107.md;
logs/calendar_agenda_gate_20261107.log, calendar_agenda_targeted_20261107.log,
calendar_agenda_live_read_20261107.log a calendar_agenda_browser_20261107.log.
Předchozí navigace i jednoduché zadávání již nasazené v 0850e6f3, účtenka
1b8a9680c8b54bf7c48895a8267dc924, CI 42418270872 success; staré čekání
na jejich p+n je historie. Nové p+n tímto povoleno není.

## 2026-11-08 11:54 CET — Rychlé Zadání úkolu s upravitelnou hodinou

Hotovo: Lokální karta Komunikace → Kalendář → Zadání úkolu má jediné
textové pole, tři volby den/měsíc/rok a viditelný čas předvyplněný na 09:00.
Text lze zadat klávesnicí nebo systémovým diktováním iPhonu. Jedno stisknutí
Zapsat úkol potvrzuje přesný text, datum, čas a zobrazený cílový kalendář.
Po ověřeném uložení se text vyprázdní a přehled se obnoví i během cooldownu.
Úkol se automaticky klasifikuje mezi termíny. Samostatný odkaz a manifest
ikony míří přímo na tuto kartu; přidání na plochu provede Míla v Safari.

Rozhodnutí: Míla přijal rychlý formulář a 09:00, výslovně doplnil možnost
hodinu změnit. Pásmo Europe/Prague, typ task_deadline, alarmy 24 h/60 min.
Celý text včetně popisu/místa se uloží do názvu; AI nic nerozděluje.
Současný ověřený writer ukládá termín jako minutovou událost; nejde o
nový zápis do Apple Připomínek. Kolize schůzek nejsou bránou úkolu.
Zvolený kalendář se připne revizí/ID a jeho existence/zápisovatelnost se
ověří nativně při zápisu. Žádný Swift rebuild, nový OS souhlas ani model.

Další krok: samostatně schválené p+n lokálně ověřené nové karty.
Živý Cockpit tuto novou kartu ještě neobsahuje.

Navrhované další kroky: po nasazení Mílova přejímka na iPhonu a jednorázové
Přidat na plochu. Skutečný testovací zápis touto kartou zatím nepotvrzený.

Technický důkaz: 378 cílených testů PASS a posledních 5 HTTP/UI PASS; plná brána 2923 testů OK (31 SKIP).
HTTP testy ověřují skutečné host/origin ochrany, formulář, start_url a PNG.
Node scénáře ověřují 09:00, změnu hodiny, přestupný únor, jediný submit,
ztracenou odpověď, restart, status/recover a stejnou identitu při explicitním
opakování nedoručeného požadavku. Soukromá trvalá účtenka vzniká před
nativní akcí; neznámý výsledek se nikdy nepřeklopí na nový create. Jeden
automatický read-only recover řeší opožděné eventIdentifier v rámci téhož
potvrzení; další obnova je ruční a pouze čtecí. Ověřený nativní reader/writer
beze změny, pouze čtecí kontext nového formuláře PASS. Žádný skutečný event
nebyl vytvořen. Browser host unavailable a Safari cgWindowNotFound: fyzická
Mac/iPhone přejímka je otevřená. Ikona vizuálně zkontrolovaná; vlastní
syntetický QA server ukončený, žádná karta prohlížeče nevznikla.
Důkazy: logs/calendar_task_targeted_20261108.log, calendar_task_gate_20261108.log,
calendar_task_live_read_20261108.log, calendar_task_ui_20261108.log.

## 2026-11-08 12:28 CET — Oprava chyby přípravy úkolu před odesláním

Hotovo: Lokální oprava dovolí použít rychlé zadání také v prohlížeči, kde
není dostupné crypto.randomUUID. Identita zadání vzniká přes silné
crypto.getRandomValues. Při prokazatelném selhání před odesláním se pole
neuzamknou, text/datum/čas zůstávají a lze zkusit odeslání znovu. Pokud
se identita stihla uložit, zachová se původní payload a ověřuje pouze
stejný ID. Při nedostupném či nejasném úložišti je blokované jen další
odeslání; text je přístupný pro zkopírování. Kalendářový backend beze změn.

Rozhodnutí: Míla ohlásil zašedlý formulář a zprávu Zadání se nepodařilo
bezpečně uchovat, Neodesláno, Obnov stránku. Nejde o potvrzenou chybu
macOS zápisu. Při prvním agregovaném serverovém auditu nebyla žádná
účtenka zadání. Stejný stav byl reprodukovaný v profilu bez randomUUID
s funkčním úložištěm. Konkrétní schéma adresy Mílova prohlížeče zatím
nepotvrzené; stejný catch původně schovával také chyby zápisu úložiště.
Předchozí obecná rada obnovit stránku mohla ztratit neuložený text; nová
zpráva jej ponechává. Žádný slabý Math.random ani obcházení idempotence.

Další krok: samostatně schválit p+n ověřeného nového opravného commitu. Současný živý základ 6c610287 byl skutečně
Terrou nasazený (d7ac821490a17273e18be1de270b9ba8, 2923, smoke 5/5,
CI 42474671842 success); neprohlašovat opravu za nasazenou.

Navrhované další kroky: po nasazení Mílův retest na stejné adrese.

Technický důkaz: red→green Node regrese HTTP bez randomUUID, test
chyby setItem s editovatelným formulářem a následným jediným POST,
částečného uložení s read-only status a stejným ID, absence silného RNG
bez odeslání. 26 cílených PASS; plná brána 2923 testů OK (31 SKIP).
Důkazy logs/calendar_task_storage_repro_before_20261108.log,
calendar_task_storage_node_20261108.log, calendar_task_storage_targeted_20261108.log,
calendar_task_storage_gate_20261108.log a calendar_task_storage_diagnosis_20261108.log.
Žádný skutečný kalendářový zápis ani změna helperů/grantů/modelů.
Čtecí inventář UI: žádné připojené browser tabs a žádné Safari okno;
přímá přejímka Mílova prohlížeče nebyla dostupná.


## 2026-11-08 18:22 CET — Hodinové kalendářové návrhy se zachováním ručního průchodu

### Hotovo
- Volitelný doplněk nového e-mailového posouzení připraví schůzku nebo termín
  s původním citačním kontraktem. Není potřeba druhý modelový průchod ani další
  načtení pošty pro otevření připraveného návrhu.
- Stejné tlačítko Do kalendáře předá výsledek do stejného čtyřpolového editoru.
  Původní kolize, výslovný zápis, alarmy 24 h/60 min a čtecí obnova se používají dál.
- Staré karty nemigrují a zůstávají na původní ruční cestě. Existující rozpracovaný,
  nejistý nebo zapsaný návrh má před doplňkem přednost a nelze jej importem přepsat.
- Chybná volitelná citace nezahodí e-mailový koncept; v přehledu zůstává viditelný
  agregovaný problém. Formální pozvánky/opakování dál vyžadují ruční zpracování.

### Rozhodnutí
- Míla schválil navázání na bod 7 s podmínkou zachovat fungující implementaci.
- Doplňující obálka je mimo EmailProposal i jeho potvrzovací digest; starý
  e-mailový editor, archiv a odesílání zachovávají svůj dosavadní kontrakt.
- Výchozí calendar_suggestions=false. Aktuální service.json, modelové role,
  instalovaná hodinová kopie, pomocníci EventKit a jejich OS souhlasy beze změny.
- Ikony c14f2524 jsou odložené, nejde o jejich nové p+n. Chráněný obnovovací TXT
  ani Datův worktree se nemění. Poslední živě ověřený Cockpit je f51f3412.

### Další krok
- Převzít lokální změnu; před zapnutím zvlášť přijmout ruční Mac/iPhone
  průchod a domluvit p+n/registrovaný upgrade vlastní hodinové kopie.

### Navrhované další kroky
- Po kompatibilním Cockpitu i službě teprve výslovně zapnout doplněk pro nové zprávy.
- Na vybraném skutečném e-mailu ověřit správnost návrhu a cenu celého posouzení.
- Změřením porovnat dobu/usage; jeden tah není důkaz stejné ani nižší ceny.

### Technický důkaz
- 214 cílených testů PASS, včetně 20 nových doménových/adapterových scénářů
  a HTTP průchodu, import → kolize → potvrzení → jeden syntetický zápis.
- Existující source_context přemístěný beze změny AST. Browser kontrakty e-mailu
  a kalendářové karty PASS. Závěrečná plná brána 3199 testů OK (31 SKIP); logs/calendar_hourly_full_gate_v2_20261108.log.
- Žádný skutečný modelový test, e-mailový send, kalendářový zápis/mazání, p+n
  nebo servisní aktivace. Skutečná modelová kvalita, spotřeba a fyzická přejímka otevřené.


## 2026-11-09 11:30 CET — Obnovený hodinový e-mailový agent po nekompatibilní roli

### Hotovo
- Vlastní hodinová kopie je registrovaně upgradovaná z f2d6ef79 na již
  publikovaný617f3e0d. Installed/owned/loaded/enabled a skutečný parser PASS.
- První skutečná kontrola dnešního slotu11:00 dokončena v11:28:47 CET:
  7 nových zpráv,3 karty k potvrzení a4 zprávy hodinového přehledu. Živé
  Cockpit overview API ověřilo3 karty a3 přehledové zprávy; poslední nedůležitá
  zpráva je skrytá již existující visibility předvolbou. Všech7 položek je ve
  stavu zachovaných, soukromý obsah se neopisuje.
- Při systémovém přepnutí celý business stav, nastavení a všechny role
  shodné s předchozím snapshotem. Po běžném dočtení jsou všechny původní
  položky beze změny; zdrojové pozice se posunuly až zpracováním nových zpráv.

### Rozhodnutí
- Míla potvrdil přesnou globální brzdu i následné p+n. Použity pouze
  registrované pause/prepare/upgrade; starý release a servisní záloha zachované.
- Příčina: sdílený agent_roles.json již obsahoval recovery_document_maintainer,
  ale parser instalované f2d6ef79 ji neznal. AgentRoleError byl reprodukovaný
  právě v instalované kopii, před IMAP a modelem. Poslední dokončený slot
  před opravou8.11.20:00. Runtime nezačal zpracovávat dnešní poštu až do opravy.
- Terra/high, oba poskytovatelé, bez denního stropu a calendar_suggestions=false
  zachované. Žádná změna přístupů ke schránkám nebo recovery služby.
- Nový kód nebyl potřeba. Dokončovací commit obsahuje pouze Git-safe provozní
  záznam; Python služby se po něm nemění a nevyžaduje druhé přepnutí runtime.

### Další krok
- Dokončit výslovně schválené registrované p+n tohoto záznamu v project-email-cases.
  Autorita výsledku je původní účtenka a logs/email_role_compat_release_20261109.log.

### Navrhované další kroky
- Míla obnoví přehled Cockpitu a převezme3 nové karty.
- Při další nové roli předem ověřit všechny skutečné runtime parsery sdíleného JSON,
  včetně hodinové služby; samotný kompatibilní main nestačí.

### Technický důkaz
- reports/email_hourly_role_compat_20261109.md; logs/email_role_compat_upgrade_20261109.log.
- Soukromé důkazy jen v service_audits/role_compat_upgrade_20261109_1127:
  baseline, připravený plán, switch_checks, verified, první dokončený běh a HTTP projekce.
- Všechny kontroly přepnutí true; aktuální7 modelových posouzení jsou běžný
  již schválený příjem čekající pošty, ne opakování nejistého starého pokusu.
- První health completed, chybové posouzení0, zdrojové pozice posunuté;
  všechny původní položky shodné. Fyzická Mac/iPhone přejímka nepředstíraná.

## 2026-11-11 21:41 CET — Hlídání záležitostí, první implementační krok

### Hotovo
Hlídání záležitostí — etapa 1 je lokálně implementovaná jako ruční backend.
Založení, čtení/detail, úprava, Hlídání/Vyřízeno a obnovení používají stejnou
identitu, revize, generaci a trvalou doménovou účtenku. Žádný automatický monitor
ani UI nejsou připojené; API výslovně vrací automatic_monitoring=false.
Zdrojové karty, kurzory, přílohy, modelové role a běžící služba zachované.
Ověření: 22 doménových + 5 HTTP scénářů; cílené běhy 89/51/54 testů PASS.
Plná povinná brána: 3514 testů OK (31 SKIP), 504,079 s. Důkazy mimo Git: data/private/email_followups_step1_20261111/.
Další krok: etapa 2 — formulář, přepínač a přehled nad tímto kontraktem.
Dokumentační blokátor uzavření celého proudu: samostatný e-mailový TVBCP není
výslovně dohodnutý. Nevznikl nový ani náhradní obecný TVBCP. P+n této etapy
ani aktivace sledování nebyly zadány. Datův worktree zůstává nedotčený.

### Rozhodnutí
Míla schválil zahájení prvního kroku podle návrhu v Downloads
Samantha_hlidani_zalezitosti_navrh_vyvoje_2026-11-11.txt. Jde o doménu a HTTP,
bez rozšíření na následující UI, IMAP vazby či automatické kontroly. Vývoj dělá
Will v izolované větvi nad2106bead; není spuštěná Luna ani placený pilot.

### Kontrakt pro návazné UI
- GET /api/email-agent/followups vrací active/completed; volitelné jediné id
  vrátí detail. GET nevytváří úložiště a neposílá modelový požadavek.
- POST na stejnou cestu má action=create/update/set_state a stabilní operation_id.
- create: source_item_id a fields s title, goal, next_step, waiting_on, check_at.
  Zdroj se bere z uložené důležité karty, nikoli z klientem dodané cesty či těla.
- update: id, expected_revision a úplné fields. waiting_on je me/other/review/unknown.
- set_state: id, expected_revision, state=active/completed; při obnovení lze
  dodat nový check_at. Propadlý čas vyžaduje nový budoucí čas, bez tichého posunu.
- Časy vyžadují pásmo a ukládají se v UTC. Chybějící follow-up znamená nesledováno.
- API kódy: 400 neplatné údaje, 404 neznámý zdroj/záležitost, 409 konflikt,
  503 nedostupné/poškozené úložiště. Změny zachovávají originální e-mailový stav.
- Každá odpověď obsahuje monitoring=not_connected; frontend zatím nesmí slibovat,
  že automatické hlídání běží. Žádný nový model, IMAP, send ani kalendářový zápis.

### Ověření a rizika
Testy ověřily dvojklik, dvě instance, restart, souběžné editace, starou revizi,
ztracenou odpověď, poškozený/novější formát, neplatné časy, CSRF, zachování
při archivaci/skrytí a retry i po vyřazení obecné cache operation_id.
Doménový journal ověřuje otisk celého příkazu a při replay vrací aktuální stav,
nikoli starou projekci. Hlavičkové párování vlákna je teprve etapa 3;
source.thread_binding=pending není důkaz souvislosti s další zprávou.

### Další krok
Navázat etapou 2 podle dohodnutého návrhu; přesný lokální commit a zarovnání
profilů doloží integration.json v uvedené soukromé složce; veřejné vydání a servisní aktivace jsou samostatné.
Samostatný TVBCP zůstává výslovně označený dokumentační blokátor uzavření proudu.
