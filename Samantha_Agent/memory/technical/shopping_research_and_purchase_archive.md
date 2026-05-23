# Nakupni pruzkum a archiv nakupu

Priorita: 2
Stav: koncept / navrzeny lehky workflow
Datum zalozeni: 2026-05-23

## Ucel

Lehky workflow pro situace, kdy Mila zada konkretni produkt nebo nekolik variant
produktu a Samantha/Adam ma pomoci:

- najit realne prodejce,
- porovnat kamenne obchody v rozumnem okoli,
- doplnit overene e-shopy,
- vratit prime odkazy na konkretni produkt,
- po Milove objednani ulozit potvrzeni objednavky a fakturu do soukromeho archivu.

Nejde zatim o velky samostatny projekt. Je to kandidát na budoucí tool/workflow,
ktery ma byt prakticky, lehky a bez zbytecne rezie.

## Presne ulozeny puvodni koncept

Adam hlásí: dává to smysl jako **lehký nákupní workflow/tool**, ne jako velký projekt.

Navrhl bych to rozdělit na 3 části:

**1. Nákupní průzkum**
Zadáš například:

`Najdi Dolphin E20 + jemný filtr 20 mikronů, kamenně do 100 km od Mladé Boleslavi a levné ověřené e-shopy.`

Já bych ověřil aktuální weby a vrátil tabulku:

| Varianta | Prodejce | Typ | Vzdálenost / doprava | Cena | Dostupnost | Odkaz přímo na produkt | Poznámka |
|---|---|---|---|---|---|---|---|

Kategorie:
- kamenné obchody do 100 km od Mladé Boleslavi
- e-shopy s kamennou pobočkou mimo limit
- čisté e-shopy
- alternativy / kompatibilní příslušenství
- varování: nejasná kompatibilita, podezřelý e-shop, špatné recenze, neověřený produkt

**2. Objednávkový záznam**
Po objednání bys mi poslal potvrzení objednávky nebo PDF/e-mail. Já bych z toho udělal soukromý záznam:

```text
Samantha_Agent/data/private/purchases/
  2026/
    2026-05-23_dolphin-e20/
      order_summary.md
      invoice.pdf
      warranty.md
      links.md
```

V git by zůstaly jen neprivátní šablony/protokoly, samotné faktury a objednávky by byly v `data/private/`, tedy mimo commit.

**3. Záruční a znalostní evidence**
Ke každému nákupu bychom drželi stručné metadata:

```yaml
product: Dolphin E20
seller: ...
order_date: 2026-05-23
invoice_date: ...
warranty_until: ...
serial_number: ...
price: ...
documents:
  - invoice.pdf
  - order_confirmation.pdf
notes:
  - filtr 20 mikronů kompatibilní / nekompatibilní
```

Pak by ses mohl později zeptat:
- `Najdi fakturu k bazénovému vysavači`
- `Kdy končí záruka na Dolphin E20?`
- `Kde jsme kupovali filtr 20 mikronů?`
- `Najdi podobný produkt jako minule, ale levněji`

**Nejlepší forma**
Za mě ideálně:

1. `memory/protocols/shopping_research_protocol.md`  
   pravidla, jak hledat, jak hodnotit obchody, co ověřovat

2. `Samantha_Agent/data/private/purchases/`  
   soukromý archiv objednávek a faktur

3. jednoduchý intake skript později  
   například: vezme PDF/obrázek/e-mail ze složky Downloads a přesune ho do správné nákupní složky

4. report na požádání  
   `nákupní evidence`, `záruky`, `poslední nákupy`, `faktury bez přiřazení`

Důležité pravidlo: já bych **neobjednával ani neplatil**. Udělám průzkum, připravím odkazy, pomůžu zkontrolovat košík a ty objednáš. Pak mi dáš potvrzení/fakturu a já ji zařadím.

První praktický krok bych udělal malý: zavést protokol a složku pro nákupy, bez automatizace. Až to jednou použijeme na reálném nákupu, doplníme skript.

## Bezpecnostni hranice

- Adam/Samantha neobjednava a neplati za Milu.
- Adam/Samantha muze udelat pruzkum, porovnani a pripravit odkazy.
- Kosik nebo objednavku muze maximalne zkontrolovat/pomoci pripravit do kroku pred platbou, pokud to Mila vyslovne chce.
- Faktury, potvrzeni objednavek, seriova cisla a osobni udaje patri do `Samantha_Agent/data/private/purchases/`, ne do gitu ani verejne pameti.
- Do verejne commitovane pameti patri jen protokol, sablony a neprivatni metadata.

## Navrzeny budouci dalsi krok

Az Mila bude chtit workflow realne pouzit nebo rozvinout:

1. vytvorit ignorovany soukromy adresar `Samantha_Agent/data/private/purchases/`,
2. doplnit sablonu `order_summary.md` a `warranty.md`,
3. pozdeji pridat potvrzovany intake z Downloads do nakupniho archivu,
4. az po realnem pouziti zvazit samostatny systemovy report `nakupni evidence`.
