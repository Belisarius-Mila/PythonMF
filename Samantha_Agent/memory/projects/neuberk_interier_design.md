# Neuberk interier design

Zalozeno: 2026-05-31
Priorita: 2
Stav: soukromy pracovni prostor zalozen; pro Kacenku existuji soukrome fotky,
stenove prekresy, pudorys a prvni koncepty knihovny / ctecího / detskeho koutku
mimo git

## Smysl

Projekt slouzi k postupnemu navrhovani a vylepsovani interieru domu Neuberk.
Prvni mistnost je `Kacenka`: velka pudni mistnost pro hosty, hlavne pro dcery s
detmi.

## Soukromy pracovni prostor

Soukrome podklady jsou mimo git:

```text
data/private/neuberk_interier_design/
  README_START_HERE.txt
  manifest.json
  rooms/
    kacenka/
      00_zadani/
      01_fotky_raw/
      02_planky_rozmery/
      03_inspirace/
      04_navrhy/
      05_vystupy/
      06_nakupy_materialy/
  shared_references/
  tools_workbench/
```

Do `data/private/` patri fotky, planky, rozmery, dispozice domu, konkretni
nakupni uvahy a vysledne rodinne navrhy. Tyto podklady se necommituji.

Do git-safe memory patri jen obecny stav projektu, workflow a rozhodnuti bez
soukromych detailu domu.

## Workflow pro mistnost

1. Intake podkladu
   - ulozit fotky do `01_fotky_raw/`,
   - ulozit planky a rozmery do `02_planky_rozmery/`,
   - vyplnit brief mistnosti v `00_zadani/`.

2. Pochopeni mistnosti
   - popsat aktualni stav,
   - vypsat pevna omezeni: sikminy, okna, dvere, topeni, zasuvky, tramy,
   - vypsat prakticke potreby dcer a deti.

3. Koncept
   - navrhnout 2-3 varianty,
   - kazdou hodnotit podle spani, ulozneho prostoru, bezpecnosti pro deti,
     svetla, uklidu, ceny a proveditelnosti.

4. Jednoduche 2D rozmisteni
   - nejdrive text a souradnice v centimetrech,
   - potom pripadne lokalni HTML/SVG pudorys,
   - bez tezkeho designoveho programu, dokud nebude nutny.

5. Vystup
   - kratky rodinny souhrn,
   - nakupni seznam,
   - finalni obrazky nebo jednoduche vizualizace,
   - WhatsApp text pro domluvu s rodinou.

## Knihovny a technicky smer

Zatim nepridavat nove zavislosti. V lokalni `.venv` jsou dostupne:

- `Pillow` (`PIL`) pro praci s fotkami,
- `OpenCV` (`cv2`) a `numpy` pro pripadne technicke analyzy obrazu,
- stavajici `app/media/image_resize.py` pro zmensovani fotek.

Pro prvni fazi staci:

- textove sablony,
- fotografie,
- rucne zadane rozmery,
- jednoduche JSON/TXT manifesty.

Pokud pozdeji budeme delat 2D pudorysy, preferovany smer je maly vlastni
HTML/SVG generator z rozmeru mistnosti a nabytku. Neni potreba hned pouzivat
interierovy designovy software.

Nove knihovny zvazit az podle potreby:

- `svgwrite` pro generovani SVG pudorysu,
- `shapely` pro kontrolu kolizi nabytku v pudorysu,
- `ezdxf` jen pokud by Mila dodal nebo potreboval DXF/CAD podklady.

## Otevrene otazky pro Kacenku

- Kolik lidi ma v mistnosti realne spat?
- Ma byt prioritou pohodli, kapacita, hraci prostor nebo ulozny prostor?
- Ktery stavajici nabytek musi zustat?
- Jake jsou presne rozmery a poloha sikmin?
- Jake jsou limity pro vrtani, elektriku, osvetleni a topeni?
- Chceme spise rychle vylepseni, nebo cilovy dlouhodoby redesign?

## Dalsi krok

Navazat na soukrome podklady v
`data/private/neuberk_interier_design/rooms/kacenka/`. Pro Kacenku uz existuji
soukrome pracovni stenove prekresy, pudorys a prvni vizualni koncepty hlavni
zapadni steny s knihovnou a zonami pro cteni, deti a spani. Dalsi prakticky krok
je po navratu k projektu zkontrolovat posledni koncept proti pudorysu: pruchody,
kolize s topenim/dvermi a realnou hloubku knihovny a rozkladaciho gauce.

## Checkpoint 2026-06-07

V soukromych konceptech pro Kacenku vznikla ladena varianta jizniho pohledu v6.
Opraven byl vztah pricneho snizeneho stropu, sikmeho tramu smerujiciho k vychodni
stene, komina u dveri a rozkladaciho gauce za kominem. Aktualni kandidat a
mezivarianty jsou popsane v soukromem indexu:

```text
data/private/neuberk_interier_design/rooms/kacenka/04_navrhy/library_corner_concepts/library_corner_concepts_index.txt
```

Navazani: nejdrive rucne zkontrolovat posledni v6 proti realnym fotkam. Pokud je
geometrie dost dobra, prejit z generovani obrazku na jednoduchy pudorysovy check
rohu mistnosti.
