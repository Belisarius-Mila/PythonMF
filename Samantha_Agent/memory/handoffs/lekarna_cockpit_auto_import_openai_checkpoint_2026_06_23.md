Nazev: Lekarna Cockpit auto-import fotek pres OpenAI Vision
Priorita: 1
Stav: hotovo / ceka na navazujici web export
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
- Mila chtel rutinni prijem noveho leku z fotky bez Adamovy rucni ucasti.
- Cil byl: vybrat fotku z Downloads, precist obal pres OpenAI Vision, pripravit navrh, potvrdit import, zvolit umisteni a zapsat lek do lokalni evidence.
- Soucasne bylo potreba zachovat bezpecnostni brany: OpenAI krok jen po presne potvrzovaci vete, zapis do CSV jen po dalsi presne potvrzovaci vete.

Co je hotove:
- V Cockpitu existuje lokalni admin stranka `/lekarna-admin/`.
- Admin umi vyhledavat v lekarne, pripravit vyrazeni leku a potvrzene vyradit lek soft-delete postupem.
- Admin umi nacist fotky ze slozky Downloads, vybrat konkretni fotku checkboxem a spustit OpenAI Vision draft.
- OpenAI draft vyzaduje potvrzeni `Potvrzuji OpenAI vision draft lekarna`.
- Import do skladu vyzaduje potvrzeni `Potvrzuji import fotek lekarna`.
- Pred potvrzenim importu se voli umisteni: vychozi `Horní koupelna`, dale Jana, Mila, vitaminy/prvky nebo vlastni text.
- Apply krok bere jen manifesty z `data/lekarna/photo_imports/` s nazvem `lekarna_auto_import_manifest_*.csv`, kopiruje vybranou fotku z Downloads do soukrome slozky lekarny a zapisuje radek do CSV pres existujici potvrzovany import.
- Lokalne byl prijat Mucosolvan a umisteni bylo nastaveno na `Horní koupelna`.

Co neni hotove:
- Verejna/GitHub Pages Lekarna se po zmene lokalni CSV sama neaktualizuje.
- Pro web je porad potreba samostatny export, sifrovani balicku a commit jen sifrovaneho vystupu.
- Expirace a plny PIL vytah se z fotky zatim automaticky nedoplnuji spolehlive; nove polozky zustavaji jako inventar, ne zdravotni doporuceni.

Dalsi krok:
- Pri dalsim novem leku otestovat plny tok v Cockpitu: vybrat jednu fotku z Downloads, potvrdit OpenAI draft, zkontrolovat report, vybrat umisteni a potvrdit prijem na sklad.

Navrhovane dalsi kroky:
- Pozdeji doplnit samostatne tlacitko nebo workflow pro publikaci zmen na web: export private dat, sifrovani balicku a commit jen encrypted bundle.
- Pozdeji doplnit volitelny review krok pro expiraci, osobu/sekci a kratky PIL status.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/lekarna/auto_import.py`
- `app/lekarna/download_intake.py`
- `app/lekarna/openai_vision.py`
- `scripts/lekarna_auto_import.py`
- `scripts/lekarna_download_intake.py`
- `scripts/lekarna_openai_vision_pilot.py`
- `scripts/lekarna_retire.py`
- `tests/test_cockpit.py`
- `tests/test_lekarna_service.py`
- `memory/projects/lekarna_domaci_leky.md`

Bezpecnost / neukladat:
- `data/lekarna/` obsahuje soukroma domaci data a zustava mimo git.
- Fotky, CSV evidence, reporty a manifesty s realnymi leky se necommitovat.
- OpenAI Vision se spousti jen po potvrzeni, protoze odesila obrazek mimo lokalni stroj.
