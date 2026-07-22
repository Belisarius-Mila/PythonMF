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

Co je hotove:
- Builder vrací pro přesně dva různé příjemce událost, věk, režim D-2/D-1,
  předmět a tělo bez I/O nebo odesílání.
- Cockpit přijímá dvě serverově validované adresy, události odvozuje ze
  soukromého registru a náhled zobrazí bez odesílání nebo persistence.
- Odpověď používá `no-store`, UI bezpečné `textContent` a při zavření okna
  adresy z formuláře vymaže.
- Implementační commit `021adf5` je na `main` a `origin/main`; plná brána
  983 testů, vzdálená GitHub Gate, živý smoke 5/5 a ruční test prošly.
- Kanonický handoff a TVBCP existují.

Co neni hotove:
- Odesílání ani persistence doručení nejsou implementované.
- Není navržená ani potvrzená bezpečnostní brána pro testovací e-mail.

Dalsi krok:
Zahájit samostatnou read-only fázi návrhu jednoho ručně potvrzovaného
testovacího e-mailu; zatím nic neodesílat.

Navrhovane dalsi kroky:
- Po schválení návrhu implementovat pouze minimální potvrzované testovací
  odeslání; automatické odesílání ponechat vypnuté.

Zmenene nebo relevantni soubory:
- `app/family_calendar.py`
- `app/cockpit.py`
- `tests/test_family_calendar.py`
- `tests/test_family_calendar_cockpit.py`
- `.github/workflows/cockpit-quality-gate.yml`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

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
