<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obsahově narovnáno P6b a provozně ověřeno E2: 2026-07-30 09:16 CEST

### Hotovo
- R2-Adam má vlastní trvalý chat, TXT prostor, dokumentovou lištu a čtečku.
- Umí bezpečně vyhledat úplnou sadu dokumentů, pracovat po potvrzených dávkách
  a vytvořit nový create-only TXT bez změny zdrojů.
- E2 živě ověřilo souvislý tok archivovaný e-mail -> potvrzený import jednoho
  textového PDF do private vaultu -> jediná redigovaná volba R2 -> nový
  create-only TXT. Zdrojový PDF soubor zůstal bajtově nezměněný.
- Aktuální `main` `20180e2` je serverově nasazený a Cockpit smoke prošel 5/5.

### Otevřeno
- Importovaný dokument z E2 zůstává poctivě ve stavu `needs_review`; nebyla
  provedena obsahová nebo klasifikační revize ve ScanDocu.
- Chybí krátká provozní přejímka z pohledu Jany: otevření nového TXT ve čtečce
  a bezpečný návrat do chatu.
- Lokální hotové commity zůstávají v denním GitHub balíčku.

### Rizika
- Zdrojové dokumenty zůstávají read-only a nejasné údaje se nesmějí domýšlet.

### Další krok
- Zkontrolovat importovaný PDF dokument ve ScanDocu bez opisování obsahu do
  chatu nebo paměti; potom s Janou otevřít nový TXT v R2 čtečce.

### Rozhodnutí
- R2-Adam se už neposuzuje jako projekt před implementací; další práce je
  provozní přejímka při zachování read-only zdrojů a create-only výstupů.

### Navrhované další kroky
- Po úplném toku provést krátkou přejímku z pohledu Jany: kontinuita chatu,
  potvrzený výběr, TXT čtečka a bezpečný návrat do chatu.

### Technický stav checkpointu
- Deployment účtenka: `20180e2`, stav `deployed`, smoke 5/5.
- E1 přidalo syntetický end-to-end test; cílená sousední sada prošla 47/47.
- E2 potvrdilo shodu zdrojových a uložených bajtů, textovou vrstvu bez OCR,
  jednoznačný lidský výběr, nový TXT s režimem `0600` a nezměněný zdroj.
- P6a potvrdilo, že kanonická dvojice R2 je v rankingu před zastaralým
  agregátem.
- Historické chronologické bloky níže zůstávají beze změny.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: R2-Adam / Janička

Nazev: R2-Adam / Janička
Pracovni proud: project-r2-adam-janicka
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

### Automatický checkpoint 2026-07-28 09:26 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam má bezpečný backendový prostor pro vlastní TXT dokumenty bez rozšiřování Cockpitu a bez přístupu k zápisu do ostatních dat Samanthy.
- Otevřeno: Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/communication/janicka_r2_documents.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`
- Commit: `Add isolated Janička R2 document store`
- Další krok: Napojit document store na backend R2-Adama a povolit sandboxový zápis pouze do tohoto jediného adresáře.

### Automatický checkpoint 2026-07-28 09:42 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: Janička může ve svém dokumentovém prostoru vytvářet a číst TXT dokumenty do velikosti 10 MiB.
- Otevřeno: Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/janicka_r2_documents.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`
- Commit: `Raise Janička R2 text limit to 10 MiB`
- Další krok: Pokračovat backendovým napojením document store na R2-Adama.

### Automatický checkpoint 2026-07-28 10:17 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: Kliknutí na Práce nyní vždy otevře panel Pracovní změny i u čistého lazy proudu bez nasazení.
- Otevřeno: Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Always open Work panel on explicit click`
- Další krok: Po nasazení ručně ověřit kliknutí na Práce v čistém R2-Adam proudu.

### Automatický checkpoint 2026-07-28 13:46 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam má backendově připojený vlastní TXT prostor a mimo něj zůstávají soukromá zdrojová data pouze pro čtení.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/app/communication/human_adam_workstream_catalog.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_human_adam_profiles.py`, `Samantha_Agent/tests/test_human_adam_workstream_catalog.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`, `Samantha_Agent/app/communication/janicka_r2_backend.py`
- Commit: `Connect R2-Adam document backend safely`
- Další krok: Vytvořit checkpoint, nasadit změnu a živě ověřit vytvoření a změnu jednoho neškodného TXT dokumentu.

### Automatický checkpoint 2026-07-28 14:07 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam umí vytvořit nový TXT z redigovaného výtahu jednoho přesně vybraného dokumentu, aniž by změnil zdroj nebo přepsal existující výstup.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/communication/janicka_r2_backend.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`, `Samantha_Agent/app/communication/janicka_r2_compiler.py`
- Commit: `Compile R2 TXT from one read-only document source`
- Další krok: Vytvořit checkpoint, nasadit změnu a živě zkompilovat nový TXT z jednoho konkrétně vybraného dokumentu.

### Automatický checkpoint 2026-07-28 14:35 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam nyní bezpečně nalezne indexovaný dokument i při odděleném kořeni kódu a soukromého vaultu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/documents/vault.py`, `Samantha_Agent/tests/test_document_vault_tools.py`
- Commit: `Resolve R2 document paths against explicit vault`
- Další krok: Vytvořit checkpoint, nasadit změnu a zopakovat živou kompilaci vybraného dokumentu.

### Automatický checkpoint 2026-07-28 14:49 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam umí bezpečně vyhledat dokumenty a zkompilovat nový TXT až po explicitním lidském výběru.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 3.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/communication/janicka_r2_backend.py`, `Samantha_Agent/app/communication/janicka_r2_compiler.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`, `Samantha_Agent/app/communication/janicka_r2_document_selection.py`
- Commit: `Add human-selected R2 document compilation`
- Další krok: Vytvořit checkpoint, nasadit změnu a provést živý dvoukrokový test hledání a výběru.

### Automatický checkpoint 2026-07-28 15:14 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: Janička má samostatnou stránku pro bezpečné hledání, ruční výběr a vytvoření nového TXT bez terminálu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1182 testů, 278.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/communication/janicka_r2_cockpit.py`, `Samantha_Agent/tests/test_janicka_r2_cockpit.py`
- Commit: `Add thin Janička R2 document UI`
- Další krok: Vytvořit checkpoint, nasadit změnu a ručně projít hledání, výběr a vytvoření jednoho nového TXT.

### Automatický checkpoint 2026-07-28 17:16 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: Janička má samostatný čistý chat R2-Adam s vlastním trvalým vláknem a bez vývojových ovladačů.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1188 testů, 319.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_janicka_r2_cockpit.py`, `Samantha_Agent/app/communication/janicka_r2_chat.py`, `Samantha_Agent/tests/test_janicka_r2_chat.py`
- Commit: `Add standalone R2-Adam chat`
- Další krok: Vytvořit checkpoint, nasadit změnu a živě odeslat první neškodnou zprávu v novém chatu R2-Adam.

### Automatický checkpoint 2026-07-28 17:55 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2 chat nyní ukazuje aktuální dokumenty v kompaktní liště a otevírá jejich plný obsah v samostatné celostránkové čtečce.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1191 testů, 277.4 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/janicka_r2_chat.py`, `Samantha_Agent/app/communication/janicka_r2_documents.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_janicka_r2_chat.py`
- Commit: `Add R2 document shelf and reader`
- Další krok: Vytvořit checkpoint, nasadit změnu a živě otevřít jeden existující TXT z dokumentové lišty.

### Automatický checkpoint 2026-07-28 18:35 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam může v chatu bezpečně vytvořit nový přehled z více výslovně potvrzených zdrojů, aniž by jejich obsah nafukoval chat.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/communication/janicka_r2_backend.py`, `Samantha_Agent/app/communication/janicka_r2_chat.py`, `Samantha_Agent/app/communication/janicka_r2_compiler.py`, `Samantha_Agent/app/communication/janicka_r2_document_selection.py`, `Samantha_Agent/tests/test_janicka_r2_chat.py`, `Samantha_Agent/tests/test_janicka_r2_documents.py`
- Commit: `Add confirmed multi-source R2 overviews`
- Další krok: Vytvořit checkpoint, nasadit změnu a provést živý chatový test se dvěma neškodnými zdroji.

### Automatický checkpoint 2026-07-28 19:19 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam umí bezpečně vytvořit úplný soupis nebo přehled z více než pěti potvrzených dokumentů bez tichého oříznutí výsledků.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (10): `Samantha_Agent/app/communication/janicka_r2_backend.py`, `Samantha_Agent/app/communication/janicka_r2_chat.py`, `Samantha_Agent/app/communication/janicka_r2_compiler.py`, `Samantha_Agent/app/communication/janicka_r2_document_selection.py`, `Samantha_Agent/app/documents/search_service.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_document_search_service.py`, `Samantha_Agent/tests/test_janicka_r2_chat.py`, `Samantha_Agent/tests/test_janicka_r2_complete_selection.py`
- Commit: `Support complete batched R2 document sets`
- Další krok: Vytvořit checkpoint, nasadit změnu a živě ověřit soupis z více než pěti dokumentů.

### Automatický checkpoint 2026-07-28 20:50 CEST

- Pracovní proud: `project-r2-adam-janicka`
- Hotovo: R2-Adam nyní bezpečně zpracuje úplnou potvrzenou sadu pojišťovacích dokumentů a používá strukturované údaje z celého dokumentu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (10): `Samantha_Agent/app/communication/janicka_r2_backend.py`, `Samantha_Agent/app/communication/janicka_r2_chat.py`, `Samantha_Agent/app/documents/consistency_audit.py`, `Samantha_Agent/app/documents/search_service.py`, `Samantha_Agent/app/documents/vault.py`, `Samantha_Agent/tests/test_document_consistency_audit.py`, `Samantha_Agent/tests/test_document_search_service.py`, `Samantha_Agent/tests/test_document_vault_tools.py`, `Samantha_Agent/tests/test_janicka_r2_chat.py`, `Samantha_Agent/tests/test_janicka_r2_complete_selection.py`
- Commit: `Fix complete R2 insurance overviews`
- Další krok: Vytvořit checkpoint, nasadit změnu a zopakovat praktický přehled šesti dokumentů v chatu R2-Adam.
