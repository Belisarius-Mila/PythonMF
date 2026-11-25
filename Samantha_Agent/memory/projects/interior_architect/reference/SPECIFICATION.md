# Technická specifikace — Interior Architect 2.0

## Cíl a omezení
Modernizuj existující modul a Cockpit: chybné pochopení fotografií a půdorysu, deformace perspektivy, přesouvání oken a dveří, nekonzistentní pohledy a nedostatečné UI. AI smí měnit design, nikoli svévolně geometrii. Žádné nové placené služby ani API; existující placené operace pouze po výslovném souhlasu. Preferuj lokální open-source zpracování. Cílový Mac Intel i5, 16 GB RAM, bez předpokladu výkonné GPU. Ověř licence a kompatibilitu. Zachovej stávající projekty a funkční komponenty.

## 0. Audit
Zjisti umístění modulu, frontend/backend, komunikaci s Cockpitem, poskytovatele modelů, prompty, předávání obrázků a půdorysů, ukládání projektů, historii, existující testy a příčiny chyb. Sepiš AUDIT.md s riziky a migračním plánem. Nevytvářej paralelní aplikaci bez důvodu.

## 1. Spatial Locking Engine
Editor fotografie: zoom/pan, obdélník, polygon, štětec, guma, pojmenování a editace oblastí, viditelnost vrstev, undo/redo, uložení masek. Souřadnice masek ukládej v souřadnicích originálu, nezávisle na zoomu. Preferuj Canvas/SVG a existující frontend.

| Režim | Barva | Význam |
|---|---|---|
| PIXEL_LOCK | červená | Identické dekódované pixely |
| GEOMETRY_LOCK | oranžová | Zachovat polohu, tvar, rozměry a orientaci; povrch lze změnit |
| EDITABLE | zelená | Povolená cílená změna |
| FREE_DESIGN | modrá | Kreativní změna v mezích geometrie |
| CONTEXT_ONLY | šedá | Kontext, bez povolení změny |

Výchozí neoznačená oblast je chráněná. PIXEL_LOCK a CONTEXT_ONLY mají přednost před povolením změny; GEOMETRY_LOCK dovoluje pouze povrchové změny. Konflikty zobraz. Původní obraz uchovej neměnný, normalizuj orientaci a barevný režim do autoritativního bezeztrátového rastru. Kompozice: Pillow/NumPy/OpenCV; původní pixely mimo povolenou masku vždy obnov. Feathering pouze uvnitř povolené oblasti. Nepoužívej slepý resize při jiné perspektivě; nekompatibilní výstup odmítni. Ukládej PNG, kontroluj po opětovném načtení. Pixel Integrity Test: přesně nula odlišných pixelů v chráněných oblastech. Geometry Lock není garantován samotnou maskou.

## 2. Spatial Scene Model
Verzované JSON schéma, milimetry, explicitní souřadnicový systém. Stěny, podlaha, strop, okna, dveře a směr otevírání, pevné konstrukce, nábytek, sanita, přípojky, kamery, masky, omezení a historie. Každý objekt: ID, typ, pozice, rozměry, orientace, zámek a původ údaje. Rozliš potvrzené, detekované, odhadnuté a neznámé hodnoty; neznámé nevymýšlej. Vzor SCENE_MODEL.json není hotové schéma ani zaměřený půdorys.

## 3. 2D editor
Deterministický půdorys ze scene modelu: rozměry místnosti, stěny, otvory, směr dveří, nábytek, drag/drop, rotace, numerické zadávání, zámky, kóty, kolize, varianty. Nepoužívej generativní model k vykreslení technického půdorysu.

## 4. Geometry Awareness
OpenCV: hrany, přímky, dominantní směry, úběžníky, porovnání perspektivy. Volitelně SAM 2 či lehčí segmentace a Depth Anything V2 Small; nejprve ověř výkon a licence. Ruční editor musí fungovat bez nich. Automatické masky uživatel potvrzuje. Monokulární hloubka není přesné měření. Porovnávej obrysy, polohy a orientace; nejistou shodu označ jako neověřenou.

## 5. 3D jádro
Three.js pro interaktivní scénu, volitelný Blender Python API pro rendering, GLTF/GLB pro výměnu. Z modelu vytvoř stěny s otvory, podlahu, strop, parametrické vybavení, materiály, osvětlení a kamery. Pohled shora, od dveří a okna; export. Všechny pohledy ze stejného modelu. Začni jednoduchými tvary bez AI; neznámé rozměry vyžadují potvrzení před přesným renderem. Kolize kontroluj programově.

## 6. Generative Image Adapter
Odděl poskytovatele od jádra. Deklaruj schopnosti: obrazové vstupy, masky, inpainting, strukturální reference, rozlišení, hardware, náklady. Podle podpory předávej fotografii, masky, půdorys, scene model, 3D render, hloubku, hrany, materiály a omezení. Nepředstírej podporu ControlNet. Volitelně ComfyUI/Stable Diffusion/ControlNet po benchmarku a souhlasu s instalací. Bez modelu musí fungovat 2D/3D i testy kompozice. Testovací adaptér jasně označ jako testovací. Výchozí režim bez placených volání; neznámé náklady blokuj.

## 7. Cockpit UX
Pracovní režimy: podklady, analýza, masky, půdorys, dispozice, materiály, 3D, vizualizace, varianty, validace. Viditelné zámky, potvrzené vs odhadnuté údaje, schopnosti modelu, náklady a stav validace. Before/After posuvník, rozdílová mapa, upozornění na porušení omezení. Samostatné varianty a historie.

## Dokumentace a migrace
V repozitáři udržuj docs/interior_architect/{AUDIT,ARCHITECTURE,ROADMAP,TESTING,CHANGELOG}.md nebo ekvivalent dle konvencí. Verzuj data, zachovej originály, testuj migrace. Každá etapa musí být funkční a testovatelná. Neoznačuj prototyp ani neověřený výstup za hotový.
