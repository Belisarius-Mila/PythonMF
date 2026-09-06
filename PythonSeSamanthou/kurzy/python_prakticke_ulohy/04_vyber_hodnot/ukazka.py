teploty = [16, 20, 24, 19]
vybrane = []
for teplota in teploty:
    if teplota > 20:  # Patří sem také přesně 20.
        vybrane.append(teplota)
for teplota in vybrane:
    print(teplota)
pocet = len(vybrane)
print(f"Počet: {pocet}")
