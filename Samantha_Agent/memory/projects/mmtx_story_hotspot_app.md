# MMTX: příběhová hotspot aplikace pro Matýska

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
