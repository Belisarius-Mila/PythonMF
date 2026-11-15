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


## 2026-11-15 08:10 CET — Schválené vlastní Terra p+n Cestování / místa

Hotovo: Vývojový checkpoint35b5402e je připravený k vydání,114 cílených,
statická brána i izolovaný browser320/390/1280 PASS.
Rozhodnutí: Míla výslovně zadal p+n via Terra pouze pro Willovu práci.
Balíček obsahuje35b5402e, Willův závěrečný dokumentační7d8c04e4 k minulému
vydání Vocabulary EN a tento bezpečný publikační zápis. Další Datovy větve
a nový Vocabulary obsah nejsou součástí. Cíl project-knowledge-library / cockpit.
Další krok: Jediné registrované submit_release(wait=True), potom převzetí
účtenky a čtecí kontrola živé Knihovny. Po potvrzeném vydání fyzický iPhone.
Navrhované další kroky: Původní přejímky knih a poštovní A+C zůstávají
oddělené; žádná aktivace nebo změna soukromých záznamů.
Technický důkaz:8/8 finálních zdrojů/testů stále shodných s místní přejímkou.
Request travel-places-ui-20261115-own-v1, deterministický job c67e607ca431ef10d7c0522dee0e2845.
Aktuální výsledek vydání určuje výhradně přesná privátní
data/private/travel_ui_20261115/release/release_receipt.json
a live_verification.json, nikoli tento předpublikační záznam.
Účtenka explicitně odděluje push, nasazení, ověření a fyzický telefon.
Při timeoutu či nejistotě ověřit stejný job; žádné automatické opakování.


## 2026-11-15 08:29 CET — Oprava oddělení rendereru a nové přesné vlastní vydání

Hotovo: Jediná podmínka v rendereru nejprve ověří kategorii travel_places,
a teprve potom sahá na cestovní controller. Samostatný původní test
knižních obálek tak dál funguje bez nové globální závislosti. Funkce
nového UI ani rozsah se nerozšiřují.64 knižních/frontendových testů
PASS/17,073s a znovu celý browser320/390/1280 včetně nového draftu PASS.
Rozhodnutí: Pokračování stejného Mílou schváleného p+n via Terra jen
Willova balíčku. Datovy další větve zůstávají mimo.
Další krok: Po statické bráně a lokálním checkpointu nové jediné registrované
vydání opraveného headu; potom ověřit živý Cockpit a fyzický iPhone.
Navrhované další kroky: Původní přejímky knih a poštovní A+C odděleně.
Technický důkaz: Původní jobc67e607ca431ef10d7c0522dee0e2845 skončil attention;
3922 testů/53 SKIP, jediný FAIL test_online_cover_sources_and_backlink_behavior
s ReferenceError libraryTravel v izolovaném Node rendereru. Plná brána
ukončená, žádný timeout. Čerstvý registrovaný GitHub audit doložil stále
e780fe98,3 vlastní pending commity; runtime PID72316/stamp42ad54202295bc7c
beze změny. Push tedy nebyl proveden a nasazení nezačalo; původní účtenka
a first_gate.log jsou zachované v privátním travel_ui_20261115/release/.
Nová oprava vyžaduje novou identitu: request travel-places-ui-20261115-own-v2,
jobfff30ae477f38401ae8e582208e9a582. Výsledek výhradně z privátní
travel_ui_20261115/release_v2/release_receipt.json + live_verification.json.
Žádný resubmit původního jobu, změna časových limitů nebo vynechání testů.


## 2026-11-15 09:04 CET — Úplná diagnostika zelená, p+n čeká na servisní rozhodnutí

Hotovo: Opravený zdrojda1ee2bc prošel celou nezměněnou kanonickou sadou
v témže profilu Knihovny:3922 testů,0 failures/errors,31 SKIP. Testová část
822,728s; import5,669s; příprava syntaxe9,3s a jednotkový krok829,2s.
Všech8 finálních zdrojů/testů odpovídá zmrazeným otiskům opravy.
Rozhodnutí: Žádné rozšíření schváleného rozsahu UI; čeká se na samostatné
rozhodnutí Míly o servisní opravě limitu900→1500s a řízeném načtení po plné
bráně. Návrh zatím není aplikovaný. Další publikační pokus se nespouští.
Další krok: Rozhodnutí o servisní opravě; teprve poté dokončit registrované
Terra p+n a ověřit živý Cockpit.
Navrhované další kroky: Po potvrzeném vydání fyzický iPhone; poštovní A+C
a přejímka knih odděleně.
Technický důkaz: v2 fff30ae477f38401ae8e582208e9a582 skončil attention
po přibližně15min, nový gate log se nezapsal. Spolu s pevným900s limitem
a jeho větví TimeoutExpired to odpovídá vypršení času, ne novému doloženému
FAIL. Úplná samostatná brána s --unit-test-timings následně PASS. První
FAIL knižního rendereru z v1 je opravou64 testů a touto úplnou sadou uzavřený.
Čerstvý registrovaný GitHub audit pořád e780fe98; runtime PID72316 a stamp
42ad54202295bc7c beze změny. Push ani nasazení tedy neproběhly.
Privátní důkazy: travel_ui_20261115/release_v2/diagnostic_gate.log,
diagnostic_timings.json, release_receipt.json, source_manifest.json.
Servisní proposal.patch je pouze návrh mimo Git; nezměněná publikační
brána se neobchází a testy se neškrtají.
