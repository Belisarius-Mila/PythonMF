Nazev: Webova aplikace Lekarna - cockpit prototyp funguje
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-20

## Co se resilo

Postavil se prvni klikatelny staticky web nad projektem domaci lekarny pro
Janicku. Cilem je rodinne a srozumitelne zobrazit vybrane informace z lekarny
bez publikovani plneho soukromeho CSV.

Vychazi se z obrazku:

- `Samantha_Agent/data/lekarna/Lekarna_Cockpit.PNG`

Verejny/prototypovy webovy export je v:

- `docs/lekarna/`

Lokalni testovaci server bezi na:

- `http://localhost:8765/`

Spusteni serveru, pokud nebezi:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/docs/lekarna
python3 -m http.server 8765
```

## Co je hotove

- `docs/lekarna/index.html`
- `docs/lekarna/styles.css`
- `docs/lekarna/app.js`
- `docs/lekarna/assets/lekarna-cockpit.png`
- `docs/lekarna/audio/lekarna-help-intro.mp3`

Funguje:

- lehka uvodni heslova brana v prohlizeci,
- zobrazeni cockpit obrazu stare lekarny,
- klikatelne krabicky:
  - `Pils Jana`,
  - `Pils Mila`,
  - `Pils Home Store`,
- klikatelny had jako dotaz "Co vas trapi?",
- klikatelny otaznik v pravem dolnim rohu obrazku pro prehrani MP3 napovedy,
- zadne samostatne plovouci tlacitko napovedy mimo obraz,
- viditelne texty v HTML/JS jsou počeštěné s diakritikou,
- jemne hover/pulse/shimmer efekty pro klikatelna mista,
- panel s vysuvnym obsahem a krizkem pro zavreni,
- dlouhy obsah panelu se scrolluje uvnitr panelu, krizek zustava viditelny.
- detail leku ma prototypove dve okna:
  - male foto krabicky / placeholder,
  - pergamenove okno `PIL_Short` s podkladem `IPL_Short.PNG`.
- Po rucnim testu 2026-05-20 byl detail upraven:
  - pergamen je hlavni viditelna cast, neni oriznuty pres hrany,
  - foto sloupec je zmenseny,
  - text v pergamenu ma vetsi vnitrni okraje a vlastni scroll,
  - ChatGPT fallback otevira pojmenovanou samostatnou zalozku a v aplikaci nechava
    puvodni panel otevreny.
- Po dalsim rucnim testu 2026-05-20 byly opraveny problemy detailu:
  - v detailu uz nema scrollovat cely obsah s fotkou a pergamenem,
  - vnejsi detailovy panel ma scroll skryty,
  - scrolluje jen textova oblast uvnitr pergamenu,
  - textova oblast pergamenu je umistena do stredove psaci plochy a nema prekryvat
    spodní starocesky napis,
  - ChatGPT fallback byl zmenen z pojmenovane zalozky na `_blank`, aby se
    nenahrazovala ani nezavirala puvodni zalozka s lekarnou.
- Ostrá data jsou napojená bezpečným lokálním režimem:
  - aplikace se pokusí načíst `docs/lekarna/private-data/lekarna.json`,
  - pokud soubor neexistuje, zůstane veřejný demo režim,
  - `docs/lekarna/private-data/` je v `.gitignore` a nesmí se commitovat,
  - export se vytváří skriptem `Samantha_Agent/scripts/export_lekarna_web_private_data.py`,
  - aktuální lokální export obsahuje 56 položek, z toho Jana 4, Míla 3, Home 49,
    a 40 fotek,
  - skutečná data tedy lze proklikat lokálně přes `http://localhost:8765/`,
    ale na GitHub Pages zatím nejsou publikovaná.
- Rozpracovany a potvrzeny smer verejne publikace je sifrovany balicek:
  - `scripts/encrypt_lekarna_web_bundle.py` vezme lokalni `private-data/lekarna.json`,
    vlozi fotky jako data URL a vytvori `docs/lekarna/encrypted-data/lekarna.enc.json`,
  - sifrovani je AES-GCM, klic je odvozen z hesla pres PBKDF2-SHA256,
  - heslo se nezapisuje do souboru, hashe, gitu ani pameti; zadava se jen skrytym
    promptem v terminalu,
  - web se pokusi otevrit `encrypted-data/lekarna.enc.json` pomoci WebCrypto,
  - pri spatnem hesle se data nerozbali,
  - po pokusu o nacteni web zahodi heslo z JS promenne a nepouziva sessionStorage
    pro obchazeni hesla.
- Ostrý šifrovaný balíček byl 2026-05-20 vytvořen lokálně Mílou po zadání hesla
  do skrytého terminálového promptu a byl commitnut/pushnut jako:
  - `docs/lekarna/encrypted-data/lekarna.enc.json`
  - commit `e46991d Publish encrypted pharmacy data bundle`
  - heslo nebylo zadáno do chatu, nebylo uloženo do paměti ani do gitu.

MP3 napoveda byla vygenerovana z textu s diakritikou:

```text
Ahoj, hezky den. Kliknutim otevrite krabicky. Hadi otaznik se zepta, co vas trapi.
```

Poznamka: lokalni TTS zdroj je v `data/lekarna/audio/`, webova kopie je v
`docs/lekarna/audio/`.

## Lokalni hadí dotaz

Lokální hadí dotaz je rozšířený a Míla ručně potvrdil, že funguje velmi dobře.

Rozpoznává oblasti:

- bolest hlavy / horecka,
- bolest zad, kloubu, svalu nebo zubu,
- kasel / zahleneni,
- ryma, nachlazeni, chripka,
- bolest v krku / dutina ustni,
- alergie / svedeni / stipnuti,
- prujem / traveni / bricho,
- zacpa / tezke vyprazdnovani,
- paleni zahy / reflux,
- modrina / otok / podlitina,
- kuze / svedeni / drobne popaleni,
- rana / dezinfekce,
- cestovni nevolnost,
- oci,
- ucho,
- uklidneni / spanek,
- tlak / srdce.

Princip:

- dotaz se normalizuje na mala pismena a bez diakritiky,
- hledaji se synonyma a pribuzne vyrazy,
- muze vratit vice moznych oblasti,
- u oblasti bez jasne domaci polozky rekne, ze v evidenci zatim neni jasny lek,
- pri nejasnem dotazu nabidne rucni vyber oblasti misto slepe odpovedi "nevim",
- pri varovnych dotazech typu dusnost, bolest na hrudi, ochrnutí, omdleni,
  zvraceni krve nebo otok jazyka/obliceje doporuci lekare/pohotovost/155.

ChatGPT fallback:

- pri nejasnem dotazu se zobrazi tlacitko `OK, otevrit ChatGPT`,
- po kliknuti se otevre `chatgpt.com` s predvyplnenym obecnym bezpecnym dotazem,
- presmerovani je uzivatelska volba; web nic neposila potichu.

## Co neni hotove

- Je potřeba po doběhnutí GitHub Pages cache ručně otestovat veřejný web se
  skutečným heslem.
- Neprobehl Playwright vizualni test; drive byl blokovan sitovym omezenim npm.

## Dalsi krok

1. Počkejte, až GitHub Pages dosadí nový soubor z commitu `e46991d`; raw GitHub
   soubor už je dostupný, Pages může několik minut vracet starší cache.
2. Otevřít veřejný web a zadat heslo:
   `https://belisarius-mila.github.io/PythonMF/lekarna/`
3. Ověřit, že se po hesle načtou skutečné seznamy léků a fotky.
4. Z lokalnich query pravidel postupne udelat data-driven mapovani nad exportem,
   aby se nemusela udrzovat natvrdo v `app.js`.

## Zmenene nebo relevantni soubory

- `docs/lekarna/index.html`
- `docs/lekarna/styles.css`
- `docs/lekarna/app.js`
- `docs/lekarna/assets/lekarna-cockpit.png`
- `docs/lekarna/assets/ipl-short.png`
- `docs/lekarna/audio/lekarna-help-intro.mp3`
- `Samantha_Agent/memory/projects/lekarna_web_app.md`
- `Samantha_Agent/memory/ACTIVE_PROJECTS.md`
- `Samantha_Agent/memory/MEMORY_INDEX.md`
- `Samantha_Agent/data/lekarna/Lekarna_Cockpit.PNG`
- `Samantha_Agent/data/lekarna/IPL_Short.PNG`
- `Samantha_Agent/data/lekarna/audio/lekarna_help_intro.mp3`
- `Samantha_Agent/data/lekarna/tts_help_phrases.csv`
- `Samantha_Agent/scripts/export_lekarna_web_private_data.py`
- `Samantha_Agent/scripts/encrypt_lekarna_web_bundle.py`
- lokální necommitovaný export `docs/lekarna/private-data/`
- budoucí veřejně publikovatelný export `docs/lekarna/encrypted-data/lekarna.enc.json`
  je od commitu `e46991d` už reálně publikovaný v gitu jako šifrovaný balíček.

## Overeni

- `node --check ../docs/lekarna/app.js` proslo.
- `curl -I http://localhost:8765/` vratil 200.
- `curl -I http://localhost:8765/app.js` vratil 200.
- `curl -I http://localhost:8765/styles.css` vratil 200.
- Po počeštění textů znovu prošel `node --check ../docs/lekarna/app.js` a
  `curl -I http://localhost:8765/` vratil 200.
- Po doplneni detailu leku proslo `node --check ../docs/lekarna/app.js` a
  `curl -I http://localhost:8765/assets/ipl-short.png` vratil 200.
- Po oprave scrollu detailu a ChatGPT fallbacku proslo
  `node --check ../docs/lekarna/app.js`; lokalni `app.js` a `styles.css` vratily
  200 pres `http://localhost:8765/`.
- Po napojeni ostrého lokálního exportu prošlo:
  - `node --check ../docs/lekarna/app.js`,
  - `curl -I http://localhost:8765/private-data/lekarna.json` vratil 200,
  - kontrola exportu: 56 položek, 40 fotek.
- Po doplneni sifrovani proslo:
  - `node --check ../docs/lekarna/app.js`,
  - testovaci sifrovani do `/private/tmp/lekarna_test.enc.json` s dummy heslem,
  - kontrola struktury balicku: AES-GCM, PBKDF2-SHA256, 310000 iteraci,
  - Node/WebCrypto test rozbalil dummy testovaci balicek a nasel 56 leku a boxy
    `jana,mila,home`,
  - `curl -I http://localhost:8765/` vratil 200,
  - `curl -I 'http://localhost:8765/app.js?v=encrypted-data-20260520'` vratil 200.
- Po vytvoření ostrého šifrovaného balíčku:
  - `curl -I http://localhost:8765/encrypted-data/lekarna.enc.json` vratil 200,
  - kontrola struktury balíčku ukázala AES-GCM, PBKDF2-SHA256, 310000 iterací,
  - `curl -I https://raw.githubusercontent.com/Belisarius-Mila/PythonMF/main/docs/lekarna/encrypted-data/lekarna.enc.json`
    vratil 200,
  - GitHub Pages krátce po pushi ještě vracel 404 pro nový encrypted-data soubor,
    pravděpodobně kvůli cache/nasazení.
- Mila rucne otestoval web a potvrdil:
  - hotspoty funguji,
  - napoveda hraje,
  - hadí dotaz funguje velmi dobre,
  - scroll dlouheho seznamu a viditelny krizek po oprave funguje.

## Bezpecnost / neukladat

- Neulozeno zadne realne heslo.
- Heslo ma zustat jen ustne mezi Milou a Janou, ne v pameti, ne v dokumentaci,
  ne v gitu.
- Nezadavat realne heslo do chatu. Pokud se ma vytvorit realny sifrovany balicek,
  musi se heslo napsat jen do lokalniho terminaloveho promptu.
- `data/lekarna/` zustava soukrome a ignorovane gitem.
- `docs/lekarna/private-data/` zustava soukrome a ignorovane gitem.
- Plny soukromy CSV a fotky leku nepublikovat bez samostatneho rozhodnuti.
- Web nema davat lekarske doporuceni ani davkovani; ma ukazovat domaci evidenci,
  `PIL_Short`, status jistoty a upozorneni na overeni obalu/lekarne.
