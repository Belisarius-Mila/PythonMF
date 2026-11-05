# Neuberk interier design

## 2026-11-05 — praktická přejímka a příjem iPhone JPEG

První Ateliér byl vydaný do eb0d98e6 a je zachovaný i v b933de0f. Při
praktické zkoušce Míla založil vlastní projekt a zkusil tři iPhone JPEG.
Příjem je odmítl: jejich skutečný dekódovaný formát je MPO se dvěma vrstvami,
velikost cca 2 MiB a rozlišení 4032 × 2268 splňují původní limity.

Lokálně opravené: přijmout JPEG/MPO, pro náhled a kresbu jen hlavní obraz
se správnou EXIF orientací, celý originál zachovat. Limity 6 MiB a 32 Mpx
zůstávají; PNG/WebP animace se nepovolují. 30 cílených testů PASS, tři
skutečné fotografie i izolovaný příjem se shodou originálů PASS. Plná brána
2 530 testů, 2 499 PASS, 31 SKIP, bez selhání (493,044 s). Oprava zatím není nasazená;
samostatné nové p+n nebylo zadané. Report interior_iphone_jpeg_mpo_20261105.md.
Původní fotografie a živý projekt se neměnily. Nový TVBCP se nezakládá.

Míla následně potvrdil „Ano, nasaď prosím…“: oprava b449f805 schválená
k Terra p+n v existujícím proudu. Konečný výsledek až podle
logs/interior_mpo_release_20261105.log a interior_mpo_verified_20261105.log.

## Interiérový ateliér a schválené rozložení 2026-11-05

Míla navázal novou infrastrukturou: Jana pracuje ze svého Macu přes Cockpit,
v samostatném celoobrazovkovém ateliéru. Schválil rozložení Ateliér s miniaturami
vlevo, hlavní plochou uprostřed a zasouvatelným rozhovorem vpravo. Podklady a
úprava konkrétní varianty mají vlastní pracovní pohled v témže okně.

Ověření: 50 cílených kontrol PASS, 23 frontendových kontraktů PASS; plná
brána persistence 2 519 testů, 31 SKIP, bez chyb. Lokálně, zatím bez vydání.

První lokální milník ukládá projekty, místnosti, explicitně nahrané PNG/JPEG/
WebP, výběr referencí a pracovního obrázku, kreslené poznámky, rozpracované zadání
s kontrolou revize, neměnné varianty a připomínky vázané k návrhu. Žádná výchozí
ukázková data nejsou vydávaná za skutečné rodinné návrhy.

Původní soukromý strom zůstává zachovaný. Nová data jsou pouze v jeho oddělené
složce atelier/, originály a odvozené náhledy se evidují obsahovými otisky.
Čtení nic nevytváří, nesmí sledovat symlinky ani vydat obrázek cizí místnosti.
Frontend přenáší jen neprůhledné identity; nemá vstup pro libovolnou cestu.

AI generování a modelový chat nejsou připojené. Jde o lidské návrhy/poznámky
nad podkladem; rozměrový model, Konva, 3D a kolize následují samostatně.
Placená aktivace potřebuje volbu modelu, měření a schválený rozpočet.
Nové závislosti, systémová instalace, push a nasazení nejsou součástí kroku.

Aktuální kanonický handoff je memory/handoffs/workstreams/project-neuberk-kacenka.md;
historické červnové návrhy níže se tím nemažou. Kanonická cesta nového TVBCP
je registrovaná, ale dokument nebyl výslovně domluven ani vytvořen; vazbu
dořešit před dalším vývojem přes Human–Adam. Přesný důkaz a další krok:
memory/reports/interior_atelier_p1_20261105.md.

Vydání: následným „ok p+n pro vše“ dne 2026-11-05 Míla výslovně schválil
společný push a nasazení celého hotového main. Závazný konečný výsledek bude
v logs/interior_all_release_20261105.log a interior_all_verified_20261105.log;
tento zápis sám nepotvrzuje dokončení. Oddělená Datova větev není součástí.
Fyzická přejímka Jany a připojení AI zůstávají dalšími samostatnými kroky.

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
