# REC-06 — celý běhový anchor adapter a exekuční karta

2026-11-08, Data, vlastní `data/parallel-20261104`. Pouze vývoj/neplacená
příprava. **Žádný nový placený tah nebyl spuštěn.**

## Připravená karta

- Approval SHA `4b22ea9e497007087bafe9d73536057bbe3db20c1ed1053a625a629ac4cce1d1`.
- Přesný plán `dcfb8b2a…c6f805d`, main `6d5b576b`, 531 dokumentů + celý
  original, 20 inspect + 1 synthesize, nejvýše **21 modelových tahů**.
- Explicitní kandidát gpt-6.1-sol, medium, Standard per-turn. Centrální role
  se nemění ani neaktivuje. Připnutý existující server 0.163.0, CLI 0.166.0,
  účet typu chatgpt; skutečná fakturační identita a dostupný kredit nejsou tím prokázané.
- Plán bez cache **243,50895 Standard kreditu**, navržená přijímací mez **250**.
  Čtení 300 s/dávku, syntéza 900 s, celkem 6 900 s přijímacího času.
  Ani jedna mez není tvrdý billing/output/wall-clock strop či příkaz ke zrušení.
- `recovery_guide_anchor_full_pilot_card_20261108.json` uvádí celý manifest,
  rezervy, přesné instrukční/protokolové podmínky a omezení. Soukromý packet
  obsahuje zdrojové texty a identity socketu; veřejná karta je neobsahuje.

Nová karta vyžaduje samostatný lidský souhlas. Dřívější malá zkouška ani
neplacený návrh 250 kreditů ji neschválily. Nyní není vytvořen attempt,
thread, turn, candidate ani kontextový adresář nového pilotu.

## Implementace

`recovery_guide_anchor_full_pilot.py` poskytuje registrované Python API:

- `prepare(plan_digest=..., refresh=False)` načte přesnou immutable revizi,
  ověří digest/zdroje/kód, přepočítá plán a tokenizer v izolovaném procesu,
  čtecím RPC ověří přesný peer, Sol/medium, chatgpt účet a vlastněný socket.
  Uloží jednu soukromou kartu. Explicitní nová revize je možná jen před
  jakýmkoli attempt/turn/context, vždy pod stejným budoucím pevným jobem.
- `run(approved_digest=...)` přijímá jen přesný digest od trusted calleru s
  konkrétním lidským souhlasem. Změnu karty, zdrojů, modelu, parseru, roles
  JSON, transportu či protokolu nepřebírá. Před RPC uloží trvalý job a před
  turn/start marker delivery_unknown. Procesní smrt, timeout i částečně
  dokončený běh se nikdy automaticky neobnovují. Další run pouze vrací stejný
  záznam bez připojení; není reset/resume/nový týden jako obcházení slotu.
- `status()` je čisté čtení přesného lokálního jobu, bez mkdir, zámku,
  připojení, account/config RPC nebo modelu. Lze pozorovat počet pokusů,
  přijatých dávek, známou spotřebu a konečný stav.

Před každou novou fází se kontroluje zbývající kreditová rezerva a čas,
čerstvost zdrojů/implementace/protokolu, stejná socketová identita i runtime.
Těsně před wire proběhne kontrola znovu. Každá fáze používá nový ephemeral
thread přes jednu existující sdílenou connection. Není stdio fallback,
spuštění/restart daemonu ani thread/resume. Guard odmítne cizí či již použitý
thread, druhý turn, jiný vstup/schema, model/effort, sandbox nebo neplánované RPC.
`serviceTierForTurn=default` se vynucuje při každém odeslání; globální Fast
preference ani konfigurace modelových rolí se nezapisují.

Raw odpověď a numerická telemetry jsou uložené **před** JSON/kvalitativní
přejímkou. Strukturované RPC/turn chyby zůstávají v soukromých účtenkách,
ve veřejném jobu pouze bezpečný typ/kód. `willRetry` není svolení k dalšímu
turn/start. Neznámá celková cena zůstane null, dřívější známé ceny samostatně.
Částečná usage před výpadkem se nepovažuje za konečnou. Terminální failed či
interrupted událost může zachovat známou číselnou spotřebu bez přijetí výsledku.

`recovery_guide_anchor_full_worker.py` provádí pouze offline práci v již
existujícím izolovaném tiktoken prostředí: audit plánu, rekonstrukci a hash
kontrolu každého requestu, bounded inspect a syntézu z **všech** přijatých
raw dávek. Nová historie se nezkracuje, findings se nevynechávají. Syntéza
se před svým odesláním znovu celá přepočítá. Při překročení, chybě nebo
neúplnosti nastane attention; další placená fáze se neodesílá.

Po validaci se kandidát uloží pouze jako soukromý `candidate.txt` s SHA.
`full_anchor_candidate_validated / accepted=true` označuje tento pilotní
kandidát, **nikoli přijetí návodu, publication grant, iCloud upload či aktivaci**.

## Zachované meze a přejímka

- Nové příkazy nemají přidaný workflow allowlist a nejsou přidaná live/manual
  fakta Macu/iPhonu. Původní quality gate je odmítne, pokud jsou potřebná
  a chybějí. Nepřidávaly se výjimky, odhadnuté aplikace ani věrohodně znějící
  důkazy. Tento pilot nezaručuje přijatý celý návrh, úplnou aplikační inventuru
  ani věcnou správnost všech nastavení; raw výsledky zůstanou pro review.
- Platí 160 referenčních tokenů na evidence row, nejvýše 6 findings/dávku,
  2 odkazy/finding a 1 000 tokenů findings JSON; 782 dlouhých řádků nelze
  citovat. Plné texty všech dokumentů přesto zůstávají nezkrácené. Omezení
  se kontroluje i na finálních original evidencích, ne pouze v inspect.
- Referenční o200k_base/tiktoken 0.14.0 není přesný tokenizer Solu; skrytý
  App Server prompt a skutečný limit kontextu nejsou ověřené. Rezervy a
  přesný přepočet jsou ochranné přijímací kontroly, nikoli záruka účtování.
- Shell exposure/MCP/skills a další tool families jsou omezené per-thread
  stejným existujícím helperem; nečekané typy událostí odmítnou výsledek.
  Unified exec backend nemá nezávislý vypínač. Není prokázaná absolutní
  izolace čtení ani nulové nástroje pro dosud nespouštěný celý pilot.
- Nová wire obálka a celý rozsah mají syntetický/offline důkaz. Starý malý
  živý test prokázal vnitřní anchor kontrakt; tento nový celý běh dosud neproběhl.

Sazby a plán jsou z dnešního [OpenAI Docs — Token rates](https://learn.chatgpt.com/docs/pricing#token-rates).
Per-turn Standard kontrakt je doložen v
[OpenAI Docs — App Server Turns](https://learn.chatgpt.com/docs/app-server#turns)
a v připnutém lokálním 0.163.0 schématu. Žádný globální Codex ani závislost
se neinstalovaly nebo neměnily.

## Ověření

- **43 nových testů**, společná cílená sada **111 OK**. Skutečný stávající
  klient proti falešnému RPC/event transportu, celá vícefázová sekvence,
  všechny findings v syntéze, nové thready/sdílený socket/Standard/schema,
  RPC error, failed/interrupted, retry signal a timeout, procesní smrt,
  neznámá usage, rozpočet/čas, aliasy, code/source/socket/tokenizer drift,
  immutable karty a nevystavení neveřejných chyb v jobu.
- Plná projektová brána **2 729 OK / 5 skipped** (397,198 s testů).
  Finální statická brána a git diff --check také OK.
- `recovery_guide_anchor_full_pilot_offline_20261108.json`: source/hash a
  úplná 20+1 fixture nad připnutým skutečným korpusem, bez modelových tahů.
  Konstrukční fixture není skutečné čtení modelu ani nový přijatý návod.
- Všechny JSON starého v2 jobu, malého anchor testu a přípravného full plánu
  jsou porovnané s počátečními hashi. Žádný nebyl přepsán či znovu spuštěn.
- Žádná změna produkčního klienta/runtime, Cockpitu/e-mailu/kalendáře,
  centrální role, provozního TXT, iCloudu, služby, push nebo nasazení.

## Další krok

Po uzavření bran a lokálním commitu předložit výše uvedenou konkrétní kartu
k samostatnému přijetí jednoho celého kandidátního pilotu. Před run znovu
ověřit stejný digest a čerstvost. Při změně main/kódu/runtime před pokusem
vzniká jen explicitní neplacená revize a nový souhlas; po markeru žádný reset.
Will má nejprve přezkoumat izolovaný diff a zachovat svou souběžnou práci.
Převzetí do main zneplatní původní zdrojový snapshot a vyžaduje novou kartu.
Obsahové přijetí, Mac/iPhone dossier, dvě cílové kopie/upload a týdenní
aktivace zůstávají samostatné pozdější kroky. Žádný z nich tento adapter neprovádí.

## Změněné soubory

- memory/ACTIVE_PROJECTS.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/capability_routing_rules.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- scripts/cockpit_quality_gate.py
- app/recovery_guide_anchor_full_pilot.py
- app/recovery_guide_anchor_full_worker.py
- memory/reports/recovery_guide_anchor_full_pilot_20261108.md
- memory/reports/recovery_guide_anchor_full_pilot_card_20261108.json
- memory/reports/recovery_guide_anchor_full_pilot_offline_20261108.json
- tests/test_recovery_guide_anchor_full_pilot.py
- tests/test_recovery_guide_anchor_full_worker.py
