Nazev: EmailArchiveVault - read-only provider a Samantha tool hotove
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navazalo se na hotovy cisty `EmailArchiveVault` core.
- Implementovala se read-only archivace jednoho e-mailu podle UID.
- Archivace je samostatny workflow oddeleny od triage a od `EmailCaseVault`.

Co je hotove:
- Do `ICloudReadOnlyEmailProvider` pridana metoda `read_archive_source_by_uid(uid, max_chars=50000)`.
- Provider metoda pouziva `select("INBOX", readonly=True)` a `BODY.PEEK[]`.
- Provider vraci `EmailArchiveSource` s:
  - metadaty,
  - text body,
  - HTML body, pokud existuje,
  - plnymi URL,
  - metadaty priloh,
  - raw `original.eml` bytes.
- Pridan `app/email/archive_tools.py`.
- Pridan Samantha tool `archive_email_by_uid`.
- Doplneny exporty v `app/email/__init__.py`.
- Doplnena registrace toolu v `app/samantha_agent.py`.
- Doplneny instrukce v `app/samantha_agent.py`.
- Po uspesne nove archivaci tool vola `record_email_archive_completed()`.
- Tool vraci jen bezpecny technicky souhrn:
  - `archive_id`,
  - stav,
  - seznam ulozenych souboru,
  - upozorneni, ze jde o lokalni citlivy archiv.
- Pridany testy:
  - `tests/test_email_archive_tools.py`,
  - `tests/test_email_icloud_archive_provider.py`.

Co neni hotove:
- Neni proveden realny end-to-end test archivace konkretniho UID pres Samanthu.
- Neni implementovano samostatne potvrzovane stahovani souboru priloh.
- Neni implementovano cteni archivu zpet do chatu.

Dalsi krok:
- Rucne otestovat `archive_email_by_uid` pres Samanthu s jednim konkretnim UID a explicitnim potvrzenim kompletni archivace do `EmailArchiveVault`.
- Po testu zkontrolovat, ze vznikl archiv v `data/email/archive/`, ze vystup neobsahuje telo, plne URL ani neredigovane e-maily a ze `last_archive_at` bylo aktualizovano.
- Potom navrhnout samostatny read/archive WorkMode pro praci s ulozenym archivem.

Zmenene nebo relevantni soubory:
- `app/email/icloud_provider.py`
- `app/email/archive_tools.py`
- `app/email/archive_models.py`
- `app/email/archive_service.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_archive_tools.py`
- `tests/test_email_icloud_archive_provider.py`
- `tests/test_email_archive_service.py`
- `app/email/activity_state.py`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 113 testu OK.

Bezpecnost / neukladat:
- Archiv je lokalni citlivy archiv, ne memory.
- Tool nesmi bez potvrzeni volat provider ani zapisovat archiv.
- Potvrzeni musi obsahovat konkretni UID a jasny souhlas s kompletni archivaci do `EmailArchiveVault`.
- Tool nesmi vypisovat cele telo e-mailu.
- Tool nesmi vypisovat plne URL.
- Tool nesmi vypisovat neredigovane e-mailove adresy.
- Tool nesmi nic ukladat do memory ani reminders.
- Tool nesmi otevirat odkazy.
- Tool nesmi spoustet nebo samostatne ukladat prilohy.
- Tool nesmi nic odesilat, mazat, presouvat ani oznacovat jako prectene.
- `data/email/archive/` zustava citlive lokalni uloziste a nesmi se commitovat.
