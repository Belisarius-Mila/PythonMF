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
- Cílených 19 testů a plná lokální Cockpit brána s 980 testy prošly.
- Kanonický handoff a TVBCP byly vytvořeny prvním automatickým checkpointem.
- E-mailové odesílání není aktivní.

## Bezpečnostní hranice

- Soukromý registr osob, narozeniny a kontaktní adresy nepatří do Gitu ani do
  projektové paměti.
- Příjemci budoucího náhledu musí být explicitní soukromý vstup; v Gitu,
  paměti a testech nesmějí být skutečné adresy.
- Automatické odesílání se nesmí zapnout bez samostatného návrhu a potvrzení.

## Nejmenší další krok

Navrhnout samostatné read-only zobrazení náhledu v Cockpitu nad hotovým
builderem. Nadále bez odesílání, bez persistence doručení a bez skutečných
adres v Gitu, paměti nebo testech. Ručně potvrzený testovací e-mail smí přijít
až jako další oddělená fáze.
