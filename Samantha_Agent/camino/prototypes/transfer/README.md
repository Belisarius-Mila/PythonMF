# Camino C02b transfer core

Izolovaný prototyp C02b obsahuje čistý Swift model pravdivého stavu přenosové
fronty. Neobsahuje skutečný `URLSession`, UI ani přístup k médiím v telefonu.

Model po relaunchi bere jako autoritu serverový seznam přijatých částí. Lokální
hodnota 100 % odeslaných bytů může znamenat jen `verifying`; stav
`verifiedOnMac` vznikne až ze serverového `verified`. Bez dosažitelné soukromé
sítě fronta čeká a nepřepíná se na veřejný endpoint. Povolení mobilních dat je
svázané s jedinou existující dávkou a nepřenáší se na nově vytvořené médium.

Testy:

```bash
swift test --package-path camino/prototypes/transfer
```

Fyzické chování `URLSession`, zámku, nuceného ukončení a cizí Wi-Fi zůstává
neověřené a patří do navazujícího klientského kroku C02b.
