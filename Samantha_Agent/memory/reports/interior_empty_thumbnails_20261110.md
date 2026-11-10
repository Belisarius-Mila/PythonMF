# Ateliér — prázdné AI miniatury po smazání

## Příčina a výsledek

Předchozí smazání úmyslně zachovalo textové varianty, ale galerie stále vykreslovala všechny záznamy bez kontroly dostupného obrázku. Čtecí audit našel 20 AI variant bez obrázku. Oprava pouze zobrazení funguje na existujících záznamech; nemigruje a nemaže soukromá data.

- AI návrh bez existujícího obrazového podkladu zmizí z levého výběru i z odkazů k historickému AI požadavku.
- Zapamatovaný smazaný výběr se přepne na nové zadání, původní serverový text i rozepsaná lokální cache se zachovají.
- Lidské textové návrhy zůstávají dostupné jako textové kartičky bez prázdného obrazového rámečku.
- Ponechaný potomek se nenabízí k porovnání se smazaným AI rodičem.
- Právě dokončený AI výsledek ještě neznámý staršímu snímku místnosti zůstává dostupný k otevření.

## Ověření

- 36 cílených Python/HTTP/frontend kontraktů PASS: tests.test_cockpit_interior a tests.test_cockpit_frontend. Součástí jsou oba Node moduly, celkem 22 scénářů, z toho 5 nových regresí. HTML kontrakt aktualizovaný pro změněný JavaScript.
- Nativní Safari na syntetickém serveru: zapamatovaný smazaný AI výběr se načetl jako nové zadání; vlevo pouze ponechaný obrázek a lidské textové zadání bez prázdného rámu, v historii pouze platný odkaz. Ponechaná AI varianta se otevřela s obrázkem. Zkušební panel i server uzavřené, žádná mutační operace se nevolala.
- Rychlá statická brána před checkpointem. Backend, mazací protokol ani persistence se nemění; nezměněné plné testy se lokálně neopakují. Plná publikační brána zůstává povinná při případném p+n.
- Izolovaná větev adam/interior-empty-thumbnails-20261110 nad f7a4ab58, bez zápisu do Data.

## Stav a další krok

Místně opravené, bez push/deploy. Další krok je samostatně autorizované p+n a uživatelská přejímka skutečné galerie. Skutečné podklady ani textové záznamy se při této opravě nemazaly. Handoff a projektová paměť aktualizované; nový TVBCP bez dohody nevzniká. Důkazy jsou mimo Git v data/private/interior_empty_thumbnails_20261110/.
