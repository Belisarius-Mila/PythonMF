# VocabularyEN – postup pro kvalitní MP3

Webová aplikace nepoužívá systémový hlas prohlížeče. Každé anglické a české
slovíčko má předem vytvořené MP3, takže na Macu i Linuxu zní stejně a po
kliknutí se nic teprve negeneruje.

Kanonické hlasy:

- angličtina: `en-US-AriaNeural` (Aria),
- čeština: `cs-CZ-VlastaNeural` (Vlasta),
- rychlost: `-10 %`.

Výjimka pro samostatné `cat`: anglickou MP3 čte `en-US-JennyNeural`.
Aria ho opakovaně vyslovovala jako jméno Kate. Výjimka je v generátoru
`VOICE_OVERRIDES`, manifest ji označuje `enVoice`; text `cat` ani česká
nahrávka se nemění. Hlas je součástí názvu MP3, takže oprava používá novou
adresu a nespoléhá na vypršení cache staré nahrávky.

## Po každé změně VocabularyEN.csv

Z kořene projektu spusť v tomto pořadí:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
python3 VocabularyEN/build_vocabulary_en_audio.py --apply
python3 VocabularyEN/build_vocabulary_en_audio.py
```

První příkaz synchronizuje CSV, webový JSON a obrázky. Druhý vytvoří pouze
chybějící MP3 a aktualizuje audio manifest. Třetí je read-only kontrola, která
musí skončit hláškou `Audio kontrola OK`.

Názvy MP3 jsou odvozené z hlasu, rychlosti a skutečně čteného textu. Pouhé
přečíslování řádků proto nevytváří nahrávky znovu a stejný text sdílí jediný
soubor. Nepoužívané starší soubory se automaticky nemažou.

Bez `--apply` generátor nic nevytváří ani neposílá externí službě. Režim
`--apply` používá registrovanou schopnost `generate_project_audio_asset` a
odesílá Microsoft Speech pouze veřejný text slovíčka. Audio se ukládá do
projektu; příkaz nic sám nepublikuje, necommitne ani nenasadí.

## Audit slovní zásoby MMTX

`import_mmtx_vocabulary.py` kontroluje vedle původních slovníčků také
anglické texty z audio manifestů scén, barev, školy a narozeninových dialogů.
Základní tvary mají explicitní mapování (například `logs` → `log`), jména
postav se vynechávají a `me too` zůstává vyloučené. Doplňující překlady
a příkladové věty jsou v `mmtx_dialogue_supplement.csv`.

Bez `--apply` probíhá pouze audit. S `--apply` import doplní jen chybějící
řádky s okruhem Benji; původní CSV prefix zachová. Potom spusť synchronizaci
s `--preserve-extra-assets` a sestavení audia podle postupu výše. Nový
nezkontrolovaný výraz v dialogu audit označí místo falešného hlášení úplnosti.

## Kontrola webu před zveřejněním

```bash
python3 -m http.server 8811 -d docs
```

Potom otevři `http://127.0.0.1:8811/vocabulary-en/` a vyzkoušej oba směry,
`Přehrát zadání` a `Přehrát odpověď`. Pokud nové slovíčko nemá MP3, kontrolní
příkaz výše selže a změna není připravená k publikování.
