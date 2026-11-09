# ScienceNews p+n — přerušení a ochrana automatického restartu

Stav 2026-11-09 22:09 CET. Integrace Datova fb708be9 do main je dokončená v 1395956d. Původní předání Terře není potvrzené vydání. Nový placený pokus nebyl spuštěn.

## Doložená časová osa

- bd828212650df86ee5737f30a0d7a752 vytvořeno 21:54:11 CET, release_executor=gpt-6.1-terra/high, přijato přesně 1395956d a dva commity. Jedno modelové předání má účtenku; příprava plné publikační brány začala v pracovním prostoru Knihovny.
- Ve 22:00:13 CET job přešel do attention, failure_phase=push_requested, push_state=uncertain, deployment_state=not_started. Program neukládá raw exception kvůli soukromí; konkrétní síťový exception text není doložený.
- Hotkey launcher log z 22:00:26 obsahuje explicitní detekci staršího kódu a ukončení Cockpit PID 48189. Supervisor spustil nový PID 64718 ve 22:00:20. Původní publikační quality gate/testy pokračovaly s PPID1 a potom skončily; původní serverový publish frame se už nemůže dokončit.
- Ověřený vzdálený main zůstal 5ea9af40. Živý HTML se již shoduje s lokálním1395956d, code_stamp=ed4f6c6343fe3d3f. ScienceNews API je ok, pending_count=0, initialized=false, activated=false. To je automatické načtení lokálního kódu, nikoli potvrzený registrovaný deploy/push.

Log: `logs/science_news_release_reconciliation_20261109.log`; původní neredigovaná interní účtenka zůstává v soukromém store, veřejná v `logs/science_news_integration_release_20261109.log`. Žádný token ani soukromý obsah zde není.

## Lokální oprava

`open_cockpit.py` před automatickým restartem ověří `/api/human-adam/luna-release/status`. Aktivní p+n dovolí otevřít starší existující ověřený server bez restartu. Timeout, neplatná odpověď nebo neověřený stav restart blokují. Známý neaktivní stav zachovává dosavadní ověřený restart; odpovídající aktuální server žádný probe nepotřebuje. Autorizovaný restart samotného publisheru nebyl změněný.

77 cílených testů PASS; nový test přímo ověřuje, že active/unknown nedojdou k restart callu. Testy neukončovaly reálný server ani jiné procesy. Plná brána opravy PASS: 3370 testů / 31 SKIP (546,298 s), log v `logs/science_news_launcher_guard_full_gate_20261109.log`; původní integrace měla 3365 OK/31 SKIP a mobilní fixture PASS.

## Předání

Plná brána opravy je dokončená; navazuje lokální checkpoint, zarovnání čistých profilů a závěrečné ověření GitHubu i původní attention účtenky. Žádný nový push ani nasazení tímto checkpointem nevznikají. Původní job se nepřepisuje a nezakládá se automaticky druhý. AGENTS.md: „Při timeoutu či nejistotě ověř stejnou účtenku; nic automaticky neopakuj.“ Proto nový placený Terra p+n až po novém výslovném pokynu Míly pro konkrétní dokončený balíček. ScienceNews model, rozpočet, plánovač a provozní import zůstávají bez aktivace.
