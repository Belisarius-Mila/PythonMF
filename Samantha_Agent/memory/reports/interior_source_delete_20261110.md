# Ateliér — potvrzené trvalé mazání podkladů

Místní implementace vznikla v izolovaném pracovním stromu nad `fee535e5`, bez zásahu do souběžného Data vývoje. Neproběhlo p+n, restart Cockpitu, skutečné mazání rodinných podkladů ani placený AI tah.

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

Lokální krok je ověřený; do main patří pouze bezpečný fast-forward při čistém zdroji. Samostatné p+n nebylo zadané. Nasazený runtime a fyzická iPhone přejímka zůstávají neověřené pro tuto funkci.

Ateliér dosud nemá výslovně dohodnutý nový TVBCP. Na volbu byla položená otázka; bez odpovědi se nezakládá. Pro tento terminálový krok se aktualizují stávající handoff, projektová paměť a registry; budoucí vývoj přes Human–Adam musí vazbu dořešit.
