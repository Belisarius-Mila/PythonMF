"""U17 map projection: input MUST be the current authorized viewer_snapshot.

No archive reads, persistence, routing service, or independent permission cache.
"""

from camino.domain.model import ContractError


def checked_root(root_path: str) -> str:
    if root_path not in ("", "/camino-api"):
        raise ContractError("unsupported Viewer proxy prefix")
    return root_path


def route_snapshot(snapshot: dict, *, root_path: str = "") -> dict:
    root = checked_root(root_path)
    points = []
    for moment in snapshot["moments"]:
        fix = moment["map_point"]
        if fix is None:
            continue
        local = moment["captured_local"]
        points.append({
            "id": moment["id"], "title": moment["title"],
            "day": local[:10] if local else "unknown",
            "time": local[11:19] if local else "Čas neznámý",
            "utc_ms": moment["captured_utc_ms"],
            "uncertain": moment["capture_uncertain"],
            "latitude": fix["latitude"], "longitude": fix["longitude"],
            "accuracy_m": fix["accuracy_m"],
            "href": f'{root}/viewer/days/{moment["day"]}#moment-{moment["id"]}',
        })
    points.sort(key=lambda p: (p["utc_ms"] is None, p["utc_ms"] or 0, p["id"]))
    previous = None
    for point in points:
        # Every GPS fix is a new point in the captured chronology. Draw the
        # next segment even when accuracy, distance, day or time certainty is
        # poor; the map is an orientation aid, not a measured route.
        point["connect_previous"] = previous is not None
        previous = point
    return {"points": points}


def map_page(root_path: str = "") -> str:
    root = checked_root(root_path)
    return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="origin"><title>Mapa cesty · Camino</title>
<link rel="stylesheet" href="{root}/viewer/map-assets/leaflet.css">
<link rel="stylesheet" href="{root}/viewer/map-assets/map.css">
<script src="{root}/viewer/map-assets/leaflet.js" defer></script>
<script src="{root}/viewer/map-assets/map.js" defer></script></head>
<body data-map-url="{root}/viewer/map-data"><header>
<a href="{root}/viewer/">← Zpět do deníku</a><p class="eyebrow">CAMINO · PRO JANU</p>
<h1>Mapa cesty</h1><p>Místa záznamů, postupně přibývající po synchronizaci.</p>
<p class="notice">Přerušované spojnice jsou orientační, nikoli přesně prošlá trasa.
Každý nový GPS bod se spojí s předchozím bodem; nepřesnost, velká vzdálenost
nebo časová mezera proto mohou vytvořit dlouhý či nepřesný úsek.
Fotografie a komentáře přidané ke stejnému okamžiku sdílejí jeho původní bod.</p>
</header><main><section id="consent">
<h2>Otevřít skutečnou mapu?</h2><p>Mapový podklad poskytuje OpenStreetMap.
Po otevření uvidí poskytovatel tvoji IP adresu, adresu serveru Vieweru (bez cesty)
a prohlíženou oblast. Názvy, texty, seznam bodů ani přístupové údaje mu neposíláme.
Mapový podklad vyžaduje internet.</p>
<button id="open-map" type="button">Otevřít mapu</button></section>
<section id="map-controls" hidden><label for="day">Zobrazit</label>
<select id="day"><option value="">Celá cesta</option></select>
<button id="refresh" type="button">Obnovit</button>
<button id="fit" type="button">Zobrazit všechny body výběru</button></section>
<p id="status" role="status" aria-live="polite">Mapa zatím není otevřená.</p>
<p id="tile-status" role="status"></p>
<div id="map" hidden aria-label="Mapa míst záznamů"></div>
<p id="legend" hidden>● Zelená: první známý bod · ● Modrá: poslední známý bod ·
● Oranžová: přibližná poloha (nad ±100 m). Body ve stejném místě mají společný rozcestník.</p>
<details id="point-list" hidden><summary>Seznam míst a odkazy do deníku</summary><ol id="points"></ol></details>
<noscript>Pro mapu je potřeba JavaScript. Deník funguje i bez něj.</noscript>
</main><footer>Obnova každou minutu, pouze když je stránka viditelná.
Zobrazené body nejsou živá poloha ani doklad úplnosti přenosu.
Soukromé a skryté záznamy se nezobrazují. Již uložené cizí kopie nelze vzít zpět.
</footer></body></html>'''
