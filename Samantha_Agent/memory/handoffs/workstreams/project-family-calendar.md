# Handoff pracovního proudu: Rodinný kalendář

Nazev: Rodinný kalendář
Pracovni proud: project-family-calendar
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Od read-only náhledu D-2/D-1 se projekt posunul přes per-recipient stav,
privátní atomickou persistenci, idempotenci, dry-run, SMTP adaptér a přesně
potvrzovaný jednorázový runner až k živé diagnostice iCloud SMTP. Dva dřívější
testovací pokusy skončily jako `delivery_unknown`; pozorované doručení bylo
nulové, ale staré výsledky zpětně nelze prohlásit za jistě neodeslané.
No-send autentizační a envelope diagnostika později potvrdila funkční
přihlášení i přijetí odesílatele a všech čtyř příjemců bez volání `DATA`.
Následný hotfix oddělil potvrzení `DATA` od chyby při ukončení SMTP relace.

Co je hotove:
- Read-only náhled D-2/D-1 v Cockpitu je hotový a ručně ověřený.
- Cílový model používá jeden společný e-mail pro čtyři pevné příjemce uložené
  pouze v soukromé konfiguraci; příjemci o sobě mohou vědět.
- Stavový automat rozlišuje výsledek každého příjemce, podporuje recovery a
  idempotenci a při `delivery_unknown` zůstává fail-closed.
- Soukromá konfigurace schématu 2, atomické úložiště delivery stavů,
  jedno-workerový koordinátor, dry-run orchestrátor, SMTP adaptér a
  jednorázový potvrzovaný runner jsou implementované.
- No-send diagnostika rozlišuje autentizaci, TLS a SMTP envelope. Ověřený
  envelope preflight přijal odesílatele i všechny čtyři příjemce, provedl
  `RSET` a nevolal `DATA` ani odeslání.
- Commit `d38a37f` zachovává potvrzený výsledek `DATA` i při následné chybě
  `QUIT`; bez potvrzení `DATA` zůstává výsledek `delivery_unknown`.
- Hotfix je na `main` a `origin/main`, byl nasazen a Cockpit řízeně
  restartován. Prošlo 158 kalendářových testů, plná brána 1134 testů,
  vzdálená Quality Gate a smoke test 5/5.
- První nový test po hotfixu byl ručně a přesně potvrzený. SMTP výsledek byl
  `sent`, server přijal 4/4 příjemců, nikoho neodmítl, nezůstal žádný neznámý
  výsledek a relace se korektně ukončila. Míla následně potvrdil skutečné
  doručení 4/4.
- Automatické odesílání zůstává vypnuté a při obnově neběžel žádný SMTP runner.

Co neni hotove:
- Dva starší výsledky `delivery_unknown` zůstávají historicky nejisté a hotfix
  je nemůže zpětně překlasifikovat.
- Ostrý automatický režim D-2/D-1 není zapnutý ani provozně ověřený.
- Před případným zapnutím automatiky je potřeba samostatně ověřit provozní
  aktivaci, plánování, persistenci výsledku a fail-closed recovery.

Dalsi krok:
Zahájit samostatnou read-only revizi cesty k automatickému D-2/D-1 provozu:
ověřit plánovač, přechod ze současného neostrého režimu, persistenci
per-recipient výsledků, idempotenci a recovery. V této revizi nic nezapínat
ani neodesílat.

Navrhovane dalsi kroky:
- Připravit redigovaný aktivační preview a přesný seznam předpokladů bez změny
  soukromé konfigurace.
- Teprve podle výsledku revize samostatně rozhodnout, zda automatiku zapnout.
- D-1 smí být náhrada jen po jistém neodeslání D-2; starý nebo nový
  `delivery_unknown` se automaticky neopakuje.

Zmenene nebo relevantni soubory:
- `app/family_calendar.py`
- `app/family_calendar_delivery.py`
- `app/family_calendar_delivery_store.py`
- `app/family_calendar_delivery_coordinator.py`
- `app/family_calendar_delivery_config.py`
- `app/family_calendar_delivery_runner.py`
- `app/family_calendar_delivery_test_email.py`
- `app/family_calendar_icloud_smtp_client.py`
- `app/family_calendar_smtp_adapter.py`
- `scripts/family_calendar_delivery_test_email.py`
- `scripts/family_calendar_delivery_smtp_diagnose.py`
- `scripts/family_calendar_delivery_smtp_envelope_diagnose.py`
- `tests/test_family_calendar*.py`

Bezpecnost / neukladat:
- Neukládat hesla, tokeny, API klíče, skutečné adresy ani soukromý obsah do
  Gitu, projektové paměti nebo testů.
- Starý `delivery_unknown` nikdy automaticky neopakovat ani označit za jisté
  neodeslání jen podle chybějícího pozorovaného doručení.

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

### Automatický checkpoint 2026-07-22 20:39 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Schéma 2 bezpečně přidává redigovanou adresu odesílatele bez hesla nebo SMTP
- Ověření: plná Cockpit brána: 1050 testů, 256.4 s, výsledek OK
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/app/family_calendar_delivery_config.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config.py`, `Samantha_Agent/tests/test_family_calendar_delivery_runner.py`
- Commit: `Rozšířit konfiguraci rodinného kalendáře o odesílatele`
- Další krok: Připravit explicitní bezpečnou aktualizaci soukromé konfigurace na schéma 2 a ověřit ji bez SMTP

### Automatický checkpoint 2026-07-22 20:54 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán redigovaný dvoukrokový přechod schématu 1 na 2 s atomickým zápisem a soukromou zálohou
- Ověření: plná Cockpit brána: 1056 testů, 256.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/family_calendar_delivery_config.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_config_migration.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config_migration.py`
- Commit: `Doplnit bezpečnou migraci konfigurace rodinného kalendáře`
- Další krok: Vytvořit redigovaný plán nad skutečnou privátní konfigurací s lokálně získaným odesílatelem a teprve po kontrole potvrdit apply

### Automatický checkpoint 2026-07-22 21:11 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Dokončen bod 4d: lokální preview/apply runner, redigované CLI a cílené bezpečnostní testy
- Ověření: plná Cockpit brána: 1063 testů, 255.8 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/family_calendar_delivery_config_migration.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config_migration.py`, `Samantha_Agent/app/family_calendar_delivery_config_migration_runner.py`, `Samantha_Agent/scripts/family_calendar_delivery_config_migrate.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config_migration_runner.py`
- Commit: `Doplnit bezpečný lokální runner migrace konfigurace`
- Další krok: Spustit pouze redigovaný preview v prostředí vlastnícím privátní konfiguraci

### Automatický checkpoint 2026-07-22 22:10 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán create-only inicializátor schématu 2 se skrytým zadáním čtyř adres, přesným potvrzením a bezpečnostními testy
- Ověření: plná Cockpit brána: 1074 testů, 217.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/file_persistence.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_file_persistence.py`, `Samantha_Agent/app/family_calendar_delivery_config_initializer.py`, `Samantha_Agent/scripts/family_calendar_delivery_config_initialize.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config_initializer.py`
- Commit: `Doplnit bezpečný inicializátor konfigurace rodinného kalendáře`
- Další krok: Spustit inicializátor v prostředí vlastnícím privátní data a ponechat novou konfiguraci v režimu disabled

### Automatický checkpoint 2026-07-23 06:32 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Doplněn atomický přechod konfigurace Rodinného kalendáře z disabled do dry_run
- Ověření: plná Cockpit brána: 1083 testů, 308.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_config_transition.py`, `Samantha_Agent/scripts/family_calendar_delivery_config_enable_dry_run.py`, `Samantha_Agent/tests/test_family_calendar_delivery_config_transition.py`
- Commit: `Doplnit bezpečný přechod kalendáře do dry-run`
- Další krok: V hlavním prostředí spustit pouze read-only preview skriptu family_calendar_delivery_config_enable_dry_run.py bez --apply.

### Automatický checkpoint 2026-07-23 07:11 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán read-only orchestrátor dnešních D-2/D-1 kandidátů s redigovaným CLI a aktivními pojistkami proti runtime I/O
- Ověření: plná Cockpit brána: 1091 testů, 226.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_dry_run.py`, `Samantha_Agent/scripts/family_calendar_delivery_dry_run.py`, `Samantha_Agent/tests/test_family_calendar_delivery_dry_run.py`
- Commit: `Doplnit provozní dry-run rodinného kalendáře`
- Další krok: Spustit redigovaný provozní dry-run v prostředí vlastnícím privátní kalendář a konfiguraci

### Automatický checkpoint 2026-07-23 07:50 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán iCloud STARTTLS klient s povinně injektovanou SMTP relací, redigovanými výsledky a testy bez sítě
- Ověření: plná Cockpit brána: 1097 testů, 232.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_icloud_smtp_client.py`, `Samantha_Agent/tests/test_family_calendar_icloud_smtp_client.py`
- Commit: `Doplnit testovaný iCloud SMTP klient rodinného kalendáře`
- Další krok: Připravit samostatný přesně potvrzovaný testovací runner s lokálním iCloud tajemstvím

### Automatický checkpoint 2026-07-23 08:06 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán bezpečný jednorázový SMTP runner s redigovaným preview, přesným potvrzením a testy bez sítě
- Ověření: plná Cockpit brána: 1105 testů, 218.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/family_calendar_delivery_test_email.py`, `Samantha_Agent/scripts/family_calendar_delivery_test_email.py`, `Samantha_Agent/tests/test_family_calendar_delivery_test_email.py`
- Commit: `Doplnit potvrzovaný iCloud testovací e-mail rodinného kalendáře`
- Další krok: Spustit pouze redigovaný preview runneru v prostředí s privátní konfigurací a teprve samostatně potvrdit jeden skutečný testovací e-mail

### Dokumentační checkpoint 2026-07-23 17:07 CEST

- Stav byl obnoven z nejnovějšího nouzového autosavu bez opisování soukromých
  údajů. Dva dřívější živé testovací pokusy vrátily `delivery_unknown`;
  pozorované doručení bylo nulové, ale tyto staré výsledky zůstávají nejisté.
- No-send autentizační diagnostika a envelope preflight následně potvrdily
  funkční přihlášení, přijetí odesílatele i všech čtyř příjemců, `RSET` a
  nulové volání `DATA` nebo odeslání.
- Diagnostický hotfix v commitu `d38a37f` oddělil potvrzení `DATA` od
  následného `QUIT`. Potvrzené `DATA` se už při chybě ukončení relace
  nepřeklasifikuje na `delivery_unknown`.
- Ověření hotfixu: 158 kalendářových testů, plná brána 1134 testů, vzdálená
  Quality Gate, nasazení, řízený restart a smoke test 5/5 prošly.
- `d38a37f` je na `main` i `origin/main`. Automatické odesílání zůstává
  vypnuté a při obnově neběžel žádný testovací SMTP runner.
- Další krok: právě jeden nový, ručně a přesně potvrzený testovací e-mail přes
  nasazený hotfix. Při jakémkoli jiném výsledku než úplně potvrzeném přijetí
  nic automaticky neopakovat.

### Dokumentační checkpoint 2026-07-23 17:25 CEST

- Právě jeden nový testovací e-mail byl po redigovaném preview ručně a přesně
  potvrzený. App-specific heslo bylo zadáno skrytě mimo chat.
- SMTP výsledek: `status=sent`, `recipient_count=4`, `accepted_count=4`,
  `refused_count=0`, `unknown_count=0`, `transport_called=true` a
  `session_close_ok=true`.
- Míla následně potvrdil skutečné doručení `RECEIVED_COUNT=4`.
- Testovací brána je tím úspěšně uzavřená. Automatické D-2/D-1 odesílání
  zůstává vypnuté.
- Další krok: samostatná read-only revize cesty k automatickému provozu,
  zejména plánovače, přechodu režimu, persistence, idempotence a recovery.
  Během revize nic nezapínat ani neodesílat.

### Vývojový checkpoint 2026-07-23 19:52 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán dedikovaný plánovací vstup, který pouze deleguje na existující
  provozní dry-run a nemá cestu k SMTP, odesílání ani zápisu runtime stavu.
- Ověření: 167 kalendářových testů a plná Cockpit brána 1143 testů prošly.
  Živý redigovaný dry-run nevolal koordinátor ani transport a nevytvořil
  stavový nebo worker soubor.
- Readiness posun: `planner_runner_missing` je uzavřený; zbývá
  `planner_not_installed`, chybějící Keychain reference a nedostupný
  automatický režim.
- Změněné cesty před paměťovým zápisem (4):
  `Samantha_Agent/scripts/family_calendar_delivery_run.py`,
  `Samantha_Agent/scripts/cockpit_quality_gate.py`,
  `Samantha_Agent/tests/test_cockpit_quality_gate.py`,
  `Samantha_Agent/tests/test_family_calendar_delivery_dry_run.py`.
- Commit: `Doplnit bezpečný plánovací runner rodinného kalendáře`
- Další krok: Po začlenění do `main` vytvořit pouze read-only náhled budoucí
  LaunchAgent konfigurace; nic nezapisovat, neinstalovat ani nenačítat.

### Vývojový checkpoint 2026-07-23 20:03 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán read-only náhled budoucí LaunchAgent konfigurace jako
  samostatný builder a JSON CLI bez apply, instalační nebo load cesty.
- Náhled validuje Python, plánovací runner a denní čas; kandidát pro 08:00 má
  `RunAtLoad=false` a `ProcessType=Background`.
- Ověření: 171 kalendářových testů a plná Cockpit brána 1147 testů prošly.
  Živý náhled nevytvořil plist, nevolal `launchctl`, nečetl Keychain,
  nevolal transport a neprovedl žádný zápis.
- Změněné cesty před paměťovým zápisem (5):
  `Samantha_Agent/app/family_calendar_delivery_planner_preview.py`,
  `Samantha_Agent/scripts/family_calendar_delivery_planner_preview.py`,
  `Samantha_Agent/tests/test_family_calendar_delivery_planner_preview.py`,
  `Samantha_Agent/scripts/cockpit_quality_gate.py`,
  `Samantha_Agent/tests/test_cockpit_quality_gate.py`.
- Commit: `Doplnit read-only náhled plánovače kalendáře`
- Další krok: Samostatně navrhnout potvrzovanou bránu pro zápis plist pouze
  v režimu `dry_run`; zatím plist nezapisovat ani nenačítat.

### Vývojový checkpoint 2026-07-23 20:52 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidána dvoukroková create-only instalační brána pro dry-run
  LaunchAgent plist. Preview vrací přesnou konfiguraci, fingerprint a
  potvrzovací kontrakt; apply znovu kontroluje nezměněné vstupy.
- Bezpečnost: zápis je atomický s právy `0600`, odmítá existující nebo
  symlinkový cíl a nemá cestu k `launchctl`, Keychain ani transportu.
- Ověření: 34 cílených bezpečnostních testů, 177 kalendářových testů a plná
  Cockpit brána 1153 testů prošly. Zápisové testy používaly pouze dočasné
  adresáře; živě proběhl pouze read-only preview a systémový plist nevznikl.
- Změněné cesty před paměťovým zápisem (5):
  `Samantha_Agent/app/family_calendar_delivery_planner_install.py`,
  `Samantha_Agent/scripts/family_calendar_delivery_planner_install.py`,
  `Samantha_Agent/tests/test_family_calendar_delivery_planner_install.py`,
  `Samantha_Agent/scripts/cockpit_quality_gate.py`,
  `Samantha_Agent/tests/test_cockpit_quality_gate.py`.
- Commit: `Doplnit potvrzovanou instalaci plánovače kalendáře`
- Další krok: Po checkpointu spustit z `main` pouze instalační preview.
  Skutečný create-only zápis vyžaduje další Mílovo rozhodnutí, přesnou
  potvrzovací větu a fingerprint; plist zatím nenačítat.

### Automatický checkpoint 2026-07-23 22:36 CEST

- Pracovní proud: `project-family-calendar`
- Souhrn: Přidán dvoukrokový create-only Keychain setup s redigovaným preview,
  přesným potvrzením a heslem zadávaným pouze skrytým systémovým promptem.
- Ověření: 185 kalendářových testů a plná Cockpit brána 1167 testů, výsledek
  OK. Živý read-only readiness audit potvrdil existenci reference bez čtení
  hesla, zápisu nebo odesílání.
- Změněné cesty před paměťovým zápisem (5):
  `Samantha_Agent/app/family_calendar_delivery_keychain_setup.py`,
  `Samantha_Agent/scripts/family_calendar_delivery_keychain_setup.py`,
  `Samantha_Agent/tests/test_family_calendar_delivery_keychain_setup.py`,
  `Samantha_Agent/scripts/cockpit_quality_gate.py`,
  `Samantha_Agent/tests/test_cockpit_quality_gate.py`.
- Commit: `Doplnit bezpečný Keychain setup kalendáře`
- Další krok: Z `main` vytvořit pouze read-only náhled budoucího načtení
  LaunchAgentu a rollback postupu; `launchctl` zatím nevolat, neměnit
  automatický režim a nic neodesílat.
