# Oprava chyby Zadání úkolu před odesláním

Stav 2026-11-08 12:28 CET: lokální oprava, bez nového p+n. Kanonický proud
project-cockpit; handoff/TVBCP a projektová paměť aktualizované.

## Důkaz problému

Míla při odeslání viděl zašedlý formulář a hlášku Zadání se nepodařilo
bezpečně uchovat, Neodesláno, Obnov stránku. Na serveru při prvním auditu
nevzniklo žádné data/private/calendar_tasks zadání/účtenka. Stejný stav
byl reprodukovaný s funkčním localStorage a prohlížečem bez randomUUID:
regrese očekávající create skončila 0 místo 1. Chyba vzniká před POST.
Schéma skutečné Mílovy adresy zatím nebylo potvrzené; shodný catch také
schovával chyby localStorage. Není to důkaz poškozeného kalendáře/TCC.

Původní kód volal crypto.randomUUID bez ověření dostupnosti. Toto API
je omezené na secure context; getRandomValues poskytuje silné náhodné
hodnoty i v HTTP kontextu. Dokumentace primárního browser API:
https://developer.mozilla.org/en-US/docs/Web/API/Crypto/randomUUID
https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues

## Oprava

- Identita přímo ze 16 silných náhodných bajtů getRandomValues, stejný
  32znakový hex formát serveru. Bez Math.random, změny sítě nebo rolí.
- Známá chyba před POST s prázdným úložištěm nezamkne formulář. Text,
  datum a čas zůstávají; další výslovný klik může znovu připravit zadání.
- Úložiště, které se zapsalo, ale nešlo zpětně přečíst, se po ověření
  uchová pod původním ID/payloadem a následuje pouze status/recover.
  Nevzniká automatický druhý create ani přepis neznámého původního zadání.
- Nedostupné/nejednoznačné úložiště blokuje odeslání, ponechá text
  dostupný pro zkopírování. Nepravdivá obecná rada obnovit stránku
  po jakékoli chybě je odstraněná. Při neznámém skutečném zápisu
  zůstává původní ochrana proti úpravě a duplicitě.
- Kalendářový Python/Swift backend, alarmy, cíle a OS granty beze změny.

## Ověření

- Red→green Node regrese HTTP profilu bez randomUUID; pouze getRandomValues.
- HTTPS profil, normální submit, dvojklik, ztracená odpověď, restart,
  read-only status/recover a explicitní stejné ID nadále PASS.
- Zápis úložiště selže před POST: 0 create, editovatelný text; potom
  výslovný další klik a právě 1 create. Částečné uložení: status, stejný
  payload a ID, právě 1 create. Bez silného RNG se nic neodešle.
- 26 cílených testů PASS, plná brána 2923 testů OK (31 SKIP).
- logs/calendar_task_storage_repro_before_20261108.log,
  calendar_task_storage_node_20261108.log, calendar_task_storage_targeted_20261108.log,
  calendar_task_storage_gate_20261108.log a calendar_task_storage_diagnosis_20261108.log.
- Fyzické browser surfaces nebyly dostupné: 0 připojených browser tabs,
  Safari 0 oken. Mílova konkrétní browserová přejímka zůstává otevřená.
- Žádný skutečný event se netvořil. Nasazený základ je 6c610287/
  d7ac821490a17273e18be1de270b9ba8; CI 42474671842 success.

Další krok: samostatně schválit p+n ověřené opravy,
potom Mílův retest. Bez mazání browserového úložiště, textů nebo kalendáře.

Závěrečná statická brána PASS: logs/calendar_task_storage_static_20261108.log.
Přímé porovnání HTTP/source potvrzuje dosud původní živou verzi:
logs/calendar_task_storage_live_vs_source_20261108.log. Tato oprava je pouze
frontendová, Python code_stamp se proto nemění; při p+n ověřit přesnou
shodu nového HTML a odstranění závislosti na window.crypto.randomUUID().
Přesný lokální commit a počet čekajících commitů budou v závěrečném
logs/calendar_task_storage_final_verified_20261108.log.
