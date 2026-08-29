<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-29 08:52 CEST

### Hotovo
- Lokální casting porovnává čtyři kvalitní hlasy na deseti skutečných výrazech VocabularyEN pomocí 40 hotových MP3 bez prodlevy
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Poslechnout casting a vybrat vítězný anglický a český hlas

### Rozhodnutí
- Před nasazením předgenerovaných Microsoft Neural MP3 do VocabularyEN se vybere jeden anglický a jeden český hlas v odděleném lokálním castingu

### Navrhované další kroky
- Vybrat anglický hlas Ana nebo Aria
- Vybrat český hlas Vlasta nebo Antonín
- Po výběru připravit kompletní MP3 knihovnu VocabularyEN
- Teprve potom zapojit MP3 do ostré webové aplikace

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `c46450e3e019`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `c46450e3e019` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-28T19:25:37+00:00.
- Read-only živý stav: main=`aligned`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
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
