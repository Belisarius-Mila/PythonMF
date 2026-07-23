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
