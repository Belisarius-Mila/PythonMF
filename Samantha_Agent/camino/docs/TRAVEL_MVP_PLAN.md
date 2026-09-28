# Camino — minimalistický cestovní plán

Rozhodnutí Míly: 2026-09-25. Cesta 3.–17. října 2026; cílové zmrazení 2. října.
Novější rozhodnutí 27. 9.: **GPS neodkládat**, pouze nové okamžiky.
Novější rozhodnutí 28. 9.: Míla schválil **Mapu cesty ve Vieweru** (U17).
Lokálně implementováno, bez změny telefonu; dosavadní odklad mapy níže je
historický. Samostatná stránka, aktuálně povolené body, orientační spojnice,
den/celá cesta a odkazy do deníku; žádné průběžné sledování nebo kilometráž.
Ověření a další krátká přejímka: [VIEWER_ROUTE_MAP_REPORT.md](VIEWER_ROUTE_MAP_REPORT.md).
Nasazení serveru samostatně. B04 mazání dál pouze buffer. Jana podle Míly
použila dosavadní Viewer ze svého Macu přes Cockpit; nikoli PASS nové mapy/G8.
28. 9. 23:04: po samostatném souhlasu a globální brzdě U17 nasazená z ce903913bb35.
HTTPS mapa/JSON/assety a 9 povolených GPS bodů/odkazy PASS; archiv i přístupy
zachované. Bez nové IPA/push/restartu Cockpitu. Nyní krátká fyzická zkouška
mapy; Safari, externí dlaždice a nový bod po přenosu zatím NEOVĚŘENO.
28. 9. 23:09: Míla potvrzuje výborné fungování mapy, základní fyzická přejímka
U17 PASS. Konkrétní platformy a okrajové scénáře neuvedené; dál používat
stejnou verzi, pro dnešek konec práce bez dalšího nasazení.
Novější večerní rozhodnutí 27. 9.: po fyzickém potvrzení názvů a přenosu buildu 7
jediný společný B03 balíček: názvy každé foto/video/audio přílohy, nejnovější
okamžiky nahoře pouze v telefonu, počty příloh, rozbalovací Viewer nadále
od rána k večeru. Potom delší testování stejné verze, drobnosti do bufferu,
bez rychlého vydávání dalších verzí; kritické chyby se dál opravují.
Mac editor odložený. [TITLES_AND_TRANSFER_STATUS_REPORT.md](TITLES_AND_TRANSFER_STATUS_REPORT.md)
je aktuální rozsah, důkaz a krátká přejímka; nasazení/podpis/instalace samostatně.
Build 6 fyzicky funguje: GPS marker/foto/komentář/video uložené a přenesené;
Mac 48 Momentů / 5 GPS. Zbývající okrajové scénáře nejsou PASS a nyní
neblokují požadovaný přechod na Viewer. [GPS_CAPTURE_REPORT.md](GPS_CAPTURE_REPORT.md)
rozlišuje jednotlivé důkazy.
27. 9. 15:17: Viewer včetně mapového odkazu U16 nasazený z 125fddbbcb56,
grant pro Janu povolený a Cockpit odkaz nastavený po výslovném souhlasu
a globální brzdě. [VIEWER_MAP_REPORT.md](VIEWER_MAP_REPORT.md): cíleně
45/45, plná brána 1833/1833, Cockpit smoke 5/5; HTTPS a média ověřené.
27. 9. 15:27: Míla potvrzuje základní funkčnost Vieweru. RT3 částečně,
nikoli celý PASS; zařízení/jiná síť a mapový klik nejsou samostatně doložené.
Další krátká zkouška s Janou a fyzický RT4 (skrytí), potom M3 nezávislá záloha
a M4 cestovní přejímka. Vlastní mapa/trasa odložená.

Historický stav před GPS krokem:
Aktualizace 26. 9. 23:19 CEST: server a iPhone build 5 nasazené, fyzické
dokončení obnovy i stav po novém otevření PASS. Následný komentář: telefon
42 úplných, Mac 42 Momentů / 46 médií; původní archiv zachovaný, oba flagy=false.
Viewer stále nepovolený. Další je povolení Vieweru/RT3/RT4, potom M3/M4.
Podrobnosti a hranice důkazu: [M2_RECOVERY_REPORT.md](M2_RECOVERY_REPORT.md).

Historický stav před večerní přejímkou:
Stav k 26. 9.: M1 lokálně funguje podle potvrzení Míly; M2a runtime/odkaz,
M2b pořadí audia a M2c provozní ovládání jsou lokálně implementované,
Camino služba a soukromé HTTPS od 26. 9. 13:27 běží nad původním archivem
po potvrzené globální brzdě. Schéma 3, data hashově zachovaná, owner API
ověřené i po stop/start. Viewer není povolený; obnova po T058 stále blokuje
zápis a export. Nové provozní ovládání je zatím lokální, bez nového p+n.
Podrobnosti: [M2c_SERVICE_REPORT.md](M2c_SERVICE_REPORT.md)
a [M2b_AUDIO_LAYOUT_REPORT.md](M2b_AUDIO_LAYOUT_REPORT.md).

Navazující lokální krok 26. 9.: [M2_RECOVERY_REPORT.md](M2_RECOVERY_REPORT.md)
doplňuje výslovné dokončení obnovy pro shodné úplné kopie. Rozdíly neslučuje;
živou blokaci dosud nemění. Další je samostatné nasazení serveru a stejné
podepsané iPhone appky, poté jeden společný průchod, ne opakování celé T058.

Aktualizace M1 dne 25. 9.: lokální implementace a syntetické testy jsou
v [M1_VIEWER_REPORT.md](M1_VIEWER_REPORT.md). Míla náhled potvrdil jako funkční;
živý provoz nespouštěn. Původní mezera v pořadí audia je řešená lokálním M2b:
samostatná metadata návaznosti, automatické pokračování souvislých úseků a
viditelná pauza s ručním pokračováním. Telefon ještě není aktualizovaný.

## Co nyní stavíme

Soukromou osobní aplikaci pro tuto cestu, ne produkt pro prodej. Zachováme
funkční záznam a přenos z iPhonu. Jana otevře v Cockpitu **Otevřít Camino**
a uvidí jednoduchý český HTML přehled doručených záznamů po dnech: text,
fotografie, přehrání komentáře a videa. Nemusí instalovat další naši aplikaci.
Použije již zamýšlený soukromý přístup; žádný veřejný web.

Tento dokument je novější rozhodnutí o rozsahu, pořadí a cestovní akceptaci.
V těchto věcech nahrazuje původní široké P0 a lineární pořadí C06 → C07 → C08
ve v0.5. U15 a ochrana dat zůstávají závazné. Importované podklady v0.5 se
nepřepisují. Detailní technické volby níže jsou Adamův návrh realizace tohoto
minimalistického cíle; nejsou tvrzením, že je Míla jednotlivě specifikoval.

## Nejmenší architektura

`iPhone → existující Camino API a archiv na Macu → viewer_safe → HTML pro Janu`

- Znovu použít C03/C05 a jejich ověřené přenosy. Žádný nový přenosový protokol,
  databázová migrace telefonu ani přepis recorderu kvůli Vieweru.
- Jedna malá serverová HTML šablona + CSS, nejvýše nezbytný JavaScript;
  žádný nový frontendový framework, CMS, víceuživatelský editor nebo cloud.
- Viewer dostane vlastní URL a read-only autorizaci oddělenou od owner API.
  Cockpit bude jen odkaz a stručný stav, ne úložiště ani generátor obsahu.
  Přímá záložka bude fungovat i při výpadku Cockpitu.
- Pro MVP může Viewer obsluhovat tentýž proces jako Camino API na loopbacku.
  Tím se výslovně zjednodušuje starší požadavek samostatného Viewer procesu
  (D11/F80); společný výpadek API a Vieweru je přijaté návrhové omezení.
- Jeden jednoduchý obnovitelný mediální proces/periodický běh, ne obecná AI
  job infrastruktura. Nové deriváty a HTML publikovat až po dokončení;
  neúspěch ponechá poslední platný výstup a pravdivý stav.
- Po přijetí změn automaticky doplnit příslušný den; pro malý objem stačí
  periodická kontrola revizí s pracovním intervalem 60 s. Bez pevné dvojice
  večerních/ranních rebuildů, WebSocketů a Mílovy ruční večerní redakce.
  Interval je návrh, ne garance doby zpracování videa.

## Obsah Vieweru a nepřekročitelné minimum

- Index dnů a jednoduchý detail dne v časovém pořadí. Jen dostupný lidský text;
  bez přepisu ukázat audio s přehrávačem, ne čekat na AI. Bez vlastní mapy
  a souhrnů; nově schválený jednoduchý odkaz na místo doplnit před odjezdem.
- Jedna velikost očištěné foto kopie, lazy loading; jeden kompatibilní video
  proxy profil s posterem a posunem přehrávání; kompatibilní audio odvozenina
  zachovávající pořadí a mezery nahrávky. Originály neměnit ani veřejně vydávat.
- Použít pouze aktuální přijaté `diary` revize povolené cesty, neskryté,
  bez konfliktu. `Jen pro mě` nesmí do HTML, počtů, náhledů ani playlistu.
- Každý výdej HTML i média respektuje aktuální oprávnění. Po přijatém zámku
  nesmí stará URL vydat obsah; nestačí jej schovat v nové stránce. Text
  escapovat, necachovat soukromý obsah veřejně, žádné tokeny v URL.
- Jen soukromé HTTPS/Tailscale, samostatné read-only oprávnění Jany, žádný
  Funnel. Odkaz z Cockpitu není sám o sobě autorizace.
- Ukázat poslední aktualizaci a čekající povolená média; netvrdit, že server
  zná všechny záznamy telefonu. Již stažené cizí kopie nejdou odvolat.
- Originály, současné revize, hashové ověření a existující obnovu přenosu
  zachovat. Žádné automatické mazání. Méně funkcí není méně ochrany soukromí.

## Pořadí práce a podmínky hotovo

| Krok | Nejmenší výstup | Přijetí |
|---|---|---|
| M1 — Viewer lokálně (výběr C08c/d, minimum C06a) | Projekce, HTML dnů, foto/audio/video, read-only výdej; syntetická data bez živé služby | Cílené testy soukromí/autorizace a jeden prohlížečový smoke; všechny čtyři typy obsahu použitelné |
| M2 — cesta k Janě (minimum C06a/c + C08e/f) | Spravovaný Camino proces, privátní přístup, Cockpit odkaz a přímá URL; využít stávající upload | Jediný průchod iPhone → Mac → Jana z jiné sítě, krátce Safari MacBook+iPhone a návrat služby po ukončení procesu |
| M3 — jednoduchá záloha (minimum C06b) | Konzistentní databázový snapshot + neměnná média na ověřený jiný disk, verzované dávky bez automatického mazání | Obnovit jeden malý testovací den do nového cíle, porovnat hashe a otevřít médium; nikdy neobnovovat přes živá data |
| M4 — předodjezdový průchod (výběr C09) | Jeden běžný krátký venkovní pokus, kontrola místa, podpisu a stručný návod pro oba | RT1–RT6 níže s konkrétními omezeními, freeze nejpozději 2. 10. |

M2c připravilo registrované provozní ovládání a samostatné povolení Vieweru.
Další krok je schválená nasazovací příprava nad vybraným existujícím archivem,
ne AI a ne opakování všech iPhone testů. Chybějící krátkou kontrolu stavů C05c
spojíme s M2/M4. M1 zahrnuje média v jednoduché podobě, nikoli plný C08 ani
nový owner web. Po M1 žádné kosmetické rozšiřování. M2a připravilo worker a
Cockpit odkaz nezávisle na iOS; M2b doplnilo pořadí audia. Před ostrým použitím
záloha metadatové DB, nasazení serveru, poté podepsaná aktualizace telefonu
a jeden společný průchod. M2b nemění recorder ani Core Data schéma telefonu.

Pro M3 nejdřív ověřit existující nezávislý cíl a kapacitu; žádný automatický
nákup ani domněnka, že záloha repozitáře obsahuje Camino. Stačí denní dávka
a ruční spuštění při potřebě místo složitého 15min plánovače. Při nedostupném
disku může Viewer dál fungovat, ale stav zůstane „další záloha neověřena“.
Chybějící cíl je konkrétní otevřená podmínka předcestovní ochrany, ne důvod
zablokovat lokální M1. Pro iPhone nepředstírat neimplementovanou zelenou osu.

## Aktivní buffer B04 — skutečné mazání, 28. 9. 2026 13:23 CEST

Míla potvrzuje používání a základní funkčnost buildu 8. Nejde o samostatný
PASS všech scénářů B03/B01. Výslovně nyní pouze sbíráme změny; žádný vývoj,
nasazení, podpis, instalace ani mazání dat nejsou tímto zadáním povolené.

**Požadavek Míly:** každý komentář, Úvaha, fotografie a video musí být
smazatelné, aby nepovedené záznamy nezabíraly paměť telefonu. Nejde o dnešní
Skrýt z deníku, které originály zachová a místo neuvolní.

**Adamův návrh, dosud nikoli schválené provedení:**

- V detailu celé položky i jednotlivé přílohy nabídnout Smazat s potvrzením
  přesného rozsahu. Samostatná fotka/video/komentář i Úvaha; v seskupeném
  Momentu smazat jen vybranou přílohu, ostatní ponechat. Celý Moment má
  samostatnou volbu s výčtem obsahu. Hlasový komentář = celá session, všechny
  její technické segmenty; nesmazat jinou session. Prázdný rodič se nemaže skrytě.
- Po potvrzení odstranit odpovídající místní obsah včetně jeho odvozenin,
  aby se místo skutečně uvolnilo i offline. Žádný mediální koš v telefonu,
  který dál zabírá stejné místo. U dosud nepřeneseného originálu výslovně
  upozornit na nevratnou ztrátu jediné kopie. Záznam právě pořizovaného média
  nejdříve bezpečně ukončit; nesmazat soubor používaný recorderem/uploaderem.
- Nejdříve trvale uložit malý identifikátor/revizi smazání, potom uvolnit
  soubory; dokončení úklidu musí přežít pád. Ponechat potřebnou synchronizační
  historii, ne velká média. Přenos smazané přílohy už nezačínat/pokračovat;
  nesmí být vyžadováno její doposlání jen proto, aby server přijal smazání.
- U již přenesené nebo rozpracovaně přenášené položky odeslat záznam smazání
  v další povolené dávce. Offline stav poctivě Smazáno v telefonu · čeká na Mac.
  Teprve potvrzený příjem serverem znamená odstranění z Vieweru; ne samotné
  stisknutí tlačítka. Žádné zpětné přenášení smazaného obsahu do telefonu.
- Mac promítne smazání do HTML, názvů, počtů, mapových bodů a všech souvisejících
  mediálních výdejů. Smazání přílohy nesmí odstranit nezávislou polohu nebo
  ostatní obsah rodiče. Staré URL už nesmí vydat smazanou přílohu. Po obnovení
  stránky Jana položku neuvidí; již načtené/stažené kopie nelze vzdáleně odvolat.
- Opakování stejné dávky musí být neškodné, starší create/title/layout ani
  opožděný upload nesmějí smazání přebít. Zohlednit již uložené přesné obálky,
  pořadí revizí, přerušený upload a obnovu staré serverové zálohy; nesmazat
  synchronizační důkaz předčasně. Kompatibilní server musí být nasazený první.
- Pro nejmenší první variantu ponechat již přenesené originály v neveřejném
  archivu Macu, ale odstranit je z aktivního deníku/Vieweru. Jana nemá právo
  mazat. Toto uvolní telefon, nikoli disk Macu. Trvalý výmaz také z Macu,
  derivátů a politika historických záloh vyžadují zvláštní rozhodnutí; návrh
  nic neslibuje o výmazu již existujících záloh. Druhá funkce Uvolnit jen
  telefon a ponechat v deníku je odlišná a není součástí tohoto bufferu.

**Hranice:** dosavadní ochrana neměnných originálů a zákaz automatického
mazání platí dál. Před implementací výslovně schválit výjimku pro konkrétní
uživatelem potvrzené smazání; žádný automatický úklid podle stáří/kapacity.
28. 9. 2026 13:40 CEST Míla souhlasí s ponecháním již přeneseného originálu
v neveřejném archivu Macu; stále jde jen o buffer, ne pokyn k implementaci.
Mazání je
citlivější změna persistence a synchronizace, nikoli kosmetická změna Vieweru.

**Budoucí cílené ověření:** nepřenesená položka offline a reálné uvolnění
místa; přenesená položka a další dávka/Viewer včetně staré URL; příloha mezi
ostatními a komentář z více segmentů; restart během úklidu/přenosu; opakovaná
dávka a starší operace bez návratu obsahu; obnova serverové zálohy a nedostupný
Mac. Text/Úvaha bez mediálního souboru také musí zmizet ze všech aktivních
pohledů. Testy nyní neprovádíme, jde jen o návrh budoucí přejímky.

## Historický buffer — 27. 9. 17:53 CEST

Novější rozhodnutí 27. 9.: Míla schválil implementaci telefonu/názvů a B01.
Jednosměrně iPhone → Mac → Viewer; opravy názvů na Macu později, bez návratu
do telefonu, pouze pro Mílu. Stav lokální implementace a testů:
[TITLES_AND_TRANSFER_STATUS_REPORT.md](TITLES_AND_TRANSFER_STATUS_REPORT.md).
Aktualizace 27. 9. 20:35 CEST: server 403180320849 nasazený, živé ověření
názvů/Vieweru a zachování archivu PASS; podepsané IPA build 7 připravené.
Fyzický SideStore import a krátká přejímka čekají. Žádný nový push.
Následuje původní buffer; novější rozhodnutí nahrazuje jeho otevřené otázky.

- **B01 — zavádějící Čeká na Wi-Fi po úspěšné mobilní dávce.** Po ověření
  posledního média se mobilní grant správně zruší, ale následná synchronizace
  kontroluje grant dřív než prázdnou frontu. Také networkChanged nastavuje
  čekání bez kontroly zbývající práce. Snímek telefonu hlásil čekání,
  zatímco originál videa už měl na Macu ověřenou velikost a SHA-256.
  Oprava odložená do společného buildu; nejde o důkaz ztráty videa.
  Zachovat omezení souhlasu na konkrétní dávku. Návrh přidruženého UX:
  zřetelné úplné/čekající počty a rozlišení dokončené dávky od nových položek,
  které souhlas nemají. Při nejistém výsledku se nesmí zobrazit falešné ověření.
- **B02 — nepovinné editovatelné názvy.** Záměr k návratu, ne schválená
  implementace. Název zadat/změnit v telefonu offline bez zdržení pořízení,
  přenést a zobrazit ve Vieweru. Míla upřesnil: nepojmenované položky chce
  později doplňovat on na Macu, nikoli Jana. Jana zůstává read-only.
  Aktualizované řešení: jeden název celého Momentu; návrat z Macu není požadovaný.
  Budoucí oddělený owner editor má lokální přepis názvu s předností před novým
  importem. Samostatné názvy připojených médií a Mac editor nyní nevznikají.
- **Společná krátká přejímka:** stará data po aktualizaci; nový offline
  název a jeho změna po restartu/přenosu; dokončená mobilní dávka bez falešného
  čekání; později přidané médium bez zděděného souhlasu; nedostupný Mac nesmí
  znamenat ověřeno; soukromý název nesmí do Vieweru. Podle dostupných podmínek
  připojit odloženou kontrolu GPS bez fixu/přibližné polohy a offline zachování
  u média. Neprovedené varianty zůstanou NEOVĚŘENO.

Návrh: jediný společný iOS build, podpis a aktualizace zachovávající data až
po schválení rozsahu. Samotné pozdější webové úpravy nevyžadují novou IPA,
pokud se nemění telefonní datový/synchronizační kontrakt. M3 nezávislá záloha
a M4 cestovní návod/podpis mají pokračovat samostatně, bez čekání na názvy.
Žádná AI, vlastní mapa trasy, nový export ani přepis synchronizace navíc.

## Co odkládáme

- C07: AI přepisy, korektury, rozpočtový worker a T038/T055 s reálnou AI.
  Lze je doplnit později nad uloženými zdroji, bez blokování Vieweru.
- C08a/b: bohatý owner archiv a automatické denní souhrny. Jana zatím čte
  napsané texty a poslouchá komentáře; mluvený komentář nebude automaticky text.
- C04c/e: rozšířený import a plný nouzový export, pokud nejsou už hotové;
  nepředstírat jejich existenci. Riziko: bez Macu a bez funkčního podpisu není
  doložená samostatná cesta vytažení všech dat z telefonu.
- QR párovací komfort, serverová hvězdička, složitý dashboard, obecné migrace,
  plná automatizace obnovy, nepoužité varianty kodeků a rozsáhlá optimalizace.
- P1 sdílení, P2 film/trasa, komerční produkt, App Store review, placené
  členství Apple a oficiální distribuční proces. Technický podpis iOS je
  nadále nutný; žádná „certifikace“ nenahrazuje jeho obnovu.
- Kompletní zátěžová matice, opakované dlouhé audio testy, úmyslné zaplnění
  telefonu, simulace všech havárií a captive portal bez dostupné vhodné sítě.
  Neprovedené scénáře zůstávají NEOVĚŘENO/ODLOŽENO, nikdy dodatečně PASS.

## Levnější testy a práce

- Jeden funkční celek na krok; předem určit jeho cílené testy, potom jedna
  stručná předávka a lokální commit. Neopakovat již úspěšné nezměněné testy.
- Dokumentace: odkazy, soulad stavů, `git diff --check` a rychlá statická brána;
  bez iOS buildu a bez kompletní aplikační sady kvůli samotnému textu.
- Běžné UI/HTML: jen dotčené testy a jeden smoke. iOS build/instalace jen při
  změně iOS části; serverový Viewer sám nevyžaduje nový podpis telefonu.
- Soukromí/autorizace: vždy malá automatická sada s tajnou syntetickou větou,
  zakázaným přístupem, novým zámkem a starou URL. Tuto ochranu neškrtáme.
- Změna persistence, záloh, závislostí či provozního workflow nadále spouští
  povinnou plnou projektovou bránu podle kořenového AGENTS. Totéž publikační
  brány při schváleném push/deploy. Tento plán je neobchází a nemění jejich kód.
- Fyzicky jeden sdružený průchod, ne každá větev zvlášť. Chybu opravit a
  zopakovat dotčenou část. Mikrofon/hovory znovu jen při zásahu do audia.
- Na další tah číst tento plán, aktuální krátký stav a dotčené soubory;
  nerozebírat znovu celé historické vlákno. Bez paralelních agentů a nových
  obecných frameworků. Úspora je v menším rozsahu, ne ve slibu konkrétního %.

### Cestovní přejímka RT1–RT6

1. **RT1 záznam/data:** offline krátké foto, video, audio a text, znovu otevřít
   a přehrát; staré záznamy dostupné. Dřívější relevantní PASS zůstávají důkazem.
2. **RT2 přenos/stavy:** jedna malá dávka, dokončení ověřené Macem; v témže
   průchodu zbývající C05c osy a pause. Neopakovat celý přijatý C05b.
3. **RT3 Jana:** Cockpit odkaz i přímá URL, jiná síť, Safari MacBook+iPhone,
   text/foto/audio/video a pozdě doručená položka po obnovení stránky.
4. **RT4 soukromí:** jeden `Jen pro mě` se nikde neobjeví; zveřejněný testovací
   Moment po doručení zámku zmizí a stará mediální URL je odmítnuta.
5. **RT5 provoz/záloha:** návrat spravovaného procesu, nezávislá kopie a jedna
   izolovaná obnova dne; písemně počítat s místním odemknutím po restartu Macu.
   Bez místního člověka po výpadku může být Viewer dočasně nedostupný.
6. **RT6 podpis:** další obnova SideStore před cestou a kontrola posunu data
   profilu + spuštění původní aplikace s daty. Nedělat z ní záruku do 17. 10.

Jde o přijetí zúženého cestovního MVP, nikoli úplných historických G0–G8.
Blokátory: ztráta dat, únik soukromého obsahu, nefunkční hlavní záznam/přenos,
nepoužitelný Viewer nebo neřešená instalace. Krátký výpadek Macu, ruční retry,
pomalejší video a chybějící AI jsou známá přijatelná omezení. Nepředstírat
záruku dostupnosti; bez odeslání zůstává jediná kopie nových dat v telefonu.

## Podpis a aktuální důkazy k 25. září

Míla potvrdil úspěšný SideStore import s odpojeným kabelem, otevření původního
Camina a zachování/přehrání dat. Protokol druhého pokusu v 20:27 potvrzuje
instalaci stejného ID `cz.pythonmf.camino.app` a nový profil do 2. 10. 20:27 CEST.
Datum je z podpisového/instalačního logu, ne extrakce profilu běžící aplikace.
První pokus s přidanou příponou selhal na limitu aplikací; nefunkční druhá
ikona pravděpodobně zůstala po něm. Nic nemažeme a nezaměňujeme ji s originálem.

Prozatím obnovovat opakovaným importem stejného IPA, přesné ID a **Append Team
ID vypnuto**, ne neověřeným Refresh All. Zdrojová inspekce použité SideStore
verze našla riziko změny ID při běžném Refresh; není to doložený runtime FAIL.
IPA ponechat lokálně v telefonu. Další kontrola 1. 10.; navržené rezervní dny
obnovy 6., 11. a 16. 10., vždy podle skutečně získané platnosti. Jde o návod,
ne vytvořené připomínky. Selhání SideStore/párování může vyžadovat Mac; při
problému nemaž aplikaci s daty. Před odjezdem volbu znovu prakticky zhodnotit.

## Oprávnění a nejbližší zadání

M1, M2a, M2b a M2c implementují lokální kód a syntetické testy. Nenasazují službu,
nespouštějí osobní upload, nemění Serve/ACL, nepublikují média a nic nekupují.
Push, deployment, instalace služby a zpřístupnění skutečných dat zůstávají
odděleně potvrzované kroky. Nasazovací příprava a výběr stávajícího archivu
byly následně schválené a provedené. Globální brzda pro instalaci služby/Serve
byla přijata a instalace ověřená. Dokončení shodných kopií je lokálně doplněné;
server i stejná iPhone aplikace jsou následně nasazené a dokončení T058
fyzicky ověřené. Další je **samostatné povolení Vieweru a RT3/RT4 pro Janu**.
M2c runbook vyžaduje trvalý Python, ověřený checkout, existující owner token
a konkrétní trip/server ID/epochu. Schéma 3 přidává offline grant cesty;
ověřený snapshot před upgradem není nezávislá záloha M3.
