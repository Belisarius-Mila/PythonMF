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
  dokumentové persistence primitivy/transakce, ScanDocu, managed relace,
  autosave a launcher moduly prochází 532 testů.
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
- GitHub Actions běh číslo 8 pro document persistence commit `1196076` skončil
  úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29110559953`.
- `app/documents/transactions.py` je v syntax manifestu a
  `tests.test_document_transactions` v test manifestu. Šest nových testů kryje
  concurrency, rollback, dvě crash-recovery fáze a idempotentní no-change.
  Lokální gate prošel všech 472 testů.
- GitHub Actions běh číslo 9 pro document-record transaction commit `64ce395`
  skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29115015113`.
- `app/documents/scandocu.py` je nově přímo v syntax manifestu. Čtyři nové
  testy ověřují, že ScanDocu review atomicky spojí index, manifest, candidate
  status a action audit, při selhání či pádu vše obnoví a s Cockpit metadata
  transakcí sdílí primární lock. Lokální gate prošel všech 476 testů.
- GitHub Actions běh číslo 10 pro ScanDocu review transaction commit `a11e263`
  skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29117003749`.
- `tests.test_adam_service` a `tests.test_safety_quick_checks` jsou nově přímo
  v kanonickém gate. Gate navíc kontroluje `zsh -n` pro oba autosave/screen
  skripty a přímo kompiluje `app/adam_service.py`, `app/autosave_service.py` a
  `scripts/autosave_status.py`. Celkem prošlo 532 testů.
- Testy kryjí singleton watcher lock, varování při dvou watcherech, zákaz
  watcheru v managed relaci, rychlé ukončení čekajícího watcheru, ověřený stop
  Janičky a pravdivý `stop_incomplete` při přeživším screenu.
- Extrakce autosave backendu do `app/autosave_service.py` snížila Cockpit
  monolit na 22 369 řádků / 325 top-level funkcí, tedy 96 řádků pod baseline.
- Implementace je v commitu `67ba77e`. GitHub Actions Cockpit Quality Gate běh
  číslo 11 skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29119991977`.
- Fáze 1.1 přidala `app/cockpit_status_service.py`, který samostatně skládá
  health, live a plný status, včetně timingů a zamčené live cache. Veřejné
  funkce a HTTP routy v `app/cockpit.py` zůstaly kompatibilní adaptéry.
- Tři přímé kontraktní testy nové služby rozšířily gate na 535 testů. Monolit
  klesl na 22 293 řádků / 325 top-level funkcí, tedy 172 řádků pod baseline.
- Po jednorázovém restartu nové verze prošly lokální i Tailscale smoke checky
  pro `/`, `/api/server/health`, `/api/live-status`, `/api/status` a recovery;
  obě adresy obsluhovala jedna instance PID 27653.
- Implementace Fáze 1.1 je v commitu `a8857f0`. GitHub Actions Cockpit Quality
  Gate běh číslo 12 skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29121176082`.
- Fáze 1.2 přidala `app/voice_bridge_coordinator.py`. Coordinator rozhoduje
  jediného vlastníka doručení pro textovou i nahrávanou větev: při běžícím
  watcheru pouze uloží pokyn a inline adapter vůbec nezavolá; explicitně
  předaný inline adapter zůstává testovacím/fallbackovým kontraktem.
- HTTP routy, přepis audia, TTY/screen transport, pending transakce, historie a
  potvrzovací pravidla zůstaly beze změny. Čtyři přímé testy rozšířily gate na
  539 testů. Monolit klesl na 22 230 řádků / 324 top-level funkcí, tedy 235
  řádků pod baseline.
- Po nasazení prošly lokální i Tailscale smoke checky všech pěti cest. Obě
  adresy obsluhovala jedna instance PID 32168 a port 8771 byl volný.
- Ruční iPhone ownership test potvrdil jeden doručený pokyn, jednu odpověď a
  žádný nový inline delivery attempt. GitHub Actions gate pro commit `0beebbc`
  skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29122979483`.
- První audio pokus se sluchátky uvízl po úspěšné obnově AudioContextu bez
  success/error události, zatímco Edge TTS backend vracel MP3 za 1-2 sekundy i
  při třech souběžných požadavcích. Frontend nyní omezuje dekódování na pět
  sekund, playback podle délky audia, při selhání přejde na HTML Audio a v
  jednom klientu nepustí více čtení současně.
- JavaScript syntax, 225 Cockpit testů a celý gate s 539 testy prošly. Monolit
  má 22 263 řádků / 324 top-level funkcí, tedy 202 řádků pod baseline.
- Po nasazení audio opravy prošly oba smoke checky na jediné instanci PID
  35158. Mila ručně potvrdil přehrání do sluchátek a technický log zaznamenal
  pouze `audio_play_succeeded`, bez obsahu odpovědi.
- Závěrečná audio oprava je v commitu `18b9f63`. GitHub Actions Cockpit Quality
  Gate běh číslo 14 skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29123726588`.

## Co gate zatím neřeší

- Není to browser end-to-end test.
- Nehodnotí, zda je funkce mrtvý kód.
- Neřeší zatím nepřipnuté verze Python závislostí.
- Nespouští lokální ani Tailscale smoke check, protože CI nemá živý Cockpit.
- Nemá tvrdý limit počtu řádků; při bezpečné extrakci mohou krátkodobě vznikat
  importy a přechodové adaptéry.

## Další krok

Quality gate, read-only inventura, Cleanup R1, zamčené reminders/Quick Notes/
urgent reminders, dokumentové persistence primitivy, metadata/reading-status
transakce, ScanDocu review a životní cyklus autosave/managed relací jsou hotové.
Fáze 1.1 status/health i Fáze 1.2 VoiceBridge command ownership a iPhone audio
fallback jsou hotové a ručně ověřené. Hlavní roadmapa pokračuje Fází 1.3:
dokumentové routy a service vrstva. Reindex zůstává samostatný další krok
dokumentové persistence.
