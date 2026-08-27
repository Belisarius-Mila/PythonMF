<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-27 22:20 CEST

### Hotovo
- Paměť Linux PC nyní shrnuje instalovaný Mint, hardware, účel počítače, soukromý přístup ke Cockpitu, hry, kancelářskou práci, VocabularyFR, bezpečnostní hranice a otevřené kroky.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Vytvořit v Linux Mint nástrojem Web Apps ikonu Samantha Cockpit a ověřit zprávu, historii, zvuk, mikrofon a soukromou tailnet-only adresu.

### Rozhodnutí
- Mac zůstává autoritou Samanthy; Linux PC je zatím soukromý klient pro běžnou práci, výukové aplikace a starší hry, nikoli produkční server.

### Navrhované další kroky
- Vytvořit oddělený dětský účet bez Cockpitu a citlivých přístupů.
- Nainstalovat a prakticky vyzkoušet GCompris a SuperTux.
- Podle skutečné odezvy rozhodnout o SSD nebo rozšíření RAM.
- Teprve samostatně navrhnout VocabularyFR s jediným zapisujícím a případný linuxový uzel bez soukromých dat.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `a1b12f71f659`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `a1b12f71f659` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-27T12:25:28+00:00.
- Read-only živý stav: main=`aligned`, deployment=`verified_current`, runtime=`disconnected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Linux / instalace a konfigurace

Pracovni proud: `project-linux-workstation`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-27 22:20 CEST – Paměť Linux PC nyní shrnuje instalovaný Mint, hardware, účel počítače, soukromý přístup ke Cockpitu, hry, kancelářskou práci, VocabularyFR, bezpečnostní hranice a otevřené kroky.

Hotovo:
- Paměť Linux PC nyní shrnuje instalovaný Mint, hardware, účel počítače, soukromý přístup ke Cockpitu, hry, kancelářskou práci, VocabularyFR, bezpečnostní hranice a otevřené kroky.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Mac zůstává autoritou Samanthy; Linux PC je zatím soukromý klient pro běžnou práci, výukové aplikace a starší hry, nikoli produkční server.

Další krok:
- Vytvořit v Linux Mint nástrojem Web Apps ikonu Samantha Cockpit a ověřit zprávu, historii, zvuk, mikrofon a soukromou tailnet-only adresu.

Navrhované další kroky:
- Vytvořit oddělený dětský účet bez Cockpitu a citlivých přístupů.
- Nainstalovat a prakticky vyzkoušet GCompris a SuperTux.
- Podle skutečné odezvy rozhodnout o SSD nebo rozšíření RAM.
- Teprve samostatně navrhnout VocabularyFR s jediným zapisujícím a případný linuxový uzel bez soukromých dat.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-linux-workstation`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`disconnected`.
