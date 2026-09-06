# Python — další kroky

Sedm navazujících offline lekcí pro učebnu Python se Samanthou:

1. Text a f-string — zpráva z proměnné, počet znaků.
2. Seznam a index — více hodnot a výběr položky.
3. Cyklus se seznamem — jeden příkaz pro každou položku.
4. Funkce a return — vrácení vypočtené hodnoty.
5. Odpočítávání while — opakování podle podmínky.
6. Slovník a klíče — hodnoty pojmenované klíčem.
7. Bodovací panel — seznam, cyklus a podmínka společně kreslí výsledek.

Předpokládá sedm lekcí z balíčku „Python — první kroky“. Stačí jedna nová
lekce na 10–15 minut; závěrečný panel může zabrat déle. Každá má odhad výsledku,
výklad, spuštěnou ukázku, malou úpravu, nápovědu a vzorové řešení.

## Připojení samostatného ZIPu

Zavři učebnu. Z přídavného ZIPu zkopíruj složku `python_dalsi_kroky` do složky
`kurzy` své rozbalené aplikace, vedle `python_zaklady`. Uvnitř musí být
`kurzy/python_dalsi_kroky/kurz.json`. Není potřeba měnit původní balíček.

Ve verzi **1.2** učebnu znovu spusť a vlevo v **Balíček lekcí** zvol
**Python — další kroky**. Kompletní ZIP verze 1.2 už obsahuje obě sady.

Balíček je kompatibilní i s verzí **1.1**. Ta ještě nemá přepínač v okně;
v terminálu ve složce aplikace ho otevři takto:

```sh
python3 python_se_samanthou.py --course kurzy/python_dalsi_kroky/kurz.json
```

Postup používá vlastní ID `python-dalsi-kroky`. Rozepsané původní lekce zůstanou
zachované. Samotný balíček neobsahuje tvůj postup ani žádné připojení k internetu.
Čísla lekcí se v každém balíčku počítají od jedničky, celkem máš 14 lekcí.

Kontroly ověřují vybrané konstrukce a výsledky podle zadání, nejsou obecným
hodnotitelem libovolného řešení. Seznamy a slovníky si zatím prohlížej přes
print(); záložka Proměnné ukazuje jen jednoduché konečné hodnoty.
