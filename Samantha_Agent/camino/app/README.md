# Camino — iPhone aplikace

První integrovaná iPhone aplikace Camina. Má vlastní bundle ID
`cz.pythonmf.camino.app` a vlastní Application Support kontejner; nepřebírá ani
nemigruje data ze samostatných prototypů Camino Audio a Camino Transfer Test.

## Aktuální používání — 23. 10. 2026

Vývoj kroků 1–3 nabízí více projektů: samostatný název, volitelné termíny,
archivaci a oddělené záznamy/přenosy. Nabídka → **Projekty** otevře seznam
Probíhající / Archivované, založení a **Upravit projekt**. Archiv lze číst;
pro nové záznamy vypni archivaci a ulož. Termíny lze ponechat prázdné,
neplatný rozsah se neuloží. Výběr projektu zůstává zachovaný po restartu.
[Kontrakt](../docs/MULTI_PROJECT_FOUNDATION.md) a
[ovládání/přejímka](../docs/PROJECT_MANAGEMENT_UI_REPORT.md).

Jde o nové zdroje, nikoli aktualizaci nainstalovaného telefonu. Před
instalací nejprve ověř samostatný server s project_details_v1; p+n Cockpitu
telefon ani tuto službu neaktualizuje.

Poslední připravený Release je 0.1.0 (20). Zoom Míla uživatelsky přijal;
přesná nainstalovaná verze a všechny okrajové scénáře nejsou tímto
potvrzením samostatně doložené. Podrobnosti a otevřené fyzické kontroly
jsou v [reportu zoomu](../docs/CAMERA_ZOOM_REPORT.md).

### Místní podpis při vývoji

Osobní tým patří do ignorovaného `LocalSigning.xcconfig`, který načítá
`Config.xcconfig` pro Debug i Release. Verzovaný projekt nemá vlastní
přepis DEVELOPMENT_TEAM; tím zachová místní podpis a čistý main potřebný
pro přepínání proudů Human–Adam. Změnu týmu prováděj v místním xcconfig;
volba přímo v Xcode může vytvořit další přepis v projektu, který je třeba
před další prací zkontrolovat. Osobní podpisové údaje necommituj.

### Foto a video se zoomem

1. Vyber cestu a Moment; fotografii nebo video připoj ke správnému Momentu.
2. V náhledu použij gesto dvěma prsty nebo dostupné volby 0,5× / 1× / 2×.
   Kamera nabízí jen podporovaný rozsah; výchozí pohled je 1×.
3. Zoom můžeš měnit i při běžícím videu. Volba zvuku zůstává samostatná.
   Vyšší digitální přiblížení může snížit kvalitu, 2× není příslib optického zoomu.
4. Po ukončení záznamu ověř uloženou položku. Originály zůstávají v aplikaci;
   automaticky se neukládají do Fotek a nemažou se.

Ostření dotykem, ruční expozice a blesk nejsou součástí této změny.
Při aktualizaci zachovej stávající identitu aplikace a neodinstalovávej
Camino s daty; samotné p+n Cockpitu telefon neaktualizuje.

### Text z deníku do střižny

1. V detailu Momentu uprav text a vědomě zvol **Uložit**. Rozepsaný koncept
   sám není přijatá textová revize na Macu.
2. Dokonči přenos v **Uložení a přenosy** a ověř stav Macu. Místní uložení,
   přenos médií a přijetí textové operace jsou odlišné kroky.
3. V Cockpitu otevři **Film Camino**, správný den a uložený projekt.
   Použij **Načíst poslední střih a texty**; před načtením zachovej nebo ulož
   případné rozpracované úpravy filmu.
4. V panelu **Texty a komentáře** se nabídne povolený přijatý text.
   Vložení do titulku nebo karty upraví pouze filmovou revizi.

**Jen pro mě** a skryté položky se ve filmu nenabízejí. Samostatnou Úvahu
je nutné nejprve vědomě vložit do deníku a nechat přijmout změnu soukromí;
film tuto volbu neobchází. Hlasové nahrávky se automaticky nepřepisují.
Není-li text ve střižně, ověř den, skutečné Uložit a přijetí na Macu.
Podrobný [návod střižny](../film/README.md) popisuje titulky, karty i vlastní hlas.

## Starší technický přehled C04a–C05c

Následující etapové popisy a datovaná přejímka jsou technická historie.
Aktuální vydání určují přehled výše, projektová paměť a přesné účtenky.

## Výběr z Fotek (2026-10-03)

Detail okamžiku nově nabízí **Vybrat z Fotek** pro jednu fotografii/video.
Originál v knihovně zůstane zachovaný; import dědí okamžik a jeho soukromí.
Fotografie se připravují jako JPEG, Live Photo jako statický snímek;
video jako MOV bez překódování stop. Stav čekání je viditelný a načítání
lze zrušit. Přesné hranice a fyzický test jsou v
[PHOTO_LIBRARY_IMPORT.md](../docs/PHOTO_LIBRARY_IMPORT.md).
Míla 2026-10-03 fyzicky potvrdil vložení 14s videa a jeho přenos;
HEIC, iCloud a další okrajové scénáře zůstávají neověřené.

## Rozsah

- Offline založení a přepínání cest včetně oddělené Zkoušky.
- Místní Core Data SQLite evidence cesty, dne, označeného okamžiku, nového
  Momentu s audiem a jeho původního místního času včetně UTC offsetu.
- Trvalá volba soukromí pro nové běžné Momenty. První hodnota je `diary`;
  starší Momenty se změnou volby nemění a samostatná Úvaha vždy vzniká
  `owner_only`.
- Přímé znovupoužití přijatého C01c audio jádra bez změny prototypu. Identita
  cesty a soukromí se uloží k audio session před spuštěním mikrofonu. Po
  ověření dokončeného journalu se session idempotentně naváže na Moment. Po
  restartu se vazba obnoví; neznámá či nedokončená nahrávka zůstane zachovaná
  a viditelně čeká na kontrolu. Soukromí Komentáře lze při nahrávání změnit pro
  celý nový Moment, bez změny výchozí volby; Úvahu takto odemknout nelze.
- Domovská obrazovka s dnešními Momenty a pravdivým místním stavem. Obsah se
  při ztrátě aktivní scény překryje neprůhlednou plochou.
- Foto a video z vestavěné kamery s výslovným připojením ke konkrétnímu Momentu.
  Samostatné snímky vytvářejí samostatné Momenty; komentář ze záběru nebo detailu
  dědí soukromí cílového Momentu. Originály jsou v soukromém úložišti aplikace,
  neukládají se do Fotek a aplikace je automaticky nemaže.
- Před zápisem originálu se uloží identita záměru; u videa ještě před startem
  nahrávání. Foto se potvrdí až po ověření souboru
  a databáze; video kontroluje trvání, rozměry, zvuk a SHA-256. Rozpracované
  soubory se při startu zkusí bezpečně navázat, neznámé zůstanou ke kontrole.
  Video se zvukem vyžaduje mikrofon; bez zvuku vzniká jen po výslovné volbě.
  Přerušení ukončuje klip a označuje případný částečný záznam.
- Volné místo vyhodnocuje společná politika nad skutečnou kapacitou svazku:
  pod 2 GiB varuje, pod 1 GiB nespustí nové video a pod 512 MiB nespustí nové
  foto ani audio. Krátká značka se i při nízkém místě zkusí uložit; výsledek
  určí skutečný zápis. Klesne-li kapacita pod 512 MiB během audia nebo videa,
  aplikace záznam bezpečně ukončí. Nic se automaticky nemaže.
- Tepelný stav se sleduje bez skryté změny kvality. Stav `serious` varuje;
  `critical` nespustí nové video a rozběhnuté video bezpečně ukončí.
- C04d rozšiřuje místní deník o výběr dne a filtry **Vše / Důležité / Úvahy**,
  detail s čtenářským textem, hvězdičkou, současným soukromím a původním časem.
  Textový editor ukládá rozepsaný koncept při každé změně, ale teprve vědomé
  **Uložit** vytvoří novou `typed_source` nebo `human_revision`. Pozdější
  automatický přepis zůstane v historii a nepřebije lidskou revizi.
- Změna soukromí, skrytí, přesun kapitoly a textová revize vznikají jako
  souvisle číslované lokální operace s očekávanou revizí. Úvaha jde do deníku
  jen přes varovný dialog **Vložit Úvahu do deníku**; telefon změnu označí
  `čeká na server`. Skrytí je vratné, originály nemaže ani neuvolňuje místo a
  obnovení zachová soukromí. Přesun kapitoly nemění původní čas zachycení.
- **Soukromý dovětek** vytváří samostatnou `owner_only` Úvahu s vlastní
  identitou a trvalou vazbou na původní Moment. Nezmění původní Moment ani
  globální výchozí soukromí.
- C04d nemění Core Data schéma: verzovaný text, koncepty, vazby a fronta
  operací používají existující `SettingRecord`. Databáze současné C04b se tak
  dál otevře bez automatické migrace nebo resetu.
- C05b přidává trvalý přenosový journal nad stejnými místními daty. Přesné
  obálky metadata operací přežijí restart, serverový kurzor zůstává souvislý a
  priority jsou metadata, audio, fotografie, video. Jedna připravená 8MiB část
  používá background `URLSession`; po každém přerušení se skutečný serverový
  stav znovu porovná. `verified` vznikne až po serverové délce a SHA-256.
- Obrazovka **Uložení a přenosy** odděluje místní záznam od serveru. Nabízí
  ruční sync, trvalé pause a jednorázové mobilní povolení jen pro zobrazenou
  dávku s počtem a objemem. Token je v Keychain, URL musí být HTTPS a veřejný
  fallback neexistuje. Změna epochy zůstane fail-closed pro servisní kontrolu.
- C05c dělí výsledek na samostatné osy **Telefon / Mac / Další záloha / AI**.
  Telefon a Mac počítají Momenty; čekající operace, média a bajty jsou provozní
  údaje, nikoli jiný počet Momentů. Připojení nebo připravená fronta nejsou
  zelené ověření. Kopie na Macu není další záloha a přepis není záloha.
- Bez implementované C06b zůstává další záloha neověřená; bez C07 zůstává AI
  vypnutá. Syntetické kombinace T054/T055 jsou dostupné jen v Debug simulátoru,
  nikdy v produkční cestě fyzického zařízení.
- P2-B přidává do **Uložení a přenosy** vědomé uzavření dne 6. 10. 2026.
  iPhone porovná čerstvý inventář a původní soubory se soukromým Macem;
  při neshodě projekt nevznikne. Potvrzení uloží pouze filmový projekt na Macu,
  nevytváří video. Funkce je zatím jen v lokálně sestaveném zdrojovém kódu;
  fyzická instalace a přejímka čekají.

V historickém rozsahu C04a–C05c nebyly zahrnuté párování, spravovaná služba,
Viewer ani serverová záloha; tento výčet není současný provozní stav.
Hvězdička je pouze místní čtenářská pomůcka, protože C03b v1 pro její změnu
nemá operaci. C04d je nainstalované a fyzicky přijaté v dostupném lokálním
rozsahu. C05b fyzicky prošlo zámek, force quit, ztrátu a návrat tailnetu,
jednorázovou mobilní dávku, serverovou finalizaci, řízený nedostatek místa,
metadata-only změnu, změnu epochy a pause; captive portal T048 zůstává
`NEOVĚŘENO`. Přesné hranice jsou v cíleném plánu a nejde o C06a trvalý provoz.
C05c je pushnuté a podepsaná verze 0.1.0 (4) nainstalovaná; fyzický průchod
stavového UX a zachování dat zatím neproběhl.
Původní soubory se automaticky nemažou a chyba journalu nespouští reset.

Cílené fyzické průchody jsou v `C04b_IPHONE_TEST_PLAN.md`,
`C04d_IPHONE_TEST_PLAN.md`, `C05b_IPHONE_TEST_PLAN.md` a
`C05c_IPHONE_TEST_PLAN.md`.

## Historické vývojové ověření C04a–M2b

M2b (25. 9.) lokálně doplňuje do syncu pořadí a mezery z dokončených audio
účtenek; recorder a Core Data se nemění. Telefon posílá nové layouty až po
serverové schopnosti `audio_layout_v1`, již ověřené audio se znovu nenahrává.
Zatím bez podpisu/instalace, nejdřív nasadit kompatibilní server. Viz
`../docs/M2b_AUDIO_LAYOUT_REPORT.md` včetně jediného navazujícího fyzického průchodu.

```sh
cd camino/app
swift test --scratch-path /private/tmp/camino-c04d-tests
xcodebuild -project Camino.xcodeproj -scheme Camino -configuration Debug \
  -destination 'generic/platform=iOS' -derivedDataPath /private/tmp/camino-c04d-derived \
  CODE_SIGNING_ALLOWED=NO build
xcodebuild -project Camino.xcodeproj -scheme CaminoUITests -configuration Debug \
  -destination 'platform=iOS Simulator,id=<SIMULATOR_ID>' \
  -derivedDataPath /private/tmp/camino-c04d-ui-derived \
  -parallel-testing-enabled NO CODE_SIGNING_ALLOWED=NO test
```

SwiftPM testy používají pouze syntetická data včetně krátkého videa. UI testy
používají jednorázové simulátorové kontejnery. Jen v Debug simulátoru lze přes
`CAMINO_TEST_AVAILABLE_BYTES` a `CAMINO_TEST_THERMAL_LEVEL` dodat řízený stav;
produkční cesta vždy čte skutečnou kapacitu a systémový tepelný stav.
`CAMINO_TEST_ATTACHMENTS=1` spolu s platným `CAMINO_UI_TEST_SESSION` vytvoří
pouze v Debug simulátoru a v prázdném izolovaném úložišti dva označené Momenty,
foto metadata bez originálu a syntetické tiché audio pro UI test názvů příloh.
Není to test fyzického mikrofonu ani kamery; release/device cestu to nemění.
Samotný
build ani simulátor
netestují fyzickou kameru, mikrofon, orientaci, zámek, přerušení, přehrávání,
skutečný nedostatek místa, skutečné zahřátí ani obnovu po pádu na iPhonu.
