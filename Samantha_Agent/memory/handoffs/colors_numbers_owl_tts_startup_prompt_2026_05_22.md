Nazev: ColorsAndNumbers soví TTS a denni startovni dotaz
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-22

Co se resilo:
- Navazali jsme na ideu, ze kazdou noc ve 3:00 se v Gitu spusti bezpecny TTS workflow pro `ColorsAndNumbers/web_colors_numbers/`.
- Cilem je vygenerovat novou soví promluvu v MP3 a nahradit nebo prepnout aktualni audio ve webove aplikaci.
- Mila upresnil, ze tentokrat ma GitHub Actions zpracovat text uz zitra 2026-05-23 ve 3:00 Praha.
- Pracovni text byl opraven gramaticky: `připravovaly`, protoze osloveni je `studentky`.
- Mila chce, aby se Samantha pri prvnim startu v danem dni zeptala, zda budeme psat text pro sovu.

Co je hotove:
- Pracovni text sovy je ulozeny v `memory/projects/automated_recurring_tasks.md`.
- Implementovan je startovni formatter `app/startup_prompts.py`.
- `app/samantha_agent.py` pripojuje startovni soví dotaz do startup kontextu.
- Stav jednou-denne se uklada do `data/startup_prompts/owl_text_prompt.json`.
- `data/startup_prompts/` je v `.gitignore`.
- Doplnene jsou testy `tests/test_startup_prompts.py`.
- Implementovan je jednorazovy task v `scripts/daily_3am.py` pro datum `2026-05-23`.
- Konfigurace textu je v `config/colors_numbers_owl_20260523.json`.
- GitHub Actions workflow instaluje dependencies a po uspesnem behu commituje/pushuje pouze:
  `ColorsAndNumbers/web_colors_numbers/app.js` a
  `ColorsAndNumbers/web_colors_numbers/owl_230526.mp3`.
- Suchy beh pro `2026-05-23` vratil stav `planned`.

Co neni hotove:
- Zmeny musi byt pushnute do GitHubu, jinak se zitrejsi Actions beh nespusti.
- Realny GitHub Actions beh 2026-05-23 ve 3:00 Praha jeste neprobehl.
- Trvala kazdodenni produkcni rutina jeste neni navrzena; aktualni task je jednorazovy.

Dalsi krok:
- Cíleně commitnout a pushnout jen relevantni zmeny pro zítřejší TTS task a startovni dotaz.
- Zitra zkontrolovat GitHub Actions vysledek a aplikaci.

Navrhovane dalsi kroky:
- Po zítřejším testu rozhodnout, jestli z toho udelat obecny opakovatelny workflow.
- Pro trvaly rezim zvazit stabilni `owl_daily.mp3` nebo manifest s cache verzi.

Zmenene nebo relevantni soubory:
- `app/startup_prompts.py`
- `app/samantha_agent.py`
- `config/colors_numbers_owl_20260523.json`
- `scripts/daily_3am.py`
- `.github/workflows/samantha-daily-3am.yml`
- `Samantha_Agent/.github/workflows/samantha-daily-3am.yml`
- `requirements.txt`
- `tests/test_daily_3am.py`
- `tests/test_startup_prompts.py`
- `.gitignore`
- `memory/projects/automated_recurring_tasks.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Neukladat tokeny, API klice ani GitHub tajemstvi do memory nebo gitu.
- Automaticky commit/push pridat az po allowlistu, testech a jasnem rozsahu souboru.
