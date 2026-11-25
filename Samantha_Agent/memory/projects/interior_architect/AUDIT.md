# Technický audit Interiérového architekta

25. 11. 2026 · Human–Adam `project-neuberk-kacenka` · kód Ateliéru na `114c16f9`

**Závěr.** Dnešní aplikace uchovává rozpracované návrhy, původ obrazů a historii požadavků. Neumí vynutit polohu otvoru ani zachování pixelů fotografie. Pro 2.0 navrhujeme převzít přístup přes Cockpit, pravidla čtení soukromých médií a ochranu před opakovaným odesláním. Místnost, její geometrii, obrazovou úpravu a jejich revize má obsluhovat nové jádro. [Návrh backendu](BACKEND.md) · [Návrh UI](UI.md) · [Převod místností](MIGRATION.md)

## Tok dnešní aplikace

| Krok | Co kód skutečně dělá | Dopad na 2.0 |
|---|---|---|
| Vstup | Janička → Rodinné projekty → Otevřít Ateliér → `/interior/`. HTML/JS/CSS v `app/frontend/interior/`. `app/cockpit_interior.py` čte stav, soubory, náhled mazání a stav AI. Zápisy, start a recover jsou registrované POST akce v `app/cockpit.py`. | Jedna známá adresa a stávající kontroly přístupu a původu požadavku. Projekt se otevře výběrem místnosti. |
| Uložení | `app/interior_atelier.py` + `app/work_repository.py` mění jeden JSON transakčně. Návrh odkazuje na rodiče a vybrané podklady, draft patří k místnosti a základní variantě. Uložení kontroluje očekávanou revizi a ID operace. | Převzít význam revizí, rodičů a potvrzených zápisů. Současné UI ukládá také rozepsaný text, dirty draft, výběr a nejistý požadavek do localStorage konkrétního prohlížeče. Soubor na serveru je nepokrývá. |
| Média | Originál zůstává v soukromých objektech. Při nahrání se pro náhled uplatní EXIF orientace a RGB/RGBA, u iPhone MPO se použije hlavní snímek. PNG náhledy mají delší stranu nejvýše 1400 a 256 px. Čtení kontroluje příslušnost k místnosti a otisk objektu. Limit uploadu je 6 MiB a 32 milionů pixelů. | Původní soubor uchovat po bajtech. Pro editaci vytvořit nový plný normalizovaný rastr. Zmenšený náhled není autorita pro souřadnice masek. |
| Zadání | `interior_room_basis.py` přidá společný plán a text měr, pokud existují. `interior_inputs.py` čte nejvýše šest vybraných náhledů. Čistý pracovní obrázek, plán a reference mají označené role. Je-li kresba, připojí se její kopie poslední jako nejvýše sedmý vstup. | Podklad, pokyn kresbou, maska pixelů a geometrický zámek potřebují odlišné datové typy. |
| Rozhovor | `interior_ai.py` zmrazí roli, revizi, kontext a otisky. Codex App Server obdrží instrukce architekta, role vstupů a podle protokolu instrukce pro zadání a název. Chat čte historii příslušné varianty. U nového protokolu jde do obrazu schválené zadání, pracovní draft a vybrané obrázky, historie i poznámky se vyprazdňují. | Zachovat auditovatelný výběr podkladů, schválený text a oddělený rozhovor. Text sám ochranu prostoru nevynutí. |
| Výsledek a obnova | Ověřené vstupy jsou v soukromém snapshotu operace. Driver předá výsledek do journalu, dokončení přijme až čtyři obrazové výstupy a vytvoří potomky. `delivery_unknown` blokuje nový pokus, recover pracuje s původním výsledkem či vláknem. `interior_cleanup.py` při potvrzeném mazání odpojuje obraz a kresbu a čistí odpovídající kopie. | Zaznamenat odděleně doručení požadavku, dostupnost média a výsledek validace obrázku. Historický úspěch požadavku nepotvrzuje geometrii. |

Dnešní hlavní větev neobsahuje nativní masku pro image edit, model stěn a otvorů, kalibraci kamery ani porovnání výstupu s originálem. Obrazový engine, kvalita a složitost zůstávají u mostu neznámé, pokud je skutečný výsledek nedoloží. Čtecí kontrola místního Cockpitu na portu 8770 vrátila HTTP 200 pro vstup a pro stav role `interior_architect` s povolenou obrazovou funkcí.

**Samostatná větev** `data/interior-api-adapter-20261124` obsahuje commit `e0a0e8c5` a zkušební `ImagesAPITrial`. Zmrazuje povolené vstupy, explicitní souhlas a náklady, ukládá účtenku jediného pokusu. Není zapojen do HTTP ani hlavního driveru. Jeho kontrakt přijímá referenční obrazy, samostatné pole masky v něm není. Pro 2.0 je zdrojem návrhu potvrzení a účtenky. Případné připojení má vlastní přejímku skutečných schopností a nákladů.

## Ověření na Macu

| Zkouška | Pozorovaný výsledek | Co z ní plyne |
|---|---|---|
| Regrese v1 | 146 testů prošlo. Sada zahrnuje Ateliér, HTTP včetně dvou frontendových Node sad, AI, aktivaci, zadání, plán, názvy, souborovou persistenci a repository. | Výchozí chování pro porovnání při přepisu. |
| Reprodukce chyby přijímání obrázků | Jeden syntetický požadavek přes `InteriorAI.start` s testovacím driverem. K základu 600 × 400 přijal stávající backend dva radikálně překreslené obrázky, 600 × 400 a 800 × 400. Uložil oba jako varianty a operaci označil za dokončenou. | Stejné rozměry samy nezaručují zachování prostoru. Dnes projde i změna poměru stran. Reprodukce prověřuje příjem výsledku bez hodnocení výkonu skutečného modelu. |
| Lokální kompozice | Intel i5-8257U, 16 GiB, Pillow 12.2.0. Tři průchody syntetickým RGB obrazem 4032 × 3024, binární maskou, kompozicí a kontrolou po opětovném načtení PNG trvaly 0,398 / 0,333 / 0,301 s. Špička procesu 415 MiB. V chráněné oblasti bylo pokaždé přesně 0 odlišných pixelů. | Pillow stačí pro první experiment bez GPU. Jednobarevné plochy se komprimují snadno. Před přejímkou změřit reálnou fotografii, RGBA/ICC, kreslení na telefonu a horní limit 32 MP. |
| Soubory a vazby | Dva průchody stejným soukromým zdrojem daly stejných 147 souborů s velikostí a SHA-256 a stejných 180 klíčů navržené mapy. Kontrola zahrnula rodiče, živé odkazy, revizní základy, otisky mediálních objektů a dostupných vstupních snapshotů. | Vstupní data lze deterministicky spárovat. Zápis cílové databáze i návrat po přerušení jsou přejímkou budoucího importéru. Podrobné počty jsou v migračním plánu. |

Reprodukce, místní soupis s otisky a výstup sady jsou v ignorované složce `data/private/interior_architect_audit_20261125/`. Regresi lze zopakovat z kořene Samanthy:

```sh
.venv/bin/python -m unittest tests.test_interior_atelier tests.test_cockpit_interior \
  tests.test_interior_ai tests.test_interior_ai_activation tests.test_interior_brief \
  tests.test_interior_room_basis tests.test_interior_titles tests.test_file_persistence tests.test_work_repository
```

## Závislosti a otevřené důkazy

Pro první řez stačí Python ze stávajícího prostředí, SQLite 3.42.0 přes standardní knihovnu, stávající Pillow (licence MIT-CMU podle místních metadat), Canvas a SVG v prohlížeči. Validace verzovaného JSON může využít instalovaný jsonschema 4.26.0 (MIT). Metadata potvrzují přítomnost a licenci těchto Python balíčků, měření výkonu se týká pouze popsané kompozice. Nová služba ani instalace ML nejsou pro první řez potřeba.

Three.js lze posoudit ve fázi 3D. Před zařazením zafixovat verzi a licenci distribuovaných souborů, změřit interaktivitu jednoduché scény v Safari na obou zařízeních a vyzkoušet provoz s lokálně podanými soubory. OpenCV, segmentace, hloubkové modely a Blender připadají v úvahu až při konkrétní mezeře ručního postupu. U každého kandidáta ověřit zvlášť licenci knihovny i vah a paměť cílového Macu. Audit nedokládá jejich kompatibilitu.

Bez nezávislých referenčních bodů zůstává perspektiva fotografie neověřená. Historické zamítnutí geometrie v indexu Kačenky se zachová jako posudek autora. Přesnost modelu místnosti se musí opřít o doložené a potvrzené míry.
