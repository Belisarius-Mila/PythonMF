# Rodinný kalendář

Aktuální stav 18. 11.: SMS/RCS nasazené a aktivní. Test doručen, první automatický pokus zastavený před odesláním. Příčina čeká na čtecí diagnostiku podle kanonického handoffu.

## 2026-11-17 22:06 CET — Soukromé SMS v den rodinné události, vývoj bez aktivace

Hotovo: Samostatné SMS pravidlo pro jednu příjemkyni je připravené místně.
V den narozenin/svátku od09:00 Europe/Prague, pozdější hodinová kontrola
událost tentýž den dožene. Další den už včerejší SMS nevytváří. Respektuje
aktivní osoby a jejich reminders_enabled. Osobní oslovení/telefon a konkrétní
náhled jsou jen v soukromém vypnutém návrhu; nikdy v Git/docs.
Rozhodnutí: Míla zadal vývoj a následně výslovně schválil jednu testovací
SMS po dokončení lokálního commitu. Automatický provoz přesného pravidla
vyžaduje samostatný souhlas; vývoj, commit ani p+n jej nezapínají. Původní e-mailové D-2/D-1/D-0 příjemce a evidenci
neměníme; používá se existující hodinový dispatcher, bez nového LaunchAgentu.
Další krok: Po lokálním commitu provést jediný schválený test SMS se
stabilní identitou. Výsledek bude v soukromém completion.json; nejistý
pokus se neopakuje. Poté samostatné p+n a až po doloženém testu zvlášť
potvrzená aktivace přesného pravidla.
Navrhované další kroky: Fyzické přijetí testu a ověření skutečného běhového
kontextu Zpráv/iPhonu, potom první přirozená kontrola a živý stav v Cockpitu.
Technický důkaz:115 cílených kontrol PASS (SMS/hodinový kalendář, Messages,
Cockpit/JS, registry/workflow). Zahrnují souběh, letní/zimní čas, probuzení,
půlnoc během preflightu i zápisu záměru, vypnutá připomenutí, nové roční události, poškozený/
chybějící ledger a havárii před/po transportu. SQL potvrzení vyžaduje novější
ROWID, přesný plný telefon, přesný text a službu SMS; jiné texty/příjemci,
staré řádky, duplicitní shody nebo nečitelný attributed-only text zůstanou unknown.
Sending je trvalé před transportem. Opakuje se pouze prokazatelný preflight
not_sent nejdřív za1h, nejvýše24 pokusů; sent/delivered/failed/unknown/sending
se automaticky neopakují. Ztracené dokončení zůstává sending a je viditelné.
SMS chyba neblokuje e-mail a e-mailová chyba neblokuje SMS. Ruční replay
s --today nebo jinými argumenty SMS větev nikdy nespustí. Stav SMS v Cockpitu
je samostatný a redigovaný i při neověřeném e-mailovém stavu.
Soukromý návrh má700/600,0 doručovacích záznamů a enabled=false. Žádný skutečný
Messages send, model, změna systémových oprávnění, plánovače nebo e-mailového
nastavení. Vstupní živý audit ověřil původní automatiku active/0 blokátorů
s hodinovým policy; jeho aktivaci neopakovat.
Meze: Ověření skutečného SMS transportu, oprávnění Zpráv pro běhový proces
a doručení přes iPhone nejsou simulací potvrzené. Nedoložený výsledek se
přizná, neoznačí za doručený. Kódový proof neznamená zapnutou automatiku.
Finální brána/head/stav: private family_calendar/sms_development_20261117/
completion.json (targeted_tests.log, final_gate.log, private_preview.json).


## Kanonická identita

- Pracovní proud: `project-family-calendar`
- Typ: `Project`
- Režim: `active`
- Priorita: `1`
- Rodinný kalendář je samostatný projekt a nepatří do Knihovny článků.
- Dřívější vývoj pouze technicky používal izolovaný workspace Knihovny.

## Aktuální stav

## 2026-11-16 12:27 CET — Hodinové kontroly připravené místně

Hotovo: hodinové kontroly od08:00 do23:00 a kontrola při spuštění služby,
bez odesílání před08:00 v Europe/Prague. Poslední dohnání v den události
(D-0), pouze pokud předchozí pokusy nebyly přijaté ani nejisté. Prokazatelné
NOT_SENT lze opakovat s novým číslem pokusu, původní doklad se nepřepisuje;
nejvýše24 pokusů pro jeden den/offset. SMTP_ACCEPTED, PARTIAL, SENDING nebo
DELIVERY_UNKNOWN nepovolují automatické opakování. Hotové události se
přeskočí před čtením hesla. Dřívější záznamy bez attempt se čtou jako pokus0.

Rozhodnutí: Míla schválil zpevnění, změnil navržený interval15min na1hodinu
a potvrdil nalezení domněle chybějící zprávy. Živý audit ověřil automatiku
enabled,12 dokladů a0 blokátorů; obě dotčené zprávy byly nalezené v INBOX.
Žádné osoby, data narození, adresy ani texty zpráv se do zápisu neukládají.

Další krok: dokončit nyní výslovně schválené p+n kompatibilního Cockpitu a poté
registrované family_calendar_hourly_schedule: nový preview a apply se
shodným otiskem, potvrzeným rozsahem a již platnou globální brzdou. Před
přepnutím ověří načtený kód, uloží původní plist a stav přechodu. Při nejistém
bootstrap se nic neopakuje ani nezastavuje možný odesílající worker.
RunAtLoad může spustit již schválenou automatiku; nový rozsah se povolí
samostatným soukromým policy.json teprve při této aktivaci. Do té doby
zůstává původní denní D-2/D-1 provoz. Míla následně výslovně zadal „pokračuj p+n“; toto vydání je tedy schválené.

Navrhované další kroky: ověřit první přirozenou hodinovou kontrolu; stavy
PARTIAL/DELIVERY_UNKNOWN nadále řešit ručně bez automatického retry.

Technický důkaz:245 kalendářových testů PASS,13 nových scénářů (souběh,
D-0, staré doklady, oddělené retry, havárie, limit, noční blokace, načtený
reader, změněný plán a nejistý bootstrap). Živě pouze read-only preview;
žádné odeslání ani změna LaunchAgentu/Keychain. Konečná brána, commit a
navazující aktivace mají soukromý doklad family_calendar/hourly_development/
development.json. Fyzická přejímka nové automatiky zatím neproběhla.


- 2026-10-17 14:41 CEST: zobrazení bezpečného stavu je v Cockpitu pushnuté a řízeně
  nasazené (kód `ae30beddcdfd`, nový proces, smoke 5/5). Živý GET po nasazení
  potvrdil aktivní režim a bezpečnou projekci s časem; konfigurace automatiky
  ani odesílání se nemění. Důkaz drží proud `project-cockpit` a jeho release logy.
- 2026-10-17 13:33 CEST: v proudu Cockpit je lokálně připravená náhrada nepravdivého
  pevného textu o vypnutém odesílání. GET `/api/family-calendar/delivery-status`
  vrací jen bezpečný souhrn registrovaného read-only auditu a čas kontroly;
  nečte tajemství, neodesílá a nic nezapisuje. Rozlišuje režimy a překážku,
  při nedostupnosti přiznává neověřený stav. Změna neaktivuje ani nevypíná
  automatiku. Nasazení zatím neproběhlo; kanonický důkaz v `project-cockpit`.
- Živý redigovaný read-only audit 2026-08-01 12:04 CEST potvrdil
  `config_mode=enabled`, `automation_active=true`, `planner_ready`, čtyři
  nakonfigurované příjemce a nula blokujících stavů. Nebyl evidován žádný stav
  `sending`, `partial` ani `delivery_unknown`. Audit nic nezapsal, nečetl
  tajemství a nevolal transport.
- Existuje registr osob, validace, výpočet rodinných událostí a věku.
- Jednorázové předvyplnění proběhne pouze nad prázdným soukromým registrem.
- Editace je v mobilním Cockpitu dostupná přes viditelné `Upravit údaje`.
- Kandidáti upozornění podporují D-2 a D-1. Cílový provoz používá jeden
  společný e-mail pro čtyři pevné příjemce uložené pouze v soukromé
  konfiguraci; příjemci o sobě mohou vědět.
- Čistý builder náhledu upozornění je implementovaný v commitu `531ed75`:
  přijímá hotovou událost a přesně dva různé explicitní příjemce a vrací D-2/D-1,
  věk, režim `scheduled`/`catch_up`, předmět a tělo bez I/O nebo odesílání.
- Commit `021adf5` doplnil do Cockpitu read-only sekci `Náhled upozornění`:
  přijímá přesně dvě serverově validované adresy, události odvozuje pouze ze
  soukromého registru a nic neodesílá ani nepersistuje.
- Odpověď náhledu se necachuje, UI vykresluje dynamický obsah přes `textContent`
  a po zavření okna adresy z formuláře vymaže.
- Cílených 22 kalendářových testů, plná Cockpit brána s 983 testy, vzdálená
  GitHub Gate a živý smoke test 5/5 prošly.
- Míla 2026-07-22 ručně potvrdil, že read-only náhled v Cockpitu funguje.
- Doručovací pipeline má per-recipient stav, privátní atomickou persistenci,
  recovery, idempotenci, jedno-workerový koordinátor, dry-run orchestrátor,
  SMTP adaptér a samostatný přesně potvrzovaný jednorázový runner.
- Soukromá konfigurace je oddělená od Gitu a běžný provoz zůstává v neostrém
  režimu; automatické odesílání není aktivní.
- Dva dřívější živé testovací pokusy skončily jako `delivery_unknown`.
  Pozorované doručení bylo nulové, ale staré pokusy nelze zpětně označit za
  jistě neodeslané a nesmějí se automaticky opakovat.
- No-send autentizační diagnostika a envelope preflight později potvrdily
  funkční přihlášení a přijetí odesílatele i všech čtyř příjemců bez volání
  `DATA` nebo odeslání.
- Commit `d38a37f` oddělil potvrzení `DATA` od následného `QUIT`: potvrzené
  přijetí se při chybě ukončení relace zachová, zatímco bez potvrzení `DATA`
  zůstává výsledek `delivery_unknown`.
- Hotfix je na `main` a `origin/main`, je nasazený a ověřený 158
  kalendářovými testy, plnou bránou 1134 testů, vzdálenou Quality Gate a
  smoke testem 5/5.
- Po nasazení hotfixu proběhl právě jeden nový ručně a přesně potvrzený test.
  SMTP server přijal 4/4 příjemců, nikoho neodmítl, nezůstal žádný neznámý
  výsledek a relace se korektně ukončila. Míla potvrdil skutečné doručení 4/4.
- Jednorázová testovací brána je úspěšně uzavřená. Automatické D-2/D-1
  odesílání zůstává vypnuté.
- Read-only kontrola připravenosti ověřuje konfiguraci, stavové úložiště,
  recovery, plánovač a existenci Keychain reference bez čtení hesla, zápisu
  nebo odesílání.
- Dedikovaný plánovací vstup `family_calendar_delivery_run.py` bezpečně
  rozlišuje `disabled`, `dry_run` a `enabled`. Ostrá větev je dostupná pouze
  při skutečně aktivním režimu `enabled`; současný živý provoz zůstává
  `dry_run`.
- Kalendářová regrese 167 testů a plná Cockpit brána 1143 testů prošly.
- Readiness už neblokuje chybějící runner; automatika dále zůstává bezpečně
  blokovaná chybějící instalací plánovače, Keychain referencí a automatickým
  režimem.
- Read-only náhled budoucí LaunchAgent konfigurace validuje absolutní cestu
  k Pythonu a runneru, denní čas, `RunAtLoad=false` a proces typu
  `Background`. Výstup je pouze JSON a nemá apply, instalační ani load cestu.
- Živý náhled pro 08:00 prošel bez vytvoření plist, volání `launchctl`, čtení
  Keychain, transportu nebo jiného zápisu. Kalendářová regrese 171 testů a
  plná Cockpit brána 1147 testů prošly.
- Dvoukroková instalační brána nejprve vrací přesný plist, create-only cíl,
  fingerprint a vyžadovanou potvrzovací větu. Apply znovu ověřuje nezměněný
  fingerprint, režim `dry_run`, Python, runner a nepřítomnost cíle.
- Potvrzený zápis používá atomické create-only uložení s právy `0600`;
  existující soubor ani symlink nepřepíše. Brána nemá cestu k `launchctl`,
  Keychain ani transportu.
- Zápisová větev byla ověřena pouze v dočasných adresářích. Živě proběhl jen
  read-only preview a systémový plist nevznikl. Kalendářová regrese 177 testů
  a plná Cockpit brána 1153 testů prošly.
- Plist byl následně samostatně potvrzeným create-only krokem vytvořen, ale
  zůstává nenačtený; `launchctl` plánovač nespustil.
- Dvoukrokový Keychain setup nejprve ukazuje pouze redigovanou identitu položky
  a vyžaduje přesnou potvrzovací větu. Heslo přebírá skrytý systémový prompt,
  nepředává je v argumentech procesu a existující položku nepřepisuje.
- Samostatně potvrzené živé zadání vytvořilo pouze Keychain reference.
  Následný read-only readiness audit hodnotu hesla nečetl, nic nezapsal ani
  neodeslal a uzavřel blokátor chybějící reference.
- Kalendářová regrese 185 testů a plná Cockpit brána 1167 testů prošly.
  Zbývají dva blokátory automatiky: nenačtený plánovač a nedostupný automatický
  režim. Konfigurace zůstává `dry_run`.
- Read-only náhled budoucího načtení LaunchAgentu vrací přesné datové kroky
  `bootstrap`, ověření přes `print`, rollback přes `bootout` a závěrečné
  ověření odpojení. Nemá `--apply`, příkazy nespouští a před budoucím
  načtením vyžaduje samostatné potvrzení.
- Náhled fail-closed ověřuje režim `dry_run`, vlastnictví a práva plist
  `0600`, `RunAtLoad=false`, proces typu `Background`, bezpečný `launchctl`
  a fingerprint konfigurace i plist.
- Živý read-only náhled prošel bez issues. Následný readiness audit stále
  potvrdil `planner_not_loaded`; nic nebylo zapsáno, načteno ani odesláno.
  Kalendářová regrese 189 testů a plná Cockpit brána 1171 testů prošly.
- Potvrzovaná load brána vyžaduje globální bezpečnostní větu, samostatné
  `LOAD_FAMILY_CALENDAR_DRY_RUN_PLANNER` a shodný fingerprint. Těsně před
  `bootstrap` znovu ověřuje všechny vstupy a přesný stav nenačtené služby.
- Po pokusu brána ověřuje runtime stav přes `print`. Rozlišuje `loaded`,
  `unloaded` a `unknown`; při neznámém výsledku provede `bootout`, znovu
  probuje stav a zakáže automatický retry, pokud rollback není potvrzený.
- Simulované testy nevolaly skutečný `launchctl`. Živě proběhl pouze read-only
  `print`, který vrátil kanonický kód nenačtené služby; readiness nadále hlásil
  `planner_not_loaded`. Kalendářová regrese 198 testů a plná Cockpit brána
  1180 testů prošly.
- Po samostatné globální a lokální potvrzovací větě a ověření shodného
  fingerprintu byl dry-run LaunchAgent úspěšně načten. `bootstrap` skončil
  nulovým návratovým kódem, následný probe potvrdil `loaded` a rollback nebyl
  potřeba.
- Konfigurace zůstala `dry_run`, automatické odesílání vypnuté a při načtení
  nedošlo ke čtení tajemství, volání transportu ani odeslání zprávy.
- První naplánovaný dry-run proběhl 2026-07-24 v 08:00. Read-only audit v
  08:10 CEST potvrdil `runs=1`, poslední návratový kód `0`, stav
  `not running` a celkovou připravenost `planner_ready`.
- Stavový ani worker soubor nevznikl; nebyl evidován žádný záznam ve stavu
  `sending`, `partial` nebo `delivery_unknown`. Automatika zůstává neaktivní.
- Read-only náhled budoucí aktivace přesně popisuje jedinou zamýšlenou změnu
  `dry_run` na `enabled`, provozní předpoklady, D-2/D-1 podmínky, idempotenci,
  pořadí odpojení a načtení plánovače i fail-closed rollback.
- Runtime režim `enabled` je implementovaný. Používá atomickou persistenci
  `sending` před transportem, jedno-workerový zámek, D-2/D-1 idempotenci,
  recovery přerušených pokusů, pevnou Keychain identitu a existující
  redigovaný iCloud SMTP adaptér.
- Přerušené `sending` se při recovery změní na `delivery_unknown`.
  Jakýkoli `partial` nebo `delivery_unknown` globálně zastaví další
  automatické pokusy do ručního auditu; automatický retry zůstává zakázaný.
- Keychain tajemství se čte až po ověření režimu, recovery a nalezení
  kandidáta. Není předáváno v argumentech procesu ani zobrazováno v bezpečném
  výsledku. `disabled` a `dry_run` Keychain ani SMTP nevolají.
- Potvrzovaná aktivační apply brána je implementovaná. Před změnou znovu
  ověřuje fingerprint a předpoklady, odpojí plánovač, atomicky změní pouze
  režim, konfiguraci ověří, plánovač znovu načte a dokončí readiness audit;
  nejasný stav vede k ověřovanému rollbacku bez automatického retry.
- Živý read-only náhled prošel bez issues a potvrdil připravenou konfiguraci,
  načtený plánovač, Keychain reference a prázdný neblokující stav. Neprovedl
  zápis, runtime mutaci, čtení hesla ani transport.
- Kalendářová regrese 218 testů a plná Cockpit Quality Gate 1252 testů
  prošly. Kontrolní běh živého plánovače zůstal `dry_run`, našel nula
  kandidátů, nevolal koordinátor ani transport a nezměnil konfiguraci nebo
  stavové úložiště.
- Implementační checkpoint aktivační brány prošel 1217 testy a je obsažený v
  nasazeném `main`. P6a záměrně nečetlo současný soukromý režim a projektová
  paměť jej proto do živého auditu 2026-08-01 vedla jako neověřený.

## Bezpečnostní hranice

- Soukromý registr osob, narozeniny a kontaktní adresy nepatří do Gitu ani do
  projektové paměti.
- Skutečné adresy, přihlašovací údaje a obsah zprávy nesmějí být v Gitu,
  paměti ani testech. App-specific heslo se zadává pouze skrytě mimo chat.
- `delivery_unknown` je fail-closed: automaticky neopakovat a nepovažovat
  chybějící pozorované doručení za důkaz neodeslání.
- Úspěšný jednorázový test sám nezapíná automatiku. Automatické odesílání se
  smí zapnout až po samostatné read-only revizi provozní cesty a novém Mílově
  rozhodnutí.

## Nejmenší další krok

Bez nové aktivace nebo testovacího odeslání. První přirozený plánovaný výsledek
sledovat pouze redigovaně. Každý další dotaz na aktuální režim, readiness nebo
plánovač znovu ověřit živým read-only auditem, protože tento provozní stav je
proměnlivý a git-safe paměť je pouze časovaný snapshot.

## Otevřené riziko

Stav `partial` nebo `delivery_unknown` správně zastaví další automatiku, ale
zatím neexistuje samostatný potvrzovaný workflow pro jeho ruční uzavření.
Takový workflow se nesmí spojovat s aktivační branou ani automatickým retry.

## 2026-11-17 22:28 CET — Doručený původní test a schválené zapojení

Hotovo: Jediný schválený test byl po lokálním commitu odeslán a doručen.
Zprávy jej převedly na RCS; uživatel potvrdil doručení. Ověření původního
nového řádku nyní prokazuje plný kontakt, přesný dekódovaný text a delivered.
Nevznikl druhý pokus. Automatické pravidlo je před nasazením stále vypnuté.
Rozhodnutí: Míla výslovně schválil p+n a následné zapojení automatických
upozornění témuž soukromému kontaktu od09:00 v den narozenin/svátku;
hodinové dohnání jen tentýž den. Mac může zprávu odeslat jako SMS nebo RCS.
Další krok: Dokončit kontrolu a commit opravy, schválené p+n registrovanou
cestou a teprve po potvrzeném nasazení zapnout přesný soukromý policy.
Navrhované další kroky: Ověřit první přirozený hodinový běh a stav v Cockpitu.
Technický důkaz:118 cílených kontrol PASS. Chybějící import json v agentovém
obalu opraven; syntetické testy nyní skutečně volají registrované FunctionTool
status/preview/control, včetně verify a chybové větve. Foundation dekóduje
vlastní attributedBody bez aktivace aplikace; nečitelný text, jiný příjemce,
iMessage a více přesných shod dál zůstávají unknown. Ověření původního testu
má transport_called=false, delivered1/unknown0/attention0; enabled=false.
Soukromé důkazy, finální head/brána a následná aktivace budou v
family_calendar/sms_development_20261117/completion.json. Při nejistotě žádný
nový send. Odeslání přes vlastněný hodinový launchd kontext ještě nebylo
fyzicky potvrzené; test proběhl v terminálovém běhovém prostředí.
