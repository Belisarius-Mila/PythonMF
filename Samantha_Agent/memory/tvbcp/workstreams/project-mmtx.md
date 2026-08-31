<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-31 10:24 CEST

### Hotovo
- Schválený Logan v neoprenu a základ rozvodněného potoka jsou bezpečně uložené v obou projektových kopiích
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Vytvořit první dějový obraz se skupinou zvířátek před rozvodněným potokem

### Rozhodnutí
- Logan používá lehký neopren bez potápěčské výstroje a prostředí má široké břehy s bobří hrází v dálce

### Navrhované další kroky
- Přidat Logana, který si skupiny všimne
- Potom připravit interakci se třemi kládami

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `901d5fef9be3`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `901d5fef9be3` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-30T20:20:14+00:00.
- Read-only živý stav: main=`aligned`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
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
