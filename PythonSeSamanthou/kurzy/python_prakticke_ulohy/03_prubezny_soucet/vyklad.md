V seznamu jsou tři ceny. Chceme jejich součet a také vidět, jak vzniká.

Před cyklem nastavíme celkem = 0. Při každém průchodu přičteme aktuální cenu: celkem = celkem + cena. Znaménko = je přiřazení, nikoli matematické tvrzení o rovnosti. Nejdřív se vyhodnotí pravá strana, pak se uloží nová hodnota.

Pro ceny 30, 20 a 15 je průběh:
1. celkem začíná na 0; po přičtení 30 je 30.
2. K hodnotě 30 přičteme 20; dostaneme 50.
3. K hodnotě 50 přičteme 15; dostaneme 65.

print(celkem) uvnitř cyklu ukazuje mezisoučty. Závěrečný print bez odsazení se provede až po skončení cyklu.

ČASTÁ CHYBA
Pokud necháš celkem = cena, součet se vždy přepíše poslední cenou. Pokud dáš celkem = 0 dovnitř cyklu, začneš při každém průchodu znovu od nuly.

DO DÍLNY
Přidej cenu 10 a odhadni nový součet. Potom zkus prázdný seznam []. Proč zůstane celkem nula? V této lekci trénujeme cyklus; vestavěnou funkci sum() můžeme prozkoumat později.
