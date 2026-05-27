Nazev: Email unified triage, scoring a report do souboru
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-28

Co se resilo:
- Sjednoceni e-mailove triage pres iCloud, Seznam a nevyzadanou postu.
- Bezpecny automaticky read-only rezim: cist hlavicky a omezene telo pro klasifikaci,
  ale neotevirat odkazy, nestahovat prilohy, nic neodesilat, nemazat, nepresouvat
  a neoznacovat jako prectene.
- Doladeni scoringu tak, aby pojistky, faktury, platby, doruceni a bezpecnost
  uctu byly vyse; marketing, politicke pozvanky, knihkupectvi, newslettery a spam
  nize.
- Upraveni vystupu tak, aby u e-mailu bylo videt UID, zdroj, slozka a datum
  doruceni.

Co je hotove:
- `run_unified_email_triage_session` je preferovany nastroj pro Miluv pokyn typu
  "triage e-mailu za poslednich X dni".
- iCloud a Seznam providery umi nacitat vice slozek a vracet i preskocene velke
  nebo necitelne zpravy.
- Seznam spam se hleda pres IMAP slozku `spam` a dalsi fallback kandidaty.
- Report ma sekce High, Normal, deadline signaly, Low inbox/newslettery, Low spam
  a Preskocene.
- Low priorita je zkracena limitem, aby chat nebyl zahlceny newslettery a spamem.
- Testy pro triage/unified e-mail workflow prosly: 24 testu OK.
- UID 154590 bylo zpracovano read-only jako samostatny action case; bez nalezeneho
  due date a bez ukladani.
- Pojistka Volvo V40 je hlidana v lokalnich reminders; existuje otevrena high
  pripominka se splatnosti 2026-07-31.

Co neni hotove:
- Plny triage report se zatim neuklada automaticky do souboru; v chatu je jen
  zkraceny nebo citelnejsi vystup.
- HTML/CSS sumarizace nekterych e-mailu je porad obcas moc sumiva a chce lepsi
  cisteni tela.
- Extrakce dalsiho kroku u nekterych e-mailu jeste muze zachytavat boilerplate.

Dalsi krok:
- Doplnit u triage volitelne ulozeni plneho reportu do lokalniho git-ignorovaneho
  souboru, napr. `data/email/triage_reports/YYYY-MM-DD_*.md`, a do chatu vracet
  kratky souhrn s cestou k reportu.

Navrhovane dalsi kroky:
- Okamzite: implementovat report do souboru a otestovat ho na malem okne, napr.
  2 dny / 10 zprav.
- Potom: zlepsit HTML text extraction pro marketingove a bankovni e-maily.
- Potom: doladit action-item extrakci, aby se do ni nedostavaly paticky,
  odhlasovaci texty a genericke reklamni vyzvy.

Zmenene nebo relevantni soubory:
- `app/email/models.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `app/email/tools.py`
- `app/email/triage_models.py`
- `app/email/triage_service.py`
- `app/email/triage_tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_triage_tools.py`
- `tests/test_email_unified_tools.py`
- `memory/projects/email_readonly_oauth.md`

Bezpecnost / neukladat:
- Neukladat do memory ani gitu hesla, tokeny, app-specific passwords, plne e-mailove
  adresy, cela tela e-mailu, plne URL, prilohy ani privatni obsah.
- Triage report se ma ukladat jen lokalne do ignorovane slozky, ne do gitu.
- `data/session_autosave/` a privatni e-mailova data se necommituji.
