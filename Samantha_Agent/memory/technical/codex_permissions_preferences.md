# Codex: preference pro povolovani prikazu

## Kontext

Mila chce pri rutinnich ukolech omezit opakovane dotazy na povoleni, hlavne pri praci na webovych aplikacich v repozitari `PythonMF`.

Tento soubor neni technicke oprávneni samo o sobe. Skutecna povoleni uklada a vynucuje Codex CLI / Codex UI. Pamet slouzi jen jako pripominka, jaka povoleni ma Codex navrhovat pri dotazech na potvrzeni.

## Doporuceny start Codexu

Pro ukoly nad vice podslozkami repozitare spoustet Codex z korene:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF
codex
```

Tim se omezi dotazy na zapis mimo `Samantha_Agent`, protoze `docs/`, `ColorsAndNumbers/` a dalsi projektove slozky budou v pracovnim prostoru.

## Low-friction profil od 2026-06-11

Mila chce, aby sandbox nebrzdil bezne cteni, testy a provozni diagnostiku.
Prakticky cil neni vypnout bezpecnost, ale presunout opakovane read-only
dotazy do trvale povolenych prefixu.

Tento profil ma byt navrhovan pro `Always allow` / trvale povoleni:

```text
curl
ps -o pid,ppid,command -ax
ps -o pid,ppid,tty,command -ax
ps -o pid,ppid,stat,lstart,command -ax
lsof -nP -iTCP:8770
scripts/start_cockpit.sh
open http://127.0.0.1:8770
.venv/bin/python -m unittest
.venv/bin/python -m py_compile
.venv/bin/python scripts/cockpit_smoke_check.py
.venv/bin/python scripts/adam_bridge_readiness_report.py
.venv/bin/python scripts/backup_status.py
.venv/bin/python scripts/speak_edge_open.py
git -C /Users/miloslavfalta/Desktop/PythonMF status
git -C /Users/miloslavfalta/Desktop/PythonMF diff
git -C /Users/miloslavfalta/Desktop/PythonMF log
git -C /Users/miloslavfalta/Desktop/PythonMF add
git -C /Users/miloslavfalta/Desktop/PythonMF commit -m
git -C /Users/miloslavfalta/Desktop/PythonMF push origin main
```

Proc:

- `curl` pro lokalni health endpointy Cockpitu, Tailscale Cockpitu a API smoke
  testy.
- `ps` a `lsof` pro read-only diagnostiku procesu, TTY, portu Cockpitu a
  hlasoveho bridge.
- `scripts/start_cockpit.sh`, `open http://127.0.0.1:8770` pro bezny start a
  otevreni Cockpitu.
- `.venv/bin/python -m unittest` a `py_compile` pro testy bez opakovanych
  dotazu.
- `cockpit_smoke_check.py`, `adam_bridge_readiness_report.py` a
  `backup_status.py` pro opakovatelne read-only health reporty.
- `speak_edge_open.py` po zmene 2026-06-11 defaultne pouziva lokalni macOS
  `say`, ne sitove Edge TTS, a proto nema kvuli sandboxu padat na DNS. Realne
  systemove audio ale z Codex sandboxu muze skoncit falesnym uspechem bez zvuku;
  pro skutecne hlasove cteni z Codexu navrhovat spusteni mimo sandbox s prefixem
  `.venv/bin/python scripts/speak_edge_open.py`.
- `git status/diff/log` jsou read-only; `git add/commit/push` zustava cilene
  prefixovane na repozitar `PythonMF`, ne obecne `git add .`.
- Od 2026-06-26 je pro Milu potvrzene pravidlo, ze `git push origin main` smi
  po commitu probehnout bez dalsiho dotazu, pokud predtim projde
  `.venv/bin/python scripts/git_push_guard.py`. Guard musi blokovat jinou vetev,
  necisty strom, spatny upstream, vetve mimo `main`, zakazane private/autosave/env
  cesty v poslednim commitu a jakykoli force/destruktivni push.

Tento soubor sam o sobe nezmeni sandbox. Skutecne rozsireni probiha tim, ze
Codex pri prvnim pouziti navrhne prefix rule a Mila zvoli trvale povoleni.

## Bezpecne rutinni prikazy k navrzeni pro Always allow

Pri vhodne prilezitosti navrhnout trvale povoleni pro:

```text
git -C /Users/miloslavfalta/Desktop/PythonMF add
git -C /Users/miloslavfalta/Desktop/PythonMF commit -m
git -C /Users/miloslavfalta/Desktop/PythonMF push origin main
```

Pouziti:

- `git add`, `git commit`, `git push` pro standardni publikaci hotovych zmen.

## Co automaticky nepovolovat

Nenavrhovat trvale povoleni pro destruktivni nebo prilis siroke prikazy:

```text
rm
git reset
git checkout -- ...
python3
python
```

Mazani souboru, reset historie a podobne kroky ma Mila potvrzovat vzdy rucne.

## Poznamka ke GitHub push

Pokud `git push` selze chybou macOS keychainu typu:

```text
failed to get: -25308
fatal: could not read Username for 'https://github.com': Device not configured
```

nejde o chybejici Codex povoleni, ale o problem s GitHub prihlasenim v lokalnim credential helperu. Prakticky dalsi krok je spustit push z normalniho Terminalu nebo opravit GitHub prihlaseni.

## Codex CLI 0.151.0 – bezpečnostní update 2026-08-30

- Globální npm instalace byla aktualizována z `0.148.0` na `0.151.0` přes
  oficiální balíček `@openai/codex`; `codex --version`, npm registrace balíčku
  a základní `codex --help` smoke po aktualizaci prošly.
- Pro Samanthu jsou podstatné opravy zachování permission profilu při obnově
  relace a po `/cd`, zneplatnění staré Guardian klasifikace po změně oprávnění
  a přesnější vzdálené sandboxování podle skutečného OS, domovského adresáře a
  pravidel cest.
- Nová možnost extension vrstvy kontrolovat nebo nahradit MCP tool result před
  předáním modelu je zatím pouze kandidát budoucí bezpečnostní vrstvy, nikoli
  aktivní schopnost Samanthy.
- Před případnou implementací nejdřív inventarizovat konkrétní pluginy a MCP
  servery Samanthy a provést read-only syntetický pilot bez soukromých dat.
  Samostatně navrhnout pravidla redakce, blokování podezřelého obsahu,
  zachování strukturovaných chyb a fail-closed účtenky. Bez tohoto ověření
  filtr nezapínat a netvrdit, že chrání současný provoz.
- Nově spuštěné Codex CLI relace použijí `0.151.0`; již běžící relace může až
  do ukončení dál používat proces načtený před aktualizací.
