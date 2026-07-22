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
