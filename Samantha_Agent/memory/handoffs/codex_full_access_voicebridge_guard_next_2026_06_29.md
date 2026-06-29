Nazev: Codex full access, VoiceBridge finish, Guard proti mazani
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-29

Co se resilo:
- Mila chce ukoncit opakovane brzdeni prace sandboxem, protoze v osobnim provozu Samanthy prevazila ztrata produktivity nad prinosy sandboxu.
- Konkretni bolest: sandbox blokoval `ps`, PID kontrolu, lokalni HTTP diagnostiku a dalsi provozni veci, coz komplikovalo VoiceBridge a Cockpit audit.
- Dohodli jsme se, ze nejsme firma ani kriticka infrastruktura; hlavni realne riziko je omylem smazat vetsi cast projektu, ne uniky dat nebo striktni compliance.

Co je hotove:
- V uzivatelske konfiguraci mimo git je nastaveno:
  - soubor: `/Users/miloslavfalta/.codex/config.toml`
  - `sandbox_mode = "danger-full-access"`
  - `approval_policy = "never"`
- Tato zmena neni v gitu, protoze jde o lokalni osobni konfiguraci Codexu.
- Aktualni bezici relace pravdepodobne stale pouziva puvodni sandbox rezim; zmena se ma projevit az v nove Codex/Samantha relaci.
- Pred touto zmenou byla pushnuta oprava VoiceBridge statusu pro dlouho bezici `screen` relace:
  - commit `1c073ba Fix VoiceBridge status for long-running screen sessions`
  - Cockpit po restartu hlasil: Mac TTY bridge pripraveny, cil `ttys000`, Codex relace 1, screen bezi.

Co neni hotove:
- Neni hotovy finalni end-to-end VoiceBridge test v nove full-access relaci.
- Audit Cockpitu zustava rozpracovany, ale ma byt na chvili pozastaven po dokonceni VoiceBridge.
- Projekt `Guard proti mazani` jeste neni zalozeny/implementovany.

Dalsi krok:
- Spustit novou Codex/Samantha relaci, aby nacetla `danger-full-access`.
- V nove relaci overit bez sandboxu:
  - `.venv/bin/python scripts/adam_bridge_readiness_report.py`
  - Cockpit `voice_bridge` stav
  - kratky realny hlasovy/textovy pokyn Cockpit -> Codex -> odpoved zpet do Cockpitu.

Navrhovane dalsi kroky:
- Po uspesnem VoiceBridge testu docasne prerusit Cockpit audit.
- Zalozit projekt `Guard proti mazani`:
  - blokovat nebo vyzadovat presnou potvrzovaci vetu pro `rm -rf` na projektove koreny;
  - hlidat mazani vetsiho adresare nebo podezrele mnozstvi souboru;
  - hlidat `git clean`, `git reset --hard`, force push, hromadne presuny a Pythonove `shutil.rmtree`;
  - zachovat beznou plynulou praci, testy, git status, commit/push a diagnostiku bez sandboxovych zdrzeni.
- Po Guardu se vratit k Cockpit auditu podle `handoffs/cockpit_audit_live_2026_06_28.md`.

Zmenene nebo relevantni soubory:
- `/Users/miloslavfalta/.codex/config.toml` (mimo git)
- `handoffs/cockpit_audit_live_2026_06_28.md`
- `app/cockpit.py`
- `scripts/adam_bridge_readiness_report.py`
- `tests/test_cockpit.py`
- budoucí projekt: Guard proti mazani

Bezpecnost / neukladat:
- Neukladat zadna hesla, tokeny ani soukroma data do memory nebo gitu.
- Full access neznamena mazat bez potvrzeni: pro destruktivni akce stale plati projektova globalni brzda a ma vzniknout samostatny Guard proti mazani.
- Pri gitu dal nepouzivat slepe `git add .`; drzet tematicke commity a `git_safety_check.py`.
