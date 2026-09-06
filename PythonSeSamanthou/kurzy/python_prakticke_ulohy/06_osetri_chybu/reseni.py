vstupy = ["12", "ahoj", "5"]
for hodnota in vstupy:
    try:
        cislo = int(hodnota)
        print(f"Číslo: {cislo}")
    except ValueError:
        print(f"Neplatné číslo: {hodnota}")
