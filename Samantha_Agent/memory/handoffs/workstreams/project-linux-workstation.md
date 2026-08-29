<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obsahově dorovnáno: 2026-08-29 17:05 CEST

### Hotovo
- Linux zůstává soukromým klientem Samanthy a výukových aplikací; VocabularyEN s hlasy Aria a Vlasta je zveřejněné.
- MMTX Harryho MP3 jsou dorovnané do příslušného MMTX handoffu a TVBCP.

### Otevřeno
- Prakticky ověřit VocabularyEN a celý MMTX průchod na Linuxu.

### Rizika
- Historické checkpointy 15:45 a 16:22 vznikly pod aktivním proudem Linux, přestože obsah patřil MMTX; nesmí být používány jako aktuální stav Linux workstreamu.

### Další krok
- Na Linuxu provést ruční uživatelský test; případný další vývoj nejprve otevřít ve věcně správném workstreamu.

### Rozhodnutí
- Linux je testovací zařízení, nikoli vlastník vývoje MMTX nebo VocabularyEN.

### Navrhované další kroky
- Pokračovat v konfiguraci Linuxu odděleně od vývoje konkrétních aplikací.

### Technický stav checkpointu
- GitHub a Cockpit jsou na `f1499b1`; veřejné VocabularyEN i Harryho scéna byly nezávisle ověřeny.
- Chronologické chybně směrované bloky zůstávají auditní historií a jsou korigovány novým záznamem níže.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Linux / instalace a konfigurace

Nazev: Linux / instalace a konfigurace
Pracovni proud: project-linux-workstation
Typ: Project
Priorita: 2
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

### Automatický checkpoint 2026-08-27 22:20 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: Paměť Linux PC nyní shrnuje instalovaný Mint, hardware, účel počítače, soukromý přístup ke Cockpitu, hry, kancelářskou práci, VocabularyFR, bezpečnostní hranice a otevřené kroky.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `Samantha_Agent/memory/projects/linux_workstation.md`
- Commit: `Update Linux workstation project memory`
- Další krok: Vytvořit v Linux Mint nástrojem Web Apps ikonu Samantha Cockpit a ověřit zprávu, historii, zvuk, mikrofon a soukromou tailnet-only adresu.

### Automatický checkpoint 2026-08-28 14:12 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: Human–Adam nyní pro Linux bezpečně přehrává dočasný český zvuk vytvořený lokálně na Macu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1468 testů, 389.8 s, výsledek OK
- Změněné cesty před paměťovým zápisem (7): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/app/speech/__init__.py`, `Samantha_Agent/app/speech/local_tts.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_human_adam_ui.py`, `Samantha_Agent/tests/test_speech_local_tts.py`
- Commit: `Use local Mac audio for Human-Adam replies`
- Další krok: Po checkpointu a nasazení živě ověřit čtení odpovědi na Linuxu a regresi na iPhonu.

### Automatický checkpoint 2026-08-28 20:54 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: TVBCP nyní zachycuje nevyhovující praktický test a zmrazení dalšího vývoje čtení Human–Adam na Linuxu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `Samantha_Agent/memory/tvbcp/workstreams/project-linux-workstation.md`
- Commit: `Freeze Human-Adam Linux speech proposal`
- Další krok: Pokračovat jiným tématem Linux PC; ke čtení Human–Adam se vrátit pouze na nový výslovný pokyn.

### Automatický checkpoint 2026-08-29 08:52 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: Lokální casting porovnává čtyři kvalitní hlasy na deseti skutečných výrazech VocabularyEN pomocí 40 hotových MP3 bez prodlevy; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 9.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (47): `Samantha_Agent/app/speech/__init__.py`, `Samantha_Agent/tests/test_vocabularyen_audio_casting.py`, `VocabularyEN/audio_casting/app.js`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/do-you-have.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/dont-know.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/drink.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/free.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/glass-water.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/live.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/right.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/squirrel.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/three.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-antonin-neural/welcome.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/do-you-have.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/dont-know.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/drink.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/free.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/glass-water.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/live.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/right.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/squirrel.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/three.mp3`, `VocabularyEN/audio_casting/audio/cs-cz-vlasta-neural/welcome.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/do-you-have.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/dont-know.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/drink.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/free.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/glass-water.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/live.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/right.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/squirrel.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/three.mp3`, `VocabularyEN/audio_casting/audio/en-us-ana-neural/welcome.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/do-you-have.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/dont-know.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/drink.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/free.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/glass-water.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/live.mp3`, `VocabularyEN/audio_casting/audio/en-us-aria-neural/right.mp3`, … a dalších 7
- Commit: `Prepare VocabularyEN voice casting`
- Další krok: Poslechnout casting a vybrat vítězný anglický a český hlas

### Ruční handoff 2026-08-29 09:50 CEST – Produkční MP3 pro VocabularyEN

- Vybrané hlasy jsou `en-US-AriaNeural` pro angličtinu a `cs-CZ-VlastaNeural` pro češtinu, oba rychlostí `-10 %`.
- Web VocabularyEN už nepoužívá systémový `speechSynthesis`; zadání i odpověď přehrává z předem vytvořených MP3.
- Knihovna pokrývá 306 karet, 612 jazykových odkazů a 608 unikátních MP3. Shodný text sdílí jeden soubor.
- Kanonický postup po každé změně `VocabularyEN.csv` je:
  1. `python3 VocabularyEN/sync_vocabulary_en_to_docs.py`
  2. `python3 VocabularyEN/build_vocabulary_en_audio.py --apply`
  3. `python3 VocabularyEN/build_vocabulary_en_audio.py`
- Třetí příkaz je povinná read-only kontrola. Musí potvrdit `Audio kontrola OK`; bez ní není změna slovníku připravená k publikování.
- Generátor bez `--apply` nic externě negeneruje. `--apply` posílá Microsoft Speech pouze veřejný text slovíček přes registrovanou schopnost `generate_project_audio_asset` a doplní jen chybějící soubory.
- Nepoužívané staré audio se automaticky nemaže. Případný úklid je samostatný krok vyžadující výslovné rozhodnutí.
- Podrobný provozní návod je v `VocabularyEN/AUDIO_WORKFLOW.md`.
- Další krok: po checkpointu a zveřejnění prakticky vyzkoušet na Linuxu oba směry, `Přehrát zadání` a `Přehrát odpověď`.

### Automatický checkpoint 2026-08-29 09:53 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: VocabularyEN nyní používá úplnou knihovnu kvalitních předgenerovaných MP3 hlasů Aria a Vlasta bez systémového hlasu a bez prodlevy generování; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (80): `Samantha_Agent/memory/handoffs/workstreams/project-linux-workstation.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-linux-workstation.md`, `VocabularyEN/sync_vocabulary_en_to_docs.py`, `docs/vocabulary-en/app.js`, `docs/vocabulary-en/index.html`, `Samantha_Agent/tests/test_vocabularyen_audio_library.py`, `VocabularyEN/AUDIO_WORKFLOW.md`, `VocabularyEN/build_vocabulary_en_audio.py`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/00cc4ffe2e1325586465.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/01c372c9e18360fd3a72.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/01e4810718647f555107.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/036de19ecddc180da87f.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/038ea33e5403360626ce.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/04def391499947cd1236.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/05f195d97e1c1e6cf146.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/0b2907884d5f08c5344a.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/0c025b10cbc59376ab93.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/0e9ea43a2d328473e736.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/0edd9002eb6bbcf57957.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/0f9d451e00dab0b60b33.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/105dcc7925f4ac0f9879.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1191bcad39d107d76a05.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/11c5639d04a96f7fd1f9.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/11d33724807bac0b2714.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/11e36c599db4caed5ca0.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/12cfd70e3fa500f17e71.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/13f639e9a80354493fc9.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1481394c4ae520a8fb48.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1498a0307280d133be14.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1520ea7e28dc59b8b01b.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/15ee4326554ada0cb75f.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/161ed9ab4a51427f33a5.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/16f90bc807da103f89b0.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/187bde871fbdc4b2b3bc.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/197b969c4a63f088a01e.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/19afcad94affcd54d915.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1b2e952658f3186f6913.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1b6b87c6bbd9277f9330.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1c0a03a2d61d18c70e8c.mp3`, `docs/assets/vocabulary-en-audio/cs-cz-vlasta-neural/1cb7c3c365c67cc7560c.mp3`, … a dalších 40
- Commit: `Use pre-generated MP3 in VocabularyEN`
- Další krok: Po zveřejnění prakticky ověřit přehrávání VocabularyEN na Linuxu

### Automatický checkpoint 2026-08-29 15:45 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: Dokumentace MMTX nyní správně zachycuje napojení scény 3 na Harryho a nový guard brání tichému převzetí zastaralého stavu; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/memory/ACTIVE_PROJECTS.md`, `Samantha_Agent/memory/MEMORY_INDEX.md`, `Samantha_Agent/memory/handoffs/workstreams/project-mmtx.md`, `Samantha_Agent/memory/projects/mmtx_story_hotspot_app.md`, `Samantha_Agent/memory/technical/project_tvbcp_rules.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-mmtx.md`
- Commit: `Dorovnat dokumentaci MMTX po napojení Harryho`
- Další krok: Inventarizovat systémové čtení Harryho scény a připravit jeho náhradu pevnými MP3

### Automatický checkpoint 2026-08-29 16:22 CEST

- Pracovní proud: `project-linux-workstation`
- Hotovo: Harryho scéna nyní přehrává všech 136 anglických a českých dialogových a slovníkových stop z předem připravených MP3 bez systémového hlasu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (80): `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/index.html`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/script.js`, `Samantha_Agent/tests/test_mmtx_harry_guard_prototype.py`, `docs/scene04_harry_guard_prototype/index.html`, `docs/scene04_harry_guard_prototype/script.js`, `MatysekANJ/build_scene04_audio.py`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_benji_friendly_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_benji_helper_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_benji_map_answer_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_benji_no_chase_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_benji_not_me_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bruno_bruno_answer_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bruno_bruno_lake_with_friends_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bruno_no_digging_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bruno_not_me_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bunny_bunny_answer_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bunny_lake_only_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bunny_not_me_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_bunny_own_carrots_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_fiona_fiona_answer_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_fiona_fiona_lake_with_friends_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_fiona_no_chickens_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_fiona_not_me_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_badger_intro_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_badger_prompt_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_bruno_accepted_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_bunny_accepted_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_carrot_question_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_chicken_question_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_fence_question_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_fiona_accepted_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_fox_intro_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_fox_prompt_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_gate_opened_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_introduction_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_listen_again_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_map_question_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_not_me_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_nut_question_cz.mp3`, `MatysekANJ/web_mmtx/scene04_harry_guard_prototype/audio/czech/scene04_harry_rabbit_intro_cz.mp3`, … a dalších 40
- Commit: `Nahradit systémové čtení Harryho scény pevnými MP3`
- Další krok: Ručně poslechnout celý průchod Harryho scénou na Linuxu a ověřit přirozenost hlasů i tempo.

### Korekce směrování 2026-08-29 17:05 CEST

- Checkpointy 15:45 a 16:22 obsahově patří MMTX, nikoli Linux workstreamu.
- Jejich historické bloky se nemažou, ale aktuální stav a věcná autorita byly dorovnány do `project-mmtx` handoffu a TVBCP.
- Linux zůstává pouze zařízením pro ruční test. Další krok Linux workstreamu je praktické ověření; další úpravy Harryho scény se mají zahájit až po otevření MMTX.
