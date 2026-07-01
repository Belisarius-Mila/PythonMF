Nazev: Knihovna clanku - oprava kodovani, UI potvrzeni a recovery zaloha
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-01

Co se resilo:
Mila nahlasil, ze URL clanek s ceskym textem se do Knihovny ulozil s rozbitym
pismem a neprehlednym obsahem. Soucasne chtel vycistit chybne soukrome zaznamy,
presunout carbonara polozku do receptu a potom provest zalohu.

Co je hotove:
- `app/article_archive.py` respektuje deklarovane HTML kodovani a fallbacky pro
  ceske weby se starsim kodovanim.
- Extrakce preferuje hlavni obsah v `div#clanek`, `article` nebo `main`.
- Cockpit po ulozeni URL zobrazi jasne potvrzeni a otevre ulozenou polozku.
- Rozbite soukrome GVT polozky byly podle Milova pokynu odstraneny natvrdo mimo git.
- Cisty GVT zaznam byl znovu ulozen do soukromeho archivu se spravnou cestinou.
- `Špagety ala carbonara` byly v soukrome knihovne presunuty do `Recepty`.
- Probehla ostra recovery zaloha `PythonMF` do snapshotu `20260701_203915` a
  maly restore drill souboru `Samantha_Agent/AGENTS.md`.

Co neni hotove:
- Neni commitnuty soukromy obsah archivu; zustava jen lokalne v `data/private/`.
- Browser muze mit otevreny stary Cockpit tab; pri testu je vhodny tvrdy reload.

Dalsi krok:
Pri dalsim rucnim testu Knihovny otevrit Cockpit, udelat `Cmd+Shift+R` a overit,
ze ulozeni stejne URL ukaze potvrzeni `Otevřeno: ...` a otevreny detail clanku.

Navrhovane dalsi kroky:
- Pokud se objevi dalsi web se spatnym kodovanim, pridat cilovy test nad jeho
  minimalnim HTML vzorkem.
- Pozdeji zvazit deduplikacni hlasku typu `Polozka byla aktualizovana`, aby
  opakovane ulozeni stejne URL bylo jeste citelnejsi.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `memory/projects/vedecke_clanky.md`
- `memory/projects/samantha_external_backup.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Neopisovat plny text soukromych clanku.
- Necommitovat `data/private/article_archive/`.
- Nemanipulovat s dalsimi clanky natvrdo bez vyslovneho pokynu Mily.
