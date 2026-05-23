Nazev: Commitove odpoledne - uklid rozpracovanych zmen
Priorita: A1+
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-23

Co se resilo:
- Mila potvrdil, ze se rozpracovane zmeny v repozitari rychle hromadi a je potreba je uklidit po tematickych commitech.
- Dohodnuto ad hoc pravidlo: do odvolani opakovane navrhovat commitovy uklid, kdykoli Mila meni projekt nebo zada novy ukol.

Co je hotove:
- Ulozen akutni ukol priorita A1+.
- Prvni konkretni uklidovy krok je projekt `network/reconnect recovery`.

Co neni hotove:
- Zbyva postupne projit a commitnout nebo odlozit ostatni rozpracovane oblasti.
- Nesmichavat nesouvisejici soubory do jednoho commitu.

Dalsi krok:
- Po dokonceni prvnich tematickych commitu navrhnout dalsi tematicky commit podle aktualniho git stavu.
- Po velkem commitovem uklidu hned nabidnout probrani A1+ rustovych pravidel Samanthy a hlavne audit/uklid bobtnajicich handoffu podle `memory/technical/samantha_growth_rules.md`.
- Nabidnout tri maximalne prioritni body: cisty stul, pouceni z uklidu a jasnejsi rezim dalsiho vyvoje.

Navrhovane dalsi kroky:
- `network/reconnect recovery` - dokoncit a pushnout samostatny commit.
- `Sprava dokumentu / private vault` - samostatny commit po fyzickem overeni tisku nebo po dalsim potvrzenem kroku.
- `iCloud/Seznam Mail read-only` - samostatny commit pouze pro e-mailove tooly a testy, bez citlivych dat.
- `Tomik video / FamilyVideoOrganizer` - samostatny commit pro git-safe UI a bez soukromych videi/dat.
- `Reminders / platebni SMS` - samostatny commit pro tooly a testy, bez plnych URL nebo tokenu.
- Pametove soubory a handoffy uklidit v samostatnem memory-only commitu, pokud budou prilis promichane s vice projekty.
- Po velkem commitu probrat `technical/samantha_growth_rules.md`, vcetne plosneho auditu starych handoffu.
- Pilotne udelat `handoff compression per project`, idealne nejdrive pro `Sprava dokumentu / private vault`, potom pro `E-mail`.

Zmenene nebo relevantni soubory:
- `memory/handoffs/git_commit_cleanup_a1_2026_05_23.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do commitu nepridavat `data/private/`, `.env`, tokeny, API klice, app-specific passwords, cele e-maily, plne citlive URL ani soukrome dokumenty.
- Nepouzivat `git add .`; pridavat jen konkretni cesty.
