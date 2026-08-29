<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Produkční stav ověřen: 2026-08-29 19:52 CEST

### Hotovo
- Scéna 3 nyní používá úplnou pevnou anglickou a českou audio knihovnu řízenou manifestem bez systémového hlasu.
- Scény 2 a 3 jsou publikované na GitHub Pages z commitu `933834f`.

### Otevřeno
- Praktický poslech scén 2 a 3 na Linuxu.

### Rizika
- Samotný GitHub push Pages nepublikuje; je nutné spustit a ověřit samostatný Pages workflow.

### Další krok
- Prakticky projít a poslechnout celou scénu 3 na Linuxu.

### Rozhodnutí
- Existující kvalitní anglické MP3 zůstávají zachované; nové české stopy používají Vlastu a scéna nemá speechSynthesis fallback.

### Navrhované další kroky
- Po poslechovém ověření pokračovat auditem pevného audia hlavního portálu.

### Technický stav checkpointu
- Pages run `33266361424` úspěšně nasadil přesný commit `933834f`.
- Veřejné manifesty a reprezentativní české MP3 scén 2 a 3 jsou hashově shodné s lokální produkční kopií.
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
