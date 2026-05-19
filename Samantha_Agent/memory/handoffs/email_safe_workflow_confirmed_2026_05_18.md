# Handoff: Safe e-mail workflow confirmed

Nazev: Bezpecny workflow pro cteni a shrnuti e-mailu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Byl doplnen a otestovan workflow:

1. vypsat hlavicky,
2. vybrat UID,
3. vyzadat potvrzeni cteni tela konkretniho UID,
4. po potvrzeni nacist telo read-only,
5. redigovat e-mailove adresy,
6. vratit jen kratke shrnuti,
7. nic neukladat do memory bez dalsiho vyslovneho souhlasu.

## Co je hotove

Upraveno:

- `app/email/tools.py`
- `app/samantha_agent.py`

Tool `read_email_body_by_uid` uz nestaci spustit jen s booleanem
`user_confirmed=True`. Vyžaduje take `confirmation_text`, kam ma Samantha vlozit
aktualni Milovu zpravu se souhlasem. Tool overi, ze potvrzovaci text obsahuje
konkretni UID i potvrzovaci vyraz.

Samantha instrukce popisuji bezpecny e-mailovy workflow a zakazuji automaticke
ukladani obsahu e-mailu do memory.

## Overeni

Probehl lokalni test potvrzovaci podminky:

```text
bez UID -> False
bez souhlasu -> False
UID + souhlas -> True
```

Probehl end-to-end test bez potvrzeni:

- Samantha telo e-mailu necetla,
- vyzadala si explicitni potvrzeni pro dane UID.

Probehl end-to-end test s potvrzenim:

- Samantha nacetla telo read-only,
- vratila jen kratke shrnuti,
- e-mailove adresy byly redigovane,
- nic se neulozilo do memory.

## Co neni hotove

Zatim neni hotove:

- vyhledavani e-mailu podle dotazu,
- specializovany tool pro ulozeni redigovaneho shrnuti do memory po souhlasu,
- redakce dalsich citlivych udaju nez e-mailovych adres.

## Dalsi krok

Pridat vyhledavani e-mailu podle dotazu nad hlavickami nebo IMAP search, stale
read-only. Ukladani do memory resit az pote a pouze jako samostatny krok s
vyslovnym souhlasem Mily.

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- UID konkretni realne zpravy,
- app-specific password,
- iCloud adresu v plnem zneni,
- obsah e-mailu,
- konkretni hlavicky z realne schranky,
- cele e-maily,
- tokeny,
- hesla,
- citlive osobni udaje.
