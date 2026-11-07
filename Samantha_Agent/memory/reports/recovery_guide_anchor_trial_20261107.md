# REC-06 — malý anchor adapter a konkrétní cenová karta

2026-11-07, Data, pouze vlastní `data/parallel-20261104`.

## Výsledek

Připraven samostatný adapter pro dvě navazující modelové fáze nového anchor
protokolu a jeho neplacená karta. **Žádný placený pokus nebyl spuštěn.**
Původní uzavřený úplný v2 pilot se nemění ani neobnovuje. Jeho dříve doložených
21,013 Standard kreditu není rozpočtem ani souhlasem pro nový pokus.

Karta `recovery_guide_anchor_trial_card_20261107.json`:

- request `rec06-anchors-small-01`, approval SHA
  `566899e7663e4599f17fa462404ca609ef77e12566721c2ba88eafdbcddd8cb3`;
- připnutý main `0850e6f381fe359695e44c4381dbe388e7a86b00`, čtený jako Git
  objekty přes Data checkout; žádný vstup do Willovy pracovní kopie;
- celý původní TXT 1.2, beze změny SHA `a3659d9c…936935`, a dva celé dokumenty
  `C01c_RECOVERABLE_AUDIO.md`, `C02b_CHUNK_TRANSFER_EXPERIMENT.md`;
- celkem 75 100 UTF-8 bytů, dva dokumenty + original. Jde o záměrně malý
  kompatibilitní test, nikoli schválený manifest celé týdenní revize;
- explicitní kandidát `gpt-6.1-sol`, medium, Standard per-turn, bez aktivace
  či změny centrální role. Role JSON je součástí otisku implementace;
- nejvýše 1 inspect + 1 synthesize. Syntéza se spustí pouze po přesném
  přijetí první fáze. První chyba či nejistota uzavírá pokus pro další SDK akce.

Čtecí pozorování: existující sdílený server 0.163.0, místní CLI 0.166.0,
Sol/medium v katalogu a účet typu chatgpt. Není to důkaz platnosti tokenu,
konkrétního fakturačního režimu účtu ani modelového chování. Zděděná Standard
preference nevyhovuje; adapter proto vynucuje `serviceTierForTurn=default`
pouze pro každý svůj tah. Žádná konfigurace serveru se nezapisuje.

## Nové soubory a zapojení

- `recovery_guide_anchor_transport.py`: obal stávajícího sdíleného transportu,
  jeden nový ephemeral thread a jeden turn na fázi. Ověřuje vstup, schema,
  model/medium, instrukce, cwd, never approvals, read-only/network false.
  Zakazuje resume, další thread/turn, cizí thread a jiná RPC. Skryje dostupné
  tool families přes stejné existující per-thread omezení a eviduje nepovolené
  typy událostí. Oba thready sdílejí jednu existující socketovou connection;
  server se nespouští ani nerestartuje.
- `recovery_guide_anchor_costing.py`: úplný textový/schema preflight v již
  existujícím vlastním tokenizer prostředí. Zvlášť počítá dvě instrukce,
  celý payload a výstupní schema. Připíná verzi, Python/native implementaci,
  BPE tabulku, regex a special tokens. Nic neinstaluje.
- `recovery_guide_anchor_trial.py`: neměnný soukromý packet, exact approval,
  jeden trvalý job napříč předběžnými revizemi, čerstvost main/TXT/kódu,
  kontrola socketu/peer/protokolu a skutečné číselné spotřeby. Bez publisheru,
  plánovače, zápisu provozního TXT či změny role. `prepare()` je neplacený;
  `run(approved_digest=...)` je pouze pro trusted caller s konkrétním lidským
  souhlasem. Digest sám není podpis ani autorizace.
- `test_recovery_guide_anchor_trial.py`: syntetické RPC/události přes skutečný
  stávající klient. Bez živého socketu, modelu a soukromých pilotních souborů.
- Testy a compile paths připojené do `cockpit_quality_gate.py`; API zapsaná
  v `capability_routing_rules.md`, stav v projektové paměti/handoffu/TVBCP.

Privátní `.venv/recovery_rec06_anchor_trial` je odlišný od obou dřívějších
pokusů. Před prvním pokusem lze explicitně vytvořit novou neměnnou revizi
`prepare(refresh=True)` při změně zdrojů. Jakýkoli attempt/turn/context tuto
cestu zablokuje. Neexistuje reset, opakování ani pokračování částečného běhu.
Opakovaný run vrátí původní receipt i po procesní smrti nebo v jiném týdnu.

## Přesná přejímka malého testu

Inspect musí pokrýt právě dva očekávané source/anchor páry, každý současně
v coverage i jednom finding. Program vrací přesný zdrojový řádek; neopravuje
modelový quote. Nejvýše dvě findings, každé 1 500 UTF-8 bytů a jeden odkaz;
raw inspect odpověď nejvýše 14 000 bytů. Přidání quote, jiného řádku či
neúplná coverage je chyba a syntéza se neodesílá.

Syntéza vzniká deterministicky z konkrétního přijatého inspect requestu a
jeho skutečné raw odpovědi. Její konkrétní SHA/schema nejsou známy před prvním
tahem; karta proto připíná implementaci tohoto odvození a rozsah, nikoli
vymyšlený budoucí hash. Uvedené synthesis_fixture SHA jsou jen referenční
cenový podklad. Skutečný request se před druhou fází uloží a celý znovu
spočítá; změna tokenizeru nebo překročení schválené vstupní rezervy zastaví
pokus ještě před druhým thread/start. Žádné zkracování historie nebo zdrojů.

Syntéza zachová doslovně celý original v unchanged části a přidá právě dva
odstavce unverified s těmito evidencemi. Znovu prochází původním quality
validátorem. Přijatá zkouška by prokázala malý protokol/transport, nikoli
věcnou správnost návodu, nastavení Macu/iPhonu ani celou týdenní funkci.
Celý text zůstane pouze uvnitř soukromé raw účtenky, veřejně jen SHA kandidáta.

## Cena a známé meze

| Fáze | Referenční input | Input s rezervou | Output přijímací rezerva |
| --- | ---: | ---: | ---: |
| inspect | 32 556 | 48 695 | 4 096 |
| synthesis | fixture 27 590 + 18 256 allowance | 65 308 | 32 000 |

Reference je **o200k_base, tiktoken 0.14.0**, nikoli přesné upstream mapování
Solu či celý App Server prompt. Vstupy mají násobek 1,25 a 8 000 tokenů režie
na tah. Syntéza navíc rezervuje UTF-8/JSON velikost dvou finding textů a změnu
request hash. To je konzervativní textový odhad pro referenční encoding,
ne prokázaný horní odhad účtování nebo kontextu Solu.

Sazby ověřeny 2026-11-07 v [OpenAI Docs — Token rates](https://learn.chatgpt.com/docs/pricing#token-rates):
50 input, 2,5 cached input, 250 output Standard kreditů za milion tokenů.
Plán nepředpokládá cache: **14,72415 Standard kreditu**, navržená přijímací
mez **15 kreditů za oba tahy dohromady**. Jde o nový samostatný souhlas.

**Mez není tvrdý fakturační/output cap.** Spotřeba, délka a cena se vyhodnocují
po doručení; chybějící usage zůstane unknown. Před wire se total cost označí
neznámá; částečná známá cena se vede samostatně, ne jako nulový celkový účet.
Čas 300 s na tah je také následná přijímací mez. Transport 90 s znamená čekání
na jednotlivou zprávu, ne tvrdý end-to-end limit a automatické zrušení modelu.
Nejistý běh se nikdy neposílá znovu. Program nepřepíná model ani nezvyšuje cenu.

Standard override a outputSchema jsou doloženy
[OpenAI Docs — App Server Turns](https://learn.chatgpt.com/docs/app-server#turns).
Nový anchor schema/model zatím nebyl živě ověřen. Nástrojový backend
unified_exec nemá zde samostatný vypínač; zakázaná shell exposure a audit
událostí nejsou absolutní důkaz neexistence nástroje před živou přejímkou.
Omezení read-only chrání zápisy, samo neprokazuje izolaci veškerého čtení.

## Ověření tohoto vývojového kroku

- 26 nových testů; konečná cílená anchor sada **50 OK**. Pokrývá také
  skutečný klient s falešnými RPC/událostmi, změnu socketu/zdrojů/tokenizeru,
  pád po wire, neznámou cenu, přesné přijetí karty a zákaz opakování.
- Plná projektová brána OK: **2 668 testů, 5 skipped**, 544,106 s testů.
  Finální statická brána a git diff --check také OK.
- `recovery_guide_anchor_trial_offline_20261107.json`: fixture přes skutečný
  původní TXT a dva připnuté celé dokumenty prošla inspect i synthesis,
  včetně nezměněného quality gate. **Není to modelový výsledek.**
- Nový stav po přípravě obsahuje jen packet/lock, žádný attempt/turn/context.
  Původní čtyři stavové/raw soubory mají stejné hashe jako před přípravou.
- Žádné SDK/modelové volání, zápis provozního TXT/iCloud, aktivace role,
  služba, push, nasazení ani zásah do Willovy pracovní kopie.

## Další krok

Po úspěšné plné bráně a lokálním commitu předložit konkrétní kartu k přijetí
dvou placených tahů. Před run znovu ověřit stejný digest a čerstvost zdrojů,
socketu, serveru a implementace. Při driftu žádný placený tah; explicitní
neplacená revize je přípustná pouze před jakýmkoli pokusem a musí se znovu
přijmout. Po úspěchu zvlášť nacenit celý korpus a nové shrnutí, nikoli pokračovat
z rozpočtu či účtenek starého v2. REC-06 a týdenní aktivace zůstávají otevřené.

## Změněné soubory

- memory/ACTIVE_PROJECTS.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/capability_routing_rules.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- scripts/cockpit_quality_gate.py
- app/recovery_guide_anchor_costing.py
- app/recovery_guide_anchor_transport.py
- app/recovery_guide_anchor_trial.py
- memory/reports/recovery_guide_anchor_trial_20261107.md
- memory/reports/recovery_guide_anchor_trial_card_20261107.json
- memory/reports/recovery_guide_anchor_trial_offline_20261107.json
- tests/test_recovery_guide_anchor_trial.py
