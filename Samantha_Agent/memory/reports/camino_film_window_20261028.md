# Camino — větší okno a celá obrazovka

Datum: 2026-10-28 11:50 CET. Proud project-camino. Stav: publikované a nasazené do f336fd47 přes Terru 6.1/high; fyzická Safari přejímka čeká.

Míla přijal výšku miniatur a požádal o větší okno, ideálně celou obrazovku. Základní limit je zvětšen z 1440 na 1680 px, vnější okraje z 20 na 12 px. Mobilní kompaktní rozložení zůstává zachované.

Tlačítko Celá obrazovka v hlavičce současně vyplní viewport a požádá z přímého kliknutí o Fullscreen API. Nepodpora, synchronní chyba i odmítnutí ponechají použitelný viewportový fallback. Zmenšit či první Escape obnoví běžný rozměr; další Escape používá původní chráněné zavření. Escape ve fotografii zůstává obsloužený fotografickým dialogem.

Změna režimu aktualizuje aria-pressed, popisek a geometrii navigátoru i bez ResizeObserver. Výstup z nativního režimu synchronizuje stav tlačítka. Zavření proběhne až po canClose a ruší žádost o fullscreen; pozdní přijetí requestu neobnoví zavřený editor. Čekající žádost se neopakuje. Přepínání pouze mění prezentaci, bez přestavby editoru či změn draftu, zdrojového textu, historie, importu nebo souhlasů Orusu.

Ověření: 67 cílených kontrol PASS / 38,739 s (test_cockpit_frontend + test_camino_film_editor). Node scénáře pokrývají nativní vstup/výstup, browser Escape, fallback při nepodpoře/odmítnutí/výjimce, přepočet navigace, zachování scrollTop, zavření před dokončením a znovuotevření při čekající žádosti. Testy geometrie předchozí navigace prošly také. Rychlá statická brána PASS (whitespace, Python/JavaScript/shell syntax).

Fyzická Safari přejímka NEOVĚŘENO: po samostatném p+n obnovit Cockpit, vyzkoušet normální/zvětšený režim, Zmenšit i Escape, otevřít/zavřít fotografii a ověřit dostupnost poslední miniatury. Samotné syntetické DOM testy nejsou browserový důkaz.

Nasazený základ: 205789da, předchozí účtenka 226b44f2e1aa9eea783f91a5e66429dd, 2257 PASS, smoke 5/5. Nový kód je nyní nasazený ve f336fd47. Kompaktní textový/hlasový panel zůstává samostatný návrh.

Technický podklad: https://developer.mozilla.org/en-US/docs/Web/API/Element/requestFullscreen a https://developer.mozilla.org/en-US/docs/Web/API/Document/fullscreenchange_event .


## 2026-10-28 12:21 CET — Výsledek skutečného p+n

Účtenka 6bf0ff7d29efba5a7da3eff147e08d59 completed, push_state=confirmed, deployment_state=confirmed, 2 commity do f336fd47e0b77420baeab25683cbc2bb39441ed3, project-camino → Cockpit. Vykonavatel gpt-6.1-terra/high, policy digest 2658fc0b796051bbbfe1bd957bd1c62c0977bd081fe5f37561bf4ec873c0540d. Plná publikační brána 2258 PASS / 445,5 s, smoke 5/5, protected_services_unchanged=true. Code stamp 296a14675318a23b zachovaný (měnily se frontend, modelová politika a dokumentace).

Adam převzal účtenku v nativní relaci a jednou ověřil GitHub head, health HTTP 200 a přesnou shodu živého HTML se zdrojem; SHA-256 23faa858e96af264b405a3af1b7a5a78255d2e41eda3652d449b9a42393056dc, nové tlačítko přítomné. returned_to_adam=false zůstává portálový příznak, není důvodem retry.

Samotné převzetí: 26516 vstupních, 0 cached, 72 výstupních tokenů (z toho 13 reasoning), celkem 26588. Při schváleném Standard ceníku odhad 0,6719 kreditu; neobsahuje kandidátský probe, Adama ani jiné části práce a nejde o fakturu nebo důkaz úspory celého postupu. Terra zůstává preferovaným release_executor do dalšího rozhodnutí Míly; simple_developer beze změny. Fyzická Safari přejímka fullscreen NEOVĚŘENO. Tento závěrečný zápis je místní pro příští balíček, bez nového zásahu do UI nebo dalšího p+n.
