# Interiérový architekt — dokumentace projektu

Aktualizováno: 2026-11-25. Pracovní proud: `project-neuberk-kacenka`.
Kanonický název: **Interiérový architekt**. Vývojový směr: **Interior Architect 2.0**.
Typ `Project`, stav `active`, priorita 2.

## Účel a rozsah

Jeden projekt Samanthy pro navrhování interiérů, se dvěma dosud rozpracovanými
místnostmi: Kačenka a místnost z dosavadního Ateliéru. V současném úložišti
Ateliéru se druhá místnost jmenuje Koupelna dolní; její případné nové zobrazované
pojmenování zatím není potvrzené. V tomto kroku se názvy ani identity soukromých
dat nemění. Místnosti nebudou samostatnými proudy Human–Adam.

Cílem verze 2.0 je nové aplikační jádro a nové UI uvnitř existující Samanthy:
ruční masky, ověřený model místnosti, deterministický půdorys a později 3D,
řízené obrazové úpravy a pravdivá validace výsledků. Současné návrhy obou
místností zůstávají zachované a budou přístupné jako historické varianty.

„Samantha SDK“ v dodaném balíčku označuje tento existující projekt
Samantha_Agent/Cockpit; nevzniká nový repozitář. Komunikace přes Codex App Server
se tímto rozhodnutím nemigruje na OpenAI Agents SDK. Znovu se navrhne backend
aplikace a UI; osvědčenou nižší infrastrukturu lze převzít po auditu.

## Kde pokračovat

| Dokument | Odpovědnost |
|---|---|
| [Projektová paměť](../neuberk_interier_design.md) | Aktuální souhrn a zachovaná historie verze 1 |
| [Handoff](../../handoffs/workstreams/project-neuberk-kacenka.md) | Stav pro obnovení práce a bezprostřední další krok |
| [TVBCP](../../tvbcp/workstreams/project-neuberk-kacenka.md) | Potvrzená rozhodnutí, milníky, důkazy a otevřené otázky |
| [Technický audit](AUDIT.md) | Jak v1 ukládá data, proč dovolí posun geometrie a co ověřily místní zkoušky |
| [Návrh backendu](BACKEND.md) | Soukromé úložiště, kontrakty, ochranné masky, scéna, validace a milníky |
| [Návrh pracovního UI](UI.md) | Výběr místnosti, plátno na Macu i iPhonu, historie a přejímka |
| [Převod obou místností](MIGRATION.md) | Změřená inventura, původové vazby, zkušební import, přepnutí a návrat |
| [SPECIFICATION.md](reference/SPECIFICATION.md) | Výchozí technické zadání 2.0 |
| [ARCHITECTURE.md](reference/ARCHITECTURE.md) | Navržené služby a datové toky |
| [ROADMAP.md](reference/ROADMAP.md) | Vývojové etapy a první implementační sprint |
| [TEST_PLAN.md](reference/TEST_PLAN.md) | Požadovaná přejímací kritéria T01–T19 |
| [SCENE_MODEL.json](reference/SCENE_MODEL.json) | Pouze ilustrační datový příklad, nikoli schéma nebo zaměření místnosti |
| [OVERVIEW.html](reference/OVERVIEW.html) | Ilustrační lidský přehled |

Starší názvy Neuberk interiér / Kačenka, Neuberk interier design / Kacenka,
Interiérový ateliér a Ateliér zůstávají dohledatelnými aliasy jednoho proudu.
Technické ID, cesty k handoffu/TVBCP a původní soukromé cesty zůstávají stabilní.

## Zdroj a jeho platnost

Sedm souborů v `reference/` je byte-identická kopie balíčku
`Samantha_Interior_Architect_2.0.zip`, který Míla dodal po diskusi s ChatGPT Pro.
SHA-256 původního ZIPu:
`db40aa780a759f5c611c45edbf68f7422c8c8a13b267aa55b1d59bd7328104c3`.
Původní [START_HERE.md](reference/START_HERE.md) je zachovaný jako součást zdroje.

Míla po sjednocení názvu zadal technický audit a návrh řešení. Ty jsou hotové.
Dokumenty v tomto adresáři popisují návrh pro současnou Samanthu. Sedm souborů
v `reference/` uchovává dodané zadání v původním znění. Implementace a přepnutí
rodinného vstupu jsou další etapy. Aktuální rozhodnutí eviduje TVBCP.

## Hranice ověření

- Původní fotografie a návrhy jsou neměnné soukromé podklady mimo Git.
- Pixelový zámek se ověřuje proti normalizovanému bezeztrátovému rastru
  stejného pohledu, nikoli proti JPEG bajtům nebo nové kameře.
- Nulová změna chráněných pixelů není důkaz geometrické správnosti uvnitř
  upravované oblasti. Geometrie fotografie může zůstat neověřená.
- Hodnoty v příkladu scene modelu se nesmějí převzít jako míry žádné místnosti.
- Současný obrazový most nemá doloženou podporu skutečných editačních masek;
  schopnosti budoucího adaptéru musí ověřit audit.
- Bez nových placených volání, instalace velkých modelů, migrace soukromých dat,
  změny rolí, restartu služeb a p+n v tomto dokumentačním kroku.

## Další krok

Navržený první implementační milník je místní práce nad jednou syntetickou fotografií.
Na Macu a iPhonu půjde vyznačit ochranu, uložit ji, otevřít po návratu a porovnat
výsledek s originálem. Po přejímce jádra následuje zkušební import obou místností
na oddělené kopii.
