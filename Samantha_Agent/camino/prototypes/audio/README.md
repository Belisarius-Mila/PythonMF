# Camino Audio — C01c

Izolovaný nativní prototyp pro Komentář nebo Úvahu. Swift 6, SwiftUI,
AVFAudio, žádné externí balíčky, server ani AI. Nejde o celé Camino.

**Stav: C01c rozpracované, verze 0.3.0 (3). Segmentový journal a obnova po pádu jsou implementované; 52 testů jádra a 2 UI testy prošly, podepsaný build je nainstalovaný na iPhonu. Fyzické T022/T023 zatím čekají. C01a a C01b byly přijaté samostatně.** Viz
[report C01c](../../docs/C01c_RECOVERABLE_AUDIO_REPORT.md).

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
Testy vytvářejí dvě navazující 15sekundové tiché PCM/CAF části bez mikrofonu. Každý test má vlastní
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
- Stop zastaví input tap, uzavře aktuální část a úplně dekóduje všechny části
  před vytvořením dokončovacího záznamu.
- Jeden recorder nebo player. Běžící audio pokračuje po zámku; nový Start
  vyžaduje aktivní aplikaci. Přerušení pozastaví vstup a uzavře dostupnou část.
  Pokračovat vytvoří nový soubor stejné session s pauzou; nic se neobnovuje samo.
- Každý nový pokus má výhradně vytvořenou UUID složku, `started.json`,
  `journal.json`, adresář `segments/` a po ověření nový `completed.json`.
  Input tap zůstává aktivní, zatímco se nejpozději před 60 sekundami střídají
  `.partial.caf` a stabilní CAF části. Existující soubory se nepřepisují.
- Nedokončené/cizí/poškozené položky zůstávají zachované a viditelně započítané.
  Prototyp nemá funkci mazání, exportu ani automatické opravy rozpracovaného audia.
- Média jsou v Application Support aplikace, nikoli v cache nebo repozitáři.
  Adresář je vyloučený ze systémové zálohy; v tomto prototypu existuje jen
  místní kopie. Žádné iCloud kontejnery či File Sharing nejsou zapnuté.
- Audio je PCM/CAF; požadovaná route preferuje 48 kHz a jeden vstupní kanál,
  skutečný formát, délka a velikost každé části jsou v dokončovacím záznamu. Nové soubory používají completeUntilFirstUserAuthentication;
  ochrana původních souborů z C01a se nemění.

Podpora zámku a přerušení prošla C01b. Kontinuita automatických částí a záchrana
po skutečném pádu čekají na fyzické T022/T023 v C01c.
Tato verze není vhodná pro ostrá osobní média; přejímka používá neutrální záznamy.
