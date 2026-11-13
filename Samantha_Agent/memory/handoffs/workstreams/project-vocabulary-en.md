# Handoff pracovního proudu: Vocabulary EN

Nazev: Vocabulary EN
Pracovni proud: project-vocabulary-en
Typ: Project
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ne
Datum: 2026-11-13 13:13 CET

Co se resilo:
Po přijetí místní galerie Míla zadal další krok: připravit publikační vazbu.

Co je hotove:
- Galerie v1: 425 karet / 18 skupin, přijatá Mílou na Macu.
- Každá karta má anglickou větu a český překlad. Zobrazí se po odhalení
  odpovědi; současné MP3 jsou nahrávky slovíček, nikoli celých vět.
- Místně připravený katalogový projekt a přesný Pages cíl vocabulary-en/.
- Úplný předchozí vývoj a důkazy: ../vocabulary_en_gallery_v1_2026_11_13.md.

- Ověření: 244 cílených testů / 24,880 s včetně 18 Node scénářů, navíc
  67 přímých publikačních kontrol / 6,026 s PASS. Finální plná brána
  3688 testů / 631,512 s, 5 SKIP, žádné chyby/selhání.
- Finální zdroje/testy 12/12 shodné se zmrazenou účtenkou.
- Log: vocabulary_en_publication_binding_full_gate_final_20261113.log
  SHA-256: 57d9997b4d3b863a7b7c36fac7c96ced8e7c51185b893ae31fbf5897f09292c6.

Co neni hotove:
- Integrace do main, načtení nové vazby serverovým runtime, push a publikace.
- Fyzický iPhone a případné samostatné nahrávky vět.
- TVBCP není založený. Pouhé načtení katalogu nic nezakládá; bez dohody
  nepoužívat Cockpit checkpoint, který by TVBCP vytvořil. To neblokuje běžný
  místní terminálový checkpoint této registrace a projektové paměti.

Dalsi krok:
Servisní rozhodnutí pro integraci divergentní větve podle připraveného TXT
v Downloads; zachovat novější main i všechny čtyři Datovy kroky. Po integraci
ověřit spojený kód a načtení nové vazby na serveru. P+n musí dostat tento
přesný projekt a cíl. Předání se nikomu automaticky neposílá.

Navrhovane dalsi kroky:
- Samostatné schválené vydání galerie po integraci a načtení vazby na serveru.
- Fyzická iPhone přejímka včetně slovníčkového audia a návratu do galerie.
- Případná dohoda o TVBCP před checkpointem v Cockpitu.
- Nahrávky vět řešit jako samostatný navazující rozsah.

Zmenene nebo relevantni soubory:
- human_adam_workstream_catalog.py; luna_release.py; mmtx_pages_deploy.py; ACTIVE_PROJECTS.md;
  WORKSTREAMS.md; luna_release_orchestration.md; související katalogové a
  publikační testy, test_vocabularyen_gallery.py a test_vocabularyen_selection.js.

Bezpecnost / neukladat:
Žádná soukromá vlákna, TVBCP, modelové/TTS volání, push ani publikace se tímto
místním krokem nespouštějí. Nevydávat přes jiný projekt a neměnit Willův main.
