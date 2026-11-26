# Správa dokumentů a soukromý trezor

Pracovní proud project-document-vault

Cílem je příjem, kontrola, uložení a další zpracování soukromých dokumentů.
Dokumenty a extrahované texty patří mimo Git.

<!-- SAMANTHA_CURRENT_STATUS_START -->

## 2026-11-26 06:02 CET — Čtečka dokumentů a ScanDocu

### Hotovo

V Cockpitu v sekci Dokumenty funguje tlačítko Naskenovat dokument. Z iPhonu
lze postupně přidat fotografie, upravit pořadí stran, odebrat chybnou stranu,
zkontrolovat náhled a název a potvrdit uložení jednoho soukromého PDF.
Lze také vložit PDF z vestavěného skeneru iPhonu. Uložené skeny mají vlastní
seznam a lze je jednotlivě otevřít nebo předat do ScanDocu.

### Rozhodnutí

Čtečka, příjem, soukromé uložení a návazné zpracování ve ScanDocu patří do
proudu project-document-vault. Cockpit zajišťuje společné uživatelské rozhraní.
Potvrzení uložení PDF je první krok. OCR, metadata a konečné zařazení
do trezoru se provedou následně ve ScanDocu. Přijetí skenu nepoužívá placenou
analýzu. Soukromé dokumenty zůstávají mimo Git.

První verze snímá fotografie přímo v prohlížeči a zmenší delší stranu na
1800 pixelů. Pro automatický ořez hran lze použít PDF ze systémového skeneru.
Jeden dokument podporuje nejvýše 30 stran, vstupní PDF nejvýše 24 MB.
Přenos při opakování používá stejné ID a chrání uložený dokument před přepsáním.
Cockpit předává vybraný sken i staršímu běžícímu ScanDocu.

### Další krok

Fyzicky vyzkoušet na Mílově iPhonu několik stránek včetně čitelnosti náhledu,
pořadí, potvrzení uložení a otevření správného skenu ve ScanDocu.

### Navrhované další kroky

Vyzkoušet také vícestránkové PDF z vestavěného skeneru iPhonu.

### Technický důkaz

Implementace 7cc346bd byla přes Terru vydaná spolu s Datovým commitem 74e6c660.
Brána prošla 1779 testy a nasazení pěti provozními kontrolami. Následný živý
audit ověřil stránku čtečky, příjem skenů, cestu ke ScanDocu a shodu GitHubu.
Samostatná regrese staršího ScanDocu prošla 13 testy. Fyzický test iPhonu
dosud není přijatý. Autorita vydání je soukromá účtenka
data/private/document_scan_20261125/completion.json.

<!-- SAMANTHA_CURRENT_STATUS_END -->
