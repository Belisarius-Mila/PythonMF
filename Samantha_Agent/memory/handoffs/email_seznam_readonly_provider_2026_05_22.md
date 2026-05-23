Nazev: Seznam Mail read-only provider pro Samanthu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-22

Co se resilo:
- Mila pridal stary Seznam ucet do macOS Internet Accounts / Apple Mail a chce,
  aby Samantha umela zpracovavat i e-maily ze Seznamu, idealne podobne jako
  iCloud read-only workflow.
- Cilem je bezpecne rozlisit zdroj schranky: iCloud UID a Seznam UID nejsou
  zamenné.

Co je hotove:
- Pribyla konfigurace `SEZNAM_MAIL_ADDRESS` a `SEZNAM_MAIL_PASSWORD` pres lokalni
  `.env`; heslo ani adresa se neukladaji do memory.
- Pribyl `SeznamReadOnlyEmailProvider` pro read-only INBOX hlavicky a potvrzene
  cteni jednoho tela podle UID.
- Pribyly Samantha tooly:
  - `list_recent_seznam_email_headers`
  - `search_seznam_email_headers`
  - `read_seznam_email_body_by_uid`
- `app/samantha_agent.py` ma Seznam tooly v seznamu nastroju a instrukci, ze pri
  Seznamu / stare druhe adrese / Seznam e-mailu ve `Vsechny prichozi` se ma
  pouzit Seznam provider.
- Pribyl `list_unified_email_headers`: bezpecny sjednoceny read-only prehled
  hlavicek z iCloudu a Seznamu se sloupcem/uvodem `Zdroj`.
- Unified Inbox degraduje bezpecne: kdyz Seznam neni nakonfigurovany, vypise
  dostupne iCloud hlavicky a Seznam oznaci jako nedostupny zdroj.
- Pribyl test parseru a konfigurace v `tests/test_seznam_provider.py`.
- Pribyl test sjednoceneho vypisu v `tests/test_email_unified_tools.py`.

Co neni hotove:
- Realny Seznam smoke test neprosel, protoze v lokalnim `.env` zatim nejsou
  vyplnene `SEZNAM_MAIL_ADDRESS` a `SEZNAM_MAIL_PASSWORD`.
- Realny Seznam smoke test porad ceka na lokalni `.env` konfiguraci.
- Stary Seznam pojistny worklist/prilohy z drivejsiho skriptu nejsou jeste
  preklopene do nove Samantha vrstvy.

Dalsi krok:
- Lokalne doplnit Seznam prihlasovaci udaje do `.env` a udelat maly read-only
  smoke test hlavicek bez cteni tel.

Navrhovane dalsi kroky:
- Pridat potvrzovaci vetu, ktera vzdy obsahuje zdroj schranky, napr.
  `Potvrzuji, precti telo Seznam e-mailu UID 12345`.
- Pozdeji sjednotit stare Seznam pojistne skripty s novou read-only vrstvou,
  ale stale bez automatickeho cteni tel, plnych URL nebo stahovani priloh bez
  samostatneho potvrzeni.

Zmenene nebo relevantni soubory:
- `app/email/config.py`
- `app/email/seznam_provider.py`
- `app/email/tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_seznam_provider.py`
- `tests/test_email_unified_tools.py`
- `.env.example`
- `memory/handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_seznam_provider`
- `.venv/bin/python -m unittest tests.test_email_unified_tools tests.test_seznam_provider`
- `.venv/bin/python -m unittest tests.test_email_icloud_archive_provider tests.test_email_text_search_tools`
- `.venv/bin/python -m py_compile app/email/seznam_provider.py app/email/tools.py app/samantha_agent.py app/email/config.py app/email/__init__.py`
- `.venv/bin/python -c "from app.samantha_agent import build_agent; print('SAMANTHA_IMPORT=ok')"`
- Runtime zkouska `list_unified_email_headers_text(limit_per_source=2)` vratila
  iCloud hlavicky a u Seznamu korektne uvedla chybejici lokalni konfiguraci.

Bezpecnost / neukladat:
- Neukladat Seznam adresu, heslo, app password, cele e-maily, plne URL, prilohy
  ani privatni obsah e-mailu do memory nebo gitu.
- `data/private/email_seznam/` zustava soukrome a mimo git.
