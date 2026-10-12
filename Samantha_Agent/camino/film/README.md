# Camino film

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
editor/render zůstávají další fáze. Každý přehled znovu ověřuje povolenost
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
odmítnuté. Po přerušení se export opakuje od začátku a staré soubory se zachovají.

Registrovaný workflow `camino_film_render` po výslovném zadání spouští:

```bash
.venv/bin/python scripts/camino_film_editor.py render --execute
```

Vytvoří oba profily aktuální uložené revize. Běžící Camino, telefon a síť
nemění. Provozní stav a výsledky jsou v [P2-C/D reportu](../docs/P2CD_EDITOR_MP4_REPORT.md).
