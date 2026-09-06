Cyklus for polozka in polozky zná aktuální položku. Pro očíslovaný seznam potřebujeme současně i pořadové číslo. Pomůže enumerate().

enumerate(polozky, start=1) postupně poskytne dvojice: (1, "čaj"), (2, "med"), (3, "citron"). Zápis for cislo, polozka in ... rozdělí každou dvojici do dvou proměnných. Čárka mezi jmény je důležitá.

Parametr start určuje první číslo. Pokud ho vynecháš, výchozí je 0. Číslo od enumerate není automaticky index pro hranaté závorky: při start=1 je první pořadové číslo 1, ale první index původního seznamu zůstává 0.

f"{cislo}. {polozka}" vloží číslo a text do jednoho řádku. Tečka za číslem je obyčejný znak ve výpisu.

ČASTÁ CHYBA
Nezvyšuj cislo ručně: enumerate už připraví správné číslo při každém průchodu. Změnou start se seznam sám nijak nemění.

DO DÍLNY
Zkus start=5 a potom přidej čtvrtou položku. Odhadni poslední číslo ještě před spuštěním. AI může na konkrétní dvojici ukázat, jak funguje rozdělení do dvou proměnných.
