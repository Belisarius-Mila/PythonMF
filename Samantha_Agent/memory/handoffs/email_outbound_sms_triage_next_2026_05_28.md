Nazev: Email management, outbound, SMS/RCS a triage reporty
Priorita: 1
Stav: hotovo / ceka na realny retest
Pripomenout pri startu: ano
Datum: 2026-05-28

Co se resilo:
- Read-only email triage iCloud + Seznam vcetne spamu.
- Dohledatelne preposilani e-mailu do Milova souhrnneho iCloud uctu.
- Diagnostika SMS/RCS odesilani z Macu pres Messages.
- Bezpecny SMS/RCS sender tool se samostatnym potvrzenim.
- Ukladani plneho triage reportu do lokalni ignorovane slozky.
- Dohledani e-mailu k pojistnym PDF a pravidel k heslum bez ukladani skutecnych
  osobnich hodnot.

Co je hotove:
- E-mailovy outbound workflow zustava dvoukrokovy:
  1. `prepare_forward_email_by_uid` vytvori lokalni draft po vyslovnem potvrzeni.
  2. `send_prepared_email_draft` odesle existujici draft az po dalsim samostatnem
     potvrzeni s `draft_id` a prijemcem.
- `send_prepared_email_draft` po SMTP odeslani uklada best-effort kopii do IMAP
  Odeslanych, vychozi provider je iCloud `Sent Messages`, aby Mila videl
  dohledatelnou kopii v iCloud klientovi.
- Metadata draftu rozlisuji SMTP odeslani a stav ulozene kopie v Odeslanych.
- SMS/RCS diagnostika:
  - problem byl na iPhonu v `Zpravy -> Odesilani a prijem`: bylo zaskrtnute jen
    e-mailove Apple ID, ne telefonni cislo;
  - po zaskrtnuti telefonniho cisla rucni zprava z Macu odesla;
  - navazujici test pres Samanthu na Android kontakt prosel jako RCS s
    `is_sent=1`, `is_delivered=1`, `error=0`.
- Implementovan novy tool `send_confirmed_sms_rcs`:
  - vstup: kontakt nebo telefonni cislo, text, samostatne potvrzeni;
  - odeslani pres macOS Messages bez shell interpolace;
  - po odeslani povinne cte lokalni `~/Library/Messages/chat.db`;
  - vraci stav podle `is_sent`, `is_delivered`, `error`;
  - nehlasi uspech jen podle exit code AppleScriptu.
- Rodinne kontakty jsou v soukromem ignorovanem souboru
  `data/private/contacts/family_contacts.json`; telefonni cisla nejsou v gitu.
- Plny triage report se uklada do ignorovane lokalni slozky
  `data/email/triage_reports/`; chatovy vystup vraci jen souhrn a cestu k reportu.
- Triage reporty stale rediguji e-mailove adresy a URL a neukladaji se do gitu.
- Pojistne PDF 2024 od Kooperativy:
  - zdrojovy e-mail byl dohledan podle Seznam UID `134162`;
  - navazujici nabidka byla UID `134158`;
  - pravidlo z tela e-mailu: heslo je osobni identifikator pojistnika bez
    oddelovace; skutecna hodnota nesmi byt ulozena do memory.
- Pojistne PDF 2025 od CPP:
  - zdrojovy e-mail byl dohledan podle Seznam UID `143498`;
  - pravidlo z tela e-mailu: heslo je datum narozeni pojistnika ve formatu
    `RRRRMMDD`; skutecna hodnota nesmi byt ulozena do memory.

Co neni hotove:
- Neni jeste udelany realny produkcni test noveho `send_confirmed_sms_rcs` toolu
  s aktualnim potvrzovacim workflow.
- Neni jeste jednotny outbound "receipt" model spolecny pro e-mail i SMS/RCS.
- HTML/CSS cisteni tel nekterych e-mailu je porad misty sumive.
- Action item extrakce muze obcas zachytit paticku, odhlaseni nebo reklamni vyzvu.
- Pojistne PDF 2024/2025 zustavaji sifrovana; odemceni ma probihat jen lokalne
  u Mily bez ukladani skutecnych osobnich hesel.

Dalsi krok:
- Pri prvni realne potrebe poslat SMS/RCS pouzit `send_confirmed_sms_rcs` a
  porovnat vraceny stav s Messages/iPhonem.
- Pri dalsi email triage zkontrolovat souhrn v chatu a podle potreby otevrit
  lokalni plny report v `data/email/triage_reports/`.
- U pojistnych PDF pouzit pravidla z e-mailu pouze lokalne, bez zapisovani
  citlivych hodnot.

Navrhovane dalsi kroky:
- Okamzite:
  - realny retest SMS/RCS toolu na kratke schvalene zprave;
  - pokud uspeje, ulozit jen technicky stav retestu bez plneho textu zpravy.
- Potom:
  - pridat jednotny outbound receipt model pro e-mail a SMS/RCS, aby bylo jasne:
    co bylo odeslano, pres jaky kanal, jestli existuje dohledatelna kopie a jaky
    je stav doruceni.
- Potom:
  - doladit HTML text extraction a action-item extraction u marketingovych,
    bankovnich a pojistnych e-mailu.
- Volitelne pozdeji:
  - propojit dulezite triage vystupy s document vaultem a reminders, ale pouze
    pres samostatna potvrzeni podle konkretniho UID/prilohy.

Zmenene nebo relevantni soubory:
- `app/messages/outbound.py`
- `app/messages/tools.py`
- `app/email/triage_tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `app/capability_audit.py`
- `tests/test_messages_outbound_tools.py`
- `tests/test_email_triage_tools.py`
- `.gitignore`
- `data/private/contacts/family_contacts.json` lokalne, ignorovane gitem
- `data/email/triage_reports/` lokalne, ignorovane gitem

Bezpecnost / neukladat:
- Neukladat do memory ani gitu hesla, tokeny, app-specific passwords, plne
  e-mailove adresy, telefonni cisla, cela tela e-mailu, plne URL, prilohy ani
  privatni obsah.
- Neukladat skutecna rodna cisla, data narozeni ani jina hesla k PDF.
- `data/email/outbox_drafts/`, `data/email/archive/`, `data/email/triage_reports/`,
  `data/private/` a `.env` zustavaji lokalni a necommituji se.
- U e-mailu se cteni, forward, archivace, odkazy, prilohy a reminders drzi jako
  samostatne potvrzovane kroky.
- U SMS/RCS se nesmi hlasit doruceno bez overeni v Messages DB nebo jine
  spolehlive stavove vrstve.
