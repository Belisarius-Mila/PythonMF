Nazev: Obecna rutina pro automaticke opakujici se ukoly - smer GitHub Actions/cloud
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Mila chtel obecnou denni rutinu pro automaticke spousteni opakujicich se ukolu.
- Konkretni motiv byl nocni workflow typu TTS MP3 + git push pro aplikaci `ColorsAndNumbers`, ale bylo upresneno, ze lokalni Mac muze byt vypnuty.
- Vysledek je obecna bezpecna rutina v `Samantha_Agent`, ktera umi bezet lokalne pres macOS `launchd` i v cloudu pres GitHub Actions.

Co je hotove:
- Vznikl `scripts/daily_3am.py` jako hlavni vstupni bod.
- Rutina loguje do `logs/daily_3am.log`.
- Runtime stav a lock jsou v `data/daily_3am/`.
- Rutina je idempotentni: jeden den zapisuje stav a dalsi spusteni dela no-op.
- Soubeh je blokovany pres `fcntl` lock.
- Jsou definovane navratove kody:
  - `0` hotovo/no-op,
  - `10` uz bezi,
  - `20` setup/runtime chyba,
  - `30` chyba tasku,
  - `40` neplatne argumenty.
- Existuje `docs/daily_3am.md` s vysvetlenim spanku, probuzeni a uplneho vypnuti Macu.
- Existuji instalacni a odinstalacni skripty pro macOS `launchd`:
  - `scripts/install_daily_3am_launchd.sh`,
  - `scripts/uninstall_daily_3am_launchd.sh`.
- GitHub Actions workflow je pripraveny v:
  - `.github/workflows/samantha-daily-3am.yml` v koreni repozitare,
  - `Samantha_Agent/.github/workflows/samantha-daily-3am.yml` jako projektovy template.
- Testy jsou v `tests/test_daily_3am.py`.

Co neni hotove:
- Neni jeste pridany konkretni TTS task pro `ColorsAndNumbers`.
- Neni jeste implementovany git commit/push task adapter.
- Cloud beh po pushi neni jeste realne overeny v GitHub Actions.
- Neni jeste rozhodnuto, jaky prvni skutecny cloudovy ukol se ma automatizovat.

Dalsi krok:
- Pokracovat prioritne smerem GitHub Actions/cloud.
- Po pushi overit, ze workflow `Samantha Daily 3 AM` v GitHubu existuje a da se rucne spustit pres `workflow_dispatch`.
- Potom navrhnout prvni realny task adapter jako samostatny, testovany a allowlistovany krok.
- Pro `ColorsAndNumbers` pripadne nejdriv navrhnout CSV/JSON frontu TTS zadani a preflight `git status`, bez automatickeho `git add .`.

Zmenene nebo relevantni soubory:
- `.github/workflows/samantha-daily-3am.yml`
- `Samantha_Agent/.github/workflows/samantha-daily-3am.yml`
- `Samantha_Agent/.gitignore`
- `Samantha_Agent/README.md`
- `Samantha_Agent/docs/daily_3am.md`
- `Samantha_Agent/logs/.gitkeep`
- `Samantha_Agent/scripts/daily_3am.py`
- `Samantha_Agent/scripts/install_daily_3am_launchd.sh`
- `Samantha_Agent/scripts/uninstall_daily_3am_launchd.sh`
- `Samantha_Agent/tests/test_daily_3am.py`
- `Samantha_Agent/memory/projects/automated_recurring_tasks.md`

Bezpecnost / neukladat:
- Do memory ani gitu neukladat tokeny, API klice, hesla ani tajemstvi GitHubu.
- Necommitovat runtime stav `data/daily_3am/` ani logy `logs/*.log`.
- Nepouzivat `git add .`.
- Nepribirat nesouvisejici rozpracovane soubory z `VocabularyIT`, `PictNew` ani Lekarna skript.
- Automaticky git push pro budouci tasky pridat az po allowlistu, testech a jasnem rozsahu souboru.
