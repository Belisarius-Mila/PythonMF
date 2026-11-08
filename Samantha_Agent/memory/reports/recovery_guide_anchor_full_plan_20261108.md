# REC-06 — neplacený plán celého anchor korpusu

2026-11-08, Data, pouze vlastní `data/parallel-20261104`.

## Výsledek a rozsah

Připraven a skutečným izolovaným tokenizerem spočten nový **neplacený plán**.
Žádný modelový tah, nové vlákno, publikace TXT ani aktivace neproběhly.
Plán není exekuční karta a nyní neexistuje nový placený `run()` adapter.
Souhlas se spuštěním se v této etapě nepožaduje.

- Plan SHA `dcfb8b2aa73432d30117931c01a7bb90ad0f6980ae0bbef302e0f11c5c6f805d`.
- Připnutý main `6d5b576bb0901b09eb8f36cdf0c5131f2137315f`, načtený jako Git
  objekty přes Data checkout, bez vstupu do Willovy pracovní kopie.
- **531 dokumentů + celý původní TXT**, 6 314 979 UTF-8 bytů, **20 čtecích
  dávek + 1 syntéza**. Každý vybraný dokument právě jednou, bez dělení či
  krácení jednotlivých zdrojů; celý původní TXT v každé čtecí dávce.
- Návrh rozsahu je stejná veřejná sledovaná dokumentace Samantha/PythonMF,
  připojené docs/MatysekANJ/iOS a README/AGENTS. Přesné cesty, hashe, scopes
  a počet ostatních vynechaných textů jsou v JSON. Nejde o tvrzení úplnosti
  inventury všech aplikací, živých nastavení, soukromých dat či rozepsaných worktrees.
- Kandidát zůstává explicitně gpt-6.1-sol / medium / Standard. Centrální role
  se nemění. Čtecí runtime pozorování: server 0.163.0, místní CLI 0.166.0,
  Sol/medium v katalogu. Kontextový limit a pricing basis účtu nejsou ověřené;
  zděděná Standard preference nevyhovuje, budoucí adapter musí připnout per-turn default.

Původní immutable plán `5370e4fb…949480` byl po lokálním zpřesnění plánovače
zachován; finální revize má výše uvedený SHA v privátním `revisions/`.
Obě verze jsou čistě neplacené plány. Nevznikl či neobnovil se žádný modelový
job. Explicitní refresh nikdy nesahá na žádný dřívější placený slot.

## Výpočet ceny a času

| Rezerva | Hodnota |
| --- | ---: |
| Input všech fází s marží | 4 300 579 tokenů |
| Inspect output | 20 × 4 096 tokenů |
| Synthesis output | 32 000 tokenů |
| Všechen output | 113 920 tokenů |
| Plán bez cache | **243,50895 Standard kreditu** |
| Navržená přijímací mez | **250 kreditů**, dosud neschválená |
| Inspect časová mez | 300 s / dávku |
| Synthesis časová mez | 900 s |
| Součet časových mezí | 6 900 s = 115 minut |

Součet časových mezí není předpověď běžné délky ani tvrdé zrušení po timeoutu.
Syntéza vychází z měření malého testu: 400,240 s při 19 837 output tokenech;
přepočet na rezervu 32 000 s 25% marží dává 807,058 s, zaokrouhlený návrh
je 900 s. Jde o budoucí plán, **nikoli změnu 300 s limitu uzavřeného testu**.

Textový počet používá o200k_base / tiktoken 0.14.0 jen ve vlastním izolovaném
prostředí. Připíná implementaci, BPE tabulku, regex i special tokens. Úplné
instrukce jsou počítané dvakrát, dále celý skutečný wire payload a schema.
Marže je 1,25 + 8 000 tokenů režie na tah. Přesné mapování Solu, skrytý App
Server prompt a živý kontext nejsou tímto měřením prokázané.

Sazby ověřeny 2026-11-08 v [OpenAI Docs — Token rates](https://learn.chatgpt.com/docs/pricing#token-rates):
50 input / 2,5 cached input / 250 output Standard kreditů za milion tokenů.
Cache se nepředpokládá. Meze jsou přijímací rezervy; **nejsou tvrdý billing,
output ani wall-clock cap**. Nových 250 není navýšením žádného starého souhlasu.

## Jak je ohraničená syntéza

Pouhé sečtení čtecích vstupů nestačí: dopředu nejsou známé modelové findings
ani vybrané řádky. Nový samostatný `recovery_guide_anchor_full_plan.py` proto
obsahuje neplacený návrh obálky nad nezměněným vnitřním anchor protokolem:

- Všechny plné texty zůstávají v `anchor_request`. `citation_limits` navíc
  explicitně označí 782 řádků, jejichž přesný JSON evidence row přesahuje
  160 referenčních tokenů. Tyto řádky zůstávají čitelné, ale jako citace jsou
  v tomto omezeném protokolu nepodporované. Ani quote se nezkracuje.
- Každý zdroj má alespoň jednu povolenou neprázdnou citaci. Bez ní se celý
  plán zastaví před modelem; zdroj se nevynechá. Totéž při nadlimitním celém
  dokumentu, příliš mnoha zdrojích/dávkách nebo nadlimitní syntézní rezervě.
- Nejvýše 6 findings/dávku, 2 evidence/finding a 1 000 referenčních tokenů
  pro celý JSON findings. Vnitřní response validátor zůstává aktivní a nové
  offline kontroly odmítnou překročení. Omezený počet findings sám nezaručuje,
  že model zachytí všechny relevantní změny; je nutné následné obsahové review.
- Pro syntézu je rezervováno až **771 evidence rows**, všechna findings,
  celý original, metadata a schema. Fixed reference 32 406, celý konzervativní
  referenční vstup 182 766; po marži **236 458 input tokenů** proti limitu 240 000.
- Úplná syntézní fixture s coverage všech 531 dokumentů a prázdnými findings
  má 61 287 referenčních tokenů. Je to konstrukční kontrola rozsahu, **nikoli
  modelový výsledek, hotové čtení dokumentace či cena skutečné syntézy**.
- Budoucí adapter musí všechny skutečné responses ověřit, nic nevynechat,
  vytvořit konkrétní syntézu z celé přijaté historie a před odesláním syntézy
  ji znovu celou přepočítat. Překročení znamená attention, nikoli krácení,
  nový model, další vlákno nebo opakování.

Připojené API `inspection`, `validate_inspection`, `synthesis`, `measure`
a `prepare` jsou nyní čistě plánovací/offline. Nová obálka a její užší meze
zatím nebyly modelově ověřené. Dřívější malý živý test prokázal původní
vnitřní source/anchor kontrakt, nikoli tuto novou celou orchestraci.

## Ověření a zachovaná izolace

- 18 nových testů, společná cílená sada **68 OK**: celé texty/coverage,
  nepodporované citace, nadlimitní dokument, náklad celé syntézy, žádné
  krácení findings, změna zdrojů, immutable plán a absence placeného run.
- Plná projektová brána **2 686 OK / 5 skipped** (386,801 s testů),
  finální statická brána a git diff --check také OK.
- `recovery_guide_anchor_full_plan_offline_20261108.json` ověřuje všechny
  připnuté zdroje, request hashe, úplné texty a syntézní fixture. Nejde o live QA.
- Všechny JSON soubory obou dřívějších uzavřených placených jobů byly
  porovnány s počátečními hashi; žádný se nemění ani neobnovuje.
- Výstup je pouze ve vlastní privátní .venv a Git-safe reportech. Žádná
  instalace závislostí, změna společné .venv, role JSON, globálního CLI,
  produkčního klienta/runtime, provozního TXT/iCloud, služby, push nebo nasazení.

## Přesný další integrační krok

Dokončit samostatný běhový adapter, např. nový `recovery_guide_anchor_full_pilot.py`:
vybírá přesný plan_digest, ověřuje snapshot/kód/tokenizer, účelově připíná
peer/socket/účet/Standard, před thread i turn ukládá trvalý společný job/slot,
ukládá raw účtenky před přejímkou a nikdy neopakuje nejistý výsledek. Adapter
musí vynutit nové bounded response kontroly i konkrétní syntézní přepočet,
fázové/úhrnné přijímací rezervy a původní quality gate. Nemá publikovat návod.

Až po této implementaci, testech a novém ověření čerstvosti vznikne skutečná
exekuční karta se samostatným souhlasem. Teď žádný takový souhlas nechybí:
placený vstup záměrně není implementovaný. Will má nejprve přezkoumat plán
a izolovaný diff; převzetí nových commitů do main zneplatní tento snapshot
a vyžádá novou neplacenou revizi. Úplná inventura aplikací/Mac/iPhone,
obsahové přijetí, dvě kopie/upload a týdenní aktivace jsou pozdější přejímky.

## Změněné soubory

- memory/ACTIVE_PROJECTS.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/capability_routing_rules.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- scripts/cockpit_quality_gate.py
- app/recovery_guide_anchor_full_plan.py
- memory/reports/recovery_guide_anchor_full_plan_20261108.json
- memory/reports/recovery_guide_anchor_full_plan_20261108.md
- memory/reports/recovery_guide_anchor_full_plan_offline_20261108.json
- tests/test_recovery_guide_anchor_full_plan.py
