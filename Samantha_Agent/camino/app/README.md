# Camino app — C04a

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

Foto a video, detail a ruční revize Momentu, přenos na Mac, párování, Viewer a
serverová záloha jsou další etapy. Aplikace zatím nehlásí úspěšnou synchronizaci.
Není to instalovaná ani fyzicky přijatá verze. Původní soubory se nemažou a při
chybě databáze se neprovádí automatická migrace či reset.

## Vývojové ověření

```sh
cd camino/app
swift test --scratch-path /private/tmp/camino-c04a-tests
xcodebuild -project Camino.xcodeproj -scheme Camino -configuration Debug \
  -destination 'generic/platform=iOS' -derivedDataPath /private/tmp/camino-c04a-derived \
  CODE_SIGNING_ALLOWED=NO build
xcodebuild -project Camino.xcodeproj -scheme CaminoUITests -configuration Debug \
  -destination 'platform=iOS Simulator,id=<SIMULATOR_ID>' \
  -derivedDataPath /private/tmp/camino-c04a-ui-derived \
  -parallel-testing-enabled NO CODE_SIGNING_ALLOWED=NO test
```

SwiftPM testy používají pouze syntetická data. UI test používá jednorázový
simulátorový kontejner. Samotný build ani simulátor netestují fyzický mikrofon,
zámek, přerušení, přehrávání ani obnovu po pádu na iPhonu.
