# 05/P1 — kompatibilita klienta App Serveru a Python SDK

Datum: 2026-11-04. Autor: Data. Větev: `data/parallel-20261104`.
Etapa: izolovaný pilot, bez integrace, modelového volání a připojení k živému socketu.

## Výsledek a doporučení

**Dílčí úpravy současného klienta; SDK zatím neadoptovat do produkce.**
SDK 0.163.0 funguje proti syntetickému App Serveru se schématem instalované
CLI 0.166.0 v ověřené podmnožině. Je užitečné pro typy, obnovu bez přenosu
historie, proud událostí a RPC chyby. Není přímou náhradou kontraktu Samanthy:
veřejné `Thread.run/turn` nemá vlastní `clientUserMessageId`, výchozí schvalování
se liší, nemá nativní Unix transport a neposkytuje trvalý záznam nejistého doručení.
Úspěch syntetických testů není živým průkazem kompatibility celého protokolu.

## Podklady a hranice

- Přečteny `AGENTS.md`, `MEMORY_INDEX.md`, relevantní LL-018/019,
  kanonický Human–Adam handoff, pravidla TVBCP a infrastrukturní paměť.
- Bod 05 přečten z `Samantha_navrh_rozvoje_a_kontinualni_agent_2026-11-04.txt`
  v Downloads. Jeho údaj CLI 0.163.0 je historický; globální `codex --version`
  v této etapě vrátil **0.166.0**. Globální Codex se neměnil.
- Stabilní PyPI SDK bylo při ověření **openai-codex 0.163.0**. Přesná závislost
  `openai-codex-cli-bin==0.163.0` opravdu obsahuje CLI 0.163.0; samotná instalace
  SDK tedy není použitím globální CLI 0.166.0.
- SDK i testovací závislosti instalovány jen do nové ignorované `.venv` tohoto
  worktree. Sdílená `.venv`, requirements, modelové role a produkční kód beze změn.
- Použito pouze `--version`, `--help` a offline generování schémat. Nespouštěn
  App Server, daemon, proxy k živému socketu, Cockpit ani jiná služba.
- CLI schémata obou verzí, jejich otisky, prostředí a otisky produkčních
  souborů jsou v `codex_sdk_pilot_20261104_environment.json`.

## Mapa současného klienta a runtime

| Oblast | Současný stav | Důsledek |
| --- | --- | --- |
| `resume_thread` | Zachová přesné thread ID, cwd, sandbox, instrukce a případně model; nepošle `excludeTurns` | Zbytečné načítání historie, historicky až přibližně 44 MiB obrázkového vlákna |
| Stránkování | `list_models` prochází `nextCursor`; obsluha stránek historie není implementovaná | Nevytvářet náhradní plošné načítání historie |
| `send_text` | Koreluje thread, turn, `clientUserMessageId`, vyžaduje started, právě jeden vstup a completion | Zachovat jako důkaz doručení; pouhý finální text nestačí |
| Phase | Vrací poslední agent message bez rozlišení phase | Kontraktní test reprodukuje doručenou odpověď obsahující pozdější commentary |
| RPC chyba | Vyhodí `AppServerContractError` bez code/data | Nelze přesně rozlišit neplatné parametry, přetížení a další příčiny |
| Chyba tahu | Neúspěšný stav skončí obecnou chybou doručení; strukturované detaily nevrací | Oddělit chybu od důkazu opakování; retry hint není oprávnění |
| Unix transport | WebSocket přes soukromý Unix socket, 64 MiB limit rámce | Zachovat existující proces a socket; `close` klienta zavírá spojení |
| Přerušení | Výjimka při rozbitém transportu, při tichém EOF může čekat do timeoutu | Bez completion se odpověď nesmí vydávat za doručenou |
| `CanonicalSessionHub` | Trvalé pending před odesláním, po chybě `delivery_unknown`, blokace opakování stejného ID, obnova po restartu | SDK nesmí tuto vrstvu obejít |
| Recovery | Jen jeden přesný lokální rollout, thread/client ID, stejný final_answer a task_complete, žádný konflikt | Neopakovat původní akci; nejprve dohledat její důkaz |
| `LocalAppServerProcessController` | Sdílený socket, evidence vlastnictví procesu, řízená obnova jen pro doloženého vlastníka | Pilot ho nevolá; změny procesu ani socketu nejsou součást etapy |

Zachování vstupní položky při jejím vynechání z finální události je již řešeno
v klientu a zůstává požadavkem. Finální vstupní položka, pokud přítomna je,
má přednost; neshodné client ID musí nadále selhat uzavřeně.

## Matice SDK 0.163.0

| Vlastnost | Podpora | Co je skutečně doloženo / co chybí |
| --- | --- | --- |
| Obnova téhož vlákna | Ano | `thread_resume`, kontrola vráceného ID; jiné ID pilot odmítá bez startu nového vlákna |
| Obnova bez historie | Ano | `include_turns=False` se serializuje jako **`excludeTurns: true`**, nikoli `includeTurns: false`; kontext modelu se tím nemaže |
| Historie po stránkách | Částečně | CLI obou verzí má `thread/turns/list`, `thread/items/list`; přes nízkoúrovňový `request` SDK ověřeny dvě stránky; bez pohodlných veřejných metod |
| Ochrana stránkování | Pilot | Limit stránek, opaque cursor, detekce cyklu, žádný fallback na full-history read; `itemsView: notLoaded` |
| Sdílený Unix socket | Pouze kandidát | SDK spouští stdio dítě; konfigurace `codex app-server proxy --sock <explicitní socket>` doložena CLI help a mockem. Živá interoperabilita, vlastnictví a přežití serveru při zavření proxy **neověřeny** |
| Oprávnění | Vyžaduje adaptér | Explicitní `Sandbox.read_only`, `ApprovalMode.deny_all` -> `read-only`/`never`. Veřejný start defaultuje na auto_review; low-level default handler přijímá command/file approval. Není to oprávnění Samanthy |
| Role modelů | Jen průchod parametrů | SDK nezná registr rolí Samanthy. Synteticky ověřen přenos modelu/effort ze současné schválené role, bez změny JSON či skutečné inference. Způsobilost modelu/účtu neověřena |
| Provider při resume | Parametr existuje | Předat uloženého providera; CLI >=0.166 vyžaduje původního. Žádný automatický provider/model fallback ani fork při chybě |
| Commentary/final_answer | Ano | Pozdější commentary nepřepíše explicitní final_answer; phase-less je legacy fallback; commentary-only nemá final_response |
| Události | Ano, s omezeními | Typované raw události; neznámý/nesprávný payload zůstává `UnknownNotification.params`. `run()` ho nevyužije: při chybějícím completedAtMs synteticky ztratí výstup i když terminal turn obsahuje text |
| RPC strukturovaná chyba | Ano | `JsonRpcError.code`, `.data`, bez automatického opakování při běžném requestu |
| Strukturovaná chyba tahu | Jen stream | Raw `TurnCompletedNotification.turn.error` zachová detaily; vysoká `run()` cesta při failed vyhodí obecný RuntimeError a strukturu zahodí |
| Přerušení tahu | Stav dostupný | `interrupted` se nesmí označit za úspěch, ani pokud obsahuje text |
| Výpadek spojení | Částečně | EOF před ack, po ack a po finálním textu bez completion -> TransportClosedError. Zkoušeno jedno odeslání, další volání blokováno |
| Tiché zamrznutí spojení | Chybí přejímka | Low-level request čeká na frontu bez veřejného deadline; před adopcí nutný dohled bez automatického resendu |
| Trvalé exactly-once účtenky | Ne | SDK není session hub. Vlastní client ID lze poslat přes low-level turn params; veřejné Thread.run/turn ho nenabízí |
| JSON Schema výstup | Průchod ano | OutputSchema beze změny na drátu; SDK vrací text a lokálně jej nevaliduje. Inkompatibilní syntetický JSON pilotní test odhalí jako povinnost volajícího |
| Změna runtime | Riziko při výchozím použití | `Codex()` bez konfigurace spustí přibalený runtime, ne existující sdílený proces |
| Úklid SDK spojení | Drobné omezení | SDK close ukončí dítě, ale stdout/stderr zůstávají otevřené; syntetický context manager je zavře. Produkční knihovna neupravována |

## Pilotní soubory

- `app/codex_sdk_pilot.py`: výhradně offline demonstrace, návrh proxy konfigurace
  bez spuštění, referenční kontrakt doručení, omezené stránkování.
- `scripts/codex_sdk_synthetic_peer.py`: deterministický stdio protějšek,
  pouze standardní knihovna, žádné sockety, účty, zdrojová data či modely.
- `tests/test_codex_sdk_pilot.py`: charakterizace stávajícího klienta,
  referenční kontrakt, skutečný SDK transport/parser a CLI schémata.
- Tento report, snapshot prostředí a samostatný handoff pro Willa.

`attempt_once` v pilotu je pouze sekvenční in-memory demonstrace. Neřeší zámky,
restart, persistenci ani souběžné klienty. Nemá se zapojit do produktu místo
`CanonicalSessionHub`. Soukromé rollouty ani sdílené provozní registry se nečetly.

## Ověření a reprodukce

Nové kontrakty: **38 testů PASS**. Celý cílený běh: **79 testů PASS**, bez skipů:
nový modul a existující `test_codex_appserver`, `test_local_appserver_runtime`,
`test_communication_session_hub`, `test_codex_delivery_recovery`.
Syntetické zprávy validovány proti schématu globální CLI 0.166.0; stránkovací
požadavky také proti schématu přibalené 0.163.0. Nejde o všechny RPC metody.
Rychlá statická brána `cockpit_quality_gate.py --skip-unit-tests` PASS,
kompilace všech tří nových Python souborů PASS, whitespace PASS, `pip check`
izolovaného prostředí PASS. Samostatný pilot vrátil completed a `{"ok":true}`,
počet placených modelových tahů 0. Celá produkční testovací brána ani fyzická
Mac/iPhone přejímka se v této izolované etapě neprováděly.

Příklad v novém worktree s vlastním prostředím (nepoužívat společnou .venv):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install openai-codex==0.163.0 websockets==16.0 jsonschema
codex app-server generate-json-schema --out .venv/p1-cli-schema
.venv/lib/python3.11/site-packages/codex_cli_bin/bin/codex app-server generate-json-schema --out .venv/p1-sdk-cli-schema
.venv/bin/python -m app.codex_sdk_pilot
.venv/bin/python -m unittest tests.test_codex_sdk_pilot -v
```

Cesta přibaleného executable se může lišit podle Pythonu/platformy. Další
závislosti pro existující regresní moduly jsou zachyceny ve snapshotu prostředí;
jejich instalace neznamená změnu projektových requirements. Chybí-li SDK nebo
vygenerovaná schémata, příslušné testy se výslovně přeskočí, což není plná přejímka.
V této etapě bylo prostředí kompletní a uvedených 79 testů nepřeskočilo nic.

## Přesný návrh následujícího integračního kroku

1. Will nejdříve přečte tento report a diff vlastního pilotního commitu. Po
   samostatném rozhodnutí otevřít úzký krok **05/P1-B: modernizace původního
   adaptéru**, bez SDK závislosti. Sjednotit aktuální baseline s jeho e-mailovým
   proudem; žádná automatická integrace této větve do main.
2. Rozsah příští změny: `app/codex_appserver.py` a jeho testy. `resume_thread`
   posílá `excludeTurns=True` při doložené kompatibilitě serveru, minimálně
   kontraktově ověřené 0.163/0.166; starší server vyžaduje rozhodnutí, ne tichý
   retry. Zachovat kontrolu ID a nezavádět fork nebo nové vlákno jako fallback.
3. Upravit výběr odpovědi: explicitní final_answer před commentary/partial;
   legacy phase-less jen jako dokumentovaná kompatibilita. Zachovat started,
   přesně korelovaný user item a completed. Přidat code/data a strukturovanou
   turn error do chyb bez vyzrazení soukromého textu v logu. Nevolat retry helper
   nad mutujícím požadavkem a neměnit session hubovou persistenci.
4. Historii načítat po vyžádání přes bounded stránky, jen pokud je skutečný
   konzument; běžný resume ji nepotřebuje. Přenést kontrakty jako požadavky na
   produkční klient místo trvalých assertions dokumentujících jeho dnešní chyby.
5. Přejímka integračního kroku: cílené kontrakty včetně výpadků, restartu a
   client ID; povinná odpovídající brána; kanonický handoff/TVBCP daného proudu.
   Žádný push/deploy/restart bez dalšího oprávnění. Teprve zvlášť autorizovaný
   testovací runtime může ověřit proxy: dvě spojení, stejné vlákno, odpojení
   klienta, server stále živý, žádný nový listener ani změna vlastníka socketu.

Celková adopce SDK má smysl znovu posoudit až po této přejímce a prokázání úspory
kódu. Nynější pilot se do Cockpitu, runtime ani Willova e-mailového agenta nezapojuje.

## Paměť a předání

Tento nový report je projektový zápis izolované etapy. Nový handoff pro Willa
je `data_05_appserver_sdk_pilot_20261104.md`. Existující kanonický Human–Adam
handoff, TVBCP a registry zůstaly podle omezení na nové pilotní soubory beze změn;
jejich writeback bude součástí případného schváleného integračního kroku.
Nový TVBCP nevznikl. Will nebyl v této relaci dostupný jako adresovatelný agent;
souborové předání je připravené, potvrzení jeho převzetí zatím chybí.

## Primární zdroje ověřené v etapě

- [Oficiální Codex SDK](https://developers.openai.com/codex/sdk/) — stabilní Python
  SDK, přibalený runtime, include_turns a provider při obnově.
- [Oficiální App Server protokol](https://developers.openai.com/codex/app-server/)
  — generovaná schémata, lifecycle, stránkování, phase a strukturované chyby.
- [Oficiální SDK API reference](https://github.com/openai/codex/blob/main/sdk/python/docs/api-reference.md)
  a [FAQ](https://github.com/openai/codex/blob/main/sdk/python/docs/faq.md) — veřejné rozhraní.
- [Publikovaný balíček 0.163.0](https://pypi.org/pypi/openai-codex/0.163.0/json)
  a skutečně instalované zdroje SDK 0.163.0 — rozhodující pro výchozí handler,
  serializaci, výjimky a omezení; dokumentace main se může měnit.
- Místní `codex --version`, `codex app-server proxy --help` a schémata obou
  executable — důkaz lokálního rozhraní, nikoli běžící verze sdílené služby.
