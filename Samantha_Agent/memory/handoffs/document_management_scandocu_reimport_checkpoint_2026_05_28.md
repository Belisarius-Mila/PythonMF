Nazev: Document management - ScanDocu reimport a revize ulozenych priloh
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-28

Co se resilo:
- Navazovalo se na dokumentovy private vault a ScanDocu workflow pro PDF z Downloads.
- Hlavni vstup je potvrzen: Mila pripravi PDF mimo Samanthu, ulozi ho do Downloads, ScanDocu ho nacte, navrhne metadata a po kontrole ho ulozi do private vaultu.
- Resila se i revize drive ulozenych dokumentu: nove cteni umi lepe doplnit typ, protistranu, souvisejici vec a tagy, takze nektere stare prilohy chceme znovu projit dokument po dokumentu.

Co je hotove:
- ScanDocu umi revidovat uz ulozene dokumenty pres rezim `?mode=review` a cockpit ma tlacitko `Revidovat ulozene`.
- ScanDocu zobrazuje napovedu pro sifrovane/uzamcene PDF a doporucuje odemcenou kopii pres Preview/Tisk do PDF.
- Ulozeni odemcene varianty PDF z Downloads funguje a stara podobna sifrovana varianta se umi oznacit jako preskocena, aby se znovu nenabizela ve fronte.
- Zlepsena metadata pro vozidla: motocykl, znacka/model, Volvo/V40 a SPZ/RZ se maji promitat do `related_asset` a tagu, pokud jsou v textu dostupne.
- Pravdepodobne duplicity/souvisejici dokumenty se ve ScanDocu blokuji, dokud Mila vyslovne nezaskrtne `Presto ulozit jako dalsi dokument`.
- Testy dokumentoveho modulu prosly: `46 tests OK`.

Co neni hotove:
- Pokracovat ve znovuukladani / revizi uz ulozenych priloh dokument po dokumentu.
- Najemni smlouva se ma znovu naskenovat a vlozit do Downloads az pozdeji; nepokracovat dnes bez noveho vstupu.
- Po dokonceni aktualni davky bude vhodne znovu projit, ktere stare metadata-only nebo sifrovane dokumenty maji odemcenou lepsi kopii a ktere zustanou preskocene.

Dalsi krok:
- Pri pristim startu Codexu nabidnout pokracovani v dokument managementu jako prioritu 1: naskenovat / vlozit novou kopii najemni smlouvy do Downloads a projit ji ve ScanDocu.

Navrhovane dalsi kroky:
- Okamzite: po vlozeni noveho PDF do Downloads otevrit ScanDocu, zkontrolovat kvalitu nacteni, metadata a duplicity, potom ulozit.
- Navazujici: pokracovat v `Revidovat ulozene` pro drive ulozene prilohy, ale jen po jednom dokumentu s lidskym potvrzenim.
- Pozdeji: doplnit cockpit prehled "cekaji re-review", aby bylo videt, kolik starsich dokumentu jeste nebylo znovu projito.

Zmenene nebo relevantni soubory:
- `app/documents/scandocu.py`
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/cockpit.py`
- `tests/test_document_vault_tools.py`
- `scripts/scandocu_server.py`
- `scripts/cockpit_server.py`
- `memory/projects/document_management_private_vault.md`

Bezpecnost / neukladat:
- Necommitovat `data/private/`, PDF, OCR texty, manifesty ani jine soukrome dokumenty.
- Do memory neukladat plne texty dokumentu, adresy, rodna cisla, SPZ/RZ konkretniho realneho dokumentu ani dalsi citlive identifikatory.
- Sifrovana PDF neobchazet; hesla nepsat do chatu ani do souboru.
