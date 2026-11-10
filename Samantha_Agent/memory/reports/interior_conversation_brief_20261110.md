# Interiérový ateliér — zadání z rozhovoru

Stav: lokální vývoj, 2026-11-10 19:50 CET; bez push/nasazení. Proud `project-neuberk-kacenka`, podklad `ba2f9bbc`, vlastní větev `adam/interior-conversation-brief-20261110`. Zahrnuje dosud nevydanou předchozí opravu prázdných AI miniatur.

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

Soukromé důkazy: `data/private/interior_conversation_brief_20261110/` (full_gate.log, browser_counts.json, approved_snapshot.json, preservation_before.json, qa.json). Před převzetím se znovu čte Git a aktivní vydání; lokální commit obsahuje jen výslovně zkontrolované soubory. Bez p+n. TVBCP pro tento proud nebyl výslovně dohodnutý; nevytváří se, jeho vazba pro Human–Adam zůstává otevřená.

## Další krok

Samostatně autorizované p+n obou lokálních změn a následná lidská přejímka na skutečné místnosti/iPhonu. Bez automatického placeného testu.
