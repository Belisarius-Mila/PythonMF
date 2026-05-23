Nazev: Tomik video iMovie - review PDF hotove, dalsi krok editovatelny rozhodovaci list
Priorita: 1
Stav: ceka na navazani
Pripomenout pri startu: ano
Datum: 2026-05-22

Co se resilo:
- Mila potreboval podklady pro rozhodnuti s dcerou, ktera videa ponechat,
  vyradit nebo upravit pro rodinny iMovie strih.
- Nejdrive vznikl bezobrazkovy chronologicky katalog vsech 217 videi.
- Potom se katalog upravoval: zvetsit pismo, rozdelit na 8 stran, pridat trvani,
  pridat sloupce `VideoShort` a `VideoFamily`, a nakonec pridat `Puvodni nazev`,
  aby dcera dokazala dohledat a pustit konkretni puvodni video.
- Vedle toho vznikl celkovy obrazovy katalog se 3 nahledy na video, rozdeleny
  do dvou mensich PDF souboru.
- Na konci se resilo, zda ma smysl delat editovatelne PDF. Doporučení: ne jako
  hlavni workflow; lepsi bude editovatelny CSV/Excel rozhodovaci list.

Co je hotove:
- Bezobrazkovy rozhodovaci katalog:
  `data/private/tomik_rok_2/03_audit/video_catalog_all_8pages_selection.pdf`
  - 8 stran
  - vsech 217 videi
  - sloupce: `#`, `Datum`, `Nazev`, `Puvodni nazev`, `Strucny popis`, `Trvani`,
    `VideoShort`, `VideoFamily`
  - `ano` ve sloupcich `VideoShort`/`VideoFamily` jen pokud je video v danem
    vyberu
  - velikost cca 5,1 MB
- Obrazovy review katalog se 3 nahledy na video:
  - `data/private/tomik_rok_2/03_audit/video_review_all_part1_of_2.pdf`
    - 28 stran, cca 4,8 MB
  - `data/private/tomik_rok_2/03_audit/video_review_all_part2_of_2.pdf`
    - 27 stran, cca 4,5 MB
- Generatory:
  - `scripts/tomik_video_catalog_pdf.py`
  - `scripts/tomik_video_full_review_pdf.py`
- Zdrojem dat je soukromy audit:
  `data/private/tomik_rok_2/03_audit/video_audit_described.csv`
  plus manifesty short/family vyberu.

Co neni hotove:
- Neni vytvoreny editovatelny rozhodovaci soubor pro dceru.
- Neni vyreseno, zda ho poslat jako CSV, XLSX nebo HTML.
- Neni doplnen finalni workflow, jak dceriny poznamky importovat zpet do vyberu.
- Neni provedena finalni uprava short/family vyberu podle dcery.
- Neni import do iMovie ani finalni strih.

Dalsi krok:
- Pri navazani vytvorit editovatelny rozhodovaci list se stejnymi zakladnimi
  sloupci jako PDF a s navic sloupci pro dcerino rozhodnuti.

Navrhovane dalsi kroky:
- Varianta A, doporucena: vygenerovat CSV/Excel rozhodovaci list se sloupci:
  `#`, `Datum`, `Nazev`, `Puvodni nazev`, `Strucny popis`, `Trvani`,
  `VideoShort`, `VideoFamily`, `Vybrat`, `Vyradit`, `Poznamka dcery`,
  `Preferovana verze`.
- Varianta B: vygenerovat HTML review stranku s nahledy a odkazy na videa,
  pozdeji pripadne doplnit lokalni ukladani poznamek.
- Varianta C: PDF formular nedoporucovat jako hlavni cestu; technicky by slo,
  ale pro tabulkove rozhodovani je neohrabany.
- Po navratu dcerinych poznamek udelat read-only vyhodnoceni: co zustava,
  co vypadava, co pridat do short/family, a az po potvrzeni upravit vybery.

Zmenene nebo relevantni soubory:
- `scripts/tomik_video_catalog_pdf.py`
- `scripts/tomik_video_full_review_pdf.py`
- `data/private/tomik_rok_2/03_audit/video_catalog_all_8pages_selection.pdf`
- `data/private/tomik_rok_2/03_audit/video_review_all_part1_of_2.pdf`
- `data/private/tomik_rok_2/03_audit/video_review_all_part2_of_2.pdf`
- `data/private/tomik_rok_2/03_audit/video_audit_described.csv`
- `data/private/tomik_rok_2/05_imovie_vyber_short/selection_manifest_short.csv`
- `data/private/tomik_rok_2/06_imovie_vyber_family/selection_manifest_family.csv`

Bezpecnost / neukladat:
- Rodinna videa, nahledy a PDF vystupy jsou soukrome v `data/private/` a
  nepatri do gitu.
- Do memory neukladat detailni soukromy obsah videi; staci workflow, pocty,
  nazvy vystupu a dalsi kroky.
- Originaly nemazat ani neupravovat bez vyslovneho souhlasu.
