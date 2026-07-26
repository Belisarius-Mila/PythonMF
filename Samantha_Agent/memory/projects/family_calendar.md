# Rodinný kalendář

## Kanonická identita

- Pracovní proud: `project-family-calendar`
- Typ: `Project`
- Režim: `active`
- Priorita: `1`
- Rodinný kalendář je samostatný projekt a nepatří do Knihovny článků.
- Dřívější vývoj pouze technicky používal izolovaný workspace Knihovny.

## Aktuální stav

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
- Aktivační náhled po implementaci nemá implementační blokátor a potvrzuje
  podporu cílového režimu. Stále ale nemá zápisovou apply větev:
  `activation_implementation_available=false` a `apply_available=false`.
- Živý read-only náhled prošel bez issues a potvrdil připravenou konfiguraci,
  načtený plánovač, Keychain reference a prázdný neblokující stav. Neprovedl
  zápis, runtime mutaci, čtení hesla ani transport.
- Kalendářová regrese 218 testů a plná Cockpit Quality Gate 1252 testů
  prošly. Kontrolní běh živého plánovače zůstal `dry_run`, našel nula
  kandidátů, nevolal koordinátor ani transport a nezměnil konfiguraci nebo
  stavové úložiště.

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

Samostatně implementovat potvrzovanou aktivační bránu podle už schváleného
pořadí: znovu ověřit fingerprint a předpoklady, odpojit plánovač, atomicky
změnit pouze režim na `enabled`, konfiguraci ověřit, znovu načíst plánovač a
ověřit readiness. Do té doby režim neměnit a nic automaticky neodesílat.

## Otevřené riziko

Stav `partial` nebo `delivery_unknown` správně zastaví další automatiku, ale
zatím neexistuje samostatný potvrzovaný workflow pro jeho ruční uzavření.
Takový workflow se nesmí spojovat s aktivační branou ani automatickým retry.
