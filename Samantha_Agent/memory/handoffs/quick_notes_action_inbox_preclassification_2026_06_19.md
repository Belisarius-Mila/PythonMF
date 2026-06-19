Nazev: Quick Notes akcni inbox s automatickou predklasifikaci
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-19

Co se resilo:
Mila chtel navazujici malou implementaci k Quick Notes akcnímu inboxu podle systemoveho auditu. Dulezita korekce byla, ze se pocita s automatickou predklasifikaci z textu, ale bez automatickeho provadeni akci.

Co je hotove:
- `app/quick_notes.py` ma datovou tridu `QuickNoteClassification`.
- Pridana je pravidlova predklasifikace textu Quick Note do typu: pripominka, projekt, tool/workflow, ukol, citliva akce, archiv/znalostni databaze nebo napad.
- Klasifikace vraci jistotu, riziko, bezpecne kratke shrnuti, navrzeny dalsi krok a par matchnutych terminu.
- `quick_notes_action_status_text(...)` sklada prehled Quick Notes akcniho inboxu s predklasifikaci a linkem na detail `show_quick_note_detail(...)`.
- `scripts/samantha_quick_notes.py --status` umi vypsat akcni inbox z terminalu.
- Samantha agent ma novy tool `quick_notes_action_status(limit=30)`.
- Testy overuji klasifikaci kandidatu a status vystup nad docasnou testovaci slozkou.

Co neni hotove:
- Zatim neni Cockpit UI pro akci `hotovo`, `odlozit`, `prevest na pripominku` nebo `zalozit projekt`.
- Zatim neni perzistentni rozhodnuti nad konkretni QN, jen read-only predklasifikovany prehled.
- Pravidla jsou zamerne jednoducha a konzervativni; nektere QN mohou byt falesne zarazene jako pripominka nebo citliva akce.

Dalsi krok:
Rucne pouzit `quick_notes_action_status` nebo `scripts/samantha_quick_notes.py --status`, projit prvnich par QN a rozhodnout, jestli dalsi mala implementace ma byt `mark done`, Cockpit filtr podle rizika, nebo prevod konkretni QN na pripominku/projekt.

Navrhovane dalsi kroky:
Okamzity: nechat read-only prehled pouzivat jako vstupni triage.
Volitelne: pridat potvrzovane akce nad jednou QN, hlavne `označit vyřešeno` a `vytvořit návrh připomínky`, ale bez automatickeho mazani, posilani nebo zapisu citlivych dat.

Zmenene nebo relevantni soubory:
- `app/quick_notes.py`
- `app/samantha_agent.py`
- `scripts/samantha_quick_notes.py`
- `tests/test_quick_notes.py`

Overeni:
- `.venv/bin/python -m py_compile app/quick_notes.py app/samantha_agent.py scripts/samantha_quick_notes.py`
- `.venv/bin/python -m unittest tests.test_quick_notes`
- `.venv/bin/python scripts/samantha_quick_notes.py --status --limit 5`

Bezpecnost / neukladat:
- Do handoffu neukladat texty realnych Quick Notes.
- Predklasifikace je pouze read-only orientace. Nic neposila, nemaze, neplati, necommitne a nepracuje s dokumenty bez dalsiho potvrzeni.
- QN s e-mailem, PDF, mazanim, platbou, commitem, pushem, tajemstvimi nebo dokumenty ma koncit jako vysoke riziko a vyzadovat dalsi potvrzeni pred akci.
