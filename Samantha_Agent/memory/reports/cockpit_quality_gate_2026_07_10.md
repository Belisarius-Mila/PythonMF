# Cockpit quality gate — 2026-07-10

## Cíl

Před rozdělováním monolitu vznikla jedna opakovatelná bezpečnostní brána pro
lokální vývoj i GitHub Actions. Nemění runtime chování Cockpitu, nespouští
server a nečte ani nezapisuje soukromá data.

Kanonický lokální příkaz je:

```text
.venv/bin/python scripts/cockpit_quality_gate.py
```

## Co gate kontroluje

1. `git diff --check` pro whitespace chyby.
2. Syntax klíčových Cockpit, VoiceBridge a persistence modulů. Python
   `SyntaxWarning` je chyba, ne pouze upozornění.
3. Pevně vyjmenovanou regresní sadu Cockpitu, VoiceBridge, persistence,
   dokumentů, e-mailů, backupu a single-instance migrace.
4. Informativní architektonickou metriku; její růst gate nezastaví, ale vypíše
   varování, že nová doménová logika patří do samostatného modulu.

Výchozí metrika před rozdělováním:

- `app/cockpit.py`: 22 465 řádků, 332 top-level funkcí, 2 třídy.
- `app/speech/adam_voice_mode.py`: 1 105 řádků, 39 top-level funkcí, 1 třída.

Metrika není hodnocení kvality jednotlivých řádků ani automatická mazací brána.
Slouží k tomu, aby další růst monolitu nebyl neviditelný.

## GitHub Actions

Repozitářový workflow je v kořenové cestě
`.github/workflows/cockpit-quality-gate.yml`, tedy na místě, které GitHub
skutečně načítá. Používá:

- `macos-14` a Python 3.12,
- pouze oprávnění `contents: read`,
- timeout 25 minut,
- zrušení staršího běhu stejné větve,
- path filtry, takže se nespouští při změnách nesouvisejících s Cockpitem,
- žádné tokeny, tajemství, runtime servery ani private vault data.

Workflow lze spustit ručně a automaticky běží pro relevantní push na `main`
nebo pull request.

## První ověření

- Lokální quality gate prošel kompletně.
- Nový test ověřuje manifest cest/modulů a architektonickou metriku.
- Po rozšíření o samostatné reminders, Quick Notes, urgent reminders,
  dokumentové persistence primitivy a launcher moduly prochází 466 testů.
- Gate při prvním běhu odhalil tři ekvivalentní JavaScript regex escape zápisy
  uvnitř Python HTML řetězce. Byly opraveny bez změny výsledného JavaScriptu a
  syntax kontrola nyní podobný `SyntaxWarning` odmítne.
- YAML workflow prošel lokálním parserem.
- První vzdálený běh správně odhalil, že osm VoiceBridge CLI testů natvrdo
  používalo lokální `.venv/bin/python`. Testy nyní používají `sys.executable`,
  tedy interpreter aktuálního prostředí.
- Gate umí při vzdáleném selhání vytvořit bezpečnou GitHub anotaci s koncem
  testovacího tracebacku, takže diagnostika nevyžaduje hádání ani soukromá data.
- Třetí GitHub Actions běh pro commit `3ba9d59` skončil úspěšně za 1 minutu
  19 sekund. Lokální a vzdálená pojistka jsou tím ověřené.
- Ruční otevření přes `Ctrl+Option+Command+C` odhalilo rozdílný code-stamp
  manifest serveru a launcheru. Zdravý server byl proto chybně označen jako
  starý a launcher ho restartoval.
- Nový `app/cockpit_code_stamp.py` je jediný zdroj manifestu pro server i
  launcher. Manifest automaticky zahrnuje Python moduly v `app/` a
  `scripts/cockpit_server.py`; regresní test hlídá shodu obou spotřebitelů.
- První běh po změně záměrně provedl jediný restart a trval 42,47 s. Následující
  běžné ověření `open_cockpit.py --no-open` trvalo 0,89 s a server/launcher měly
  shodný stamp. Lokální i Tailscale smoke check byly zelené.
- Přesun výpočtu stampu snížil `app/cockpit.py` na 22 454 řádků a 331 top-level
  funkcí, tedy 11 řádků a jednu funkci pod výchozí baseline.
- GitHub Actions běh číslo 5 pro commit `17729ec` skončil úspěšně za 1 minutu
  29 sekund.
- `app/urgent_reminders.py` a jeho nový samostatný dvouprocesový test jsou nyní
  přímo v lokálním gate i v GitHub Actions path filtrech. Lokální běh po zamčení
  urgent indexu prošel všech 463 testů.
- GitHub Actions běh číslo 7 pro urgent-reminders commit `6e6dc5c` skončil
  úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29109790245`.
- `app/documents/vault.py` je nově přímo v syntax manifestu a samostatný
  `tests.test_document_persistence` v test manifestu. Lokální gate po převodu
  dokumentového JSON/JSONL/appendu na sdílenou persistence vrstvu prošel všech
  466 testů.

## Co gate zatím neřeší

- Není to browser end-to-end test.
- Nehodnotí, zda je funkce mrtvý kód.
- Neřeší zatím nepřipnuté verze Python závislostí.
- Nespouští lokální ani Tailscale smoke check, protože CI nemá živý Cockpit.
- Nemá tvrdý limit počtu řádků; při bezpečné extrakci mohou krátkodobě vznikat
  importy a přechodové adaptéry.

## Další krok

Quality gate, read-only inventura, Cleanup R1, zamčené reminders/Quick Notes/
urgent reminders a první dokumentové persistence primitivy jsou hotové. Další
rollout má nejdřív navrhnout skutečnou více-souborovou transakci index + manifest
a teprve potom převést metadata a reading status s concurrency/consistency testy.
