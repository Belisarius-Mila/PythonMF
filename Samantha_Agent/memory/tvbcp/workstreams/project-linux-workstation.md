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

### 2026-08-28 20:53 CEST – Čtení odpovědí Human–Adam na Linuxu je po praktickém testu zmrazeno.

Hotovo:
- Praktický test na Linuxu ukázal, že dočasné M4A vytvořené přes macOS `say` se spouští se zpožděním a český systémový hlas je pro běžné používání nepřijatelně syntetický.
- Technicky funkční varianta proto nesplnila uživatelský cíl; současné tlačítko není považováno za použitelné řešení.

Rizika:
- Současná implementace `say` zůstává nasazená, ale její praktická kvalita je nevyhovující.
- Kvalitní Edge TTS by odesílal text vybrané odpovědi externí službě Microsoft Speech a nesmí být zapojen automaticky ani bez výslovného souhlasu s tímto přenosem.

Rozhodnutí:
- Další vývoj čtení dynamických odpovědí Human–Adam se nyní zmrazuje. Při práci na Linux PC bude Míla odpovědi číst jako text.
- Pokud se téma znovu otevře, výchozím návrhem je kvalitní český hlas `cs-CZ-AntoninNeural` přes Edge TTS pouze po vědomém kliknutí, s viditelným upozorněním na externí přenos textu a nejprve s neškodným poslechovým pilotem.
- Předem vytvořené MP3 pro pevný výukový obsah zůstávají samostatnou možností; nejde o řešení dynamických odpovědí Human–Adam.

Další krok:
- Žádný další krok pro čtení Human–Adam nyní neprovádět; vrátit se k němu jen na nový výslovný Mílův pokyn.

Navrhované další kroky:
- Při případném obnovení nejprve na jedné veřejné větě ověřit hlas a skutečný čas od kliknutí do začátku přehrávání na Linuxu.
- Teprve po přijatelném pilotu a výslovném souhlasu rozhodnout o zapojení Edge TTS, případně o přehrávání po větách.

Technický důkaz:
- Mac má pro češtinu dostupný hlas `Zuzana`; lokální měření úplného vytvoření M4A bylo přibližně 0,47 s pro 29 znaků a 0,98 s pro 740 znaků, bez započtení přenosu a načtení v prohlížeči.
- Dřívější projektové testy Edge TTS doložily české MP3 přibližně za 1–2 sekundy, ale tato varianta nebyla v tomto kroku zapojena ani živě ověřena na Linuxu.

### 2026-08-28 20:54 CEST – TVBCP nyní zachycuje nevyhovující praktický test a zmrazení dalšího vývoje čtení Human–Adam na Linuxu.

Hotovo:
- TVBCP nyní zachycuje nevyhovující praktický test a zmrazení dalšího vývoje čtení Human–Adam na Linuxu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Další vývoj dynamického čtení Human–Adam na Linuxu je zmrazen; odpovědi se budou číst jako text a Edge TTS zůstává pouze budoucím návrhem vyžadujícím nový výslovný souhlas.

Další krok:
- Pokračovat jiným tématem Linux PC; ke čtení Human–Adam se vrátit pouze na nový výslovný pokyn.

Navrhované další kroky:
- Případný budoucí návrat zahájit jednou veřejnou testovací větou
- Pevná výuková hlášení řešit samostatně pomocí předem vytvořených MP3

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-linux-workstation`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.
