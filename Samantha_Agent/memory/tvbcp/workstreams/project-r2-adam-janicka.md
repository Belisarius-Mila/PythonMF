<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-07-28 15:14 CEST

### Hotovo
- Janička má samostatnou stránku pro bezpečné hledání, ruční výběr a vytvoření nového TXT bez terminálu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Vytvořit checkpoint, nasadit změnu a ručně projít hledání, výběr a vytvoření jednoho nového TXT.

### Rozhodnutí
- R2 dokumentové UI je samostatná stránka; Cockpit obsahuje pouze minimální tlačítko a routování.

### Navrhované další kroky
- Po živém UI ověření pokračovat vlastním kompaktním soukromým kontextem R2-Adama.

### Technický stav checkpointu
- Změna je otestovaná (1182 testů).
- Git před checkpointem: lokální `main` na `4df9fbd12f13`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `4df9fbd12f13` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-07-28T12:51:19+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
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

### 2026-07-28 10:17 CEST – Kliknutí na Práce nyní vždy otevře panel Pracovní změny i u čistého lazy proudu bez nasazení.

Hotovo:
- Kliknutí na Práce nyní vždy otevře panel Pracovní změny i u čistého lazy proudu bez nasazení.

Otevřeno:
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Explicitní kliknutí na Práce má vždy otevřít detail pracovních změn; kompaktní stav tlačítka zůstává pouze informativní.

Další krok:
- Po nasazení ručně ověřit kliknutí na Práce v čistém R2-Adam proudu.

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`unverified`, runtime=`connected`.

### 2026-07-28 13:46 CEST – R2-Adam má backendově připojený vlastní TXT prostor a mimo něj zůstávají soukromá zdrojová data pouze pro čtení.

Hotovo:
- R2-Adam má backendově připojený vlastní TXT prostor a mimo něj zůstávají soukromá zdrojová data pouze pro čtení.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Jediným zapisovatelným private prostorem R2-Adama je jeho vyhrazený dokumentový adresář obsluhovaný přes JanickaR2DocumentStore.

Další krok:
- Vytvořit checkpoint, nasadit změnu a živě ověřit vytvoření a změnu jednoho neškodného TXT dokumentu.

Navrhované další kroky:
- Přidat kompilaci dokumentu z prvního registrovaného read-only zdroje jako R2.0-C.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 14:07 CEST – R2-Adam umí vytvořit nový TXT z redigovaného výtahu jednoho přesně vybraného dokumentu, aniž by změnil zdroj nebo přepsal existující výstup.

Hotovo:
- R2-Adam umí vytvořit nový TXT z redigovaného výtahu jednoho přesně vybraného dokumentu, aniž by změnil zdroj nebo přepsal existující výstup.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- První kompilovaný zdroj R2-Adama je registrovaná read-only schopnost inspect_document_text nad jedním explicitním document_id; výstup je vždy create-only TXT.

Další krok:
- Vytvořit checkpoint, nasadit změnu a živě zkompilovat nový TXT z jednoho konkrétně vybraného dokumentu.

Navrhované další kroky:
- Po živém ověření přidat bezpečné hledání dokumentu a lidský výběr document_id před kompilací.
- Později doplnit vlastní kompaktní soukromý kontext R2-Adama.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 14:35 CEST – R2-Adam nyní bezpečně nalezne indexovaný dokument i při odděleném kořeni kódu a soukromého vaultu.

Hotovo:
- R2-Adam nyní bezpečně nalezne indexovaný dokument i při odděleném kořeni kódu a soukromého vaultu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Vytvořit checkpoint, nasadit změnu a zopakovat živou kompilaci vybraného dokumentu.

Navrhované další kroky:
- Po živém ověření doplnit bezpečné hledání dokumentu a lidský výběr document_id.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 14:49 CEST – R2-Adam umí bezpečně vyhledat dokumenty a zkompilovat nový TXT až po explicitním lidském výběru.

Hotovo:
- R2-Adam umí bezpečně vyhledat dokumenty a zkompilovat nový TXT až po explicitním lidském výběru.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Ani jediná nalezená shoda se nevybírá automaticky; kompilace vyžaduje aktuální lidskou volbu selection_ref.

Další krok:
- Vytvořit checkpoint, nasadit změnu a provést živý dvoukrokový test hledání a výběru.

Navrhované další kroky:
- Po živém ověření navrhnout další malý krok R2-Adama, přednostně vlastní kompaktní soukromý kontext.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 3.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 15:14 CEST – Janička má samostatnou stránku pro bezpečné hledání, ruční výběr a vytvoření nového TXT bez terminálu.

Hotovo:
- Janička má samostatnou stránku pro bezpečné hledání, ruční výběr a vytvoření nového TXT bez terminálu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- R2 dokumentové UI je samostatná stránka; Cockpit obsahuje pouze minimální tlačítko a routování.

Další krok:
- Vytvořit checkpoint, nasadit změnu a ručně projít hledání, výběr a vytvoření jednoho nového TXT.

Navrhované další kroky:
- Po živém UI ověření pokračovat vlastním kompaktním soukromým kontextem R2-Adama.

Technický důkaz:
- plná Cockpit brána: 1182 testů, 278.1 s, výsledek OK.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
