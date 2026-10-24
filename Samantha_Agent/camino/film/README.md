# Camino — filmová střižna


## Aktuální stav — 24. 10. 2026

V `0a18db30` nasazené ovládání **Koš projektů a žádosti z iPhonu · 7 dní**: kontrola rozsahu,
přesné potvrzení, obnovení a přehled dokončení iPhonu. **Smazat celý film…**
odstraní po lhůtě film se všemi revizemi, hlasy a exporty; originály zůstanou.
Žádost o smazání celé cesty zahaj na iPhonu. Samostatná služba je nyní
na schématu 4 a telefon aktualizovaný na build 21 bez odinstalace; fyzický
tok koše dosud nepřijatý. [Aktualizace](../docs/CLIENT_21_SERVICE_UPGRADE_REPORT.md).
[Rozsah, ověření a nutné samostatné vydání](../docs/PROJECT_TRASH_REPORT.md).

Nový místní krok odděluje **původní text z iPhonu** od **pracovního textu**
a přidává historii nahrávek, obnovitelný koš i import MP3/WAV.
[Postup a ověření pracovního cyklu](../docs/COMMENTARY_WORKFLOW_REPORT.md).

Místní nový vývoj doplňuje **Cesta nebo dovolená** před výběrem dne a filmu.
Záznamy, revize a exporty se drží vybrané cesty i při shodném datu/názvu.
Před přepnutím dokonči uložení střihu. Výběr je vlastní každé kartě.
[Ověření a hranice vydání](../docs/MULTI_PROJECT_ACCESS_REPORT.md).

Místně je také přepracované **Text a komentář** přímo u fotografie:
statický panel, plynulý text nebo uložené místní české čtení.
[Nový postup, ověření a hranice vydání](../docs/PHOTO_TEXT_COMMENT_REPORT.md).

Následující vydání panelu Texty a komentáře je dřívější funkční základ:


Střižna je dostupná v Cockpitu jako **Film Camino**. Vydání `d8d16f1b`
zahrnuje panel **Texty a komentáře**; Luna doložila push, nasazení,
plnou bránu PASS (2 174 testů v účtence) a kontroly po restartu 5/5.
Účtenka `4b1ed8c23af048f133e00971d0ad1038`. Nový panel byl po nasazení
ověřený na HTTP, jeho fyzický proklik a poslech uživatelem zatím čekají.
Samostatné nové render větve karet a poslechových kopií nemají vlastní
funkční přejímku. [Podrobný report](../docs/FILM_TEXT_AUDIO_REPORT.md).

## Běžný postup

### 1. Vyber film a připrav podklady

Obnov stránku Cockpitu, otevři **Film Camino**, vyber **Cesta nebo dovolená**
a v **Moje filmy** vyber uložený film pro tuto cestu. Jiný den lze vybrat z Mac dat. Nový projekt ulož až po
skutečném dokončení přenosů a vědomém potvrzení konečnosti dat tohoto dne
na Macu. Prázdná fronta telefonu ani samotný seznam dnů úplnost nedokládají.
Při chybě originálů, účtenek nebo soukromí se projekt nevytvoří.

Každý uložený jednodenní film má vlastní revize a exporty. Přepnutí projektu
čeká na dokončení uložení rozpracovaného střihu. Vícedenní film P2-F zatím
není součástí editoru.

### 2. Uprav obraz

- Záběry řaď šipkami Dříve/Později; výslovné vyřazení mění jen film.
- U fotografie uprav délku a titulek. **Otevřít fotografii** zobrazí v nové
  kartě odvozený obraz bez původních EXIF/GPS; nevytváří se render záběru.
  Oprava větších fotografií přijímá vstupy do 64 Mpx/64 MiB a
  zachovává celý rám. Náhled se přizpůsobí do 4096 × 4096; pracovní kopie
  filmu do 720p/1080p s poměrem stran a případnými pruhy. Originál se nemění.
  Nasazení této opravy je samostatné: [rozsah a ověření](../docs/LARGE_PHOTO_REPORT.md).
- Video je výchozí celé. **Otevřít video pro střih** připraví chráněný náhled;
  vyber **Tady začít / Tady skončit**, případně dolaď číselné časy a použij
  **Přehrát výběr**. Tato volba nevyrábí nový filmový export.
- **Vytvořit náhled záběru s titulkem** vytvoří u videa i fotografie dílčí render,
  v němž je výsledný titulek i umístěný komentář.

Platné úpravy se automaticky ukládají do nové revize. Před přepnutím nebo
zavřením vyčkej na potvrzení **Uložena revize**. Při výpadku spojení zůstává
koncept v otevřené kartě; není to trvalá záloha po jejím násilném zavření.

### 3. Přidej text přímo k fotografii

U fotografie otevři **Text a komentář**. Můžeš napsat vlastní text nebo
převzít celý přijatý text deníku; tlačítko **Předat celý text na fotografii**
je také dole v nabídce přijatých textů. Filmový text se ukládá průběžně,
původní deník zůstává zachovaný. Titulek záběru má samostatný limit 140 znaků;
text fotografie dovolí až 6000 znaků. Pracovní pole je ručně upravitelné;
původní načtený text je vedle zvlášť, pouze pro čtení. Tlačítko
**Obnovit pracovní text z originálu** jej kdykoliv vrátí.

Vyber **Statický text přes fotografii**, **Plynulý text v okně**, případně
zatím **Pouze uložit text**. Dlouhý statický text vyžaduje výběr úryvku;
pro celý text zvol plynulý režim a **Prodloužit pro celý text / čtení**.
Délka se sama nemění. Nejvýše 300 sekund na fotografii; delší obsah vědomě
zkrať. Náhled odmítne nečitelný či příliš rychlý text s vysvětlením u fotografie.

**Náhled fotografie s textem a zvukem** ukáže skutečný filmový výsledek.
Samostatné textové karty mezi obrazy zůstávají dole odděleně: každá do
1000 znaků, nejvýše 32 karet, výchozí délka 5 sekund. Nejde o text přes fotografii.

### 4. Připoj hlas k fotografii

- Pro čtení filmového textu zvol **Komentář — čtení nebo MP3/WAV**,
  **Vytvořit místní čtení**, poslechni si zvuk a až pak **Použít čtení ve filmu**.
  Čte český hlas Zuzana místně na Macu. Namluvení nic neodesílá do externí TTS.
- Vytvořený zvuk zůstává uložený pro poslech i po obnovení stránky. Jeho
  vytvoření jej samo nezařadí do filmu. Změna textu vyžaduje nové čtení;
  předchozí pokus se zachová v **Uložené pokusy a nahrávky** se svým textem.
- **Importovat MP3/WAV k fotografii** přijme hotový komentář nebo vlastní
  namluvení (do 64 MiB a 300 s). Po importu jej poslechni a výslovně použij.
- **Smazat pokus do koše** odstraní pokus z běžného přehledu; v koši jej
  lze obnovit. Texty a starší filmy zůstanou. Koš neuvolňuje místo na disku.
- U fotografie můžeš také vybrat původní nahrávku, poslechnout a připojit ji.
  Ruční začátek a konec nastav v **Poslechnout / vybrat úsek** u komentářů dole.
- Hlas musí vejít do vlastní fotografie. **Prodloužit fotografii pro nahrávku**
  či **Prodloužit pro celý text / čtení** mění délku teprve po tvém kliknutí.
  Překrývající se hlasy server odmítne; nenásleduje automatické useknutí.
- Nové komentáře se přesouvají se svou fotografií. Starší komentář s ručně
  nastaveným absolutním časem zůstává beze změny; lze jej nově připojit.

Hlasitost nahrávky a zvuk videa během komentáře (výchozí poměr 0,2) doladíš
dole. Souběh ověř krátkým renderovaným náhledem. Neprovádí se automatický
přepis původních nahrávek ani AI výběr obsahu.

### 5. Vyrob náhled a MP4

Po potvrzeném uložení zvol **Náhled úseku** pro krátkou kontrolu, **Vytvořit
náhled 720p** nebo **Vytvořit MP4 1080p**. Náhled a finále vycházejí ze stejné
uložené revize; starý export zůstane označený svou revizí. Fronta přežije
zavření stránky i restart Cockpitu. Přerušený export opakuj vědomě podle
stavu fronty; před opakováním ztracené odpovědi nejprve obnov přehled.

Hotový výstup přehraj celý se zvukem. Tlačítko **Otevřít / uložit MP4**
slouží k soukromému stažení, nic veřejně nepublikuje. Vybranou nepotřebnou
filmovou variantu lze po přesném potvrzení **Smazat natrvalo**; dialog ukáže
rozsah a velikost. Originály a uložené střihy se tím nemažou. Otevřený
přehrávač nebo stažené kopie mohou dál držet místo či vlastní kopii dat.

## Když něco chybí

- **Text:** zkontroluj správný den, vědomé Uložit v deníku a přijetí textu na
  Macu; rozepsaný koncept ani přenesená fotografie nejsou důkazem přenosu
  textu. Při auditu 23. 10. neměl 6. říjen přijatý text, měl však pět hlasových
  nabídek. Jde o datovaný audit, nikoli pravidlo pro budoucí stav dne.
- **Komentář:** musí patřit do povolených uzavřených podkladů a mít ověřené
  médium. Samotná přítomnost nabídky ještě neznamená zařazení do filmu.
- **Projekt nebo export přestal být dostupný:** obnov ověření zdrojů a
  aktuálního soukromí. Starý odkaz ani náhled neobcházejí nové omezení.
- **Dlouhý text nebo hlas:** délku a obsah uprav vědomě; cílová stopáž je
  automaticky nezkrátí. Podrobná [technická omezení](../docs/P2CD_EDITOR_MP4_REPORT.md).

## Technické a historické podklady

Následující etapy popisují jednotlivé vrstvy a původní zkoušky. Současné
uživatelské ovládání je uvedené výše, provozní důkaz je v přesné účtence.

## P2-A: syntetický prototyp

P2-A zůstává syntetický. Jeho renderer není připojený k owner archivu,
iPhonu ani Vieweru a nevytváří návrhy nad skutečným dnem.

Registrovaný workflow `camino_p2a_synthetic_film` spouští ze Samantha_Agent:

```bash
.venv/bin/python -m scripts.camino_p2a_film --execute
```

Bez `--execute` pouze vypíše rozsah. Každý experiment vytvoří nový adresář
v `data/private/camino/p2a/`, uloží zdroje a `project-r1.json`, znovu načte
projekt a sestaví náhled 720p i finále 1080p. Staré běhy nepřepisuje ani
neuklízí. `experiment.json` a účtenky exportů obsahují měření a kontrolní
součty. `review.html` je místní přehrávač, nikoli mobilní editor.

Struktura:
- `project.py`: formát v1, validace, kontrola zdrojů a neměnné uložení revize.
- `media.py`: místní FFmpeg/FFprobe a české titulky přes Pillow/Arial.
- `render.py`: časová osa → MP4, kontrola celého souboru a měření disku.
- `synthetic.py`: generátor obrázku, videí a testovací řeči macOS Zuzana.
- `scripts/camino_p2a_film.py`: jednorázový experiment a místní přehled výsledků.
- `tests/test_camino_film.py`: smlouva, chyby a skutečné dekódování obrazu/zvuku.

Používá existující Python prostředí, Pillow, FFmpeg/FFprobe a místní hlas
macOS; nic neinstaluje ani neodesílá. Syntetická řeč je pouze kalibrační
vzorek, nikoli funkce generovaného vyprávění či náhrada autorova hlasu.

Limity P2-A: nejvýše 120 sekund, 16 zdrojů/obrazových položek, 8 nepřekrývajících
se komentářů, SDR a rozměry zdrojů do 3840 pixelů. HDR/BT.2020 se odmítá.
Knihovní renderer přijímá pouze tento prototypový formát; jeho příznaky
nenahrazují produkční ověření úplnosti a oprávnění z P2-B.

## P2-B: uzavření skutečného dne

`closed_day.py` přijímá důkaz z iPhonu pouze přes soukromé owner API
`POST /api/v1/film/closed-days`. Telefon v obrazovce **Uložení a přenosy**
vědomě vybere 6. 10. 2026, po nové inventuře zkontroluje prázdnou frontu,
neaktivní přenosy a SHA-256 místních originálů. Mac ve stejném požadavku
porovná identitu serveru, epochu, kurzor, úplný inventář Momentů/revizí a
médií, ověřené účtenky i SHA-256 všech původních souborů. Při nesouladu se
projekt nevytvoří.

Uzavřený manifest a chronologický projekt revize 1 jsou v soukromém
`film-projects/` mimo Git. Obsahují všechny povolené obrazové zdroje dne,
celá videa a samostatný seznam povoleného audia. `owner_only`, skryté a
neznámě povolené zdroje nejsou v návrhu. Originály se nekopírují ani
nepřepisují. `GET /api/v1/film/projects/{id}` po restartu znovu kontroluje
celý inventář, aktuální povolenost a hash zdrojů; změna vyžaduje nové
uzavření. P2-B neprovádí render, editor ani publikování filmu.

Aktuální místní vývoj a oddělený provozní stav jsou v
[P2-B reportu](../docs/P2B_CLOSED_DAY_REPORT.md).

Podrobný důkaz a přejímka: [P2-A report](../docs/P2A_FILM_REPORT.md).

## P2-B z konečné Mac sady v Cockpitu

Po výslovném potvrzení Míly pro 6. 10. je dostupná oddělená varianta
`app/camino_film_workshop.py`: potvrzené konečné Mac vstupy, striktně
read-only SQLite a stejné ověření originálů. Původ je `owner_confirmed_mac`,
nikoli iPhone důkaz; telefonní fronty se nevymýšlejí. Uložení vytváří
samostatné soukromé filmové soubory mimo archiv a Git. Službu ani aplikaci
Camino nemění. Registrovaný create vyžaduje výslovnou konečnost Mac dat.
Cockpit Film Camino zobrazí přehled uloženého dne, celá videa a počty audia;
na samotné uzavření navazuje editor a render popsaný výše. Každý přehled znovu ověřuje povolenost
a SHA-256, neplatný stav staré položky ani počty nevydá.

## P2-C/D: uložený střih a soukromý MP4 export

`app/camino_film_editor.py` váže neměnné revize střihu a frontu exportů na
potvrzený Mac manifest. Cockpit nabízí pořadí, výslovné vyřazení, titulky,
délku foto, ruční in/out videa a původních hlasových částí, hlasitost a
ztišení videa během komentáře. Platné úpravy se automaticky ukládají,
souběžný střih neprojde bez aktuální revize. Originály zůstávají beze změny.

`app/camino_film_render.py` vyrenderuje jednotlivé záběry v pracovních
kopiích, ověří všechna média a znovu prověří zdroje i revizi. Náhled 720p,
dílčí úsek a MP4 1080p jsou v soukromé idempotentní frontě. Neúplný výsledek
se nevydává; každý GET/HEAD/Range kontroluje aktuální povolenost projektu.
MPO foto používá hlavní SDR obraz s EXIF/ICC převodem, HDR video je zatím
odmítnuté. Po přerušení se export opakuje od začátku; staré varianty zůstávají
do jejich výslovného trvalého smazání v editoru.

Registrovaný workflow `camino_film_render` po výslovném zadání spouští:

```bash
.venv/bin/python scripts/camino_film_editor.py render --execute
```

Vytvoří oba profily aktuální uložené revize. Běžící Camino, telefon a síť
nemění. Provozní stav a výsledky jsou v [P2-C/D reportu](../docs/P2CD_EDITOR_MP4_REPORT.md).
