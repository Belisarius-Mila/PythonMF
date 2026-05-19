# VocabFR LockScreen (SwiftUI MVP)

Toto je minimalni iOS MVP, ktere:
- nacita `VocabularyFR.csv`,
- vybira slova nahodne bez opakovani v ramci aktualni sady,
- umi `Auto/Fin` cyklus (`FR` -> `CZ` -> dalsi slovo po 2s),
- pouziva `AVSpeechSynthesizer` a je pripravene pro prehravani na zamcene obrazovce.

## 1) Vytvor projekt v Xcode
1. Otevri Xcode -> `New Project` -> `App` (iOS, SwiftUI, Swift).
2. Nazev napr. `VocabFRLockscreen`.
3. Zavri Xcode projekt v navigatoru (jen aby se lepe kopirovaly soubory).

## 2) Nahraď soubory
Do projektu vloz tyto soubory z teto slozky:
- `VocabFRLockscreenApp.swift`
- `ContentView.swift`
- `TrainerViewModel.swift`
- `Word.swift`
- `CSVStore.swift`

V Xcode pri pridani souboru zatrhni:
- `Copy items if needed`
- target `VocabFRLockscreen`

## 3) Pridani CSV
1. Zkopiruj tvuj `VocabularyFR.csv` do Xcode projektu.
2. Ujisti se, ze je soucasti targetu (`Target Membership`).

App pri prvnim spusteni zkopiruje CSV z bundle do `Documents/VocabularyFR.csv` a dale pracuje s touto kopii.

## 4) Info.plist nastaveni (dulezite pro lock screen audio)
Do `Info.plist` pridej:
- `Required background modes` (`UIBackgroundModes`) -> `App plays audio` (`audio`)

Detaily viz `InfoPlistAdditions.md`.

## 5) Chovani Auto
- `Auto` spusti nekonecny cyklus:
  - vybere dalsi slovo bez opakovani,
  - precte FR (fr-FR),
  - precte CZ (cs-CZ),
  - pocka 2 sekundy,
  - pokracuje dal.
- `Fin` zastavi cyklus.

## Poznamka
Na realnem zarizeni (iPhone) je treba otestovat konkretni dostupnost hlasu `fr-FR` a `cs-CZ`.
Kdyz hlas neni dostupny, iOS pouzije nejblizsi mozny.
