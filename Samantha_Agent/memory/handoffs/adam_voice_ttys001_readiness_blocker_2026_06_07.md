Nazev: Adam Voice Remote Cockpit - ttys001 marker a readiness blocker
Priorita: 1
Stav: ceka na rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-06-07

Co se resilo:
Adam v Cockpitu bezi, iPhone portál ukazuje TTY `ttys001`, ale pri pokusu o predani textoveho pokynu se porad vracela hlaska, ze se nepodarilo overit pripravenost Codex relace.

Co je hotove:
- Marker runtime soubor je srovnany na `ttys001`.
- `normalize_tty()` uz sjednocuje kratky zapis typu `ttys01` na kanonicky tvar.
- Textovy bridge uz neblokuje doruceni jen kvuli neoverene ready fazi.
- Testy pro terminal bridge a Adam service prosly.

Co neni hotove:
- Prakticky end-to-end smoke test z praveho Adamova TTY nebo z iPhone portalu, ktery by potvrdil, ze zprava opravdu dorazi a odpoved se vrati zpet.
- Overeni, proc Cockpit na poslednim pokusu stale hlasi neoverenou pripravenost.

Dalsi krok:
Z praveho Adamova chatu nebo z Cockpitu zkusit jednoduchy read-only dotaz a sledovat, jestli dorazí do `ttys001` a vrati se odpoved.

Navrhovane dalsi kroky:
- Pokud ready check stale blbne, zjednodusit ho na informativni stav a nechat doruceni bez cekaci brzdy.
- Kdyz se potvrdi spravne doruceni, dodelat jen kratky status v UI, aby bylo jasne `Adam cte` / `Adam odpovida`.

Zmenene nebo relevantni soubory:
- `app/adam_service.py`
- `app/speech/terminal_bridge.py`
- `scripts/mark_current_codex_tty.py`
- `tests/test_adam_service.py`
- `tests/test_terminal_bridge.py`
- `data/private/voice_inbox/current_codex_tty.json`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, recovery klice, plne e-maily ani jina citliva data.
- Pokud se bude testovat v realnem chatu, pouzit jen bezpecny read-only dotaz.
