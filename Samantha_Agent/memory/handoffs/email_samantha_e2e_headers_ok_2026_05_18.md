# Handoff: Samantha e-mail headers end-to-end test OK

Nazev: Samantha read-only e-mail headers end-to-end test OK
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Probehl end-to-end test hlavniho Samantha agenta s read-only iCloud Mail tool call.

## Co je hotove

Spravny prikaz pro spusteni je pres modul z korene projektu:

```bash
.venv/bin/python -m app.samantha_agent "Vypis posledni 3 e-mailove hlavicky."
```

Tento tvar je dulezity, protoze prime spusteni `app/samantha_agent.py` muze zpusobit,
ze lokalni balicek `app/email` zastini standardni Python modul `email`.

Test mimo Codex sandbox probehl OK:

- Samantha se spustila pres Agents SDK,
- pouzila tool `list_recent_email_headers`,
- vratila pouze 3 hlavicky,
- necetla tela e-mailu,
- nic neukladala do memory,
- nic nemazala, neposilala, nepresouvala ani neoznacovala jako prectene.

## Co neni hotove

Zatim neni hotove:

- vyhledavani e-mailu podle dotazu,
- nacteni konkretniho e-mailu po rucnim potvrzeni,
- shrnuti konkretniho e-mailu v chatu,
- rucne schvalene ulozeni vybraneho shrnuti do memory.

## Dalsi krok

Navrhnout druhy read-only krok: nacist jeden konkretni e-mail podle UID az po
vyslovnem potvrzeni Mily. Pred implementaci stanovit, zda se ma cist jen textove
telo, jak redigovat citlive udaje a jak potvrzovat pripadne ulozeni shrnuti do
memory.

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- app-specific password,
- iCloud adresu v plnem zneni,
- obsah e-mailu,
- konkretni hlavicky z realne schranky,
- cele e-maily,
- tokeny,
- hesla,
- citlive osobni udaje.
