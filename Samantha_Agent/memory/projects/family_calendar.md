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
- Čistý builder náhledu upozornění zatím není implementovaný.
- E-mailové odesílání není aktivní.

## Bezpečnostní hranice

- Soukromý registr osob, narozeniny a kontaktní adresy nepatří do Gitu ani do
  projektové paměti.
- Příjemci budoucího náhledu musí být explicitní soukromý vstup; v Gitu,
  paměti a testech nesmějí být skutečné adresy.
- Automatické odesílání se nesmí zapnout bez samostatného návrhu a potvrzení.

## Nejmenší další krok

Implementovat jen čistou funkci pro sestavení náhledu: událost, D-2/D-1,
věk, přesně dva příjemci, předmět a tělo. Bez endpointu, bez persistence
odeslání a bez skutečného e-mailu.

Kanonický handoff a TVBCP mají stabilní lazy cesty, ale fyzické soubory vzniknou
až prvním potvrzeným checkpointem po zelené bráně.
