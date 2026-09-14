# Camino — změny v0.3 → v0.4

**Datum:** 14. září 2026. **Stav:** nová funkční specifikace, ne implementace. Původní soubory nebyly přepsány.

## Zachováno jako potvrzené

Film cestopis + osobní příběh orientačně 20–30 minut; vedle něj podrobný deník. Krátká audio i úvahy, požadavek na zámek telefonu, jemné opravy úvah, bez povinné večerní práce, jeden autor, soukromý archiv a volitelný rodinný výběr. „Jen pro mě“ vylučuje film a rodinu, nikoli externí AI. Body polohy z aplikace, celá trasa z hodinek. Autentický hlas, případně pozdější nové namluvení, bez umělého hlasu. Podmíněná přijatelnost poplatku Apple, neurčený AI rozpočet.

## Co v0.4 přidává

Patnáct obrazovek UI00–UI14 s přesným vstupem, obsahem, akcemi a chybami. Sedmdesát tři funkčních pravidel F01–F73. Osmdesát akceptačních scénářů T001–T080 a vazbu na malé úkoly C00–C11. Odděluje se první pouť P0, volitelné rodinné sdílení P1 a film po návratu P2.

Konkrétně je definováno přiřazování příloh do Momentu, lokální záznam bez AI, rozpracovaný text, pozdější vzpomínka, importní reprezentace, nejistá časová metadata, trvalá fronta, potvrzení celého souboru, obnova journalu, konzistentní záložní snapshot, neaktuální souhrn a čtyři oddělené stavy.

## Nová návrhová rozhodnutí Samanthy, nikoli další uživatelův souhlas

| Oblast | Zpřesnění |
|---|---|
| Režim soukromí nových záznamů | Výchozí Do deníku; pak se pamatuje do změny. Zámek se sám nevypne návratem na domovskou obrazovku. |
| Editace | V P0 upravuje obsah a soukromí jen hlavní iPhone. Web je pro čtení a provozní stav. |
| Soukromý dodatek | Samostatná zamčená úvaha s vazbou, nikoli nejasně skrytá příloha běžné fotografie. |
| Hovor a mikrofon | Přerušit a zachovat dosavadní rozsah; pokračování pouze vědomým krokem. |
| Přenosy | Automaticky Wi-Fi; jednorázové mobilní povolení pro konkrétní dávku. |
| Systémové Fotky | Vlastní záznamy se tam automaticky neduplikují; import vytvoří vlastní kopii předaných dat. |
| Skrytí | Vratné vyřazení z deníku, ne fyzický výmaz a ne uvolnění místa. |
| Přepis videa | V P0 pouze samostatné hlasové nahrávky; ne automaticky všechny video ruchy. |
| Rodinný export | V P1 až po aktuální kontrole soukromí; bez offline předávání starého výběru. |
| Rozhraní filmu | V P0 žádná prázdná záložka nebo povinný večerní render. |

Tyto volby se dají na základě testů či Mílova podnětu upravit. Žádná neznamená nákup, nový souhlas s publikací nebo schválení finančního limitu.

## Vyjasněné hranice

Fotografie ukázaná jako náhled není nutně celá stažená z iCloudu. Importovaná upravená reprezentace se nesmí vydávat za nedotčený původní senzorový soubor. Stovka procent uploadu není dokončené ověření. Záloha médií neprokazuje, že už obsahuje novou změnu zámku. Kopie v Souborech na telefonu není nezávislá záloha. Přepis není jistě doslovný a strukturovaný výstup AI není důkaz pravdivosti.

Předání výběru komunikační aplikaci není důkaz doručení. Soukromí nelze zpětně vynutit u již odeslané cizí kopie. Server nezná neodeslanou offline změnu. Obnova starého serveru proto musí porovnat nový stav telefonu před novými exporty.

## Co zůstává k ověření, nikoli k opakovanému dotazování

Skutečný vývojový Mac vs domácí Mac server; verze systému a nástrojů; platnost instalace; mikrofon; chování nahrávání a přenosů na zamčeném telefonu; záložní disk a restart zabezpečeného Macu; reálná velikost a spotřeba testovacího dne. Částku pro API je potřeba rozhodnout před placeným pilotem. Export hodinek patří do pozdějšího ověření a neblokuje první záznamovou aplikaci.
