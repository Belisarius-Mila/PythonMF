# Správa dokumentů a soukromý trezor

Pracovní proud project-document-vault
Priorita 1
Stav opravy lokálně dokončené, čeká samostatné nasazení a přejímka iPhonu
Připomenout při startu ne

<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-11-26 15:36 CET

### Hotovo
- PDF má návrat do Dokumentů a ScanDocu umožňuje přesun skenů i uložených dokumentů do obnovitelného koše.

### Otevřeno
- Potřeba následného nasazení tohoto checkpointu není v provozním snapshotu určená.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Samostatně potvrdit vydání lokální opravy; poté fyzicky ověřit návrat z PDF a koš na iPhonu.

### Rozhodnutí
- PDF se otevírá ve stejném okně s návratem do Dokumentů. Původní sken a zařazený dokument se přesouvají do koše jednotlivě po potvrzení.

### Navrhované další kroky
- Po nasazení ověřit návrat z vícestránkového PDF na iPhonu v Safari i aplikaci z plochy.
- Vyzkoušet koš a obnovu původního skenu i již zařazeného dokumentu.
- Vyzkoušet vícestránkové PDF ze systémového skeneru iPhonu.

### Technický stav checkpointu
- Změna je otestovaná (67 testů).
- Git před checkpointem: lokální `main` na `75b3d27a9172`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: serverová deployment receipt pro tento proud není dostupná.
- Read-only živý stav: main=`aligned`, deployment=`unverified`, runtime=`unverified`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

## Podklady pro navázání

- Projektová paměť v memory/projects/document_management_private_vault.md
- Průběžný záznam v memory/tvbcp/workstreams/project-document-vault.md
- Pravidla v memory/technical/private_document_vault_workflow.md
- Příjem v app/documents/scan_inbox.py
- Ovládání v app/frontend/cockpit/document_scan.js
- Návazné zpracování v app/documents/scandocu.py
- Historický intake checkpoint v memory/handoffs/document_email_attachments_scandocu_metadata_checkpoint_2026_06_16.md

Starší dokumentový trezor, příjem příloh a existující ScanDocu jsou popsány
v projektové paměti a historických handoffech. Tento proud zastřešuje také
novou čtečku. Skutečné dokumenty, OCR texty a osobní údaje patří pouze
do soukromého dokumentového úložiště.

### Automatický checkpoint 2026-11-26 15:36 CET

- Pracovní proud: `project-document-vault`
- Hotovo: PDF má návrat do Dokumentů a ScanDocu umožňuje přesun skenů i uložených dokumentů do obnovitelného koše.
- Otevřeno: Potřeba následného nasazení tohoto checkpointu není v provozním snapshotu určená.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: cílená Cockpit brána: 67 testů, 52.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (24): `Samantha_Agent/app/capabilities/registry.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/cockpit_document_readers.py`, `Samantha_Agent/app/cockpit_frontend.py`, `Samantha_Agent/app/documents/scan_inbox.py`, `Samantha_Agent/app/documents/scandocu.py`, `Samantha_Agent/app/documents/search_service.py`, `Samantha_Agent/app/frontend/cockpit/document_scan.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/memory/LESSONS_LEARNED.md`, `Samantha_Agent/memory/handoffs/workstreams/project-document-vault.md`, `Samantha_Agent/memory/projects/document_management_private_vault.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-document-vault.md`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/document_reader_frontend.test.cjs`, `Samantha_Agent/tests/document_scan_frontend.test.cjs`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/tests/test_cockpit_scandocu_proxy.py`, `Samantha_Agent/tests/test_document_archive_browser.py`, `Samantha_Agent/tests/test_document_vault_tools.py`, `Samantha_Agent/app/documents/lifecycle.py`, `Samantha_Agent/app/frontend/shared/document_lifecycle.js`, `Samantha_Agent/tests/test_document_lifecycle.py`
- Commit: `Fix scan PDF navigation and add recoverable document trash`
- Další krok: Samostatně potvrdit vydání lokální opravy; poté fyzicky ověřit návrat z PDF a koš na iPhonu.
