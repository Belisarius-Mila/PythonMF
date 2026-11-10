<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- 2026-11-10: Lokálně hotové části 1–3 nové šestky, čtyři ilustrace a 25 přesných EN replik / pevných MP3. Druhý obraz navazuje na třetí část Jumping Practice. Obraz 03 zobrazuje první tři věty; od Bunnyho otázky (4/8) přechází na obraz 031 s Freddiem ve vodě. Repeat zachová obraz, Again vrací začátek šestky.
- Třetí část přidává 8 unikátních Azure požadavků / 458 SSML znaků, limit 500, tempo −10 %. Freddie Guy a Dotty Jenny podle původní hlasové mapy. Všech 23 původních podkladů a obě dřívější raw účtenky zůstaly byte-identické; žádný starší požadavek se neopakoval.
- Ověření třetí části: 59 cílených kontrol PASS, po posledním CSS doplnění 21 relevantních testů PASS; dekódování 25/25, mirrory shodné, lokální HTTP 39/39 přesné. Plná brána třetí části: 2974 testů OK (5 SKIP), 620,446 s unit. Ruční přejímka obou nových obrazů a hlasů na Mílově zařízení včetně fyzického iPhonu zůstává otevřená.
- První p+n proběhlo JEDNOU Terrou pro main fee535e5, job `4b261f77c13a77e845684bbbd90cc876`: brána 3412 PASS, push confirmed, Pages run `42839271179` build success / deploy failure po 600000 ms při syncing_files. Historická účtenka attention / deployment uncertain, HTML po zrušení HTTP 404 v 16:10 CET. Není to aktuální veřejná přejímka. Nový pokus nebyl spuštěný ani schválený pokračováním třetí částí.
- Druhá část je uložená v `3cdc5c26`; třetí je uložená ve vlastním místním checkpointu. Obě jsou mimo zmrazený první balíček. Do main se nyní nezasahuje. Willovo WIP zůstává zaparkované ve stashi `550024e17da59eb258556f5d3f0979650d5a4d30` a ověřené privátní záloze; při zahájení tohoto vývoje byly oba checkouty čisté.
- Data servisní commit `06c34051` pouze zaznamenal již dříve provedený úklid původní šestky; do main NEPŘEBÍRAT podruhé. Neprovádět reset, pop/drop Willova stashe ani nové nasazení bez odpovídajícího pokynu.
- Další krok: místní přejímka třetí části; další vývoj nebo samostatně autorizované vydání podle Mílova pokynu. Report `reports/mmtx_scene06_picture3_20261110.md`; původní release report se nepřepisuje.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: MMTX

Pracovni proud: `project-mmtx`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-07-21 07:06 CEST – Živý zapisovací pilot MMTX fáze 4.5 prošel

Pracovní proud: `project-mmtx`.

Milník: Živý zapisovací pilot MMTX fáze 4.5 prošel

Důkaz: plná Cockpit brána: 965 testů, 281.5 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Ověřit čistý main, synchronizaci legacy workspaces a vznik kanonického MMTX handoffu a TVBCP

### 2026-08-12 19:17 CEST – Samostatný prototyp Harry–Benji

Hotovo: Vznikl samostatný prototyp scény se schváleným obrazovým základem,
dvojjazyčným režimem, systémovým hlasem, bezpečným opakováním poslední věty,
výběrem Benjiho a prvním úkolem `YES/NO`. Živá třetí scéna zůstala nedotčená.

Rozhodnutí: První verze používá systémový český hlas a zůstává odděleným
prototypem, dokud neprojde ručním ověřením na Macu a iPhonu.

Další krok: Ručně ověřit vzhled, ovládání a systémové hlasy na Macu a iPhonu.

Navrhované další kroky: Po ověření doplnit výslech Bunnyho, Fiony, Sunnyho a
Bruna; potom přidat počítání pěti ovcí a otevření branky.

Technický důkaz: Prošly 3/3 cílené testy, JavaScript syntaxe a
`git diff --check`. PNG má kanonické rozměry 1672 x 941 a jeho kontrolní otisk
odpovídá schválenému private kandidátu.

### 2026-08-12 21:13 CEST – Benji v prototypu upřednostňuje Andrewa a používá pouze mužské anglické alternativy

Hotovo:
- Benji v prototypu upřednostňuje Andrewa a používá pouze mužské anglické alternativy
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Harryho hlas zůstává beze změny; Benji má Andrewa jako první volbu a nesmí přejít na ženský hlas

Další krok:
- Poslechnout Benjiho hlas v prototypu na iPhonu a Macu

Navrhované další kroky:
- Po poslechovém ověření připravit pevné Andrew MP3 pro stejný hlas na všech zařízeních
- Potom pokračovat výslechem Bunnyho, Fiony, Sunnyho a Bruna se schválenými hlasy

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 07:18 CEST – Benji v prototypu používá čtyři pevná Andrew MP3 se spolehlivým přehráváním i fallbackem

Hotovo:
- Benji v prototypu používá čtyři pevná Andrew MP3 se spolehlivým přehráváním i fallbackem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Benjiho anglické repliky používají pevný hlas en-US-AndrewNeural; Harryho a české systémové hlasy zůstávají beze změny

Další krok:
- Poslechnout celý prototyp na iPhonu a Macu a potvrdit charakter i hlasitost Benjiho hlasu

Navrhované další kroky:
- Po poslechovém schválení pokračovat výslechem Bunnyho, Fiony, Sunnyho a Bruna

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 07:57 CEST – Prototyp pokračuje druhým výslechem Bunnyho s interaktivní otázkou a pevným hlasem Ana

Hotovo:
- Prototyp pokračuje druhým výslechem Bunnyho s interaktivní otázkou a pevným hlasem Ana
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Druhý výslech se týká mrkve v zahrádce; Bunny používá en-US-AnaNeural a Harry po odpovědi ponechá branku zavřenou

Další krok:
- Poslechnout druhý výslech na iPhonu a Macu a ověřit Bunnyho hlas i tempo

Navrhované další kroky:
- Přidat třetí výslech se Sunnym a podezřením na ořechy
- Potom doplnit výslech Fiony a Bruna, počítání ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 11:20 CEST – Vznikly dvě poslechové ukázky Benjiho s hlasem klonovaným podle první scény

Hotovo:
- Vznikly dvě poslechové ukázky Benjiho s hlasem klonovaným podle první scény
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Nové Benjiho věty nejprve porovnáme jako F5 kandidáty podle zamčené reference z první scény

Další krok:
- Poslechnout oba kandidáty a rozhodnout, zda jimi nahradit Andrewův hlas

Navrhované další kroky:
- Po schválení vygenerovat zbývající dvě Benjiho věty stejným F5 nastavením
- Nahradit všechny čtyři Benjiho nahrávky v prototypu a znovu ověřit celý průchod

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 18:16 CEST – Čtyři výslechy mají připravené vlastní obrazové scény s příslušným zvířátkem v popředí

Hotovo:
- Čtyři výslechy mají připravené vlastní obrazové scény s příslušným zvířátkem v popředí
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Samostatné obrazy výslechů budou patřit Benjimu, Bunnymu, Sunnymu a Fioně; Bruno zůstává členem skupiny

Další krok:
- Zapojit obrazy do jednotlivých fází dialogu a připravit třetí výslech Sunnyho

Navrhované další kroky:
- Doplnit přepínání obrazů mezi výslechy
- Navrhnout a implementovat dialog Harry–Sunny o ořeších
- Poté doplnit výslech Fiony, počítání pěti ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.7 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 22:50 CEST – Sérii výslechů doplnil pátý obraz s Brunem a Harrym

Hotovo:
- Sérii výslechů doplnil pátý obraz s Brunem a Harrym
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Harry vyslechne také Bruna kvůli podezření na podhrabání ohrady

Další krok:
- Zapojit pět obrazů do jednotlivých výslechů prototypu

Navrhované další kroky:
- Doplnit dialog Harry–Bruno
- Dokončit výslechy Sunnyho a Fiony
- Po pěti výsleších přidat počítání ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-13 23:03 CEST – Opravený Brunův výslech nyní zachovává celou skupinu včetně jasně viditelného Benjiho

Hotovo:
- Opravený Brunův výslech nyní zachovává celou skupinu včetně jasně viditelného Benjiho

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Brunova scéna musí v pozadí zobrazovat Bunnyho, Fionu, Sunnyho i Benjiho

Další krok:
- Použít opravenou verzi při zapojení obrazů do prototypu

Navrhované další kroky:
- Po vizuálním potvrzení lze původní verzi ponechat jen jako historického kandidáta
- Zapojit všech pět schválených obrazů do výslechů

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-14 07:42 CEST – Druhý výslech nyní používá vlastní Bunnyho obraz a odpovídající klikací místa

Hotovo:
- Druhý výslech nyní používá vlastní Bunnyho obraz a odpovídající klikací místa
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Bunnyho obraz se přepne ještě před Harryho úvodní otázkou druhého výslechu

Další krok:
- Ručně ověřit přechod obrazu a klepnutí na Bunnyho na iPhonu nebo Macu

Navrhované další kroky:
- Po vizuálním ověření připravit a zapojit třetí výslech Sunnyho
- Později zapojit obrazy Fiony a Bruna

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-14 09:09 CEST – Prototyp nyní obsahuje třetí výslech Sunnyho s vlastním obrazem a pevným hlasem

Hotovo:
- Prototyp nyní obsahuje třetí výslech Sunnyho s vlastním obrazem a pevným hlasem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Sunny používá kanonický hlas en-US-MichelleNeural

Další krok:
- Ručně ověřit třetí výslech, Sunnyho hlas a klikací místo na iPhonu nebo Macu

Navrhované další kroky:
- Zapojit čtvrtý výslech Fiony
- Poté doplnit Brunův výslech, počítání ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-14 10:01 CEST – Prototyp nyní obsahuje čtvrtý výslech Fiony s vlastním obrazem a pevným hlasem

Hotovo:
- Prototyp nyní obsahuje čtvrtý výslech Fiony s vlastním obrazem a pevným hlasem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Fiona používá kanonický hlas en-US-JennyNeural

Další krok:
- Ručně ověřit Fionin výslech, hlas a klikací místo na iPhonu nebo Macu

Navrhované další kroky:
- Zapojit poslední výslech Bruna s opraveným obrazem obsahujícím Benjiho
- Poté doplnit počítání pěti ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-14 10:56 CEST – Fionin blikající box nyní spolehlivě přijímá první klepnutí i v překryvu s ostatními postavami

Hotovo:
- Fionin blikající box nyní spolehlivě přijímá první klepnutí i v překryvu s ostatními postavami
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Ověřit Fionin výslech jedním klepnutím na iPhonu nebo Macu

Navrhované další kroky:
- Zapojit poslední výslech Bruna
- Poté doplnit počítání pěti ovcí a otevření branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-14 11:48 CEST – Prototyp nyní obsahuje Brunův pátý výslech s vlastním obrazem a hlubším hlasem

Hotovo:
- Prototyp nyní obsahuje Brunův pátý výslech s vlastním obrazem a hlubším hlasem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Ručně ověřit Brunův hlas a klikací oblast v nasazeném prototypu

Navrhované další kroky:
- Navázat závěrečným počítáním pěti ovcí a otevřením branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-15 11:11 CEST – Závěr prototypu nabízí slovníček 22 nových slov s anglickou výslovností a volitelnou češtinou

Hotovo:
- Závěr prototypu nabízí slovníček 22 nových slov s anglickou výslovností a volitelnou češtinou
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Slovníček se zpřístupní až po pátém výslechu a český překlad se řídí režimem EN nebo EN + CZ

Další krok:
- Ručně ověřit slovníček, jeho rozložení a výslovnost na iPhonu

Navrhované další kroky:
- Navázat závěrečným počítáním pěti ovcí a otevřením branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-16 17:58 CEST – Harry se představí před prvním výslechem a další repliky se přehrávají jednotlivě až po stisknutí Next

Hotovo:
- Harry se představí před prvním výslechem a další repliky se přehrávají jednotlivě až po stisknutí Next
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Každá další věta ve výslechu se aktivuje tlačítkem Next

Další krok:
- Ručně ověřit tempo a rozložení tlačítka Next na iPhonu nebo Macu

Navrhované další kroky:
- Po živém ověření pokračovat počítáním pěti ovcí a otevřením branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-16 22:15 CEST – Harry po posledním výslechu dovolí přátelům pokračovat otevřenou brankou

Hotovo:
- Harry po posledním výslechu dovolí přátelům pokračovat otevřenou brankou
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Závěrečná replika používá přirozenou angličtinu „The gate is open for you, friends!“ a zůstává samostatným krokem Next

Další krok:
- Ověřit závěrečnou repliku, hlas a přechod do dokončené scény na iPhonu

Navrhované další kroky:
- Po ověření navázat počítáním pěti ovcí a skutečným otevřením branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-17 22:23 CEST – Repeat nyní zopakuje každou právě zobrazenou větu bez posunutí nebo přerušení dialogu

Hotovo:
- Repeat nyní zopakuje každou právě zobrazenou větu bez posunutí nebo přerušení dialogu
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Repeat je replay-only ovládání aktuální věty a nesmí měnit tok tlačítka Next

Další krok:
- Ručně ověřit Repeat a Next v celém výslechu na iPhonu nebo Macu

Navrhované další kroky:
- Po živém ověření pokračovat počítáním pěti ovcí a skutečným otevřením branky

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-25 13:17 CEST – MMTX má samostatné přání Jane s pozměněnými texty, anglickou výslovností jména a vlastními zvukovými stopami.

Hotovo:
- MMTX má samostatné přání Jane s pozměněnými texty, anglickou výslovností jména a vlastními zvukovými stopami.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Jméno Jane se v anglickém i českém audia vyslovuje anglicky jako džejn; původní Kate birthday zůstává beze změny.

Další krok:
- Ručně ověřit hlasy a výslovnost Jane na iPhonu nebo Macu a poté použít ovládací prvky Cockpitu pro checkpoint a nasazení.

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-29 17:05 CEST – Pevná MP3 knihovna Harryho scény dorovnána do MMTX

Hotovo:
- Harryho scéna přehrává 136 pevných anglických a českých dialogových a slovníkových stop bez `speechSynthesis`.
- Commit `f1499b1` je na GitHubu, Cockpit jej potvrzuje jako nasazený a veřejná Pages publikace je hashově shodná.

Rozhodnutí:
- Tento milník je součástí MMTX. Automatický checkpoint vytvořený pod aktivním proudem Linux zůstává historickou auditní stopou, nikoli aktuální věcnou autoritou.

Další krok:
- Ručně projít scénu 3 → Harry na Linuxu a Macu a ověřit `Next`, `Repeat`, pořadí jazyků, přirozenost hlasů a tempo.

Navrhované další kroky:
- Případně vyměnit pouze konkrétní problematické stopy.
- Další příběhový vývoj zahájit až po otevření workstreamu MMTX.

Technický důkaz:
- Cílené testy 5/5; vzdálená Cockpit Quality Gate 1468/1468; smoke 5/5.
- Pages run `33259207533` uspěl a veřejný HTML, JavaScript, manifest i vzorky obou jazykových MP3 odpovídají `f1499b1`.

### 2026-08-29 17:30 CEST – Linuxové přizpůsobení MMTX prakticky potvrzeno

Hotovo:
- Míla prakticky vyzkoušel aktuální MMTX na Linux PC a potvrdil, že pevné MP3 fungují dobře.
- Linuxový retest Harryho scény je uzavřený bez známého blokátoru.

Rozhodnutí:
- Pevné MP3 řízené manifestem zůstávají kanonickým multiplatformním řešením bez systémového nebo prohlížečového `speechSynthesis`.
- Další vývoj bude pokračovat v Human–Adam proudu `project-mmtx`.

Další krok:
- Pokračovat dalším vývojovým krokem MMTX; při jeho dokončení aktualizovat tento TVBCP i příslušný handoff.

Navrhované další kroky:
- Retest na Macu provést jen tehdy, pokud bude potřeba ověřit konkrétní rozdíl platformy.
- Při změně dialogového textu společně regenerovat MP3, aktualizovat manifest a ověřit shodu produkční kopie se zrcadlem MMTX.

Technický důkaz:
- Praktické potvrzení Míly na Linux PC doplňuje cílené testy 5/5, vzdálenou Cockpit Quality Gate 1468/1468, smoke 5/5 a úspěšný Pages run `33259207533` s hashovou shodou zveřejněných souborů.

### 2026-08-29 18:13 CEST – Scéna 2 používá 55 pevných anglických a českých stop řízených manifestem a funguje bez systémového hlasu.

Hotovo:
- Scéna 2 používá 55 pevných anglických a českých stop řízených manifestem a funguje bez systémového hlasu.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Existující kvalitní MP3 zůstávají zachované; nové české stopy používají Vlastu a scéna nemá speechSynthesis fallback.

Další krok:
- Prakticky projít a poslechnout celou scénu 2 na Linuxu.

Navrhované další kroky:
- Po poslechovém ověření pokračovat stejným způsobem scénou 3.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-29 19:03 CEST – Scéna 3 nyní používá úplnou pevnou anglickou a českou audio knihovnu řízenou manifestem bez systémového hlasu.

Hotovo:
- Scéna 3 nyní používá úplnou pevnou anglickou a českou audio knihovnu řízenou manifestem bez systémového hlasu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Existující kvalitní anglické MP3 zůstávají zachované; nové české stopy používají Vlastu a scéna nemá speechSynthesis fallback.

Další krok:
- Prakticky projít a poslechnout celou scénu 3 na Linuxu.

Navrhované další kroky:
- Po poslechovém ověření pokračovat auditem pevného audia hlavního portálu.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-29 19:52 CEST – Scény 2 a 3 nasazeny na GitHub Pages

Hotovo:
- Pages workflow publikoval commit `933834f`; scény 2 a 3 s pevnými MP3 jsou veřejně dostupné.

Rozhodnutí:
- Push a Pages nasazení jsou dva samostatné kroky a produkční stav se potvrzuje až deploymentem a veřejnou kontrolou.

Další krok:
- Prakticky projít a poslechnout scény 2 a 3 na Linuxu.

Navrhované další kroky:
- Další MMTX dokončení ukončit příkazem `p+n`, jakmile bude samoobslužná capability Human–Adam živě ověřená.

Technický důkaz:
- Run `33266361424` uspěl a GitHub deployment ukazuje přesný commit `933834f`.
- Veřejné manifesty a reprezentativní české MP3 scén 2 a 3 jsou hashově shodné s lokální produkční kopií.

### 2026-08-29 20:44 CEST – MMTX p+n živě dokončeno

Hotovo:
- Human–Adam přímým `p+n` publikoval aktuální čistý GitHub main `72aedbf` a vrátil pravdivou dokončovací účtenku.

Rozhodnutí:
- Další dokončený MMTX vývoj končit v tomto proudu pokynem `p+n`; samotný push není produkční důkaz.

Další krok:
- Prakticky projít a poslechnout scény 2 a 3 na Linuxu.

Navrhované další kroky:
- Po poslechovém ověření pokračovat auditem pevného audia hlavního portálu.

Technický důkaz:
- Run `33269031345`, deployment `6158917594`, přesná shoda commitu `72aedbf` a veřejný HTTP 200.

### 2026-08-29 21:01 CEST – MMTX p+n nezávislé na modelové obálce

Hotovo:
- Opravený Human–Adam přímým `p+n` publikoval aktuální čistý main `0230cf5` a vrátil úplnou serverovou účtenku.

Rozhodnutí:
- Modelová obálka neautorizuje ani nevolí produkční operaci; rozhoduje přesný pokyn Míly a deklarovaný Pages cíl MMTX.

Další krok:
- Prakticky projít a poslechnout scény 2 a 3 na Linuxu.

Navrhované další kroky:
- Po poslechovém ověření pokračovat auditem pevného audia hlavního portálu.

Technický důkaz:
- Run `33269734786`, deployment `6159053676`, přesná shoda commitu `0230cf5` a veřejný HTTP 200.

### 2026-08-29 21:27 CEST – První scéna Cesty k jezeru nyní používá 49 pevných anglických a českých MP3 řízených manifestem bez systémového hlasu.

Hotovo:
- První scéna Cesty k jezeru nyní používá 49 pevných anglických a českých MP3 řízených manifestem bez systémového hlasu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Existující kvalitní anglické nahrávky zůstávají zachované; nové české stopy používají Vlastu a změna je omezena na clearingMeeting.

Další krok:
- Po potvrzeném checkpointu publikovat aktuální MMTX pomocí p+n a scénu poslechnout na Linuxu.

Navrhované další kroky:
- Publikovat potvrzený checkpoint na GitHub Pages pomocí p+n.
- Prakticky projít první scénu na Linuxu a ověřit tempo, hlasitost a výslovnost.
- Potom pokračovat další dosud systémově namluvenou částí hlavního portálu.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-30 12:17 CEST – Forest School nyní používá kompletní knihovnu 203 pevných anglických a českých stop bez systémového hlasu a Benjiho ukázka správně odpovídá No, it isn’t.

Hotovo:
- Forest School nyní používá kompletní knihovnu 203 pevných anglických a českých stop bez systémového hlasu a Benjiho ukázka správně odpovídá No, it isn’t.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Forest School používá pevná MP3 řízená manifestem a Benji v ukázce odpovídá No, it isn’t.

Další krok:
- Po potvrzeném checkpointu scénu poslechnout a samostatně spustit p+n.

Navrhované další kroky:
- Prakticky projít Forest School na Linuxu nebo Macu
- Potom samostatně publikovat aktuální MMTX pomocí p+n

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-31 10:24 CEST – Schválený Logan v neoprenu a základ rozvodněného potoka jsou bezpečně uložené v obou projektových kopiích

Hotovo:
- Schválený Logan v neoprenu a základ rozvodněného potoka jsou bezpečně uložené v obou projektových kopiích
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Logan používá lehký neopren bez potápěčské výstroje a prostředí má široké břehy s bobří hrází v dálce

Další krok:
- Vytvořit první dějový obraz se skupinou zvířátek před rozvodněným potokem

Navrhované další kroky:
- Přidat Logana, který si skupiny všimne
- Potom připravit interakci se třemi kládami

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-31 11:24 CEST – Vznikly dvě výrazně lehčí WebP varianty potoka a stránka pro přímé porovnání na velké obrazovce

Hotovo:
- Vznikly dvě výrazně lehčí WebP varianty potoka a stránka pro přímé porovnání na velké obrazovce

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Originální PNG zůstává nedotčené a pilot porovnává plné rozlišení WebP q90 a q85

Další krok:
- Porovnat q90 a q85 na 22palcové obrazovce a vybrat produkční kvalitu

Navrhované další kroky:
- Po výběru zapojit zvolenou WebP variantu do scény 5
- Stejným nastavením připravovat další obrazy scény 5
- Později samostatně optimalizovat starší obrazy MMTX

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 9.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-31 12:15 CEST – Produkční obrazy scén MMTX budou vždy optimalizované

Hotovo:
- Do kanonického handoffu a TVBCP je zapsané společné pravidlo pro obrazové podklady všech scén MMTX.

Rozhodnutí:
- Každý obrázek scény MMTX se před produkčním nasazením zmenší a nasazuje se až jeho vizuálně ověřená lehčí produkční varianta.
- Zdrojový originál zůstává zachovaný a optimalizace jej nesmí tiše přepsat.

Další krok:
- Dokončit bod 1: porovnat WebP q90 a q85 scény 5 a vybrat produkční kvalitu.

Navrhované další kroky:
- Zvolenou variantu zapojit do scény 5.
- Stejný postup použít pro další nové obrazy a starší scény optimalizovat samostatně.

Technický důkaz:
- Pravidlo vychází z Mílova výslovného rozhodnutí a navazuje na existující create-only WebP pilot q90/q85.

### 2026-08-31 12:22 CEST – Pro scénu 5 je vybraná produkční kvalita WebP q90

Hotovo:
- První WebP varianta q90 je na porovnávací stránce označená a zobrazovaná jako vybraná produkční kvalita.

Rozhodnutí:
- Pro základ rozvodněného potoka ve scéně 5 použít WebP q90.
- PNG originál i q85 zůstávají zachované; tento krok nic nepublikuje ani nenasazuje.

Další krok:
- Zapojit q90 jako obrazový základ funkční scény 5 bez přepsání zdrojového PNG.

Navrhované další kroky:
- Stejné nastavení použít při přípravě dalších obrazů scény 5.
- Starší scény optimalizovat po samostatných ověřených dávkách.

Technický důkaz:
- Cílený test `tests.test_mmtx_scene05_webp_pilot` prošel 5/5, obě projektové kopie stránky jsou shodné a `git diff --check` je čistý.

### 2026-08-31 15:21 CEST – Scéna 5 má samostatně otevřitelný responzivní základ s WebP q90 a PNG fallbackem

Hotovo:
- Scéna 5 má samostatně otevřitelný responzivní základ s WebP q90 a PNG fallbackem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Ručně zkontrolovat vzhled a potom připravit první dějový obraz se skupinou zvířátek

Navrhované další kroky:
- Doplnit první dějový obraz a následně interakci se třemi kládami
- Dialogy a pevná MP3 přidat až s potvrzeným dějovým stavem
- Do hlavního příběhu scénu napojit až po dokončení prvního hratelného úseku

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-31 15:54 CEST – První obraz ukazuje pět kamarádů u rozvodněného potoka a Logana ve vodě; připravena je lehká q90 varianta

Hotovo:
- První obraz ukazuje pět kamarádů u rozvodněného potoka a Logana ve vodě; připravena je lehká q90 varianta
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Potvrdit obraz a zapojit jej jako první dějový stav scény 5

Navrhované další kroky:
- Doplnit úvodní dialog po jednotlivých větách
- Připravit pevná anglická a česká MP3
- Potom vytvořit interakci se třemi kládami

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-31 17:15 CEST – Scéna 5 má první dějový průchod s Loganem, dialogem po větách, pevnými EN/CZ MP3 a stavbou mostu ze tří klád

Hotovo:
- Scéna 5 má první dějový průchod s Loganem, dialogem po větách, pevnými EN/CZ MP3 a stavbou mostu ze tří klád

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Aktivní relace má neuzavřenou nejistotu doručení.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Ručně ověřit vzhled, ovládání a zvuk scény 5 na Macu a iPhonu; potom rozhodnout o napojení ze scény 4

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`delivery_uncertain`.

### 2026-09-01 12:03 CEST – Schválený most je zapojený do produkčního modelu úvodu scény 5

Hotovo:
- Úvodní obraz nyní ukazuje zachované čtyři kůly a příčné nosníky bez starých podélných klád.
- Tři skutečné alfa sprity pokroucených, suchých a bobrem ohlodaných kmenů postupně létají na základy po jednotlivých klepnutích.
- Po třetím dosednutí se zobrazí přesný schválený finální obraz se třemi novými kmeny.
- Dialog po jedné větě, `Next`, `Repeat`, jazykový režim a 22 pevných EN/CZ MP3 zůstaly beze změny.

Rozhodnutí:
- Schválené obrazy z lokálního layout prototypu jsou nyní produkčními WebP aktivy scény 5; samostatný prototyp zůstává mimo Git.
- Produkční zdroj v `docs` a MMTX mirror zůstávají byte-identické.
- Lokální implementace a commit nejsou důkazem pushnutí ani Pages nasazení.

Další krok:
- Ručně ověřit tři lety, dosednutí a finální překrytí na Macu a iPhonu; teprve potom samostatně potvrdit MMTX `p+n`.

Navrhované další kroky:
- Po vizuálním schválení rozhodnout o napojení scény 5 ze scény 4.

Technický důkaz:
- `node --check` prošel, generátor audia potvrdil 22 pevných stop, cílené testy prošly 18/18 a `git diff --check` je čistý.
- Automatizovaný browser nebyl v této relaci dostupný, proto vizuální retest zůstává otevřený a nesmí být vydáván za provedený.

### 2026-09-01 21:47 CEST – Scéna 5 pokračuje interaktivním přechodem Benjiho a Sunny a končí Bunnym, který se bojí přejít.

Hotovo:
- Scéna 5 pokračuje interaktivním přechodem Benjiho a Sunny a končí Bunnym, který se bojí přejít.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Ručně ověřit přechody obrazů, klikací oblasti a zvuk na Macu nebo iPhonu.

Navrhované další kroky:
- Doplnit přemlouvání Bunnyho
- Nechat Bruna převzít Bunnyho batoh a vést ho přes most
- Navázat pádem Brunovy lampy do vody

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-09-01 22:31 CEST – Benjiho přechod nyní používá hladkou 3D grafiku odpovídající původnímu MMTX při zachování plného rozlišení a lehkého WebP q90.

Hotovo:
- Benjiho přechod nyní používá hladkou 3D grafiku odpovídající původnímu MMTX při zachování plného rozlišení a lehkého WebP q90.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Scéna 5 bude používat hladký 3D standard původního MMTX; WebP q90 zůstává produkční formát.

Další krok:
- Ověřit pilot na velké obrazovce a po schválení stejným stylem opravit ostatní situační obrazy scény 5.

Navrhované další kroky:
- Opravit navazující obraz s Benjim a Sunnym
- Sjednotit úvodní a mostové obrazy scény 5

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-09-01 22:44 CEST – Úvod, hotový most i přechod Benjiho se Sunny nyní používají jednotnou hladkou 3D grafiku a jsou zapojené v lokální scéně 5.

Hotovo:
- Úvod, hotový most i přechod Benjiho se Sunny nyní používají jednotnou hladkou 3D grafiku a jsou zapojené v lokální scéně 5.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Aktivní situační obrazy scény 5 používají hladký 3D standard původního MMTX a produkční WebP q90.

Další krok:
- Vizuálně ověřit všechny přechody scény 5 na 22palcové obrazovce.

Navrhované další kroky:
- Po schválení provést p+n jako samostatný krok
- Pokračovat Bunnyho a Brunovou částí příběhu

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-09-02 21:04 CEST – Pátá scéna je dokončená Loganovou záchranou Brunovy lampy

Hotovo:
- Fiona předvede bezpečný přechod, Bruno převezme Bunnyho těžký batoh a vede ho přes most.
- Brunova lampa spadne do vody, Logan ji po klepnutí zachrání a závěr uzavírá cesta k jezeru.
- Čtyři nové obrazy zachovávají hladký 3D styl, rozměr 1672 x 941, zdrojová PNG a produkční WebP q90.
- Scéna má 36 krokovaných vět, 72 pevných EN/CZ MP3 a tři nové klikací úkoly pro Fionu, Bruna a Logana.
- Dokončená scéna 4 nyní nabízí přímé pokračování do scény 5.

Rozhodnutí:
- Logan zachrání Brunovu lampu ještě v páté scéně; jeho pomoc uzavírá význam nové postavy v této kapitole.
- `Next` zpřístupní právě jednu další větu, `Repeat` opakuje jen aktuální větu a neúspěšné klepnutí nemá trest.

Další krok:
- Po samostatném Milově potvrzení provést serverově řízené MMTX `p+n` a potom celou scénu projít na Macu a iPhonu.

Navrhované další kroky:
- Po produkčním retestu opravit jen konkrétně potvrzené hotspoty nebo audio.
- Teprve po schválení závěru navrhnout obsah scény 6.

Technický důkaz:
- Celý MMTX balík prošel 61/61 testy; generátor ověřil 72/72 pevných MP3.
- Oba JavaScripty prošly `node --check`, `git diff --check` je čistý a `docs` s MMTX mirrorem jsou pro scény 4 a 5 byte-identické.
- Browserový backend nebyl dostupný, proto interaktivní vizuální smoke není vydáván za provedený.
- Push ani nasazení v tomto vývojovém kroku neproběhly.

### 2026-09-02 21:49 CEST – Dokončená pátá scéna je publikovaná na GitHub Pages

Hotovo:
- Přesný serverový požadavek `mmtx_pages_publish_current_main` pushnul jediný čekající commit `d0fd66c3c581`.
- GitHub Pages workflow a deployment doběhly úspěšně a veřejná produkce vrací HTTP 200.
- Veřejné HTML, JavaScript, audio manifest, závěrečný obraz a reprezentativní Loganovo MP3 jsou SHA-256 shodné s lokální produkční kopií.

Rozhodnutí:
- MMTX `p+n` je dokončené jen při korelaci přesného commitu, workflow, deploymentu a veřejného smoke; modelová odpověď ani samotný push nejsou autoritou.

Další krok:
- Projít celou scénu 5 na Macu a iPhonu, zejména umístění tří nových hotspotů, přechody obrazů a všech 72 stop.

Navrhované další kroky:
- Případnou opravu dělat pouze podle konkrétního výsledku ručního retestu.
- Po schválení závěru navrhnout obsah scény 6 jako nový vývojový krok.

Technický důkaz:
- Workflow run `33674738263` má stav `completed/success` a `headSha=d0fd66c3c581c92081a2d3a4febda6a811f552a3`.
- GitHub Pages deployment `6230419264` má stav `success` a stejný commit.
- Server i nezávislý systémový `curl` potvrdily HTTP 200; pět reprezentativních souborů má shodný SHA-256.
- Funkční commit je na `origin/main`; následný git-safe paměťový zápis je samostatný lokální checkpoint a znovu nespouští push ani deployment.

### 2026-09-07 10:52 CEST – Pátá scéna má slovník 16 výrazů s místním anglickým a českým audiem v obou synchronizovaných kopiích

Hotovo:
- Pátá scéna má slovník 16 výrazů s místním anglickým a českým audiem v obou synchronizovaných kopiích

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Po potvrzeném checkpointu samostatně spustit řízené p+n a potom ověřit slovník na Macu a iPhonu

Navrhované další kroky:
- Projít otevření slovníku a všech 16 položek v režimech EN a EN + CZ
- Po nasazení ověřit veřejnou kopii a reprezentativní MP3

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-mmtx`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-09-12 09:40 CEST – Závěrečné loučení na druhém břehu

Hotovo:
- Scéna 5 má odstraněný horní nadpis, dialog posunutý nahoru a nový obraz loučení všech pěti přátel s Loganem na druhém břehu. Poslední věta To the lake! se přehraje až na novém obrazu.
- Zdrojové PNG i produkční WebP q90 (1672 × 941; 504 810 B) jsou v obou byte-identických kopiích scény.

Rozhodnutí:
- Jeden nový obraz zachovává postavy a prostředí; Bruno drží zachráněnou lampu, Logan zůstává u potoka.
- Pevné audio, jedna věta na Next, Repeat a slovník po dokončení zachovávají dosavadní chování.
- Míla v tomto kroku výslovně zadal vývoj, push i produkční publikaci.

Další krok:
- Dokončit řízený push s plnou bránou a MMTX Pages publikaci; výsledek dopsat do tohoto handoffu i TVBCP.

Navrhované další kroky:
- Po veřejném ověření krátce poslechnout závěr na skutečném iPhonu.

Technický důkaz:
- 63/63 cílených MMTX testů, 104/104 pevných MP3, JavaScript syntaxe a rychlá statická brána prošly.
- Browserový průchod ověřil 36 kroků, poslední audio na novém obrazu, Repeat v EN/EN+CZ a 16 položek slovníku. Zvukové konce byly při automatickém průchodu simulované; skutečný poslech není vydáván za provedený.
- Riziko při zápisu: push a veřejná publikace teprve následují; tento vývojový zápis sám nepotvrzuje produkci.

### 2026-09-12 09:50 CEST – Loučení ve scéně 5 je na produkci

Hotovo:
- Scéna 5 je veřejně publikovaná: horní nadpis je odstraněný, dialog je výše a To the lake! zazní na novém obrazu loučení všech pěti přátel s Loganem na druhém břehu.
- Řízená operace `mmtx_pages_publish_current_main` dokončila push jednoho funkčního commitu a ověřenou Pages publikaci.

Rozhodnutí:
- Při užším obrazu jsou ovládací prvky závěru vlevo, aby nezakrývaly loučící se postavy vpravo.
- Tento následný zápis zachycuje skutečnou publikaci funkčního commitu; sám nemění veřejnou aplikaci.

Další krok:
- Otevřít veřejnou scénu 5 a běžně poslechnout závěr na skutečném zařízení.

Navrhované další kroky:
- Případné další úpravy odvodit až z konkrétního Mílova retestu.

Technický důkaz:
- Commit `84c2809fb334`, workflow `34681649893` completed/success a deployment `6407386976` success mají shodné SHA.
- Veřejné HTML, oba styly, skript, audio manifest, nový WebP a EN/CZ MP3 poslední věty: 8/8 byte-identických souborů, HTTP 200.
- Plná brána 1 554/1 554 testů; cílený MMTX balík 63/63; audio kontrola 104/104.
- Browser: 36 kroků, finální obraz před poslední větou, Repeat EN/EN+CZ, slovník 16 položek, pět rozměrů (1440×1000 až 390×844), bez JS výjimek a kolize dialogu s tlačítky.
- Obraz: `assets/scene05_friends_farewell_smooth_source.png`; produkční `scene05_friends_farewell_smooth_q90.webp`, 1672×941, 504 810 B, obě kopie shodné. Zadání generátoru: stejné postavy a hladký 3D styl, všech pět přátel na pravém břehu mává Loganovi, Bruno drží zachráněnou lampu, prázdný most a levý břeh, bez textu.
- Mez ověření: browserový test simuloval události konce audia; fyzický poslech na iPhonu zbývá pro uživatelský retest.

### 2026-09-12 10:17 CEST – Oprava Loganova loučení a počtu klád

Hotovo:
- Logan při závěrečném loučení stojí zády k divákovi a mává přímo přátelům. Obraz hotového mostu ukazuje tři samostatné klády hned po jejich usazení, ještě před Benjiho přechodem.
- Vyměněna dvě zdrojová PNG a dva WebP q90 v obou kopiích scény; URL verze `20260912artfix1` obnoví obrázky z cache.

Rozhodnutí:
- Chyba počtu klád byla v obrázku `finalScene`, který překryl správně usazené tři animované klády; oprava je proto pouze obrazová.
- Míla autorizoval opravu, push a nasazení s čistým předáním do Human–Adam.

Další krok:
- Dokončit řízenou publikaci a dopsat její přesný veřejný důkaz.

Navrhované další kroky:
- Večer navázat na čistý `project-mmtx` podle Mílova dalšího zadání.

Technický důkaz:
- Cílené testy 63/63, audio 104/104, rychlá brána, byte-identické mirrory a browserový průchod 36 kroků prošly.
- Screenshot po třetím polenu potvrzuje tři klády před Benjiho přechodem; závěr byl ověřen i v úzkém mobilním obrazu.
- Výstupy a přesná zadání generátoru: `reports/mmtx_scene05_artfix_2026_09_12.md`.
- Riziko při zápisu: p+n teprve následuje. Automatický test simuluje konce audia, nikoli fyzický poslech.

### 2026-09-12 10:27 CEST – Opravené obrazy publikované, čisté předání pro Human–Adam

Hotovo:
- Obrazové opravy scény 5 jsou na produkci: Logan je při loučení vidět zezadu a mává přátelům; tři klády jsou viditelné ihned po sestavení mostu před Benjiho přechodem.
- MMTX `p+n` dokončilo push a přesně ověřenou Pages publikaci.

Rozhodnutí:
- Oprava zůstává u dvou obrazů a jejich cache verze; dialogy, audio, animace i ovládání se nemění.
- Dvě dodatečně vzniklé kopie předchozích zdrojových PNG byly obsahově ověřeny proti Gitu a zachovány mimo publikovanou scénu v soukromém pracovním adresáři; nic nebylo smazáno.

Další krok:
- Večer pokračovat v čistém pracovním proudu MMTX podle Mílova dalšího zadání.

Navrhované další kroky:
- Při běžném použití ověřit nové obrázky i na skutečném iPhonu.

Technický důkaz:
- Commit `49401df07e43`, workflow `34683204037` completed/success, deployment `6407668406` success; všechna ID korelují se stejným SHA.
- Veřejná kontrola: HTTP 200 a 9/9 byte-identických souborů včetně obou opravených WebP a EN/CZ poslední věty.
- Testy: 1 554/1 554 plné brány, 63/63 MMTX, 104/104 pevných stop; oba mirrory shodné.
- Browser prošel 36 kroky, stavem po třetí kládě, závěrem, Repeat EN/EN+CZ a slovníkem; pět velikostí obrazu bez kolize dialogu s tlačítky.
- Read-only audit před závěrečným dokumentačním commitem: main aligned, workspaces aligned_clean (2/2), runtime connected bez busy či nejistého doručení, pending integration not_pending.
- Souhrnný live-status deployment stále odkazuje na starší nasazení samotného Cockpitu `d1e0b5bca0bc` (verified_other_main); tento údaj není důkazem neúspěchu Pages a není zaměňován s výše ověřenou MMTX publikací. Cockpitový kód se touto opravou nemění.
- Výstupy a přesná zadání vestavěného ImageGen: `reports/mmtx_scene05_artfix_2026_09_12.md`.

### 2026-09-13 18:21 CEST — Jednotná navigace scén 1–5

Hotovo:
- Dveře pokračují do další scény, šipky vlevo nahoře vracejí do předchozí. Návrat ve scénách 4 a 5 funguje i před spuštěním vyprávění.
- Opravený návrat ze scény 2 a nefunkční závěrečné pokračování scény 3; dveře ve scénách 2–4 lze aktivovat klávesnicí.

Rozhodnutí:
- Míla požaduje dveře vpřed a šipku vlevo nahoře zpět a schválil commit, push a nasazení. Zachovat dokončení scény jako podmínku zobrazení dveří.

Další krok:
- Dokončit publikaci a doložit veřejnou verzi.

Navrhované další kroky:
- Další scéna za mostem zůstává budoucím příběhovým rozšířením.

Technický důkaz:
- 63 cílených testů prošlo; 18 skutečných prokliků v Edge ve viewports 1440 × 900 a 390 × 844. Pět návratů a čtyři pokračování pro každou velikost, žádné JS chyby; vizuálně zkontrolované screenshoty dveří.
- Dokončení bylo nastaveno testem kvůli izolaci navigace, nikoli přehráno novým průchodem všech dialogů. Změny v `docs/` a `MatysekANJ/web_mmtx/` jsou shodné.

### 2026-09-13 18:31 CEST — Veřejně ověřená navigace Cesty k jezeru

Hotovo:
- Opravené dveře vpřed a šipky zpět jsou dostupné na veřejném MMTX. Návraty fungují i před spuštěním vyprávění ve scénách 4 a 5.

Rozhodnutí:
- Dokončeno Mílou schválené c+p+n pro navigaci scén 1–5; žádné další příběhové scény nevznikly.

Další krok:
- Běžně používat opravenou navigaci; při ponechané staré kartě stránku obnovit.

Navrhované další kroky:
- Další příběh za scénou 5 zůstává samostatným rozšířením.

Technický důkaz:
- Publikace: commit `0e1906b8578d`, Pages run `34768695626`, deployment `6423781674`; HTTP 200 a byte-shoda všech 10 změněných veřejných souborů.
- Plná brána 1 640/1 640, cílené MMTX testy 63/63; mirror 537/537 souborů shodný. Browser: 18 lokálních návratů/pokračování včetně Enter a dalších 18 skutečných kliknutí na veřejné produkci, vždy desktop 1440 × 900 a mobilní viewport 390 × 844, bez JS chyb.
- Test se soustředil na navigaci a nastavoval dokončený stav; neověřoval znovu celý příběh a fyzický poslech na iPhonu. Následný dokumentační commit nemění nasazené webové soubory.

### 2026-10-28 13:35 CET — Scéna 6: místní pracovní náhled bez volitelných setkání

Hotovo:
- Příchod k jezeru lze místně projít přes čtyři nová setkání až k písničce a zakončení. 72 krátkých replik EN/CZ, velké klikací cíle, Repeat, změna jazyka a napojení na pátou scénu. Čtyři nové ilustrace zachovávají původní postavy; kopie docs/mirror shodné.

Rozhodnutí:
- Míla výslovně schválil scénář vytvořený Terrou 6.1 a zadal stejné Terře jeho naprogramování bez options: vynechané Tilly/Pip/Lulu/Momo a volitelná větvení. Výběr nemění centrální role ani nepovoluje publikaci. Kvůli nedostupné službě nebyl bez potvrzení nahrazen žádný původní hlas.

Další krok:
- Mílův první obrazový/textový průchod místním náhledem a rozhodnutí o chybějících hlasech; bez náhrady dokončit původní audio až po odblokování Edge.

Navrhované další kroky:
- Po doplnění zvuku provést skutečnou hlasovou přejímku celé scény; potom samostatně rozhodnout o případném vydání.

Technický důkaz:
- 71 MMTX testů PASS / 2,384 s; Node kontrola syntaxe a automatický stavový průchod PASS. HTTP 200 a přesná shoda 13/13 zdrojů. Čtyři ilustrace vizuálně zkontrolované, přesné prompty v image_prompts.txt, vestavěný ImageGen.
- Audio pouze 2/144, 142 chybějících: první Edge dávka NoAudioReceived, jediná další sériová zkouška kompatibilního endpointu HTTP 429, pak zastavení. Existující EN000/001 FFmpeg dekódování PASS; --check exit 1 je očekávaná neúplnost. Reprodukovatelný builder chrání text/hlas/rate/SHA-256 a neprovádí automatický retry či přepis.
- Žádný připojený browser, takže Safari/iPhone/proklik i lidský poslech NEOVĚŘENO; konzervativní výpočet geometrie je pouze pomocná kontrola. Statické obrazy nemají všechna navržená komická gesta; písnička je krátká syntetická melodie s postupným světlem bublin. Pracovní checkpoint, bez nového push/nasazení a bez zásahu do Camina.

### 2026-10-28 14:17 CET — Terra p+n: push potvrzený, Pages zablokované sovím audiem

Hotovo:
- Schválené dva commity včetně scény 6 jsou na GitHubu do 5564aec3. Místní pracovní náhled zachovaný; veřejné vydání scény zatím neproběhlo.

Rozhodnutí:
- Míla výslovně zadal „OK, terra p+n“. Jediné registrované submit_release(wait=True) zmrazilo projekt MMTX, oba heads a Terru 6.1/high; bez nativního pomocníka, přepínání modelu nebo retry.

Další krok:
- Vyřešit chybu sdíleného generování sovího audia před novým výslovným publikačním pokusem.

Navrhované další kroky:
- Doplnit 142 řečových stop scény 6 a provést skutečnou obrazovou/hlasovou přejímku; do té doby místní pracovní náhled.

Technický důkaz:
- Účtenka eab22667ea9a7286189f6fc1a1f563e2 attention, push_state=confirmed, deployment_state=uncertain, failure_phase=publish_requested; plná brána 2260 PASS / 481,8 s. GitHub main přesně 5564aec373f4e87c0187bc9a1d2d2f10dc338668 a lokální main 0/0 před tímto zápisem.
- Pages workflow 40694554621 / build-pages 122837760412: Generate and verify today's owl before publication failure/exit20; Edge TTS websocket Invalid response status, upload i deploy skipped. Pro tento head není deployment, veřejná nová scéna HTTP 404. Původní účtenka neměněná, žádná opakovaná publikace.
- Caller účtenku převzal a Adam jednou ověřil GitHub, původní workflow a veřejný stav. returned_to_adam=false neprokazuje automatický portálový návrat. Závěrečné potvrzení protected_services_unchanged v neúspěšné účtence není; dostupný živý Cockpit má code_stamp b90aa847fa54ce76. Bez nového Cockpit deploymentu, zásahu do hlasů scény 6 či souvisejících služeb.

### 2026-10-28 14:24 CET — Zrušení automatického sovího audia

Hotovo:
- V místním kódu je zrušené automatické soví TTS: Pages bez generování, Python/TTS instalace a denního cronu; místní rutina už soví úkol nevolá. Historické soubory i přehrávač zachované.

Rozhodnutí:
- Míla výslovně zadal „Soví audio zruš.“ Sdílený ruční Pages publisher a jeho ochrany zůstávají pro MMTX a další weby, bez závislosti na sovím audiu. Nový publikační pokus tímto krokem spuštěný nebyl.

Další krok:
- Po úspěšné plné bráně a lokálním commitu nový samostatný Terra p+n; původní úspěšný push a neúspěšné vydání se neopakují automaticky.

Navrhované další kroky:
- Odděleně doplnit hlasové stopy scény 6 a udělat fyzickou přejímku.

Technický důkaz:
- 43 cílených testů PASS včetně regrese, že ani při připraveném CSV běžná rutina nezavolá TTS ani nepřepíše app.js. Obě workflow kopie shodné a YAML validní; plná brána 2260 PASS (511,838 s unit část), log cancel_automatic_owl_gate_20261028.log. Žádné soubory smazané, žádná nová řečová síťová generace, žádný nový push/nasazení či restart.

### 2026-10-28 14:45 CET — Soví automatika zrušená a MMTX veřejně nasazené

Hotovo:
- Automatické soví TTS už není součástí běžné místní rutiny ani sdílených Pages. Opravený web je zveřejněný; scéna 6 i přechod ze scény 5 se podávají ve správné verzi. Historické soubory a přehrávač zachované.

Rozhodnutí:
- Adam navázal na Mílův předchozí pokyn Terra p+n a konkrétní opravu „Soví audio zruš.“ Nové předání zmrazilo nový opravený balíček do 30d3c58b; původní neúspěšná účtenka zůstala zachovaná. Žádná změna hlasů scény 6 či centrálních rolí.

Další krok:
- Mílův obrazový/textový průchod veřejnou scénou 6.

Navrhované další kroky:
- Samostatně dokončit 142 řečových stop scény 6 a fyzickou/poslechovou přejímku.

Technický důkaz:
- Účtenka 6b2cea8ea2f983ae95be21cb287ee2e4 completed, push_state/deployment_state=confirmed, Terra 6.1/high, 2 commity do 30d3c58be7aee89d1003864a0c8b0335fe8e20f7. Publikační full gate 2260 PASS/472,6 s, protected_services_unchanged=true. Pages workflow 40699075925 success, deployment 7387046778.
- Jedna Adamova kontrola: GitHub/main 0/0 na vydaném headu před tímto zápisem, HTTP 200 + přesná shoda 13/13 zdrojů. HTML SHA-256 f538f932e84b00eea2b817ea11610b7e407e2650c8885711b41bab628788b719. Nový build pouze Checkout→Configure Pages→Upload→Deploy, bez TTS a bez denního cronu.
- return_channel=caller: terminálový Adam převzal a ověřil; returned_to_adam=false nepotvrzuje automatický portálový návrat a není důvodem retry. Předchozí gate 2260/511,838 s a 43 cílených kontrol/YAML PASS. Řeči scény 6 nadále 2/144 a fyzický browser/poslech NEOVĚŘENO. Následný lokální dokumentační checkpoint.

### 2026-10-28 15:58 CET — Obvyklá levá dolní zkratka ze scény 5 do scény 6, lokálně

Hotovo:
- Doplněný místní odkaz z levého dolního rohu páté scény přímo k jezeru. Funguje i před zahájením dialogu; běžné dokončovací dveře zachované.

Rozhodnutí:
- Míla chtěl otevření nové scény obvyklým kliknutím vlevo dole ve scéně 5. Převzít rozměry stávající zkratky ze scény 4, minimální cíl 44 px a vrstvu nad audio bránou. Při otevřeném slovníčku zkratku skrýt, aby nepřekrývala jeho položky.

Další krok:
- Samostatné p+n MMTX a fyzický proklik rohu scény 5; přímá URL scény 6 je veřejně dostupná už nyní.

Navrhované další kroky:
- Zachované doplnění řečí scény 6 a skutečná přejímka hlavního průchodu.

Technický důkaz:
- Rychlá statická brána PASS. 71 MMTX testů PASS / 2,262 s, odkaz i byteová shoda obou kopií ověřené. CSS má plochu 16%×24%, min. 44 px, z-index 22 nad audio bránou 20 a fokusový rámeček; cache parametr upravený. Skutečný browserový proklik NEOVĚŘENO. Bez nového push/publikace, bez změny audia nebo děje.

### 2026-10-28 19:19 CET — Terra p+n rohové zkratky 5→6 dokončené

Hotovo:
- Veřejná pátá scéna má obvyklou zkratku vlevo dole přímo do šestky, dostupnou i před spuštěním příběhu. Nové HTML a CSS se skutečně podávají, běžné dokončovací dveře zachované.

Rozhodnutí:
- Míla výslovně zadal „ok, terra p+n“. Jedno registrované submit_release(wait=True) předalo přesné dva commity a schválenou Terru 6.1/high. Bez nativního prostředníka, změny rolí či opakování.

Další krok:
- Obnovit veřejnou pětku a přijmout proklik vlevo dole i před audio bránou.

Navrhované další kroky:
- Zachované doplnění vlastních řečových stop šestky a skutečná obrazová/poslechová přejímka.

Technický důkaz:
- Účtenka 46daf0cd2eae60a54363365d9f52a290 completed, push_state/deployment_state=confirmed, dva commity do 46173ef987c345ebf6875c24301f38532471434f. Plná publikační brána 2262 PASS / 466,3 s, protected_services_unchanged=true. Pages workflow 40743712328 success, deployment 7393736182, smoke HTTP 200.
- Adamova jedna kontrola: GitHub/main 0/0 na vydaném headu před zápisem, veřejné 3/3 HTML/CSS zdroje HTTP 200 a přesné bajty. Pětka SHA-256 e96ca0b045dfbfe9f5bc76948baf165174ea652bb9cee4e580dacbf86f4b904e; CSS 3982bedefa5210387d97c16411f972e517dfdf62de18f3147a4eaa3042ec6a79; šestka f538f932e84b00eea2b817ea11610b7e407e2650c8885711b41bab628788b719. Odkaz i verzovaný CSS parametr ověřené.
- Caller účtenku převzal; returned_to_adam=false nepotvrzuje automatický portálový návrat a nevyvolává retry. Fyzický proklik/Safari/iPhone a poslech NEOVĚŘENO. Řeči šestky stále 2/144, zrušené soví TTS se neobnovilo. Bez nového Cockpit deploymentu či zásahu do chráněných služeb. Následný lokální výsledkový zápis pro další balíček.

### 2026-10-30 09:28 CET — Audio šestky: tři nové stopy, poskytovatel dál blokuje dokončení

Hotovo:
- Místní scéna obsahuje pět platných řečových stop místo dvou; úspěšné výsledky jsou zachované i v druhé kopii aplikace.

Rozhodnutí:
- Navázat na Mílův pokyn dokončit audio. Zachovat původní hlasy a tempo; po doloženém 429 neprovádět další automatické pokusy ani hlasovou náhradu.

Další krok:
- Po uvolnění služby doplnit zbývajících 139 stop od CZ 002. Dokončení nyní blokuje externí Microsoft TTS.

Navrhované další kroky:
- Po úplné generaci provést proklik a poslech na Macu/iPhonu; publikaci zadat samostatně.

Technický důkaz:
- 71 MMTX testů PASS; offline kontrola potvrzuje 5/144 a očekávaný exit 1 kvůli 139 chybějícím stopám. MP3 mají odpovídající text/hlas/-10%/SHA-256 a dekódují se. Dvě původní EN stopy zůstaly beze změny.
- První sériový běh přidal CZ 000, CZ 001 a EN 002, potom HTTP 429. Jedno pokračování po pauze s 10s rozestupy opět HTTP 429 bez Retry-After, žádný další síťový pokus. Logy mmtx_scene06_audio_20261030.log a mmtx_scene06_audio_paced_20261030.log. Zdrojový generátor ani společná speech vrstva se neměnily; bez push/nasazení.

### 2026-10-30 10:20 CET — Pokus o pětici: dvě nové stopy, další zastavila chyba 429

Hotovo:
- Zachované dvě nové řečové stopy CZ 002 a EN 003; místní audio nyní 7/144, zbývá 137.

Rozhodnutí:
- Na Mílův pokyn pokračovat v dávkách po pěti, další dávku spustit jen po úspěšné předchozí. Původní hlasy a tempo zachovat. Při HTTP 429 zastavit bez retry.

Další krok:
- Po uvolnění Microsoft TTS navázat od CZ 003. První pětice byla neúplná, další se nespustila.

Navrhované další kroky:
- Po všech 144 stopách ověřit skutečný proklik a poslech; publikace vyžaduje samostatný pokyn.

Technický důkaz:
- 4 cílené testy scény 6 PASS; MP3/vazby/mirror ověřené. Offline --check: 7/144, očekávaný exit 1 pro neúplné audio. Generátor ani společná speech vrstva se neměnily.
- Běh po více než 50min pauze: 10s před novým požadavkem, 30s pauza připravená mezi úspěšnými pěticemi. Dvě úspěšné stopy, potom CZ 003 → HTTP 429 bez Retry-After. Dokončených pětic 0, opakování 0; výsledek a kurzor v logs/mmtx_scene06_batches_20261030_1018_state.log. Bez push/nasazení.

### 2026-10-30 15:55 CET — Devět nových stop v dávkách po pěti, další blokuje 429

Hotovo:
- Místní audio šestky rozšířené ze 7 na 16 stop, zbývá 128. První pětice kompletní, druhá má 4/5; všechny úspěšné výsledky zachované a synchronizované.

Rozhodnutí:
- Na Mílův pokyn pokračovat po pěti. Po více než pěti hodinách od předchozího pokusu použít 30s rozestupy a 60s mezi úspěšnými pěticemi; původní hlasy a tempo zachovat. Při HTTP 429 zastavit.

Další krok:
- Po uvolnění poskytovatele doplnit EN 008 jako poslední stopu rozpracované druhé pětice; teprve po jejím ověření navázat třetí pěticí.

Navrhované další kroky:
- Po kompletních 144 stopách skutečný proklik a poslech; publikaci zadat samostatně.

Technický důkaz:
- 4 cílené testy scény 6 PASS; offline --check ověřil 16/144 a očekávaný exit 1 kvůli neúplnému audiu. Předchozích sedm MP3 zachovaných; obě kopie stejné. Generátor ani společná speech vrstva se neměnily.
- První běh přidal sedm stop, potom EN 007 → ClientConnectorDNSError/gaierror. Čtecí DNS kontrola domény služby i microsoft.com prošla; obnovení zachovalo stav pětic a přidalo EN 007/CZ 007. Následně EN 008 → HTTP 429 bez Retry-After, další dávka se nespustila.
- Průběh a kurzor v logs/mmtx_scene06_batches_20261030_154314_state.log a logs/mmtx_scene06_batches_20261030_155259_state.log. Bez push/nasazení; fyzický poslech/proklik NEOVĚŘENO.

### 2026-11-01 21:35 CET — Azure generátor a šest poslechových ukázek

Hotovo:
- Připravený Azure generátor a šest ukázek původních hlasů, společný poslech 22,488 s. Kanonické audio zůstává 16/144 a oba mirrory beze změny.

Rozhodnutí:
- Na Mílův pokyn napojit již vytvořený Azure účet a před doplněním celé scény připravit ukázky. Zachovat hlasy, texty a -10 %; výslovná volba Azure, limit 10 000 znaků na běh, žádný automatický retry ani publikace.

Další krok:
- Přijmout zvuk ukázek a následně doplnit zbývajících 128 stop přes Azure.

Navrhované další kroky:
- Po úplné generaci offline kontrola a fyzický proklik/poslech Mac/iPhone; publikaci zadat samostatně.

Technický důkaz:
- 44 cílených testů PASS; šest platných MP3, 274 účtovaných znaků, shodné původní SHA-256 obou kopií scény. Plná projektová brána 2273 testů PASS. Report mmtx_scene06_azure_preview_20261101.md. Lidské přijetí NEOVĚŘENO.

### 2026-11-01 22:29 CET — Dokončené audio šesté scény: 144/144

Hotovo:
- Celá sada 72 anglických a 72 českých MP3 je připravená místně v obou kopiích hry. Původní nahrávky, hlasy, texty a tempo zachované.

Rozhodnutí:
- Míla přijal šest hlasových ukázek a výslovně zadal dokončení přes Azure. Zachován limit 10 000 znaků na běh a zastavení bez automatického retry.

Další krok:
- Prakticky projít a poslechnout celou scénu na Macu/iPhonu.

Navrhované další kroky:
- Po přejímce samostatně zadat p+n.

Technický důkaz:
- 128 nových MP3 / 128 unikátních úspěšných požadavků / 5 870 účtovaných znaků. Původních 16 souborů a vazeb přesně shodných. Oba mirrory shodné; offline --check 144/144, chybí 0, exit 0.
- 4 závěrečné testy scény a plná brána 2273 testů PASS. Report mmtx_scene06_azure_complete_20261101.md. Výsledek pouze místně; fyzická přejímka celé scény zatím NEOVĚŘENO.

### 2026-11-02 07:20 CET — Terra p+n zastavené publikační bránou

Hotovo:
- Audio šestky zůstává místně dokončené 144/144. Výslovně zadané vydání nepřešlo přes testovací bránu; nic nového se nepublikovalo.

Rozhodnutí:
- Míla zadal „ok, předej Terra p+n“. Jedno submit_release(wait=True) předalo šest commitů do 2270248c, project-mmtx → GitHub Pages, centrálně schválené Terře 6.1/high. Bez změny role a bez automatického opakování.

Další krok:
- Opravit izolaci rozpočtového testu vůči FFmpeg/PATH a ověřit jej také pod službovým PATH; pak připravit nový přesný balíček.

Navrhované další kroky:
- Zachovaný praktický proklik a poslech celé scény Mac/iPhone; po úspěšném vydání ověřit veřejné soubory.

Technický důkaz:
- Účtenka dc35a8df61b2ce0ff6b55c4293b6a454: attention, push_state=uncertain, deployment_state=not_started. Jedna Adamova kontrola: GitHub/main stále 46173ef987c345ebf6875c24301f38532471434f, main čistý napřed o šest; health OK se stejným code_stamp ae3b321d9492092a.
- Log human_adam_deploy_gate.log: 2273 testů / 449,410 s, FAILED(errors=1, skipped=18). test_whole_plan_over_limit_sends_nothing místo očekávané rozpočtové chyby skončil SystemExit kvůli nenalezenému ffmpeg. FFmpeg je instalovaný v /usr/local/bin, test závisí na PATH a tuto závislost neizoluje. Brána selhala před voláním push; žádný Pages workflow/deployment nevznikl.
- Před auditem existující LocalAppServerProcessController.start() spustil chybějící místní Codex App Server. Bez změny zdrojů, konfigurace služby, sítě nebo audio dat. Fyzická přejímka zůstává otevřená. Tento výsledkový zápis je místní pro další balíček.

### 2026-11-02 08:08 CET — Izolace rozpočtového testu před novým Terra p+n

Hotovo:
- Rozpočtový test už nepotřebuje skutečný FFmpeg. Při překročení rozpočtu ověřuje nulové dekódování i nulové požadavky na Azure pod stejným PATH jako služba.

Rozhodnutí:
- Míla výslovně zadal opravit izolaci, ověřit a znovu předat balíček. Jen lokální test; produkční generátor, audio i službové prostředí zachované. Nové předání používá nový request ID a nový přesný commit; stará účtenka zůstává zachovaná.

Další krok:
- Nový přesný balíček předat Terře přes submit_release(wait=True), včetně plné publikační brány.

Navrhované další kroky:
- Po potvrzeném vydání veřejná kontrola souborů; celý fyzický proklik/poslech Mac/iPhone zůstává otevřený.

Technický důkaz:
- Před opravou cílený test pod PATH=/usr/bin:/bin:/usr/sbin:/sbin reprodukoval SystemExit kvůli nenalezenému ffmpeg. Po opravě Azure/builder sada 11/11 PASS v běžném i službovém PATH. Test mockuje pouze dohledání nástroje; skutečnou rozpočtovou podmínku i assert_not_called zachovává.
- Změna tests/test_mmtx_scene06_azure_audio.py, bez nového generování nebo odchozího placeného požadavku. Předpublikační plná brána a samotné vydání zatím čekají.

### 2026-11-02 08:18 CET — Kompletní audio šestky publikované přes Terru

Hotovo:
- Šestá scéna veřejně podává všech 144 řečových stop. Opravený rozpočtový test prošel i ve skutečné publikační bráně.

Rozhodnutí:
- Na Mílův výslovný pokyn k opravě, ověření a novému předání proběhlo jedno nové submit_release(wait=True), osm commitů do b0b4e172, centrálně schválená Terra 6.1/high. Bez přepínání modelu, změny produkčního generátoru, placené regenerace nebo systémového prostředí.

Další krok:
- Praktický proklik a poslech celé scény na Macu/iPhonu.

Navrhované další kroky:
- Žádné nové rozšíření; zachované dřívější fyzické přejímky navigace.

Technický důkaz:
- Účtenka 81db27cc7794d9ba88dcd888156b35b6 completed, push_state/deployment_state=confirmed; osm commitů do b0b4e172ab8b2fe69216af9d7520a23e22e2f624. Plná brána 2273 testů / 0 chyb / 18 přeskočených, 342,3 s (unit 332,552 s), protected_services_unchanged=true.
- Pages workflow 41405199009, deployment 7486464591, smoke HTTP 200. Jedna Adamova kontrola: skutečný GitHub head shodný; veřejných 147/147 souborů (HTML, dva JSON, 144 MP3) HTTP 200 a byte/SHA-256 shoda s vydanými zdroji. Důkaz logs/mmtx_scene06_terra_public_verification_20261102.json.
- Cockpit health OK, stejný PID 1866 a code_stamp ae3b321d9492092a. Caller účtenku převzal; returned_to_adam=false nepředstavuje portálové doručení a není důvodem retry. Bez dalšího vydání nebo restartu Cockpitu; následný výsledkový zápis místně pro další balíček. Fyzický poslech/proklik celé scény NEOVĚŘENO.


### 2026-11-10 15:17 CET — Nová šestka, první obraz a anglické MP3

Hotovo:
- První obraz The Lake má přijatý boční pohled a sedm schválených replik s pevným anglickým zvukem. Next, Repeat, Again, čitelné bubliny nad vodou a návrat k mostu.

Rozhodnutí:
- Míla zadal vývoj pouze prvního obrazu, anglické MP3, Terra p+n a následné napojení z pětky pro produkční zkoušku. Další hotové ilustrace tím nejsou implementované.

Další krok:
- Převzít konkrétní ověřený commit do uvolněného kanonického main a provést autorizované p+n.

Navrhované další kroky:
- Po vydání připojit konec pětky a fyzicky ověřit přechod a hlasy na Mílově zařízení.

Technický důkaz:
- 35 cílených testů PASS, syntaxe/statická brána PASS, 7/7 MP3 dekódovaných, oba mirrory a 13 HTTP souborů přesné. Azure 7 unikátních požadavků / 410 znaků, bez retry. Lokální Safari: první věta i stav 7/7. Plná brána 2960 testů OK (5 SKIP); publikace nové šestky dosud neprovedena. Podrobnosti a otisky v `reports/mmtx_scene06_opening_20261110.md`.


### 2026-11-10 15:24 CET — Připravené napojení pětky a publikační blokátor

Hotovo:
- Po dokončení pětky je v Datově pracovní kopii viditelný vstup To the lake! do prvního obrazu nové šestky. Úprava vychází z Willova již schváleného ukončení staré šestky a zachovává odstranění neviditelné zkratky; obě kopie stejné.

Rozhodnutí:
- Mílovo zadání zahrnuje Terra p+n i produkční propojení. První obraz je ve vývojovém commitu `1c40b6db`; samotné propojení má samostatný následný commit, aby šlo dodržet pořadí živého vydání.

Další krok:
- Míla upřesní, zda hotové commity do kanonického main převezme Will, nebo Data. Zdrojové neuzavřené změny vlastníka ani profilový stav se neobcházejí.

Navrhované další kroky:
- Po převzetí: registrované Terra submit_release(wait=True), přesné potvrzení Pages, potom vydat propojení a zkontrolovat skutečné veřejné bajty a vstup z pětky. Fyzický iPhone a hlasy převezme Míla.

Technický důkaz:
- 37 cílených testů PASS; nově i skutečný cíl odkazu, jeho umístění až v původně skrytém dokončení a shoda HTML/CSS obou mirrorů. Plná místní brána 2960 OK (5 SKIP) zůstává důkazem nezměněné infrastruktury; nová markup změna byla ověřená cíleně. Žádné nové modelové/audio volání a žádná publikace této šestky. Registrovaný deploy audit: source main není čistý; batch audit: pracovní prostředí není připravené.


### 2026-11-10 16:05 CET — Ollieho obraz připojený lokálně

Hotovo:
- První a druhý obraz propojuje Next picture. Ollie nabízí rybu a deset anglických replik odkáže přátele ke staré lodi a chatrči. Čitelné dialogy nekrývají postavy ani podběrák; na úzkém displeji jsou pod obrazem.

Rozhodnutí:
- Míla výslovně zadal druhý obraz po předání prvního p+n. Aby se dlouhé čekání na Pages nepřeneslo do vývoje, druhý obraz vzniká odděleně v Datově worktree; zmrazený první main ani balíček se nemění. Žádné nové p+n pro druhý obraz se bez dalšího pokynu neodesílá.

Další krok:
- Dokončit plnou místní bránu druhého obrazu a konkrétní commit; programově převzít stejnou účtenku prvního vydání.

Navrhované další kroky:
- Po potvrzení prvního vydání zkontrolovat veřejné soubory a vstup z mostu. Druhý obraz pak samostatně převzít s Mílou a případně vydat na jeho pokyn.

Technický důkaz:
- 57 cílených kontrol PASS, všech 17 MP3 dekódovaných, 27 HTTP souborů přesné; Safari druhý obraz a Bunny 10/10 + Again. Nových 10 Azure požadavků / 635 znaků, původní první audio/data/obraz i raw účtenka zachované. Plná místní brána zatím běží. První release job `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deploy requested; Pages run `42839271179` zatím běží. Viz nový report.


### 2026-11-10 16:11 CET — Uložený dřívější WIP úklid staré šestky v Datově větvi

Hotovo:
- Git evidence Datovy větve zaznamenává již dříve provedené a schválené odstranění původní šestky: 311 dávno chybějících souborů a odpojené staré Azure workflow/registrace. Při tomto kroku se žádné další soubory z disku neodstraňují.

Rozhodnutí:
- Míla nyní zadal vyčistit repo. Všechny evidované absence byly předem porovnané s kanonickým main a omezené na starou šestku; původní potvrzené odstranění zůstává zachované. Tento servisní commit se do main znovu nepřebírá, protože tam je stejný úklid už vydaný. Nový druhý obraz dostane vlastní následující commit.

Další krok:
- Uložit ověřený druhý obraz samostatně a potvrdit čistý stav Datovy větve.

Navrhované další kroky:
- Pro neúspěšné první nasazení čeká Mílovo rozhodnutí o jednom novém pokusu; původní účtenka `4b261f77c13a77e845684bbbd90cc876` zůstává attention, push confirmed, deployment uncertain.

Technický důkaz:
- Přesně 311 absencí mimo nové názvy médií, všechny v rozsahu staré šestky a již nepřítomné na main. Konkrétní místní plán má seznam cest a původní head; plná brána aktuálního pracovního stavu 2972 testů OK (5 SKIP), 57 cílených kontrol PASS. Žádný reset, mazání dalších dat ani přepis historie.


### 2026-11-10 16:12 CET — Druhý obraz ověřený, první nasazení Pages zrušené po timeoutu

Hotovo:
- Lokálně funguje příběhové spojení prvních dvou obrazů a všech 17 anglických MP3. Druhý obraz má schválený obrázek, přesných 10 replik a vlastní neměnné audio podklady.

Rozhodnutí:
- Druhý obraz je oddělený následující vývoj, není součástí prvního zmrazeného p+n. První p+n se neopakuje automaticky; Míla má konkrétní otázku na jediný nový pokus stejného fee535e5. Starý WIP Data je zaznamenaný samostatně v `06c34051` a do main se znovu nepřebírá. Willovo nesouvisející WIP zůstává zachované.

Další krok:
- Uložit konkrétní nový commit druhého obrazu a potvrdit čisté pracovní kopie; poté počkat na Mílovo rozhodnutí o novém pokusu nasazení.

Navrhované další kroky:
- Druhý obraz samostatně projít na Mílově zařízení a případně vydat po jeho pokynu. Produkční Pages po zrušeném nasazení zatím není přejímka nové šestky.

Technický důkaz:
- Plná místní brána 2972 OK (5 SKIP), 665,420 s unit; 57 cílených kontrol PASS, 17/17 MP3 decode, 27 HTTP souborů přesné. Skutečné Safari: obraz Ollie, Bunny 10/10, Again, viditelné postavy a podběrák. První Azure podklady beze změny. První Terra receipt `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deployment uncertain; GitHub Pages run `42839271179` po 600000 ms syncing_files deployment zrušil. Po zrušení HTML 404. Výsledkový report zachovává první neúspěšný běh bez přepisu.


### 2026-11-10 16:33 CET — Třetí část: Freddieho skok a rozhovor ve vodě

Hotovo:
- Po Olliem pokračuje třetí část s osmi přesnými replikami, dvěma schválenými ilustracemi 03/031 a osmi novými anglickými MP3. Obraz se mění před Bunnyho otázkou 4/8; čítač pokračuje do 8/8, Repeat zachová aktuální ilustraci.

Rozhodnutí:
- Míla zadal pokračovat třetí částí. Nejde o schválení nového pokusu nasazení. Vývoj zůstává v Datově worktree; Willův main a zaparkované WIP se nemění. Historická první release účtenka zůstává beze změny. Další části se nyní neimplementují.

Technický důkaz:
- 59 cílených kontrol PASS a po finálním CSS 21 relevantních PASS. Přechod 2 → 3, 03 → 031, Repeat po chybě, pozdní callbacky a restart ověřené v Node VM. Dekódování 25/25, shodné mirrory a 39 HTTP souborů s přesnými bajty. Plná brána třetí části: 2974 testů OK (5 SKIP), 620,446 s unit.
- 8 unikátních Azure požadavků, 458 SSML znaků z limitu 500, −10 %, Freddie Guy / Dotty Jenny. 23 starších podkladů a dvě původní raw účtenky SHA-256 beze změny. Žádné opakování placeného požadavku. Report `reports/mmtx_scene06_picture3_20261110.md`.

Rizika a další krok:
- Obě nové ilustrace a hlasy čekají na místní přejímku na Mílově zařízení včetně fyzického iPhonu. Obrazy 2+3 nejsou publikované tímto krokem; případné vydání vyžaduje samostatné zadání. Další krok je přejímka nebo další vývoj podle Míly.
