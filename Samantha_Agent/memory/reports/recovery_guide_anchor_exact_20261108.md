# REC-06 — přesné domény citací: offline oprava a nový přepočet

2026-11-08, Data, pouze vlastní `data/parallel-20261104`.

## Výsledek

Nový samostatný kontrakt **source_citation_index_v1** dovoluje pro konkrétní
zdroj právě jeho vydané a povolené reference. Už neověřuje jen tvar `l+číslo`.
Původní přesný resolver, quality gate a rozpočtové kontroly zůstávají aktivní.
Žádný placený tah, obnovení starého jobu, publikace ani nasazení neproběhly.

Samostatné nové soubory:

- `recovery_guide_anchor_exact_schema.py`: immutable index, kompilace přesných
  inspect/synthesis schémat, explicitní dekodér nové verze a stávající kontroly.
- `recovery_guide_anchor_exact_plan.py`: neplacený přepočet celé dokumentace
  a immutable soukromý plán. Nemá `run`, nevolá model ani server.
- `test_recovery_guide_anchor_exact_schema.py`: 19 syntetických testů včetně
  nezávislého JSON Schema oracle (již instalovaný balíček, bez změny závislostí).

Původní core/plan/worker/executor se **neměnily**. Nový protokol zatím není
zapojen do běhového adapteru a nemá exekuční kartu ani souhlas s dalším modelem.

## Přesná reference bez velkého enum či přibližného regexu

Pro každý request vzniká neměnná tabulka `(source_id, citation_index) -> lN`.
`citation_index` je husté číselné pořadí **1 až počet povolených citací daného
zdroje**, nikoli fyzický řádek. Prázdné a nadlimitní řádky do tabulky nevstupují,
jejich úplný text zůstává v modelovém vstupu s null indexem. Všechny ostatní
texty i whitespace se zachovají; původní lN zůstává interní identitou resolveru.

Schema používá `integer` s `minimum=1`, `maximum=N`. `source_id` je přesný
enum. Nested `anyOf` váže oba parametry; zdroje se stejným N sdílejí větev,
protože jejich doména je ve všech případech právě 1…N. Nevznikne nepovolený
kartézský součin zdrojů a různých rozsahů. Root zůstává object, required
obsahuje všechny properties a additionalProperties je false.

Index/katalog/request mají oddělené SHA. Nový wire request má nové ID
odvozené z celé nové reprezentace a tabulky; čísla se nesmějí přenášet mezi
requesty. Syntéza nově očísluje právě předané dokumentové evidence plus
všechny povolené original reference. Nezíská nezaslané úseky dokumentace.

Dekodér po kontrole nové verze a request ID vytvoří nový **interní** core
response s původními lN. Nepřepisuje raw modelovou odpověď a nemá fallback
pro staré formáty. Strings, bool, zlomky, NaN/Inf a mimo-rozsahové hodnoty
jsou odmítnuté. JSON Schema chápe 1.0 jako matematické celé číslo; pouze tento
přesný význam lze převést na 1, nikdy ne textové "1" nebo odhad kotvy.

Přesný resolver následně znovu ověří vazbu ke zdroji a doslovnou citaci.
Platná reference stále není důkaz věcné správnosti tvrzení nebo skutečného
nastavení Macu/iPhonu. Limity findings/citací, registered-command/live-claim
gate a úplnost původního návodu nejsou uvolněné.

## Dokumentace a ověření schémat

Přečtená [OpenAI Docs — Supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas)
uvádí integer/minimum/maximum, nested anyOf a defs/ref. Omezení: 5 000
object properties, 10 úrovní, 1 000 enum values a 120 000 znaků jmen/enum/const.
Nová schémata nepotřebují regex lookaround, dlouhé seznamy anchor enumů ani
nepodporované if/then/not/allOf.

Nad skutečným připnutým korpusem bylo ověřeno **21 schémat** nezávislým
`jsonschema.Draft202012Validator`, **8 683 source-domain probes** a **99 874
mapování indexů**. Největší naměřené hodnoty schémat:

| Limit | Naměřené maximum |
| --- | ---: |
| Object properties | 195 |
| Enum values | 536 |
| Znaky jmen/enum/definice | 2 846 |
| Hloubka | 6 |
| JSON velikost schématu | 17 290 B |

Jde o lokální schema/decoder důkaz podle dokumentovaného subsetu. **Přijetí
nového formátu připojeným App Serverem a skutečným modelem nebylo živě
ověřené.** Testy nesmějí být vydávané za nový modelový výsledek.

## Regrese z konkrétní chybné odpovědi

Raw prvního celého pilotu zůstává SHA `6177159d…505b55a`, jeho job attention,
0 přijatých dávek a cena 9,58995 beze změny. Neopravoval se `l131111` ani
žádné jeho notes a neodeslal se zbytek původního plánu.

Pro čistě offline regresi vznikl **odvozený testovací protipříklad nové verze**:
ostatní reference jsou převedené pomocí vydané tabulky a problémové číslo je
131111. Není to skutečná ani opravená modelová odpověď. Nezávislý validator
zjistil právě jedinou chybu `covered.d0001`: `maximum=21`, tedy číslo 131111
nepatří do domény kořenového AGENTS.md. Samostatná pozitivní fixture je také
pouze konstrukční test; není přijetím původní dávky.

Celá 20+1 fixture zachovala všech 531 dokumentů a celý original; syntéza s
nezměněným originalem prošla původním quality gate. Není to obsahová revize.
Soukromé fixture obsahující skutečné texty zůstávají jen ve vlastní .venv;
Git-safe důkaz je `recovery_guide_anchor_exact_offline_20261108.json`.

## Nový neplacený plán a cena

Finální plan SHA `a59c80c453adc81d95104bdbee7e4736a3087204a38112168f68966ad516c070`,
main `6d5b576b`, **531 dokumentů + celý original**, 6 314 979 B,
**20 inspect + 1 synthesis**. Podrobnosti v `recovery_guide_anchor_exact_plan_20261108.json`.
Původní neplacený výpočet bbe5d4e6…611a1eb je zachován; finální plán
je v immutable `revisions/<plan_digest>.json`, nikoli přepsaný původní plan.json.

- Input s rezervou 4 179 159, output 113 920 tokenů.
- Nový konzervativní plán bez cache **237,43795 Standard kreditu**, návrh
  přijímací meze **240**. Proti předchozímu plánu je rezerva nižší o 6,071.
  Není to naměřená cena nového modelu, zaručená úspora ani schválený rozpočet.
- Synthesis rezerva 181 487 referenčních tokenů, po marži **234 859 input**,
  tedy v dosavadních 240 000. Skutečná syntézní fixture má 56 712 reference
  tokenů; cena reálné syntézy z ní neplyne.
- Cena zahrnuje nové instrukce, celé wire vstupy, schémata a rezervu budoucích
  skupin source-domain i všech findings/evidence. Skutečný syntézní request
  bude vždy vyžadovat nový celý přepočet před odesláním, nikoli krácení dat.
- Stále jen o200k_base/tiktoken 0.14.0, marže 1,25 + 8 000/tah, ne přesné
  Sol mapování ani tvrdý billing/output cap. Sazby jsou z dnešního
  [OpenAI Docs — Token rates](https://learn.chatgpt.com/docs/pricing#token-rates).
- Časový návrh 300/900 s zůstává, nepřepisuje staré nepřijaté časové meze.

## Brány a další krok

19 nových testů, cílená sada **130 OK**. Plná projektová brána **2 748 OK / 5 skipped** (430,239 s testů);
statická brána a git diff --check také OK.
Všechny JSON pěti dřívějších jobů/plánů zkontrolované proti původním hashům;
žádný změněný. Žádná změna klienta/runtime, role, živé služby, provozního
TXT/iCloudu, push, nasazení nebo nový modelový tah.

Další krok je explicitně zapojit novou verzi a její dekodér do samostatného
adapteru/workeru s novou přesnou exekuční kartou a přepočtem po případném
převzetí změn Willem. Původní executor/card/job zůstávají uzavřené a nemají
se používat pro novou reprezentaci či automaticky opakovat první dávku.
Před dalším placením určit konkrétní postup, kompatibilitu a využitelnost
známých validních částí bez opravování vadného ID; případný model musí mít
samostatný souhlas. V této offline etapě žádná exekuční karta nevzniká.

## Změněné soubory

- memory/ACTIVE_PROJECTS.md
- memory/LESSONS_LEARNED.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/capability_routing_rules.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- scripts/cockpit_quality_gate.py
- app/recovery_guide_anchor_exact_plan.py
- app/recovery_guide_anchor_exact_schema.py
- memory/reports/recovery_guide_anchor_exact_20261108.md
- memory/reports/recovery_guide_anchor_exact_offline_20261108.json
- memory/reports/recovery_guide_anchor_exact_plan_20261108.json
- tests/test_recovery_guide_anchor_exact_schema.py
