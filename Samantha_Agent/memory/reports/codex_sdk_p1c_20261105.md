# 05/P1-C — SDK, sdílený socket a životní cyklus proxy

Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Proud: `layer-human-adam-development`. Výchozí commit: `d50fccbd`.

## Uzavření přejímky — 2026-11-05 13:03 CET

**05/P1 přejímka uzavřená.** Míla po uživatelských bodech 1–4 sdělil také
úspěch Willovy technické části (bod 2 dvoubodového návodu, reconnect).
Data neprovedl nový vlastní živý audit ani neobdržel technickou účtenku.
Doporučení se nemění: ponechat současný klient, SDK neadoptovat. Níže je
zachovaný předchozí vývojový report a postup nyní přijaté technické zkoušky.

## Výsledek a doporučení

**Ponechat modernizovaný původní klient. SDK nyní neadoptovat.**
Nový izolovaný pilot prokázal fungování skutečného SDK a skutečného CLI proxy
proti syntetickému proudovému Unix socketu. Současně prokázal nekompatibilitu
téže proxy s WebSocket transportem, který používá současný klient Samanthy.
Cesta k Unix socketu sama nestačí: protokoly nad ní se liší.

Testovací fixture byla jediným nově vytvořeným posluchačem. Žádný App Server,
daemon ani model nebyl spuštěn; žádné připojení k živému sdílenému socketu,
čtení uživatelských vláken, restart služby či změna provozních dat.
Nula placených modelových tahů, žádný push, deploy ani integrace do main.

Mílovo navazující „Funguje to!“ evidujeme jako přijetí bodu 3 předchozího
postupu (návrat na Mac / kontrola jedinečného zobrazení). Body 1–3 jsou
uživatelsky přijaté. Následně Míla potvrdil i bod 4: obnova Safari během
odpovědi na iPhonu zcela OK. **Uživatelské body 1–4 PASS.** Zbývá pouze
skutečný technický reconnect sdíleného App Serveru pro Willa; syntetické testy
C jej nenahrazují. Míla oznámil nasazení C, Data neprovedl nový živý audit.
Původní vývojový rozsah a jeho zákazy výše zachycují práci Data, nikoli
pozdější nasazení oznámené Mílou.

## Ověřené prostředí a zdroje

- Místní CLI `0.166.0`, SDK `openai-codex 0.163.0`; PyPI dne 5. 11. znovu
  potvrzuje stabilní SDK `0.163.0`. Nejde o doporučení měnit globální CLI.
- SDK a testové závislosti pouze v již existující vlastní ignorované `.venv`.
  Žádná nová instalace, změna requirements či konfigurace modelových rolí.
- [Oficiální SDK dokumentace](https://developers.openai.com/codex/sdk/)
  popisuje Python SDK nad JSON-RPC a přibalený připnutý runtime.
- [Zdroj proxy přesně pro CLI 0.166.0](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/stdio-to-uds/src/lib.rs)
  přenáší bajty mezi stdio a UnixStream; nedělá WebSocket handshake ani framing.
  Totéž lokálně odpovídá `codex app-server proxy --help`.
- Implementace současného `UnixSocketAppServerTransport` volá `unix_connect`
  s URI `ws://localhost/rpc`. V tomto kroku nebyla měněna.

## Podporované a chybějící vlastnosti

| Vlastnost | Důkaz / omezení |
| --- | --- |
| SDK + CLI proxy + proudový Unix socket | PASS, skutečný SDK parser i CLI proces, syntetický NDJSON protějšek |
| SDK + CLI proxy + současný WebSocket socket | **NEKOMPATIBILNÍ**: initialize nedojde do RPC handleru; časový limit ukončí pouze proxy. Kontrolní spojení současným transportem ke stejné fixture PASS |
| Dva klienti a společná identita vlákna | PASS: dvě samostatné proxy, souběžné resume stejného ID, sdílený syntetický stav viditelný druhým klientem |
| Uzavření klienta / nové připojení | PASS: proxy zanikne, inode socketu i posluchač přežijí; druhý klient a výslovně připojený třetí fungují; žádný thread/start, fork ani replay |
| Zavření během rozpracovaného tahu | PASS: žádný turn/interrupt ani druhý turn/start, klientský stav delivery_unknown. Skutečné dokončení práce serverem po odpojení není prokázáno |
| Obnova bez historie | PASS: excludeTurns:true, stejné ID, cwd, model, provider, instrukce, sandbox a approvalPolicy na drátě |
| Oprávnění | PASS v pilotu: never + read-only, command/file approval výslovně decline. Neznámá žádost zastaví reader bez schválení. Výchozí SDK handler přijímá známá schválení, nesmí se převzít |
| Modelové role | Beze změn; test přenáší syntetický model/provider/effort/instrukce. Nejde o aktivaci role ani ověření entitlementu |
| Události a finále | PASS: started, clientUserMessageId, jediný user item, final_answer před pozdějším commentary, completed; neznámá událost zachová raw payload |
| Strukturovaný výstup | PASS přenos outputSchema a syntetického JSON; skutečné dodržení schématu modelem nebylo testováno, SDK samo JSON proti schématu nevaliduje |
| Strukturované chyby | PASS: RPC code/data, retryAfterMs i error.willRetry zůstanou zachované; žádný z nich nevyvolá nový turn/start |
| Výpadek před/po ack, mlčící peer | PASS: deadline nebo nedokončený přepis zůstane delivery_unknown; druhý pokus se stejným ID blokován i souběžně; sdílený fixture posluchač není ukončen |
| Nativní Unix WebSocket SDK transport | Chybí; CLI proxy jej nedoplňuje |
| Trvalý journal / obnova po restartu klienta | Chybí v SDK i novém pilotu; vlastníkem musí zůstat CanonicalSessionHub. Procesový guard pilotu není persistence |
| Veřejné SDK timeouty a kompletní high-level kontrakt | Ve zkoušené verzi chybí deadline synchronního requestu, high-level caller client ID a zachování strukturované chyby v run(); část vyžaduje low-level API a vlastní adaptér |
| Živý sdílený runtime a fyzická přejímka výpadku | NEOVĚŘENO, nepovažovat syntetické PASS za produkční akceptaci |

## Nové soubory a ověření

- `app/codex_sdk_socket_pilot.py`: pouze fixture proxy, odmítací approval handler,
  konečné čekání a lokální rezervace ID bez retry; oddělené čekání na důkaz doručení.
- `scripts/codex_sdk_socket_fixture.py`: testový NDJSON/WebSocket socket,
  syntetické události a deterministické poruchy. Žádné produkční importy.
- `tests/test_codex_sdk_socket_pilot.py`: **12 nových testů**, včetně dalších
  podscénářů pro přerušení před/po ack, mlčení a retry hint.
- Tento report a `codex_sdk_p1c_20261105_environment.json` s kontrolními otisky.
- Aktualizované zápisy: `data_05_appserver_sdk_pilot_20261104.md`,
  `human_adam_layer_workstream_start_2026_07_20.md`,
  `architektura_komunikace_samantha.txt`, `MEMORY_INDEX.md`, `ACTIVE_PROJECTS.md`,
  `human_adam_iphone_send_failure_20261105.md`, `LESSONS_LEARNED.md` (LL-095).
  Celkem 12 změněných/přidaných souborů; dosavadní produkční soubory beze změn.

**105 cílených testů PASS, 0 skipů**: nový C pilot, původní SDK pilot, App Server
klient, session hub a shared-thread probe. Běh s ResourceWarning jako chybou.
Rychlá statická Cockpit brána PASS, pip check PASS. Plná produkční brána se
kvůli samostatnému pilotu bez změn produkce neopakovala; dřívějších 2 374 testů
a 5 PDF skipů z UI opravy se tím nevydává za nový výsledek C.

Reprodukce pouze ve vlastním prostředí:

```sh
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python -W error::ResourceWarning -m unittest tests.test_codex_sdk_socket_pilot tests.test_codex_sdk_pilot tests.test_codex_appserver tests.test_communication_session_hub tests.test_codex_appserver_shared_thread_probe -v
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python scripts/cockpit_quality_gate.py --skip-unit-tests
```

Sockety mají krátkou cestu ve vlastním testovém TemporaryDirectory pod `/tmp`
(limit sun_path na macOS), adresář 0700 a socket 0600. Nejde o změnu TMPDIR,
služby ani sdílené konfigurace. Kontexty po sobě ukončí proxy a testové fixture.
Pilot používá privátní `_proc` jen k uzavření rour zkoušeného SDK; není vhodný
jako produkční adaptér a nezaručuje globální serializaci různých operací.

## Přesný další integrační krok pro Willa

1. C je podle Míly nasazené. Do kanonického stavu main převzít také tento
   následný zápis úspěšné fyzické přejímky; při konfliktu paměti zachovat
   novější stav main. **Produkční klient, controller, session hub, role
   a závislosti se tím nemění.**
2. Bod 4 je po Mílově fyzickém testu přijatý. Technický reconnect provést
   jako samostatně autorizovanou read-only zkoušku současného transportu:
   dvě nová klientská spojení k existujícímu socketu, initialize a metadata
   verze, resume původního vlákna s excludeTurns, kontrola ID a stejných
   oprávnění/modelu/cwd, zavření jen prvního spojení a následné čtení druhým.
   Bez restartu serveru, zakládání vlákna, turn/start či opakování staré zprávy.
3. SDK migraci znovu otevřít až při konkrétním přínosu a samostatném rozhodnutí.
   Musela by dodat skutečný WebSocket adaptér nebo schválenou změnu transportu,
   veřejné deadline, explicitní approvals a napojení na trvalý journal. Pouhá
   náhrada executable za CLI proxy pro současnou Samanthu nefunguje.

Míla oznámil nasazení C; přesný nasazený head ani přímé převzetí Willem
Data novým auditem neověřoval. Následný zápis fyzické přejímky je připravený
k souborovému předání z větve Data. Přímý Willův agent zde není k dispozici.
Data po lokálním commitu čeká; další živé testy ani publikování neprovádí.
