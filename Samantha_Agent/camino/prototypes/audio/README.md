# Camino Audio — C01a

Izolovaný nativní prototyp pro krátký Komentář nebo Úvahu. Swift 6, SwiftUI,
AVFAudio, žádné externí balíčky, server ani AI. Nejde o celé Camino.

**Stav: podepsaný Xcode build a strict kontrola podpisu ověřeny;
instalace na iPhone prošla, spuštění čeká na kontrolu důvěry vývojáři a fyzická přejímka není hotová.** Viz
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

## Chování a soubory

- První žádost o mikrofon pouze žádá o povolení; záznam vyžaduje nový Start.
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
