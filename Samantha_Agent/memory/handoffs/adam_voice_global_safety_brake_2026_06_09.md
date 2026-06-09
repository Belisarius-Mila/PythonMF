Nazev: Adam Voice - default povolit, globalni brzda jen pro vysoke riziko
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-09

Co se resilo:
- Mila upresnil filozofii hlasove komunikace: nema byt prehnane svazana, protoze spravujeme osobni system, mame zalohy a cilem je, aby hlasovy rezim prakticky fungoval.
- Dohodnuty smer: defaultne povolit beznou praci a blokovat jen explicitne vyjmenovane vysoce rizikove veci.

Co je hotove:
- Zalozeno pravidlo `memory/technical/global_safety_brake.md`.
- `AGENTS.md` odkazuje na globalni brzdu pro vysoce rizikove destruktivni/systemove akce.
- `MEMORY_INDEX.md` obsahuje odkaz na globalni brzdu.
- Potvrzovaci veta pro akce pod brzdou je:
  `Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.`

Co neni hotove:
- Pravidlo zatim neni napojene do kodoveho routeru hlasovych schopnosti.
- Neni implementovana capability registry ani UI approval centrum.

Dalsi krok:
- Pri dalsim malem kroku navrhnout `safe_voice`/capability pravidla tak, aby bezna read-only a nizkorizikova hlasova prace prosla hladce a globalni brzda se pouzila jen pro destruktivni/systemove veci.

Navrhovane dalsi kroky:
- Okamzite: commitnout a pushnout pravidlo, aby se nacitalo v dalsich relacich.
- Pozdeji: upravit Adam/Cockpit routing tak, aby byl model `allow by default except high-risk denylist`, ne opacne.

Zmenene nebo relevantni soubory:
- `memory/technical/global_safety_brake.md`
- `AGENTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Nejsou ulozena hesla, tokeny, API klice ani tajemstvi.
- Potvrzovaci veta neni tajne heslo; je to zamerna textova brzda pred rizikovou akci.
