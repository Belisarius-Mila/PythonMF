Filtrování znamená vybrat z více hodnot jen ty, které splňují určitou podmínku. Původní seznam si ponecháme a vhodné hodnoty ukládáme do nového seznamu.

vybrane = [] vytvoří prázdný seznam. Cyklus postupně vezme každou teplotu. Podmínka rozhodne, zda ji připojit pomocí append().

Zápis >= znamená větší nebo rovno. Pro hranici 20 tedy projdou 20 i 24, ale 16 a 19 ne. Zápis > znamená jen větší; přesnou hranici by vyřadil.

Řádek vybrane.append(teplota) je odsazený uvnitř if, které je uvnitř for. Použij osm mezer před append. Kdyby byl append odsazen jen jako if, připojoval by každou teplotu.

Druhý cyklus už prochází pouze vybrané hodnoty. Zachovají si původní pořadí; filtrování je samo neseřadí.

DO DÍLNY
Přidej teplotu 20 podruhé: má se objevit také dvakrát. Potom změň hranici tak, aby neprošla žádná hodnota. Očekávej počet 0. AI se můžeš zeptat, co se mění na každé úrovni odsazení.
