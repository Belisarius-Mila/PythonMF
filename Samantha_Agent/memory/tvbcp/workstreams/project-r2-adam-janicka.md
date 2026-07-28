<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-07-28 09:42 CEST

### Hotovo
- Janička může ve svém dokumentovém prostoru vytvářet a číst TXT dokumenty do velikosti 10 MiB.

### Otevřeno
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Pokračovat backendovým napojením document store na R2-Adama.

### Rozhodnutí
- Maximální velikost jednoho TXT dokumentu R2-Adama je 10 MiB.

### Navrhované další kroky
- Při budoucím náhledu zobrazovat jen omezenou část velkého dokumentu.
- Při e-mailovém draftu kontrolovat velikost přílohy samostatně.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `8aa7cfc51814`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: serverová deployment receipt pro tento proud není dostupná.
- Read-only živý stav: main=`local_ahead`, deployment=`unverified`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: R2-Adam / Janička

Pracovni proud: `project-r2-adam-janicka`
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

### 2026-07-28 09:26 CEST – R2-Adam má bezpečný backendový prostor pro vlastní TXT dokumenty bez rozšiřování Cockpitu a bez přístupu k zápisu do ostatních dat Samanthy.

Hotovo:
- R2-Adam má bezpečný backendový prostor pro vlastní TXT dokumenty bez rozšiřování Cockpitu a bez přístupu k zápisu do ostatních dat Samanthy.

Otevřeno:
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Janička smí spravovat dokumenty pouze ve svém vyhrazeném private adresáři; ostatní zdroje Samanthy zůstávají read-only a odesílání bude možné jen po potvrzení na přednastavený kontakt.

Další krok:
- Napojit document store na backend R2-Adama a povolit sandboxový zápis pouze do tohoto jediného adresáře.

Navrhované další kroky:
- Přidat kompilaci dokumentu z prvního registrovaného read-only zdroje.
- Později přidat náhled a potvrzované odeslání na pevný soukromý kontakt.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 6.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`unverified`, runtime=`connected`.

### 2026-07-28 09:42 CEST – Janička může ve svém dokumentovém prostoru vytvářet a číst TXT dokumenty do velikosti 10 MiB.

Hotovo:
- Janička může ve svém dokumentovém prostoru vytvářet a číst TXT dokumenty do velikosti 10 MiB.

Otevřeno:
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Maximální velikost jednoho TXT dokumentu R2-Adama je 10 MiB.

Další krok:
- Pokračovat backendovým napojením document store na R2-Adama.

Navrhované další kroky:
- Při budoucím náhledu zobrazovat jen omezenou část velkého dokumentu.
- Při e-mailovém draftu kontrolovat velikost přílohy samostatně.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`unverified`, runtime=`connected`.
