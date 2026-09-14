# Camino — aktualizovaný návrh v0.3

**Datum:** 13. září 2026  
**Zadavatel a jediný autor obsahu:** Míla  
**Zpracovala:** Samantha  
**Stav:** zapracovaná potvrzená uživatelská rozhodnutí; technický návrh k postupnému ověření a rozdělení do úkolů pro Codex. Nejde o hotovou aplikaci ani o potvrzení funkčnosti na zařízení.  
**Předchozí verze:** `CAMINO_pracovni_navrh_v0.2-DRAFT.md` zůstává beze změny. Pro další práci má přednost tato v0.3.

> Během pouti prožívat a zaznamenávat. Archivace, přepis a soukromý deník mají pracovat automaticky. Film se dokončuje po návratu, nikoli každý večer na ubytování.

**Jak dokument číst:** oddíl 1 uvádí rozhodnutí potvrzená Mílou. Konkrétní výchozí nastavení a technická řešení v dalších oddílech jsou návrhová rozhodnutí Samanthy; jejich realizovatelnost prověří Codex a zkoušky na skutečném telefonu. Požadavky na bezpečnost a akceptační scénáře nejsou tvrzením, že už byly splněny. Číselné parametry prototypu nejsou naměřené výsledky. Otevřený zůstává zejména finanční strop AI, nikoli souhlas se zpracováním obsahu.


## 1. Potvrzená uživatelská rozhodnutí

| ID | Rozhodnutí | Dopad do návrhu |
|---|---|---|
| U01 | Výsledkem je kombinace cestopisu a osobního příběhu. Orientační stopáž 20–30 minut, podle materiálu. | Podrobný deník zůstává vedle filmu. Žádné natahování filmu na pevnou délku. |
| U02 | Krátké komentáře i delší samostatné úvahy. Žádoucí je nahrávání se zamčeným telefonem v kapse. | Dvě srozumitelná tlačítka nad společným audio základem; raný test zámku, mikrofonu a přerušení. |
| U03 | U úvah minimální zásahy a zachování autorova vyjadřování. Automaticky čistit gramatiku, překlepy a interpunkci; souhrn může být více uhlazený. | Oddělené redakční profily; neměnné původní audio a samostatné textové revize. |
| U04 | Žádná povinná večerní redakce ani střih. Jednoduchá možnost opravy má zůstat. | Soukromé zpracování nečeká na schválení. Nejasnosti nesmějí vytvořit povinný seznam úkolů. |
| U05 | Autorem je pouze Míla. Základ je soukromý archiv. Rodině lze během pouti posílat vybrané denní zápisy, bude-li to jednoduché. | Žádný víceuživatelský systém v první verzi. Sdílení jako malý volitelný export. |
| U06 | Povinná volba „Jen pro mě — nezahrnovat do sdíleného deníku ani filmu“. | Omezení se týká originálu, přepisu i všech odvozených výstupů; zahrnuje i finální film pro vlastní použití. |
| U07 | Aplikace ukládá jen polohu jednotlivých záznamů. Celou trasu měří hodinky. | Bez nepřetržitého GPS sledování a bez vlastní hodinkové aplikace. Pozdější import podle skutečného exportu hodinek. |
| U08 | Autentický hlas z cesty a zvuk prostředí; nekvalitní komentář lze později namluvit znovu. Bez umělého hlasu. | Původní zvuk je archivním zdrojem. Případné nové namluvení se označí jako pozdější nahrávka. |
| U09 | Externí AI smí zpracovat jakýkoli autorův komentář, text i osobní úvahu. | Také „Jen pro mě“ se může přepisovat a jazykově upravovat externím API. Soukromí vůči rodině a filmu není zákaz cloudového zpracování. |
| U10 | Případný Apple Developer poplatek 99 USD/rok je přijatelný, bude-li potřeba. Podrobné vysvětlení má přijít později. | Nativní aplikace zůstává preferovanou cestou. Nejprve ověřit vybavení a instalaci, nic automaticky nekupovat. |
| U11 | Finanční strop AI nebyl určen. | Nevymýšlet schválenou částku. Vývoj s mocky; před zapnutím placeného provozu nastavit limit a ověřit cenu pilotu. |

Dosavadní kontext uvádí iPhone 14 a MacBook Pro Intel s macOS Sequoia 15.7.7. Není potvrzeno, že tento MacBook je zamýšleným serverem v ČR. Přesná verze iOS, skutečný server, dostupné disky, zálohy a kompatibilita vývojových nástrojů patří do technického auditu, nikoli do nového produktového dotazníku. Model hodinek a jejich exportní možnosti zatím nejsou doloženy; jejich zjištění neblokuje první verzi.

Aktuální souhlas s externí AI nahrazuje starší podmíněnou variantu z v0.2. Povinné tlačítko „Bez externí AI“ se nyní nezavádí. Globální pozastavení AI kvůli provozu či rozpočtu zůstává.

## 2. Hlavní změny proti v0.2

Dřívější Q1–Q8 jsou uzavřené produktově s výjimkou konkrétního stropu AI. Večerní kontrola se mění z doporučeného kroku na čistě nepovinnou možnost. Rodinný web a automatické denní filmy nejsou součástí nutného předodjezdového rozsahu.

Zavádíme dva nezávislé významy: **souhlas s AI zpracováním** a **způsobilost pro sdílení či film**. Míla schválil první pro všechny své záznamy; „Jen pro mě“ omezuje druhý. Rodinný text se nesmí vyrábět z kompletního osobního souhrnu, protože do něj již mohly proniknout soukromé úvahy.

U hlasu je výslovný požadavek na pokračování již spuštěného záznamu po uzamčení telefonu. Není to požadavek na nepřetržitý poslech, samovolné spuštění mikrofonu, záznam hovoru ani automatický restart nahrávání po havárii. Apple podporuje vhodně nastavený audio režim se zámkem obrazovky; konkrétní chování bude nutné otestovat. [S15]

U trasy se vývoj vlastního průběžného záznamu vypouští: zdrojem bude případně záznam hodinek. U instalace odpadá otázka obecné přijatelnosti ročního poplatku, nikoli povinnost ověřit proveditelnost a platnost podpisu.

Z původního návrhu zůstávají bezpečnostní základy: offline originály; přenos s ověřením; další nezávislá záloha; neměnné zdroje; verzované odvozené texty; obnova po chybách; oddělení aplikace, AI a střihu.

## 3. Cíl a rozsah první verze

**Cíl:** zaznamenat situaci několika dotyky a bez další povinné práce získat dohledatelný originál, deníkový záznam a podklad pro pozdější film.

### 3.1 Nutné před první poutí

Nativní iPhone aplikace s fotografií, videem, komentářem a úvahou; offline uložení; import z knihovny; přiřazení ke dni a Momentu; zámek „Jen pro mě“; bezpečné delší audio včetně zamčené obrazovky po ověření; fronta přenosu přes Tailscale; ověření příjmu; druhá záloha a zkouška obnovy; AI přepis a střídmá korektura; automatický soukromý deník; nouzový export bez serveru.

Nedostupná AI nebrání záznamu ani přenosu. Nedostupný Mac nebrání používání telefonu. Chyba deníku nesmí ohrozit média. Při problému mají přednost uložená data a srozumitelný stav před hezkým rozhraním.

### 3.2 Malé volitelné rozšíření během pouti

Výběr běžných záznamů pro rodinu, krátký text a několik exportovaných fotografií přes systémové sdílení. Zařadit až po testech soukromí. Když funkce nebude spolehlivě dokončená, pouť proběhne bez ní a soukromý archiv není dotčen.

### 3.3 Po návratu

Import trasy z hodinek; filmová časová osa a návrh střihu; jednoduché titulky a mapa; možnost pozdějšího komentáře; render výsledného dokumentu. Základní média a vazby pro tyto funkce se ukládají už od začátku.

### 3.4 Mimo první rozsah

Veřejný web, rodinné účty, spoluautorství, aplikace na hodinky, živá poloha, každodenní povinný film, automatická vizuální analýza všech videí, generované záběry, klonování hlasu, sociální síť, komplexní videoeditor. Nezavádět je jen proto, že by to technicky bylo možné.

## 4. Ovládání telefonu

### 4.1 Hlavní obrazovka

Čtyři velká tlačítka: **Foto**, **Video**, **Komentář**, **Úvaha**. Dole pouze **Dnes** a **Stav uložení / synchronizace**. Drobné doplňky: hvězdička důležitosti, označení okamžiku a nabídka importu. Ovládání pro jednu ruku, velký text, dobrý kontrast a dostatečně velké aktivní plochy; žádné povinné pojmenovávání záznamu.

Komentář popisuje situaci a může patřit k médiu. Úvaha je osobní vyprávění a má přísnější pravidla zachování stylu. Krátký či dlouhý záznam může být kterýkoli z obou typů; samotná délka nic nepřeklasifikuje.

Navržené výchozí nastavení pro všechny typy je **Do deníku**: stále soukromé, ale způsobilé k pozdějšímu filmovému výběru. Přepínač **Jen pro mě** je na obrazovce záznamu a v detailu, s trvale viditelným stavem. Žádná z variant sama nic nepublikuje. Přepnutí na soukromé nesmí vyvolat potvrzovací překážku; u již odeslaných výstupů se následně vysvětlí, že je nelze vzít zpět.

### 4.2 Fotografie a videa

Otevřít fotoaparát jedním klepnutím, pořídit záběr, uložit. Nepovinná nabídka „Přidat komentář“ nezastaví další fotografování. Nový samostatný záběr je výchozím Momentem; další soubory lze připojit výslovnou volbou. Neprovádět skryté slučování událostí jen podle časové blízkosti.

Technické výchozí nastavení vlastního videa: 1080p, 30 snímků/s, SDR, k ověření poměru kvality a velikosti. Importované zdroje zachovat v původní kvalitě. Orientace na šířku je doporučená pro budoucí 16:9 film, nikoli povinná. Video na výšku nesmí být odmítnuté ani později bez kontroly agresivně oříznuté.

Cílem není kopie systémového Fotoaparátu. Pořídit lze i mimo naši aplikaci a později importovat. U importu zkontrolovat skutečnou dostupnost celého souboru, nikoli jen náhledu; chybějící data například při offline dostupnosti knihovny zůstanou viditelně čekající. Zachovat čas pořízení a dostupná původní metadata.

### 4.3 Komentář a úvaha

Klepnutí spustí nahrávání po udělení oprávnění, další jej dokončí. Úvodní oprávnění k mikrofonu vyřešit při přípravě před cestou, ne až u prvního důležitého zážitku. Během záznamu zobrazit čas, indikaci vstupu a skutečně vybraný mikrofon. Po uložení žádné povinné přehrávání ani schvalování přepisu.

Samostatná úvaha vzniká jako vlastní Moment. Volba z detailu existujícího média ji může propojit s dřívější událostí, ale čas nahrání zůstane oddělený. Význam „Jen pro mě“ se řídí oddílem 11; obyčejná fotografie nemá být nechtěně sdílena se soukromým dodatkem.

Pauza a pokračování jsou vhodný doplněk, nikoli důvod odkládat bezpečné spuštění a ukončení. Psané doplnění textu bude v detailu, ne jako páté hlavní tlačítko. Zadaný text se ukládá také před AI opravou.

### 4.4 Zamčená obrazovka a mikrofon

Požadovaný scénář: v popředí spustit úvahu → ověřit aktivní mikrofon → uzamknout telefon → pokračovat v nahrávání → odemknout a ukončit. Nahrávání v patřičném audio režimu se zámkem platforma podporuje. [S15] Spuštění či ovládání tlačítkem na libovolných sluchátkách ani spuštění z uzamčené obrazovky není součástí závazného prvního rozsahu.

Sluchátka nejsou podmínkou samotného nahrávání. Pro telefon v kapse navrhuji ověřený externí mikrofon, například mikrofon v kompatibilních sluchátkách, aby vstup nezůstával zakrytý. Samotná sluchátka bez mikrofonu tuto potřebu neřeší. Nevybírat ani nekupovat model bez praktického srovnání dosavadního vybavení s vestavěným mikrofonem. Bluetooth nepovažovat automaticky za lepší kvalitu; podporu vstupu a výslednou srozumitelnost ověřit.

Při příchozím hovoru, ztrátě vstupu nebo systémovém přerušení bezpečně uzavřít zachovanou část, označit přerušení a podle možností systému upozornit. Po ztrátě externího mikrofonu nepokračovat bez oznámení na mikrofon telefonu schovaného v kapse. Obnovení nahrávání po hovoru nebo restartu vyžaduje vědomý úkon uživatele; žádný tajný restart mikrofonu. Události přerušení a změny zvukové cesty jsou podporované systémové mechanismy. [S16, S17]

V první verzi nenatáčet současně samostatnou úvahu a video. Při přechodu nabídnout jednoduché „Uložit úvahu a spustit video“. U souběhu s fotografováním postupovat stejně konzervativně, dokud nebude otestováno, že se audio nepřerušuje.

### 4.5 Dlouhý záznam a obnova

Prototyp ověří průběžně uzavírané navazující zvukové segmenty v rámci jedné nahrávky. Návrhový interval 60–120 sekund je k měření; nezasahovat do řeči slyšitelnými mezerami. Originálem je v tomto režimu soubor původních segmentů s manifestem, spojená souvislá nahrávka je odvozená kopie. Neoznačovat překódované spojení za jediný originál.

Po pádu musí zůstat dokončené segmenty. U poslední rozpracované části neslibovat nulovou ztrátu; obnovit, co jde, a přiznat rozsah neúplnosti. Testy zahrnou i kompatibilitu ochrany souborů a přístupových údajů se zámkem obrazovky; nelze řešit zápis při zamčení vypnutím zabezpečení celého telefonu.

Cílová zkouška: 30 minut řeči se zamčeným telefonem, včetně ukončení a přehrání. Dále samostatně hovor, odpojení mikrofonu, restart aplikace, nedostatek místa a záznam bez sítě. Délka je testovací požadavek, nikoli tvrzení o ověřené výdrži.

### 4.6 Dnešní den a tichý provoz

Časová osa fotografií, videí, komentářů a úvah. V detailu lze přehrát originál, přečíst upravený text, provést malou opravu, změnit přiřazení či soukromí. Večer se nevyžaduje otevření této obrazovky.

Běžné dokončení přepisu a každá stylistická nejasnost nevytváří upozornění. Viditelně a prioritně řešit neuložený záznam, zastavený mikrofon, kriticky málo místa a dlouhodobě neodeslané originály. Přesnou četnost upozornění doladit při terénní zkoušce; nezahlcovat opakovanými hláškami téhož problému.

„Označit okamžik“ vytvoří prázdný Moment s časem a případnou polohou. Hvězdička na existujícím Momentu označuje důležitost. Ani jedno není žádost o publikování.

## 5. Datový model a vlastnictví dat

### 5.1 Objekty

**Trip:** cesta, stabilní ID, název, jazyk, výchozí pravidla přenosu a AI. Není napevno svázaná s jedním rokem ani pevnými daty odjezdu.

**JourneyDay:** denní kapitola, místní datum, pořadí, případný potvrzený název etapy. Může být příjezdový, pěší, odpočinkový či prázdný den; nezakódovat předpoklad, že každý den znamená další etapu.

**Moment:** situace s ID vytvořeným offline, časem události, přiřazenou kapitolou, typem, důležitostí, příznakem `owner_only` a nepovinnou vazbou na jiný Moment. Metadata mají číslo revize. Jeden autor, jedno hlavní mobilní zařízení.

**Asset:** konkrétní původní soubor, ID, typ, velikost, SHA-256, původní čas, technická metadata a stav místních/serverových kopií. Moment může obsahovat více Assetů nebo žádný. Nahrávka se segmenty nese pořadí, časové offsety a informaci o přerušení.

**TextRevision:** vstupní psaný text, surový strojový přepis, jazyková úprava, lidská revize nebo odvozený scénář. Uchovává zdrojové ID a časové úseky, rodičovskou revizi, autora změny, model/verzi instrukcí a údaj o lidské kontrole. Audio je autoritativní zdroj, přepis není zaručeně doslovný.

**ProcessingJob:** trvalá fronta s opakováním a verzí operace. **BackupReceipt:** doklad ověřené další kopie. **ExportRevision:** konkrétní výstup včetně přesných zdrojových revizí, publika a kontroly soukromí. Budoucí **TrackImport** a **FilmTimeline** se doplní až v příslušném úkolu; od začátku nebudovat zbytečné prázdné moduly.

### 5.2 Čas, den a poloha

Uchovat UTC, lokální datum a časový offset při pořízení, dostupný identifikátor časového pásma a odděleně čas přijetí serverem. Denní kapitolu neodvozovat od hodin Macu v ČR. Dodatečný import ani upload po několika dnech nezmění den události.

Výchozí přiřazení podle místního data záznamu, s možností později jednoduše změnit den kapitoly bez přepisování originálních metadat. Úvaha přes půlnoc patří výchozím pravidlem k dni začátku; její koncový čas se zachová. Později namluvená vzpomínka má vlastní čas i vazbu na starší událost.

Poloha je jednorázový údaj s časem měření a přesností. Je-li nedostupná nebo zastaralá, média se přesto pořídí. První verze nepotřebuje trvalé sledování ani oprávnění k souvislé poloze na pozadí. Název místa a etapy musí mít známý původ; AI návrh není potvrzený zeměpisný fakt.

Body médií nejsou skutečně prošlá GPS stopa a nedávají spolehlivou kilometráž. Hodinky jsou samostatný zdroj, nikoli již integrovaná součást aplikace. Pozdější import může využít například GPX, pokud ho skutečný záznam poskytuje. Zachovat původ exportu, časové pásmo a mezery ve stopě; žádné domyšlené úseky označené jako měřené.

### 5.3 Neměnnost a konflikty

Originální soubory neměnit. Úpravy textu, soukromí a přiřazení dne jsou revize; nepřenášet kvůli nim znovu video. Lidskou úpravu nesmí nová AI generace přepsat. Konflikt webu a telefonu uchová obě verze. Nevyřešený konflikt textu blokuje pouze jeho nové zveřejnění, nikoli záznam dalších médií.

U rozporu o soukromí použít do vyřešení přísnější variantu. Neznámá viditelnost nesmí umožnit export. V jedné jednoduché první verzi se zámek vztahuje na celý Moment včetně příloh a textu. Soukromý dovětek k běžné fotografii lze vytvořit jako samostatný zamčený Moment s vazbou; rodinný export tuto vazbu nesmí následovat ani prozradit existenci skrytého dovětku.

### 5.4 Tři oddělené významy

`owner_only = true` zakazuje sdílené výstupy a všechny filmy, dokud autor omezení výslovně nezmění. `owner_only = false` pouze dovoluje budoucí výběr; neznamená publikaci. Souhlas s externím AI je pro tuto cestu potvrzený i u `owner_only` záznamů. Skutečné odeslání rodině je samostatná vědomá akce nad konkrétní verzí exportu.

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

Uživatel dostane „Synchronizovat nyní“ s počtem zbývajících záznamů a bytů. Automatické přenosy mají být běžný režim. Krátké otevření aplikace při nabíjení může být nutné jako záloha automatizace; nikdy to není povinná redakce nebo střih. Přesné chování na pozadí musí ověřit terénní test. Zvlášť testovat hotelovou síť vyžadující přihlášení, uzamčený telefon a přechod mezi Wi-Fi a mobilní sítí.

### 6.5 Pravidla datového přenosu

Výchozí konzervativní návrh: originální video a velké dávky pouze Wi-Fi; metadata a malé zvukové záznamy mohou používat mobilní data po výslovném nastavení. Fotografie nejsou automaticky „malé“; i zde je vhodný denní limit. Jednorázové povolení mobilního přenosu musí ukázat objem a platit jen pro zvolenou dávku.

Odhad úložiště určit testovacím dnem: součet skutečně naměřených mediálních velikostí × délka cesty plus rezerva a pracovní prostor. Nenahrazovat měření paušálním slibem, že určitý počet GB stačí. Před cestou ověřit i příjem z jiné sítě, nikoli pouze doma přes Wi-Fi.

### 6.6 Priority a změna soukromí

Nejvyšší prioritu mají změny soukromí a malá metadata; poté dokončené audio, fotografie a videa. Přenos se nesmí snažit dohnat velká videa na úkor probíhajícího nahrávání nebo kritické baterie. Chunkování se plánuje po omezených dávkách; iOS nemusí aplikaci vždy probudit pro naplánování další dávky, proto se nevyvozuje zaručený neomezený přenos ze samotné existence background URLSession.

Před novým sdíleným exportem ověřit, že server zná aktuální soukromí vybraných zdrojů a telefon nemá jeho neodeslanou změnu. Jinak export podržet. Offline nastavený zámek se nemůže magicky projevit na nedosažitelném serveru; rozhraní tento stav nesmí skrýt. Žádné průběžné automatické publikování z domácího serveru.

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

### 7.6 Provoz bez každovečerní správy

Služba a worker mají startovat spravovaně, obnovovat trvalou frontu a zobrazovat stav bez hledání v terminálu. Před cestou prakticky ověřit nepřerušené napájení, neuspávání během služby a přístup po restartu v reálném nastavení šifrování. Domácí server se nesmí automaticky ztotožnit s vývojovým notebookem.

Večer uživatel nejvýše připojí telefon k napájení a dostupné síti, případně otevře synchronizaci. Serverové úkoly nečekají na tlačítko „uzavřít den“. Kdyby server vypadl, pokračuje se v záznamu a fronta zůstává v telefonu. Pro dlouhý výpadek se použije předem otestovaný nouzový export na skutečně dostupné úložiště; samotný export do další složky téhož telefonu není ochrana proti ztrátě zařízení.

## 8. AI přepis, jazyková úprava a automatický deník

### 8.1 Cesta zpracování

Nejdříve bezpečně uložit originál a ověřit přenos. Potom vytvořit pracovní audio, přepsat řeč a uložit surový přepis, provést jazykovou korekturu a připojit výsledek ke dni. Zálohování probíhá nezávisle; text nevytváří falešný doklad zálohy.

Vstupem jsou v první verzi samostatně nahrané komentáře a úvahy i ručně zadané texty. Automaticky nepřepisovat veškerou řeč náhodně zachycenou v každém videu. Video lze později výslovně označit „obsahuje můj komentář“ a jeho pracovní audio zpracovat, ale tento doplněk nemá blokovat hlavní audio cestu.

Pro OpenAI file transcription dokumentace uvádí podporu M4A a limit 25 MB na soubor. Pracovní segmentaci pro API provádět podle aktuálního endpointu; tato segmentace je jiná než záchranné segmenty při pořizování audia. Zachovat časové offsety a nenarušit originál. Konkrétní model vybrat testem české řeči a aktuálních cen, nikoli napevno podle názvu z prvního návrhu. [S6]

### 8.2 Dva redakční profily

**Komentář / úvaha:** automaticky opravit pravopis, gramatiku, interpunkci a zjevné překlepy. Zjevnou chybu rozpoznání opravit jen s oporou ve zdroji; nejasnost označit. U úvah nepřidávat stylistickou pompéznost, neměnit slovní zásobu na knižní, zachovat smysluplné opakování a emocionální odstín. Rozlišovat zjevnou chybu od záměrně hovorového vyjadřování.

Příklad: „no dneska sme šli dlouho ale bylo to dobrý“ → „No, dneska jsme šli dlouho, ale bylo to dobrý.“ Opraven je čitelný zápis; autorův hlas není přepsán na úřední češtinu. Příklad je pravidlo stylu, nikoli povinný tvar pro každý záznam.

**Denní souhrn:** lze uspořádat události, spojit opakování a vytvořit plynulý krátký text. Souhrn musí být označen jako sestavený automaticky ze záznamů, nikoli jako doslovný citát autora. Zachovat stejný faktický obsah a nejistotu.

Nesmí přibýt počasí, kilometráž, historie kostela, osoba, motivace ani pocit, který není doložen. Pozor zejména na negaci, jména, čísla, časové vztahy a záměnu „já/my“. Ticho či vítr nevydávat za řeč. Věty v nahrávkách jsou data, ne instrukce ke změně pravidel nebo spuštění nástrojů.

### 8.3 Bez povinného schvalování

Běžná jazyková úprava se automaticky uloží jako aktuální soukromá verze. Originál, surový přepis a dřívější revize zůstávají. Text může nést tiché označení nejasných úseků; uživatel je nemusí večer řešit. Ani příznak nejasnosti nesmí zablokovat upload nebo vytvoření galerie.

Uživatel může otevřít detail a text upravit. Ruční revize se stává chráněnou aktuální verzí. Pozdější automatický výsledek se uloží vedle, nikoli přes ni. Upravení jediného jména nemá spustit znovu přepis celého dne.

AI má vracet validované strukturované údaje a odkazy na zdroje. Validace formátu není záruka pravdivosti; tuto mez uvádí i dokumentace Structured Outputs. [S8] Ke kvalitě patří česká testovací sada proti audiu, ne jen kontrola gramatiky výstupu.

### 8.4 Kdy vzniká denní kapitola

Galerie a časová osa vznikají průběžně bez placené AI. Přepisy se přidávají po dokončení zpracování. Textový souhrn se sestavuje z dostupných vstupů dávkově, nikoli po každém přenosovém chunku nebo otevření stránky.

Technický výchozí návrh: po ustálení nové dávky textových vstupů použít odklad 15 minut a nejvýše jednu automatickou regeneraci souhrnu stejného dne za hodinu. Hodnoty jsou ladicí parametry. Souhrn ukládá hash seznamu vstupních revizí; pokud se změnil pouze náhled nebo stav kopie, nový AI požadavek se neprovádí. Náročné renderování se do této fronty nezařazuje během běžného přepisu.

Pozdní upload jde do správné historické kapitoly a může vytvořit novou soukromou revizi. Již odeslaný rodinný výběr se sám nezmění a znovu se neodešle. Manuálně upravený souhrn se nepřepíše.

### 8.5 AI a soukromí

Míla schválil externí zpracování i osobních úvah. Do API proto lze poslat jejich audio a potřebný text pro přepis a korekturu. Neznamená to automatické povolení dalších funkcí, například odesílání veškerého videa do vizuálního AI modelu.

Klíč API je pouze na serveru. Posílat jen potřebná data; pro korekturu zpravidla není potřebná přesná GPS. Použít bezstavové požadavky, kde je to vhodné, a nastavit `store=false`, pokud ho endpoint podporuje. Nezakládat pro tento účel zbytečné trvalé cloudové konverzace ani index celého deníku.

OpenAI uvádí, že API data standardně nepoužívá k trénování bez zapojení zákazníka do sdílení; režimy uchování se ale liší podle endpointu a nastavení. `store=false` není automaticky Zero Data Retention. Nelze tvrdit, že všechna data zůstávají výhradně na Macu. [S7]

Soukromý deník může zahrnout „Jen pro mě“. Vstup rodinného výběru a filmu se musí sestavit znovu jen z povolených zdrojů, bez těchto úvah a bez celkového osobního souhrnu. Oddělit kontext, cache i seznam použitých zdrojů pro jednotlivé účely; nespoléhat na samotnou instrukci „tohle neprozraď“.

### 8.6 Cena a chyby

Konkrétní limit AI nebyl schválen. V čisté vývojové konfiguraci běží mock. Skutečný provoz vyžaduje vědomé nastavení klíče, rozpočtu a aktuální cenové konfigurace. Odhad pilotu nejdříve založit na délce ukázkového audia a reálném množství textu.

Před požadavkem evidovat odhadovanou rezervaci nákladu, po něm dostupnou spotřebu. U prvního nasazení omezená souběžnost, omezené opakování a rozlišení chyby od neznámého výsledku po timeoutu. Lokální limit není záruka přesné částky vyúčtované poskytovatelem. Po dosažení limitu čeká jen AI; nahrávání, záloha a galerie pokračují.

## 9. Podoba denního deníku a sdíleného výběru

### 9.1 Soukromá denní kapitola

Základ: **den a datum**, případný známý název etapy, úvodní fotografie, chronologický přehled, krátký automatický souhrn, komentáře u situací, samostatné úvahy, galerie a odkazy na původní audio. Zamčené položky vidí pouze vlastník a jsou v jeho přehledu označené.

Nejsou povinná pole pro počasí, kilometráž, ubytování, náladu nebo nadpis každé fotografie. Chybějící údaje se vynechají. Dokud neexistuje import z hodinek, nenazývat spojnici bodů fotografování skutečnou trasou. Prázdný den nemusí mít uměle vygenerovaný odstavec.

Návrhová délka běžného souhrnu je 100–200 slov, pouze když vstupy odpovídají této délce. Krátký den může mít dvě věty. Úvahy se nezkracují jen kvůli jednotné šabloně. Volitelná titulní fotografie se výchozím pravidlem vezme z označených snímků, jinak z prvního vhodného snímku; automatická estetická AI analýza není nutná.

Souhrn uvádí čas sestavení a dostupnost vstupů; přenos může být ještě neúplný. Nepředstírat, že server ví o médiích, která z telefonu dosud nedostal.

### 9.2 Jednoduchá zpráva rodině

Doplněk po dokončení jádra: **Dnes → Poslat výběr**. Uživatel zvolí povolené fotografie a záznamy; lze předvybrat běžné hvězdičkou označené položky, nikdy zamčené. Z povolených vstupů vznikne krátký text a exportované fotografie, k náhledu a předání přes systémové sdílení. Volba cílové aplikace a adresáta je vědomý úkon uživatele. Aplikace sama neodesílá emaily ani zprávy na pozadí.

Žádný přístup rodiny na domácí server, instalace Tailscale u čtenářů, nové účty ani veřejná URL nejsou pro tuto první variantu potřeba. Předává se kopie textu a médií, nikoli přihlašovací odkaz. Přesné chování více položek v cílové komunikační aplikaci se ověří; neslibovat automaticky dokonalý layout ve všech aplikacích.

Podoba může být 3–5 vybraných fotografií a krátký odstavec; to je návrhový výchozí rozsah, ne povinná denní činnost. Při nedostatku vstupů sdílet kratší výběr. Pokud uživatel nic nestiskne, nic se nepublikuje. Chyba této funkce neohrozí soukromý deník.

### 9.3 Dlouhodobá čitelnost

Soukromý archiv exportovat jako HTML a Markdown s JSON manifestem a médii nebo přenositelnými relativními cestami. Nouzový export do běžně čitelného balíčku musí být možný z telefonu bez Macu. Export soukromého archivu je jasně jiná operace než „Poslat výběr“ a nesmí omylem otevřít rodinné sdílení.

Rodinné kopie zbavit přesné GPS a jiných nepotřebných metadat i v souborech, ne pouze ve stránce. Originály zůstávají nedotčené. Již odeslané kopie nejde technicky spolehlivě odvolat; pozdější zámek chrání budoucí exporty, ne cizí uložené kopie.

## 10. Film

### 10.1 Potvrzený směr výstupu

Osobní cestopis propojující místa a úvahy, přibližně 20–30 minut po návratu. Krátká verze pro rodinu může vzniknout ze stejného projektu později. Denní automatické filmy nejsou povinnou funkcí před odjezdem; jednodušší je denní stránka a případně kontaktní přehled záběrů.

Míla schválil kombinaci míst a osobního příběhu i orientační délku. Program nesmí uměle natahovat film jen kvůli stopáži. Jednotlivé dny nemusí dostat stejný čas: důležitý okamžik může být delší, klidný den kratší. Příjezd, průběh pouti a závěr jsou přirozená možnost členění, nikoli povinný scénář s vymyšlenými zážitky.

### 10.2 Materiál, zvuk a střih

Hvězdičky, komentáře, chronologie a uživatelské volby jsou první zdroj výběru. AI může navrhnout zajímavé úseky řeči; sama bez analýzy obrazu neví, co je ve videu. Automatická obrazová analýza velkého množství videí je samostatná pozdější funkce s náklady a soukromím.

Střihová časová osa ukládá ID zdroje, přesný počátek a konec úseku, délku, titulky, zvukové úrovně, případné hudební podklady a původ každé textové věty. Ručně uzamčené záběry se při dalším návrhu nemění.

Původní hlas je preferovaný, ale zvuk ve větru nemusí být použitelný. Deník přesto vznikne; komentář lze později namluvit znovu. Žádné nevyžádané klonování hlasu ani automatické přepisování vyřčeného obsahu syntetickým hlasem.

Hudba: v první verzi žádná; později pouze výslovně dodané či odpovídajícím způsobem licencované podklady s evidencí oprávnění. Nezabudovávat stahování komerčních skladeb do aplikace.

### 10.3 Render a export

Render podle validované časové osy provádí FFmpeg, nikoli jazykový model. FFmpeg nabízí potřebné filtry pro měřítko, skládání, titulky a zvukové úpravy; dostupnost konkrétních filtrů ověřit u instalované sestavy. [S12]

Pracovní kopie normalizují orientaci, rozměry, proměnlivou snímkovou frekvenci a případné HDR. Originál se nepřepisuje. Testy musí obsahovat výškové video, video bez zvuku, delší hlas, HEIC fotografii a importovaný HDR záznam.

Předběžný finální výstup: MP4 1080p 16:9 a samostatná časová osa v JSON; případný standardní výměnný formát pro střihový program řešit až podle ověřené kompatibility. Neslibovat univerzální otevření projektu ve všech editorech.

### 10.4 Závazné hranice autenticity

Položka „Jen pro mě“ nesmí být ve filmu ani jako zvuk v pozadí, titulky, citát, název kapitoly, náhled nebo parafráze. Tato ochrana platí i pro automatický pracovní sestřih a film určený jen vlastníkovi. K zařazení by autor musel omezení výslovně změnit.

Původní komentář lze po návratu namluvit znovu, ale nový záznam má vlastní datum a vazbu na starý; originál se nemaže. Čtenářská korektura není náhradou časově věrných titulků k původnímu hlasu. Jazykový model navrhuje sestřih pouze z dostupných zdrojů; samotný přepis mu nedává znalost obrazu videa.

Na cestě žádný povinný střih. Před odjezdem stačí ověřit, že exportované zdroje, jejich orientace a zvuk jsou použitelné pro budoucí zpracování. Hotový 20–30minutový render není podmínkou dokončení záznamové aplikace.

## 11. Soukromí, autorizace a kontrola exportů

### 11.1 Soukromé úložiště

Základ je privátní aplikace jednoho vlastníka, žádné veřejné adresy. Tailscale Serve zpřístupňuje lokální službu v tailnetu; nepoužívat veřejné Funnel. Backend naslouchá jen na localhostu, síťová pravidla omezují přístup na potřebná zařízení. [S3]

Síťový přístup doplnit odvolatelným oprávněním aplikace. Token uložit na telefonu v Keychain, ne v URL nebo logu; klíč AI nikdy nedávat do telefonu. Webové rozhraní vlastníka chránit odpovídající autorizací a proti nechtěným změnovým požadavkům. Testovací data oddělit od reálného archivu.

Při nahrávání souborů nepoužívat klientský název jako cestu. Kontrolovat velikosti, povolené formáty a identifikátory, streamovat data a neočekávaný vstup nepředávat příkazovému shellu. Logy nesmějí obsahovat tokeny, přesnou GPS, přepisy ani osobní texty. Veřejné chybové hlášky nemají vracet interní cesty nebo stack trace.

### 11.2 „Jen pro mě“ je pravidlo dat, nikoli vzhledu

Pro rodinný export i film nejdříve sestavit explicitně povolený seznam zdrojů. Nezačínat celým osobním deníkem a nespoléhat, že AI následně soukromé části správně vynechá. Zakázaný zdroj nesmí být vstupem ani pro generování titulku, hudebního pokynu, mapové poznámky, výběru citátu nebo názvu kapitoly.

Textová revize odvozená z více zdrojů zdědí přísnější omezení, pokud zahrne jediný zamčený zdroj. V praxi kompletní osobní denní souhrn neslouží jako vstup pro rodinný výběr ani film. Kontext požadavků a cache se pro tyto účely oddělují.

Změna běžného záznamu na „Jen pro mě“ zneplatní závislé exporty, náhledy a navržené střihy, které aplikace ještě kontroluje. Před předáním do systémového sdílení znovu prověřit aktuální seznam zdrojů a revize. Odeslaná kopie je mimo tuto kontrolu a neexistuje slib jejího odvolání.

### 11.3 Exportní test je podmínka, nikoli doplněk

Testy musí hledat únik v textu, názvu, příloze, zvuku, titulcích, metadatech, náhledu, cache i v odvozené parafrázi. Soukromý testovací údaj nesmí být v požadavku na generování rodinného souhrnu vůbec přítomen. Testovat také pozdní změnu zámku, soukromý dovětek k běžné fotografii a neodeslanou offline změnu soukromí.

Aplikace nekontroluje, zda se citlivá skutečnost nezávisle objevuje i v jiném běžném záznamu. Zámek je ochrana označených zdrojů a jejich odvozenin, nikoli vševědoucí anonymizace veškerého obsahu. Proto má skutečné sdílení náhled a vědomý krok uživatele.

### 11.4 Ztráta zařízení a obnova

Připravený postup odvolání telefonu a přístupového tokenu. Existující archiv zůstane na Macu a v záloze. Nesynchronizovaná média ze ztraceného telefonu aplikace zachránit nemůže. Neodinstalovávat aplikaci jako první řešení chyby, dokud není ověřen export jejích místních dat.

## 12. Instalace, vybavení a náklady

### 12.1 Technický audit je první brána

Před hlavním vývojem zjistit dostupný vývojový Mac, jeho macOS, Xcode, skutečný iOS, způsob připojení iPhonu a provoz domácího Mac serveru. Přítomnost Macu neznamená automaticky kompatibilitu všech aktuálních nástrojů. Apple publikuje tabulku podporovaných kombinací; starší Xcode může mít jiné požadavky než nejnovější vydání. [S5]

Nenutit koupi nového počítače, aktualizaci systému, veřejné publikování aplikace ani migraci zabezpečení bez doloženého důvodu. Audit může zachytit nedostupný údaj jako NEOVĚŘENO; Codex nesmí napsat, že zkouška na zařízení proběhla, když neměl zařízení k dispozici.

### 12.2 Apple Developer

Míla akceptoval případný roční poplatek. Apple uvádí 99 USD za členský rok, místní cena se zobrazí při registraci. Bezplatné profily Personal Team podle Apple expirují po sedmi dnech, a proto nejsou výchozím řešením pouti bez pravidelného obnovování instalace. [S2, S13]

Preferovaný směr je legitimně podepsaná nativní aplikace na vlastním registrovaném iPhonu. Konkrétní distribuci zvolit technicky, ověřit platnost přes celou cestu s rezervou a instalaci mimo připojený vývojový Mac. TestFlight ani App Store nejsou automaticky povinné. Před koupí členství ověřit, že zvolená cesta na dostupném vybavení funguje; tento dokument žádnou platbu neprovádí.

Podrobné vysvětlení důvodu poplatku je odložené podle Mílova přání; v návrhu zůstává jen technická návaznost a podmínka ověření.

### 12.3 AI

Souhlas se zpracováním obsahu je potvrzený, částka rozpočtu není. Vývoj s mocky nic neposílá poskytovateli. Před skutečným placeným pilotem se stanoví maximální výdaj; před poutí rozpočet provozu a chování po jeho vyčerpání. Neuvádět odhad nákladů jako garanci.

Předplatné ChatGPT a spotřeba API se účtují odděleně. [S14] Aplikace musí mít vlastní měření, omezené opakování a možnost zastavit pouze AI. Nezaměňovat upozornění poskytovatele na útratu s garantovanou blokací dalšího účtování.

### 12.4 Dosud nevyžadované výdaje

Není schválena koupě sluchátek, mikrofonu, disku ani dalšího počítače. Nejprve využít a otestovat existující vybavení. Nutné kapacity telefonu a serveru se určí měřením realistického testovacího dne, ne výmyslem přesného počtu GB.

## 13. Převod návrhu na práci Codexu

Tato revize uzavírá uživatelské volby, ale není příkaz „vyrob vše naráz“. Doprovodný `CAMINO_plan_Codex_v0.3.md` rozděluje práci na ověřitelné kroky. Úplný OpenAPI kontrakt a přesné závislosti se mají stabilizovat po prvních zkouškách, ne vymyslet bez zařízení.

Pro repozitář následně připravit `AGENTS.md`, produktovou specifikaci, záznamy rozhodnutí, technické kontrakty, testy a provozní návod. Codex podporuje čtení `AGENTS.md` jako projektových instrukcí. [S9]

Každý pracovní úkol musí mít cíl, povolený rozsah, vstupy, výslovné ne-cíle a akceptační scénáře. Při předání uvést změněné soubory, skutečně spuštěné testy, výsledek a manuální zkoušky, které ještě neproběhly. Čistě softwarový test nenahrazuje uzamčený skutečný iPhone, příchozí hovor ani výpadek domácí sítě.

Společná pravidla: nemazat originály; neodesílat data bez odpovídajícího provozního nastavení; nepřidávat veřejný přístup; nepřepisovat ruční revize; nepoužívat soukromé vstupy ve sdíleném textu; testy nevolají placené API; žádné tajné klíče či osobní média v repozitáři. Neřešit obsluhu uživatele technickým dotazníkem, pokud odpověď lze zjistit bezpečným auditem nebo prototypem.

## 14. Pořadí vývoje a rozhodovací brány

| Krok | Výsledek | Důkaz před pokračováním |
|---|---|---|
| C00 | Technický audit a plán instalace | Známe proveditelnou kombinaci Mac/Xcode/iPhone, dostupnost serveru a neověřené body. |
| C01 | Samostatný nahrávací prototyp | Skutečný telefon, offline audio, 30minutový zámek, přerušení, mikrofon, přehrání a obnova zachovaných částí. |
| C02 | Minimální síťový prototyp | Jeden testovací soubor bezpečně dorazí přes Tailscale z cizí sítě; žádný veřejný endpoint. |
| C03 | Datový kontrakt a offline evidence | Moment/Asset/revize, čas a soukromí; restart neztratí uložená testovací data. |
| C04 | Záznamová aplikace | Čtyři tlačítka, foto, video, audio, import, zámek, denní přehled a nouzový export. |
| C05 | Spolehlivá synchronizace | Přerušení a opakování přenosu nevytvoří duplicitu ani falešné potvrzení; obnova po force-quit. |
| C06 | Provoz a druhá záloha | Obnovitelný den na jiném úložišti, stav služby, restart serveru, kontrola místa. |
| C07 | AI přepis a korektura | České zkoušky, verze textu, nejasnosti bez blokace, rozpočet a izolace selhání. |
| C08 | Automatický deník | Kapitola bez večerního schvalování, pozdní upload, chráněné lidské úpravy, HTML/Markdown export. |
| C09 | Terénní zkouška a zmrazení rozsahu | Reálný den venku, baterie, objem dat, mikrofon, cizí Wi-Fi, offline období a obnova. |
| C10 | Volitelný rodinný výběr | Povolené zdroje, nezávislý souhrn, odstraněná metadata, náhled a vědomé sdílení. |
| C11 | Později trasa a film | Ověřený import hodinek, zdrojová časová osa, původní hlas, soukromí, náhled a render. |

C00–C02 jsou malé experimenty k omezení největších rizik, ne zárodek rozsáhlého systému. Po nich stabilizovat kontrakty a skládat hotové části. Pořadí drobných nezávislých úkolů lze upravit, ale nikoli obejít bezpečnostní brány.

Nutný předodjezdový cíl končí terénní zkouškou jádra. Rodinný výběr je volitelný; hotový film není nutnou součástí první verze. Jakmile se blíží odjezd, nové funkce nesmějí vytlačit zkoušky a opravy. Přesné datum odjezdu tento dokument nestanovuje.

## 15. Akceptační scénáře

Všechny scénáře jsou požadavky k provedení; v této konverzaci nebyly otestovány na Mílově zařízení.

**A01 — Offline:** režim letadlo, nový komentář/foto/video, řádné ukončení, restart aplikace, přehrání a export bez Macu.

**A02 — Zámek:** 30 minut úvahy se zamčeným telefonem; přehrání začátku, středu, konce i hranic segmentů; žádná neoznačená mezera.

**A03 — Mikrofon:** před startem skutečný vstup; během nahrávání odpojit externí mikrofon; zachovat hotovou část, zobrazit přerušení, nepředstírat pokračování kvalitního záznamu.

**A04 — Hovor:** přerušení hovorem a návrat; žádný záznam telefonního hovoru ani samovolné nové spuštění mikrofonu. Pokračování pouze vědomým úkonem.

**A05 — Havárie:** ukončení procesu uprostřed dlouhé nahrávky; dokončené segmenty přežijí, případně chybějící konec je přiznaný.

**A06 — Místo:** nedostatek prostoru na telefonu i Macu; žádné tiché mazání originálů a žádné falešné „uloženo“.

**A07 — Síť:** výpadek během uploadu, duplicitní chunk, ztracená odpověď na dokončení, restart serveru; jediný ověřený Asset s původním obsahem.

**A08 — Integrita:** záměrně změněný chunk nebo celý soubor neprojde kontrolou; stav Macu nezíská úspěšné potvrzení.

**A09 — iOS přenos:** force-quit a nové otevření; fronta zjistí skutečný stav a pokračuje, nevytváří dojem zaručeného běhu po ukončení.

**A10 — Dny:** opožděné přijetí, změna pásma, záznam přes půlnoc a přiřazení pozdější úvahy ke starší události; originální časy se nezamění.

**A11 — AI věrnost:** české nahrávky s negací, čísly, jmény, hovorovými výrazy, větrem a tichem; výsledek porovnat se zdrojem, nejen s gramatikou.

**A12 — Bez večerní redakce:** nejasné slovo zůstane označené; po dni bez otevření přepisů přesto vznikne soukromá kapitola z dostupných dat.

**A13 — Ruční revize:** člověk opraví větu; nová dávka ani opakovaná AI oprava ji nepřepíše. Konflikt má obě zachované verze.

**A14 — Schválená AI u soukromého obsahu:** se zapnutým provozem a rozpočtem může mock externího přepisu obdržet audio „Jen pro mě“. Tento příznak není zákaz AI.

**A15 — Zákaz sdílení soukromého:** stejný testovací zdroj se nesmí objevit ve vstupu rodinného/filmového generování ani v textu, titulcích, zvuku, názvu, náhledu či metadatech výstupu.

**A16 — Zámek dodatečně:** změna běžné položky na „Jen pro mě“ zneplatní dosud neodeslané závislé exporty. U již odeslané kopie aplikace neslibuje stažení od příjemce.

**A17 — Offline soukromí:** neodeslaná změna zámku zablokuje nový export s neověřenou serverovou revizí. Neznámá nebo konfliktní viditelnost nikdy nepovolí výstup.

**A18 — Kontext:** soukromý dovětek navázaný na běžnou fotografii se neobjeví v rodinné zprávě ani nepřímo skrze kompletní osobní denní souhrn.

**A19 — Rozpočet:** chybějící limit / dosažený limit / timeout zastaví nebo pozdrží AI podle pravidel, ne archivaci. Automatické testy nevolají placené API.

**A20 — Obnova:** do prázdného umístění obnovit vybraný den z druhé kopie včetně médií, textových revizí a vazeb. Obnovu prokázat přehráním, nikoli jen existencí souborů.

**A21 — Bezpečnost:** odvolaný token nečte ani nezapisuje; škodlivé názvy nemění cesty; soukromý text/klíče nejsou v logu; sdílené kopie neobsahují přesnou GPS.

**A22 — Aktualizace:** migrace verze aplikace neztratí nesynchronizované soubory. Destruktivní reinstalace není automatický opravný krok.

**A23 — Média pro film:** výškové video, HDR import, HEIC, video bez zvuku, souvislé segmentované audio a delší vlastní komentář; pracovní konverze nepoškodí originály.

**A24 — Sdílení:** předání vybraného textu a fotografií do skutečné cílové aplikace po vědomém výběru adresáta; nic se neodešle pouhým dokončením souhrnu.

**A25 — Hodinky později:** import zachová zdroj a mezery; chybějící stopa nesmí vést k domyšlené kilometráži nebo „skutečné trase“ ze spojnice fotografií.

## 16. Doporučená výchozí nastavení v0.3

Tato konkrétní nastavení navrhuje Samantha na základě Mílových odpovědí. Nejsou to nové dotazy ani tvrzení, že byla každá číselná hodnota zvlášť schválena.

| Nastavení | Výchozí návrh |
|---|---|
| Jazyk rozhraní a deníku | Čeština. |
| Autor | Jeden vlastník, Míla. |
| Běžná viditelnost | Do deníku — soukromé, způsobilé k pozdějšímu výběru; nepublikovat. |
| Zámek Jen pro mě | Dostupný u všech typů; vztahuje se na celý Moment. |
| AI u zamčené úvahy | Povolena po provozním zapnutí AI, stejně jako u běžné. |
| Automatické publikování | Vypnuto, v první verzi se neimplementuje. |
| Korektura úvah | Minimální jazykové opravy, zachovat autorův styl. |
| Souhrn dne | Automatický, více uhlazený, pouze z doložených vstupů. |
| Večerní kontrola | Nepovinná. Žádné povinné uzavření dne. |
| Video pořizované aplikací | 1080p / 30 fps / SDR k ověření. |
| Audio v kapse | Aktivní nahrávání po zamčení, otestovaný mikrofon. |
| Ztráta mikrofonu / hovor | Zachránit část, označit přerušení; pokračovat vědomě. |
| Poloha | Jen u událostí, bez kontinuálního sledování. |
| Mobilní data | Média jen po jednorázovém povolení a s omezením; velká videa přednostně Wi-Fi. |
| Priority uploadu | Soukromí a metadata → audio → fotografie → video. |
| Mazání z telefonu | Bez automatického mazání originálů. |
| Film | Autentický 20–30minutový cestopis po návratu; délka není pevná kvóta. |
| Hlas a hudba | Původní hlas, bez syntézy; hudba není podmínkou první verze. |
| AI limit | Zatím neurčený; placený provoz nespouštět automaticky. |

## 17. Co zbývá ověřit bez nového produktového dotazníku

Produktový směr je dostatečně konkrétní pro technický audit a první prototypy. Neopakovat Q1–Q8.

Zbývá skutečná kompatibilita vývojového stroje a iPhonu, podpis a platnost instalace, domácí server a disky, záznam po uzamčení, zvuk při chůzi, chování přerušení, přenos přes cizí síť a druhá obnovitelná kopie. Nástroje a prototypy mají co nejvíce odpovědí zjistit přímo. Když přístup k zařízení není k dispozici, uvést NEOVĚŘENO a jasný krátký manuální test, nikoli domnělý úspěch.

Technické parametry, konkrétní knihovny, schéma přenosu a verze nástrojů řeší Samantha a Codex. Finanční limit AI je jediné dosud nedodané uživatelské číslo; vyřešit při přípravě placeného pilotu, nikoli jím blokovat celou specifikaci. Model hodinek ani nákup mikrofonu neblokují první záznamový prototyp.

V tomto kroku vznikly dokumenty a byla ověřena jejich návaznost na odpovědi. Nebyl napsán a spuštěn klient, kontaktován domácí server, proveden skutečný přepis osobní nahrávky, zakoupeno členství Apple ani založen vývojový repozitář.

## 18. Zdrojové podklady

Zdroje zděděné z ověřování v0.2 a doplněné při v0.3, 13. září 2026. V tomto kroku byl znovu přečten obsah S2, S3, S5, S6, S7, S9, S13 a nově S15–S17. Některé moderní stránky Apple vyžadují JavaScript; audio chování proto dokládá také oficiální archivní příručka. Starší ukázkový kód nepřebírat bez kontroly aktuálního SDK. S1, S4, S8, S10, S11, S12 a S14 zůstávají bibliografickými podklady v0.2 a musí se znovu ověřit v příslušném implementačním úkolu. Zdroje dokládají vlastnosti platforem, ne funkčnost budoucí aplikace.

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


[S15] Apple — Audio Session Categories and Modes; režim Record pokračuje se zamčenou obrazovkou: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/AudioSessionCategoriesandModes/AudioSessionCategoriesandModes.html`

[S16] Apple — Responding to Interruptions, ukládání stavu a přerušení hovorem: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/HandlingAudioInterruptions/HandlingAudioInterruptions.html`

[S17] Apple — Responding to Route Changes, změny vstupu a reakce záznamové aplikace: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/HandlingAudioHardwareRouteChanges/HandlingAudioHardwareRouteChanges.html`
