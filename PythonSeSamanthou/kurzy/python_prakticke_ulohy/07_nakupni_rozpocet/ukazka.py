def v_limitu(celkem, rozpocet):
    return celkem < rozpocet  # Má projít i přesná hranice.

nakup = [
    {"nazev": "chléb", "cena": 30},
    {"nazev": "čaj", "cena": 45},
    {"nazev": "citron", "cena": 10},
]
rozpocet = 100
celkem = 0
for polozka in nakup:
    celkem = polozka["cena"]  # Cenu přičítej.
    print(polozka["nazev"])
zbyva = rozpocet - celkem
print(f"Celkem: {celkem} Kč")
print(f"Zbývá: {zbyva} Kč")
if v_limitu(celkem, rozpocet):
    print("Nákup je v limitu.")
else:
    print("Nákup překročil rozpočet.")
if v_limitu(100, 100):
    print("Přesná hranice je v limitu.")
else:
    print("Přesná hranice neprošla.")
if v_limitu(101, 100):
    print("Překročení chybně prošlo.")
else:
    print("Překročení není v limitu.")
