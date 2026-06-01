# Matysek English - scene 1 full voice recast

Datum: 2026-06-01
Stav: recast odsouhlasen, finalni produkcni audio jeste nepripraveno

## Odsouhlaseny vyber Mily

Finalni hlasove reference jsou zamcene v:

```text
VOICE_LOCK_20260601.md
selected_references/
```

- Benji: `reference_benji_fable_i_am_benji.mp3`
- Bunny: `reference_bunny_echo_i_am_bunny.mp3`
- Bruno: `bruno_macos_daniel_01_hello_i_am_bruno.mp3`
- Fiona: `fiona_macos_karen_01_hi_i_am_fiona.mp3`
- Sunny: `sunny_young_coral_01_hello_i_am_sunny.mp3`

Predchozi smer Fiona=`shimmer`, Bruno=`onyx`, Sunny=`nova` je nahrazen timto
recastingem.

## Proc znovu

Produkce ukazala, ze samotny nazev TTS hlasu neni spolehliva identita postavy.
Novy `fable`, `echo`, `shimmer` nebo `nova` muze znit jinak nez starsi MP3 ve
scene Friends. Proto se pri recastingu neposuzuje nazev hlasu, ale konkretni
MP3 soubor.

## Zasadni pravidlo

- Benji a Bunny maji jako prvni referenci stare produkcni MP3 ze sceny Friends.
- Pokud chceme, aby zneli stejne jako ve Friends, nesmime je nahrazovat novou
  generaci jen podle jmena hlasu.
- Bruno, Fiona a Sunny se musi vybrat tak, aby byli od Benjiho/Bunnyho i mezi
  sebou zretelne rozeznatelni.
- Po vyberu se zamkne konkretni MP3 jako hlasova reference postavy.
- Teprve potom se pripravi finalni dialogy sceny.

## Doporucene poradi poslechu

1. `00_reference_old_friends/`
   - Poslechni puvodni Benji/Bunny z produkcni sceny Friends.
   - To je kvalita a charakter, ke kteremu se chceme vratit.
2. `10_benji/`
   - Porovnej starou referenci s nove generovanym Benjim.
   - Pokud novy Benji neni dost podobny staremu, nebrat.
3. `20_bunny/`
   - Porovnej starou referenci s novymi Bunny kandidaty.
   - U Bunnyho uz bylo zjisteno, ze novy `echo` neni automaticky stary Bunny.
4. `30_bruno/`
   - Bruno ma byt klidny, hlubsi, jasne muzsky hlas.
   - Musi se odlisit od Benjiho.
5. `40_fiona/`
   - Fiona ma byt mila, chytra, zensky hlas.
   - Musi se odlisit od Sunny.
6. `50_sunny/`
   - Sunny ma byt mladsi, lehci, hravy hlas.
   - Musi byt jasne odlisitelna od Fiony.

## Puvodni pracovni nazor pred poslechem Mily

- Benji: drzet se stare produkcni reference, pokud to jen pujde.
- Bunny: drzet se stare produkcni reference; novy `echo` je rizikovy.
- Bruno: zkusit `bruno_onyx_*`, ale pokud zni moc podobne Benjimu, hledat dal.
- Fiona: zkusit spis `fiona_coral_*` nebo macOS `Samantha/Moira`, pokud Shimmer
  splývá se Sunny.
- Sunny: nejspis nehledat v `nova/shimmer`; zkusit macOS `Junior/Flo/Kathy` nebo
  dalsi detsky smer.

## Poznamka k macOS hlasum

Soubory `*_macos_*` jsou lokalni castingove ukazky z macOS `say`.
Jsou prakticke pro rychly poslech a odliseni charakteru. Pred verejnym nasazenim
je potreba potvrdit licencni vhodnost konkretniho pouziti.

## Necommitovat automaticky

Tahle slozka je pracovni casting. Do produkce patri az finalni vybrane MP3,
ne cela sada pokusnych variant.
