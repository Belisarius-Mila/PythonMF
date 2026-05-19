# Handoff: iCloud Mail read-only workflow

Nazev: iCloud Mail read-only workflow pro Samanthu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Pokracovalo se v bezpecnem read-only napojeni iCloud Mailu na Samanthu.
Cilem bylo dostat se od testovaciho vypisu hlavicek k praktickemu workflow:

1. vypsat hlavicky,
2. vybrat UID,
3. vyzadat potvrzeni cteni tela,
4. nacist telo read-only,
5. redigovat citlive udaje,
6. vratit kratke shrnuti,
7. nic neukladat do memory bez vyslovneho souhlasu.

## Co je hotove

Hotove a overene:

- read-only iCloud IMAP pristup pres lokalni `.env`,
- `app/email/` vrstva pro hlavicky,
- `scripts/email_list_recent.py`,
- `scripts/email_read_uid.py`,
- Samantha tool `list_recent_email_headers`,
- Samantha tool `read_email_body_by_uid`,
- redakce e-mailovych adres pres `app/email/redaction.py`,
- ochrana pred ctenim tela bez potvrzeni,
- end-to-end test bez potvrzeni, kde Samantha telo necetla,
- end-to-end test s potvrzenim, kde Samantha nacetla telo read-only a vratila jen kratke redigovane shrnuti.

Tool `read_email_body_by_uid` uz nestaci spustit jen s `user_confirmed=True`.
Vyžaduje take `confirmation_text`, kam Samantha musi vlozit aktualni Milovu zpravu
se souhlasem. Tool overuje, ze potvrzovaci text obsahuje konkretni UID i jasny
souhlas.

## Co neni hotove

Zatim neni hotove:

- read-only vyhledavani e-mailu podle dotazu,
- specializovane hledani podle odesilatele, predmetu nebo klicoveho slova,
- normalizovane shrnuti e-mailu jako samostatny workflow,
- ulozeni redigovaneho shrnuti do memory po vyslovnem souhlasu,
- redakce dalsich citlivych udaju nez e-mailovych adres.

## Dalsi krok

Pridat read-only vyhledavani e-mailu podle dotazu. Prakticky zacatek:

- `search_email_headers(query: str, limit: int = 10)` jako dalsi tool,
- hledat nejdrive jen v hlavickach nebo bezpecnym IMAP search,
- vracet pouze UID, datum, odesilatele a predmet,
- necist telo zpravy automaticky,
- pro cteni tela stale pouzivat potvrzovaci workflow podle UID.

## Zmenene nebo relevantni soubory

- `app/samantha_agent.py`
- `app/email/__init__.py`
- `app/email/config.py`
- `app/email/icloud_provider.py`
- `app/email/models.py`
- `app/email/redaction.py`
- `app/email/tools.py`
- `scripts/email_list_recent.py`
- `scripts/email_read_uid.py`
- `memory/projects/email_readonly_oauth.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/email_safe_workflow_confirmed_2026_05_18.md`

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
