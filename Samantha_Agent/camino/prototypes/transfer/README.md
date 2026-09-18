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
nepřenáší se na nově vytvořené médium. Dostupná povolená Wi-Fi může spustit
reconciliaci automaticky; `Synchronizovat nyní` je ruční provozní záloha.

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

Podepsaný build 0.4.0 (2), strict kontrola podpisu, instalace a spuštění na
iPhonu prošly. T043 doložil skutečné přerušení sítě, následné doplnění všech
částí, shodnou délku/hash a jediný objekt daného Assetu. T047 je fyzický PASS
v syntetickém rozsahu: zámek, force quit, pravdivý mezistav a ruční relaunch
doplnily jen chybějící části; dvě relace i dva objekty/účtenky jsou ověřené.
Fyzický průchod také odhalil zahozený souběžný impuls reconciliace; build 2 jej
koaleskuje a následná 96MiB dávka doběhla bez dalšího klepnutí. Profil je místní
a časově omezený; tým ani účet nejsou verzované. Cizí Wi-Fi, mobilní data,
zadržené ověření a T048–T050 zůstávají neověřené. T043 workflow po důkazu
receiver zastavil a původní Serve konfiguraci přesně obnovil. T047 workflow
byl po důkazu registrovaně ukončen; Serve je přesně obnovený, Funnel vypnutý a
auditní objekty/účtenky zůstávají zachované.
