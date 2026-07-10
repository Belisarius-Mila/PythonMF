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
- Celkem prošlo 424 testů.
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

## Co gate zatím neřeší

- Není to browser end-to-end test.
- Nehodnotí, zda je funkce mrtvý kód.
- Neřeší zatím nepřipnuté verze Python závislostí.
- Nespouští lokální ani Tailscale smoke check, protože CI nemá živý Cockpit.
- Nemá tvrdý limit počtu řádků; při bezpečné extrakci mohou krátkodobě vznikat
  importy a přechodové adaptéry.

## Další krok

Pokračovat malou datově bezpečnostní dávkou: zmapovat reminders/Quick Notes
read-modify-write cesty a převést jednu nejmenší registry na zamčenou transakci
s dvouprocesovým testem. Poté vytvořit read-only inventuru kandidátů mrtvého
kódu bez mazání.
