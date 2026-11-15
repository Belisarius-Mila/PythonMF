<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-11-15 20:54 CET
- Míla schválil webový port podle Vocabulary EN a zahájil bod1 plánu.
- Bod1 místně hotový:471 stabilních identit;18 témat a ostatní metadata jsou návrhy.
- Uzavřený snímek777 souborů/761 obrazů; původní CSV, rody, L/HT a EN zachované.
- Revizní fronta112 prioritních karet, všechny obrazové vazby čekají na bod2.
- Dále: revize významů a konkrétních ilustrací podle věty, potom export/galerie/audio.
- Vývoj lokální, bez nového publikování; souběžný main zachovaný.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Vocabulary IT

Nazev: Vocabulary IT
Pracovni proud: project-vocabulary-it
Typ: Project
Priorita: 2
Stav: rozpracovane — webovy port, bod1 mistne hotovy
Pripomenout pri startu: ne
Datum: 2026-11-15 20:54 CET

Co se resilo:
Schválený webový port IT podle EN, první bod: katalog významů a uzavřené vstupy.

Co je hotove:
-471 trvalých identit a návrhy metadat,777 zmrazených souborů, prioritní revizní fronta.

Co neni hotove:
- Redakční revize, obrazové vazby, exporter/miniatury, IT galerie/profily/audio a vydání.

Dalsi krok:
Bod2: revize významů a přesné obrazy podle věty; katalog zatím obsahuje návrhy.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

### Automatický checkpoint 2026-08-04 19:15 CEST

- Pracovní proud: `project-vocabulary-it`
- Hotovo: AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `MBSoft/AppIT.py`
- Commit: `Add Last 20 and 50 filters to AppIT`
- Další krok: V Pythonistě krátce ověřit tlačítka 20, 50 a jejich vypnutí

### Auditní dorovnání 2026-08-07 14:07 CEST

- Hotovo: Míla potvrdil funkční Last 20/50 v AppIT i funkční lokální VocabularyIT z Cockpitu.
- Rozhodnutí: Původní pokyn k ručnímu testu je splněný; proud je nyní pozastavený.
- Další krok: Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat společný audit dat.
- Navrhované další kroky: Bez nového věcného požadavku nic dalšího neměnit.
- Technický důkaz: Commity `b2355b7` a `ae67bea`; následné potvrzení Míly v reálném používání.

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


### 2026-11-15 20:54 CET — Schválený webový port: bod1, identity a zmrazené vstupy

Hotovo: Na konec původní analýzy v Downloads je připsaný podrobný osmibodový
plán, původní text včetně Mílových SOUHLAS zachovaný. Místně založený katalog
všech471 původních významů s trvalými vit-0001–0471 a návrhy18 témat, slovních
druhů, typu učiva a tří vlastních stupňů obtížnosti. Všech471 zůstává aktivních.
Soukromý uzavřený snímek777 vstupních souborů včetně761 plně dekódovaných obrazů,
celkem121703729 bajtů; kanonické i zmrazené vstupy prošly přesnou kontrolou.
Připravená konkrétní prioritní fronta112 karet, nikoli112 prokázaných chyb.

Rozhodnutí: Míla schválil analýzu, doplnění plánu a zahájení prvního bodu.
Prázdné IT profily A–D, hotový poslech slov i vět, časování samostatně později.
ID byla přidělená jednou; další čtení používá přesnou NFC IT/CZ dvojici a
výslovné aliasy, nikoli Order. Zachované odlišné významy a konkrétní tvary.
Nová metadata jsou proposals/needs-review, žádné tvrzení o ověřeném CEFR.

Další krok: Bod2 — redakční revize významů a přesné obrazové vazby podle
vět, začít16 rozpory resolverů a piacere/perché/stare, potom tvary a rody.

Navrhované další kroky: Bezpečný export s miniaturami; vlastní IT galerie
a profily; samostatně odsouhlasený zvukový vzorek a knihovna; přejímka/p+n
podle celého plánu. Žádný modelový pomocník ani zvuková výroba nyní neběží.

Technický důkaz:30 cílených testů včetně nových identit a validační domény PASS.
Reverzní pořadí i jiné Order zachovají471 UID; neznámá/dvojitá identita selže,
diakritika a case se neslévají. CSV, rody, L/HT, mapping, obrázky a EN předloha
zůstaly bajtově zachované. Navržených460 Slovíček a11 Interakcí; žádný idiom
a žádné rozdělení/skrytí nyní. Obrázkové vazby všech471 pending-review.
Soukromé důkazy vocabulary_it_foundation_20261115, finální programová brána
v gate.json/gate.log. Worktree má745 obrazů; chybějících16 je bezpečně v úplném
snímku. Vlastní lokální brána se porovnává proti společnému77b5f652, protože
origin mezitím pokročil Willovými bcc548fe/0f059c3e; žádný merge/rebase/push
ani zásah do souběžného main. Nová webová aplikace ani IT audio dosud nejsou
implementované/nasazené. Původní CSV a původní desktop/Pythonista fungují dál.
