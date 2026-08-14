<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-14 09:09 CEST

### Hotovo
- Prototyp nyní obsahuje třetí výslech Sunnyho s vlastním obrazem a pevným hlasem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Ručně ověřit třetí výslech, Sunnyho hlas a klikací místo na iPhonu nebo Macu

### Rozhodnutí
- Sunny používá kanonický hlas en-US-MichelleNeural

### Navrhované další kroky
- Zapojit čtvrtý výslech Fiony
- Poté doplnit Brunův výslech, počítání ovcí a otevření branky

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `6a65af50bf67`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `6a65af50bf67` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-14T06:24:02+00:00.
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
