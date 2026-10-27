<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- 2026-10-27 18:04 CET: Orus cs-CZ-Chirp3-HD-Orus a tempo 0,90 přijaté Mílou poslechem. Google Cloud projekt camino-orus, povolené TTS a chráněný místní přístup funkční; jedna schválená smyšlená syntéza 166 znaků / 11,184 s HTTP 200, pomalejší poslech 12,414 s vznikl místně bez další syntézy.
- Místně implementované zapojení do střižny: celý text do 6000 znaků, části do 5000 UTF-8 B beze ztráty, spojení a zpomalení atempo=0.9, historie/koš/import zachované. Před každým novým vytvořením checkbox pro konkrétní text a cenu; editace souhlas ruší. Před každým odesláním a připojením opětovná kontrola povolení/textu. Bez automatického opakování, bez náhradního hlasu při chybě Orusu.
- Cílené ověření: 100 kontrol PASS / 62,419 s a nový HTTP test souhlasu/origin/idempotence PASS / 0,770 s. Plná brána: 2256 PASS / 482,110 s unit část, celkem 496,501 s. Google-auth 2.62.0 v projektovém venv a skutečný read-only přístup přes nový adaptér potvrzené; žádná další syntéza ani soukromý text při vývoji.
- Jen místní vývoj, bez nového p+n, restartu či změny samostatné služby a iPhonu. Nasazená funkční verze zatím zůstává předchozí. Další krok: samostatně autorizované Luna p+n a fyzická přejímka ovládání ve střižně. Detail: memory/reports/camino_orus_integration_20261027.md.
<!-- SAMANTHA_CURRENT_STATUS_END -->

### Předchozí stav po p+n UI 1

- 2026-10-26 09:28 CET: První UI krok střižny publikovaný a nasazený registrovanou Lunou do bc1fe4adfa5c006570058769d62d91a436263d3b. Účtenka 1173a162fd7197d9f5281e76a0f9d400: completed, push/deployment confirmed, jeden commit, project-camino → Cockpit, release_executor gpt-6-luna/high.
- Plná publikační brána 2232 PASS / 345,9 s, smoke 5/5, protected_services_unchanged=true. Adam jednou převzal účtenku; GitHub/main aligned 0/0 na vydaném headu před tímto dokumentačním zápisem, profily ready. Health OK a HTTP 200 podává přesně nové složené HTML včetně společné odezvy; code_stamp 28c8f0a83e59bc1b.
- Nasazené jsou společné hlášky, důvody nedostupného ukládání/náhledu/MP4 a obnova pozice/panelu po návratu od fotografie. Soukromé zdroje, backendové kontrakty, osobní střihy, iPhone a samostatná služba Camino beze změny.
- return_channel=caller: účtenku skutečně převzal terminálový Adam zde. Automatický portálový návrat returned_to_adam=false zůstává nepotvrzený a není důvodem opakovat úspěšné vydání.
- Skutečný browser/Safari/iPhone proklik viditelnosti, překrytí a návratu po fotografii NEOVĚŘENO. Další krok: po uloženém střihu obnovit Cockpit a provést přejímku v memory/reports/camino_film_ui_feedback_20261025.md. Větší rozložení pracovní plochy a český hlas zůstávají dalšími kroky.
- Tento výsledkový zápis je následný lokální dokumentační checkpoint, bez dalšího p+n. Vydaný UI kód je bc1fe4ad; další lokální zápis účtenky ho nemění.

### Předchozí lokální UI stav před p+n

- 2026-10-25 20:28 CET: První UI krok střižny lokálně hotový: společná sticky stavová lišta, odlišené probíhající práce/chyby/podmínky, procenta exportu nahoře a vysvětlení nedostupného ukládání/náhledu/MP4. Chybu fotografie nepřekryje běžné Uloženo.
- Návrat z fotografie/skryté karty i překreslení zachová pozici, kotvu a otevřený/zavřený panel; soukromý DOM se při skrytí nadále odstraňuje. Ochrany stale GET, textu, revizí a mazání zachované; žádné změny backendu ani osobních dat.
- Ověření: 102 cílených Python testů PASS (49,366 s) včetně Node scénářů panelu, návratu a původních ochranných kontraktů; rychlá statická brána PASS. Skutečný browser/Safari/iPhone a viditelnost/překrytí při scrollu NEOVĚŘENO — žádný prohlížeč není připojený.
- Jen lokální vývojový checkpoint, bez nového push/nasazení, produkčního renderu či změny iPhonu/služby. Předchozí společné p+n v této relaci c9c3a5af je historie; tento nový UI kód v něm není. Detail: memory/reports/camino_film_ui_feedback_20261025.md.
- Další krok: samostatné p+n, potom fyzicky ověřit návrat od fotografie, hlášky při práci dole v seznamu a dostupné důvody blokací. Větší rozložení editoru a český hlas zůstávají dalšími kroky.

### Předchozí stav po p+n klienta

- 2026-10-24 21:44 CEST: P+n všech pěti čekajících commitů do 3590c288 dokončené napoprvé registrovanou Lunou. Účtenka a2500be19e301dc26e6db4cd9fb597a8: completed, push/deployment confirmed, projekt project-camino, cíl Cockpit, release_executor gpt-6-luna/high; role beze změny.
- Publikační plná brána 2232 PASS / 454,2 s, smoke 5/5, protected_services_unchanged=true. Adamova jedna závěrečná kontrola: GitHub/main aligned 0/0 na 3590c288 před tímto výsledkovým checkpointem; Cockpit health OK, code_stamp 7ae887842f089e5c, PID 41492. Stejný stamp je očekávaný: balíček měnil Swift klienta a dokumentaci.
- Účtenku převzal a ověřil terminálový Adam zde; return_channel=caller. Automatický portálový návrat returned_to_adam=false, není potvrzený a není důvodem opakovat úspěšné vydání.
- Samostatná služba Camino, autosave a chráněné konfigurace/Serve zachované. Toto p+n neinstaluje IPA ani neprovádí úklid telefonu. IPA Camino-Projects-Trash-23-20261024.ipa je připravená v Downloads/iCloud (podpis/ZIP/hash/upload PASS), profil do 29. 10. 2026. Poslední přímý audit telefonu potvrdil 22 a 2 prázdné video intenty bez souborů; novější instalace/úklid nejsou ověřené.
- Další krok: v telefonu přijmout IPA 23 při zachování stejné aplikace bez odinstalace, poté Zkontrolovat a odstranit pokusy → Odstranit prázdné pokusy → potvrdit. Swift 95 a oba UI scénáře byly ověřené před vydáním; fyzická přejímka 23, celé cesty/filmu v koši a skutečná lhůta/uvolnění místa zůstávají otevřené. Dále text/historie nahrávek/jejich koš/MP3-WAV a český hlas.
- Tento následný zápis účtenky je lokální dokumentační checkpoint pro další GitHub balíček; vydaný funkční kód zůstává 3590c288. Podrobnosti: camino/docs/PENDING_MEDIA_REVIEW_REPORT.md.

### Předchozí stav před p+n úklidu médií

- 2026-10-24 21:15 CEST: Read-only audit iPhonu a soukromé Core Data kopie (quick_check OK) potvrdil 2 prázdné video intenty z 13. 10. Nemají pending/original soubory, Asset ani Moment a nepatří k cestě v koši. Instalovaný klient živě ověřený jako 0.1.0 (22). Živá DB nebyla přepisovaná; 2 intenty zatím zůstávají v telefonu.
- Lokálně hotový potvrzený úklid: Zkontrolovat a odstranit pokusy → Odstranit prázdné pokusy (2), případně jednotlivý nedokončený soubor. Potvrzení v klasickém alertu nabízí Zrušit a Odstranit natrvalo. Přijaté Assety, hotové Momenty, fronty a cesta držená sedmidenním košem chráněné; změna souboru/přijetí po kontrole zneplatní staré potvrzení. Bez automatického mazání neznámých souborů.
- Prevence: příprava videa po zavření kamery během GPS už nevytvoří intent; odmítnutý start a neúspěch bez souboru ruší prázdný intent. Nepřijaté soubory zůstávají zachované ke kontrole; po pádu je dostupný ruční úklid. Obnova/zápis se nepřekrývají.
- Ověření PASS: 95 Swift testů včetně 8 nových mazacích/preservačních scénářů; skutečné UI zrušení/potvrzení/poškozený testovací soubor/restart 31,631 s; projektová navigace 88,193 s; plná brána 2232 (unittest 465,698 s). Podepsaný archive/export/strict podpis/ZIP a release texty PASS, testovací seed v Release nepřítomný.
- IPA Camino-Projects-Trash-23-20261024.ipa, 1103371 B, shodné Downloads/iCloud Dokumenty a upload potvrzený, profil do 29. 10. 2026. Build 23 připravený, neinstalovaný. Další krok: aktualizovat stávající Camino bez odinstalace a potvrdit cílený úklid v aplikaci. Detail: camino/docs/PENDING_MEDIA_REVIEW_REPORT.md.
- Žádný nový push, p+n ani změna služby/Cockpitu. Dřívější služba schéma 4 a Cockpit 0a18db30/Luna b75c48be patří k předchozí samostatné přejímce. Fyzický koš celých cest/filmů, sedmidenní lhůta a uvolnění místa, text/historie nahrávek/jejich koš/MP3-WAV a český hlas zůstávají otevřené.

### Předchozí stav po opravě návratu

- 2026-10-24 20:41 CEST: Míla potvrdil spuštění IPA 21 a žádost o smazání projektu. Snímek ukázal navigační chybu: po skrytí aktivní cesty obrazovka Připravit projekt neměla cestu k ostatním projektům, koši ani přenosům.
- Lokálně opravené UI: bez aktivní cesty dostupné Projekty a koš (při existujícím projektu/koši) a Uložení a přenosy. Lze vybrat jinou cestu, sledovat žádosti a doručit je Macu; pevné nepravdivé tvrzení o nepřipojeném Macu odstraněné. Mazací kontrakt, persistence a serverový kód beze změny.
- Regresní scénář proti původní binárce reprodukoval chybějící tlačítko (FAIL 129,859 s); po opravě PASS 89,366 s: dvě cesty, zachovaný Moment jiné cesty, žádost o poslední cestu, restart, koš a otevření/zavření přenosů. Statická brána PASS; archiv/export/strict podpis/ZIP a přítomnost nových textů v Release PASS.
- Podepsaná IPA 0.1.0 (22), Camino-Projects-Trash-22-20261024.ipa, 1074899 B, shodné kopie Downloads/iCloud Dokumenty; iCloud upload potvrzený, profil do 29. 10. 2026. Telefon aktuálně 21 dle Mílova testu; build 22 připravený, neinstalovaný. Při aktualizaci zachovat stejnou aplikaci a data, neodinstalovávat. Detail: camino/docs/PROJECT_TRASH_NAVIGATION_REPORT.md.
- Samostatná služba byla při přejímce 19:48 ověřená na schématu 4, Cockpit koš vydaný přes Lunu b75c48be do 0a18db30; tato UI oprava je nepřepínala ani nepushovala. Poslední servisní důkaz: 4 ověřené místní DB snapshoty, původní tabulky a 316 originálů SHA/Viewer PASS; aktuální obsah žádostí se zde znovu neauditoval. Externí záložní svazek tehdy nepřipojený.
- Další krok: nahradit stávající Camino IPA 22 a fyzicky ověřit návrat přes Projekty a koš. Celý sedmidenní výmaz a uvolnění místa dosud nepřijaté; praktický text, historie nahrávek, jejich koš, MP3/WAV a příjemnější český hlas zůstávají otevřené.

### Předchozí stav po aktualizaci služby a telefonu

- 2026-10-24 19:48 CEST: Samostatná služba Camino aktualizovaná registrovaným stop/snapshot/upgrade/start na schéma 4, release f00fcb13; project_trash_v1 potvrzené. Čtyři ověřené místní DB snapshoty, původní konfigurace/release zachované. Externí šifrovaný svazek nepřipojený; místní snapshot není nezávislá záloha.
- Všechny původní tabulky čtyř DB a archiv po přechodu shodné: 921 operací, 132 Momentů, 4 cesty, 316/316 originálů / 2 379 212 189 B SHA-256 PASS. Serve, identity, přístupová oprávnění a flags zachované; žádná skutečná cesta ani média se nemazaly.
- Owner HTTP/HTTPS a auth PASS; Viewer katalog, deník, mapa a map-data 200, fotografie/zvuk/video Range 206. Poslední registrovaný status služby running=true a owner health PASS. Cockpit koš dostupný, seznam prázdný; dřívější p+n Luna b75c48be do 0a18db30 zůstává potvrzené.
- Na stejném iPhonu nainstalované Camino 0.1.0 (21), stejné bundle ID, bez odinstalace. Všech 7 původních položek kontejneru zachovaných; velikosti a časy změn SQLite/WAL/SHM před prvním spuštěním přesně shodné. První spuštění přes CoreDevice odmítl zamčený telefon; zobrazení původních záznamů a fyzický tok koše zatím NEOVĚŘENO.
- Podepsaná IPA Camino-Projects-Trash-21-20261024.ipa v Downloads/iCloud Dokumentech, podpis/ZIP/hash/upload PASS, profil do 29. 10. 2026. SideStore evidenci přímá instalace neověřila; pro obnovu použít IPA 21 a zachovat identitu aplikace. Další krok: odemknout a otevřít Camino, potvrdit původní data; potom syntetická fyzická přejímka koše. Praktická editace textu, historie nahrávek, jejich koš, MP3/WAV a český hlas zůstávají otevřené. Detail: camino/docs/CLIENT_21_SERVICE_UPGRADE_REPORT.md.

### Předchozí stav přípravy IPA a služby

- 2026-10-24 19:24 CEST: Podepsaná IPA Camino 0.1.0 (21) hotová: Camino-Projects-Trash-21-20261024.ipa, 1072250 B; archive/export/strict codesign/ZIP PASS, profil do 29. 10. 2026. Downloads a iCloud Dokumenty mají shodný hash, iCloud upload potvrzený. iPhone je dostupný s buildem 20; verze 21 neinstalovaná.
- Servisní preflight PASS: zdravé schéma 3, 921 operací, 132 Momentů, 4 cesty a 316/316 ověřených originálů. Migrace 3→4 na kopii v paměti zachovala původní řádky, nové tabulky prázdné; izolovaný import ve venv služby a shoda requirements PASS. Služba ani její data se neměnily.
- Aktuální autorizace pokrývá přípravu IPA i zamýšlenou aktualizaci. Před změnou LaunchAgentu ještě chybí přesná globální věta pro tento servisní krok; původní potvrzení bylo k SSD. Externí záložní svazek nyní nepřipojený. Před upgradem budou ověřené čtyři místní DB snapshoty; původní data/config/Serve zachovat.
- Další krok: po potvrzení registrovaný stop/upgrade/start a ověření schématu 4, owner HTTP/HTTPS/Viewer, řádků/identit/SHA/Serve; potom aktualizovat stejnou aplikaci buildem 21 bez odinstalace a fyzicky ověřit data. Detail: camino/docs/CLIENT_21_SERVICE_UPGRADE_REPORT.md.
- Předchozí p+n Cockpitu do 0a18db30 zůstává potvrzené (Luna b75c48be, 2232 PASS, smoke 5/5). Nový push, služba ani telefon se tímto přípravným checkpointem nevydávají.

### Předchozí stav po p+n Cockpitu

- 2026-10-24 17:56 CEST: P+n sedmidenního koše proběhlo napoprvé registrovanou Lunou. Pět commitů do 0a18db3038e0b9cf1069d52714a69b0f16d9ff26 je na GitHubu, Cockpit je nasazený. Účtenka b75c48be083a1f26e8e7296ccf5997de: completed, push/deployment confirmed, plná brána 2232 PASS, smoke 5/5, chráněné služby shodné.
- Hlavní Adam jednou ověřil účtenku a živý stav: GitHub/main 0/0 na vydaném headu, health OK, code_stamp 7ae887842f089e5c. Automatický portálový návrat returned_to_adam=false; výsledek skutečně převzal a ověřil Adam zde v terminálu. Publikování se neopakuje kvůli tomuto poli.
- Nasazené je ovládání ve střižně. Samostatná služba Camino a iPhone se tímto p+n neaktualizovaly; kompletní koš stále vyžaduje jejich samostatné vydání. Bez schématu 4 vrací ovládání požadavek na upgrade. Skutečné cesty ani média se nemazaly.
- Další krok: samostatně schválit upgrade služby Camino a instalaci iPhonu, potom fyzická přejímka syntetické cesty a filmu. Praktická editace textu, historie nahrávek, jejich koš, import MP3/WAV a příjemnější český hlas zůstávají otevřené.
- Zápis tohoto výsledku je následný dokumentační checkpoint pro další GitHub balíček; nemění vydaný funkční kód. Postup: camino/docs/PROJECT_TRASH_REPORT.md.


### Předchozí stav před p+n 24. 10. 2026

- 2026-10-24 17:32 CEST: Místně implementovaný společný sedmidenní koš cest a filmů. Celou cestu zahajuje iPhone; Mac potvrdí rozsah, umožní obnovu a po lhůtě vymaže spravovaná data. Telefon smaže až po ověřeném výmazu Macu a potvrdí ACK. Samostatný film zachová originály cesty.
- Ověřeno: 16 syntetických Python/HTTP testů koše, DOM potvrzení/obnovy a 87 Swift/Core Data testů PASS; iOS Release PASS. Finální plná brána PASS: 2232 testů bez selhání, unit část 381,487 s.
- Rozsah a hranice: `camino/docs/PROJECT_TRASH_CONTRACT.md`, `camino/docs/PROJECT_TRASH_REPORT.md`. Schéma 4, oba filmové kořeny, originály, historie/fronty, Viewer a místní SQLite/WAL. Nejasné historické kopie výmaz zastaví; zálohy, Fotky a ruční kopie mimo Camino jsou samostatné.
- Jen vývoj: bez nového push, nasazení, upgradu služby, instalace iPhonu či výmazu skutečných dat. Předchozí funkční vydání je 0cb79f32, Luna d7d836b810818f61162d4a887686f3a2 (p+n dokončené; returned_to_adam=false). Předchozí datovaná oprávnění neopravňují vydat nynější koš. Živá kontrola 17:32 CEST: PIDy a chráněné konfigurace shodné, Cockpit health OK.
- Další krok: samostatně schválit vydání příslušných částí (služba Camino, Cockpit, iPhone), potom fyzicky přijmout syntetickou cestu. Vývojový checkpoint je hotový; aktuální commit zjisti v git log podle Add seven-day project trash lifecycle. Otevřená zůstává praktická editace textu, historie nahrávek, jejich koš, import MP3/WAV a výběr příjemnějšího českého hlasu poslechem.


### Historické stavové záznamy před vývojem koše

- 2026-10-24 09:49 CEST: Místně dokončené kroky 4–5 více projektů: aplikace rozlišuje stejné názvy/období, Viewer má katalog povolených cest a oddělené deníky/mapy/média, granty jsou samostatné, střižna volí cestu a její den. Worker/export používají manifest konkrétního filmu. 34 integračních, Node a skutečné syntetické PNG přes HTTP PASS; iOS Release PASS. plná brána 2193 PASS (453,570 s unit část), závěrečné 3 testy dispatcheru PASS. Bez nového vydání, iPhone/Safari nepřijaté. Python 3.15.1 navržený k oddělenému pilotu, bez instalace.

- 2026-10-23 22:39 CEST: UI projektů v 15e0467a ověřené (tři UI scénáře, Release PASS), ale p+n c3aba0302d0661fbff03b131e65357a4 zastavila plná brána před pushem: 1/2185 selhání kvůli souběhu status probe a startu workeru. GitHub živě stále 8bc31d07, nasazení nezačalo. Úzká oprava startovacího souběhu lokálně hotová, 57 cílených testů PASS, plná brána 2186 PASS (333,492 s unit část), opakovaný souběh 10/10 PASS. Nový placený pokus se automaticky neopakuje.

- 2026-10-23 22:28 CEST: Krok 3 — ovládání projektů převzaté od Luny c39307ba80c8e9e373149a9a7696c220 a integrované Adamem. Založení, termíny, přepínání, archivace/znovuotevření; Release a statická brána PASS, tři vybrané UI scénáře PASS (offline 1/1, projekty a přejmenování 2/2). Míla výslovně schválil nový pokus i p+n všech dokončených commitů (účtenka c3aba0302d0661fbff03b131e65357a4; výsledek ověřit živě). Telefon ani samostatná služba se tím neaktualizují.

- 2026-10-23 21:59 CEST: Krok 3 — datová příprava v 176a6c66 hotová (Swift 82, plná brána 2185, iOS build PASS). UI návrh Luny 971d17d401d57207ca3ef7d762836191 není převzatý: rozsah dodaný Adamem vynechal závěrečnou závorku. Opravený požadavek připravený, nový placený pokus čeká na výslovné potvrzení; žádný retry ani změna UI neproběhly.

- 2026-10-23 21:49 CEST: Pokračování víceprojektového Camina — připravené atomické uložení formuláře a správa versus pořizování v modelu. Swift 82 PASS, plná brána 2185 PASS a iOS build PASS. Navazuje ovládání projektů (krok 3) registrovanou Lunou, kontrola a integrace Adamem. Dřívější oba commity již publikované/nasazené přes job 5b60714d658675cfedd05f1df1bafad7, 2185 PASS, smoke 5/5 a velká fotografie HTTP 200.

- 2026-10-23 21:03 CEST: Lokálně opravené velké fotografie v náhledu i filmu; pracovní kopie zachová celý rám a originál. Konkrétní zdroj dne 14. 10. prošel PNG a odděleným 1s QA v 720p/1080p, původní střihy/jobs shodné. 54 filmových + 18 gate testů a statická brána PASS. Bez p+n. Více projektů kroky 1–2 zůstávají dokončené lokálně; další vývoj krok 3.

- 2026-10-23 20:35 CEST: Lokálně implementované kroky 1–2 zobecnění na více cest/dovolených. Stabilní Trip UUID, volitelné termíny a archivace jako revize; owner katalog, oddělení dat a zachované fronty. Swift 81 PASS, cíleně 57 Python PASS; plná brána 2180 PASS a iOS build PASS. Bez push, nasazení či instalace. Další krok 3: ovládání projektů.

- 2026-10-20 22:23 CEST: Fotografie mají lokálně Otevřít fotografii v nové kartě a nemají renderovaný náhled záběru. Read-only PNG bez EXIF/GPS a bez diskové kopie; správné natočení/ICC, aktuální projekt/soukromí/hash a kontrola po dekódování. Video ovládání zachované. Funkční kód skutečně vytvořila Luna, Adam zkontroloval a převzal; opravil pouze citaci old, testové literály, úklid testserveru a složený frontendový otisk. Ověřit finální účtenku schváleného p+n 92b4b7704c6503fb8b2ed300b600c7f9 a živý audit. Při completed navázat fyzickou přejímkou fotografie v Cockpitu na Macu/iPhonu; p+n slepě neopakovat. Tento Git checkpoint zachycuje stav před vydáním; výsledek publikace/nasazení je v přesné účtence a logs/luna_photo_release_20261020.log.

- 2026-10-20 22:13 CEST: Míla potvrdil funkční opravu osiřelých metadat. Nově požaduje u fotografií Otevřít fotografii a odstranit jejich renderovaný náhled záběru. Vývoj i p+n výslovně Lunou; nejprve zprovoznit širší delegaci. Centrální vývojová role již gpt-6-luna/high, přejímací kontrakt připravený, samotná funkce zatím chybí.

- Aktualizováno: 2026-10-20 21:23 CEST — odstraněná čtyři osiřelá metadata videí, den 8. října znovu platný

### Hotovo
- Oprava mazání filmových variant `84336632` byla přes Lunu pushnutá a nasazená
  pouze do Cockpitu. Míla potvrdil funkční mazání a hotová MP4 dnů 6. a 7. října.
- Při zakládání filmu 8. října chyběly čtyři originály videí: jejich metadata
  byla přijatá před zastavením přenosu, ale Míla videa potom smazal na telefonu.
  Nebyla ve frontě, neměla upload session ani mediální účtenku.
- Po přesném potvrzení globální brzdy a zkoušce na kopii v paměti odstraněny
  pouze čtyři předem určené řádky živého inventáře Asset. Před změnou ověřená
  obnovovací kopie metadata DB v private; transakce, FK a ostatní řádky PASS.
- Zůstalo 304/304 ověřených originálů se shodnými SHA-256, všech 894 přijatých
  operací, 124 Momentů, identity, kurzor, flags a ostatních 10 metadata tabulek.
  Mediální DB i všech 797 existujících filmových souborů beze změny.
- Den 8. října prošel skutečným validátorem: 44 zdrojů, 24 fotografií,
  14 videí a 6 zvuků. Nový projekt ani MP4 se automaticky nevyráběly.
- Camino bylo krátce zastavené registrovaným vlastněným řízením, offline
  kontrola a záloha proběhly před zápisem, původní služba znovu běží.
  HTTPS owner health 200 a Cockpit katalog OK; konfigurace a síť shodné.

### Rozhodnutí
- Přesný jednorázový úklid čtyř nepřenesených videí tohoto dne podle Mílova
  potvrzení. Historické synchronizační obálky a sekvence se nepřepisují.
- Telefon, originály, střihy ani existující filmové varianty se nemažou.

### Otevřeno / rizika
- Další skutečný kontakt iPhonu po opravě zatím není ověřený.
- Obecný serverový kontrakt mazání při každém lokálním smazání tím nevznikl;
  případný další takový úklid vyžaduje vlastní přesný inventář a potvrzení.

### Další krok
- V Cockpitu znovu uložit projekt pro 8. října a pokračovat střihem/MP4.

### Navrhované další kroky
- Další připomínky střihu podle Míly; P2-F spojování dnů zůstává později.

### Technický důkaz
- `logs/camino_metadata_cleanup_20261020.log`: rows_removed=4, zbytek 304,
  FK/quick_check PASS, 304 originálů / 2 339 685 533 B SHA-256 zachovaných,
  797 filmových souborů shodných, projekty 6. a 7. dne platné, den 8 validní.
- Přesný plán, snapshot a účtenka jsou jen v `data/private/camino_metadata_cleanup/`.
- Předchozí vydání opravy: účtenka `68228ea9cbb839b07316f30df8bd9322`,
  push/deploy confirmed, 2 151 plných testů PASS a smoke 5/5.
  Terminál účtenku převzal; samostatný portálový návrat nepotvrzený.


# TVBCP: Camino

Pracovni proud: `project-camino`
Typ: `Project`
Rezim: `active`
Priorita: 1

## Cíl a hranice

Soukromý cestovní deník podle v0.5 + U15: jeden autor na iPhonu, soukromý
owner archiv a read-only Camino Viewer pro Janu bez veřejného webu. `Jen pro mě`
je vyloučeno; celé `Do deníku` je po synchronizaci Viewer-eligible.

## Aktuální stav a další krok

- V0.5 importovaná beze změny, 6/6 manifestovaných souborů ověřeno; U15 je závazný novější dodatek. Samostatná Úvaha začíná `Jen pro mě` a do deníku se převádí vědomě.
- Viewer delta audit potvrdil Tailscale/Serve/Cockpit základ, smoke 5/5, Funnel vypnutý, AC bez spánku a FileVault zapnutý. Viewer služby, autorizace, záloha/restart a Janina vzdálená zkouška chybějí; G8 NEPROVEDENO.
- Profilový fast-forward nyní kontroluje whitespace s příchozími `.gitattributes`; ostatní fail-closed brány zůstávají zachované.
- T016 PASS: přesně 30:24,406, 175 147 072 B, 48 kHz mono, režim Letadlo, převážně pod zámkem a celý poslech OK. T018–T020, T024 a T059 PASS podle Míly. T021 PASS v rozsahu C01b prototypu; plná integrace se zopakuje v C04. T059 po restartu ochránil data a řízené opakování zachytilo všechny značky pod zámkem. Vítr neověřen.
- C01b 0.2.0 (2) je historicky přijaté pro background audio, přerušení a vědomé pokračování; před přechodem na C01c prošla instalace i zachování tehdejších 15 položek. Aktuálně je na iPhonu C01c 0.3.0 (4).
- Běžící recorder přežije změnu scenePhase; nový Start/Pokračovat pouze v popředí. Přerušení ihned pozastaví vstup, ověří dostupnou část a nabídne Pokračovat/Ukončit. Pokračování vytváří novou část stejné session s evidovanou pauzou, bez přepisu předchozího média.
- Soubory vytvořené v C01b mají completeUntilFirstUserAuthentication; původní C01a soubory se nemigrují ani nemění. Staré JSON podporuje volitelné continuation. Tyto starší jednotlivé CAF samy nejsou C01c journal ani důkaz 60s cíle.
- Ověřeno 47/47 Swift testů, 2/2 UI testy simulátoru včetně snímku obrazovky, finální podepsaný iOS build a strict podpis; UIBackgroundModes=[audio]. Plná projektová brána PASS, 1684/1684 testů.
- C01b 0.2.0 (2) přijato v prototypovém rozsahu. Krátký test zámku a T016/T018–T021/T024/T059 PASS; T059 prošel po řízeném zopakování jedním nepřerušeným 107,801s souborem. Předchozí nevysvětlený tichý úsek se nezopakoval.
- Po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí stav, řekne, zda je potřeba vývoj, a rovnou předá podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu. Shoda s návrhem sama změnu kódu nevyvolává.
- C01c build 3 při prvním Start padal. Pět shodných crash reportů potvrdilo Swift 6 actor-isolation trap: inline tap callback zdědil `MainActor`, ale běžel na real-time audio frontě.
- Opravený build 0.3.0 (4) vytváří callback v `nonisolated` helperu. 52/52 Swift + 2/2 UI PASS, oba arm64 buildy, strict podpis, instalace i launch PASS; všech 136 položek se po instalaci shoduje v cestě, typu a velikosti.
- Pět nedokončených pokusů z pádů zůstalo zachováno. Profil hlavní aplikace do 22. září 18:16 CEST. Krátký fyzický smoke buildu 4 PASS podle Míly: bez pádu, rostoucí čas i ukazatel a přehratelný nový záznam.
- T022 PASS ve dvou odlišných fázích otevřené části: klidový relaunch, pravdivé označení obnoveného rozsahu a přehratelné uzavřené části. T023 PASS přes čtyři poslechnuté 55s hranice bez opakování či nevysvětlené díry. C01c je přijato v prototypovém rozsahu; G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C02a minimální receiver prošel 10/10 automatickými testy i privátním HTTPS smoke přes dočasnou Tailscale Serve cestu. Správný upload vytvořil právě jeden objekt a účtenku, retry neduplikoval, chybný hash a konflikt byly odmítnuty. Funnel zůstal vypnutý, Cockpit dostupný a původní Serve stav byl obnoven.
- C02b má fyzický PASS T043 v syntetickém rozsahu. Letový režim zachytil relaci s 0/13 přijatými částmi; po návratu sítě vznikl jediný objekt daného Assetu, 13/13, 100 663 553 B a shodný SHA-256.
- `Camino Transfer Test` 0.4.0 (2) koaleskuje souběžné impulsy reconciliace; následná celá dávka doběhla automaticky. Build 0.4.0 (3) přidal per-request síťovou politiku a prošel syntetickou mobilní částí T049. Swift 20/20, Python workflow 13/13 a UI 1/1 PASS při jeho přípravě. T050 prošel ve druhém fyzickém syntetickém běhu se 14s zadržením ověření a souběžným videodůkazem; předchozí brána 1719/1719 PASS. T043/T047/T049/T050 receiver a testovací cesta jsou po bězích ukončené, Serve obnovený, Funnel vypnutý.
- T048 prošel v dostupném syntetickém rozsahu běžné cizí Wi-Fi, přerušení a návratu sítě a nedostupného/obnoveného tailnetu. Captive portal zůstává NEOVĚŘENO. Po registrovaném stopu je receiver i cesta vypnutá, původní Serve obnovený a Funnel vypnutý.


C04a/C04b mají lokální implementaci; bezpečná část T060 je PASS a zbytek
čeká na rozhodnutí o bezpečně simulovatelném hardeningu. C05a připojí API.
Captive portal T048 ověřit jen při skutečně dostupné síti. C01c ani C02a dále
nerozšiřovat bez nového důvodu.

## Rizika

- C01a přijato, ale širší brány G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C01b přijato v prototypovém rozsahu. Vítr a plná integrace T021 v C04 čekají; jeden nevysvětlený nereprodukovaný tichý úsek z prvního T059 zůstává rizikem.
- C01c je přijato v prototypovém rozsahu po T022/T023. Výsledek nepokrývá dlouhodobou terénní spotřebu ani plný databázový a serverový T061, který zůstává C05a.
- C02a je přijato jen v omezeném serverovém prototypu. Smoke z téhož Macu přes tailnet DNS není důkaz iPhone klienta, cizí sítě, přerušení velkého souboru, trvalé služby ani úplných T043/T048/T051.
- C02b má T043, T047 a T050 PASS v syntetickém rozsahu, T049 úspěšnou syntetickou mobilní část a T048 PASS ve třech dostupných síťových podscénářích. Captive portal T048 a plné T049 se skutečným videem zůstávají NEOVĚŘENO; build 4 má fyzický PASS části A, část B je částečná. Receiver není produkční služba ani záloha.
- C03a/C03b jsou referenční model a lokální persistence, nikoli zapojený iPhone, produkční služba či ochrana Vieweru. Před provozním použitím musí C04/C05/C08 zavést vynucení a ověřit U15 včetně T096. C03b nepokrývá finalizaci médií ani skutečnou obnovu.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Instalace a launch nejsou fyzická přejímka přenosu; vývojový profil je časově omezený do 24. září 2026. U01–U15 se bez nového rozhodnutí neotevírají.

## Chronologické záznamy

### 2026-09-14 21:22 CEST — Založení Camina před meziúkolem

Hotovo:
- Samostatný katalogový projekt, vlastní paměť, handoff a TVBCP; podklady v0.4 uchované.

Rozhodnutí:
- Míla zadal založení projektu a integraci do Human–Adam, commit, push a nasazení.
- Vývoj se dnes tímto krokem nezahajuje; nejdřív meziúkol, potom C00.
- Potvrzené U01–U11 z podkladů se znovu neotevírají. Návrhy D01–D10 nejsou nová uživatelská rozhodnutí.

Další krok:
- Vyřešit Mílův meziúkol; při návratu ke Caminu začít C00.

Navrhované další kroky:
- Po C00 připravit jen malý audio prototyp C01a podle skutečně ověřeného prostředí.

Technický důkaz:
- Manifest 15/15 shodných SHA-256; ZIP odpovídá všem 16 rozbaleným souborům.
- Testy integrace a stav publikace: viz `memory/reports/camino_registration_2026_09_14.md`.
- Testy aplikace a manuální hardware zkoušky NEPROVEDENO.

Ověření založení: 56/56 testů integrace (54 + 2 profilové testy) a rychlá statická brána OK.
Publikační plná brána a finální nasazení se ověřují registrovaným živým auditem;
tento zápis předchází schválenému push a nasazení.

### 2026-09-14 23:26 CEST — C00, Xcode a checkpoint po recovery záloze

Hotovo:

- C00 a samostatně schválená instalace Xcode dokončeny; projektové předání dorovnáno na skutečný stav.
- Před úklidem vznikla ověřená recovery záloha `20260914_231439`; dokumenty Camina zachované a porovnané pomocí SHA-256.

Rozhodnutí:

- Míla zadal nejdřív ostrou zálohu, potom úklid repozitáře. Úklid tvoří lokální dokumentační checkpoint bez mazání; push ani nasazení nejsou součástí tohoto kroku.
- U01–U11 beze změny. C01a se automaticky nezahajuje.

Další krok:

- Po výslovném zadání C01a připojit odemčený iPhone a ověřit rozpoznání, kompatibilitu a podpis pro malý audio prototyp.

Navrhované další kroky:

- Nahrát, bezpečně dokončit a přehrát krátký neutrální vzorek na skutečném telefonu; server není vstupní podmínka.

Technický důkaz:

- `camino/docs/ENVIRONMENT_AUDIT.md`, `DECISIONS.md`, `XCODE_INSTALLATION.md` a `camino/tasks/C01a_AUDIO_PROTOTYPE.md`.
- Instalační kontroly Xcode/first launch/iPhone SDK prošly; build a fyzické audio testy NEPROVEDENO.
- Recovery: 63 295 souborů, 28 892 kopírováno, 34 360 hardlinků, 43 symlinků, 0 přeskočeno; zkušební obnova AGENTS.md se shodným SHA-256.
- Závěrečná plná kontrolní brána checkpointu: 1684/1684 testů OK; syntaxe a Git safety check OK. Nejde o testy aplikace Camino.

### 2026-09-15 08:19 CEST — C01a: první prototyp, telefon připraven, build blokován

Hotovo:

- Malý prototyp Start/Stop, skutečný vstup, místní evidence a přehrání; 25 testů logiky a syntetického audia prošlo.
- Míla připravil důvěru a Developer Mode; přímý audit potvrdil párování, spojení a vývojové služby telefonu.

Rozhodnutí:

- Na Mílův pokyn pokračovat ve vývoji zahájeno pouze C01a. Žádná placená AI ani další etapa.
- Přímá kompilace není náhrada Xcode buildu, instalace nebo fyzického poslechu. Celý krok zůstává BLOCKED.

Další krok:

- V Xcode → Settings → Components ověřit a zpřístupnit Platform Support iOS 26.2, potom zopakovat build připraveného CaminoAudio projektu.

Navrhované další kroky:

- Po sestavení připravit podpis, nainstalovat prototyp a ručně ověřit neutrální vzorky Komentář/Úvaha. Žádná automatická aktivace mikrofonu.

Technický důkaz:

- `camino/docs/C01a_AUDIO_PROTOTYPE_REPORT.md`, `camino/prototypes/audio/README.md`.
- 25/25 XCTest OK; arm64/iOS kompilace/link exit 0, bez warnings; project.pbxproj lint OK.
- Xcode build exit 70: platform support iOS 26.2 chybí; platné signing identity 0. Fyzické testy NEPROVEDENO.
- Plná společná brána před checkpointem: 1684/1684 testů OK; nové Swift testy jsou samostatných 25/25 výše.

### 2026-09-15 13:34 CEST — Zahájení instalace podpory iOS

- Míla po dokončeném úklidu výslovně zadal spuštění instalace.
- Xcode Components: spuštěn balíček iOS 26.2 + iOS 26.3.1 Simulator; živě potvrzen postup stahování 185 MB z 10,47 GB (2 %). Úvodní odhad před spuštěním byl 8,39 GB.
- Před spuštěním 92 116 107 264 B volných (85,79 GiB). Instalační doklad je soukromý, mimo Git.
- Dokončení instalace, nový Xcode build, signing a fyzická přejímka zatím neověřeny; C01a zůstává BLOCKED.
- Další krok: Po dokončení stahování ověřit instalaci iOS Platform Support v Xcode Components a zopakovat nepodepsaný build C01a. Potom dořešit signing, instalaci na iPhone a fyzickou přejímku T015/T017/T025.

### 2026-09-15 15:01 CEST — Podpora iOS a standardní build ověřeny

- Xcode Components a `simctl list runtimes` potvrdily instalaci; iOS runtime 26.3.1 / 23D8133 dostupný.
- `xcodebuild -project camino/prototypes/audio/CaminoAudio.xcodeproj -scheme CaminoAudio -configuration Debug -destination generic/platform=iOS -derivedDataPath <soukromý-build-adresář> CODE_SIGNING_ALLOWED=NO build`: exit 0, BUILD SUCCEEDED.
- Vznikl skutečný balíček CaminoAudio.app s arm64 executable; `codesign` potvrdil, že není podepsaný. Jediné varování: přeskočená extrakce AppIntents metadat, protože target nemá AppIntents.framework.
- SDK/platforma už build neblokují. Zdroje aplikace beze změny; dřívějších 25 testů logiky se bez nové změny neopakovalo.
- Volné místo po instalaci přibližně 69,3 GiB. Platných podpisových identit aktuálně 0; DEVELOPMENT_TEAM v projektu nenastaven. Přihlášení k Apple Account zatím neověřeno.
- Instalace aplikace na telefon, spuštění a fyzické T015/T017/T025 NEPROVEDENO. C01a zůstává BLOCKED na podpisu a fyzické přejímce; C01b nezahájeno.
- Další krok: Nastavit v Xcode Apple Account a vývojový tým pro podpis, potom podepsat a nainstalovat CaminoAudio na iPhone a provést fyzickou přejímku T015/T017/T025.

### 2026-09-15 18:31 CEST — Podpis ověřen, instalace čeká na telefon

- Míla nastavil tým v Xcode. Aktuálně jedna platná podpisová identita; automatický vývojový podpis a profil ověřeny. Účty, certifikáty a identifikátory týmu nejsou v Gitu.
- Podepsaný `xcodebuild` Debug / generic/platform=iOS: exit 0. `codesign --verify --deep --strict` nad CaminoAudio.app: exit 0. Vývojový profil platí do 2026-09-22 18:16 CEST, obsahuje jedno zařízení.
- První build v projektovém data/private skončil na FinderInfo u .app. Nový DerivedData adresář v /private/tmp problém odstranil bez změny zdrojů či odstraňování atributů originálů. [Apple QA1940](https://developer.apple.com/library/archive/qa/qa1940/_index.html).
- Volba týmu z Xcode přesunuta do existujícího mechanismu LocalSigning.xcconfig; význam verzovaných nastavení projektu je shodný s původním HEAD, zachováno jen formátování Xcode.
- Poslední devicectl inventura: iPhone 14 Plus odpojený; Developer Mode enabled je evidovaný stav, nikoli důkaz aktuálního spojení. Instalace, spuštění a fyzický poslech NEPROVEDENO; C01a zůstává BLOCKED.
- Další krok: Připojit a odemknout iPhone, ověřit dostupnost zařízení a nainstalovat podepsaný CaminoAudio.app. Potom provést fyzickou přejímku T015/T017/T025; nahrávání zahajuje uživatel vědomým Start.

### 2026-09-15 18:36 CEST — Aplikace nainstalována, spuštění odmítnuto

- iPhone 14 Plus živě ověřen: wired, tunnel connected, Developer Mode enabled. Zařízení odpovídá vývojovému profilu; podpis znovu ověřen strict kontrolou.
- `devicectl device install app`: exit 0, success, přesný bundle cz.pythonmf.camino.audio.prototype v installedApplications. Instalace na telefon PASS.
- `devicectl device process launch`: exit 1, FBSOpenApplicationErrorDomain / Security. Hlášení uvádí podpis, oprávnění nebo nepotvrzenou důvěru profilu; vzhledem k platnému podpisu a úspěšné instalaci je dalším krokem ruční kontrola důvěry. Příčina zatím není definitivně potvrzena.
- Spuštění, UI, mikrofon a fyzický poslech NEOVĚŘENO; C01a stále BLOCKED, C01b nezahájeno. Žádné nahrávání nebylo spuštěno.
- Další krok: Na iPhonu potvrdit důvěru vlastnímu vývojářskému účtu v Nastavení → Obecné → VPN a správa zařízení. Potom ověřit spuštění Camino Audio a provést fyzickou přejímku T015/T017/T025.

### 2026-09-15 18:39 CEST — Míla potvrdil otevření aplikace; zadal c+p+n

- Míla výslovně potvrdil, že se Camino Audio na iPhonu otevřelo. Otevření je potvrzení uživatele; nejde o automaticky ověřený průchod UI, mikrofon ani poslech. Předchozí blokace spuštění již podle tohoto potvrzení nebrání otevření.
- Podepsaný build, strict podpis a instalace mají strojové doklady; profil platí do 2026-09-22 18:16 CEST. Ruční T015/T017/T025, oba audio vzorky a poslech zůstávají NEPROVEDENO, C01a není přijaté.
- Míla zadal nejprve commit + push + nasazení aktuálního balíčku do Cockpitu. Autorizace zahrnuje čekající lokální commity a tento redigovaný stav; po c+p+n se zatím další vývoj ani nahrávání nespouští.
- Doklad výsledku c+p+n: aktuální GitHub batch audit, plná brána a kanonická simple-main deployment receipt s novým PID, shodou otisku a smoke 5/5; historické nasazení není důkaz tohoto kroku.
- Další krok: Po uzavření schváleného c+p+n pokračovat ruční přejímkou C01a na iPhonu: T015/T017/T025, neutrální krátký Komentář a Úvaha, Stop a poslech; nahrávání zahajuje Míla. C01b nezahajovat.

### 2026-09-15 19:15 CEST — Uživatelské zkoušky krátkého audia

- Zařízení: iPhone 14 Plus / iOS 26.6.1; Camino Audio 0.1.0 (1), instalovaný podepsaný Debug build z 15. září. Níže je svědectví Míly z řízených kroků v konverzaci, nikoli měření na dálku.
- Komentář: podle potvrzení běžel čas, reagoval ukazatel signálu, Stop dokončil uložení a celý záznam byl slyšet včetně začátku a konce. Zadáno asi 30 s; skutečná délka a stav sítě nebyly změřeny.
- Úvaha: Míla potvrdil všechny kroky zkoušky v režimu Letadlo s vypnutou Wi-Fi, včetně uložení a poslechu. Zadáno asi 30 s; skutečná délka nebyla změřena.
- Opětovné otevření po ukončení přes přepínač aplikací: oba dokončené vzorky zachovány a přehratelné, mikrofon se sám nespustil — uživatelský PASS. Není to zkouška pádu během zápisu.
- Odebrání oprávnění v Nastavení: aplikace oznámila zakázaný mikrofon; po povolení vše fungovalo — uživatelský PASS tohoto scénáře. První odmítnutí systémového dialogu tím není ověřeno; samovolný Start po změně oprávnění nebyl v poslední odpovědi zvlášť popsán.
- T015 částečně ověřeno (oba typy a poslech, offline výslovně jen Úvaha), T017 částečně (signál a hlas, bez potvrzení názvu vstupu), T025 částečně (odebrání/povolení v Nastavení). Neoznačovat celé scénáře za PASS.
- Přesné délky, velikosti a SHA-256 telefonních vzorků dosud nezjištěny; obsah ani soubory nahrávek se nepřenášely. Žádný hlášený funkční FAIL, ale C01a zatím formálně nepřijato; G0/G1 neuzavřeny.
- Dřívější c+p+n d573e90c dokončeno: 1684 testů, šest commitů pushnuto, canonical deployment receipt deployed a smoke 5/5. Tento nový zápis výsledků vzniká až po tomto nasazení a je určen k místnímu commitu.
- Další krok: Doplnit krátký Komentář bez internetu a potvrdit název zobrazeného vstupu. Potom doplnit doklady vzorků a přesný scénář prvního odmítnutí oprávnění T025; dosavadní výsledky neopakovat bez důvodu. C01b nezahajovat.

### 2026-09-15 19:25 CEST — Oprava zobrazení průběhu přehrávání

- Míla po doplňujícím testu potvrdil přehrání Komentáře a nahlásil chybějící průběh. Snímek IMG_0503.PNG ukazuje režim Letadlo, Přehrávám, čas 00:30, název Mikrofon iPhonu a uložený Komentář 00:30. Obrázek nebyl kopírován do Gitu. Sám nedokládá pohyb času ani vypnutí Wi-Fi; přehrání potvrzuje uživatel.
- Příčina ověřena v kódu: společná obrazovka při poslechu dál zobrazovala elapsed posledního záznamu, vstup a mikrofonní meter. Playback tick pouze hlídal konec, nečetl pozici přehrávače.
- Oprava: AVAudioPlayer.currentTime a duration přes AudioDriver; samostatný stav přehrávání v controlleru a oznámení změny při každém odečtu. SwiftUI při poslechu zobrazuje uplynulý/celkový čas a modrý průběh místo údajů mikrofonu. Žádné dopočítávání času podle timeru. [Apple currentTime](https://developer.apple.com/documentation/avfaudio/avaudioplayer/currenttime).
- Ověření: 28/28 Swift XCTest, podepsaný Debug xcodebuild generic/platform=iOS exit 0 a codesign --verify --deep --strict exit 0. Tři nové testy pokrývají skutečnou pozici vs. čas záznamu/nástěnné hodiny, chybné hodnoty a Stop/opakování/odchod do pozadí; rozšířen test přirozeného konce.
- Zápis a formát médií se nemění. Nová verze zatím NENÍ nainstalovaná na iPhonu; ruční UI/poslech opravy NEOVĚŘENO. Před aktualizací čeká potvrzení, že nahrávání i přehrávání stojí. Existující vzorky zachovat, aplikaci neodinstalovávat.
- T015: doplňující Komentář přehrán podle uživatele, screenshot v režimu Letadlo; offline test proběhl podle zadaného postupu, samostatný technický důkaz vypnuté Wi-Fi chybí. T017: název vstupu Mikrofon iPhonu nyní doložen snímkem (při poslechu šlo o zachovaný údaj záznamu). Přesná metadata vzorků a první odmítnutí systémového dialogu T025 zůstávají otevřené.
- Další krok: Při zastaveném záznamu i přehrávání aktualizovat aplikaci v připojeném iPhonu a ručně ověřit běžící čas/průběh, Stop a opakované přehrání existujícího vzorku. Potom doplnit zbývající doklady C01a a první odmítnutí oprávnění; C01b nezahajovat.

### 2026-09-15 20:15 CEST — Přerušení poslechu, práce bez telefonu

Hotovo:

- Poslech po události přerušení ihned skončí a obrazovka přizná přerušení; další poslech vyžaduje Přehrát. Čas i průběh se vynulují.

Rozhodnutí:

- Na Mílův pokyn pokračováno bez připojeného telefonu v opravách C01a. C01b nezahájeno; bez změny formátu a zápisu médií.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit průběh, Stop, opakované přehrání a přerušení poslechu.

Navrhované další kroky:

- Doplnit metadata neutrálních vzorků a první odmítnutí systémového oprávnění. Fyzická přejímka C01a zůstává otevřená.

Technický důkaz:

- Regresní test před opravou selhal: přerušení nechalo stav playing. Po opravě 30/30 Swift XCTest; podepsaný Debug xcodebuild a strict codesign exit 0. Dva nové testy ověřují okamžitou reakci bez timeru a opakované události bez automatického spuštění či změny nahrávek.
- Instalace této verze, simulátor a fyzické zkoušky NEPROVEDENO. Starší verze zůstává v iPhonu.

### 2026-09-15 20:20 CEST — Srozumitelné chyby při zahájení poslechu

Hotovo:

- Nedostupný soubor má vlastní hlášení, odlišné od chyby načtení/přehrání. Nastavení mikrofonu se nabízí jen při zakázaném oprávnění. Po chybě lze vybrat jinou nahrávku.

Rozhodnutí:

- Pokračování bez telefonu v C01a; žádné nové projektové rozhodnutí ani zahájení C01b.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit opravený průběh, Stop a opakované přehrání.

Navrhované další kroky:

- Dokončit ruční přejímku včetně oprávnění a metadat neutrálních vzorků.

Technický důkaz:

- 32/32 Swift XCTest, podepsaný Debug xcodebuild a strict codesign exit 0. Dva nové testy: nedostupný soubor bez změny evidence a následný poslech jiného vzorku; nabídka nastavení podle oprávnění i při nesouvisející chybě uložení.
- Pět zdrojových/testovacích souborů; formát ani zápis médií beze změny. Instalace a fyzický retest NEPROVEDENO, C01a stále nepřijato.

### 2026-09-15 20:42 CEST — Ověření rozhraní v iOS simulátoru

Hotovo:

- Dva opakovatelné UI testy ovládají SwiftUI a skutečný AVAudioPlayer: čas i průběh postupují, Stop a opakování fungují; vzorek přežije ukončení aplikace a návrat sám nic nepřehraje. Prohlédnutý snímek ukazuje 00:03 / 00:30, modrý průběh a dostupný Stop bez překryvů.

Rozhodnutí:

- Další práce bez telefonu zůstává v C01a. Samostatné schéma CaminoAudioUITests, pouze tiché syntetické audio a oddělené UUID úložiště. Pomocný kód se překládá jen pro Debug simulátor; návrat aplikace nesmí vytvořit náhradní vzorek.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit opravený průběh, Stop a opakované přehrání.

Navrhované další kroky:

- Dokončit fyzickou přejímku oprávnění a metadat neutrálních vzorků. C01b nezahájeno.

Technický důkaz:

- CaminoAudioUITests: 2/2 PASS, 0 skipped, xcodebuild test exit 0; iPhone 14 Plus simulátor, iOS 26.3.1 / 23D8133, x86_64. Snímek exportován z xcresult a vizuálně zkontrolován. Logy, výsledek a snímek zůstávají mimo Git.
- Dřívějších 32 testů jádra se beze změny jádra neopakovalo. Standardní podepsaný iPhone build a strict podpis OK; testovací vstupní značky nejsou v jeho programu.
- Mikrofon, fyzický poslech, iOS 26.6.1 a instalace aktualizace na telefon NEOVĚŘENO tímto krokem. C01a/G0/G1 stále nepřijato.

### 2026-09-15 21:09 CEST — Aktualizace opravené aplikace na iPhone

Hotovo:

- Po Mílově potvrzení připravenosti aktualizována aplikace na připojeném iPhonu 14 Plus a úspěšně spuštěna. Instalovaná verze zahrnuje opravy průběhu, přerušení a hlášení chyb poslechu.

Rozhodnutí:

- Aktualizace stejného bundle bez odinstalace; před zahájením potvrzen zastavený záznam i poslech. Nahrávání nebylo spuštěno.

Další krok:

- V otevřeném Caminu přehrát existující vzorek a ověřit běžící čas, modrý průběh, Stop a opakované přehrání. Potom doplnit metadata neutrálních vzorků a první odmítnutí oprávnění; C01b nezahajovat.

Navrhované další kroky:

- Po dílčím retestu dokončit fyzickou přejímku C01a; nová etapa není tímto krokem zahájena.

Technický důkaz:

- Zdroj aplikace 259b7476, Camino Audio 0.1.0 (1). Znovu ověřen strict podpis, platný profil a shoda zařízení. Devicectl install i launch: exit 0 / success; inventář potvrzuje přesný bundle aplikace.
- Soukromé identifikátory, instalační doklady a runtime média zůstávají mimo Git. Zachování a poslech konkrétních vzorků po této aktualizaci čekají na potvrzení uživatele; C01a/G0/G1 stále otevřené.

### 2026-09-15 21:18 CEST — Míla potvrdil opravu přehrávání na iPhonu

Hotovo:

- Míla potvrdil, že nové přehrání podle zadaného postupu po Stop začíná od začátku, a následně potvrdil běžící čas i modrý průběh. Regrese z původního snímku je uživatelsky ověřena jako opravená na telefonu.

Rozhodnutí:

- Zkoušku opraveného průběhu neopakovat bez nového důvodu. Celé C01a zatím neuzavírat kvůli zbývajícím dokladům a prvnímu odmítnutí oprávnění.

Další krok:

- Při dostupném odemčeném telefonu doplnit délku a velikost neutrálních vzorků; potom provést první odmítnutí systémové žádosti o mikrofon na samostatné testovací instalaci podle T025. C01b nezahajovat.

Navrhované další kroky:

- Po dokončení těchto dokladů vyhodnotit přijetí C01a.

Technický důkaz:

- Uživatelské potvrzení v této konverzaci, iPhone 14 Plus / iOS 26.6.1, instalovaný zdroj 259b7476. Není to nové automatické měření ani přejímka systémových přerušení.
- Pokus o read-only inventář souborových metadat v kontejneru Camino přes devicectl skončil outcome timeout / exit 2. Délky a velikosti nebyly získány; žádný zvukový soubor se nekopíroval. Kód se neměnil, testy se neopakovaly.

### 2026-09-15 21:25 CEST — Připraven oddělený test mikrofonu, čeká obnovení spojení

Hotovo:

- Sestaven a podepsán Camino Test se samostatným bundle cz.pythonmf.camino.audio.permissioncheck; původní Camino ani jeho úložiště se neměnily. Testovací instalace zatím nezačala.

Rozhodnutí:

- Míla zadal pokračování přejímky a potvrdil připravený telefon. T025 používá novou samostatnou instalaci, aby nebylo nutné odinstalovat původní aplikaci s nahrávkami.

Další krok:

- Po odpojení a opětovném připojení kabelu ověřit živé vývojové spojení s odemčeným iPhonem. Potom dokončit čtení metadat a instalaci připraveného Camino Test pro první odmítnutí mikrofonu; C01b nezahajovat.

Navrhované další kroky:

- V Camino Test ručně odmítnout první systémovou žádost, později povolit mikrofon a ověřit nový vědomý Start. Do té doby T025 neoznačovat za PASS.

Technický důkaz:

- Samostatný Debug build ze zdroje 0fbfd0b3: xcodebuild exit 0, strict codesign exit 0; bundle a jméno ověřeny z Info.plist. Profil do 2026-09-22 21:20 CEST; účty, podpisové identity a balíček zůstávají mimo Git.
- Telefon v inventáři connected, ale živé details/apps skončily timeoutem. Opakovaný nerekurzivní inventář metadat: com.apple.mobiledevice / -402653181, Failed to allocate RSD device. Bez výpisu médií, bez kopírování audia, bez instalace či spuštění nové aplikace.
- Míla dostal požadavek na odpojení/připojení kabelu a ponechání telefonu odemčeného. Odpověď dosud čeká. Kód se neměnil, testy jádra/UI se neopakovaly; oprava přehrávání zůstává uživatelsky potvrzená.

### 2026-09-15 21:37 CEST — Obnovené spojení, Camino Test nainstalován a metadata ověřena

Hotovo:
- Přepojení kabelu nepomohlo. Po Mílou provedeném restartu Xcode živý seznam aplikací uspěl; VPN ani síťová konfigurace se neměnily. Příčina původní chyby RSD není definitivně určena.
- Strict podpis, oddělený bundle a profil pro cílový telefon ověřeny. Instalace a spuštění Camino Test: exit 0 / success; původní Camino i Camino Test přítomné. Profil testovací aplikace platí do 22. září 21:20 CEST.
- Přečteno pouze 5 completed.json a inventář souborů původního Camina. Všech 5 byteCount odpovídá skutečné velikosti příslušného CAF; 48 kHz, mono, interrupted=false. Obsah audia se nepřenášel ani neposlouchal nástrojem.

Rozhodnutí:
- První odmítnutí oprávnění se zkouší v oddělené aplikaci. Instalace sama není fyzický PASS T025. Původní nahrávky zachovány; C01b nezahájeno.

Další krok:
- V nainstalovaném Camino Test dokončit ruční první odmítnutí mikrofonu, následné povolení v Nastavení a nový vědomý Start. T025 a přejímka C01a zůstávají otevřené; C01b nezahajovat.

Navrhované další kroky:
- Po uživatelském výsledku doplnit T025 a vyhodnotit rozsah přejímky C01a; dosavadní úspěšné testy neopakovat bez důvodu.

Technický důkaz:
- Soukromá instalační účtenka latest_permission_check.txt odkazuje na poslední xcode_restart pokus: apps/install/launch/apps_after, 5 metadata copy receipts a file_sizes; git-safe tabulka délek/velikostí je v C01a_AUDIO_PROTOTYPE_REPORT.md.
- Kód aplikace se neměnil; dřívějších 32 testů jádra a 2 UI testy nebyly opakovány. T025 první odmítnutí/povolení zatím uživatelsky NEOVĚŘENO; G0/G1 neuzavřeny.

### 2026-09-15 21:39 CEST — První odmítnutí mikrofonu uživatelsky potvrzeno

- Hotovo / důkaz: Míla po zadání Start → Nepovolovat v samostatném Camino Test potvrdil hlášení zakázaného mikrofonu a že nahrávání nezačalo. Tato část T025 je uživatelský PASS.
- Rizika: následné povolení, návrat bez automatického záznamu a nový vědomý Start v této instalaci dosud NEOVĚŘENO; celý T025 ani C01a nejsou uzavřeny.
- Další krok: V Camino Test povolit mikrofon přes Nastavení, vrátit se a ověřit, že nahrávání nezačne samo. Potom vědomým Start pořídit krátký neutrální vzorek, Stop a přehrát. T025 a přejímka C01a zůstávají otevřené; C01b nezahajovat.
- Kód se neměnil; dřívější testy jádra/UI se neopakovaly.

### 2026-09-15 21:43 CEST — T025 dokončeno, C01a přijato v prototypovém rozsahu

Hotovo:
- Míla potvrdil všechny tři zadané kroky v Camino Test: povolení mikrofonu, návrat bez automatického záznamu a vědomý Start krátkého vzorku, Stop a poslech. Spolu s předchozím odmítnutím jde o uživatelský PASS T025 v C01a.
- Vyhodnocena podmínka přijetí z C01a_AUDIO_PROTOTYPE.md: automatizovaná část A i fyzická část B doloženy, žádný známý otevřený FAIL vedoucí ke ztrátě/přepsání souboru či nevyžádanému mikrofonu. C01a přijato.

Rozhodnutí a rizika:
- Přijetí platí pro krátký foreground prototyp. T015 je splněno jen bez integrace Momentu; zámek, hovory, dlouhý běh a obnova při pádu během zápisu nejsou otestované funkce této etapy. G0/G1 zůstávají nesplněné.
- Nahrávky mají jen místní kopii a prototyp není pro ostrá média. Profil původní aplikace vyprší 22. září 18:16 CEST.

Další krok:
- C01a uzavřeno; vyčkat na zadání C01b pro audio pod zámkem, přerušení a vědomé pokračování. C01b automaticky nezahajovat.

Technický důkaz:
- Fyzické zkoušky: řízené uživatelské potvrzení z dnešní konverzace; výsledky a hranice důkazů v C01a_AUDIO_PROTOTYPE_REPORT.md.
- Dosavadních 32 Swift testů a 2 UI testy simulátoru PASS; podepsaný build, strict podpis, instalace/spuštění a metadata mají místní účtenky. Kód se nyní neměnil a testy nebyly bez nového důvodu opakovány.

### 2026-09-15 21:57 CEST — C01b zahájeno, připraven background audio prototyp

Hotovo:
- Výslovný pokyn Míly zahájit C01b; nové zadání a report. Verze 0.2.0 (2), background audio, explicitní navazující části a pauza, bezpečné omezení nového Start na popředí, lokální oznámení jen při již uděleném oprávnění.
- 47 Swift testů PASS, 2 UI testy PASS; snímek vizuálně zkontrolován. Finální podepsaný build a strict podpis PASS, správné UIBackgroundModes. Plná projektová brána PASS, 1684/1684 testů.

Rozhodnutí:
- Změna ochrany platí jen pro nově vytvořené soubory; legacy data bez migrace. Žádný push/deploy, nákup ani C01c. Fyzická přejímka se nenahrazuje simulátorem.

Rizika:
- C01b dosud nepřijato, skutečný zámek/hovor/30 minut/Bluetooth a T059 NEPROVEDENO. Jediný soubor na nepřerušený úsek může být při pádu neúplný; žádná garance záchrany nebo kontinuity segmentů.

Další krok:
- Po potvrzení připraveného telefonu nainstalovat 0.2.0 (2) bez odinstalace a provést nejdřív krátkou zkoušku zámku. Potom T016/T018–T021/T024/T059 podle zadání C01b; C01c nezahajovat.

Technický důkaz:
- C01b_BACKGROUND_AUDIO_REPORT.md, C01b_BACKGROUND_AUDIO.md a soukromá účtenka latest_c01b.txt. 15 nových testů C01b + 32 dosavadních; hlasy ani soukromé identifikátory nejsou v Gitu.

### 2026-09-15 22:03 CEST — C01b 0.2.0 nainstalováno a spuštěno na iPhonu

Hotovo / důkaz:
- Míla potvrdil připojený odemčený telefon a zastavené audio. Aktuální zdroje se shodují s buildovou účtenkou 0d2ae8e0; strict podpis a platný profil pro připojený telefon ověřeny.
- devicectl install a launch: exit 0 / success. Následný živý seznam aplikací potvrzuje hlavní bundle s verzí 0.2.0. Bez odinstalace.
- Inventář před/po: stejné relativní cesty a velikosti všech 15 souborů původních pěti pokusů. Jde o metadata, nikoli porovnání obsahu či hashů; audio se nekopírovalo.

Otevřeno / rizika:
- Míla dostal postup krátkého offline testu zámku; výsledek dosud čeká. Instalace není PASS fyzického zámku, hovoru, Bluetooth ani 30minutového záznamu. C01b/G0/G1 nepřijato; C01c nezahájeno.

Další krok:
- Dokončit krátkou offline zkoušku zámku v nainstalované verzi 0.2.0 (2): asi 30 s pod zámkem se slyšitelným počítáním, Stop a celý poslech. Potom T016/T018–T021/T024/T059; C01c nezahajovat.

Ověření:
- Kód se neměnil; dřívějších 47 Swift testů, 2 UI testy a plná brána 1684 testů nebyly opakovány. Soukromé instalační účtenky jsou pod latest_c01b.txt / latest_install.txt.

### 2026-09-15 22:15 CEST — Krátký funkční test zámku potvrzen

Hotovo:
- Míla potvrdil nahrávání během zámku, pokračování po odemčení a přehrání záznamu v hlavním Camino Audio 0.2.0 (2). Krátké funkční ověření zámku: PASS podle uživatele.

Rozhodnutí:
- Žádné nové rozhodnutí. C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T016: 30 minut záznamu převážně pod zámkem, průběžné neosobní zvukové značky, Stop a celý poslech; doplnit délku/velikost z metadat. Potom T018–T021/T024/T059; C01c nezahajovat.

Navrhované další kroky:
- Po T016 ověřit dostupná sluchátka a přerušení hovorem/změnou vstupu; poté zbývající scénáře C01b.

Technický důkaz:
- Uživatelské potvrzení z fyzického telefonu po instalaci 0.2.0. Přesná délka, velikost, úplnost poslechu a offline režim nejsou touto odpovědí samostatně doloženy; metadata nového vzorku ani aktuální verze iOS nebyly v tomto kroku čteny. Audio zůstalo na telefonu.
- Kód beze změn; automatické testy se neopakovaly. Krátká zkouška neuzavírá 30minutový T016, hovor, sluchátka ani ochranu po restartu.

### 2026-09-15 22:17 CEST — Konec dne, předání a schválené p+n

Hotovo:
- C01a přijato; C01b 0.2.0 (2) nainstalováno. Míla potvrdil krátký test zámku, pokračování po odemčení a přehrání. Dnešní práce je přerušená, 30minutový T016 nebyl proveden.

Rozhodnutí:
- Míla výslovně zadal ukončení dne a p+n celého čekajícího balíčku. Oprávnění zahrnuje tento závěrečný zápis, push na main a řízené nasazení do Cockpitu.
- C01b/G0/G1 zůstávají otevřené, C01c nezahájeno. Testy na telefonu pokračují až při příštím návratu.

Další krok:
- Příště navázat 30minutovým T016 v Camino Audio: režim Letadlo a vypnutá Wi-Fi, převážně zamčený telefon, průběžné hlasové značky, Stop, celý poslech a délka/velikost.

Navrhované další kroky:
- Potom dostupná sluchátka, přerušení hovorem/změnou vstupu a zbývající scénáře C01b.

Technický důkaz:
- 47 Swift testů a 2 UI testy PASS; krátký fyzický test potvrzen uživatelem. Přesná délka/velikost krátkého vzorku a jeho offline režim samostatně nedoloženy.
- Doklad p+n určuje aktuální GitHub batch audit a kanonická simple-main deployment receipt: cílový commit, brána, nový proces, otisk a smoke. Při zápisu tohoto předání p+n ještě probíhá; starší nasazení není důkaz výsledku.
- Profil hlavní aplikace do 2026-09-22 18:16 CEST; audio pouze na telefonu, bez ověřené další kopie. Žádná soukromá média v balíčku.

### 2026-09-16 13:43 CEST — T016 PASS podle Míly

- Stav: T016 dokončen fyzickým uživatelským testem v Camino Audio. Přibližná délka 30:16, režim Letadlo, převážně zamčený telefon, nahrávání bez hlášeného výpadku a celý záznam přehratelný.
- Důkaz: svědectví Míly. Velikost souboru nebyla sdělena; verze aplikace, telefon a iOS nebyly v dnešní zprávě znovu čteny a navazují na evidovaný kontext 0.2.0 (2), iPhone 14 Plus / iOS 26.6.1.
- Pozorování: přehrávání při zamčené obrazovce neběželo. Není to akceptační kritérium T016 a nevzniklo rozhodnutí rozšířit rozsah.
- Rizika: T018–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno. Jediný soubor úseku není segmentový journal ani garance 60s obnovy. Audio zůstává pouze na telefonu.
- Další krok: T018 s dostupnými sluchátky, potom T019–T021/T024/T059.
- Ověření: kód beze změn, automatické testy se neopakovaly; změněn pouze projektový zápis.

### 2026-09-16 19:46 CEST — T018 PASS a dílčí T019

- Stav: T018 PASS podle Míly s AirPods jako zobrazeným aktivním vstupem; stání i chůze pod zámkem, několikaminutové úseky, bez výpadků, celý poslech OK. Vítr nebyl přítomen.
- Důkaz: CoreDevice potvrdil Camino Audio 0.2.0 (2) a opravil T016 na 30:24,406 / 175 147 072 B / 48 kHz mono. Žádný CAF se nekopíroval ani neposlouchal.
- Telefonát: první samostatná část 3:08,56 byla označena `interrupted=true`; Pokračovat vytvořilo druhý samostatný soubor 4:53,57 ve stejné session s pauzou 2:25,13. Grafické seskupení není fyzické slepení médií.
- Mikrofon iPhonu: pozdější záznam byl nová session bez continuation. Podle Míly byl v kapse tišší a méně kvalitní; nejde o automatické pokračování.
- Rizika: úplný T019 a T020 čekají; T019 vyžaduje příchozí hovor ignorovaný i přijatý, T020 změnu aktivního vstupu během záznamu. C01b/G0/G1 otevřené, C01c nezahájeno.
- Další krok: dokončit T019, potom T020–T021/T024/T059.

### 2026-09-16 20:02 CEST — Automatický návod k dalšímu testu

- Rozhodnutí: po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí PASS/FAIL/BLOCKED či dílčí stav, řekne, zda je potřeba vývoj, a rovnou poskytne podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu.
- Hranice: shoda s návrhem nevyžaduje změnu kódu. Při FAIL se nejdřív doloží přesný projev, potom se opraví C01b a zopakuje dotčený scénář. C01c zůstává mimo rozsah.
- Další krok: dokončit T019 příchozím běžným telefonním hovorem jednou ignorovaným a jednou přijatým; potom automaticky předat T020.
- Ověření: pouze projektový zápis pravidla; kód aplikace ani soukromá data se neměnily.

### 2026-09-16 20:25 CEST — T019 PASS

- Stav: ignorovaný i přijatý příchozí hovor PASS podle Míly; obě části přehratelné, nic z hovoru v audu a žádné samovolné pokračování.
- Důkaz: technická metadata potvrzují dvě přerušené první části 44,410 s a 26,798 s a jejich samostatná vědomá pokračování stejné session 21,551 s a 20,999 s, s pauzami 43,153 s a 112,272 s. Všechny části jsou 48 kHz mono; žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: chování odpovídá návrhu C01b, oprava ani nový build nejsou potřeba.
- Rizika: T020–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.
- Další krok: provést T020 změnou skutečně aktivního vstupu během běžícího záznamu; potom automaticky předat T021.

### 2026-09-16 20:39 CEST — T020 PASS

- Stav: odpojení aktivních AirPods přerušilo záznam, části zůstaly přehratelné, nic se samo neobnovilo a AirPods se znovu staly aktivním vstupem až při dalším vědomém spuštění. T020 PASS podle Míly.
- Důkaz: metadata potvrzují tři části jedné session — 34,776 s přerušená, 25,944 s navazující a přerušená, 18,215 s navazující a dokončená — s pauzami 28,002 s a 90,312 s; 48 kHz mono. Žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: pouhé Bluetooth připojení není aktivní route; vstup AirPods se potvrdil až při vědomé reaktivaci audio session. Oprava ani nový build nejsou potřeba.
- Rizika: T021/T024/T059, C01b/G0/G1 otevřené; C01c nezahájeno.
- Další krok: provést T021 v prototypovém rozsahu; potom automaticky předat T024.

### 2026-09-16 21:27 CEST — T021 PASS v rozsahu C01b prototypu

- Stav: volba typu a Přehrát byly za běžící Úvahy neaktivní, druhý recorder nešel spustit, po návratu z jiné aplikace pokračovala stejná session a čas narostl; jedna část bez přerušení a celý poslech OK podle Míly.
- Důkaz: poslední Úvaha 56,350 s, 5 413 696 B, 48 kHz mono, `interrupted=false`, bez continuation. Dřívější samostatný přípravný pokus byl oddělen; žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: T021 PASS v rozsahu C01b prototypu; plný scénář videa/Momentu se zopakuje v C04. Oprava ani nový build nejsou potřeba.
- Rizika: T024/T059, C01b/G0/G1 otevřené; C01c nezahájeno.
- Další krok: provést T024, potom automaticky předat T059.

### 2026-09-16 21:43 CEST — Přijetí v0.5, rozhodnutí U15 a delta C00

Hotovo:
- Původní v0.5 je importovaná a ověřená; vznikl závazný U15 dodatek a Viewer readiness audit bez změny systému.

Rozhodnutí:
- Celé `Do deníku` může být po synchronizaci dostupné Janě v soukromém Vieweru. Samostatná Úvaha vždy vzniká `Jen pro mě` a vyžaduje vědomé `Vložit do deníku`.
- Původní balíček se kvůli manifestu nepřepisuje. U15 se implementuje v C03/C04, Viewer v C08c–C08f; C01b zůstává izolovaný audio prototyp.

Další krok:
- Provést T024, potom T059; C01c nezahajovat před uzavřením C01b.

Navrhované další kroky:
- Po C01b pokračovat C01c; následně zachovat pořadí malých etap v0.5 a před C08 dokončit potřebný datový, přenosový a serverový základ.

Technický důkaz:
- Manifest v0.5 6/6, přesná kopie ZIP; Tailscale 1.102.4 online, Serve bez Funnel, Cockpit smoke 5/5, AC `sleep=0`, FileVault zapnutý. Viewer/G8 NEPROVEDENO.

### 2026-09-16 21:48 CEST — Oprava profilového whitespace preflightu

Hotovo:
- Human–Adam workspace umí bezpečně převzít commit, který současně přidává importovaný Markdown i jeho `.gitattributes`.

Rozhodnutí:
- Preflight používá atributy z `FETCH_HEAD`; globální ignorování whitespace ani oslabení ostatních sync bran nebylo přijato.

Další krok:
- Po commitu zopakovat dorovnání čistých profilů; Camino pokračuje T024.

Navrhované další kroky:
- Žádný nový produktový krok; oprava pouze odstraňuje falešný blokátor převzetí již schváleného balíčku.

Technický důkaz:
- Regresní test + 192 souvisejících testů PASS; rychlá kontrolní brána PASS.

### 2026-09-16 22:41 CEST — T024 PASS

Hotovo:
- Po nuceném ukončení aplikace za rozpracované Úvahy zůstal relaunch v klidu, dříve dokončené části byly přehratelné a nový neověřený pokus byl viditelně započítán.

Rozhodnutí:
- T024 PASS; oprava ani nový build nejsou potřeba. Samostatný rozpracovaný pokus splňuje kanonický scénář i bez vazby continuation.

Další krok:
- Provést T059; C01c nezahajovat před uzavřením C01b.

Navrhované další kroky:
- Po T059 vyhodnotit C01b a teprve potom případně zahájit C01c.

Technický důkaz:
- Snímek ukazuje `Připraveno` 00:00, vědomý `Start`, jednu neověřenou položku a přehratelné části. CoreDevice metadata: zachovaná dokončená session 25,093 s + 2,254 s, nový pokus jen `started.json` bez `completed.json`; žádný CAF se nekopíroval ani neposlouchal.

### 2026-09-16 23:09 CEST — první T059: ochrana PASS, audio FAIL

Hotovo:
- Ochrana před prvním odemknutím, klidový relaunch, zachovaný počet neúplných položek a přehratelnost souboru prošly. Vyslovený hlas během zamčené části však v poslechu chyběl.

Rozhodnutí:
- T059 zůstává otevřený jako FAIL audio části. Před změnou kódu proběhne řízená reprodukce, protože T016 pod zámkem dříve prošel.

Další krok:
- Zopakovat audio část T059 s Mikrofonem iPhonu a přesnými hlasovými značkami; při opakovaném FAIL diagnostikovat C01b.

Navrhované další kroky:
- C01c nezahajovat, dokud není T059 vysvětlený a C01b uzavřené.

Technický důkaz:
- Před prvním odemknutím `unavailable` bez čtení kontejneru; po odemknutí `Připraveno 00:00`, žádné samovolné nahrávání a count 1. Dokončený Komentář 53,567 s, 5 146 528 B, 48 kHz mono, bez přerušení; audio neposloucháno nástrojem.

### 2026-09-16 23:21 CEST — T059 PASS po opakování; C01b přijato

Hotovo:
- Řízené zopakování zachytilo všechny hlasové značky před zámkem, pod zámkem i po odemčení a zůstalo jednou nepřerušenou částí.

Rozhodnutí:
- T059 PASS po opakování; C01b přijato v prototypovém rozsahu. Bez opravy a nového buildu.

Další krok:
- Vyčkat na výslovný pokyn k C01c; T022 netestovat na 0.2.0.

Navrhované další kroky:
- Po schválení vyvinout C01c a potom předat T022, následně T023/T061.

Technický důkaz:
- Komentář 107,801 s, 10 352 992 B, 48 kHz mono, bez přerušení/continuation; poslech potvrzuje Míla, CAF nebyl kopírován ani poslouchán nástrojem. První tichý úsek zůstává nevysvětleným nereprodukovaným pozorováním.

### 2026-09-17 07:59 CEST — C01c 0.3.0: implementace a instalace

Hotovo:
- Segmentový zápis s 55s checkpointem, create-only journalem, obnovou po pádu a sekvenčním přehráním. Staré C01a/C01b zůstává bez migrace.
- 52/52 Swift testů, 2/2 UI testy, signed build, strict podpis, instalace a launch PASS.
- Plná projektová brána PASS, 1685/1685 testů; po jednom nesouvisejícím časovacím selhání prošel cílený test 1/1 a celý opakovaný průchod čistě.

Rozhodnutí:
- C01c zůstává rozpracované do fyzických T022/T023. Platná otevřená část je po pádu vždy označena jako částečná s možným chybějícím koncem.

Další krok:
- T022 na fyzickém telefonu; potom automaticky T023 nebo oprava C01c.

Navrhované další kroky:
- Po přijetí T022/T023 uzavřít prototypový rozsah C01c; plný T061 zopakovat v C05a.

Technický důkaz:
- Build 0.3.0 (3), profil do 22. 9. 18:16 CEST. Dvoučástový UI fixture 15 + 15 s. Inventář před/po instalaci 111 položek se shodným SHA-256 cest/velikostí; audio se nečetlo.

### 2026-09-17 11:32 CEST — Oprava pádu C01c při Start

Hotovo:
- Crash reporty určily chybnou actor izolaci tap callbacku. Build 4 vytváří callback v `nonisolated` kontextu a zachovává Swift 6 strict concurrency.
- 52/52 Swift testů, 2/2 UI testy, nepodepsaný i podepsaný arm64 build, strict podpis, rychlá statická brána, instalace a launch PASS.

Rozhodnutí:
- C01c se nepřijímá bez fyzického mikrofonu. Pět nedokončených pokusů se nemaže; nejsou vydávány za dokončené nahrávky.

Další krok:
- Krátký neutrální Start/Stop a celý poslech na 0.3.0 (4); při PASS pokračovat T022.

Navrhované další kroky:
- Po T022 vyhodnotit T023 nebo další opravu; plný T061 zůstává C05a.

Technický důkaz:
- Pět shodných `SIGTRAP` v `_swift_task_checkIsolatedSwift`. Všech 136 položek před instalací zůstalo po instalaci a launchi shodných v cestě, typu a velikosti; audio se nekopírovalo ani neposlouchalo.

### 2026-09-17 11:46 CEST — Krátký fyzický smoke buildu 4 PASS

Hotovo:
- Míla potvrdil, že Start nepadá, čas i ukazatel rostou a nový záznam lze po Stop přehrát.

Rozhodnutí:
- Oprava pádu je fyzicky potvrzená; před T022 není potřeba další vývoj. Krátký smoke nenahrazuje T022 ani přijetí C01c.

Další krok:
- Provést první průchod T022 na 0.3.0 (4), potom test zopakovat s pádem v jiné fázi otevřeného segmentu.

Technický důkaz:
- Účtenka: Komentář 10,7 s, 2 058 496 B, 48 kHz mono, jeden segment, `interrupted=false`, `recovered=false`, bez mezery. Všech 136 předchozích položek zůstalo shodných; přibylo sedm očekávaných položek. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

### 2026-09-17 13:12 CEST — T022/T023 PASS; C01c přijato

Hotovo:
- T022 prošlo dvěma nucenými ukončeními v odlišných fázích otevřené části. Relaunch zůstal bez mikrofonu, obnovený rozsah byl pravdivě označený a přehratelný.
- T023 prošlo souvislým testem přes čtyři 55s hranice bez slyšitelného opakování, nevysvětlené mezery nebo useknutí.

Rozhodnutí:
- C01c 0.3.0 (4) je přijato v prototypovém rozsahu. C01c se dál nerozšiřuje; plný databázový a serverový T061 patří do C05a.

Další krok:
- Vyčkat na výslovný pokyn k C02a.

Navrhované další kroky:
- V C02a připravit pouze minimální přijímač syntetického souboru a porovnání hashe přes soukromé HTTPS. U15 zůstává C03/C04 a Viewer C08c–C08f.

Technický důkaz:
- První T022 ukázalo tři obnovitelné části a 02:18 zachovaného přehratelného rozsahu; druhé splnilo stejná kritéria při pozdějším pádu. Osm značek T023 kolem čtyř hranic bylo podle Míly slyšet jednou a ve správném pořadí. Audio nebylo čteno nástrojem; telefon byl při závěrečném zápisu nedostupný.

### 2026-09-17 14:19 CEST – Lokální C02a přijímač bezpečně ověřuje syntetický soubor serverovým hashem bez přepisu či duplicit

Hotovo:
- Lokální C02a přijímač bezpečně ověřuje syntetický soubor serverovým hashem bez přepisu či duplicit
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- C02a zůstává izolovaný standard-library prototyp; produkční serverový cíl zůstává FastAPI v samostatném prostředí Camina

Další krok:
- Po checkpointu autorizovat privátní HTTPS smoke přes Tailscale Serve se syntetickým souborem

Navrhované další kroky:
- Ověřit správný upload a shodu velikosti/SHA-256
- Ověřit chybný hash a identický retry
- Potvrdit, že Funnel ani veřejná cesta nejsou aktivní

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-camino`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-09-17 15:19 CEST — C02a privátní HTTPS smoke PASS

Hotovo:
- Dočasná privátní HTTPS cesta Tailscale Serve předala syntetický soubor loopback přijímači. Server potvrdil vlastní délku a SHA-256 a vytvořil právě jeden objekt a jednu účtenku.
- Chybný hash i konflikt byly odmítnuty, identický retry neduplikoval. Kořen Cockpitu zůstal dostupný, Funnel vypnutý a původní Serve konfigurace byla přesně obnovena.

Rozhodnutí:
- C02a je přijato v prototypovém rozsahu. Produkční cíl zůstává FastAPI v samostatném prostředí; dočasný standard-library receiver se nepovyšuje na trvalou službu.

Další krok:
- Vyčkat na výslovný pokyn k C02b.

Navrhované další kroky:
- V C02b ověřit velký soubor, souborové části, přerušení a skutečný iOS klient na cizí síti bez veřejného alternativního endpointu.

Technický důkaz:
- Tailnet HTTPS health 200; upload 201; retry 200 s `created=false`; chybný hash 422; konflikt 409; úložiště 1 objekt + 1 účtenka se shodným serverovým hashem. Cockpit health 200, pouze tailnet, Serve stav po testu shodný s výchozím.

### 2026-09-17 16:13 CEST — C02b zahájeno; části a pravdivá fronta lokálně ověřené

Hotovo:
- Receiver bezpečně eviduje 8MiB části, po přerušení vrací chybějící indexy a finalizuje jediný objekt až po serverové kontrole celkové délky a SHA-256.
- Swift model po relaunchi používá serverovou pravdu, bez sítě čeká, 100 % bytů drží jako `verifying` a mobilní povolení nepřenáší na novou dávku.

Rozhodnutí:
- První checkpoint C02b zafixoval serverový kontrakt a čistou reconciliaci. Skutečný `URLSession` klient a fyzické scénáře navážou; žádný veřejný fallback nevzniká.

Další krok:
- Vytvořit nativní iOS harness se souborovými úlohami `URLSession`, trvalou frontou a nejvýše dvěma připravenými částmi.

Navrhované další kroky:
- Po buildu a instalaci provést T043 a odděleně T047–T050 přes privátní HTTPS na fyzickém telefonu a cizí síti.

Technický důkaz:
- Python C02b 9/9, Swift 9/9, C02a regrese 10/10 a plná projektová brána 1704/1704 PASS. Fyzický iPhone test NEPROVEDENO; push ani nasazení neproběhly.

### 2026-09-17 16:53 CEST — C02b druhý checkpoint; iOS harness připraven k instalaci

Hotovo:
- Samostatná aplikace `Camino Transfer Test` vytváří pouze syntetickou dávku 96 MiB + 257 B. Má trvalý journal, Keychain token, jednu background `URLSession`, souborové uploady a nejvýše dvě připravené 8MiB části.
- Po relaunchi znovu porovnává server, 100 % bytů nevydává za ověření a mobilní povolení váže jen na aktuální dávku. Serverový snapshot s cizími či chybějícími indexy odmítá.

Rozhodnutí:
- Harness má vlastní bundle ID a nepřistupuje k Fotkám, mikrofonu ani kontejneru Camino Audio. Force quit neslibuje background pokračování; po ručním návratu proběhne reconciliace.

Další krok:
- Připojit a odemknout iPhone, lokálně podepsat a nainstalovat harness bez odinstalace Camino Audio; potom provést první řízený T043 přes privátní HTTPS.

Navrhované další kroky:
- Po T043 samostatně provést T047–T050 včetně zámku, force quit, cizí sítě, jednorázových mobilních dat a zadrženého serverového ověření.

Technický důkaz:
- Python C02b 10/10, Swift core 18/18, C02a regrese 10/10, UI simulátoru 1/1, nepodepsaný arm64 iOS build a plná projektová brána 1705/1705 PASS.
- Instalace, privátní HTTPS běh i fyzické T043/T047–T050 jsou NEPROVEDENO. Push, nasazení ani Tailscale/Funnel změna neproběhly.

### 2026-09-17 19:58 CEST — C02b nainstalováno; T043 čeká na potvrzení trasy

Hotovo:
- `Camino Transfer Test` 0.4.0 (1) byl automaticky podepsán místním vývojovým týmem, strict ověřen, nainstalován a po odemčení spuštěn na iPhonu 14 Plus / iOS 26.6.1. Samostatný bundle neodinstaloval ani neměnil Camino Audio.
- Přidán registrovaný vratný workflow pro jedinou privátní Serve cestu `/camino-c02b`, loopback receiver, bezpečné předání URL/token přes schránku, read-only důkaz a přesné ukončení se srovnáním původní konfigurace.

Rozhodnutí:
- Síťový zápis se nespustí ad hoc. Přesný `camino_c02b_t043_start` čeká na samostatné potvrzení po zobrazeném náhledu. Funnel se nezapíná a kořen Cockpitu se nesmí změnit.

Další krok:
- Po potvrzení spustit workflow, vložit URL a token do otevřeného harnessu, vytvořit syntetickou dávku a řízeně přerušit a obnovit síť u T043.

Navrhované další kroky:
- Po serverovém `verified` ověřit jediný objekt/účtenku, shodnou délku/hash a obnovu chybějících částí; potom dočasnou trasu registrovaně ukončit.

Technický důkaz:
- Podepsaný generic iOS build a `codesign --verify --deep --strict` PASS; instalace i launch PASS. Vývojový profil harnessu platí do 24. září 2026.
- Cílené workflow testy 4/4; související sada 30/30; plná projektová brána 1709/1709 PASS. Serve/Funnel zůstaly po read-only auditu beze změny; fyzické T043/T047–T050 jsou NEPROVEDENO.

### 2026-09-17 20:08 CEST — První T043 start bezpečně vrácen; entrypoint opraven

Hotovo:
- Potvrzený `camino_c02b_t043_start` skončil před otevřením receiver portu. Přímé spuštění souboru z `app/` vložilo tento adresář na začátek importní cesty a místní `app/email` zastínilo standardní Python balíček `email`.
- Fail-closed rollback odebral `/camino-c02b`, ukončil receiver a nevytvořil aktivní běh. Živý audit potom potvrdil jediný původní Serve handler, žádný listener na portu 8765 a žádnou aktivní Camino cestu.
- Receiver se nyní spouští modulově přes `python -m app.camino_chunk_receiver`; vlastnictví procesu kontroluje stejný modulový podpis a nový regresní test ověřuje, že entrypoint načte standardní `email` správně.

Rozhodnutí:
- Původní potvrzení se po opravě nepoužije automaticky. Opakování stejného síťového workflow vyžaduje nový náhled a nové samostatné potvrzení.

Další krok:
- Znovu zobrazit přesný `camino_c02b_t043_start`; po potvrzení připravit URL/token a pokračovat fyzickým T043.

Technický důkaz:
- Regresní test modulu PASS; cílená sada 31/31 a plná projektová brána 1710/1710 PASS. T043 zůstává NEPROVEDENO, Funnel ani kořen Cockpitu se nezměnily.

### 2026-09-17 20:15 CEST — Druhý start bezpečně vrácen; systémový CA trust doplněn

Hotovo:
- Druhý start potvrdil opravený receiver, ale privátní HTTPS smoke skončil na `CERTIFICATE_VERIFY_FAILED` v Python.org instalaci. Workflow znovu odebralo `/camino-c02b`, ukončilo receiver a nezanechalo aktivní běh.
- Podle LL-025 a existující macOS zkušenosti používá kontrolní `urllib` explicitní `/etc/ssl/cert.pem`; ověřování certifikátu zůstává zapnuté. Přímý tailnet Cockpit health s tímto kontextem vrátil HTTP 200.

Rozhodnutí:
- Přesný příkaz a jeho zápisový rozsah zůstaly stejné; Mílovo potvrzení se použije k dokončení opraveného startu bez třetí žádosti.

Další krok:
- Po checkpointu znovu spustit registrovaný start, vložit zkopírovanou URL a následně token do harnessu a pokračovat T043.

Technický důkaz:
- TLS regresní test zachovává `ssl.create_default_context` a načítá systémový CA bundle. Cílená sada 32/32 a plná projektová brána 1711/1711 PASS; Serve má opět jen původní handler a port 8765 neposlouchá.

### 2026-09-17 21:01 CEST — T043 PASS; fyzický zádrhel fronty opraven

Hotovo:
- T043 fyzicky přerušil upload Letovým režimem při klientských 5 %, 0/13 potvrzených částech a 2/2 připravených. Mac doložil relaci `uploading` s 0/13 přijatými částmi a bez nového finálního objektu.
- Po návratu sítě bylo přijato 13/13 částí; pro testovaný Asset vznikl jediný objekt a účtenka, oba 100 663 553 B, se shodným SHA-256. T043 je PASS v rozsahu syntetického C02b experimentu.
- Build 0.4.0 (2) opravuje zahozené souběžné impulsy reconciliace. Je strict podepsaný, nainstalovaný a spuštěný; následná celá dávka doběhla automaticky bez dalšího klepnutí.

Rozhodnutí:
- Dostupná povolená Wi-Fi může spustit přenos automaticky; `Synchronizovat nyní` je ruční provozní záloha. Souběžné impulsy se koaleskují místo tichého zahození.

Další krok:
- Po samostatném potvrzení registrovaně ukončit T043 receiver a Serve cestu; poté odděleně provést T047 se zámkem a force quit.

Technický důkaz:
- Živý receiver eviduje tři rozdílné ověřené syntetické Assety/účtenky, každý 13/13 a 100 663 553 B; celkem 301 990 659 B. Funnel je vypnutý.
- Swift 19/19, T043 ovladač + oba receivery 28/28 a UI 1/1 PASS; podepsaný build 2, strict podpis, instalace a launch PASS. Plná projektová brána 1713/1713 PASS.


### 2026-09-17 21:23 CEST — T043 ukončeno; oddělené T047 připraveno

Hotovo:
- Potvrzený stop odebral jen `/camino-c02b`, zastavil pouze vlastněný T043 receiver a doložil přesnou obnovu původního Serve. Funnel zůstal vypnutý; tři relace jsou `verified` 13/13 a jejich tři objekty/účtenky zůstaly hashově shodné, celkem 301 990 659 B.
- Připravený T047 workflow používá vlastní soukromý stav a nový prázdný receiver. Read-only audit fail-closed ověřuje relace, stav poslední relace, každý přijatý chunk a finální objekty/účtenky. iOS build 0.4.0 (2) se neměnil.

Rozhodnutí:
- Zámek a force quit se provedou jako dvě různé dávky. Po force quit se nejprve zaznamená serverový mezistav a teprve potom proběhne ruční relaunch a klientská reconciliace.

Další krok:
- Po samostatném potvrzení spustit `camino_c02b_t047_start`, vložit novou URL/token a provést nejprve dávku se zámkem.

Technický důkaz:
- Živý T043 audit: `stopped`, receiver i cesta neaktivní, Funnel vypnutý, 3/3 relace ověřené a 39/39 částí. T047 audit: `INACTIVE`, žádný běh zatím nevznikl.
- T047/T043 workflow modul 11/11, související sada 37/37 a plná projektová brána 1716/1716 PASS.

### 2026-09-18 08:23 CEST — T047 PASS; relaunch obnovil chybějící části

Hotovo:
- První T047 dávka byla testována pod zámkem telefonu. Po odemčení UI pravdivě
  ukázalo mezistav a server dokončil všech 13 částí.
- U druhé dávky byl po přijetí 1/13 částí skutečně ukončen proces. Audit po
  20 s zůstal na 1/13 bez druhého objektu; po ručním relaunchi UI ukázalo
  15 %, 1/13, 1/2 a server doplnil jen chybějící části do 13/13.
- Živé potvrzení má 2 relace, 2 ověřené objekty/účtenky, každý 100 663 553 B,
  celkem 201 327 106 B. T047 je PASS v rozsahu syntetického C02b experimentu.

Rozhodnutí:
- T047 se uzavírá až registrovaným stopem po samostatném potvrzení; T048–T050
  zůstávají oddělené.

Další krok:
- Po potvrzení spustit `camino_c02b_t047_stop`, ověřit přesnou obnovu Serve a
  potom pokračovat T048–T050.

Technický důkaz:
- `receiver_alive=true`, `private_route_exact=true`, `funnel_enabled=false`,
  `object_count=2`, `receipt_count=2`, `verified_match=true`,
  `session_count=2`, `session_verified_count=2`, `latest_session_chunks=13/13`.
- Swift 19/19, T047/T043 workflow 11/11, související sada 37/37 a plná
  projektová brána 1716/1716 PASS. Push ani nasazení neproběhly.

### 2026-09-18 08:29 CEST — T047 ukončeno a Serve obnoveno

Hotovo:
- Registrovaný stop odebral pouze `/camino-c02b`, zastavil pouze vlastněný T047
  receiver a porovnal Serve s přesným stavem před testem.
- Funnel zůstal vypnutý. Dva ověřené objekty/účtenky, dvě relace a celkem
  201 327 106 B zůstaly zachované; syntetický důkaz se nemaže.

Další krok:
- T048–T050 zůstávají samostatné a fyzicky NEPROVEDENO.

Technický důkaz:
- Živý audit po stopu: `phase=stopped`, `receiver_alive=false`,
  `funnel_enabled=false`, `object_count=2`, `receipt_count=2`,
  `verified_match=true`, `session_count=2`, `session_verified_count=2`,
  `latest_session_chunks=13/13`.

### 2026-09-19 11:12 CEST — T048 připraveno; nejprve syntetické T049

Hotovo:
- Oddělené potvrzované workflow T048 a T049 mají vlastní soukromý stav a
  bezpečný start, kontrolu, token i stop. Žádný nový receiver ani Serve cesta
  nebyly spuštěny; T047 důkazy zůstávají zachované.
- `Camino Transfer Test` 0.4.0 (3) před mobilním grantem ukazuje jednu dávku
  o 100 663 553 B a upozornění na další bajty při retry. Všechny požadavky
  mají per-request síťovou politiku. Build 3 je podepsaný a nainstalovaný,
  Camino Audio zůstává nainstalované. Pokus o launch blokoval zámek iPhonu.

Rozhodnutí:
- Na Mílův pokyn půjde nejprve T049 bez cizí Wi-Fi, potom T048 při dostupné
  jiné Wi-Fi. Jde jen o změnu pořadí, nikoli o snížení akceptačních kritérií.

Další krok:
- Odemknout iPhone, ověřit launch buildu 3 a po samostatném potvrzení spustit
  registrované T049 workflow pro fyzickou syntetickou mobilní zkoušku.

Navrhované další kroky:
- Po T049 receiver/cestu registrovaně ukončit; T048 provést odděleně při jiné
  Wi-Fi včetně portálu, bude-li dostupný. T050 zůstává samostatné.

Technický důkaz:
- Swift 20/20, Python workflow 13/13, iOS UI 1/1, podepsaný iOS build a
  strict podpis PASS; plná projektová brána 1718/1718 PASS.
- Read-only T048/T049 `INACTIVE`; T047 `stopped`, receiver/cesta neaktivní,
  Funnel vypnutý, dva objekty/účtenky hashově shodné. Fyzické T048–T050
  NEPROVEDENO. Harness nepokrývá skutečné nové video pro plný T049.

### 2026-09-19 11:45 CEST — T049 syntetická mobilní část ověřena a ukončena

Hotovo:
- Při zkoušce na iPhonu bez mobilního grantu nová dávka zůstala na 0 %, 0/13;
  ruční synchronizace neodeslala serveru relaci. Zrušení potvrzovacího dialogu
  zachovalo zákaz. Po vědomém povolení této jediné dávky Mac ověřil 13/13 částí,
  jeden objekt a účtenku, 100 663 553 B a shodný SHA-256; Míla viděl
  `Ověřeno na Macu`.
- Další syntetická dávka povolení nezdědila: po ruční synchronizaci zůstala na
  0 %, 0/13, 0/2. Server nadále evidoval pouze první ověřenou relaci. T049
  bylo potvrzeně ukončeno; receiver/cesta vypnuté, Serve přesně obnovený,
  Funnel vypnutý a syntetický důkaz zachovaný.

Rozhodnutí:
- Bez změny kritérií: syntetický mobilní průchod je úspěšný, plné T049 se
  skutečně nově pořízeným videem zůstává otevřené. Samotná shoda s návrhem
  nevyžaduje opravu kódu.

Další krok:
- Při dostupné cizí Wi-Fi provést oddělený T048 podle připraveného postupu.

Navrhované další kroky:
- Není-li cizí Wi-Fi dostupná, po samostatném zadání připravit T050 se
  zadrženým serverovým ověřením; nic z něj zatím nespouštět.
- Plné T049 s novým skutečným videem vrátit až do integrované aplikace.

Technický důkaz:
- Registrovaný audit po stopu: `phase=stopped`, `receiver_alive=false`,
  `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`,
  `session_verified_count=1`, `latest_session_chunks=13/13`, `object_count=1`,
  `receipt_count=1`, `verified_match=true`, `verified_byte_count=100663553`.
  Úplné znění fyzického dialogu nebylo opsáno; spotřeba operátora nebyla měřena.

### 2026-09-19 17:33 CEST — T050 připraveno, fyzicky nespouštěno

Hotovo:
- Pro T050 vznikl oddělený potvrzovaný soukromý workflow a postup. Přijímač
  zadrží ověření pouze tohoto běhu o 14 s po 13/13 a stavu `verifying`, poté
  provede nezměněnou kontrolu délky a SHA-256. iPhone build 0.4.0 (3) se nemění.
- T049 je nadále bezpečně zastavené; T050 má prázdný neaktivní stav. Žádná
  nová Serve cesta, receiver ani mobilní přenos se přípravou nespustily.

Rozhodnutí:
- Míla chce T050 zkusit před T048, protože cizí Wi-Fi není k dispozici.
  Fyzický PASS vyžaduje současný telefonní a serverový mezistav, ne jen
  konečnou účtenku. Samostatné potvrzení startu i tokenu zůstává povinné.

Další krok:
- Po samostatném potvrzení spustit `camino_c02b_t050_start`, předat novou
  URL/token a provést řízený fyzický test podle `C02b_T050_FIELD_PLAN.md`.

Navrhované další kroky:
- Po testu samostatně potvrdit stop a ověřit obnovu Serve; T048 provést až při
  dostupné cizí Wi-Fi.

Technický důkaz:
- Cílená sada 32/32 a plná projektová brána 1719/1719 PASS. Read-only T050
  `INACTIVE`, T049 `stopped` s jedním zachovaným ověřeným objektem/účtenkou.
  Pozorovací okno 14 s je kratší než klientský timeout 20 s; fyzický T050
  NEPROVEDENO.

### 2026-09-19 18:06 CEST — T050 fyzicky PASS v syntetickém rozsahu

Hotovo:
- První průchod měl správné finále, ale nezachytil souběžný stav telefonu a
  serveru; nebyl vydán za PASS. Po potvrzeném stopu vznikl nový oddělený běh.
- Ve druhém průchodu video iPhonu zachytilo `Ověřuji`, 100 % a 13/13 v době,
  kdy server evidoval `verifying`, 13/13 a ještě žádný objekt ani účtenku.
  Teprve následné serverové ověření délky a SHA-256 vytvořilo jediný objekt a
  účtenku; telefon poté ukázal `Ověřeno na Macu`.
- Oba běhy byly samostatně potvrzeným stopem ukončeny. Testovací Serve cesta a
  vlastněný receiver jsou pryč, původní Serve přesně obnovený, Funnel vypnutý;
  syntetické důkazy zůstaly zachované, soukromé video není v Gitu.

Rozhodnutí:
- Míla výslovně zvolil opakování s videem místo přijetí pouhého finále.
  Automatický start čerstvé povolené dávky po návratu aplikace není schválené
  produktové rozhodnutí; jeho UX se vyjasní samostatně.

Další krok:
- T048 na cizí Wi-Fi podle připraveného postupu, až bude dostupná.

Navrhované další kroky:
- Před dalším mobilním během oddělit vědomý start nové dávky od bezpečné obnovy
  již rozpracovaného přenosu a prověřit krátké `Vyžaduje pozornost` před retry.
- Plné T049 s novým skutečným videem až v integrované aplikaci.

Technický důkaz:
- Server `verifying` 17:58:22–17:58:36 CEST bez objektu/účtenky, video v tomto
  okně `Ověřuji`; po něm 1/1 ověřená relace/objekt/účtenka, 100 663 553 B a
  shodný SHA-256. Druhý běh po stopu `phase=stopped`, `receiver_alive=false`,
  `private_route_exact=false`, `funnel_enabled=false`. iPhone build 0.4.0 (3)
  beze změny; předchozí automatická brána 1719/1719 PASS, neopakovaná.

### 2026-09-19 19:31 CEST — Schválené p+n a dorovnání Git historie

Hotovo:
- Funkční oprava prvního mobilního startu buildu 4 je po potvrzeném p+n na
  GitHubu a v řízeně restartovaném Cockpitu. Oba profily jsou čisté a navázané
  na stejný místní `main`.

Rozhodnutí:
- Dva souběžné soví commity měly shodný obsah před změnou i po ní. Běžné
  sloučení zachovalo obě historie; žádná větev nebyla přepsána.

Další krok:
- Podepsat a nainstalovat build 4 a na nové syntetické dávce fyzicky ověřit
  vědomý první start a obnovu již zahájeného přenosu.

Navrhované další kroky:
- T048 provést při dostupné cizí Wi-Fi; plné T049 se skutečně novým videem až
  v integrované aplikaci. T050 znovu jen při nové pochybnosti o finalizaci.

Technický důkaz:
- GitHub batch 17 commitů po plné bráně 1719/1719. Soukromá účtenka
  nasazení funkčního commitu `4a965ccb`: nový PID, shodný kódový otisk a
  smoke 5/5. Konečný stav dokumentačního checkpointu určuje živý audit.

### 2026-09-19 21:35 CEST — Build 4 na iPhonu, cílená zkouška připravená

Hotovo:
- Build `Camino Transfer Test` 0.4.0 (4) byl podepsán a instalován jako
  aktualizace stejné aplikace na iPhonu 14 Plus. Starší podepsaný build 3 na
  Macu a samostatná aplikace Camino Audio zůstaly zachované.
- Připravený postup odděluje nulový přenos po mobilním grantu od vědomého
  prvního startu a automatické obnovy stejné rozpracované dávky.

Rozhodnutí:
- Nové produktové rozhodnutí nevzniklo. Samostatný privátní T049 receiver
  se spustí až pro fyzický test; předchozí důkazy se zachovají.

Další krok:
- Spustit nový registrovaný T049 běh a provést část A/B na nové syntetické
  dávce podle `C02b_BUILD4_FIRST_START_FIELD_PLAN.md`.

Navrhované další kroky:
- Po výsledku odděleně ověřit T048 na cizí Wi-Fi; plné T049 se skutečným
  videem zůstává pro integrovanou aplikaci.

Technický důkaz:
- Podepsaný iOS build exit 0, strict podpis a platný profil obsahující
  připojený iPhone PASS; CoreDevice hlásí verzi 0.4.0 (4). T049/T050 jsou
  read-only ověřené jako `stopped`, bez vlastní trasy a s vypnutým Funnelem.
  Aplikace po instalaci nebyla spuštěna; fyzický PASS zatím není.

### 2026-09-19 22:11 CEST — Cílený fyzický test buildu 4; T049 ukončené

Hotovo:
- Část A PASS: mobilní grant, návrat z Ovládacího centra a obnova sítě
  nespustily dosud nezahájenou syntetickou dávku. Telefon zůstal na 0/13,
  server na 0 relacích, objektech a účtenkách.
- V části B vědomý start vytvořil jednu relaci. Po přerušení při 1/13 a 8/13
  byla aplikace nuceně ukončena; po otevření s dostupnou sítí dokončila stejnou
  relaci bez dalšího stisku. Telefon potvrdil `Ověřeno na Macu`, server jednu
  ověřenou relaci, objekt a účtenku, 13/13 a shodnou délku i SHA-256.
- Potvrzený stop odstranil pouze vlastní Serve cestu a receiver, přesně
  obnovil původní Serve a zachoval důkaz. Funnel zůstal vypnutý.

Rozhodnutí:
- Úplný PASS plánu B se netvrdí: při výpadku došlo k dalšímu stisku
  synchronizace a aplikace se po nuceném ukončení znovu otevřela až s dostupnou
  sítí. Otevření bez sítě a jeho UI zůstalo neověřené. Míla zvolil neopakovat
  další mobilní dávku jen kvůli této mezeře, protože Letový režim odpojuje i
  chat používající data iPhonu. Pozorované chování nevyžaduje změnu kódu.

Další krok:
- T048 až při dostupné cizí Wi-Fi, na novém potvrzeném privátním receiveru
  a syntetické dávce podle `C02b_T048_T049_FIELD_PLAN.md`.

Navrhované další kroky:
- Plné T049 s novým skutečným videem až v integrované aplikaci; T050 opakovat
  jen při nové pochybnosti o finalizaci.

Technický důkaz:
- Audit po stopu: `phase=stopped`, `receiver_alive=false`,
  `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`,
  `session_verified_count=1`, `latest_session_chunks=13/13`, `object_count=1`,
  `receipt_count=1`, `verified_byte_count=100663553`, `verified_match=true`.

### 2026-09-19 23:25 CEST — C03a datový kontrakt a soukromí

Hotovo:
- Referenční model stabilních offline ID, vazeb Moment/Asset, metadatových a
  textových revizí, místního času s offsetem, nejistého importu a volitelné
  polohy. Nová Úvaha je v doménové logice `owner_only`; vědomé vložení do
  deníku je prioritní revize. Viewer výběr používá jen poslední serverem
  přijatou revizi a neznámý nebo konfliktní stav zavře.

Rozhodnutí:
- C03a nepřepisuje v0.5, nemigruje C01/C02 prototypy a netvrdí fyzický PASS
  T005/T008/T027–T032/T039/T041/T096. Lokální zámek čeká na přijetí serverem;
  cizí kopii už nelze odvolat.

Další krok:
- C03b: verzované API a mapování revizí/konfliktů do persistence.

Navrhované další kroky:
- C04/C05/C08 vynutí soukromí na telefonu, serveru a Vieweru včetně starých
  mediálních URL. T048 zůstává oddělený při dostupné cizí Wi-Fi.

Technický důkaz:
- Nové syntetické testy 9/9 a plná projektová brána 1728/1728 PASS. Bez
  iPhone instalace, push a nasazení v tomto kroku.

### 2026-09-20 08:52 CEST — C03b lokální API v1 a revizní úložiště

Hotovo:
- Owner API v1 a přesné JSON schéma přijímají souvislé metadata/textové
  operace. Soukromé SQLite uchovává revize, účtenky a konflikty i po restartu;
  stejné bajty se potvrdí idempotentně. Referenční výběr pro Viewer se při
  konfliktu nebo obnově uzavře.
- Řízená změna epochy vyžaduje porovnání inventáře Momentů a žádné položky
  sama nemaže ani neodblokuje.

Rozhodnutí:
- Na Mílův pokyn jde o lokální referenční C03b bez síťového listeneru.
  Produkční identita, média, záloha a jejich fyzické testy zůstávají v C05/C06.

Další krok:
- Po samostatném zadání navázat C04a místním úložištěm a hlavní obrazovkou.

Navrhované další kroky:
- C05a ověří produkční server, média a konflikty; C06b skutečnou obnovu.
- T048 při dostupné cizí Wi-Fi, plné T049/T053/T058 až v integrované aplikaci;
  C08 vynutí aktuální oprávnění k Viewer médiím.

Technický důkaz:
- C03b syntetické kontraktní testy 12/12, OpenAPI JSON a 21 komponent schématu
  validní, plná projektová brána 1740/1740 PASS.
- Bez iPhone instalace, push a nasazení.

### 2026-09-20 09:30 CEST — C04a offline iPhone základ

Hotovo:
- Nové místní Trip/Day/Moment, Zkouška, značka a hlavní obrazovka. D02
  výchozí `diary` a trvalá volba; U15 samostatná Úvaha `owner_only`.
- C01c audio beze změny, trvalý záměr před mikrofonem a vazba validované
  dokončené session na Moment po restartu. Komentář má soukromí pro celý záznam.

Rozhodnutí:
- Míla zadal C04a. Nový bundle a kontejner nemigrují prototypová média;
  C03b není připojené síťové API.

Další krok:
- C04b foto/video; fyzický iPhone průchod C04a před přijetím audio chování.

Navrhované další kroky:
- C04d detail a vědomá revize Úvahy, C05a produkční server. T048 a plné T049
  zůstávají oddělené podle svých podmínek.

Technický důkaz:
- Swift 8/8, UI simulátoru 1/1, nepodepsaný iOS build a plná brána
  1740/1740 PASS. Žádná fyzická instalace, push ani nasazení.

### 2026-09-20 10:00 CEST — C04b foto/video a výslovné vazby

Hotovo:
- Aplikace ukládá samostatné foto/video a dovoluje připojit další médium
  nebo komentář ke konkrétnímu Momentu se stejným soukromím. Originály jsou
  místní, neznámé a rozpracované soubory se nemažou. Tiché a částečné video
  mají pravdivý stav.

Rozhodnutí:
- C04b navazuje na C04a bez serveru. Míla zadal instalaci/test, ale nové
  bundle ID potřebuje provisioning profil. Profily prototypů se nepoužijí.

Další krok:
- Zajistit podpis nového ID, instalovat na iPhone a fyzicky projít
  T007–T014/T060; syntetické testy nejsou jejich přijetí.

Navrhované další kroky:
- C04d detail/revize a C05a privátní produkční spojení. T048 a plné T049
  zůstávají podle samostatných podmínek.

Technický důkaz:
- Swift 13/13, UI test simulátoru, nepodepsaný iOS build a plná brána
  1740/1740 PASS. Podepsané
  sestavení bez profilu selhalo. Bez instalace, fyzického PASS, push a nasazení.

### 2026-09-20 12:12 CEST — C04b vývojově na iPhonu

Hotovo:
- Integrovaná aplikace 0.1.0 (1) je podepsaná, nainstalovaná a spuštěná
  na iPhonu 14 Plus. Prototypy se nepřepisovaly.

Rozhodnutí:
- Instalace neuzavírá C04b hardware akceptaci; fyzické T007–T014/T060
  čekají na pozorování a přehrání skutečných médií.

Další krok:
- Projít testovací plán na nové Zkoušce a zapsat PASS/FAIL po scénářích.

Navrhované další kroky:
- C04d detail/revize a C05a produkční přenos; plné T049 až s novým videem.

Technický důkaz:
- Podpis a profil pro přesné ID/telefon, instalace i launch ověřeny; profil
  do 27. 9. 2026. Fyzické testy zatím NEOVĚŘENÉ. Bez push a nasazení.

### 2026-09-20 12:27 CEST — C04b úspěšný snímek po restartu

Hotovo:
- Na iPhonu byla fotografie uložena a zůstala v detailu Momentu po úplném
  zavření a opětovném spuštění nové aplikace.

Rozhodnutí:
- T007 má fyzicky ověřený úspěšný zápis/restart, ale chyba zápisu na
  zařízení nebyla vyvolána; celý test zůstává částečný.

Další krok:
- T008: rozlišit dva rychlé snímky a explicitní komentář/foto u prvního.

Navrhované další kroky:
- T011–T014 skutečné video a zbývající bezpečné fyzické scénáře.

Technický důkaz:
- Mílovo pozorování a nový proces při relaunchi; bez kopírování média,
  push a nasazení.

### 2026-09-20 — C04b T008 průběžně

Hotovo:
- Na iPhonu jsou dva samostatné řádky Fotografie po dvou rychlých snímcích
  a komentář je u prvního.

Rozhodnutí:
- T008 není uzavřený: zbývá připojení další fotografie a kontrola po
  restartu.

Další krok:
- Ověřit dvě fotografie a komentář u prvního Momentu, druhý beze změny,
  následně trvalost vazeb po restartu.

Navrhované další kroky:
- T011–T014 a další bezpečné fyzické scénáře.

Technický důkaz:
- Mílovo pozorování; kontrolní brána 1740/1740 PASS. Bez push a nasazení.

### 2026-09-20 — C04b T008 fyzický PASS

Hotovo:
- Dva rychlé snímky zůstaly samostatnými Momenty; první má dvě fotografie
  a komentář, druhý jednu fotografii. Vazby přežily úplné zavření a nové
  spuštění podle Mílova potvrzení.

Rozhodnutí:
- T008 PASS na fyzickém iPhonu 14 Plus. T007 chybový zápis a ostatní
  fyzické scénáře zůstávají otevřené.

Další krok:
- T011: nahrát video se zvukem, zastavit, znovu spustit aplikaci a ověřit
  jediný klip, obraz, zvuk a délku.

Navrhované další kroky:
- T012–T014, T009, bezpečná část T060 a poté C04d/C05a.

Technický důkaz:
- Mílovo fyzické pozorování bez kopie obsahu; gate 1740/1740 PASS. Bez push.

### 2026-09-20 — C04b T011 fyzický PASS

Hotovo:
- Video zůstalo po návratu přehratelné s obrazem a zvukem bez duplicit;
  délka se ukazuje v přehrávači během přehrávání.

Rozhodnutí:
- T011 PASS dle Mílova fyzického pozorování. Trvale viditelná délka v
  detailu je volitelné zlepšení UI, ne blokátor akceptace.

Další krok:
- T012 výška/šířka, po restartu ověřit orientaci a ořez obou klipů.

Navrhované další kroky:
- T013–T014, T009 a bezpečná část T060; poté C04d/C05a.

Technický důkaz:
- Přímé hlášení Míly na fyzickém iPhonu, bez kopie média a bez push.

### 2026-09-20 — C04b T012 fyzický PASS

Hotovo:
- Klipy na výšku a na šířku po restartu přehrány se správnou orientací
  a bez chybného ořezu podle Mílova potvrzení.

Rozhodnutí:
- T012 PASS na fyzickém iPhonu; další scénáře C04b čekají.

Další krok:
- T013 vědomé video bez zvuku a chování při odepřeném mikrofonu.

Navrhované další kroky:
- T014, T009, bezpečná část T060; poté C04d/C05a.

Technický důkaz:
- Mílovo pozorování bez kopie média, bez push a nasazení.

### 2026-09-20 — C04b T013 částečný

Hotovo:
- Výslovně tiché video má štítek Bez zvuku před Start, během záznamu
  i v detailu po restartu podle Mílova potvrzení.

Rozhodnutí:
- Celý T013 zůstává otevřený do testu s odepřeným mikrofonem.

Další krok:
- Při odepřeném mikrofonu ověřit odmítnutí běžného videa bez skrytého
  přechodu na ticho a možnost výslovného tichého klipu.

Navrhované další kroky:
- T014, T009, bezpečná část T060; potom C04d/C05a.

Technický důkaz:
- Uživatelské pozorování na fyzickém iPhonu; bez kopie média či push.

### 2026-09-21 08:28 CEST — Camino p+n a předání Human–Adam

Hotovo:
- Dokončené C03a/C03b/C04a/C04b změny a fyzické výsledky do částečného T013
  jsou v dávkovém p+n. Soví produkční commit byl sloučen bez přepisu historie.
- UI testy staršího audio prototypu používají ignorovanou místní podpisovou
  konfiguraci; osobní tým není ve sledovaném projektu.
- Main, GitHub a oba profilové workspaces jsou čisté a zarovnané; Cockpit běží
  z téhož main.

Rozhodnutí:
- Míla autorizoval všechno p+n a čistý návratový bod pro Human–Adam. T013 je
  nadále jen částečný a neprovedené fyzické testy se nepovyšují na PASS.

Další krok:
- Dokončit T013, potom T014, T009 a bezpečnou část T060; následně C04d/C05a.

Navrhované další kroky:
- T048 na cizí Wi-Fi; plné T049 až s reálným videem a produkčním serverem.

Technický důkaz:
- Plná brána 1740/1740 PASS; GitHub batch a simple-main deployment receipt
  potvrzují přesný head, nový proces a smoke 5/5.

### 2026-09-21 20:46 CEST — T048 na cizí Wi-Fi a bezpečný stop

Hotovo:
- Běžná syntetická dávka na fyzickém iPhonu a jiné Wi-Fi doběhla do 13/13 a
  ověřeného finále.
- Druhá dávka při vypnutí Wi-Fi zůstala na klientu i serveru 2/13 bez objektu;
  po návratu se bez dalšího stisku doplnily pouze chybějící části.
- Třetí dávka s vypnutým tailnetem nevytvořila serverovou relaci ani veřejný
  fallback; po obnovení Tailscale se bez dalšího stisku dokončila.
- Registrovaný stop ukončil receiver i vlastní trasu, přesně obnovil původní
  Serve a ponechal Funnel vypnutý.

Rozhodnutí:
- T048 má omezený PASS pro tři provedené podscénáře. Captive portal zůstává
  NEOVĚŘENO, protože použitá síť jej neměla; nejde o úplný produkční PASS.
- Důkaz je syntetický a nenahrazuje produkční server, zálohu médií ani Viewer.

Další krok:
- Dokončit T013 s odepřeným mikrofonem, potom T014, T009 a bezpečnou část T060;
  následně C04d a C05a.

Navrhované další kroky:
- Captive portal doplnit pouze při přirozeně dostupné síti; tři doložené
  podscénáře bez nové pochybnosti neopakovat.

Technický důkaz:
- Finální audit: T048 zastavený, receiver/cesta neaktivní, Funnel vypnutý,
  3/3 relace ověřené, 39/39 částí, 3 objekty, 3 účtenky, 301 990 659 B a
  shodný hash. Kód se neměnil; automatické testy se neopakovaly.

### 2026-09-21 21:15 CEST — C04b T013 fyzický PASS

Hotovo:
- Míla po dvouvětvém fyzickém postupu potvrdil T013 jako odpovídající
  předpokladu: při odepřeném mikrofonu se běžné video samo nepřepnulo na tiché
  a výslovně zvolený tichý klip zůstal dostupný a označený.

Rozhodnutí:
- T013 je fyzicky PASS a nevyžaduje opravu kódu.
- T048 se znovu neotevírá; jeho tři dostupné podscénáře jsou hotové a captive
  portal zůstává NEOVĚŘENO do přirozeně vhodné sítě.

Další krok:
- T014: během krátkého videa odejít z aplikace nebo zamknout telefon a po
  návratu ověřit použitelný dokončený klip, nebo pravdivě částečný stav bez
  tvrzení, že kamera stále nahrává.

Navrhované další kroky:
- Po T014 provést T009 a bezpečnou část T060; potom C04d a C05a.

Technický důkaz:
- Přímé potvrzení Míly na fyzickém iPhonu; bez kopírování média, změny kódu,
  opakování automatických testů, push a nasazení.

### 2026-09-21 21:23 CEST — C04b T014 větev zámku PASS

Hotovo:
- Míla během rozběhnutého videa zamkl telefon. Po návratu byl klip
  přehratelný a aplikace jej pravdivě označila jako částečný s upozorněním,
  že konec může chybět.

Rozhodnutí:
- Větev T014 se zámkem telefonu je PASS: aplikace neslibovala pokračující
  kameru ani úplný konec, ale zachovala použitelný rozsah. Oprava není potřeba.
- Celý T014 zůstává částečný do samostatného odchodu z aplikace a systémového
  přerušení.

Další krok:
- Spustit nové krátké běžné video, během záznamu přejít na plochu nebo do jiné
  aplikace bez nuceného ukončení, po několika sekundách se vrátit a ověřit,
  že záznam neběží a klip je použitelný úplný nebo pravdivě částečný.

Navrhované další kroky:
- Potom samostatné bezpečné systémové přerušení T014, T009 a bezpečná část
  T060; následně C04d a C05a.

Technický důkaz:
- Přímé pozorování Míly na fyzickém iPhonu; bez kopie klipu, změny kódu,
  automatických testů, push a nasazení.

### 2026-09-21 21:35 CEST — C04b T014 odchod z aplikace PASS

Hotovo:
- Míla během nového rozběhnutého videa odešel z aplikace bez jejího nuceného
  ukončení. Po návratu byl klip přehratelný a opět pravdivě označený jako
  částečný s možným chybějícím koncem.

Rozhodnutí:
- Větev T014 s odchodem z aplikace je PASS a nevyžaduje opravu kódu.
- Celý T014 zůstává částečný pouze do samostatného systémového přerušení.

Další krok:
- Během nového krátkého běžného videa vyvolat bezpečné systémové přerušení,
  po návratu ověřit, že kamera sama nepokračuje, a přehrát zachovaný klip.

Navrhované další kroky:
- Po dokončení T014 provést T009 a bezpečnou část T060; potom C04d a C05a.

Technický důkaz:
- Přímé pozorování Míly na fyzickém iPhonu; bez kopie klipu, změny kódu,
  automatických testů, push a nasazení.

### 2026-09-21 21:43 CEST — C04b T014 fyzický PASS

Hotovo:
- Míla samostatně ověřil zámek telefonu, odchod z aplikace a přijatý krátký
  hovor během tří nových rozběhnutých videí. Záznam se pokaždé ukončil,
  sám nepokračoval a zachovaný klip byl přehratelný a pravdivě označený
  jako částečný. Hovor se do videa nezaznamenal.

Rozhodnutí:
- Celý T014 je fyzicky PASS. Výsledek odpovídá návrhu a nevyžaduje opravu
  kódu.

Další krok:
- T009: v Nastavení iPhonu odepřít Caminu kameru, v aplikaci otevřít `Foto`
  a ověřit vysvětlení se `Zpět`; `Komentář` a místní deník musí dál
  fungovat.

Navrhované další kroky:
- Po T009 provést bezpečnou část T060; potom C04d a C05a.

Technický důkaz:
- Přímé pozorování Míly na fyzickém iPhonu; bez kopírování média,
  změny kódu, opakování automatických testů, push a nasazení.

### 2026-09-21 22:04 CEST — C04b T009 fyzický PASS

Hotovo:
- Míla potvrdil celý fyzický scénář T009: při odepřené kameře
  otevření `Foto` zobrazilo vysvětlení a `Zpět`; `Komentář` i místní
  deník dál fungovaly.

Rozhodnutí:
- T009 je fyzicky PASS. Výsledek odpovídá návrhu a nevyžaduje opravu kódu.

Další krok:
- Provést pouze bezpečnou část T060: vrátit kamerové oprávnění, bez
  zaplňování úložiště a tepelného stresu pořídit a normálně ukončit
  krátké video, ověřit absenci falešného varování, přehratelnost a že se
  nic nesmazalo. Plné T060 zůstane částečné bez nízkého místa a tepelného
  stresu; pravdivé přerušení už dokládá T014.

Navrhované další kroky:
- Po bezpečné části T060 následují C04d a C05a; rizikovou část T060
  neprovádět bez nového bezpečného plánu.

Technický důkaz:
- Přímé potvrzení Míly na fyzickém iPhonu; bez kopírování média,
  změny kódu, opakování automatických testů, push a nasazení.

### 2026-09-21 22:12 CEST — C04b T060 bezpečná část PASS

Hotovo:
- Míla při běžném volném místě dokončil bezpečný fyzický průchod:
  bez falešného varování, s normálně dokončeným a přehratelným krátkým
  videem a se zachovanými staršími položkami. Pravdivé přerušení dokládá
  dřívější T014.

Rozhodnutí a rizika:
- Bezpečná část T060 je fyzicky PASS. Celý T060 zůstává částečný,
  protože skutečné nízké místo před/během audia, videa a textu nebylo
  vyvoláno.
- Read-only audit kódu našel přímé prahy u foto/videa, ale bez
  injektovatelné kapacity a prahových automatických testů. Audio/text nemají
  shodnou politiku doloženou a tepelný stav se nesleduje.

Další krok:
- Po Mílově souhlasu doplnit malý bezpečně simulovatelný C04b hardening.
  Hlavní iPhone uměle nezaplňovat ani nezahřívat; skutečný fyzický low-space
  test ponechat postradatelnému zařízení nebo přirozenému stavu.

Navrhované další kroky:
- Po technickém hardeningu C04b pokračovat C04d a C05a.

Technický důkaz:
- Přímé potvrzení Míly na fyzickém iPhonu a read-only kontrola
  `CaminoMediaVault.swift`, `CaminoViewModel.swift` a Swift testů. Bez změny
  aplikačního kódu, kopírování média, push a nasazení.

### 2026-09-21 22:36 CEST — C04b low-space/thermal hardening

Hotovo:
- Kapacita úložiště je injektovatelná a společná politika pokrývá značku,
  foto, audio i video. Varuje pod 2 GiB, blokuje nový video Start pod 1 GiB,
  foto/audio pod 512 MiB a pod rezervou bezpečně dokončí běžící audio/video.
- Tepelná politika videa při `serious` varuje a při `critical` blokuje
  nový Start nebo bezpečně ukončí běžící klip. Kvalita se skrytě nemění.
- Debug simulátor umí řízenou kapacitu a teplotu; produkční cesta dál používá
  skutečný stav systému. Žádná větev automaticky nemaže originály.

Rozhodnutí a rizika:
- Automatizovaná bezpečnostní politika je PASS, ale nejde o fyzický PASS
  nízkého místa ani tepelného stresu. Hardening nebyl instalován na iPhone;
  celý T060 zůstává částečný.
- Hlavní iPhone se uměle nezaplňuje ani nezahřívá. Skutečný low-space test až
  na postradatelném zařízení nebo při přirozeném stavu.

Další krok:
- Pokračovat C04d a potom C05a. Případná instalace tohoto hardeningu na iPhone
  je samostatný potvrzený krok.

Navrhované další kroky:
- C04d dokončí detail a vědomou revizi Úvahy; C05a připojí produkční API.

Technický důkaz:
- Swift 17/17, UI simulátoru 3/3, nepodepsaný simulátorový a generic iOS build
  i plná projektová brána 1740/1740 PASS. UI při 400 MiB odmítlo velké
  záznamy, uložilo značku přes restart a
  při kritické teplotě odmítlo video; integrační test zachoval starší originál
  byte-for-byte. Bez push, nasazení a instalace na telefon.

### 2026-09-23 21:35 CEST — C04d instalace a fyzická přejímka

Hotovo:
- Zdrojový checkpoint `e3868100` po plné bráně 1740/1740 byl pushnut na
  `origin/main`. Podepsané Camino 0.1.0 (2) prošlo strict kontrolou, aktualizací
  stejného bundle ID, instalací a spuštěním na iPhonu 14 Plus / iOS 26.6.1.
- Starší C04b data a média zůstala dostupná. Míla fyzicky potvrdil PASS pro
  T010, obě větve T019, T020, T021, T026, T030, T039, T040, T041 a T096.
  Použitá změna vstupu v T020 byla z mikrofonu iPhonu na AirPods s mikrofonem.

Rozhodnutí a rizika:
- C04d je přijaté v dostupném lokálním a na zařízení ověřitelném rozsahu;
  z výsledků nevznikla potřeba opravy kódu.
- T038 zůstává jen synteticky a automatizovaně ověřené. Bez produkční AI nebyl
  možný fyzický end-to-end důkaz opožděného automatického textu. Serverové
  přijetí a Viewer u T040/T096 zůstávají C05/C08; `čeká na server` není potvrzení.

Další krok:
- Navázat C05a produkčním privátním API, přičemž se zachová fail-closed U15,
  jeden zapisující iPhone, odvolatelné přihlášení, idempotence, ověření médií
  a pravdivé rozlišení místní fronty od serverového přijetí.

Navrhované další kroky:
- Po C05a doplnit integrační serverové důkazy; T038 dokončit až s reálnou
  opožděnou AI. Plné T060 ani captive portal T048 bez vhodné podmínky nevyvolávat.

Technický důkaz:
- `C04d_IPHONE_TEST_PLAN.md` obsahuje jednotlivé výsledky a hranice. Strict
  podpis, CoreDevice instalace/launch a inventář verze 0.1.0 (2) prošly; obsah
  testovacích médií zůstal mimo Git. Cockpit se v tomto kroku nenasazoval.

### 2026-09-23 22:16 CEST — C05a lokální produkční přijímač

Hotovo:
- FastAPI adaptér spojil C03b metadata s obnovitelnými částmi a ověřenou
  finalizací. Přijatý Asset manifest je autorita a stav `verified` vyžaduje
  serverový hash celého objektu i trvalou účtenku.
- Odvolatelné owner tokeny se zakládají mimo síťové API a ukládají jen jako
  hash. Listener odmítá vše kromě loopbacku; neznámé bajty se nemažou.

Rozhodnutí a rizika:
- T043–T046/T052/T061 mají lokální serverový syntetický důkaz, nikoli nový
  fyzický nebo produkční PASS. Služba, privátní cesty/token, Tailscale Serve,
  C05b klient, push a nasazení nebyly provedeny.

Další krok:
- Samostatně připravit privátní cesty/token a loopback smoke nad prázdnými
  syntetickými daty; potom zvlášť rozhodnout o Serve a C05b.

Technický důkaz:
- Core + C03b 23/23, FastAPI 4/4, validní OpenAPI, veřejný bind odmítnut exit 2
  a plná projektová brána 1751/1751 PASS.

### 2026-09-23 22:59 CEST — C05a loopback smoke PASS

Hotovo:
- Míla samostatně potvrdil uložený registrovaný příkaz. Běh
  `20260923T205907Z-e64b0346` prošel 12/12 kontrolami přes skutečné HTTP na
  loopbacku: 1 048 699 B v 5 částech, autorizace, C03b metadata, idempotentní
  retry, blokace časné finalizace, serverový hash, opakovaná finalizace,
  odvolání obou tokenů a restart se zachovaným `verified` stavem.

Rozhodnutí a rizika:
- Syntetická data a redigovaná privátní účtenka zůstávají zachované. Vlastněný
  proces skončil; Serve, Funnel, iPhone, push ani nasazení se nezměnily.
- PASS nepředstavuje produkční přenos, spravovanou službu ani zálohu.

Další krok:
- Nově a samostatně rozhodnout o privátním Tailscale Serve; C05b iPhone klient
  následuje jako oddělený krok.

### 2026-09-24 22:47 CEST — C05b fyzické přijetí a bezpečný stop

Hotovo:
- Integrované Camino 0.1.0 (3) zachovalo starší data a fyzicky prošlo T051,
  T047-A/B, dostupnou část T048, T049, T050, T052, T053, T058 a pause.
- Session-owned služba je po registrovaném stopu vypnutá, cesta odebraná,
  token odvolaný a původní Serve přesně obnovený; Funnel zůstal vypnutý.

Rozhodnutí:
- C05b je přijato v akceptačním rozsahu. Captive portal T048 zůstává
  `NEOVĚŘENO`; spravovaný provoz, druhá kopie a Viewer jsou další etapy.

Další krok:
- Navázat C05c stavovým UX.

Navrhované další kroky:
- C06a/C06b otevřít samostatným rozhodnutím; captive portal testovat jen při
  bezpečné dostupnosti a T038 až s reálnou opožděnou AI.

Technický důkaz:
- Konečný stop: 104 operací, 41 Momentů, 45 Assetů, 45/45 médií,
  214 555 219 B, 0 aktivních tokenů. Uzavírací plná brána 1770/1770 PASS.

### 2026-09-24 23:23 CEST — C05c pravdivé stavové osy

Hotovo:
- Uložení a přenosy má čtyři samostatné pravdy: Telefon, Mac, Další záloha a
  AI. Počty Momentů jsou oddělené od operací, médií a bajtů a chybové texty
  nevymýšlejí neprokázanou příčinu.
- Bez C06b/C07 produkční cesta nepředstírá zálohu ani AI. T054/T055 mají pouze
  syntetický modelový důkaz a fixture jsou uzavřené v Debug simulátoru.

Rozhodnutí:
- Uložené připojení ani připravená fronta nejsou zelené ověření. Kopie na Macu
  není další záloha a přepis není záloha.

Další krok:
- Samostatně povolit push a podepsanou aktualizaci C05c, potom projít
  `C05c_IPHONE_TEST_PLAN.md`.

Navrhované další kroky:
- C06a, C06b a C07 otevřít vlastním rozhodnutím; fyzické T054/T055 uzavřít až
  nad skutečnou zálohou a AI.

Technický důkaz:
- Swift 33/33, UI T054 1/1, UI pause 1/1, generic iOS build a plná projektová
  brána 1770/1770 PASS. Push, instalace a fyzická akceptace NEPROVEDENY.
  Registrovaný audit potvrdil zastavený C05b server, nepřítomnou privátní cestu,
  vypnutý Funnel a 0 aktivních tokenů.

### 2026-09-24 23:33 CEST — C05c push a podepsaná aktualizace

Hotovo:
- Zdrojový checkpoint C05c je na GitHubu. Camino 0.1.0 (4) bylo aktualizováno
  přes stejné bundle ID bez odinstalace a po instalaci spuštěno.

Rozhodnutí:
- Fyzický průchod proběhne 2026-09-25. Dnešní instalace sama nepotvrzuje
  zachování dat, čitelnost ani skutečné UX a neotevírá C06a/C06b/C07.

Další krok:
- Projít `C05c_IPHONE_TEST_PLAN.md` od části A; C05b server ponechat vypnutý.

Navrhované další kroky:
- Skutečné T054/T055 uzavřít až nad reálnou C06b zálohou a C07 AI.

Technický důkaz:
- `f0f714f4` je na `origin/main`. Strict podpis, shoda týmu, profil zahrnující
  iPhone, instalace, launch a inventář Camino 0.1.0 (4) PASS. Cockpit deployment,
  C05b server, Serve a Funnel se nezměnily.

### 2026-09-25 20:59 CEST — minimalistický cestovní plán a podpis

Hotovo:
- Nový `camino/docs/TRAVEL_MVP_PLAN.md` sjednocuje levnější cestovní rozsah,
  pořadí M1–M4, krátkou přejímku RT1–RT6 a odložené funkce. Viewer zatím
  není implementovaný; aplikace ani služby se tímto krokem nezměnily.
- Míla potvrdil SideStore import bez kabelu, otevření původního Camina,
  zachování starých záznamů a přehrávání. Celý stavový C05c není tímto PASS.

Rozhodnutí:
- Míla chce funkčnost pro cestu 3.–17. 10., nikoli absolutní spolehlivost,
  komerční produkt nebo App Store přípravu. Prioritou je jednoduché HTML pro
  Janu z Cockpitu. AI, souhrny a širší produkt se v novém plánu odkládají.
- Zachovat U15, originály, autorizaci, hashové ověření a povinné rizikové
  brány. Neopakovat přijaté nezměněné testy, fyzické zkoušky sloučit.
- Návrh: API a Viewer v jednom Camino procesu s vlastní přímou URL,
  odděleném od Cockpitu; jednoduché odvozeniny a nezávislá denní záloha.
  Krátké výpadky a ruční retry jsou omezení MVP, ne zatajené chyby.

Další krok:
- M1: lokální minimalistický Viewer nad syntetickými daty; bez AI,
  nového iOS buildu, startu služby, Serve, push či deploymentu.

Navrhované další kroky:
- M2 soukromý provoz/Cockpit a Janina zkouška; zbývající C05c spojit s ní.
- M3 nezávislá kopie a jedna obnova dne, M4 krátká předcestovní přejímka.
- Podpis znovu ověřit 1. 10.; opakovaný import s původním ID a vypnutým
  Append Team ID. Standardní Refresh All ani celá cesta nejsou ověřené.

Technický důkaz:
- Pouze dokumentace; rychlá statická brána `--skip-unit-tests` PASS.
  Dřívější plné sady ani iPhone build se kvůli plánu neopakovaly.
- Soukromý log SideStore: první pokus s přidanou příponou selhal na limitu
  aplikací; druhý v 20:27 zachoval ID a úspěšně instaloval profil do
  2. 10. 20:27 CEST. Datum není odečtené z nainstalovaného profilu.
  Nefunkční druhá ikona pravděpodobně souvisí s prvním pokusem; nic nesmazáno.
  Aktuální dlouhodobý provoz serveru ani automatická obnova podpisu nejsou
  tímto doložené. Tajemství a osobní data zůstávají mimo Git.

### 2026-09-25 21:16 CEST — M1 lokální Viewer, vizuální přejímka otevřená

Hotovo:
- Lokální volitelný HTML Viewer umí dny, text, foto, audio a video. Čte jen
  aktuální povolenou projekci; originály nemění. Oddělená čtecí autorizace,
  revokace, staré URL po zámku a mediální Range mají syntetické testy.
- Připraven samostatný HTML náhled s umělými médii. Běžící server, Cockpit,
  iPhone, Serve, Funnel ani skutečná uživatelská data se nezměnily.

Rozhodnutí:
- M1 používá existující API/stores bez nové databázové migrace nebo závislosti.
  Viewer je výchozím stavem vypnutý; zapojení `viewer=` je explicitní.
- Server dosud nezná pořadí audiočástí/mezery (iPhone registruje Assety podle
  UUID). M1 proto části nabízí samostatně s upozorněním. Před ostrými dlouhými
  komentáři nutno vyřešit minimální přenos pořadí, ne odhadovat chronologii.
- Vizuální/browser PASS nelze připsat: není připojený žádný browser provider.
  M1 má hotový kód a automatické důkazy, nikoli úplnou fyzickou přejímku.

Další krok:
- Otevřít syntetický HTML náhled a ověřit vzhled, jedno audio a video.

Navrhované další kroky:
- Potom M2: minimální pořadí audiočástí a soukromý provoz/čtecí přístup,
  Cockpit odkaz a Janina zkouška; skutečná publikace vyžaduje vlastní souhlas.
- M3/M4 zůstávají podle cestovního plánu. Žádný nový test mikrofonu ani
  opakování přijatého C05b jen kvůli serverovému HTML.

Technický důkaz:
- 29/29 projekce/C03b/media-store, 7/7 HTTP/deriváty a 5/5 stávající FastAPI
  scénáře PASS; hash původních bajtů zachován, skutečné deriváty zkontrolované
  ffprobe, citlivé testovací metadata odstraněné, Range 206.
- Plná brána a přesné hranice jsou zaznamenané v `camino/docs/M1_VIEWER_REPORT.md`.
  Browser náhled není privátní síťový test a G8 zůstává otevřená.

### 2026-09-25 21:52 CEST — M1 náhled potvrzen, místní M2a připravené

Hotovo:
- Míla potvrdil funkční náhled a povolil pokračování. Připravená automatická
  příprava doručených médií, privátní proxy odkazy a tlačítko z Cockpitu.
- Vše jen v lokálním kódu a syntetických testech. Bez nasazení nebo iPhone
  změny; skutečné tokeny, média, launchd, Serve a Funnel nedotčené.

Rozhodnutí:
- Rozsah cestovního MVP se nemění. M2a je nezávislá provozní příprava;
  oprava pořadí audia stále musí předcházet ostrým dlouhým komentářům.
- Cockpit jen otevře soukromou adresu; nestartuje server, nedrží čtecí token
  a nenahrazuje autorizaci. Stav odkazu není živý audit dostupnosti.

Další krok:
- M2b: doplnit minimální přenos pořadí a mezer audiočástí, bez přepisu recorderu.

Navrhované další kroky:
- Registrovaný provozní start/status/stop a vědomé povolení cesty/čtenáře.
- Samostatně schválené nasazení a jeden společný iPhone → Mac → Jana průchod.
- M3 nezávislá záloha a M4 předcestovní přejímka podle cestovního plánu.

Technický důkaz:
- Nové testy: 5 rychlých worker/link a 6 izolovaných runtime/proxy PASS.
  Regrese: 7 Viewer HTTP, 5 owner FastAPI, 18 frontend PASS.
- Opětovný start aplikačního lifecycle je syntetický důkaz, ne launchd
  restart po pádu. Nové živé UI, vzdálená síť a G8 zůstávají neověřené.
- Plná brána a přesné hranice jsou v `camino/docs/M2_RUNTIME_REPORT.md`.

### 2026-09-25 22:13 CEST — M2b pořadí a mezery audiočástí lokálně

Hotovo:
- Telefonní sync umí z dokončených účtenek doplnit pořadí a zaznamenané mezery,
  bez změny recorderu nebo opakovaného uploadu již ověřeného audia.
- Viewer řadí podle návaznosti, souvislé úseky automaticky navazuje a skutečné
  pauzy/nejistoty označuje. Soukromé layouty se nepromítají do Janina výstupu.

Rozhodnutí:
- M2b podle Mílova zadání používá samostatná neměnná metadata; staré obálky,
  identita médií, originály a Core Data se nemění. Rozsah MVP nerozšiřujeme.
- Pauza není uměle vyrobené ticho; pokračování po pauze spustí Jana ručně.
  Safari autoplay zůstává k ověření, ruční přehrání je dostupné i bez skriptu.
- Serverový upgrade přidává tabulku ve schématu 2. Před živým upgradem kopie
  DB; instalovat nejdřív server, potom telefon. V tomto kroku jen syntetické DB.

Další krok:
- M2c: registrovaný provozní start/status/stop a vědomé povolení cesty/čtenáře.

Navrhované další kroky:
- Po schválení nasazení serveru a podepsaná aktualizace stejné iPhone aplikace.
- Jeden krátký iPhone → Mac → Jana průchod podle M2b reportu, ne celá C01c matice.
- M3 nezávislá záloha a M4 freeze podle cestovního plánu.

Technický důkaz:
- SwiftPM 36/36 a nepodepsaný generic iOS build PASS. Python layout/kontrakt
  26/26, izolovaná serverová sada 21/21 PASS. Node ověřuje pokračování i fallback.
- Plná brána a nasazovací hranice: `camino/docs/M2b_AUDIO_LAYOUT_REPORT.md`.
  Žádný push, podpis, instalace, live migrace, deployment ani změna Serve/Funnel.

### 2026-09-26 06:30 CEST — M2c provozní ovládání lokálně

Hotovo:
- Připravené potvrzované ovládání služby a Janina přístupu. Start sám neudělí
  Viewer; instalace sama nespustí server. Stav netvrdí ověřený přenos.
- Kopie před změnou DB zahrnuje potvrzený WAL a ověření integrity. Původní
  data a operace zůstávají, povolení cesty se ukládá zvlášť.

Rozhodnutí:
- Míla povolil lokální M2c. Rozsah cestovního MVP se nerozšiřuje; nasazení,
  skutečná oprávnění a síť zůstávají zvlášť potvrzované.
- Provozní zdroj musí být konkrétní stávající archiv, ne nový prázdný server.
  Lokální snapshot je pojistka upgradu, nikoli náhrada nezávislé zálohy M3.

Další krok:
- Schválit nasazovací přípravu a výběr konkrétního existujícího zdroje dat.

Navrhované další kroky:
- Nasadit nejdřív server, potom podepsanou aktualizaci stejné iPhone aplikace.
- Jeden společný RT3/RT4 a skutečný návrat procesu; ne opakování celé matice.
- M3 nezávislá záloha a M4 předcestovní průchod/freeze.

Technický důkaz:
- M2c offline 17/17 a izolovaný server 22/22 PASS. Plná brána a runbook:
  `camino/docs/M2c_SERVICE_REPORT.md`. launchd operace jsou zatím mockované.
- Nový status vrací konfiguraci nepřipravenou. Žádná reálná migrace, token,
  instalace, síťová změna, push ani deployment nebyly provedené.

### 2026-09-26 06:46 CEST — schválená nasazovací příprava a p+n

Hotovo:
- Živý read-only audit identifikoval zastavený stávající archiv: 41 Momentů,
  45 médií, 214 555 219 B, SQLite integrita OK. Dvě cesty, jen jedna naplněná.
- Připravené registrované workflow pro hashovou kontrolu, snapshoty, pevný
  release, trvalý Python a owner připojení. Offline přípravná sada 20/20 PASS.

Rozhodnutí:
- Míla schválil přípravu a p+n. Archiv zachovat, nevracet starou epochu ani
  neoživovat odvolaný token. T058 stále blokuje zápis/export; neobcházet.

Další krok:
- Provést ověřenou přípravu a schválený push/nasazení Cockpitu.

Navrhované další kroky:
- Instalace LaunchAgentu a privátní Serve až po přesné globální brzdě.
- Dořešit obnovu s telefonem; potom povolení Vieweru a společný RT3/RT4.
- M3 nezávislá záloha a M4 předcestovní průchod.

Technický důkaz:
- Audit staré služby: stopped, server/route neaktivní, Funnel off,
  active_tokens=0, reconciliation_required=1, exports_blocked=1, konflikty=0.
- `camino/docs/M2c_SERVICE_REPORT.md`; skutečná příprava/p+n zatím čekají
  na provedení, systémové změny na přesné potvrzení. Nic nebylo odblokováno.

### 2026-09-26 06:55 CEST — příprava archivu provedena, p+n kódu ověřené

Hotovo:
- Archiv i všech 45 médií hashově ověřené a zachované; tři potvrzené DB
  snapshoty, neměnný release a trvalé prostředí připravené.
- Nové owner připojení pouze v soukromém úložišti. Kód pushnutý a běžící
  Cockpit aktualizovaný s ověřením 5/5.

Rozhodnutí:
- Bez přesné globální brzdy neinstalovat LaunchAgent ani měnit Serve.
  Neodblokovat T058 a neudělit Reader grant jako vedlejší účinek nasazení.

Další krok:
- Získat přesnou globální brzdu pro instalaci Camino služby a privátní Serve.

Navrhované další kroky:
- Bezpečně dokončit obnovu s telefonem; compare_inventory je nyní read-only.
- Potom skutečný Viewer/Jana a RT3/RT4, M3 záloha a M4 přejímka.

Technický důkaz:
- 41 Momentů, 104 operací, 45 médií / 214 555 219 B; identita před/po shodná.
  Snapshoty 3/3, release 27/27, runtime import/pip check PASS, schéma stále 1.
- P+n `c9fbc3ee`: brána 1809/1809, nový Cockpit PID 90507, smoke 5/5.
  Finální docs checkpoint nemění kód; konečný p+n stav určuje živá účtenka.
- Camino není instalované/spuštěné; grant=false, obě T058 blokace=true.


### 2026-09-26 13:27 CEST — služba a privátní HTTPS nad původním archivem

Hotovo:
- Po přesné globální brzdě instalace/start Camino a vlastní Serve cesta.
  HTTPS owner API ověřené, Cockpit zachovaný, Funnel off; skutečný stop/start PASS.
- Schéma 1→3 po ověřeném snapshotu, všechny původní údaje a média zachované.

Rozhodnutí:
- Runtime zachovává release c9fbc3ee. TERM=dumb opravuje Tailscale CLI pod
  launchd; starý plist zůstává v soukromé kopii. Nové Serve karty jsou lokální.
- T058 blokace ani Viewer grant se nemění. Žádná změna telefonu nebo reader token.

Další krok:
- Bezpečné dokončení obnovy s iPhonem; samotné compare_inventory neodblokuje.

Navrhované další kroky:
- Poté skutečné povolení Vieweru a RT3/RT4; M3 nezávislá záloha, M4 přejímka.
- Nový lokální checkpoint lze samostatně publikovat; dnešní oprava zatím bez p+n.

Technický důkaz:
- Cíleně 29/29 a plná brána 1818/1818 PASS (377,590 s jednotkové sady).
- 104 operací, 41 Momentů, 45 médií / 214 555 219 B hashově shodné s přípravou.
- Registrovaný status: owned/loaded/running=true, privátní HTTPS=true,
  Cockpit healthy=true, Funnel=false, grant=false; Viewer 404, reader DB absent.
- Stop/start PID 14219→14329; po stop vyčkat uvolnění portu, ne ihned startovat.
  Pád procesu, přihlášení/restart Macu ani nový iPhone přenos nejsou PASS.


### 2026-09-26 13:42 CEST — lokální dokončení obnovy shodných kopií

Hotovo:
- Owner-only recovery endpoint a výslovné tlačítko iPhonu. Server ověřuje
  historii operací, identity, revize/soukromí, skutečné soubory a absenci
  konfliktů. Telefon kontroluje místní soubory a potvrzení přesného požadavku.

Rozhodnutí:
- Pouze shodné úplné kopie: žádné automatické slučování či přepis rozdílů.
  Staré obálky se nemění; nová epocha platí pro další operace, pause zůstává.
- Živý archiv neodblokovat jako součást vývoje. Nové místní čekající operace
  či chybějící média vyžadují samostatné cílené řešení, nikoli vypnutí flagů.

Další krok:
- Samostatně schválit nasazení nového serveru a aktualizaci téže iPhone appky;
  pak provést jeden krátký průchod z M2_RECOVERY_REPORT.md.

Navrhované další kroky:
- Při shodě dokončit obnovu, poté vědomě povolit Viewer a RT3/RT4; M3/M4 platí.

Technický důkaz:
- 9/9 recovery, 39/39 Swift, 24/24 HTTP/Viewer/runtime PASS; nepodepsaný iOS
  build PASS. Výsledek plné brány zaznamenán v M2_RECOVERY_REPORT.md.
- Živý read-only state HTTP 200: stejná identita, oba flagy=true,
  identical_recovery_v1 není nasazené. Registrovaný HTTPS audit PASS, Funnel off.
- Bez push, deploymentu, podpisu/instalace, změny sítě, grantu nebo osobních dat.


### 2026-09-26 17:08 CEST — nasazovací příprava po souhlasu pokračovat

Hotovo:
- Registrovaný upgrade s archivem staré konfigurace a DB snapshoty; 24 cílených testů PASS.
- Podepsaný build 5 se stejným ID a ověřená IPA pro nový podpis v SideStore.

Rozhodnutí:
- Zachovat archiv/flagy/granty; nic neodblokovat bez telefonu.
- Přímá instalace neprovedena: starý profil do 27. 9. 12:10 CEST by zkrátil
  předchozí SideStore platnost. Neřešit CoreDevice 12040 násilným zásahem.

Další krok:
- Dokončit plnou bránu, uložit čistý commit a registrovaně přepnout server.

Navrhované další kroky:
- Import stejné IPA přes SideStore, Append Team ID off, pak společné porovnání.

Technický důkaz:
- Strict podpis/profil zahrnující telefon PASS, ZIP integrita PASS.
- Podrobnosti a SHA-256 v M2_RECOVERY_REPORT.md; žádná instalace telefonu,
  změna sítě, reader grant ani živé dokončení T058.

### 2026-09-26 23:19 CEST — fyzická obnova a nový komentář doručený na Mac

Hotovo:
- Import stejné aplikace přes SideStore a zachování dat potvrzené Mílou.
- Obnova ověřena a dokončena, stav drží po zavření a otevření aplikace.
- Jeden nový komentář doručen: telefon zeleně 42 úplných, Mac 42 Momentů.

Rozhodnutí:
- Rozsah MVP se nemění. Prázdný komentář není důkaz přenosu neprázdného textu.

Další krok:
- Samostatně povolit soukromý Viewer pro Janu a provést RT3/RT4.

Navrhované další kroky:
- M3 nezávislá záloha a izolovaná obnova, M4 krátká předcestovní přejímka.
- Před cestou znovu ověřit SideStore podpis; jeho nová expirace nebyla odečtena.

Technický důkaz:
- Server po dokončení obnovy: oba blokující flagy=false, identita a původní
  archiv 104/41/45 beze změny. Po novém komentáři 129 operací, 42 Momentů,
  46 médií / 216 344 915 B; 0 konfliktů, původních 104 operací a 41 Momentů
  byte-exact, původních 45 účtenek shodných se snapshotem; soubory rehashované.
- Delta: create_day 1, create_moment 1, create_asset 1, create_audio_layout 22.
  Nové médium 1 789 696 B. Obsah ani hlas nebyly přehrávány/posuzovány.
- SideStore dostupnost napravena skutečným RemotePair portem z Network Discovery.
  Obnova Camina prošla po přepnutí na Tailscale a výměně starého tokenu
  (401) za aktuální (200). Nezaměňovat opravu podpisového připojení s Camino API.
- Tento zápis mění jen dokumentaci; Viewer grant, službu ani síť nemění.

## 2026-09-27 07:55 CEST — nové GPS body a plán odkazu pro Janu

Hotovo:
- Lokální implementace polohy nových Momentů, offline uložení, přenos a
  zobrazení přítomnosti/přesnosti na telefonu. Staré záznamy beze změny.

Rozhodnutí:
- Míla: mapu odložit, GPS nikoli. Před cestou odkaz z povoleného okamžiku
  Vieweru na mapový bod (U16), ne souvislé sledování. Staré body nedoplňovat.

Další krok:
- Samostatně schválená aktualizace telefonu a
  jediný krátký GPS1–GPS4 průchod podle GPS_CAPTURE_REPORT.md.

Navrhované další kroky:
- Odkaz na mapu pro Janu, poté povolení Vieweru/RT3/RT4, M3/M4 a podpis 1. 10.

Technický důkaz:
- Swift 44/44, API 3/3 (včetně Swift → owner API → restart DB), UI 1/1,
  iOS build a plná brána 1830/1830 PASS. Fyzická GPS NEOVĚŘENO.
- Záznam nečeká; před prvním fixem či po stáří nad 120 s může bod chybět.
  Žádný backfill, změna živých dat, push, nasazení ani instalace iPhonu.

## 2026-09-27 08:02 CEST — GPS aktualizace připravená pro SideStore

Hotovo:
- Nové IPA buildu 6 je ve Stahování; zachovává stejné ID a je ověřené.

Rozhodnutí:
- Pokračování autorizuje přípravu aktualizace, ne push či nasazení serveru.
  Starý vývojový profil se nesmí použít k přímé instalaci; SideStore jej nahradí.

Další krok:
- Ruční import přes SideStore, Append Team ID off, ověřit data a novou platnost.

Navrhované další kroky:
- GPS1–GPS4, mapový odkaz pro Janu, Viewer/RT3/RT4, M3/M4.

Technický důkaz:
- Podepsaný build a strict codesign PASS, ZIP integrita a shoda binárky PASS.
  Velikost/hash a postup v GPS_CAPTURE_REPORT.md. Kód nezměněn od 3fbf7232;
  předešlá plná brána platí, nyní pouze statická kontrola dokumentace.
  Telefon, soukromý archiv a služby beze změny; fyzická GPS NEOVĚŘENO.

## 2026-09-27 08:33 CEST — data a GPS1 fyzicky PASS

Hotovo:
- Nová verze se otevřela, data fungují. Nový okamžik bez povolené GPS
  správně uvádí nepřítomnost polohy; data a GPS1 PASS podle Míly.

Rozhodnutí:
- Bez nového rozhodnutí či změny kódu. GPS1 není důkaz polohy/přenosu.

Další krok:
- GPS2: venku povolit GPS při používání, počkat na připravený bod a vytvořit
  nový okamžik; ověřit skutečnou polohu a zachování offline/po otevření.

Navrhované další kroky:
- GPS3 přenos, zbývající GPS4, mapový odkaz a Janin Viewer; M3/M4.

Technický důkaz:
- Míla: „GPS u tohoto okamžiku není uložená ... všechna data fungují“.
  Dříve potvrdil nové tlačítko. SideStore 7 DAYS na snímku, přesná expirace
  neověřená. Žádné souřadnice, nový podpisový zásah, push či deploy.

## 2026-09-27 13:24 CEST — první skutečný GPS bod

Hotovo: GPS2 — část získání a uložení bodu PASS podle Míly, přesnost ±8 m.

Rozhodnutí: Bez nového rozhodnutí; přesnost je hlášený odhad telefonu.

Další krok: Offline vytvořit nový bod a ověřit zachování po zavření/otevření.

Navrhované další kroky: GPS3 přenos, zbytek GPS2/GPS4 a mapový odkaz pro Janu.

Technický důkaz: Míla hlásí „GPS uložena“ a ±8 m. Souřadnice nečteny.
GPS2 není celé PASS; restart/offline, média a přenos nejsou tímto doložené.

## 2026-09-27 13:30 CEST — GPS offline a po otevření

Hotovo: Nový GPS okamžik vznikl offline a poloha zůstala po zavření/otevření.

Rozhodnutí: Bez nového rozhodnutí; GPS2 je stále částečně PASS, média zbývají.

Další krok: GPS3 — přenést malou dávku a ověřit uloženou GPS na Macu.

Navrhované další kroky: Média GPS2, GPS4 a mapový odkaz pro Janu.

Technický důkaz: Míla potvrzuje „GPS offline + po otevření PASS“.
Souřadnice nečteny; přenos a mediální větve nejsou tímto doložené.

## 2026-09-27 13:44 CEST — GPS u fotografie a komentáře

Hotovo: Míla potvrzuje GPS u nové fotografie (±4 m) a komentáře (±11 m).
Předchozí dva GPS markery jsou prokazatelně uložené i na Macu.

Rozhodnutí: Bez nového rozhodnutí. Telefonní PASS neznamená doručení médií.

Další krok: Přenést nové foto/komentář a ověřit jejich GPS i média na Macu.

Navrhované další kroky: Zbývající GPS2/GPS3, GPS4 a mapový odkaz pro Janu.

Technický důkaz: Read-only Mac 45 Momentů / 133 operací / 2 GPS markery,
43 bez GPS, 0 konfliktů, oba recovery flagy=false, quick_check OK.
U obou GPS shoda všech čtyř polí přijatý payload → uložený Moment,
platný hash zprávy a zachování po novém otevření DB. Nová média dosud
nejsou v tomto snapshotu; opakovaný přenos bez duplikátu neověřený.
Souřadnice ani obsah nebyly vypsané; token, služba, síť a Viewer nezměněné.

## 2026-09-27 13:47 CEST — přenos fotografie a komentáře s GPS

Hotovo: Obě média i jejich GPS jsou na Macu. Telefon po synchronizaci 47/0.

Rozhodnutí: Bez nového rozhodnutí; rozdíl hlášené přesnosti fota nezakrývat.

Další krok: V telefonu zkontrolovat detail stejné fotografie: ±4 m nebo ±6 m.

Navrhované další kroky: Zbývající GPS2/GPS3, GPS4 a mapový odkaz pro Janu.

Technický důkaz: Read-only Mac 47 Momentů / 138 operací / 4 GPS body,
48 ověřených médií celkem. Nové foto a audio ověřeny velikostí a SHA-256.
Všechna čtyři GPS pole u všech bodů shodná mezi přijatou zprávou a DB
i po novém otevření, hashe zpráv platné, 0 konfliktů, oba flagy=false,
quick_check obou DB OK. Foto uložené zaokrouhleně ±6 m proti hlášení ±4 m,
komentář ±11 m. Shoda přenosu na serveru neprokazuje shodu detailu telefonu.
Bez výpisu souřadnic/obsahu, změny tokenu, služby, sítě nebo Vieweru.

## 2026-09-27 13:51 CEST — potvrzená přesnost fotografie

Hotovo: Detail fotografie v telefonu ukazuje ±6 m, shodně s Macem.

Rozhodnutí: Bez nového rozhodnutí; původní hlášení ±4 m opraveno Mílou.

Další krok: Krátké video s GPS (zbývající mediální větev GPS2).

Navrhované další kroky: Zbytek GPS2/GPS3, GPS4 a mapový odkaz pro Janu.

Technický důkaz: Míla potvrzuje „Ukazuje to +-6 m“. Mac ±6 m byl ověřen
v 13:47; nyní bez opakování DB auditu a bez změny dat, tokenu nebo služeb.
Přenos fota/komentáře doložen, plné GPS2/GPS3 tím ještě nejsou PASS.

## 2026-09-27 13:58 CEST — video s GPS doručeno

Hotovo: Video má GPS ±11 m v telefonu i na Macu; soubor dorazil beze změny.

Rozhodnutí: Bez nového rozhodnutí. Video větev uložení/přenosu PASS.

Další krok: Opakovat synchronizaci bez nového záznamu a ověřit stejné počty.

Navrhované další kroky: Zbytek GPS2/GPS3, GPS4 a mapový odkaz pro Janu.

Technický důkaz: Míla potvrzuje GPS ±11 m a dokončenou synchronizaci.
Read-only Mac 48 Momentů / 140 operací / 5 GPS bodů / 49 ověřených médií.
GPS u všech pěti bodů shodná přijatý payload → DB → nové otevření DB,
hashe zpráv platné. Tři GPS média (foto/audio/video) ověřena velikostí
a SHA-256 proti účtenkám. 0 konfliktů, oba recovery flagy=false, quick_check OK.
Bez přehrání soukromého obsahu nebo výpisu souřadnic; služby a token nezměněné.
Offline/restart mediálních větví ani opakovaný přenos tím nejsou doložené.

## 2026-09-27 14:21 CEST — minimalistický Viewer a mapový odkaz

Hotovo: U povoleného okamžiku s GPS je lokálně odkaz „Otevřít místo v mapě“,
odhad přesnosti a upozornění na předání bodu Apple Mapám po kliknutí.
Dosavadní dny/texty/foto/audio/video zachované. Bez nové instalace iPhonu.

Rozhodnutí: Na Mílovo přání pokračujeme Viewerem; zbývající okrajové GPS
zkoušky necháváme neověřené, neoznačujeme je dodatečně PASS.

Další krok: Potvrdit nasazení Camino serveru a grant pro Janu plus nastavení
odkazu v Cockpitu s potřebným restartem. Bez takového souhlasu nyní nenasazeno.

Navrhované další kroky: Společný RT3/RT4 a mapový klik, M3/M4, kontrola podpisu 1. 10.

Technický důkaz: 45/45 cílených testů PASS a rychlá statická brána PASS.
Projekce chrání owner-only/hidden/unknown, grant/obnovu/konflikt; HTTP testy
chrání auth, staré URL, referrer a allowlist mapového odkazu. EXIF beze změny.
Syntetický HTML náhled vygenerovaný; browser smoke neproveden, prohlížeč
není dostupný. Živě viewer_granted=false, Cockpit link configured=false,
privátní HTTPS zdravé, Funnel off. Report `camino/docs/VIEWER_MAP_REPORT.md`.
Při opakované kontrole GPS počet 48/140/5 beze změny; nejde o nucený retry.
Žádné souřadnice/tokeny v Gitu, žádný push/deploy/grant ani placené volání.

## 2026-09-27 15:17 CEST — Viewer pro Janu zprovozněný

Hotovo: Soukromý Viewer běží nad stávajícími daty, včetně mapových odkazů.
Cockpit má nastavené Otevřít Camino; samostatné přihlášení jana připravené,
heslo předané do schránky Macu. Token telefonu zůstal stejný.

Rozhodnutí: Míla schválil nasazení, Do deníku včetně GPS pro Janu a restart
Cockpitu, poté přesnou globální brzdu pro LaunchAgent. Současná data označil
za testovací/nahraditelná kromě dalšího testovacího využití; nyní nic nemažeme.

Další krok: Otevřít Viewer z Cockpitu, přihlásit se a společně ověřit jeden den.

Navrhované další kroky: RT3/RT4 se Safari/mapovým klikem, M3/M4, podpis 1. 10.

Technický důkaz: Registrované stop/upgrade/enable-viewer/start na 125fddbbcb56,
plná brána 1833/1833 PASS. První start OSError, po ověření volného portu
opakovaný start uspěl. Cockpit registrované nasazení, PID 72621→8376, smoke 5/5.
Privátní HTTPS 200: 6 dnů, 35 povolených Momentů, 5 správných mapových odkazů,
49 mediálních URL HEAD 200, video Range 206/16 B, žádná čekající média.
Owner-only/skrytá ID v HTML nepřítomná, anonymous/owner na Viewer i reader
na owner API 401. Archiv/identita/tabulky/originály/owner token hashově shodné,
48 Momentů / 140 operací / 49 médií / 228226831 B, oba recovery flagy=false.
Konfigurace a DB snapshoty zachované; ostatní env hodnoty shodné, Serve beze změny.
Žádný push, iPhone update, reálný mapový klik ani tvrzení fyzického RT3/RT4 PASS.

## 2026-09-27 15:27 CEST — První uživatelské potvrzení Vieweru

Hotovo: Míla po předání nasazeného Vieweru uvádí „Zdá se, že vše funguje
skvěle...“. Zapsané jako potvrzení základní funkčnosti, bez změny aplikace.

Důkaz a hranice: Uživatelské hlášení; konkrétní zařízení/síť, přehrání
jednotlivých médií ani otevření mapy neurčuje. RT3 částečně potvrzený,
nikoli celý PASS; fyzický RT4 (skrytí po změně na Jen pro mě) zatím nedoložený.
Technický audit z 15:17 se neopakuje a není vydáván za nové měření.

Další krok: Krátká zkouška s Janou a jeden test skrytí záznamu po synchronizaci,
potom M3 nezávislá záloha a M4 cestovní návod/přejímka; podpis zkontrolovat 1. 10.
Bez změny dat, restartu, nového nasazení nebo push.

## 2026-09-27 17:53 CEST — Buffer společné aktualizace

Hotovo: Diagnostikované zavádějící hlášení po dokončení mobilní dávky
uložené jako B01 do cestovního plánu, bez opravy či nového podpisu.

Rozhodnutí: Míla chce chybu odložit a zvážit společnou aktualizaci s názvy.
Pozdější doplňování názvů na Macu má provádět on, nikoli Jana.

Další krok: Při návratu schválit nejmenší rozsah B01/B02 před implementací.

Navrhované další kroky: Společný build a krátký test včetně pravdivých stavů;
M3 nezávislá záloha; M4 přejímka a obnova podpisu před cestou.

Technický důkaz: Snímek ukázal čekání na Wi-Fi po serverovém ověření videa.
Read-only audit v 17:44: 51 Momentů, 58 médií, všechny soubory velikostí/SHA-256
shodné, 0 konfliktů, oba recovery flagy=false. Kód ruší grant po dokončení,
ale synchronize/networkChanged nastavují čekání bez podmínky neodeslané práce.
Bez čtení journalu telefonu nejde doložit všechny jeho tehdejší položky.
RT3/RT4 ani GPS okraje se tím nezvyšují na PASS. Jen dokumentační změna.

## 2026-09-27 18:14 CEST — Jednosměrné názvy a oprava mobilního stavu

Hotovo: Lokálně přidané nepovinné názvy Momentů v telefonu, přenos na Mac
a zobrazení ve Vieweru. Dokončená mobilní dávka už nemá jen kvůli vyčerpanému
souhlasu hlásit čekání na Wi-Fi. Podrobnosti a výsledky ověření v
`camino/docs/TITLES_AND_TRANSFER_STATUS_REPORT.md`.

Rozhodnutí: Míla výslovně schválil nejprve telefonní aplikaci/názvy a opravu
B01. Tok názvů je jednosměrný; pozdější opravy na Macu se nevracejí do telefonu.
Adam zvolil odložený owner editor s lokálním přepisem názvu, který telefon
nepřepíše; Jana zůstává čtenář. Samostatné názvy připojených souborů nyní nejsou.

Další krok: Po ověření samostatně nasadit server s podporou názvů a připravit
jednu podepsanou aktualizaci telefonu, zachovat stávající aplikaci a data.

Navrhované další kroky: Krátký sdružený fyzický test; M3 nezávislá záloha;
M4 a podpis před cestou; owner editor Mac až podle času a kreditů.

Technický důkaz: Cíleně Swift 47/47, doména/projekce 21/21, HTTP 14/14,
Swift wire → ASGI API → reopen/Viewer 1/1 PASS, UI relaunch/clear 1/1 PASS,
generic iOS build 7 bez podpisu PASS, plná brána 1836/1836 PASS.
Neprovedené fyzické kroky drží uvedený report. Core Data schéma a originály
beze změny; title je nová revize. Starší server explicitně odmítnut před
odesláním názvů, staré přesné obálky zůstávají. Nasazení ani instalace neprovedené.

## 2026-09-27 20:04 CEST — Podepsaná aktualizace připravená

Hotovo: Build 7 s názvy a opravou mobilního stavu je podepsaný a zabalený
ve Stahování jako Camino-Names-7-20260927.ipa. Starý balíček a data zachované.

Rozhodnutí: Míla schválil nasazení, podpis a instalaci. Nové přepnutí
LaunchAgentu vyžaduje přesnou globální brzdu, kterou jsme vyžádali.

Další krok: Po potvrzení přepnout server, ověřit podporu názvů a zachování dat;
teprve potom importovat aktualizaci přes SideStore do stejné aplikace.

Navrhované další kroky: Jediný krátký fyzický test názvů a mobilního stavu;
M3/M4; případný owner editor Mac zůstává odložený.

Technický důkaz: Podepsaný build a strict codesign PASS, stejné ID/tým/zařízení
jako build 6, ZIP a shoda všech 5 souborů PASS. Profil do 4. 10. 18:07 CEST;
SideStore podpis/expirace až po importu. Služba/privátní HTTPS ověřené jako
dostupné před nasazením, Funnel off. Žádný stop/upgrade, push ani instalace.

## 2026-09-27 20:35 CEST — Server připravený na názvy z telefonu

Hotovo: Server a soukromý Viewer přijímají novou verzi s názvy. Všechna
původní data a přístupy zůstaly zachované; IPA build 7 je připravený k importu.

Rozhodnutí: Míla potvrdil novou globální brzdu pro registrovaný upgrade
LaunchAgentu. Tailscale, tokeny ani běžící Cockpit se nemění. Push neproveden.

Další krok: Import Camino-Names-7-20260927.ipa přes SideStore do téže aplikace
bez odinstalace; Customize AppID zapnuté, Append Team ID vypnuté.

Navrhované další kroky: Krátký fyzický průchod názvu a mobilní dávky;
M3/M4. Mac owner editor nadále odložený.

Technický důkaz: Registrovaný stop/upgrade/start, release 403180320849.
Před/po shodné metadata, identita, owner/reader token a archiv: 51 Momentů,
155 operací, 58 originálů ověřených SHA-256, 263 578 290 B; oba recovery
flagy=false. HTTPS moment_title_v1 PASS, Viewer a 6 denních stránek HTTP 200,
anonymní přístup i záměna owner/reader 401. Soukromá trasa a Cockpit zdravé,
Funnel off; upgrade uchoval snapshoty DB a původní konfiguraci. Plná brána
nezměněného kódu 1836/1836 PASS. Fyzický import, nový SideStore podpis a přenos
názvu/mobilní regrese zatím NEOVĚŘENO; neproveden downgrade ani smazání dat.

## 2026-09-27 21:31 CEST — Přílohy a přehled dne, potom delší testování

Hotovo: Míla potvrzuje názvy Momentů i přenos v předchozí aktualizaci.
Lokálně doplněné názvy jednotlivých fotografií, videí a celých komentářů;
telefon novější nahoře a počty příloh, Viewer rozbalovací karty.

Rozhodnutí: Viewer se na výslovné přání Míly dál čte od rána k večeru.
Přejmenování nepřesouvá Moment. Po jednom společném balíčku delší používání
stejné verze a sběr drobností; žádné další rychlé kosmetické verze.
Kritické chyby dat/soukromí/záznamu/přenosu se tím neodkládají. Mac editor později.

Další krok: Samostatně schválit a provést
serverovou aktualizaci, podpis a import stejné aplikace bez odinstalace.

Navrhované další kroky: Krátká fyzická přejímka B03+B01; delší běžné testování;
M3 nezávislá záloha; M4 před odjezdem. Jana zůstává pouze čtenář.

Technický důkaz: 49 Swift, 31 Python doména/projekce/layout, 15 HTTP a jeden
skutečný Swift wire → API/reopen/Viewer test PASS. iOS build 8 bez podpisu,
UI 2/2 a plná brána 1838/1838 PASS; detaily v reportu B01/B02/B03. Staré přesné obálky,
originály i verified média se nemění; feature gate attachment_title_v1,
nový audio layout před názvem session. Bez schématové migrace; downgrade po
nové operaci nepodporovaný. Fyzický build 8 a Safari NEOVĚŘENO. Žádný nový
push, deployment, podpis/IPA, token ani změna osobního archivu v tomto kroku.

## 2026-09-27 21:56 CEST — Podepsaný build 8, server čeká na brzdu

Hotovo: Balíček nové verze s názvy příloh je podepsaný a ověřený ve Stahování.
Telefon se zatím nezměnil.

Rozhodnutí: Míla schválil nasazení, podpis a instalaci. Pro zásah do
LaunchAgentu je vyžádaná nová přesná globální brzda; dosud nedoručená.
Push není součástí tohoto pokynu.

Další krok: Po potvrzení přepnout registrovaným upgrade server a ověřit
archiv, přístupy a attachment_title_v1; teprve potom import stejné app.

Navrhované další kroky: Krátký B03+B01 průchod; delší používání stejné verze;
M3 nezávislá záloha; M4 před odjezdem.

Technický důkaz: Zdroj ee10ec28, build 0.1.0 (8), strict codesign a všech
5 souborů IPA shodných s podepsaným výstupem PASS. Stejné ID/tým/zařízení,
profil do 4. 10. 18:07 CEST; SideStore expirace až po importu. SHA-256 a
velikost v TITLES_AND_TRANSFER_STATUS_REPORT.md. Plná brána nezměněného kódu
1838/1838 již PASS. Žádný stop/upgrade, push, změna tokenů/sítě ani instalace.

## 2026-09-27 22:13 CEST — Server B03 nasazený, nyní import buildu 8

Hotovo: Soukromý server a Viewer přijímají názvy jednotlivých příloh.
Viewer má rozbalovací karty; archiv a přístupy zůstaly zachované.

Rozhodnutí: Míla dodal novou přesnou globální brzdu pro tento upgrade.
Registrovaný stop/upgrade/start hotový. Síť, tokeny ani Cockpit se nemění.

Další krok: SideStore import Camino-Attachments-8-20260927.ipa do stejné app,
bez odinstalace; Customize AppID on a Append Team ID off pro tento import.

Navrhované další kroky: Krátký B03+B01 průchod; delší testování stejné verze;
M3 nezávislá záloha; M4 před odjezdem.

Technický důkaz: Release ab34bb5ec217 obsahuje kód ee10ec28. Před/po startu
shodná metadata, identita, owner/reader tokeny a archiv: 53 Momentů,
170 operací, 62 SHA-256 ověřených originálů / 271 510 864 B, recovery flagy=false.
HTTPS attachment_title_v1, Viewer a 6 dnů HTTP 200, 40 výchozích zavřených karet;
anonymní přístup a záměna rolí HTTP 401. Funnel off, Cockpit healthy.
Upgrade uchoval DB snapshoty a konfiguraci, nikoli nezávislou M3 zálohu.
Po stopu krátce obsazený port bez poslouchajícího procesu; po uvolnění normální
start, bez kill či úpravy síťových ochran. Fyzický import a přejímka B03/B01
dosud NEOVĚŘENO; žádný push. Podpis a SHA-256 IPA viz report.

## 2026-09-28 13:23 CEST — Buffer B04, nikoli vývoj mazání

Hotovo: Zapsaný požadavek na mazání každého typu obsahu a jednotlivých příloh
s reálným uvolněním telefonu. Míla potvrzuje základní funkčnost buildu 8.

Rozhodnutí: Pouze buffer změn, nic neimplementovat. Přenos smazání do Vieweru
další dávkou je Adamův návrh; zachování již přenesených originálů v neveřejném
Mac archivu zatím není Mílovo schválené rozhodnutí.

Další krok: Upřesnit rozsah smazání na Macu; pokračovat v testování stejné verze.

Navrhované další kroky: Večer kontrola rozběhnuté recovery zálohy; M3/M4;
případné budoucí mazání až po samostatném schválení.

Technický důkaz: Read-only kontrola dosavadního kontraktu neměnných originálů
a ochrany Vieweru; návrh B04 v TRAVEL_MVP_PLAN.md rozlišuje lokální uvolnění,
doručené smazání, retry/obnovu a historické kopie. Žádné nové runtime testy,
změny aplikace/služby, nasazení, podpis, push ani skutečné smazání.

## 2026-09-28 13:40 CEST — Schválená archivní pojistka B04

Hotovo: Upřesněný buffer B04: již přenesené originály zůstanou v neveřejném
archivu Macu, po budoucím smazání v telefonu zmizí z aktivního Vieweru.

Rozhodnutí: Míla souhlasí s touto archivní pojistkou. Žádný vývoj ani smazání
nyní nejsou povolené; Jana zůstává čtenář. Míla požádal také o přístup k Vieweru.

Další krok: Uložit existující čtecí heslo do správce hesel; dál testovat build 8.

Navrhované další kroky: Večer kontrola recovery zálohy; B04 jen sbírat;
M3/M4 zůstávají.

Technický důkaz: Existující reader přístup jana ověřený živým soukromým HTTPS,
HTTP 200. Heslo nevypsané, nezapsané do dokumentace ani změněné; žádná rotace,
restart, nasazení nebo změna aplikace. Uložení hesla uživatelem není ověřené.

## 2026-09-28 22:04 CEST — Autorizovaný c+p+n celého balíčku

Hotovo: Předpublikační audit čistého main a obou zarovnaných profilů.
B03 server je nasazený z ab34bb5ec217; Míla používá build 8.

Rozhodnutí: Míla výslovně schválil c+p+n všeho, včetně připravené sovy
pro 29. září. B04 zůstává jen buffer; žádný vývoj mazání ani nové IPA.
Neměnit tokeny, Serve/Funnel, archiv ani znovu instalovat nezměněné Camino.

Další krok: Plná brána a push přesného celého balíčku, řízené nasazení
aktuálního main do Cockpitu a živé ověření; výsledek v běhové deployment receipt.

Navrhované další kroky: Zítra veřejná kontrola sovy; pokračovat v delším
testování buildu 8; M3/M4.

Technický důkaz: Audit main a1382856 před tímto zápisem: 10 commitů / 31 cest,
origin 22dea402 je předkem, profily čisté/zarovnané. Žádný force push ani
přepis historie. Předchozí plná vývojová brána 1838/1838 nenahrazuje dnešní
publikační bránu. Nové fyzické scénáře ani recovery záloha zde neověřované.

## 2026-09-28 22:50 CEST — Mapa cesty v read-only Vieweru

Hotovo: Lokální samostatná mapa míst záznamů, celá cesta/jeden den,
orientační spojnice, názvy/čas/přesnost a odkazy do rozbalených okamžiků.
Nové doručené body přibývají při obnově bez změny přiblížení. Jana podle Míly
už používá dosavadní Viewer ze svého Macu; nová mapa není fyzicky převzatá.

Rozhodnutí: Míla schválil návrh a zahájení vývoje; U17 rozšiřuje Viewer o mapu
existujících povolených GPS, ne o průběžné sledování. Telefon/build 8 beze změny.
Leaflet lokálně, OSM podklad až po kliknutí a vysvětlení externích požadavků.
B04 zůstává buffer, žádné mazání nebo Mac editor. Žádný nový push/nasazení.

Další krok: Samostatně schválit nasazení serveru a krátce převzít mapu podle
VIEWER_ROUTE_MAP_REPORT.md; není potřeba nové IPA ani restart Cockpitu.

Navrhované další kroky: Delší testování buildu 8; odložená kontrola zálohy;
M3/M4; pozdější B04 podle času a kreditů.

Technický důkaz: 30/30 projekčních/runtime/audio + 17/17 HTTP testů PASS,
Node frontend 4/4 PASS, ověřené Leaflet JS/CSS upstream SRI.
Plná brána 1843/1843 PASS. Žádný dostupný browser: Safari, živé dlaždice a fyzické UX
NEOVĚŘENO. Bez změn archivu, sítě, tokenů, běžící služby nebo telefonu.

## 2026-09-28 23:04 CEST — Mapa nasazená na soukromém serveru

Hotovo: Viewer nabízí Mapu cesty a server poskytuje 9 povolených GPS bodů
včetně odkazů do správných okamžiků. Archiv i dosavadní přihlášení zachované.

Rozhodnutí: Míla schválil nasazení serveru a krátkou zkoušku, poté přesnou
globální brzdu. Žádná změna telefonu, sítě, nový push nebo restart Cockpitu.

Další krok: Míla otevře Viewer → Mapa cesty → Otevřít mapu a vyzkouší bod
a odkaz do deníku. Skutečné vykreslení není zatím potvrzené.

Navrhované další kroky: Jeden nový GPS okamžik a přírůstek po synchronizaci;
delší testování buildu 8; odložená kontrola zálohy a M3/M4; B04 jen buffer.

Technický důkaz: Neměnný release ce903913bb35; předchozí plná brána stejného
kódu 1843/1843 PASS. Registrovaný stop/upgrade/start a živé HTTPS/mapové
assety/auth/projekce/anchor kontroly PASS. Zachováno 53 Momentů, 177 operací,
62 hashově ověřených médií / 271 510 864 B, identita a obě tabulky oprávnění;
Funnel off, recovery flagy=false. Safari/dlaždice/UX NEOVĚŘENO (browser není
dostupný). Přesný redigovaný průchod v VIEWER_ROUTE_MAP_REPORT.md.

## 2026-09-28 23:09 CEST — Míla potvrzuje mapu, konec dne

Hotovo: Základní fyzická přejímka mapy PASS podle Mílova výslovného potvrzení
jejího výborného fungování. Stav pro příští pokračování uložený.

Rozhodnutí: Pro dnešek ukončit práci, nic dalšího nenasazovat.

Další krok: Běžné používání a delší testování stejné verze.

Navrhované další kroky: Přírůstek nového GPS bodu po synchronizaci;
odložená kontrola zálohy; M3/M4; B04 dál pouze buffer.

Technický důkaz: Uživatelské potvrzení 28. 9. 23:09, nikoli automatický test.
Zařízení/prohlížeč a jednotlivé okrajové scénáře neuvedené; nerozšiřovat na
celé G8, všechny platformy ani revokaci/výpadek. Pouze dokumentační zápis,
bez změny kódu, sítě, archivu, telefonu, nasazení či push.

## 2026-09-29 18:38 CEST — Bod 2 push a řízené nasazení

Hotovo: Oddělený editor názvů a stabilní video přehrávač jsou součástí
pushnutého main. Cockpit nyní běží z tohoto main a jeho základní smoke kontroly
jsou po restartu v pořádku.

Rozhodnutí: Míla výslovně schválil push a nasazení. Nasazení se týká běžícího
Cockpitu; aktualizace iOS aplikace je samostatný podepsaný build a instalace.

Další krok: Připravit podepsaný iOS build, nainstalovat jej bez odinstalace
stávající Camino a krátce ověřit psaní i ukládání názvů na telefonu.

Navrhované další kroky: Zopakovat přerušené UI testy na stabilním runneru;
po fyzickém průchodu vyhodnotit případné další zpomalení profilerem.

Technický důkaz: Kód bodu 2 je v pushnutém main jako `9579dcfb` a aktuální
lokální main je shodný s `origin/main`; plná brána 1843/1843 PASS. Předrestartový
audit měl oba profilové workspaces čisté a
zarovnané; po restartu byl potvrzen nový proces, shodný otisk a Cockpit smoke
5/5. Cílený UI runner byl dříve přerušen bez PASS/FAIL a fyzický iPhone test
zůstává NEOVĚŘENÝ.

## 2026-09-29 18:59 CEST — B04 lokální mazání před novým buildem

Hotovo: Implementováno potvrzené lokální mazání celého Momentu i jednotlivé
foto/video přílohy. Komentář nebo Úvaha se mažou jako celá audio session včetně
technických segmentů; u připojené session zůstává rodičovský Moment. Běžící
foto/video/audio capture mazání zablokuje. Trvalý tombstone je v SettingRecord,
originál se uvolňuje až po potvrzení metadata a restart smazaný obsah nevrátí.
Synchronizační fronta potlačí dosud neodeslané create položky, přijatá historie
zůstává zachovaná.

Rozhodnutí: Míla výslovně schválil implementaci před novým buildem a fyzickými
testy. Změna je lokální část B04; serverový delete/Viewer, Mac archivní pojistka
pro již přenesené originály a podepsaný iPhone build nejsou tímto krokem hotové.
Žádný push, deploy, podpis ani skutečné uživatelské mazání dat se neprovedlo.

Důkaz: 56/56 Swift package testů PASS, generic iOS Simulator build bude znovu
ověřen po poslední úpravě. Nové testy pokrývají restart tombstonu, zachování
rodiče při mazání přílohy, blokaci aktivního capture, fyzické uvolnění JPEG a
potlačení čekající sync práce. Fyzické iPhone UX, reálné volné místo a Viewer
server mazání zůstávají NEOVĚŘENÉ.

Další krok: Dokončit serverový delete kontrakt jako samostatný krok, potom nový
podepsaný build a krátké fyzické testy mazání/obnovy bez odinstalace.

## 2026-09-29 20:35 CEST — B05 pořadí obsahu v detailu Momentu

Hotovo: Akce pro přidání komentáře, Úvahy, fotografie a videa jsou na začátku
detailu Momentu. Obsah se přidává pod nimi a přijaté foto/video přílohy se ukazují
od nejnovějších; lokální data a privacy kontrakt se nemění.

Rozhodnutí: Lokální iOS UI krok uzavřený automatickým ověřením. Push, deployment,
podpis a iPhone instalace nejsou součástí tohoto kroku.

Další krok: Samostatně připravit schválený podepsaný build a krátkou fyzickou
kontrolu panelu na iPhonu.

Navrhované další kroky: Ověřit více příloh v jednom Momentu; pokračovat odděleně
v B04 serverovém delete kontraktu a archivní pojistce.

Technický důkaz: 56/56 Swift testů, generic simulator build a UI 8/8 PASS. Test
relaunch ověřil titulky foto/audio po uložení a restartu. AssetRecord stále nemá
samostatný presentation timestamp, takže foto/video používá obrácený accepted order;
fyzické zařízení zůstává NEOVĚŘENO.

## 2026-09-29 20:47 CEST — B05 podepsaný build nainstalován

Hotovo: Aktuální B05 build byl podepsán, exportován do IPA a přes CoreDevice
nainstalován na spárovaný iPhone 14 Plus bez odinstalace. Stejné bundle ID
`cz.pythonmf.camino.app`, aplikace `0.1.0`; po instalaci úspěšně spuštěná.

Rozhodnutí: Fyzická instalace je hotová, uživatelská přejímka nového pořadí
zatím čeká na Mílův krátký průchod. Push, deployment ani serverová změna se nedělaly.

Další krok: Na iPhonu otevřít Moment a ověřit panel přidávání nahoře, přidat jednu
fotografii/video a zkontrolovat jejich umístění pod panelem; následně zkusit
komentář nebo Úvahu a návrat bez ztráty stávajících dat.

Technický důkaz: Archive/export strict codesign PASS; `devicectl` install a launch
PASS, proces Camino je viditelný v seznamu procesů. Fyzické UX a pořadí více příloh
zůstávají NEOVĚŘENÉ do uživatelského potvrzení.


## 2026-09-29 21:23 CEST — U17 mapa pushnutá a nasazená po „vše p+n“

Hotovo: Míla výslovně schválil kompletní „vše p+n“. Čtyři čekající lokální
commity byly po plné bráně odeslané na GitHub; `main` a `origin/main` nyní
ukazují na `879a2e7199b6` a oba čisté profilové workspace jsou fast-forwardem
zarovnané. Cockpit byl řízeně restartován z aktuálního main a smoke je 5/5 PASS.

Rozhodnutí: Camino managed service byla řízeně zastavena, upgradována na
neměnný release z tohoto commitu a znovu spuštěna. Původní soukromý archiv,
konfigurace, oprávnění a data zůstaly zachované; Serve cesta se neměnila a
Funnel zůstal vypnutý. iPhone build se neměnil, protože jde o serverový Viewer.

Další krok: Při běžném používání otevřít Viewer → Mapa cesty → Otevřít mapu a
krátce ověřit vizuální šipku, popup/odkaz a přírůstek jednoho nového bodu po
fyzické synchronizaci.

Navrhované další kroky: Pokud vizuální průchod projde, ponechat release v běžném
používání; při nesouladu nejdříve pořídit redigovaný screenshot nebo popis
scénáře a teprve potom řešit další úpravu. M3/M4, kontrola zálohy a B04 buffer
zůstávají samostatné otevřené položky.

Technický důkaz: Lokální cílené testy projekce 16/16, Node frontend 5/5,
syntax check a diff check PASS; před push byla plná brána 1843/1843 PASS.
Cockpit deployment receipt potvrdila nový proces a smoke 5/5. Živý HTTPS audit
13/13 PASS: mapa/data 200, anonymní i owner Viewer 401, správný prefix a
hlavičky, map.js/map.css 200 s no-store, živý asset obsahuje čárkované úseky
a `route-arrow`; 13 bodů/12 návazných úseků. Audit nevypisoval souřadnice,
názvy ani tokeny a neměnil osobní data. Safari/OSM dlaždice a fyzická UX jsou
NEOVĚŘENO.

## 2026-10-02 12:04 CEST — iOS discovery po čistém resetu přestává frontovat prázdnou kostru

Hotovo: Diagnostika telefonního stavu vysvětlila viditelných 13 metadat jako 2
historické Trip záznamy a 11 Day záznamů bez aktivních Momentů nebo médií.
Úprava iOS discovery prázdný telefon vynechá; skutečný Trip/Day se přidá při
prvním Momentu, médiu nebo audio layoutu. Podepsaný Camino 0.1.0 (12) byl bez
odinstalace nainstalován a spuštěn.

Rozhodnutí: Nulový lokální obsah nesmí vytvářet přenosovou frontu pouze z
prázdné historické struktury. Místní soubory, nastavení a serverová data se
úpravou nemění.

Další krok: Na iPhonu vytvořit jeden malý nový Moment a ověřit, že se první
skutečný obsah i s potřebnou strukturou přenese na čistý server; potom ověřit
Viewer.

Navrhované další kroky: Pokud průchod projde, ponechat build v běžném používání.
Při opakování prázdných metadat nejdříve zachytit redigovaný stav journalu a
serverového cursoru; neprovádět další ruční reset.

Technický důkaz: Commit `06dca6d7`; SwiftPM 58/58, generic iOS build, strict
codesign, IPA export/ZIP validace, `devicectl` install/launch PASS. Read-only
journal po spuštění: metadata 0, media 0, cursor 0, reconciliation false.
Plná projektová brána po předchozím serverovém kroku zůstává 1847/1847 PASS;
GitHub push a serverové nasazení tohoto iOS-only kroku se neprováděly.

## 2026-10-02 17:35 CEST — Oprava přenosu po resetu

**Hotovo:** Telefon znovu přenáší nový Moment i fotografii na Mac; ověřeno také
po restartu aplikace a služby. Místní chyba zápisu má odpovídající hlášení.

**Rozhodnutí:** Opravit současné úložiště a přístup bez dalšího mazání.
GitHub zůstává bez odeslání podle Mílova pokynu.

**Další krok:** Uživatelsky ověřit další nový okamžik.

**Navrhované další kroky:** Žádné nové.

**Technický důkaz:** Root-owned Sync/0755 → Cocoa 513/EACCES; po obnově
adresáře pod mobile odhalen a opraven HTTP 401. Journal accepted 15 /
verified 1 / pending 0, server cursor 15, HTTPS s ověřením certifikátu PASS.
Opravena zaniklá trip vazba configu; registrovaný restart/status PASS.
SwiftPM 58/58, build 14 a statická brána PASS. Bez plošné přejímky ostatních médií.

## 2026-10-02 21:16 CEST — Obnovení Vieweru po resetu

**Hotovo:** Privátní Viewer znovu odpovídá po přihlášení Jany.

**Rozhodnutí:** Míla výslovně požádal obnovit přístup a jednodušeji
čitelné heslo; použita náhodná heslová fráze bez změny owner tokenu.

**Další krok:** Přihlásit se novým heslem a uložit jej v prohlížeči.

**Navrhované další kroky:** Žádné nové.

**Technický důkaz:** Registrované stop/enable-viewer/start, živý grant true;
HTTPS Viewer anonymous 401, Jana 200, mapa 200, owner state 200.
Bez mazání dat, změny zdrojů aplikace nebo GitHub odeslání.

## 2026-10-03 20:39 WEST — Přesný úklid českých Momentů před Portugalskem

**Hotovo:** Po schválení odstraněny 2 fotky, 1 video a jejich odvozené/přenosové
kopie z aplikace a Macu. Tři české Momenty už nejsou v deníku ani Vieweru.
Spojení telefonu, přístup Jany a historie synchronizace zůstaly zachovány.

**Rozhodnutí:** Míla požadoval fyzické smazání konkrétních tří záznamů; schválil
ponechání původních synchronizačních metadat a potvrdil globální brzdu.
Nejde o reset serveru ani plošné mazání jiných dat či starších záloh.

**Další krok:** První portugalský Moment a uživatelské potvrzení jeho přenosu.

**Navrhované další kroky:** Žádné nové.

**Technický důkaz:** Telefon 3 originály + cache pryč; Mac 13 souborů a 9
prázdných adresářů pryč, měřený nárůst volného místa 21 528 576 B. Přesná
historie 19 operací/identity/cursor beze změny. Na kopiích retry, nový Moment
a complete_recovery PASS. Live DB/FK, HTTPS owner 200, Jana 200, anonym 401,
4 staré mediální URL 404; telefon znovu kontaktoval Mac bez blokace či pauzy.
Bez nového buildu a bez GitHub odeslání.

## 2026-10-03 21:02 WEST — Vložení fotografie či videa z Fotek

**Hotovo:** Horní menu okamžiku má výběr jedné fotografie/video z knihovny.
Import má stav, zrušení načítání a zachová originál ve Fotkách i údaje
okamžiku. Funkce je zatím jen v lokálně ověřeném kódu.

**Rozhodnutí:** Míla výslovně schválil doplnění navrženého importu do okamžiku.
Kompatibilní kopie JPEG/MOV využívají stávající ukládání a synchronizaci.

**Další krok:** Nový podepsaný build pro SideStore a fyzický test jedné HEIC.

**Navrhované další kroky:** Žádné nové.

**Technický důkaz:** SwiftPM 63/63, závěrečné cílené testy médií 14/14,
generic iOS build PASS; původ, orientace, tiché video, kapacita, zrušení,
smazaný parent a obnova bez duplicit mají syntetickou regresi. Plná
projektová brána 1847/1847 a rychlá statická kontrola PASS. Bez instalace,
změny serveru a GitHub push. Fyzický picker/iCloud a end-to-end přenos
nově importovaného média zůstávají NEOVĚŘENO.

## 2026-10-03 21:06 WEST — Build 15 pro SideStore

**Hotovo:** Podepsaný instalační balíček s importem z Fotek je v Downloads
jako `Camino-15-20261003.ipa`.

**Rozhodnutí:** Míla výslovně zadal nový build. Instalace proběhne přes
SideStore se zachováním původní aplikace a dat; žádný GitHub push.

**Další krok:** Import IPA v SideStore a fyzický test jedné HEIC fotografie.

**Navrhované další kroky:** Žádné nové.

**Technický důkaz:** Zdroj `73085f17`, verze 0.1.0 (15), původní bundle ID.
Podepsaný iOS build, strict codesign před i po ZIP roundtrip, CRC a kontrola
verze PASS; 1 229 377 B. Podpis aktuálního profilu vyprší 4. 10. 16:07 UTC,
SideStore provede nový podpis. Předchozí 63/63 a plná brána 1847/1847 platí
pro stejný kód. Telefon bez instalace; fyzická přejímka není tímto potvrzena.

## 2026-10-03 21:23 WEST — Fyzický import videa a pokyn p+n

**Hotovo:** Míla potvrzuje vložení 14s videa z Fotek a jeho úspěšný přenos.

**Rozhodnutí:** Míla nyní výslovně autorizoval p+n čekající Camino dávky.
Nasazení Cockpitu se dokončí řízeným postupem a živým auditem; skutečnou
publikační účtenku vydává backend po pushnutí a ověření nového procesu.
Server Camina již obsahuje potřebný kontrakt; nový import je iOS funkce.

**Další krok:** Dokončit autorizované p+n; následně běžné používání.

**Navrhované další kroky:** Při příležitosti ověřit jednu HEIC fotografii.

**Technický důkaz:** Uživatelský PASS se týká importu a přenosu konkrétního
14s videa. Zvuk, orientace, iCloud, HEIC a dlouhá videa tím nejsou plošně
přijaté. Stejný kód má 63/63 SwiftPM, závěrečné 14/14 a bránu 1847/1847;
publikační brána se provede v registrovaném push/deploy postupu.

## 2026-10-10 20:18 CEST — Návrh filmové dílny z dat Camina

**Hotovo:** Na Mílův výslovný požadavek je zde uložen návrh, aby si ho mohl
přečíst celý bez posouvání SSH konverzace na telefonu. Jde o návrh budoucí
filmové dílny, nikoli o dokončenou funkci.

Navrhuji jednoduchou filmovou dílnu přímo v Cockpitu. Ovládala by se
v prohlížeči i z telefonu; samotný film by sestavoval Mac. Nebylo by potřeba
používat iMovie ani jiný samostatný videoeditor.

Největší smysl má automatický návrh, který můžeš před exportem upravit:

1. **Vybereš rozsah a délku:** jeden den, několik dnů nebo celou cestu
   a přibližnou požadovanou délku výsledného filmu.
2. **Aplikace sestaví návrh:** použije fotografie, vybrané úseky videí,
   názvy Momentů a tvoje nahrané hlasové komentáře. Dny mohou tvořit kapitoly.
3. **Návrh si prohlédneš a upravíš:** v přehledu záběrů změníš pořadí,
   vyřadíš záběr, zkrátíš video, nastavíš délku zobrazení fotografie
   a upravíš titulky.
4. **Tlačítkem „Vytvořit film“ vznikne MP4:** běžný soubor pro přehrávání
   a následné sdílení podle tvé volby.
5. **Návrh zůstane uložený:** později ho upravíš a vytvoříš novou verzi filmu
   bez nutnosti začínat znovu.

První verzi bych postavil jako krátký film z jednoho dne: chronologické
pořadí, fotografie, vybrané úseky videí, tvůj hlas a jednoduché titulky.
Technické sestavení může zajišťovat FFmpeg; jednoduché prolínání záběrů
je možné doplnit do návrhu. Rozsah a proveditelnost konkrétního exportu
ověří až prototyp.

Chytrý výběr nejlepších záběrů bych přidal později. Automatika nemusí poznat,
který okamžik má pro tebe osobní význam, proto je důležitá možnost ručních
úprav. Originály musí zůstat zachované a obsah označený „Jen pro mě“ se do
filmu nezařadí. Filmová část patří do samostatné budoucí etapy P2.

**Rozhodnutí:** Míla požádal uložit návrh do existujícího TVBCP Camina.
Zahájení implementace, konkrétní rozsah první verze ani nasazení tím nejsou
schválené; nové architektonické rozhodnutí nevzniklo.

**Další krok:** Míla si přečte návrh; před případným vývojem společně
upřesnit a potvrdit rozsah prvního filmu z jednoho dne.

**Navrhované další kroky:** Po odsouhlasení jednoduché první verze doplnit
uložení a opakované úpravy návrhu; chytrý výběr záběrů ponechat na později.

**Technický důkaz:** Dokumentační zápis vychází z návrhu v rozhovoru
10. října 2026. V tomto kroku se nemění aplikace ani média a nevzniká film;
funkčnost exportu nebyla testována.

## 2026-10-10 21:31 CEST — Podrobný návrh filmové dílny a Mílova upřesnění

**Hotovo:** Na výslovný pokyn Míly je zde uložen rozpracovaný plán P2 po
zapracování jeho připomínek. Jde o návrh vývoje; aplikace ani render nevznikly.
Tento zápis upřesňuje návrh z 20:18 a nahrazuje dřívější návrh automaticky
nabízet krátké výřezy videí a řešit čekající telefonní změny až před exportem.

**Rozhodnutí:** Míla určil dvě závazné podmínky:

- Každé video nabídnout celé. Výchozí rozsah je od začátku do konce;
  zkrácení začátku či konce provádí uživatel. Cílová délka filmu nesmí
  automaticky zkrátit video ani useknout hlas. Při přesahu se ukáže skutečná
  délka a uživatel může upravit výběr, ručně zkrátit klip nebo přijmout přesah.
- Film se vytváří výhradně z konečných, uzavřených dat a metadat doručených
  na Mac. Před zahájením filmové práce jsou všechny změny z telefonu odeslané
  a přijetí ověřené; nic nečeká ani se právě nepřenáší. Filmová dílna není
  živým střihem souběžně se měnící telefonní fronty. Telefon může dál sloužit
  jako prohlížeč pro ovládání dílny; to není pokračování sběru či synchronizace.

Ostatní níže uvedené technické volby a etapy zůstávají návrhem Adama.
Uložení plánu samo nepovoluje implementaci, nasazení ani práci s reálnými médii.

### Výsledek a první verze

Filmová dílna dostupná z Cockpitu, ovladatelná v prohlížeči na Macu i iPhonu;
film sestavuje Mac. První verze pracuje s jedním uzavřeným dnem, fotografiemi,
celými videi s ručním zkrácením, skutečným hlasem a jednoduchými titulky.
Orientační délka 2–5 minut je doporučení, ne limit; skutečný materiál má přednost.
Dlouhodobý cíl z F68 zůstává cestopis přibližně 20–30 minut podle materiálu.
Uložení a opakované úpravy návrhu patří už do první použitelné verze.

### Uživatelský postup

1. Dokončit záznamy a změny, odeslat je z telefonu a ověřit úplné přijetí
   na Macu. Teprve potom uzavřít vstupní sadu pro film.
2. V dílně vybrat uzavřený den, název a orientační délku filmu.
3. Projít chronologický návrh; fotografie mají navrženou délku, videa celou
   délku. U každé položky je patrný zdrojový okamžik a možnost vyřazení.
4. Upravit pořadí, délky fotografií, případně ručně zkrátit videa, doplnit
   titulky a vybrat vlastní hlasové komentáře.
5. Vytvořit a přehrát pracovní náhled, opravit střih a poté vytvořit MP4.
6. Uložený návrh lze později upravit; nový export má vlastní verzi a
   nepřepisuje předchozí film ani zdrojová média.

### Ovládání na telefonu

Čtyři části: Moje filmy, Výběr zdrojů, Sestavení, Náhled a export.
Editor používá svislé karty s náhledy, tlačítky Nahoru/Dolů, délkou fotografie,
in/out videa s přehráním úseku, zvukem, titulkem a volbou Zachovat při novém
návrhu. Vyřadit z filmu nemaže obsah Camina. Automatické ukládání ukazuje
Uloženo / Změny čekají na uložení; souběžná editace ze dvou prohlížečů nesmí
potichu přepsat novější revizi. Tato editace filmového projektu je oddělená
od již uzavřených zdrojových dat Camina.

### Návrh střihu, hlas a mapy

Automatika řadí chronologicky a může navrhnout výběr napříč dnem. Vynechané
povolené zdroje zůstávají dostupné k ručnímu přidání. Fotografie mohou mít
výchozí délku přibližně 4 s; video vždy celé. Hvězdičky se použijí jen při
ověřené dostupnosti jejich stavu na Macu. Ručně uzamčené střihy se při
přepočtu zachovají. Automatika bez obrazové analýzy neprohlašuje výřez za
nejlepší záběr a nevymýšlí události.

Zvuk videa lze ponechat, ztlumit nebo vypnout. Vlastní hlasový komentář lze
položit přes jeden nebo více obrazových záběrů; délka obrazu se přizpůsobí
řeči nebo se nabídne doplnění záběrů. Audio segmenty se skládají podle
skutečných návazností; mezery a chybějící části se nemaskují. Názvy filmu,
dne a záběrů jsou editovatelné titulky. Časově zarovnané titulky řeči jsou
pozdější funkce; upravený deník není přesným přepisem audia.

Mapa etapy může být obyčejný zařazený obrázek, například na začátku kapitoly.
Nevytváří GPS body ani nemění celkovou mapu Vieweru. Animovaná mapa a import
skutečné trasy patří do navazující etapy.

### Technický návrh a uzavření vstupů

Využít metadata a ověřené originály Camina, kontroly integrity a přípravu
náhledů. Doplnit filmový projekt, editor/API, validátor časové osy a samostatný
renderovací proces. Navržený základ: Python v prostředí Camina, SQLite pro
filmové projekty a trvalou frontu, soukromé pracovní soubory mimo Git a FFmpeg.
Zpočátku jeden render současně s nižší prioritou než základní provoz Camina.
Cockpit poskytuje vstup; nasazení filmové služby se ověřuje samostatně.

Před vznikem návrhu musí být ověřeno dokončení telefonní fronty, shoda
přijatých metadat a dostupnost ověřených médií na Macu. Samotný momentálně
prázdný seznam úloh není důkazem úplnosti. P2-B proto navrhne a ověří explicitní
uzavření vstupů s manifestem zdrojových ID, revizí a hashů. Nelze-li úplnost
prokázat, sada není uzavřená a filmová práce nezačne. Nejde o už existující
runtime funkci ani o požadavek, aby během renderu zůstával telefon připojený.

Časová osa ukládá stabilní ID položky, zdrojové ID/revizi/hash, in/out,
umístění ve filmu, orientaci, zvuk, původ titulku a ruční uzamčení. Export
odkazuje na konkrétní revizi návrhu a uzavřený manifest. Další zdrojové změny
se do něj samy nepřimíchají; jejich zahrnutí vyžaduje nové dokončení přenosu
a novou uzavřenou revizi vstupů.

Pracovní náhled navržen v 720p, finále MP4 1080p/16:9 z ověřených originálů,
nikoli ze zmenšených videí Vieweru. Svislé záběry celé bez automatického ořezu;
HDR a různé snímkové frekvence se sjednotí pouze v pracovních kopiích.
Nejprve jednoduché střihy, prolínání po ověření základu. FFmpeg a jeho místní
schopnosti ověří prototyp; nic zde netvrdí hotový či otestovaný export.

### Soukromí a spolehlivost

Editor je pro vlastníka; Jana zůstává čtenář. Filmový výběr má samostatnou
kontrolu povolenosti: Jen pro mě, skryté či nejasné zdroje se vyloučí již
před návrhem. Osobní souhrn není vstupem filmu. Originály se nemění.
Uzavření vstupů neobchází soukromí: případné pozdější doručené uzamčení
zneplatní ovládané navázané návrhy a výstupy a zastaví jejich výdej/render;
již stažené kopie nelze odvolat. Kontrola před renderem a před předáním
ověří platnost uzavřené sady, nikoli čekání na běžící synchronizaci.

Přerušený render se nevydává za hotový. Trvalá fronta zachová stav po restartu
a umožní bezpečné opakování nebo pokračování v ověřených částech. Kontrolovat
volné místo, zdroje, délky obrazu/zvuku a dokončení výsledného souboru.
Hudba, generovaný hlas, obrazová AI a automatické sdílení nejsou v první verzi.

### Etapy a přejímka

| Etapa | Výsledek | Podmínka dokončení |
|---|---|---|
| P2-A | Syntetický krátký film a minimální uložená časová osa. | Foto, celé vodorovné/svislé video, hlas a české titulky; správná orientace, celý konec řeči a přehrání na Macu/iPhonu. |
| P2-B | Uložený projekt, uzavření vstupů a výběr jednoho dne. | Doložená úplnost přenosu dat/metadat, manifest, obnova po restartu, vyloučení nepovolených zdrojů a nezměněné originály. |
| P2-C | Mobilní editor včetně ručního zkrácení celých videí. | Úpravy přežijí reload, konflikty neztratí práci, výchozí video není automaticky krácené, fyzické ovládání na iPhonu přijato. |
| P2-D | Trvalá renderovací fronta, náhled a verzovaný export. | Pád, zrušení, plný disk či chybějící zdroj nevytvoří falešný úspěch; render používá přesnou uzavřenou sadu. |
| P2-E | Jeden skutečný den upravený Mílou. | Celý film zhlédnutý a poslechnutý, přijatý výběr/stopáž/obraz/zvuk; základní provoz Camina zachovaný. |
| P2-F | Více dnů, kapitoly, prolog a závěr. | Delší projekt zachová ruční úpravy a původ zdrojů při přepočtu. |

T077 rozpadnout na konkrétní scénáře: úplnost a uzavření dat, odmítnutí čekajícího
či probíhajícího přenosu, celé video ve výchozím návrhu, ruční trim, přesah
stopáže bez automatického krácení, orientace/HDR/fps, návaznost hlasu,
zneplatnění zdroje, restart, chyba disku a skutečné přehrání výsledku.
Časový odhad dalších etap určit až podle rychlosti a nároků prototypu P2-A.

**Další krok:** Při samostatně zadaném vývoji začít P2-A se syntetickými
médii a minimálním formátem časové osy; zatím je uložen pouze plán.

**Navrhované další kroky:**
- P2-B: ověřitelné uzavření vstupů a uložený projekt jednoho dne.
- P2-C/P2-D: mobilní editor, pracovní náhled a obnovitelný export.
- P2-E/P2-F: přejímka skutečného dne a rozšíření na vícedenní film.
- Až po základu posoudit prolínání, titulky řeči, hudbu a skutečnou trasu.

**Technický důkaz:** Dokumentační úprava podle dvou výslovných připomínek
Míly. Kontrolují se dokumenty a diff; render, změna runtime, média ani
implementační testy nejsou součástí tohoto kroku.

### 2026-10-10 21:32 CEST – Podrobný návrh filmové dílny je uložen v TVBCP včetně obou Mílových připomínek

Hotovo:
- Podrobný návrh filmové dílny je uložen v TVBCP včetně obou Mílových připomínek
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Videa se nabízejí celá s možností ručního zkrácení. Filmová práce začíná pouze nad konečnými uzavřenými daty a metadaty přijatými na Macu, bez čekajícího či probíhajícího přenosu z telefonu.

Další krok:
- Po zadání vývoje zahájit syntetický prototyp P2-A s uloženou časovou osou

Navrhované další kroky:
- P2-B: ověřitelné uzavření vstupů a uložený projekt jednoho dne
- P2-C/P2-D: mobilní editor, náhled a obnovitelný export
- P2-E/P2-F: přejímka skutečného dne a vícedenní film
- Po přijetí základu posoudit prolínání, titulky řeči, hudbu a skutečnou trasu

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-camino`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.


## 2026-10-10 22:15 CEST — Schválená upřesnění filmové dílny po revizi zadání

**Hotovo:** Plán filmové dílny je doplněný o sedm upřesnění níže. Tento zápis
má přednost před rozpornými návrhy z 20:18 a 21:31, zejména před ručním
zapínáním ochrany střihu, automatickým vynecháváním zdrojů a požadavkem na
pokračování renderu po částech již v první verzi.

**Rozhodnutí:** Míla schválil doplnění návrhu a následné p+n celého čekajícího
balíčku. Jde o zadání budoucí filmové dílny a publikaci dokumentace, nikoli
pokyn k zahájení P2-A nebo práci s reálnými médii. Platí obě dřívější podmínky:
celá videa ve výchozím výběru a konečné uzavřené vstupy přijaté na Macu.

1. **Automatická ochrana ručních úprav (P2-B/P2-C/P2-F).** Každá uživatelská
   změna pořadí, délky, titulku, zvuku či vyřazení se zachová automaticky;
   uživatel nemusí dodatečně zapínat „Zachovat“. Nový automatický návrh vznikne
   jako samostatná varianta. Ochrana ručních úprav nikdy neobchází pozdější
   zneplatnění soukromí zdroje.
2. **Souběh komentáře a zvuku videa (P2-A/P2-C).** Během hlasového komentáře
   je zvuk videa ve výchozím nastavení ztišený; uživatel může poměr změnit.
   U videa s důležitou řečí lze komentář umístit před video nebo za ně.
   Automatické rozpoznání důležité řeči není součástí tohoto zadání.
3. **Ruční výběr úseku hlasu (P2-C).** Komentář se nabídne celý a uživatel
   může vědomě nastavit začátek a konec. Cílová stopáž řeč automaticky nekrátí.
   Pokud hlas přesahuje obraz, editor ukáže přesah a nabídne prodloužení
   fotografie nebo přidání záběrů; dlouhý nehybný závěr nevznikne bez
   upozornění. Návaznosti, skutečné mezery a chybějící audiočásti zůstávají
   rozlišitelné podle dosavadního kontraktu.
4. **Jednoduchý první návrh (P2-B).** Výchozí chronologický návrh zahrne
   všechny povolené položky vybraného uzavřeného dne; nic nevynechá jen kvůli
   orientační délce. Samostatný hlas se nabídne ve výběru komentářů a jeho
   umístění se potvrdí v editoru. Uživatel rozhoduje o vyřazení; automatický
   výběr menšího počtu položek je odložený.
5. **Věrný a krátký pracovní náhled (P2-A/P2-D).** Náhled a finále vycházejí
   ze stejné konkrétní uložené revize časové osy: shodné pořadí, délky,
   titulky, orientace a zvuk. Lišit se mohou rozlišením a kvalitou kódování.
   Po změně projektu je starší náhled jasně označený. Doplnit náhled zvoleného
   úseku pro kontrolu drobné opravy bez renderu celého filmu.
6. **Srozumitelné uzavření podkladů (P2-B).** Vědomá akce „Ověřit přenos
   a uzavřít podklady“ ověří dokončení telefonní fronty, přijaté revize
   metadat a dostupnost hashově ověřených médií. Při neúspěchu vypíše
   konkrétní chybějící či neověřenou část a filmovou práci nepovolí. Další
   doplnění vytvoří novou uzavřenou sadu; dosavadní střih se zachová a jeho
   převzetí nad novými vstupy musí být přehledné a vědomé. Pouhý prázdný
   seznam úloh nadále není důkazem úplnosti.
7. **Jednoduchá obnova a měření (P2-A/P2-D).** První verze po pádu bezpečně
   zopakuje export od začátku ze stejné uložené revize a manifestu, po
   opětovné kontrole povolenosti a integrity zdrojů. Zachová projekt i starší
   hotové exporty; neúplný soubor se nevydává za výsledek. Pokračování z
   vyrenderovaných částí je odložené do doby, kdy ho odůvodní naměřené časy.
   Už P2-A změří na Mílově Macu délku vzorku, čas náhledu/exportu, velikost
   výsledku a nejvyšší dodatečnou spotřebu disku včetně pracovních kopií.

**Další krok:** Dokončit autorizované p+n dokumentačního balíčku. Po
samostatném zadání vývoje začít syntetickým P2-A s uloženou časovou osou,
přejímkou obrazu/zvuku a měřením času i prostoru.

**Navrhované další kroky:**
- P2-B: ověřitelné uzavření vstupů, všechny povolené zdroje dne a uložený projekt.
- P2-C/P2-D: mobilní editor s chráněnými úpravami, pravidla hlasu, věrný náhled a opakovatelný export.
- P2-E/P2-F: přejímka skutečného dne a vícedenní film se zachováním ručního střihu.
- Optimalizace renderu po částech až podle naměřených nároků základu.

**Technický důkaz:** Revize byla porovnána s plánem P2-A až P2-F a F68–F70.
Jde pouze o dokumentaci; funkční, renderovací a fyzické přejímky nejsou
provedené. Rizika času exportu, diskových nároků a použitelnosti mobilního
střihu zůstávají otevřená. Výsledek p+n dokládá aktuální GitHub audit a
serverová nasazovací účtenka, nikoli tento předpublikační zápis.


## 2026-10-10 22:38 CEST — P2-A: lokální syntetický film, časová osa a měření

**Hotovo:** Implementovaný jednorázový prototyp sestaví z uloženého projektu
syntetický film s fotografií, celými videi v obou orientacích i s rotační
maticí, českými titulky a testovací řečí přes střihy. Náhled a finále mají
stejnou 22s časovou osu. Vzniká kontrolovaný MP4, místní přehrávač výsledků
a měřicí účtenka. Zdrojová média ani předchozí exporty se nepřepisují.

**Rozhodnutí:** Míla výslovně zahájil P2-A a požádal o report struktury a
řádků kódu. Vyvinutý rozsah je lokální syntetický prototyp. P2-B ani práce
nad skutečným archivem se nezahajují; nový krok není pushnutý nebo nasazený.
Testovací lokální TTS není produktová funkce generovaného hlasu. HDR se
zatím odmítá, protože převod barev nebyl ověřený.

**Další krok:** Jediný fyzický checkpoint P2-A/MAC1: přehrát celé finále
se zvukem. PASS = česká diakritika, správná orientace a celé rámy, celý
komentář včetně „šťastnou cestu“. Potom samostatně P2-A/IPHONE1.

**Navrhované další kroky:**
- P2-B po přijetí P2-A: ověřitelné uzavření skutečných vstupů a projekt dne.
- P2-C/P2-D: mobilní editor, dílčí náhled a trvalá fronta.
- Převod HDR a produkční povolenost médií ověřit před skutečnými vstupy.

**Technický důkaz:** 15/15 cílených testů P2-A PASS; celý 720p/1080p výstup
dekódován, snímky pěti scén vizuálně ověřené. Konec aktivní řeči má korelaci
PCM se zdrojem 0,996558. Běh `run-xip7fnef`: náhled 4,221 s / 1 865 006 B,
finále 12,490 s / 4 723 927 B; celý experiment 20,877 s a měřená alokovaná
špička 10 383 360 B. Podrobná metoda, konečný výsledek plné brány, rozsah
809 přidaných řádků Pythonu a struktura jsou v `camino/docs/P2A_FILM_REPORT.md`.
Fyzický Mac/iPhone a lidský poslech NEOVĚŘENO, P2-A není plně přijaté.

## 2026-10-11 15:20 CEST — P2-A: první kontrola přes iPhone

**Hotovo:** Lokálně připravená Cockpit stránka zpřístupní jen syntetický
náhled a finální film P2-A. Video se vydává jako MP4 s podporou částečného
načítání pro Safari; jiné soubory z testovacího adresáře cesta odmítá.

**Rozhodnutí:** Míla je na Caminu daleko od Macu. První fyzická kontrola se
proto přesouvá na iPhone; Mac kontrola zůstává otevřená pro pozdější návrat.
Původní kritéria obrazu a zvuku ani požadavek obou výsledků se nemění.

**Další krok:** Po samostatném schválení nasazení Cockpitu živě ověřit odkaz,
pak požádat Mílu jen o P2-A/IPHONE1: celé 22s finále se zvukem PASS/FAIL.

**Navrhované další kroky:** Po návratu dokončit P2-A/MAC1. Po přijetí P2-A
navázat P2-B s uzavřením skutečných vstupů.

**Technický důkaz:** Test modulu Cockpit serveru 4/4 PASS včetně HTTP 206,
MIME `video/mp4`, odmítnutí jiné cesty a neplatného rozsahu; plná brána
1867/1867 PASS. Běžící Cockpit
ani fyzický iPhone ještě nejsou ověřené; připravený kód není pushnutý/nasazený.

## 2026-10-11 15:45 CEST — P2-A: nasazení náhledu pro iPhone

**Hotovo:** Syntetický film lze otevřít přes tailnet Cockpit. Dva lokální
vývojové commity byly odeslány na GitHub; řízený restart nasadil nový kód.
Stránka i MP4 fungují přes HTTPS, finální soubor je bitově shodný s místním.

**Rozhodnutí:** Míla výslovně zadal c+p+n. První fyzickou přejímkou zůstává
iPhone, Mac bude možné ověřit po návratu; automatické testy nejsou lidský PASS.

**Další krok:** Míla otevře odkaz na iPhonu, přehraje celé 22s finále se
zvukem a vrátí výsledek P2-A/IPHONE1 PASS/FAIL.

**Navrhované další kroky:** P2-A/MAC1 po návratu; po obou výsledcích rozhodnout
o přijetí P2-A a navázání P2-B.

**Technický důkaz:** Plná brána 1867/1867 PASS, GitHub `main` po pushi
shodný s lokálním, Cockpit `deployed` a smoke 5/5. Tailnet HTTPS stránka
200, video 206, celé MP4 200 a SHA-256 shodné s místním výstupem.

## 2026-10-11 16:05 CEST — P2-A: film přímo v Cockpitu

**Hotovo:** Lokálně připravený přímý vstup Film P2-A v horní liště Cockpitu
otevírá vestavěný přehrávač finálního syntetického filmu. Po zavření se video
zastaví. Původní soukromá serverová cesta a allowlist zůstaly stejné.

**Rozhodnutí:** Míla chtěl film spustit přes Cockpit; samostatný Safari odkaz
hlásil chybu a nesplnil očekávaný způsob otevření. Přesný text chyby neznáme,
proto změna netvrdí vyřešení síťové příčiny.

**Další krok:** Dokončit schválené c+p+n opravy a ověřit nový vstup přes
tailnet; pak Míla provede P2-A/IPHONE1 přímo v Cockpitu.

**Navrhované další kroky:** P2-A/MAC1 po návratu. Po obou fyzických výsledcích
rozhodnout o přijetí P2-A a pokračování P2-B.

**Technický důkaz:** Frontend a server cíleně 22/22 PASS; plná brána a nové
nasazení ještě běží. Fyzický iPhone zůstává NEOVĚŘENO.

## 2026-10-11 16:17 CEST — P2-A: vstup v Cockpitu nasazený

**Hotovo:** Film P2-A lze v běžícím Cockpitu otevřít přímo z horní lišty a
spustit ve vestavěném přehrávači. Nasazení i kontrola soukromé HTTPS cesty
proběhly; syntetické finále je bitově shodné s původním výstupem.

**Rozhodnutí:** P2-A/IPHONE1 zůstává otevřená fyzická přejímka. Nasazené UI
a síťový test nenahrazují lidské přehrání ani nevysvětlují původní Safari chybu.

**Další krok:** Míla přehraje celé 22s finále se zvukem přes Film P2-A v
Cockpitu na iPhonu a sdělí P2-A/IPHONE1 PASS/FAIL nebo přesnou chybu.

**Navrhované další kroky:** P2-A/MAC1 po návratu; po obou fyzických výsledcích
rozhodnout o přijetí P2-A a pokračování P2-B.

**Technický důkaz:** 1867/1867 testů PASS, nasazení `deployed` a smoke 5/5.
Tailnet HTTPS stránka obsahuje nový vstup; finální MP4 HTTP 206 `video/mp4`,
4 723 927 B a shodný SHA-256.

## 2026-10-11 16:35 CEST — P2-A: oprava závěru syntetického komentáře

**Hotovo:** Mílův poslech odhalil, že původní testovací film mluví kontrolní
instrukci a hlas končí dlouho před obrazem. Nový neměnný syntetický běh má
samostatnou závěrečnou větu „Šťastnou cestu.“ a po ní jednu sekundu obrazu.
Původní běh zůstává zachovaný, opravená verze je zatím jen lokální.

**Rozhodnutí:** Původní iPhone přehrání není P2-A/IPHONE1 PASS. Opravujeme
pouze obsah a časování syntetické zkoušky; skutečná média ani soukromostní
pravidla se nemění.

**Další krok:** Dokončit push a řízené nasazení opravené verze;
potom Míla znovu přehraje celé finále na iPhonu se zvukem a sdělí PASS/FAIL.

**Navrhované další kroky:** P2-A/MAC1 po návratu; P2-B až po obou fyzických
přejímkách.

**Technický důkaz:** Původní hlas končil v 12,775 s z 22 s. Nový hlas začíná
v 7,335 s a končí v 21,000 s; finální MP4 začíná poslední ticho v 20,956 s.
Nový běh `run-112rz9am`, 16/16 filmových testů a plná brána 1868/1868 PASS, oba profily celé
dekódované, závěrečný snímek vizuálně ověřený. Publikační a lidský důkaz čekají.

## 2026-10-11 17:10 CEST — P2-A: opravený film živě v Cockpitu

**Hotovo:** Opravené syntetické finále je dostupné přes tlačítko Film P2-A
v běžícím Cockpitu. Vzdáleně vydávaný soubor odpovídá přesně místnímu
opravenému běhu.

**Rozhodnutí:** Rozsah P2-A a kritéria fyzické přejímky se nemění. Dřívější
iPhone přehrání chybné verze není PASS.

**Další krok:** Míla na iPhonu přehraje celé nové 22s finále se zvukem a
sdělí P2-A/IPHONE1 PASS/FAIL nebo přesnou chybu.

**Navrhované další kroky:** P2-A/MAC1 po návratu k Macu; P2-B až po obou
fyzických přejímkách.

**Technický důkaz:** GitHub `main` obsahuje `1208ea21`, publikační brána
1868/1868 PASS, řízené nasazení `deployed`, nový proces a smoke 5/5.
Tailnet HTTPS stránka vrací 200; finální MP4 podporuje 206 `video/mp4` a
celých 4 728 960 B má SHA-256
`abb68af56188dea97e40e0eb54fe3f85626d262309a12ffb4437591c10142e1d`.
Fyzický iPhone poslech ani Mac přehrání nové verze nebyly provedené.

## 2026-10-11 17:16 CEST — P2-A/IPHONE1: opravený film PASS

**Hotovo:** Míla po přehrání opraveného 22s finále přes Film P2-A v Cockpitu
na iPhonu oznámil **P2-A/IPHONE1 PASS**.

**Rozhodnutí:** Jde o přejímku opravené verze; původní chybná verze zůstává
nepřijatá. P2-A jako celek vyžaduje ještě samostatné P2-A/MAC1.

**Další krok:** Po dostupnosti Macu přehrát celé opravené finále se zvukem
a sdělit P2-A/MAC1 PASS/FAIL.

**Navrhované další kroky:** Po obou fyzických přejímkách rozhodnout o
přijetí P2-A a zahájení P2-B s uzavřenými skutečnými vstupy.

**Technický důkaz:** Mílovo přímé hlášení PASS po výzvě k fyzickému přehrání
nového filmu; nasazení commitu `1208ea21` a shoda vzdáleného MP4 byly
ověřené samostatně. Mac výsledek dosud chybí.

## 2026-10-11 17:31 CEST — P2-B: rozhodnutí o uzavření jednoho dne

**Hotovo:** Míla zadal P2-B pro první den 6. 10. 2026 a potvrdil úplnost
Macu. Lokální kód přidal vědomé uzavření telefonu proti autoritativnímu
Macu, neměnný manifest a uložený projekt dne. P2-B zatím nevytváří MP4.

**Rozhodnutí:** Server vyžaduje shodu úplného inventáře včetně revizí,
identity serveru, epochy a kurzoru, nulovou čekající frontu a ověření
originálů. Do projektu vybírá aktuální `diary` a neskryté zdroje;
videa zůstávají celá, audio je samostatnou volbou. Po změně inventáře,
povolenosti nebo hashů vyžaduje nové uzavření. Skutečný den se neprohlašuje
za uzavřený bez čerstvého iPhone důkazu.

**Další krok:** Po samostatném oprávnění k publikaci nasadit kompatibilní
server a aplikaci bez mazání dat; na iPhonu vědomě uzavřít den a ověřit
projekt s 30 povolenými zdroji.

**Navrhované další kroky:** P2-A/MAC1 dokončit fyzicky po návratu k Macu;
po skutečném uzavření dne navázat P2-C/D.

**Technický důkaz:** Read-only Mac audit: 11 Momentů, 34 úplných ověřených
originálů; 30 zdrojů `diary` a 4 soukromé audio přílohy. Syntetický owner
API test ověřil odmítnutí neúplnosti, idempotenci, restart a pozdější
změnu soukromí; iOS Simulator build a plná brána 1876/1876 prošly. Skutečný
filmový projekt ani manifest nebyly uloženy.

## 2026-10-11 17:46 CEST — P2-B: lokální checkpoint a iPhone artefakt

**Hotovo:** Lokální kód P2-B je v commitu `cde61193`, oba profilové
workspaces jsou čistě zarovnané. Nepodepsaný iPhoneOS build 17 a IPA byly
sestaveny a ověřeny bez instalace.

**Rozhodnutí:** Podpis a fyzická přejímka jsou samostatné. Nepodepsané IPA
není důkaz instalovatelnosti ani úplnosti dne; dosud nebylo distribuováno.

**Další krok:** Po samostatném publikačním pokynu bezpečně zpřístupnit
kompatibilní server a aplikaci, na iPhonu ověřit SideStore podpis a
zachování dat, potom uzavřít 6. 10. přes čerstvý inventář telefonu.

**Navrhované další kroky:** P2-A/MAC1 dokončit po návratu k Macu; po
skutečném uzavření dne navázat P2-C/D.

**Technický důkaz:** Plná brána 1876/1876 a iOS Simulator build PASS.
Podepsaný Release build zastavil CodeSign `errSecInternalComponent` při
nepřístupném login Keychain. Nepodepsané IPA 1 226 501 B prošlo ZIP
kontrolou a shodou binárky; podrobnost je v P2-B reportu.

## 2026-10-11 18:03 CEST — P2-B: připravený release, push čeká

**Hotovo:** Míla schválil push a řízené nasazení P2-B. Opravený výběr
serverových souborů zahrnuje filmový modul i jeho pomocnou knihovnu;
izolovaný release import a plná brána 1876/1876 prošly.

**Rozhodnutí:** Po přesném pushi provést stop, upgrade a start vlastněné
služby, s kontrolou archivu a živého owner API. Existující Serve cestu
nepřenastavovat.

**Další krok:** Dokončit GitHub přihlášení na iPhonu a odeslat auditovaný
balíček; pak řízeně nasadit server a ověřit funkci P2-B.

**Navrhované další kroky:** Samostatně řešit podpis/instalaci iPhone app;
P2-A/MAC1 dokončit po návratu k Macu; po uzavření dne navázat P2-C/D.

**Technický důkaz:** Lokální `2fada468`, pět čekajících commitů vůči
`1208ea21`. HTTPS push blokuje Keychain `-25308`; `gh` token je neplatný,
SSH klíč GitHub nepřijal. Archiv před změnou: 578 operací, 75 Momentů,
202 ověřených médií. Server stále běží na starém releasu bez P2-B.

## 2026-10-11 18:10 CEST — P2-B: přihlášení vypršelo

**Hotovo:** Lokální release a projektové předání jsou uložené. Stará
služba běží dál; žádný archivní soubor ani Serve cesta se neměnily.

**Rozhodnutí:** Schválené p+n pokračuje až po nové GitHub autentizaci.
Zastavení a upgrade služby před pushem neproběhly.

**Další krok:** Obnovit přihlášení GitHub CLI z iPhonu, zkontrolovat přesný
fast-forward, pushnout a řízeně nasadit s živým auditem.

**Navrhované další kroky:** Samostatně řešit instalaci iPhone app a
skutečný důkaz uzavření dne; P2-A/MAC1 po návratu k Macu.

**Technický důkaz:** Device flow skončil `expired_token`. K 18:10 bylo
šest lokálních commitů nad `origin/main` a běžící owner API stále
nehlásilo `film_closed_day_v1`.

## 2026-10-12 16:45 CEST — P2-B: publikace dokončena bez změny telefonu

**Hotovo:** GitHub blokátor je vyřešený a připravený server P2-B je
publikovaný a běží. Soukromé owner API, Viewer, mapa a přehratelné mediální
cesty prošly kontrolou. Archiv včetně všech 216 originálů zůstal přesně
shodný. Míla oznámil polední obnovení běžné funkčnosti aplikace; dnešní
serverový krok telefon neměnil.

**Rozhodnutí:** Navázali jsme na schválené p+n; Míla doplnil přesnou globální
brzdu. Přepnula se pouze vlastní služba se zachovanou původní konfigurací
a čtyřmi DB snapshoty. Síť ani přístupy se neměnily. Skutečný den nelze
uzavřít bez nového explicitního důkazu telefonu.

**Další krok:** Dokončit GitHub bránu opraveného workflow; potom na
fungujícím iPhonu ověřit P2-B vstup Film a vědomě uzavřít 6. 10.; potom zkontrolovat skutečnou účtenku a povolené zdroje.

**Navrhované další kroky:** P2-A/MAC1 po návratu k Macu; P2-C/D teprve po
skutečném uzavření dne a samostatném zadání.

**Technický důkaz:** Release `e95568b7999e`, owner API 200 a
`film_closed_day_v1`, Viewer/mapa 200, foto/audio/video 206, anonymní přístup
odmítnutý, soukromý zdroj 404, Cockpit smoke 5/5. Cíleně 71/71 PASS a
izolovaný import PASS; přenosový kód, schéma i závislosti shodné s běžící
předchozí verzí. Archiv před/po: 624 operací, 82 Momentů, 216 médií,
1 673 901 399 B, shodné identity/cesty a všechny SHA-256. Podrobnosti v
`camino/docs/P2B_CLOSED_DAY_REPORT.md`. Fyzické P2-B a P2-A/MAC1 neověřené.
GitHub běh `38264584628` odhalil starší Xcode Git a chybějící serverové
závislosti. Opravuje se pouze workflow (macOS 15/Xcode 26.3, Git preflight,
oba requirements); plná místní brána 1876/1876 PASS, nová GitHub brána
zatím čeká na výsledek.
Běžící Camino se kvůli opravě CI znovu nenasazuje.

## 2026-10-12 17:01 CEST — P2-B: GitHub kontrola dokončená

**Hotovo:** Publikační blokátory P2-B jsou odstraněné. Připravený server
běží a opravené GitHub kontrolní prostředí prošlo celou bránou.
Fungující telefonní aplikace zůstala beze změny, archiv i Viewer mají
ověřené zachování. Skutečný den ještě čeká na důkaz telefonu.

**Rozhodnutí:** Žádné nové produktové rozhodnutí. Oprava se týká jen
GitHub testovacího prostředí; ověřená služba se znovu nenasazuje.

**Další krok:** Na fungujícím telefonu ověřit sekci Film a vědomě uzavřít
6. 10.; potom zkontrolovat skutečnou účtenku a aktuální povolené zdroje.

**Navrhované další kroky:** P2-A/MAC1 po návratu k Macu; P2-C/D až po
skutečném uzavření dne a samostatném zadání.

**Technický důkaz:** Čerstvá místní plná brána 1876/1876 PASS.
[GitHub běh 38266173656](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38266173656) pro `31927650` je success:
1876 testů OK, 10 podmíněně přeskočených; vybraný Apple Git 2.50.1
přijal `--attr-source` a oba requirements se nainstalovaly. Běžící
Camino release `e95568b7999e` má stejný serverový kód; mezi těmito heads
jsou jen workflow a dokumentace. Privátní filmové úložiště zatím 0 projektů.

## 2026-10-12 17:58 CEST — P2-B: konečná Mac sada a projekt pro Cockpit

**Hotovo:** Skutečný projekt 6. října je uložený na Macu a ověřený.
Obsahuje 11 fotografií, 14 celých videí a 5 zvukových voleb; obrazová osa
má 25 položek a 3 min 20,475 s. Lokální Cockpit zobrazí jeho přehled,
syntetickou ukázku drží samostatně. Původní archiv zůstal přesně shodný.

**Rozhodnutí:** Míla potvrdil konečnost Mac dat a upřesnil zamýšlený postup
přes Cockpit. Následně zadal pokračování. Projekt proto zaznamenává
vlastnické potvrzení Mac sady, nepředstírá telefonní inventář ani prázdnou
frontu. Tato varianta nepotřebuje změnu nebo znovupotvrzení v telefonu.
Archiv se čte striktně read-only, filmové soubory jsou oddělené.

**Další krok:** Po lokálním checkpointu a samostatném souhlasu
pushnout a nasadit pouze Cockpit a ověřit nový přehled skutečného projektu.

**Navrhované další kroky:** P2-C editor uloženého projektu po přijetí
přehledu; render P2-D samostatně; P2-A/MAC1 po návratu k Macu.

**Technický důkaz:** 12/12 nových testů a 82/82 souvisejících PASS;
HTTP náhled 200, 30 povolených zdrojů, 25 obrazových položek a 5 audio
voleb. Plná závěrečná brána 1888/1888 PASS (297,270 s testů). Archiv před/po je přesně shodný: 624 operací,
82 Momentů, 216 ověřených originálů a 1 673 901 399 B, stejné identity
a SHA-256. Telefon, Camino služba a síť beze změny. Prohlížečová vizuální
kontrola NEOVĚŘENO (CUA nemá prohlížeč); nový Cockpit není nasazený.

## 2026-10-12 18:19 CEST — P2-B: schválené Cockpit p+n dokončené

**Hotovo:** Přesný commit `2e60f8db` je na GitHubu. Řízeně se restartoval
jen ověřený Cockpit: PID 23125 → 98814, otisk `59ae89a955a402c4`, účtenka
`deployed`, smoke 5/5. Film Camino je dostupný přes loopback i soukromé
HTTPS a vrací skutečný validní projekt 6. 10.: 11 foto, 14 celých videí,
5 zvukových voleb, 25 obrazových položek a 200 475 ms.

**Rozhodnutí:** Míla výslovně zadal „ok, p+n“ pro připravený Mac projekt
a nasazení pouze Cockpitu. Telefon, Camino služba ani síť se nemění.

**Další krok:** Obnovit Cockpit a fyzicky potvrdit přehled Film Camino.

**Navrhované další kroky:** P2-C editor této uložené sady po samostatném
zadání; P2-D render a P2-A/MAC1 poslech zůstávají oddělené.

**Technický důkaz:** Plná místní brána 1888/1888 PASS. Živý root/projekt
HTTP/HTTPS 200; owner API a Viewer/mapa zdravé, foto/audio/video Range 206,
anonymní 401, owner-only zdroj 404. Archiv před/po přesně shodný:
624 operací, 82 Momentů, 216 originálů a 1 673 901 399 B, shodné identity,
epocha, kurzor, tripy a všechny SHA-256. Camino zůstává na `e95568b7999e`,
PID 67017; Serve beze změny, Funnel off. Vizuální Safari/telefonní klik
NEOVĚŘENO (CUA nemá prohlížeč). [GitHub brána 38276225453](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38276225453) pro `2e60f8db` má success: 1888 testů OK, 10 podmíněně přeskočených, 157,222 s.


## 2026-10-12 19:21 CEST — P2-C/D: editor a první skutečné MP4

**Hotovo:** Lokální editor uloženého dne 6. 10. umí řadit záběry, upravit
foto/video/titulky/zvuk a chrání ruční práci neměnnými revizemi. Trvalá
fronta má dílčí náhled, 720p a 1080p MP4; hotové jsou oba skutečné profily
revize 1, přibližně 3:20, se všemi 25 obrazovými položkami. Pět hlasových
částí se nabízí celých k vědomému umístění. Původní archiv je beze změny.

**Rozhodnutí:** Míla zadal pokračování editorem a MP4. Nový krok je místní;
push a nasazení nového Cockpitu vyžadují samostatné potvrzení. Telefon ani
Camino služba se nemění; žádné zkracování obsahu jen kvůli cílové délce.

**Další krok:** Po checkpointu samostatné p+n pouze Cockpitu.

**Navrhované další kroky:** P2-E fyzická přejímka editoru a celého filmu
se zvukem; P2-F až po přijetí základu a samostatném zadání.

**Technický důkaz:** Oba MP4 úplně dekódované, 6014 snímků, video
200 465 ms / audio 200 466 ms. Náhled 25 617 860 B / 135,034 s, finále
115 011 021 B / 181,017 s. Lokální HTTP editor 200 a film Range 206 / HEAD
200, všechny záběry náhledu vizuálně zkontrolované. Cílené testy PASS,
závěrečná plná brána 1907/1907 PASS (319,041 s testů). Archiv před/po přesně shodný: 624 operací,
82 Momentů, 216 originálů, 1 673 901 399 B a všechny SHA-256. Owner/Viewer,
mapa i média zdravé, Serve beze změny a Funnel off. Safari/iPhone ovládání
a celý lidský poslech NEOVĚŘENO. Report `P2CD_EDITOR_MP4_REPORT.md`.


## 2026-10-12 19:47 CEST — P2-C/D: nasazený editor a skutečné MP4 v Cockpitu

**Hotovo:** Film Camino v běžícím Cockpitu nabízí editor a oba hotové
720p/1080p filmy dne 6. 10., revize 1, přibližně 3:20. Existující MP4
se použily přímo, bez nového renderu. Původní Camino a všechna data jsou
zachované.

**Rozhodnutí:** Míla potvrdil „ok p+n cockpit“: publikovat připravený
editor a nasadit pouze Cockpit. Telefon, Camino služba, originály ani
síť se nemění.

**Další krok:** P2-E: fyzicky otevřít editor a přehrát celý skutečný film
se zvukem přes Film Camino.

**Navrhované další kroky:** Ruční umístění samostatných hlasových částí
a přejímka takto upraveného filmu; P2-F až po přijetí základu.

**Technický důkaz:** Nasazený `7c9547fc`, nový Cockpit PID 35526, otisk
`4f1f0c17ac72659f`, účtenka `deployed`, smoke 5/5. Plná místní brána
1907 testů OK (319,041 s), přednasazovací statická brána PASS. Živý
HTTP/HTTPS root/editor 200, 25 záběrů a 5 hlasových nabídek; oba MP4
HEAD 200 / Range 206 s přesnými bajty. Celé HTTPS finále má shodný
SHA-256. Archiv před/po přesně shodný: 624 operací, 82 Momentů, 216
originálů, 1 673 901 399 B, identity/tripy a všechny SHA-256. Camino
nadále `e95568b7999e`, PID 67017; owner HTTP/HTTPS, Viewer/mapa/map-data
200, foto/audio/video Range 206, anonymní Viewer 401. Serve shodný,
Funnel off. Safari/iPhone ovládání a celý lidský poslech NEOVĚŘENO.
[GitHub brána 38285925799](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38285925799) nasazeného `7c9547fc` má success: 1907 testů OK, 13 podmíněně přeskočených, 203,452 s. Skutečné render testy a všech 19 editor testů prošly místně bez přeskočení.


## 2026-10-12 20:14 CEST — první hodnocení filmu OK, editor zítra

**Hotovo:** Míla 12. 10. hodnotí první skutečný film „na první dobrou ok“ a strukturu editoru dobře. Ovládání vyzkouší 13. 10.; není hlášená chyba vyžadující dnešní opravu.

**Rozhodnutí:** Dnes ukončit relaci; pokračovat zkouškou editoru 13. 10.
Žádné nové vývojové, renderovací ani provozní změny nejsou potřebné.

**Další krok:** 13. 10. ověřit ovládání: změnit pořadí dvou záběrů a délku jedné fotky, vyčkat uložení, obnovit stránku a přehrát dílčí náhled. PASS: pořadí i délka zůstanou uložené a náhled odpovídá střihu.

**Navrhované další kroky:** Ruční komentář a podrobná P2-E přejímka;
P2-F až po přijetí základu a samostatném zadání.

**Technický důkaz:** Uživatelské hodnocení v této relaci. Zařízení, profil
a rozsah poslechu nejsou uvedené; není to úplný protokol P2-E. Technické
ověření nasazení zůstává v `P2CD_EDITOR_MP4_REPORT.md`. Tento krok mění
pouze projektové zápisy, bez nového renderu či nasazení.


## 2026-10-13 18:11 CEST — video se zvukem opět startuje; příčina nepotvrzená

**Hotovo:** Po cílených telefonních testech Míla hlásí, že video se
zvukem v Caminu opět běží i se zapnutým Bluetooth. Kamera, tiché video
a Komentář fungují. Aplikace se neaktualizovala ani nepřeinstalovala.

**Rozhodnutí:** Příčinu nepřipsat Bluetooth bez reprodukce. Pracovní
hypotéza je dočasně zaseknutá příprava zvuku videa; další opravu
neodvozovat jen z matoucí hlášky o mikrofonu.

**Další krok:** Ukončit a uložit nynější klip, přehrát a potvrdit
slyšitelný zvuk. Při návratu závady nejdřív zachytit přesnou hlášku
a předchozí činnost.

**Navrhované další kroky:** Ovládání filmového editoru po stabilizaci
běžného záznamu; podrobná P2-E přejímka zůstává otevřená.

**Technický důkaz:** Uživatelská pozorování a čtení nezměněného kódu.
Samostatně nepotvrzené uložení/poslech posledního klipu a chybějící
telefonní log nedovolují označit kořenovou příčinu či úplný PASS.
Report `VIDEO_AUDIO_INCIDENT_20261013.md`. Tento krok mění jen zápisy.


### 2026-10-14 17:26 CEST — Odmítnutá metadata, příprava bezpečné diagnostiky

Hotovo:
- Mac je dostupný a dosavadní archiv prošel úplným integritním auditem. Připravené doplnění ukáže technický důvod konkrétního odmítnutí bez soukromého obsahu; dosud není nasazené a přenos není opravený.

Rozhodnutí:
- Míla odložil film a zadal diagnostiku přenosu. Žádná nová instalace, reset, změna identity, sítě nebo archivních dat. Nasazení není dosud schválené.

Další krok:
- Po aktuálním potvrzení řízeně nasadit diagnostiku pouze Camino služby a jedním opakováním telefonní synchronizace zachytit konkrétní důvod.

Navrhované další kroky:
- Cílená oprava podle doloženého důvodu a kontrola dokončení metadat i médií.
- Film/editor až po obnovení spolehlivého přenosu.

Technický důkaz:
- HTTP/HTTPS 200, flags false, žádný konfliktní kandidát; 740 operací, 103 Momentů, všech 234 ověřených originálů / 1 870 503 746 B má správné SHA-256. Cílené testy 17/17, plná brána 1909/1909 a sedm samostatných nových testů PASS; izolovaný import PASS. Report `METADATA_REJECTION_INCIDENT_20261014.md`.


### 2026-10-14 17:55 CEST — Diagnostika odmítnutých metadat nasazená

Hotovo:
- Mac už umí zaznamenat technický důvod odmítnuté operace bez soukromých textů, médií, GPS, UUID či přihlašovacích údajů. Nasazení dokončené, konkrétní chyba zatím nezachycená a přenos není označený za opravený.
- Archiv před/po přesně shodný včetně všech 234 ověřených originálů; owner HTTP/HTTPS, Viewer/mapa a foto/audio/video Range fungují. Čtyři snapshoty DB a původní konfigurace ověřené; Cockpit a Serve beze změny.

Rozhodnutí:
- Míla přesnou větou globální brzdy potvrdil nasazení diagnostiky pouze Camino služby. Žádná instalace telefonu, změna validace, reset, párování, archivní oprava ani síťový zásah.

Další krok:
- Jeden telefonní pokus „Synchronizovat nyní“; přečíst bezpečný nový log a podle konkrétního důvodu cíleně opravit přenos.

Navrhované další kroky:
- Po opravě ověřit dokončení metadat i médií; film/editor naváže později.

Technický důkaz:
- Registrované stop/upgrade/start: vydání `e815ae75dc38`, PID 75891. Shodných 740 operací, kurzor 740, 103 Momentů, identity/tripy a 234 originálů / 1 870 503 746 B, SHA-256 PASS. Owner/Viewer/mapa HTTP/HTTPS 200, mediální Range 206, anonymní Viewer 401. Cockpit PID 35526 / otisk `4f1f0c17ac72659f`, smoke 5/5; Serve otisk shodný, Funnel off. Karta schvalování vyčištěná; report `METADATA_REJECTION_INCIDENT_20261014.md`.


### 2026-10-14 18:01 CEST — Zachycená neplatná změna názvu přílohy

Hotovo:
- Mílův telefonní pokus je zachycený: stále stejná operace názvu přílohy 741 končí HTTP 422. Server nevidí platnou cílovou fotografii/video u požadovaného Momentu; přenos není opravený.

Rozhodnutí:
- Žádné nové rozhodnutí o opravě dat. Kontrola vazby, přijaté přesné obálky, cursor a originály zůstávají zachované.

Další krok:
- Zjistit od Míly, zda před závadou přejmenoval či smazal přílohu; podle doložené příčiny připravit cílenou opravu.

Navrhované další kroky:
- Po opravě ověřit navazující metadata i média. Další opakování stejného telefonního pokusu nyní nepomůže.

Technický důkaz:
- Bezpečný log: `status=422 code=invalid_request reason=title target must be a photo or video of this Moment kind=update_metadata sequence=741`, shodný při opakování. `CaminoSyncDiscovery` vychází z živých Assetů, zatímco snapshot zachovává historické změny názvů; `suppressDeletedContent` odstraňuje deklaraci smazaného Assetu, ale ne název přílohy ponechaného Momentu. Jde o doložené riziko kódu, nikoli ještě potvrzený spouštěč tohoto incidentu.


### 2026-10-14 18:41 CEST — Místní oprava fronty po smazání přejmenované přílohy

Hotovo:
- Mílou potvrzený scénář je zopakovaný. Připravené výslovné storno zachovává odmítnutý požadavek i revize a dovolí pokračovat ve stejném pořadí bez přepsání přijaté historie nebo médií. Dosud není nasazené.
- Balíček stejného Camina 0.1.0 (18) a chráněné soukromé stažení jsou místně ověřené; SideStore podpis a skutečný přenos na telefonu zůstávají otevřené.

Rozhodnutí:
- Míla potvrdil několikeré přejmenování/smazání. Oprava je pouze pro smazané fotografie/video, s místním tombstonem, čerstvým důkazem odmítnutí a dodatečným serverovým ověřením. Diagnostické schválení není schválení nového nasazení.

Další krok:
- Po konkrétním aktuálním potvrzení pouze Camino server/staging, potom SideStore aktualizace stejné aplikace a fyzický sync.

Navrhované další kroky:
- Ověřit původní telefonní data, video se zvukem, Komentář a dokončení přenosu. Film až později.

Technický důkaz:
- 68 Swift testů, 52 cílených API/HTTP/workflow testů, arm64 build, CRC/binární roundtrip a izolovaný import PASS. Nepodepsaný IPA 1247937 B, SHA-256 `42c964f9579fe09663632dbafc7a2dfc85e6e8d6424f2c9a7f04fef07ec64f51`. Živý diagnostický server nezměněný; report `METADATA_REJECTION_INCIDENT_20261014.md`.


### 2026-10-14 18:57 CEST — Opravný server a IPA18 v iCloud Dokumentech

Hotovo:
- Serverová část opravy běží a je živě ověřená. IPA18 je nahraný do iCloud Dokumentů; plný hash je shodný, macOS potvrzuje dokončený upload bez chyby. Archiv a ostatní služby zachované.

Rozhodnutí:
- Míla požádal o iCloud dodání a přesnou větou globální brzdy potvrdil připravené nasazení Camino opravy. GitHub ani Cockpit se nepublikovaly.

Další krok:
- Ruční SideStore aktualizace původního Camina bez odinstalování, kontrola starých záznamů a jeden sync.

Navrhované další kroky:
- Potvrdit dokončení metadat i médií, video se zvukem a Komentář. Film až po stabilizaci přenosu.

Technický důkaz:
- Server `d5d19b4b9ddd`, PID 7951, owner HTTP/HTTPS repair feature PASS; Viewer/mapa 200, foto/audio/video Range 206. Čtyři DB snapshoty/hash/quick_check a všechny řádky tabulek shodné; 740 operací, 103 Momentů, všech 234 originálů / 1 870 503 746 B se shodnými SHA-256.
- IPA18 1247937 B, SHA-256 `42c964f9579fe09663632dbafc7a2dfc85e6e8d6424f2c9a7f04fef07ec64f51`, iCloud upload a soukromé HTTPS stažení/hash PASS. Plná brána 1925/1925 a Swift 68/68 PASS. Cockpit PID 35526 / `4f1f0c17ac72659f`, smoke 5/5; Serve shodný, Funnel off. Telefonní instalace a přenos NEPROVEDENO.


### 2026-10-14 20:18 CEST — Míla přijal opravu přenosu a zadal p+n

Hotovo:
- Po IPA18 Míla potvrzuje „funguje ok“. Mac současně přijal dalších 27 operací, jedno storno smazaného názvu a 30 ověřených médií. Akutní přenosový incident je uživatelsky přijatý jako vyřešený.

Rozhodnutí:
- Míla výslovně zadal p+n hotové opravy. Publikuje se git-safe kód a zápis přejímky; server už opravu používá, nový Cockpit proces odpovídá aktuálním zdrojům.

Další krok:
- Film/editor až podle dalšího Mílova pokynu; služby není potřeba znovu přepínat.

Navrhované další kroky:
- Film/editor až podle dalšího Mílova pokynu; P2-E ovládání a P2-A/MAC1 zůstávají samostatné.

Technický důkaz:
- Kurzor/operace 767, 103 Momentů, 264 ověřených originálů / 2 068 743 342 B; plný SHA-256 audit PASS. Starých 740 přijatých paketů a 234 mediálních účtenek přesně zachované; server/epocha/zařízení a tripy shodné, flags false.
- Camino `d5d19b4b9ddd`, PID 7951, owner HTTP/HTTPS + repair feature PASS. Cockpit PID 9218 / `118d4c6208030edb` odpovídá aktuálním zdrojům, smoke 5/5; Serve shodný, Funnel off. Předchozí plná brána 1925/1925 a Swift 68/68 PASS. Podrobné retesty telefonu nelze odvodit jen z obecné odpovědi.


### 2026-10-15 17:11 CEST — Nové odmítnutí audio layoutu, připravená oprava IPA19

Hotovo:
- Dnešní blokace je dohledaná: popis zvuku odkazuje na chybějící deklaraci zdroje. Na syntetických datech zopakované smazání audio session před přenosem, připravená prevence a vymezené storno s původní obálkou a místním tombstonem.
- Již přidělené/přijaté pakety zůstávají zachované. Originály, model telefonu, kamera a nahrávání se nemění. IPA19 stejné identity je připravený, nenasazený.

Rozhodnutí:
- Míla zadal vyšetření obnovené chyby; nová oprava běžící služby zatím nemá konkrétní potvrzení. Skutečné dnešní smazání není odvozené jen ze serverové hlášky.

Další krok:
- Po aktuálním potvrzení Camino server se snapshoty/archivním porovnáním, iCloud IPA19 a SideStore aktualizace původní app bez odinstalování.

Navrhované další kroky:
- Ověřit jeden skutečný sync; pokud chybí místní deletion record, pokračovat v diagnostice původního odkazu. Film až později.

Technický důkaz:
- HTTP 404 `not_found`, `create_audio_layout`, sequence 879; kurzor 878, 123 Momentů a všech 264 originálů / 2 068 743 342 B ověřené. Owner HTTP/HTTPS a Cockpit smoke 5/5 PASS, Serve shodný, Funnel off.
- Swift 74/74, 24 cílených testů a kompatibilní retry šesti paketů na starém serveru PASS; Release arm64 build19, CRC/binární roundtrip PASS. Plná brána viz aktuální stav/report. Telefonní přejímka NEPROVEDENO.


### 2026-10-15 17:20 CEST — Audio oprava nasazená a IPA19 nahraný do iCloudu

Hotovo:
- Serverová oprava běží a je živě ověřená. IPA19 je v iCloud Dokumentech; macOS potvrzuje dokončený upload bez chyby a plný hash odpovídá. Archiv a ostatní služby zachované.

Rozhodnutí:
- Míla přesnou větou globální brzdy potvrdil pouze připravený Camino server a iCloud dodání. GitHub push nebyl součástí potvrzení.

Další krok:
- SideStore aktualizace původního Camina bez odinstalování, kontrola starých záznamů a jeden sync.

Navrhované další kroky:
- Ověřit přenos po 879; bez odpovídajícího místního tombstonu zůstává storno zakázané a pokračuje diagnostika původní vazby. Film později.

Technický důkaz:
- `f60a33c98fd5`, PID 47332; owner HTTP/HTTPS repair features PASS, Viewer/den/mapa 200, foto/audio/video Range 206, anonymní 401. Před/po stejných 878 operací/kurzor, 123 Momentů, identity/tripy a všech 264 originálů / 2 068 743 342 B se shodnými SHA-256; všechny řádky čtyř DB a ověřené snapshoty shodné.
- Cockpit PID 9218 / `118d4c6208030edb`, smoke 5/5, Serve shodný, Funnel off. IPA19 1259687 B, SHA-256 `6d532538e18c333f3cfdae2de64c081a29c5e0c07c7ed822f66e97ebae5bf3cf`, iCloud upload/hash PASS. Plná brána 1936/1936, Swift 74/74 PASS; telefonní přejímka NEPROVEDENO.


### 2026-10-15 19:40 CEST — Přenos uživatelsky přijatý a návrh dalšího kroku střižny

Hotovo:
- Míla potvrzuje funkční přenos po IPA19. Mac přijal storno zvukového layoutu a navazující metadata i 36 nových ověřených médií; akutní incident je uživatelsky uzavřený.
- Film 6. 10. zůstává platný: 25 záběrů, 5 samostatných hlasových nabídek, revize 1 a oba hotové MP4 živě dostupné. Nový střih ani render neproběhly.

Rozhodnutí:
- Míla požádal o audit střižny a návrh dalšího vývojového kroku. Navržený přímý náhled a ruční trim jsou návrh k rozhodnutí, ne souhlas s implementací.

Další krok:
- Rozhodnout o přehrávání vybraného videa přímo ve střižně, tlačítkách začátku/konce z aktuální pozice a přehrání zvoleného úseku pro první vlastní střih 6. 10.

Navrhované další kroky:
- Přijmout jeden skutečný ruční střih na iPhonu: výběr úseku, uložení/reload a shodný náhled/MP4. Videa jsou výchozí celá, staré revize a originály zachované; P2-F až později.

Technický důkaz:
- Kurzor 883, 123 Momentů, 300 ověřených originálů / 2 316 799 213 B, plný SHA audit PASS, flags false, jedno audio storno. Registrovaný Mac film status a editor HTTP vrací validní den 6. 10., revizi 1, 11 foto/14 videí/5 zvuků; žádný samostatný hlas zapnutý.
- Oba výstupy přes HTTP/HTTPS HEAD 200 a Range 206. Frontend nyní nabízí číselné in/out a renderovaný dílčí náhled; přímý zdrojový náhled není implementovaný. Jen projektové zápisy, bez provozních změn.

### 2026-10-15 20:09 CEST — přímý náhled videa a ruční označení střihu

Hotovo:
- Ve střižně je místně připravené otevření celého videa, posun v přehrávači, „Tady začít“, „Tady skončit“ a „Přehrát výběr“. Číselné upřesnění zůstává; změny používají dosavadní automatické ukládání nových revizí.
- Chráněný 720p náhled zdroje se připraví jednou v dosavadní sériové frontě a při dalším otevření se znovu použije. Výběr se přehrává bez renderování filmu. Náhled zdroje neobsahuje titulek ani samostatný hlas; ty patří do renderovaného střihu.
- Originály, uložené revize a výchozí celé video jsou zachované. Živý audit v 19:58 CEST: přesná shoda archivu s podkladem před vývojem, všech 300 originálů / 2 316 799 213 B SHA-256 PASS, 883 operací, flags false a stejný Serve; Camino stále běží na `f60a33c98fd5`. Skutečný film 6. 10. zůstal v revizi 1, bez nového produkčního renderu či změny střihu.

Rozhodnutí:
- Míla „ok, jdeme na to!“ výslovně schválil realizaci navrženého přímého náhledu a ručního trimu v Cockpitu. Rozsah neobsahuje nový telefonní build, změnu přenosové služby, push ani nasazení.

Další krok:
- Po samostatném pokynu nasadit pouze Cockpit a na iPhonu vybrat úsek jednoho videa ze 6. 10., uložit/reload a porovnat s náhledem výsledného filmu.

Navrhované další kroky:
- Dokončit P2-C/E fyzickou přejímku: ruční úsek, pořadí záběrů a délka fotografie; původní revize i celé video musí zůstat dostupné.
- P2-F vícedenní film až po přijetí ovládání prvního dne.

Technický důkaz:
- 23/23 cílených editorových testů PASS, včetně skutečné odvozeniny celého videa a renderu ručního úseku: barvy/snímky, délka, svislý celý obraz, odstranění soukromých metadat, nezměněný SHA originálu. Node test ověřuje tlačítka, čísla, uložení/reload, konec přehrání, chybu média, pozdní odpověď a odvolání soukromí. Plná brána 1940/1940 PASS.
- Registrovaný POST `/api/camino/film/source` připravuje jen odvozeninu; dosavadní chráněný output kontroluje manifest, aktuální soukromí a hash pro GET/HEAD/Range. Originál se nevydává. Ověřeno odmítnutí cizího Origin, soukromého/cizího zdroje, poškozeného náhledu a změny soukromí během renderu i před výdejem.
- Důkazy: `logs/camino_film_trim_final_tests_20261015.log`, `logs/camino_film_trim_gate_final_20261015.log`, `logs/camino_film_trim_live_audit_20261015.log`, `logs/camino_film_trim_smoke_20261015.log`; report `camino/docs/P2CD_EDITOR_MP4_REPORT.md`. Nástrojový prohlížeč není dostupný; fyzická Safari/iPhone přejímka neprovedena.

### 2026-10-15 20:26 CEST — p+n, skutečný náhled a prostředí filmového workeru

Hotovo:
- Schválená dávka čtyř commitů je na GitHubu, `298b6dc2` má úspěšnou vzdálenou bránu. Cockpit byl řízeně přepnutý, nový proces ověřený a smoke 5/5.
- Skutečný pokus o zdrojový náhled zachytil rozdíl oproti terminálu: launchd nemá v PATH místní FFmpeg/FFprobe. Neúspěšný pokus zůstal zachovaný, nic se nevydalo.
- Místní oprava rozšiřuje PATH výhradně novému filmovému workeru o známé instalační adresáře, dosavadní výběr nástroje má přednost. Nemění rodičovský proces, macOS konfiguraci, přenosovou službu ani síť. Pod omezeným PATH už skutečný samostatný worker vytvořil ověřený celý náhled 6 732 ms / 988 097 B; revize 1 a střih zůstaly shodné.

Rozhodnutí:
- Mílovo „ok p+n“ schvaluje push a nasazení pouze Cockpitu včetně nutné opravy nalezené při živém ověření. iPhone IPA ani služba Camino se nepřepínají.

Další krok:
- Dokončit bránu opravy, push a druhé řízené nasazení Cockpitu; potom ověřit nové video přes HTTP/HTTPS a zachování archivu.

Navrhované další kroky:
- Po úspěšném nasazení fyzická přejímka iPhone úsek/save/reload/náhled. P2-F až později.

Technický důkaz:
- 24/24 cílených testů PASS, včetně dohledání mediálních nástrojů při službovém PATH bez změny rodiče. Plná brána 1941/1941 PASS.
- První nasazení `298b6dc2`: PID 70357, stamp `9b76cb02cb956175`, receipt deployed a smoke 5/5. [GitHub brána 38784392159](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38784392159) success. Skutečný omezený worker: úplné dekódování a SHA-256 `70aa61e3ab27a85078bf20adf33ee86e94e0814f58f415f04ef56d339b8b4ab6` PASS; nejde o fyzický poslech.
- Archiv před/po prvním nasazení přesně shodný: 883 operací, 123 Momentů, 300 originálů / 2 316 799 213 B SHA-256 PASS, flags false. Camino stále `f60a33c98fd5`, PID 47332, konfigurace i Serve shodné, Funnel off. Produkční střih revize 1 a oba hotové filmy zůstávají zachované. Důkazy `logs/camino_film_trim_predeploy_20261015.log`, `logs/camino_film_trim_postdeploy_20261015.log`, `logs/camino_film_trim_worker_live_20261015.log` a worker test/gate logy.

### 2026-10-15 20:29 CEST — dokončené p+n střižny a skutečný náhled z Cockpitu

Hotovo:
- Nové ovládání střižny je pushnuté a nasazené pouze do Cockpitu, včetně opravy prostředí filmového workeru. Řízený restart doložil nový proces a povinný smoke 5/5.
- Běžící Cockpit přes nový POST připravil další dosud nenachystané celé video: 8 763 ms / 1 484 481 B, celé dekódované a hash ověřený. Je tak ověřené skutečné spuštění workeru z macOS služby, ne jen terminálový render.
- Oba původní filmy a nový zdrojový náhled: HTTP i soukromé HTTPS HEAD 200 / Range 206, ověřené TLS. Revize 1 a celý střih před/po shodné; žádný nový render celého filmu. Jeden původní neúspěšný zdrojový pokus i dva hotové odvozené náhledy zůstávají zachované.
- Závěrečný audit: 883 operací, 123 Momentů a všech 300 originálů / 2 316 799 213 B se shodnými SHA-256; flags false, stejný server `f60a33c98fd5`, PID 47332, konfigurace i Serve přesně shodné, Funnel off. Owner API HTTP/HTTPS i anonymní odmítnutí PASS. Telefonní IPA a přenosová služba se nepřepínaly.

Rozhodnutí:
- Dokončeno Mílovo „ok p+n“ pro střižnu v Cockpitu. Nutná PATH oprava se omezuje na nový filmový worker, bez systémových změn.

Další krok:
- Na iPhonu obnovit Cockpit, otevřít Film Camino, u videa „Otevřít video pro střih“, posunout/označit začátek a konec, přehrát výběr, vyčkat uložení a ověřit zachování po reloadu. Potom porovnat renderovaný náhled s ručním střihem.

Navrhované další kroky:
- Dokončit P2-C/E fyzickou přejímku také pořadím dvou záběrů a délkou fotografie. P2-F vícedenní film až potom.

Technický důkaz:
- Kód `ff87ee2d`, runtime otisk `ba5bfa185ffd57b9`, receipt deployed, nový proces potvrzený, smoke 5/5. Plná místní brána 1941/1941 PASS (331,381 s testů), cílené testy 24/24 PASS; při nasazení opakovaná statická brána nad shodným kódem.
- Skutečný nový náhled SHA-256 `53170d49201fb43ec7d381124e9a2644c65d26903f5c9f5a125962cc1a27f173`. Důkazy `logs/camino_film_trim_worker_deployed_20261015.log`, `logs/camino_film_trim_final_preview_20261015.log`, `logs/camino_film_trim_final_archive_20261015.log`. Předchozí `298b6dc2` má vzdálenou bránu success; nová [GitHub brána 38785696792](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38785696792) při zápisu ještě běží, její případné nahrazení dalším dokumentačním pushem není výsledek testů.
- HTTP/API/render důkaz nenahrazuje fyzické ovládání a poslech na iPhonu. Nová telefonní přejímka zatím neprovedená; celá videa, uzavřený manifest a starší revize zachované.


### 2026-10-19 21:49 CEST — Šifrovaný doplněk Camina a návod na SSD

Hotovo:
- Živý archiv má samostatnou dokončenou externí kopii `20261019_212828-78238a8a`
  včetně čtyř DB, všech médií, střihů, konfigurace a pevného releasu.
- Celá kopie byla obnovena do nové soukromé složky a ověřena; produkční
  služba je zpět zdravá. Návod v TXT obsahuje konkrétní obnovu a je na SSD,
  spolu s doplňkem novějšího kódu pro projektový snapshot z 18. 10.

Rozhodnutí:
- Výslovný pokyn Míly pokrývá ostrý doplněk a uložení návodu na SSD.
  Nový recovery běh přidává doplněk automaticky a odkazuje na něj manifestem.
  Starší snapshoty se nepřepisují; žádný push/deploy ani nová iPhone instalace.

Další krok:
- Pravidelná recovery záloha aktualizovaným programem; úplná obnova nového
  Macu zůstává samostatnou přejímkou podle TXT.

Navrhované další kroky:
- Samostatný restore test skutečného nového Macu; otevřená telefonní přejímka
  střižny zůstává podle P2CD reportu, bez změny rozsahu.

Technický důkaz:
- 1 587 souborů / 5 078 684 995 B; čtyři DB, 304 originálů /
  2 339 685 533 B, archiv 893 operací / 124 Momentů / 3 cesty.
- Úplné SHA-256, quick_check, mediální účtenky a nezávislá souborová obnova PASS.
  Produkce owner HTTP/HTTPS a anonymní odmítnutí PASS, archiv/config/síť shodné.
- 34 cílených a plná brána 2 133/2 133 PASS; logy `camino_backup_*_20261019*`.
  První pokus bez snapshotu vedl k ověřené opravě čekání na asynchronní stop/start.
- Předchozí neshoda vlastnické účtenky Serve zachovaná; skutečné HTTPS funguje.
  Systémová Klíčenka, další externí data a celková nová instalace nejsou tímto testem pokryté.


### 2026-10-20 10:35 CEST — Moje filmy a výběr dalšího dne

Hotovo:
- Místně implementovaný přehled ověřených filmových projektů a výběr dalšího
  dne z Mac archivu. Samostatná karta drží svůj výběr; střih, revize a exporty
  jsou vždy vázané na konkrétní projekt, také při práci workeru.
- Neuložené změny brání přepnutí, síťový výpadek zachová koncept v kartě
  a pozdní odpověď nemění vybraný den. Přehled nevydává soukromé/skryté
  ani nově neplatné projekty.
- Současný film má revizi 5; osm původních JSON souborů a všech šest hotových
  výstupů před/po shodných SHA-256. Nevznikl žádný produkční projekt ani render.

Rozhodnutí:
- Míla schválil navržený další krok. Více jednodenních projektů nyní,
  P2-F společný vícedenní film/kapitoly později. Adam realizuje tento zásah
  do persistence a výběru; bez autorizace nového push/deploye.
- Míla hodnotí první film/střih dobře a místní přehrávání plynule;
  nejde o doložení všech jednotlivých fyzických testů editoru.

Další krok:
- Po samostatném p+n nasadit pouze Cockpit přes registrovanou Lunu
  a fyzicky ověřit přepnutí dvou dnů se zachováním původního střihu.

Navrhované další kroky:
- V druhém dni uložit úpravu, ověřit reload a vrátit se k prvnímu filmu.
- P2-F spojení dnů/kapitoly až po přijetí přehledu; celý nový Mac odděleně.

Technický důkaz:
- 60/60 cílených testů a plná brána 2 137/2 137 PASS.
- Testy: dva syntetické dny, cizí zdroje a výstupy odmítnuté, vlastní revize,
  worker druhého dne, read-only katalog, aktuální soukromí a HTTP parametry.
  Node testy ověřují dvě nezávislé karty, neuložený/offline koncept a pozdní odpovědi.
- Logy `camino_film_library_targeted_final_20261020.log`,
  `camino_film_library_preservation_final_20261020.log`,
  `camino_film_library_gate_final_20261020.log`; report `P2CD_EDITOR_MP4_REPORT.md`.
- Nová UI přejímka Mac/iPhone neprovedená, nástrojový prohlížeč nedostupný.
  Záloha z 19. 10. zachovaná, služba Camino a síť se nepřepínaly.


### 2026-10-20 17:20 CEST — Trvalé mazání vybrané filmové varianty

Hotovo:
- Místně implementované „Smazat natrvalo“ pro celý export, dílčí náhled a
  neúspěšný pokus. Nabízí konkrétní revizi/úsek a velikost všech pracovních
  souborů; seznam dílčích náhledů nově ukazuje i časy úseků.
- Fyzické odstranění všech pracovních pokusů vybrané varianty bez koše či
  nové kopie. Malá technická metadata brání obnovení starým request ID.
  Po přerušení lze dokončit zbývající již potvrzené soubory.
- Dosavadní „Moje filmy“ bylo nasazené přes Lunu na `96ce7bab`;
  Míla ověřil druhý den a vytvoření MP4. Nové mazání ještě nasazené není.

Rozhodnutí:
- Nový výslovný požadavek nahrazuje starší zachovávání všech exportů.
  Platí jen pro vědomě vybranou filmovou variantu a její pracovní soubory;
  originály, uložený střih, ostatní varianty a zdrojové náhledy se zachovají.
- Přesná věta globální brzdy před konkrétním smazáním podle místního pravidla.
  Žádné automatické čistění záloh ani produkční mazání během vývoje.

Další krok:
- Po samostatném p+n jen Cockpit přes Lunu, potom fyzicky potvrdit a smazat
  jeden nepotřebný dílčí náhled; po reloadu ověřit zmizení a nedostupný odkaz.

Navrhované další kroky:
- Ověřit zachování přehratelného finále a úprav obou dnů.
- Další úpravy druhého dne podle Míly, P2-F zůstává samostatnou etapou.

Technický důkaz:
- 71/71 cílených testů a plná brána 2 146/2 146 PASS.
- Syntetické zkoušky zahrnují více pokusů/segmentů, dvě stejné dílčí varianty,
  dvě současná mazání, výpadek uprostřed operace, bezpečné dokončení,
  odmítnutí cizího projektu/odkazu/hardlinku a aktivního workeru.
- HTTP potvrzení a Origin, zrušení/nesprávná věta v UI a GET/HEAD/Range 404;
  staré render ID se neobnoví, nový výslovný render zůstává možný.
- Logy `camino_export_delete_targeted_final_20261020.log`,
  `camino_export_delete_gate_verified_20261020.log`, `camino_export_delete_preservation_20261020.log`.
- Staré externí zálohy a stažené kopie tato akce neodstraňuje; otevřený
  soubor může držet bloky do ukončení přehrávání/stahování. Nejde o SSD secure erase.
- První plná sada: 2 145 testů, jedna kolize worker lease v existujícím testu předání Luny; samostatný modul 13/13 PASS. Produkční Luna se neměnila. První log zachovaný jako `camino_export_delete_gate_20261020.log`.


### 2026-10-20 17:51 CEST — Oprava mazání skutečných filmových výstupů

Hotovo:
- Dohledaná příčina Mílova neúspěšného mazání po nasazení: ochrana odmítla
  dva interní názvy téhož MP4 vytvořené samotným rendererem. Produkční mazání
  nezačalo; restart nemohl varianty odstranit.
- Místní oprava uznává pouze plně vnitřní pevné odkazy a zahrnuje pracovní
  podadresáře. Před každým odstraněním znovu kontroluje identitu a zbývající
  počet odkazů; přerušení mezi názvy lze bezpečně dokončit.
- 42 cílených testů PASS, včetně skutečného render → smazání. Všech 10 živých
  variant projde pouze čtecím inventářem; 570 původních souborů shodných.

Rozhodnutí:
- Bez změny rozsahu: konkrétní varianta, potvrzený plán a globální brzda.
  Žádné produkční mazání během opravy, nové kopie ani automatický p+n.

Další krok:
- Po samostatném p+n pouze Cockpitu zopakovat skutečné smazání nepotřebného
  náhledu a ověřit zmizení po reloadu při zachování ostatních variant.

Navrhované další kroky:
- Další připomínky střihu druhého dne, společný vícedenní film P2-F až později.

Technický důkaz:
- Plná brána opravy 2 151/2 151 PASS (323,406 s testů), `camino_export_delete_fix_gate_20261020.log`.
- Logy `camino_export_delete_fix_reproduction_20261020.log`,
  `camino_export_delete_fix_targeted_20261020.log`,
  `camino_export_delete_fix_production_readonly_20261020.log`.
- Původní vydání `3b129ded` potvrzené účtenkou `cb5a8c476ff62f035fbf48241bccafe4`,
  2 146 plných testů a smoke 5/5. Oprava je samostatný místní krok.


### 2026-10-20 21:23 CEST — Odstranění osiřelých záznamů čtyř videí z 8. října

Hotovo:
- Osmý den znovu projde ověřením pro založení filmu: 24 fotografií,
  14 videí a 6 zvuků. Odstraněny právě čtyři záznamy videí, která Míla po
  přenosu metadat, ale před přenosem souborů smazal na telefonu.
- Ostatních 304 originálů, 894 přijatých operací, 124 Momentů, synchronizační
  identita/kurzor, ostatní tabulky a všechny existující filmové soubory zachované.
- Původní Camino služba obnovená a zdravá přes HTTPS; konfigurace a síť shodné.
- Míla již potvrdil funkční mazání variant po nasazení `84336632` a má MP4 dnů 6 a 7.

Rozhodnutí:
- Míla přesnou větou globální brzdy potvrdil tento konkrétní úklid čtyř osiřelých
  položek. Pouze živý Asset inventář, historické synchronizační obálky zachované.
- Žádné další mazání telefonu, originálů, filmů ani obecná změna serverového kontraktu.

Další krok:
- V Cockpitu znovu uložit projekt 8. října a pokračovat střihem/MP4.

Navrhované další kroky:
- Při dalším běžném kontaktu ověřit synchronizaci telefonu; P2-F později.

Technický důkaz:
- Kopie v paměti před potvrzením PASS; ostrý offline SQL zásah až po snapshotu,
  přesném porovnání plánu a uzamčení filmových zápisů. 4 řádky odstraněné,
  304 zůstaly, 10 ostatních metadata tabulek a celá media DB shodné.
- FK/quick_check PASS; všech 304 originálů / 2 339 685 533 B SHA-256 PASS,
  797 filmových souborů beze změny; původní projekty 6 a 7 platné, den 8 validní.
- HTTPS owner health 200, Cockpit katalog OK. Další fyzický kontakt telefonu
  neověřený. Log `logs/camino_metadata_cleanup_20261020.log`, detail a snapshot private.

## 2026-10-20 22:13 CEST — Příprava fotografického ovládání pro Lunu

Hotovo: Míla potvrdil funkční opravu osiřelých metadat. Nově požaduje u fotografií Otevřít fotografii a odstranit jejich renderovaný náhled záběru. Vývoj i p+n výslovně Lunou; nejprve zprovoznit širší delegaci. Centrální vývojová role již gpt-6-luna/high, přejímací kontrakt připravený, samotná funkce zatím chybí.
Rozhodnutí: fotografie otevřít v nové kartě bez renderu či diskové kopie, video ovládání zachovat.
Další krok: předat vymezený kód a nezměnitelné syntetické testy skutečné Luně.
Navrhované další kroky: kontrola návrhu a schválené p+n pouze Cockpitu.
Technický důkaz: 4 přejímací testy záměrně FAIL pro chybějící metodu, bez chyb prostředí; originály a projekty nebyly změněné. Riziko: soukromí musí být ověřeno i po dekódování, žádná raw metadata v obrazu.

## 2026-10-20 22:23 CEST — Fotografie ve střižně vyvinuté Lunou

Hotovo: Fotografie mají lokálně Otevřít fotografii v nové kartě a nemají renderovaný náhled záběru. Read-only PNG bez EXIF/GPS a bez diskové kopie; správné natočení/ICC, aktuální projekt/soukromí/hash a kontrola po dekódování. Video ovládání zachované. Funkční kód skutečně vytvořila Luna, Adam zkontroloval a převzal; opravil pouze citaci old, testové literály, úklid testserveru a složený frontendový otisk.
Rozhodnutí: výslovný vývoj Lunou i pro více souborů a JavaScript; žádná nová kopie médií, video zachovat.
Další krok: Ověřit finální účtenku schváleného p+n 92b4b7704c6503fb8b2ed300b600c7f9 a živý audit. Při completed navázat fyzickou přejímkou fotografie v Cockpitu na Macu/iPhonu; p+n slepě neopakovat. Tento Git checkpoint zachycuje stav před vydáním; výsledek publikace/nasazení je v přesné účtence a logs/luna_photo_release_20261020.log.
Navrhované další kroky: pokračovat v již rozpracovaném střihu dne 8; vícedenní film zůstává pozdější samostatný krok.
Technický důkaz: Skutečný model gpt-6-luna/high; původní job d67ea8e3a4c26b3c088fd33a821194e8, přijatá kontrola 393b9e1a2d6920d7ed27d41c74473cea, 4 původní FAIL → 4 PASS. Další modelový pokus neproběhl, původní odhad 0,161725 Standard, kontrola 0. Node PASS; integrační běh 69 testů, po opravě jediného fixture rozměru původních 68 PASS + konkrétní 1 PASS. Statická brána PASS. Důkazy logs/luna_photo_accepted_20261020.log, luna_photo_integration_tests_20261020.log, luna_photo_frontend_contract_final_20261020.log. Riziko: fyzická přejímka uživatelem zatím neprovedená; pozdější změna soukromí nebo vstupů obraz správně zablokuje.

## 2026-10-23 08:11 CEST — První krok zoomu fotoaparátu

Hotovo:
- Zoom fotografie i videa je místně implementovaný: gesto dvěma prsty, skutečná aktuální hodnota a podporované volby 0,5×/1×/2×. Zadní kamera přednostně používá dostupný virtuální víceobjektivový přístroj, náhled začíná na 1×. Limity a měřítko se berou ze zařízení; 2× není slib optického teleobjektivu. Swift 79/79 PASS, arm64 Debug a Release 0.1.0 (20) PASS, nepodepsaná IPA ověřená. Instalace, fyzická přejímka, push a nasazení neprovedené. Další krok: aktualizace stejné aplikace přes SideStore a fyzické foto/video zkoušky podle CAMERA_ZOOM_REPORT.md; případné p+n pouze registrovanou Lunou.

Rozhodnutí:
- Míla schválil první krok: zoom gestem a rychlými volbami. Ostření dotykem,
  expozice a blesk zůstávají mimo tento krok. Další p+n provádí Luna.

Další krok:
- Aktualizovat stejné Camino přes SideStore a fyzicky ověřit foto/video zoom,
  zvuk, přední kameru a návrat z pozadí; aplikaci s daty neodinstalovávat.

Navrhované další kroky:
- Podle fyzické přejímky případná úzká oprava; případné p+n až samostatně
  schválenou registrovanou cestou. Samotné serverové p+n neaktualizuje iPhone.

Technický důkaz:
- Pět nových testů měřítka a limitů; celá Swift sada 79/79 PASS. Arm64 iOS
  Debug i Release build PASS. Release IPA 0.1.0 (20), stejné bundle ID,
  ZIP/CRC a shoda kopie ve Stahování PASS. Telefonní hardware NEOVĚŘENO.
- Report `camino/docs/CAMERA_ZOOM_REPORT.md`; logy a build receipt v
  `data/private/camino_zoom_20261023/`. Žádná změna datového schématu ani synchronizačního kontraktu.
- Osiřelý prázdný index.lock bez držitele byl přesunut do technického archivu
  v projektu, původní Git index zachován. Nesouvisející změna Xcode projektu
  zůstává mimo tento checkpoint; profilový sync vyžaduje čistý zdrojový main.

## 2026-10-23 09:16 CEST — Texty a komentáře ve střižně

Hotovo:
- Lokální panel nabízí povolené přijaté texty deníku, jejich úpravu pro film,
  vložení do titulku nebo samostatné časované karty. Hlas má poslech celého
  zdroje / ruční výběr úseku a výslovné vložení od vybraného záběru.
- Předchozí dva commity jsou přes Lunu pushnuté a nasazené do Cockpitu
  (účtenka 698ae54bb9df52516cd35c2821f88f4c, plná brána 2174, smoke 5/5).
  Míla následně potvrzuje funkčnost zoomu; podrobný telefonní protokol tím nevznikl.

Rozhodnutí:
- Míla schválil vývoj navrženého panelu. Žádný souhlas s novým p+n, přepisem
  audia, generovanou řečí nebo změnou existujícího produkčního střihu.
- Film pinuje přijatou textovou revizi; originály, deník i starší střihy
  zůstávají neměnné, Jen pro mě a skryté zdroje mimo film.

Další krok:
- Funkčně ověřit uložení, soukromí, kartu a poslechovou kopii před publikováním.

Navrhované další kroky:
- Po samostatném p+n Lunou krátký vlastní náhled s titulkem, kartou a hlasem.
- Chybějící konkrétní text sledovat od uložení v telefonu po přijetí na Macu;
  bez čerstvé telefonní evidence nepřisuzovat chybu přenosu.

Technický důkaz:
- Statická brána --skip-unit-tests, py_compile, Node --check a diff --check PASS.
- Read-only revize 5 dne 6. 10.: 25 záběrů, 5 hlasových nabídek, 0 zapnutých
  hlasů a 0 přijatých textů. Archiv má 8 append_text / textových revizí;
  povolené texty v 5 dnech. Jedna textová nabídka i přesná reference ověřené
  čtením jiného existujícího dne bez uložení. Žádný produkční render nebo
  přepis projektu; původní Xcode nastavení SHA-256 shodné.
- Automatické testy a funkční render/Safari NEOVĚŘENO; nelze tvrdit provozní
  opravu. Hlas je umístěný absolutním časem, po změně obrazu zkontrolovat.
- Podrobnosti camino/docs/FILM_TEXT_AUDIO_REPORT.md; čtecí účtenky pouze private.

## 2026-10-23 09:53 CEST — Oprava kontrolního otisku před p+n

Hotovo:
- Očekávaná délka, počet řádků a SHA-256 složené stránky Cockpitu odpovídají
  zkontrolovanému novému panelu. Cílený kontrakt znovu PASS; žádná jeho
  kontrola nebyla vypnutá. Funkční kód panelu se touto opravou nemění.

Rozhodnutí:
- Míla výslovně zadal p+n Lunou. První úloha se neopakuje: plná brána
  selhala před pushem, živý GitHub prokazatelně zůstal na 07109721 a
  nasazení nezačalo. Po nutné opravě vznikne nový commit a přesné předání.

Další krok:
- Předat Luně opravený celý čekající balíček a vyčkat konečné účtenky.

Navrhované další kroky:
- Po potvrzeném nasazení fyzicky vyzkoušet text, kartu a poslech komentáře.

Technický důkaz:
- Účtenka a3d0c4730ea1ef7a0e9f3b5f7a2336b7: attention, bez potvrzeného
  push/deploy. Zachovaný plný log: 2174 testů, jediný FAIL v původním
  délkovém/otiskovém fixture; ostatní kontroly bez dalšího selhání.
- Přímý ls-remote ověřil původní GitHub head. Opravený kontrakt 1/1 PASS,
  kontroluje 564694 znaků, 11023 řádků a nový SHA-256. Soukromý důkaz
  failure_resolution.json a původní first_failed_gate.log se zachovávají.
- Plná nová brána a nasazení teprve přes další přesnou účtenku Luny;
  Safari a nové větve renderu tím zatím nejsou přijaté.

## 2026-10-23 10:49 CEST — Aktuální dokumentace Camina a filmové střižny

Hotovo:
- Hlavní rozcestník, iPhone návod, střižna a technické reporty popisují zoom,
  přijaté texty, titulky, karty, poslech, umístění hlasu a soukromé MP4.
- Opravené zastaralé stavy čekajícího p+n; funkční panel je prokazatelně
  pushnutý a nasazený. Historické etapy jsou označené jako historie.

Rozhodnutí:
- Míla výslovně zadal aktualizaci dokumentace, commit a jeho p+n Lunou.
  Dokumentace nemění aplikaci, data, existující střihy ani rozsah funkcí.

Další krok:
- Předat dokumentační commit registrované Luně a ověřit konečnou účtenku.

Navrhované další kroky:
- Fyzicky projít panel Texty a komentáře, uložení/reload a krátký náhled
  s titulkem, kartou a vlastním hlasem; podrobný zoom protokol jen podle potřeby.

Technický důkaz:
- Funkční vydání d8d16f1b: účtenka 4b1ed8c23af048f133e00971d0ad1038,
  completed, push/deploy confirmed, plná brána PASS (2174 testů), smoke 5/5,
  chráněné služby zachované. Při aktualizaci dokumentace HTTP znovu vrací
  nový panel a runtime otisk shodný s účtenkou.
- Obecné Mílovo potvrzení zoomu neprokazuje všechny telefonní scénáře.
  Samostatné nové větve renderu karty/poslechu ani Safari nejsou přijaté.
- Stav publikace tohoto dokumentačního checkpointu určí až jeho vlastní
  účtenka; výsledek předchozího funkčního vydání jej nezastupuje.
- Dokumentační kontrola: 11 Markdown souborů, 52 místních odkazů bez chyb;
  rychlá statická brána a diff --check PASS. Žádná funkční změna kódu.

## 2026-10-23 12:22 CEST — Místní podpis Xcode bez blokování pracovních proudů

Hotovo:
- Verzovaný projekt už nemá dvě duplicitní hodnoty DEVELOPMENT_TEAM.
  Debug i Release načítají stejný místní tým z ignorovaného LocalSigning.xcconfig.
- Původní uspořádání Xcode skupiny se dvěma existujícími referencemi zachované;
  celý původní soubor uložený pro obnovu jen v private. Žádný podpisový údaj
  se nepřidává do Gitu, nevzniká nový build/IPA ani změna telefonních dat.

Rozhodnutí:
- Míla schválil vyřešení lokálního Xcode WIP a úpravu panelu p+n, následné
  předání výsledných commitů registrované Luně. Bezpečnostní kontrola čistého
  main pro přepínání proudů zůstává zachovaná.

Další krok:
- Po commitu zarovnat čisté profily a ověřit Camino → MMTX → Camino;
  potom dokončit pravdivé stavy panelu p+n.

Navrhované další kroky:
- P+n celého opraveného balíčku Lunou a opakování přepnutí po nasazení.

Technický důkaz:
- Strukturální porovnání potvrdilo výhradně odstranění dvou duplicitních
  nastavení; skupiny a reference zachované. xcodebuild -showBuildSettings
  pro Debug i Release: místní tým účinný, bundle ID shodné. Původní lokální
  xcconfig má shodný SHA-256. Účtenky pouze data/private/human_adam_switch_release_20261023/.

## 2026-10-23 12:34 CEST — Živé ověření přepnutí po sjednocení Xcode

Hotovo: Po commitu a50a9007 a čistém zarovnání profilů skutečné přepnutí
Camino → MMTX → Camino prošlo. Debug i Release zachovávají účinný místní
podpisový tým; žádný podpisový údaj se nově necommitoval.
Rozhodnutí: Schválené oba body a společné p+n Lunou; ochrana čistého main
zůstává zachovaná. UI část je v kanonickém proudu project-cockpit.
Další krok: P+n obou commitů přes Lunu, následná kontrola a návrat do Camina.
Navrhované další kroky: Uživatel po obnově Human–Adam přepne na MMTX.
Technický důkaz: Dva skutečné registrované profile POST úspěšné, bez zprávy
či modelového tahu; redigovaný switch_before_ui.json pouze v private.


## 2026-10-23 20:35 CEST — Více projektů: společný základ a oddělení dat (kroky 1–2)

Hotovo:
- Jeden projekt je dosavadní Trip UUID. Volitelné termíny a archivace jsou
  samostatné revize, bez změny původních záznamů, front nebo DB schématu.
- Soukromý owner katalog zpřístupní přijatá metadata projektů. Rozpracovaný
  přenos A zůstane A po přepnutí na B i restartu; shodné názvy a dny se nemíchají.
- Příprava záznamu chrání původní projekt. Archivace blokuje nové zachycení,
  zachová čtení a dokončení již připravených záznamů/přenosů.

Rozhodnutí:
- Míla schválil celkový šestikrokový směr a nyní vývoj kroků 1–2 Adamem.
  Ovládání telefonu, výběr Vieweru/střižny a vydání jsou další kroky.
- Výběr projektu v telefonu je oddělený od archivace a povolení Vieweru.
  Žádná nová identita aplikace, veřejné sdílení ani automatická migrace.

Další krok:
- Po uzavření tohoto vývojového checkpointu krok 3: jednoduché ovládání
  projektů v telefonu, včetně termínů a archivace/znovuotevření.

Navrhované další kroky:
- Jasně vymezené obrazovky a návody navržené pro Lunu, integrace Adamem.
- Krok 4 projektový Viewer/Mac, krok 5 střižna, krok 6 fyzická přejímka.
- Později spojování denních filmů do celé dovolené.

Technický důkaz:
- 81 Swift testů a 57 cílených Python testů PASS. Skutečné Swift obálky,
  izolované API, oba soubory a vazby, restart/replay, konflikty i oddělené
  Viewer granty ověřené. Plná brána 2180 PASS a iOS build PASS.
- docs/MULTI_PROJECT_FOUNDATION.md; důkazy jen data/private/camino_projects_20261023/.
- Živá služba, archiv, střihy ani iPhone se nemění. Fyzická přejímka nové
  verze NEOVĚŘENO. Neprovádět p+n ani instalaci bez odpovídajícího pokynu;
  samostatná služba Camino musí před novou operací umět project_details_v1.


## 2026-10-23 21:03 CEST — Oprava větších fotografií ve střižně

Hotovo:
- Fotografie nad 4096 pixelů lze připravit pro náhled a film při omezeném
  vstupu. Celý záběr, poměr stran a původní archiv zůstávají zachované.
- Společný převod hlavního obrazu, orientace, ICC/sRGB a Lanczos pracovní
  kopie; náhled do 4096, film dál 720p/1080p. Video a HDR ochrany zachované.
- Konkrétní zdroj dne 14. 10. prošel PNG a odděleným 1s QA v obou profilech;
  původní fotografie, uložené střihy a dosavadní exporty zůstaly shodné.

Rozhodnutí:
- Míla schválil opravu po vysvětlení přepočtu do rozlišení filmu. Žádná změna
  rozlišení finálního profilu ani automatická úprava originálu.

Další krok:
- Samostatně schválené p+n registrovanou Lunou; potom finální export uložené
  revize dne 14. 10. a jeho uživatelská přejímka.

Navrhované další kroky:
- Po vyřešení incidentu pokračovat krokem 3 více projektů (ovládání telefonu),
  potom Viewer/Mac, střižna a fyzická přejímka celého toku.

Technický důkaz:
- 54 cílených filmových testů a 18 testů brány PASS, statická brána PASS.
  Syntetický 5918 × 3860 obraz: oba výstupy, okraje/pruhy, 30 snímků, celé
  dekódování; skutečný zdroj 720p/1080p QA PASS. Plný film čeká po vydání.
- docs/LARGE_PHOTO_REPORT.md, soukromé důkazy data/private/camino_large_photo_20261023/.
- Kód není nasazený; plná publikační brána až v samostatném p+n. Živá služba
  Camino a telefon se nemění. Nový commit naváže na lokální kroky 1–2 více projektů.


## 2026-10-23 21:49 CEST — Krok 3, příprava formulářů projektů

Hotovo:
- Založení a úprava názvu, termínů, zkušebního příznaku a archivace v jedné
  místní transakci. Neplatná data zachovají původní projekt i místní výběr.
- Model nabízí rozlišené oprávnění spravovat projekty a nově zaznamenávat.
  Archivace brání novému pořizování, nikoli čtení či doběhnutí přenosů.
- Předchozí oprava velkých fotografií i základ více projektů jsou podle
  účtenky Luny publikované a nasazené v Cockpitu; skutečný PNG HTTP 200.

Rozhodnutí:
- Míla zadal pokračování vývoje Camina. Výchozí návaznost je krok 3
  schváleného plánu; otázka na přednost serveru/Macu je položená asynchronně.
- Kritickou datovou část řeší Adam, jasně vymezené obrazovky navážou Lunou
  podle již schváleného rozdělení; integrace a přejímka zůstávají Adamovi.

Další krok:
- Dokončit ověření datové přípravy a předat ohraničené obrazovky projektů Luně.

Navrhované další kroky:
- Krok 4 výběr projektu a oprávnění ve Vieweru/Macu, krok 5 střižna.
- Krok 6 fyzický průchod dvěma projekty, později spojení denních filmů.

Technický důkaz:
- 82 Swift testů PASS; nově neplatné vytvoření/úprava, opětovné otevření DB,
  nezměněná identita a původní create_trip. Plná brána 2185 PASS a iOS build PASS.
- Důkazy data/private/camino_projects_ui_20261023/. Dřívější živé p+n:
  job 5b60714d658675cfedd05f1df1bafad7, commit 8bc31d07, 2185 PASS, smoke 5/5.
- Nová příprava není vydaná ani nainstalovaná. Telefonní a serverová
  aktualizace jsou samostatné operace; originály a živé projekty se nemění.


## 2026-10-23 21:59 CEST — Krok 3, návrh obrazovek čeká na nové předání

Hotovo:
- Datová příprava je lokálně dokončená v 176a6c66, Swift 82 PASS, plná brána
  2185 PASS a generic iOS build PASS. Uložení projektu je atomické.
- Luna vytvořila návrh obrazovek; předané zdrojové úseky ale omylem končily
  o jednu závorku dřív. Registrované převzetí návrh správně zastavilo.
  UI zdroje se nezměnily, opravený rozsah a nová přejímka jsou připravené.

Rozhodnutí:
- Nový placený pokus se automaticky neopakuje. Mílovi je položená žádost
  o jeden nový pokus se správným rozsahem. Oprava old bez změny new by
  ponechala přebytečnou závorku, proto se tato cesta nepoužila.

Další krok:
- Po výslovném potvrzení použít připravený luna_request_scopefix.json přes
  app.luna_development.run, pak kontrolu, accept a iOS/simulátor přejímku.

Navrhované další kroky:
- Dokončit krok 3; potom projektový Viewer/Mac (4), střižna (5), přejímka (6).

Technický důkaz:
- Návrh 971d17d401d57207ca3ef7d762836191, baseline 15 PASS, bez kandidáta
  a bez after. Jen 1 původní modelový tah, odhad 0,1073875 Standard;
  nejde o fakturační údaj. Privátní pracovní kopie návrhu prošla jen parse.
- Zdrojový problém je přesně první rozsah 46–74 místo 46–75; ostatních
  pět citací leží v povolených úsecích. Žádné ruční obejití accept brány.
- Důkazy data/private/camino_projects_ui_20261023/. Současná aplikace,
  originály, archiv i služby beze změny; nové commity nejsou publikované.


## 2026-10-23 22:28 CEST — Krok 3, ovládání více projektů

Hotovo:
- Telefonní obrazovky nabízejí vlastní projekty, volitelné termíny, přepínání
  a archivaci/znovuotevření. Archiv je čitelný, nové pořizování vypnuté.
- Úprava načte skutečné hodnoty a uloží celý formulář atomicky. Zkouška
  a původní záznamy zůstávají zachované; nové názvy nepřepisují identity.

Rozhodnutí:
- Míla výslovně schválil jeden nový vývojový pokus Lunou a p+n hotových
  commitů. Registrovaný návrh byl zkontrolován a převzat; Adam doplnil
  validační stav zakládání a identifikátor Zkoušky pro UI přejímku.
- P+n nasazuje společný Cockpit. Aktualizace služby Camino a instalace
  iPhonu vyžadují vlastní postup; nová fronta vyžaduje project_details_v1.

Další krok:
- Ověřit výsledek schváleného p+n v účtence c3aba0302d0661fbff03b131e65357a4;
  po dokončení navázat krokem 4 (projektový Viewer/Mac).

Navrhované další kroky:
- Krok 4 projektový Viewer/Mac, krok 5 výběr projektu ve střižně.
- Samostatná aktualizace služby a telefonu, poté fyzická přejímka dvou projektů.

Technický důkaz:
- Luna c39307ba80c8e9e373149a9a7696c220: baseline/after 15 PASS, accept applied.
  První nepřevzatý návrh zůstává historií; opravený pokus schválil Míla.
- Datová příprava 176a6c66: Swift 82 PASS, full 2185 PASS; UI Release
  a rychlá statická brána PASS. tři vybrané UI scénáře PASS (offline 1/1, projekty a přejmenování 2/2).
- Report camino/docs/PROJECT_MANAGEMENT_UI_REPORT.md; soukromé důkazy
  data/private/camino_projects_ui_20261023/. Skutečný telefon, mikrofon,
  kamera ani přenos nové verze nejsou tímto krokem přijaté.
- Git checkpoint zachycuje stav před publikací; konečný výsledek určuje
  přesná účtenka c3aba0302d0661fbff03b131e65357a4, nikoli předchozí p+n.


## 2026-10-23 22:39 CEST — Publikační překážka a oprava startovacího souběhu

Hotovo:
- Ovládání více projektů v 15e0467a má tři vybrané UI scénáře a Release PASS.
  Záznamy obou projektů zůstávají oddělené i po restartu a archivaci.
- Odhalená startovací kolize p+n má úzkou místní opravu: status během již
  existující 30s startovací lhůty nezkouší zámek workeru. Kontrola mrtvého
  workeru po lhůtě i zákaz souběžných workerů zůstávají zachované.

Rozhodnutí:
- P+n bylo výslovně předané Luně jednou a zastavilo se před publikací.
  Původní účtenka je zachovaná; žádný nový placený pokus ani ruční push/deploy.
- Prokázanou překážku opravil Adam v nezbytném rozsahu. Nové vydání až po
  samostatném potvrzení konkrétního opraveného balíčku.

Další krok:
- Předložit ověřený opravený balíček pro nový konkrétní pokyn p+n.

Navrhované další kroky:
- Po úspěšném vydání navázat krokem 4 projektového Vieweru/Macu.
- Službu Camino a stejnou aplikaci iPhonu aktualizovat samostatným postupem.

Technický důkaz:
- Původní účtenka c3aba0302d0661fbff03b131e65357a4: attention, push uncertain, deployment
  not_started. Přímé git ls-remote potvrzuje GitHub na 8bc31d07; nic nepushnuto.
- Brána: 2185 testů, 1 selhání test_native_one_call_runs_one_luna_and_returns_to_caller
  s BlockingIOError. Čtecí probe před startovací lhůtou krátce vlastnil stejný
  worker lock; skutečný worker jej proto nemohl získat.
- Oprava má deterministický regresní test zákazu probe v čerstvé úloze.
  57 cílených testů PASS, plná brána 2186 PASS (333,492 s unit část), opakovaný souběh 10/10 PASS. Důkazy pouze
  data/private/camino_projects_ui_20261023/release/failed_full_gate.log a
  release_lock_tests.log / release_fix_full_gate.log v nadřazené složce.
- Živý Cockpit zůstává na předchozím vydání. Telefon, samostatná služba,
  archiv i střihy se novým kódem neaktualizovaly.


## 2026-10-24 09:49 CEST — Více projektů, Viewer a střižna (kroky 4–5)

Hotovo:
- Nabídka telefonu ukazuje období, rozliší shodná jména a připomíná vypnutý
  Viewer nového projektu. Viewer nabízí pouze povolené cesty; každá má
  vlastní deník, mapu a odkazy médií, staré odkazy zůstávají použitelné.
- Jednotlivý grant lze výslovně povolit/odvolat bez změny čtecího přihlášení
  a ostatních cest. Obnova, konflikt, odvolání i staré URL zůstávají uzavřené.
- Střižna vybírá cestu před dnem a filmem. Stejná data/názvy se nemíchají,
  karty mají vlastní volbu a neuložený střih brání přepnutí. Render worker
  i výdej fotografie/exportu se řídí konkrétním uzavřeným manifestem.
- Předchozí opravený balíček do e11d949a má potvrzený push a nasazení
  Cockpitu v účtence e47cdb394ec5441c5d25632f11c8c995 (2186, smoke 5/5).
  Dřívější neúspěšná účtenka c3aba030 zůstává zachovanou historií.

Rozhodnutí:
- Míla zadal pokračování aplikace/Vieweru/střižny a posouzení Pythonu 3.15.
  Propojené bezpečnostní změny a integraci provedl Adam. Nové vydání služby,
  instalace telefonu a systémový upgrade mají samostatný postup/oprávnění.
- Python 3.15.1 je vhodný kandidát pro paralelní test. Místní 3.12.0rc3
  zasluhuje pozdější výměnu; resolver není skutečná provozní přejímka.

Další krok:
- Převzít místní checkpoint a samostatně určit vydání a fyzickou přejímku.

Navrhované další kroky:
- Schválené p+n Cockpitu; odděleně služba project_details_v1 a stejná aplikace
  iPhonu bez odinstalace, se zálohou/otisky a následnou kontrolou zachování.
- Krok 6: dvě cesty, přenos, Viewer a film na skutečném zařízení/Safari.
- Paralelní pilot Pythonu 3.15.1 s oddělenými závislostmi a plnou bránou;
  společný vícedenní film až jako další samostatná etapa.

Technický důkaz:
- 34 cílených integračních testů PASS, Node přepínání/karty/late response
  a reload PASS. Skutečné dva syntetické JPEG → PNG 1024×768 bez EXIF,
  jiné pixely a cizí asset HTTP 404. Archivy i původní filmové soubory shodné.
- iOS Release generic build PASS; plná brána 2193 PASS (453,570 s unit část), závěrečné 3 testy dispatcheru PASS. Browser v tomto
  prostředí není registrovaný; fyzické Safari/iPhone/přenos nové verze NEOVĚŘENO.
- Report camino/docs/MULTI_PROJECT_ACCESS_REPORT.md, soukromé důkazy jen
  data/private/camino_projects_20261024/. Žádná změna živých oprávnění,
  produkčního archivu, střihů, sítě, služby ani instalace aplikace.
- Python: reports/python_315_assessment_2026_10_24.md. Oficiální 3.15.1
  ověřené, 18 položek metadat a binární dry-run závislostí; bez instalace.


### 2026-10-24 11:02 CEST — Text a komentář přímo u fotografie

Hotovo:
- Celý text se předává a ukládá u fotografie, kde se volí statické zobrazení,
  plynulé okno nebo uložené české čtení. Původní nahrávky i nové čtení lze
  navázat na fotografii; přesun obrazu neponechá hlas na starém místě.
- Chyby jsou u ovládání; náhled fotografie obsahuje skutečný text i zvuk.

Rozhodnutí:
- Míla schválil všechny tři navržené vývojové kroky. Čtení je místní,
  bez tichého krácení; prodloužení fotografie a zařazení zvuku jsou výslovné.
- Původní deník, média a osobní střih se při vývoji nemění. Starší střihy,
  samostatné karty a ruční časy komentářů zůstávají zpětně kompatibilní.

Další krok:
- Předat dokončený místní balíček k samostatnému p+n Lunou a poté přejít k přejímce.

Navrhované další kroky:
- Po nasazení fyzicky ověřit převzetí textu a poslech na Safari/iPhonu.
- Zachovat přejímku dvou cest, víceprojektový krok 6 a oddělený Python pilot.

Technický důkaz:
- 72 cílených testů PASS, včetně 13 nových regresí a DOM scénáře s texty/kartami.
- Syntetický text 3022 znaků u fotografie 25 s: uložení/reload, vědomé prodloužení,
  přesun, místní TTS a skutečné dekódované MP4 v 720p/1080p PASS.
- Kontroly soukromí, vazby textu, symlinků a HTTP Origin/HEAD/Range PASS.
- Plná brána 2206 PASS (450,207 s unit část), po závěrečné drobné úpravě ovládání 22 frontendových testů PASS. Safari/iPhone ani poslech uživatelem neověřené.
- Podrobnosti: `camino/docs/PHOTO_TEXT_COMMENT_REPORT.md`.


### 2026-10-24 11:20 CEST — Publikační brána a dohledání Node ve službě

Hotovo:
- Luna převzala oba připravené commity. Publikaci zastavilo jediné selhání
  nového DOM testu: hledal Node pouze v PATH, které má Cockpit omezené.
- Test nyní používá společný projektový `node_binary` a sám vynucuje
  službové PATH. Rozhraní ani uložené filmy se touto opravou nemění.

Rozhodnutí:
- Míla výslovně zadal p+n Lunou. Neúspěšná účtenka se nepřepisuje ani neopakuje.
- Nové placené předání po této opravě se automaticky nespouští.

Další krok:
- Před novým placeným pokusem ukázat Mílovi opravený balíček tří lokálních commitů.

Navrhované další kroky:
- Po úspěšném p+n fyzicky přijmout text a komentář na Safari/iPhonu.

Technický důkaz:
- Účtenka `570b4fc7ce1e29b96fac6a9b4f1654b2`: attention, push_state uncertain,
  deployment_state not_started. Brána 2206 testů: 1 ERROR, 15 skipped,
  405,950 s. Příčina pouze v dohledání Node v novém testu.
- Přímé read-only ls-remote stále e11d949a; nový main nebyl na GitHubu potvrzený.
- 21 cílených kontrol PASS, včetně původně selhávajícího DOM testu s vynuceným
  službovým PATH a kontraktu celého frontendu. Závěrečná statická brána
  rovněž pod omezeným PATH PASS. Produkční kód se touto opravou nemění.


### 2026-10-24 12:21 CEST — Upravitelný text, hlasové pokusy a obnovitelný koš

Hotovo:
- U fotografie je původní text z iPhonu pouze pro čtení a samostatná ručně
  upravitelná pracovní verze. Lze ji uložit, vrátit k originálu a opakovaně číst.
- Předchozí nahrávky zůstávají v seznamu se svým přesným pracovním textem.
  Lze je použít, jejich text znovu upravit, smazat pokus do koše a obnovit.
- Import MP3/WAV umožní dodat hotový přirozenější komentář nebo vlastní hlas.

Rozhodnutí:
- Míla schválil pokračování a výslovně požádal o smazání pokusů, zachování
  původního textu a opakovaný cyklus ruční editace a čtení.
- Smazání je obnovitelný koš; není to trvalé mazání originálů či souborů.
  Starší uložené filmy a zdrojové texty zůstávají platné a nezměněné.
- Místní hlas je zatím Zuzana. Příjemnější hlas vyžaduje zvláštní poslechovou
  zkoušku; osobní text se nyní neposílal do externí TTS a neproběhl placený pokus.

Další krok:
- Předat dokončený místní krok k samostatnému p+n Lunou, poté prakticky přijmout na Safari/iPhonu.

Navrhované další kroky:
- Po nasazení fyzicky přijmout celý cyklus u fotografie na Safari/iPhonu.
- Poslechem vybrat vhodnější český hlas; import MP3 již má společnou cestu.
- Víceprojektový krok 6 a oddělený Python pilot zůstávají otevřené.

Technický důkaz:
- 45 cílených kontrol PASS: 23 testů komentářů, 20 frontendových kontraktů,
  2 kontroly POST registru. Skutečné WAV/MP3 pod PATH služby, HTTP původ/limity,
  koš/obnovení, starší nahrávka, neměnný originál i hotový film PASS.
- Souběh opožděného načítání s ruční editací/autosave reprodukovaný jako FAIL;
  oprava generace čtení a oba řízené souběhy v DOM PASS. Bez prohlížeče
  ve dostupných plochách zůstává fyzický proklik otevřený.
- Plná brána 2216 PASS (458,188 s unit část). Osobní střih ani produkční nahrávky se neměnily.
- Předchozí vydání 5cd323ef: účtenka 4f7f51ee421b4fd20b71e09b454c509f
  potvrzuje push tří commitů, plnou bránu 2206, nasazení a smoke 5/5.
  Živý registrovaný audit 24. 10. to potvrdil; 570b4fc7 není poslední vydání.
- Postup a hranice: `camino/docs/COMMENTARY_WORKFLOW_REPORT.md`.


### 2026-10-24 17:32 CEST — sedmidenní koš celé cesty a filmu: místní vývoj dokončen

Hotovo:
- iPhone ukládá žádost o smazání celé cesty, skryje ji a pozastaví její práci. Mac ve střižně ukáže přesný rozsah, přijme potvrzení do koše a umožní obnovení před společnou sedmidenní lhůtou. Samostatný filmový projekt má vlastní koš a zachová originály cesty.
- Po lhůtě služba odstraní spravované soubory, textovou historii, fronty, odvozeniny a upload zbytky. Telefon čeká na ověřené dokončení Macu, smaže vlastní data a odešle ACK. Přerušený unlink i kompaktace jsou obnovitelné; nejasné starší kopie nebo změněné kořeny výmaz zastaví.
- Jen lokální zdroje a checkpoint. Žádný nový push, deploy, upgrade služby, instalace iPhonu ani mazání skutečného projektu. Předchozí funkční vydání zůstává 0cb79f32; dokončená Luna účtenka d7d836b810818f61162d4a887686f3a2 patří dřívějšímu komentářovému cyklu (returned_to_adam=false).

Rozhodnutí:
- Míla schválil koš na 7 dní a vývoj jednosměrného postupu: žádost iPhone → Mac, potvrzení/obnova na Macu, zpět pouze řízení a výsledky. Koš nevytváří mediální kopii. Zálohy, Fotky a ruční exporty mimo spravované kořeny zůstávají samostatné. Nový TVBCP se nezakládal.

Další krok:
- Samostatně schválit a provést odpovídající vydání služby Camino se schématem 4, Cockpitu a iPhonu; potom fyzická přejímka jedné syntetické cesty a filmu. P+n společného runtime tyto samostatné aktualizace nenahrazuje.

Navrhované další kroky:
- Na iPhonu/Safari přijmout offline žádost, potvrzení a obnovení na Macu, dokončení výmazu/ACK a skutečné uvolnění místa. Produkční čekání 7 dní zatím neověřené.
- Dokončit praktickou editaci textu fotografie, historii nahrávek, jejich koš a import MP3/WAV z dřívějšího vydání.
- Poslechem vybrat příjemnější český hlas.

Technický důkaz:
- Plná brána PASS: 2232 testů, unit část 381,487 s. Cílená finální přejímka 20 PASS: 16 testů koše, DOM scénář, frontend otisk a oba route kontrakty.
- Swift/Core Data 87 PASS a iOS Release PASS. Synteticky ověřené odstranění osobního textu z DB/WAL, zmenšení DB, přesné retry bez obnovení projektu, zachování druhé cesty, pozdní upload, interní/cizí hardlinky, alias kořene kontejneru, přerušený unlink i VACUUM a shoda potvrzených úložišť.
- Živá read-only kontrola 17:32 CEST: Camino/Cockpit/autosave PIDy i chráněné konfigurace shodné se zahájením; Cockpit health OK. Bez produkčních médií nebo tajemství v Gitu.
- Kontrakt a postup: camino/docs/PROJECT_TRASH_CONTRACT.md a camino/docs/PROJECT_TRASH_REPORT.md. Fyzická iPhone/Safari přejímka nového koše NEOVĚŘENO.


### 2026-10-24 17:56 CEST — p+n koše Lunou potvrzené

Hotovo:
- GitHub a Cockpit obsahují všech pět schválených commitů včetně 0a18db30. Ovládání koše ve střižně je nasazené. Vydání prošlo napoprvé; oprava ani další modelový pokus nebyly potřeba.

Rozhodnutí:
- Míla výslovně autorizoval p+n Lunou a při skutečném selhání opravu a další předání Luně až do úspěchu. Použit jediný registrovaný submit_release s wait=True; nejistý výsledek nebyl zaměněný za chybu ani opakovaný.

Další krok:
- Samostatně schválit upgrade služby Camino a instalaci nového iPhonu; běžné p+n tyto části nepřepíná. Potom fyzická přejímka syntetického koše.

Navrhované další kroky:
- Dokončit dřívější praktickou přejímku textu, hlasových pokusů, jejich koše a MP3/WAV; vybrat příjemnější český hlas poslechem.

Technický důkaz:
- Účtenka b75c48be083a1f26e8e7296ccf5997de: completed; push_state=confirmed; deployment_state=confirmed; 5 commitů; gate 2232 PASS / 550,9 s; smoke 5/5; protected_services_unchanged=true. Centrální release_executor gpt-6-luna/high beze změny.
- Adamova závěrečná živá kontrola: GitHub/main aligned 0/0 na 0a18db30, Cockpit health OK, code_stamp 7ae887842f089e5c a nový PID 10531. Samostatná služba Camino/autosave a jejich konfigurace nezměněné.
- returned_to_adam=false označuje nepotvrzený automatický portálový návrat. Účtenku skutečně převzal a jednou ověřil terminálový Adam; nejde o důvod opakovat potvrzené p+n. Fyzický iPhone/Safari a celý koš po aktualizaci služby dosud NEOVĚŘENO.


### 2026-10-24 19:24 CEST — podepsaná IPA 21 připravená, upgrade čeká na globální potvrzení

Hotovo:
- Nový podepsaný instalační balíček 21 ověřený a dostupný v Downloads i iCloud Dokumentech; cloud upload potvrzený. Stávající iPhone build 20 zachovaný.
- Read-only servisní preflight a migrace v RAM PASS; živá služba/archiv/config/Serve beze změny.

Rozhodnutí:
- Míla zadal vytvoření nové IPA a aktualizaci služby. Pro konkrétní změnu LaunchAgentu ještě chybí přesná věta podle globální brzdy; dřívější SSD souhlas se nerozšiřuje. Nový TVBCP nevznikl.

Další krok:
- Vyžádat přesnou globální větu pro předložený stop/snapshot/upgrade/start; potom ověřit službu a navázat aktualizací stejné aplikace v telefonu.

Navrhované další kroky:
- Fyzicky ověřit zachování dat a syntetický koš, následně dřívější přejímku střižny a českého hlasu.

Technický důkaz:
- Archive/export i strict codesign/ZIP PASS; verze 0.1.0 (21), stejné bundle ID, 1072250 B, profil do 29. 10. 2026; hashe uložené v CLIENT_21_SERVICE_UPGRADE_REPORT.md.
- Zdrojový archiv: 921 operací, 132 Momentů, 4 cesty, 316 originálů / 2 379 212 189 B SHA PASS, flags false. Schema 3→4 pouze v paměti, původní tabulky shodné; service venv import a požadavky PASS.
- Živý upgrade, instalace a fyzická přejímka NEPROVEDENO. Externí šifrovaná záloha nyní nepřipojená.

### 2026-10-24 19:48 CEST — služba schéma 4 a iPhone 21 aktualizované

Hotovo:

- Služba podporuje společný sedmidenní koš. iPhone aktualizovaný ze stejné aplikace 20 na 21 bez odinstalace, původní kontejner zachovaný. Viewer, deník, mapa a média po upgradu dostupné.

Rozhodnutí:

- Míla dodal přesnou globální větu pro konkrétní servisní přechod a aktualizaci telefonu. Tím se nepovoluje smazání skutečné cesty. Žádné nové funkční rozhodnutí ani TVBCP.

Další krok:

- Odemknout iPhone, otevřít Camino a vizuálně potvrdit původní cesty a záznamy; vzdálené spuštění odmítnuté kvůli zámku telefonu.

Navrhované další kroky:

- Fyzicky přijmout koš na syntetické cestě a filmu včetně obnovy; produkční sedmidenní lhůta a skutečné uvolnění místa dosud NEOVĚŘENO.
- Dokončit praktickou editaci textu, historii hlasů, jejich koš a import MP3/WAV; český hlas vybrat poslechem.

Technický důkaz:

- Čtyři DB snapshoty quick_check/SHA PASS; všechny původní tabulky i archiv shodné: 921 operací, 132 Momentů, 4 cesty a 316 originálů / 2 379 212 189 B SHA PASS. Serve/auth/identity zachované. Owner HTTP/HTTPS a Viewer PASS, všechna tři média Range 206.
- CoreDevice install a dotaz na build 21 PASS; všech 7 původních položek a velikosti/mtime SQLite/WAL/SHM před prvním spuštěním shodné. Toto není úplná hashová ani vizuální přejímka telefonu. Profil IPA do 29. 10. 2026; SideStore evidenci přímá instalace neověřila.
- Důkazy pouze v ignorovaném private adresáři, veřejný souhrn CLIENT_21_SERVICE_UPGRADE_REPORT.md. Externí šifrovaná záloha nepřipojená; ověřené místní snapshoty nejsou externí záloha. Zdrojový kód se neměnil; předchozí plná brána 2232 PASS. Závěrečná statická brána a git diff --check PASS.

### 2026-10-24 20:41 CEST — oprava návratu po žádosti o smazání, IPA 22

Hotovo:

- Bez aktivní cesty zůstává přístup k ostatním projektům, koši a přenosům. Nová podepsaná IPA 22 je připravená v Downloads a iCloud Dokumentech, telefon nebyl touto opravou aktualizovaný.

Rozhodnutí:

- Opravit Mílou doložený slepý konec v UI; žádné nové funkční rozhodnutí. Cesta se sama neobnovuje a její žádost se neruší.

Další krok:

- Aktualizovat stávající Camino IPA 22 bez odinstalace a fyzicky ověřit tlačítko Projekty a koš i přenosy.

Navrhované další kroky:

- Dokončit praktický koš na syntetické cestě/filmu včetně obnovy; skutečná sedmidenní lhůta a uvolnění místa zůstávají nepřijaté.
- Navázat přejímkou textu, historie nahrávek, jejich koše, MP3/WAV a českého hlasu.

Technický důkaz:

- Izolovaný UI scénář: původní binárka FAIL na chybějícím návratu (129,859 s), oprava PASS (89,366 s). Zachovaný Moment při návratu do jiné cesty, koš i přenosy dostupné po žádosti o poslední cestu a restartu. Statická brána PASS.
- Release archive/export, strict codesign a ZIP/CRC PASS; IPA 0.1.0 (22), 1074899 B, profil do 29. 10. 2026, shodné kopie v Downloads/iCloud. Fyzická instalace/přejímka 22 NEPROVEDENO. Handoff a projektová paměť odkazují PROJECT_TRASH_NAVIGATION_REPORT.md.
- Jen UI a syntetický simulátor: bez změny datového modelu, serveru, živých žádostí, smazání dat, nového push či p+n. Míla před opravou potvrdil spuštění 21 a žádost, původní blokátor zamčeného telefonu tím není aktuální.

### 2026-10-24 21:15 CEST — potvrzený úklid nedokončených médií, IPA 23

Hotovo:

- Připravený klient nabízí odstranění prázdných pokusů a jednotlivých nedokončených souborů přímo v aplikaci. Neúspěšný start bez souboru už nezanechá prázdný intent. Podepsaná IPA 23 v Downloads/iCloud; stávající telefon 22 a jeho dva prázdné pokusy zatím zachované.

Rozhodnutí:

- Míla požádal o odstranění doložených zbytků a prevenci nebo možnost smazání v aplikaci. Použít potvrzenou aplikační operaci s ověřeným rozsahem; živá Core Data DB se zvenčí nepřepisuje. Přijaté záznamy ani sedmidenní koš se neobcházejí.

Další krok:

- Aktualizovat stávající Camino IPA 23 bez odinstalace a potvrdit Odstranit prázdné pokusy (2) v nové obrazovce kontroly. Fyzické vyčištění zatím NEPROVEDENO.

Navrhované další kroky:

- Dokončit koš syntetické celé cesty/filmu včetně obnovy a skutečné lhůty/uvolnění místa.
- Navázat praktickou přejímkou textu, historie nahrávek, jejich koše a MP3/WAV; český hlas vybrat poslechem.

Technický důkaz:

- Read-only telefonní inventář + soukromá SQLite/WAL kopie: 2 video intenty z 13. 10., žádné soubory, Assety ani Momenty, žádný v blokovaném projektu. Klient 22 ověřený. Privátní obsah/ID do Gitu nepatří.
- Swift 95 PASS (8 nových), nový UI scénář 31,631 s PASS, navigace 88,193 s PASS, plná brána 2232 PASS / 465,698 s unit část. Test ruší potvrzení, maže jen vybrané pokusy a po restartu zachová původní Moment. Finální UI test čerstvě zkompilovaný.
- Archive/export/strict codesign/ZIP PASS, IPA 0.1.0 (23), 1103371 B, profil do 29. 10. 2026, shodné kopie a iCloud upload PASS; zdroje doložené hashy v privátní účtence. Fyzický klient 23, úklid těchto dvou řádků a skutečná kamera NEOVĚŘENO. Podrobnosti PENDING_MEDIA_REVIEW_REPORT.md. Bez nového push/p+n či zásahu do služby.

### 2026-10-24 21:44 CEST — všech pět commitů publikovaných a Cockpit nasazený Lunou

Hotovo:

- Schválený balíček pěti commitů včetně oprav klienta a podepsané IPA dokumentace je na GitHubu do 3590c288. Cockpit vydaný a zdravý; samostatná služba i telefon zachované.

Rozhodnutí:

- Míla výslovně zadal všechny čekající commity Luně pro p+n. Jeden registrovaný submit_release s wait=True, přesný živý proud Camino a zmrazený head; žádný nativní pomocník, retry ani přepnutí modelu. Nové funkční rozhodnutí nevzniklo.

Další krok:

- Fyzicky přijmout IPA 23 a potvrdit cílený úklid prázdných pokusů v aplikaci. Poslední přímý telefonní audit je build 22; novější instalace/úklid tímto p+n nejsou ověřené.

Navrhované další kroky:

- Dokončit přejímku koše celé syntetické cesty/filmu včetně obnovy a skutečné lhůty/uvolnění místa.
- Dokončit text, historii nahrávek, jejich koš a MP3/WAV; český hlas vybrat poslechem.

Technický důkaz:

- Účtenka a2500be19e301dc26e6db4cd9fb597a8: completed, 5 commitů 0a18db30→3590c288, push_state/deployment_state=confirmed; full gate 2232 PASS / 454,2 s, smoke 5/5, protected_services_unchanged=true.
- Adamova závěrečná kontrola GitHub/main 0/0 na vydaném headu, health OK, stamp 7ae887842f089e5c, PID 41492. Zápis výsledku je následný lokální dokumentační checkpoint, nikoli další funkční vydání.
- return_channel=caller, returned_to_adam=false: portálový automatický návrat nepotvrzený; původní terminálový Adam účtenku skutečně převzal a jednou ověřil. Úspěšné p+n se kvůli tomu neopakuje. Předchozí Swift 95/UI a IPA podpis/ZIP/cloud PASS; fyzický telefon 23 zatím NEOVĚŘENO.


### 2026-10-25 20:28 CET — první UI krok filmové střižny

Hotovo:

- Střižna má společnou viditelnou odezvu, vysvětlené hlavní blokace a návrat na rozpracované místo po fotografii. Provedeno lokálně.

Rozhodnutí:

- Míla schválil první krok z UI analýzy; nejprve zpětná vazba a orientace, větší přestavba plochy později. Původní datové a bezpečnostní kontrakty zachované.

Další krok:

- Po samostatném pokynu p+n ověřit skutečný prohlížeč podle přejímky v reportu.

Navrhované další kroky:

- Prostornější pracovní plocha a jasné hlavní akce.
- Praktická přejímka textu/nahrávek/importu a příjemnější český hlas.

Technický důkaz:

- 102 cílených testů PASS a rychlá statická brána PASS; Node regrese pozice, hlášek, podmínek, procent exportu, soukromí a stale odpovědí.
- Browser viditelnost/overlap a fyzický Safari/iPhone NEOVĚŘENO. Bez nového vydání či změny osobního filmu; report camino_film_ui_feedback_20261025.md.


### 2026-10-26 09:28 CET — Luna p+n prvního UI kroku střižny dokončené

Hotovo:

- Nová odezva střižny a zachování místa po fotografii jsou nasazené v Cockpitu. Podávaná stránka obsahuje nové ovládání; fyzický proklik zůstává otevřený.

Rozhodnutí:

- Míla výslovně zadal p+n Lunou. Použit jeden registrovaný submit_release s wait=True a přesným lokálním headem; bez opakovaného předání a bez změny rolí.

Další krok:

- Po uložení případného rozpracovaného střihu obnovit Cockpit a fyzicky ověřit hlášky při posouvání a návrat od fotografie podle reportu.

Navrhované další kroky:

- Prostornější pracovní plocha a jasné hlavní akce.
- Praktická přejímka textu/nahrávek/importu a příjemnější český hlas.

Technický důkaz:

- Účtenka 1173a162fd7197d9f5281e76a0f9d400, jeden commit do bc1fe4ad, push/deployment confirmed; plná brána 2232 PASS / 345,9 s, smoke 5/5, chráněné služby shodné.
- Jedna kontrola Adama: GitHub/main 0/0 a profily ready, health OK, HTTP 200 a přesná shoda nového frontendového HTML, code_stamp 28c8f0a83e59bc1b. Skutečný browser/Safari/iPhone NEOVĚŘENO.
- return_channel=caller, returned_to_adam=false: portálový automatický návrat nepotvrzený, terminálové převzetí a kontrola proběhly. Následný lokální zápis účtenky; žádné další publikování.


### 2026-10-26 09:59 CET — přijatý UI 1 a lokální pracovní plocha UI 2

Hotovo:

- Míla potvrdil první UI krok jako fungující. Nově lokálně připravená přehlednější pracovní plocha, výběr záběru a dostupné hlavní akce; změny zůstávají uložené při přepínání pohledu.

Rozhodnutí:

- Na Mílův pokyn pokračovat navazuje druhý krok z odsouhlasené UI analýzy. Adam zachoval datové kontrakty a řešil pouze pohled/ovládání; nové TVBCP ani trvalé úložiště nevzniklo.

Další krok:

- Samostatné p+n druhého kroku, poté skutečná přejímka rozložení a výběru podle reportu.

Navrhované další kroky:

- Praktická přejímka textu/nahrávek/importu a příjemnější český hlas.

Technický důkaz:

- 103 cílených testů PASS / 47,818 s; závěrečné Node interakce a 21 frontendových kontraktů PASS / 2,216 s; rychlá statická brána PASS.
- Bez renderu při procházení/přehrání hotového výsledku, zachované texty, pořadí podle identity, skryté privátní URL a ignorování opožděné chyby přehrávání. Skutečný browser UI 2 NEOVĚŘENO.
- Report camino_film_workspace_20261026.md; předchozí UI 1 vydané v bc1fe4ad, uživatelské přijetí bez určení zařízení. Tento krok je lokální, bez dalšího push/nasazení či zásahu do telefonu/služby.


### 2026-10-26 10:28 CET — Luna p+n pracovní plochy UI 2 dokončené

Hotovo:

- Nová pracovní plocha a hlavní ovládání filmu jsou nasazené v Cockpitu. Podávané HTML obsahuje nový seznam/náhled/nastavení i horní toolbar; fyzický proklik čeká na přejímku.

Rozhodnutí:

- Míla výslovně zadal p+n Lunou. Jeden registrovaný submit_release s wait=True převzal přesný balíček dvou commitů; žádné opakované předání ani změna rolí.

Další krok:

- Po uložení rozpracovaného střihu obnovit Cockpit a fyzicky ověřit výběr, rozložení a hlavní akce podle reportu.

Navrhované další kroky:

- Praktická přejímka nahrávek/importu a příjemnější český hlas.

Technický důkaz:

- Účtenka aedb878e354d3771056c54fa12acc909, dva commity do 41ac2e1d, push/deployment confirmed; plná brána 2233 PASS / 350,9 s, smoke 5/5, protected_services_unchanged=true.
- Adamova jedna kontrola: GitHub/main 0/0 na vydaném headu, profily ready, health OK a HTTP 200 přesně shodné s novým frontendovým HTML včetně workspace/toolbaru. Code stamp 28c8f0a83e59bc1b; nové UI ověřené skutečným HTML, ne pouze stampem.
- Return caller skutečně převzal; returned_to_adam=false neprokazuje portálový automatický návrat. Fyzický browser UI 2 NEOVĚŘENO. Následuje jen lokální výsledkový zápis, nikoli další publikování.


### 2026-10-26 11:25 CET — odstranění ukázky a optimalizace načítání, lokálně

Hotovo:

- Z lokálního UI zmizela nepoužívaná P2-A ukázka a její stará HTTP cesta. Menší obrázky a odstraněné opakované plné čtení filmu výrazně zrychlily serverové operace; skutečná přejímka celé stránky čeká na nasazení.

Rozhodnutí:

- Odstranit jen ověřené syntetické P2-A běhy podle zmrazeného inventáře. Mazání čeká na přesnou globální větu pro tento rozsah. Oprávnění se nikdy necachují; plné ověření při ukládání/renderu zachované.

Další krok:

- Po přesném potvrzení znovu ověřit inventář a odstranit pouze 4 testovací běhy / 109 souborů / 69,04 MiB; dosud 0 smazaných souborů.

Navrhované další kroky:

- Samostatně zadané p+n Lunou, potom porovnat načtení stejného filmu v prohlížeči. Praktické nahrávky/import a příjemnější český hlas zůstávají otevřené.

Technický důkaz:

- Finální plná brána 2243 PASS / 458,763 s unit část, cíleně 45 + 6 kontrol PASS. Teplé ověření stavů i malé PNG chrání změnu soukromí, poškození se stejnou velikostí/mtime, symlink a změnu při hashování. První selhání evidence tuple-prefixů opravené bez oslabení testu.
- Miniatura 5,287 → 0,192 s, 16 227 034 → 100 491 B; stav editoru 45 záběrů 1,324 → 0,039 s při již ověřených souborech. Studená kontrola zdrojů 1,241 s. Místní serverová měření, nikoli celá stránka; originály a střihy zachované.
- Soukromý plán: cleanup_receipts/camino_p2a_20261026/plan.json, SHA-256 b0bcf0c26c660467b7dbe3aabbd07a4262b37507d3a8359d93ea1e80b5859034. Report camino_film_loading_20261026.md. Bez push/nasazení, bez výmazu dat.


### 2026-10-26 11:29 CET — potvrzený úklid syntetických dat P2-A dokončený

Hotovo:

- Všechny čtyři staré testovací běhy P2-A jsou odstraněné. Zůstává prázdný kořen a malá soukromá účtenka, žádné testovací médium v tomto kořeni.

Rozhodnutí:

- Míla dodal přesnou globální větu pro předem připravený výmaz. Rozsah zůstal shodný s potvrzeným plánem; skutečné projekty, originály a historické zálohy nebyly součástí výmazu.

Další krok:

- Samostatně zadané p+n kódu odstraněné ukázky a optimalizací přes Lunu; zatím místně v 11098612.

Navrhované další kroky:

- Přijmout skutečnou rychlost celé stránky po nasazení; navázat nahrávkami/importem a českým hlasem.

Technický důkaz:

- Plan SHA-256 b0bcf0c26c660467b7dbe3aabbd07a4262b37507d3a8359d93ea1e80b5859034 ověřený; 109 souborů se shodnými metadaty a SHA-256, pouze očekávané názvy a interní hardlinky. Výmaz přes otevřené adresáře bez následování symlinků, před každým unlink opět identita/hash; průběžná soukromá účtenka.
- Receipt cleanup_receipts/camino_p2a_20261026/receipt.json: completed, 109 souborů, 16 adresářů, 72 396 174 logických B; následná nezávislá kontrola prázdného kořene a účtenky PASS. Unikátní alokované bloky před výmazem 43 364 352 B (41,36 MiB); součet 69,04 MiB zahrnoval hardlinky. Čistá změna volných bloků celého SSD NEOVĚŘENO.
- Produkční kód se neměnil; předchozí plná brána 2243 PASS se neopakovala. Bez push/nasazení a bez zásahu do telefonu/služby.


### 2026-10-26 11:48 CET — Luna p+n optimalizace načítání dokončené

Hotovo:

- Cockpit podává střižnu s menšími obrázky a bez nepotřebné P2-A ukázky. Nové HTML přesně odpovídá vydávanému kódu; skutečnou rychlost v uživatelově prohlížeči je ještě nutné přijmout.

Rozhodnutí:

- Míla výslovně zadal „luna p+n roger!“. Jeden registrovaný submit_release s wait=True předal celý přesný balíček; bez nativního pomocníka a bez opakování.

Další krok:

- Po uloženém střihu obnovit Cockpit a porovnat načtení stejného filmu a přepínání fotografií.

Navrhované další kroky:

- Praktické nahrávky/import a výběr příjemnějšího českého hlasu poslechem.

Technický důkaz:

- Účtenka 51926adfe2cd519ff4d8d57a66916024, 3 commity do d99093c1, push/deployment confirmed. Plná brána 2243 PASS / 431.5 s, smoke 5/5 a protected_services_unchanged=true.
- Jedna Adamova kontrola účtenky: health OK, nové složené HTML HTTP 200 a přesná shoda se zdrojem, thumbnail/image-preview přítomné, demo chybí, starý odkaz HTTP 404. P2-A datový kořen znovu prázdný. Code stamp dd0a0d1332d72444.
- Return caller převzatý; returned_to_adam=false neprokazuje automatický portálový návrat a nevede k retry. Celá stránka přes fyzický browser/iPhone NEOVĚŘENO. Následuje jen místní výsledkový zápis.


### 2026-10-26 13:48 CET — vlastní zvětšení fotografie, lokálně

Hotovo:

- Fotografii lze zvětšit přímo ve střižně a zavřít bez návratu na začátek seznamu či přestavby rozepsaných polí. Velká fotografie se načte pouze ručně.

Rozhodnutí:

- Míla povolil další vývoj. Navazuje vlastní zvětšovací dialog z předchozí UI analýzy; stávající soukromý obrazový endpoint a fallback nové karty zůstávají. Výběr jiného českého hlasu vyžaduje samostatné poslechové rozhodnutí; Mac nyní nabízí jen Zuzanu.

Další krok:

- Samostatné p+n Lunou, poté skutečný proklik fotografie uprostřed filmu včetně Esc, scrollu, fokusu a rozepsaného textu.

Navrhované další kroky:

- Praktická přejímka historie nahrávek/koše/importu a výběr příjemnějšího českého hlasu.

Technický důkaz:

- 88 cílených kontrol PASS / 60,868 s; Node regrese návratu, nulových save/source/render, zrušení při skrytí/oprávnění, starých událostí a fallbacku PASS. HTML struktura/otisk PASS; rychlá statická brána PASS.
- Nový obrázek/identita/epocha při každém otevření, při zavření a invalidaci odstraněné src/DOM/název. Backend, originály, revize a produkční render beze změny. Report camino_film_photo_dialog_20261026.md.
- Žádný připojený browser; fyzická vizuální/klávesová přejímka NEOVĚŘENO. Lokální checkpoint, bez nového push/nasazení. Poslední vydání d99093c1/Luna 51926adf zůstává předchozím odděleným výsledkem.


### 2026-10-26 14:02 CET — Luna p+n zvětšovacího okna dokončené

Hotovo:

- Cockpit podává verzi s fotografickým oknem přímo ve střižně. Podávané HTML přesně odpovídá novému kódu; fyzický proklik v uživatelově prohlížeči ještě čeká na přejímku.

Rozhodnutí:

- Míla výslovně zadal „Ok luna p+n“. Jediné registrované submit_release s wait=True předalo celý přesný balíček dvou commitů; bez nativního pomocníka a bez retry.

Další krok:

- Po uloženém střihu obnovit Cockpit a fyzicky ověřit zvětšení/zavření, Esc, scroll/fokus a rozepsaný text.

Navrhované další kroky:

- Praktická přejímka nahrávek/historie/koše/importu a příjemnější český hlas poslechem.

Technický důkaz:

- Účtenka 05b42458927b15403b14a7eaf4eb3bb9, 2 commity do 004ec7e1, push/deployment confirmed. Plná brána 2243 PASS / 431.0 s, smoke 5/5, protected_services_unchanged=true.
- Adamova jedna kontrola: health OK, HTTP 200 a přesná shoda složeného HTML včetně dialogu/obsluhy. HTML SHA-256 996571f43ceeb225384e0d6173a06421e3d91a057edc985abc91304ae040b0ab, code stamp dd0a0d1332d72444; shoda obsahu je důkaz frontendu i při stejném stampu.
- Return caller převzatý, returned_to_adam=false neprokazuje automatický portálový návrat. Fyzický browser/Safari/iPhone NEOVĚŘENO. Následný výsledkový zápis je místní, bez dalšího publikování.


### 2026-10-26 16:33 CET — čtyři české hlasy k poslechu

Hotovo:

- Míla může porovnat čtyři krátké české hlasy na místní stránce s volbou tempa. Zvukové soubory jsou uložené v projektu, dohromady asi 190 KiB.

Rozhodnutí:

- Po Mílově odmítnutí Zuzany připravit poslechové kandidáty před změnou hlasu ve střižně. Vlastní generování Microsoftu odmítlo první požadavek HTTP 429; konečné skutečné MP3 pocházejí z oficiálního českého katalogu Google. Žádný hlas nebyl automaticky vybraný.

Další krok:

- Míla vybere A Kore, B Aoede, C Charon nebo D Orus a případně tempo, nebo všechny odmítne.

Navrhované další kroky:

- Ověřit proveditelnou API integraci, rozpočet a soukromí pro vybraný hlas; zachovat celý komentář. Praktická přejímka editoru a nahrávek/importu, potom P2-F.

Technický důkaz:

- Čtyři MP3 / 194 796 B, úplné FFmpeg dekódování, délky 6,48 / 6,04 / 5,68 / 6,32 s, hashy a soubory PASS. Poslechová stránka node --check PASS, Safari open exit 0; skutečný lidský poslech NEOVĚŘENO.
- Soukromý ignorovaný manifest a index: data/private/camino/voice-audition-20261026/. Report camino_voice_audition_20261026.md; jen veřejné reference a smyšlený vstup, žádný placený API požadavek, soukromý deník, změna produkčního kódu či p+n.
- Pro budoucí film nelze použít chatové krácení na 1500 znaků. Žádné tajemství ani token se do tohoto zápisu neukládá.


### 2026-10-26 17:01 CET — vybraný Orus, aktivace čeká na přístup

Hotovo:

- Výběr D — Orus je uložený a poslechová stránka jej označuje jako vybraný. Připravený konkrétní plán jeho připojení a cena první malé zkoušky.

Rozhodnutí:

- Míla řekl „OK, použij D.“ Použít přesný Orus z katalogu Chirp 3 HD, bez tiché záměny za jiný hlas. Tato volba sama nenastavila Google účet, fakturaci ani rozpočet.

Další krok:

- Míla doplní, zda má existující Google Cloud projekt, případně zadá přípravu nového připojení. Přístup, rozpočet a oprávnění k aktivaci je nutné vyřešit před skutečným generováním.

Navrhované další kroky:

- Smyšlená zkouška do 1000 znaků (nejvýše 0,03 USD při zveřejněné sazbě), potom zapojení do střižny s celým textem a potvrzením odeslání. Editor/nahrávky/import a pozdější P2-F zůstávají otevřené.

Technický důkaz:

- Místní manifest: selected_voice=cs-CZ-Chirp3-HD-Orus, selection_pending=false, installed_in_editor=false. Privátní integration-plan.json neobsahuje klíče; approved_budget_usd=null a new_paid_requests=0.
- V projektovém prostředí nenalezené nastavení Google, místní ADC ani Google auth/TTS balíčky; kontrola četla jen přítomnost, nevypisovala žádné hodnoty tajemství. Oficiální API vyžaduje projekt, povolené TTS a fakturaci; limit 5000 UTF-8 bajtů/požadavek, celý filmový text má zůstat do 6000 znaků bez krácení.
- Ceník 30 USD/milion znaků po dokumentované bezplatné kvótě, ověřeno 26. 10. 2026. Žádná skutečná syntéza Orus, instalace, přihlašování, aktivace či p+n. Report camino_voice_audition_20261026.md.


### 2026-10-26 17:16 CET — Luna p+n dokumentace Orusu dokončené

Hotovo:

- Projektová dokumentace vybraného hlasu a konkrétního připojení je publikovaná. Samotný Orus stále čeká na Google Cloud přístup; toto vydání jej neaktivovalo.

Rozhodnutí:

- Míla výslovně zadal p+n Lunou. Jediný registrovaný submit_release s wait=True vydal celý přesný dokumentační balíček, bez opakování.

Další krok:

- Získat informaci o existujícím Google Cloud projektu nebo přípravu nového připojení; poté vyřešit přístup a aktivaci/rozpočet před první skutečnou syntézou.

Navrhované další kroky:

- První malá smyšlená zkouška Orusu, potom integrace celého komentáře s výslovným potvrzením externího zpracování. Přejímka editoru a později P2-F.

Technický důkaz:

- Účtenka c418d280bd7f24e0146cf90fabe2e4c6, 3 commity do 4dc65832, push/deployment confirmed; gate 2243 PASS / 430.7 s, smoke 5/5 a protected_services_unchanged=true.
- Jedna Adamova kontrola: Git rozsah vůči 004ec7e1 pouze memory, health OK, HTML HTTP 200 přesně shodné se zdrojem a SHA-256 996571f43ceeb225384e0d6173a06421e3d91a057edc985abc91304ae040b0ab. Soukromý manifest vybraný Orus/installed_in_editor=false potvrzený. Code stamp dd0a0d1332d72444.
- Return caller převzatý; returned_to_adam=false neprokazuje automatický portálový návrat a nevede k opakování. Následný výsledkový zápis je místní checkpoint pro příští vývoj.

### 2026-10-27 18:05 CET — Orus s klidnějším tempem a místní integrace

Hotovo:

- Přístup Google funguje a Orus přečetl vlastní smyšlenou ukázku. Míla přijal výslovnost a příjemnost a vybral prostřední tempo o 10 % pomalejší. Nový hlas je zapojený v místním kódu střižny.

Rozhodnutí:

- Použít cs-CZ-Chirp3-HD-Orus a tempo 0,90 se zachováním výšky hlasu. Rozpočet 0,01 USD platil pro jedinou syntetickou zkoušku; nové UI vyžaduje samostatný souhlas a cenu pro každý konkrétní text.

Další krok:

- Samostatně zadat Luna p+n; po vydání fyzicky přijmout nové ovládání a komentář.

Navrhované další kroky:

- Po vydání fyzicky ověřit ovládání souhlasu, přesný celý komentář a umístění do filmu; zachovat přejímku historie, koše a MP3/WAV, později P2-F.

Technický důkaz:

- První syntéza: HTTP 200, 166 znaků, MP3 44 736 B / 11,184 s, full decode PASS. Přijaté místní tempo 0,90 má 12,414 s, bez dalšího cloudového generování. Nový adaptér s google-auth ověřený přihlášením a read-only seznamem hlasů. Klíč jen v ignorované chráněné složce.
- 100 cílených kontrol PASS / 62,419 s a nový HTTP test PASS / 0,770 s. Plná brána: 2256 PASS / 482,110 s unit část, celkem 496,501 s. Bez nového p+n, změny skutečných projektů, samostatné služby či iPhonu. Nové UI fyzicky NEOVĚŘENO. Detail: camino_orus_integration_20261027.md.
