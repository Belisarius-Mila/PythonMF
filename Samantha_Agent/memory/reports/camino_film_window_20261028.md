# Camino — větší okno a celá obrazovka

Datum: 2026-10-28 11:50 CET. Proud project-camino. Stav: místní vývoj, bez nového p+n.

Míla přijal výšku miniatur a požádal o větší okno, ideálně celou obrazovku. Základní limit je zvětšen z 1440 na 1680 px, vnější okraje z 20 na 12 px. Mobilní kompaktní rozložení zůstává zachované.

Tlačítko Celá obrazovka v hlavičce současně vyplní viewport a požádá z přímého kliknutí o Fullscreen API. Nepodpora, synchronní chyba i odmítnutí ponechají použitelný viewportový fallback. Zmenšit či první Escape obnoví běžný rozměr; další Escape používá původní chráněné zavření. Escape ve fotografii zůstává obsloužený fotografickým dialogem.

Změna režimu aktualizuje aria-pressed, popisek a geometrii navigátoru i bez ResizeObserver. Výstup z nativního režimu synchronizuje stav tlačítka. Zavření proběhne až po canClose a ruší žádost o fullscreen; pozdní přijetí requestu neobnoví zavřený editor. Čekající žádost se neopakuje. Přepínání pouze mění prezentaci, bez přestavby editoru či změn draftu, zdrojového textu, historie, importu nebo souhlasů Orusu.

Ověření: 67 cílených kontrol PASS / 38,739 s (test_cockpit_frontend + test_camino_film_editor). Node scénáře pokrývají nativní vstup/výstup, browser Escape, fallback při nepodpoře/odmítnutí/výjimce, přepočet navigace, zachování scrollTop, zavření před dokončením a znovuotevření při čekající žádosti. Testy geometrie předchozí navigace prošly také. Rychlá statická brána PASS (whitespace, Python/JavaScript/shell syntax).

Fyzická Safari přejímka NEOVĚŘENO: po samostatném p+n obnovit Cockpit, vyzkoušet normální/zvětšený režim, Zmenšit i Escape, otevřít/zavřít fotografii a ověřit dostupnost poslední miniatury. Samotné syntetické DOM testy nejsou browserový důkaz.

Nasazený základ: 205789da, předchozí účtenka 226b44f2e1aa9eea783f91a5e66429dd, 2257 PASS, smoke 5/5. Nový kód zatím není nasazený. Kompaktní textový/hlasový panel zůstává samostatný návrh.

Technický podklad: https://developer.mozilla.org/en-US/docs/Web/API/Element/requestFullscreen a https://developer.mozilla.org/en-US/docs/Web/API/Document/fullscreenchange_event .
