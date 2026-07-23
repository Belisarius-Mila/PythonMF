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
- Dedikovaný plánovací vstup `family_calendar_delivery_run.py` je omezený
  pouze na existující provozní dry-run. Živá redigovaná zkouška nevolala
  koordinátor ani transport a nevytvořila stavový nebo worker soubor.
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

Samostatně navrhnout dvoukrokovou instalační bránu pro vytvoření plist pouze
v režimu `dry_run`: nejprve přesný náhled, potom zvláštní potvrzení zápisu.
V této další fázi ještě plánovač nenačítat přes `launchctl`, nepracovat s
Keychain, neměnit automatický režim a nic neodesílat.
