# Handoff: iCloud Mail read-only test OK

Nazev: iCloud Mail read-only pristup pro Samanthu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Mila navazoval na praci kolem zpristupneni jeho e-mailu pro Samantha/Codex.
Cilem je bezpecny read-only pristup k iCloud Mailu, ne prace pres Apple Mail GUI.

Relevantni kontext je v:

- `memory/projects/email_readonly_oauth.md`
- `memory/handoffs/email_icloud_setup_conversation_2026_05_18.txt`
- `memory/handoffs/email_mail_permissions_2026_05_17.txt`

## Co je hotove

Read-only iCloud Mail test byl uspesne overen mimo Codex sandbox v normalnim SSH
terminalu.

Pouzity prikaz:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/icloud_list_recent.py --limit 10
```

Vysledek:

- test probehl OK,
- iCloud IMAP read-only pristup funguje,
- lokalni `.env` je nastaveny funkcne,
- app-specific password funguje,
- skript umi vypsat hlavicky poslednich e-mailu.

## Co neni hotove

Zatim existuje jen testovaci skript:

- `scripts/icloud_list_recent.py`

Zatim neni hotove:

- normalizovane rozhrani v `app/email/`,
- nastroj pro Samanthu,
- vyhledavani e-mailu podle dotazu,
- bezpecny workflow pro rucne schvalene shrnuti e-mailu do memory.

## Dalsi krok

Navrhnout a potom implementovat malou bezpecnou vrstvu:

```text
app/email/
  __init__.py
  models.py
  icloud_provider.py
```

Prvni verze ma zustat read-only:

- vypsat hlavicky poslednich zprav,
- nacist pouze metadata,
- neodesilat,
- nemazat,
- nepresouvat,
- neoznacovat jako prectene,
- neukladat obsah e-mailu do memory.

## Relevantni soubory

- `Samantha_Agent/scripts/icloud_list_recent.py`
- `Samantha_Agent/.env` lokalne, necommitovat
- `Samantha_Agent/.env.example`
- `Samantha_Agent/memory/projects/email_readonly_oauth.md`
- `Samantha_Agent/memory/handoffs/email_icloud_setup_conversation_2026_05_18.txt`

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- app-specific password,
- iCloud adresu v plnem zneni,
- obsah e-mailu,
- cele e-maily,
- tokeny,
- hesla,
- citlive osobni udaje.

Autosave session logy mohou obsahovat citlive udaje, proto se necommituji.
