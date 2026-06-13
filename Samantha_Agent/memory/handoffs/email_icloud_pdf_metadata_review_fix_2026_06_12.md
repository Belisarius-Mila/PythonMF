Nazev: E-mailovy PDF intake - iCloud metadata a revize dokumentu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-12

Co se resilo:
- Po zmrazeni voice bridge se navazalo na e-mailovy workflow.
- Mila poslal testovaci iCloud e-mail s PDF prilohou, ale Cockpit ho nejdrive neukazal v nactenych e-mailech za posledni den.
- Po opraveni nacteni se e-mail zpracoval a PDF se ulozilo do private document vaultu, ale neobjevilo se v karte `Ulozene dokumenty k revizi`.

Co je hotove:
- Opravena iCloud/Seznam volba payloadu pro hlavicky: provider uz nebere prvni IMAP literal naslepo, ale prvni payload, ktery obsahuje Date/From/Subject.
- Opraveno parsovani IMAP BODYSTRUCTURE pro rozdelene literaly a RFC2231 `FILENAME*`, aby se PDF metadata z iCloudu nacetla spravne.
- Cockpit po restartu videl testovaci iCloud e-mail jako dokumentovy kandidat s 1 PDF prilohou.
- Opravena budoucnost: PDF prilohy importovane z Email Work Queue se ukladaji do document vaultu s explicitnim `reading_status = needs_review`.
- Po Milove potvrzeni byl uz ulozeny testovaci PDF dokument oznacen jako `k revizi`.
- Overeno pres Cockpit API: `Ulozene dokumenty k revizi` hlasi 1 kandidat a review report take hlasi 1 kandidat.

Co neni hotove:
- Zmeny v kodu zatim nejsou commitnute ani pushnute.
- Nebyla provedena rucni revize ulozeneho dokumentu v Cockpitu/ScanDocu.
- Nebyl udelan finalni git safety check a tematicky commit.

Dalsi krok:
- Zitra zacit kontrolou `git status --short`, spustit relevantni testy a pak rucne zkontrolovat kartu `Ulozene dokumenty k revizi` v Cockpitu.

Navrhovane dalsi kroky:
- Okamzite: potvrdit v UI, ze se ulozeny PDF dokument nabizi k revizi a ze se da otevrit v dokumentove revizi bez cteni obsahu v chatu.
- Potom: po kontrole diffu udelat tematicky commit pro opravu iCloud metadat a email->document review workflow.
- Volitelne: zlepsit text v Cockpitu, aby bylo jasne, ze nove e-mailove PDF jde po ulozeni nejdriv do rucni revize.

Zmenene nebo relevantni soubory:
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `app/email/header_metadata.py`
- `app/cockpit.py`
- `app/documents/vault.py`
- `tests/test_email_header_metadata.py`
- `tests/test_cockpit.py`
- Private metadata v `data/private/documents/` byla zmenena jen po Milove potvrzeni; necommitovat.

Overeni:
- `.venv/bin/python -m unittest tests.test_email_header_metadata tests.test_cockpit tests.test_email_icloud_archive_provider` proslo: 140 testu OK.
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_document_vault_tools tests.test_email_header_metadata` proslo: 199 testu OK.
- `git diff --check` proslo bez vystupu.
- Cockpit local i Tailscale byly restartovane a bezi pod novymi PID.

Bezpecnost / neukladat:
- Do handoffu neukladat telo e-mailu, obsah PDF, cele e-mailove adresy, cisla smluv, castky ani dalsi citlive udaje.
- Pri dalsim cteni/stahovani/otevirani obsahu PDF nebo pri mazani, presunu do kose, odesilani a commitu dodrzet potvrzovaci brany.
- `data/private/` a `data/session_autosave/` necommitovat.
