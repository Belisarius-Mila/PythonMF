# Interiérový architekt — úvodní audit pro nové vymezení

Datum: 2026-11-25. Rozsah: čtení dokumentace, kódu a soukromé evidence;
sjednocení identity a dokumentace. **Nejde o dokončenou technickou etapu 0**
z výchozí roadmapy ani o důkaz nasazení nebo kvality generování.

## Co existuje

| Oblast | Současná implementace |
|---|---|
| Identita Human–Adam | `app/communication/human_adam_workstream_catalog.py`, stabilní ID `project-neuberk-kacenka` |
| Vazba dokumentů | `app/communication/human_adam_workstream_memory.py`, kanonický handoff a TVBCP podle ID |
| Vstup | Janička → Rodinné projekty → Otevřít Ateliér → `/interior/` |
| HTTP | `app/cockpit_interior.py`, registrované operace v `app/cockpit.py` |
| UI verze 1 | `app/frontend/interior/page.html`, `app.js`, `styles.css` |
| Projekty, místnosti, média, varianty | `app/interior_atelier.py`, `JsonWorkRepository` |
| Rozhovor a generování | `app/interior_ai.py`, Codex App Server, role `interior_architect` v `config/agent_roles.json` |
| Souhrn zadání a názvy | `app/interior_brief.py`, `app/interior_titles.py` |
| Společný půdorys a text měr | `app/interior_room_basis.py`; nejde o geometrický scene model |
| Potvrzované mazání | `app/interior_cleanup.py`; zahrnuje související obrazové snapshoty |

Projekt se 31. 5. 2026 založil pro Neuberk a místnost Kačenka. V listopadu se pod
stejným proudem vyvinula obecná aplikace Ateliér. Červnové podklady se do ní
automaticky neimportovaly. Hlavní větev obsahuje i změny z 24. 11.: metadata
původu obrazů a oddělený čistý obrázek/kreslené pokyny. Starší pracovní kopie
Data má tuto oblast pouze do 11. 11.; pro nový vývoj je nutné vyjít z aktuálního
main a zachovat její nesouvisející EN/MMTX práci.

## Redigovaná inventura

Čtecí audit 25. 11. 2026 doložil dva dosud oddělené zdroje:

- Starší strom místnosti Kačenka obsahuje 72 souborů.
- Současný manifest Ateliéru, schema_version 1, má jeden projekt s jednou
  místností. Obsahuje 7 podkladů, 27 záznamů variant a 15 draftů. Čtyři varianty
  mají vazbu na existující obrazový podklad; počet variant není počet obrazů.
- Všech 21 souborů evidovaných u sedmi podkladů existuje a souhlasí jejich
  SHA-256. Evidence dále obsahuje 36 dokončených AI požadavků; audit nic
  znovu neodesílal ani neobnovoval.

Přesné identity, uživatelské texty, cesty k jednotlivým souborům a jejich
otisky zůstávají mimo Git. Názvy existujících místností ani manifest se
v tomto kroku nepřepisují. Počty jsou datovaný snímek, nikoli trvalý invariant.
Porovnání před/po dokumentačním kroku eviduje soukromý důkaz
`data/private/interior_project_reset_20261125/`.

## Rozdíly proti cíli 2.0

- Současná kresba je obrazové vodítko, nikoli editor ochranných masek ani
  maska skutečně vynucovaná obrazovým poskytovatelem.
- Půdorys a text měr nejsou jednotný geometrický model pro 2D/3D.
- Neexistuje doložená garance zachování perspektivy či polohy otvorů
  v generovaném obrázku. Technický zámek nemůže nahradit samotný prompt.
- Metadata architekta nerozlišují skutečný obrazový engine podle domněnky;
  současný most nedokládá volbu enginu, kvality a složitosti.
- Historie a návrhy mají být převzaté; současný aplikační backend a UI se
  podle Míly navrhnou znovu. Použitelnost nižší infrastruktury ověří audit.

## Co ještě musí obsahovat technická etapa 0

1. Úplnou mapu současných datových vazeb, změn stavu, promptů, snapshotů,
   obnovy nejistého požadavku a vlastností obrazového adaptéru.
2. Baseline relevantních Ateliér/HTTP/frontend/persistence testů podle
   registrované validační politiky a konkrétní reprodukce hlášených problémů.
3. Návrh nových kontraktů a verzí, suchý migrační plán s návratem a návrh UI
   před implementací; žádné automatické doplnění neznámých rozměrů.
4. Ověření potřeby, licencí a výkonu nových závislostí na cílovém hardwaru.
   Návrhy knihoven z balíčku nejsou důkaz kompatibility ani povolení instalace.

Samotné čtení kódu, testy se syntetickými daty ani staré HTTP ověření nejsou
fyzickou přejímkou nového UI na Macu/iPhonu nebo testem skutečného generování.
