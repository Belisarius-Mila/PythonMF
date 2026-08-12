# TVBCP: MMTX

Pracovni proud: `project-mmtx`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-07-21 07:06 CEST – Živý zapisovací pilot MMTX fáze 4.5 prošel

Pracovní proud: `project-mmtx`.

Milník: Živý zapisovací pilot MMTX fáze 4.5 prošel

Důkaz: plná Cockpit brána: 965 testů, 281.5 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Ověřit čistý main, synchronizaci legacy workspaces a vznik kanonického MMTX handoffu a TVBCP

### 2026-08-12 19:17 CEST – Samostatný prototyp Harry–Benji

Hotovo: Vznikl samostatný prototyp scény se schváleným obrazovým základem,
dvojjazyčným režimem, systémovým hlasem, bezpečným opakováním poslední věty,
výběrem Benjiho a prvním úkolem `YES/NO`. Živá třetí scéna zůstala nedotčená.

Rozhodnutí: První verze používá systémový český hlas a zůstává odděleným
prototypem, dokud neprojde ručním ověřením na Macu a iPhonu.

Další krok: Ručně ověřit vzhled, ovládání a systémové hlasy na Macu a iPhonu.

Navrhované další kroky: Po ověření doplnit výslech Bunnyho, Fiony, Sunnyho a
Bruna; potom přidat počítání pěti ovcí a otevření branky.

Technický důkaz: Prošly 3/3 cílené testy, JavaScript syntaxe a
`git diff --check`. PNG má kanonické rozměry 1672 x 941 a jeho kontrolní otisk
odpovídá schválenému private kandidátu.
