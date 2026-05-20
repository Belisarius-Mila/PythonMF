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

- Skutecna data z `data/lekarna/domaci_leky.csv` zatim nejsou napojena.
- Seznamy leku v krabickach jsou zatim mock/prototyp.
- Detail leku zatim nezobrazuje skutecne foto krabicky a skutecny `PIL_Short`.
- Neni hotovy git-safe/export/sifrovaci krok.
- Heslova brana je zatim jen vizualni/local session brana, ne skutecna ochrana dat.
- Neprobehl Playwright vizualni test; drive byl blokovan sitovym omezenim npm.

## Dalsi krok

1. Rozhodnout technicky rezim publikace:
   - lokalni/Tailscale-only,
   - soukromy hosting s autentizaci,
   - nebo staticky web se zasifrovanym datovym balickem.
2. Pripravit samostatny export z CSV jen s povolenymi poli.
3. Napojit krabicky na skutecne seznamy:
   - `Pils Jana`,
   - `Pils Mila`,
   - `Pils Home Store`.
4. Napojit detail leku:
   - foto krabicky, pokud smi byt v exportu,
   - `PIL_Short`,
   - `PIL_Match_Status`,
   - zdroj/datum overeni.
5. Z lokalnich query pravidel postupne udelat data-driven mapovani nad exportem,
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

## Overeni

- `node --check ../docs/lekarna/app.js` proslo.
- `curl -I http://localhost:8765/` vratil 200.
- `curl -I http://localhost:8765/app.js` vratil 200.
- `curl -I http://localhost:8765/styles.css` vratil 200.
- Po počeštění textů znovu prošel `node --check ../docs/lekarna/app.js` a
  `curl -I http://localhost:8765/` vratil 200.
- Po doplneni detailu leku proslo `node --check ../docs/lekarna/app.js` a
  `curl -I http://localhost:8765/assets/ipl-short.png` vratil 200.
- Mila rucne otestoval web a potvrdil:
  - hotspoty funguji,
  - napoveda hraje,
  - hadí dotaz funguje velmi dobre,
  - scroll dlouheho seznamu a viditelny krizek po oprave funguje.

## Bezpecnost / neukladat

- Neulozeno zadne realne heslo.
- Heslo ma zustat jen ustne mezi Milou a Janou, ne v pameti, ne v dokumentaci,
  ne v gitu.
- `data/lekarna/` zustava soukrome a ignorovane gitem.
- Plny soukromy CSV a fotky leku nepublikovat bez samostatneho rozhodnuti.
- Web nema davat lekarske doporuceni ani davkovani; ma ukazovat domaci evidenci,
  `PIL_Short`, status jistoty a upozorneni na overeni obalu/lekarne.
