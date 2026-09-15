# C01a — malý offline audio prototyp

**Stav: ROZPRACOVÁNO / přehrávání potvrzeno, Camino Test nainstalován/spuštěn, metadata 5 vzorků ověřena; první odmítnutí bez nahrávání potvrzeno, čeká návrat po povolení a vědomý Start (T025), 2026-09-15 21:39 CEST.** Zadání vytvořeno v C00.
Implementace, 32 testů logiky/syntetického audia a nově 2 UI testy v simulátoru hotovy; přímá iOS kompilace
prošla. Standardní nepodepsaný Xcode build ověřen 15. září v 15:01 CEST;
nově podepsaný build a strict podpis OK. Instalace na telefon prošla a Míla potvrdil otevření; dílčí fyzické zkoušky uživatelsky prošly, úplná přejímka čeká.
[Aktuální report](../docs/C01a_AUDIO_PROTOTYPE_REPORT.md) má přednost před
historickými vstupními předpoklady C00 níže.
Aktualizace předpokladů: Xcode 26.3 je nainstalovaný, první nastavení dokončené
a iPhone SDK 26.2 ověřené; viz [instalační doklad](../docs/XCODE_INSTALLATION.md).
Párování, Developer Mode a DDI byly 15. září přímo ověřeny. Podpis i instalace již ověřeny; otevření potvrdil Míla.
Výsledky dílčích fyzických testů a zbývající mezery jsou v aktuálním reportu. Míla zadal pokračování vývoje;
C01b, nákup členství a placené zpracování zadány nejsou.

Cílové zařízení následně potvrzené Mílou: **iPhone 14 Plus, iOS 26.6.1**.
Nejde o provedenou fyzickou zkoušku; technický build iOS, párování, podpis,
instalace a audio zůstávají NEOVĚŘENO. Model a verzi znovu nezjišťovat dotazníkem.

## Cíl

Na skutečném iPhonu po vědomém Start zachytit krátký Komentář nebo Úvahu,
ukázat skutečný vstup a signál, pomocí Stop bezpečně dokončit místní soubor
a lokálně jej přehrát bez serveru, internetu, GPS nebo AI. Nejde o celé Camino.

Přečíst společné/projektové AGENTS, v0.4 zejména F05, F08, F15–F18, F42,
F44 a F73, scénáře T015/T017/T025, [audit C00](../docs/ENVIRONMENT_AUDIT.md)
a [rozhodnutí](../docs/DECISIONS.md). U01–U11 neotevírat znovu.

## Vstupní podmínky a dvě oddělené úrovně důkazu

| Úroveň | Co potřebuje | Co lze tvrdit |
|---|---|---|
| A — automatizovatelná příprava | Dostupný Swift, nové oprávnění k implementaci, samostatný balíček logiky a mock adaptéry | Výsledek konkrétních testů logiky na Macu; žádný PASS mikrofonu nebo iPhonu. |
| B — nativní integrace a přejímka | Plný kompatibilní Xcode a iPhone SDK, dostatek místa, skutečný cílový telefon/iOS, vyřešený signing a uživatelem připravený Developer Mode | Build/install/run a skutečné fyzické výsledky, odděleně zaznamenané. |

Při C00 je k dispozici pouze spuštěný Swift 6.2.4 CLI; balíček ani jeho testy
ještě neexistují. Xcode/iOS SDK a fyzické zařízení pro přejímku nejsou ověřeny.
Domácím serverem je podle Mílova upřesnění tentýž vývojový MacBook.
Nepřipravené serverové služby Camino **nejsou vstupní blokátor ani jedné úrovně**.
Pokud B chybí, lze po zadání dokončit A, ale celý C01a zůstane **BLOCKED**.
Nenahrazovat telefon browserem, mikrofonem Macu nebo úspěšným simulátorem.

## Povolený budoucí rozsah změny

- Jeden samostatný prototypový iOS target se SwiftUI obrazovkou, bez externích
  závislostí. Návrh umístění `prototypes/audio/`; názvy zde nejsou vytvořené soubory.
- Samostatná čistá Swift logika a testy; iOS audio adaptér podle ADR-C00-03.
- Prototypová lokální evidence: jedinečné ID, typ Komentář/Úvaha, čas zahájení,
  skutečně zaznamenaná délka, stav a relativní soubor. Bez celého modelu Moment/Trip.
- Výsledek v novém reportu s verzí kódu/nástrojů, příkazy, skutečnými výsledky
  a neprovedenými zkouškami. Originální balíček v0.4 zůstává neměnný.

## Chování prototypu

1. **Připraveno:** viditelný typ, Start a seznam vlastních testovacích nahrávek.
   První povolení mikrofonu neaktivuje záznam; po návratu je třeba vědomý Start.
   Pozdější Start s již uděleným oprávněním začne přímo. Odmítnutí má vysvětlení
   a cestu zpět, nikoli smyčku žádostí.
2. **Připravuji mikrofon:** blokovat dvojitý Start. Audio session aktivovat
   vědomě; pro kombinaci záznamu a poslechu použít odpovídající kategorii
   `playAndRecord`. Aktivní vstup získat z `currentRoute.inputs`, ne ze seznamu
   spárovaných sluchátek. V první přejímce stačí vestavěný mikrofon.
3. **Nahrávám:** teprve po úspěšném spuštění recorderu a postupu jeho mediálního
   času. Zobrazit skutečnou dobu a aktualizované měření úrovně. Animace nebo
   nástěnné hodiny nejsou důkaz. Ticho je platné audio; nulový signál sám nesmí
   být označen jako porucha. Zastavený postup záznamu řešit pravdivým stavem.
4. **Ukončuji:** po Stop nepovolit další nahrávání nebo přehrávání, dokud není
   znám výsledek uzavření. Ověřit dokončení recorderu, existenci a nenulovou
   přehratelnou délku souboru, pak dokončit prototypovou evidenci.
5. **Uloženo v telefonu:** pouze po předchozím dokončení. Nabídnout lokální
   Play/Stop; přehrávání se samo nespouští. Rozlišit chybu dekódování od chybějícího
   souboru. Během nahrávání nelze zapnout soupeřící player nebo další recorder.
6. **Chyba/přerušeno:** žádné automatické znovuspuštění mikrofonu. Při ztrátě
   session nebo vstupu se pokusit ukončit dostupný záznam, ukázat skutečnost.
   V C01a lze po vyřešení spustit nový samostatný záznam; pokračování téže
   session s mezerou a plná obsluha přerušení patří do C01b.

`AVAudioRecorder` umí soubor, úroveň a mediální čas; stop uzavírá soubor.
Samotný návrat `true` ze startu není fyzická přejímka slyšitelnosti.
[Apple: AVAudioRecorder](https://developer.apple.com/documentation/avfaudio/avaudiorecorder).
Úrovně nejprve aktualizovat; nezobrazovat staré hodnoty jako živý signál.
[Apple: updateMeters](https://developer.apple.com/documentation/avfaudio/avaudiorecorder/updatemeters()).

## Soubory, chyby a obnova

- Krátké vzorky zapisovat do trvalého prostoru prototypové aplikace, mimo cache,
  Fotky, repozitář a automaticky sdílená úložiště. Po restartu aplikace jsou
  dříve dokončené vzorky dohledatelné a lze je přehrát.
- Pro každý pokus použít novou nekolidující souborovou identitu. Existující
  nahrávku nikdy nepředat jako cíl `prepareToRecord`: toto API může soubor
  přepsat. Kontrola kolize musí předcházet přípravě recorderu.
  [Apple: prepareToRecord](https://developer.apple.com/documentation/avfaudio/avaudiorecorder/preparetorecord()).
- PCM/CAF z ADR-C00-03 je pracovní experimentální profil. Uložit skutečné
  parametry; změnu odůvodnit měřením. Žádné tiché přepnutí mikrofonu či kvality.
- Chyba startu, zápisu, dokončení nebo dekódování nesmí skončit falešným Uloženo.
  Zachovat již existující soubory i případný neúplný nový soubor; nic automaticky nemazat.
- Restart prototypu nikdy nespustí mikrofon. Neúplný soubor není vydáván za
  bezpečně zachráněnou nahrávku; zachovat jej a označit k vyhodnocení.
- C01a nemá segmentový journal ani garanci obnovy rozpracované části. To jsou
  výstupy C01c. Úspěšný krátký soubor nesmí být popisován jako splněné F18.
- Chyby místa testovat injektovanou chybou adaptéru, ne zaplněním uživatelova disku.

## Automatizované ověření A — budoucí testy, nyní NEPROVEDENO

| Test prototypu | Očekávaný důkaz |
|---|---|
| Dvojitý Start a rychlý Start/Stop | Nejvýše jeden recorder; deterministické dokončení i při opožděné aktivaci. |
| Zamítnuté/právě udělené oprávnění | Žádná aktivace bez nové vědomé akce po prvním povolení. |
| Neúspěšný start a nepostupující záznam | Nevznikne falešné Nahrávám nebo Uloženo; ticho samo není porucha. |
| Aktivní skutečný vstup vs. pouze připojená sluchátka | UI odpovídá hodnotě adaptéru, nepředpokládá hardware podle názvu. |
| Kolize názvu a chyba zápisu/uzavření/evidence | Staré soubory beze změny, žádný tichý přepis a žádné potvrzení neúspěšného zápisu. |
| Souběh přehrávání a záznamu | Nemohou běžet dvě soupeřící operace. |
| Restart a dokončený/neúplný vzorek | Dokončený dohledatelný, neúplný pravdivě označený, mikrofon vypnutý. |
| Komentář a Úvaha | Typ se zachová bez odvozování od délky; žádný povinný název. |

Mock adaptéry neotevírají mikrofon, síť ani AI. Automatické integrační
kontroly použijí malé syntetické audio a dočasné izolované úložiště.
Po vytvoření balíčku spustit jeho skutečný `swift test`; přesný příkaz, adresář,
verzi kompilátoru a počty zapsat do reportu. Neuvádět nyní vymyšlené počty PASS.
Po zpřístupnění Xcode zvlášť ověřit kompilaci iOS targetu. Testování čistého
Swift balíčku na Macu nenahrazuje kompilaci AVFoundation adaptéru pro iOS.

## Fyzické ověření B — pouze cílový telefon

Testovací řeč bude neutrální, výslovně určená pro zkoušku, bez osobních údajů;
například krátké počítání a známá neosobní věta. Nahrávky zůstanou v telefonu.
Report obsahuje délku, hash/velikost a výsledek poslechu, nikoli hlasový obsah.

| Vazba | Postup | Přijetí |
|---|---|---|
| Příprava pro T079 | Zapsat model, iOS/build, Xcode/SDK, verzi prototypu, typ podpisu a expiraci; skutečně instalovat a spustit. | Není potřeba veřejný endpoint; plný T079 upgrade/migrace tím ještě neprošel. |
| T015 — prototypový rozsah | Bez sítě nahrát 30–60 s Komentář, poté samostatně Úvahu; Stop a přehrání celých vzorků. | Správný typ, čas, slyšitelný začátek i konec, bez povinného názvu; integrace Momentu až C04. |
| T017 | Vestavěný mikrofon, viditelné označení skutečné route a reakce signálu na testovací řeč. | Hlas slyšitelný, vstup správně označen; sluchátka nejsou podmínkou. |
| T025 | Na samostatné testovací instalaci nejprve odmítnout mikrofon, později jej uživatel povolí. | Jasná omezená funkce; návrat z nastavení ani prvního dialogu sám nenahrává. |
| Doplněk C01a | Po Stop aplikaci ukončit a znovu otevřít; přehrát oba dokončené vzorky. | Soubory zůstaly, mikrofon sám nezačal. Nejde o test pádu během zápisu. |

Pro každý výsledek: ID, verze, zařízení, předpoklady, kroky, skutečnost,
důkaz, datum a PASS/FAIL/BLOCKED/NEPROVEDENO. Poslech provádí člověk;
samotný dekodér nebo nenulová velikost nesmějí být označeny jako slyšitelný hlas.
Bez telefonu se B označí BLOCKED a všechny neprovedené scénáře zůstanou viditelné.

## Co do C01a nepatří

Pokračování pod zámkem, 30minutový běh, sluchátka/chůze, hovory a pokračování
s mezerami jsou C01b (T016, T018–T021, T024, T059). V C01a nepřidávat background
audio jako neověřený příslib; při odchodu do pozadí bezpečně ukončit krátký vzorek.
Bezešvé uzavírání částí, journal a testy pádů během zápisu jsou C01c (T022/T023/T061).
Žádná AI, síť, GPS, kamera, galerie, rodinné sdílení, produkční zálohy,
finální datový model, migrace nebo veřejná distribuce.

## Podmínka přijetí a zastavení

Přijatý C01a vyžaduje skutečně prošlou A **i** B, jasně vymezenou prototypovou
část T015/T017/T025, build/install/run a poslech obou místních vzorků. Žádný
otevřený FAIL vedoucí ke ztrátě či přepsání souboru nebo nevyžádanému mikrofonu.
Samotná A je dílčí výsledek, celý C01a zůstává BLOCKED do fyzické zkoušky.
Výsledek neuzavírá G0/G1 ani neprohlašuje aplikaci za připravenou na pouť.

Předat změněné soubory, skutečně spuštěné příkazy a testy, stav hardwarových
zkoušek, rizika a jeden další krok. Poté zastavit; C01b automaticky nezahajovat.
