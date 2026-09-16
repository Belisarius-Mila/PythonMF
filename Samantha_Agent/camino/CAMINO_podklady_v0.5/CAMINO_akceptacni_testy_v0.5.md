# Camino — akceptační scénáře v0.5

**Datum:** 16. září 2026. **Stav všech níže uvedených scénářů:** NEPROVEDENO. Jde o zadání testů, nikoli zprávu o funkčnosti aplikace.

Navazuje na `CAMINO_funkcni_specifikace_v0.5.md`. Značky F odkazují na její funkční pravidla. **A** = automatizovatelný test logiky, **I** = integrační test procesů a úložišť, **D** = skutečné zařízení / fyzická zkouška. Kombinace znamená, že softwarový test nenahrazuje zařízení.

Pro každý provedený test zaznamenat verzi klienta/serveru, skutečné zařízení a systém, vstupní podmínky, provedené kroky, očekávání, skutečnost a důkaz. Výsledek je PASS / FAIL / BLOCKED / NEPROVEDENO; bez důkazu nepoužívat PASS. Testy pracují se syntetickými médii nebo výslovně určenými testovacími nahrávkami. Automatické běhy používají mock AI; skutečný placený pilot je samostatný schválený krok.

## Příprava a rychlé zachycení

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T001 | P0 · A,D | F07 | Bez sítě vytvořit zkušební cestu, pak skutečnou; změnit aktivní cestu. | Obě mají různá ID; obsah se nemíchá; bez serveru lze zaznamenávat. |
| T002 | P0 · D | F08 | Postupně odmítnout kameru, mikrofon, polohu a oznámení; ostatní ponechat. | Každé odmítnutí omezí jen nutnou funkci; není nucené opakování všech dialogů. |
| T003 | P0 · A,I,D | F09,F65 | Použít platný, prošlý a znovu použitý párovací údaj; odvolat zařízení. | Platný funguje jednou; neplatný neudělí přístup; místní média zůstávají. |
| T004 | P0 · A,D | F10,F44 | Rychle dvakrát klepnout na Komentář při startu mikrofonu. | Jedna session a jeden Moment; stav Připravuji není označen Nahrávám. |
| T005 | P0 · A,D | F02,F10 | Zapnout režim Jen pro mě, uložit, vrátit se a aplikaci restartovat. | Nové záznamy zůstávají zamčené do ruční změny; staré Momenty se nemění. |
| T006 | P0 · A,D | F11 | Označit okamžik bez média, pak zvlášť označit hvězdičkou starší Moment. | Dvě různé akce; značka má čas a režim, sama nezapne mikrofon. |
| T007 | P0 · I,D | F12,F42 | Pořídit fotografii a simulovat chybu dokončení zápisu. | Hláška Uloženo až po zápisu; při chybě se předchozí média nemažou. |
| T008 | P0 · A,D | F01,F21,F38 | Uložit dva rychlé snímky, přidat komentář k prvnímu a další foto do jeho detailu. | Dva samostatné Momenty; explicitní přílohy patří prvnímu; stabilní ID. |
| T009 | P0 · D | F08,F12 | Otevřít Foto bez povolené kamery. | Jasné vysvětlení a návrat; audio a deník dále fungují. |
| T010 | P0 · A,I | F03,F24 | K nahrávce vytvořit korekturu a ruční revizi; zkontrolovat původní soubor. | Hash originálu je stejný; původní text i další revize dohledatelné. |

## Video, audio a skutečný mikrofon

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T011 | P0 · I,D | F13,F44 | Natočit klip, Stop, ihned přejít na hlavní obrazovku a znovu otevřít. | Dokončený klip přehratelný; čas a zvuk správné; nevzniknou duplicity. |
| T012 | P0 · I,D | F13 | Natočit nebo importovat video na výšku a na šířku. | Obě orientace uložené správně bez nevratného ořezu; metadata zachována. |
| T013 | P0 · D | F14 | Zakázat mikrofon při povolené kameře a zvolit výslovně video bez zvuku. | Před Start i při nahrávání viditelné Bez zvuku; žádný skrytý fallback. |
| T014 | P0 · D | F14 | Během videa zamknout telefon, opustit aplikaci a samostatně vyvolat přerušení. | Pokus o dokončení, po návratu pravdivý úplný/částečný stav; žádný slib běžící kamery. |
| T015 | P0 · I,D | F15 | Nahrát krátký komentář i úvahu, ukončit a přehrát. | Správný typ, skutečný čas, příslušný Moment; bez povinného názvu a schválení. |
| T016 | P0 · D | F16,F18 | Na skutečném telefonu nahrávat 30 minut, většinu se zamčenou obrazovkou. | Celý skutečně zachycený průběh přehratelný, návaznost částí doložená poslechem a časem. |
| T017 | P0 · D | F16 | Nahrávat vestavěným mikrofonem, ověřit jeho označení a slyšitelnost řeči. | UI ukazuje skutečný vstup; sluchátka nejsou nesprávně deklarována jako nutná. |
| T018 | P0 · D | F16 | Otestovat dostupná sluchátka při stání i chůzi se zamčeným telefonem. | Slyšitelný hlas a skutečně vybraný vstup; zaznamenat omezení větru i připojení. |
| T019 | P0 · D | F17 | Vyvolat příchozí hovor, jednou ignorovat a jednou přijmout. | Zachovaný dosavadní zvuk, jasné přerušení; žádný záznam hovoru a samovolné pokračování. |
| T020 | P0 · D | F17 | Odpojit a připojit aktivní mikrofon za běhu nahrávání. | Nezůstane falešné Nahrávám; pokračování až po akci, nová část s označenou mezerou. |
| T021 | P0 · A,D | F15,F16 | Při úvaze chtít spustit video, přehrávání a jinou úvahu; přepnout jinam a zpět. | Ne soupeřící dvě session; návrat k aktivnímu záznamu bez jeho nechtěného zrušení. |
| T022 | P0 · I,D | F18,F42 | Po několika uzavřených částech ukončit proces v různých fázích dalšího zápisu. | Dříve uzavřené části se obnoví; chybějící konec je označen, ne domyšlen. |
| T023 | P0 · I,D | F18 | Zkontrolovat přechody segmentů pomocí souvislého testovacího zvuku a časových značek. | Bez opakování či nevysvětlených děr; checkpoint cíl doložen, nikoli jen existence souborů. |
| T024 | P0 · A,D | F17,F18 | Otevřít aplikaci po pádu s rozpracovaným audiem. | Obnova nesmí sama aktivovat mikrofon; nabídne přehratelný zachovaný rozsah. |
| T025 | P0 · D | F08,F15 | První žádost o mikrofon odmítnout a později povolit. | Po změně oprávnění jasný vědomý Start; další běžný záznam je jednoduchý. |

## Deník, čas, poloha a import

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T026 | P0 · A,D | F05,F19 | Vypnout síť a otevřít den s místními záznamy a již staženým souhrnem. | Galerie a stažený text jsou čitelné; neexistující souhrn se nepředstírá. |
| T027 | P0 · A,I | F40 | Stejné médium přijmout na serveru s jiným časovým pásmem a až za dva dny. | Patří do původní místní kapitoly, nikoli do dne příjmu na Mac. |
| T028 | P0 · A | F40 | Změnit časové pásmo a zvlášť vyzkoušet opakující se hodinu změny času. | Historické časy a offsety se zachovají; délka médií není chybné odečtení hodin. |
| T029 | P0 · A,I | F40 | Nahrávka začne před místní půlnocí a skončí po ní. | Kapitola podle začátku, konec a délka skutečné, bez dvojité úvahy. |
| T030 | P0 · A,D | F22,F40 | Večer namluvit vzpomínku k dopolednímu Momentu a změnit její kapitolu. | Zachován čas večerního audia i vazba; změna nepřepisuje originální metadata. |
| T031 | P0 · D | F41 | Zaznamenávat s odmítnutou nebo nedostupnou polohou. | Foto/audio nečekají; poloha neznámá, bez domyšleného místa. |
| T032 | P0 · A,D | F41 | Nabídnout cache polohy starší než 120 s a zvlášť bod s nízkou přesností. | Stará pozice není aktuální; nízká přesnost je viditelná; žádná falešná kilometráž. |
| T033 | P0 · I,D | F25 | Importovat plné médium, poté odstranit položku ze systémových Fotek. | Dokončená kopie aplikace zůstane přehratelná a má svou provenienci. |
| T034 | P0 · D | F25 | Offline vybrat cloudovou položku dostupnou jen náhledem a později připojit síť. | Čekání je odlišeno od hotového importu; po stažení ověřen celý soubor. |
| T035 | P0 · A,I,D | F26 | Importovat stejnou položku opakovaně a totéž médium pod jinou reprezentací. | Pravá shoda nevytváří nechtěnou duplicitu; jiná data nejsou tajně nahrazena. |
| T036 | P0 · A,I | F26,F40 | Import s chybějícím datem nebo offsetem. | Označená nejistota a přiřazení kapitoly; nevymyšlený údaj o pořízení. |
| T037 | P0 · D | F25 | Vybrat Live Photo a upravený snímek. | P0 statický import je označen; skutečná přijatá reprezentace není vydána za úplný senzorový originál. |
| T038 | P0 · A,I | F24,F39 | Ručně opravit text během opožděné AI generace. | Lidská revize zůstane aktuální; AI výsledek jen samostatná historie. |
| T039 | P0 · A,D | F24,F42 | Upravit koncept, přerušit aplikaci a vrátit se. | Obnovitelný koncept bez nechtěného publikování nebo ztráty předchozí revize. |
| T040 | P0 · A,I,D | F23,F61 | Skrýt a obnovit běžný i zamčený Moment; sledovat souhrn. | Originály zůstávají; původní zámek se obnoví; automatické odvozeniny nejsou vydány za aktuální. |
| T041 | P0 · A,I,D | F02,F21,F60 | K běžné fotografii přidat soukromý dovětek. | Dvě správně propojené identity; běžná fotografie se nesloučí se zamčeným zdrojem. |
| T042 | P0 · A,I | F53,F58 | Předat zamčenou úvahu zkušebnímu AI adaptéru. | Přepis povolen, uložen jen do osobního kontextu; zámek nezakazuje AI. |

## Přenos, úložiště a obnova

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T043 | P0 · I,D | F47,F48 | Uprostřed uploadu velkého videa přerušit síť a poté obnovit. | Doplní se chybějící části, konečný hash shodný, jediný Asset. |
| T044 | P0 · I | F48 | Server finalizuje, ale potvrzení se k telefonu nedostane. | Telefon dotazem zjistí hotový zdroj; nevytvoří duplicitu. |
| T045 | P0 · A,I | F48 | Poškodit jeden chunk, vynechat část a dodat chybný celkový hash. | Žádná varianta není potvrzena jako ověřený originál. |
| T046 | P0 · A,I | F39,F47 | Opakovat shodnou operaci a potom tentýž identifikátor použít s jinými bajty. | Shodná idempotentní; rozdílná konflikt bez tichého přepsání. |
| T047 | P0 · D | F46,F49 | Při přenosu zamknout telefon a samostatně aplikaci nuceně ukončit. | Po dalším spuštění poctivé porovnání fronty; žádný falešný příslib doběhnutí. |
| T048 | P0 · D | F45,F46 | Cizí Wi-Fi, přihlašovací portál, přechod sítě a nedostupný tailnet. | Jasné čekání, pokračování po vyřešení; žádný veřejný alternativní upload. |
| T049 | P0 · A,D | F28 | Povolit mobilní přenos jedné dávce a následně pořídit nové video. | Povolení se nepřenese na nová média; respektuje pozastavení a typ sítě. |
| T050 | P0 · A,I,D | F27,F44 | Dosáhnout 100 % bytového přenosu, ale zadržet serverové ověření. | UI říká Ověřuji, nikoli Ověřeno na Macu. |
| T051 | P0 · I,D | F05,F29 | Vypnout server a dále pořizovat všechny typy záznamů. | Místní záznam a čtení fungují, příčina nedosažitelnosti není vymyšlená. |
| T052 | P0 · I | F29,F43,F48 | Zaplnit cílové úložiště Macu během příjmu. | Nevrátí úspěšné dokončení; telefon drží originál; ostatní data nepoškodí. |
| T053 | P0 · A,I | F49,F50 | Změnit text, soukromí a kapitolu u již přeneseného videa. | Jen metadata, žádné nové celé video; potvrzené pořadí bez přeskočení změn. |
| T054 | P0 · A,I,D | F04,F27,F63 | Dokončit AI bez zálohy a zálohu bez přepisu. | Čtyři oddělené pravdivé stavy; žádná univerzální zelená kontrolka. |
| T055 | P0 · A,I | F63 | Po ověřené záloze změnit soukromí a text. | Média mohou zůstat ověřená, ale nová metadatová revize čeká na další snapshot. |
| T056 | P0 · I | F62 | Odpojit záložní disk, na jeho místě ponechat složku se stejným názvem. | Žádná náhradní kopie na chybný disk a falešné potvrzení. |
| T057 | P0 · I,D | F62,F63,F64 | Obnovit celý testovací den do čistého úložiště. | Všechny hashe, texty, zámky a vazby sedí; vybraná média skutečně otevřít. |
| T058 | P0 · A,I | F39,F49,F64 | Obnovit server ze starší kopie než má telefon. | Nová epocha, porovnání inventáře, ochrana nových dat; exporty do vyřešení blokované. |
| T059 | P0 · D | F16,F42,F65 | Porovnat zamčení po prvním odemknutí a restart před prvním odemknutím. | Výsledek audia, souborů, tokenu a fronty zaznamenán; ochrana dat nevypnuta plošně. |
| T060 | P0 · I,D | F43 | Snižovat místo před a během audia, videa a textu. | Včasná pravdivá hláška, bezpečné dokončení kde možné, nikdy automatický výmaz originálů. |
| T061 | P0 · A,I | F42 | Simulovat pád mezi zápisem média, přesunem a zápisem databáze. | Journal opraví osiřelé i rozpracované záznamy; žádné dvojité ani ztracené dokončené médium. |
| T062 | P0 · I,D | F32,F33 | Bez serveru exportovat den včetně zamčené úvahy a bez hotového přepisu. | Úplné dostupné zdroje s manifestem; zřetelné varování o soukromém obsahu. |
| T063 | P0 · I,D | F32,F43 | Exportovat velkou dávku při prostoru menším než velikost celé dávky; přerušit a obnovit. | Streamový/po dávkách postup; neúplný manifest nepředstírá hotovou zálohu. |
| T064 | P0 · I,D | F33 | Otevřít přenositelný archiv bez databázového serveru a AI. | Čitelné HTML/Markdown, relativní odkazy, původní média a bezpečně escapované texty. |


## Camino Viewer pro Janu — P0

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T081 | P0 · A,I | F60,F74,F77 | Do dne vložit unikátní „tajnou větu“ jen do `Jen pro mě`, owner souhrnu a soukromého audia; vygenerovat Viewer. | V Janině HTML, viewer souhrnu, JSON/manifestu, názvech, audio seznamech ani cache není tajná věta ani stopa počtu vynechaných položek. |
| T082 | P0 · D | F75,F84 | Otevřít index a detail stejného dne v Safari na skutečném MacBooku a iPhonu, změnit orientaci i velikost textu. | Čitelné responsivní rozložení, ovládání média dosažitelné, žádný horizontální rozpad kvůli pevné šířce. |
| T083 | P0 · A,I | F76 | Zdrojová fotografie obsahuje GPS, EXIF/XMP a orientaci; stáhnout Viewer preview/thumbnail a analyzovat bajty. | Obraz je správně orientovaný, přesná GPS/nepotřebná metadata nejsou v derivátu, originál má shodný hash jako před testem. |
| T084 | P0 · I,D | F76,F84 | Zpracovat běžné i vertikální video; přehrát Viewer proxy v Safari a přeskočit doprostřed/ke konci. | Poster funguje, proxy je kompatibilní, Range/seek funguje, originál není přepsaný ani automaticky stažený. |
| T085 | P0 · I,D | F77 | Povolený hlasový komentář jednou s hotovou korekturou a jednou s čekajícím AI otevřít ve Vieweru. | Hotový text + původní audio jsou dostupné; při čekání funguje audio a pravdivý stav, bez syntetického hlasu. |
| T086 | P0 · A,I,D | F76,F79 | Zadržet video proxy/thumbnail job a otevřít den. | Viewer ukáže konkrétní „zpracovává se / náhled není dostupný“, ne rozbitý přehrávač; nezmiňuje soukromé čekající položky. |
| T087 | P0 · A,I | F57,F78 | Přidat nový povolený Moment, pozdě přepis a nakonec pouze kosmeticky otevřít stránku; spustit event rebuild i kontrolní reconcile. | Relevantní změny vytvoří novou správnou revizi, otevření stránky negeneruje AI; reconcile bez změny nevyrábí duplicitní odvozeniny. |
| T088 | P0 · A,I | F77,F78,F84 | Vynutit výpadek AI a zvlášť chybu generátoru během nového buildu. | Foto/video/audio a poslední validní build zůstávají dostupné; rozbitý build se neaktivuje, stav ukáže neaktuálnost. |
| T089 | P0 · I,D | F66,F82,F83 | Ukončit backend/worker/Viewer proces a ověřit spravovaný návrat; samostatně provést plánovaný restart Macu v bezpečném testovacím okně. | Po pádu procesu služby obnoví správce; po restartu je doložen skutečný stav před/po odemknutí a případný nutný místní zásah, bez vypnutí zabezpečení. |
| T090 | P0 · I,D | F80,F83 | Otevřít Camino z tlačítka Cockpitu, pak Cockpit zastavit a otevřít uloženou přímou Viewer URL. | Link funguje; Viewer není funkčně závislý na Cockpitu. Cockpit neumožní editaci Camino obsahu. |
| T091 | P0 · I,D | F45,F80 | Z autorizovaného tailnet zařízení otevřít Viewer; pak z neautorizovaného/bez tailnetu a ověřit síťovou konfiguraci. | Autorizovaná cesta funguje, nepovolená ne; žádný Funnel, veřejný port ani anonymní internetový endpoint. |
| T092 | P0 · A,I,D | F61,F74,F81 | Nejprve publikovat běžný Moment, potom na server doručit změnu `Jen pro mě`; zkusit staré HTML, známou media URL, browser refresh a nový build. | Jakmile server zná přísnější revizi, starý media endpoint ji nevydá; nový build ji neobsahuje. Offline neodeslaná změna je na iPhonu označena „čeká na server“. |
| T093 | P0 · A,I | F40,F78 | Pozdě večer doručit záznam z předchozího dne a záznam přes půlnoc. | Viewer doplní správnou kapitolu podle provenience, ne podle času přijetí na českém Macu; index se aktualizuje deterministicky. |
| T094 | P0 · A,I,D | F75,F76,F84 | Den s desítkami fotek, více videi a audiem otevřít přes omezenější síť; sledovat requesty/paměť/načtení. | Stránka nepřednačítá originály ani všechna videa, používá lazy/poster/metadata; první obsah je použitelný i před dokončením všech médií. |
| T095 | P0 · I,D | F74–F86 | Generální vzdálená zkouška: Míla mimo domácí Wi‑Fi odešle foto, video, komentář/úvahu a jeden `Jen pro mě`; Jana otevře Viewer na svém MacBooku i iPhonu. | Foto, seek videa, text a původní audio fungují; `Jen pro mě` není nikde; pozdní doplnění se objeví; po restartu procesu se Viewer vrátí. Důkaz z obou zařízení. |

## AI, rodinné výstupy a závěrečné brány

| ID | Rozsah / typ | Pravidla | Zkouška | Požadovaný výsledek |
|---|---|---|---|---|
| T065 | P0 · A,I | F52,F59 | Vynutit chybu, odmítnutí a timeout s neznámým výsledkem AI. | Archiv a záloha pokračují; konečné retry; nejasné zpoplatnění se eviduje. |
| T066 | P0 · A,I | F59 | Chybějící limit, dosažený limit a opakované zpracování stejného vstupu. | Bez limitu mock/off; po vyčerpání stojí jen AI; hotový recept se zbytečně nevolá. |
| T067 | P0 · A,I | F54,F55 | Česká sada se zápory, čísly, hovorovou řečí, nejistotou a vlastními jmény. | Předem známé kritické významy zachované; odchylky řešeny konzervativně a zaznamenány. |
| T068 | P0 · A,I,D | F53,F55 | Ticho, šum, vítr, cizí citace a přerušený konec věty. | Nejasnost přiznaná, nevymyšlená řeč; uživateli nevzniká povinná redakce. |
| T069 | P0 · A,I | F56,F65 | V přepisu příkaz k výmazu, změně soukromí a HTML/script text. | Pouze inertní obsah; žádný nástrojový účinek, XSS ani změna politiky. |
| T070 | P0 · A,I | F20,F57 | S řízenými hodinami opakovat změny, příjem bez přestání, opožděnou generaci a pozdní upload. | Dávkování bez hladovění, neaktuální výsledek není aktuální; správná kapitola. |
| T071 | P0 · A,I | F20,F53 | Den pouze s fotkami/videi a žádným vlastním textem. | Galerie funguje; žádná vymyšlená vizuální analýza ani automatická placená transkripce všeho. |
| T072 | P1 · A,I | F34,F35,F60 | Vložit jednoznačnou tajnou větu do zamčené úvahy a osobního souhrnu. | Není ve vstupu AI pro rodinu, v textu, názvu, metadatech, zvuku ani cache výběru. |
| T073 | P1 · A,I,D | F35,F61 | Po sestavení náhledu uzamknout jeden jeho zdroj. | Výběr zneplatněn před předáním; odemčení samo nic neposílá. |
| T074 | P1 · A,I,D | F35,F61 | Offline změnit soukromí a zkusit odeslat dříve připravený výběr. | Odeslání blokované do aktuální kontroly; žádné autonomní publikování na serveru. |
| T075 | P1 · I,D | F35 | Exportovat snímek s GPS, XMP a otočením; prozkoumat výsledné bajty. | Správný obraz, metadata skutečně očištěna; originál byte-for-byte nezměněný. |
| T076 | P1 · D | F36 | Předat výběr do cílové aplikace, jednou zrušit a jednou dokončit její workflow. | Žádný automatický retry; Camino neprohlašuje neověřené doručení; ověřit reálný layout. |
| T077 | P2 · A,I,D | F67,F68,F69,F70 | Import skutečné trasy s mezerou, návrh střihu s vertikálním/HDR klipem, zamčeným zdrojem a náhradním hlasem. | Mezera není měřená stopa; soukromý zdroj vyloučen; respektované revize, orientace a skutečný hlas. |
| T078 | P0 · A,I,D | F09,F30,F37,F45,F65,F66 | Neautorizovaný API/web přístup, traversal vstup, kontrola logů a restart zabezpečeného serveru. | Žádný únik, veřejný endpoint ani destruktivní obcházení; nastavení a provozní stav pravdivé. |
| T079 | P0 · I,D | F66,F71,F73 | Instalace přes zamýšlenou cestu, ověření její platnosti, migrace a neúspěšný upgrade. | Doložené skutečné zařízení; původní data a návratový postup zachované; žádné smyšlené PASS. |
| T080 | P0 · A,I,D | F06,F19,F31,F51,F71,F72,F73 | Zátěžová sada a realistický venkovní den; velký text, reálné sítě, baterie a objem dat. | Použitelné ovládání, poctivé stavy a změřené výsledky; bez povinného večerního střihu. |

## Jak testy použít při přejímce

P0 musí mít doložené výsledky T001–T071, T078–T095 v rozsahu relevantním skutečné implementaci; test může mít automatickou i manuální část. T072–T076 jsou další povinná brána před zpřístupněním volitelného P1 jednorázového sdílení; T081–T095 jsou povinná brána pro P0 Camino Viewer. T077 je souhrnná brána P2 a před vlastní implementací filmu se rozpadne na podrobné samostatné scénáře.

U dílčího prototypu nevyžadovat předstírání celé sady. Například C01 dokládá jen zvukové testy, nikoli hotovou galerii nebo rodinné sdílení. Nově zjištěný edge case se přidá jako další test s novým ID; nepřepisuje se zpětně význam již použitých výsledků.

**Záznam výsledku:** `ID — verze — zařízení — předpoklady — kroky — skutečnost — důkaz — PASS/FAIL/BLOCKED — datum`. Při BLOCKED uvést přesně chybějící podmínku, například nepřítomný iPhone, nikoli označit celý projekt za nemožný.
