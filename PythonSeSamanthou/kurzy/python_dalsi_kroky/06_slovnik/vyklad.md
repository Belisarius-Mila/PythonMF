Seznam vybírá položky číselným indexem. Slovník je ukládá pod klíči, například pod texty "jmeno" a "mesto".

Zápis kontakt = {"jmeno": "Míla", "mesto": "Praha"} vytvoří slovník. Mezi klíčem a hodnotou je dvojtečka, dvojice odděluje čárka. Slovník ohraničují složené závorky.

Hodnotu přečteš jako kontakt["mesto"]. Přiřazením kontakt["mesto"] = "Brno" ji změníš. Klíče jsou přesné: "Mesto" a "mesto" jsou různé. Čtení neexistujícího klíče způsobí KeyError.

Celý slovník se v záložce Proměnné zatím nezobrazuje; jednoduchá proměnná mesto ano.
