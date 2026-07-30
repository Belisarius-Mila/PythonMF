<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obsahově narovnáno P6b: 2026-07-30 07:25 CEST

### Hotovo
- R2-Adam má vlastní trvalý chat, TXT prostor, dokumentovou lištu a čtečku.
- Umí bezpečně vyhledat úplnou sadu dokumentů, pracovat po potvrzených dávkách
  a vytvořit nový create-only TXT bez změny zdrojů.
- Aktuální `main` `20180e2` je serverově nasazený a Cockpit smoke prošel 5/5.

### Otevřeno
- Chybí souvislá provozní přejímka z pohledu Jany přes skutečný tok
  e-mail -> private vault -> R2 TXT a návrat do chatu.
- Lokální hotové commity zůstávají v denním GitHub balíčku.

### Rizika
- Zdrojové dokumenty zůstávají read-only a nejasné údaje se nesmějí domýšlet.

### Další krok
- V navazujícím systémovém směru ověřit jeden úplný tok
  e-mail -> private vault -> R2 TXT.

### Rozhodnutí
- R2-Adam se už neposuzuje jako projekt před implementací; další práce je
  provozní přejímka při zachování read-only zdrojů a create-only výstupů.

### Navrhované další kroky
- Po úplném toku provést krátkou přejímku z pohledu Jany: kontinuita chatu,
  potvrzený výběr, TXT čtečka a bezpečný návrat do chatu.

### Technický stav checkpointu
- Deployment účtenka: `20180e2`, stav `deployed`, smoke 5/5.
- P6a potvrdilo, že kanonická dvojice R2 je v rankingu před zastaralým
  agregátem.
- Historické chronologické bloky níže zůstávají beze změny.
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

### 2026-07-30 07:25 CEST – P6b odstranilo stav „před implementací“

Hotovo:
- Aktivní stav R2-Adama odpovídá skutečné funkční vrstvě: vlastní chat, TXT
  prostor, dokumentová lišta, čtečka a práce s úplnou potvrzenou sadou.
- Starý implementační start už není vydáván za současný další krok.

Rozhodnutí:
- Zdrojové dokumenty zůstávají read-only, výstupy create-only a nejasné údaje
  se označují jako nezjištěno.

Další krok:
- Ověřit jeden úplný tok e-mail -> private vault -> R2 TXT.

Navrhované další kroky:
- Potom provést provozní přejímku z pohledu Jany včetně návratu do chatu bez
  ztráty kontextu.

Technický důkaz:
- P5 ranking vrací kanonický handoff a TVBCP R2 před agregátem.
- Aktuální Cockpit běží na `20180e2` a smoke prošel 5/5.

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

### 2026-07-28 17:16 CEST – Janička má samostatný čistý chat R2-Adam s vlastním trvalým vláknem a bez vývojových ovladačů.

Hotovo:
- Janička má samostatný čistý chat R2-Adam s vlastním trvalým vláknem a bez vývojových ovladačů.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- R2-Adam používá jednoduché chatové UI odvozené od Human-Adam, ale nemá TVBCP, pracovní proudy, Git ani vývojové funkce.

Další krok:
- Vytvořit checkpoint, nasadit změnu a živě odeslat první neškodnou zprávu v novém chatu R2-Adam.

Navrhované další kroky:
- Doplnit přirozený chatový tok pro vyhledání více zdrojů, vytvoření dokumentu a jeho náhled.
- Poté přidat samostatně potvrzovaný tisk a e-mail.

Technický důkaz:
- plná Cockpit brána: 1188 testů, 319.3 s, výsledek OK.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 17:55 CEST – R2 chat nyní ukazuje aktuální dokumenty v kompaktní liště a otevírá jejich plný obsah v samostatné celostránkové čtečce.

Hotovo:
- R2 chat nyní ukazuje aktuální dokumenty v kompaktní liště a otevírá jejich plný obsah v samostatné celostránkové čtečce.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Plný obsah TXT se nezobrazuje v historii chatu; chat ukazuje pouze metadata a bezpečný odkaz do samostatné čtečky.

Další krok:
- Vytvořit checkpoint, nasadit změnu a živě otevřít jeden existující TXT z dokumentové lišty.

Navrhované další kroky:
- Pokračovat R2.1-B2: vytvoření strukturovaného TXT z více lidsky potvrzených read-only zdrojů přímo v chatu.

Technický důkaz:
- plná Cockpit brána: 1191 testů, 277.4 s, výsledek OK.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 18:35 CEST – R2-Adam může v chatu bezpečně vytvořit nový přehled z více výslovně potvrzených zdrojů, aniž by jejich obsah nafukoval chat.

Hotovo:
- R2-Adam může v chatu bezpečně vytvořit nový přehled z více výslovně potvrzených zdrojů, aniž by jejich obsah nafukoval chat.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Vytvořit checkpoint, nasadit změnu a provést živý chatový test se dvěma neškodnými zdroji.

Navrhované další kroky:
- Po živém ověření doplnit samostatně potvrzovaný tisk dokumentu.
- Později doplnit potvrzované odeslání dokumentu e-mailem.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 19:19 CEST – R2-Adam umí bezpečně vytvořit úplný soupis nebo přehled z více než pěti potvrzených dokumentů bez tichého oříznutí výsledků.

Hotovo:
- R2-Adam umí bezpečně vytvořit úplný soupis nebo přehled z více než pěti potvrzených dokumentů bez tichého oříznutí výsledků.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Požadavek na všechny dokumenty se nesmí tiše omezit na prvních pět; názvy se zpracují z metadat a obsahové přehledy po dávkách.

Další krok:
- Vytvořit checkpoint, nasadit změnu a živě ověřit soupis z více než pěti dokumentů.

Navrhované další kroky:
- Po živém ověření doplnit samostatně potvrzovaný tisk dokumentu.
- Později doplnit potvrzované odeslání dokumentu e-mailem.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-28 20:50 CEST – R2-Adam nyní bezpečně zpracuje úplnou potvrzenou sadu pojišťovacích dokumentů a používá strukturované údaje z celého dokumentu.

Hotovo:
- R2-Adam nyní bezpečně zpracuje úplnou potvrzenou sadu pojišťovacích dokumentů a používá strukturované údaje z celého dokumentu.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Chybějící nebo nejednoznačné údaje se označí jako nezjištěno a nikdy se nedomýšlejí.

Další krok:
- Vytvořit checkpoint, nasadit změnu a zopakovat praktický přehled šesti dokumentů v chatu R2-Adam.

Navrhované další kroky:
- Po nasazení potvrdit zobrazenou šestici a ověřit výsledný TXT v dokumentové čtečce.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-r2-adam-janicka`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-07-30 09:16 CEST – E2 živě ověřilo úplný tok e-mail -> private vault -> R2 TXT

Hotovo:
- Jeden existující e-mailový archiv byl podle redigovaných metadat ručně vybrán
  a po přesném potvrzení z něj bylo do private vaultu importováno jedno PDF
  s použitelnou textovou vrstvou.
- R2 našel právě jednu redigovanou volbu a po druhém přesném potvrzení vytvořil
  nový create-only TXT ve svém vlastněném soukromém prostoru.
- Zdrojové a uložené PDF se bajtově shodují; kompilace zdroj nezměnila.

Rozhodnutí:
- Reálný import zůstává ve stavu `needs_review` a jeho definitivní klasifikace
  se nebude domýšlet bez kontroly ve ScanDocu.
- Private názvy, UID, obsah, opaque provozní reference ani výsledný TXT se
  nezapisují do Gitu, memory nebo technického reportu.

Další krok:
- Zkontrolovat importovaný dokument ve ScanDocu a potom z pohledu Jany otevřít
  nový TXT v R2 čtečce a ověřit bezpečný návrat do chatu.

Navrhované další kroky:
- Po přejímce rozhodnout, zda je potřeba samostatný dvoukrokový workflow pro
  odeslání nového TXT e-mailem; v E2 se nic neodesílalo.

Technický důkaz:
- E1 syntetický end-to-end test a sousední sada prošly 47/47.
- Živý PDF import měl textovou vrstvu bez potřeby OCR, vytvořil jediný
  `needs_review` záznam a R2 hledání vrátilo jedinou aktuální volbu.
- Nový TXT má bezpečný režim `0600`, guardovanou strukturu a jeden potvrzený
  zdroj; zdrojový PDF hash zůstal před a po kompilaci stejný.

### 2026-07-30 11:47 CEST – E3 odhalilo technickou obálku lidského TXT a připravilo její bezpečné odstranění

Hotovo:
- Ruční revize importovaného PDF proběhla a read-only kontrola potvrdila, že
  Archiv e-mailu i vložená dokumentová čtečka mají k PDF funkční cestu.
- Lokální oprava odstraňuje z nových R2 TXT servisní hlavičky, kandidáty na
  datum, interní identity a značky extrakce.
- Již vytvořený TXT se nepřepisuje; čtečka stejnou technickou obálku skryje až
  při zobrazení a ponechá lidský obsah.

Rozhodnutí:
- Servisní inspekce vaultu zůstává beze změny pro diagnostiku. Její výstup ale
  není vhodný jako začátek dokumentu pro Janu a kompilátor ho musí převést na
  lidský text.
- Zdrojový PDF ani existující TXT se kvůli prezentační opravě nemění.

Další krok:
- Po samostatném potvrzení nasadit lokální commit do Cockpitu a zopakovat
  otevření uložené přílohy i E2 TXT.

Navrhované další kroky:
- Při retestu na iPhonu stránku Archivu e-mailu znovu načíst; pokud se PDF
  nadále vizuálně neukáže, zaznamenat konkrétní pohled a řešit pouze mobilní
  vykreslení, nikoli nový import.

Technický důkaz:
- Uložená příloha, dokumentová čtečka i vložené PDF odpověděly HTTP 200;
  PDF má očekávanou signaturu a velikost se shoduje s uloženým záznamem.
- Filtr nad současným E2 TXT ponechal neprázdný lidský obsah a odstranil všechny
  kontrolované technické markery bez zápisu do soukromého souboru.
- Cílená sada prošla 40/40 a plná Cockpit brána 1241/1241.

### 2026-07-30 12:27 CEST – Oprava lidského R2 TXT je nasazená

Hotovo:
- Funkční commit s čištěním nových i starších R2 TXT byl řízeně nasazen do
  Cockpitu.
- Živá R2 čtečka vrací neprázdný lidský obsah bez kontrolovaných technických
  markerů.
- Archiv e-mailu vrací uloženou přílohu a její vložené PDF je backendově
  dostupné.

Rozhodnutí:
- Backendové ověření nenahrazuje poslední vizuální přejímku na zařízení Jany.

Další krok:
- Obnovit Archiv e-mailu a R2 čtečku a ručně potvrdit samostatné zobrazení PDF,
  čistý začátek TXT a návrat do chatu.

Navrhované další kroky:
- Pokud se PDF na iPhonu nadále nezobrazí, řešit úzce mobilní vykreslení
  konkrétního pohledu; nový import ani další kopii přílohy nevytvářet.

Technický důkaz:
- Deployment účtenka: funkční commit `9dea930`, stav `deployed`, očekávaný
  otisk odpovídá běžícímu procesu.
- Samostatný Cockpit smoke prošel 5/5.
- Živý TXT má 0 kontrolovaných technických markerů; PDF endpoint odpověděl
  HTTP 200 s platnou PDF signaturou.

### 2026-07-30 19:08 CEST – R2 předává nalezený e-mail do plné místní čtečky

Hotovo:
- R2 má pro konkrétní archivovaný e-mail pracovat s celým dostupným
  `body_text`, nikoli jen s úryvkem nebo metadatovým souhrnem.
- Odpověď R2 nese pouze neprůhledný `archive_ref`; chat z něj nabídne tlačítko
  pro otevření celého místního e-mailu a jeho příloh.
- Archiv umí přílohy read-only otevřít také přímo z immutable původního EML,
  aniž by kvůli zobrazení vytvářel další soubor.

Rozhodnutí:
- Dlouhé tělo e-mailu se nebude automaticky kopírovat celé do chatové bubliny.
  Plný text a přílohy patří do samostatné místní čtečky.
- Veřejný odkaz používá jen opaque reference; interní archive ID, UID,
  souborová cesta a soukromý obsah zůstávají mimo Git a TVBCP.
- PDF a běžné obrázky se mohou zobrazit inline; potenciálně aktivní nebo jiné
  typy příloh se nabídnou jako stažení.

Další krok:
- Po samostatném potvrzení nasadit aktuální `main` do Cockpitu a z R2 zopakovat
  hledání konkrétního e-mailu; v odpovědi otevřít nové tlačítko a vizuálně
  ověřit celý text i přílohy.

Navrhované další kroky:
- Po přejímce ladit jen konkrétní mobilní formát přílohy, který by se na iPhonu
  neotevřel; neprovádět nový import ani kopii bez doložené potřeby.

Technický důkaz:
- Živá read-only kontrola cílového archivu potvrdila nezkrácené tělo o 2 899
  znacích, dvě otevíratelné přílohy a úspěšné rozlišení přílohy z původního EML.
- Cílená sada prošla 22/22 a plná Cockpit brána 1247/1247.

### 2026-07-30 20:07 CEST – Plná čtečka e-mailu z R2 je nasazená

Hotovo:
- Funkční commit s předáním e-mailu z R2 do plné místní čtečky byl řízeně
  nasazen do Cockpitu.
- Živý průchod potvrdil plný nezkrácený text, dvě otevíratelné přílohy a
  úspěšnou read-only HTTP odpověď první přílohy.

Rozhodnutí:
- Nasazení je dokončené backendově; poslední vizuální přejímka zůstává na
  konkrétním zařízení Míly nebo Jany.

Další krok:
- V R2 znovu vyhledat konkrétní e-mail, použít nové tlačítko pro celý e-mail a
  vizuálně zkontrolovat text i obě přílohy.

Navrhované další kroky:
- Případnou další chybu řešit podle konkrétního formátu nebo mobilního
  vykreslení, nikoli novým importem celého e-mailu.

Technický důkaz:
- Deployment účtenka: funkční commit `3c9a3ed`, stav `deployed`, nový proces
  `50992` a očekávaný kódový otisk `9894d08d149185ad`.
- Samostatný Cockpit smoke prošel 5/5.
- R2 stránka, deep-link čtečka, detailní API a read-only endpoint přílohy
  odpověděly HTTP 200; odpověď přílohy má `no-store` a platnou délku.
