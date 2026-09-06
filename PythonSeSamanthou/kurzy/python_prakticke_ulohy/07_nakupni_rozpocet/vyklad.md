Závěrečný projekt spojí známé stavební prvky. Nákup je seznam; každá jeho položka je slovník s klíči "nazev" a "cena". Seznam tedy nemusí obsahovat jen texty nebo čísla — může obsahovat i slovníky.

V cyklu je polozka vždy jeden slovník. polozka["nazev"] vrátí jeho název a polozka["cena"] jeho cenu. Ceny postupně sčítáme stejně jako ve třetí lekci.

Funkce v_limitu(celkem, rozpocet) vrací True nebo False. Porovnání celkem <= rozpocet samo vytvoří tuto logickou hodnotu; není potřeba uvnitř funkce další if. True znamená ano, False ne.

Funkci pak použijeme přímo jako podmínku if. Parametry jsou místní jména uvnitř funkce. Při každém volání dostanou hodnoty předané v závorkách.

Úkol má dvě opravy. Udělej nejdřív součet a zkontroluj 30 + 45 + 10 = 85. Potom uprav funkci a ověř i hranici: nákup přesně za 100 při rozpočtu 100 je ještě v limitu. Poslední část programu tuto hranici zkouší zvlášť a kontroluje také překročení: 101 Kč při rozpočtu 100 už neprojde.

DO DÍLNY
Zkopíruj řešení do dílny. Zkus rozpočet 80, pak 85 a 100. Přidej další položku nebo nastav nakup = []. Vysvětli, proč je při překročení zbyva záporné. Volitelně požádej AI: Dej mi jednu malou úpravu tohoto rozpočtu a zatím neprozrazuj řešení.

Kontroly v lekci porovnávají předepsaná data a výsledek. Vlastní varianty dělej v dílně, kde nemusí splnit původní zadání.
