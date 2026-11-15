# Cestování / místa — jednodušší přehled a detail

Stav: místně dokončené, 2026-11-15 08:05 CET. Proud project-knowledge-library.
Schválení: Míla přijal návrh a zadal zahájit vývoj, warp1. Nasazení není zadané.

## Výsledek

- Cestovní karty ukazují původní fotografii a krátký úvod z uloženého textu.
- Jeden přepínač kategorií, hledání, Přidat místo s volbou poznámky/odkazu.
- Samostatný detail s fotografiemi a poznámkami; metadata, čtení, export
  a vyřazení v Další možnosti a údaje. Fotografie se spravují při editaci.
- Návrat zachovává hledání/pozici/fokus; i po uložení úprav nebo stavu.
- Opožděný detail/list/fulltext nesmí přepsat novější výběr. Nejasné čtení
  dovolí návrat. Přidání a editace dál používají původní handlery/potvrzení.

## Rozsah a bezpečnost

Nový library_travel.js je součástí stávajícího sestavení Cockpitu. CSS je
scoped na travel-mode. Recepty, knihy a ostatní kategorie zachovávají původní
ovládání; jejich společný details obal je otevřený a nemá viditelný přepínač.
Backend přidává jen čtecí preview_image (ID/varianta) a preview_text; nejvýše
2048 čtených/241 vrácených znaků pro zobrazené cestovní karty, bez průchodu
celým archivem. Path.resolve kontroluje kořen i symlinky. Ostatní typy
preview pole nedostávají, zdrojové texty/přílohy/UID/stavy se nepřepisují.
Pouze textContent, fotografie přes stávající místní attachment endpoint;
žádné generování, model nebo nový odchozí zápis.

## Ověření

114 cílených PASS /16,501s: article_archive, cockpit_frontend, library_photos
a35 knihovních kontraktů. Dvě nové backendové kontroly ověřují skutečný
list/search náhled, zachování bajtů archivu a hranici kořene. Stávající
bajtový kontrakt sestaveného frontendu a pořadí modulů aktualizované.
Browser používá celý skutečný produkční HTML/CSS/JS se syntetickými API
a zachycením veškeré sítě.320/390/1280 seznam i detail bez přetékání;
vizuálně prohlédnuté screenshoty. Hledání/scroll/Zpět, foto viewer, čtecí PDF
odkaz, editor včetně odmítnutí zahodit draft, uložení/stav a pozdní odpověď
PASS.2 syntetické POST (stav/edit),0 produkčních POST,0 nechycených výjimek.
Chybný HTML obsah v názvu zůstává textem. Recepty/knihy přepnuté a funkční.
Statická brána PASS. Plná brána přísluší následnému p+n; v tomto
kroku se neopakuje plná sada nezměněných odchozích/persistenčních vrstev.

Důkazy mimo Git: data/private/travel_ui_20261115/final_targeted.json,
browser_1794726432532020000/result.json a screenshoty. Logy
travel_ui_targeted_final_20261115.log, travel_ui_browser_final_20261115.log,
travel_ui_static_final_20261115.log.

## Meze a další krok

Bez push/nasazení, fyzického iPhonu nebo zásahu do soukromého archivu.
Nasazení vyžaduje samostatné schválení; poté fyzicky ověřit přehled, detail,
fotografii a návrat s hledáním. Původní přejímky knih a pošty zůstávají
oddělené. Kanonický handoff a existující TVBCP Knihovny doplněné; nový
TVBCP se nezakládá.

Závěrečné čtecí zpřesnění: i plný text/editor kontrolují původní pořadí
požadavku v úspěchu, chybě a dokončení. Browser výslovně podržel starý
editorový GET, otevřel stejné místo znovu a napsal nový draft; opožděný
výsledek jej nezměnil. Nová finální sada114 PASS/16,501s a statická brána
PASS. Otisky8 finálních zdrojů/testů v privátním source_manifest.json.
