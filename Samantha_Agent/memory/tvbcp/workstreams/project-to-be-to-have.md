<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-11 10:01 CEST

### Hotovo
- KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Po checkpointu a nasazení otevřít v Cockpitu Webové aplikace → KPTL Introduction a ověřit okno i zvuk

### Rozhodnutí
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

### Navrhované další kroky
- Žádné další návrhy nad rámec bezprostředního kroku.

### Technický stav checkpointu
- Změna je otestovaná (1336 testů).
- Git před checkpointem: lokální `main` na `260f40b5b981`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `260f40b5b981` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-11T07:37:22+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: ToBeToHave

Pracovni proud: `project-to-be-to-have`
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

### 2026-08-11 09:33 CEST – KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty

Hotovo:
- KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Spustit kptl_viewer.py v běžném desktopovém prostředí a krátce vizuálně ověřit okno a zvuk

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 11.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-to-be-to-have`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-11 10:01 CEST – KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher

Hotovo:
- KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Po checkpointu a nasazení otevřít v Cockpitu Webové aplikace → KPTL Introduction a ověřit okno i zvuk

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- plná Cockpit brána: 1336 testů, 319.1 s, výsledek OK.
- Pracovní proud: `project-to-be-to-have`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
