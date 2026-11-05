# První lokální Interiérový ateliér

Datum: 2026-11-05. Proud: project-neuberk-kacenka. Autor: Will.
Výchozí zdroj: 040fea774beebd1f1274fbcc0d997eb7b6badb49.

## Výsledek a uživatelský tok

Schválené rozložení Ateliér je samostatná celoobrazovková plocha dostupná
z Janička → Rodinné projekty. Nahoře se volí projekt a místnost, vlevo jsou
varianty, uprostřed pracovní obrázek a vpravo zasouvatelné zadání/připomínky.
Podklady a úprava návrhu mají samostatný pracovní pohled se zpětným návratem.

Uživatel vytvoří projekt a místnost, přidá vlastní PNG/JPEG/WebP a označí
skutečný stav, náčrt/rozměry nebo inspiraci. Pro konkrétní návrh vybere
reference a pracovní obrázek, zadá požadovanou změnu a pevné prvky, může
kreslit poznámky nad obrázkem. Rozpracované zadání ukládá explicitně; nová
varianta je neměnná a nese vazbu na rodiče. Porovnání ukáže rodičovský návrh.

Galerie nepředstírá AI výstup: zobrazí podklad s uloženými kreslenými poznámkami
a lidské zadání. Pravý panel výslovně uvádí, že AI ještě není připojená.
Rozměrový půdorys, kolize, Konva, 3D a obrazové modely jsou další milníky.

## Ukládání a bezpečnost

- Nový stav je v odděleném soukromém atelier úložišti. Původní soukromé
  návrhy a podklady se nepřesouvají ani automaticky neimportují.
- Čtení ani import Python modulu nezakládají projekty či soubory.
- Metadata používají stávající JsonWorkRepository, procesový souborový zámek
  a atomický zápis. Explicitní operace mají UUID a otisk obsahu; opakování
  stejné identity vrátí účtenku, jiný obsah se stejnou identitou je konflikt.
- Rozpracované zadání má vlastní revizi pro projekt/místnost/výchozí variantu.
  Zastaralý klient novější text nepřepíše. Editor uchová neuloženou práci
  v konkrétním prohlížeči; při konfliktu ukáže možnost porovnat a vědomě
  převzít poslední serverovou verzi.
- Originály jsou obsahově adresované a neměnné. Náhledy mají odstraněná
  obrazová metadata. Skutečný formát se dekóduje, nikoli odhaduje z názvu.
- Limit je 6 MiB a 32 milionů pixelů na statický obrázek. SVG, PDF, HEIC
  a animace se odmítají s vysvětlením. Neexistuje vstup pro libovolnou cestu.
- Výdej souboru ověřuje vlastnictví v místnosti, obsahový hash, velikost,
  pravidelný soubor a symlinky. Odpovědi mají no-store a sdílené bezpečnostní
  hlavičky Cockpitu; zápisy podléhají stávající kontrole Origin/Host.
- Přerušení před zveřejněním metadat může ponechat nepřipojený obrazový
  objekt. Žádný automatický úklid se neprovádí, neúplný podklad se nevydává.
- Stávající přístupová hranice Cockpitu není samostatný účet Jany. P1
  nezavádí ani neslibuje izolaci jednotlivých uživatelů.

## Ověření

- Cílená sada: 50 Python testů PASS, včetně bezpečného příjmu, metadat,
  neměnných originálů, opakovaných požadavků, souběhu, restartu a skutečného
  HTTP toku. Frontendový wrapper v této sadě provádí 8 Node scénářů:
  kontexty, opožděné odpovědi, obnova neuložených úprav, konflikt revizí,
  ochrana před vložením značek a normalizované souřadnice kresby.
- Frontendové kontrakty: 23 PASS, aktualizované přesné otisky rozšířeného
  Cockpitu a nového Ateliéru; kontrola původních stránek zachovaná.
- Rychlá statická brána PASS. Povinná plná brána persistence PASS: 2 519
  testů, 2 488 PASS a 31 SKIP, 0 chyb/selhání; unittest 451,172 s.
  Cílené nové moduly mají 28 PASS a žádný SKIP. Žádný test nebyl oslaben.
- Živá uživatelská Mac/Safari/iPhone přejímka není provedená. Browser host
  byl v této relaci nedostupný; automatické DOM/protokolové testy ji nenahrazují.

Důkazy: logs/interior_atelier_targeted_20261105.log,
logs/interior_frontend_contract_20261105.log,
logs/interior_atelier_static_20261105.log,
logs/interior_atelier_full_gate_20261105.log.

## Rozsah vydání a další krok

Lokální zdrojový krok, žádný push, nasazení ani restart hlavního Cockpitu.
Žádná změna App Serveru, jeho klienta/transportu, rolí, SDK, živých e-mailů
nebo služeb. Nula nových placených modelových tahů a žádné nové závislosti.
Datův worktree je zachovaný; starší necommitované zápisy 05/P1 se do tohoto
checkpointu nezahrnují.

Před fyzickou přejímkou Jany je třeba samostatně schválit vydání. Následující
věcný milník má ověřit multimodální analýzu a obrazovou editaci na omezeném
vzorku se zvoleným modelem a schváleným rozpočtem.

Kanonický handoff a projektová paměť jsou aktualizované. Nový TVBCP nebyl
výslovně domluven ani vytvořen; registrovaná cesta je dohledatelná v handoffu.
Před vývojem či předáním přes Human–Adam tuto vazbu dořešit.
