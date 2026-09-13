# Cockpit — měření testovací brány, 13. 9. 2026

Měření dokončeno: 2026-09-13 22:42 CEST. Jeden plný běh na Macu, Python 3.12.0rc3,
nad lokálním základem `f1b41dc5` a právě přidaným měřením. Jde o jeden
orientační vzorek, ne benchmark zrychlení ani odhad výkonu jiného počítače.

## Výsledek

- Plná brána OK: **1649 testů**, žádné chyby, selhání ani přeskočení.
- Samotný běh unittest: **426,384 s**; celý podproces testů **429,7 s**.
- Import/načtení sady **2,773 s**. Součet jednotlivých testů **426,313 s**.
- Zbývající čas běhu **0,071 s** zahrnuje sdílené class/module fixtures a režii runneru.
- 127 modulů s vykonanými testy; součet jejich počtů je přesně 1649.
- Čtyři nejdražší skupiny mají 88 testů (5,3 % počtu), ale **313,32 s / 73,5 % času**.
- `test_cockpit` má 265 testů a stojí 5,48 s; frontendová sada 15 testů a 1,19 s.

| Modul | Testů | Sekundy | Podíl běhu |
| --- | ---: | ---: | ---: |
| `tests.test_simple_main_checkpoint` | 28 | 113.15 | 26.5 % |
| `tests.test_simple_main_deploy` | 17 | 97.49 | 22.9 % |
| `tests.test_human_adam_takeover` | 13 | 61.99 | 14.5 % |
| `tests.test_human_adam_workspace` | 30 | 40.69 | 9.5 % |
| `tests.test_document_vault_tools` | 81 | 19.74 | 4.6 % |
| `tests.test_github_batch` | 5 | 11.33 | 2.7 % |
| `tests.test_main_remote_sync` | 6 | 10.93 | 2.6 % |
| `tests.test_document_transactions` | 6 | 7.65 | 1.8 % |
| `tests.test_reminders_store` | 7 | 6.52 | 1.5 % |
| `tests.test_cockpit` | 265 | 5.48 | 1.3 % |

Nejpomalejší jednotlivé testy:
- `SimpleMainDeploymentTests.test_batch_mode_deploys_local_ahead_main_with_quick_gate`: 13,84 s.
- `SimpleMainDeploymentTests.test_audit_accepts_clean_peer_behind_and_prepare_synchronizes_it`: 13,68 s.
- `SimpleMainCheckpointTests.test_clean_peer_may_wait_behind_main_without_blocking_active_profile`: 11,71 s.

## Co je doložené a co je zatím hypotéza

Čas je soustředěný v integračních testech Git checkpointu, nasazení a
pracovních kopií. Statická kontrola nejpomalejších testů potvrdila, že
používají skutečné dočasné repozitáře, lokální bare origin, kopie a opakované
Git/status/sync operace. `successful_gate`, `passing_gate_runner` a smoke
jsou v těchto případech nahrazené testovacími odpověďmi: nejde o rekurzivní
spouštění dalších úplných sad ani o skutečné nasazování Cockpitu.

Současné měření neurčuje podíl vytvoření testovacího prostředí proti
jednotlivým Git příkazům. Tvrzení, že všech 313 s způsobuje jen příprava
repozitářů, by bylo nepodložené.

## Přesný návrh dalšího zrychlení

První pilot omezit na dva nejpomalejší testy `test_simple_main_deploy`:
1. V testovacím pomocném kódu rozdělit měření na `prepare_clean_main` a vlastní
   audit/prepare/verify; současně sečíst počet a dobu Git procesů bez ukládání
   obsahu příkazových argumentů nebo výstupů.
2. Pokud převažuje opakovaná příprava, porovnat izolované kopie jedné předem
   připravené syntetické výchozí historie se současnou tvorbou od nuly. Každý
   test musí mít vlastní zapisovatelný source/origin/profily a stejné stavy.
   Pokud převažují dotazy během operace, nejprve identifikovat opakované čtení
   stejného stavu; neodstraňovat produkční kontroly změn/identity kvůli testům.
3. Přijmout změnu až po stejných výsledcích testů, nezměněné izolaci a doloženém
   poklesu časů. Zatím nelze poctivě slíbit počet ušetřených sekund.

Tento commit zavádí měření a návrh, nikoli optimalizaci přípravy nebo
paralelní spouštění. Nevyřazuje testy, nezkracuje timeouty a nemění release bránu.

## Kdy bránu opakovat

- Běžný malý přesun: cílené testy a statická brána podle projektových pravidel.
- Změna workflow/persistence či zde samotného runneru: jedna plná brána po změně.
- Registrovaný GitHub batch vždy volá plnou bránu pro svůj přesný auditovaný head.
  Kontroly této operace se nemají obcházet dřívějším volným logem.
- Nasazení v dávkovém režimu používá rychlou bránu (`quick_validation`), takže
  v této cestě není druhá automatická plná sada. Mimo tento režim je plná brána.
- Předchozí 462–486s běhy nejsou přímým srovnáním: liší se sada a provozní podmínky.

## Použití a hranice měření

```sh
.venv/bin/python scripts/cockpit_quality_gate.py --unit-test-timings /tmp/cockpit-test-timings.json
```

Bez přepínače zůstává původní `python -m unittest` se stejným manifestem.
Přepínač je neslučitelný s `--skip-unit-tests`. Měření používá stejný loader,
pořadí a jednu TestSuite; zachovává návratové kódy 0/1/5 včetně prázdné sady.
Časy testů zahrnují jejich setUp/tearDown, sdílené fixtures jsou vykázané
odděleně. JSON obsahuje jen statické názvy testů, počty a časy, žádné výpisy,
tracebacky ani argumenty dokumentů. Standardní chybový log se nemění.

Ověření změny: 18 cílených testů; zachované pořadí/fixtures a pass/fail/error/
skip/expected-failure/unexpected-success; CLI 0/1/5; shodný manifest obou režimů;
odmítnutí měření bez testů a žádné citlivé chybové texty v JSON. Následovala
jedna plná brána 1649/1649. Nová měření jsou v sousedním JSON souboru.
