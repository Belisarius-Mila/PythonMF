Nazev: Document Management / Cockpit case health checkpoint
Priorita: 1
Stav: hotovo, ceka na rucni retest
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Navazani na ranni plan dokumentu po stabilizaci Cockpitu.
- Cockpit byl rozsireny o prakticke dokumentove panely a workflow:
  `Dokumenty k revizi`, `Vazby / cases`, `Klasifikace`, `Terminy v dokumentech`
  a detail case.
- Detail case ma byt misto pouheho seznamu vazeb pouzitelny jako rozhodovaci
  centrum pro konkretni vec: ukaze dokumenty, otevrene pripominky, terminove
  kandidaty, konflikty a kratke doporuceni.

Co je hotove:
- Panel/report `Dokumenty k revizi` pro zero-text/OCR, kratky text, slaba metadata
  a stav cteni.
- Dokumentove cases skryvaji samostatne jedno-dokumentove vazby, aby UI nematlo.
- Detail case umi rozbalit konkretni case a zobrazit vsechny dokumenty v case.
- Detail case umi otevrit dostupne PDF pres redigovanou `document_ref`.
- Detail case v2 ukazuje:
  - souvisejici otevrene pripominky,
  - terminove kandidaty z dokumentu,
  - platebni konflikty,
  - `case_health` shrnuti a doporuceni.
- Due-date kandidati jsou napojeni na potvrzovane vytvoreni pripominky.
- Klasifikace dokumentu ma prehled pokryti metadat a tlacitko `Doplnit metadata`.
- Pro pojistny konflikt byla pridana cesta, jak zrusenou/duplicitni platebni
  pripominku uzavrit s e-mailovym dukazem, bez ukladani celeho e-mailu do git.
- Cockpit byl po posledni uprave bezpecne restartovan a API smoke test ukazal,
  ze realna auto case ma existujici hlidani, zadny novy konflikt a nic ke
  schvaleni.

Co neni hotove:
- Rucni UI retest noveho detailu case po poslednim restartu.
- OCR/zero-text samotne zpracovani jeste neni automatizovane; panel zatim hlavne
  ukazuje kandidaty a doporucene dalsi kroky.
- Sjednoceny intake Downloads / e-mail / mobilni sken je zatim dalsi navazujici
  oblast, ne finalni hotovy workflow.

Dalsi krok:
- V Cockpitu otevrit `Vazby / cases`, rozbalit relevantni case a zkontrolovat,
  jestli sekce `Připomínky`, `Termíny case`, `Konflikty` a `Dokumenty v case`
  davaji prakticky smysl.

Navrhovane dalsi kroky:
- Okamzite: rucni UI retest detailu case v Cockpitu.
- Potom: rozhodnout mezi dvema smery:
  1. OCR/re-review pipeline pro zero-text dokumenty.
  2. Jednotny intake panel pro Downloads / e-mail / mobilni sken.
- Volitelne: zjemnit texty v detailu case, pokud budou v praxi moc dlouhe nebo
  neprehledne.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/documents/scandocu.py`
- `app/documents/vault.py`
- `app/documents/consistency_audit.py`
- `app/reminders/store.py`
- `app/urgent_reminders.py`
- `scripts/document_consistency_audit.py`
- `scripts/restart_cockpit.py`
- `tests/test_cockpit.py`
- `tests/test_document_vault_tools.py`
- `tests/test_document_consistency_audit.py`
- `memory/projects/document_management_private_vault.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do gitu nepatri PDF, OCR texty, plne e-maily, rodna cisla, cele adresy,
  platebni symboly, hesla, API klice ani soukrome dokumentove indexy.
- Handoff uklada jen redigovane shrnuti workflow a technicky stav.
- `data/private/` a `data/session_autosave/` zustavaji mimo git.
