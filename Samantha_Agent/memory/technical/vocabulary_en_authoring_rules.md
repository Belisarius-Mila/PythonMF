# Pravidlo autorství Vocabulary EN

Schváleno Mílou15.11.2026 před zahájením implementace: „Doplň deset hlavních
částí těla. Ještě předtím zapiš tvůj návrh jako pravidlo. Pak proveď vývoj.“

Tento dokument je kanonickým pravidlem pro jednotlivé i dávkové doplňování.
Výchozí návrh je zachovaný níže; časový stav442/432 a checkpoint97d34aef
v převzatém návrhu popisují jeho vznik. Pravidlo nevydává návrh za implementaci.

Závazný rozsah první verze: interní registrovaný Python postup náhled,
příprava a zařazení. Přirozené zadání interpretuje Data v chatu, tentýž
postup přijme jednu položku nebo strukturovaný seznam/CSV. Formulář může
přibýt později. Hotové obrázky se předávají ze schváleného imagegen nebo
existující knihovny; audio používá dosavadní registrovaný generátor.

„Doplň deset“ znamená deset nových významových karet po kontrole duplicit.
Místní doplnění včetně médií je tímto zadáním autorizované; nové p+n není
součástí zadání. První skutečná dávka jsou head, face, ear, nose, mouth,
neck, arm, hand, leg, foot podle vět v převzatém návrhu.

Před úplným zařazením musí být ověřené všechny položky a média. Nedokončený
externí požadavek se neopakuje automaticky. Zařazení se opírá o přesnou
zdrojovou revizi, stabilní identitu dávky, kontrolu souběhu a účtenku.
Obnova přerušeného zápisu rozlišuje původní a očekávané výsledné bajty;
cizí změnu nepřepisuje. Dokončená dávka se znovu nepřidává.

Původní UID, osobní A–D a18 témat zůstávají zachované. Nové karty nepřebírají
osobní výběry ani Benji. Konkrétní význam, slovní druh, věta a obrázek
musí souhlasit. Nové obrazové vazby jsou explicitní; others není hotová ilustrace.
Čtyři reference audia na kartu: heslo EN/CZ a věta EN/CZ, sdílení shodných
nahrávek podle přesného textu/hlasu/tempa. Náročnost je draft, nikoli CEFR.

## Schválený výchozí návrh

VOCABULARY EN — NÁVRH VSTUPU NOVÝCH SLOVÍČEK
15. 11. 2026 — podklad k příštímu rozhodnutí, nikoli hotová nová funkce

Doporučení: ovládat první verzi naším chatem a pod ním sjednotit autorský
postup. Jeden postup obslouží jednotlivé slovíčko, vložený seznam i tematické
zadání. Samostatný formulář může později používat stejné operace. Studentům
zůstane jednoduchá galerie; PINy A–D slouží osobním výběrům, nikoli změnám
společného slovníku.

1. Co už máme a co chybí

Ověřeno na místní zdrojové větvi s checkpointem97d34aef: CSV a katalog
trvalých významových identit, export webových dat, obrázky/náhledy,
slovní i větné audio, filtry a místní výběry A–D. Aktuální místní obsah
má442 záznamů,432 aktivních. Tento návrh není čerstvý audit veřejného webu.

Chybí hlavně jednotný autorský vstup a řízení celého doplnění. Dnes jsou
jednotlivé nástroje oddělené. První novou funkcí by proto měl být jeden
opakovatelný postup připravit–ověřit–zařadit, který používá současné zdroje.
Samostatnou novou databázi slovíček nepotřebujeme.

2. Jednotlivé přidání

Příklad zadání: „Přidej shoulder — rameno, s obrázkem a jednoduchou větou.“
Míla nemusí zadávat technická ID, názvy souborů ani příkazy v terminálu.

Data navrhne konkrétní význam, český překlad, slovní druh, jedno hlavní téma
z existujících18, případně vedlejší témata, příkladovou větu EN/CZ a obrázek.
U běžného konkrétního zadání je doplní automaticky. Nejasnost typu bank
(banka/břeh) se ukáže jako volba významu; ostatní jasné položky mohou pokračovat.

Významově nová karta dostane nové UID. Oprava téže existující karty ponechá
její UID. Doplnění jiného významu second ponechá původní sekundu a vytvoří
samostatnou kartu druhý. Stejné EN se nesmí automaticky sloučit ani odmítnout.

3. Dávka ze seznamu nebo tabulky

Vstupem může být prostý seznam, vložená tabulka nebo CSV v UTF-8.
Základní sloupce mohou být pouze EN a CZ; věty, slovní druh a téma jsou volitelné.
Import musí předem ukázat, jak rozpoznal oddělovač a sloupce. Uvozovky,
čárky a středníky uvnitř věty zpracuje jako běžné CSV, nikoli dělením řádku
na každé čárce. Technická interní pole se při importu přidělí automaticky.

Dávka se nejprve porovná se současným katalogem i sama se sebou:
- již existující stejný význam: použít stávající kartu, nevytvářet kopii;
- jiný význam nebo slovní druh stejného hesla: nabídnout novou významovou kartu;
- původní rezervovaný překlad/alias: ukázat existující identitu a současné znění;
- skrytá položka: vysvětlit její stav, neobnovovat ji potichu;
- nejasný význam: vyžádat jen potřebné upřesnění konkrétní položky.

Je nutné porovnávat význam, slovní druh a kontext. Podobný zápis sám nestačí.
Singulár/plurál se nesmí řešit strojovým odříznutím koncovky s/es. Platí již
schválené rozlišení pravidelných duplicit, nepravidelných tvarů a jiných významů.

4. Tematická dávka z přirozeného zadání

Příklad: „Doplň asi10 hlavních částí těla, včetně obrázků a vět.“

Doporučený výklad slova doplň: přibližně10 NOVÝCH významových karet po odečtení
stávajících. U formulace „vytvoř okruh celkem10 slov“ by počet naopak zahrnoval
i existující karty. V náhledu musí být jasně napsáno, které z těchto dvou zadání
postup provádí. Tím se zabrání tomu, aby se kvůli naplnění počtu tvořily duplicity.

Postup:
a) Zkontrolovat pokrytí tématu v katalogu.
b) Navrhnout chybějící základní pojmy; ukázat stávající a nové odděleně.
c) Připravit texty a při jasném zadání odpovídající obrázky a audio.
d) Zkontrolovat celý konkrétní balíček a uložit místní checkpoint.
e) Publikaci provést odpovídajícím samostatně autorizovaným Terra p+n.

Při kontrole zdrojů už v tématu Tělo a zdraví jsou eyes=oči a hair=vlasy;
další dvě položky skupiny jsou energy a health. Deset níže navržených názvů
ani jejich běžné anglické plurály se ve zkontrolovaném obsahu nevyskytují.
Eyes nepřidávat znovu. Případný přechod na základní tvar eye má být samostatně
viditelná obsahová úprava podle našich pravidel, se zachováním původního UID.

Konkrétní návrh první zkušební dávky — ZATÍM NEZAŘAZENO:

EN      CZ         Příklad EN                     Příklad CZ
head    hlava      I nod my head.                 Kývám hlavou.
face    obličej    I wash my face.                Myji si obličej.
ear     ucho       This is my ear.                Tohle je moje ucho.
nose    nos        Touch your nose.               Dotkni se nosu.
mouth   ústa       Open your mouth.               Otevři ústa.
neck    krk        This is my neck.               Tohle je můj krk.
arm     paže       Raise your arm.                Zvedni paži.
hand    ruka       I wash my hands.               Myji si ruce.
leg     noha       I stand on one leg.            Stojím na jedné noze.
foot    chodidlo   Put your foot on the floor.    Polož chodidlo na podlahu.

Všech deset hesel jsou podstatná jména a typ učiva Slovíčka. Rozkazovací
příkladová věta z názvu části těla neudělá Interakci. Arm a hand mají mít
odlišný překlad i vyznačenou část končetiny; podobně leg a foot. Pravidelný
plurál může být v příkladové větě, aniž vznikne další duplicitní karta hands.
Budoucí foot/feet patří k nepravidelným tvarům, které zachováváme.

Pro názorné části těla navrhuji pracovní náročnost1 s příznakem draft,
nikoli tvrzení o oficiální úrovni A1. Rozhodnutí není závislé na Oxford3000.

5. Obrázky a věty

Pro dávku Tělo zvolit jednotný přehledný styl: cílová část jasně zvýrazněná,
okolí potlačené. Ear má ukazovat ucho, nikoli celý obličej s nejasnou šipkou.
Head a face se mají vizuálně rozlišit. Obrázky bez napsaného hesla, aby
neprozrazovaly anglickou odpověď při procvičování.

Nejprve posoudit existující použitelný obrázek. Nový vytvářet, když přesný
význam vhodný obraz nemá. Každá přijatá nová karta dostane pevnou vazbu na
konkrétní soubor, stejně jako nynější zrevidované karty. Náhradní others
se nesmí vydávat za dokončenou vlastní ilustraci.

Věty mají být krátké, přirozené a skutečně procvičovat zvolený význam.
Česká věta má odpovídat anglické. Oba texty lze upravit ještě v návrhu;
při opravě už vytvořené věty se změní jen dotčené audio. Příkladové věty
budou vlastní, bez kopírování Oxford obsahu.

6. Audio a průběh dávky

Zachovat současné hlasy a tempo: Aria pro EN, Vlasta pro CZ, -10%.
Každá karta má čtyři zvukové reference: heslo EN/CZ a větu EN/CZ.
U deseti karet jde nejvýše o40 nových nahrávek; přesný počet klesne podle
shodných již hotových textů. Anglické heslo pro více významů může sdílet MP3,
každý význam ale zachová vlastní identitu, překlad a větu.

Průběh má být čitelný: připravené položky, hotové obrázky, hotové zvuky,
nejasnosti a konečný výsledek. Při přerušení se dávka obnoví podle své
účtenky. Dokončené obrázky a zvuky se nevyrábějí znovu; nejistý externí
požadavek se automaticky neopakuje.

Když jsou například dvě položky nedokončené, musí být jasně vidět8 hotových
plus2 rozpracované. Výchozí dokončení má respektovat objednaný celek;
případné vydání jen hotové části je výslovná změna rozsahu, nikoli tichý úspěch10/10.

7. Ovládání bez opakovaných potvrzení

„Navrhni10 slov“ = obsahový návrh k posouzení, bez výroby nových médií.
„Připrav10 karet včetně obrázků, vět a audia“ = úplný pracovní balíček.
„Přidej/doplň10 karet včetně obrázků, vět a audia“ = oprávnění k místnímu
zařazení jasně vymezeného balíčku; stejný souhlas se nemá žádat znovu
pro každý řádek či obrázek. Náhled a závěrečný přehled zůstávají dostupné.
U skutečné nejasnosti se řeší příslušná položka, ne celá dávka od začátku.

Publikace zůstane samostatná. Pokud ji Míla výslovně zahrne do zadání,
naváže registrované p+n s auditem celého skutečného GitHub balíčku.
Pouhé kliknutí studenta na webu ani PIN osobního profilu nesmějí spouštět
autorský zápis nebo generování společného obsahu.

8. Nejmenší užitečná technická první verze

Jeden registrovaný autorský postup se třemi operacemi: návrh, příprava,
zařazení. Vstup do něj poskytne nejprve náš chat; pozdější interní formulář
použije tentýž postup. Volba knihovny nebo nového modelu není součástí návrhu.

Pracovní balíček uloží zdrojovou revizi, položky, stav médií a výsledky kontrol.
Nové trvalé identity přidělí jednou; při pokračování zachová už přidělené.
Před zařazením zkontroluje souběžné změny a možné kolize, protože slovník
můžeme doplňovat průběžně. Zapisuje jeden autor v daném okamžiku.

Příprava proběhne v odděleném autorském prostoru. Současné CSV, katalog,
webová data a média se převezmou jako jeden ověřený balíček s checkpointem.
Nedokončená změna více souborů se nesmí prohlásit za hotovou ani publikovat;
obnova musí vycházet ze skutečného stavu a uložené účtenky.

Nové karty se nezařazují automaticky do A–D. Zůstanou společně dostupné
pod svými tématy a Míla či uživatel si je vybere do osobní slovní zásoby.
Nová témata se nezakládají automaticky; těch18 současných zachováme.
Stávající CSV a katalog zůstanou autoritou; žákovský web nevyžaduje nový
editor ani změnu své architektury ukládání osobních výběrů.

9. Doporučené pořadí realizace

Nejprve jednotlivé přidání celého hotového záznamu a následně stejnou cestou
import seznamu. Potom tematický návrh chybějících slov, který vytváří tentýž
formát dávky. Nakonec podle potřeby jednoduchý interní formulář s přehledem
obrázků a poslechem. Nevytvářet tři nezávislé způsoby zápisu.

Přejímací zkouška první verze: právě deset částí těla výše. Musí vzniknout
jen skutečně nové významy, přehratelné čtyři zvukové reference na každou
kartu, zkontrolované ilustrace a stejné výsledky při obnově přerušené dávky.
Původní UID, osobní A–D a18 témat musí zůstat zachované.

Dnešní výsledek je tento návrh. Žádné části těla, nové obrázky ani nahrávky
se tímto dokumentem nepřidávaly; zdrojový checkpoint97d34aef zůstává čistý.
