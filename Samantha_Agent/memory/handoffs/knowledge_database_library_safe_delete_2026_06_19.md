Nazev: Knihovna / bezpecne vyradení nerelevantnich receptu a clanku
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-19

Co se resilo:
Mila chtel po importu starsich receptu moznost rucne odstranit nerelevantni nebo spatne polozky z Cockpit knihovny. Kvuli bezpecnostnim pravidlum nejde o tvrde mazani, ale o vyradeni z knihovny s presunem do soukromeho kose.

Co je hotove:
- V `app/article_archive.py` je pridana funkce `delete_article(...)` s potvrzovaci frazi `Potvrzuji vyřazení z knihovny`.
- Funkce nejdriv presune slozku polozky do `data/private/article_archive/trash/articles/`, potom odstrani radek z registru a zapise manifest `removed_from_registry.json`.
- V `app/cockpit.py` je novy endpoint `/api/library/delete`.
- V modalnim okne `Knihovna` je tlacitko `Vyřadit z knihovny`, aktivni jen po vyberu polozky.
- Pred vyraděnim se v prohlizeci zobrazi potvrzovaci dialog.
- Po uspesnem vyradeni se seznam znovu nacte a vybrana karta se vycisti.
- Doplnene testy overuji potvrzeni, presun do kose, zmizeni z registru a napojeni Cockpitu.

Co neni hotove:
- Neni implementovane UI tlacitko pro obnovu z kose.
- Neni udelany rucni browser test na realne polozce v Cockpitu.
- Soukromy kos je zatim urceny pro rucni dohledani/obnovu podle manifestu.

Dalsi krok:
Otevrit Cockpit, vybrat jednu zjevne nerelevantni testovaci/starsi polozku v Knihovne a rucne overit, ze tlacitko `Vyřadit z knihovny` po potvrzeni polozku schova ze seznamu.

Navrhovane dalsi kroky:
Okamzity: rucni UI retest na jedne bezpecne polozce, kde Míla opravdu chce vyradeni.
Volitelne: pozdeji pridat filtr nebo samostatny pohled `Koš knihovny` a akci `Obnovit`, pokud se ukaze, ze bude potreba castejsi vraceni omylem vyrazenych polozek.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `data/private/article_archive/` zustava soukrome mimo git.

Overeni:
- `.venv/bin/python -m py_compile app/article_archive.py app/cockpit.py`
- `.venv/bin/python -m unittest tests.test_article_archive tests.test_cockpit`
- Testy prosly: 161 testu OK.
- Pri kompilaci zustava starsi `SyntaxWarning` k HTML stringu v `app/cockpit.py`; tato uprava ho nezavedla.

Bezpecnost / neukladat:
- Do gitu nepatri zadna data z `data/private/article_archive/`, zadne recepty z private archivu ani obsah ChatGPT exportu.
- Funkce nema tvrde mazat soubory. Vyradene polozky se presouvaji do soukromeho kose.
- Skutecne vyradeni realne polozky v UI je uzivatelska akce s potvrzenim; bez Mílova vyberu nepoustet hromadne.
