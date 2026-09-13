<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-13 10:12 CEST

### Hotovo
- Doplněno 8 IT položek z NewWords.txt; celkem 471 slovíček.
- Již existující hesla bez duplicit; usi má i infinitiv usare,
  vinti příklad ve správném množném čísle, quelle ukazovací význam.
- Dříve potvrzené Last 20/50/HT a lokální Tk spuštění zůstávají beze změny.
- Společný audit: FR Míla 234 / FR Jana 413 / IT Míla 471 řádků,
  žádné chybějící obrázky v desktopových ani Pythonista resolverech.
- Doplněno také devět starších Janiných českých vazeb chybějících v Pythonistě.
- Osm nových ilustrací WebP do 250 kB; kanonické české abecední mapování
  1 082 položek (+27) je bajtově shodné s Janinou sdílenou kopií.
- Šest testů kanonického mappingu i rychlá statická brána prošly; původní řádky Míly včetně L/HT
  zachované. Všechny nové položky mají Sentence/SentenceT a L=ne, HT=ne.


### Rozhodnutí
- Míla pověřil Adama doplněním dat, výběrem/generováním ilustrací i c+p
  bez mezidotazů a bez schvalovací galerie. Výběr významů je v reportu.

### Další krok
- Načíst aktualizovaná data v používané aplikaci; vzdálenou iCloud synchronizaci
  a skutečný iPhone běh tento místní audit nepotvrzuje.

### Navrhované další kroky
- Další obsah doplňovat stejným společným auditem tří slovníků.

### Rizika a technický důkaz
- Před zápisem soukromé zálohy a kontrola vstupních snímků. Janina data mimo Git.
- Kód aplikací se neměnil. Dřívější otevřené náměty, např. Linux poslech
  a reload CSV po konfliktu, nejsou tímto datovým krokem vyřešené.
- Podrobnosti: `reports/vocabulary_fr_it_refresh_2026_09_13.md`.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Vocabulary IT

Pracovni proud: `project-vocabulary-it`
Typ: `Project`
Rezim: `paused`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-04 19:15 CEST – AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru

Hotovo:
- AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- V Pythonistě krátce ověřit tlačítka 20, 50 a jejich vypnutí

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-vocabulary-it`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-07 14:07 CEST – Funkční stav IT aplikace je potvrzený a proud je pozastavený

Hotovo:
- Míla potvrdil funkční Last 20/50 v AppIT.
- Lokální VocabularyIT se po opravě Tk runtime spouští z Cockpitu správně.

Rozhodnutí:
- Původní pokyn k ručnímu testu je splněný; proud je nyní pozastavený.

Další krok:
- Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat společný audit dat.

Navrhované další kroky:
- Bez nového věcného požadavku nic dalšího neměnit.

Technický důkaz:
- Filtry: commit `b2355b7`.
- Oprava lokálního spuštění: commit `ae67bea`.
- Následné potvrzení Míly v reálném používání.

### 2026-09-13 10:12 CEST – Slovíčka a ilustrace z NewWords.txt

Hotovo:
- Doplněno 8 IT položek z NewWords.txt; celkem 471 slovíček.
- Již existující hesla bez duplicit; usi má i infinitiv usare,
  vinti příklad ve správném množném čísle, quelle ukazovací význam.
- Dříve potvrzené Last 20/50/HT a lokální Tk spuštění zůstávají beze změny.
- Společný audit: FR Míla 234 / FR Jana 413 / IT Míla 471 řádků,
  žádné chybějící obrázky v desktopových ani Pythonista resolverech.
- Doplněno také devět starších Janiných českých vazeb chybějících v Pythonistě.
- Osm nových ilustrací WebP do 250 kB; kanonické české abecední mapování
  1 082 položek (+27) je bajtově shodné s Janinou sdílenou kopií.
- Šest testů kanonického mappingu i rychlá statická brána prošly; původní řádky Míly včetně L/HT
  zachované. Všechny nové položky mají Sentence/SentenceT a L=ne, HT=ne.


Rozhodnutí:
- Realizován výslovný pokyn Míly od A do Z včetně generování, přiřazení
  a c+p. Kontrola ilustrací delegovaná Adamovi; galerie se nevyžaduje.

Další krok:
- Načíst nová data v používaných aplikacích; vzdálený přenos a iPhone retest
  se tímto místním ověřením nepotvrzují.

Navrhované další kroky:
- Další dávku opět ověřit napříč třemi slovníky.

Technický důkaz:
- Původní CSV hodnoty a mapovací vazby zachované, soukromé zálohy ověřené.
- Skutečné desktopové/Pythonista resolvery, dekódování Pillow, SHA-256 obou
  obrazových kopií, shoda mappingů a úplnost Janiných vět prošly.
- Report `reports/vocabulary_fr_it_refresh_2026_09_13.md`; soukromé důkazy
  `vocabulary_refresh_20260913/audit_result.json` a `apply_manifest.json`.
- Riziko: stav na vzdáleném iPhonu/Macu závisí na následném přenosu dat.
