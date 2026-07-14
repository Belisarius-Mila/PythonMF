# Pravidla projektových TVBCP

TVBCP je průběžný human–machine rozhodovací dokument většího projektu nebo
ucelené vývojové úlohy. Drží zhuštěné pracovní vlákno po celou dobu vývoje.

## Kdy TVBCP založit

- Pouze po výslovné dohodě Míly a Adama.
- Pro větší projekt, významnou architektonickou změnu nebo delší úlohu s více
  rozhodnutími a milníky.
- Ne automaticky pro malou funkci, drobnou opravu, krátký test nebo snadno
  opakovatelný zásah.

## Umístění a dohledatelnost

- Git-safe projektový TVBCP patří do `memory/tvbcp/`.
- Aktivní TVBCP se odkáže z `memory/MEMORY_INDEX.md` a z příslušné položky v
  `memory/ACTIVE_PROJECTS.md`.
- Pokud projekt pracuje s citlivými daty, gitový TVBCP obsahuje pouze redigovaný
  stav a bezpečné závěry. Citlivý detail zůstává v odpovídajícím private úložišti.

## Co průběžně zapisovat

- cíl a hranice projektu;
- podstatné návrhy Míly a Adama;
- přijatá kanonická rozhodnutí a jejich důvod;
- významné vývojové kroky a milníky;
- důležité automatické a ruční testy;
- otevřené kroky, blokátory a rizika;
- změny cílové architektury nebo bezpečnostního kontraktu.

TVBCP není úplný přepis chatu. Vynechává provozní mezistavy, běžné tool výstupy,
opakování a textovou omáčku.

## Chronologické záznamy

- Každý nový průběžný záznam se přidává na konec souboru, ne doprostřed staršího
  protokolu.
- Nadpis záznamu vždy obsahuje místní datum, čas a časovou zónu ve formátu
  `YYYY-MM-DD HH:MM TZ`, například `2026-07-14 13:13 CEST`.
- Souhrnné sekce, tabulky milníků a otevřené kroky lze aktualizovat na jejich
  místě, ale odpovídající nový vývojový záznam musí být současně dohledatelný na
  konci dokumentu.
- Jeden časovaný záznam stručně oddělí požadavek nebo rozhodnutí, provedenou
  implementaci, důkaz testu a další krok. Nekopíruje celý chat.

## Vztah k ostatním vrstvám paměti

- TVBCP: průběžná smlouva, rozhodnutí a vývojové vlákno.
- Handoff: stav pro přerušení, obnovu nebo předání práce.
- Autosave: nouzová technická obnova konverzace.
- Capsule: kompaktní předání při rotaci relace nebo havárii.
- Project memory: dlouhodobě platný stav oblasti.

Tyto vrstvy se navzájem nenahrazují.

## Ukončení nebo archivace

Při dokončení projektu se do TVBCP doplní konečný výsledek, důkazy testů,
zbývající rizika a případný další směr. Dokument se nemaže. Změna stavu a odkazy
se promítnou do registru aktivních projektů a paměťového indexu.
