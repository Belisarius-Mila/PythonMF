Nazev: FamilyVideoOrganizer - prvni UI prototyp a dalsi kroky
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-22

Co se resilo:
- Mila chce pro dceru misto PDF/Excelu malou lokalni webovou aplikaci
  `FamilyVideoOrganizer`, ktera pomuze rozhodovat o videich pro short/family
  rodinny strih.
- Aplikace nema byt verejny web s rodinnymi daty. V gitu ma byt jen zobrazovac
  a formulare; soukroma data, nahledy a videa zustanou mimo git.
- Navrh smeru: dcera rozbali balicek do slozky s videi, otevre HTML, vybere
  pripadne slozku s videi, upravi rozhodnuti a poznamky, autosave chrani praci
  a na konci exportuje JSON rozhodnuti pro Milu.
- Pri testu se objevil bug s video modalem, ktery nesel zavrit.

Co je hotove:
- Zalozen prvni prototyp v:
  `docs/family-video-organizer/`
- Soubory:
  - `docs/family-video-organizer/index.html`
  - `docs/family-video-organizer/styles.css`
  - `docs/family-video-organizer/app.js`
  - `docs/family-video-organizer/videos-data.example.js`
- UI obsahuje:
  - hlavni tabulku videi,
  - sloupce Short, Family, Nazev, Puvodni nazev, Rozhodnuti, Poznamka, Video,
  - filtrovani podle textu, short/family/mimo vybery, upravenych a poznamek,
  - preview panel,
  - modal pro prehrani videa,
  - autosave do `localStorage`,
  - import draftu,
  - export rozhodnuti do JSON,
  - tlacitko `Slozka s videi` pro prohlizece s File System Access API
    hlavne Chrome/Edge.
- Opraven bug modalu:
  - CSS `modal[hidden] { display: none; }`
  - zavirani pres tlacitko, klik mimo modal a klavesu Escape
  - video se pri zavreni zastavi a vycisti.
- Implicitni logika sloupce `Rozhodnuti`:
  - Short + Family -> `Obe verze`
  - jen Short -> `Jen short`
  - jen Family -> `Jen family`
  - mimo vybery -> `Vyradit`
- Syntaxe `app.js` overena pres `node --check`.
- Lokální test server bezel na `http://localhost:8766/` a vracel HTML/CSS/JS.

Co neni hotove:
- Neni vytvoreny realny soukromy datovy balicek z `data/private/tomik_rok_2/`.
- Neni vygenerovany `videos-data.js` s realnymi 217 zaznamy a cestami k nahledum.
- Neni pripraven ZIP balicek pro dceru.
- Neni otestovane realne prehravani videi ze slozky s puvodnimi MP4.
- Neni doresene, zda finalni balicek bude:
  - jen HTML + data + thumbs a videa ve stejne slozce,
  - nebo HTML + data + thumbs a dcera vybere slozku s videi.
- Neni implementovany zpetny import dcerina JSON rozhodnuti do short/family
  vyberu; to musi byt samostatny potvrzovany krok.

Dalsi krok:
- Vygenerovat soukromy realny datovy balicek mimo git:
  `data/private/tomik_rok_2/family_video_organizer_package/`
  s aplikaci, `videos-data.js`, nahledy a navodem.
- Otestovat lokalne na realnych datech:
  - nacitani 217 videi,
  - hover/click nahledy,
  - autosave,
  - export JSON,
  - prehrani videa podle `Puvodni nazev`.

Navrhovane dalsi kroky:
- Pridat generator realneho `videos-data.js` z
  `data/private/tomik_rok_2/03_audit/video_audit_described.csv` a short/family
  manifestu.
- Pridat generator ZIP balicku pro dceru, bez commitu soukromych dat.
- Do aplikace pridat jasny stav, zda video soubor byl nalezen ve slozce s videi.
- Pridat CSV export vedle JSON, aby bylo mozne rozhodnuti precist i v Excelu.
- Pozdeji pridat import dcerina JSON a read-only diff:
  co zustava, co vypadava, co se presouva do short/family.

Zmenene nebo relevantni soubory:
- `docs/family-video-organizer/index.html`
- `docs/family-video-organizer/styles.css`
- `docs/family-video-organizer/app.js`
- `docs/family-video-organizer/videos-data.example.js`
- `memory/handoffs/tomik_video_review_pdfs_done_editable_next_2026_05_22.md`
- `memory/projects/tomik_video_imovie.md`
- `data/private/tomik_rok_2/03_audit/video_audit_described.csv`
- `data/private/tomik_rok_2/05_imovie_vyber_short/selection_manifest_short.csv`
- `data/private/tomik_rok_2/06_imovie_vyber_family/selection_manifest_family.csv`

Bezpecnost / neukladat:
- Rodinna videa, nahledy, realny datovy balicek a exporty od dcery patri do
  `data/private/` a nepatri do gitu.
- Do memory ukladat jen workflow, stav a nazvy souboru; ne detailni soukromy
  obsah videi.
- Originaly videi nemazat ani neupravovat bez vyslovneho souhlasu.

Poznamka k eseji:
- Pri hledani bylo potvrzeno, ze v pameti existuje koncept:
  `memory/projects/fraška_dante_esa_concept.md`.
- Obsahuje koncept eseje o frašce, dantovske ose, egu, smireni a dustojnosti.
- Nenasel se plny finalni text eseje, jen projektovy koncept a pracovni definice.
