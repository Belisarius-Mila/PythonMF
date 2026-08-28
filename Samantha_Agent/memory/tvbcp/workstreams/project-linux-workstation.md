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

### 2026-08-28 14:12 CEST – Human–Adam nyní pro Linux bezpečně přehrává dočasný český zvuk vytvořený lokálně na Macu.

Hotovo:
- Human–Adam nyní pro Linux bezpečně přehrává dočasný český zvuk vytvořený lokálně na Macu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Dynamické odpovědi Human–Adam se pro vzdálený Linux namluví lokálně na Macu bez trvalého ukládání; iPhone si ponechá systémový hlas a při chybě se použije systémový fallback.

Další krok:
- Po checkpointu a nasazení živě ověřit čtení odpovědi na Linuxu a regresi na iPhonu.

Navrhované další kroky:
- Vytvořit checkpoint tohoto vývojového kroku
- Po schválení změnu nasadit do Cockpitu
- Vyzkoušet delší českou odpověď a tlačítko Zastavit na Linuxu
- Poté projít pevné výukové hlášky a určit, které převést na MP3

Technický důkaz:
- plná Cockpit brána: 1468 testů, 389.8 s, výsledek OK.
- Pracovní proud: `project-linux-workstation`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.
