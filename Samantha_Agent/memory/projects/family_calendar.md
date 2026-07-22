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
- Kandidáti upozornění podporují D-2, D-1 a ochranu přes `sent_event_keys`.
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
- Kanonický handoff a TVBCP byly vytvořeny prvním automatickým checkpointem.
- E-mailové odesílání není aktivní.

## Bezpečnostní hranice

- Soukromý registr osob, narozeniny a kontaktní adresy nepatří do Gitu ani do
  projektové paměti.
- Příjemci budoucího náhledu musí být explicitní soukromý vstup; v Gitu,
  paměti a testech nesmějí být skutečné adresy.
- Automatické odesílání se nesmí zapnout bez samostatného návrhu a potvrzení.

## Nejmenší další krok

Zahájit samostatnou read-only fázi návrhu jednoho ručně potvrzovaného
testovacího e-mailu. Nejprve vymezit odesílací adaptér, pevnou bezpečnostní
bránu, auditní důkaz a zacházení s doručením; v této fázi ještě nic neodesílat
ani nezapínat automatické odesílání.
