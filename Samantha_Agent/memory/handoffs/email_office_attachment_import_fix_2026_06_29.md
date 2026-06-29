Nazev: Email Work Queue - Office prilohy a darovaci smlouvy
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-29

Co se resilo:
- Po realnem ulozeni e-mailu s prilohami se ukazalo, ze PDF prilohy prosly do dokumentoveho vaultu spravne, ale Word priloha se musela vytahnout a zaradit rucne.
- Pricina nebyla ztrata dat, ale obecne chovani e-mailove fronty: davkovy import ukladal jen PDF a obrazky; Office soubory preskakoval. Pri rucnim importu pak klasifikace nekdy spadla na obecny typ `document`.

Co je hotove:
- Email Work Queue umi ukladat vybrane Office prilohy jako `.doc`, `.docx`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.ods`, `.ppt`, `.pptx`, `.odp`.
- Office priloha se nevnucuje do typu `email-attachment-pdf`; typ dokumentu se necha urcit obecnym klasifikatorem podle nazvu a textu.
- Klasifikator rozpoznava `darovaci smlouva` / `darovací smlouva` a pady `smlouvy`; s vyrazem `navrh` / `návrh` nastavi `gift_contract_draft`, jinak `gift_contract`.
- Cockpit ma lidske popisky pro `gift_contract` a `gift_contract_draft`.
- Pridan regresni test, ze `.doc` priloha z e-mailove fronty se ulozi jako samostatny dokument typu `gift_contract_draft`.

Co neni hotove:
- Neni pridany specialni prevod Word souboru na PDF ani Office preview v prohlizeci; otevreni Office dokumentu zustava pres lokalni aplikaci / download panel.
- Neni resena nova oblast pro nemovitostni smlouvy obecne; aktualni oprava je na urovni typu dokumentu a podpory Office priloh.

Dalsi krok:
- Commitnout a pushnout hotovou opravu.
- Potom pokracovat planovanym tematem Guard proti mazani.

Navrhovane dalsi kroky:
- Okamzite: po pushi spustit `scripts/work_context_guard.py`.
- Volitelne pozdeji: doplnit obecnejsi typy pro dalsi smlouvy k nemovitostem, pokud se v realnem provozu objevi.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/documents/vault.py`
- `tests/test_cockpit.py`

Overeni:
- `.venv/bin/python -m unittest tests.test_cockpit`
- `.venv/bin/python -m unittest tests.test_document_vault_tools`

Bezpecnost / neukladat:
- Do handoffu nejsou ulozena tela e-mailu, osobni udaje, e-mailove adresy ani obsah dokumentu.
- Soukrome dokumenty a archivy zustavaji mimo git.
