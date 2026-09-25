# Camino app — C04a až C05c

První integrovaná iPhone aplikace Camina. Má vlastní bundle ID
`cz.pythonmf.camino.app` a vlastní Application Support kontejner; nepřebírá ani
nemigruje data ze samostatných prototypů Camino Audio a Camino Transfer Test.

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

Párování, C06a spravovaná služba, Viewer a serverová záloha jsou další etapy.
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

## Vývojové ověření

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
produkční cesta vždy čte skutečnou kapacitu a systémový tepelný stav. Samotný
build ani simulátor
netestují fyzickou kameru, mikrofon, orientaci, zámek, přerušení, přehrávání,
skutečný nedostatek místa, skutečné zahřátí ani obnovu po pádu na iPhonu.
