# Camino C02b transfer harness

Izolovaný prototyp C02b obsahuje čisté Swift jádro a samostatnou iOS aplikaci
`Camino Transfer Test`. Aplikace vytváří pouze syntetickou dávku 96 MiB + 257 B,
nežádá o přístup k Fotkám ani mikrofonu a nesdílí úložiště s Camino Audio.

Model po relaunchi bere jako autoritu serverový seznam přijatých částí. Lokální
hodnota 100 % odeslaných bytů může znamenat jen `verifying`; stav
`verifiedOnMac` vznikne až ze serverového `verified`. Bez dosažitelné soukromé
sítě fronta čeká a nepřepíná se na veřejný endpoint. Background uploady jsou
souborové, journal je trvalý a současně existují nejvýše dvě připravené 8MiB
části. Povolení mobilních dat je svázané s jedinou existující dávkou a
nepřenáší se na nově vytvořené médium.

Testy:

```bash
swift test --package-path camino/prototypes/transfer
```

UI test v simulátoru:

```bash
xcodebuild -project camino/prototypes/transfer/CaminoTransfer.xcodeproj \
  -scheme CaminoTransfer \
  -destination 'platform=iOS Simulator,name=iPhone 14 Plus' \
  CODE_SIGNING_ALLOWED=NO test
```

Účet ani tým se neverzují. Volitelný místní `LocalSigning.xcconfig` je ignorovaný
Gitem a může obsahovat pouze lokální volbu `DEVELOPMENT_TEAM`.

Fyzické chování background `URLSession`, zámku, nuceného ukončení a cizí Wi-Fi
zůstává neověřené. Připojení telefonu, instalace a T043/T047–T050 jsou další
řízený krok C02b.
