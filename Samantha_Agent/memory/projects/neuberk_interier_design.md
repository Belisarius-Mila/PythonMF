# Neuberk interier design


## 2026-11-05 21:04 CET — schválený živý AI pilot a příprava nasazení

Míla přesnou větou globální brzdy schválil Terra/high, jeden rozbor vybraných
soukromých podkladů, jeden obrazový požadavek, následné Terra p+n a registrovaný
upgrade kompatibility vlastní e-mailové služby. Není nutné souhlas opakovat.

Živý pilot je přijatý. Proběhl právě jeden potvrzený chatový tah a jeden
potvrzený obrazový tah přes původní sdílený socket/server 0.163.0. Obrazový tah
vrátil dva platné PNG (1672 × 941) a rozporný chybový text; oba skutečné
výsledky byly místně ověřené a uložené jako dvě neměnné AI varianty bez dalšího
modelu. UI stav vychází z ověřených artefaktů a nabízí otevření obou variant.
Žádný další placený pilot se nespouštěl. Původní zadání má stále revizi 7,
původní podklady zachované; model dostal jen jeden explicitně vybraný podklad.

Dvě přípravná selhání nepřijala žádný modelový tah. Dokumentovaný readOnly.access
server odmítá; používá se explicitně povolené permission-profile API, soukromý
profil pouze v konfiguraci konkrétního vlákna, minimální systémové čtení a čtení
snapshotu bez zápisu/sítě. Server musí potvrdit přesný profil, cwd, model a
approvalPolicy=never. Prázdná konfigurace permissions=null je ošetřená.
Pokračování přípravy zachovalo původní job/client ID/vlákno a vyžadovalo
nečinné vlákno, pouze metadatový rollout a doloženou sondou zakázané odesílání.
Timeout ani skutečný dřívější tah opakovat nelze. Globální konfigurace a App Server
se neměnily. Rychlost je výslovně Standard; zděděné priority/Fast se nepoužije.

Kritický modelový klient, instrukce a oprávnění mají otisk skutečné exekuce.
Následná oprava pouze zpracování obrazových artefaktů byla ověřená přehráním
původních terminálních journalů; změna exekučního otisku takové ověření blokuje.
Důkaz: logs/interior_ai_pilot_verified_20261105.log; cílených 133 testů PASS
včetně 4 Node DOM scénářů; závěrečná plná brána PASS: 2574 testů,
0 chyb, 31 přeskočených (393,754 s). Soukromé důkazy, fotografie
a odpovědi zůstávají mimo Git. Centrální role ještě není zapsaná ani aktivní.

Další krok: checkpoint a registrované kompatibilní p+n přes Terru,
upgrade vlastní e-mailové kopie se zachováním business stavu, potom aktivace role
z přijatého důkazu a závěrečné p+n. Nový TVBCP stále nebyl domluvený.
Starší záznam o čekajícím souhlasu níže je historický, nyní překonaný.


## 2026-11-05 — skutečný AI architekt připravený lokálně

Míla zadal zapojení AI. Nové lokální rozhraní má rozhovor nad explicitně
vybranými podklady a samostatné „Vytvořit AI návrh“. Výsledky patří ke
konkrétní variantě, obrazový výstup vytvoří nový neměnný návrh. Celé zadání,
poznámky, rozhovor a obrazové vstupy se před odesláním zmrazí. Přepnutí
místnosti ani novější rozepsané změny odpověď nepřesměrují nebo nepřepíšou.
Nejistý požadavek se neopakuje; původní výsledek lze číst a místně dokončit.

Transport zůstává Codex App Server; klient nově přijímá volitelné localImage
vstupy, výchozí textový kontrakt zůstává. Pouze náhledy vybraných podkladů,
bez EXIF, kontext aktuální varianty, žádné automatické generování. Chat má
vypnuté obrazové generování, shell, konektory, paměti a delegaci; obrazový
režim povoluje jen nativní obrazový nástroj navíc. Nezavádí se nové závislosti.

145 cílených kontrol PASS, Node DOM dvojklik/kontext/neověřené HTTP PASS;
plná brána PASS: 2559 testů, 0 chyb, 31 přeskočených. Lokální krok dokončený.
Produkční role ještě není aktivovaná, placený pilot ani
nové p+n nebyly provedené. Položená otázka na Terra/high a rozsah jednoho
pilotního rozboru / jednoho obrázku zatím nemá odpověď.

Nová role vyžaduje před aktivací kompatibilní parser v běžícím Cockpitu
i samostatném e-mailovém agentu. Audit jeho kopie ac9f3bed tuto kompatibilitu
nepotvrdil; příslušný registrovaný upgrade vyžaduje přesnou globální větu.
Zatím se služba, její stav a config/agent_roles.json neměnily. Aktivátor tyto
brány kontroluje a zpřístupnění role odkládá až do odpovídajícího nasazení.
Handoff: project-neuberk-kacenka.md; report interior_ai_integration_20261105.md.
Starší výroky níže jsou historické milníky; živé AI zapnutí zatím není prokázané.

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
