vstupy = ["12", "ahoj", "5"]
for hodnota in vstupy:
    try:
        cislo = 0  # Sem patří převod aktuálního textu.
        print(f"Číslo: {cislo}")
    except ValueError:
        print(f"Neplatné číslo: {hodnota}")
