# Camino film — P2-A

Lokální syntetický prototyp. Není připojený k owner archivu, iPhonu, Vieweru
ani HTTP API Cockpitu. Nevytváří návrhy nad skutečným dnem; to patří P2-B.

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

Podrobný důkaz a přejímka: [P2-A report](../docs/P2A_FILM_REPORT.md).
