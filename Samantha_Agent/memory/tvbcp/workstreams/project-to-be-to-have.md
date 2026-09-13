<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-13 10:35 CEST.
- Kanonický proud: `project-to-be-to-have`; aplikace `ToBeTraining/`.
- Hotovo: samostatný lokální web se 107 otázkami, 24 skládáními vět,
  barevným animovaným převodem na otázku, pauzou a volitelným překladem.
- Média: 184 hotových anglických MP3; 47 WebP, z toho 11 nových ilustrací.
  Každý WebP je nejvýše 0,25 MiB; největší ověřený soubor 256 386 B.
- Důkaz: 14 automatických JS testů (včetně UI modulu s náhradním DOM/audiem),
  184 MP3 ověřených ffprobe, 47 dekódovaných obrázků a 236 místních HTTP
  odpovědí; rychlá projektová statická brána OK.
- Otevřeno: skutečná vizuální a zvuková revize Mac/iPhone. Browser se v této
  relaci nepřipojil kvůli chybějícímu nativnímu propojení; simulovaný DOM
  neověřuje layout ani přehrávání Safari.
- Další krok: na Macu otevřít lokální prototyp a projít oba režimy; potom
  domluvit dostupnost na iPhonu a samostatné umístění webu.
- Zdrojový prototyp byl 13. 9. odeslán na GitHub v denním balíčku. Samostatné hostování webu ani jeho integrace do Cockpitu nebyly provedeny.
- Zdrojový desktopový skript a obě CSV beze změny. Vývoj VocabularyFR/IT
  zůstal mimo rozsah tohoto kroku.
- Oprava vazby: starší checkpointy KPTL níže byly vedené pod chybným proudem.
  Jsou zachované jako historie, ale nedokládají stav ToBeToHave.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: ToBeToHave

Pracovni proud: `project-to-be-to-have`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-11 09:33 CEST – KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty

Hotovo:
- KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Spustit kptl_viewer.py v běžném desktopovém prostředí a krátce vizuálně ověřit okno a zvuk

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 11.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-to-be-to-have`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-11 10:01 CEST – KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher

Hotovo:
- KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Po checkpointu a nasazení otevřít v Cockpitu Webové aplikace → KPTL Introduction a ověřit okno i zvuk

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- plná Cockpit brána: 1336 testů, 319.1 s, výsledek OK.
- Pracovní proud: `project-to-be-to-have`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-11 11:00 CEST – KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre

Hotovo:
- KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Každá ze čtyř postav má 8 otázek, z toho 4 s odpovědí YES a 4 s odpovědí NO

Další krok:
- V Cockpitu otevřít KPTL Introduction, projít krátký vizuální a zvukový test kvízu a ověřit závěrečné skóre

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-to-be-to-have`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.


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
