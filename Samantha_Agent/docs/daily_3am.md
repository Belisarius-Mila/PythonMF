# Daily 3 AM Routine

Tento dokument popisuje bezpecnou denni rutinu pro `Samantha_Agent`.

## Co rutina dela

Hlavni vstupni bod je:

```bash
python scripts/daily_3am.py
```

Aktualni verze je zamerne nedestruktivni. Pouze:

- zapise bezpecny log do `logs/daily_3am.log`,
- pouzije lock v `data/daily_3am/daily_3am.lock`, aby nebezely dve kopie najednou,
- zapise denni stav do `data/daily_3am/YYYY-MM-DD.json`,
- dalsi spusteni ve stejny den udela no-op,
- vraci jasne navratove kody.

Konkretni ukoly jako TTS generovani, commit nebo push se maji pridat az jako
samostatne otestovane kroky s allowlistem souboru a preflightem `git status`.

## Navratove kody

| Kod | Vyznam |
| --- | --- |
| `0` | Hotovo nebo bezpecny no-op. |
| `10` | Rutina uz bezi v jinem procesu. |
| `20` | Chyba pripravy nebo neocekavana runtime chyba. |
| `30` | Selhal nakonfigurovany denni ukol. |
| `40` | Neplatne argumenty prikazu. |

## Lokalne: macOS launchd + probuzeni v 02:55

Instalace:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
zsh scripts/install_daily_3am_launchd.sh
```

Instalacni skript:

- vytvori `~/Library/LaunchAgents/com.miloslavfalta.samantha.daily-3am.plist`,
- nastavi spousteni v 03:00 lokalniho casu pres `launchd`,
- nastavi probuzeni/zapnuti pres:

```bash
pmset repeat wakeorpoweron MTWRFSU 02:55:00
```

Odinstalace launchd jobu:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
zsh scripts/uninstall_daily_3am_launchd.sh
```

Pokud byl `pmset repeat` pouzit jen pro tuto rutinu, zrus ho rucne:

```bash
pmset repeat cancel
```

Kontrola:

```bash
launchctl list | grep com.miloslavfalta.samantha.daily-3am
pmset -g sched
tail -n 100 logs/daily_3am.log
```

Rucni test bez zmeny denniho stavu:

```bash
python scripts/daily_3am.py --dry-run
```

Vynucene opakovani pro dnesek:

```bash
python scripts/daily_3am.py --force
```

## Dulezite: spanek, probuzeni a vypnuty Mac

`launchd` spusti ulohu jen tehdy, kdyz macOS bezi.

- Spanek: Mac je uspany, ale system ho muze predem probudit. Tady pomaha
  `pmset repeat wakeorpoweron ...`.
- Probuzeni: Mac se v 02:55 probudi, `launchd` muze ve 03:00 spustit rutinu.
- Uplne vypnuti: lokalni Python kod na vypnutem pocitaci nebezi. `pmset
  wakeorpoweron` muze na podporovanem Macu naplanovat zapnuti, ale neni to
  nahrada za cloud. Pokud je Mac bez napajeni, vybity, zavreny v rezimu, ktery
  neumi zapnuti, nebo je zakazana funkce firmwaru, lokalni rutina se nespusti.

Pro rutinu, ktera musi bezet i pri vypnutem Macu, pouzij cloud variantu.

## Cloud: GitHub Actions v 03:00 Europe/Prague

GitHub Actions cron pouziva UTC, ne `Europe/Prague`. Praha ma v zime UTC+1 a v
lete UTC+2. Schedule se muze opozdit, proto je pro cloud lepsi spustit job kratce
po cilove hodine a v Pythonu povolit casove okno.

Aktualni jednorazovy soví retry pro 2026-05-24 bezi v letnim case v 03:17 Praha:

```yaml
schedule:
  - cron: "17 1 * * *"
```

Spousteci krok:

```bash
python scripts/daily_3am.py --window-start-hour 3 --window-hours 5
```

Soubor workflow pro skutecne spousteni GitHubem patri do korene git repozitare:

```text
.github/workflows/samantha-daily-3am.yml
```

Projektova kopie je ponechana i v `Samantha_Agent/.github/workflows/` jako
snadno dohledatelny template k teto dokumentaci. GitHub ji ale sam nespousti,
pokud neni zkopirovana do korene repozitare.

Pro rucni spusteni pres `workflow_dispatch` se kontrola hodiny nepouziva.
Casove okno se pouziva jen u naplanovaneho `schedule` behu.

## Budouci TTS + git push krok

Az se bude pridavat konkretni uloha pro `ColorsAndNumbers`, doporuceny bezpecny
postup je:

1. Nacist zadani z pevneho souboru, napr. `ColorsAndNumbers/tts_queue.csv`.
2. Generovat jen do allowlistu, napr. `ColorsAndNumbers/web_colors_numbers/` a
   `docs/colors-numbers/`.
3. Pred commitem zkontrolovat `git status --short`.
4. Commitovat jen konkretni povolene soubory, nikdy `git add .`.
5. Push povolit az po testu a logovat jen technicke informace bez tajemstvi.
