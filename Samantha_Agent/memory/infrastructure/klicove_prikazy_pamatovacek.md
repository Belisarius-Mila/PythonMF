# Mílův pamatováček klíčových příkazů

Datum první verze: 2026-07-18

Toto je kanonický git-safe tahák pro několik příkazů, které Míla potřebuje znát
i bez Adama. Je uložený v infrastrukturní paměti Samanthy a dohledatelný z
`MEMORY_INDEX.md`.

## Adam a zachovaná terminálová relace

| Příkaz nebo klávesy | Stručné vysvětlení |
| --- | --- |
| `cd ~/Desktop/PythonMF/Samantha_Agent` | Přejde do hlavní složky Samanthy. Odtud fungují relativní příkazy níže. |
| `samantha` | Připojí existující hlavní relaci Adam–Codex, nebo ji založí, pokud ještě neexistuje. |
| `source ~/.zshrc` | Znovu načte nastavení shellu, když Terminál příkaz `samantha` nezná. Potom spusť `samantha`. |
| `screen -ls` | Jen vypíše existující `screen` relace. Stav `Attached` znamená, že Adam běží, ale je zobrazený v jiném terminálu. |
| `screen -d -r samantha_codex` | Bez restartu převezme tutéž živou relaci do aktuálního terminálu. Zachová chat, kontext i autosave. |
| `Ctrl+A`, potom `D` | Korektně odpojí aktuální terminál od `screen`; Adam a jeho práce běží dál. |
| `Ctrl+A`, potom `Esc` | Otevře historii výstupu ve `screen`. Samotný `Esc` historii zase zavře. |

## Cockpit

| Příkaz | Stručné vysvětlení |
| --- | --- |
| `scripts/start_cockpit.sh` | Spustí nebo otevře lokální Samantha Cockpit bezpečným projektovým launcherem. |
| `open http://127.0.0.1:8770` | Otevře běžící lokální Cockpit v prohlížeči bez restartu serveru. |
| `.venv/bin/python scripts/cockpit_smoke_check.py` | Provede read-only kontrolu, že hlavní stránky a stavové endpointy Cockpitu odpovídají. |

## Git, záloha a diagnostika

| Příkaz | Stručné vysvětlení |
| --- | --- |
| `git status --short --branch` | Stručně ukáže větev, změněné soubory a vztah k GitHubu. Nic nemění. |
| `git --no-pager log -5 --oneline --decorate` | Ukáže posledních pět commitů bez otevření stránkovacího režimu. Nic nemění. |
| `.venv/bin/python scripts/work_context_guard.py` | Read-only ověří, zda je práce checkpointovaná a zda lze bezpečně přejít k jinému tématu. |
| `.venv/bin/python scripts/backup_status.py` | Jen ukáže datum a stáří poslední úspěšné recovery zálohy; novou zálohu nevytváří. |
| `.venv/bin/python scripts/autosave_status.py` | Read-only ukáže, zda nouzový autosave Codex relace běží a je aktuální. |
| `.venv/bin/python scripts/samantha_health_check.py --mode quick` | Provede krátkou read-only kontrolu základního zdraví Samanthy. |
| `.venv/bin/python scripts/codex_session_report.py --include-current` | Vypíše běžící Codex relace, jejich TTY a role; žádnou relaci neukončí. |

## Co bez Adama raději nepoužívat

| Příkaz | Proč ho nepoužívat samostatně |
| --- | --- |
| `SAMANTHA_RESTART_SCREEN=1 samantha` | Ukončí dosavadní `screen` relaci místo jejího bezpečného převzetí. |
| `screen -S samantha_codex -X quit` | Tvrdě ukončí hlavní zachovanou relaci. |
| `git add .` | Může do checkpointu přidat cizí, dočasné nebo citlivé soubory. |
| `git reset --hard` | Může zahodit necheckpointovanou práci; patří pod globální bezpečnostní brzdu. |
| `git push --force` | Přepisuje vzdálenou historii a bez výslovného bezpečnostního postupu se nesmí používat. |

## Nejkratší záchranná cesta k Adamovi

Když nový Terminál hlásí, že `samantha_codex` je `Attached`, Adam není ztracený.
Použij:

```bash
screen -d -r samantha_codex
```

Když Terminál nezná příkaz `samantha`, použij:

```bash
source ~/.zshrc
samantha
```

Pokud ani potom relaci nevidíš, nic neukončuj a nejdřív spusť read-only přehled:

```bash
.venv/bin/python scripts/codex_session_report.py --include-current
```
