# P2-A — syntetický film a uložená časová osa

Stav 2026-10-10: lokální implementace a strojová přejímka; skutečné přehrání
celého filmu na Macu a iPhonu zůstává NEOVĚŘENO. Bez push a nasazení tohoto
vývojového kroku. Produkční archiv ani média Camina nebyly použité.

## Rozsah

- Neměnný JSON projekt v1 se stabilními ID, revizemi a SHA-256 zdrojů,
  obrazovou a hlasovou osou, in/out časy, titulky, původem textu a příznakem
  ruční úpravy. Nová revize se ukládá do nového souboru; nejde ještě o editor
  nebo správu variant P2-C/F.
- Syntetický výchozí film: fotografie, celé vodorovné a svislé video,
  video otočené skutečnou display matrix, závěrečná fotografie a testovací
  česká řeč přes několik záběrů. Rozdílné vstupní fps se převádějí na 30 fps.
- Přehratelný pracovní MP4 1280 × 720 a finální MP4 1920 × 1080, 16:9,
  H.264 / AAC 48 kHz. Oba výstupy mají totožnou revizi a otisk časové osy.
- Celá plocha svislého obrazu v rámu, české titulky přes Pillow; místní
  FFmpeg 8.1 nemá drawtext/libass. Text se nikdy nevkládá do filtergraphu.
- Zvuk videa, komentář na časové ose, základní ztišení zvuku videa na 20 %
  během komentáře a společná hlasitost 80 % pro rezervu. Ruční gain je
  součástí formátu, jeho ovládání v UI patří až P2-C.
- Před renderem kontrola souborů, metadat, délky a prostoru. Po renderu
  kontrola rozměrů/kodeků/délek, dekódování celého výstupu a opětovná kontrola
  zdrojů i projektu. Teprve potom vznikne create-only `film.mp4` a účtenka.
- Neúspěšné a pracovní soubory zůstávají jako důkaz; nový běh se neplete
  se starým výstupem. Publikovaný soubor je hardlink k pracovnímu výstupu,
  nikoli druhá plná kopie. Žádná trvalá fronta, automatické mazání ani resume
  po částech. Opakování vytvoří nový samostatný export.
- Jednorázový registrovaný workflow, sekvenční náhled/final, FFmpeg encoder
  se dvěma vlákny a snížená priorita experimentu (`nice +5`).

## Měření na Mílově Macu

Přijatý syntetický běh: `run-xip7fnef`, FFmpeg 8.1, Pillow 12.2.0.
Obrazová i zvuková stopa mají podle FFprobe 22 000 ms.
Časy zahrnují render, kontrolu/dekódování a kontrolní součty exportu;
nezahrnují vytvoření vstupů. Celý experiment včetně vstupů trval 20,877 s.

| Výstup | Čas | Velikost MP4 | Špička pracovních dat, logická / alokovaná |
| --- | ---: | ---: | ---: |
| Náhled 720p | 4,221 s | 1 865 006 B | 1 922 375 / 2 162 688 B |
| Finále 1080p | 12,490 s | 4 723 927 B | 4 828 705 / 5 365 760 B |

Celý adresář experimentu včetně vstupů, obou výstupů a pracovních souborů:
špička 9 824 582 B logicky / 10 383 360 B alokovaně (cca 9,4 / 9,9 MiB).
Měření vzorkuje každých 50 ms a hardlinky započítá jednou. Nejde o absolutní
špičku všech systémových zápisů nebo záruku stejné spotřeby APFS. Dodatečné
QA snímky vznikly až po měření. Na dlouhý skutečný film nelze časy lineárně
přenést; jednoduché kalibrační obrazce nenahrazují 4K/HDR zdroje.

## Ověření

- 15/15 cílených testů P2-A PASS: persistence/reopen, odmítnutí přepisu,
  poškozený hash, soukromý/nejasný zdroj, formát/revize/cesty/symlink, neplatné
  časy, překryv/mezera obrazu, přesah hlasu, disk před renderem, selhání
  procesu, zdroj změněný během renderu, skutečná rotace, dekódovaný konec
  videa a hlasu, shoda návrhu obou profilů a zachování starého exportu.
- Výsledný 22s film celý strojově dekódovaný; oba profily sdílejí fingerprint
  `ef8cd422e91352cfc11e586210568da094b79c3b944fb6e1e41b5d879831d887`.
- Posledních 100 ms aktivní řeči porovnáno se zdrojovým PCM v očekávaném
  čase 12 730,65 ms filmu: normalizovaná korelace 0,996558. To dokládá
  zachování konce zvuku, nikoli lidský poslech nebo srozumitelnost na telefonu.
- Vizuálně zkontrolovány dekódované snímky v 1/6/11/16/20 s: česká diakritika,
  celé rámování, svislý a skutečně otočený obraz, závěrečný titulek.
- Automatizovaný prohlížeč nebyl dostupný (inventář prázdný). Mac browser
  playback, lidský poslech a fyzický iPhone zůstávají NEOVĚŘENO.
- Plná společná Cockpit brána PASS: 1 865/1 865 testů, unittest 295,564 s;
  syntaxe Python/JavaScript/shell a whitespace také PASS. Po doplnění
  kontroly dostupnosti místního fontu znovu 15/15 cílených testů PASS.

Dvě chyby nalezené experimentem byly opravené: sampler disku ignoruje zmizelý
atomický dočasný soubor a propaguje jiné chyby; video fixture používá
`-display_rotation` a ověřuje matici přes FFprobe. První dva běhy zůstávají
diagnostické, nejsou důkazem finální P2-A přejímky.

## Struktura a rozsah kódu

Počítány fyzické řádky souborů, včetně komentářů a prázdných řádků:

| Soubor | Řádky | Úloha |
| --- | ---: | --- |
| `camino/film/__init__.py` | 1 | hranice prototypu |
| `camino/film/project.py` | 144 | validace a persistence |
| `camino/film/media.py` | 84 | média a titulky |
| `camino/film/render.py` | 195 | renderer a měření |
| `camino/film/synthetic.py` | 78 | kalibrační vstupy |
| `scripts/camino_p2a_film.py` | 75 | experiment a přehrávač výsledků |
| `tests/test_camino_film.py` | 213 | 15 testů |

Celkem 577 nových řádků aplikace/runneru, 213 testovacích řádků a 19 přidaných
řádků v existujícím registru workflow a quality gate: **809 přidaných řádků
Pythonu**, 7 nových a 2 upravené Python soubory. Dokumentace se počítá zvlášť.

Tok: registrovaný workflow → syntetické zdroje → uložený JSON → validace →
FFmpeg/Pillow → kontrola celého MP4 → export a měřicí účtenka → review.html.
Žádná nová databáze, HTTP endpoint, systémová služba, iOS build ani závislost.

## Hranice a další přejímka

P2-A je omezené na syntetické SDR zdroje do 120 s, nejvýše 16 zdrojů a 8
nepřekrývajících se komentářů. HDR/BT.2020 se bezpečně odmítá; skutečný převod
HDR, reálné audio s chybějícími částmi a produkční revokace nejsou hotové.
Kontrola příznaků syntetického manifestu není napojení na živou autoritu
souhlasů. Uzavření telefonní fronty a zdrojů patří P2-B. Mobilní editor,
krátké dílčí náhledy a trvalá renderovací fronta patří P2-C/D.

Jediný následující fyzický checkpoint **P2-A/MAC1**: otevřít finální MP4
v prohlížeči nebo QuickTime, přehrát všech 22 s se zvukem. PASS znamená
správné titulky a orientaci, celé obrazy a slyšitelnou závěrečnou větu
„šťastnou cestu“. Pak následuje samostatný P2-A/IPHONE1. P2-A nelze označit
za plně přijaté před oběma výsledky. Originály a skutečný archiv se při tom
nepoužijí. Nový krok nebyl pushnutý ani nasazený.

Soukromé důkazy a výstupy jsou v `data/private/camino/p2a/run-xip7fnef/`:
`experiment.json`, `audio-tail-check.json`, `contact-sheet.png`, `review.html`,
`preview-712fb6726a95/film.mp4` a `final-59b109f77f12/film.mp4`.

Technická reference: [FFmpeg filtry](https://ffmpeg.org/ffmpeg-filters.html)
a [FFmpeg volby vstupu a výstupu](https://ffmpeg.org/ffmpeg.html).
Konkrétní schopnosti byly ověřené místním FFmpeg, nikoli pouze dokumentací.
