# Handoff pracovního proudu: Vocabulary EN

Nazev: Vocabulary EN
Pracovni proud: project-vocabulary-en
Typ: Project
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ne
Datum: 2026-11-13 13:13 CET

Co se resilo:
Po přijetí místní galerie Míla zadal publikační vazbu a nyní schválil integraci
všech čtyř Datových commitů; Willovy souběžné commity ponechat stranou.

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
- Lokální integrační merge je ověřený, 105 cílených PASS. Plná brána
  PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP.
- Skutečný main/merge SHA uvádí závěrečná účtenka v Downloads.
- Načtení nové vazby serverovým runtime, push a publikace.
- Fyzický iPhone a případné samostatné nahrávky vět.
- TVBCP není založený. Pouhé načtení katalogu nic nezakládá; bez dohody
  nepoužívat Cockpit checkpoint, který by TVBCP vytvořil. To neblokuje běžný
  místní terminálový checkpoint této registrace a projektové paměti.

Dalsi krok:
Samostatně určit publikační rozsah: současný souhlas zahrnuje čtyři Datovy
commity, nikoli Willův čekající balíček. Skutečný merge/main SHA a převzetí
profilů uvádí závěrečná účtenka v Downloads. Před Pages p+n musí novou vazbu
znát serverový runtime. Bez nového TVBCP a bez automatického p+n.

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


### 2026-11-13 13:22 CET — Schválená integrace čtyř Datových commitů

Hotovo: Připravený integrační kandidát nad main9857d2e6 spojuje HA-06,
galerii Vocabulary EN, testovou SDK opravu a přesnou Pages registraci.
77 souborů změněných pouze na main zůstává bajtově shodných; konfliktní
registry zachovávají Willovy záznamy a doplňují Datovy. Původní worktree
Data zůstává čistý na 9f113231; integrační výsledek je připravený k převzetí
na main. Skutečné převzetí potvrzuje závěrečná účtenka v Downloads.

Rozhodnutí: Míla schválil všechny Datovy commity a určil nechat Willovy
stranou. Integrace zachová historii main i schválené f95734f5, 9b584b95,
2f16cf66 a 9f113231. Žádný push, nasazení nebo služba tím nejsou povolené.

Další krok: Samostatně rozhodnout o případném publikačním rozsahu.
Závěrečná účtenka uvádí merge SHA a skutečné fast-forward převzetí na main;
Willovy čekající commity se tímto souhlasem nepublikují.

Navrhované další kroky: Samostatné publikování Vocabulary EN vyžaduje vlastní
schválené p+n a serverově načtenou novou vazbu. Fyzický iPhone a případné
nahrávky vět zůstávají otevřené. Žádný nový Vocabulary EN TVBCP nevznikl.

Technický důkaz: 105 cílených kontrol PASS / 22,338 s; plná integrační brána
PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP. Zachovaný originální main i Datovy soubory,
žádný reset/rebase/force push. Privátní source manifest a porovnání 77 souborů
jsou v data/private/vocabulary_en_integration_20261113/ integračního worktree.

Rozsah souhlasu k další fázi: Míla schválil čtyři Datovy commity a požádal
nechat Willovy stranou. Toto není souhlas s celým čekajícím GitHub balíčkem.
Běžné p+n audituje celý rozsah origin/main..main, takže se v této etapě
nespouští. Před zveřejněním je potřeba samostatně určit a schválit jeho rozsah.


## 2026-11-13 15:04 CET — Oprava servisního nalezení Node před společným p+n

Hotovo: Regresní test galerie používá stejné nalezení Node jako kanonická
brána. Funguje také při minimálním launchd PATH, bez změny systémového PATH,
instalace či přeskočení testu. Galerie a její produkční data se nemění.

Rozhodnutí: Míla výslovně schválil p+n všech čekajících commitů; tím je
překonané předchozí omezení publikace pouze na Datovy commity. Nejprve
společný runtime, následně vlastní registrovaný Pages cíl Vocabulary EN.
Nový TVBCP se nezakládá.

Další krok: Commit opravy, zarovnání čistých profilů a nové registrované
p+n opraveného headu. Původní nejisté vydání se neopakuje.
Navrhované další kroky: Po potvrzeném nasazení fyzická iPhone přejímka.

Technický důkaz: Původní účtenka a843815b941d7872bcc6e69bea341829 skončila
attention; 3823 testů / 53 skip / 1 error: FileNotFoundError node v novém
galerijním testu. Brána skončila před _push_exact_head; živý GitHub dál
fb062e34, main498ba91a o12 commitů napřed, žádné nasazení. Oprava:29 testů
PASS/13,193s s PATH=/usr/bin:/bin:/usr/sbin:/sbin, včetně skutečných Node
scénářů; rychlá statická brána PASS. Původní důkaz zachovaný v
logs/all_commits_failed_gate_20261113.log a all_commits_runtime_release_20261113.log.
