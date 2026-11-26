# Správa dokumentů a soukromý trezor

Pracovní proud project-document-vault

Cílem je příjem, kontrola, uložení a další zpracování soukromých dokumentů.
Dokumenty a extrahované texty patří mimo Git.

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

## 2026-11-26 14:05 CET — Návrat z PDF a koš uložených dokumentů

### Hotovo

Lokální změna otevírá PDF skenů v Cockpitu s návratem do Dokumentů bez
ztráty rozpracovaných stran. ScanDocu nabízí přesun skenu i už zařazeného
dokumentu do koše a jejich jednotlivou obnovu. Položky v koši jsou skryté
z aktivních seznamů, vyhledávání a revizí; původní soubory zůstávají zachované.

### Rozhodnutí

Míla schválil obě opravy a výslovně zahrnul odstranění již uložených
nekvalitních nebo chybných dokumentů. Přesun do obnovitelného koše potvrzuje
konkrétní kopii; původní sken a dokument v trezoru se neodstraňují společně.

### Další krok

Předat lokální změnu Cockpitu pro checkpoint a zvlášť potvrzené nasazení.

### Navrhované další kroky

- Po nasazení ověřit návrat z vícestránkového PDF na iPhonu v obou způsobech spuštění.
- Ověřit koš a obnovu původního skenu i zařazeného dokumentu.
- Vyzkoušet PDF ze systémového skeneru iPhonu.

### Technický důkaz

Závěrečné programově vybrané statické kontroly a 1739 testů prošly.
Protokol je v povolené dočasné oblasti; prostředí blokuje podpis účtenky
do Git metadat. Podepsané dokončovací potvrzení musí vystavit Cockpit. Kontroly koše zahrnují revizi,
otisk souboru, souběh, nejisté opakování, rollback a obnovu. Automatická
obnova nepokrývá starší fyzický koš bez obnovovacích metadat. Změna zatím
není nasazená a fyzická přejímka telefonu zůstává otevřená; skutečné
soukromé dokumenty nebyly upravovány.

### 2026-11-26 15:36 CET – PDF má návrat do Dokumentů a ScanDocu umožňuje přesun skenů i uložených dokumentů do obnovitelného koše.

Hotovo:
- PDF má návrat do Dokumentů a ScanDocu umožňuje přesun skenů i uložených dokumentů do obnovitelného koše.

Otevřeno:
- Potřeba následného nasazení tohoto checkpointu není v provozním snapshotu určená.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- PDF se otevírá ve stejném okně s návratem do Dokumentů. Původní sken a zařazený dokument se přesouvají do koše jednotlivě po potvrzení.

Další krok:
- Samostatně potvrdit vydání lokální opravy; poté fyzicky ověřit návrat z PDF a koš na iPhonu.

Navrhované další kroky:
- Po nasazení ověřit návrat z vícestránkového PDF na iPhonu v Safari i aplikaci z plochy.
- Vyzkoušet koš a obnovu původního skenu i již zařazeného dokumentu.
- Vyzkoušet vícestránkové PDF ze systémového skeneru iPhonu.

Technický důkaz:
- cílená Cockpit brána: 67 testů, 52.3 s, výsledek OK.
- Pracovní proud: `project-document-vault`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`unverified`, runtime=`unverified`.
