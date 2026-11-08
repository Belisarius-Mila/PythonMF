# REC-06 — přesný číselný protokol zapojený do běhového adapteru

2026-11-08, Data, vlastní větev `data/parallel-20261104`.

## Výsledek a rozsah

Technická integrace `source_citation_index_v1` je dokončená: samostatný
executor používá přesné číselné wire requesty, izolovaný worker reprodukuje
jejich mapy a schema, ověřuje raw odpovědi a předává všechny přijaté dávky
závěrečné syntéze. Výsledek může vzniknout pouze jako soukromý kandidát.
Nový placený běh, provozní TXT/iCloud, role, scheduler, služby, push ani
nasazení nejsou tímto krokem provedené nebo povolené.

Nové `recovery_guide_anchor_exact_pilot.py` a `recovery_guide_anchor_exact_worker.py`
nepřepisují původní full executor/worker. Z původního executor souboru se
používá pouze transportní pozorovatel terminálních událostí `ObservedTurn`;
nevstupuje do jeho jobu. Nový pevný request `rec06-exact-indices-full-01`
a vlastní stav jsou odlišné. Obě implementace jsou součástí otisku nové karty.

## Konkrétní karta k novému schválení

- Approval digest: `741e71daf575220121eea137cc59d693b57ee8607abfa51c82171758d492f570`.
- Plan digest: `586cdf965f8b33dc2fb2340aac02b1cf07bf4f828f52350dfa7c9333cf3a3add`.
- Zdrojový main: `6c61028794950b3167eb4f90a47fdcf37df8e619`.
- Celý původní TXT + **532 dokumentů**, 6 332 788 B textů; 114 ostatních
  textových souborů mimo schválený návrh rozsahu. Nejde o důkaz úplné inventury aplikací.
- **20 inspect + 1 synthesis**, `gpt-6.1-sol`, medium, per-turn Standard/default.
- Plán bez cache **237,88715 kreditu**, navržená přijímací mez **240 kreditů**.
- Synthesis input 235 090 / současná mez 240 000; output acceptance 32 000.
  Inspect output 4 096; časy inspect 300 s / synthesis 900 s, celý běh 6 900 s.
- Čtecí runtime preflight: peer 0.163.0, místní CLI 0.166.0, ChatGPT account type,
  přesný model/effort dostupný. Čísla neoznačují nejnovější vydání CLI.
- Příprava provedla pouze audit a čtecí RPC; skutečný job je `not_started`,
  nula modelových pokusů. Karta připíná kód, zdroje, tokenizer, runtime i socket.

Předchozí offline plán a59c80c4 zůstává zachovaný. Nová revize přidává
explicitní synthesis output mez a čerstvý main, který mezitím obsahuje další
dokument. Karta nemění dřívější souhlas a sama neopravňuje volání `run`.
Plán a karta jsou v připojených `*_execution_plan_20261108.json` a
`*_execution_card_20261108.json`; plné vstupy jsou pouze v soukromé .venv.

## Podporované vlastnosti

| Oblast | Výsledek |
| --- | --- |
| Celé texty | Celý original v každé fázi, každý vybraný dokument přesně jednou v inspect; bez krácení |
| Přesné citace | Per-request source/index doména, kontrola wire/schema/map hashů, interní decode do původního exact resolveru |
| Syntéza | Všechny dávky, raw a findings; samostatně přečíslovaná pouze předaná dokumentová evidence |
| Spojení a model | Jedno připojení pro celý run, vlastní ephemeral thread pro každou fázi; přesný Sol/medium/Standard |
| Oprávnění | Read-only/network false, never approval, vypnuté tool families, audit neočekávaných událostí |
| Události | Commentary oddělené od final_answer, korelace vláken/tahů, terminální usage a strukturované chyby |
| Selhání | Trvalý marker před odesláním, raw před přejímkou; nejistota, timeout, pád, willRetry ani další volání neopravňují nový send |
| Soukromí | Raw/error data v soukromém stavu; veřejné karty bez obsahu zdrojů, socketu, účtu a konfigurace |
| Kandidát | Stejný quality gate, kontrola hashů, jediný soukromý soubor; žádné automatické publikování |

## Výslovné limity

- Nový wire/schema formát není živě ověřen modelem/providerem. Offline důkaz
  neprokazuje obsahovou správnost budoucí modelové odpovědi ani kontextový limit.
- o200k_base je referenční tokenizer, nikoli záruka přesného účtování Sol.
  Přijímací cena/output/čas nejsou tvrdé serverové ani fakturační stropy.
- Nové příkazy bez registrovaného allowlistu a současná nastavení Mac/iPhone
  bez doložených živých faktů zůstávají nepodporované. Gate se neoslabuje.
- Seznam aplikací a fyzická přejímka Macu/iPhonu nejsou dokončené. Kandidát
  z tohoto pilotu není automaticky schválený nový obnovovací návod.
- Role, produkční scheduler a obě cílové kopie nejsou zapnuté; jejich dřívější
  základ zůstává oddělený. Celý týdenní agent proto dosud není v provozu.

## Ověření

- 46 nových kontraktních testů: skutečný klient nad syntetickými RPC/událostmi
  a skutečný nový worker. Pokrývají i ztrátu spojení, procesovou smrt mezi
  dávkami, cenu/čas/usage, nepovolené ID, starý formát, cizí zdroj, drift
  kódu/zdrojů/socketu, změnu historie a bezzápisový/nepřipojující status/replay.
- Úplná skutečná zdrojová fixture přes nový executor/worker a izolovaný
  skutečný tokenizer **prošla 20+1**. Všech 532 dokumentů přesně jednou,
  celý původní návod v každé fázi, všech 20 findings v syntéze; soukromý
  kandidát prošel původním quality gate a kontrolou SHA. Wire byl syntetický,
  skutečná modelová volání i spojení do runtime: nula.
- Nezávislá kontrola uložených účtenek potvrdila přesné bajty a wire/map SHA.
  Replay neotevřel klienta ani nevyslal akci, status zachoval všechny bajty i
  mtime. Doklad `recovery_guide_anchor_exact_execution_offline_20261108.json`.
- Plná kanonická brána **OK: 2 794 testů, 5 přeskočeno**, 539,094 s testů.
  Závěrečná statická brána i git diff --check OK.

Všech 24 JSON v pěti původních stavech/plánech i původní raw `6177159d…505b55a` jsou shodné
s předchozími SHA. Uzavřený job zůstává attention / 9,58995, přijatých
dávek nula. Nové číslování neopravuje jeho `l131111`, nezachraňuje notes
ani nepřenáší zbývajících 20 modelových tahů do nového souhlasu.

## Změněné soubory (19)

- Kód: `recovery_guide_anchor_exact_pilot.py`, `recovery_guide_anchor_exact_worker.py`,
  `recovery_guide_anchor_exact_plan.py`.
- Testy/brána: `test_recovery_guide_anchor_exact_pilot.py`,
  `test_recovery_guide_anchor_exact_worker.py`, `test_recovery_guide_anchor_exact_schema.py`,
  `cockpit_quality_gate.py`.
- Doklady: tento report, `recovery_guide_anchor_exact_execution_plan_20261108.json`,
  `recovery_guide_anchor_exact_execution_card_20261108.json`,
  `recovery_guide_anchor_exact_execution_offline_20261108.json`.
- Projektový zápis: `ACTIVE_PROJECTS.md`, `MEMORY_INDEX.md`, `LESSONS_LEARNED.md`,
  `samantha_external_backup.md`, `recovery_guide_maintainer.md`,
  `capability_routing_rules.md`, `handoffs/workstreams/project-samantha-infrastructure.md`,
  `tvbcp/workstreams/project-samantha-infrastructure.md`.

## Jediný bezprostřední krok

Po souhlasu Míly s konkrétní novou kartou zavolat jednou registrované
`app.recovery_guide_anchor_exact_pilot.run(approved_digest=...)` s výše
uvedeným úplným approval digestem a programově počkat na stejnou účtenku.
Při nejistotě číst `status()`; neopakovat model, nezakládat náhradní job.
Při změně připnutých vstupů běh odmítne; změněná karta vyžaduje nové přijetí.
Není potřeba další vývoj adapteru před touto zkouškou.
