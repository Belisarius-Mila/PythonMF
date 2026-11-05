# 05/P1 — skutečný reconnect současného App Server klienta

Datum: 2026-11-05 12:50 CET. Autor: Will. Proud: `layer-human-adam-development`.
Výchozí main: `040fea774beebd1f1274fbcc0d997eb7b6badb49`.

## Výsledek

**PASS, 17/17 živých kontrol. Přejímka 05/P1 je uzavřená.** Uživatelské
Mac/iPhone body 1–4 Míla výslovně potvrdil; tento audit dokončil poslední
samostatný technický bod. SDK se neadoptuje a produkční kód se nemění.

## Postup a důkaz

- Cockpit před připojením hlásil `turn_busy=false`, žádný `active_turn`.
  Ve všech šesti globálních kontrolách server načítal jediné vlákno `idle`.
- Klienti A a B jsou skutečné instance `CodexAppServerClient` nad současným
  `UnixSocketAppServerTransport` (`unix_connect`, WebSocket na Unix socketu).
  Auditní obal `_send` propustil jen initialize/initialized, thread/loaded/list,
  thread/read a thread/resume; žádný druhý proces serveru se nespouštěl.
- Tři handshaky (A, B, A po reconnectu) shodně potvrdily **připojený server
  0.163.0**. Jde o `serverInfo.version` / `userAgent`, nikoli místní CLI verzi.
- A i B poslaly `thread/resume` pouze s `threadId` existujícího vlákna a
  `excludeTurns:true`. Po zavření A zůstalo B připojené a `thread/read`
  s `includeTurns:false` vrátilo totožná metadata. Nové spojení A znovu
  potvrdilo totéž ID a nastavení, B po něm stále fungovalo.
- Efektivní model **gpt-6.1-sol**, provider **openai**, cwd, approvalPolicy
  **never**, sandbox (včetně kořenů a síťového oprávnění), reasoning effort
  **high** byly porovnány s posledním uloženým `turn_context`/`session_meta`.
  Všechny tři resume odpovědi mají totožnou projekci dalších nastavení:
  approvalsReviewer, serviceTier, collaborationMode, instructionSources,
  disabledPluginIds. Chybějící volitelná pole jsou porovnávána jako null.
- Instrukce ani konfigurace nebyly při resume předány, proto se nepřepisují
  diagnostickými defaulty. Celý původní rollout včetně instrukcí i celý
  Cockpit session snapshot zůstaly beze změny. Žádné tělo zprávy, instrukce,
  skutečné ID vlákna ani soukromá cwd nejsou součástí tohoto reportu.
- Server PID **5791**, launcher **5789**, otisky identity procesu a inode
  socketu **105313040** byly shodné před/při/po testu, také po zavření všech
  auditních spojení. Server pokračoval původní a nepřerušený.

## Rozsah a limity

Žádný `turn/start`, `thread/start`, fork, replay zprávy, restart, změna rolí,
instalace závislostí, push ani nasazení. Nula placených modelových tahů.
Ověřen je reconnect nečinného vlákna. Výpadek během aktivního tahu a trvalý
recovery journal SDK nejsou tímto výsledkem prokázané. Dosavadní zákaz
automaticky opakovat nejistou zprávu zůstává platný. Datův worktree se neměnil.

## Redigovaná účtenka

- Čas: `2026-11-05T11:50:49.583056+00:00` až
  `2026-11-05T11:50:56.702577+00:00` (12:50:49–12:50:56 CET).
- RPC: initialize 3, initialized 3, thread/loaded/list 6, thread/read 10,
  thread/resume 3; konfigurace override 0.
- Otisk nastavení: `a91858ea24961ed0e2bbaa511f653fb95b52e4df07d357259d96f52d522c3a6e`.
- Otisk celého nezměněného rolloutu: `d772ec628676c17b47f5d8a057ab246e02368a353607f24227adab82179c571b`.
- Podrobná místní účtenka: `logs/codex_p1_reconnect_verified_20261105.log`.
  SHA-256: `59efab5a37cae41349b6c1917f844d988a708e950aca23a43913b062d3c8affc`.

Kanonický handoff i TVBCP, Datovo předání v main, index, aktivní projekt
a LL-101 aktualizované v témže kroku. Nový TVBCP nevznikl.

Kontrakt metadata-only obnovy: [oficiální App Server dokumentace](https://learn.chatgpt.com/docs/app-server#resume-or-fork-an-existing-thread).
Skutečné chování výše dokládá živý server a jeho uložený kontext.
