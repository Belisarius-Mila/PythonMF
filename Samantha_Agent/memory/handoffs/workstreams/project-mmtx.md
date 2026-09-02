<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno produkčním dorovnáním: 2026-09-02 21:49 CEST

### Hotovo
- Pátá scéna je obsahově i technicky dokončená: Fiona přejde, Bruno převezme Bunnyho těžký batoh a vede ho přes most, Brunova lampa spadne do vody a Logan ji zachrání.
- Čtyři nové situační obrazy používají hladký 3D standard, rozměr 1672 x 941 a produkční WebP q90; zdrojová PNG zůstávají zachovaná.
- Scéna má 36 vět a 72 pevných EN/CZ MP3, tři nové klikací úkoly a závěr `To the lake!`.
- Dokončená Harryho scéna 4 nyní nabízí přímé pokračování do scény 5.
- Commit `d0fd66c3c581` je pushnutý a úspěšně publikovaný na GitHub Pages.

### Otevřeno
- Ruční vizuální a zvukový smoke celé scény na Macu a iPhonu zůstává otevřený.

### Rizika
- Browserový backend nebyl v této relaci dostupný; interaktivní průchod proto není vydáván za provedený.

### Další krok
- Projít celou scénu 5 na Macu a iPhonu, zejména nové hotspoty Fiony, Bruna a Logana a všech 72 stop.

### Rozhodnutí
- Logan zachrání Brunovu lampu ještě v páté scéně; tím se uzavírá pomoc kamarádům i význam nové postavy.
- Každá další věta se zpřístupní přes `Next`, `Repeat` opakuje pouze právě zobrazenou větu a klikací úkoly zůstávají bez trestu.

### Navrhované další kroky
- Po produkčním retestu případně upravit pouze potvrzené umístění hotspotů nebo hlasitost konkrétní stopy.
- Teprve po schválení závěru navrhnout obsah scény 6.

### Technický stav checkpointu
- Celý MMTX balík prošel 61/61 testy, generátor ověřil 72/72 MP3, oba JavaScripty prošly `node --check` a `git diff --check` je čistý.
- `docs` a `MatysekANJ/web_mmtx` jsou pro scény 4 a 5 byte-identické.
- Serverová operace `mmtx_pages_publish_current_main` pushnula 1 commit; workflow `33674738263` a deployment `6230419264` odpovídají přesně commitu `d0fd66c3c581` a veřejný smoke vrátil HTTP 200.
- Veřejné `index.html`, `script.js`, `audio_manifest.js`, závěrečný obraz a reprezentativní Loganovo MP3 jsou SHA-256 shodné s lokální produkční kopií.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: MMTX

Nazev: MMTX
Pracovni proud: project-mmtx
Typ: Project
Priorita: 1
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

### Automatický checkpoint 2026-07-21 07:06 CEST

- Pracovní proud: `project-mmtx`
- Souhrn: Živý zapisovací pilot MMTX fáze 4.5 prošel
- Ověření: plná Cockpit brána: 965 testů, 281.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (1): `MatysekANJ/PROJECT_NOTES_MMTX.md`
- Commit: `Document MMTX Human-Adam workstream`
- Další krok: Ověřit čistý main, synchronizaci legacy workspaces a vznik kanonického MMTX handoffu a TVBCP

### Terminálový checkpoint 2026-08-12 19:17 CEST

- Pracovní proud: `project-mmtx`
- Souhrn: Samostatný prototyp Harry–Benji je připravený mimo živou třetí scénu.
- Hotovo: Režimy `EN` a `EN + CZ`, systémová výslovnost, bezpečné `Repeat`, výběr Benjiho a úkol `YES/NO`; schválený obrazový kandidát je součástí prototypu.
- Ověření: 3/3 cílené testy, JavaScript syntaxe a `git diff --check` prošly; obrazový soubor odpovídá schválenému private kandidátu.
- Rozhodnutí: Prototyp zůstává samostatný a zatím není napojený do produkčního průchodu Forest Journey.
- Další krok: Ručně ověřit vzhled, ovládání a systémové hlasy na Macu a iPhonu.
- Navrhované další kroky: Po ověření doplnit výslech dalších postav; následně počítání pěti ovcí a otevření branky.
- Bezpečnost: Private zdrojový kandidát ani interní identifikátory nejsou v handoffu uloženy.

### Automatický checkpoint 2026-08-12 21:13 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Benji v prototypu upřednostňuje Andrewa a používá pouze mužské anglické alternativy; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`
- Commit: `Prevent female fallback for Benji voice`
- Další krok: Poslechnout Benjiho hlas v prototypu na iPhonu a Macu

### Automatický checkpoint 2026-08-13 07:18 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Benji v prototypu používá čtyři pevná Andrew MP3 se spolehlivým přehráváním i fallbackem; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_hello_we_are_friendly_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_i_have_a_map_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_i_help_little_animals_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_no_i_do_not_chase_sheep_en.mp3`
- Commit: `Add fixed Andrew audio to Harry prototype`
- Další krok: Poslechnout celý prototyp na iPhonu a Macu a potvrdit charakter i hlasitost Benjiho hlasu

### Automatický checkpoint 2026-08-13 07:57 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Prototyp pokračuje druhým výslechem Bunnyho s interaktivní otázkou a pevným hlasem Ana; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bunny_i_am_bunny_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bunny_i_only_want_to_go_to_the_lake_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bunny_no_i_have_my_own_carrots_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bunny_not_me_en.mp3`
- Commit: `Add Harry and Bunny interrogation prototype`
- Další krok: Poslechnout druhý výslech na iPhonu a Macu a ověřit Bunnyho hlas i tempo

### Automatický checkpoint 2026-08-13 11:20 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Vznikly dvě poslechové ukázky Benjiho s hlasem klonovaným podle první scény; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_f5_candidate_hello_we_are_friendly_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_benji_f5_candidate_no_i_do_not_chase_sheep_en.mp3`
- Commit: `Add F5 Benji voice candidates`
- Další krok: Poslechnout oba kandidáty a rozhodnout, zda jimi nahradit Andrewův hlas

### Automatický checkpoint 2026-08-13 18:16 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Čtyři výslechy mají připravené vlastní obrazové scény s příslušným zvířátkem v popředí; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.7 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/harry_interrogation_benji_01.png`, `docs/scene04_harry_guard_prototype/harry_interrogation_bunny_01.png`, `docs/scene04_harry_guard_prototype/harry_interrogation_fiona_01.png`, `docs/scene04_harry_guard_prototype/harry_interrogation_sunny_01.png`
- Commit: `Add Harry interrogation scene artwork`
- Další krok: Zapojit obrazy do jednotlivých fází dialogu a připravit třetí výslech Sunnyho

### Automatický checkpoint 2026-08-13 22:50 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Sérii výslechů doplnil pátý obraz s Brunem a Harrym; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/harry_interrogation_bruno_01.png`
- Commit: `Add Bruno interrogation artwork`
- Další krok: Zapojit pět obrazů do jednotlivých výslechů prototypu

### Automatický checkpoint 2026-08-13 23:03 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Opravený Brunův výslech nyní zachovává celou skupinu včetně jasně viditelného Benjiho
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/harry_interrogation_bruno_02.png`
- Commit: `Correct Bruno artwork with Benji`
- Další krok: Použít opravenou verzi při zapojení obrazů do prototypu

### Automatický checkpoint 2026-08-14 07:42 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Druhý výslech nyní používá vlastní Bunnyho obraz a odpovídající klikací místa; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`
- Commit: `Switch prototype to Bunny interrogation scene`
- Další krok: Ručně ověřit přechod obrazu a klepnutí na Bunnyho na iPhonu nebo Macu

### Automatický checkpoint 2026-08-14 09:09 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Prototyp nyní obsahuje třetí výslech Sunnyho s vlastním obrazem a pevným hlasem; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/audio/english/scene04_sunny_hello_i_am_sunny_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_sunny_i_want_to_go_to_the_lake_with_my_friends_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_sunny_no_i_have_my_own_nuts_en.mp3`
- Commit: `Add Harry and Sunny interrogation prototype`
- Další krok: Ručně ověřit třetí výslech, Sunnyho hlas a klikací místo na iPhonu nebo Macu

### Automatický checkpoint 2026-08-14 10:01 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Prototyp nyní obsahuje čtvrtý výslech Fiony s vlastním obrazem a pevným hlasem; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/audio/english/scene04_fiona_hi_i_am_fiona_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_fiona_i_want_to_go_to_the_lake_with_my_friends_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_fiona_no_i_do_not_catch_chickens_en.mp3`
- Commit: `Add Harry and Fiona interrogation prototype`
- Další krok: Ručně ověřit Fionin výslech, hlas a klikací místo na iPhonu nebo Macu

### Automatický checkpoint 2026-08-14 10:56 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Fionin blikající box nyní spolehlivě přijímá první klepnutí i v překryvu s ostatními postavami; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/styles.css`
- Commit: `Fix overlapping Fiona hotspot`
- Další krok: Ověřit Fionin výslech jedním klepnutím na iPhonu nebo Macu

### Automatický checkpoint 2026-08-14 11:48 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Prototyp nyní obsahuje Brunův pátý výslech s vlastním obrazem a hlubším hlasem; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bruno_hello_i_am_bruno_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bruno_i_want_to_go_to_the_lake_with_my_friends_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_bruno_no_i_do_not_dig_under_fences_en.mp3`
- Commit: `Add Bruno interrogation to Harry prototype`
- Další krok: Ručně ověřit Brunův hlas a klikací oblast v nasazeném prototypu

### Automatický checkpoint 2026-08-15 11:11 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Závěr prototypu nabízí slovníček 22 nových slov s anglickou výslovností a volitelnou češtinou; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (26): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/styles.css`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_answer_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_badger_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_believe_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_catch_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_chase_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_chicken_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_closed_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_come_closer_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_dig_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_eat_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_fence_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_fox_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_gate_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_little_animals_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_own_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_question_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_rabbit_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_sheep_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_squirrel_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_trust_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_under_en.mp3`, `docs/scene04_harry_guard_prototype/audio/english/scene04_vocab_yard_en.mp3`
- Commit: `Add final glossary to Harry prototype`
- Další krok: Ručně ověřit slovníček, jeho rozložení a výslovnost na iPhonu

### Automatický checkpoint 2026-08-16 17:58 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Harry se představí před prvním výslechem a další repliky se přehrávají jednotlivě až po stisknutí Next; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `docs/scene04_harry_guard_prototype/styles.css`
- Commit: `Přidat krokování výslechů tlačítkem Next`
- Další krok: Ručně ověřit tempo a rozložení tlačítka Next na iPhonu nebo Macu

### Automatický checkpoint 2026-08-16 22:15 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Harry po posledním výslechu dovolí přátelům pokračovat otevřenou brankou; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`
- Commit: `Doplnit závěrečnou Harryho repliku`
- Další krok: Ověřit závěrečnou repliku, hlas a přechod do dokončené scény na iPhonu

### Automatický checkpoint 2026-08-17 22:23 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Repeat nyní zopakuje každou právě zobrazenou větu bez posunutí nebo přerušení dialogu; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`
- Commit: `Povolit Repeat u každé věty výslechu`
- Další krok: Ručně ověřit Repeat a Next v celém výslechu na iPhonu nebo Macu

### Automatický checkpoint 2026-08-25 13:17 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: MMTX má samostatné přání Jane s pozměněnými texty, anglickou výslovností jména a vlastními zvukovými stopami.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (61): `MatysekANJ/web_mmtx/index.html`, `MatysekANJ/web_mmtx/script_intro_v2.js`, `MatysekANJ/web_mmtx/styles_intro_v2.css`, `docs/index.html`, `docs/script_intro_v2.js`, `docs/styles_intro_v2.css`, `MatysekANJ/web_mmtx/scene_jane_birthday/README.md`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_01_benji_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_02_benji_wish_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_03_bunny_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_04_bunny_wish_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_05_bruno_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_06_bruno_wish_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_07_fiona_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_08_fiona_wish_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_09_sunny_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/czech/jane_birthday_10_sunny_wish_cz.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_01_benji_hello_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_02_benji_wish_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_03_bunny_hello_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_04_bunny_wish_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_05_bruno_hello_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_06_bruno_wish_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_07_fiona_hello_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_08_fiona_wish_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_09_sunny_hello_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_10_sunny_wish_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/audio/english/jane_birthday_11_song_en.mp3`, `MatysekANJ/web_mmtx/scene_jane_birthday/index.html`, `MatysekANJ/web_mmtx/scene_jane_birthday/jane_birthday_clearing.png`, `MatysekANJ/web_mmtx/scene_jane_birthday/jane_birthday_clearing.svg`, `MatysekANJ/web_mmtx/scene_jane_birthday/script.js`, `MatysekANJ/web_mmtx/scene_jane_birthday/styles.css`, `Samantha_Agent/tests/test_mmtx_jane_birthday.py`, `docs/scene_jane_birthday/README.md`, `docs/scene_jane_birthday/audio/czech/jane_birthday_01_benji_hello_cz.mp3`, `docs/scene_jane_birthday/audio/czech/jane_birthday_02_benji_wish_cz.mp3`, `docs/scene_jane_birthday/audio/czech/jane_birthday_03_bunny_hello_cz.mp3`, `docs/scene_jane_birthday/audio/czech/jane_birthday_04_bunny_wish_cz.mp3`, `docs/scene_jane_birthday/audio/czech/jane_birthday_05_bruno_hello_cz.mp3`, … a dalších 21
- Commit: `Přidat narozeninovou scénu Jane`
- Další krok: Ručně ověřit hlasy a výslovnost Jane na iPhonu nebo Macu a poté použít ovládací prvky Cockpitu pro checkpoint a nasazení.

### Terminálové dorovnání 2026-08-29 17:05 CEST – Pevná MP3 knihovna Harryho scény

- Pracovní proud: `project-mmtx`
- Hotovo: Harryho scéna používá 136 pevných anglických a českých stop bez systémového hlasu; commit `f1499b1` je pushnutý, Cockpit jej potvrzuje jako nasazený a Pages publikace je hashově ověřená.
- Rozhodnutí: Věcný milník patří do MMTX. Automatický zápis 16:22 pod proudem Linux zůstává pouze historickou auditní stopou.
- Rizika: Automatické směrování podle právě aktivního proudu nepoznalo změnu tématu; při dalším vývoji je nutné nejprve otevřít MMTX.
- Další krok: Ručně poslechnout celý průchod na Linuxu a Macu.
- Ověření: cílené testy 5/5, vzdálená brána 1468/1468, smoke 5/5 a veřejné hash shody HTML, JavaScriptu, manifestu i obou jazykových MP3.

### Praktické uzavření 2026-08-29 17:30 CEST – Linuxové přizpůsobení potvrzeno

- Pracovní proud: `project-mmtx`
- Hotovo: Míla prakticky vyzkoušel aktuální MMTX na Linux PC a potvrdil, že pevné MP3 fungují dobře. Linuxový retest Harryho scény je tím uzavřený bez známého blokátoru.
- Rozhodnutí: Pevné MP3 řízené manifestem zůstávají kanonickým multiplatformním řešením bez `speechSynthesis`.
- Rizika: Při změně dialogového textu je nutné společně aktualizovat příslušné MP3, manifest, produkční kopii a zrcadlo MMTX.
- Další krok: Pokračovat dalším vývojem v aktivním Human–Adam proudu `project-mmtx`.
- Ověření: Praktické potvrzení Míly na Linux PC doplňuje dřívější cílené testy 5/5, vzdálenou bránu 1468/1468, smoke 5/5 a veřejné hashové shody publikace.

### Automatický checkpoint 2026-08-29 18:13 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Scéna 2 používá 55 pevných anglických a českých stop řízených manifestem a funguje bez systémového hlasu.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (64): `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/README.md`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/README.md`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/index.html`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/script.js`, `docs/scene02_sunnys_lost_nuts/README.md`, `docs/scene02_sunnys_lost_nuts/audio/README.md`, `docs/scene02_sunnys_lost_nuts/index.html`, `docs/scene02_sunnys_lost_nuts/script.js`, `MatysekANJ/build_scene02_audio.py`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_01_sunny_no_nuts_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_02_fiona_benji_nuts_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_03_benji_map_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_04_fiona_bunny_nuts_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_05_bunny_carrot_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_06_bruno_bag_wait_second_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_07_bruno_look_inside_friends_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_08_sunny_my_nuts_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_09_fiona_ready_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_main_help_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_prompt_tap_bunny_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_bag_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_carrot_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_do_you_have_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_does_he_have_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_happy_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_i_dont_have_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_i_have_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_look_inside_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_map_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_nuts_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_ready_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_wait_cz.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/english/scene02_vocab_happy_en.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/english/scene02_vocab_ready_en.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio/english/scene02_vocab_wait_en.mp3`, `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/audio_manifest.js`, `Samantha_Agent/tests/test_mmtx_scene02_audio.py`, `docs/scene02_sunnys_lost_nuts/audio/czech/scene02_01_sunny_no_nuts_cz.mp3`, `docs/scene02_sunnys_lost_nuts/audio/czech/scene02_02_fiona_benji_nuts_cz.mp3`, `docs/scene02_sunnys_lost_nuts/audio/czech/scene02_03_benji_map_cz.mp3`, … a dalších 24
- Commit: `Nahradit systémové čtení scény 2 pevnými MP3`
- Další krok: Prakticky projít a poslechnout celou scénu 2 na Linuxu.

### Automatický checkpoint 2026-08-29 19:03 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Scéna 3 nyní používá úplnou pevnou anglickou a českou audio knihovnu řízenou manifestem bez systémového hlasu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (80): `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/README.md`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/index.html`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/script.js`, `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene03_journey_to_the_lake/README.md`, `docs/scene03_journey_to_the_lake/index.html`, `docs/scene03_journey_to_the_lake/script.js`, `MatysekANJ/build_scene03_audio.py`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_all_lets_go_left_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_all_thank_you_fiona_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_hello_i_am_benji_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_i_am_not_scared_i_will_go_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_i_dont_know_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_look_two_paths_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_thank_you_crow_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_benji_thank_you_for_the_warning_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bruno_i_am_pushing_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bruno_let_us_drink_in_the_forest_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bruno_no_this_way_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_bears_no_thank_you_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_how_do_we_get_water_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_i_am_scared_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_i_dont_know_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_this_way_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_bunny_water_we_have_water_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_caw_bye_bye_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_caw_go_left_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_caw_no_no_go_left_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_it_is_a_deep_valley_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_left_is_good_right_is_bad_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_crow_maybe_bears_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_bruno_push_it_up_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_i_know_sunny_jump_on_the_handle_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_look_a_pump_but_the_bucket_is_empty_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_me_too_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_okay_left_it_is_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_the_pump_needs_help_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_fiona_wait_wait_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_horse_careful_a_dog_lives_there_cz.mp3`, `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/audio/czech/scene03_horse_come_drink_some_water_cz.mp3`, … a dalších 40
- Commit: `Nahradit systémové čtení scény 3 pevnými MP3`
- Další krok: Prakticky projít a poslechnout celou scénu 3 na Linuxu.

### Produkční dorovnání 2026-08-29 19:52 CEST – Scény 2 a 3 nasazeny na Pages

- Pracovní proud: `project-mmtx`
- Hotovo: Pages workflow publikoval commit `933834f`; scény 2 a 3 s pevnými MP3 jsou veřejně dostupné.
- Rozhodnutí: Push a Pages nasazení jsou dva samostatné kroky a produkční stav se potvrzuje až deploymentem a veřejnou kontrolou.
- Rizika: Bez výslovného spuštění Pages workflow může GitHub obsahovat novější MMTX než produkce.
- Další krok: Prakticky projít a poslechnout scény 2 a 3 na Linuxu.
- Ověření: run `33266361424` uspěl; veřejné manifesty a reprezentativní české MP3 obou scén jsou hashově shodné s lokální produkční kopií.

### Samoobslužné nasazení 2026-08-29 20:44 CEST – MMTX p+n živě dokončeno

- Pracovní proud: `project-mmtx`
- Hotovo: Human–Adam přímým `p+n` publikoval aktuální čistý GitHub main `72aedbf` a vrátil pravdivou dokončovací účtenku.
- Rozhodnutí: Další dokončený MMTX vývoj končit v tomto proudu pokynem `p+n`; samotný push není produkční důkaz.
- Další krok: Prakticky projít a poslechnout scény 2 a 3 na Linuxu.
- Ověření: run `33269031345`, deployment `6158917594`, přesná shoda commitu a veřejný HTTP 200.

### Regresní nasazení 2026-08-29 21:01 CEST – MMTX p+n nezávislé na modelové obálce

- Pracovní proud: `project-mmtx`
- Hotovo: Opravený Human–Adam přímým `p+n` publikoval aktuální čistý main `0230cf5` a vrátil úplnou serverovou účtenku.
- Rozhodnutí: Modelová obálka neautorizuje ani nevolí produkční operaci; rozhoduje přesný pokyn Míly a deklarovaný Pages cíl MMTX.
- Další krok: Prakticky projít a poslechnout scény 2 a 3 na Linuxu.
- Ověření: run `33269734786`, deployment `6159053676`, přesná shoda commitu a veřejný HTTP 200.

### Automatický checkpoint 2026-08-29 21:27 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: První scéna Cesty k jezeru nyní používá 49 pevných anglických a českých MP3 řízených manifestem bez systémového hlasu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (80): `MatysekANJ/web_mmtx/index.html`, `MatysekANJ/web_mmtx/script_intro_v2.js`, `Samantha_Agent/tests/test_mmtx_jane_birthday.py`, `docs/index.html`, `docs/script_intro_v2.js`, `MatysekANJ/build_scene01_audio.py`, `MatysekANJ/web_mmtx/audio/czech/scene01_01_benji_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_02_bunny_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_03_benji_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_04_bruno_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_05_fiona_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_06_sunny_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_07_fiona_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_08_bruno_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_09_benji_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_10_sunny_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_11_fiona_dialogue_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_ui_complete_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_ui_help_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_ui_intro_help_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_friends_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_going_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_hello_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_i_am_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_lake_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_together_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_too_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/scene01_vocab_we_are_cz.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_great_open_the_door_or_run_again_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_tap_benji_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_tap_bruno_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_tap_bunny_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_tap_fiona_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_ui_tap_sunny_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_friends_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_going_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_hello_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_i_am_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_lake_en.mp3`, `MatysekANJ/web_mmtx/audio/english/scene01_vocab_together_en.mp3`, … a dalších 40
- Commit: `Nahradit systémový hlas první scény pevnými MP3`
- Další krok: Po potvrzeném checkpointu publikovat aktuální MMTX pomocí p+n a scénu poslechnout na Linuxu.

### Automatický checkpoint 2026-08-30 12:17 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Forest School nyní používá kompletní knihovnu 203 pevných anglických a českých stop bez systémového hlasu a Benjiho ukázka správně odpovídá No, it isn’t.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (80): `MatysekANJ/web_mmtx/index.html`, `MatysekANJ/web_mmtx/script_intro_v2.js`, `Samantha_Agent/tests/test_mmtx_jane_birthday.py`, `Samantha_Agent/tests/test_mmtx_scene01_audio.py`, `docs/index.html`, `docs/script_intro_v2.js`, `MatysekANJ/build_forest_school_audio.py`, `MatysekANJ/web_mmtx/audio/czech/forest_school_lesson_choice_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_lesson_preview_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_apple_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_bag_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_ball_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_banana_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_bed_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_bike_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_block_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_boat_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_book_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_boots_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_box_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_bread_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_bus_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_cake_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_car_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_chair_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_cloud_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_cookie_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_corn_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_cup_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_doll_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_flower_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_fork_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_grape_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_hat_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_house_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_key_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_kite_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_lamp_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_leaf_cz.mp3`, `MatysekANJ/web_mmtx/audio/czech/forest_school_word_milk_cz.mp3`, … a dalších 40
- Commit: `Doplnit pevná MP3 pro Forest School`
- Další krok: Po potvrzeném checkpointu scénu poslechnout a samostatně spustit p+n.

### Automatický checkpoint 2026-08-31 10:24 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Schválený Logan v neoprenu a základ rozvodněného potoka jsou bezpečně uložené v obou projektových kopiích; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `MatysekANJ/web_mmtx/scene05_log_bridge/assets/logan_neoprene_reference.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_stream_base.png`, `docs/scene05_log_bridge/assets/logan_neoprene_reference.png`, `docs/scene05_log_bridge/scene05_stream_base.png`
- Commit: `Uložit obrazové podklady scény 5`
- Další krok: Vytvořit první dějový obraz se skupinou zvířátek před rozvodněným potokem

### Automatický checkpoint 2026-08-31 11:24 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Vznikly dvě výrazně lehčí WebP varianty potoka a stránka pro přímé porovnání na velké obrazovce
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 9.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_stream_base_q85.webp`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_stream_base_q90.webp`, `MatysekANJ/web_mmtx/scene05_log_bridge/webp_quality_pilot.html`, `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `docs/scene05_log_bridge/scene05_stream_base_q85.webp`, `docs/scene05_log_bridge/scene05_stream_base_q90.webp`, `docs/scene05_log_bridge/webp_quality_pilot.html`
- Commit: `Přidat WebP pilot scény 5`
- Další krok: Porovnat q90 a q85 na 22palcové obrazovce a vybrat produkční kvalitu

### Kanonické produkční pravidlo 2026-08-31 12:15 CEST

- Rozhodnutí: Všechny obrázky scén MMTX se před nasazením na produkci zmenší a použije se jejich ověřená lehčí produkční varianta.
- Bezpečnost: Zdrojové originály zůstávají zachované; optimalizace je nesmí tiše přepsat a produkční formát nebo kvalita se nejprve vizuálně ověří.
- Další krok: Dokončit bod 1 — porovnat WebP q90 a q85 scény 5 a vybrat produkční kvalitu, která se následně zapojí do scény.

### Volba produkční kvality 2026-08-31 12:22 CEST

- Hotovo: Míla zvolil první WebP variantu, q90; porovnávací stránka ji nyní otevírá a označuje jako vybranou produkční kvalitu.
- Rozhodnutí: Pro obraz potoka ve scéně 5 je produkční volbou WebP q90. Původní PNG i q85 zůstávají zachované pro audit a nic se zatím nenasazuje.
- Ověření: Cílená regrese prošla 5/5, q90 má původní rozlišení 1672 × 941, je menší než PNG a produkční i zdrojová kopie stránky jsou shodné.
- Riziko: Volba kvality sama ještě nezapojuje obraz do funkční scény 5.
- Další krok: Zapojit `scene05_stream_base_q90.webp` jako obrazový základ scény 5 bez přepsání zdrojového PNG.

### Automatický checkpoint 2026-08-31 15:21 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Scéna 5 má samostatně otevřitelný responzivní základ s WebP q90 a PNG fallbackem; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `MatysekANJ/web_mmtx/scene05_log_bridge/index.html`, `MatysekANJ/web_mmtx/scene05_log_bridge/styles.css`, `docs/scene05_log_bridge/index.html`, `docs/scene05_log_bridge/styles.css`
- Commit: `Zapojit q90 základ scény 5`
- Další krok: Ručně zkontrolovat vzhled a potom připravit první dějový obraz se skupinou zvířátek

### Automatický checkpoint 2026-08-31 15:54 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: První obraz ukazuje pět kamarádů u rozvodněného potoka a Logana ve vodě; připravena je lehká q90 varianta; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_arrival_logan_01_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_arrival_logan_01.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_arrival_logan_01_q90.webp`, `docs/scene05_log_bridge/assets/scene05_arrival_logan_01_source.png`, `docs/scene05_log_bridge/scene05_arrival_logan_01.png`, `docs/scene05_log_bridge/scene05_arrival_logan_01_q90.webp`
- Commit: `Přidat první dějový obraz scény 5`
- Další krok: Potvrdit obraz a zapojit jej jako první dějový stav scény 5

### Automatický checkpoint 2026-08-31 17:15 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Scéna 5 má první dějový průchod s Loganem, dialogem po větách, pevnými EN/CZ MP3 a stavbou mostu ze tří klád
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.; Aktivní relace má neuzavřenou nejistotu doručení.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (55): `MatysekANJ/web_mmtx/scene05_log_bridge/index.html`, `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `docs/scene05_log_bridge/index.html`, `MatysekANJ/build_scene05_audio.py`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_benji_bridge_gone_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_bunny_stream_wide_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_fiona_get_across_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_bridge_ready_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_can_help_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_hello_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_one_log_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_strong_logs_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_tap_logs_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_three_logs_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_two_logs_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_benji_bridge_gone_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_bunny_stream_wide_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_fiona_get_across_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_bridge_ready_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_can_help_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_hello_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_one_log_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_strong_logs_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_tap_logs_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_three_logs_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_two_logs_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio_manifest.js`, `MatysekANJ/web_mmtx/scene05_log_bridge/interaction.css`, `MatysekANJ/web_mmtx/scene05_log_bridge/script.js`, `Samantha_Agent/tests/test_mmtx_scene05_first_interaction.py`, `docs/scene05_log_bridge/audio/czech/scene05_benji_bridge_gone_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_bunny_stream_wide_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_fiona_get_across_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_bridge_ready_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_can_help_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_hello_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_one_log_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_strong_logs_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_tap_logs_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_three_logs_cz.mp3`, … a dalších 15
- Commit: `Complete scene 5 opening interaction`
- Další krok: Ručně ověřit vzhled, ovládání a zvuk scény 5 na Macu a iPhonu; potom rozhodnout o napojení ze scény 4

### Produkční implementace 2026-09-01 12:03 CEST – schválený most v úvodu scény 5

- Pracovní proud: `project-mmtx`
- Hotovo: Kanonická scéna 5 i zdrojový mirror používají schválený obraz se zachovanými základy mostu, tři neprůhledné alfa sprity pokroucených kmenů a přesný schválený finální obraz mostu. Každé klepnutí položí jeden kmen obloukovým letem; po třetím dosednutí následuje plynulé překrytí finálním obrazem.
- Zachováno: Původní pořadí dialogů, ovládání `Next` a `Repeat`, volba EN / EN + CZ i všech 22 pevných MP3.
- Otevřeno: Automatizované prohlížečové připojení nebylo v relaci dostupné; před publikací zbývá krátký ruční vizuální retest na Macu a iPhonu.
- Rizika: Tento zápis ani lokální commit nepotvrzují push, Pages publikaci nebo veřejný produkční stav.
- Další krok: Ručně projít tři klepnutí a finální obraz; po schválení samostatně autorizovat MMTX `p+n`.
- Ověření: JavaScript syntaxe OK, audio kontrola 22/22, cílené testy 18/18, obě kopie scény jsou byte-identické a `git diff --check` je čistý.

### Automatický checkpoint 2026-09-01 21:47 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Scéna 5 pokračuje interaktivním přechodem Benjiho a Sunny a končí Bunnym, který se bojí přejít.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (50): `MatysekANJ/build_scene05_audio.py`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio_manifest.js`, `MatysekANJ/web_mmtx/scene05_log_bridge/index.html`, `MatysekANJ/web_mmtx/scene05_log_bridge/interaction.css`, `MatysekANJ/web_mmtx/scene05_log_bridge/script.js`, `Samantha_Agent/tests/test_mmtx_scene05_first_interaction.py`, `docs/scene05_log_bridge/audio_manifest.js`, `docs/scene05_log_bridge/index.html`, `docs/scene05_log_bridge/interaction.css`, `docs/scene05_log_bridge/script.js`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_benji_across_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_benji_sunny_across_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_benji_bridge_safe_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_benji_go_first_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_benji_tap_benji_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_bunny_bunny_scared_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_logan_who_first_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_sunny_my_turn_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_sunny_tap_sunny_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/czech/scene05_sunny_three_jumps_cz.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_benji_bridge_safe_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_benji_go_first_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_benji_tap_benji_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_bunny_bunny_scared_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_logan_who_first_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_sunny_my_turn_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_sunny_tap_sunny_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/audio/english/scene05_sunny_three_jumps_en.mp3`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_benji_across_q90.webp`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_benji_sunny_across_q90.webp`, `docs/scene05_log_bridge/assets/scene05_benji_across_source.png`, `docs/scene05_log_bridge/assets/scene05_benji_sunny_across_source.png`, `docs/scene05_log_bridge/audio/czech/scene05_benji_bridge_safe_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_benji_go_first_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_benji_tap_benji_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_bunny_bunny_scared_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_logan_who_first_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_sunny_my_turn_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_sunny_tap_sunny_cz.mp3`, `docs/scene05_log_bridge/audio/czech/scene05_sunny_three_jumps_cz.mp3`, … a dalších 10
- Commit: `Extend Scene 5 with Benji and Sunny crossing`
- Další krok: Ručně ověřit přechody obrazů, klikací oblasti a zvuk na Macu nebo iPhonu.

### Automatický checkpoint 2026-09-01 22:31 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Benjiho přechod nyní používá hladkou 3D grafiku odpovídající původnímu MMTX při zachování plného rozlišení a lehkého WebP q90.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (7): `MatysekANJ/web_mmtx/scene05_log_bridge/index.html`, `Samantha_Agent/tests/test_mmtx_scene05_first_interaction.py`, `docs/scene05_log_bridge/index.html`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_benji_across_smooth_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_benji_across_smooth_q90.webp`, `docs/scene05_log_bridge/assets/scene05_benji_across_smooth_source.png`, `docs/scene05_log_bridge/scene05_benji_across_smooth_q90.webp`
- Commit: `Smooth Benji crossing artwork in scene 5`
- Další krok: Ověřit pilot na velké obrazovce a po schválení stejným stylem opravit ostatní situační obrazy scény 5.

### Automatický checkpoint 2026-09-01 22:44 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Úvod, hotový most i přechod Benjiho se Sunny nyní používají jednotnou hladkou 3D grafiku a jsou zapojené v lokální scéně 5.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (16): `MatysekANJ/web_mmtx/scene05_log_bridge/index.html`, `Samantha_Agent/tests/test_mmtx_scene05_first_interaction.py`, `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `docs/scene05_log_bridge/index.html`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_benji_sunny_across_smooth_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_log_bridge_complete_smooth_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/assets/scene05_log_bridge_supports_smooth_source.png`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_benji_sunny_across_smooth_q90.webp`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_log_bridge_complete_smooth_q90.webp`, `MatysekANJ/web_mmtx/scene05_log_bridge/scene05_log_bridge_supports_smooth_q90.webp`, `docs/scene05_log_bridge/assets/scene05_benji_sunny_across_smooth_source.png`, `docs/scene05_log_bridge/assets/scene05_log_bridge_complete_smooth_source.png`, `docs/scene05_log_bridge/assets/scene05_log_bridge_supports_smooth_source.png`, `docs/scene05_log_bridge/scene05_benji_sunny_across_smooth_q90.webp`, `docs/scene05_log_bridge/scene05_log_bridge_complete_smooth_q90.webp`, `docs/scene05_log_bridge/scene05_log_bridge_supports_smooth_q90.webp`
- Commit: `Unify Scene 5 artwork with smooth MMTX style`
- Další krok: Vizuálně ověřit všechny přechody scény 5 na 22palcové obrazovce.

### Terminálový checkpoint 2026-09-02 21:04 CEST

- Pracovní proud: `project-mmtx`
- Hotovo: Pátá scéna pokračuje přes Fionin přechod, Brunovu pomoc Bunnymu a pád lampy až k potvrzené Loganově záchraně; scéna 4 nyní vede do dokončené scény 5.
- Rozhodnutí: Logan zachrání Brunovu lampu ještě v páté scéně; další věty zůstávají krokované přes `Next` a `Repeat` opakuje jen aktuální větu.
- Ověření: 61/61 MMTX testů, 72/72 pevných EN/CZ MP3, JavaScript syntaxe, byte-identické produkční kopie a čistý `git diff --check`.
- Riziko: Browserový backend nebyl dostupný, proto zůstává otevřený reálný vizuální a zvukový smoke na Macu a iPhonu.
- Další krok: Po samostatném Milově potvrzení provést MMTX `p+n` a následný ruční smoke.

### Produkční dorovnání 2026-09-02 21:49 CEST – MMTX p+n dokončeno

- Pracovní proud: `project-mmtx`
- Hotovo: Serverová operace `mmtx_pages_publish_current_main` pushnula jediný čekající commit `d0fd66c3c581` a publikovala dokončenou scénu 5 na GitHub Pages.
- Rozhodnutí: Produkční důkaz tvoří až shoda commitu, úspěšný workflow, deployment a veřejný HTTP smoke; samotný push nestačí.
- Ověření: workflow `33674738263`, deployment `6230419264`, přesný commit `d0fd66c3c581`, veřejný HTTP 200 a SHA-256 shoda pěti reprezentativních souborů.
- Riziko: Automatizovaný browser nebyl dostupný, proto zůstává otevřený ruční vizuální a zvukový smoke.
- Další krok: Projít celou scénu 5 na Macu a iPhonu, zejména nové hotspoty Fiony, Bruna a Logana a nové audio.
