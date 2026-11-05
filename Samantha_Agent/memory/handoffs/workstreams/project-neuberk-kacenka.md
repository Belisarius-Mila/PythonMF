# Neuberk interiér a Interiérový ateliér

Pracovni proud: project-neuberk-kacenka
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-11-05

## 2026-11-05 — oprava příjmu iPhone JPEG/MPO

Míla při praktickém zkoušení narazil na odmítnutí tří iPhone JPEG po cca
2 MiB, 4032 × 2268 px. Příčina živě reprodukovaná: dekodér je kvůli druhé
pomocné obrazové vrstvě klasifikuje jako MPO, které příjem nepovoloval.
Nejde o překročení limitu 6 MiB ani 32 Mpx. Chyba byla ve validačním kódu.

Lokální oprava povoluje JPEG/MPO, používá výhradně hlavní obraz seek(0),
respektuje EXIF orientaci a vytváří statické náhledy bez metadat. Originál
zůstává přesně zachovaný včetně pomocných vrstev, MIME image/jpeg.
PNG/WebP animace se dál odmítají a původní limity se nezvyšují. Chybové
hlášky nyní oddělují nepodporovaný formát a příliš velké rozlišení.

Ověření: regrese před opravou FAIL, po opravě 30 cílených testů PASS.
Všechny tři skutečné fotografie mají úspěšný decode i odvozené náhledy;
izolovaný příjem tří souborů, znovunačtení a shoda originálů ověřené.
Plná brána PASS: 2 530 testů, 2 499 PASS, 31 SKIP, bez selhání (493,044 s).
Report:
memory/reports/interior_iphone_jpeg_mpo_20261105.md.
Živý projekt a původní soubory se při zkoušce neměnily. Oprava zatím
není nasazená; tento požadavek byl diagnostika aktuální chyby, nové p+n
zatím výslovně nezaznělo. AI a chybějící TVBCP zůstávají samostatné.

### Následné potvrzení vydání

Míla poté výslovně potvrdil „Ano, nasaď prosím…“. Ověřená oprava b449f805
je schválená k registrovanému Terra p+n v project-neuberk-kacenka společně
s tímto potvrzovacím zápisem. Konečný výsledek podle účtenky
logs/interior_mpo_release_20261105.log a následného čtecího ověření
logs/interior_mpo_verified_20261105.log. Předchozí čekání na souhlas je
tím překonané; úspěch se nevydává za potvrzený před dokončením úlohy.

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

## 2026-11-05 — výslovně schválené společné p+n

Míla zadal „ok p+n pro vše“: schvaluje vydání celého hotového rozsahu
lokálního main včetně Ateliéru a zápisů uzavřené přejímky 05/P1.
Předchozí omezení na lokální vývoj tím pro tento balíček končí. Oddělená
Datova větev se bez integračního zadání nepřebírá. Vydání provede jediný
registrovaný submit_release(wait=True), vykonavatele vybere centrální role.
Výsledek až podle konečné účtenky a živého ověření; nikoli podle tohoto
předběžného zápisu. Místní důkazy: logs/interior_all_release_20261105.log
a logs/interior_all_verified_20261105.log. Mac/Safari přejímka Jany zůstává
samostatná; AI modely ani nový TVBCP se tímto pokynem nezavádějí.
