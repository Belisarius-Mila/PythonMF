Nazev: Matysek anglictina - Scene 1 Clearing Meeting review a prvni implementace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Navazujeme na novy odsouhlaseny story bible navrh pro Matyskovu anglictinu:
  `data/matysek_english/scene_proposals_20260530_forest_journey/`.
- Obrazky k lesni ceste jsou podle Mily nyni OK.
- Story bible navrh je podle Mily odsouhlaseny.
- Aktualni predmet prace je prvni scena:
  `scene_specs/scene_01_clearing_meeting.md`.
- Mila otevrel tento soubor rucne a muze do nej doplnit vlastni poznamky nebo
  upravy.

Co je hotove:
- Otevren a precten navrh `Scene 1 - Clearing Meeting`.
- Mila potvrdil, ze se mu libi sekce `Interakce pro Matyska`.
- Dohodnuty smer interakce:
  - napoveda ma prijit anglicky hlasem,
  - u aktivni postavy ma blikat sipka nebo jina jasna vizualni napoveda,
  - Matysek klikne na Benjiho a pak postupne i opakovane na dalsi postavy,
  - vpravo nahore ma byt souhrnna napoveda ke scene v cestine.
- 2026-06-01 po Milove odsouhlaseni se zacal prvni implementacni pruchod.
- Scena je zapojena do webove MMTX verze jako `clearingMeeting`.
- Podle Milovy korekce 2026-06-01 ma cesta k jezeru vlastni samostatnou ikonu
  `Lake` na rozcestniku `intro4` a nema byt soucasti starych cest.
- Dvere po Benji+Bunny zustavaji ve stare vetvi a vedou dal do soví zahrady.
- Dvere z paseky po dokonceni sceny vedou take do soví zahrady.
- Lokální testovaci URL:
  `http://127.0.0.1:8012/index.html?scene=clearingMeeting`

Co neni hotove:
- Je potreba rucne otestovat rozmery a presnost hotspotu nad realnym obrazkem.
- Je potreba doladit vizualni umisteni bublin, sipky, napovedy a slovnicku podle
  realneho prohlizece.
- Anglicke a ceske repliky v prvnim implementacnim pruchodu jedou pres webovou
  rec/fallback; dalsi krok je dogenerovat a zamknout finalni MP3 pro vsechny
  repliky podle odsouhlasenych hlasovych referenci.

Dalsi krok:
- Rucne otestovat rozcestnik a `clearingMeeting` v prohlizeci, hlavne: nova
  samostatna ikona `Lake` na rozcestniku, start sceny, ceska napoveda pod `?`,
  slovnicek pod knihou, aktivni sipka, klikani na postavy, postup dialogu a
  dvere do soví zahrady.

Navrhovane dalsi kroky:
- Okamzite:
  1. Otestovat rozcestnik a `http://127.0.0.1:8012/index.html?scene=clearingMeeting`.
  2. Doladit hotspoty a UI podle toho, co bude v prohlizeci mimo.
  3. Rozhodnout, zda prvni pruchod staci pro commit, nebo jeste pred commitem
     dogenerovat finalni MP3.
- Potom:
  1. Vygenerovat finalni MP3 pro vsechny repliky podle zvolenych hlasu.
  2. Zamknout finalni audio jako assety a uz neregenerovat bez vyslovneho recastu.

Zmenene nebo relevantni soubory:
- `data/matysek_english/scene_proposals_20260530_forest_journey/scene_specs/scene_01_clearing_meeting.md`
- `data/matysek_english/scene_proposals_20260530_forest_journey/english_dialogue_pack.md`
- `data/matysek_english/scene_proposals_20260530_forest_journey/01_story_bible.md`
- `data/matysek_english/scene_proposals_20260530_forest_journey/interaction_design.md`
- `memory/projects/matysek_english_game_concept.md`
- `memory/projects/mmtx_story_hotspot_app.md`
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/styles_intro_v2.css`
- `docs/ForestJourneyScene01.png`
- `MatysekANJ/web_mmtx/index.html`
- `MatysekANJ/web_mmtx/script_intro_v2.js`
- `MatysekANJ/web_mmtx/styles_intro_v2.css`
- `MatysekANJ/web_mmtx/ForestJourneyScene01.png`

Bezpecnost / neukladat:
- Neukladat zadna hesla, tokeny, API klice ani soukroma rodinna data.
- Pokud jsou v pracovnim stromu cizi rozpracovane zmeny, nebrat je do commitu
  bez samostatne kontroly.
