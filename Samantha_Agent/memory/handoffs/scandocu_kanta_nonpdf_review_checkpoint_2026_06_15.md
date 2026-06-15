Nazev: ScanDocu Review - Kanta dokumenty a ne-PDF prilohy
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-06-15

Co se resilo:
- Po e-mailovem miningu stavebnich praci Frantiska Kanty byly potvrzene prioritni
  prilohy stazene do soukrome slozky a vytazeny z nich castky.
- Dokumenty s nalezenymi castkami byly zarazene do private document vaultu jako
  dokumenty k revizi.
- Pri prvnim dokumentu ve ScanDocu Review se ukazalo, ze stary Word `.doc`
  soubor existuje, ale UI ho chybne posilalo do PDF iframe, kde se nezobrazil.
- Nasledne se ukazalo, ze tlacitko pro ne-PDF soubor oteviralo prazdnou kartu
  `about:blank`, protoze kombinovalo novou kartu a download response.

Co je hotove:
- Kanta prilohy s castkami jsou ve private vaultu mimo git jako `needs_review`.
- Duplicitni prilohy byly rozpoznane podle SHA a nebyly zbytecne rozmnozene.
- Do registru oblasti byly pridane popisky pro Jizerni Vtelno, Tepelne cerpadlo,
  Byt MB / Cejeticky a Neuberk.
- Dve zjevne spatne klasifikovane polozky UID 117308 byly prehozeny z tepelneho
  cerpadla do Jizerniho Vtelna.
- ScanDocu Review umi rozlisit PDF a ne-PDF kandidaty:
  - PDF se zobrazuje v inline nahledu,
  - ne-PDF dokumenty ukazou panel `Nahled neni dostupny`,
  - tlacitko `Stahnout soubor` stahuje dokument bez otevirani prazdne karty.
- ScanDocu server byl po oprave restartovan a odpovida na `127.0.0.1:8766`.
- Dokumentove testy prosly: `.venv/bin/python -m unittest tests.test_document_vault_tools`
  hlasilo `68 tests OK`.

Co neni hotove:
- Kanta dokumenty je jeste potreba projet ve ScanDocu Review a potvrdit/upravit
  metadata jeden po druhem.
- Nektere starsi dokumenty mohou byt vecne zarazene jen priblizne; pri revizi je
  vhodne doladit oblast, typ dokumentu a souvisejici vec.
- Ne-PDF soubory zatim nemaji inline preview ani konverzi do PDF; aktualni reseni
  je bezpecny download a lokalni otevreni.

Dalsi krok:
- V Cockpitu otevrit ScanDocu Review a pokracovat v revizi Kanta fronty.
- U `.doc`/`.xls` dokumentu pouzit `Stahnout soubor`, otevrit lokalne a metadata
  potvrdit vlevo v Review.

Navrhovane dalsi kroky:
- Pokud bude ne-PDF dokumentu hodne, zvazit samostatnou konverzi kopie do PDF pro
  nahled, ale jen jako doplnek; original ve vaultu musi zustat zachovany.
- Po dokonceni Kanta revize zkontrolovat stav `Dokumenty k revizi`, aby se
  nepotvrzene Kanta dokumenty nezasekly ve fronte.

Zmenene nebo relevantni soubory:
- `app/documents/scandocu.py`
- `tests/test_document_vault_tools.py`
- `data/private/documents/` - soukromy vault mimo git
- `data/private/email_seznam/kanta_extraction/` - soukrome reporty mimo git

Bezpecnost / neukladat:
- Do gitu nepatri samotne prilohy, cele texty dokumentu, castky v detailnich
  kontextech, e-maily ani obsah `data/private/`.
- Originální e-maily se nemenily ani nemazaly.
