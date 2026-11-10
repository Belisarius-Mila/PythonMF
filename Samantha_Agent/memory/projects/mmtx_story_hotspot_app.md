# MMTX: příběhová hotspot aplikace pro Matýska

## Aktuální stav

- 2026-11-10 21:36 CET: Benjiho opravy 01/02/03/031/04 jsou vydané na Pages ab123bb6. Terra job 27d6be4c4435a3fa50f12a059ddf0d8e completed, push/deploy confirmed, gate3457 PASS / 597,8 s; Pages run 42896378127 / deployment 7693545647. Veřejných 327/327 aktuálních souborů byte/SHA přesných (10 529 491 B), pět nových WebP použitých, deset starých odstraněno z obou zdrojových složek. Čtyři staré URL HTTP404; staré freddie_jump.webp vrací HTTP503, jeho 404 není potvrzené a p+n se kvůli tomu neopakuje. Main/origin aligned, čistý, 0 čekajících commitů; oba profily aligned/čisté, chráněné služby beze změny. Pět PNG nahrazených v Downloads. Závěrečný Data receipt je pouze místní pro další balíček.

- 2026-11-10 21:20 CET: Main převzal přesný obrazový balíček Data e903dc7a nad čistým 19703fdb. Deset původních WebP odstraněno, deset nových v obou složkách; katalog/HTML/cache verze a dvě stávající testové reference aktualizované. Jeden předchozí interiérový receipt commit zůstává v čekajícím GitHub balíčku. Výslovně schválené Terra p+n bude jediné submit_release(wait=True), request data-mmtx-benji-upright-e903dc7a-20261110-v1, project-mmtx → GitHub Pages; tento přípravný zápis ještě nepotvrzuje skutečný job, push ani deployment.

- 2026-11-10 21:19 CET: Na Mílův výslovný pokyn opraven Benji v obrazech 01/02/03/031/04: vzpřímený postoj, dvě přední a dvě zadní končetiny. Pět image_gen editací vizuálně ověřených, nové _benji_v2.webp v obou složkách; deset původních WebP smazáno, pět PNG nahrazeno v Downloads. 319 ostatních veřejných souborů včetně 288 MP3 beze změny; 40 cílených testů a statická brána OK, HTTP8/8 přesné, Safari ukázalo opravenou čtyřku. P+n Terrou současně výslovně schválené, dosud v tomto checkpointu neprovedené. Reporty mmtx_scene06_benji_upright_20261110.md, assets JSON a prompts MD.

- 2026-11-10 20:35 CET: Slovníček i rozcestník 1–6 jsou vydané na GitHub Pages: main e867c165, Terra job 2394a9c62db8603de3108a4bfee600a4 completed, push/deployment confirmed. Plná publikační brána 3457 PASS / 576,2 s, Pages run 42886285641 / deployment 7692193075. Nezávislá veřejná kontrola 330/330 souborů přesná, 10 851 277 B; skutečné Safari otevřelo veřejnou nabídku všech šesti scén. Main čistý a aligned s origin, 0 čekajících commitů; oba profily čisté a aligned. Chráněné služby beze změny. Závěrečný zápis je pouze místní Data receipt pro další balíček, žádné opakování p+n.

- 2026-11-10 20:21 CET: Míla výslovně zadal vše předat k p+n Terře. Main převzal pouze slovníček b62c4aa8 a rozcestník 376ae421 z Datovy oddělené větve; dva již hotové commity interiéru  ba2f9bbc a 448d2902 zůstávají součástí celého čekajícího GitHub balíčku. Cíl je project-mmtx → GitHub Pages, centrální Terra 6.1/high. Nová účtenka vznikne jedním submit_release(wait=True), request data-mmtx-dictionary-selector-376ae421-20261110-v1; tento přípravný zápis ještě nepotvrzuje předání, push ani deployment.

- 2026-11-10: Tlačítko Cesta k jezeru nyní otevírá modální výběr scén 1–6. Jednička spouští původní mýtinu přímo, 2–6 vedou na vlastní stránky scén; křížek/Escape zavře nabídku. Lokální změna navazuje na slovníček b62c4aa8, obě rozšíření dosud bez nového p+n. 49 cílených testů a rychlá statická brána OK; Safari: čitelná nabídka, proklik 1 a 6, návrat a Escape. Všech pět cílových HTML i tři vstupní soubory přesné přes lokální HTTP a mirror. Fyzický iPhone zatím neověřený.

- 2026-11-10: Lokálně doplněný závěrečný slovníček nové šestky: ikona knihy až po poslední replice desátého obrazu, v režimu s češtinou až po EN i CS. 77 nových hesel a spojení, dvousloupcové posuvné karty, stejné tři režimy češtiny jako příběh. Zavření/Escape zastaví řeč a vrátí příběh, Again ikonu znovu skryje.
- Novost se ověřuje proti dialogům, anglickým pokynům a slovníčkům scén 1–5: 450 úseků, 191 známých lemmat, deset souborů bajtově shodných s publikovaným f7a4ab58. Výslovné mapování tvarů (trees→tree, coming→come, better→good), bez vlastních jmen a osobních/přivlastňovacích zájmen. Každé heslo má doložený výskyt v šestce; JSON audit je `reports/mmtx_scene06_dictionary_audit_20261110.json`.
- 154 slovníčkových MP3 (77 EN Andrew + 77 CS Vlasta, −10 %), z toho 20 přesně shodných CS převzatých z VocabularyEN a 134 nových Azure požadavků / 4964 SSML znaků z limitu 5000. Žádný retry ani změna starých podkladů. Šestka nyní má 288 MP3. 167 dřívějších materiálů a deset dřívějších účtenek beze změny, lokální HTTP 327/327 přesné.
- 74 cílených testů PASS; samostatné JS kontroly nových přístupných názvů a chyby anglického slovíčka také PASS. Celý příběh, 77 EN→CS karet, hranice odemknutí, textové režimy, chyby/nový klik, stop, Escape, historie a Again ověřené. Plná místní brána slovníčku: 2989 testů OK (5 SKIP), 625,637 s; rychlá statická brána také OK. Skutečné Safari dokončilo obraz 10 / 6/6, zobrazilo ikonu knihy a otevřelo čitelný posuvný dvousloupcový seznam. Kliknutí na beautiful načetlo EN i CS MP3 (HTTP 200 ve správném pořadí). Fyzický iPhone a Mílova jazyková/hlasová přejímka zůstávají otevřené.
- Poslední doložené publikované MMTX je f7a4ab58 bez tohoto nového slovníčku: Terra job 0de6f2870dbe4d325b61522f6510e6d1 completed, push+deployment confirmed, publikační gate 3441 PASS, dřívější veřejná kontrola 173/173 přesná. Tento vývoj hlavní checkout ani produkci nemění; nové p+n nebylo zadané.
- Data zůstává na data/parallel-20261104, současný slovníček tvoří vlastní lokální checkpoint navazující na cd37aa9a. Willovo WIP i historie zachované, servisní 06c34051 nepřebírat podruhé. Další krok: Mílova přejímka a případné nové vydání podle samostatného pokynu. Report `reports/mmtx_scene06_dictionary_20261110.md`.

## Stav

Nový směr anglické hry pro Matýska byl oddělen od `anglictina_matysek_V3.py`.

Bylo rozhodnuto:

- V3 nechat beze změny,
- novou aplikaci stavět jako samostatný soubor:

```text
MatysekANJ/MMTX.py
```

## Cíl

Cílem `MMTX.py` je vytvořit příběhovou scénu, kde dítě nevybírá položky z menu, ale kliká na objekty přímo v obrázku.

Stejné objekty mohou mít různé chování podle režimu:

- v režimu barev houba řekne barvu,
- v režimu čísel houba dostane číslici a přehraje se číslo,
- později v příběhovém režimu může objekt spustit část příběhu nebo úkol.

## Důležité poznatky

Pygame na tento typ aplikace stačí.

Není potřeba nový framework.

Technický princip:

- jeden hlavní obrázek jako pozadí,
- nad ním seznam klikacích zón,
- každá zóna má ID, barvu, souřadnice a případná data,
- aktuální režim určuje, co kliknutí udělá.

Příklad hotspotu:

```python
{
    "id": "orange_mushroom_big",
    "rect": (760, 210, 170, 120),
    "color_word": "orange",
    "number_value": 3,
}
```

Později bylo rozhodnuto, že pro přesnější klikání v režimu čísel mají být místo hrubých obdélníků použity menší elipsy.

## Rozhodnutí

### Režim Barvy

V `MMTX.py` vznikl režim barev.

Používá obrázek:

```text
MatysekANJ/NumCol1.JPG
```

Klikací skupiny hub:

- Red
- Blue
- Green
- Orange

Po kliknutí:

- přehraje se anglické slovo,
- kliknutá oblast se zvýrazní,
- na chvíli se zobrazí anglický název barvy.

### Režim Čísla

Byl doplněn druhý režim `Cisla`.

Původní logika:

- každá konkrétní houba měla pevně přiřazené číslo.

To bylo změněno, protože Míla chtěl přirozenější chování:

- první kliknutá houba dané barvy dostane 1,
- další nová houba stejné barvy dostane 2,
- další dostane 3,
- pokud se klikne znovu na už očíslovanou houbu, zopakuje se její existující číslo.

Příklad:

- klik na libovolnou zelenou houbu jako první: zobrazí 1, přehraje `one`,
- klik na další zelenou houbu: zobrazí 2, přehraje `two`,
- klik na další: zobrazí 3.

Toto chování je důležité zachovat.

### Geometrie hotspotů

Geometrie byla opakovaně laděna.

Problém:

- obdélníkové nebo velké kruhové plochy byly nepřesné,
- číslice se kreslily na nevhodná místa,
- klikací zóny neodpovídaly kloboukům hub.

Úpravy:

- hotspot umí zvlášť klikací oblast a `label_center`,
- číslice se kreslí na vlastní kotevní body,
- v režimu čísel se používají menší elipsy,
- klikací oblasti jsou menší a přesnější.

Geometrie může stále vyžadovat ruční doladění podle reálného klikání v okně.

## Otevřené otázky

- Doladit hotspoty skoro po pixelu podle skutečného obrázku.
- Rozhodnout, jak odstranit nebo schovat horní přepínače a nahradit je příběhovým ovládáním.
- Přidat třetí režim typu úkol:
  - `Find blue`
  - `Find three`
- Přidat další příběhové scény nebo objekty.
- Rozhodnout, zda sova, pes, batoh nebo jiný objekt bude sloužit jako příběhový průvodce.
- Připravit další obrázky ve stejném stylu.

## Další kroky pro Codex

Před prací číst:

- `MatysekANJ/MMTX.py`
- `MatysekANJ/PROJECT_HANDOFF_MMTX.md`, pokud existuje
- `MatysekANJ/MMTX_STRUCTURE_PLAN.md`, pokud existuje
- tento memory soubor

Pravidla:

- Neplést si `MMTX.py` s `anglictina_matysek_V3.py`.
- V3 neupravovat, pokud Míla výslovně neřekne.
- Hlavní nová aplikace je `MMTX.py`.
- Udržet technickou jednoduchost.
- Preferovat jeden obraz, hotspoty a režimy před mnoha obrazovkami.
- Při úpravě čísel zachovat dynamickou logiku číslování podle pořadí kliknutí v rámci barvy.
- Při práci s hotspoty dávat pozor na přesnost a oddělit klikací oblast od pozice labelu.

Po změnách ověřit alespoň:

```bash
python3 -m py_compile MatysekANJ/MMTX.py
```

A headless pygame start, pokud je to možné.

## Zdroj

Souhrn ChatGPT/Codex konverzace k nové aplikaci `MMTX.py`, příběhové scéně s houbami, režimu barev, režimu čísel, hotspotům, geometrii klikacích oblastí a dynamickému číslování hub.

## Web MMTX - ForestSchool 2026-05-26

Ve webové verzi MMTX je rozpracovaná nová funkcionalita `forestSchool`:

- hlavní produkční soubory jsou `docs/index.html`, `docs/script_intro_v2.js`, `docs/styles_intro_v2.css`,
- mirror je `MatysekANJ/web_mmtx/`,
- nové assety jsou `ForestSchool1.PNG` a `audio/czech/forest_school_help_cz.mp3` v obou složkách,
- scéna jde otevřít přímo přes `?scene=forestSchool`,
- po pěti správných barvách v `houseBunny` hra přejde do `forestSchool`,
- `forestSchool` je YES/NO cvičení: sova vykouzlí předmět, zeptá se anglicky `Is this a ...?`, dítě volí `YES` nebo `NO`,
- první pětka předmětů je `ball`, `book`, `apple`, `car`, `house`,
- po úpravě 2026-05-26 začíná `forestSchool` krátkým demo ántré: Bunny jednou odpoví špatně `Yes, it is.`, Benji pak správně `No, it isn't.`, skóre se během dema neplní, sova řekne `Will you try?` a teprve pak začíná Matýskovo odpovídání,
- Bunny a Benji v demu mají lokální anglická MP3, aby nepřebírali hlas sovy,
- Matýskovy předměty se vybírají z promíchané fronty bez opakování, takže se v pětikolovém běhu vystřídají všechny položky,
- odměny jsou zobrazené jako malé mochomůrky posunuté víc vpravo, aby méně kryly sovu,
- kouzlení má paprsek z hůlky směrem k předmětu; případně doladit `left`/`top`/`rotate` ve `.forest-school-wand-beam`,
- předměty jsou napojené jako PNG assety v `assets/forest_school_*.png`; `book`, `apple`, `car` a `house` byly 2026-05-26 znovu vygenerované AI workflow ve stylu `PictNew` a převedené na průhledné 1254x1254 PNG,
- za správné odpovědi přibývá pět odměnových koleček, špatná odpověď zopakuje stejnou otázku,
- česká nápověda je přes tlačítko mikrofonu a přehrává lokální MP3; viditelný text používá `klikni ... no`, audio kvůli výslovnosti používá fonetické `klikňi ... nou`.
- lokální kandidáti na dalších 40 předmětů jsou v `data/forest_school_object_candidates_20260526.txt`; root `.gitignore` ignoruje `Samantha_Agent/data/*`, takže tento seznam je zatím lokální pracovní podklad, pokud nebude explicitně force-addnutý.

Ověřeno 2026-05-26:

- `node --check ../docs/script_intro_v2.js` prošel,
- `docs/` a `MatysekANJ/web_mmtx/` měly stejný JS/CSS,
- lokální server `python3 -m http.server 8011` v `docs/` vracel `index.html`, `script_intro_v2.js`, `styles_intro_v2.css`, `ForestSchool1.PNG`, českou nápovědu i demo MP3 přes HTTP 200.

Další krok:

- ručně otevřít `http://127.0.0.1:8011/index.html?scene=forestSchool` a ověřit poslední vizuální umístění mochomůrek, paprsku, tlačítek a audia v reálném prohlížeči.

## Web MMTX - Forest Journey Scene 3 2026-06-30

Treti produkcni webova scena Forest Journey je zalozena jako samostatny modul:

```text
docs/scene03_journey_to_the_lake/
MatysekANJ/web_mmtx/scene03_journey_to_the_lake/
```

Scena navazuje ze `Scene 2 - Sunny's Lost Nuts`: dokoncovaci bublina
`Next: Journey to the Lake` ve scene 2 otevre novy modul.

Obrazove faze:

- `journey_lake_3a.png` - rozcesti pod dubem,
- `journey_lake_3b.png` - havran radi z vetve,
- `journey_lake_3c.png` - kun na ceste pred statkem,
- `journey_lake_3d.png` - Benji mluvi s konem,
- `journey_lake_3e.png` - prazdne vedro u pumpy,
- `journey_lake_3f.png` - Sunny a Bruno pumpuji vodu.

Interakcni beaty:

- klik na havrana spusti radu jit vlevo,
- klik na levou cestu pokracuje ke statku; prava cesta jen jemne vrati zpet,
- u pumpy Matysek hleda, kdo vi jak ziskat vodu,
- spatne kliky na Bunny/Benji/Bruno/Sunny jsou neutralni,
- klik na Fionu spusti reseni, pumpovani a finalni odmenu.

Nova slovni zasoba: `left`, `right`, `way`, `bears`, `scared`, `friendly`,
`dog`, `careful`, `water`, `jump`, `push`.

Ověřeno 2026-06-30:

- vsech sest PNG ma rozmer 1672 x 941,
- `node --check` prosel pro scene 2 i scene 3,
- lokalni server `python3 -m http.server 8011` v `docs/` vracel novy modul,
  JS, CSS a vsech sest PNG pres HTTP 200,
- mirror `docs/scene03_journey_to_the_lake/` a
  `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/` je shodny.

Další krok:

- historicky bod z 2026-06-30 je splneny; aktualni stav sceny 3 je nize v
  sekcich po rucnim retestu a publikaci.

## Web MMTX - Forest Journey voice lock 2026-06-30

Mila po poslechu starsi PTKL To Be / To Have castingove palety rozhodl pro
rychlejsi produkcni MP3 generovani pouzit hotove Edge Neural hlasy pro vetsinu
MMTX postav. Zdrojova paleta byla historicky v commitu `8200d58` a docasne byla
vytažena pro poslech na Plochu jako `ptkl_voice_casting_8200d58`.

Aktualni zamceni pro nove Forest Journey MP3:

| Postava | Hlas | Puvod v castingu | Poznamka |
| --- | --- | --- | --- |
| Bunny | `en-US-AnaNeural` | `cast_b_child_plus_clear`, Kate sample | Mila ho bere jako jasny Bunny kandidat. |
| Sunny | `en-US-MichelleNeural` | `cast_selected_ptkl`, Lucy | Novy Sunny lock misto narocneho lokalniho F5 generovani. |
| Benji | `en-US-BrianNeural` / korekce Scene 3: `en-US-AndrewNeural` | `cast_selected_ptkl`, Tom; dodatecny Scene 3 retest | Brian byl vybran pri castingu, ale ve Scene 3 pusobil prilis brucive / jako Bruno, proto je v teto scene nahrazen Andrewem. |
| Fiona | `en-US-JennyNeural` | `cast_selected_ptkl`, Kate | Novy Fiona lock. |
| Bruno | puvodni brucivy hlas | Forest Journey F5/Onyx reference | Bruno zustava jedina vyjimka se starym brucivym charakterem. |

Prakticky dopad:

- pro nove dialogy scen 2+3 nejdrive generovat MP3 pres Edge TTS podle tohoto
  locku, protoze je to radove rychlejsi nez lokalni F5-TTS na Macu Intel,
- F5 workflow drzet jako zalozni nebo specialni cestu pro Bruna a pripadne
  finalni precizni recast,
- pred hromadnym prepisem produkcniho audia udelat malou poslechovou sadu pro
  sceny 2+3 a az po Milove potvrzeni ji napojit do `docs/` i mirroru.

Nasazeni 2026-06-30:

- Mila rozhodl risknout prime nasazeni novych hlasu do Scene 3.
- V `docs/scene03_journey_to_the_lake/audio/english/` a mirroru je
  vygenerovano 60 anglickych MP3 pro puvodni sadu anglickych dialogu, UI instrukci,
  napovedy a slovnicek.
- `script.js` preferuje MP3 pred `speechSynthesis`; kdyz soubor chybi nebo nejde
  prehrat, scenar zustava funkcni pres fallback.
- Doplnena oprava po Milove hlášení, ze nektere anglicke MP3 se nectou: puvodne
  mely MP3 jen Bunny, Sunny, Benji a Fiona; nyni maji MP3 i Bruno, havran, kun,
  skupinove vety, UI instrukce a slovnicek.
- Ceske napovedy a preklady zustavaji pres fallback.
- Overeno tehdy: `node --check` prosel, kontrola proti `script.js` hlasila
  `required=60 all_mp3=60 missing=0 extra=0`, vsech 60 MP3 vraci pres lokalni
  server HTTP 200 a mirror Scene 3 je shodny s `docs`.

Dodatecna oprava 2026-07-01:

- `journey_lake_3a.png` byl opakovane pregenerovan, protoze Benji v prvni
  obrazove fazi porad pusobil jako sestinohy. Finalni nasazena verze
  `20260701fix8` drzi rozmer 1672 x 941 a Benji je kresleny tak, aby ctyri
  nohy byly vizualne jednoznacne.
- Kruhová sipka ve Scene 3 uz neopakuje automaticky celou scenu; po kliknuti
  znovu spusti aktualni obrazovou fazi od jejiho zacatku a je dostupna i behem
  prehravani.
- Benjiho Edge MP3 byly ve Scene 3 preobsazene z `en-US-BrianNeural` na
  `en-US-AndrewNeural`, protoze prvni replika pusobila jako Bruno. Bunnyho
  repliky jsou znovu vygenerovane jako `en-US-AnaNeural` a Brunovy repliky
  jsou prepnute z Edge `Guy` na lokalni hlubsi hlas `Daniel`.
- Havrani ceske citoslovce je aktualne `Krá krá`, hotspot havrana je mensi,
  hotspot leve cesty je mimo Benjiho, pred prechodem ke studni je pridany
  pulzujici hotspot dveri statku, Fionina bublina u pumpy je posunuta a ceska
  instrukce u hadanky je rozsirena na kliknuti na kamarada.
- `playAudioElement()` ve Scene 3 uz nebere neuspesne `audio.play()` jako
  prehrany anglicky zvuk, takze se prvni obrazova faze nema tise prepnout jen
  na cesky fallback, kdyz prohlizec MP3 nepovoli nebo nestihne.
- `primeHtmlAudio()` a `preloadOpeningAudio()` pri prvnim klepnuti probudi a
  prednactou HTML audio vrstvu pred prvnimi replikami Benji/Bunny; cache verze
  jsou zvednute na `20260701fix8` / `20260701voice5`.
- Slovnicek Scene 3 je rozsireny na 35 polozek vcetne `look`, `path`, `crow`,
  `bad`, `deep`, `valley`, `maybe`, `but`, `horse`, `me too`, `live`,
  `warning`, `farm`, `door`, `stranger`, `come`, `drink`, `pump`, `get`,
  `bucket`, `empty`, `I don't know`, `forest` a `handle`; pro vsechny polozky
  existuje `scene03_ui_*_en.mp3` v `docs/` i mirroru. Audio soubor pro `live`
  je zamerne vygenerovany z vyslovnostniho textu `liv`, aby neznel jako `lajv`.
- Pumpovaci hadanka uz predem nezvyraznuje Fionu jako spravnou odpoved; prompt
  pouziva neutralni ikonu a Fionin hotspot se zvyrazni az po kliknuti.
- Overeno: Scene 3 `docs/` a mirror jsou shodne, `node --check` prosel,
  kontrola proti `script.js` nema chybejici MP3 a
  `journey_lake_3a.png?v=20260701fix8` i nove Benji/Bunny/Bruno MP3 vraci pres
  lokalni server HTTP 200.

Rucni webovy retest 2026-07-01:

- Mila potvrdil, ze Scene 3 je na webu rucne projita; auditni bod "otestovat
  MMTX na webu" je splneny.
- Scena je funkcne v poradku. Zname zbytkove tema je jen kvalita Benjiho hlasu:
  ma rezervy, ale neblokuje pouziti sceny.
- Soucasny stav kodu drzi Benjiho Scene 3 pres pripravené MP3 a fallback vzor
  `andrew|evan|alex|samantha|ava|fable`; nejde o otevrenou chybu typu "Benji
  mluvi Brunem".
- Pri dalsi male MMTX davce lze udelat Benji-only poslechovy recast, ale nema
  se z toho automaticky delat podminka pro dalsi Forest Journey scenu.

## Web MMTX - Harry napojen za scénu 3 (2026-08-26)

Aktuální produkční průchod už nepoužívá Harryho scénu pouze jako samostatný
prototyp:

- commit `6418137` napojil dokončení scény 3 na
  `scene04_harry_guard_prototype/index.html`,
- commit `3b97df3` opravil také skrytý rychlý přechod ve scéně 3,
- stejné napojení je v produkčním `docs/` i v mirroru
  `MatysekANJ/web_mmtx/`,
- historické rozhodnutí z 2026-08-12 o samostatném prototypu popisuje jen
  tehdejší stav a po této integraci už není současnou autoritou.

Otevřený krok pro Linux:

- udělat úplnou inventuru všech mluvených řetězců Harryho scény,
- české a další nepokryté systémové čtení nahradit předem připravenými MP3,
- zachovat okamžité lokální přehrávání bez čekání na TTS build,
- po změně ručně projít celý přechod scéna 3 → Harry na Linuxu i Macu.

Obsah projektové paměti byl podle kódu a Git historie dorovnán 2026-08-29;
poslední automatický MMTX checkpoint před tímto dorovnáním byl z 2026-08-25.

### 2026-09-13 18:21 CEST — Jednotná navigace scén 1–5

Hotovo:
- Dveře pokračují do další scény, šipky vlevo nahoře vracejí do předchozí. Návrat ve scénách 4 a 5 funguje i před spuštěním vyprávění.
- Opravený návrat ze scény 2 a nefunkční závěrečné pokračování scény 3; dveře ve scénách 2–4 lze aktivovat klávesnicí.

Rozhodnutí:
- Míla požaduje dveře vpřed a šipku vlevo nahoře zpět a schválil commit, push a nasazení. Zachovat dokončení scény jako podmínku zobrazení dveří.

Další krok:
- Dokončit publikaci a doložit veřejnou verzi.

Navrhované další kroky:
- Další scéna za mostem zůstává budoucím příběhovým rozšířením.

Technický důkaz:
- 63 cílených testů prošlo; 18 skutečných prokliků v Edge ve viewports 1440 × 900 a 390 × 844. Pět návratů a čtyři pokračování pro každou velikost, žádné JS chyby; vizuálně zkontrolované screenshoty dveří.
- Dokončení bylo nastaveno testem kvůli izolaci navigace, nikoli přehráno novým průchodem všech dialogů. Změny v `docs/` a `MatysekANJ/web_mmtx/` jsou shodné.

### 2026-09-13 18:31 CEST — Veřejně ověřená navigace Cesty k jezeru

Hotovo:
- Opravené dveře vpřed a šipky zpět jsou dostupné na veřejném MMTX. Návraty fungují i před spuštěním vyprávění ve scénách 4 a 5.

Rozhodnutí:
- Dokončeno Mílou schválené c+p+n pro navigaci scén 1–5; žádné další příběhové scény nevznikly.

Další krok:
- Běžně používat opravenou navigaci; při ponechané staré kartě stránku obnovit.

Navrhované další kroky:
- Další příběh za scénou 5 zůstává samostatným rozšířením.

Technický důkaz:
- Publikace: commit `0e1906b8578d`, Pages run `34768695626`, deployment `6423781674`; HTTP 200 a byte-shoda všech 10 změněných veřejných souborů.
- Plná brána 1 640/1 640, cílené MMTX testy 63/63; mirror 537/537 souborů shodný. Browser: 18 lokálních návratů/pokračování včetně Enter a dalších 18 skutečných kliknutí na veřejné produkci, vždy desktop 1440 × 900 a mobilní viewport 390 × 844, bez JS chyb.
- Test se soustředil na navigaci a nastavoval dokončený stav; neověřoval znovu celý příběh a fyzický poslech na iPhonu. Následný dokumentační commit nemění nasazené webové soubory.


### 2026-10-28 13:35 CET — Scéna 6: místní pracovní náhled bez volitelných setkání

Hotovo:
- Příchod k jezeru lze místně projít přes čtyři nová setkání až k písničce a zakončení. 72 krátkých replik EN/CZ, velké klikací cíle, Repeat, změna jazyka a napojení na pátou scénu. Čtyři nové ilustrace zachovávají původní postavy; kopie docs/mirror shodné.

Rozhodnutí:
- Míla výslovně schválil scénář vytvořený Terrou 6.1 a zadal stejné Terře jeho naprogramování bez options: vynechané Tilly/Pip/Lulu/Momo a volitelná větvení. Výběr nemění centrální role ani nepovoluje publikaci. Kvůli nedostupné službě nebyl bez potvrzení nahrazen žádný původní hlas.

Další krok:
- Mílův první obrazový/textový průchod místním náhledem a rozhodnutí o chybějících hlasech; bez náhrady dokončit původní audio až po odblokování Edge.

Navrhované další kroky:
- Po doplnění zvuku provést skutečnou hlasovou přejímku celé scény; potom samostatně rozhodnout o případném vydání.

Technický důkaz:
- 71 MMTX testů PASS / 2,384 s; Node kontrola syntaxe a automatický stavový průchod PASS. HTTP 200 a přesná shoda 13/13 zdrojů. Čtyři ilustrace vizuálně zkontrolované, přesné prompty v image_prompts.txt, vestavěný ImageGen.
- Audio pouze 2/144, 142 chybějících: první Edge dávka NoAudioReceived, jediná další sériová zkouška kompatibilního endpointu HTTP 429, pak zastavení. Existující EN000/001 FFmpeg dekódování PASS; --check exit 1 je očekávaná neúplnost. Reprodukovatelný builder chrání text/hlas/rate/SHA-256 a neprovádí automatický retry či přepis.
- Žádný připojený browser, takže Safari/iPhone/proklik i lidský poslech NEOVĚŘENO; konzervativní výpočet geometrie je pouze pomocná kontrola. Statické obrazy nemají všechna navržená komická gesta; písnička je krátká syntetická melodie s postupným světlem bublin. Pracovní checkpoint, bez nového push/nasazení a bez zásahu do Camina.

### 2026-10-28 14:17 CET — Terra p+n: push potvrzený, Pages zablokované sovím audiem

Hotovo:
- Schválené dva commity včetně scény 6 jsou na GitHubu do 5564aec3. Místní pracovní náhled zachovaný; veřejné vydání scény zatím neproběhlo.

Rozhodnutí:
- Míla výslovně zadal „OK, terra p+n“. Jediné registrované submit_release(wait=True) zmrazilo projekt MMTX, oba heads a Terru 6.1/high; bez nativního pomocníka, přepínání modelu nebo retry.

Další krok:
- Vyřešit chybu sdíleného generování sovího audia před novým výslovným publikačním pokusem.

Navrhované další kroky:
- Doplnit 142 řečových stop scény 6 a provést skutečnou obrazovou/hlasovou přejímku; do té doby místní pracovní náhled.

Technický důkaz:
- Účtenka eab22667ea9a7286189f6fc1a1f563e2 attention, push_state=confirmed, deployment_state=uncertain, failure_phase=publish_requested; plná brána 2260 PASS / 481,8 s. GitHub main přesně 5564aec373f4e87c0187bc9a1d2d2f10dc338668 a lokální main 0/0 před tímto zápisem.
- Pages workflow 40694554621 / build-pages 122837760412: Generate and verify today's owl before publication failure/exit20; Edge TTS websocket Invalid response status, upload i deploy skipped. Pro tento head není deployment, veřejná nová scéna HTTP 404. Původní účtenka neměněná, žádná opakovaná publikace.
- Caller účtenku převzal a Adam jednou ověřil GitHub, původní workflow a veřejný stav. returned_to_adam=false neprokazuje automatický portálový návrat. Závěrečné potvrzení protected_services_unchanged v neúspěšné účtence není; dostupný živý Cockpit má code_stamp b90aa847fa54ce76. Bez nového Cockpit deploymentu, zásahu do hlasů scény 6 či souvisejících služeb.

### 2026-10-28 14:24 CET — Zrušení automatického sovího audia

Hotovo:
- V místním kódu je zrušené automatické soví TTS: Pages bez generování, Python/TTS instalace a denního cronu; místní rutina už soví úkol nevolá. Historické soubory i přehrávač zachované.

Rozhodnutí:
- Míla výslovně zadal „Soví audio zruš.“ Sdílený ruční Pages publisher a jeho ochrany zůstávají pro MMTX a další weby, bez závislosti na sovím audiu. Nový publikační pokus tímto krokem spuštěný nebyl.

Další krok:
- Po úspěšné plné bráně a lokálním commitu nový samostatný Terra p+n; původní úspěšný push a neúspěšné vydání se neopakují automaticky.

Navrhované další kroky:
- Odděleně doplnit hlasové stopy scény 6 a udělat fyzickou přejímku.

Technický důkaz:
- 43 cílených testů PASS včetně regrese, že ani při připraveném CSV běžná rutina nezavolá TTS ani nepřepíše app.js. Obě workflow kopie shodné a YAML validní; plná brána 2260 PASS (511,838 s unit část), log cancel_automatic_owl_gate_20261028.log. Žádné soubory smazané, žádná nová řečová síťová generace, žádný nový push/nasazení či restart.

### 2026-10-28 14:45 CET — Soví automatika zrušená a MMTX veřejně nasazené

Hotovo:
- Automatické soví TTS už není součástí běžné místní rutiny ani sdílených Pages. Opravený web je zveřejněný; scéna 6 i přechod ze scény 5 se podávají ve správné verzi. Historické soubory a přehrávač zachované.

Rozhodnutí:
- Adam navázal na Mílův předchozí pokyn Terra p+n a konkrétní opravu „Soví audio zruš.“ Nové předání zmrazilo nový opravený balíček do 30d3c58b; původní neúspěšná účtenka zůstala zachovaná. Žádná změna hlasů scény 6 či centrálních rolí.

Další krok:
- Mílův obrazový/textový průchod veřejnou scénou 6.

Navrhované další kroky:
- Samostatně dokončit 142 řečových stop scény 6 a fyzickou/poslechovou přejímku.

Technický důkaz:
- Účtenka 6b2cea8ea2f983ae95be21cb287ee2e4 completed, push_state/deployment_state=confirmed, Terra 6.1/high, 2 commity do 30d3c58be7aee89d1003864a0c8b0335fe8e20f7. Publikační full gate 2260 PASS/472,6 s, protected_services_unchanged=true. Pages workflow 40699075925 success, deployment 7387046778.
- Jedna Adamova kontrola: GitHub/main 0/0 na vydaném headu před tímto zápisem, HTTP 200 + přesná shoda 13/13 zdrojů. HTML SHA-256 f538f932e84b00eea2b817ea11610b7e407e2650c8885711b41bab628788b719. Nový build pouze Checkout→Configure Pages→Upload→Deploy, bez TTS a bez denního cronu.
- return_channel=caller: terminálový Adam převzal a ověřil; returned_to_adam=false nepotvrzuje automatický portálový návrat a není důvodem retry. Předchozí gate 2260/511,838 s a 43 cílených kontrol/YAML PASS. Řeči scény 6 nadále 2/144 a fyzický browser/poslech NEOVĚŘENO. Následný lokální dokumentační checkpoint.

### 2026-10-28 15:58 CET — Obvyklá levá dolní zkratka ze scény 5 do scény 6, lokálně

Hotovo:
- Doplněný místní odkaz z levého dolního rohu páté scény přímo k jezeru. Funguje i před zahájením dialogu; běžné dokončovací dveře zachované.

Rozhodnutí:
- Míla chtěl otevření nové scény obvyklým kliknutím vlevo dole ve scéně 5. Převzít rozměry stávající zkratky ze scény 4, minimální cíl 44 px a vrstvu nad audio bránou. Při otevřeném slovníčku zkratku skrýt, aby nepřekrývala jeho položky.

Další krok:
- Samostatné p+n MMTX a fyzický proklik rohu scény 5; přímá URL scény 6 je veřejně dostupná už nyní.

Navrhované další kroky:
- Zachované doplnění řečí scény 6 a skutečná přejímka hlavního průchodu.

Technický důkaz:
- Rychlá statická brána PASS. 71 MMTX testů PASS / 2,262 s, odkaz i byteová shoda obou kopií ověřené. CSS má plochu 16%×24%, min. 44 px, z-index 22 nad audio bránou 20 a fokusový rámeček; cache parametr upravený. Skutečný browserový proklik NEOVĚŘENO. Bez nového push/publikace, bez změny audia nebo děje.

### 2026-10-28 19:19 CET — Terra p+n rohové zkratky 5→6 dokončené

Hotovo:
- Veřejná pátá scéna má obvyklou zkratku vlevo dole přímo do šestky, dostupnou i před spuštěním příběhu. Nové HTML a CSS se skutečně podávají, běžné dokončovací dveře zachované.

Rozhodnutí:
- Míla výslovně zadal „ok, terra p+n“. Jedno registrované submit_release(wait=True) předalo přesné dva commity a schválenou Terru 6.1/high. Bez nativního prostředníka, změny rolí či opakování.

Další krok:
- Obnovit veřejnou pětku a přijmout proklik vlevo dole i před audio bránou.

Navrhované další kroky:
- Zachované doplnění vlastních řečových stop šestky a skutečná obrazová/poslechová přejímka.

Technický důkaz:
- Účtenka 46daf0cd2eae60a54363365d9f52a290 completed, push_state/deployment_state=confirmed, dva commity do 46173ef987c345ebf6875c24301f38532471434f. Plná publikační brána 2262 PASS / 466,3 s, protected_services_unchanged=true. Pages workflow 40743712328 success, deployment 7393736182, smoke HTTP 200.
- Adamova jedna kontrola: GitHub/main 0/0 na vydaném headu před zápisem, veřejné 3/3 HTML/CSS zdroje HTTP 200 a přesné bajty. Pětka SHA-256 e96ca0b045dfbfe9f5bc76948baf165174ea652bb9cee4e580dacbf86f4b904e; CSS 3982bedefa5210387d97c16411f972e517dfdf62de18f3147a4eaa3042ec6a79; šestka f538f932e84b00eea2b817ea11610b7e407e2650c8885711b41bab628788b719. Odkaz i verzovaný CSS parametr ověřené.
- Caller účtenku převzal; returned_to_adam=false nepotvrzuje automatický portálový návrat a nevyvolává retry. Fyzický proklik/Safari/iPhone a poslech NEOVĚŘENO. Řeči šestky stále 2/144, zrušené soví TTS se neobnovilo. Bez nového Cockpit deploymentu či zásahu do chráněných služeb. Následný lokální výsledkový zápis pro další balíček.

### 2026-10-30 09:28 CET — Audio šestky: tři nové stopy, poskytovatel dál blokuje dokončení

Hotovo:
- Místní scéna obsahuje pět platných řečových stop místo dvou; úspěšné výsledky jsou zachované i v druhé kopii aplikace.

Rozhodnutí:
- Navázat na Mílův pokyn dokončit audio. Zachovat původní hlasy a tempo; po doloženém 429 neprovádět další automatické pokusy ani hlasovou náhradu.

Další krok:
- Po uvolnění služby doplnit zbývajících 139 stop od CZ 002. Dokončení nyní blokuje externí Microsoft TTS.

Navrhované další kroky:
- Po úplné generaci provést proklik a poslech na Macu/iPhonu; publikaci zadat samostatně.

Technický důkaz:
- 71 MMTX testů PASS; offline kontrola potvrzuje 5/144 a očekávaný exit 1 kvůli 139 chybějícím stopám. MP3 mají odpovídající text/hlas/-10%/SHA-256 a dekódují se. Dvě původní EN stopy zůstaly beze změny.
- První sériový běh přidal CZ 000, CZ 001 a EN 002, potom HTTP 429. Jedno pokračování po pauze s 10s rozestupy opět HTTP 429 bez Retry-After, žádný další síťový pokus. Logy mmtx_scene06_audio_20261030.log a mmtx_scene06_audio_paced_20261030.log. Zdrojový generátor ani společná speech vrstva se neměnily; bez push/nasazení.

### 2026-10-30 10:20 CET — Pokus o pětici: dvě nové stopy, další zastavila chyba 429

Hotovo:
- Zachované dvě nové řečové stopy CZ 002 a EN 003; místní audio nyní 7/144, zbývá 137.

Rozhodnutí:
- Na Mílův pokyn pokračovat v dávkách po pěti, další dávku spustit jen po úspěšné předchozí. Původní hlasy a tempo zachovat. Při HTTP 429 zastavit bez retry.

Další krok:
- Po uvolnění Microsoft TTS navázat od CZ 003. První pětice byla neúplná, další se nespustila.

Navrhované další kroky:
- Po všech 144 stopách ověřit skutečný proklik a poslech; publikace vyžaduje samostatný pokyn.

Technický důkaz:
- 4 cílené testy scény 6 PASS; MP3/vazby/mirror ověřené. Offline --check: 7/144, očekávaný exit 1 pro neúplné audio. Generátor ani společná speech vrstva se neměnily.
- Běh po více než 50min pauze: 10s před novým požadavkem, 30s pauza připravená mezi úspěšnými pěticemi. Dvě úspěšné stopy, potom CZ 003 → HTTP 429 bez Retry-After. Dokončených pětic 0, opakování 0; výsledek a kurzor v logs/mmtx_scene06_batches_20261030_1018_state.log. Bez push/nasazení.

### 2026-10-30 15:55 CET — Devět nových stop v dávkách po pěti, další blokuje 429

Hotovo:
- Místní audio šestky rozšířené ze 7 na 16 stop, zbývá 128. První pětice kompletní, druhá má 4/5; všechny úspěšné výsledky zachované a synchronizované.

Rozhodnutí:
- Na Mílův pokyn pokračovat po pěti. Po více než pěti hodinách od předchozího pokusu použít 30s rozestupy a 60s mezi úspěšnými pěticemi; původní hlasy a tempo zachovat. Při HTTP 429 zastavit.

Další krok:
- Po uvolnění poskytovatele doplnit EN 008 jako poslední stopu rozpracované druhé pětice; teprve po jejím ověření navázat třetí pěticí.

Navrhované další kroky:
- Po kompletních 144 stopách skutečný proklik a poslech; publikaci zadat samostatně.

Technický důkaz:
- 4 cílené testy scény 6 PASS; offline --check ověřil 16/144 a očekávaný exit 1 kvůli neúplnému audiu. Předchozích sedm MP3 zachovaných; obě kopie stejné. Generátor ani společná speech vrstva se neměnily.
- První běh přidal sedm stop, potom EN 007 → ClientConnectorDNSError/gaierror. Čtecí DNS kontrola domény služby i microsoft.com prošla; obnovení zachovalo stav pětic a přidalo EN 007/CZ 007. Následně EN 008 → HTTP 429 bez Retry-After, další dávka se nespustila.
- Průběh a kurzor v logs/mmtx_scene06_batches_20261030_154314_state.log a logs/mmtx_scene06_batches_20261030_155259_state.log. Bez push/nasazení; fyzický poslech/proklik NEOVĚŘENO.

### 2026-11-10 13:35 CET – Boční perspektiva prvního obrázku u jezera

Hotovo: Připravený samostatný obrazový návrh s rozpoznatelnými pěti přáteli z boku a pohledem přes vodu k mrakům.

Rozhodnutí: Na Mílův pokyn zkusit obrázek znovu zůstává zachovaná identita postav a motiv uší tvořených mraky; mění se perspektiva a směr pohledů. Původní publikovaný obrázek se nenahrazuje automaticky.

Další krok: Posoudit návrh; případná výměna aktivního obrázku a nové publikování jsou samostatný další krok.

Navrhované další kroky: Žádné nové.

Technický důkaz: Vestavěný image_gen, jedna varianta 1672 × 941, PNG 2948769 B. Vizuálně ověřen počet pěti postav, jejich boční natočení, pohled k jezeru a mrakům; původní arrival.webp má nadále původní SHA-256. PNG, prompt a účtenka jsou v místním private imagegen adresáři mimo Git.

### 2026-11-10 15:22 CET – Čekající úklid původního obrázku publikovaný

Hotovo: Starý první obrázek u jezera už není veřejně dostupný. Scény 1–5 a Logan zůstávají zachované; nový boční návrh zůstává bezpečně uložený mimo produkční průchod.

Rozhodnutí: Míla po čtecí obnově výslovně zadal p+n a schválil dočasné odložení přesně tří nesouvisejících source změn s následným vrácením. Provedeno jediné registrované vydání čtyř čekajících commitů přes centrálně schválenou Terru 6.1/high.

Další krok: Navazovat na souběžný Data vývoj samostatně; tuto větev automaticky neintegrovat ani nepřepisovat.

Navrhované další kroky: Žádné nové.

Technický důkaz: Účtenka `19622ad4cec58c0ce7762c8afa311ea6`, head `51a2cabe`, Pages run `42832718423` / deployment `7684562278`, push/deployment confirmed. Plná brána 3402 testů PASS / 49 SKIP; veřejně 158 URL HTTP 404 a 54 zachovaných souborů s přesnými bajty. Source WIP vrácený včetně shodných otisků obou draftů; tři nové PNG shodné. Data head `c87f6064` zachovaný, jeho souběžně změněný WIP touto relací nedotčený. Doklady mimo Git v `data/private/mmtx/release_51a2cabe_20261110/`; výsledkový zápis místně pro příští balíček, bez opakování p+n. Fyzická přejímka neověřená.


### 2026-11-10 15:17 CET — Nová šestka, první obraz a anglické MP3

Hotovo:
- První obraz The Lake má přijatý boční pohled a sedm schválených replik s pevným anglickým zvukem. Next, Repeat, Again, čitelné bubliny nad vodou a návrat k mostu.

Rozhodnutí:
- Míla zadal vývoj pouze prvního obrazu, anglické MP3, Terra p+n a následné napojení z pětky pro produkční zkoušku. Další hotové ilustrace tím nejsou implementované.

Další krok:
- Převzít konkrétní ověřený commit do uvolněného kanonického main a provést autorizované p+n.

Navrhované další kroky:
- Po vydání připojit konec pětky a fyzicky ověřit přechod a hlasy na Mílově zařízení.

Technický důkaz:
- 35 cílených testů PASS, syntaxe/statická brána PASS, 7/7 MP3 dekódovaných, oba mirrory a 13 HTTP souborů přesné. Azure 7 unikátních požadavků / 410 znaků, bez retry. Lokální Safari: první věta i stav 7/7. Plná brána 2960 testů OK (5 SKIP); publikace nové šestky dosud neprovedena. Podrobnosti a otisky v `reports/mmtx_scene06_opening_20261110.md`.


### 2026-11-10 15:24 CET — Připravené napojení pětky a publikační blokátor

Hotovo:
- Po dokončení pětky je v Datově pracovní kopii viditelný vstup To the lake! do prvního obrazu nové šestky. Úprava vychází z Willova již schváleného ukončení staré šestky a zachovává odstranění neviditelné zkratky; obě kopie stejné.

Rozhodnutí:
- Mílovo zadání zahrnuje Terra p+n i produkční propojení. První obraz je ve vývojovém commitu `1c40b6db`; samotné propojení má samostatný následný commit, aby šlo dodržet pořadí živého vydání.

Další krok:
- Míla upřesní, zda hotové commity do kanonického main převezme Will, nebo Data. Zdrojové neuzavřené změny vlastníka ani profilový stav se neobcházejí.

Navrhované další kroky:
- Po převzetí: registrované Terra submit_release(wait=True), přesné potvrzení Pages, potom vydat propojení a zkontrolovat skutečné veřejné bajty a vstup z pětky. Fyzický iPhone a hlasy převezme Míla.

Technický důkaz:
- 37 cílených testů PASS; nově i skutečný cíl odkazu, jeho umístění až v původně skrytém dokončení a shoda HTML/CSS obou mirrorů. Plná místní brána 2960 OK (5 SKIP) zůstává důkazem nezměněné infrastruktury; nová markup změna byla ověřená cíleně. Žádné nové modelové/audio volání a žádná publikace této šestky. Registrovaný deploy audit: source main není čistý; batch audit: pracovní prostředí není připravené.


### 2026-11-10 15:43 CET — Data přebírá integraci a první p+n

Hotovo:
- Oba hotové vývojové kroky se integrují do kanonického main se zachováním Willovy i Datovy historie. První obraz má všech sedm EN MP3, přijatý boční pohled a napojení po dokončení mostu.

Rozhodnutí:
- Míla oznámil, že Will nepracuje, a výslovně zadal předat p+n nyní Terře a vyčistit repo; potom připojit obraz 2. Nesouvisející WIP se zachovává, nikoli zahazuje: 3 přesné změny ve stashi `550024e17da59eb258556f5d3f0979650d5a4d30`, scénáře navíc v soukromé záloze s otisky.

Další krok:
- Cíleně ověřit integrovaný kód, dokončit převzetí a bezpečné zarovnání čistých profilů; spustit jedno registrované p+n s plnou bránou a přesným headem.

Navrhované další kroky:
- Ověřit veřejné soubory nové šestky a vstup z pětky. Poté připojit Ollieho, druhý obraz a jeho EN dialogy.

Technický důkaz:
- Převzetí řeší očekávané modify/delete konflikty pouze nových HTML/JS/CSS a zachovává obě historie paměti. Vybrané WIP má ověřené přesné bajty ve stashi i privátní záloze. Žádné další TTS nebo modelové volání zatím neproběhlo. Samostatné testy prvního obrazu a propojení jsou přidané do trvalé plné brány. Publikační výsledek bude mít novou vlastní účtenku.


### 2026-11-10 16:05 CET — Ollieho obraz připojený lokálně

Hotovo:
- První a druhý obraz propojuje Next picture. Ollie nabízí rybu a deset anglických replik odkáže přátele ke staré lodi a chatrči. Čitelné dialogy nekrývají postavy ani podběrák; na úzkém displeji jsou pod obrazem.

Rozhodnutí:
- Míla výslovně zadal druhý obraz po předání prvního p+n. Aby se dlouhé čekání na Pages nepřeneslo do vývoje, druhý obraz vzniká odděleně v Datově worktree; zmrazený první main ani balíček se nemění. Žádné nové p+n pro druhý obraz se bez dalšího pokynu neodesílá.

Další krok:
- Dokončit plnou místní bránu druhého obrazu a konkrétní commit; programově převzít stejnou účtenku prvního vydání.

Navrhované další kroky:
- Po potvrzení prvního vydání zkontrolovat veřejné soubory a vstup z mostu. Druhý obraz pak samostatně převzít s Mílou a případně vydat na jeho pokyn.

Technický důkaz:
- 57 cílených kontrol PASS, všech 17 MP3 dekódovaných, 27 HTTP souborů přesné; Safari druhý obraz a Bunny 10/10 + Again. Nových 10 Azure požadavků / 635 znaků, původní první audio/data/obraz i raw účtenka zachované. Plná místní brána zatím běží. První release job `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deploy requested; Pages run `42839271179` zatím běží. Viz nový report.


### 2026-11-10 16:11 CET — Uložený dřívější WIP úklid staré šestky v Datově větvi

Hotovo:
- Git evidence Datovy větve zaznamenává již dříve provedené a schválené odstranění původní šestky: 311 dávno chybějících souborů a odpojené staré Azure workflow/registrace. Při tomto kroku se žádné další soubory z disku neodstraňují.

Rozhodnutí:
- Míla nyní zadal vyčistit repo. Všechny evidované absence byly předem porovnané s kanonickým main a omezené na starou šestku; původní potvrzené odstranění zůstává zachované. Tento servisní commit se do main znovu nepřebírá, protože tam je stejný úklid už vydaný. Nový druhý obraz dostane vlastní následující commit.

Další krok:
- Uložit ověřený druhý obraz samostatně a potvrdit čistý stav Datovy větve.

Navrhované další kroky:
- Pro neúspěšné první nasazení čeká Mílovo rozhodnutí o jednom novém pokusu; původní účtenka `4b261f77c13a77e845684bbbd90cc876` zůstává attention, push confirmed, deployment uncertain.

Technický důkaz:
- Přesně 311 absencí mimo nové názvy médií, všechny v rozsahu staré šestky a již nepřítomné na main. Konkrétní místní plán má seznam cest a původní head; plná brána aktuálního pracovního stavu 2972 testů OK (5 SKIP), 57 cílených kontrol PASS. Žádný reset, mazání dalších dat ani přepis historie.


### 2026-11-10 16:12 CET — Druhý obraz ověřený, první nasazení Pages zrušené po timeoutu

Hotovo:
- Lokálně funguje příběhové spojení prvních dvou obrazů a všech 17 anglických MP3. Druhý obraz má schválený obrázek, přesných 10 replik a vlastní neměnné audio podklady.

Rozhodnutí:
- Druhý obraz je oddělený následující vývoj, není součástí prvního zmrazeného p+n. První p+n se neopakuje automaticky; Míla má konkrétní otázku na jediný nový pokus stejného fee535e5. Starý WIP Data je zaznamenaný samostatně v `06c34051` a do main se znovu nepřebírá. Willovo nesouvisející WIP zůstává zachované.

Další krok:
- Uložit konkrétní nový commit druhého obrazu a potvrdit čisté pracovní kopie; poté počkat na Mílovo rozhodnutí o novém pokusu nasazení.

Navrhované další kroky:
- Druhý obraz samostatně projít na Mílově zařízení a případně vydat po jeho pokynu. Produkční Pages po zrušeném nasazení zatím není přejímka nové šestky.

Technický důkaz:
- Plná místní brána 2972 OK (5 SKIP), 665,420 s unit; 57 cílených kontrol PASS, 17/17 MP3 decode, 27 HTTP souborů přesné. Skutečné Safari: obraz Ollie, Bunny 10/10, Again, viditelné postavy a podběrák. První Azure podklady beze změny. První Terra receipt `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deployment uncertain; GitHub Pages run `42839271179` po 600000 ms syncing_files deployment zrušil. Po zrušení HTML 404. Výsledkový report zachovává první neúspěšný běh bez přepisu.


### 2026-11-10 16:33 CET — Třetí část: Freddieho skok a rozhovor ve vodě

Hotovo:
- Po Olliem pokračuje třetí část s osmi přesnými replikami, dvěma schválenými ilustracemi 03/031 a osmi novými anglickými MP3. Obraz se mění před Bunnyho otázkou 4/8; čítač pokračuje do 8/8, Repeat zachová aktuální ilustraci.

Rozhodnutí:
- Míla zadal pokračovat třetí částí. Nejde o schválení nového pokusu nasazení. Vývoj zůstává v Datově worktree; Willův main a zaparkované WIP se nemění. Historická první release účtenka zůstává beze změny. Další části se nyní neimplementují.

Technický důkaz:
- 59 cílených kontrol PASS a po finálním CSS 21 relevantních PASS. Přechod 2 → 3, 03 → 031, Repeat po chybě, pozdní callbacky a restart ověřené v Node VM. Dekódování 25/25, shodné mirrory a 39 HTTP souborů s přesnými bajty. Plná brána třetí části: 2974 testů OK (5 SKIP), 620,446 s unit.
- 8 unikátních Azure požadavků, 458 SSML znaků z limitu 500, −10 %, Freddie Guy / Dotty Jenny. 23 starších podkladů a dvě původní raw účtenky SHA-256 beze změny. Žádné opakování placeného požadavku. Report `reports/mmtx_scene06_picture3_20261110.md`.

Rizika a další krok:
- Obě nové ilustrace a hlasy čekají na místní přejímku na Mílově zařízení včetně fyzického iPhonu. Obrazy 2+3 nejsou publikované tímto krokem; případné vydání vyžaduje samostatné zadání. Další krok je přejímka nebo další vývoj podle Míly.


### 2026-11-10 16:52 CET — Dokončená šestá scéna až k Benjiho plánu

Hotovo:
- Nová šestka má celý průchod částmi 1–10, 11 schválených ilustrací a 67 anglických MP3. Tichý devátý obraz je samostatný ručně ovládaný krok bez řeči; závěr používá opravenou mapu. Dialogy nových částí jsou pod obrázkem, takže nezakrývají postavy ani mapu.

Rozhodnutí:
- Míla výslovně zadal pokračovat až do konce všemi zbývajícími částmi šestky. Scéna 7 není součástí tohoto zadání. Jde o místní dokončení; nové p+n ani opakování nejistého prvního nasazení tímto krokem neproběhlo.

Další krok:
- Místně převzít celý příběh a nové hlasy na Mílově zařízení.

Navrhované další kroky:
- Po samostatném pokynu integrovat věcné commity částí 2, 3 a dokončení 4–10 a předat registrované p+n. Servisní úklid 06c34051 nepřebírat podruhé; Willovo WIP ponechat zachované.

Technický důkaz:
- 52 cílených kontrol PASS, přesné otisky schválených dialogů, všech 67 MP3 dekódovatelných, shodné mirrory a 101 HTTP souborů s přesnými bajty. Plná brána dokončené šestky: 2978 testů OK (5 SKIP), 444,963 s unit. Node VM ověřil celý příběh, nulové Audio během ticha, Repeat/chyby, historii i závěrečný Again.
- 42 jednorázových Azure požadavků / 2570 SSML znaků z limitu 4000; 35 starších podkladů a 3 raw účtenky SHA-256 beze změny. Safari vizuální testy produkčního HTML/CSS prošly pro mapu, ticho a 390px rozložení; fyzický iPhone a hlasová přejímka otevřené. Report `reports/mmtx_scene06_complete_20261110.md`.


### 2026-11-10 18:19 CET — Viditelné pokračování od čtvrtého obrazu

Hotovo:
- Obrázek, dialog a Next od části 4 sdílejí výšku okna; ovládání zůstává viditelné. Přímý odkaz #picture=4 umožní místní přejímku od chatrče při zachování zvukové brány. Safari živý průchod už dosáhl večeře, Bruno 5/7.

Rozhodnutí:
- Oprava řeší Mílovo skutečné hlášení o zastavení na začátku čtvrtého obrazu. Dosavadní headless návaznost nebyla důkaz viditelnosti ovládání. Média a texty zůstávají zachované; žádná nová syntéza ani p+n.

Další krok:
- Mílova přejímka dalšího průchodu v otevřeném náhledu.

Navrhované další kroky:
- Při samostatně zadané integraci přebrat tento opravný commit navíc po dca70ad9, pak registrované p+n. Fyzický iPhone zůstává k ověření.

Technický důkaz:
- 53 cílených testů PASS: všech 67 replik, ticho, historie, callbacky, přímé vstupy a bezpečné fallbacky bez automatického zvuku. Skutečné Safari: obraz 4 / 1/7 se všemi ovládacími prvky viditelnými, následně obraz 5 / 5/7. Statická brána PASS; dřívější plná 2978 OK není opakovaná přejímka této opravy. Report `reports/mmtx_scene06_viewport_fix_20261110.md`.


### 2026-11-10 18:32 CET — Volitelný český text a čtení v celé nové šestce

Hotovo:
- Všech 67 vět ve všech deseti obrazech šestky má český překlad a samostatnou českou MP3. Přepínač nabízí vypnuto, text a text + hlas; čeština zní po angličtině a ovládání zůstává uvnitř okna. Devátý obraz zůstává tichý ve všech režimech.

Rozhodnutí:
- Míla zadal postupné zapnutí českého textu a pak i čtení. Rozsah tohoto checkpointu je deset obrazů právě dokončené šestky; doplňující otázka na starší hlavní scény zůstala bez odpovědi. České nahrávky používají stávající Azure hlas Vlasta a −10 %. Nové p+n tímto krokem neproběhlo.

Další krok:
- Mílova přejímka českých překladů, hlasu a přepínače v otevřeném náhledu.

Navrhované další kroky:
- Po samostatném zadání integrovat věcné commity včetně tohoto českého rozšíření a předat registrované p+n. Podle odpovědi případně sjednotit i starší hlavní scény 1–5.

Technický důkaz:
- 58 cílených testů PASS, Node VM 67 EN→CS dvojic a ticho, přepínání za běhu, chyby, stop, historie a úložiště. Dekódování 134/134, shodné mirrory, lokální HTTP 170/170 přesné. Plná místní brána českého rozšíření 2984 OK (5 SKIP), 570,813 s unit.
- 67 jednorázových CS požadavků / 3977 SSML znaků z limitu 4000. 98 původních podkladů a 9 raw EN účtenek SHA-256 beze změny. Safari ukázalo čitelný dvojjazyčný text a režim s hlasem, protokol doložil české MP3 v živém průchodu. Fyzický iPhone a výslovné jazykové/hlasové hodnocení otevřené. Report `reports/mmtx_scene06_czech_20261110.md`.


### 2026-11-10 18:40 CET — Skrytý přechod z posledního obrazu pětky a schválené p+n

Hotovo:
- Velké průhledné pole vlevo dole na dokončeném rozlučkovém obrazu pětky vede do celé nové šestky. Před závěrem, během řeči/animace a při slovníčku je nepřístupné. České režimy všech deseti obrazů jsou hotové.

Rozhodnutí:
- Míla výslovně autorizoval propojení a následné p+n celého balíčku Terrou. Integrovat jen MMTX, zachovat Willovo WIP i jeho historické projektové zápisy. Existující jeden čekající main commit a459920b je dokumentace dřívějšího vydaného úklidu interiéru, bez nové změny soukromých podkladů.

Další krok:
- Integrovat ověřený lokální balíček do čistého main a zavolat jediný registrovaný submit_release(wait=True).

Navrhované další kroky:
- Převzít přesnou účtenku jobu a veřejně ověřit nový head, šestku i odkaz z pětky. Fyzickou přejímku provede Míla.

Technický důkaz:
- Plná místní brána českého rozšíření 2984 OK (5 SKIP), 570,813 s unit; poslední cílená sada 70 PASS včetně rohu a pětky. Publikační worker ověří celý přesný main znovu. 134 MP3 decode, 170 HTTP souborů přesné, 98 původních podkladů a 9 EN účtenek beze změny. Kanonický živý audit main a459920b / origin 748cec00, ready a 2 připravené profily.


### 2026-11-10 18:42 CET — Integrovaná celá nová šestka a skrytý roh před Terra p+n

Hotovo:
- Main obsahuje celou šestku, 67 EN + 67 CS MP3, třípolohovou češtinu a skrytý přechod z posledního obrazu pětky. Převzaté jsou jen cesty MMTX a jeho zápisy; původní Willovy chronologické záznamy zůstaly celé zachované.

Rozhodnutí:
- Míla výslovně zadal p+n celého balíčku Terrou. Zdroj Data 51af4d56 se integruje věcně do jednoho main commitu; servisní 06c34051 se nepřebírá podruhé. Balíček zahrne i jeden dříve čekající dokumentační commit a459920b.

Další krok:
- Zarovnat čisté profily, přepnout registrovaný kontext na project-mmtx a jednou spustit submit_release(wait=True) pro přesný integrovaný head.

Navrhované další kroky:
- Převzít konečnou účtenku a ověřit veřejné soubory; fyzická přejímka zůstává Mílovi.

Technický důkaz:
- Přímo nad integrovaným main 70 cílených testů PASS a rychlá statická brána PASS. Dřívější Data plná brána češtiny 2984 OK (5 SKIP); publikační worker ověří přesný main znovu. Před zápisem 346 konkrétních MMTX cest, žádná nová smazání ani nesouvisející kód. Report `reports/mmtx_scene06_full_release_20261110.md`.


### 2026-11-10 18:45 CET — Terra převzala přesný integrovaný balíček

Hotovo:
- Data vývoj je uložený v 51af4d56, celý věcný MMTX balíček integrovaný do main f7a4ab58. Oba čisté profily jsou zarovnané. Registrovaný kontext byl obnoven a přepnut na project-mmtx; jediný předaný job má ID 0de6f2870dbe4d325b61522f6510e6d1.

Rozhodnutí:
- Výslovně schválené p+n běží přes submit_release(wait=True), request data-mmtx-full-51af4d56-20261110-v1. Audit zmrazil main f7a4ab58, origin 748cec00, 2 commity, GitHub Pages, Terra 6.1/high a schválený otisk centrální politiky. Původní job se nepřepisuje ani neopakuje.

Další krok:
- Programově převzít konečnou účtenku stejného jobu.

Navrhované další kroky:
- Ověřit veřejné soubory přesného headu a Mílovu fyzickou přejímku.

Technický důkaz:
- Main 70 cílených a statická brána PASS; Data plná brána 2984 OK (5 SKIP). Registrovaný audit ready a oba profily aligned na f7a4ab58. Vydání je nyní předané, push a deployment zatím nejsou tímto zápisem potvrzené.


### 2026-11-10 18:59 CET — Terra p+n dokončené, veřejné soubory přesně ověřené

Hotovo:
- Pětka je propojená tajným velkým polem na posledním obrazu s celou šestkou. Všech deset obrazů, 11 ilustrací a 67 EN + 67 CS MP3 včetně tří českých režimů je veřejně dostupných. Ověřeno 173/173 přesných veřejných souborů.

Rozhodnutí:
- Schválené předání proběhlo jednou Terrou přes registrované submit_release(wait=True). Main po vydání zůstává f7a4ab58 a čistý; závěrečný zápis je místní Data receipt, bez nového publikování či změny vydaného headu.

Další krok:
- Mílova přejímka hry na jeho zařízeních.

Navrhované další kroky:
- Fyzicky vyzkoušet tajný roh po dokončení pětky, přepínač text/čtení i iPhone. Další vývoj podle Míly.

Technický důkaz:
- Job 0de6f2870dbe4d325b61522f6510e6d1 completed; push a deployment confirmed. Terra 6.1/high, plná brána 3441 PASS / 634,3 s. Pages run 42869959321, deployment 7689928869, exact head f7a4ab58, HTTP 200, chráněné služby beze změny. Nezávislých 173/173 HTTP souborů byte/SHA shodných (9 012 903 B). GitHub audit aligned, main 0 čekajících commitů a 2 profily ready. Reporty mmtx_scene06_full_release_20261110.md/json a mmtx_scene06_public_verification_20261110.json.


### 2026-11-10 19:41 CET — Slovníček nových slov na konci desátého obrazu

Hotovo:
- Na konci šestky je lokálně ikona knihy s 77 novými hesly a spojeními. Karty mají EN/CZ zvuk a respektují všechny tři české režimy. Odemknutí nastává až po poslední větě, včetně její češtiny; ticho devítky, příběh i vazba z pětky zůstávají zachované.

Rozhodnutí:
- Míla zadal analog slovníčku pětky pouze pro slova dosud nepoužitá v předchozích pěti scénách. Audit zahrnuje dialogy, pokyny i slovníčky a explicitně mapuje tvary, nikoli pouze rozdíl hotových seznamů. Nové p+n nezadal; změna zůstává lokální v Data.

Další krok:
- Převzít Mílovo hodnocení místního slovníčku; případné nové p+n pouze podle samostatného pokynu.

Navrhované další kroky:
- Mílova přejímka hesel a hlasů; po samostatném pokynu integrovat a předat p+n.

Technický důkaz:
- 74 cílených kontrol PASS, nové izolované JS kontroly také PASS. Deset zdrojů předchozích scén ověřených proti f7a4ab58, 450 úseků a 191 lemmat; každé nové heslo doložené v šestce. 154 MP3 dekódovaných, 134 nových unikátních požadavků / 4964 SSML znaků a 20 převzatých přesných CS nahrávek. 167 starých materiálů a deset účtenek beze změny; HTTP 327/327 přesné. Plná místní brána slovníčku: 2989 testů OK (5 SKIP), 625,637 s; rychlá statická brána také OK. Reporty mmtx_scene06_dictionary_20261110.md a mmtx_scene06_dictionary_audit_20261110.json.

### 2026-11-10 20:14 CET — Výběr šesti scén Cesty k jezeru

Hotovo: Tlačítko Cesta k jezeru otevírá přehledné okno s čísly 1–6. Každé číslo vede do odpovídající scény; okno lze zavřít křížkem nebo Escape. Nabídka zůstala otevřená v místním Safari pro Mílu.

Rozhodnutí: Zachovaná struktura příběhu: první scéna běží přímo v úvodní stránce, další mají vlastní stránky. Jde o místní vývoj, nové p+n nebylo zadané ani spuštěné.

Další krok: Mílova přejímka rozcestníku a slovníčku; případné společné vydání až podle samostatného pokynu.

Navrhované další kroky: Žádné nové.

Technický důkaz: 49 cílených testů OK / 16,975 s, rychlá statická brána OK. Safari zobrazilo všech šest čísel a prošlo spuštění první i šesté scény, návrat a zavření Escape. Tři vstupní HTML/JS/CSS a všech pět cílových HTML přesné přes lokální HTTP a mirror. Verze CSS/JS aktualizované proti cache. Žádné nové TTS ani jiné placené volání; hlavní checkout nedotčený. Fyzický iPhone otevřený.

### 2026-11-10 20:21 CET — Připravené společné vydání slovníčku a rozcestníku

Hotovo: Do main je převzatý slovníček 77 nových hesel se 154 MP3 a nabídka scén 1–6. Obě webové kopie jsou shodné s ověřenou Datovou větví. Historie MMTX a nesouvisející práce na main zůstaly zachované.

Rozhodnutí: Míla výslovně autorizoval vše předat k p+n Terře. Jediná registrovaná cesta submit_release(wait=True), project-mmtx → GitHub Pages; dva čekající interiérové commity se zachovají v celém GitHub balíčku. Běžící Cockpit se tímto vydáním nerestartuje.

Další krok: Po kontrolách uložit integrovaný main, zarovnat pouze čisté profily a jednou předat přesný commit; převzít konečnou účtenku téhož jobu a ověřit veřejné bajty.

Navrhované další kroky: Mílovo proklikání veřejné nabídky a slovníčku; fyzická přejímka iPhonu zůstává otevřená.

Technický důkaz: Data 376ae421 a b62c4aa8 zachované v odděleném worktree, main výchozí 448d2902 čistý a bez divergence. Dřívější plná místní brána slovníčku 2989 OK (5 SKIP); rychlá integrační brána OK. Nové audio ani placené pokusy se nespouštějí. Request data-mmtx-dictionary-selector-376ae421-20261110-v1 je nový; staré účtenky se nepřepisují.

### 2026-11-10 20:35 CET — Slovníček a rozcestník vydané Terrou

Hotovo: Veřejná Cesta k jezeru nabízí scény 1–6 a na konci šestky slovníček 77 nových hesel s EN/CZ zvukem. Safari na skutečné produkční URL otevřelo nabídku; zůstala připravená pro Mílu.

Rozhodnutí: Schválené předání proběhlo jednou přes submit_release(wait=True), request data-mmtx-dictionary-selector-376ae421-20261110-v1. Terra 6.1/high převzala tři commity do e867c165 včetně dřívějšího interiérového balíčku. P+n cílilo na Pages, bez restartu Cockpitu nebo nových TTS/modelových pokusů mimo jediné převzetí Terrou.

Další krok: Mílova přejímka veřejné nabídky a slovníčku.

Navrhované další kroky: Fyzický iPhone a výslovná jazyková/hlasová přejímka zůstávají otevřené.

Technický důkaz: Účtenka 2394a9c62db8603de3108a4bfee600a4 completed, push a deployment confirmed, plná publikační brána 3457 PASS / 576,2 s. Pages run 42886285641, deployment 7692193075, HTTP 200 a exact main e867c165; chráněné služby beze změny. Nezávisle 330 veřejných souborů bajtově i SHA-256 shodných (10 851 277 B). Main/origin aligned, 0 čekajících commitů, dva profily aligned a čisté. Returned_to_adam=false je portálový příznak; nativní Adam účtenku převzal jednou zde, nejde o důvod retry. Reporty mmtx_dictionary_selector_release_20261110.md/json a mmtx_dictionary_selector_public_20261110.json.

### 2026-11-10 21:19 CET — Benji správně na zadních v pěti prvních ilustracích

Hotovo: Benji v obrazech 01, 02, 03, 031 a 04 stojí vzpřímeně se dvěma předními a dvěma zadními končetinami. Ve dvojce jsou odstraněné přebytečné nohy. Zachované pohledy i děj, včetně skoku a samostatného rozhovoru ve vodě. Původní obrázky jsou nahrazené v aplikaci i Downloads.

Rozhodnutí: Míla výslovně zadal překreslit pět obrázků, staré smazat a vše poslat Terře k p+n. Nové soubory mají verzi v názvu proti cache; žádná změna dialogů nebo audií.

Další krok: Uložit Data checkpoint a integrovat přesný věcný rozsah do čistého main, poté jedno autorizované registrované Terra p+n.

Navrhované další kroky: Veřejné potvrzení nových obrázků a odstranění starých; fyzická iPhone přejímka zůstává otevřená.

Technický důkaz: Pět samostatných vestavěných image_gen editací, čtyři končetiny vizuálně ověřené v každém úplném obrázku. 40 cílených testů OK / 24,849 s, rychlá statická brána OK, obě kopie shodné, 319 ostatních podkladů včetně 288 MP3 zachované a HTTP8/8 přesné. Safari screenshot opravované čtyřky. Assets JSON eviduje původní a nové SHA-256; prompty a výstupy mají vlastní report.

### 2026-11-10 21:20 CET — Integrované opravené Benjiho ilustrace pro Terra p+n

Hotovo: Main má pět vizuálně ověřených oprav Benjiho a obě stejné webové kopie. Původních deset WebP cest je odstraněných. Datova vývojová větev a všechny jiné hotové změny zůstávají zachované.

Rozhodnutí: Mílou výslovně schválené p+n směřuje na project-mmtx / GitHub Pages. Jediný request data-mmtx-benji-upright-e903dc7a-20261110-v1, bez nových obrazových nebo TTS pokusů.

Další krok: Po místních kontrolách uložit main commit, zarovnat pouze čisté profily, registrovaně zvolit MMTX a jednou předat Terře.

Navrhované další kroky: Veřejné porovnání nových obrázků a HTTP404 starých cest; fyzický iPhone později převezme Míla.

Technický důkaz: Data e903dc7a, main před integrací 19703fdb čistý, žádná divergence. Data 40 cílených OK a statická brána OK; 319 nedotčených veřejných souborů včetně 288 MP3 shodných. Main 40 cílených testů OK / 31,873 s a rychlá statická brána OK; plná publikace je povinnou částí workeru.

### 2026-11-10 21:36 CET — Opravené Benjiho ilustrace publikované Terrou

Hotovo: Obrazy 01, 02, 03, 031 a 04 veřejně používají opraveného Benjiho na zadních se dvěma předními a dvěma zadními končetinami. Pět PNG nahradilo původní v Downloads. Ve vydaném zdroji jsou všechny staré WebP smazané a aplikace načítá nové názvy.

Rozhodnutí: Mílou schválené p+n proběhlo jednou přes registrované submit_release(wait=True), request data-mmtx-benji-upright-e903dc7a-20261110-v1. Žádný další obrazový/TTS pokus ani opakované vydání. Před předáním se pouze obnovilo připojení existujícího pracovního kontextu nad již reachable App Serverem, nikoli restart služby.

Další krok: Mílova vizuální přejímka veřejné opravené šestky.

Navrhované další kroky: Při příští potřebě ověřit HTTP404 původního freddie_jump.webp, nyní po omezených čtecích kontrolách vrací HTTP503. Fyzická iPhone přejímka zůstává otevřená.

Technický důkaz: Terra 6.1/high, job 27d6be4c4435a3fa50f12a059ddf0d8e completed, push/deployment confirmed, dva commity do ab123bb6, plná brána 3457 PASS / 597,8 s. Pages run 42896378127 / deployment 7693545647, HTTP smoke200 a protected_services_unchanged=true. Všech 327 aktuálních veřejných souborů přesných, 10 529 491 B, 319 ostatních materiálů včetně 288 MP3 zachované. Ze starých URL čtyři potvrzené 404, jedna neověřená kvůli503; v Git tree a obou složkách deset starých cest neexistuje. Místní Safari před vydáním obraz04 správně zobrazilo; po vydání Safari GUI nebylo dostupné (cgWindowNotFound), nepředstírat produkční proklik. Main/origin aligned a oba profily čisté/aligned, 0 pending main commitů. Native caller účtenku převzal jednou, returned_to_adam=false není retry.
