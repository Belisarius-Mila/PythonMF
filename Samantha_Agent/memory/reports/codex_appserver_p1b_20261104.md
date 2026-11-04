# 05/P1-B — modernizace původního App Server klienta

Datum: 2026-11-04. Autor: Data. Větev: `data/parallel-20261104`.
Výchozí bod: pilot `607fc538`. Pracovní proud: `layer-human-adam-development`.

## Integrace Willem — 2026-11-05 00:53 CET

Na výslovný Mílův pokyn převzaty originály 607fc538/862b6225 do main jako
1b6fd61e/ccece787. Will zkontroloval produkční diff i oddělení SDK a ověřil
společné kontrakty: 192 testů: 172 PASS a 20 explicitních skipů volitelného SDK prostředí.
Živý upravený klient se připojil k serveru 0.163.0 a načetl katalog; lokální
CLI je 0.166.0. Produkční SDK/runtime architektura ani závislosti se nemění.
Společná plná brána prošla: 2462 testů, 2442 PASS a 20 SDK SKIP (377,0 s), log data_email_integration_gate_20261105.log.
Následuje autorizované registrované p+n; jeho výsledek je autoritativní až
v přesné účtence. Starší vývojový report níže popisuje stav před integrací.

## Výsledek

Původní klient je lokálně upravený, SDK se neadoptuje. Běžný reconnect žádá
metadata vlákna bez historie; úspěšná odpověď upřednostňuje explicitní
`final_answer`; RPC a turn chyby zachovávají strukturu bez jejího přidávání
do běžného textu výjimky. Nejistý výsledek nevyvolává opakování akce.

Změny kódu jsou pouze v `codex_appserver.py`; změny testů v
`test_codex_appserver.py` a `test_codex_sdk_pilot.py`. Session hub, procesový
controller, Cockpit, e-mailové moduly, requirements a role zůstávají beze změn.
Nevznikl žádný nový posluchač, SDK runtime ani připojení k živému socketu.

## Kontrakt kompatibility a obnovy

- `initialize` ověří **připojený server** z `userAgent` nebo `serverInfo.version`.
  Diagnostická `client.version` nadále popisuje lokální executable;
  nová `client.server_version` popisuje metadata připojení. Tyto verze nemusí být shodné.
- Konzervativní minimum je stabilní **0.163.0**, odvozené z ověřených schémat
  0.163/0.166 z první etapy. Není to tvrzení, že pole v dřívější verzi neexistuje.
  Chybějící, starší či prerelease verze selže před jakoukoli operací s vláknem.
- Kontrola probíhá v konstruktoru, nikoli až uvnitř resume: session hub má
  zachovaný fallback pro nedokončeně založená prázdná vlákna. Nesmí za takový
  případ považovat nepodporovanou verzi serveru a založit náhradní vlákno.
- `thread/resume` vždy posílá **`excludeTurns: true`**. Cwd, sandbox, approval,
  instrukce, model a kontrola přesné shody thread ID zůstávají zachované.
- Žádný fallback na plnou historii, fork, změnu modelu/provideru nebo opakovaný
  požadavek po odmítnutí. Nová stránkovací API do produkce nepřibyla: nynější
  klient nemá konzumenta historie; bounded demonstrace zůstává v pilotu.

## Odpověď a důkaz doručení

- Explicitní `final_answer` má přednost před pozdějším commentary, partial
  answer i phase-less textem. Prázdné nebo neplatné explicitní finále nezpůsobí
  návrat ke starému textu. Neznámá phase se nepovažuje za finále.
- Při absenci explicitního finále zachována kompatibilita s poslední neprázdnou
  zprávou bez phase. Commentary/partial-only tah není potvrzen jako doručený.
- Dvě odlišná explicitní finále jsou nejednoznačná. Opakovaná identická položka
  se stejným ID je přijatelná. Koncový snapshot má přednost, pokud obsahuje
  agentní položky; jinak se zachová již přijatý text ze streamu.
- Zachován `turn/started`, právě jeden korelovaný user item, odpovídající thread
  a turn a `turn/completed`. Když koncový snapshot vstup vynechá, předchozí
  korelovaný vstup zůstává důkazem. Pokud jej obsahuje, má přednost; více
  koncových user items včetně cizího client ID nesmí projít jako jediný vstup.
- `failed` a `interrupted` nikdy nevytvoří úspěšnou účtenku. Neplatný koncový
  stav je kontraktní chyba.

## Strukturované chyby a soukromí

- `AppServerRpcError` dědí z `AppServerContractError`: zachová `method`, `code`,
  kopii `data` a `server_message`. `str` i `repr` obsahují pouze bezpečnou
  obecnou zprávu, takže dosavadní volající nepersistují serverový obsah do UI/logu.
- `AppServerTurnError` zachová `status`, kopii `turn_error` a `will_retry=False`.
  Koncová chyba má přednost, chybějící detail může dodat předchozí `error` událost.
- `error.willRetry=True` popisuje práci serveru v témže tahu. Klient čeká na
  koncový důkaz, sám neposílá další `turn/start`. Pokud přijde transportní chyba,
  její původní typ zůstává zachován a nese `turn_error`/`will_retry` pro výslovnou
  diagnostiku. Retry hint nikdy nemění stav doručení na potvrzený.
- Nové atributy jsou určeny k vědomému zpracování, nikoli k hromadnému logování
  `__dict__`. Nemění se formát úspěšných účtenek ani session hubová persistence.

## Ověření

- **100 cílených testů PASS**, bez přeskočení: klient, SDK pilot, session hub,
  delivery recovery a lokální runtime. Zahrnuto 21 nových testů původního klienta.
- Přeneseny původní charakterizační testy pilotu do regresních assertions pro
  nové chování; historický report první etapy dál popisuje tehdejší stav.
- Dva testy propojují skutečného klienta se session hubem nad syntetickým
  transportem a dočasným stavem. Potvrzeno `delivery_unknown` i po restartu,
  jediný `turn/start`, žádný únik syntetické privátní chyby do uloženého stavu
  a žádný fallback na nové vlákno při selhání verze serveru.
- **Úplná Cockpit brána PASS: 2 373 testů, 0 chyb a selhání, 5 přeskočených**
  (531,205 s unit testů). Těchto pět skipů jsou PDF exporty článků bez ReportLabu;
  netýkají se App Server klienta. Python/JavaScript/shell syntax a whitespace PASS.
- První úplný běh měl 2 343 testů, 154 chyb a 4 selhání (5 skipů). Příčinami
  bylo chybné nastavení TMPDIR pod Gitem a chybějící HEIF/FastAPI/Google Auth/
  OpenCV v nové izolované `.venv`, nikoli změna klienta. Pro další běh je použit
  standardní systémový dočasný adresář mimo Git a doplněné knihovny pouze ve
  vlastní `.venv`; FastAPI/HTTPX/Uvicorn podle existujících
  `camino/server/requirements.txt`. Kontrolní sada instalátoru/serveru 42/42 PASS.
- Tato brána obsahuje registrovaný výběr 177 testovacích modulů; není tvrzením
  o spuštění všech testů repozitáře. Pilotní SDK modul je ověřen zvlášť v cílené sadě.
- Logy jsou pouze v ignorované `.venv`: `p1b-targeted.log`, `p1b-full-gate.log`.
  Opravený úplný běh má samostatný `p1b-full-gate-final.log`; žádné projektové
  requirements ani kód Camina se kvůli přípravě tohoto prostředí neměnily.

Izolované ověřovací prostředí používá Python 3.11.5 a následující verze;
nejde o návrh změny produkčních závislostí:

| Balíček | Verze |
| --- | --- |
| openai-codex / přibalená CLI | 0.163.0 |
| openai-agents | 0.17.2 |
| Pillow / pillow-heif | 13.0.0 / 1.8.1 |
| opencv-python-headless / numpy | 5.0.0.93 / 2.4.6 |
| google-auth | 2.62.1 |
| FastAPI / HTTPX / Uvicorn | 0.141.1 / 0.28.1 / 0.53.0 |

## Hranice a další krok

Lokální vývoj ve vlastní větvi. Žádný placený modelový tah, push, nasazení,
integrace do main, restart služby ani změna společné `.venv` či provozních dat.
Testovací procesy a soubory jsou syntetické. Verze již běžící sdílené služby
nebyla v této etapě živě zjišťována; nasazení proto nelze odvodit z testů.

Will může převzít diff obou lokálních kroků a porovnat jej se svým e-mailovým
proudem. `main` během souběžné práce pokročil mimo tuto větev; pracovní kopie
zůstává na vlastním základu, bez merge/rebase či jiné synchronizace. Integrace
do main zůstává samostatným rozhodnutím a musí zohlednit jeho aktuální změny. Po případné
autorizované integraci a nasazení ověřit handshake podporované stabilní verze,
reconnect stejného vlákna, zachování oprávnění a jediný tah bez opakování;
Mac/iPhone a proxy přejímka zůstávají samostatné.

Zapsáno též do kanonického handoffu a TVBCP komunikačního proudu a do
`data_05_appserver_sdk_pilot_20261104.md`. Nový TVBCP nevzniká.

Podklad protokolu: [oficiální App Server dokumentace](https://developers.openai.com/codex/app-server/),
ověřená schémata z etapy A a jejich inventář v
`codex_sdk_pilot_20261104_environment.json`.

## Změněné soubory

- `app/codex_appserver.py`
- `tests/test_codex_appserver.py`
- `tests/test_codex_sdk_pilot.py`
- `memory/reports/codex_appserver_p1b_20261104.md`
- `memory/reports/codex_sdk_pilot_20261104.md`
- `memory/handoffs/data_05_appserver_sdk_pilot_20261104.md`
- `memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`
- `memory/tvbcp/architektura_komunikace_samantha.txt`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/LESSONS_LEARNED.md`
