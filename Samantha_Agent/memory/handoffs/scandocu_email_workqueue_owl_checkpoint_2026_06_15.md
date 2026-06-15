Nazev: ScanDocu, e-mail Work Queue a soví text - checkpoint 2026-06-15
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-15

Co se resilo:
- Dokonceni dnesniho zpracovani e-mailove dokumentove fronty a navazujici opravy ergonomie.
- Opravy Email Work Queue pro lepsi blokove zpracovani a mensi riziko omylu.
- Opravy ScanDocu Review po realnem zpracovani ulozenych e-mailovych PDF.
- Zmena soví promluvy pro ColorsAndNumbers na 2026-06-16.

Co je hotove:
- Email Work Queue filtruje odchozi/konceptove slozky z pracovnich polozek.
- Email Work Queue zobrazuje odesilatele v metaradku a vysvetluje, ze blokove filtry jsou az v okne Work Queue.
- Klasifikace e-mailu typu `danovy doklad k objednavce` uz nespadne automaticky pod Financni spravu, ale jako faktura/e-shop.
- ScanDocu Review ma volbu `Jina oblast...` a umi zapsat vlastni oblast pri revizi dokumentu.
- ScanDocu ma soukromy registr oblasti `data/private/documents/index/domain_registry.json`; nova vlastni oblast se po ulozeni nabidne pri dalsim dokumentu.
- Opraven bug dlouheho ScanDocu review tokenu s koncovou pomlckou, ktery vedl na chybu `ScanDocu kandidat nebyl nalezen`.
- ScanDocu server byl restartovan a endpoint `/api/domains` byl overen.
- Soví text pro 2026-06-16 je v `config/OwlSpeech.csv` a sladene je i `ColorsAndNumbers/OwlSpeech.txt`.

Co neni hotove:
- Neni hotova plna centralni sprava oblasti s ceskymi popisky a slucovanim podobnych oblasti.
- Neni hotove tlacitko `Preposlat` primo v dokumentovem detailu; zatim se da preposilat rucnim dvoukrokovym outbound workflow.
- Cast dnes zpracovanych dokumentu muze byt stale k rucni revizi podle stavu v Cockpitu.

Dalsi krok:
- V Cockpitu znovu otevrit ScanDocu Review a pokracovat v revizi zbylych dokumentu; pri nove oblasti pouzit `Jina oblast...`, potom uz vybirat z nabidky.

Navrhovane dalsi kroky:
- Po dokonceni aktualnich revizi zvazit maly spravce oblasti: prejmenovat popisek, sloucit podobne oblasti, zakazat duplicitni podobne nazvy.
- Potom navrhnout a implementovat dvoukrokove tlacitko `Preposlat` u nalezeneho dokumentu.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/app/cockpit.py`
- `Samantha_Agent/tests/test_cockpit.py`
- `Samantha_Agent/app/documents/scandocu.py`
- `Samantha_Agent/tests/test_document_vault_tools.py`
- `Samantha_Agent/config/OwlSpeech.csv`
- `ColorsAndNumbers/OwlSpeech.txt`
- `Samantha_Agent/memory/handoffs/scandocu_email_workqueue_owl_checkpoint_2026_06_15.md`

Bezpecnost / neukladat:
- Do gitu nepatri `data/private/`, PDF, textove indexy dokumentu, e-mailove archivy, plne e-maily, identifikatory dokumentu s citlivym obsahem ani `data/session_autosave/`.
- Soukromy registr oblasti v `data/private/documents/index/domain_registry.json` zustava mimo git.
