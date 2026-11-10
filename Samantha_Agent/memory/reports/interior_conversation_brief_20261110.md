# Interiérový ateliér — zadání z rozhovoru

Stav: skutečně nasazeno 2026-11-10 21:03 CET; GitHub zarovnaný na e867c165, Cockpit potvrzený účtenkou 81e34ae6bd5c3f646d93706a115796e1. Původní vývojový podklad ba2f9bbc; implementace 448d2902. Předchozí oprava prázdných miniatur vydaná současně.

## Uživatelský výsledek a rozhodnutí

Míla schválil nahradit duplicitní editovatelná pole jedním souhrnem připravovaným v rozhovoru. Architekt vrací běžnou odpověď a návrh zadání: changes, preserve, unresolved. Souhrn není automatické spuštění obrázku. Pod obrázkem jsou přehled, názvy referencí, rozbalitelný pracovní obrázek s kresbou a tlačítko „Vytvořit podle tohoto zadání“. Rozepsaná zpráva a neuložené změny vytvoření blokují. Odlišné podmínky zachování jsou zvýrazněné.

Hypotetické úvahy mají zůstat otevřenými otázkami; obrazový prompt požaduje zachovat nerozhodnuté části podle původního obrázku. Jde stále o koncepční vizualizaci. Významové porozumění modelu nebylo ověřeno novým placeným tahem.

## Kontrakt a zachování dat

- `interior-brief-v1`: chat používá strict output schema; návrh se uloží pouze při shodě původního základu, bez přepsání novějšího draftu. Vadná odpověď nezaloží souhrn ani automatický nový pokus.
- Schválení obrázku nese přesný token a expected_revision. Token váže projekt/místnost/variantu, revizi, obsah souhrnu, poslední chat, poznámky, vybrané soubory a kresbu. Server znovu kontroluje stav při rezervaci požadavku.
- Obrazový kontext obsahuje approved_brief, pracovní obrázek, reference a kresbu. Historie a volné poznámky jsou prázdné; text klientské image message obrazový prompt nenahrazuje.
- Nejasnosti se přenesou do vytvořených AI i lidských variant. Existující drafty, uložené texty, varianty a cache se nemigrují ani nemažou. Nová UI pole prompt/fixed nejsou duplicitně editovatelná.
- Staré provozní request ID lze ověřit/opakovaně načíst bez druhého tahu. Nové staré požadavky produkční služba odmítne s výzvou obnovit stránku. Interní starší aktivační testy/pilot zůstávají kompatibilní; změněný zdroj/instrukce jsou součástí otisků budoucího pilotu. Role a přijatý model se nemění, nový pilot neběžel.
- Ochrana před opakováním nejistých placených požadavků a obnova původních výsledků zůstávají. Data/Will worktrees, skutečné fotky a běžící Cockpit se nemění.

## Ověření

118 cílených Python/HTTP/frontend kontrol PASS (117 společně + nová izolovaná driver kontrola; celý modul znovu 12/12). Zahrnují 24 Node scénářů a 12 nových serverových kontraktů. Testy pokrývají přesné potvrzení, změnu revize/poznámek/kresby, pozdní návrh, vadný souhrn, delivery_unknown, idempotenci, staré požadavky a přenos nejasností. Staré mazání i galerie prošly.

Safari přes CUA na lokální syntetické místnosti: počáteční souhrn, blokování rozepsanou zprávou, odpověď s novým souhrnem, zvlášť nerozhodnutý přesun dveří, zvýrazněné zachování, náhled a vizuální kontrola, potvrzení a otevření výsledku s přeneseným souhrnem. Fake driver čítač: chat1/image1/paid0; přesný schválený snapshot v private důkazu, historie/poznámky prázdné. Testovací panel zavřený, vlastní server ukončený. Nejde o skutečné nasazení ani placenou přejímku.

Plná brána PASS: 3453 testů, 0 chyb, 31 SKIP, 639,2 s.

Soukromé důkazy: `data/private/interior_conversation_brief_20261110/` (full_gate.log, browser_counts.json, approved_snapshot.json, preservation_before.json, qa.json). Před převzetím se znovu čte Git a aktivní vydání; lokální commit obsahuje jen výslovně zkontrolované soubory. Vývojový checkpoint byl bez p+n; následné vydání viz níže. TVBCP pro tento proud nebyl výslovně dohodnutý; nevytváří se, jeho vazba pro Human–Adam zůstává otevřená.

## Další krok

Obnovit stránku Ateliéru a provést lidskou přejímku na skutečné místnosti/iPhonu. Bez automatického placeného testu.


## 2026-11-10 21:03 CET — Souhrn zadání a oprava galerie nasazené

Hotovo: Běžící Ateliér obsahuje jedno zadání z rozhovoru s tlačítkem „Vytvořit podle tohoto zadání“ i opravu prázdných miniatur. Živá stránka zobrazuje nové rozhraní bez původních dvou vstupních polí. Stačí obnovit stránku Ateliéru.

Rozhodnutí: Mílovo výslovné „OK, předej na p+n“ se provedlo jediným registrovaným submit_release pro project-neuberk-kacenka. Oba vývojové commity 448d2902/ba2f9bbc už byly na GitHubu v následném společném balíčku MMTX; tento běh ověřil zarovnaný e867c165 a nasadil Cockpit. Runtime app/config/scripts je shodný se schváleným 448d2902. Žádný nový push, placený tah architekta ani zásah do Data.

Další krok: Obnovit stránku a provést lidskou přejímku rozhovoru a souhrnu na skutečné místnosti; iPhone zůstává samostatný.

Navrhované další kroky: Žádné nové. Výsledkový zápis zůstává místní pro další balíček; druhé p+n se kvůli němu nespouští. Nový TVBCP bez dohody nevzniká.

Technický důkaz: Účtenka 81e34ae6bd5c3f646d93706a115796e1, completed; release_executor gpt-6.1-terra/high, push_state=already_aligned, deployment_state=confirmed. Plná publikační brána 3457 testů PASS / 674,4 s, smoke 5/5, protected_services_unchanged=true. Nasazený head e867c165d97c5b09a4c06c609af820db2d1965a4, code_stamp 3a11cc681db9bcac. Adam jednou ověřil HTTP 200 a byte-identickou živou stránku (SHA-256 8c7f37f809e6a899885f0e260f1be3ad075d9543909888b0850b70e7ececad84), nový brief_protocol=interior-brief-v1 a aktivní chat/image capabilities. Shodný manifest před/po, všech 7 podkladů a 25 variant zachovaných. Soukromé důkazy data/private/interior_conversation_brief_20261110/release/. Fyzická uživatelská přejímka ani sémantický placený test nového souhrnu nejsou tímto HTTP ověřením nahrazené. Vazba TVBCP pro budoucí Human–Adam zůstává otevřená.
