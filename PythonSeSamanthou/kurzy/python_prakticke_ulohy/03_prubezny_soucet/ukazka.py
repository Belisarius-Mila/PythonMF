ceny = [30, 20, 15]
celkem = 0
for cena in ceny:
    celkem = cena  # Přičti cenu místo přepsání součtu.
    print(celkem)
print(f"Celkem: {celkem} Kč")
