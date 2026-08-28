<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-28 14:12 CEST

### Hotovo
- Human–Adam nyní pro Linux bezpečně přehrává dočasný český zvuk vytvořený lokálně na Macu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Po checkpointu a nasazení živě ověřit čtení odpovědi na Linuxu a regresi na iPhonu.

### Rozhodnutí
- Dynamické odpovědi Human–Adam se pro vzdálený Linux namluví lokálně na Macu bez trvalého ukládání; iPhone si ponechá systémový hlas a při chybě se použije systémový fallback.

### Navrhované další kroky
- Vytvořit checkpoint tohoto vývojového kroku
- Po schválení změnu nasadit do Cockpitu
- Vyzkoušet delší českou odpověď a tlačítko Zastavit na Linuxu
- Poté projít pevné výukové hlášky a určit, které převést na MP3

### Technický stav checkpointu
- Změna je otestovaná (1468 testů).
- Git před checkpointem: lokální `main` na `1c028de35ca9`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `1c028de35ca9` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-28T10:50:57+00:00.
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
