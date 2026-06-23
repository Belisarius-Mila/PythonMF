Nazev: Knihovna - stav clanku K precteni / Hotovo
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
Mila chtel mit v Cockpit Knihovne jednoduchou pracovni frontu clanku, ke kterym se chce vratit. Konkretni prvni pripad byl zdravotni clanek o kratkozrakosti u deti, ktery se ma zobrazovat jako `K precteni`.

Co je hotove:
- Backend Knihovny uklada u clanku `read_state`, `read_note` a `read_state_updated_at`.
- Stare clanky bez techto poli se automaticky berou jako `normal`.
- Podporovane stavy jsou `normal`, `to_read` a `done`.
- `list_articles` a `search_articles` umi filtrovat podle `read_state`; specialni kategorie `all` funguje pro pohled pres vsechny kategorie.
- Cockpit ma v detailu clanku tlacitka `K přečtení`, `Hotovo` a `Zrušit příznak`.
- Cockpit ma samostatnou zalozku `K přečtení`, ktera ukazuje oznacene clanky napric kategoriemi.
- Import/cleanup clanku byl doplnen o preferenci znacky `Hlavní obsah`, aby se pri URL importu mene chytal patickovy duplicitni titulek.
- Konkretni soukromy clanek o kratkozrakosti u deti byl lokalne oznacen jako `to_read` s kratkou poznamkou.

Co neni hotove:
- Neni proveden rucni klikaci retest v prohlizeci po commitu/pushi.
- Neni doplnen sirsi UX pro ruzne fronty typu `dulezite`, `na shrnuti` apod.; zamerne zustalo jen jednoduche `K precteni` / `Hotovo`.

Dalsi krok:
V Cockpitu otevrit `Knihovna -> K přečtení`, overit, ze je videt clanek o kratkozrakosti u deti, zkusit ho otevrit a pripadne prepnout na `Hotovo` nebo zrusit priznak.

Navrhovane dalsi kroky:
Okamzity: rucni UI retest zalozky `K přečtení`.
Volitelne: az po realnem pouziti rozhodnout, zda staci tri stavy, nebo ma vzniknout obecnejsi fronta znalostnich ukolu.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`

Bezpecnost / neukladat:
- Soukromy article archive v `data/private/article_archive/` se necommituje.
- Do gitu neukladat cele zdravotni texty, ChatGPT exporty, diagnozy ani osobni zdravotni udaje.
