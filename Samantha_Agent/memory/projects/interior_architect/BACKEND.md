# Návrh backendu 2.0

Návrh k rozhodnutí, 25. 11. 2026. Cílem je otevřít obě místnosti v jednom projektu, dohledat původ každé varianty a bezpečně vyzkoušet první úpravu fotografie. Vše běží uvnitř existující Samanthy za přístupovými pravidly Cockpitu.

## Co bude zdrojem pravdy

Navrhuji **jednu soukromou databázi SQLite a neměnné soubory médií**. Dnešní uložení celého projektu v JSON se osvědčilo pro drafty. V nové verzi se při uložení jedné varianty musí společně potvrdit několik vazeb mezi konkrétními verzemi masky, scény, média a reportu. SQLite umožní zapsat tyto vazby i účtenku příkazu jednou transakcí a vyhledat historii jedné místnosti bez načítání ostatních. Soukromé úložiště v2 bude oddělené od v1. Bez dalšího procesu nebo databázového serveru.

| Entita | Klíč a obsah | Podmínka zápisu |
|---|---|---|
| Project, Room | Stabilní ID, zobrazované jméno, pořadí. Jeden projekt, samostatná ID obou místností. | Změna názvu nemění odkazy. Každá další doménová položka patří konkrétní místnosti. |
| Asset, Blob, View | Asset nese původ, roli a titul. Blob má SHA-256, délku, typ. View váže původní soubor na normalizovaný rastr, šířku, výšku, kanály a verzi normalizace. | Stejné bajty mohou sdílet blob. Uživatel čte přes vazbu místnosti na asset. Cesta a holý hash nejsou oprávnění ke čtení. |
| Variant, Draft | Neměnná pojmenovaná varianta s volitelným rodičem, obrázkem, referencemi na přesné revize a report. Draft má vlastní revizi, poznámky, zdrojovou variantu a stav. | Textová či historická varianta smí existovat bez obrázku. Potomek i rodič musí být ve stejné místnosti. |
| MaskRevision | ID pohledu a hash jeho rastru, rozměry, orientace, seznam pojmenovaných vrstev s režimem a tahy v nativních px, verze rasterizéru a hash výsledné masky. | Posun/zoom obrazovky je pouze transformace UI. Změna podkladového rastru vyžaduje novou vazbu. |
| SceneRevision | Verze schématu a dokument scény, předchozí revize, jednotky mm. Stěny, otvory, strop, trám, vybavení, přípojky, materiály, pohledy a omezení mají stabilní ID. | Každá měřitelná hodnota nese původ a stav potvrzená, detekovaná, odhadnutá nebo neznámá. Neznámá má hodnotu null. |
| Job, Operation, Report | Job zmrazí adaptér, vstupy, jejich revize, schválený rozsah a návratovou účtenku. Operation drží jedinečné ID příkazu a otisk obsahu. Report váže výsledek na základ, kandidáta, masku a verzi validátoru. | Doručení, dostupnost souboru, integrita pixelů a geometrie mají vlastní stavy. U historických výsledků se nový report nevymýšlí. |
| LegacyMap, Tombstone | Jedinečný zdrojový prostor a původní klíč → cílový klíč, importní běh. Marker smazání eviduje původní identitu a rozsah. | Stejný vstup se při opakování páruje ke stejné identitě. Zákaz vzkříšení platí i pro obnovu z journalu. |

Zapnout cizí klíče na každém připojení. Vazby mezi entitami vynutit i podle místnosti. Binární objekt nejdřív zapsat do neveřejného dočasného souboru, ověřit délku a hash, synchronizovat a atomicky zveřejnit na stejném svazku. Potom transakčně zapsat metadata, revizi a účtenku. Po pádu před commitem zůstane nanejvýš nedosažitelný objekt. Opakování ověří existující bajty. Kontrola nedosažitelných objektů pouze hlásí jejich seznam. Historická smazání mohou sdílet obsah s dosud živým assetem, proto se uplatní na identitu a její odkazy. Záloha musí obsahovat konzistentní snapshot databáze a všechny jím odkazované objekty.

## Rozhraní pro nové UI

Názvy níže vymezují **budoucí** API. Stávající rodinný vstup zůstane na `/interior/`. Server odvodí soukromý kořen a oprávnění stejně jako dnes.

| Požadavek | Výsledek |
|---|---|
| GET `/api/interior/v2/project` | Jeden projekt, obě místnosti, počet dostupných obrázků a zvlášť počet historických záznamů. |
| GET `/api/interior/v2/rooms/{room}/workspace?variant={id}` | Vybraná větev, pracovní pohled, dostupné podklady, revize draftu/masky/scény, stav a dostupné úkony. Těžká média a historie zvlášť a po stránkách. |
| GET `/api/interior/v2/rooms/{room}/assets/{asset}/{view}` | Kontrola příslušnosti k místnosti a soukromá odpověď pro originál, rastr nebo náhled. Surový importovaný HTML/SVG/Python pouze ke stažení jako příloha. Pro prohlížení připravit bezpečný náhled. |
| POST `/api/interior/v2/rooms/{room}/commands` | Např. `saveMask`, `setMeasurement`, `moveObject`, `saveDraft`, `commitVariant`. Vstup obsahuje ID příkazu, druh, cílové ID, očekávanou revizi a vymezený payload. Vrací uložené ID/revizi nebo původní účtenku stejného příkazu. |
| POST `…/jobs/preview`, POST `…/jobs/start`, GET `…/jobs/{id}` | Náhled vypíše podklady, požadované schopnosti, cenu/limit a otisk zamýšlené operace. Start přijme schválení vážící přesně tento otisk. Po přerušení ověřit původní operaci. |
| GET `…/variants/{id}/report` | Vrátí zkontrolované hashe a rozměry, počet porušených pixelů, geometrický výsledek, důvody a dostupnost exportu. |

Příklad souběhu: iPhone i Mac mají masku v revizi 4. Mac uloží revizi 5. iPhone při uložení proti 4 dostane HTTP 409 s aktuální revizí. Jeho tahy zůstanou viditelné a lze je uložit do nové pracovní kopie. Stejné ID příkazu se shodným obsahem vrátí původní výsledek, se změněným obsahem 409. Neplatná data nebo nepovolená mutace zamčeného objektu vrátí 422 s označením pole. Cizí nebo nedostupný objekt vrátí 404 bez prozrazení jiné místnosti.

## Jak vznikne ověřený výsledek

1. **Autoritativní rastr.** Zachovat originál. Z hlavního snímku po orientaci vytvořit verzovaný bezeztrátový RGB/RGBA PNG s určenou barevnou transformací. Zaznamenat rozměry, hash a zacházení s ICC/alfa. Pokud konverze profilu není podporovaná, podklad zůstane čitelný, editor vysvětlí blokaci. Další editace i kontrola používají tentýž rastr.
2. **Maska.** Obdélník, polygon, štětec a guma mění pojmenovanou vrstvu. Neukreslená oblast je chráněná. PIXEL_LOCK a CONTEXT_ONLY vždy vítězí. GEOMETRY_LOCK dovolí jen povrchovou změnu při zachování tvaru. EDITABLE omezuje zásah na zadanou změnu a FREE_DESIGN dovoluje volnější návrh. Při překryvu vyhraje přísnější režim. Undo/redo mění pracovní revizi. Pro přesný návrat uložit i efektivní rastr masky.
3. **Kandidát a kompozice.** Ověřit rozměry, orientaci, pohled a vazbu na správný základ. Změnu rozměrů odmítnout. Nekompatibilní pohled zastavit, nerozhodnutelnou perspektivu označit k posouzení. Feathering omezit na vnitřek povolené plochy. Chráněné pixely včetně alfy převzít přímo ze základu. Po uložení a novém dekódování PNG porovnat po kanálech. Pro úspěch musí být počet změněných chráněných pixelů přesně nula.
4. **Geometrie.** Počátek scény je zvolený potvrzený referenční bod, osa X/Y v půdorysu a Z vzhůru. Otvor patří na stěnu přes vzdálenost od určeného počátku stěny, šířku a výšky. U dveří uložit dovnitř/ven, stranu závěsu při pohledu zvenku a orientaci stěny. Stejný model kreslí 2D i 3D, počítá oblouk dveří i kolizi s nábytkem. Modelová mutace zamčené geometrie musí selhat na serveru. Změna kamery mění jen pohled. Volnou fotografii lze porovnat s modelem až po registraci pohledu a doložení referencí. Výsledek je ověřeno / porušeno / neověřeno s odůvodněním. Neověřený obrázek lze uložit jako označený koncept, porušený zobrazit v kontrole. Ani jeden se nenabízí jako ověřený výstup.
5. **Adaptér.** Deklaruje podporované vstupy, nativní masku, inpainting, strukturální referenci, omezení rozměrů, síť a náklady. První implementace používá označený lokální testovací obrázek. Požadavek na nepodporovanou funkci se zastaví před odesláním. Náklady neznámé či mimo schválený limit blokují start. Jediný schválený start dostane trvalou účtenku před odesláním. Při nejistém doručení pouze ověřit původní výsledek.

## Pořadí implementace a přejímka

| Milník | Ukázka pro Mílu | Ověření |
|---|---|---|
| 1. První pracovní řez | Na syntetickém projektu otevřít místnost, v jedné fotce ochránit okno, upravit část stěny lokálním kandidátem, uložit, znovu otevřít a porovnat. | T01–T07, T14–T16 a příslušná T18 ze [zadání](reference/TEST_PLAN.md). Zvlášť Mac a iPhone, konflikt revize, RGBA, nulová změna po PNG a odmítnutí změněného rozlišení. |
| 2. Historie místností | Verze čte oddělenou zkušební kopii obou místností. Návrhy, dostupné obrazy, drafty i stará smazání jsou dohledatelné. | T08/T14/T18 a úplná [přejímka importu](MIGRATION.md), včetně opakování a pádu. |
| 3. Scéna a půdorys | Změřit stěnu, osadit otvor, posunout nábytek. Zamčené dveře zůstávají na místě, oblouk ukáže kolizi. | T09–T12 a T17 pro 2D. Neznámé hodnoty a odhady mají vlastní vykreslení. |
| 4. Jeden model pro 3D a obraz | Dvě kamery zobrazí stejný otvor. Kontrola fotografie pravdivě přizná neověřenou perspektivu. Připojení skutečného adaptéru je oddělené rozhodnutí. | T13, T15–T19, lokální výkon a licence konkrétní verze, offline 3D a lidská přejímka obou zařízení. |

Pořadí je návrh. První milník lze posoudit bez přepnutí rodinného vstupu a bez přístupu k rodinným fotografiím.
