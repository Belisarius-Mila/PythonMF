# Neuberk interiér a Interiérový ateliér

Pracovni proud: project-neuberk-kacenka
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-11-05

## Aktuální vývojový krok

Míla schválil rozložení Ateliér: samostatná celoobrazovková pracovní plocha,
varianty vlevo, velký obrázek uprostřed, zasouvatelný rozhovor vpravo.
Human–Adam je koncepční inspirace; architekt má vlastní UI.

Lokální první milník přidává projekty a místnosti, explicitní příjem PNG/JPEG/
WebP, označení skutečnosti/plánu/inspirace, pracovní obrázek a výběr referencí,
kreslené poznámky, verzované rozpracované zadání, neměnné odvozené varianty,
porovnání s rodičem a poznámky vázané na konkrétní návrh.

Vstup: Janička → Rodinné projekty → Interiérový ateliér, samostatná /interior/.
Full-screen API má fallback na celé okno. Nový stav vzniká teprve explicitním
zápisem do odděleného soukromého atelier úložiště. Čtecí vstup nic nezakládá.

## Hranice a bezpečnost

- AI rozhovor ani generování zatím nejsou připojené. Galerie ukazuje pracovní
  obrázek a skutečně uložené lidské zadání; nevydává kopii podkladu za AI návrh.
- 2D rozměrový model, Konva, 3D, kolize a placené obrazové modely jsou další
  milníky; tento krok nepřidává závislosti ani nemění role či App Server.
- Starší fotografie, rozměry a návrhy Kačenky se neimportují, nepřepisují,
  nemažou ani neodesílají. Původní návrhová práce zůstává zachovaná.
- Originály nových uploadů jsou neměnné, náhledy bez EXIF/textových metadat;
  čtení ověřuje místnost, hash a odmítá symlinky. PNG/JPEG/WebP do 6 MiB,
  nejvýše 32 milionů pixelů; animace nejsou přijímané.
- Explicitní operace mají stabilní identitu a otisk obsahu, ukládání používá
  transakční repository. Konflikt revize zachová novější serverové zadání
  i vlastní rozepsaný text pro vědomé porovnání.
- Oprávnění přístupu přebírá stávající Cockpit. Samostatné účty/role Jany
  tento milník nezavádí; nejde o doloženou izolaci jednotlivých uživatelů.
- Soukromé podklady a uživatelské texty patří mimo Git. Logy, handoff a
  report obsahují jen obecné technické důkazy.

## Ověření a vydání

Lokální milník PASS: 50 cílených Python testů včetně 8 Node scénářů,
23 frontendových kontraktů a statická brána. Plná brána persistence:
2 519 testů, 2 488 PASS, 31 SKIP, 0 chyb/selhání (451,172 s). Důkaz:
memory/reports/interior_atelier_p1_20261105.md a příslušné logy.
Skutečná Mac/Safari/iPhone přejímka se nevydává za provedenu.
Push, nasazení ani restart hlavního Cockpitu nejsou tímto vývojem povolené.

## Kanonická paměť

Tento handoff odpovídá existující vazbě WorkstreamMemoryRegistry. Historické
návrhy místnosti zachovává neuberk_kacenka_south_wall_v6_geometry_checkpoint_2026_06_07.md.
Projektová paměť: memory/projects/neuberk_interier_design.md.

Kanonická cesta TVBCP je podle registru
memory/tvbcp/workstreams/project-neuberk-kacenka.md, ale dokument dosud
neexistuje. Nový TVBCP nebyl výslovně domluven a nevzniká ani tímto terminálovým
krokem. Před pozdějším vývojem/předáním přes Human–Adam je nutné tuto vazbu
dořešit; stav je viditelně otevřený podle project_tvbcp_rules.md.

## Další krok

Lokálně dokončený první milník předložit Mílovi. Nasazení a skutečný
Mac test Jany jsou samostatné. Následující věcný milník je ověřená multimodální
cesta a řízená obrazová editace se zvoleným modelem a rozpočtem.


## 2026-11-05 14:15 CET — první lokální milník ověřený

Hotovo: Funkční místní Ateliér, explicitní podklady, rozpracovaná zadání,
neměnné odvozené varianty a připomínky; plná brána PASS.
Rozhodnutí: Schválené rozložení Ateliér; placené modely a nasazení zvlášť.
Další krok: Samostatně schválit vydání a provést skutečný Mac/Safari test.
Navrhované další kroky: Omezený multimodální a obrazový pilot se zvoleným
modelem/rozpočtem; rozměrový půdorys a 3D až navazující milníky.
Technický důkaz: 2 519 testů / 31 SKIP, bez selhání; cílené nové moduly
28 PASS bez SKIP; report interior_atelier_p1_20261105.md.
