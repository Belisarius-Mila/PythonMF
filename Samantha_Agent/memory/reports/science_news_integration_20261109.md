# Převzetí Datova ScienceNews — 2026-11-09 21:46 CET

Míla výslovně autorizoval převzetí konkrétního Datova checkpointu a následné předání Terře pro p+n. Zdroj `fb708be93760a064b804dc845e8602fd1378c4df`, hlavní základ `5ea9af407e2c01f89299a0eae0f191685a8e714f`. Kanonický proud `project-knowledge-library`, existující Knihovna handoff/TVBCP aktualizované; nový TVBCP nevzniká.

## Rozsah a integrace

Jediný nový commit proti main, 37 zdrojových souborů. Data worktree byl čistý a zůstává na data/parallel-20261104/fb708be9; nepřepíná se, nic z jeho soukromého/runtime stavu se nemigruje. Šest očekávaných konfliktů: frontend registry, role parser, workflow registry, quality gate, asset snapshoty a souběžná oprava testu recovery role.

Registry zachovávají všechny main moduly/role/workflow/testy a přidávají ScienceNews. Snapshot Cockpitu přepočítaný nad skutečně sjednocenými assety; kontrola není odstraněná. Recovery test ponechaný v silnější main variantě s izolovaným chybějícím bindingem, ověřením všech živých schválených rolí a nezměněných bajtů JSON. Kalendář Splněno/Editovat a společný Archiv zachované.

`config/agent_roles.json` je byte-identický s5ea9af40. ScienceNews role nemá binding, soukromá aktivace/služba se nevytváří, žádný produkční import ani nový placený tah. Před budoucím bindingem je nutná kompatibilita také instalovaného hodinového parseru, ne jen nově nasazeného Cockpitu (LL-070).

## Důkazy

- 161 cílených testů PASS: ScienceNews store/model/HTTP/frontend, kalendář, Archiv, centrální role, recovery a společné asset kontrakty. `logs/science_news_integration_targeted_20261109.log`.
- Izolovaný mobilní headless Edge390×844 nad skutečně sjednoceným DOM/CSS a ScienceNews modulem, se samostatným fixture archivem/frontou: zelená→Knihovna, Uložit/Sledovat/Nezařazovat, překlad bez vyřízení, dvě sledovaná témata, poslední šedá a stav po reload PASS. Žádný model ani produkční import. Screenshot zkontrolovaný. `logs/science_news_integration_browser_receipt_20261109.log`.
- Registry compile/test/workflow ID bez duplicit, všechny původní schválené role platné; centrální bindingy byte-identické.
- Plná integrační brána 3365 testů OK (31 SKIP), 481,501 s unit testů: `logs/science_news_integration_full_gate_20261109.log`.

## Publikace a další kroky

Po lokálním merge checkpointu zarovnat jen čisté, nedivergentní Human–Adam a Knihovna profily. Pak registrované `submit_release(wait=True)` pro project-knowledge-library se stabilním požadavkem, celým schváleným main SHA a centrální volbou release_executor/Terra. Role/model se ručně nemění. Konečná autorita je runtime účtenka v `logs/science_news_integration_release_20261109.log`, nikoli tento předpublikační checkpoint.

Po publikaci živě ověřit UI/API, neimportovat demonstrační karty bez samostatného souhlasu. Fronta může být správně prázdná a ikona šedá. Následuje případný schválený UI import, fyzická Mac/iPhone přejímka, konkrétní placený pilot a role/rozpočet; teprve poté povolená aktivace plánovače. Syntetický test není živá vědecká QA. Omezené zdrojové pokrytí převážně Nature zůstává přiznané; dřívější budget proposal není schválený limit.
