Nazev: Commitove odpoledne - uklid rozpracovanych zmen
Priorita: A1+
Stav: aktivni pravidlo
Pripomenout pri startu: ano
Datum: 2026-05-23

Co se resilo:
- Mila potvrdil, ze se rozpracovane zmeny v repozitari rychle hromadi a je potreba je uklidit po tematickych commitech.
- Dohodnuto ad hoc pravidlo: do odvolani opakovane navrhovat commitovy uklid, kdykoli Mila meni projekt nebo zada novy ukol.

Co je hotove:
- Ulozen akutni ukol priorita A1+.
- Velka memory/RAG cleanup davka byla commitnuta a pushnuta jako
  `ef15589 Clean up Samantha memory handoffs and RAG search`.
- Repo bylo po pushi ciste.
- Pravidlo zustava aktivni do odvolani: pri delsim `git status`, zmene projektu
  nebo nove rozpracovane oblasti navrhnout tematicky commitovy uklid.

Co neni hotove:
- Nejde o jednorazovy task, ale o provozni pravidlo.
- Pri novych zmenach stale plati: nesmichavat nesouvisejici soubory do jednoho
  commitu a nepouzivat `git add .`.

Dalsi krok:
- Drzet cisty stul: pred dalsi vetsi praci vzdy zkontrolovat `git status`.
- Pokud vzniknou nove zmeny, delat male tematicke commity podle oblasti.
- Po infrastructure/network cleanupu udelat samostatny maly commit, pokud vzniknou
  souborove zmeny.

Navrhovane dalsi kroky:
- Pokracovat jen podle aktualniho `ACTIVE_PROJECTS.md`, ne podle stareho seznamu
  rozpracovanych commitu v tomto handoffu.
- Infrastructure/network reconnect cleanup je dalsi vybrana oblast po commitu
  `ef15589`.
- Pokud bude git stav opet narustat, navrhnout dalsi tematicky commit pred
  zmenou projektu.

Zmenene nebo relevantni soubory:
- `memory/handoffs/git_commit_cleanup_a1_2026_05_23.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do commitu nepridavat `data/private/`, `.env`, tokeny, API klice, app-specific passwords, cele e-maily, plne citlive URL ani soukrome dokumenty.
- Nepouzivat `git add .`; pridavat jen konkretni cesty.
