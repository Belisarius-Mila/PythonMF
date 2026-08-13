<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-13 07:57 CEST

### Hotovo
- Prototyp pokračuje druhým výslechem Bunnyho s interaktivní otázkou a pevným hlasem Ana
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Poslechnout druhý výslech na iPhonu a Macu a ověřit Bunnyho hlas i tempo

### Rozhodnutí
- Druhý výslech se týká mrkve v zahrádce; Bunny používá en-US-AnaNeural a Harry po odpovědi ponechá branku zavřenou

### Navrhované další kroky
- Přidat třetí výslech se Sunnym a podezřením na ořechy
- Potom doplnit výslech Fiony a Bruna, počítání ovcí a otevření branky

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `7265156f60d1`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `7265156f60d1` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-13T05:45:17+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
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
