Nazev: Systemovy audit projektu, toolu a vrstev - opakovatelny generator
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
- Mila chtel z rucniho reportu `systemovy_audit_projekty_tooly_vrstvy_2026_06_23.txt` udelat opakovatelny generator.
- Cilem bylo zachovat podobny tvar jako rucni audit: provozni poznamka, rychla doporuceni, priority 1-3, tooly/schopnosti, vrstvy a zaver.

Co je hotove:
- Novy modul `app/project_audit_report.py` generuje git-safe systemovy audit z bezpecnych zdroju.
- Novy CLI wrapper `scripts/samantha_project_audit.py` podporuje:
  - `--mode quick`
  - `--mode full`
  - `--save`
- Samantha ma novy tool `samantha_project_audit(mode="quick", save=False)`.
- Report je registrovany v `app/system_reports.py`, `memory/technical/system_reports.md`, `memory/technical/capability_routing_rules.md` a `memory/technical/workflow_command_registry.md`.
- Capability audit je srovnany: po doplneni `samantha_project_audit` a `quick_notes_action_status` hlasi 81/81 namapovanych toolu a 0 nemapovanych.
- `--save` uz neprepisuje existujici denni report; pokud soubor pro dany den existuje, pouzije casovou priponu.
- Navrh generatoru je ulozen v `memory/technical/system_project_audit_generator_design.md`.

Co neni hotove:
- Generator zatim nema Cockpit tlacitko.
- Generator zatim neaktualizuje automaticky `MEMORY_INDEX.md` po kazdem ulozeni reportu.
- Report je deterministicky a sablonovy; nema nahradit lidsky usudek pri vyberu priority.

Dalsi krok:
- Pri dotazu typu `Udelej aktualni systemovy audit` pouzit:
  `.venv/bin/python scripts/samantha_project_audit.py --mode quick`
- Pri ulozeni aktualniho auditu pouzit:
  `.venv/bin/python scripts/samantha_project_audit.py --mode full --save`

Navrhovane dalsi kroky:
- Okamzite: nechat generator stabilni a pouzivat ho jako read-only orientacni report.
- Pozdeji: pridat Cockpit servisni tlacitko pro quick report.
- Pozdeji: promyslet, zda se ulozene reporty maji automaticky dopisovat do `MEMORY_INDEX.md`, nebo zustat jen v `memory/reports/`.

Zmenene nebo relevantni soubory:
- `app/project_audit_report.py`
- `scripts/samantha_project_audit.py`
- `app/samantha_agent.py`
- `app/system_reports.py`
- `app/capability_audit.py`
- `tests/test_project_audit_report.py`
- `tests/test_system_reports.py`
- `memory/technical/system_project_audit_generator_design.md`
- `memory/technical/system_reports.md`
- `memory/technical/capability_routing_rules.md`
- `memory/technical/workflow_command_registry.md`
- `memory/reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_23.txt`
- `memory/reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_23_180157.txt`

Bezpecnost / neukladat:
- Generator nesmi cist private vault, cela tela e-mailu, soukrome dokumenty, fulltexty clanku, `.env`, tokeny ani app-specific passwords.
- `--save` uklada jen git-safe textovy report do `memory/reports/`.
- Navazujici akce z reportu, ktere meni data, commitují, posilaji zpravy nebo cteji citlivy obsah, musi jit pres samostatne potvrzeni podle existujicich pravidel.
