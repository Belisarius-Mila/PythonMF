# Camino — detailní funkční specifikace v0.4

**Datum:** 14. září 2026  
**Zadavatel a jediný autor deníku:** Míla  
**Zpracovala:** Samantha  
**Navazuje na:** `CAMINO_navrh_v0.3.md` a `CAMINO_plan_Codex_v0.3.md`  
**Stav:** funkční specifikace pro postupný vývoj. Žádná popsaná funkce ani zkouška na telefonu není tímto dokumentem prohlášena za implementovanou nebo ověřenou.

> Na pouti prožívat a zaznamenávat. Telefon bezpečně uchovává zdroje. Mac automaticky připravuje osobní deník. Film vzniká po návratu, nikoli jako každovečerní povinnost.

## 0. Platnost, čtení a předání

Tato v0.4 je aktuální pracovní specifikace. Zachovává potvrzená rozhodnutí U01–U11 z v0.3 a konkretizuje obrazovky, akce, výchozí hodnoty a chování při chybě. Starší soubory zůstávají beze změny. V případě rozporu má pro další vývoj přednost v0.4; historické varianty se nemají vracet do kódu.

**U** označuje rozhodnutí potvrzené Mílou. **D** je nové návrhové rozhodnutí Samanthy, které lze změnit záznamem důvodu, nikoli vydávat za dodatečně schválené uživatelem. **F** je funkční pravidlo; **UI** označuje obrazovku. Testy **T001–T080** jsou v samostatném souboru `CAMINO_akceptacni_testy_v0.4.md`. Etapy **C00–C11** jsou v `CAMINO_Codex_v0.4.md`.

Slova „musí“ a „nesmí“ stanovují podmínky implementace, nikoli záruku současné funkčnosti. Rozměry, časové intervaly a výkonové cíle jsou návrhové hodnoty, pokud není výslovně uvedeno měření. Konkrétní verze knihoven, modelů AI a systémů se zafixují až po auditu; funkční význam stavů se přitom nesmí oslabit.

Tato revize **není pokyn vyvinout celou aplikaci jedním během Codexu**. Plný OpenAPI kontrakt a databázové migrace vzniknou v C03 po prvních experimentech. Tento dokument už určuje jejich význam a bezpečnostní podmínky.

## 1. Cíl, rozsah a potvrzené volby

### 1.1 Rozhodnutí uživatele

| ID | Potvrzená volba | Závazný dopad |
|---|---|---|
| U01 | Kombinace cestopisu a osobního příběhu; film přibližně 20–30 minut podle materiálu. | Úplný deník vedle výběrového filmu; žádná povinná stopáž dne. |
| U02 | Krátké komentáře i delší úvahy; žádoucí nahrávání se zamčeným telefonem. | Společný audio základ, dva významy nahrávky, rané testy skutečného iPhonu. |
| U03 | Jemná korektura úvah, automatická gramatika a překlepy; souhrn smí být uhlazenější. | Neměnit autorův hlas ani smysl, zachovat originál a všechny revize. |
| U04 | Žádná povinná večerní práce; jednoduchá oprava je nepovinná. | Deník nečeká na schválení, nevzniká fronta povinné redakce. |
| U05 | Jeden autor, soukromý archiv; jednoduché rodinné sdílení vítáno. | Bez rodinných účtů a veřejného webu; sdílení až po výslovném kroku. |
| U06 | „Jen pro mě“ vylučuje záznam ze sdíleného deníku a filmu. | Platí i pro soukromý pracovní sestřih, citace, náhledy a parafráze. |
| U07 | Jen GPS bod u záznamu; celou trasu měří hodinky. | Bez průběžného GPS sledování aplikací a bez vlastní hodinkové aplikace. |
| U08 | Autentický hlas, případně nové namluvení po návratu; žádný umělý hlas. | Originální zvuk zachovat, nový komentář označit samostatně. |
| U09 | Externí AI smí zpracovat všechny autorovy komentáře a úvahy. | Také „Jen pro mě“; nejde však o souhlas se zveřejněním ani neomezeným výdajem. |
| U10 | Případný roční poplatek Apple Developer je přijatelný; vysvětlení později. | Ověřit instalaci a platnost, nic automaticky nekupovat. |
| U11 | Číselný rozpočet AI zatím není určen. | Vývoj bez placených volání; limit vyřešit před jejich zapnutím. |

### 1.2 Vývojový rozsah

**P0 — jádro před poutí:** offline fotografování, video, audio, textové doplnění, import, Moment a den, zámek, lokální přehled a přehrávání, nouzový export, soukromý upload, obnova přenosů, druhá záloha a zkouška obnovy, přepisy a automatický osobní deník, jednoduchá oprava textu, provozní stav a připravená instalace.

**P1 — nepovinné rozšíření:** vybraný text a fotografie rodině přes systémové sdílení. Nezařadit do vydání, dokud neprojde testy ochrany soukromí. Nesmí blokovat dokončení P0.

**P2 — po návratu:** import skutečné trasy, sestavení a kontrola střihové časové osy, titulky a render filmu, pozdější namluvení. Už v P0 se zachovávají použitelné zdroje a vazby; žádný předčasný komplexní editor.

**Mimo rozsah:** více autorů, veřejné odkazy na server, živé sledování polohy rodinou, automatické rozesílání, denní povinné filmy, generované záběry a hlas, automatická obrazová analýza všech médií, integrace sociálních sítí, vlastní VPN, navigace na trase.

### 1.3 Nová pracovní rozhodnutí této revize

| ID | Rozhodnutí Samanthy | Důvod |
|---|---|---|
| D01 | V P0 se obsah a soukromí upravují pouze v hlavním iPhonu; web je pro čtení a stav. | Méně konfliktů a žádná druhá povinná pracovní plocha. |
| D02 | Režim nových Momentů je vidět na hlavní obrazovce a pamatuje se do dalšího přepnutí. První hodnota je „Do deníku“. | Po osobní úvaze se zámek nesmí nepozorovaně vypnout. |
| D03 | Soukromý dodatek k běžnému Momentu vzniká samostatně s vazbou. | Fotografie může zůstat použitelná, soukromý hlas se k ní nepřibalí. |
| D04 | Hovor či změna aktivního mikrofonu přeruší nahrávání; automatický návrat mikrofonu nahrávání nespustí. | Ochrana obsahu a předcházení tichému přepnutí na telefon v kapse. |
| D05 | Automatický upload je zpočátku pouze přes Wi-Fi; mobilní data lze povolit jedné zobrazené dávce. | Neurčený datový tarif; žádná skrytá velká spotřeba. |
| D06 | Není automatická kopie vlastních záznamů do systémových Fotek. Je možný samostatný export. | Srozumitelné vlastnictví kopie a žádné nepozorované zdvojení místa. |
| D07 | „Skrýt z deníku“ je vratné a neuvolňuje prostor; fyzické mazání není v běžném P0 ovládání. | Vyhnout se ztrátě originálů a domnělé záloze. |
| D08 | P0 automaticky přepisuje samostatná hlasová audia, nikoli každý zvuk z videa. | Neplatit za náhodné rozhovory a ruchy; video zvuk zůstane pro film. |
| D09 | P1 sdílení vyžaduje kontrolu aktuálního soukromí proti serveru; offline neodešle starý připravený výběr. | Jednoduchá a ověřitelná ochrana místo složité offline publikace. |
| D10 | P0 nemá tlačítko střihu ani prázdnou sekci „Film“. | Na cestě nezatěžovat uživatele nedokončenými funkcemi. |

Žádné další produktové odpovědi nejsou pro tuto specifikaci nutné. Hardware serveru, hodinky a verze systémů nejsou domyšlené; řeší je audit. Rozpočet AI se řeší až před placeným pilotem.

## 2. Základní pojmy a pevná pravidla

### 2.1 Co je Moment

**F01.** Moment je jedna zachycená situace, nikoli automaticky jeden soubor. Obsahuje vlastní identifikátor, čas události, denní kapitolu, typ, příznak důležitosti a společné pravidlo soukromí. Může mít jednu fotografii, několik výslovně připojených médií, hlas a text, nebo jen časovou značku.

Samostatné pořízení z hlavní obrazovky zakládá nový Moment. Připojení do existujícího je vždy výslovné: z detailu nebo z nabídky „Přidat komentář k tomuto záběru“. Blízké časy ani stejná poloha nejsou důvodem pro skryté slučování.

Příklad: fotografie kostela + komentář u fotografie = jeden Moment. Večerní osobní dovětek „Jen pro mě“ = druhý Moment s vazbou na první. Pro rodinný export se tato vazba automaticky nenásleduje.

### 2.2 Nezaměnitelné významy

**F02.** „Do deníku“ znamená **stále soukromé**, ale použitelné pro pozdější vědomý výběr. „Jen pro mě“ zakazuje film a rodinné výstupy; nezakazuje AI. Hvězdička znamená důležitost, nikoli souhlas s publikací. „Skrýt“ znamená vyřadit z běžného přehledu, nikoli smazat soubory.

**F03.** Každý originál je neměnný. Korektury, nové namluvení, náhledy a filmové kopie jsou jiné objekty. Původní hlas má přednost před tvrzením, že strojový přepis je určitě přesný.

**F04.** Čtyři oddělené skutečnosti: lokální uložení, ověřená kopie na Macu, ověřená další záloha a stav AI. Zelený přepis nesmí maskovat neodeslaný originál.

**F05.** Nahrávání a lokální čtení uložených dat nesmějí čekat na přihlášení k serveru, GPS, internet, rozpočet ani AI. Selhání jedné funkce zastaví nejmenší nutnou část systému.

## 3. Mapa obrazovek a společné ovládání

| Obrazovka | Název | Vstup | Rozsah |
|---|---|---|---|
| UI00 | Příprava a připojení | První spuštění / Nastavení | P0 |
| UI01 | Zachytit | Výchozí hlavní obrazovka | P0 |
| UI02 | Foto | Foto / Přidat fotografii | P0 |
| UI03 | Video | Video / Přidat video | P0 |
| UI04 | Nahrávání | Komentář / Úvaha | P0 |
| UI05 | Dnes a dny cesty | Dnes / výběr data | P0 |
| UI06 | Detail Momentu | Klepnutí na položku dne | P0 |
| UI07 | Oprava textu | Upravit v detailu | P0 |
| UI08 | Import | Nabídka hlavní obrazovky / detail | P0 |
| UI09 | Uložení a přenosy | Stavový řádek | P0 |
| UI10 | Nastavení a pomoc | Nabídka hlavní obrazovky | P0 |
| UI11 | Soukromý archiv a nouzový export | Nastavení → Archiv | P0 |
| UI12 | Výběr rodině | Dnes → Poslat výběr | P1 |
| UI13 | Soukromý web na Macu | Autorizovaný přístup | P0 |
| UI14 | Film a trasa | Samostatné pozdější rozhraní | P2 |

**F06.** Rozhraní je česky, v telefonu tyká. Čas používá 24hodinový zápis. Stav nesděluje jen barvou: vždy text nebo srozumitelný symbol s popiskem. Hlavní záznamová tlačítka mají velké aktivní plochy; návrhové minimum běžného ovladače je 48 × 48 bodů. Text reaguje na systémové zvětšení. Důležité funkce nevyžadují dlouhý stisk, skryté gesto ani přesné míření. Jde o naše návrhové požadavky, nikoli tvrzení o již provedeném testu přístupnosti.

Na hlavní obrazovku se vrací jedním zřetelným krokem. Záznam nemá povinný název, tagy, hodnocení, počasí ani formulář. Příběh nesmí vzniknout jen pro vyplnění prázdných polí.

Při skutečném nahrávání je po návratu do aplikace přednostně vidět UI04, nikoli domovská obrazovka s dojmem, že mikrofon neběží. Při přechodu mimo aplikaci se osobní texty a fotografie zakryjí v jejím přepínacím náhledu. Není to příslib ochrany proti všem screenshotům nebo proti člověku s odemčeným telefonem.

## 4. UI00 — příprava, zkušební cesta a připojení

**F07.** První spuštění umožní vytvořit místní cestu bez serveru. Předvyplněný název lze změnit; žádné skutečné datum odjezdu se nezakóduje do aplikace. Pro zkoušky je samostatná cesta „Zkouška“ se samostatným ID, aby se testovací řeč a fotky nemíchaly s poutí.

Příprava má tři samostatné části: **Cesta**, **Záznam**, **Domácí Mac**. Není nutné je všechny dokončit, aby šlo lokálně něco uložit. Připravenost na pouť je však samostatná přísnější podmínka v kapitole 24.

Cesta má název, jazyk čeština a volitelný začátek. Do nastavení začátku se zobrazují data, ne vymyšlené „Dny 1–10“. Nastavení nebo oprava začátku mění zobrazené číslování, nikoli původní časy médií. Jedna cesta je aktivní; přepnutí na jinou nic nemaže a není dovoleno uprostřed nahrávání.

**F08.** Oprávnění se žádají s vysvětlením příslušné funkce. Kamera a mikrofon se dají předem ověřit testovacím snímkem a krátkým záznamem s přehráním. Poloha je nepovinná a jen při používání. Oznámení jsou nepovinná. Odmítnutí jednoho oprávnění nezakáže ostatní funkce. Systémové Fotky se vybírají přes výběr položek; nežádáme plošný přístup jen pro procházení celé knihovny.

Při první žádosti o mikrofon se po povolení ukáže jasné „Spustit nahrávání“; mikrofon se nespustí nepozorovaně návratem ze systémového dialogu. Při dalších běžných použitích hlavní tlačítko nahrávání přímo spouští.

**F09.** Propojení s Macem se provede v přípravě pomocí jednorázového párovacího údaje, například QR kódu z již připraveného serveru. Ruční vložení je záloha. Kód obsahuje identitu soukromého serveru a krátkodobé oprávnění; není to trvalý token sdílený s rodinou. Návrhová platnost je pět minut a jedno použití. Aplikace nepřijímá libovolný cizí server bez zobrazení identity a potvrzení. Žádné vypnutí kontroly HTTPS certifikátu.

Po spárování se testovací soubor odešle a porovná jeho kontrolní součet. Výsledek oddělí **Spojení funguje** od **Další záloha ověřena**. Chyba zobrazí „Mac teď není dostupný. Můžeš zatím zaznamenávat do telefonu.“ Opakované párování nesmí založit novou kopii celé cesty nebo smazat místní data.

## 5. UI01 — hlavní obrazovka Zachytit

**F10.** Horní část ukazuje název cesty a aktuální místní datum, případně číslo dne. Přímo pod tím je viditelný režim **Do deníku / Jen pro mě** pro nové samostatné Momenty. Zapnutý zámek zůstane zapnutý přes návrat na hlavní obrazovku i restart aplikace, dokud ho uživatel nezmění. Přepnutí zde nemění už existující záznamy. Zámek upravený v detailu naopak nemění režim nových záznamů.

Střed tvoří čtyři velká tlačítka. Dole jsou **Dnes** a stavový řádek. V nabídce jsou Import, Označit okamžik a Nastavení. Žádné filmové přehrávače, reklamy ani redakční úkoly.

Textové schéma, nikoli grafický prototyp:

```text
CAMINO                         Nabídka
Den 4 · datum podle telefonu
Nové záznamy: [Do deníku | Jen pro mě]

          FOTO          VIDEO
          KOMENTÁŘ      ÚVAHA

Dnes: 12 momentů                    Otevřít
V telefonu uloženo · 3 momenty čekají na Mac
```

Klepnutí na Foto/Video otevře náhled. Klepnutí na Komentář/Úvaha po připravených oprávněních zahájí příslušný hlasový záznam a zobrazí UI04. Dvojité klepnutí nesmí založit dvě nahrávky; tlačítko má stav zahajování a začne znovu reagovat až po jeho vyřešení.

**F11.** „Označit okamžik“ vytvoří Moment bez média, s časem a případně GPS. Potvrdí „Okamžik označen“ a nabídne nepovinné „Doplnit“. Neukládá fotografii ani neaktivuje mikrofon. Hvězdička v již existujícím Momentu pouze přepne důležitost; tyto funkce se nepletou.

## 6. UI02 — fotografie a navazující komentář

**F12.** Obrazovka ukazuje náhled, spoušť, zadní/přední kameru a režim soukromí. Výchozí kamera je zadní; pokročilé foto režimy nejsou P0. Režim u připojování do existujícího Momentu zdědí jeho nastavení a je zřetelně uvedeno „Přidáváš do: [čas a náhled]“.

Po stisku se zachytí zdrojový snímek, bezpečně uloží a zapíše. Až poté se objeví „Fotografie uložena v telefonu“. Náhled před dokončením zápisu není důkaz uložení. Vlastní snímek se ukládá v plné zvolené kvalitě capture pipeline, nikoli pouze jako zmenšenina pro deník. Konkrétní HEIC/JPEG volbu určí prototyp kompatibility; systém nesmí slibovat uchování dat senzoru, která vůbec nepořizuje.

Po uložení se nabídne malý pás s náhledem a **Přidat komentář**. Není nutné ho potvrdit ani zavřít pro další snímek. Tlačítko komentáře má vazbu na konkrétní ID právě ukázaného záběru, nikoli na neurčité „něco z poslední minuty“. Další samostatný snímek z hlavní kamery zakládá další Moment; další fotografie do téže situace se přidává z jejího detailu.

U nepovolené kamery se ukáže „Povol kameru v nastavení telefonu“ a Zpět; žádná prázdná černá obrazovka bez vysvětlení. Při chybě zápisu se nepoužije hláška Uloženo. Pokud část zdroje zůstala dostupná, nabídne se bezpečné opakování zápisu nebo nouzový export, nikdy smazání předchozích snímků.

Vlastní fotografie není automaticky kopírována do systémových Fotek. Import z Fotek naopak vytváří nezávislou kopii v aplikaci; smazání položky v původní knihovně nesmí smazat již dokončený import.

## 7. UI03 — video

**F13.** Otevření ukáže náhled a Start. Nahrávání začíná až stiskem Start a zřetelně ukazuje skutečně běžící čas, příjem zvuku a Stop. Během zahajování a dokončování se nedá založit další záznam.

Výchozí vlastní video navrhujeme **1080p / 30 snímků za sekundu / SDR**. Obraz na šířku je užitečný pro zamýšlený film, ale video na výšku se přijme bez překážky. Aplikace nezobrazuje před každým klipem školení o orientaci. Původní orientace se uloží a později respektuje. Import vyšší kvality se nepřekóduje jen kvůli těmto výchozím hodnotám.

Po Stop se uzavře soubor, zapíše evidence a teprve pak potvrdí uložení. Lze přidat komentář nebo pokračovat dál. Není povinné video přehrávat. Neexistuje záměrné krátké časové omezení klipu; skutečné hranice určují místo a stav zařízení a musí se zjistit testem.

**F14.** Pokračování se zamčeným telefonem je požadavek pro samostatné audio, nikoli video. Při opuštění video obrazovky, uzamčení, systémovém přerušení nebo ztrátě vstupu se aplikace pokusí klip řádně ukončit. U nepoužitelného konce přizná částečný záznam; neslibuje zachování každého posledního snímku při nuceném ukončení procesu.

Nedostupný mikrofon se nesmí tajně nahradit tichým videem. Před Start je možné výslovně zvolit „Natočit bez zvuku“ s trvalým označením. Při ztrátě zvuku v běžícím klipu se tento klip ukončí; další bez zvuku začíná až vědomou volbou. Při tepelném varování nebo nedostatku místa se nesníží kvalita skrytě uprostřed klipu.

## 8. UI04 — komentáře a úvahy

### 8.1 Průběh

**F15.** Stejný technický záznamový základ slouží oběma typům. Komentář popisuje situaci; úvaha dostává přísnější profil zachování vyjadřování. Dlouhý komentář se automaticky nemění na úvahu a krátká úvaha na komentář.

Obrazovka při nahrávání obsahuje: typ, případnou cílovou situaci, soukromí, skutečnou délku zachyceného audia, aktivní mikrofon, indikaci přijímaného signálu a velké **Ukončit a uložit**. Střídání animace nebo běžící hodiny bez nových audio vzorků se nepovažuje za důkaz nahrávání. Změna soukromí na této obrazovce platí pro celý právě nahrávaný Moment, ne jen pro slova po přepnutí, a nemění výchozí režim na hlavní obrazovce. Při připojování do existujícího Momentu platí jeho společné soukromí; oddělený soukromý dovětek se zakládá podle F21.

```text
ÚVAHA · Jen pro mě
NAHRÁVÁM                 04:32
Mikrofon: sluchátka
[indikace vstupního signálu]

        UKONČIT A ULOŽIT
```

Běžný konec nepotřebuje potvrzení. Po bezpečném zápisu se zobrazí „Úvaha uložena v telefonu“ a návrat do předchozího kontextu. Přepis se zobrazí později. Není živý cloudový diktát a není povinný poslech nahrávky. V P0 není uživatelská pauza samostatnou velkou funkcí; systémová přerušení jsou ošetřena explicitně.

Je dovolena právě jedna aktivní záznamová session. Otevření dalšího audia či videa nebo přehrávače se nejprve vrátí k běžícímu záznamu. Telefon nepřepíná mikrofon mezi dvěma soupeřícími funkcemi a sám žádnou z nich bez oznámení neukončí.

### 8.2 Zámek, sluchátka a přerušení

**F16.** Již spuštěné samostatné audio má pokračovat po uzamčení telefonu. Podporu vhodných audio režimů popisuje Apple; správná audio session, oprávnění a background režim se ověřují na zařízení. [S01] Na zamčeném telefonu se nahrávání v P0 nově nespouští. Ovládání tlačítkem libovolných sluchátek, Siri a hodinkami není součástí tohoto závazku.

Vestavěný mikrofon je použitelný vstup; pro telefon v kapse se má otestovat mikrofon mimo kapsu. Z existence sluchátek se nevyvozuje, že obsahují mikrofon nebo že jej systém skutečně používá. Aplikace ukazuje aktivní vstup a umožní jeho ověření v přípravě. Není schválen žádný nákup vybavení.

**F17.** Při hovoru, deaktivaci audio session nebo změně skutečně používaného vstupu se uloží dosud dostupná část a záznam přejde do stavu **Přerušeno**. Apple poskytuje události přerušení a změny zvukové cesty; po přerušení nemusí vždy přijít odpovídající událost konce. [S02, S03]

Výchozí aplikace sama neobnovuje nahrávání po hovoru, opětovném připojení sluchátek, návratu z jiné aplikace nebo restartu. Nabízí **Pokračovat** a **Ukončit**. Pokračování vytvoří další část téže session s evidovanou mezerou. Přijetí hovoru není zdroj audia do deníku. Obrazovka jasně říká například „Nahrávání přerušeno. Zachováno 4:32.“

Při dostupném oprávnění se aplikace pokusí použít místní upozornění bez citlivého textu. Nelze slíbit slyšitelnou nebo okamžitou výstrahu za každého režimu telefonu. Při návratu do aplikace je stav vždy zřetelný.

### 8.3 Dlouhý záznam a zotavení

**F18.** Dlouhé audio se nemá stát jedním zranitelným souborem, který existuje teprve po Stop. Návrhový cíl prototypu je uzavírat obnovitelné části nejvýše po 60 sekundách, bez restartování fyzického vstupu mezi částmi. Uživatel stále vidí jednu úvahu.

Způsob zápisu a formát částí se vyberou v C01 podle zkoušky kontinuity, kvality a spotřeby. Uchová se pořadí, skutečná délka a mezery. Při havárii může být poslední neuzavřená část poškozená; dříve uzavřené části se mají obnovit. Limit 60 sekund je cíl ztráty neuzavřeného úseku při testovaných chybách, nikoli garance při poruše úložiště nebo celého zařízení.

Po návratu aplikace nabídne zachovaný obsah jako **Obnovená částečná nahrávka** a ukáže, co je skutečně přehratelné. Nikdy se sama znovu nerozposlouchá. AI neobdrží domnělé chybějící věty; pracuje jen s potvrzenými částmi a s informací o přerušení. Serverový pohodlný spojený soubor je odvozenina; původní části zůstávají archivním zdrojem.

## 9. UI05 — Dnes, jiné dny a soukromý deník

**F19.** Dnes se otevře okamžitě z místních dat. Server není nutný pro zobrazení vlastních uložených médií. Obrazovka obsahuje datum a číslo dne, případný vlastní název etapy, stručný stav přenosu, přehled Momentů a poslední dostupný souhrn. Výběrem data se přejde na jiný den. Po návratu z detailu se zachová místo v přehledu.

Časová osa se řadí od rána k večeru. Nový záznam je dohledatelný bez čekání na náhled nebo AI; při výrobě náhledu má dočasnou neutrální kartu. Dlouhý den se nenačítá celý ve vysokém rozlišení. Každá karta ukazuje čas, typ, dostupný náhled nebo úryvek textu, hvězdičku a případný zámek. Skryté položky nejsou ve výchozím přehledu.

Filtrování má v P0 pouze **Vše**, **Důležité** a **Úvahy**. Tím nevzniká katalog desítek tagů. Zamčený obsah je v soukromém přehledu viditelný vlastníkovi a označený; samotný zámek neznamená další šifrovaný trezor uvnitř aplikace.

**F20.** Denní souhrn má vedle textu nenápadný stav: „Z dostupných záznamů“, „Čeká na přepis“, „Nové záznamy ještě nejsou zahrnuté“ nebo „Ručně upraveno“. Zobrazený čas sestavení neznamená, že server zná vše, co je v telefonu. Telefon může doplnit přesný místní počet čekajících položek; web jen počet těch, o nichž ví.

Nevzniká povinné schválení nebo „Uzavřít den“. Prázdný den ukáže „Zatím tu nejsou žádné záznamy“, nikoli vymyšlený text. Den s fotografiemi bez komentářů má galerii, ale AI si nesmí domýšlet jejich obsah. Krátký den může mít dvě věty; doporučení 100–200 slov se použije jen při dostatku textových podkladů.

Kapitola deníku má tuto šablonu; prázdné bloky se vynechají:

```text
Den a datum — nepovinný potvrzený název etapy
Titulní fotografie
Krátký souhrn z dostupných textových záznamů
Momenty v časovém pořadí s komentáři
Samostatné úvahy v plném rozsahu
Galerie a původní audio/video
Stav úplnosti a datum posledního sestavení
```

Titulní snímek se určí bez placeného hodnocení: explicitně vybraný snímek, jinak první hvězdičkou označená fotografie, jinak první dostupná fotografie podle času. Pro osobní deník může být i ze zamčeného Momentu; jeho soukromí zdědí všechny odvozeniny. Rodinný výběr nepřebírá tuto obálku automaticky.

Pokud je souhrn stažený, je čitelný i offline. Dosud nestáhnutý souhrn se offline nevygeneruje. Soukromá galerie a textové poznámky fungují i při vypnuté AI.

## 10. UI06 — detail Momentu a jednoduché opravy

**F21.** Detail zobrazuje média v pořadí připojení, hlasový přehrávač, čtenářský text, čas situace, kapitolu, dostupnou polohu, stav kopií, hvězdičku a soukromí. U později namluvené vzpomínky rozlišuje „Patří k: [událost]“ a „Nahráno: [skutečný čas]“.

Běžné akce: přehrát, prohlédnout, hvězdička, přepínač soukromí, **Přidat komentář**, **Soukromý dovětek**, **Upravit text**. Další méně časté akce jsou v nabídce: připojit médium, napsat doplnění, změnit den kapitoly, nastavit titulní fotografii dne, zobrazit původní přepis, skrýt Moment. Název lze doplnit, ale není povinný a AI jej nemusí sama vymýšlet.

„Přidat komentář“ přidává audio do právě otevřeného Momentu a dědí jeho zámek. „Soukromý dovětek“ založí samostatnou úvahu `owner_only=true`, s viditelnou vazbou pro vlastníka. Nezmění původní fotografii ani globální režim nových záznamů. Soukromí celého Momentu nelze obejít odlišným příznakem jedné přílohy.

Při přehrávání delšího audia jsou k dispozici Play/Pause a posun v čase. Více částí jedné session se přehrává v pořadí; v přerušení se ukáže značka mezery. Média se sama hlasitě nespouštějí při otevření detailu.

**F22.** Přesun do jiného dne mění jen kapitolu. V dialogu je datum a věta „Čas původní fotografie nebo nahrávky zůstane zachován.“ Pozdější upload použije nové přiřazení, ale zachová oba časové údaje. Opravovat časovou kapitolu nemusí uživatel každý večer.

**F23.** „Skrýt z deníku“ je vratná akce s možností Vrátit. Položka včetně originálů zůstane v archivu a záloze, ale zmizí z běžného přehledu i nových filmových a rodinných výběrů. Soukromý automatický souhrn se označí jako zastaralý a vytvoří se jeho nová verze bez skrytého zdroje. Ručně upravený text se nepřepíše; dostane upozornění, že může odkazovat na skrytou položku.

Skryté položky jsou dostupné v Nastavení → Archiv → Skryté. Obnovení vrací jejich předchozí soukromí, ne automaticky „Do deníku“. Hláška u skrytí výslovně uvádí, že neuvolňuje místo. P0 nemá běžné tlačítko nevratného mazání originálů. Již odeslané kopie nemůže skrytí ani zámek vzít zpět.

## 11. UI07 — editor textu a jeho verze

**F24.** Editor se otevírá jen na výslovnou akci. Zobrazuje aktuální čtenářský text, jednoduché textové pole, **Uložit** a **Zrušit**. Žádné nástroje pro sazbu, práci se stopami nebo formátování dokumentu. Přepis a původní audio zůstávají vedle editoru dohledatelné.

Rozpracovaný text se průběžně ukládá lokálně jako koncept, například po sekundě klidu a při opouštění obrazovky. Koncept není hotová lidská revize ani nový vstup do AI. Po pádu je dostupný k obnovení. Zrušení ruší koncept po potvrzení pouze tehdy, když obsahuje změny.

Uložit vytváří lidskou revizi a označí ji jako aktuální. Dokud ji uživatel sám nenahradí, pozdější AI výsledek ji nesmí přepsat. Nový AI návrh se může objevit v historii, nikoli jako změněný text bez vědomí autora. První verze nemá automatickou korekturu každého stisku klávesy.

Ručně psané nové doplnění se nejprve uloží jako zdrojový text a následně může dostat automatickou jazykovou korekturu. Text, který už autor výslovně upravil v editoru, se automaticky dál nepřepisuje. Rozdíl mezi psaným vstupem a ruční opravou musí být v modelu rozlišen.

## 12. UI08 — import ze systémových Fotek

**F25.** Z hlavní nabídky lze vybrat více fotografií a videí. Každá samostatně vybraná položka výchozím pravidlem vytvoří nový Moment. Import z detailu Momentu naopak výslovně připojí vybrané zdroje do něj a zdědí jeho soukromí.

Import má seznam s počtem **Zkopírováno / Čeká / Chyba**. Skutečné uložení znamená, že aplikace vlastní celý vybraný soubor v trvalém úložišti, ne odkaz na dočasný náhled. U položky dostupné jen v iCloudu se zobrazí „Čeká na stažení z Fotek“. Získání takového souboru se může řídit také nastavením systémové knihovny, nikoli jen naší upload fronty; při požadavku sítě se musí uživatel dozvědět, že se data teprve stahují.

Originálem importu se rozumí **bajty skutečně předané systémovým výběrem**. Může jít o upravenou nebo exportovanou reprezentaci. Aplikace zachová tuto reprezentaci a její dostupná metadata; neslibuje přístup k nezměněnému foto-originálu senzoru. Pokud zná variantu, uloží `original / edited / current / unknown`. Import neprovádí další skrytou ztrátovou kompresi.

Vlastní Live Photos nevytváříme. V P0 je import Live Photo výslovně importem statické fotografie, nikoli zárukou zachování celé pohyblivé dvojice; uživatel to u takové položky uvidí. Zachování obou zdrojových částí lze doplnit později.

**F26.** Opakovaný výběr téhož dostupného identifikátoru z knihovny se rozpozná. Jako další kontrola slouží hash skutečných dat. Výchozí akce při shodě je „Už je v deníku — zobrazit“, nikoli duplikace či automatické sloučení soukromí dvou situací. Pokud uživatel výslovně potřebuje samostatný Moment se stejným souborem, vznikne nový Moment a vlastní Asset ID se stejnými zdrojovými bajty. Jeden Asset ID se nesdílí mezi Momenty s různým soukromím. Případná fyzická deduplikace je až vnitřní optimalizace, nikoli propojení oprávnění; v P0 není nutná.

Import zachová známý čas pořízení. Chybějící časové pásmo se neodvodí s falešnou jistotou z aktuální polohy telefonu. Nejasné položky lze předvybrat do otevřeného dne s označením „Den přiřazen při importu“ a nepovinnou opravou. Den importu ani přijetí na Mac se nesmí vydávat za doložený čas fotografie.

Přerušení importu ponechá dokončené kopie. Neúplná kopie zůstane označená a lze ji opakovat. Originál ve Fotkách se žádnou importní akcí nemaže.

## 13. UI09 — stav uložení, fronta a mobilní data

**F27.** Obrazovka používá oddělené sekce:

| Sekce | Co přesně tvrdí | Příklad |
|---|---|---|
| Telefon | Dokončené zdroje jsou lokálně zapsané a evidované. | 38 momentů uložených |
| Mac | Všechny požadované zdroje mají potvrzený hash a metadata dané revize. | 33 úplných, 5 čeká |
| Další záloha | Existuje ověřená další kopie zahrnující zdroje a relevantní metadata. | Ověřeno do 18:42 |
| AI | Stav přepisů, korektur a souhrnů nezávisle na kopiích. | 2 audia čekají na přepis |

Počet Momentů se neplete s počtem souborů nebo vnitřních audio segmentů. Detail může říci „1 úvaha, 14 částí“, ale hlavní přehled z toho neudělá 14 úvah. Zobrazené bajty jsou skutečné čekající přenosy, nikoli velikost již ověřeného archivu.

**F28.** Jsou zde **Synchronizovat nyní**, **Pozastavit přenosy** a po otevření čekající dávky **Odeslat i přes mobilní data**. Pozastavení zastaví plánování nových úloh a podle možností bezpečně přeruší probíhající; neznamená, že už přenesené bajty vrátí. Záznam, lokální čtení a změny metadat fungují dál.

Výchozí automatický režim je pouze Wi-Fi. Jednorázové mobilní povolení zobrazí konkrétní počet souborů a objem a platí jen pro výslovně vybranou dávku, nikoli pro další záznamy pořízené později. Retry stejného souboru může přenést další bajty; odhad proto není garance vyúčtování operátora. Hotspot telefonu připojeného přes Wi-Fi může být z hlediska tarifu placené připojení; aplikace nemůže vždy poznat způsob jeho účtování.

Pokročilý trvalý mobilní režim s limitem není nutný pro P0. Datovou politiku lze po měření rozšířit bez zásahu do záznamového modelu. „Synchronizovat nyní“ neruší omezení sítě a nevypíná Tailscale; ukáže skutečnou překážku.

**F29.** Důvody čekání se nerozmazávají do jedné animace:

| Stav | Text pro uživatele | Dovolená akce |
|---|---|---|
| Není vhodná síť | Čeká na Wi-Fi. V telefonu je uloženo. | Mobilní dávka / později |
| API nedosažitelné | Domácí Mac teď není dostupný. | Zkusit spojení / pomoc |
| Autorizace neplatí | Obnov připojení k domácímu Macu. | Párování bez smazání dat |
| Na Macu chybí místo | Na Macu není místo pro další soubory. | Nechat čekat / stav serveru |
| Ověřování | Soubor dorazil, kontroluji úplnost. | Žádný falešný zelený stav |
| Nesouhlasí data | Přenos se nepodařilo ověřit; originál zůstává v telefonu. | Bezpečné opakování |
| Uživatel pozastavil | Přenosy jsou pozastavené. | Pokračovat |
| AI stojí na limitu | Přepis čeká na rozpočet. Ukládání pokračuje. | Stav AI |

Z nedosažitelnosti API nelze bez důkazu určit, že je vypnutý Mac, rozbitý internet nebo Tailscale. Diagnostika nabízí možnosti, ale netvrdí jednu příčinu jako jistou.

## 14. UI10 — nastavení, pomoc a upozornění

**F30.** Nastavení obsahuje pouze skupiny **Cesta**, **Připojení**, **Přenosy**, **Záznam a mikrofon**, **Archiv**, **AI a spotřeba**, **Pomoc**. V běžném rozhraní nejsou databázové názvy, modelová ID, porty nebo chunk velikost.

Položka AI ukazuje zapnuto/pozastaveno/mock, odhad čerpání schváleného limitu a datum poslední známé synchronizace. Bez spojení se tato čísla neoznačí jako živá. Konkrétní technické nastavení klíče je na serveru, nikoli v telefonu.

**F31.** Upozornění mají tři úrovně. Kritické: nezapsaný záznam nebo úplná ztráta audio vstupu; viditelně ihned, a pokud lze, i místním oznámením. Důležité: nedostatek místa, dlouho neodeslané originály, dlouho neověřená záloha; stavový pruh a nejvýše jedno opakování stejného problému za den při příležitosti běhu aplikace. Běžné: hotový přepis, nová gramatická oprava či souhrn; bez push a bez přerušení uživatele.

Návrhová hranice dlouhého čekání je 24 hodin od pořízení nezálohovaného dokončeného zdroje. Bez povolených oznámení se vše ukazuje uvnitř aplikace. Neexistuje záruka přesného času upozornění, pokud iOS aplikaci nespustí. V P0 nezřizujeme veřejnou push infrastrukturu, která by tuto nejistotu jen zakryla.

Zprávy na zamčené obrazovce neobsahují přepisy, jména míst, úvahy ani citlivé náhledy. Podrobnosti se zobrazují až uvnitř aplikace. Pomoc obsahuje jasné „Neodinstalovávej aplikaci, dokud nemáš ověřenou kopii místních dat.“

## 15. UI11 — nouzový export a přenositelný archiv

**F32.** Vlastník může bez domácího serveru vyexportovat den nebo celou dostupnou cestu z telefonu. Výstup obsahuje zdrojové soubory, lokální textové revize, přiřazení dnů, zámky, vazby, časy, manifest velikostí a hashů a jednoduchý čitelný přehled. Chybějící přepisy nejsou chyba exportu originálů.

Úvodní obrazovka výslovně říká: **„Soukromý archiv obsahuje i Jen pro mě a může obsahovat přesnou polohu. Není to zpráva pro rodinu.“** Cíl se vybírá jako vlastní úložiště v Souborech, nikoli jako nabídka adresátů rodinné zprávy. Výchozí archiv není prezentován jako heslem šifrovaný trezor.

Pro krizově málo místa se nesmí nejprve vyrobit druhá úplná kopie celé cesty v interní paměti. Preferuje se průběžný export do zvolené složky po souborech. Pokud konkrétní poskytovatel úložiště nedovolí bezpečný zápis tímto způsobem, aplikace nabídne menší dávku nebo jiný cíl; nevydává nedokončenou kopii za zálohu.

Manifest začíná jako neúplný. Teprve po ověření všech zkopírovaných položek se export označí za dokončený. Při přerušení jsou rozpoznatelné hotové soubory a lze pokračovat. Již existující cílový soubor se přepíše jen tehdy, je-li doložena shoda a bezpečná operace; jiný obsah je konflikt, ne tiché nahrazení.

„Export vytvořen v Souborech“ není automaticky „Nezávislá záloha ověřena“. Složka Na mém iPhonu zůstává na témž zařízení. U cloudového cíle může místní dokončení předcházet jeho vzdálenému nahrání. Pro skutečnou jistotu další kopie je nutné ověření na druhé straně.

**F33.** Na Macu vzniká úplný přenositelný archiv s HTML, Markdown, JSON manifestem a relativními cestami k médiím. Musí být čitelný bez databázového serveru a bez AI účtu. HTML je statické, s escapovanými uživatelskými texty a bez externích sledovacích prvků. Odkazy neobsahují přístupové tokeny. HEIC či zvláštní video může vyžadovat kompatibilní prohlížeč; k běžnému prohlížení proto existují odvozené JPEG/video náhledy, originály však zůstávají.

## 16. UI12 — volitelný výběr rodině

**F34. P1.** Vstup je Dnes → Poslat výběr. Nejde o odeslání kompletní osobní kapitoly. Výběr obsahuje jen nezamčené a neskryté zdroje. Zamčené položky se nenabízejí a ve výsledku nesmí být ani sdělení, kolik jich bylo vynecháno.

Výchozí nabídka může předvybrat až pět hvězdičkou označených fotografií; nejsou-li, nabídne ruční výběr. Cílem jsou zpravidla 3–5 fotografií, nikoli povinný počet. Lze odeslat i jedinou fotografii. Automatické připojení všech videí a původních nahrávek se v P1 nedělá.

Průchod je **Výběr → Náhled textu a fotografií → Sdílet**. Text se vyrábí jen z vybraných povolených komentářů. Kompletní osobní souhrn, soukromé dodatky ani kontext dřívějších zamčených úvah se k tomu nepoužívají. Není-li text připraven nebo AI dostupná, je možný výběr bez souhrnu nebo s přímo převzatými povolenými popisky; žádné domyšlené vyprávění.

**F35. P1.** Před sestavením a znovu před předáním do systémového sdílení se zkontrolují identifikátory a aktuální revize soukromí, vybraných textů a skrytí. Lokální neodeslaná změna soukromí nebo nedostupný server export pozdrží. Na telefonu se ještě provede okamžitá lokální kontrola těsně před předáním. Tím se nevyžaduje večerní práce; pouze se nepublikuje zastaralý výběr bez vědomé akce.

Rodinné fotografie se vytvoří jako samostatné kopie, návrhově JPEG s delší hranou 2048 bodů obrazu. Transformace orientaci skutečně zapracuje a z výstupu odstraní GPS i další nepotřebná EXIF/XMP metadata. Pouhé skrytí souřadnic v rozhraní nestačí. Názvy exportů jsou neutrální, nikoli převzaté z tajných poznámek. Originály se nemění.

**F36. P1.** Uživatel sám vybere cílovou aplikaci a adresáta. Camino nevytváří rodinné účty a samo neodesílá zprávy. Po předání smí říci „Předáno do sdílení“, nikoli bez důkazu „Rodině doručeno“. Zrušení nezpůsobí pozdější automatický pokus. Rozložení více fotografií a textu se musí vyzkoušet v konkrétní cílové aplikaci; není garantováno ve všech komunikačních aplikacích stejně.

Změna soukromí před předáním výběr zneplatní. Po předání jiné aplikaci nebo po odeslání už nelze zaručit odvolání kopie. I ručně napsaný text v náhledu může obsahovat osobní informaci; zámek je ochrana označených zdrojů a jejich odvozenin, ne vševědoucí kontrola toho, co sám autor napíše.

## 17. UI13 — soukromý web na Macu

**F37.** Web má v P0 dvě hlavní části: **Deník** a **Stav systému**. Deník zobrazuje cesty, dny, média, texty a zámky; je pouze pro vlastníka. Stav ukazuje poslední kontakt telefonu, počty známých nedokončených zdrojů, místo, frontu zpracování, poslední zálohu a výsledek poslední zkoušky obnovy.

V P0 se přes web nepřepisují komentáře, nemění soukromí a nespouští rodinné publikace. Tím je jasný jediný uživatelský zapisovatel metadat: hlavní iPhone. Správce serveru může provozně pozastavit AI či worker; to není druhý editor deníku. Pozdější rozšíření na více editorů vyžaduje výslovný konfliktový model.

Nedostupné médium se neotevře jako rozbitý prázdný přehrávač: je vidět, zda čeká na upload, nemá náhled, nebo je zdroj neúplný. Web nemůže tvrdit, že má všechno z telefonu, pokud nezná jeho aktuální inventář.

Přístup je pouze autorizovaný uvnitř soukromé sítě. Webová session používá bezpečné cookies, žádné tokeny v URL, žádné veřejné náhledy zámků. Přesná provozní instalace je úkol C06.

## 18. Datový význam, čas a polohové údaje

### 18.1 Minimální model

**F38.** Identifikátory se vytvářejí offline a jsou stabilní po přenosu. Pořadí ve frontě ani název souboru nejsou identita. Před implementací se v C03 zafixuje přesný kontrakt; tato tabulka stanovuje význam polí, nikoli hotové databázové migrace.

| Objekt | Povinný význam | Důležitá nepovinná data |
|---|---|---|
| Trip | ID, název, jazyk, aktivní stav, provozní politika | Začátek a konec cesty; nikdy povinný pevný počet dnů |
| JourneyDay | ID, Trip, datum kapitoly | Vlastní název etapy, titulní zdroj, revize souhrnu |
| Moment | ID, Trip, kapitola, typ, časová provenience, soukromí, revize, skrytí | Hvězdička, vlastní název, vazba na jiný Moment, poloha |
| Asset | ID, Moment, mediální typ, původ, byte velikost, po dokončení SHA-256 | Délka, rozměry, orientace, kodek, importní reprezentace |
| RecordingSession | ID, Moment, typ audia, stav, pořadí částí | Mikrofon, přerušení, zachycená délka, časové mezery |
| TextRevision | ID, role textu, obsah, seznam zdrojů, rodičovská revize, autor změny | Model a recept, nejasná místa, časové úseky |
| LocalOperation | Jednoznačné ID, pořadí v zařízení, cílový objekt a očekávaná revize | Důvod konfliktu, potvrzení serveru |
| UploadSession | ID, Asset, očekávaná velikost/hash, seznam potvrzených částí | Poslední aktivita, pokusy, dokončovací stav |
| ProcessingJob | Jednoznačný klíč operace, vstupní verze, stav | Retry, lease, náklady, chyba |
| BackupReceipt | Cílové úložiště, snapshot, ověřené soubory a metadatová revize | Datum kontroly a zkoušky obnovy |
| ExportRevision | Publikum, seznam přesných zdrojových revizí, stav, soukromostní kontrola | Předání jiné aplikaci; nikoli domnělé doručení |

Soukromí je vlastnost celého Momentu. Asset je pro publikaci vždy vyhodnocen přes svůj Moment; nulová nebo neznámá politika se považuje za nepovolenou. Odvozené texty uchovávají všechny zdroje, ne pouze poslední fotografii.

**F39.** Jeden hlavní telefon je jediný zapisovatel uživatelského obsahu v P0. Server vytváří AI revize a odvozeniny, nikoli nevyžádané úpravy uživatelských polí. Každá změna obsahuje ID operace a očekávanou revizi. Znovu odeslaná táž operace má stejný efekt a nezakládá další lidskou revizi.

Po konfliktu se neztrácí žádná varianta. Lidská revize má přednost v zobrazování před později doručenou AI, ale obě zůstávají. Při rozporu o soukromí je účinná přísnější varianta. Server neřeší pořadí změn jen podle hodin telefonu; používá vlastní revize a potvrzené pořadí operací.

Obnova staršího telefonu, výměna zařízení nebo serveru není obyčejné pokračování starého kurzoru. Spustí se řízené znovuporovnání inventáře a změnové historie. Z této situace nikdy nesmí vyplynout automatické mazání novějšího originálu.

### 18.2 Čas a kapitoly

**F40.** Uchovávají se čas zachycení v UTC, známý místní čas a offset při zachycení, dostupné ID časového pásma, zdroj časového údaje a samostatný čas přijetí serverem. Trvání audia a videa se odvozuje z mediální časové základny, ne odečtením dvou nestabilních hodin telefonu.

Výchozí kapitola je místní datum při začátku situace nebo nahrávky. Audio přes půlnoc zůstane v dni začátku. Po překročení hranice či změně pásma se již uložené kapitoly samy nepřesouvají. Denní souhrn se neřídí časem Macu v ČR. Nejasný import nese údaj o nejistotě; správný offset se nevymýšlí.

Den má stabilní ID, jeho zobrazené pořadí se vypočte z nastaveného začátku cesty. Přípravné záznamy před začátkem mohou být označené „Před cestou“. Odpočinkový nebo prázdný den není chyba. Pozdější vzpomínka má vlastní čas audia a explicitní vazbu nebo uživatelem změněnou kapitolu původní situace.

### 18.3 Poloha

**F41.** Poloha se pořídí jednorázově pro situaci, bez blokování fotoaparátu nebo mikrofonu. Návrhově se použije aktuální měření či cache stará nejvýše 120 sekund. U každého bodu se ukládá čas a horizontální přesnost; např. hodnota nad 100 metrů se označí jako přibližná. Tyto hranice jsou naše pracovní parametry, nikoli slib skutečné přesnosti GPS.

Starší známá poloha se nevydává za aktuální; raději je bod neznámý. Odepřená poloha nebrání žádnému typu záznamu. Názvy míst a etap nejsou odhadované AI jako jistá fakta. V P0 stačí bod a případně uživatelský popisek. Zápis názvu místa zvenku musí mít známý původ.

Mapa bodů se nazývá **Místa záznamů**, nikoli Prošlá trasa. Kilometráž se nepočítá jako součet spojnic fotografií. První verze nemá oprávnění pro průběžnou polohu na pozadí ani příjem biometrických údajů z hodinek.

## 19. Bezpečné místní uložení a stavové automaty

### 19.1 Zápis a obnova

**F42.** Média jsou v trvalém prostoru aplikace, nikoli ve vymazatelné cache. Při zápisu existuje journal rozpracované operace. Dokončený soubor se bezpečně přesune na své stabilní místo a propojí s databází. Protože databáze a souborový systém nejsou jediná společná transakce, při každém startu se musí opravit neuzavřené operace a osiřelé soubory.

SHA-256 velkého videa se počítá proudově mimo hlavní vlákno. Hláška místního uložení může přijít po dokončeném bezpečném zápisu a evidenci před dokončením hashe; k ověřenému serverovému přenosu je ale konečný hash povinný. Uživatelské rozhraní nesmí čekat na načtení celého videa do paměti.

Pracovní náhledy lze obnovit. Nedokončené soubory se zkoušejí rozpoznat a obnovit; neodstraňují se bez vyhodnocení jen proto, že nejsou v běžném seznamu. Vymazat cache není totéž jako vymazat originály.

Ochrana souborů a tokenu musí být nastavena tak, aby fungovalo již spuštěné audio i souborové přenosy při zamčení po prvním odemknutí zařízení. Režim po úplném restartu před prvním odemknutím je oddělený test. Neobcházet problém plošným vypnutím ochrany dat. Přesné třídy ochrany a jejich dopady jsou výstup auditu/prototypu, ne volba pro Mílu. [S13]

### 19.2 Úložiště a priorita záznamu

**F43.** Pracovní varování je při méně než 2 GiB volného místa. Hodnota není příslib, kolik hodin videa zbývá. Pro Start se vyhodnocuje prostor pro bezpečné dokončení, aktuální profil videa a pracovní rezervu. Předběžně se drží 512 MiB provozní rezerva; způsob jejího zachování se musí ověřit a upravit podle měření.

Při nedostatku se nezamknou automaticky všechny funkce: krátký text může být stále možný, velké video ne. Aplikace řekne, která akce nejde a proč. Běžící záznam se snaží včas řádně ukončit. V krajní chybě přizná částečnost. Nikdy automaticky nesmaže nesynchronizovaná data kvůli novému klipu.

Nahrávání má přednost před generováním náhledů, hashováním velkých importů a plánováním dalších velkých uploadů. Při nízké baterii se nejdříve omezí nepovinná práce; audio se nezastaví jen na základě libovolně zvoleného procenta, ale skutečné systémové ukončení nelze znemožnit.

### 19.3 Stavy médií

**F44.** Záznamový automat:

```text
připraveno → zahajuji → nahrávám / zachycuji → dokončuji → uloženo
                              ↘ přerušeno → pokračuji / dokončuji
jakýkoli nedokončený stav → obnova po chybě → částečně obnoveno / nelze obnovit
```

„Uloženo“ se vztahuje ke konkrétně zachovanému rozsahu. Částečná úvaha zůstane označená i po úspěšném uploadu; serverová kopie nezmění historickou částečnost na úplný zážitek.

Přenosový automat:

```text
čeká na dokončení zdroje → připraveno → čeká podle sítě → odesílá se
                                      ↖ dočasná chyba      ↓
                                                     ověřuje se → ověřeno na Macu
```

Neplatná autorizace, nesoulad obsahu a server bez místa jsou samostatné blokace. AI má vlastní stavy `čeká / běží / hotovo / nejasné / pozastaveno limitem / chyba`, nesdílí jediný příznak „hotovo“ s uploadem.

## 20. Přenos iPhone ↔ Mac

### 20.1 Síť a dosažitelnost

**F45.** Preferovaná architektura zůstává nativní iPhone aplikace, soukromé HTTPS přes Tailscale Serve a API naslouchající na localhostu Macu. Serve zpřístupňuje službu uvnitř tailnetu; pro veřejné služby existuje odlišná funkce Funnel, kterou zde nepoužijeme. Přístup se omezí síťovými pravidly a vlastním odvolatelným oprávněním aplikace. [S05]

Tailscale je samostatná aplikace a nastavení, ne komponenta vlastní VPN v Caminu. VPN On Demand může pomoci s navázáním spojení, ale není zárukou okamžité synchronizace, obcházení přihlašovací hotelové stránky nebo probuzení domácího Macu. [S06]

**F46.** Přenosy používají souborové úlohy URLSession a trvalou lokální frontu. iOS plánuje práci na pozadí; nucené ukončení aplikace má jiné důsledky než prosté zamčení. Implementace musí přežít zrušené úlohy a po dalším otevření zjistit skutečný stav, nikoli předpokládat pokračování. [S04]

V P0 neslibujeme neomezenou bezobslužnou synchronizaci za všech situací. Krátké otevření aplikace a „Synchronizovat nyní“ je provozní záloha automatizace, ne večerní redakce. Nedostupný internet několik dnů nevadí architektuře, pokud je dost místního prostoru; nesynchronizovaný obsah ovšem zůstává vystaven ztrátě telefonu.

### 20.2 Význam přenosového kontraktu

**F47.** Telefon nejprve založí či aktualizuje manifest Momentu a Assetu. Server dostane identifikátory, očekávanou velikost, konečný hash a relevantní revize. Založení opakované se stejným ID a shodným obsahem nezaloží druhý soubor.

Velké soubory se přenášejí po očíslovaných částech; výchozí experimentální velikost je 8 MiB. Klient má současně připravený jen omezený počet částí, například dvě, a soubory musí ponechat dostupné po dobu skutečně běžící přenosové úlohy. Nenakopíruje celé video do druhého dočasného adresáře. Část má délku a hash; opakovaná stejná část je bezpečná, jiné bajty pod stejnou identitou jsou konflikt.

Server potvrzuje přijaté části až po jejich bezpečném zápisu. Klient po přerušení požádá o skutečný seznam přijatých částí a doplní zbytek. Byte progress může dosáhnout 100 %, ale UI stále ukazuje **Ověřuji**, dokud není potvrzena finalizace.

**F48.** Finalizace sestaví soubor, ověří celkovou velikost a hash, dokončí zápis a evidenci a vydá potvrzení vázané na konkrétní zdroj. Nelze ji nahradit jen důvěrou klientskému hashi bez jeho výpočtu na serveru. Při restartu mezi souborovým přesunem a databázovým potvrzením proběhne oprava journalu.

Ztracená odpověď na dokončení nevyvolá bezhlavé nahrání všeho znovu: klient načte stav Assetu. Neznámý hash, jiná velikost, chybějící část nebo neověřený manifest nikdy nedávají stav „Ověřeno na Macu“. Opakované potvrzení může být doručeno vícekrát, funkční výsledek je jeden.

Průběžné chunkování na iOS musí být ověřeno jako celek. Samotná existence souborových background uploadů neznamená, že systém dovolí kdykoli okamžitě připravit další část. Při nedostatečném výsledku C02/C05 lze přenosovou strategii upravit se zachováním ověření a obnovy; neobětovat bezpečnost jen pro zachování čísla 8 MiB.

### 20.3 Metadata, priority a stav zařízení

**F49.** Změny soukromí, skrytí a malé manifesty mají prioritu před velkými médii. Potom přichází dokončené audio, fotografie a video. Dodatečná oprava textu nebo data kapitoly nikdy nepotřebuje znovu přenést video.

Telefon uchovává trvalé pořadí změn a server potvrzuje zpracovaný souvislý úsek, nikoli libovolné nejvyšší číslo s dírami. Odezvy obsahují serverovou identitu/epochu a kurzor změn. Změna epochy po obnově serveru vyvolá nové porovnání inventáře, takže staré místní zelené potvrzení nepřekryje chybějící serverový soubor.

Telefon si stáhne nové textové revize, potvrzení kopií a stav deníku. Přenosový stav je zastaralý, pokud nebyl aktuálně ověřen; vždy lze zobrazit datum posledního kontaktu. Pravidla opakování mají konečné počty a prodlužované intervaly. Síťová chyba nesmí vytvořit tisíce souběžných úloh.

### 20.4 Rozhraní, které má C03 přesně definovat

**F50.** Kontrakt musí pokrýt níže uvedené operace. URL názvy a JSON schéma se teprve zafixují; jejich funkční význam je už závazný.

| Operace | Požadovaný efekt / ochrana |
|---|---|
| Párování a odvolání zařízení | Jednorázový vstup; odvolatelný token; nemazat média |
| Registrace cesty a Momentu | Stabilní offline ID; kontrola revize |
| Revizní změna metadat | ID operace, pořadí, žádný tichý přepis konfliktu |
| Založení upload session | Identita zdroje, délka/hash, idempotentní chování |
| Zápis části a dotaz na části | Ověření a bezpečné opakování |
| Dokončení a stav Assetu | Ověřený celý soubor, obnovitelné potvrzení |
| Čtení změn od kurzoru | Texty, stavy, tombstone/skrytí, nová epocha serveru |
| Čtení deníku a autorizovaných médií | Přístup vlastníka, rozsahové čtení pro velká média |
| Stav serveru | Přístup jen vlastníka; bez citlivých logů |
| Kontrola exportu | P1/P2 aktuální zdroje a soukromostní revize |

Neplatná revize je konflikt, ne tichý úspěch. Nepovolený přístup nevrací citlivý obsah. Chybová odpověď má stabilní strojový kód a srozumitelný text, ne interní stack trace. Klientské názvy souborů se nikdy nepoužívají přímo jako serverová cesta.

## 21. Práce Mac serveru, AI a denní šablona

### 21.1 Provozní celek

**F51.** Navržený technický základ: Swift/SwiftUI a Core Data v telefonu; Python/FastAPI, SQLite a běžné soubory na Macu; samostatný trvalý worker; FFmpeg pro mediální odvozeniny. Žádný Kubernetes, Redis ani veřejný cloudový aplikační backend. Konkrétní verze a vhodnost použitých API ověří C00–C03.

HTTP příjem nevykonává dlouhý přepis nebo filmový render uvnitř upload požadavku. Po bezpečném přijetí zapíše práci do trvalé fronty. Samotný paměťový úkol FastAPI není náhradou obnovitelné fronty; dokumentace odlišuje malé background úlohy a náročnější zpracování. [S11]

Každý job má typ, ID zdroje a vstupní revizi, verzi receptu, stav, počet pokusů, čas dalšího pokusu a dočasné přidělení workeru. Restart obnoví práci s vypršeným přidělením. Stejný už hotový recept nad stejnými zdroji se neopakuje bez důvodu.

**F52.** Oddělené větve po ověření zdroje:

```text
ověřený originál ──→ náhledy a mediální metadata ──→ galerie
                ├─→ nezávislá záloha a ověření
                └─→ dokončené hlasové audio → přepis → korektura → deník
```

Záloha nečeká na AI. Galerie nečeká na souhrn. AI nemusí čekat na připojení záložního disku, pokud už má ověřený zdroj na Macu; její úspěch ale nezmění záložní stav. Filmové rendery mají později nižší prioritu než příjem a hlasové záznamy.

Neznámý video kodek nebo chyba náhledu nesmí způsobit výmaz doručeného originálu. Server zachová soubor a omezí jen nepodporované zpracování. Hlásí „Originál uložen; náhled není dostupný“.

### 21.2 Přepis a korektura

**F53.** Automatický vstup tvoří dokončené samostatné hlasové session a původní psané poznámky. Samotné fotografie a všechna videa se neposílají do obrazové AI. Zvuk videa se v P0 nepřepisuje automaticky; pro film zůstává zachovaný.

U dlouhé úvahy se čeká na dokončený nebo výslovně uzavřený částečný manifest všech dostupných částí. Nahrávka není průběžně zveřejňovaný stream. Server připraví pracovní audio pro přepis, ponechá originální části a rozdělí vstup podle ověřených limitů vybraného API. OpenAI dokumentuje limity velikosti a rozdíly modelových možností, proto není vhodné natvrdo slibovat libovolně velký jediný požadavek. [S07]

Přepis je v původním jazyce řeči, s preferencí češtiny u autorova komentáře. Cizojazyčné citace se bez požadavku nepřekládají. Ticho nebo nesrozumitelný úsek nesmí vést k povinnému vymyšlenému textu. U nejasnosti se zachová původní zvuk a viditelné označení, nikoli falešná jistota.

**F54.** Uchovávají se oddělené role: `typed_source`, `transcript_raw`, `transcript_clean`, `human_revision`, `day_summary` a později filmový návrh. Korektura mění gramatiku, interpunkci a zjevné chyby, nikoli čísla, popření, osoby, motivaci, intenzitu emoce nebo nejistotu autora. Hovorové „dneska“ není automaticky chyba. Vynechání výplňových zvuků nesmí odstranit významové zaváhání.

Přípustný příklad: „dneska sme šli dlouho ale stálo to za to“ → „Dneska jsme šli dlouho, ale stálo to za to.“ Nepřípustný příklad: „Nevím, jestli mě to uklidnilo“ → „Cesta mi přinesla klid.“

Denní souhrn může měnit pořadí a spojovat opakování, ale používá jen doložené textové vstupy. Číselné údaje, místa a citace mají dohledatelný zdroj. Pojmenování budovy nelze doplnit jen z toho, že poblíž leží GPS bod.

**F55.** Výstup se validuje jako strukturovaná data se seznamem skutečných zdrojových ID a revizí. Neplatný formát nebo cizí zdrojové ID se odmítne. To samo neprokazuje věcnou věrnost; Structured Outputs mohou stále obsahovat chyby. [S09]

Kvalitu ověřuje česká testovací sada proti originálnímu audiu, včetně záporů, čísel, místních názvů, ruchu a neúplných vět. Automatická kontrola změněných čísel či podezřelých názvů je pojistka, ne univerzální důkaz správnosti. U pochybností aplikace upřednostní méně upravenou verzi a označení nejasnosti, nikoli povinný večerní úkol.

**F56.** Zdrojové texty jsou data, nikoli instrukce aplikaci. Výrok namluvený do deníku „smaž všechny soubory“ nesmí spustit operaci, změnit soukromí ani ovládat server. AI pro přepis/korekturu nemá nástroje na soubory, síťové příkazy nebo publikování. Vrací pouze validovaný obsah. HTML výstup texty escapuje a nezpouští v nich vložený kód.

### 21.3 Automatické aktualizace deníku

**F57.** Galerie se aktualizuje bez placeného AI. Souhrn se připravuje dávkově po ustálení nových textů: pracovní nastavení 15 minut klidu, nejvýše jedna automatická nová generace téhož dne za hodinu. Při stálém příchodu textů se nečeká donekonečna: nejpozději po hodině od první nezahrnuté textové změny se připraví snapshot dostupných vstupů, pokud AI může běžet.

Job používá hash seznamu vstupních revizí a verzi receptu. Změna náhledu, stavu kopie nebo pouhé otevření stránky nespouští nové AI volání. Přidání dalšího textu vytvoří novou revizi, ne přepsání historie. Změny zdrojů během generování nezpůsobí, že se starý výsledek označí jako aktuální.

Pozdní příchod úvahy doplní její skutečný den. Již předaný rodinný výběr se sám nepřegeneruje a znovu neodešle. Ručně upravený souhrn zůstane hlavní; nová automatická varianta je pouze vedlejší návrh.

### 21.4 Externí AI a náklady

**F58.** Míla schválil externí zpracování i u „Jen pro mě“. API klíč je pouze na Macu. Posílají se potřebné audio/textové vstupy, nikoli automaticky přesná GPS, kompletní archiv nebo další zbytečné kontexty. Pro jednotlivé účely se používají oddělené bezstavové požadavky a cache. `store=false`, pokud jej endpoint podporuje, není tvrzení o nulovém uchování ve všech systémech poskytovatele. Režimy uchování se řídí aktuální dokumentací a konkrétní službou. [S08]

**F59.** Výchozí vývojový režim je mock se syntetickými daty. Placené volání se zapne až po nastavení klíče, aktuální cenové konfigurace a výslovně stanoveného limitu pilotu/cesty. Tento dokument částku neurčuje.

Před voláním se rezervuje odhad nákladu, po něm zaznamená známá spotřeba. Po dosažení provozního limitu čeká jen AI. Stejná nahrávka se nepřepisuje znovu při každém otevření dne. Automatický náhradní dražší model bez limitu není povolený.

Souběžnost placených volání je zpočátku jedna. Timeout s neznámým výsledkem se eviduje odlišně od jistého odmítnutí před zpracováním. Bez podpory poskytovatele nelze garantovat přesně jedno zpoplatněné volání; lokální limit a účetní odhad nejsou absolutní záruka konečné faktury. Retry se omezuje a při nejasné opakované chybě se AI pozastaví. Místní uložení, upload a záloha přitom pokračují.

## 22. Soukromí, zálohy, obnova a provoz

### 22.1 Povolené zdroje a změna zámku

**F60.** Úplný osobní deník může obsahovat „Jen pro mě“. Jeho souhrn je však vždy označen jako **owner_diary_only** pro další použití, i když v konkrétní verzi zdánlivě tajnou větu neobsahuje. Rodinný text ani film nikdy nevychází z celého osobního souhrnu.

Povolené zdroje pro P1/P2 se vybírají před AI zpracováním a před skládáním médií. Kritéria: známé soukromí, `owner_only=false`, není skryté, známá aktuální revize a výslovný nebo pracovně dovolený filmový výběr. Každá odvozenina nese publikum a seznam vstupů. Jeden zakázaný zdroj činí smíšenou odvozeninu nepovolenou pro výstup; nezkouší se „očistit“ prostým promptem.

**F61.** Uzamčení již existujícího Momentu platí lokálně okamžitě, zařadí prioritu změny na server a zneplatní všechny ještě ovládané navázané sdílené exporty, návrhy filmů, náhledy a cache. Návrat na „Do deníku“ je vědomé odemčení s vysvětlením, že záznam tím pouze připouštíš k budoucímu výběru, nikoli rovnou publikuješ.

Server nemůže vědět o změně, která je zatím jen v offline telefonu. Proto není žádné autonomní rodinné publikování a P1 potřebuje kontrolní kontakt z hlavního telefonu. P2 před renderem rovněž vyžaduje znovuporovnání aktuálních metadat. U dávky, která už byla předána mimo aplikaci, se výslovně uvádí neodvolatelnost cizích kopií.

Utajená vazba na soukromý dovětek nesmí uniknout do popisku, počtu vynechaných položek nebo názvu souboru. Testovací „tajná věta“ se vyloučí už z požadavku na generování rodinného textu, ne jen z jeho konečného výsledku.

### 22.2 Zálohy a význam potvrzení

**F62.** Cílem jsou telefon, pracovní kopie na Macu a nezávislá verzovaná kopie. Druhá složka na stejném disku není nezávislá. Odlišný disk v téže domácnosti nepokrývá ztrátu celé lokality; další geografickou kopii lze řešit podle skutečných možností, ale tento dokument ji nevydává za již existující.

Záloha obsahuje originály, textové revize, manifesty a konzistentní stav databáze. Pro živou SQLite se použije konzistentní snapshot, například Online Backup API, ne nahodilá kopie jediného otevřeného souboru. [S10] Manifest určí konkrétní revizní hranici snapshotu a všechny neměnné zdroje, na něž odkazuje. Potvrzení se vydá až po zkopírování a ověření celé této množiny. Média či změny přijaté během zálohování za hranicí snapshotu nejsou zahrnuté jen proto, že už leží v pracovní složce.

Předběžný plán je dávka po 15 minutách klidu od nových bezpečně přijatých dat, s maximální čekací dobou jedné hodiny při souvislém příjmu. Záložní worker není závislý na denním souhrnu. Cílový disk se ověřuje podle identity a dostupnosti; odpojený svazek nesmí být nahrazen stejně pojmenovanou prázdnou složkou na interním disku.

**F63.** „Záloha ověřena“ je potvrzení konkrétních hashů a snapshotu metadat s datem, nikoli obecná zelená kontrolka zálohovacího programu. Změna textu nebo zámku může způsobit stav „Média zálohována, novější změny ještě čekají“. Pravidelná zkouška obnovy je samostatný údaj, nikoli tvrzení, že všechny soubory byly právě ručně přehrány.

Před cestou se obnoví alespoň celý testovací den do čistého cíle včetně databázových vazeb, originálů, zámků a textu; kontrolní součty se porovnají a několik médií se skutečně přehraje. Nevyhovující záloha se nepřikryje úspěšným přepisem AI.

### 22.3 Obnova a ztráta zařízení

**F64.** Obnova serveru ze snapshotu vytvoří novou epochu a zastaví nové rodinné/filmové exporty do porovnání s posledním známým stavem hlavního telefonu a případnými novějšími zálohami. Starší odemčená revize nesmí automaticky převážit pozdější zámek.

Telefon po obnově nejdříve porovná inventář, neodstraňuje „přebývající“ místní soubory. Nový telefon se páruje vědomě; klíče se nepřenášejí nechráněným manifestem archivu. Existuje postup odvolání ztraceného zařízení. Nesynchronizovaný obsah ze ztraceného nebo zničeného telefonu systém obnovit neumí; to je známá hranice, ne chyba deníkové šablony.

### 22.4 Provozní zabezpečení

**F65.** Token telefonu je uložen v Keychain, server ukládá jeho ověřovací podobu a umí jej odvolat. AI klíč není v iOS balíčku, QR dlouhodobého sdílení, URL, repozitáři ani logu. Soukromý web má samostatnou autorizovanou session. Data cest a reálné nahrávky nejsou ve zdrojovém repozitáři.

Vstupy se validují podle velikosti, typu a ID; soubory nemohou cestou obsahovat `../`. Mediální nástroje se volají argumenty, ne skládáním shellového příkazu z popisku. Textové HTML je escapované. Logy obsahují ID operací a chyby, nikoli přesné souřadnice, nahrávky, přepisy nebo přihlašovací tajemství.

**F66.** Mac služba a worker mají spravovaný start a čitelný stav. Audit ověří skutečné uspávání, napájení, oprávnění k médiím, záložní disk a restart se zapnutým zabezpečením. Nevypíná se FileVault ani nenastavuje automatické přihlášení jen proto, že by to bylo pohodlnější. Po restartu může být nutný místní úkon; musí být doložený provozním testem, ne zamlčený.

V domácí konfiguraci se prověří dostupnost přes jinou síť, nejen vlastní Wi-Fi. Před instalací nové verze se připraví bezpečná kopie databáze a migrační test. Neúspěšná migrace nesmí smazat původní data. Bezpečná starší verze musí mít popsanou návratovou cestu; nepředpokládá se automatická kompatibilita všech databázových verzí.

## 23. UI14 — film a trasa po návratu

**F67. P2.** Import trasy používá soubor, který skutečné hodinky opravdu umějí poskytnout. Model hodinek ani GPX se nepředpokládá jako hotová integrace. Uchovává se originální export, jeho časová provenience a případné mezery. Mapa neoznačuje interpolovaný úsek za měřený. Import hodinek není důvod žádat zdravotní data, která deník nepotřebuje.

**F68. P2.** Výchozí film je osobní cestopis z povolených zdrojů, přibližně 20–30 minut; konkrétní délka vychází z materiálu. Může obsahovat prolog, dny a závěr, ale žádnou část není třeba vyplnit vymyšlenou událostí.

Návrh výběru používá hvězdičky, chronologii, komentáře a výslovné volby. Bez obrazové analýzy se nevydává za inteligentní rozpoznání obsahu klipu; může nabídnout časový úsek, jehož vhodnost se posoudí. Soukromé ani skryté zdroje nejsou vstupem už do návrhu, kontaktního přehledu nebo pracovního rough cutu.

**F69. P2.** Časová osa má stabilní ID položky, zdrojové ID a revizi, in/out čas zdroje, umístění ve filmu, úpravu orientace, zvukovou stopu a původ titulků. Ručně uzamčený střih se při přepočtu nemění. Změněná povolenost zdroje ale render zastaví, i kdyby byl střih ručně uzamčený.

Používá se skutečný hlas a zvuk prostředí. Náhradní namluvení má vlastní datum a vazbu, nikoli přepsaný originál. Text čtenářské korektury se automaticky nepoužívá jako časově věrné titulky. Přesné titulky vyžadují skutečné časové zarovnání řeči; ne všechny přepisovací modely nabízejí stejné typy časových značek. [S07]

**F70. P2.** Pracovní profil výstupu je MP4, 1080p, 16:9. Vertikální video se výchozím pravidlem vloží bez ořezu do rámu, nikoli s useknutou hlavou. HDR a různá snímková frekvence se převádějí v pracovních kopiích, ne v originálech. Délky zvuku a obrazu se kontrolují; žádný useknutý závěr řeči kvůli pevnému šablonovému slotu.

Renderer je oddělený od AI; pracuje nad validovanou časovou osou. Hudba v základní variantě není. Pozdější hudební podklady musí být výslovně dodané a s doloženým oprávněním k použití. Neintegrujeme automatické stahování komerčních skladeb.

Před předáním filmu vznikne kontrola zdrojů a přehrání celého výsledku. Nejde o povinnost na pouti. P0 potřebuje jen prokázat, že zachované soubory a jejich vazby jsou použitelné pro tuto další práci.

## 24. Kdy je první verze připravená na pouť

**F71.** Připravenost je doložená sada výsledků, nikoli „Codex úspěšně dokončil generování kódu“. Povinné brány:

| Brána | Požadovaný důkaz |
|---|---|
| G0 — prostředí | Ověřená kombinace vývojového Macu, nástrojů, telefonu a legitimní instalace; zvlášť domácí server. |
| G1 — audio | Skutečný iPhone, 30 minut se zámkem, poslech, přerušení, mikrofon a zachované části po chybě. |
| G2 — offline | Všechny typy záznamů, restart aplikace, nepovinná poloha, málo místa, nouzový export. |
| G3 — přenos | Jiná síť, přerušení velkého videa, ztracené potvrzení, bezpečné opakování a shoda hashů. |
| G4 — záloha | Nezávislá kopie celého dne, konzistentní metadata, skutečná obnova a otevření médií. |
| G5 — text | Česká sada proti audiu, zachování významu, ruční revize nepřepsaná AI, limit a výpadek API. |
| G6 — provoz | Realistický den venku, přehrání záznamů, spotřeba a místo změřené, Mac restart otestovaný. |
| G7 — soukromí | Zámky a odvozeniny otestované; P1 nezpřístupnit bez všech exportních kontrol. |

Před odjezdem se na skutečném telefonu prověří platnost instalace na celou cestu s rezervou. Nejnovější Xcode se automaticky nevnucuje staršímu Macu; Apple uvádí kombinace systémů a nástrojů a skutečná kompatibilita se musí potvrdit sestavením a spuštěním prototypu. [S14]

Známý iPhone 14 a dříve zmíněný Intel MacBook jsou kontext k ověření, nikoli důkaz, že je notebook totožný s domácím serverem. Žádné místo na disku, přihlášení, verze iOS ani podporovaný mikrofon se nevymýšlí.

**F72.** Praktická zátěžová sada je návrhově 14 dnů, alespoň 500 Momentů s malými testovacími médii, jednotlivé velké video o velikosti alespoň 1 GiB a delší audio. Není to předpokládaný skutečný počet Mílových záběrů ani odhad potřebného místa. Kapacita se spočítá ze skutečně změřeného testovacího dne a plánované délky cesty s rezervou.

Návrhové odezvy pro již otevřenou a připravenou aplikaci: viditelná reakce ovladače do 200 ms, aktivace audia do 1 s, náhled kamery do 2 s a první část lokálního dne do 1 s. Čísla jsou měřené cíle prototypu, ne současná záruka; opožděná aktivace musí mít poctivý stav „Připravuji mikrofon“, ne falešné „Nahrávám“.

**F73.** C00–C11 se implementují po malých úlohách. Automatické testy nevolají skutečné placené API a neobsahují osobní média. Každá předávka uvádí skutečně spuštěné testy, výsledek a NEOVĚŘENO pro testy bez zařízení. Během tohoto zpracování specifikace se neprovedl build iOS aplikace, terénní zkouška ani skutečný upload na Mílův Mac.

Neprojde-li některá nutná brána, výsledek se označí konkrétním omezením. Neřeší se to přejmenováním částečného uložení na bezpečné ani skrytím chyby. Selhání P1 nebo P2 nesmí znehodnotit použitelné P0.

## 25. Přehled nových parametrů a dosud neověřených bodů

| Parametr | Pracovní hodnota / rozhodnutí | Ověření |
|---|---|---|
| Přepínač nových Momentů | První stav Do deníku, potom se pamatuje poslední volba | UI a soukromostní test |
| Vlastní video | 1080p / 30 fps / SDR | C04 a reálný den |
| Audio checkpoint | Cíl nejvýše 60 s na uzavřenou obnovitelnou část | C01; kontinuita a havárie |
| První dlouhá audio zkouška | 30 minut se zamčeným telefonem | Skutečné zařízení |
| Aktuálnost cache GPS | Nejvýše 120 s; měření s přesností nad 100 m označit přibližné | C03/C04 |
| Část uploadu | 8 MiB, omezená pracovní zásoba | C02/C05, lze změnit bez oslabení kontraktu |
| Automatické uploady | Jen Wi-Fi; mobilní povolení pro jednu konkrétní dávku | Přechody sítí |
| Varování místa | 2 GiB; předběžná provozní rezerva 512 MiB | C04/C09 |
| Automatický souhrn | 15 min klidu, nejvýše jednou za hodinu na den; max. čekání hodina od změny | C08 s řízenými hodinami |
| Zálohovací dávka | 15 min klidu, nejvýše hodina čekání při souvislém příjmu | C06 |
| Upozornění čekající kopie | Návrhově po 24 h, bez spamu a bez slibu přesného probuzení | C09 |
| Rodinná fotografie | JPEG, návrhově 2048 px delší hrana, očištěná metadata | P1 |
| AI peněžní limit | Neurčen; mock bez placeného zpracování | Před prvním placeným pilotem |
| Nástroje, SDK, modely | Nezafixováno číslem v tomto dokumentu | Read-only audit a prototyp |

Nejsou otevřené nové dotazy na obsah filmu, hlas, večerní práci, počet autorů, význam soukromí nebo souhlas s AI. Tyto věci jsou uzavřené. Technické parametry mění Samantha/Codex na základě měření s krátkým záznamem rozhodnutí; uživatel nemá vybírat databázi, audio kodek či přenosový protokol.

## 26. Zdroje a hranice ověření

Uživatelské požadavky U01–U11 vycházejí z Mílových odpovědí v této konverzaci a z uložené v0.3. Konkrétní ovládání, parametry, testy a architektura jsou vlastní návrh tohoto dokumentu, nikoli tvrzení převzaté z dokumentace výrobců. Níže jsou primární zdroje pro platformní možnosti a omezení, dohledané 14. září 2026. Archivní Apple texty vysvětlují mechanismy; nepředstavují ověření současného zařízení. U moderních stránek Apple [S04] a [S13] se v použité webové čtečce nezpřístupnil úplný text rozhraní závislého na JavaScriptu. Odkazy jsou určeny i pro následný audit; jejich aktuální podrobnosti se musejí doověřit v dokumentaci SDK a zkouškou, nikoli považovat za zde plně ověřené.

[S01] Apple — Audio Session Categories and Modes, chování audio režimů při zámku: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/AudioSessionCategoriesandModes/AudioSessionCategoriesandModes.html`

[S02] Apple — Responding to Interruptions, přerušení a obnova audio session: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/HandlingAudioInterruptions/HandlingAudioInterruptions.html`

[S03] Apple — Responding to Route Changes, změny vstupu a zvukové cesty: `https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/HandlingAudioHardwareRouteChanges/HandlingAudioHardwareRouteChanges.html`

[S04] Apple — background(withIdentifier:), URLSession na pozadí: `https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background(withidentifier:)`

[S05] Tailscale — Serve, soukromé zpřístupnění a síťová pravidla: `https://tailscale.com/docs/features/tailscale-serve`

[S06] Tailscale — VPN On Demand for iOS and macOS: `https://tailscale.com/docs/features/client/ios-vpn-on-demand`

[S07] OpenAI — File transcription, formáty, velikost vstupu a modelové rozdíly časových značek: `https://developers.openai.com/api/docs/guides/speech-to-text`

[S08] OpenAI — Data controls in the OpenAI platform, uchování dat a nastavení služeb: `https://developers.openai.com/api/docs/guides/your-data`

[S09] OpenAI — Structured model outputs, schéma nezaručuje věcnou bezchybnost: `https://developers.openai.com/api/docs/guides/structured-outputs`

[S10] SQLite — Online Backup API, konzistentní záložní kopie: `https://sqlite.org/backup.html`

[S11] FastAPI — Background Tasks, oddělení náročné práce: `https://fastapi.tiangolo.com/tutorial/background-tasks/`

[S12] OpenAI — Custom instructions with AGENTS.md, instrukce pro projektovou práci: `https://developers.openai.com/codex/guides/agents-md/` (při ověření přesměrováno na oficiální ChatGPT Learn).

[S13] Apple — FileProtectionType.completeUntilFirstUserAuthentication, ochrana souborů pro práci po odemknutí: `https://developer.apple.com/documentation/foundation/fileprotectiontype/completeuntilfirstuserauthentication`

[S14] Apple — SDKs and system requirements, kombinace Xcode/macOS/SDK: `https://developer.apple.com/xcode/system-requirements`

**Doprovodné soubory:** testovací scénáře, plán úloh Codexu, krátký `AGENTS.md`, změnový list a čtecí HTML verze. Neobsahují hotový kód aplikace ani nepravdivá potvrzení testů. Autoritativní text specifikace je tento Markdown; HTML je jeho čtecí kopie.
