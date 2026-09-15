# Camino Audio — C01a

Izolovaný nativní prototyp pro krátký Komentář nebo Úvahu. Swift 6, SwiftUI,
AVFAudio, žádné externí balíčky, server ani AI. Nejde o celé Camino.

**Stav: C01a přijato 2026-09-15 21:43 CEST. Podepsaný build/install/run, 32 testů jádra a 2 UI testy prošly. Míla na iPhonu potvrdil záznam/poslech, zachování dokončených vzorků, průběh přehrávání i první odmítnutí a následné povolení mikrofonu bez samovolného záznamu. Metadata 5 původních vzorků ověřena. C01b nezahájeno; G0/G1 a terénní připravenost zůstávají otevřené.** Viz
[report C01a](../../docs/C01a_AUDIO_PROTOTYPE_REPORT.md).

## Otevření a sestavení

Otevři `CaminoAudio.xcodeproj`, schéma `CaminoAudio`. Cíl je iPhone, minimální
iOS 17; testovací zařízení je iPhone 14 Plus / iOS 26.6.1. Podpora platformy iOS je nainstalovaná.

Podepisování používá Automatic Signing. Tým případně nastav jen v lokálním,
ignorovaném `LocalSigning.xcconfig` pomocí `DEVELOPMENT_TEAM`; žádné identity
účtů, profily či klíče necommitovat. Bundle ID `cz.pythonmf.camino.audio.prototype`
je oddělené od budoucí produkční aplikace. Placené členství se tím nepořizuje.

Z projektového adresáře:

```sh
swift test --scratch-path /private/tmp/camino-audio-tests
xcodebuild -project CaminoAudio.xcodeproj -scheme CaminoAudio \
  -configuration Debug -destination 'generic/platform=iOS' \
  -derivedDataPath /private/tmp/camino-audio-derived CODE_SIGNING_ALLOWED=NO build
```

Druhý příkaz ověřuje nepodepsaný build, nikoli instalaci. Pro podepsaný build
vynech CODE_SIGNING_ALLOWED=NO a použij místní tým. DerivedData drž mimo
synchronizovanou Plochu (například nový adresář v /private/tmp); při ověření
podpisu build na Ploše blokoval atribut FinderInfo. Testy na
Macu používají syntetické CAF soubory v nových dočasných složkách, ne mikrofon.

### UI testy v iOS simulátoru

Samostatné schéma `CaminoAudioUITests` ovládá skutečnou SwiftUI aplikaci a
AVAudioPlayer. Ověřuje postup času i ukazatele, Stop, opakované přehrání a
návrat po ukončení procesu bez samovolného poslechu. V Xcode vyber toto schéma,
nainstalovaný iPhone simulátor a Test. Z příkazové řádky:

```sh
xcodebuild -project CaminoAudio.xcodeproj -scheme CaminoAudioUITests \
  -configuration Debug -destination 'platform=iOS Simulator,id=<SIMULATOR_UDID>' \
  -derivedDataPath /private/tmp/camino-ui-derived \
  -parallel-testing-enabled NO CODE_SIGNING_ALLOWED=NO test
```

`<SIMULATOR_UDID>` nahraď ID dostupného simulátoru z `xcrun simctl list devices`.
Testy vytvářejí 30sekundové tiché PCM/CAF bez mikrofonu. Každý test má vlastní
UUID úložiště `CaminoAudioUITests`, při opětovném spuštění aplikace stejného
testu se použije již dokončený vzorek; vytvoření náhradního vzorku je při návratu
zakázané, aby test nemohl zakrýt ztrátu dat. Žádné soubory se automaticky nemažou.
Pomocný kód je pod `DEBUG && targetEnvironment(simulator)`; fyzická a Release
verze jej neobsahují. Testy na fyzickém zařízení se přeskočí. Výsledek simulátoru
nenahrazuje přejímku mikrofonu, poslechu ani systémových přerušení na iPhonu.

## Chování a soubory

- První žádost o mikrofon pouze žádá o povolení; záznam vyžaduje nový Start.
- Nedostupný soubor má jiné hlášení než chyba načtení či přehrání. Nastavení mikrofonu se nabízí jen při zakázaném oprávnění.
- Systémové přerušení ihned ukončí poslech; nový poslech vyžaduje vědomé Přehrát.
- Při přehrávání se zobrazuje aktuální/celkový čas a průběh podle skutečné pozice přehrávače; mikrofonní ukazatel patří jen záznamu.
- Stav Nahrávám vyžaduje postup mediálního času recorderu a skutečný vstup.
  Ticho je platný záznam. Při zastaveném postupu se nejpozději při následujícím
  vyhodnocení po dvousekundovém intervalu zahájí bezpečné dokončení.
- Stop čeká na potvrzení recorderu a plné dekódování krátkého souboru.
  Chybějící potvrzení do tří sekund znamená neověřené uložení.
- Jeden recorder nebo player. Odchod do pozadí i přerušení záznam ukončí;
  návrat nikdy automaticky neotevírá mikrofon.
- Každý pokus má výhradně vytvořenou UUID složku, `started.json`, `audio.caf`
  a po ověření nový `completed.json`. Existující soubory se nepřepisují.
- Nedokončené/cizí/poškozené položky zůstávají zachované a viditelně započítané.
  Prototyp nemá funkci mazání, exportu ani automatické opravy rozpracovaného audia.
- Média jsou v Application Support aplikace, nikoli v cache nebo repozitáři.
  Adresář je vyloučený ze systémové zálohy; v tomto prototypu existuje jen
  místní kopie. Žádné iCloud kontejnery či File Sharing nejsou zapnuté.
- Krátké audio je PCM/CAF, mono, požadovaných 48 kHz / 16 bitů; skutečný
  formát, délka a velikost jsou v dokončovacím záznamu. Ochrana médií je Complete.

Segmentace, pokračování pod zámkem, hovory, dlouhé záznamy a záchrana po pádu
během zápisu patří do C01b/C01c. Tato verze není vhodná pro ostrá osobní média.
Přejímka používá neutrální 30–60s vzorky a ruční poslech na skutečném telefonu.
