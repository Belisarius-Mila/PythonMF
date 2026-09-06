Seznam znáš jako několik hodnot v hranatých závorkách. Nemusí zůstat stejně dlouhý: metoda append() připojí jednu položku na konec.

polozky.append("čaj") změní existující seznam polozky. To je rozdíl proti metodám textu z minulé lekce: textové strip() a lower() vracejí nový text, append() mění seznam a jeho návratová hodnota je None.

Proto nepiš polozky = polozky.append("čaj"). Proměnnou bys přepsal hodnotou None a přišel bys v ní o seznam.

len(polozky) spočítá položky. Výpočet udělej až po doplnění. Cyklus for pak vypíše každou položku na samostatný řádek.

PRŮBĚH
Začínáme se dvěma položkami. Po prvním append máme tři, po druhém čtyři. Pořadí vložení určuje pořadí výpisu.

DO DÍLNY
Přidej vlastní pátou položku a ověř, že se počet změní bez úpravy řádku s len(). Vypiš také celý seznam pomocí print(polozky). AI může vysvětlit rozdíl mezi změnou seznamu a vytvořením nového textu.
