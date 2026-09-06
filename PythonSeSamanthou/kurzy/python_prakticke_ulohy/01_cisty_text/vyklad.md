Nejdřív odhadni výsledek, potom spusť ukázku. Vstup "  ČAJ  " obsahuje dvě mezery před slovem i za ním. I mezera je znak, takže len() je započítá.

hodnota.strip() vrátí nový text bez bílých znaků na začátku a na konci. Mezera uvnitř slovního spojení zůstane. hodnota.lower() vrátí text s malými písmeny, například "ČAJ" změní na "čaj".

Tečka znamená, že voláš metodu daného textu. Zápis hodnota.strip().lower() provede dva malé kroky: výsledek strip() předá metodě lower(). Původní proměnná se tím nepřepíše.

Funkci a return už znáš. Funkce vycisti zde dostane text v parametru hodnota a vrátí jeho upravenou podobu. Pomocí stejné funkce zpracujeme dva různé vstupy.

ČASTÁ CHYBA
Samotné hodnota.strip() bez přiřazení či return vytvoří výsledek, který nikam neuložíš. Zápis lower bez závorek metodu nezavolá.

DO DÍLNY
Přenes řešení tlačítkem Do dílny. Zkus vstup "  ZELENÝ  ČAJ  " se dvěma mezerami uvnitř. Nejdřív odhadni, co zůstane. Volitelně se AI zeptej: Proč strip nezměnil vnitřní mezery?
