<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-14 10:01 CEST

### Hotovo
- Prototyp nyní obsahuje čtvrtý výslech Fiony s vlastním obrazem a pevným hlasem
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Ručně ověřit Fionin výslech, hlas a klikací místo na iPhonu nebo Macu

### Rozhodnutí
- Fiona používá kanonický hlas en-US-JennyNeural

### Navrhované další kroky
- Zapojit poslední výslech Bruna s opraveným obrazem obsahujícím Benjiho
- Poté doplnit počítání pěti ovcí a otevření branky

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `b9293021d09f`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `b9293021d09f` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-14T07:24:10+00:00.
- Read-only živý stav: main=`aligned`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
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
