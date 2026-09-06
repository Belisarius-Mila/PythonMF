def vycisti(hodnota):
    return hodnota.strip().lower()

puvodni = "  ČAJ  "
nazev = vycisti(puvodni)
delka = len(nazev)
print(nazev)
print(delka)
print(vycisti("  ZELENÝ ČAJ  "))
