# MMTX: příběhová hotspot aplikace pro Matýska

## Aktuální stav

- 2026-10-28 14:45 CET: Automatické soví audio je zrušené a opravené Pages vydání dokončené do 30d3c58be7aee89d1003864a0c8b0335fe8e20f7. Sdílený workflow nemá denní cron, TTS krok ani Python/TTS instalaci; běžná místní rutina už soví generátor nevolá. Historická média, CSV, přehrávač a explicitní ruční nástroje zachované.
- Terra p+n 6b2cea8ea2f983ae95be21cb287ee2e4 completed, push/deployment confirmed, 2 commity, project-mmtx → github_pages. Plná publikační brána 2260 PASS / 472,6 s; předtím místní plná brána 2260 PASS (511,838 s unit část), 43 cílených testů a YAML kontrola PASS. Chráněné služby beze změny podle účtenky.
- Pages workflow 40699075925 success, deployment 7387046778 pro přesný head. Adamova jedna kontrola: GitHub/main shodné 0/0 před následným výsledkovým zápisem; veřejné HTTP 200 a přesné bajty 13/13 zdrojů scény 6 i napojení scény 5. HTML SHA-256 f538f932e84b00eea2b817ea11610b7e407e2650c8885711b41bab628788b719. Veřejná scéna https://belisarius-mila.github.io/PythonMF/scene06_lake_arrival/ .
- Původní účtenka eab22667 zůstává historické attention/confirmed push/uncertain deployment; nebyla změněná ani automaticky opakovaná. Na původní pokyn „Terra p+n“ a navazující zrušení sovího audia navázalo nové předání nového opraveného commitu. Caller účtenku převzal, returned_to_adam=false není důvodem retry.
- Scéna 6 je veřejný pracovní náhled hlavní cesty bez options: 72 EN/CZ replik, čtyři ilustrace a setkání s Daisy/Freddiem/Dotty/Olliem. Její vlastní řečové audio stále pouze 2/144, 142 chybí; hlasy nenahrazené. Statické obrazy a krátká syntetická melodie; browser/Safari/iPhone a lidský poslech NEOVĚŘENO.
- 2026-10-28 15:58 CET: Místně doplněná obvyklá zkratka v levém dolním rohu scény 5 → scéna 6, také před audio bránou. Stejná plocha 16%×24% jako v předchozích scénách, min. 44 px, přístupný odkaz a fokus; při otevřeném slovníčku skrytá. Dveře po dokončení zůstávají. Obě kopie shodné, 71 MMTX testů PASS / 2,262 s; nová zkratka zatím nepublikovaná.
- Další krok: samostatné MMTX p+n pro novou rohovou zkratku; nynější veřejnou scénu 6 lze otevřít přímo přes její URL nebo po dokončení pětky dveřmi. Hlasy scény 6 zůstávají 2/144 a fyzická přejímka otevřená.


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
