# Handoff: Samantha read body by UID tool OK

Nazev: Samantha tool pro read-only cteni tela e-mailu podle UID
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Byl pridan Samantha tool pro read-only nacteni tela jednoho konkretniho iCloud
e-mailu podle UID. Tool je urceny az pro situaci, kdy Mila vyslovne potvrdi cteni
tela konkretni zpravy.

## Co je hotove

Pribylo:

- `app/email/redaction.py`
- `read_email_body_by_uid` v `app/email/tools.py`

Upraveno:

- `app/email/__init__.py`
- `app/samantha_agent.py`
- `scripts/email_read_uid.py`

Vlastnosti:

- cteni tela pouziva existujici read-only provider,
- tool vyzaduje parametr `user_confirmed=True`,
- pokud potvrzeni chybi, vrati zadost o potvrzeni a telo necte,
- telo je omezene pres `max_chars`,
- e-mailove adresy v tele a odesilateli jsou redigovane,
- vystup se nema ukladat do memory.

## Overeni

Probehl py_compile pro upravene soubory.

Registrace nastroju v Samantha agentovi potvrdila:

```text
['search_memory', 'list_recent_email_headers', 'read_email_body_by_uid']
```

End-to-end test mimo Codex sandbox pres:

```bash
.venv/bin/python -m app.samantha_agent "Potvrzuji, ze chci precist telo e-mailu s UID ... Vypis maximalne 500 znaku a rediguj e-mailove adresy."
```

probehl OK. Samantha nacetla telo konkretniho e-mailu, redigovala e-mailovou adresu
a neukladala obsah do memory.

## Co neni hotove

Zatim neni hotove:

- vyhledavani e-mailu podle dotazu,
- normalizovane shrnuti e-mailu,
- workflow pro rucne schvalene ulozeni vybraneho shrnuti do memory,
- jemnejsi redakce dalsich citlivych udaju nez jen e-mailovych adres.

## Dalsi krok

Navrhnout workflow:

1. vypsat hlavicky,
2. Mila vybere UID,
3. Samantha si vyzada potvrzeni cteni tela,
4. Samantha nacte telo redigovane,
5. pripadne vytvori kratke shrnuti,
6. do memory ulozi jen Milou vyslovne schvalene shrnuti.

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
