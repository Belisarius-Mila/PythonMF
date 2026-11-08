# REC-06 — celý anchor pilot zastaven po prvním známém tahu

2026-11-08, Data, pouze vlastní `data/parallel-20261104`.

Míla výslovně přijal jediný celý pilot podle karty `4b22ea9e…4cce1d1`
(531 dokumentů + original, nejvýše 21 Sol/medium Standard tahů, návrh
243,50895 / přijímací mez 250 kreditů, nikoli tvrdý billing cap).
Před spuštěním byla ověřena platnost karty, zdrojů/kódu a protokolu i absence
attemptu. Registrovaný `run(approved_digest=...)` byl zavolán **jednou**.

## Výsledek

**Pilot neprošel: attention / accepted=false.** První odpověď jednoznačně
completed/delivered, ale obsahuje nevydané ID kotvy. Řadič odmítl celou
dávku a dalších **20 plánovaných tahů se neodeslalo**. Není to výpadek či
nejisté doručení; jde o doloženou neplatnou hodnotu v odpovědi modelu.
Syntéza, kandidát ani nový provozní TXT nevznikly. Žádný retry či reset.

| Metrika | Výsledek |
| --- | ---: |
| Jedinečné modelové tahy | 1 |
| Dokumenty v první dávce / coverage keys | 27 / 27 |
| Findings / jejich evidence | 6 / 12 |
| Všechny odkazy / platná vydaná ID | 39 / 38 |
| Přijaté dávky | 0 |
| Input / cached input | 184 414 / 0 |
| Output / reasoning subset | 1 477 / 189 |
| Total tokenů | 185 891 |
| Délka modelového tahu | 34,567 s |
| Celý job včetně lokální režie | 57,990 s |
| Odhad Standard kreditu | **9,58995** |

Delivery, telemetry, input/output meze, čas i audit tool událostí prošly.
Nežádoucí typy nástrojových událostí nebyly pozorované. Cena je odhad ze
skutečné spotřeby podle připnutých Standard sazeb, nikoli fakturační účtenka.
Tato cena se nesčítá se starými joby jako cena jedné úlohy.

## Přesná příčina

`covered.d0001 = "l131111"` odkazuje na kořenový `AGENTS.md`, který má
**26 fyzických řádků**. Toto ID nebylo vydáno; nejde ani o existující prázdný
řádek. Zdroj má SHA `da5cfee3…e2e8`. Ostatních 26 coverage referencí a všech
12 finding referencí jsou vydaná ID v příslušném scope.

Současné output schema vynucuje formát `^l[1-9][0-9]*$`, který řetězec
`l131111` splňuje, ale neomezuje jej na skutečně vydané kotvy daného zdroje.
Přesný resolver tuto chybu správně odmítl. Structured output s platným tvarem
není důkazem platné reference. Dřívější malý úspěch ani offline fixtures
nedokazovaly, že model v novém velkém vstupu nevytvoří neexistující ID.

Bez dalšího modelu byly z raw zkontrolovány i ostatní meze: scope keys přesně
sedí, raw má 3 906 UTF-8 bytů, findings JSON **721 referenčních tokenů** proti
1 000, počet findings a jejich evidencí v limitu. Ostatní validní reference
nepřesáhly row limit, finding texty jsou bezpečné a evidence unikátní/v scope.
To není dodatečné přijetí chybné celé dávky ani důkaz věcné správnosti zjištění.

## Zachovaný důkaz a hranice

- `recovery_guide_anchor_full_pilot_result_20261108.json`: numerické metriky,
  úplný safe error kód, source/AID diagnostika a hashe; žádný text návodu.
- Raw SHA `6177159d990a5d0e69551876bdc109fc85f9401d2399bd012c19d9636505b55a`.
  Thread `01a1baa0-3785-7473-9dcc-1996a2623809`,
  turn `01a1baa0-3849-7e43-8efe-0760d5fc1204`.
- Původní raw/modelová odpověď i její request se neupravovaly. Vadné ID se
  nenahradilo odhadnutým řádkem; žádná fuzzy oprava, přijetí notes či pokračování.
- Starý v2 job, malý anchor test i přípravný plán mají stejné JSON hashe
  jako před tímto celým pilotem. Nový slot je uzavřený a nesmí se resetovat.
- Žádné další placené tahy, spuštění/restart služby, změna role/modelu,
  produkčního klienta/runtime, provozní TXT/iCloud, push či nasazení.
- Kód se neměnil; předchozí 111 cílených a 2 729 plných testů / 5 skipped
  zůstávají vývojovým důkazem. Aktuální statická brána a git diff --check OK.

## Přesný další krok

Neplaceně zpřísnit kontrakt **na skutečně vydaná a pro daný zdroj povolená ID**, ne jen na formát čísla.
Nejprve offline ověřit schéma, velikost a upstream limity pro konkrétní
source/anchor kombinace (například explicitní povolené hodnoty či přesný
vzor pro daný zdroj). Nestačí pouze omezit počet číslic nebo ID při čtení opravit.
Přesný resolver zůstává druhou nezávislou kontrolou.

Regrese má používat tuto raw odpověď jako fixture pouze pro doložení chyby,
bez jejího přepisování nebo přijetí starého jobu. Je třeba znovu spočítat
novou schématovou/tokenovou režii a teprve z konkrétního výsledku navrhnout
další integrační postup a případný nový souhlas. Nové schéma ani modelová
kompatibilita v této etapě nebyly implementované či ověřené.

Neodesílat znovu první dávku ani automaticky zbytek schváleného plánu.
REC-06, celý obsahový návrh, Mac/iPhone dossier, obě kopie/upload i týdenní
aktivace zůstávají otevřené. Lokální handoff/TVBCP předávají Willovi přesný
známý výsledek, nikoli pokyn k opakování nebo nasazení.

## Změněné soubory

- memory/ACTIVE_PROJECTS.md
- memory/LESSONS_LEARNED.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- memory/reports/recovery_guide_anchor_full_pilot_result_20261108.json
- memory/reports/recovery_guide_anchor_full_pilot_run_20261108.md
