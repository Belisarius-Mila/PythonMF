Nazev: Cockpit hledani nakupu a filtr knihovnich PDF exportu
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-22

Co se resilo:
- Mila hledal fakturu k bazenovemu robotu Dolphin a zjistilo se, ze nakup uz je ulozeny v `data/private/purchases/`, ale nebyl dobre napojeny na Cockpit hledani.
- Po prvni oprave se nakup sice nasel, ale rozkliknuti slo do stare document-vault ctecky `/documents/read`, ktera zna jen `data/private/documents/`, a vratilo chybu `Dokument nebyl nalezen ve vault indexu.`
- Dalsi problem: testovaci PDF exporty z Knihovny prisle e-mailem se zacaly nabizet v e-mailove/document intake fronte, prestoze maji byt jen lidsky export, ne vstup zpet do Samanthy.

Co je hotove:
- `search_document_index` v Cockpitu umi jako dalsi read-only zdroj prohledat `data/private/purchases/*/*/invoice_manifest.json`.
- Dotazy jako `dolphin` a `bazénový robot` najdou ulozenou nakupni kartu jako `source_type: purchase`.
- Nákupní vysledek ma vlastni ctecku `/purchases/read?purchase_id=...` a PDF endpoint `/purchases/pdf?purchase_id=...`.
- Resolver povoli otevrit jen PDF, ktere opravdu lezi uvnitr `data/private/purchases/`.
- UI pro vysledky typu `purchase` zobrazuje `Otevřít nákupní PDF` a uz neposila nakup do `/documents/read`.
- Exporty z Knihovny jsou v e-mailovych hlavickach a dokumentovem e-mail scan workflow potlacene podle subject prefixu `[SamanthaLibraryExport]` a pripraveny helper umi zachytit i marker `X-Samantha-Library-Export`, pokud bude v budoucnu dostupny v metadatech.
- Filtr je pouzity pro nove hlavicky, dokumentovy scan, pending work queue i ulozeny overview.
- Realny iCloud scan za 3 dny ukazal `skipped_library_export_count: 2` a v polozkach se uz nevracel `SamanthaLibraryExport`.
- Lokalni i Tailscale Cockpit byly restartovane; pri overovani pozor na `curl | rg`, ktery muze predcasne zavrit velke HTML a vyvolat benigni `BrokenPipeError`. Stahovat celou stranku do souboru je spolehlivejsi.

Co neni hotove:
- Zatim neni obecny systemovy report nakupni evidence ani plny intake novych nakupu; jde jen o vyhledani a otevreni existujicich manifestu/PDF.
- Custom e-mail header `X-Samantha-Library-Export` se v beznem prehledu hlavicek zatim necte, proto filtr prakticky stoji hlavne na subject prefixu `[SamanthaLibraryExport]`.

Dalsi krok:
- Po commitu a pushi zkontrolovat v Cockpitu: hledani `dolphin` -> `Otevřít nákupní PDF` a e-mail/document intake refresh -> exporty Knihovny se nenabizeji ke zpracovani.

Navrhovane dalsi kroky:
- Okamzite: po obnoveni stranky overit UI z iPhonu/Tailscale i lokalne.
- Pozdeji: zvazit lehky `Nákupy / záruky` panel s dotazy typu `Kdy končí záruka?`, ale az po samostatnem rozhodnuti.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `data/private/purchases/2026/2026-05-23_dolphin-e20/` je relevantni soukromy priklad, ale nepatri do gitu.
- `data/private/article_archive/exports/` muze obsahovat testovaci PDF exporty Knihovny, take nepatri do gitu.

Bezpecnost / neukladat:
- Do gitu neukladat faktury, PDF exporty, e-mailova tela, cele e-maily, osobni udaje ani private archiv.
- Commitovat jen kod, testy a tento git-safe handoff/index.
