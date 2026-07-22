# Handoff pracovního proudu: Rodinný kalendář

Nazev: Rodinný kalendář
Pracovni proud: project-family-calendar
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Čistý builder D-2/D-1 a read-only sekce `Náhled upozornění` v Cockpitu byly
dokončeny, otestovány, commitnuty, pushnuty a ručně ověřeny Mílou.
Míla následně upřesnil cílový provoz: čtyři pevné soukromé adresy, jeden
společný e-mail a po bezpečném zprovoznění automatické odesílání bez běžné
ruční kontroly.

Co je hotove:
- Builder vrací pro přesně dva různé příjemce událost, věk, režim D-2/D-1,
  předmět a tělo bez I/O nebo odesílání.
- Cockpit přijímá dvě serverově validované adresy, události odvozuje ze
  soukromého registru a náhled zobrazí bez odesílání nebo persistence.
- Odpověď používá `no-store`, UI bezpečné `textContent` a při zavření okna
  adresy z formuláře vymaže.
- Implementační commit `021adf5` je na `main` a `origin/main`; plná brána
  983 testů, vzdálená GitHub Gate, živý smoke 5/5 a ruční test prošly.
- Cílový model čtyř pevných příjemců a automatického odesílání je potvrzený;
  příjemci o sobě mohou vědět.
- Kanonický handoff a TVBCP existují.

Co neni hotove:
- Odesílání ani persistence doručení nejsou implementované.
- Současný builder a read-only UI stále pracují se dvěma ručně zadanými
  adresami; cílové čtyři adresy ještě nejsou zapojené.
- Není navržený automatický odesílací adaptér, soukromá konfigurace čtyř adres,
  stav jednotlivých příjemců ani plánovač.

Dalsi krok:
Zahájit samostatnou read-only fázi návrhu automatického odesílání jednomu
společnému e-mailu na čtyři pevné soukromé adresy; zatím nic neodesílat.

Navrhovane dalsi kroky:
- Nejdříve vymezit soukromou konfiguraci, odesílací adaptér, stav každého
  příjemce, redigovaný audit a fail-closed pravidla.
- D-2 odeslat automaticky jednou; D-1 použít jen jako náhradu po jistém
  neodeslání D-2. Při nejistém výsledku D-2 automaticky neopakovat.
- Automatiku zapnout až po samostatně otestované implementační fázi.

Zmenene nebo relevantni soubory:
- `app/family_calendar.py`
- `app/cockpit.py`
- `tests/test_family_calendar.py`
- `tests/test_family_calendar_cockpit.py`
- `.github/workflows/cockpit-quality-gate.yml`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice, skutečné adresy ani soukromy obsah do
  Gitu, projektové paměti nebo testů.

### Automatický checkpoint 2026-07-22 08:48 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Čistý builder náhledu D-2/D-1 a cílené testy jsou hotové
- Ověření: plná Cockpit brána: 980 testů, 208.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/family_calendar.py`, `Samantha_Agent/tests/test_family_calendar.py`
- Commit: `Doplnit náhled upozornění rodinného kalendáře`
- Další krok: Potvrdit checkpoint tohoto kroku v Cockpitu

### Dokumentační checkpoint 2026-07-22 11:03 CEST

- Implementační checkpoint výše už byl dokončen: commit `531ed75` je na
  `main` a `origin/main`. Jeho tehdejší řádek „Potvrdit checkpoint“ tímto
  novějším záznamem pozbývá platnosti.
- Projektová paměť, aktivní registr a aktuální souhrn tohoto handoffu jsou
  srovnány se skutečně dokončeným stavem builderu.
- GitHub Cockpit Quality Gate nově sleduje `app/family_calendar.py` a všechny
  `tests/test_family_calendar*.py` při pull requestu i pushi.
- Ověření: 28 cílených testů prošlo; plná lokální Cockpit Quality Gate prošla
  s 980 testy za 208.0 s; `git diff --check` byl součástí zelené brány.
- Další krok: navrhnout samostatné read-only zobrazení náhledu v Cockpitu,
  stále bez odesílání a bez persistence doručení.

### Automatický checkpoint 2026-07-22 12:01 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Cockpit bezpečně zobrazuje náhledy D-2/D-1 bez odesílání a persistence
- Ověření: plná Cockpit brána: 983 testů, 304.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/family_calendar.py`, `Samantha_Agent/tests/test_family_calendar.py`, `Samantha_Agent/tests/test_family_calendar_cockpit.py`
- Commit: `Doplnit read-only náhled rodinných upozornění`
- Další krok: Potvrdit checkpoint a potom ručně ověřit náhled na Macu nebo iPhonu

### Dokumentační checkpoint 2026-07-22 13:20 CEST

- Implementační checkpoint výše je dokončen: commit `021adf5` je na `main`
  a `origin/main`. Jeho řádek „Potvrdit checkpoint“ tímto novějším záznamem
  pozbývá platnosti.
- Míla ručně potvrdil, že read-only náhled v Cockpitu funguje.
- Ověření: 22 kalendářových testů, plná Cockpit brána s 983 testy, vzdálená
  GitHub Gate a živý smoke test 5/5 prošly.
- Projektová paměť, aktivní registr, aktuální souhrn handoffu a TVBCP jsou
  srovnány se skutečně dokončeným stavem.
- Další krok: samostatná read-only fáze návrhu jednoho ručně potvrzovaného
  testovacího e-mailu; zatím nic neodesílat ani nezapínat automatiku.

### Rozhodnutí o cílovém automatickém odesílání 2026-07-22 14:19 CEST

- Míla potvrdil cílový počet čtyř příjemců. Adresy budou pevně uložené pouze
  v soukromé konfiguraci Samanthy mimo Git, projektovou paměť a testy.
- Cílem je jeden společný e-mail všem čtyřem příjemcům; příjemci o sobě mohou
  vědět. Po bezpečném zprovoznění proběhne běžné odesílání automaticky bez
  ruční kontroly jednotlivých zpráv.
- D-2 je standardní automatický termín. D-1 je náhradní termín pouze tehdy,
  když D-2 prokazatelně nebylo odesláno. Stav `delivery_unknown` se automaticky
  neopakuje a vyžaduje diagnostické vyřešení.
- Riziko částečného přijetí společného e-mailu se musí sledovat zvlášť pro
  každého příjemce. Audit bude git-safe a redigovaný, bez adres a obsahu zprávy.
- Rozhodnutí je návrhový cíl, nikoli tvrzení o hotové implementaci. V tomto
  kroku se nic neodesílalo a automatika zůstává vypnutá.
- Další krok: read-only návrh soukromé konfigurace, odesílacího adaptéru,
  per-recipient stavu, idempotence a plánovače.

### Automatický checkpoint 2026-07-22 14:24 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Handoff a TVBCP nyní zachycují čtyři pevné příjemce a cílové automatické odesílání
- Ověření: plná Cockpit brána: 986 testů, 257.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/memory/handoffs/workstreams/project-family-calendar.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-family-calendar.md`
- Commit: `Zapsat cílový model automatických rodinných upozornění`
- Další krok: Navrhnout read-only kontrakt soukromé konfigurace, odesílacího adaptéru a stavu doručení

### Automatický checkpoint 2026-07-22 15:59 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán čistý stavový automat D-2/D-1 s per-recipient výsledky a cílenými testy
- Ověření: plná Cockpit brána: 986 testů, 256.0 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/family_calendar_delivery.py`, `Samantha_Agent/tests/test_family_calendar_delivery.py`
- Commit: `Doplnit stavový automat doručení rodinného kalendáře`
- Další krok: Doplnit soukromou konfiguraci čtyř příjemců a atomickou persistenci stavu bez zapnutí SMTP

### Automatický checkpoint 2026-07-22 16:39 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidáno privátní atomické úložiště delivery stavů, recovery a cílené bezpečnostní testy
- Ověření: plná Cockpit brána: 1007 testů, 213.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `.github/workflows/cockpit-quality-gate.yml`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_store.py`, `Samantha_Agent/tests/test_family_calendar_delivery_store.py`
- Commit: `Doplnit atomické úložiště doručení rodinného kalendáře`
- Další krok: Doplnit loader soukromé konfigurace přesně čtyř příjemců v režimu disabled bez zapnutí SMTP

### Automatický checkpoint 2026-07-22 17:15 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán jedno-workerový koordinátor s recovery, fail-closed transportem a testy skutečného souběhu i pádu procesu
- Ověření: plná Cockpit brána: 1014 testů, 213.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_coordinator.py`, `Samantha_Agent/tests/test_family_calendar_delivery_coordinator.py`
- Commit: `Doplnit koordinátor doručení rodinného kalendáře`
- Další krok: Doplnit loader soukromé konfigurace čtyř příjemců v režimu disabled a předávat ji výhradně koordinátoru

### Automatický checkpoint 2026-07-22 18:06 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán fail-closed read-only loader přesně čtyř příjemců v režimu disabled s ochranou soukromí a cílenými testy
- Ověření: plná Cockpit brána: 1025 testů, 262.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_config.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config.py`
- Commit: `Doplnit privátní konfiguraci doručení rodinného kalendáře`
- Další krok: Propojit loader s bezpečným runnerem, který v režimu disabled nevolá koordinátor ani transport a vrací pouze redigovaný no-op stav

### Automatický checkpoint 2026-07-22 18:21 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Bod 3a přidal redigovaný fail-closed runner bez volání koordinátoru nebo transportu
- Ověření: plná Cockpit brána: 1029 testů, 260.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_runner.py`, `Samantha_Agent/tests/test_family_calendar_delivery_runner.py`
- Commit: `Doplnit bezpečný runner doručení rodinného kalendáře`
- Další krok: Navrhnout bod 3b s bezpečným dry-run režimem bez SMTP

### Automatický checkpoint 2026-07-22 18:57 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Runner podporuje redigovaný dry-run D-2 a D-1 bez runtime I/O nebo transportu
- Ověření: plná Cockpit brána: 1032 testů, 259.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/family_calendar_delivery_config.py`, `Samantha_Agent/app/family_calendar_delivery_runner.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config.py`, `Samantha_Agent/tests/test_family_calendar_delivery_runner.py`
- Commit: `Doplnit bezpečný dry-run doručení rodinného kalendáře`
- Další krok: Doplnit čistý builder jednoho společného e-mailového obalu pro čtyři příjemce bez SMTP

### Automatický checkpoint 2026-07-22 19:28 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán čistý redigovaný builder jednoho upozornění pro čtyři příjemce
- Ověření: plná Cockpit brána: 1037 testů, 259.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/family_calendar.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_message.py`, `Samantha_Agent/tests/test_family_calendar_delivery_message.py`
- Commit: `Doplnit společný e-mailový obal rodinného kalendáře`
- Další krok: Implementovat SMTP adaptér s injektovaným falešným klientem bez skutečného odesílání

### Automatický checkpoint 2026-07-22 20:08 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán redigovaný SMTP adaptér s falešným klientem a čtyřmi výsledky přijetí
- Ověření: plná Cockpit brána: 1043 testů, 259.2 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_smtp_adapter.py`, `Samantha_Agent/tests/test_family_calendar_smtp_adapter.py`
- Commit: `Doplnit testovaný SMTP adaptér rodinného kalendáře`
- Další krok: Propojit adaptér s koordinátorem v end-to-end testu stále pouze s falešným SMTP klientem

### Automatický checkpoint 2026-07-22 20:23 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Doplněn redigovaný end-to-end tok s falešným SMTP klientem, persistencí a idempotencí
- Ověření: plná Cockpit brána: 1047 testů, 260.0 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/family_calendar_smtp_adapter.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_family_calendar_delivery_integration.py`
- Commit: `Propojit SMTP adaptér s koordinátorem rodinného kalendáře`
- Další krok: Rozšířit privátní konfiguraci o odesílatele a bezpečnou referenci na přihlašovací tajemství bez skutečného SMTP
