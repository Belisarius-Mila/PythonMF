# Obecna rutina pro automaticke opakujici se ukoly

## Stav

Zalozeno 2026-05-20 jako obecna infrastruktura pro bezpecne automaticke
spousteni opakujicich se ukolu v projektu `Samantha_Agent`.

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
- podporuje `--dry-run`, `--force` a `--only-at-hour`.

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
- ma dva UTC crony kvuli letnimu/zimnimu casu v Praze:
  - `0 1 * * *`,
  - `0 2 * * *`,
- skutecnou praci pri schedule pusti jen tehdy, kdyz `scripts/daily_3am.py`
  vidi v `Europe/Prague` hodinu 3 (`--only-at-hour 3`).

## Budouci TTS/git workflow

Pro budoucí automatizaci typu `ColorsAndNumbers` TTS + commit + push plati:

1. Zadani musi byt v pevném souboru, napriklad CSV/JSON fronta.
2. Skript smi zapisovat jen do allowlistu konkretnich cest.
3. Pred commitem musi byt preflight `git status --short`.
4. Commitovat jen explicitne povolene soubory, nikdy `git add .`.
5. Push az po testech a jasne omezene scope.
6. Logovat jen technicke informace, bez tokenu, API klicu nebo citlivych dat.

## ColorsAndNumbers - soví promluva 2026-05-23

Mila chce, aby GitHub Actions 2026-05-23 ve 3:00 Praha jednorazove zpracoval
soví text pro webovou aplikaci `ColorsAndNumbers/web_colors_numbers/`, vygeneroval
MP3 pres TTS a prepnúl aplikaci na nove audio.

Finalni pracovni text pro zpracovani 2026-05-23:

```text
Milé studentky, pan učitel se na vás už těší. Doufám, že jste se pilně připravovaly. Pokud vím, tak vás čeká malý test, ale nebude se známkovat. Krásný den a nezklamte mě, moudrou sovu. Hů, hů, hů.
```

Implementovano:

- konfigurace textu je v `config/colors_numbers_owl_20260523.json`,
- `scripts/daily_3am.py` ma jednorazovy datumovy gate pro `2026-05-23`,
- generuje `ColorsAndNumbers/web_colors_numbers/owl_230526.mp3`,
- prepina `ColorsAndNumbers/web_colors_numbers/app.js` na
  `owl_230526.mp3?v=20260523a`,
- GitHub Actions instaluje dependencies, po behu commituje a pushuje jen
  `ColorsAndNumbers/web_colors_numbers/app.js` a
  `ColorsAndNumbers/web_colors_numbers/owl_230526.mp3`,
- suchy beh pro `2026-05-23` vratil stav `planned`.

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

## Dalsi krok

Navazat cloudovou verzi:

- overit GitHub Actions beh po pushi,
- rozhodnout, jaky prvni realny nedestruktivni ukol ma cloud spoustet,
- az potom pridat konkretni task adapter s allowlistem a testy.
