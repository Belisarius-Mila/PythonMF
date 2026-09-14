<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-14 21:44 CEST.
- Kanonický proud `project-to-be-to-have`; Míla schválil lokální prototyp a zadal web.
- Publikační kopie `docs/to-be-to-have/` je totožná s `ToBeTraining/web/`.
- Cílová adresa: https://belisarius-mila.github.io/PythonMF/to-be-to-have/
- Cockpit: horní lišta → Webové aplikace → ToBeToHave; samostatné webové okno.
- 107 otázek, 24 skládání vět, 184 MP3, 47 WebP; obsah ani původní CSV se nemění.
- Ověření: 14 JS testů, 22 testů Cockpitu, 236 HTTP souborů, 184 MP3 a 47 obrázků.
- Publikační checkpoint; finální veřejný stav a nasazení ověřovat živými účtenkami.
- Lokální prototyp Míla hodnotí jako dobrý. Fyzický iPhone/audio po veřejném
  zveřejnění zůstává samostatnou přejímkou; offline/PWA není součást zadání.
- Historické KPTL checkpointy níže jsou nesouvisející historie, nikoli stav tohoto projektu.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: ToBeToHave

Nazev: ToBeToHave
Pracovni proud: project-to-be-to-have
Typ: Project
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Kanonicky handoff byl zalozen prvnim potvrzenym checkpointem tohoto proudu.

Co je hotove:
- Viz chronologicke checkpointy nize.

Co neni hotove:
- Viz posledni checkpoint a jeho dalsi krok.

Dalsi krok:
Viz posledni chronologicky checkpoint.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

### Automatický checkpoint 2026-08-11 09:33 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 11.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `kptl_viewer.py`
- Commit: `Fix KPTL application asset paths`
- Další krok: Spustit kptl_viewer.py v běžném desktopovém prostředí a krátce vizuálně ověřit okno a zvuk

### Automatický checkpoint 2026-08-11 10:01 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1336 testů, 319.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add KPTL launcher to Cockpit catalog`
- Další krok: Po checkpointu a nasazení otevřít v Cockpitu Webové aplikace → KPTL Introduction a ověřit okno i zvuk

### Automatický checkpoint 2026-08-11 11:00 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/tests/test_cockpit.py`, `kptl_viewer.py`
- Commit: `Add KPTL character quiz`
- Další krok: V Cockpitu otevřít KPTL Introduction, projít krátký vizuální a zvukový test kvízu a ověřit závěrečné skóre


### 2026-09-13 10:35 CEST — Lokální web ToBeToHave s obrázky a MP3

Hotovo:
- Oba výukové režimy mají vlastní webovou podobu, kontextové obrázky,
  anglické MP3, výběr lekce/věty, náhodné pořadí a ovládání tempa.
- Barevné slovní dílky přeskakují do otázky; Do/Does a změna has/goes
  jsou vizuálně zdůrazněné. Pauza zmrazí přehrávání i animaci.
- Zdrojová CSV pouze čtena, Pict pouze použit jako zdroj samostatných kopií.
- Nesouvisející historické checkpointy KPTL výslovně odděleny od aktuálního
  stavu tohoto proudu, bez mazání původních záznamů.

Rozhodnutí:
- Míla schválil lokální prototyp, hravé barevné animace, kontextové obrázky
  z Pict nebo nově vytvořené kolem 0,25 MiB a finální anglické věty jako MP3.
- Samostatné HTML/CSS/JS, vlastní data a média ve `ToBeTraining/web/`.
  Žádná databáze, účty, zápis pokroku nebo generování hlasu v prohlížeči.

Další krok:
- Mílova vizuální a zvuková revize obou režimů na Macu; přímý náhled je
  lokální loopback a sám o sobě nezpřístupňuje aplikaci na iPhonu.

Navrhované další kroky:
- Ověřit iPhone Safari, první tap, pauzu a návrat z pozadí.
- Po revizi samostatně rozhodnout o HTTPS hostingu a odkazu z Cockpitu.

Technický důkaz:
- 14/14 JS testů, 184/184 MP3 ověřených jako MP3 s rozumnou délkou,
  47/47 obrázků dekódovatelných a do 262 144 B, 236/236 HTTP odpovědí.
- Browser UI a reálný poslech zůstávají otevřené, neprohlašují se za ověřené.
- Kanonické soubory: `README_WEB.md`, `IMAGE_PLAN.md`, `scripts/`, `web/`.
- Lokální vývojový krok bez pushnutí, publikování nebo nasazení Cockpitu.

### 2026-09-13 13:18 CEST — Zdrojový prototyp uložený na GitHubu

Hotovo:
- Lokální webový prototyp s obrázky a MP3 je součástí odeslaného hlavního repozitáře.

Rozhodnutí:
- Míla schválil odeslání čekajícího balíčku; hostování prototypu tím nevzniká.

Další krok:
- Pokračovat uživatelskou revizí lokálního prototypu.

Navrhované další kroky:
- Případné hostování a integraci řešit samostatně.

Technický důkaz:
- Commit `0ce9c5bd` je předkem ověřeného GitHub headu `ea13d3d6`; publikační brána balíčku prošla 1 640/1 640 testy.


### 2026-09-14 21:44 CEST — Web ToBeToHave a přímý vstup z Cockpitu

Hotovo:
- Schválený lokální prototyp má kompletní publikační kopii v `docs/to-be-to-have/`.
- Dlaždice ToBeToHave otevírá web v samostatném okně; Webové aplikace jsou opět
  přímo v horní liště, bez nutnosti hledat je v Servisu.

Rozhodnutí:
- Míla potvrdil, že lokální prototyp je dobrý, a zadal jeho zpřístupnění na webu
  z Cockpitu. Používá se stávající GitHub Pages, cílová adresa https://belisarius-mila.github.io/PythonMF/to-be-to-have/
- Původní aplikace, CSV a zdrojový web se nemění; nejde o vývoj C00 Camina ani U07 Cockpitu.

Další krok:
- Po zveřejnění otevřít Webové aplikace → ToBeToHave a používat oba režimy.

Navrhované další kroky:
- Na fyzickém iPhonu ověřit první tap se zvukem a návrat z pozadí; automatická
  přejímka není důkaz systémové audio politiky Safari.

Technický důkaz:
- 14/14 JS testů trenažéru, 22/22 cílených testů Cockpitu.
- 184/184 MP3, 47/47 WebP a 236/236 místních HTTP odpovědí shodných se zdrojem.
- Regresní test hlídá vstup do aplikací přímo v hlavičce a webový cíl dlaždice.
- Zdrojový checkpoint předchází publikaci; finální head, Pages a nasazení
  ověřují živé GitHub a Cockpit účtenky. Podrobnosti v `reports/to_be_web_release_2026_09_14.md`.
