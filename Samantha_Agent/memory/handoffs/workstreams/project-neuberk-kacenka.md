# Neuberk interiér a Interiérový ateliér

Pracovni proud: project-neuberk-kacenka
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-11-05

## 2026-11-05 21:04 CET — schválený živý AI pilot a příprava nasazení

Míla přesnou větou globální brzdy schválil Terra/high, jeden rozbor vybraných
soukromých podkladů, jeden obrazový požadavek, následné Terra p+n a registrovaný
upgrade kompatibility vlastní e-mailové služby. Není nutné souhlas opakovat.

Živý pilot je přijatý. Proběhl právě jeden potvrzený chatový tah a jeden
potvrzený obrazový tah přes původní sdílený socket/server 0.163.0. Obrazový tah
vrátil dva platné PNG (1672 × 941) a rozporný chybový text; oba skutečné
výsledky byly místně ověřené a uložené jako dvě neměnné AI varianty bez dalšího
modelu. UI stav vychází z ověřených artefaktů a nabízí otevření obou variant.
Žádný další placený pilot se nespouštěl. Původní zadání má stále revizi 7,
původní podklady zachované; model dostal jen jeden explicitně vybraný podklad.

Dvě přípravná selhání nepřijala žádný modelový tah. Dokumentovaný readOnly.access
server odmítá; používá se explicitně povolené permission-profile API, soukromý
profil pouze v konfiguraci konkrétního vlákna, minimální systémové čtení a čtení
snapshotu bez zápisu/sítě. Server musí potvrdit přesný profil, cwd, model a
approvalPolicy=never. Prázdná konfigurace permissions=null je ošetřená.
Pokračování přípravy zachovalo původní job/client ID/vlákno a vyžadovalo
nečinné vlákno, pouze metadatový rollout a doloženou sondou zakázané odesílání.
Timeout ani skutečný dřívější tah opakovat nelze. Globální konfigurace a App Server
se neměnily. Rychlost je výslovně Standard; zděděné priority/Fast se nepoužije.

Kritický modelový klient, instrukce a oprávnění mají otisk skutečné exekuce.
Následná oprava pouze zpracování obrazových artefaktů byla ověřená přehráním
původních terminálních journalů; změna exekučního otisku takové ověření blokuje.
Důkaz: logs/interior_ai_pilot_verified_20261105.log; cílených 133 testů PASS
včetně 4 Node DOM scénářů; závěrečná plná brána PASS: 2574 testů,
0 chyb, 31 přeskočených (393,754 s). Soukromé důkazy, fotografie
a odpovědi zůstávají mimo Git. Centrální role ještě není zapsaná ani aktivní.

Další krok: checkpoint a registrované kompatibilní p+n přes Terru,
upgrade vlastní e-mailové kopie se zachováním business stavu, potom aktivace role
z přijatého důkazu a závěrečné p+n. Nový TVBCP stále nebyl domluvený.
Starší záznam o čekajícím souhlasu níže je historický, nyní překonaný.

## 2026-11-05 — zapojení AI, lokální příprava aktivace

Míla po praktickém vyzkoušení Ateliéru zadal „Zapoj teď AI“. Oprava iPhone
JPEG/MPO je už nasazená do b9b59c7d, CI 42083732254 success; tehdejší CI
bylo spuštěné ručně kvůli chybějícím filtrům cest. Ty jsou nyní doplněné.

Lokálně je připravený skutečný AI rozhovor nad vybranými podklady a samostatná
obrazová varianta. Každý požadavek má neměnný snapshot zadání, podkladů,
kreslených značek a rozhovoru konkrétní varianty. Generovaný obrázek vytvoří
nový neměnný návrh; původní podklady a novější rozepsané změny zůstanou.
Asynchronní UI rozlišuje čekání, výsledek, neúspěšné generování a neověřené
doručení. Ověření původního výsledku neprovádí další modelový tah.

Připojení používá současný sdílený App Server a jeho localImage vstupy.
Model má jen vybrané metadata-free náhledy, omezené čtení snapshotu,
vypnutý shell, konektory, paměti, web a delegaci. V chat režimu je systémově
vypnuté generování obrázků; povolí se jen samostatnému obrazovému požadavku.
Volba modelu je připravená pro centrální roli interior_architect. Produkční
config/agent_roles.json zatím není změněný a neproběhl žádný placený pilot.

Ověření: 145 cílených Python kontrol PASS, včetně 3 nových Node DOM scénářů
a původních 8 frontendových scénářů. Závěrečná plná brána PASS: 2559 testů,
0 chyb, 31 přeskočených (388,844 s). Lokální krok je dokončený; bez push a nasazení. Report: memory/reports/interior_ai_integration_20261105.md.

### Otevřené vstupy a brány

- Asynchronně je položená volba Terra/high: jeden skutečný rozbor vybraných
  soukromých podkladů, případně navíc jeden obrazový návrh. Odpověď dosud
  není doložená. Bez ní se placený pilot nespouští. Sazby byly znovu ověřené
  v oficiální dokumentaci; nejde o pevný slib ceny jednoho obrázku.
- Nasazení tohoto nového AI balíčku nebylo výslovně zadáno; předchozí p+n
  se vztahovalo k opravě MPO. Pro živé zapnutí je nutný kompatibilní Cockpit
  a pak přijatý pilot / centrální modelová politika.
- Skutečný čtecí audit zjistil, že hodinová e-mailová kopie ac9f3bed má
  starší KNOWN_ROLES bez interior_architect. Přidání nové role by ji rozbilo.
  Aktivace je proto blokovaná, dokud registrovaný upgrade její vlastní kopie
  nedoplní kompatibilní parser. Služba ani její data se zatím neměnily.
  Upgrade vyžaduje přesnou globální potvrzovací větu; běžné „zapoj AI“ ji
  nenahrazuje. Příprava respektuje app/email/service_control.py a global_safety_brake.md.
- Model se zpřístupní až po nasazení s odpovídající politikou; samotná změna
  JSON jej v běžícím starém procesu nezapne. Starý parser Cockpitu také nesmí
  dostat novou roli před prvním kompatibilním p+n.
- Nový TVBCP stále nebyl domluvený; nevzniká tímto terminálovým krokem.

Další krok: dokončit checkpoint, získat volbu pilotu a konkrétní souhlas
k následnému kompatibilnímu nasazení / servisnímu přepnutí. Teprve po živém
ověření lze tvrdit, že AI v uživatelově Cockpitu skutečně pracuje.

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
