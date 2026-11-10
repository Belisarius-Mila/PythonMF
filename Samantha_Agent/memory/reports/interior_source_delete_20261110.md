# Ateliér — potvrzené trvalé mazání podkladů

Implementace vznikla v izolovaném pracovním stromu nad `fee535e5`, bez zásahu do souběžného Data vývoje. Výslovně schválené p+n nyní potvrdilo push a nasazení `748cec00` do Cockpitu přes Terru. Skutečné rodinné podklady se nemazaly; nevolal se AI architekt ani generování obrázků.

## Výsledek

- Každá kartička Podklady má Smazat, předem čtecí náhled velikosti, sdílení a dopadu, potom přesnou potvrzovací větu globální brzdy. Zrušení nic nemaže.
- Smazání zahrnuje nesdílené originály, oba náhledy a příslušné AI pracovní kopie včetně obrazového výsledkového JSON. Mimo Ateliér uložené originály/Downloads, starší podklady a zálohy se neprocházejí ani nemažou.
- Texty, varianty a poznámky zůstávají; mazaný obrázek a jeho kresba se odpojí od všech souvisejících variant a draftů, revize dotčených draftů se zvýší. Lokální browser cache odfiltruje smazané reference a zachová rozepsaný text.
- Jiným podkladem používané soubory se zachovají; náhled uvádí jen skutečně mazatelné logické bajty. APFS fyzické bloky ani diskové úspory otevřených souborů se neměří.
- Neukončená či nejistá AI blokuje mazání, příprava AI snapshotu a obrazové mutace používají společný zámek.
- Před fyzickým odstraněním se atomicky uloží neobrazový záznam operace. Přerušení, částečný unlink nebo selhání finálního JSON commitu lze bezpečně dokončit stejným požadavkem. Výsledek se neopakuje automaticky; starý AI recover neumí data znovu založit.

## Ověření

- 129 cílených kontrol PASS: `tests.test_interior_atelier`, `tests.test_interior_ai`, `tests.test_interior_ai_activation`, `tests.test_cockpit_interior`, `tests.test_capability_registry`, `tests.test_cockpit_frontend`, `tests.test_capability_audit`; HTTP testy spouštějí také oba Node frontendové scénáře.
- Regrese pokrývají přesné potvrzení, změněný token, souběžné revize, cizí místnost, symlink/hardlink, sdílené objekty, přerušený unlink, chybu finálního commitu, AI snapshot souběh, neobnovení smazaného AI výsledku, dvojklik, nejisté HTTP a zachování neuloženého textu.
- Nativní Safari: oddělený syntetický server, otevření Podkladů/dialogu, vizuální kontrola deaktivovaného finálního tlačítka před potvrzením, Escape a zachování podkladu. Finální smazání v browseru nebylo spuštěné. Zkušební panel a server uzavřené; původní živý panel zachovaný.
- První plná brána zkontrolovala 3426 testů a našla dva neaktualizované kontrolní údaje (HTML otisk/délka a počet rizikových schopností). Ty byly upravené podle skutečného rozšířeného rozhraní a registru; oba moduly 26/26 PASS. Opakovaná plná brána 3426 testů OK / 31 SKIP.
- Důkazy mimo Git: `data/private/interior_source_delete_20261110/` v kanonickém projektu; pracovní větev `adam/interior-source-delete-20261110`.

## Hranice a další krok

Výslovné p+n je dokončené; nasazený runtime je ověřený. Další krok je obnova stránky v prohlížeči a lidská Mac/iPhone přejímka. Výsledkový paměťový checkpoint zůstává místní pro příští balíček a sám nespouští další vydání.

Ateliér dosud nemá výslovně dohodnutý nový TVBCP. Na volbu byla položená otázka; bez odpovědi se nezakládá. Pro tento terminálový krok se aktualizují stávající handoff, projektová paměť a registry; budoucí vývoj přes Human–Adam musí vazbu dořešit.

## 2026-11-10 16:41 CET — Mazání podkladů nasazené

Na Mílovo výslovné „ok, p+n“ je `748cec00c3ab4e4f873b911c5ceb3547e6659caf` odeslaný na GitHub a nasazený do běžícího Cockpitu v proudu `project-neuberk-kacenka`. Jediné registrované předání přes Terru 6.1/high: `3eddf9c73d866c2a196b447b09762bd7`, completed, push/deployment confirmed. Publikační brána 3426 testů PASS, 655,5 s, smoke 5/5; code_stamp `76ec558a9e3b0742`, chráněné služby beze změny.

Živá stránka HTTP 200 je byte-identická s vydaným rozhraním (SHA-256 `9b781db4341853eb01074c8dbe4c7ad3d81a95e1f3d8f2bdcabf3b0fb563d2ff`) a obsahuje nové tlačítko. Čtecí `/api/interior/delete-preview` je dostupné a vrací přesný rozsah i potvrzení. Před/po shodný otisk manifestu: všech 27 podkladů a 25 variant zachovaných. Nevolala se mazací akce ani požadavek AI architektovi, do Data se nezapisovalo.

Další krok: obnovit stránku Ateliéru v prohlížeči a provést lidskou přejímku ovládání na Macu/iPhonu. Tato přejímka není nahrazená HTTP ani dřívější syntetickou zkouškou dialogu. Skutečné smazání bude vždy samostatná explicitní uživatelská akce. Výsledkový paměťový zápis zůstává místní pro další balíček; další p+n se kvůli němu neopakuje. TVBCP se bez nové dohody nezakládá. Důkazy: `data/private/interior_source_delete_20261110/release/`.
