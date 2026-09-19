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
reconciliaci automaticky. U nové dávky s povolenými mobilními daty je první
start vědomý přes `Synchronizovat nyní` nebo `Pokračovat`; potom se přenos může
bez dalšího klepnutí obnovovat. Starší journal si při aktualizaci zachová
dosavadní obnovu. Toto chování buildu 0.4.0 (4) čeká na fyzické ověření.

Testy:

```bash
swift test --package-path camino/prototypes/transfer
```

UI test v simulátoru:

```bash
xcodebuild -project camino/prototypes/transfer/CaminoTransfer.xcodeproj \
  -scheme CaminoTransfer \
  -destination 'platform=iOS Simulator,name=Camino UI — iPhone 14 Plus' \
  CODE_SIGNING_ALLOWED=NO test
```

Účet ani tým se neverzují. Volitelný místní `LocalSigning.xcconfig` je ignorovaný
Gitem a může obsahovat pouze lokální volbu `DEVELOPMENT_TEAM`.

Poslední build na iPhonu je podepsaný 0.4.0 (3). T043 doložil skutečné
přerušení sítě, doplnění všech částí, shodnou délku/hash a jediný objekt
daného Assetu. T047 je fyzický PASS
v syntetickém rozsahu: zámek, force quit, pravdivý mezistav a ruční relaunch
doplnily jen chybějící části; dvě relace i dva objekty/účtenky jsou ověřené.
Fyzický průchod také odhalil zahozený souběžný impuls reconciliace; build 2 jej
koaleskuje a následná 96MiB dávka doběhla bez dalšího klepnutí. Profil je místní
a časově omezený; tým ani účet nejsou verzované. T048 a plné T049 zůstávají
neověřené. T043 workflow po důkazu receiver zastavil a přesně obnovil Serve.
T047 workflow
byl po důkazu registrovaně ukončen; Serve je přesně obnovený, Funnel vypnutý a
auditní objekty/účtenky zůstávají zachované.

Pro T048 a T049 jsou připravené oddělené registrované řadiče a terénní postup
`camino/tasks/C02b_T048_T049_FIELD_PLAN.md`. Build 0.4.0 (3) navíc
vyžaduje vědomé potvrzení mobilního přenosu s počtem a velikostí dávky; síťová
politika platí pro všechny HTTPS požadavky, nejen velké části. Build 3 prošel
na iPhonu syntetickou mobilní částí T049; T050 prošel ve druhém fyzickém
syntetickém běhu. T048 na cizí Wi-Fi a plné T049 s novým skutečným videem
zůstávají otevřené. Build 4 s vědomým prvním mobilním startem prošel 22/22
Swift testy, simulátorovým UI testem, nepodepsaným iOS buildem a plnou
projektovou bránou 1719/1719. Na iPhonu ještě není nainstalovaný.
