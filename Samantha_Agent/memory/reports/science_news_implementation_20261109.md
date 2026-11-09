# ScienceNews — lokální implementace 03/K4, 2026-11-09

ScienceNews přidává do Knihovny frontu důležitých vědeckých zpráv. Horní ikona
je zelená a pulzuje, dokud zbývá některou zprávu vyřídit. Český abstrakt má
původní odkaz, datum, obor, význam a nejistoty. Uložit zprávu současně sleduje,
Sledovat pouze sleduje, Nezařazovat vyřídí jednu zprávu. Všechny tři volby po
ověření skryjí kartu a poslední volba zešedne ikonu. Překlad má samostatné okno
bez automatického vyřízení zprávy. Sledování lze vypnout.

Ztracená odpověď není pokyn k druhému zápisu nebo modelovému tahu. Trvalá
identita a stav umožňují ověřit stejnou akci; opakovaný nebo přerušený zápis
nevytvoří druhou kartu ani nepřepíše pozdější editaci. Při vyprázdnění/selhání
zdrojů nevzniká umělá výplň. Běhový adapter podporuje pátek 08:00 přípravu,
09:00 publikaci Europe/Prague a jediné předání redakčního jobu.

## Ověření

- 115 cílených unit testů PASS, včetně 10 Node scénářů a izolovaných skutečných
  HTTP tras: všechny volby, zelená/šedá, překlad bez vyřízení, read-only polling,
  restart/reconnect, souběh, přerušený archiv, zachování editace, DOI/revize,
  primární citace, role/rozpočet, striktní Standard/readOnly a neověřené doručení.
- Plná projektová brána: 2929 testů OK (5 SKIP), syntaxe a whitespace OK. Výstup logs/science_news_full_gate_20261109.log.
- Osm RSS kanálů prošlo živým čtecím testem bez modelu. CERN/NIH dříve vracely
  404/403; nejsou vydávány za fungující. Pokrytí je omezené, převážně Nature.
- Modelový katalog nad existujícím socketem potvrdil gpt-6.1-sol a medium;
  role nebyla navázaná, žádné vlákno ani placený tah se nespustily.
- config/agent_roles.json je byte-identický s výchozím commitem. Provozní
  ScienceNews adresář/aktivace neexistují; žádný článek se do živé Knihovny nezapsal.
- Skutečný browser host nebyl dostupný. Node/HTTP ověření není vizuální ani
  fyzická Mac/iPhone přejímka; ta je otevřená po samostatně schváleném nasazení.

Plná brána zachytila neaktuální test, který vyžadoval nepřítomnost již aktivované
recovery role. Test nyní ověřuje neaktivovanou roli v izolované syntetické
konfiguraci. Skutečný recovery JSON ani provozní služba se nemění. Srovnání
pořadí POST tras také opravilo umístění nových metadat v registru; kontrola
nebyla oslabena ani odstraněna.

## Hranice a rizika

Implementace je pouze lokální na data/parallel-20261104. Bez push, převzetí do
main, nasazení, instalace/restartu služby, změny role bindingů a placeného běhu.
Sdílený App Server klient, runtime, e-mail, kalendář, Camino a závislosti se nemění.

Parser zná nový název science_news_editor, avšak aktivace vyžaduje samostatně
schválený model, cenu, skutečnou malou zkoušku a soukromý runtime config.
Kandidát Sol/medium Standard má doložený čtecí katalog, nikoli živou vědeckou QA.
Návrh rezervace 15 kreditů/job a 100/měsíc není schválený limit, faktura ani
upstream hard cap; zahrnuje výběry i vyžádané překlady. Konzervativní byte odhad
60 aktuálních podkladů činí přibližně 6,10565 kreditu při přijímací mezi 16k
výstupních tokenů, bez záruky protokolové režie a bez skutečné tokenizace.
Oficiální Standard sazby ověřené 2026-11-09: https://learn.chatgpt.com/docs/pricing#token-rates.
Podrobnosti v science_news_budget_proposal_20261109.json.

Plný text se překládá jen při ověřené dostupnosti a oprávnění; chybějící text,
paywall nebo neúplný výsledek nejsou nahrazovány abstraktem označeným jako celý
překlad. Hodnocení významnosti a odborná správnost potřebují další uživatelskou
zpětnou vazbu. Nečekané/neověřené modelové výsledky se automaticky neopakují.

## Přesný další krok

Will převezme tento jediný Datův commit do aktuálního main a zkontroluje drobné
integrační body Cockpitu a snapshot assetů. Potom samostatně schválené p+n
registrovanou cestou a přejímka UI/API na Macu/iPhonu. Následuje schválený
konkrétní modelový pilot, role/rozpočet a až potom aktivace plánovače ve skutečném
provozním checkoutu. Podrobný postup: ../technical/science_news.md.

Pro první neplacenou UI přejímku je připravený konkrétní paket
`science_news_ui_pilot_20261109.json`: K02/K05/K08, původní data a zdroje, české
vlastní abstrakty. Není vložený do živé fronty ani Knihovny. Až po výslovném
schválení cílového provozního importu lze použít registrovaný redakční vstup:
`.venv/bin/python scripts/science_news.py import --input memory/reports/science_news_ui_pilot_20261109.json --editor-reviewed`.
Jednotlivé články se archivují až skutečným uživatelským tlačítkem. Samotný
import předložení karet ani čtení abstraktů nevyžaduje aktivaci editoru.

## Změněné soubory

- `app/cockpit.py`
- `app/cockpit_frontend.py`
- `app/cockpit_science_news.py`
- `app/communication/agent_roles.py`
- `app/frontend/cockpit/page.html`
- `app/frontend/cockpit/science_news.js`
- `app/frontend/cockpit/styles.css`
- `app/science_news.py`
- `app/science_news_model.py`
- `app/science_news_runner.py`
- `app/science_news_sources.py`
- `app/science_news_translation_page.py`
- `app/workflows/commands.py`
- `config/science_news_activation.example.json`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/knowledge_library_article_editing_2026_07_16.md`
- `memory/projects/vedecke_clanky.md`
- `memory/reports/science_news_budget_proposal_20261109.json`
- `memory/reports/science_news_calibration_20261108.json`
- `memory/reports/science_news_implementation_20261109.json`
- `memory/reports/science_news_implementation_20261109.md`
- `memory/reports/science_news_model_preflight_20261109.json`
- `memory/reports/science_news_sources_20261109.json`
- `memory/technical/capability_routing_rules.md`
- `memory/technical/science_news.md`
- `memory/tvbcp/knihovna_cockpit.txt`
- `scripts/cockpit_quality_gate.py`
- `scripts/science_news.py`
- `tests/science_news_frontend.test.cjs`
- `tests/test_cockpit_frontend.py`
- `tests/test_recovery_guide.py`
- `tests/test_science_news.py`
- `tests/test_science_news_frontend.py`
- `tests/test_science_news_http.py`
- `tests/test_science_news_model.py`
- `memory/reports/science_news_ui_pilot_20261109.json`
