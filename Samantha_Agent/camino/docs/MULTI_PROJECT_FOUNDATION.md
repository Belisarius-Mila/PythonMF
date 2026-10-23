# Více cest a dovolených — základ, kroky 1–2

Rozhodnutí Míly 23. 10. 2026: rozšířit stávající aplikaci na více projektů
se stejným pořizováním a zpracováním dat. Nyní schválené kroky 1–2,
nikoli automatické vydání, instalace nebo změna živého archivu.

## Společná identita a metadata

Projekt je dosavadní Trip se stejným UUID. Nemění se bundle ID aplikace,
adresáře originálů, identity Momentů/Assetů, původní operace ani filmové
projekty. Název zůstává samostatnou historií set_trip_title.

Volitelné start_date/end_date a status active/archived se ukládají operací
set_project_details. Obě data mohou být null; platná kalendářní data musejí
být YYYY-MM-DD a konec nesmí předcházet začátku. Neexistuje minimální délka
výletu. Termín je popis projektu, nikoli filtr nebo přepis dat záznamů.

Původní create_trip se nemění. Místní historie je v existujícím SettingRecord,
serverová v accepted_operations, bez migrace Core Data či SQLite schématu 3.
Chybějící historie znamená active, původní start_date a end_date=null.
Vybraný projekt je místní volba telefonu; historické pole Trip.active není
serverový výběr ani archivace. Více projektů může současně zůstat active.

Archivace nemaže a nezastavuje již připravené přenosy či finalizaci původního
záznamu. Nový místní Moment/audio/media intent vyžaduje znovu otevřený projekt.
Výběr archivovaného projektu pro čtení zůstává možný. Archivace není nová
privacy volba ani neměnný zámek již existujících textových revizí.

## Kontrakt vlastníka

Příprava ovládání projektů (23. 10.): createTrip a updateTrip přijímají
volitelné detaily formuláře a uloží název, příznak Zkoušky i detaily v jedné
místní transakci. Neplatný termín nezaloží částečný projekt ani nepřejmenuje
původní; stávající volání bez detailů zachovávají dosavadní význam.
Výběr projektu vrací úspěch a vyčistí dřívější detail Momentu. Sdílené
příznaky modelu oddělují možnost správy projektů od možnosti nového záznamu;
archiv lze dál vybrat pro čtení, nové pořizování vyžaduje active.

- GET /api/v1/projects: soukromý katalog přijatých projektů.
- GET /api/v1/projects/{trip_id}: konkrétní přijatý projekt.
- POST /api/v1/operations, kind=set_project_details, payload přesně
  trip_id, start_date, end_date, status. Vlastní details_revision začíná 1,
  každá přijatá změna ji zvýší; nezávisí na revizi názvu ani Momentů.
- Vyžaduje serverovou schopnost project_details_v1 před odesláním nové změny.
  Staré fronty bez nových revizí dál fungují se starým serverem. Nová fronta
  nepokračuje proti serveru, který by novou operaci neuměl zpracovat.

Katalog vrací pouze metadata vlastníka a aktuální viewer_enabled. Není
Viewer projekcí a read-only token čtenáře k němu nemá oprávnění. Bez historie
se neodvozují nové granty; nové cesty telefonu začínají s Viewerem vypnutým.
Výstupy pro Janu ani film se tímto krokem nerozšiřují na další cesty.

## Oddělení projektů a přenosů

Vazba zůstává Trip → Day → Moment → Asset. Den určuje dvojice UUID projektu
a místní datum, nikoli datum samotné nebo název. Různé projekty smějí mít
stejné názvy a stejné dny; druhé ID pro stejný den téhož projektu se odmítá.
Před sestavením fronty se odmítne neúplný inventář, duplicitní identity
nebo chybějící rodiče. Server dále ověřuje rodiče a vazby mezi projekty.

Discovery sbírá všechny projekty, ne pouze právě vybraný. Existující položky
fronty, přesné serializované obálky a přenosové stavy se při novém discovery
nepřepisují. Serverové upload sessions váže stabilní Asset, ne aktivní projekt.
Přepnutí při čekání na GPS/import/audio je blokované; příprava foto/video
po asynchronním čekání ještě ověří původní projekt.

Čtecí kontrola archivu při budoucím upgradu zachová i další naplněné projekty.
Legacy Viewer stále vyžaduje explicitně vybrané existující trip_id; bez
výběru se mezi více projekty nehádá. Hashuje se celý archiv, včetně všech
cest, ověřených originálů, identity a kurzoru, s kontrolou FK.

## Ověření

- Swift: 81 testů PASS, včetně opětovného otevření SQLite, archivace,
  dokončení starého intentu, obnovení projektu a neplatných dat.
- Skutečný Swift/Core Data fixture: dva projekty se stejným názvem a datem,
  samostatné dny/Momenty/média, stará zmrazená fronta a rozpracovaný upload.
- Izolované Python API a MediaStore: replay a restart, původní create_trip,
  původní Momenty a schema 3 zachované. Upload A dokončen po přijetí B;
  soubory A/B mají správné bajty a vlastní vazby. Cizí Day/Moment a konflikt
  revize odmítnuté, granty Vieweru se nepřenášejí mezi projekty.
- Cílená sada před doplněním HTTP přejímky: 57 testů PASS. Nová HTTP zkouška
  ověřuje owner-only katalog, detail a capability. Závěrečná plná brána
  2180 testů PASS (455,777 s unit část), bez přeskočení. Nepodepsaný generic
  iOS Debug build PASS; podpis, nová IPA ani instalace nebyly provedené.

Důkazy jsou v data/private/camino_projects_20261023/, bez reálných médií
nebo soukromých textů ve verzované dokumentaci.

## Navazující kroky a vydání

Krok 3 nabídne metadata/archivaci v ovládání telefonu; nyní jde o datový
a přenosový základ. Krok 4 doplní výběr a oprávnění ve Vieweru/Macu, krok 5
projektový výběr střižny, krok 6 celkovou fyzickou přejímku. Spojení denních
filmů do celé dovolené zůstává později. Nová aplikace, nový Human–Adam proud,
nové TVBCP ani veřejné sdílení se nezakládají.

Pro zavedení nejprve samostatně schválit a ověřit aktualizaci soukromé služby
Camino, potom stejné aplikace na iPhonu bez odinstalace; běžné p+n Cockpitu
nenahrazuje ani jeden krok. Před živou aktualizací ověřit zálohu a otisky
existujícího archivu/střihů a po ní jejich zachování. Fyzické přepínání,
mikrofon, fotografie a video nové verze zatím NEOVĚŘENO.
