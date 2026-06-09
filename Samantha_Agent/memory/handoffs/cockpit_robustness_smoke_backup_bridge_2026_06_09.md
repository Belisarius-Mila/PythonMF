Nazev: Cockpit robustnost - smoke check, backup status a Adam bridge readiness
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-09

Co se resilo:
- V uspornem rezimu po varovani o nizkem tydennim limitu Codexu byly zvoleny tri male prace pro robustnost systemu.
- Cilem bylo zlepsit rychle overeni Cockpitu, strukturovat stav zaloh v `/api/status` a pridat read-only diagnostiku Adam/Codex bridge.

Co je hotove:
- Pridan `scripts/cockpit_smoke_check.py`: read-only smoke check pro `/`, `/api/status` a `/api/recovery/status`; u `/api/status` overuje i `backup_status` a `voice_bridge`.
- Pridan `scripts/adam_bridge_readiness_report.py`: read-only CLI report markeru, aktivnich Codex TTY, screen stavu a varovani.
- `app.backup.activity_state` ma novy `backup_activity_status()` se strukturovanym stavem `ok/missing/stale/error`, stari zalohy a puvodnim textem.
- `app.cockpit.cockpit_status()` vraci puvodni textovy `backup` kvuli kompatibilite a novy strukturovany `backup_status`.
- Dashboard Cockpitu pouziva `backup_status`, pokud je dostupny, a pada zpet na puvodni textovou klasifikaci.
- Lokální i Tailscale Cockpit byly bezpecne restartovane a smoke check prosel na obou instancich.

Co neni hotove:
- Neni reseno vlastni dorucovani Adam bridge ani approval centrum.
- `screen` podle readiness reportu nebezel; marker miril na zivou Codex relaci `ttys001`, ale stav zustava `warn` kvuli chybejicimu screenu.

Dalsi krok:
- Pri dalsim podezreni na problem Cockpitu spustit `.venv/bin/python scripts/cockpit_smoke_check.py`.
- Pri problemu s Adam bridge spustit `.venv/bin/python scripts/adam_bridge_readiness_report.py` a podle varovani resit marker/screen.

Navrhovane dalsi kroky:
- Okamzite: commitnout a pushnout maly checkpoint robustnosti.
- Volitelne: pozdeji doplnit Cockpit read-only capability registry a approval centrum, ale nedelat to v teto male davce.

Zmenene nebo relevantni soubory:
- `app/backup/activity_state.py`
- `app/cockpit.py`
- `scripts/cockpit_smoke_check.py`
- `scripts/adam_bridge_readiness_report.py`
- `tests/test_backup_activity_state.py`
- `tests/test_cockpit.py`

Bezpecnost / neukladat:
- Handoff neobsahuje tajemstvi, API klice, cele e-maily ani soukroma data.
- Smoke check a bridge readiness report jsou read-only.
