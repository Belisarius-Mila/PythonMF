<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-28 20:54 CEST

### Hotovo
- TVBCP nyní zachycuje nevyhovující praktický test a zmrazení dalšího vývoje čtení Human–Adam na Linuxu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Pokračovat jiným tématem Linux PC; ke čtení Human–Adam se vrátit pouze na nový výslovný pokyn.

### Rozhodnutí
- Další vývoj dynamického čtení Human–Adam na Linuxu je zmrazen; odpovědi se budou číst jako text a Edge TTS zůstává pouze budoucím návrhem vyžadujícím nový výslovný souhlas.

### Navrhované další kroky
- Případný budoucí návrat zahájit jednou veřejnou testovací větou
- Pevná výuková hlášení řešit samostatně pomocí předem vytvořených MP3

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `7219effd7f2e`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `7219effd7f2e` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-28T12:57:13+00:00.
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
