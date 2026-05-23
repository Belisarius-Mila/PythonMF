# Projekt: Webova aplikace Lekarna

Datum zalozeni: 2026-05-20

## Cil

Postavit nad projektem domaci lekarny jednoduchou webovou aplikaci spustitelnou
pres git/GitHub Pages nebo podobny staticky web, aby bylo mozne vybrane informace
z lekarny srozumitelne zprostredkovat Janicce.

## Kontext

Zdrojova evidence je soukroma:

- `data/lekarna/domaci_leky.csv`
- fotky v `data/lekarna/Leky_v_Krabickach/`
- lokalni reporty a zalohy v `data/lekarna/`

`data/lekarna/` je ignorovane v gitu. Plny inventar domaci lekarny se nema
automaticky publikovat.

## Aktualni stav zdroju

Projekt Lekarna ma:

- 56 evidovanych polozek,
- foto import workflow,
- soft-delete workflow pro vyrazeni leku,
- zmensene fotky krabicek,
- doplnene `PIL_Short`, `PIL_Source`, `PIL_Checked_Date` a `PIL_Match_Status`
  pro vsechny radky, vcetne nejistych nebo ne-lekovych polozek.

Kanonicky PIL workflow:

- `technical/lekarna_pil_short_workflow.md`

## Navrzeny smer webu

Web nema byt lekarske doporuceni. Ma byt rodinny orientacni prehled:

- co doma je,
- k cemu to obecne patri,
- kde je to ulozene, pokud Mila potvrdi, ze se tato informace muze ukazat,
- expirace / zda je potreba fyzicky overit,
- kratky `PIL_Short`,
- stav overeni `PIL_Match_Status`,
- zdroj `PIL_Source` pro dohledani.

## Navrzeny UX workflow

Miluv navrh z 2026-05-20:

1. Uvodni stranka ma mit formular s heslem.
2. Po zadani hesla se zobrazi uvodni obraz/fotografie interieru stare lekarny.
3. Na obrazu budou tri klikatelne kovove krabicky:
   - `Pils Jana`
   - `Pils Mila`
   - `Pils Home Store`
4. Klik na `Pils Jana` nebo `Pils Mila` zobrazi seznam leku dane osobni krabicky.
5. Klik na konkretni lek zobrazi detail:
   - fotku krabicky, pokud existuje a je povolena pro dany rezim,
   - pokud fotka neni, zobrazit detail bez fotografie,
   - okno/panel s `PIL_Short`,
   - stav overeni, napr. `overeno_sukl_dlp_pil`, `nejisty_nazev`, `overit obal`.
6. Klik na `Pils Home Store` zobrazi seznam domacich/spolecnych leku a detail stejne
   jako vyse.
7. Na uvodnim obrazu muze byt otaznik. Klik na otaznik otevre formular:
   - "Jake mate potize?"
   - "Co boli?"
8. Po zadani dotazu typu "boli me hlava" web zobrazi relevantni leky podle lokalni
   evidence a kategorii/synonym.
9. Pokud nic nenajde, zobrazi napr. "Nemame doma nic jasne evidovane pro tento dotaz."
10. Pokud dotazu nerozumi, zobrazi napr. "Nerozumim presne. Zkuste dotaz preformulovat
    nebo se poradte s lekarnikem/lekarem; pro obecnou orientaci muzete pouzit ChatGPT."

### Doplnene UX pravidla

- Uvodni heslo nesmi vytvaret falesny pocit skutecne ochrany, pokud jsou data/fotky
  normalne ulozene ve verejnem gitu.
- Na kazde strance/detailu ma byt kratka veta: "Toto je domaci evidence, ne
  doporuceni lecby ani davkovani."
- Detail leku nema zobrazovat davkovaci instrukce jako radu; jen `PIL_Short` a zdroj.
- Osobni krabicky `Pils Jana` a `Pils Mila` povazovat za citlivejsi nez `Pils Home Store`.
- U dotazoveho formulare pouzit jen lokalni filtrovani nad exportem, ne generovat
  lekarske doporuceni.
- U nejistych polozek jasne zobrazit "overit obal" nebo "nejisty nazev".

## Cockpit obraz a audio

Mila dodal obraz:

- `data/lekarna/Lekarna_Cockpit.PNG`

Popis obrazu:

- interier stare lekarny,
- tri hlavni klikatelne krabicky na pultu:
  - `Pils Jana`,
  - `Pils Mila`,
  - `Pils Home Store`,
- vpravo je had jako otaznik; bude slouzit jako hotspot pro dotazovy formular
  "co vas trapi / co boli",
- vpravo dole je samostatny otaznik pro napovedu.

Audio napoveda byla vygenerovana pres projektovy TTS nastroj `../scripts/generate_tts.py`
hlasem `cs-CZ-AntoninNeural`.

Lokalni soubory:

- vstupni CSV: `data/lekarna/tts_help_phrases.csv`
- MP3: `data/lekarna/audio/lekarna_help_intro.mp3`

Text nahravky:

```text
Ahoj, hezky den. Kliknutim otevrite krabicky. Hadi otaznik se zepta, co vas trapi.
```

Poznamka: soubory v `data/lekarna/` jsou soukrome/ignorovane gitem. Pro web bude
potreba pozdeji rozhodnout, zda se obraz a MP3 zkopiruji do verejneho `docs/`
exportu, nebo se budou pouzivat jen v soukromem build/export kroku.

## Cockpit prototyp

Od 2026-05-20 existuje prvni staticky prototyp:

- `docs/lekarna/index.html`
- `docs/lekarna/styles.css`
- `docs/lekarna/app.js`
- `docs/lekarna/assets/lekarna-cockpit.png`
- `docs/lekarna/audio/lekarna-help-intro.mp3`

Funkce prototypu:

- uvodni lehka heslova brana,
- zobrazeni cockpit obrazu,
- klikatelne hotspoty na `Pils Jana`, `Pils Mila`, `Pils Home Store`,
- klikatelny had jako formular "Co vas trapi?",
- klikatelny otaznik pro prehrani MP3 napovedy,
- jemne zlate hover/pulse/shimmer efekty, ktere maji evokovat klikatelnost bez
  tvrdeho ramecku,
- zatim mock seznamy leku a prototyp detailu leku; skutecna data budou napojena az
  po exportu/sifrovani,
- detail leku uz ma dve vizualni casti:
  - male foto krabicky / placeholder,
  - pergamenove okno `PIL_Short` s podkladem `docs/lekarna/assets/ipl-short.png`
    z lokalniho zdroje `data/lekarna/IPL_Short.PNG`.

### Lokalni hadí dotaz

Od 2026-05-20 je lokální dotazový formulář rozšířený tak, aby nekončil příliš
často odpovědí "nevím".

Lokálně rozpoznává tyto oblasti:

- bolest hlavy / horečka,
- bolest zad, kloubů, svalů nebo zubů,
- kašel / zahlenění,
- rýma, nachlazení, chřipka,
- bolest v krku / dutina ústní,
- alergie / svědění / štípnutí,
- průjem / trávení / břicho,
- zácpa / těžké vyprazdňování,
- pálení žáhy / reflux,
- modřina / otok / podlitina,
- kůže / svědění / drobné popálení,
- rána / dezinfekce,
- cestovní nevolnost,
- oči,
- ucho,
- uklidnění / spánek,
- tlak / srdce.

Princip:

- dotaz se normalizuje na malá písmena a bez diakritiky,
- hledají se lokální synonyma a příbuzné výrazy,
- může se vrátit až několik možných oblastí,
- u oblastí bez jasného léku v domácí evidenci se řekne přímo, že jasná položka
  zatím není evidovaná,
- při nejasném dotazu se zobrazí ruční výběr oblastí místo slepé odpovědi "nevím",
- varovné dotazy typu dušnost, bolest na hrudi, ochrnutí, omdlení, krev ve stolici
  nebo otok jazyka/obličeje se nepřeklápějí do domácí lékárny, ale upozorní na
  lékaře/pohotovost/155.

ChatGPT fallback:

- pokud lokální režim nerozumí, zobrazí tlačítko `OK, otevrit ChatGPT`,
- po kliknutí otevře `chatgpt.com` s předvyplněným bezpečným obecným dotazem,
- web se nepokouší tiše posílat osobní data; přesměrování je uživatelská volba.

Overeno:

- `curl -I http://localhost:8765/` vratil 200,
- obraz a MP3 asset vratily 200,
- `node --check ../docs/lekarna/app.js` proslo,
- jednoduchy HTML parser nacetl `index.html`.

Playwright vizualni kontrola nebyla provedena, protoze `npx playwright --version`
narazil na sitove omezeni `ENOTFOUND registry.npmjs.org`.

## Bezpecnostni hranice

- Nepublikovat plny soukromy CSV bez vyslovneho rozhodnuti.
- Pro web vytvorit samostatny export s vybranymi poli.
- U osobnich leku a leku na predpis jasne zobrazit "pouze podle lekare / pro
  konkretni osobu".
- U nejistych polozek nezobrazovat falesnou jistotu; radsi status "overit obal".
- Neuvadet konkretni davkovani jako doporuceni.
- Zdroje a datum overeni ponechat viditelne.

## Publikacni politika

Vychozi predpoklad: pokud web pobezi verejne pres git/GitHub Pages, vystavuje se
jen omezeny git-safe dataset. Plny lokalni inventar zustava soukromy.

Pozor: obycejny formular s heslem v ciste staticke strance neni skutecna
bezpecnost, pokud jsou JSON data a fotky verejne pristupne v repozitari nebo
ve vygenerovanem webu. Je to jen vizualni brana. Skutecnejsi moznosti jsou:

- soukromy hosting se serverovou autentizaci,
- Cloudflare Access / Netlify / Vercel s autentizaci pred pristupem,
- staticky web s predem zasifrovanym datovym balickem a fotkami, kde heslo
  skutecne dešifruje data v prohlizeci,
- lokalni nebo Tailscale-only web mimo verejny internet.

Pro verejny GitHub Pages bez sifrovani plati: co je v `docs/`, je v praxi
verejne, i kdyz aplikace pred zobrazenim ukazuje formular s heslem.

Milovo rozhodnuti 2026-05-20:

- Heslo bude znat jen Jana a Mila ustne.
- Heslo nema byt ulozene nikde v projektu, dokumentaci, pameti, gitu ani datech.
- "Uloziste hesla" je pouze hlava Jany a Mily.

Technicky dusledek:

- Pokud ma web heslo jen kontrolovat, musel by byt v kodu ulozen aspon hash nebo
  jina overovaci stopa. To odporuje pravidlu "heslo nikde".
- Pokud nema byt heslo ulozene nikde, nejlepsi varianta je pouzit heslo jako
  dešifrovaci klic pro zašifrovany datovy balicek. Web pak neoveruje heslo proti
  ulozene hodnote; jen zkusi dešifrovat data. Pri spatnem hesle se data nerozbali.
- V gitu by byl pouze zašifrovany JSON/fotky a aplikacni kod. Heslo samotne ani
  jeho hash by v gitu nebyly.

Implementovany smer od 2026-05-20:

- Lokalni nezasifrovany export zustava v `docs/lekarna/private-data/` a je
  ignorovany gitem.
- Verejne publikovatelny balicek ma byt jen
  `docs/lekarna/encrypted-data/lekarna.enc.json`.
- Sifrovaci skript `scripts/encrypt_lekarna_web_bundle.py` vezme lokalni
  `private-data/lekarna.json`, vlozi fotky jako data URL do payloadu a vysledek
  zasifruje pomoci AES-GCM.
- Klic se odvozuje z hesla pres PBKDF2-SHA256 se soli a 310000 iteracemi.
- Heslo se zadava jen do terminalu skrytym promptem; nepatri do chatu, pameti,
  dokumentace ani gitu.
- Web na GitHub Pages stahne jen zasifrovany JSON a zkusi jej v prohlizeci
  otevrit pomoci WebCrypto. Pri spatnem hesle se data nerozbali.
- Web neuklada heslo ani `sessionStorage` odemceni; po pokusu o nacteni se
  heslo z JS promenne zahodi.
- Ostrý `docs/lekarna/encrypted-data/lekarna.enc.json` byl vytvořen Mílou lokálně
  po zadání hesla do skrytého terminálového promptu a pushnut v commitu
  `e46991d Publish encrypted pharmacy data bundle`.
- Při zápisu do paměti ani do gitu nebylo uloženo heslo ani hash hesla.

### Smime vystavit verejne

- `nazev` - jen pokud nejde o citlivy osobni lek, protoze uz samotny nazev muze
  prozradit zdravotni stav.
- `ucinna_latka`, `forma`, `sila` - pomahaji rozlisit leky a snizuji riziko
  zameny; u osobnich leku jen po samostatnem rozhodnuti.
- `kategorie` a obecne `pouziti` - orientacni popis typu "bolest", "kasel",
  "alergie"; nesmi byt formulovan jako doporuceni lecby pro konkretni osobu.
- `PIL_Short` - prakticky vytah, pokud je formulovan konzervativne a bez
  davkovaciho navodu.
- `PIL_Match_Status` - nutne ukazovat, aby bylo jasne, co je overene a co je
  nejiste.
- `PIL_Checked_Date` - ukazuje stari overeni.
- `PIL_Source` - vhodne ukazat jako odkaz nebo zdrojovou poznamku; pomaha
  dohledatelnosti a brani dojmu, ze informace vznikla bez zdroje.
- Bezpecnostni stitek typu "pouze podle lekare", "overit obal", "neni lek",
  "nejisty nazev".

### Smime vystavit jen v soukromem/rodinnem rezimu

- `umisteni` - prakticke pro domaci pouziti, ale verejne prozrazuje, co a kde je
  doma ulozene.
- `mnozstvi` - verejne muze prozrazovat zasoby leku a citlive informace o lecbe.
- `expirace` - pro rodinu uzitecne, verejne zbytecne soukrome; lze zobrazit jen
  jako obecny stav `overit_expiraci`/`expirace_neznama`, pokud bude web verejny.
- Fotky krabicek - vhodne jen pro soukromy rezim; mohou obsahovat casti domaciho
  prostredi, rukopis, sarze, etikety, nalepky nebo jine nechtene detaily.
- `zdroj` lokalni fotky - nezverejnovat verejne jako cesta v souborovem systemu;
  v soukromem rezimu muze slouzit k dohledani fotky.

### Nevystavovat verejne

- Plny `data/lekarna/domaci_leky.csv`.
- Lokalne zalozene backupy a reporty v `data/lekarna/`.
- Jmena osob nebo oznaceni typu "Jana", pokud souvisi s osobnimi leky.
- Informace, ze konkretni osobni lek patri konkretni osobe.
- Interni poznamky z fotek, rukopisu nebo importu, pokud nejsou vycistene pro web.
- Presne domaci umisteni osobnich leku.
- Cokoliv, co by slo chapat jako doporuceni davky, zmenu lecby nebo nahrazeni
  lekare/lekarnika.

### Doporučený verejny export

Pro verejny web vytvorit odvozeny dataset, ne kopii CSV. Navrzena pole:

- `id` - anonymni stabilni identifikator, ne lokalni cesta.
- `display_name`
- `active_substance`
- `form`
- `strength`
- `category`
- `general_use`
- `pil_short`
- `match_status`
- `checked_date`
- `source_label`
- `source_url`
- `safety_badges`
- `public_note`

Verejny export ma vynechat nebo zobecnit:

- `umisteni`
- `mnozstvi`
- `zdroj`
- `poznamky`
- fotky
- osobni vazby

### Doporučený soukromy export pro Janicku

Pokud ma byt web jen rodinny a neverejny, muze obsahovat navic:

- `umisteni`
- `mnozstvi`
- `expirace`
- odkaz na lokalni/zmensene fotky

I v soukromem rezimu musi zustat viditelne:

- "Toto neni doporuceni lecby ani davkovani."
- "U deti, tehotenstvi, alergii, chronickych nemoci, kombinaci leku a silnych
  nebo trvajicich potizi overit lekare/lekarnika."
- "U polozek s nejistym statusem nejdrive overit obal."

## Aktualni stav 2026-05-20

Projekt webove aplikace Lekarna je uzavreny jako hotovy / udrzba priorita 2.

Hotove:

- Verejny web bezi na `https://belisarius-mila.github.io/PythonMF/lekarna/`.
- Aplikace se odemyka heslem jako desifrovacim klicem; heslo ani hash nejsou ulozene v projektu.
- Skutecna data, fotky a `PIL_Short` jsou publikovane jen jako sifrovany balik
  `docs/lekarna/encrypted-data/lekarna.enc.json`.
- Nesifrovany export `docs/lekarna/private-data/` je lokalni/ignorovany a nesmi se commitovat.
- ChatGPT fallback ma kopirovaci panel a rucni odkaz, protoze nektere prohlizece na Macu neoteviraji novou zalozku ani po kliknuti.
- Míla potvrdil, ze nacitani funguje uspokojive; na iPhonu se ChatGPT otevira v jinem okne, na Macu je k dispozici manualni/copy fallback.

Dalsi vyvoj:

- Zadny aktivni dalsi vyvoj neni otevreny.
- Projekt zustava jako priorita 2, az bude cas nebo novy urgentni pozadavek.
- Pri novem pozadavku nejdrive cist `handoffs/lekarna_web_app_hotovo_2026_05_20.md`.

## Udrzbovy postup pri zmene dat

Pokud se pri dalsim doplneni leku zmeni CSV/fotky, opakovat lokalne export a
sifrovani:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/export_lekarna_web_private_data.py
.venv/bin/python scripts/encrypt_lekarna_web_bundle.py
```

Novy sifrovany balicek znovu cilene commitnout; `docs/lekarna/private-data/`
nikdy necommitovat. Heslo zadavat jen do lokalniho skryteho promptu, nikdy do
chatu, memory, dokumentace ani gitu.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii webove aplikace, ale nepouzivat je
jako aktivni navazovaci stav. Aktualni stav webu je tento projektovy soubor a
`handoffs/lekarna_web_app_hotovo_2026_05_20.md`.

- `handoffs/lekarna_pil_short_done_web_app_start_2026_05_20.md` - dokoncil
  `PIL_Short` v evidenci a zalozil smer webove aplikace; prekryto hotovym webem.
- `handoffs/lekarna_web_app_cockpit_prototype_2026_05_20.md` - rozsahly
  prototyp cockpit webu, sifrovani a ladeni fallbacku; prekryto hotovo handoffem.
