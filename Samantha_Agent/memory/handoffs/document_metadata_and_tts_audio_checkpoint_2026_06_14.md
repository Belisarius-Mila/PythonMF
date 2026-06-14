Nazev: Dokumentovy vault metadata + TTS sandbox pravidlo
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-14

Co se resilo:
- Ranni dokonceni dokumentove klasifikace ve vaultu: danove priznani a ctyri pojistne e-mailove prilohy uz nemaji technicky typ `email-attachment-pdf` jako skutecny typ dokumentu.
- Metadata zadana cesky se maji ukladaji do bezpecnych ASCII slug hodnot, aby nevznikaly poskozene hodnoty typu `da-ov-p-izn-n`.
- Cockpit ma lidstejsi popisky pro nove typy dokumentu.
- Po realnem hlasovem testu se ukazalo, ze `scripts/speak_edge_open.py` muze v Codex sandboxu nahlasit uspech, ale Mac audio se neozve.

Co je hotove:
- Pridan helper `safe_ascii_slug()` a pouzity pro manualni metadata dokumentu, ScanDocu import/revizi, mobile final metadata a custom oblasti.
- Cockpit zobrazuje `danove-priznani` jako `daňové přiznání`.
- Cockpit zobrazuje pojistne typy `green_card`, `insurance_assistance_card` a `insurance_payment_confirmation` lidsteji.
- Soukromy vault byl po Milove potvrzeni upraven tak, ze klasifikace hlasi 27/27 dokumentu s kompletnimi zakladnimi metadaty.
- Hlasovy terminal prompt nove rika, ze skutecne Mac audio pres `speak_edge_open.py` ma bezet mimo Codex sandbox, jinak muze vzniknout falesny uspech bez zvuku.
- Technicka pamet TTS a Codex permission preference byly upraveny podle realneho testu.

Co neni hotove:
- Neni delan dalsi UI redesign dokumentoveho vaultu.
- Neni resena obecna vzdalená automatizace Codex approvalu; pouze konkretni TTS audio pravidlo.
- Cockpit nebyl po teto male zmene restartovan a rucne proklikan.

Dalsi krok:
- Pri dalsim realnem dokumentu otestovat v Cockpitu, ze nova oblast/case a ceske nazvy metadat zustanou citelne.

Navrhovane dalsi kroky:
- Okamzite: po dalsim startu Cockpitu zkontrolovat panel klasifikace a jeden detail dokumentu.
- Volitelne: pridat maly smoke test pro TTS pravidlo do provozniho checklistu, ne do bezneho automatickeho testu, protoze skutecny zvuk je systemova/GUI vec.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/scandocu.py`
- `app/cockpit.py`
- `app/speech/terminal_bridge.py`
- `tests/test_document_vault_tools.py`
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/technical/codex_permissions_preferences.md`

Bezpecnost / neukladat:
- Do handoffu nejsou ukladane obsahy PDF, e-mailu, osobni udaje ani soukroma runtime data.
- `data/private/` a `data/session_autosave/` zustavaji mimo git.
