Nazev: Lekarna - foto import, PIL, produkcni publikace a vyrazeni overeno
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-09

Co se resilo:
- Zjednoduseni a realny test prijmu noveho leku z fotky v `Lekarna - sprava`.
- Napojeni online stazeni konkretniho PIL dokumentu a validacni brzda, aby bez overeneho PIL workflow nepokracovalo.
- Automaticka publikace sifrovaneho produkcniho balicku po prijmu na sklad.
- Test celeho cyklu na docasne testovaci polozce SERTIVAN / sertralin.
- Nasledne potvrzene vyrazeni testovaci polozky a oprava exportu, aby vyradene radky nesly do produkcni webove Lekarny.

Co je hotove:
- Sprava Lekarny ukazuje po priprave navrhu automaticky nactenou kontrolu; tlacitko je preznacene na `Znovu nacist kontrolu` a dava viditelnou zpetnou vazbu.
- Prijem z fotky pro testovaci SERTIVAN prosel: OCR, SUKL DLP, PIL dokument, `PIL_Short`, prijem na sklad, kopie fotky, web export a sifrovany balicek.
- Po prijmu na sklad se automaticky commituje a pushuje pouze `docs/lekarna/encrypted-data/lekarna.enc.json`.
- Produkcni Lekarna dostala filtr v seznamu krabicky, aby se dlouhy `Pils Home Store` dal filtrovat podle nazvu nebo latky; alias `setralin` hleda `sertralin` / `sertivan`.
- Vyrazeni SERTIVANu bylo potvrzene: v lokalnim CSV zustava auditni radek s `mnozstvi=vyradeno` a `umisteni=vyradeno`.
- Webovy export byl opraven tak, aby radky oznacene jako `vyradeno` v mnozstvi, umisteni nebo poznamce do `lekarna.json` vubec nesly.
- Po vyrazeni se nově automaticky obnovi web export, sifrovany balicek a produkcni push stejne jako po prijmu.
- Overeno po oprave: lokalni web export ani produkcni sifrovany balicek uz SERTIVAN neobsahuji.

Co neni hotove:
- Neni jeste delany dalsi realny prijem jineho leku po techto opravach.
- Produkcni GitHub Pages muze po pushi drzet CDN cache az nekolik minut; UI zatim jen hlasi, ze push probehl, neceka na potvrzeni Pages CDN hashe.
- Fuzzy hledani v produkcni aplikaci je zatim jen lehke: konkretni alias `setralin -> sertralin/sertivan` a filtr v krabicce, ne obecny spellchecker.

Dalsi krok:
- Pri dalsim testu vzit novy lek z fotky a overit cely tok znovu: `Pripravit navrh z fotek` -> automaticka kontrola -> `Prijmout navrh na sklad` -> produkce -> vyhledani -> pripadne vyrazeni.

Navrhovane dalsi kroky:
- Okamzite neni nutny dalsi zasah do Lekarny, workflow je pouzitelny.
- Volitelne zlepsit status po publikaci: po pushi opakovane overit GitHub Pages hash a v UI ukazat `produkce uz servíruje novy balik`.
- Volitelne pridat obecnejsi fuzzy vyhledavani/preklepy pro lekarnu.
- Volitelne doplnit samostatny test produkcniho dešifrovani balicku v lokalnim browser-like smoke testu, pokud bude k dispozici heslo v bezpecnem prostredi.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/open_cockpit.py`
- `scripts/export_lekarna_web_private_data.py`
- `tests/test_cockpit.py`
- `tests/test_open_cockpit.py`
- `tests/test_lekarna_web_export.py`
- `docs/lekarna/app.js`
- `docs/lekarna/styles.css`
- `docs/lekarna/index.html`
- `docs/lekarna/encrypted-data/lekarna.enc.json`
- `data/lekarna/domaci_leky.csv` zustava soukrome/ignorovane mimo git.

Bezpecnost / neukladat:
- Neopisovat plny obsah `PIL_Short`, fotky obalu ani privatni CSV do chatu nebo memory.
- Necommitovat `data/lekarna/` ani `docs/lekarna/private-data/`.
- Produkcni commit ma obsahovat jen sifrovany balicek a kod/testy, nikdy nesifrovany `lekarna.json`.
