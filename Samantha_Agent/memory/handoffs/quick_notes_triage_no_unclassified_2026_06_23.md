Nazev: Quick Notes triage bez Nezarazeno pro QN 42
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
- Mila nahlasil, ze posledni QN #42 se v Cockpitu zobrazuje jako `Nezařazeno`.
- Ukazalo se, ze to nebylo selhani celeho Quick Notes systemu, ale rozdil mezi
  novou akční predklasifikaci a starsi Cockpit funkci `quick_note_triage_hint`.

Co je hotove:
- `app/cockpit.py` ponechava starsi domenove Cockpit stitky tam, kde neco trefi.
- Pokud starsi domenova pravidla nic netrefi, Cockpit uz nevraci `Nezařazeno`,
  ale pouzije novou `classify_quick_note_text` predklasifikaci z `app.quick_notes`.
- QN typu knihovna / URL clanek / ulozit clanek se zobrazi jako
  `archiv/znalostní databáze`.
- Doplnene testy v `tests/test_cockpit.py` hlidaji obecny fallback na `nápad`
  a konkretni fallback pro knihovnu/URL clanek.
- Lokalni i Tailscale Cockpit byly restartovane, aby nacetly novy kod.

Co neni hotove:
- Nic pro tento blok.

Dalsi krok:
- Pri dalsi nove QN sledovat, zda stav v Cockpitu ukazuje smysluplny stitek
  misto `Nezařazeno`; pokud bude potreba, rozsirit pravidla uz v jedne spolecne
  vrstve klasifikace.

Navrhovane dalsi kroky:
- Pozdeji sjednotit UI popisky Quick Notes tak, aby Cockpit vsude ukazoval stejne
  `classification`, `confidence`, `risk` a dalsi krok jako akcni inbox.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`

Bezpecnost / neukladat:
- Necommitovat obsah `data/private/quick_notes/`.
- Do pameti ani gitu neopisovat cele texty Quick Notes; staci bezpecny souhrn a
  technicky popis klasifikace.
