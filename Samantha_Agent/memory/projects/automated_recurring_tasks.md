# Obecna rutina pro automaticke opakujici se ukoly

## Stav

Zalozeno 2026-05-20 jako obecna infrastruktura pro bezpecne automaticke
spousteni opakujicich se ukolu v projektu `Samantha_Agent`.

## Aktualni navazani 2026-07-13

- Dnesni automaticky vytvorene `owl_130726.mp3` bylo na Miluv pokyn nahrazeno
  novou promluvou a cache verze aplikace se zvedla z `20260713a` na
  `20260713b`, aby klienti nestahovali starsi zvuk.
- `--force` u CSV sovího workflow nově skutecne regeneruje i existujici denni
  MP3; bez `--force` zustava idempotentni no-op.
- Navrh male soukrome galerie nejvyse tri fotografii byl odlozen bez
  implementace. Bezpecny navrh je v
  `handoffs/colors_numbers_private_photo_gallery_proposal_2026_07_13.md`.
- Rodinne fotografie nesmi jit do verejneho repozitare ani GitHub Pages;
  doporucena prvni verze je lokalni `IndexedDB` bez synchronizace.

## Aktualni kanonicky stav 2026-05-26

Automaticke opakujici se ukoly maji dve vrstvy:

1. Obecny scheduler skeleton `scripts/daily_3am.py`.
2. Jednorazove ColorsAndNumbers soví TTS tasky rizene datumem v JSON configu.

Stav po realnem behu 2026-05-23:

- prvni skutecny GitHub Actions soví TTS task nakonec uspel;
- commit `c8647de Update ColorsAndNumbers owl audio` pridal
  `ColorsAndNumbers/web_colors_numbers/owl_230526.mp3` a prepnul
  `ColorsAndNumbers/web_colors_numbers/app.js` na `owl_230526.mp3?v=20260523a`;
- puvodni prilis tvrda kontrola `--only-at-hour 3` byla nahrazena casovym oknem
  `--window-start-hour ... --window-hours ...`, protoze GitHub schedule se muze
  opozdit.

Navazujici jednorazovy ukol 2026-05-24 je splneny:

- `config/colors_numbers_owl_current.json` je aktualni jednorazovy config pro
  datum `2026-05-24`;
- vystup `ColorsAndNumbers/web_colors_numbers/owl_240526.mp3` existuje;
- publikovana kopie `docs/colors-numbers/owl_240526.mp3` existuje;
- `ColorsAndNumbers/web_colors_numbers/app.js` a `docs/colors-numbers/app.js`
  miri na `owl_240526.mp3?v=20260524a`;
- kontrola byla provedena 2026-05-26 lokalne ve workspace.

Aktualni dalsi krok:

- Potom rozhodnout, jak automatizovat denni zadavani sovich textu bez rucniho
  prepisovani jednoho JSON configu.

## ColorsAndNumbers soví CSV fronta od 2026-05-28

Stav 2026-05-27:

- ruční jednorázový JSON zůstává jako fallback pro starší testovaný režim;
- nový kanonický zdroj denních promluv je `config/OwlSpeech.csv`;
- čitelný kontrolní náhled je `../ColorsAndNumbers/OwlSpeech.txt`;
- `scripts/daily_3am.py` pro datum z CSV generuje MP3 do:
  - `ColorsAndNumbers/web_colors_numbers/owl_DDMMYY.mp3`,
  - `docs/colors-numbers/owl_DDMMYY.mp3`;
- stejný běh přepíná `app.js` v obou kopiích na nové audio se zdrojem typu
  `owl_280526.mp3?v=20260528a`;
- GitHub Actions workflow je nastavené na denní cron `0 1 * * *`, což v pražském
  letním čase odpovídá 03:00, a Python skript má navíc bezpečnostní okno
  03:00-08:00 Praha;
- workflow commituje jen explicitně povolené soubory `app.js` a `owl_*.mp3`
  v adresářích ColorsAndNumbers a `docs/colors-numbers`.

Ověření:

```bash
.venv/bin/python -m unittest tests/test_daily_3am.py
.venv/bin/python -m py_compile scripts/daily_3am.py
.venv/bin/python scripts/daily_3am.py --run-date 2026-05-28 --dry-run --force
```

Prvni implementace je denni rutina ve 3:00:

- `scripts/daily_3am.py` - hlavni Python vstupni bod,
- `docs/daily_3am.md` - navod pro lokalni macOS a cloud variantu,
- `scripts/install_daily_3am_launchd.sh` - instalace macOS `launchd` jobu,
- `scripts/uninstall_daily_3am_launchd.sh` - odinstalace macOS `launchd` jobu,
- `.github/workflows/samantha-daily-3am.yml` - skutecny GitHub Actions workflow v koreni repozitare,
- `Samantha_Agent/.github/workflows/samantha-daily-3am.yml` - projektova kopie/template,
- `tests/test_daily_3am.py` - testy idempotence, locku a chybovych stavu.

## Bezpecnostni princip

Rutina je zamerne nedestruktivni. Sama zatim negeneruje TTS, necommituje a
nepushuje. Slouzi jako bezpecny scheduler skeleton:

- loguje do `logs/daily_3am.log`,
- pouziva `fcntl` lock v `data/daily_3am/daily_3am.lock`,
- zapisuje denni stav do `data/daily_3am/YYYY-MM-DD.json`,
- druhe spusteni ve stejny den dela no-op,
- vraci jasne navratove kody,
- podporuje `--dry-run`, `--force`, `--only-at-hour` a casove okno
  `--window-start-hour` + `--window-hours`.

Runtime data a logy jsou ignorovane gitem.

## Lokalni macOS varianta

Lokalni varianta pouziva:

- `launchd` pro spusteni v 03:00,
- `pmset repeat wakeorpoweron MTWRFSU 02:55:00` pro pokus o probuzeni/zapnuti.

Dulezite omezeni:

- pokud Mac spi, `pmset` ho muze probudit a `launchd` pak spusti rutinu,
- pokud je Mac uplne vypnuty, lokalni Python kod nebezi,
- `wakeorpoweron` muze na podporovanem Macu pomoct se zapnutim, ale neni to
  spolehliva nahrada za cloud,
- pokud musi rutina bezet nezavisle na lokalnim Macu, preferovat GitHub Actions.

## Cloud smer

Dalsi vyvoj ma prioritu 1 a ma pokracovat smerem GitHub Actions/cloud.

Soucasny GitHub Actions workflow:

- bezi na `workflow_dispatch`,
- pro aktualni jednorazovy soví task 2026-05-24 je napevno nastaveny na
  `17 1 * * *`, tedy 03:17 Praha v letnim case;
- skutecnou praci pri schedule pusti jen v okne 03:00-08:00 Praha
  (`--window-start-hour 3 --window-hours 5`).

## Budouci TTS/git workflow

Pro budoucí automatizaci typu `ColorsAndNumbers` TTS + commit + push plati:

1. Zadani musi byt v pevném souboru, napriklad CSV/JSON fronta.
2. Skript smi zapisovat jen do allowlistu konkretnich cest.
3. Pred commitem musi byt preflight `git status --short`.
4. Commitovat jen explicitne povolene soubory, nikdy `git add .`.
5. Push az po testech a jasne omezene scope.
6. Logovat jen technicke informace, bez tokenu, API klicu nebo citlivych dat.

## ColorsAndNumbers - soví promluva 2026-05-24

Mila chce, aby GitHub Actions 2026-05-24 ve 3:00 Praha jednorazove zpracoval
soví text pro webovou aplikaci `ColorsAndNumbers/web_colors_numbers/`, vygeneroval
MP3 pres TTS a prepnúl aplikaci na nove audio.

Finalni pracovni text pro zpracovani 2026-05-24:

```text
Opět zdravím, krásnou neděli. Prý jste osiřeli a bude asi větší klid, že? Takže klid i na učení angličtiny. Ale běžte i ven. Hlavně Jana, je hodně doma a pak je bledá. A ty brýle jsou super!
```

Implementovano:

- konfigurace textu je v `config/colors_numbers_owl_current.json`,
- `scripts/daily_3am.py` ma jednorazovy datumovy gate pro `2026-05-24`,
- generuje `ColorsAndNumbers/web_colors_numbers/owl_240526.mp3`,
- prepina `ColorsAndNumbers/web_colors_numbers/app.js` na
  `owl_240526.mp3?v=20260524a`,
- GitHub Actions instaluje dependencies, po behu commituje a pushuje jen
  `ColorsAndNumbers/web_colors_numbers/app.js` a
  `ColorsAndNumbers/web_colors_numbers/owl_240526.mp3`.

Domluvene startovni pravidlo do odvolani:

- pri prvnim startu Samanthy v danem dni napsat status k sovimu textu,
- na konci se zeptat presne:
  `Budeme dnes psát text pro sovu? Pokud ano odpověz: OK.`,
- pokud Mila odpovi necim jinym nez `OK`, v danem dni uz se znovu neptat,
  ani po restartu Samanthy.

Implementacni poznamka:

- startovni dotaz je napojen v `app/startup_prompts.py`,
- denni stav je runtime soubor v `data/startup_prompts/` a je mimo git,
- TTS/Git adapter je zatim udelany jako jednorazovy ukol pro datum 2026-05-23,
  ne jako trvala kazdodenni produkcni rutina.

## Overeni

Probehlo:

```bash
.venv/bin/python -m unittest tests/test_daily_3am.py
.venv/bin/python -m py_compile scripts/daily_3am.py
zsh -n scripts/install_daily_3am_launchd.sh
zsh -n scripts/uninstall_daily_3am_launchd.sh
```

Cilena sada prosla. Cela stavajici sada `unittest discover -s tests` mela jedno
starsi selhani mimo tuto zmenu: e-mailovy archivacni test ocekaval fixni datum
`2026-05-19`, zatimco aktualni den v prostredi byl `2026-05-20`.

## Historicke handoffy

- `handoffs/automated_recurring_tasks_cloud_2026_05_20.md` - prvni scheduler
  skeleton, macOS `launchd`, GitHub Actions smer a bezpecnostni pravidla pro
  budouci allowlistovane tasky.
- `handoffs/colors_numbers_owl_tts_startup_prompt_2026_05_22.md` - jednorazovy
  ColorsAndNumbers soví TTS task pro 2026-05-23 a denni startovni dotaz na soví
  text.

## 2026-07-15 – souběh sovího workflow a Human–Adam nasazení

Soví GitHub Actions workflow zůstává zapnuté. Jeho commit je úzce omezený na
allowlist ColorsAndNumbers souborů a push je záměrně obyčejný fast-forward bez
`pull`, rebase nebo retry. Pokud `main` mezitím změnil jiný bezpečný writer,
soví push atomicky selže a příští běh může výstupy znovu vygenerovat.

Human–Adam nasazení po dlouhé testovací bráně znovu načte živý `origin/main`.
Přesný auditovaný checkpoint nejdřív pushne přímo na vzdálený `main` a teprve po
úspěchu posune lokální `main`. Když sova vyhraje závod před kontrolou nebo těsně
po ní, non-fast-forward zablokuje převzetí a lokální `main` i WIP checkpoint
zůstanou zachované. Regresní simulace obou pořadí a celá brána 723 testů prošly.
