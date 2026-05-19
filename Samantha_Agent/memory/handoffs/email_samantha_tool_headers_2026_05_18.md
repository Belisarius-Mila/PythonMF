# Handoff: Samantha e-mail headers tool

Nazev: Samantha read-only nastroj pro iCloud Mail hlavicky
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Po uspesnem realnem testu `scripts/email_list_recent.py --limit 10` se pokracovalo
v napojeni read-only iCloud Mail vrstvy do hlavniho Samantha agenta.

## Co je hotove

Pribyl soubor:

- `app/email/tools.py`

Obsahuje Agents SDK tool:

- `list_recent_email_headers(limit: int = 10)`

Nastroj vraci pouze:

- UID,
- datum,
- odesilatele,
- predmet.

Byl zapojen do:

- `app/email/__init__.py`
- `app/samantha_agent.py`

Samantha ma v instrukcich vyslovne omezeni, ze e-mailovy nastroj smi pouzit jen
na Miluv vyslovny dotaz na posledni e-maily nebo e-mailove hlavicky.

## Overeni

Probehl prikaz:

```bash
.venv/bin/python -m py_compile app/email/tools.py app/email/__init__.py app/samantha_agent.py
```

Probehl take importni test bez volani site:

```bash
.venv/bin/python -c "from app.samantha_agent import build_agent; agent = build_agent('test'); print([getattr(tool, 'name', type(tool).__name__) for tool in agent.tools])"
```

Vystup potvrdil:

```text
['search_memory', 'list_recent_email_headers']
```

## Co neni hotove

Zatim nebyl proveden end-to-end test pres samotnou Samanthu, protoze by vyzadoval
OpenAI API volani a realny sitovy pristup.

Zatim neni hotove:

- vyhledavani e-mailu podle dotazu,
- cteni konkretniho e-mailu po rucnim potvrzeni,
- shrnuti e-mailu v chatu,
- rucne schvalene ulozeni vybraneho shrnuti do memory.

## Dalsi krok

Spustit rucni end-to-end test pres Samantha agenta, napr.:

```bash
.venv/bin/python app/samantha_agent.py "Vypis posledni 3 e-mailove hlavicky."
```

Ocekavani: Samantha pouzije `list_recent_email_headers` a vypise pouze UID, datum,
odesilatele a predmet. Nesmí cist tela e-mailu ani nic ukladat do memory.

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- app-specific password,
- iCloud adresu v plnem zneni,
- obsah e-mailu,
- cele e-maily,
- tokeny,
- hesla,
- citlive osobni udaje.
