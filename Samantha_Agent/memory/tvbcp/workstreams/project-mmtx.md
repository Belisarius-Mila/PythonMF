<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obsahově a provozně dorovnáno: 2026-08-29 17:05 CEST
- Poslední věcný MMTX checkpoint: commit `f1499b1`

### Hotovo
- Produkční webová scéna 3 pokračuje přímo do Harryho scény 4.
- Harryho scéna přehrává všech 136 anglických a českých dialogových a slovníkových stop z pevných MP3 řízených manifestem a nepoužívá `speechSynthesis`.
- GitHub `main`, Cockpit a veřejná Pages publikace byly ověřeny na `f1499b1`.

### Otevřeno
- Ruční poslech celého průchodu scéna 3 → Harry na Linuxu a Macu.

### Rizika
- Automatický checkpoint 16:22 vznikl pod aktivním proudem Linux; historický záznam zůstává auditní stopou, ale aktuální věcná autorita je tento MMTX handoff a TVBCP.

### Další krok
- Ověřit `Next`, `Repeat`, pořadí jazyků, přirozenost hlasů a tempo; případně vyměnit jen konkrétní problematické stopy.

### Rozhodnutí
- Pevná MP3 knihovna Harryho scény patří do pracovního proudu MMTX, nikoli Linux.

### Navrhované další kroky
- Po ručním poslechu pokračovat dalším příběhovým krokem pouze z MMTX workstreamu.

### Technický stav checkpointu
- Cílené testy 5/5, vzdálená Cockpit Quality Gate 1468/1468 a Pages run `33259207533` prošly.
- Veřejný HTML, JavaScript, audio manifest a reprezentativní anglické i české MP3 jsou hashově shodné s `f1499b1`.
- Chronologické bloky níže zůstávají historickými snapshoty a nepřepisují tento aktuální souhrn.
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
