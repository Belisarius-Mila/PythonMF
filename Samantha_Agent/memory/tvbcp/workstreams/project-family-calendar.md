<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obsahově narovnáno P6b: 2026-07-30 07:25 CEST

### Hotovo
- Potvrzovaná aktivační apply brána je implementovaná včetně revalidace,
  odpojení plánovače, atomické změny režimu a ověřeného rollbacku.
- Aktuální `main` `20180e2` je serverově nasazený a Cockpit smoke prošel 5/5.

### Otevřeno
- Současný živý režim, readiness a stav plánovače nebyly v P6a čteny ze
  soukromé konfigurace a zůstávají neověřené.
- Samostatný potvrzovaný workflow pro ruční uzavření blokujícího
  `partial` nebo `delivery_unknown` není doložený.

### Rizika
- Neověřený režim se nesmí domýšlet a nejisté doručení se nesmí automaticky
  opakovat.

### Další krok
- Provést pouze redigovaný read-only audit živého režimu, readiness a
  plánovače; aktivační apply neopakovat podle staré paměti.

### Rozhodnutí
- Implementovaná aktivační brána není důkazem současného režimu ani pokynem k
  dalšímu odeslání.

### Navrhované další kroky
- První přirozený plánovaný výsledek sledovat pouze přes redigovaný stav.
- Stavy `sending`, `partial` a `delivery_unknown` ponechat fail-closed.

### Technický stav checkpointu
- Implementační checkpoint aktivační brány prošel 1217 testy.
- Deployment účtenka: `20180e2`, stav `deployed`, smoke 5/5.
- P6a nečetlo soukromý režim ani tajemství.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Rodinný kalendář

Pracovni proud: `project-family-calendar`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-07-22 08:48 CEST – Čistý builder náhledu D-2/D-1 a cílené testy jsou hotové

Pracovní proud: `project-family-calendar`.

Milník: Čistý builder náhledu D-2/D-1 a cílené testy jsou hotové

Důkaz: plná Cockpit brána: 980 testů, 208.3 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Potvrdit checkpoint tohoto kroku v Cockpitu

### 2026-07-22 11:03 CEST – Dokumentační uzavření builderu a doplnění CI triggeru

Implementační checkpoint je dokončen: commit `531ed75` je na `main` a
`origin/main`. Dřívější další krok „Potvrdit checkpoint“ tímto novějším
záznamem pozbývá platnosti.

Kanonická projektová paměť, aktivní registr a handoff nyní popisují hotový
čistý builder. GitHub Cockpit Quality Gate nově sleduje
`app/family_calendar.py` a `tests/test_family_calendar*.py` při pull requestu
i pushi. Změna nezasahuje aplikaci, soukromá data, odesílání ani persistence
doručení.

Ověření: 28 cílených testů prošlo. Plná lokální Cockpit Quality Gate prošla
s 980 testy za 208.0 s a zahrnula čistý `git diff --check`.

Další krok: navrhnout samostatné read-only zobrazení náhledu v Cockpitu,
stále bez odesílání a bez persistence doručení.

### 2026-07-22 12:01 CEST – Cockpit bezpečně zobrazuje náhledy D-2/D-1 bez odesílání a persistence

Pracovní proud: `project-family-calendar`.

Milník: Cockpit bezpečně zobrazuje náhledy D-2/D-1 bez odesílání a persistence

Důkaz: plná Cockpit brána: 983 testů, 304.3 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Potvrdit checkpoint a potom ručně ověřit náhled na Macu nebo iPhonu

### 2026-07-22 13:20 CEST – Ruční potvrzení read-only náhledu a srovnání stavu

Implementační checkpoint je dokončen: commit `021adf5` je na `main` a
`origin/main`. Dřívější další krok „Potvrdit checkpoint a potom ručně ověřit
náhled“ tímto novějším záznamem pozbývá platnosti.

Míla ručně potvrdil, že sekce `Náhled upozornění` v Cockpitu funguje.
Ověření dále zahrnuje 22 kalendářových testů, plnou Cockpit bránu s 983 testy,
úspěšnou vzdálenou GitHub Gate a živý smoke test 5/5. Náhled nic neodesílá ani
nepersistuje a automatické odesílání zůstává vypnuté.

Projektová paměť, aktivní registr, aktuální souhrn handoffu a TVBCP nyní
odpovídají skutečně dokončenému stavu.

Další krok: zahájit samostatnou read-only fázi návrhu jednoho ručně
potvrzovaného testovacího e-mailu; zatím nic neodesílat ani nezapínat
automatiku.

### 2026-07-22 14:19 CEST – Cílový model čtyř pevných příjemců a automatického odesílání

Míla rozhodl, že cílový provoz bude používat čtyři pevné e-mailové adresy
uložené pouze v soukromé konfiguraci Samanthy mimo Git, projektovou paměť a
testy. Všem čtyřem příjemcům se odešle jeden společný e-mail a příjemci o sobě
mohou vědět. Po bezpečném zprovoznění má běžné odesílání probíhat automaticky
bez ruční kontroly jednotlivých zpráv.

D-2 je standardní automatický termín. D-1 je náhradní termín pouze po jistém
neodeslání D-2. Potvrzeně odeslané D-2 se neopakuje; stav `delivery_unknown`
zůstává fail-closed bez automatického opakování a vyžaduje diagnostické
vyřešení. Protože společný e-mail může být poskytovatelem přijat jen pro část
příjemců, budoucí soukromý stav musí rozlišit výsledek každé ze čtyř adres.
Git-safe audit smí obsahovat jen redigovanou technickou identitu a stav, nikdy
adresy ani obsah zprávy.

Důkaz rozhodnutí: přímé Mílovo upřesnění cíle v pracovním proudu. Nejde o důkaz
implementace nebo odeslání; automatika i persistence doručení jsou nadále
vypnuté.

Další krok: read-only návrh soukromé konfigurace čtyř adres, automatického
odesílacího adaptéru, per-recipient stavu, idempotence a plánovače.

### 2026-07-22 14:24 CEST – Handoff a TVBCP nyní zachycují čtyři pevné příjemce a cílové automatické odesílání

Pracovní proud: `project-family-calendar`.

Milník: Handoff a TVBCP nyní zachycují čtyři pevné příjemce a cílové automatické odesílání

Důkaz: plná Cockpit brána: 986 testů, 257.7 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Navrhnout read-only kontrakt soukromé konfigurace, odesílacího adaptéru a stavu doručení

### 2026-07-22 15:59 CEST – Přidán čistý stavový automat D-2/D-1 s per-recipient výsledky a cílenými testy

Pracovní proud: `project-family-calendar`.

Milník: Přidán čistý stavový automat D-2/D-1 s per-recipient výsledky a cílenými testy

Důkaz: plná Cockpit brána: 986 testů, 256.0 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Doplnit soukromou konfiguraci čtyř příjemců a atomickou persistenci stavu bez zapnutí SMTP

### 2026-07-22 16:39 CEST – Přidáno privátní atomické úložiště delivery stavů, recovery a cílené bezpečnostní testy

Pracovní proud: `project-family-calendar`.

Milník: Přidáno privátní atomické úložiště delivery stavů, recovery a cílené bezpečnostní testy

Důkaz: plná Cockpit brána: 1007 testů, 213.9 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Doplnit loader soukromé konfigurace přesně čtyř příjemců v režimu disabled bez zapnutí SMTP

### 2026-07-22 17:15 CEST – Přidán jedno-workerový koordinátor s recovery, fail-closed transportem a testy skutečného souběhu i pádu procesu

Pracovní proud: `project-family-calendar`.

Milník: Přidán jedno-workerový koordinátor s recovery, fail-closed transportem a testy skutečného souběhu i pádu procesu

Důkaz: plná Cockpit brána: 1014 testů, 213.5 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Doplnit loader soukromé konfigurace čtyř příjemců v režimu disabled a předávat ji výhradně koordinátoru

### 2026-07-22 18:06 CEST – Přidán fail-closed read-only loader přesně čtyř příjemců v režimu disabled s ochranou soukromí a cílenými testy

Pracovní proud: `project-family-calendar`.

Milník: Přidán fail-closed read-only loader přesně čtyř příjemců v režimu disabled s ochranou soukromí a cílenými testy

Důkaz: plná Cockpit brána: 1025 testů, 262.6 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Propojit loader s bezpečným runnerem, který v režimu disabled nevolá koordinátor ani transport a vrací pouze redigovaný no-op stav

### 2026-07-22 18:21 CEST – Bod 3a přidal redigovaný fail-closed runner bez volání koordinátoru nebo transportu

Pracovní proud: `project-family-calendar`.

Milník: Bod 3a přidal redigovaný fail-closed runner bez volání koordinátoru nebo transportu

Důkaz: plná Cockpit brána: 1029 testů, 260.9 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Navrhnout bod 3b s bezpečným dry-run režimem bez SMTP

### 2026-07-22 18:57 CEST – Runner podporuje redigovaný dry-run D-2 a D-1 bez runtime I/O nebo transportu

Pracovní proud: `project-family-calendar`.

Milník: Runner podporuje redigovaný dry-run D-2 a D-1 bez runtime I/O nebo transportu

Důkaz: plná Cockpit brána: 1032 testů, 259.9 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Doplnit čistý builder jednoho společného e-mailového obalu pro čtyři příjemce bez SMTP

### 2026-07-22 19:28 CEST – Přidán čistý redigovaný builder jednoho upozornění pro čtyři příjemce

Pracovní proud: `project-family-calendar`.

Milník: Přidán čistý redigovaný builder jednoho upozornění pro čtyři příjemce

Důkaz: plná Cockpit brána: 1037 testů, 259.9 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Implementovat SMTP adaptér s injektovaným falešným klientem bez skutečného odesílání

### 2026-07-22 20:08 CEST – Přidán redigovaný SMTP adaptér s falešným klientem a čtyřmi výsledky přijetí

Pracovní proud: `project-family-calendar`.

Milník: Přidán redigovaný SMTP adaptér s falešným klientem a čtyřmi výsledky přijetí

Důkaz: plná Cockpit brána: 1043 testů, 259.2 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Propojit adaptér s koordinátorem v end-to-end testu stále pouze s falešným SMTP klientem

### 2026-07-22 20:23 CEST – Doplněn redigovaný end-to-end tok s falešným SMTP klientem, persistencí a idempotencí

Pracovní proud: `project-family-calendar`.

Milník: Doplněn redigovaný end-to-end tok s falešným SMTP klientem, persistencí a idempotencí

Důkaz: plná Cockpit brána: 1047 testů, 260.0 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Rozšířit privátní konfiguraci o odesílatele a bezpečnou referenci na přihlašovací tajemství bez skutečného SMTP

### 2026-07-22 20:39 CEST – Schéma 2 bezpečně přidává redigovanou adresu odesílatele bez hesla nebo SMTP

Pracovní proud: `project-family-calendar`.

Milník: Schéma 2 bezpečně přidává redigovanou adresu odesílatele bez hesla nebo SMTP

Důkaz: plná Cockpit brána: 1050 testů, 256.4 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Připravit explicitní bezpečnou aktualizaci soukromé konfigurace na schéma 2 a ověřit ji bez SMTP

### 2026-07-22 20:54 CEST – Přidán redigovaný dvoukrokový přechod schématu 1 na 2 s atomickým zápisem a soukromou zálohou

Pracovní proud: `project-family-calendar`.

Milník: Přidán redigovaný dvoukrokový přechod schématu 1 na 2 s atomickým zápisem a soukromou zálohou

Důkaz: plná Cockpit brána: 1056 testů, 256.6 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Vytvořit redigovaný plán nad skutečnou privátní konfigurací s lokálně získaným odesílatelem a teprve po kontrole potvrdit apply

### 2026-07-22 21:11 CEST – Dokončen bod 4d: lokální preview/apply runner, redigované CLI a cílené bezpečnostní testy

Pracovní proud: `project-family-calendar`.

Milník: Dokončen bod 4d: lokální preview/apply runner, redigované CLI a cílené bezpečnostní testy

Důkaz: plná Cockpit brána: 1063 testů, 255.8 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Spustit pouze redigovaný preview v prostředí vlastnícím privátní konfiguraci

### 2026-07-22 22:10 CEST – Přidán create-only inicializátor schématu 2 se skrytým zadáním čtyř adres, přesným potvrzením a bezpečnostními testy

Pracovní proud: `project-family-calendar`.

Milník: Přidán create-only inicializátor schématu 2 se skrytým zadáním čtyř adres, přesným potvrzením a bezpečnostními testy

Důkaz: plná Cockpit brána: 1074 testů, 217.7 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Spustit inicializátor v prostředí vlastnícím privátní data a ponechat novou konfiguraci v režimu disabled

### 2026-07-23 06:32 CEST – Doplněn atomický přechod konfigurace Rodinného kalendáře z disabled do dry_run

Pracovní proud: `project-family-calendar`.

Milník: Doplněn atomický přechod konfigurace Rodinného kalendáře z disabled do dry_run

Důkaz: plná Cockpit brána: 1083 testů, 308.3 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: V hlavním prostředí spustit pouze read-only preview skriptu family_calendar_delivery_config_enable_dry_run.py bez --apply.

### 2026-07-23 07:11 CEST – Přidán read-only orchestrátor dnešních D-2/D-1 kandidátů s redigovaným CLI a aktivními pojistkami proti runtime I/O

Pracovní proud: `project-family-calendar`.

Milník: Přidán read-only orchestrátor dnešních D-2/D-1 kandidátů s redigovaným CLI a aktivními pojistkami proti runtime I/O

Důkaz: plná Cockpit brána: 1091 testů, 226.1 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Spustit redigovaný provozní dry-run v prostředí vlastnícím privátní kalendář a konfiguraci

### 2026-07-23 07:50 CEST – Přidán iCloud STARTTLS klient s povinně injektovanou SMTP relací, redigovanými výsledky a testy bez sítě

Pracovní proud: `project-family-calendar`.

Milník: Přidán iCloud STARTTLS klient s povinně injektovanou SMTP relací, redigovanými výsledky a testy bez sítě

Důkaz: plná Cockpit brána: 1097 testů, 232.9 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Připravit samostatný přesně potvrzovaný testovací runner s lokálním iCloud tajemstvím

### 2026-07-23 08:06 CEST – Přidán bezpečný jednorázový SMTP runner s redigovaným preview, přesným potvrzením a testy bez sítě

Pracovní proud: `project-family-calendar`.

Milník: Přidán bezpečný jednorázový SMTP runner s redigovaným preview, přesným potvrzením a testy bez sítě

Důkaz: plná Cockpit brána: 1105 testů, 218.5 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Spustit pouze redigovaný preview runneru v prostředí s privátní konfigurací a teprve samostatně potvrdit jeden skutečný testovací e-mail

### 2026-07-23 17:07 CEST – Obnoven aktuální stav SMTP diagnostiky a nasazeného DATA/QUIT hotfixu

Pracovní proud: `project-family-calendar`.

Po ranním checkpointu proběhly dva ručně spuštěné živé testovací pokusy.
Oba v tehdejší implementaci skončily jako `delivery_unknown`. Pozorované
doručení bylo nulové, ale absence pozorovaného e-mailu není důkazem jistého
neodeslání; staré pokusy se proto nesmějí automaticky opakovat ani zpětně
překlasifikovat.

Následná no-send diagnostika oddělila autentizaci, TLS a SMTP envelope.
Po obnovení platného app-specific hesla prošla autentizace a envelope
preflight potvrdil přijetí odesílatele i všech čtyř příjemců. Transakce byla
ukončena přes `RSET`; `DATA` ani odeslání nebyly volány.

Read-only audit odhalil, že původní klient mohl ztratit už potvrzený výsledek
`DATA`, pokud následné ukončení relace přes `QUIT` vyhodilo výjimku. Commit
`d38a37f` tento problém opravil: potvrzené `DATA` zůstane `sent` nebo
`partial`, stav ukončení relace se hlásí samostatně a `delivery_unknown`
zůstává pouze tam, kde potvrzení `DATA` skutečně chybí.

Důkaz: 158 kalendářových testů a plná Cockpit Quality Gate s 1134 testy
prošly. Commit `d38a37f` je na `main` a `origin/main`, nasazení má stav
`deployed`, Cockpit byl řízeně restartován, vzdálená Quality Gate i smoke test
5/5 prošly. Během implementace, testů a nasazení se nespustila žádná SMTP
diagnostika ani e-mail.

Rozhodnutí: automatické D-2/D-1 odesílání zůstává vypnuté. Dva staré
`delivery_unknown` výsledky zůstávají historicky nejisté a hotfix je nemůže
zpětně vyřešit.

Další krok: spustit právě jeden nový, ručně a přesně potvrzený testovací
e-mail čtyřem pevně nakonfigurovaným příjemcům přes nasazený hotfix.
App-specific heslo zadat pouze skrytě mimo chat. Při `partial`, `refused`,
`delivery_unknown` nebo chybě nic automaticky neopakovat.

### 2026-07-23 17:25 CEST – Nový test po hotfixu byl přijat i doručen 4/4

Pracovní proud: `project-family-calendar`.

Po redigovaném preview byl spuštěn právě jeden nový ručně a přesně potvrzený
testovací e-mail. App-specific heslo bylo zadáno skrytě mimo chat.

Redigovaný SMTP důkaz: `status=sent`, `recipient_count=4`,
`accepted_count=4`, `refused_count=0`, `unknown_count=0`,
`transport_called=true` a `session_close_ok=true`. Míla následně ručně
potvrdil skutečné doručení `RECEIVED_COUNT=4`.

Milník: jednorázová testovací brána je úspěšně uzavřená. Nasazený hotfix
správně rozlišil potvrzené přijetí a korektní ukončení relace. V tomto
checkpointu nejsou adresy, heslo ani obsah zprávy.

Rozhodnutí: úspěšný test sám nezapíná automatické D-2/D-1 odesílání.
Automatika zůstává vypnutá a vyžaduje samostatnou provozní revizi a nové
Mílovo rozhodnutí.

Další krok: read-only ověřit plánovač, přechod ze současného neostrého režimu,
persistenci per-recipient výsledků, idempotenci a recovery. Během této revize
nic nezapínat ani neodesílat.

### 2026-07-23 19:52 CEST – Přidán pouze dry-run plánovací vstup

Pracovní proud: `project-family-calendar`.

Milník: vznikl dedikovaný vstup `family_calendar_delivery_run.py`, který je
určený pro budoucí plánovač, ale v současné fázi pouze volá existující
provozní dry-run. Nemá odesílací přepínač ani vlastní SMTP, koordinační nebo
persistenční cestu.

Důkaz: 167 kalendářových testů a plná Cockpit Quality Gate s 1143 testy
prošly. Redigovaná zkouška nad privátní konfigurací v režimu `dry_run`
nevolala koordinátor ani transport a nevytvořila stavový nebo worker soubor.
Readiness nyní místo `planner_runner_missing` správně hlásí
`planner_not_installed`; stavové úložiště ani recovery nemají blokující stav.

Rozhodnutí: automatika zůstává vypnutá. Tento milník pouze uzavírá chybějící
spustitelný vstup a neopravňuje k instalaci plánovače, práci s Keychain,
přechodu režimu ani odesílání.

Další krok: vytvořit read-only náhled budoucí LaunchAgent konfigurace s
redigovanými metadaty. Náhled nesmí nic zapisovat, instalovat, načítat ani
odesílat.

### 2026-07-23 20:03 CEST – Vytvořen read-only náhled LaunchAgent konfigurace

Pracovní proud: `project-family-calendar`.

Milník: samostatný builder a CLI sestavují pouze JSON náhled budoucí plist.
Validují absolutní cestu k Pythonu a dry-run runneru, denní čas a bezpečné
režimy. Kandidát používá `RunAtLoad=false` a `ProcessType=Background`.

Důkaz: 171 kalendářových testů a plná Cockpit Quality Gate s 1147 testy
prošly. Živý náhled pro 08:00 nevytvořil plist, nevolal `launchctl`, nečetl
Keychain, nevolal transport a neprovedl zápis. CLI nemá `--apply`, výstupní
cestu ani instalační operaci.

Rozhodnutí: tento checkpoint pouze umožňuje kontrolu přesného kandidáta.
Plánovač není nainstalovaný ani načtený, automatický režim zůstává nedostupný
a odesílání vypnuté.

Další krok: samostatně navrhnout dvoukrokovou instalační bránu pro vytvoření
plist pouze v režimu `dry_run`: náhled a až potom zvláštní potvrzení zápisu.
Ani tato příští fáze ještě nemá volat `launchctl`, Keychain nebo transport.

### 2026-07-23 20:52 CEST – Přidána potvrzovaná create-only instalace plist

Pracovní proud: `project-family-calendar`.

Milník: instalační workflow má dvě oddělené fáze. Preview je read-only a vrací
přesný plist, cílovou cestu, režim `0600`, fingerprint a vyžadovanou
potvrzovací větu. Apply přijme pouze plán se shodným fingerprintem, znovu
ověří režim `dry_run`, Python, runner a volný kanonický cíl a teprve potom
provede atomický create-only zápis.

Důkaz: 34 cílených bezpečnostních testů, 177 kalendářových testů a plná
Cockpit Quality Gate s 1153 testy prošly. Testy potvrdily nulový zápis při
chybné potvrzovací větě nebo fingerprintu, odmítnutí změněného runneru,
existujícího souboru i symlinku a přesný atomický zápis s právy `0600` pouze
v dočasném prostoru. Živý běh byl jen preview; systémový plist nevznikl.

Rozhodnutí: implementace neznamená souhlas se skutečnou instalací. Brána
nevolá `launchctl`, nečte Keychain a nemůže odeslat e-mail. Automatický režim
zůstává nedostupný.

Další krok: po checkpointu spustit z `main` jen nový instalační preview.
Create-only zápis provést až po samostatném Mílově rozhodnutí s přesnou
potvrzovací větou a fingerprintem. Ani po zápisu zatím plist nenačítat.

### 2026-07-23 22:36 CEST – Keychain reference je vytvořená bezpečnou dvoukrokovou branou

Pracovní proud: `project-family-calendar`.

Milník: vznikl samostatný Keychain setup, jehož první fáze pouze redigovaně
ukazuje identitu budoucí položky. Zápis vyžaduje přesnou potvrzovací větu,
odmítá existující položku a app-specific heslo přijímá pouze skrytým promptem
macOS `security`, bez hodnoty hesla v argumentech procesu.

Důkaz: 185 kalendářových testů a plná Cockpit Quality Gate s 1167 testy
prošly. Samostatně potvrzené živé zadání vytvořilo reference; následný
read-only readiness audit její existenci ověřil bez čtení hodnoty hesla,
zápisu nebo transportu.

Rozhodnutí: vytvořená reference sama nezapíná automatiku. Plist zůstává
nenačtený, konfigurace je `dry_run` a automatický režim je nedostupný.
Zbývají přesně tyto dva blokátory: `planner_not_loaded` a
`automatic_mode_unavailable`.

Další krok: z `main` připravit pouze read-only náhled přesné operace pro
budoucí načtení LaunchAgentu a bezpečný rollback postup. Zatím nevolat
`launchctl`, neměnit automatický režim a nic neodesílat.

### 2026-07-23 22:57 CEST – Přidán read-only náhled načtení a rollbacku LaunchAgentu

Pracovní proud: `project-family-calendar`.

Milník: nový náhled vrací přesné datové příkazy pro budoucí `bootstrap`,
ověření služby přes `print`, rollback přes `bootout` a ověření odpojení.
CLI nemá `--apply` a implementace nemá callback ani jinou cestu, která by
`launchctl` příkazy spustila.

Bezpečnostní kontrakt: náhled fail-closed ověřuje stále platný `dry_run`,
kanonický vlastněný plist s právy `0600`, `RunAtLoad=false`, proces typu
`Background`, bezpečný systémový `launchctl` a fingerprint svázaný s plist,
konfigurací a uživatelskou GUI doménou. Aktuální load stav záměrně neprobuje;
budoucí load brána jej musí znovu ověřit těsně před zápisem do runtime.

Důkaz: 189 kalendářových testů a plná Cockpit Quality Gate s 1171 testy
prošly. Živý read-only náhled neměl issues, nic nezapsal, nenačetl ani
neodeslal. Následný readiness audit stále hlásil `planner_not_loaded`.

Rozhodnutí: náhled ani jeho fingerprint nejsou souhlasem s načtením.
Automatický režim zůstává nedostupný a konfigurace `dry_run`.

Další krok: po začlenění zopakovat náhled z `main`. Teprve samostatně
navrhnout potvrzovanou load bránu s revalidací fingerprintu, aktuálního stavu
a rollbacku; zatím `launchctl` nevolat a nic neodesílat.

### 2026-07-24 07:32 CEST – Přidána potvrzovaná load brána s ověřovaným rollbackem

Pracovní proud: `project-family-calendar`.

Milník: samostatná load brána navazuje na read-only preview a před jakoukoli
runtime mutací vyžaduje přesnou globální bezpečnostní větu, lokální potvrzení
`LOAD_FAMILY_CALENDAR_DRY_RUN_PLANNER` a shodný fingerprint. Potom znovu
ověří nezměněný `dry_run` kontrakt, plist i skutečně nenačtenou službu.

Provozní kontrakt: stav služby se neodvozuje z libovolné chyby. Nenačtená
služba má přesný očekávaný návratový kód. Po `bootstrap` se stav znovu probuje
a výsledek se označí jako `loaded`, `unloaded` nebo `unknown`. Neznámý stav
spustí připravený `bootout` rollback a další probe. Jakákoli runtime mutace
zakazuje automatický retry, i když se následně podaří potvrdit odpojení.

Důkaz: 18 cílených bezpečnostních testů, 198 kalendářových testů a plná
Cockpit Quality Gate s 1180 testy prošly. Testy simulovaly úspěch, změněné
vstupy, nečekané návratové kódy, selhání bootstrapu, potvrzený rollback i
nevyřešený stav. Živě proběhl jen read-only `launchctl print`; fingerprint
zůstal shodný a readiness dál hlásil `planner_not_loaded`.

Rozhodnutí: implementace ani testy nejsou souhlasem se skutečným načtením.
Nebyl volán `bootstrap` ani `bootout`, automatický režim zůstává nedostupný
a žádný e-mail nebyl odeslán.

Další krok: po začlenění a pushi zopakovat z `main` pouze read-only load
preview. Skutečné načtení provést až po nové přesné globální i lokální
potvrzovací větě a se shodným fingerprintem; konfiguraci ponechat `dry_run`.

### 2026-07-24 08:12 CEST – První naplánovaný dry-run prošel bez transportu

Pracovní proud: `project-family-calendar`.

Provozní milník: po přesné globální i lokální potvrzovací větě a ověření
shodného fingerprintu byl dry-run LaunchAgent načten. `bootstrap` skončil
nulovým návratovým kódem, následný probe potvrdil `loaded` a rollback nebyl
potřeba. Protože plist zachoval `RunAtLoad=false`, samotné načtení úlohu
nespustilo.

Důkaz prvního plánu: úloha byla naplánována na 2026-07-24 v 08:00. Read-only
audit v 08:10 CEST zaznamenal `runs=1`, poslední návratový kód `0` a stav
`not running`. Readiness zůstal `planner_ready`; jedinou zbývající překážkou
automatiky je nedostupný automatický režim.

Bezpečnostní výsledek: konfigurace zůstala `dry_run`,
`automation_active=false`, stavový ani worker soubor nevznikl a nebyl
evidován žádný záznam ve stavu `sending`, `partial` nebo `delivery_unknown`.
Heslo nebylo čteno, transport nebyl volán a žádný e-mail nebyl odeslán.

Rozhodnutí: dry-run plánovač je provozně ověřený. Tento důkaz není souhlasem
s přechodem do automatického režimu.

Další krok: připravit pouze read-only návrh přechodu z `dry_run` do
automatického režimu včetně potvrzovacího, rollback a recovery kontraktu.
Režim zatím neměnit a nic neodesílat.

### 2026-07-24 08:34 CEST – Read-only návrh aktivace je ověřený

Pracovní proud: `project-family-calendar`.

Milník: nový náhled přesně popisuje jedinou budoucí změnu konfigurace
`dry_run` na `enabled`. Současně zachycuje podmínky D-2/D-1, čtyři kanonické
příjemce, identitu operace podle události a offsetu, jednoho workera a trvalý
stav `sending` před případným transportem.

Aktivační kontrakt: po revalidaci fingerprintu a provozních předpokladů se má
plánovač nejprve odpojit a jeho stav ověřit. Teprve potom smí následovat
atomická změna konfigurace s právy `0600`, ověření režimu, nové načtení a
závěrečný readiness audit.

Rollback a recovery: před obnovou `dry_run` se musí plánovač vždy znovu
odpojit a ověřit. Pokud není možné bezpečný stav potvrdit, plánovač zůstane
odpojený, konfigurace vyžaduje ruční audit a automatický retry je zakázaný.
`sending` a `delivery_unknown` blokují aktivaci; `partial` vyžaduje ruční
revizi před případným retry.

Důkaz: 203 kalendářových testů a plná Cockpit Quality Gate s 1185 testy
prošly. Živý read-only náhled neměl issues, provozní předpoklady byly
připravené a jediný implementační blokátor byl
`automatic_mode_unavailable`. Náhled nezapsal data, nezměnil runtime, nečetl
heslo a nevolal transport.

Rozhodnutí: návrh není souhlasem s aktivací. Nemá `--apply`, režim `enabled`
ani ostrý plánovací vstup zatím nejsou implementované a automatické odesílání
zůstává vypnuté.

Další krok: po začlenění zopakovat živý read-only náhled z `main`. Potom
samostatně implementovat potvrzovanou aktivační bránu a ostrý plánovací vstup
podle tohoto kontraktu; režim zatím neměnit a nic neodesílat.

### 2026-07-26 13:59 CEST – Ostrá runtime větev je připravená, ale neaktivní

Hotovo: plánovací vstup umí podle soukromé konfigurace bezpečně zvolit
`disabled`, `dry_run` nebo `enabled`. Ostrá větev propojuje existující
atomickou persistenci, D-2/D-1 idempotenci, recovery, pevnou Keychain identitu
a redigovaný iCloud SMTP adaptér. Tajemství se čte až po recovery kontrole a
nalezení kandidáta.

Rozhodnutí: `partial`, `delivery_unknown` nebo přerušené `sending` nesmí vést
k automatickému retry. Recovery přerušený stav uzavře jako
`delivery_unknown` a všechny další automatické pokusy zablokuje do ručního
auditu. Runtime implementace sama není souhlasem s aktivací.

Další krok: implementovat samostatně potvrzovanou aktivační apply bránu podle
už schváleného pořadí unload, atomická změna jediného pole `mode`, ověření,
load a závěrečný readiness audit.

Navrhované další kroky:

- Po začlenění zopakovat read-only aktivační preview z čistého `main`.
- Skutečnou aktivaci provést jen po nové globální a lokální potvrzovací větě.
- Zvlášť navrhnout ruční workflow pro uzavření blokujícího
  `partial`/`delivery_unknown`; nespojovat jej s automatickým retry.

Technický důkaz: prošlo 218 kalendářových testů a úplná Cockpit Quality Gate
s 1252 testy. Živý kontrolní běh zůstal `dry_run`, našel nula kandidátů,
nevolal koordinátor ani transport a nezměnil konfiguraci nebo stavové
úložiště. Skutečné Keychain tajemství ani síť nebyly při tomto kroku použity.

### 2026-07-28 21:52 CEST – Aktivační brána bezpečně a potvrzovaně přepíná automatizaci z dry-run do enabled s ověřeným rollbackem

Hotovo:
- Aktivační brána bezpečně a potvrzovaně přepíná automatizaci z dry-run do enabled s ověřeným rollbackem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Zkontrolovat změny a vytvořit checkpoint v Cockpitu

Navrhované další kroky:
- Po checkpointu spustit pouze redigovaný aktivační preview; samotné apply potvrdit samostatně

Technický důkaz:
- plná Cockpit brána: 1217 testů, 290.5 s, výsledek OK.
- Pracovní proud: `project-family-calendar`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-30 07:25 CEST – P6b oddělilo implementaci od živého režimu

Hotovo:
- Aktivní paměť už nenabízí implementaci aktivační brány jako budoucí krok;
  brána je implementovaná a nasazený `main` ji obsahuje.

Rozhodnutí:
- Z implementace se nesmí odvozovat aktuální soukromý režim.
- P6b nečetlo konfiguraci, příjemce, tajemství ani delivery obsah.

Další krok:
- Provést redigovaný read-only audit režimu, readiness a plánovače.

Navrhované další kroky:
- Aktivační apply neopakovat jen podle staré paměti.
- Přirozený plánovaný výsledek sledovat přes redigovaný stav a nejistotu
  ponechat fail-closed.

Technický důkaz:
- Implementační checkpoint prošel 1217 testy.
- Aktuální Cockpit běží na `20180e2` a smoke prošel 5/5.
