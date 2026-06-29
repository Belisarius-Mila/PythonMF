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
- V nove full-access relaci probehl 2026-06-29 prakticky VoiceBridge audit vcetne iPhone/Mac Cockpitu, textovych mezistavu, browser autoreadu a tokenovych potvrzovacich karet pro e-mailove drafty.
- Mila oznacil Cockpit oddil VoiceBridge za zatim uzavreny a uspokojivy.

Co neni hotove:
- Finalni end-to-end VoiceBridge test v nove full-access relaci je pro aktualni potrebu hotovy.
- Audit Cockpitu zustava rozpracovany jako celek, ale blok VoiceBridge je uzavren a audit se ma na chvili pozastavit.
- Projekt `Guard proti mazani` jeste neni zalozeny/implementovany.

Dalsi krok:
- Nejdrive podle Milova dalsiho pokynu hledat potrebne informace.
- Potom zalozit Guard proti mazani pro full-access rezim.

Navrhovane dalsi kroky:
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
- `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`

Bezpecnost / neukladat:
- Neukladat zadna hesla, tokeny ani soukroma data do memory nebo gitu.
- Full access neznamena mazat bez potvrzeni: pro destruktivni akce stale plati projektova globalni brzda a ma vzniknout samostatny Guard proti mazani.
- Pri gitu dal nepouzivat slepe `git add .`; drzet tematicke commity a `git_safety_check.py`.
