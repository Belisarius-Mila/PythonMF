# Camino — pracovní návrh v0.2-DRAFT

**Datum:** 13. září 2026  
**Zadavatel:** Míla  
**Stav:** odborně dopracovaný pracovní podklad, čeká na uživatelská rozhodnutí Q1–Q8. Nejde ještě o schválené zadání k implementaci.  
**Účel:** zachovat návrh, vyřešit produktové alternativy a následně připravit malé, ověřitelné úkoly pro Codex.

Tento dokument obsahuje návrhová rozhodnutí a požadavky, nikoli již implementované funkce nebo výsledky testů. Číselné parametry označené jako výchozí jsou návrhové hodnoty, které je třeba ověřit prototypem. Technické volby přebírá Samantha a později Codex; od Míly se požadují pouze rozhodnutí o používání, soukromí, podobě výsledku a nákladech.

## 1. Co je skutečně potvrzené

Míla chce jednoduchou aplikaci pro fotografování, video, hlasové komentáře a úvahy během pouti do Santiaga. Obsah má putovat přes Tailscale na Mac server v České republice. Hlasové záznamy se mají přepisovat, jazykově upravovat AI a ukládat do denní šablony. Film je zamýšlený výstup, jeho podoba zatím není rozhodnutá. Vývoj má probíhat postupně prostřednictvím Codexu.

Z dřívějšího kontextu je znám iPhone 14 a MacBook Pro Intel s macOS Sequoia 15.7.7. Není potvrzeno, že tento MacBook je zároveň zamýšleným domácím serverem. Aktuální iOS, stav vývojářského účtu, skutečný serverový disk a dostupnost záložního úložiště musí zjistit přípravný technický audit; nejde o témata tohoto uživatelského dotazníku.

Aplikace má být nejprve osobní nástroj, nikoli veřejná služba. Více autorů, rodinný přístup, úplný záznam trasy, cloudové AI zpracování a placené členství Apple jsou dosud nepotvrzené alternativy.

## 2. Změny oproti prvnímu návrhu

| Původní zjednodušení | Pracovní zpřesnění |
|---|---|
| Výsledkem má být automatický film | Nejprve bezpečný archiv a deník; film vzniká z jejich podkladů. Automatický sestřih je návrh, nikoli garantovaný kvalitní dokument. |
| Každá fotografie je samostatný Moment | Moment je kontextová událost, která může obsahovat více fotografií, video i komentář. Samostatná nahrávka je rovněž platný Moment. |
| Složky podle dní jsou hlavní úložiště | Originály mají neměnné identifikátory; denní složky a stránky jsou přegenerovatelné pohledy/exporty. Změna přiřazení dne nepřesouvá originál. |
| Server podle GPS určí etapu | Datum lze přiřadit pravidlem; skutečný začátek/konec etapy a název místa se nesmějí domýšlet. |
| Po připojení se všechno samo odešle | Přenos na pozadí je pomoc, ne záruka. Povinná je viditelná fronta, ruční synchronizace a testy se skutečným iPhonem. [S1] |
| Kontrolní součet znamená bezpečnou zálohu | Kontrolní součet dokládá shodu přenesených dat. Neřeší druhou kopii, havárii disku ani chybný výmaz. |
| AI opraví text před uložením | Nejdříve bezpečně uložit původní audio, potom surový strojový přepis a teprve pak oddělenou jazykovou úpravu. |
| Filmová varianta přepisu může být volná | Bez svolení žádné přidané okolnosti, motivace, počasí nebo emoce. Filmový text je samostatný návrh, nikdy náhrada svědectví. |
| Stačí napsat SwiftUI aplikaci | Ještě před větším vývojem ověřit instalaci a dobu její platnosti. Bezplatné profily Personal Team podle Apple vyprší po 7 dnech. [S2] |

## 3. Produktový cíl a pořadí priorit

**Pracovní produktový cíl:** jednou zachytit okamžik a mít z něj dohledatelný originál, srozumitelný deníkový záznam a použitelný filmový podklad.

Priorita P0: dokončený záznam bezpečně uchovat, umět jej najít a získat z telefonu i bez domácího serveru. Priorita P1: spolehlivě přenášet a nezávisle zálohovat. Priorita P2: přepis, korektura, denní stránka. Priorita P3: návrh střihu a export filmu.

Funkce nižší priority nesmí blokovat vyšší. Nedostupná AI nebrání nahrávání ani přenosu. Chyba při renderování filmu nebrání otevření deníku. Nedostupný server nebrání pořizování záznamů.

Předběžně preferujeme skutečné vlastní záběry, vlastní hlas a původní zvuk místa. Generované obrazy cesty, uměle doplněné zážitky a klonování hlasu nejsou součástí návrhu.

## 4. Uživatelské rozhraní

### 4.1 Úvodní obrazovka

Čtyři hlavní tlačítka: **Foto**, **Video**, **Komentář**, **Úvaha**. Doplňkové ovládání: **Označit okamžik**, **Dnes**, **Synchronizace**. Nastavení je mimo hlavní pracovní plochu.

Komentář znamená popis konkrétního místa či situace. Úvaha znamená osobní vyprávění; technicky může používat stejný záznam zvuku, ale dostane jiná pravidla jazykové úpravy a případně soukromí. Délka sama o sobě typ neurčuje.

Hlavní ovládání navrhnout pro jednu ruku, velký text a venkovní použití. Během záznamu zobrazovat zřetelné nahrávání, čas a indikaci mikrofonu. Nikdy nezobrazit úspěch před skutečným uložením. Nevyžadovat vyplnění názvu ani polohy.

### 4.2 Foto a video

Po dokončení nabídnout náhled a nepovinné „Přidat komentář“. Žádné povinné dialogové okno po každé fotografii. Umožnit přidání dalšího média ke stejnému Momentu a pozdější propojení již existujícího komentáře.

Výchozí návrh pro vlastní záznam: video 1080p, 30 snímků/s, SDR; formát a kompresi potvrdit testem kvality, velikosti a kompatibility. Rozlišení je technická volba, nikoli otázka na zadavatele. Importovaná kvalitnější média vždy uchovat v původní podobě. Originály kvůli filmu nepřekódovávat.

Pro zamýšlený film na televizi jemně doporučovat natáčení na šířku, ale nikdy neblokovat záběr na výšku. Portrétní záběr později vložit do 16:9 plochy bez svévolného ořezu důležitého obsahu.

První implementace nemusí kopírovat celý systémový Fotoaparát. Zvolit nejjednodušší nativní řešení, které projde praktickými testy. Vlastní rozsáhlé ovládání objektivů, expozice a filmových režimů není P0.

### 4.3 Hlas

Jedním stiskem zahájit, druhým dokončit. Poté lze přehrát, přiřadit k Momentu nebo dni, označit důležitost a upravit soukromí. Pozastavení nahrávky je volitelné až po ověření základního nahrávání.

Pro delší úvahy navrhnout průběžné uzavírání zvukových segmentů s návazností, aby případná havárie neohrozila celou nahrávku. Segmentace nesmí slyšitelně vynechávat řeč; ověřit na zařízení. Zachráněné segmenty označit a nepředstírat úplnost. Při přerušení hovorem uložit, co je dokončeno, a srozumitelně oznámit přerušení.

Možnost pokračovat s uzamčenou obrazovkou patří do samostatného technického testu. Neslibovat záznam při nuceně ukončené aplikaci. Změny mikrofonu, Bluetooth a vytažení sluchátek nesmějí proběhnout bez zřetelného stavu.

### 4.4 Označení okamžiku není totéž co hvězdička

„Označit okamžik“ vytvoří prázdný Moment s časem a případnou polohou. Hvězdička na existujícím Momentu pouze říká, že je důležitý. Oba úkony musí fungovat offline.

Dodatečně namluvená vzpomínka má vlastní čas nahrání a explicitní vazbu na starší událost. Aplikace její čas nepřepisuje na čas události.

### 4.5 Import a nouzové použití

Povinný import vybraných fotografií a videí z knihovny telefonu. Při importu uchovat původní čas a dostupná metadata; pokud metadata chybí, umožnit ruční zařazení a označit původ nejistoty. Kopie musí být skutečně dostupná aplikaci, nestačí pouze odkaz na náhled.

Volitelná kopie nových fotografií a videí do systémové knihovny chrání proti některým chybám vlastní aplikace, není však nezávislou zálohou telefonu. Nemazat automaticky položky v systémové knihovně. Samostatně implementovat export vlastních záznamů a manifestu do běžně čitelného balíčku.

### 4.6 Dnešní den

Časová osa fotografií, videí, komentářů a úvah. Filtr „Nesynchronizované“, „Důležité“ a „Ke kontrole“. Detail záznamu obsahuje originál, upravený text, stav přenosu a možnost přepsat či vrátit změnu. Večerní kontrola může být nabídnuta, nesmí být povinná pro zachování dat.

## 5. Datový model

### 5.1 Hlavní objekty

**Trip:** cesta, identifikátor, pracovní název, jazyk, začátek, nastavení soukromí a přenosů. Model není napevno svázán s rokem 2026.

**JourneyDay:** uživatelská denní kapitola; obsahuje datum, pořadí, případný název etapy, ručně potvrzený začátek/konec a stav redakční kontroly. Dny lze vytvořit bez obsahu. Přesuny, volné dny a příjezd mohou být běžné kapitoly.

**Moment:** identifikátor vytvořený již offline, autor/zdrojové zařízení, čas události, denní kapitola, druh, důležitost, soukromí a případná vazba na jiný Moment.

**Asset:** konkrétní originální soubor se stabilním ID, typem, velikostí, kontrolním součtem, časem pořízení, dostupnými technickými metadaty a stavem přenosu. Jeden Moment může mít více Assetů. Označený okamžik nemusí mít žádný.

**TextRevision:** surový strojový přepis, jazyková úprava, ruční revize nebo filmový návrh. Vždy uvádí zdroj, předchozí revizi, autora změny, model/verzi instrukcí, datum a stav schválení. Surový přepis není garantovaně doslovný; autoritativní zdroj je audio.

**ProcessingJob:** perzistentní úkol pro přepis, náhled, deník, render nebo zálohu. **BackupReceipt:** ověřený záznam konkrétní kopie. **ExportRevision:** přesná verze deníku nebo filmové časové osy s použitými zdroji.

### 5.2 Čas, místo a den

U každého média uchovat čas UTC, lokální datum a offset při pořízení, identifikátor časového pásma, je-li znám, a čas příjmu serverem. Čas příjmu nikdy nepoužívat jako náhradu času pořízení. Časové pásmo domácího serveru nemá řídit den cesty.

Den se výchozím pravidlem odvodí z místního data zachycení. Uživatel může záznam přiřadit k jiné denní kapitole, například u pozdní večerní úvahy. Tato redakční změna nezmění původní metadata. Při pohybu mezi pásmy zachovat obě informace; nestavět řazení jen na textovém názvu souboru.

GPS obsahuje souřadnice, čas měření a udanou přesnost. Není-li dostupná nebo je příliš stará, nezdržovat snímek a označit absenci či nejistotu. Název místa oddělit na ručně potvrzený, technicky odhadnutý a AI navržený. Žádný odhad neproměnit bez označení ve fakt.

Body pořízení nejsou GPS stopa celé cesty a nesmějí být označeny jako skutečně prošlá trasa nebo zdroj přesné kilometráže. Celou stopu řeší Q5.

### 5.3 Neměnnost, úpravy a konflikty

Originální soubory neměnit; opravy jsou nové revize metadat a textu. Ruční úprava má přednost před pozdější AI generací. Změna textu nezpůsobí opakovaný upload videa.

První verze: jeden hlavní autor. I tak web a telefon mohou editovat stejný text. Použít revizní číslo a kontrolu očekávané revize; při konfliktu uchovat obě verze a požádat o výběr, nikoli tiše přepsat. Více autorů aktivovat jen po potvrzení Q4.

## 6. Offline bezpečnost a synchronizace

### 6.1 Bezpečné lokální uložení

Média ukládat do trvalého prostoru aplikace, ne do vymazatelné cache. Záznam vzniká v dočasném souboru, po řádném dokončení je přesunut na konečné místo a zapsán do lokální databáze. Po startu aplikace provést obnovu rozpracovaných operací a vyhledat osiřelé soubory.

Úplnou atomickou transakci přes souborový systém a databázi nepředstírat; navrhnout journal a opravné kroky pro havárii mezi jednotlivými operacemi. Textové poznámky průběžně ukládat. Nová fotografie se považuje za uloženou až po potvrzení zápisu, video až po uzavření souboru. Rozpracovaný záběr může být po havárii neúplný.

Hlídání volného místa: varování s předstihem, zákaz zahájení velké nahrávky při kritickém nedostatku a snaha řádně dokončit rozpracovaný záznam. Prahy a rezervu určit měřením. Kvůli novému videu nikdy automaticky nesmazat nesynchronizovaný originál.

### 6.2 Čtyři oddělené stavy

V uživatelském rozhraní rozlišit **Uloženo v telefonu**, **Ověřeno na Macu**, **Záloha ověřena**, **AI zpracováno**. To jsou nezávislé údaje. Ani zelený přepis, ani existence náhledu nedokládají existenci zálohy originálu.

Přenosový automat: připraveno → čeká podle pravidel → přenáší se → ověřuje se → ověřeno. Odlišit čekání na síť, chybějící přihlášení, problém serveru, nedostatek místa a porušená data. Nezahrnout všechny případy pod nekonečné „Synchronizuji“.

### 6.3 Navržený protokol přenosu

Klient vytvoří manifest s ID Momentu a ID Assetu, očekávanou velikostí a celkovým SHA-256. Server založí upload session a vrátí již přijaté části. Přenášejí se souborové části, předběžně 8 MiB; velikost je ladicí parametr, nikoli uživatelská volba.

Každá část má číslo, velikost a hash. Opakované zaslání totožné části je bezpečné. Stejný identifikátor s jiným obsahem je konflikt, ne tiché nahrazení. Klient vytváří jen omezený počet připravených souborových částí, aby neduplikoval celé velké video na telefonu.

Finalizace: server sestaví soubor, zkontroluje velikost a celkový hash, dokončí bezpečný zápis a evidenci a vydá potvrzení. Teprve potom telefon přejde do stavu „Ověřeno na Macu“. Havárii mezi přesunem souboru a databázovým potvrzením opravuje obnovovací procedura. Ztracená odpověď na dokončení nesmí vytvořit duplicitní originál: klient znovu načte stav Assetu.

SHA-256 se počítá proudově, velké soubory se nenačítají celé do paměti. Neúplné uploady se čistí konzervativně podle lhůty a aktivního stavu; jejich čištění nikdy nesmaže finální originál.

Návrhové koncové body: založení Momentu, založení uploadu, PUT konkrétní části, dotaz na přijaté části, dokončení uploadu, stav Assetu, čtení změn od kurzoru, revizní změna metadat a stav serveru. Přesné OpenAPI schéma vznikne až po uzavření rozhodnutí.

### 6.4 iOS a Tailscale

Navržená implementace používá souborové úlohy background URLSession a perzistentní lokální frontu. Apple výslovně uvádí, že nucené ukončení aplikace z přepínače aplikací ruší její přenosy na pozadí. Po novém otevření musí aplikace frontu obnovit. [S1]

Tailscale Serve navrhuji jako soukromé HTTPS zpřístupnění lokálního API; přístup dále omezit pravidly a autorizací aplikace. Nepoužít veřejné Funnel. Backend naslouchá jen na localhostu. [S3]

VPN On Demand je pomocná funkce a musí projít testem; není zárukou okamžitého přenosu ani probuzení vypnutého či spícího Macu. [S4] Nezavádět vlastní VPN do naší aplikace.

Uživatel dostane „Synchronizovat nyní“ s počtem zbývajících záznamů a bytů. Večerní režim s otevřenou aplikací je praktická záloha automatizace, nikoli jediný způsob přenosu. Zvlášť testovat hotelovou síť vyžadující přihlášení, uzamčený telefon a přechod mezi Wi-Fi a mobilní sítí.

### 6.5 Pravidla datového přenosu

Výchozí konzervativní návrh: originální video a velké dávky pouze Wi-Fi; metadata a malé zvukové záznamy mohou používat mobilní data po výslovném nastavení. Fotografie nejsou automaticky „malé“; i zde je vhodný denní limit. Jednorázové povolení mobilního přenosu musí ukázat objem a platit jen pro zvolenou dávku.

Odhad úložiště určit testovacím dnem: součet skutečně naměřených mediálních velikostí × délka cesty plus rezerva a pracovní prostor. Nenahrazovat měření paušálním slibem, že určitý počet GB stačí. Před cestou ověřit i příjem z jiné sítě, nikoli pouze doma přes Wi-Fi.

## 7. Mac server, provoz a zálohy

### 7.1 Navržená architektura

Swift/SwiftUI klient → soukromé HTTPS přes Tailscale → Python/FastAPI → SQLite a soubory → samostatný pracovní proces → AI, náhledy a později render.

Na telefonu předběžně Core Data pro lokální evidenci a SwiftUI pro rozhraní; na serveru SQLite, soubory a malá serverově renderovaná webová stránka. Konkrétní podporované verze připnout po technickém auditu. Nezavádět Docker, Kubernetes, Redis ani velký frontend bez nové prokázané potřeby.

### 7.2 Trvanlivá fronta prací

FastAPI přijímá a potvrzuje uploady. Dlouhé přepisy a renderování neprobíhají uvnitř přijímacího požadavku. Dokumentace FastAPI rozlišuje jednoduché úkoly na pozadí a náročné zpracování; zde navrhujeme vlastní jednoduchý perzistentní worker nad SQLite, nikoli pouze úkol v paměti webového procesu. [S10]

Úkol má stav, počty pokusů, dobu příštího pokusu, dočasné přidělení workeru a jednoznačný klíč podle zdroje/verze operace. Po restartu lze rozpracované úkoly obnovit. Zpracování navrhnout opakovatelné; existující výsledek se nepřepisuje bez verzování.

U externí AI nelze bez podpory poskytovatele garantovat přesně jedno zpoplatněné volání při ztracené síťové odpovědi. Nejasný výsledek evidovat, omezovat automatické opakování a sledovat rozpočet. Rozhraní aplikace nesmí hlásit „žádné duplicitní poplatky“ jako jistotu.

### 7.3 Rozložení úložiště

```text
camino-data/
  originals/<trip_id>/<asset_id>/original.ext
  staging/<upload_id>/
  derived/<asset_id>/<recipe_version>/
  texts/<moment_id>/<revision_id>.json
  exports/<trip_id>/<export_revision>/days/
  manifests/
  project.sqlite
```

Denní Markdown/HTML soubory, náhledy a filmy lze obnovit ze zdrojů. Databáze a textové revize jsou důležité stejně jako média. Před exportem uložit seznam přesných vstupních verzí.

### 7.4 Dostupnost serveru

Přípravný audit ověří napájení, chování při uspání, nastartování služby, oprávnění k diskům a postup po restartu. Neprovádět slepé vypínání šifrování nebo automatické přihlášení jen pro pohodlí. Zkontrolovat obnovu po startu v reálném zabezpečeném nastavení.

Servisní stránka zobrazí: čas posledního kontaktu, volné místo, velikost fronty, poslední úspěšnou zálohu a obecný stav AI. Detailní logy neobsahují hesla, klíče, přepisy ani přesné polohy. Kódy chyb dovolí diagnostiku bez kopírování citlivých dat.

### 7.5 Politika záloh a mazání

Cíl: telefon + pracovní kopie na Macu + nezávislá verzovaná kopie. Druhá složka na stejném disku se za nezávislou kopii nepovažuje. Oddělený disk chrání proti některým poruchám, ne proti ztrátě celé lokality; další geograficky oddělenou kopii řešit podle dostupnosti a soukromí.

Záloha musí obsahovat originály, revize, manifesty a konzistentní databázi. SQLite nabízí API pro pořízení konzistentního snapshotu; neplánovat pouze kopírování otevřeného hlavního databázového souboru bez ohledu na jeho transakční stav. [S11]

„Záloha ověřena“ vyžaduje konkrétní BackupReceipt a pravidelný obnovovací test. Před první cestou obnovit vybraný den do prázdné složky, otevřít několik médií a přehrát audio.

P0: žádné automatické mazání originálů z telefonu. Pozdější ruční „Uvolnit místo“ lze nabídnout teprve pro soubory s ověřenou serverovou a záložní kopií, s jasným potvrzením. Výmaz položky z deníku je nejprve vratné skrytí; odstranění originálu a doba uchování záloh jsou oddělené operace.

## 8. Přepis, jazykové úpravy a věrnost

### 8.1 Zpracovatelská cesta

Nejdříve archivace originálu, poté případná pracovní zvuková kopie, přepis a oddělená korektura. Přepis se může zobrazit až po synchronizaci; offline dostupný text v první verzi neslibujeme. Originální audio zůstává přístupné vždy, když je lokálně dostupné.

OpenAI file transcription v ověřené dokumentaci přijímá mimo jiné M4A a má limit 25 MB na vstupní soubor. Dlouhé vstupy proto připravovat jako pracovní segmenty pod limitem, s návazností a zachováním časových offsetů; původní nahrávku neměnit. Konkrétní model vybrat podle zkoušky české řeči, nikoli napevno podle dnešního marketingového názvu. [S6]

### 8.2 Pravidla korektury

Výchozí profil opravuje překlepy, interpunkci a zjevná chybná rozpoznání. Opakování a výplňová slova lze redukovat jen v upravené verzi. U úvah zachovat význam, nejistotu, osobitý způsob řeči a emocionální odstín. Negaci, čísla, jména, časové souvislosti a subjekt „já/my“ neměnit bez doložené opory.

Příklad povoleného zásahu: „no dneska sme šli dlouho“ → „Dneska jsme šli dlouho.“ Nepovolený zásah: „u kostela bylo hezky“ → „Slunce ozářilo starobylý románský kostel a já cítil klid“, pokud tyto informace nejsou ve zdroji.

Nejasnost označit, ne doplnit. Systém musí připustit prázdný či nezpracovatelný výstup. Ticho a vítr se nesmějí proměnit v domnělou řeč. Jazykově správná věta není důkazem správného přepisu.

AI nedostane nástroje pro mazání, sdílení, přístup k serveru ani libovolné vyhledávání. Věty namluvené do záznamu jsou data, nikoli systémové instrukce. Případná pozdější encyklopedická poznámka o místě je samostatný, zdrojovaný doplněk, nikoli Mílova vzpomínka.

### 8.3 Revize a kontrola

Návrhový výstup korektury: upravený text, seznam podstatných změn a označené nejasné úseky. Schéma ověřit kódem. Structured Outputs pomáhá dodržet formát, ale podle samotné dokumentace nevylučuje obsahové chyby. [S8]

Uchovat surový přepis, první korekturu, ruční opravy i nové AI návrhy. Automaticky přijatý soukromý text se nesmí označit jako zkontrolovaný člověkem. Podstatné přepsání, vlastní jména, čísla a nejisté úseky směřují do fronty „Ke kontrole“. Toto třídění je pomůcka, ne spolehlivá detekce všech chyb.

Titulky k původnímu hlasu a čtenářský deník jsou odlišné výstupy. Silně přepsaná věta nebude sedět na původní audio. Věrné titulky proto odvozovat od časově zarovnaného přepisu; redakčně upravený text zobrazit vedle, nikoli předstírat, že jej autor přesně namluvil.

### 8.4 Externí AI a soukromí

Tailscale chrání cestu k domácímu serveru. Použití externího přepisového a jazykového API znamená další přenos audia nebo textu mimo domácí server. To je samostatné rozhodnutí Q7.

OpenAI uvádí, že data API standardně nepoužívá k trénování bez zapojení zákazníka do sdílení. Režimy uchování se liší podle endpointu: aktuální tabulka uvádí pro audio transcription žádné uchování pro abuse monitoring ani application state, zatímco běžné textové endpointy mohou mít abuse monitoring až 30 dní. Nelze proto slíbit „nikde se nic neukládá“. `store=false` samo o sobě není totéž co schválený režim Zero Data Retention. [S7]

Bez schválení cloudového režimu neodesílat reálné nahrávky. Alternativou je lokální přepis a korektura, nebo odložené zpracování; výkon a kvalitu na konkrétním Macu je nutné změřit. U položky „Bez externí AI“ neodesílat ani odvozený text této položky. Klíč poskytovatele patří pouze na server.

## 9. Denní šablona

Základní struktura kapitoly: datum a případně schválený název etapy; úvodní fotografie; chronologický přehled; krátké shrnutí; vlastní úvahy; důležité okamžiky; galerie; odkazy na originální hlas. Doplňkové údaje o trase jsou volitelné a mají původ hodnoty.

Souhrn vzniká pouze z dostupných záznamů a uvádí, ke kterému okamžiku byl sestaven. Pozdě doručené video nebo komentář zneplatní pracovní odvozený souhrn, nikoli již schválenou verzi. U schválené kapitoly nabídnout novou revizi s přehledem změn.

Chybějící údaje zůstávají prázdné. Nevyplňovat počasí, kilometráž, ubytování ani náladu AI odhadem. Nevyžadovat stejné množství textu každý den. Úvahy se nesmějí automaticky slít do souhrnu určeného rodině.

Exportovat alespoň HTML a Markdown s JSON manifestem a médii/relativními cestami. Čitelnost archivu nesmí záviset výhradně na databázi aplikace nebo konkrétním poskytovateli AI.

## 10. Film

### 10.1 Výstup podle dosud nepotvrzeného doporučení

Osobní cestopis propojující místa a úvahy, přibližně 20–30 minut po návratu. Krátká verze pro rodinu může vzniknout ze stejného projektu později. Denní automatické filmy nejsou povinnou funkcí před odjezdem; jednodušší je denní stránka a případně kontaktní přehled záběrů.

Přesná délka a míra osobního vyprávění závisí na Q1. Program nesmí uměle natahovat film jen kvůli cílové stopáži.

### 10.2 Materiál, zvuk a střih

Hvězdičky, komentáře, chronologie a uživatelské volby jsou první zdroj výběru. AI může navrhnout zajímavé úseky řeči; sama bez analýzy obrazu neví, co je ve videu. Automatická obrazová analýza velkého množství videí je samostatná pozdější funkce s náklady a soukromím.

Střihová časová osa ukládá ID zdroje, přesný počátek a konec úseku, délku, titulky, zvukové úrovně, případné hudební podklady a původ každé textové věty. Ručně uzamčené záběry se při dalším návrhu nemění.

Původní hlas je preferovaný, ale zvuk ve větru nemusí být použitelný. Deník přesto vznikne; komentář lze později namluvit znovu. Žádné nevyžádané klonování hlasu ani automatické přepisování vyřčeného obsahu syntetickým hlasem.

Hudba: v první verzi žádná; později pouze výslovně dodané či odpovídajícím způsobem licencované podklady s evidencí oprávnění. Nezabudovávat stahování komerčních skladeb do aplikace.

### 10.3 Render a export

Render podle validované časové osy provádí FFmpeg, nikoli jazykový model. FFmpeg nabízí potřebné filtry pro měřítko, skládání, titulky a zvukové úpravy; dostupnost konkrétních filtrů ověřit u instalované sestavy. [S12]

Pracovní kopie normalizují orientaci, rozměry, proměnlivou snímkovou frekvenci a případné HDR. Originál se nepřepisuje. Testy musí obsahovat výškové video, video bez zvuku, delší hlas, HEIC fotografii a importovaný HDR záznam.

Předběžný finální výstup: MP4 1080p 16:9 a samostatná časová osa v JSON; případný standardní výměnný formát pro střihový program řešit až podle ověřené kompatibility. Neslibovat univerzální otevření projektu ve všech editorech.

## 11. Zabezpečení a sdílení

Výchozí režim: soukromé, bez veřejných adres a bez automatického publikování. Oprávnění mají oddělovat vlastníka, případného přispěvatele a čtenáře. Rozšíření rolí závisí na Q4.

Tailscale přístup nestačí jako jediné pravidlo pro změnu či export obsahu. Pro aplikaci navrhnout odvolatelný přístupový token uložený v Keychain, na serveru bezpečně ověřovaný. Párování ověřit na konkrétních zařízeních. Omezit délku uploadů, typy vstupů, názvy a cesty; neverifikovaný vstup nepouštět do příkazového shellu.

Soukromé úvahy musí být vyloučeny již před generováním rodinné stránky nebo filmu. Nestačí skrýt původní kartu, pokud byl její text zapracován do souhrnu. Změna viditelnosti zneplatní dotčené odvozené výstupy a vyžaduje nové ověření sdílené verze.

Při sdílení odstranit přesné souřadnice a další vybraná metadata z exportovaných souborů, nejen z viditelné stránky. Originály se nemění. Rozhodnout, zda se místo zobrazuje přibližně a až se zpožděním; živé sdílení polohy není výchozí.

Ztráta telefonu: mít postup odvolání přístupu, zachování existujícího archivu a obnovení aplikace. Aplikace nemůže zachránit nesynchronizované soubory z fyzicky ztraceného telefonu; toto riziko nesmí maskovat tvrzením „všechno je bezpečné“.

## 12. Instalace a náklady

Ještě před hlavním vývojem ověřit build na dostupném Macu a instalaci na reálném iPhonu. Apple v ověřené tabulce uvádí pro Xcode 26.3 podporu macOS Sequoia od 15.6, zatímco novější řady mají jiné požadavky. Nevyžadovat automaticky nejnovější Xcode a neslibovat kompatibilitu pouze podle roku výroby Macu. [S5]

Bezplatný Personal Team vyžaduje obnovu instalace po sedmi dnech; to není vhodná výchozí cesta pro vícedenní pouť bez vývojového počítače. [S2] Technickou cestu delšího podepsání/distribuce zvolit po Q8 a ověřit dobu platnosti přesahující celou cestu s rezervou. Nenutit publikaci na veřejném App Storu.

Apple uvádí členství Developer Program 99 USD za rok, s regionální cenou při registraci. Jde o roční poplatek, ne jednorázovou cenu aplikace. [S13] Žádný nákup se tímto návrhem neprovádí ani neschvaluje.

Použití API se účtuje odděleně od předplatného ChatGPT. [S14] Vybrat rozpočtový limit pro AI; měřit spotřebu a před voláním rezervovat konzervativní odhad. Po dosažení limitu zastavit nové AI práce, nikoli nahrávání, upload či čtení archivu. Skutečné vyúčtování sledovat odděleně od odhadů; síťové chyby a souběžná volání mohou ovlivnit přesnost jednoduchého lokálního stropu.

Bez souhlasu s placenou nativní cestou posoudit náhradní zachytávání systémovými aplikacemi a následný import. Webová aplikace není automaticky rovnocennou náhradou z hlediska dlouhého offline záznamu a životního cyklu; její použití by vyžadovalo vlastní zkoušku. Nenavrhovat obcházení ochrany zařízení.

## 13. Balíček zadání pro Codex po potvrzení rozhodnutí

Zamýšlené soubory: `PRODUCT_SPEC.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `openapi.yaml`, `ACCEPTANCE_TESTS.md`, `OPERATIONS.md`, `PRIVACY.md` a jednotlivé úkoly v `tasks/`.

Do kořene repozitáře patří `AGENTS.md` s pravidly ochrany dat, způsobem testování, zákazem nevyžádaných rozšíření a požadavkem pracovat pouze na aktuálním úkolu. Codex tento typ instrukčního souboru podporuje a podle dokumentace jej načítá před prací. [S9]

Každý úkol obsahuje cíl, nutné vstupy, rozsah, výslovné ne-cíle, akceptační scénáře, příkazy pro testování a podmínky předání. Výstup Codexu musí rozlišovat implementaci, automaticky provedené testy, manuální testy a neověřená tvrzení.

## 14. Pořadí vývoje a ověřovací brány

| Fáze | Obsah | Podmínka dokončení |
|---|---|---|
| 0 — proveditelnost | Instalace na iPhone, lokální nahrávka, přenos jednoho souboru na Mac přes cizí síť, návrh záloh | Je prokázaná instalace na dobu cesty, uchování záznamu a dosažitelnost serveru. Zatím žádná rozsáhlá AI ani galerie. |
| 1 — offline základ | Moment, audio, jednoduchý den, restart a nouzový export | Režim letadlo → záznam → restart → přehrání a export bez serveru. |
| 2 — obrazová média | Foto, video, import, vazby komentářů, nedostatek místa | Fotografie a video po restartu nezmizí; import nezamění datum; přerušení má srozumitelný stav. |
| 3 — spolehlivý přenos | Manifesty, části, hash, retry, ruční synchronizace | Výpadek uprostřed uploadu, opakované dokončení a restart serveru nevytvoří duplikát ani falešné potvrzení. |
| 4 — záloha a provoz | Druhá kopie, obnova, stavový přehled | Obnovený den lze přečíst a přehrát mimo pracovní úložiště. |
| 5 — AI text | Přepis, korektura, revize, soukromí, rozpočtové limity | Originál je zachován; manuální revize se nepřepisuje; výpadek AI nezablokuje příjem. |
| 6 — deník | Denní šablona, prohlížení a export | Pozdní upload jde do správného dne; export se otevře bez naší aplikace. |
| 7 — terénní validace | Celodenní zkouška s reálným objemem dat a problematickou sítí | Změřená baterie, úložiště, přenosy a kontrola všech vytvořených záznamů. |
| 8 — film | Výběr, návrh časové osy, náhled, schválení, render | Výstup používá existující zdroje a neobsahuje vyloučené soukromé úvahy. |

Před odjezdem je hlavní cíl projít zachytáváním, přenosem, obnovou a deníkem. Filmovou část lze implementovat po návratu, protože již bude uchován materiál a jeho kontext. Datum odjezdu ani finální rozsah nejsou v tomto dokumentu závazně stanovené.

## 15. Akceptační scénáře napříč systémem

A01: Nový Moment bez připojení lze po restartu otevřít a exportovat.

A02: Pořízení videa při vypnuté AI a nedostupném serveru je stejné jako při online provozu.

A03: Přerušení uploadu, znovuposlání části a ztracená odpověď na finalizaci nezmění originál ani nevytvoří druhý Asset.

A04: Záměrně poškozená část vyvolá chybu kontroly; UI nepřejde do stavu ověřeno.

A05: Datum serverového příjmu o několik dní později nezmění původní den pořízení.

A06: Změna časového pásma a pozdní večerní úvaha nezmění originální metadata; manuální přiřazení kapitoly funguje.

A07: Nucené ukončení aplikace během přenosu a nové otevření obnoví kontrolu stavu; aplikace neslibuje průběžný přenos po nuceném ukončení.

A08: Restart pracovního procesu neodstraní čekající přepisy a nezpůsobí přepsání ručně upraveného textu.

A09: Krátký šum, ticho, vlastní jména, čísla a negace jsou součástí české testovací sady. Kontroluje se věrnost proti audiu, nikoli jen gramatika.

A10: Záznam „Bez externí AI“ nevyvolá síťové odeslání audia ani jeho textu k poskytovateli. Test provádět s mockem a kontrolou požadavků.

A11: Záznam označený soukromý se neobjeví v textu, titulcích, zvuku, názvu, náhledu ani GPS metadatech sdíleného výstupu.

A12: Nedostatek místa na telefonu i serveru vyvolá srozumitelnou chybu bez automatického smazání existujících originálů.

A13: Obnova náhodně vybraného dne ze zálohy na jiné místo uspěje včetně textových revizí a vazeb médií.

A14: Odvolaný token nemůže přidávat, číst ani exportovat data; chybné názvy souborů nemohou zapsat mimo určené úložiště.

A15: Portrétní video, HDR import, video bez zvuku a upravené titulky projdou testem renderu bez zničení originálů.

A16: Upgrade aplikace neztratí lokálně nesynchronizovaná média; migrace má testy a záložní postup.

## 16. Rozhodnutí pro první uživatelské kolo

**Q1 — Výsledný příběh:** převážně cestopis o místech, převážně osobní úvahy, nebo jejich kombinace? Výchozí doporučení: kombinace, kompletní deník plus film 20–30 minut po návratu. Délka je orientační a lze ji odložit.

**Q2 — Způsob mluvení:** krátké komentáře během chůze, delší večerní úvahy, nebo obojí? Výchozí doporučení: obojí, včetně možnosti přiřadit večerní komentář k dopolední fotografii. Doplňující praktická preference: má jít delší úvaha nahrávat se zamčenou obrazovkou v kapse?

**Q3 — Míra redakce a kontroly:** jen jazykové opravy, lehké uhlazení, nebo samostatný výrazně literárnější návrh? Chce Míla večer krátce prohlédnout návrh, nebo nechat soukromý deník vznikat automaticky? Výchozí doporučení: úvahy upravovat málo, souhrn více; rutinní návrhy ukládat automaticky a nejasnosti nabídnout ke kontrole. Nic nesdílet bez schválení.

**Q4 — Autoři, rodina a soukromí:** pouze Míla, Jana jako další autorka, nebo rodina jen jako čtenáři? Má rodina vybrané denní výsledky vidět už během pouti? Výchozí doporučení: první verze jeden autor, vše soukromé, rodinné sdílení pouze vybraných schválených výstupů.

**Q5 — Mapa:** pouze místa pořízení, nebo přesná souvislá stopa skutečně prošlé cesty? Výchozí doporučení: body pořízení; existující záznam trasy případně později importovat, místo okamžitého vývoje vlastního nepřetržitého sledování.

**Q6 — Hlas ve filmu:** použít autentické nahrávky z cesty, později namluvený vlastní komentář, nebo film převážně s titulky? Výchozí doporučení: autentický vlastní hlas a zvuk místa; možnost pozdějšího přenahrání nekvalitních úseků.

**Q7 — Externí AI:** smí audio a texty z Macu odejít k externímu poskytovateli kvůli přepisu a korektuře? Nebo musí vše zůstat na vlastních zařízeních? Výchozí doporučení jen při souhlasu: cloudové zpracování běžných komentářů a možnost některé záznamy zcela vyloučit. Alternativou je lokální či odložené zpracování s ověřením kvality.

**Q8 — Rozpočet:** je přijatelné případné roční členství Apple podle místní ceny (Apple uvádí 99 USD/rok) a oddělený malý rozpočet na AI? Jaký strop má AI pro tuto cestu dostat? Konkrétní částku nelze považovat za schválenou, dokud ji zadavatel nepotvrdí. [S13, S14]

## 17. Co zůstává otevřené, ale nemá se zatím přenášet na Mílu

Výběr konkrétního mikrofonního formátu, databázových knihoven, velikosti chunků, verzí Pythonu a Swiftu, modelu přepisu, podpisové cesty, detailu tokenů, FFmpeg filtrů a způsobu spouštění workeru. Tyto věci řeší technické prototypy a záznamy rozhodnutí.

Před uzavřením specifikace ověřit také praktickou dostupnost vývojového stroje a serveru, dobu platnosti instalace, obnovu po restartu, baterii při dlouhém nahrávání a množství dat z testovacího dne. Žádná z těchto vlastností nebyla v rámci této konverzace otestována na skutečných zařízeních.

## 18. Zdrojové podklady

Ověřeno webem 13. září 2026. Zdroje dokládají uvedené vlastnosti platforem, nikoli funkčnost budoucí aplikace. Podrobná pravidla poskytovatelů znovu ověřit při implementaci.

[S1] Apple — URLSessionConfiguration.background(withIdentifier:), chování při nuceném ukončení: `https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background(withidentifier:)`

[S2] Apple — Developer account overview, omezení Personal Team a sedmidenní profily: `https://developer.apple.com/help/account/basics/about-your-developer-account`

[S3] Tailscale — Serve, soukromé zpřístupnění, pravidla přístupu a localhost: `https://tailscale.com/docs/features/tailscale-serve`

[S4] Tailscale — VPN On Demand: `https://tailscale.com/docs/features/client/ios-vpn-on-demand`

[S5] Apple — Xcode SDKs and system requirements: `https://developer.apple.com/xcode/system-requirements`

[S6] OpenAI — File transcription, formáty a velikosti vstupů: `https://developers.openai.com/api/docs/guides/speech-to-text`

[S7] OpenAI — Data controls in the OpenAI platform: `https://developers.openai.com/api/docs/guides/your-data`

[S8] OpenAI — Structured model outputs, včetně omezení obsahové správnosti: `https://developers.openai.com/api/docs/guides/structured-outputs`

[S9] OpenAI — Custom instructions with AGENTS.md: `https://developers.openai.com/codex/guides/agents-md/`

[S10] FastAPI — Background Tasks: `https://fastapi.tiangolo.com/tutorial/background-tasks/`

[S11] SQLite — Online Backup API: `https://sqlite.org/backup.html`

[S12] FFmpeg — Filters Documentation: `https://ffmpeg.org/ffmpeg-filters.html`

[S13] Apple — Developer Program enrollment and membership price: `https://developer.apple.com/programs/enroll/`

[S14] OpenAI — Managing billing for ChatGPT and the API platform: `https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform`

---

**Další revize:** po odpovědích na Q1–Q8 změnit tento dokument na schválený produktový návrh; teprve potom vytvořit závazné technické kontrakty a jednotlivá zadání pro Codex. Doporučení v tomto dokumentu nejsou automaticky souhlasem zadavatele.
