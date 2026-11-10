# MMTX – odstranění šesté scény u jezera

- 2026-11-10 11:42 CET: Míla výslovně schválil odstranění šesté scény u jezera a potvrdil globální brzdu. V kanonických `docs/scene06_lake_arrival/` i `MatysekANJ/web_mmtx/scene06_lake_arrival/` zůstal pouze první obrázek `arrival.webp` (380134 B, SHA-256 `038d273ff95d3077fe26d142ad32ca6fc32d0e9b5c6997ea53c161964fedcf65`).
- Ostatní média a kód šestky jsou místně odstraněné: 144 MP3 a tři další obrázky v každé kopii, scénářová data, generátor a jeho dva testové moduly. Oba Azure workflow příkazy a odkazy z páté scény jsou odstraněné; dokončení mostu zůstává jako neklikací stavová zpráva. Sdílené TTS moduly se nemění.
- Scény 1–5, jejich média, Logan i obrázek loučení zůstávají zachované. Ze starších scén se mění pouze HTML konce páté scény a CSS zrušené zkratky v obou mirrorech; všechny ostatní soubory odpovídají předchozím otiskům. Cílená sada most/registry: 51 PASS; plná brána 3402 testů, 0 chyb, 31 přeskočených (700,764 s unit; 707,1 s brána).
- Datova větev má novější vlastní commit; ten byl zachovaný beze změny. V jejím stávajícím worktree jsou pouze související WIP změny odstranění šestky (321 cest), bez merge/rebase a bez přepsání jiné práce.
- Rozsah úklidu pěti známých pracovních prostředí a oddělených hlasových ukázek je 1584 souborů / 35524901 logických bajtů. Další kopie budou srovnány po kanonickém commitu; celkové místo skutečně uvolněné na APFS se může lišit. Historie Gitu a zálohy nejsou přepisované ani promazávané.
- Nesouvisející změny zdrojového checkoutu jsou dočasně bezpečně odložené pro čisté vydání a poté se vrátí. Nově přidaný necommitovaný scénář šestky je mimo schválený mazací seznam a zůstává zachovaný. Soukromý kontrolní manifest, otisky a návrh změn jsou mimo Git.
- Další krok: místní checkpoint, zarovnání známých kopií a jediné registrované p+n `project-mmtx` / GitHub Pages. Veřejné odstranění zatím tímto zápisem není potvrzené.

## Ověřovací hranice

- Zachovat první obrázek na jeho dosavadní veřejné i místní adrese; stránka šestky, její ostatní obrázky a všechny EN/CZ MP3 mají po vydání vracet 404.
- Ověřit veřejně zachované vstupy scén 1–5 a přesné bajty souborů scény s mostem a Loganem.
- Neměnit jiné aplikace na sdílených Pages ani chráněné služby Samanthy.
- Starší reporty popisují historické vytvoření šestky a nejsou aktuálním pokynem k jejímu obnovení.
