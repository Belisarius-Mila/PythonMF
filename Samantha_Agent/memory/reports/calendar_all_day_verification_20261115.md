# Ověření celodenního zápisu z e-mailu — 2026-11-15

Míla potvrdil funkční UI a nahlásil nepotvrzené uložení termínu. Čtecí diagnóza
našla jeden create a následné recover, full_access v nativním servisním kontextu,
správně uchovaný unknown a jednu odpovídající celodenní událost v cílovém kalendáři.
Její začátek odpovídal, konec byl o1 sekundu dříve. Přesná původní markerová
identita zatím není novým helperem živě potvrzená; podle názvu se nic neuzavírá.

Apple [TN3130](https://developer.apple.com/documentation/technotes/tn3130-changes-to-eventkit-in-macos13-ventura)
potvrzuje změnu nativního celodenního endDate na23:59:59 posledního dne.
Původní verifier vyžadoval půlnoc dalšího dne, takže tento platný výsledek odmítal.

## Provedená oprava

- V2 nativní verifier a Python přijímají jen tuto přesnou celodenní rovnocennost;
  skutečné nativní end i ostatní identifikační údaje se v účtence zachovají.
- Přehled opravuje výlučné end_day pro celodenní zobrazení. Nativní end zůstává
  beze změny, čtecí helper ani navazující mazací/editační helper se nepřestavují.
- Původní Swift soubor je zachovaný pro stávající živé sestavení. Nová generace
  má vlastní zdroj a vyžaduje nové produkční sestavení/OS přístup po nasazení.
- UI odhalí zastaralý build i potřebu oprávnění při obnově; zachová původní UUID
  a unknown. Obnova nikdy neprovádí druhý create, ani když původní událost nenajde.

## Ověření a hranice

Původní zdroj v novém nativním testu FAIL přesně na all-day create verification.
Opravený zdroj:21 nativních scénářů PASS bez skutečného EventKit;69 prvních
cílených a238 rozšířených integračních testů PASS. Moderní i staré konce,
vícedenní/DST, pevné GMT pásmo, časovaná sekunda, zlomky, chybná data/marker,
duplicitní shoda, alarmy, starý journal a ztráta oprávnění při recover.

Izolovaný build/podpis/6 self-test PASS. První build pod Desktop odmítl codesign
kvůli Finder metadatům; zůstal zachovaný a nebyl spuštěný. Úspěšný preview je
v oddělené vlastní aplikační složce mimo Desktop, produkční build.json beze změny.
Jeho jediný read-only recover správně skončil authorization_required, bez
vyžádání OS souhlasu a s calendar_writes=false. Původní state.json se neměnil.

Povinná plná brána následuje před lokálním commitem; skutečný závěrečný výsledek,
počty, zdrojový manifest a commit obsahuje pouze
`data/private/calendar_all_day_fix_20261115/completion.json`. Tento verzovaný
zápis se po závěrečné bráně nemění, aby se commitoval přesně ověřený obsah.
Bez skutečného PASS v účtence není krok uzavřený.

Samostatné p+n tohoto kroku, produkční přestavba/grant a čtecí převzetí původní
události zatím neproběhly. Další krok je jejich potvrzené provedení ve stejném
operation_id; nesmí se odeslat nový create. Testy nejsou živá přejímka iCloud/Safari.
Kanonická pravidla: technical/calendar_all_day_boundaries.md. E-mailový TVBCP
není dohodnutý; tento společný kalendářový/UI krok kryje existující Cockpit TVBCP.
