body = [6, 12, 15]
x = 100
splneno = 0
for hodnota in body:
    if hodnota >= 10:
        barva = "zelena"
        splneno = splneno + 1
    else:
        barva = "oranzova"
    kruh(x, 180, 35, barva)
    x = x + 150
print(f"Splněno: {splneno}")
