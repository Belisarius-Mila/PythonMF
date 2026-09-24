# Camino

Aktualizováno: 2026-09-24 22:47 CEST
Pracovní proud: `project-camino` · typ Project · režim active · priorita 1.

## Cíl a hranice

Offline deník na iPhonu, bezpečné originály a osobní deník na Macu. Celý obsah
`Do deníku` může být přes soukromý read-only Camino Viewer dostupný Janě;
`Jen pro mě` je z Vieweru vyloučeno. Jeden autor a jeden hlavní editující iPhone,
žádný veřejný web. P1 výběr dalším lidem a P2 film zůstávají oddělené etapy.

## Aktuální stav

- Autoritativní podklady jsou v0.5 spolu s dodatkem U15. Původní balíček v0.5 je uložen beze změny a 6/6 manifestovaných souborů prošlo SHA-256 kontrolou; ZIP je lokálně zachovaný. U15: celá položka `Do deníku` je po synchronizaci Viewer-eligible, samostatná Úvaha vždy vzniká `Jen pro mě` a vyžaduje vědomé `Vložit do deníku`.
- Delta C00 audit Vieweru: Tailscale 1.102.4 je online, soukromý HTTPS Serve vede na živý Cockpit, Funnel není povolený, Cockpit smoke 5/5, AC `sleep=0` a FileVault zapnutý. Samostatný Camino backend/worker/Viewer, jeho autorizace, záloha, restart a vzdálený test na Janiných zařízeních ještě neexistují; G8 NEPROVEDENO.
- Profilový fast-forward byl opraven tak, aby whitespace preflight použil `.gitattributes` z přijímaného commitu; importované Markdown hard breaks tak neoslabují kontrolu ostatních souborů. Regrese je krytá testem.
- T016 PASS: přesně 30:24,406, 175 147 072 B, 48 kHz mono, režim Letadlo, převážně pod zámkem a celý poslech OK. T018–T020, T024 a T059 PASS podle Míly. T021 PASS v rozsahu C01b prototypu; plná integrace se zopakuje v C04. T059 po restartu ochránil data a řízené opakování zachytilo všechny značky pod zámkem. Vítr neověřen.
- C01b 0.2.0 (2) je historicky přijaté pro background audio, přerušení a vědomé pokračování; před přechodem na C01c prošla instalace i zachování tehdejších 15 položek. Aktuálně je na iPhonu C01c 0.3.0 (4).
- Běžící recorder přežije změnu scenePhase; nový Start/Pokračovat pouze v popředí. Přerušení ihned pozastaví vstup, ověří dostupnou část a nabídne Pokračovat/Ukončit. Pokračování vytváří novou část stejné session s evidovanou pauzou, bez přepisu předchozího média.
- Soubory vytvořené v C01b mají completeUntilFirstUserAuthentication; původní C01a soubory se nemigrují ani nemění. Staré JSON podporuje volitelné continuation. Tyto starší jednotlivé CAF samy nejsou C01c segmentový journal ani důkaz 60s cíle.
- Ověřeno 47/47 Swift testů, 2/2 UI testy simulátoru včetně snímku obrazovky, finální podepsaný iOS build a strict podpis; UIBackgroundModes=[audio]. Plná projektová brána PASS, 1684/1684 testů.
- C01b 0.2.0 (2) přijato v prototypovém rozsahu. Krátký test zámku a T016/T018–T021/T024/T059 PASS; T059 prošel po řízeném zopakování jedním nepřerušeným 107,801s souborem. Předchozí nevysvětlený tichý úsek se nezopakoval.
- C01c zahájeno výslovným pokynem Míly. Verze 0.3.0 používá jeden `AVAudioEngine` input tap, 55s checkpointy s návrhovým stropem 60 s, create-only journal a obnovu platných částí po pádu bez automatického mikrofonu. Legacy C01a/C01b zůstává bez migrace.
- Build 3 při prvním Start padal. Pět shodných crash reportů potvrdilo `SIGTRAP` v `_swift_task_checkIsolatedSwift`: inline tap callback zdědil `MainActor`, ale běžel na real-time audio frontě. Build 4 vytváří callback v `nonisolated` helperu; přísné Swift 6 kontroly zůstávají zapnuté.
- Opravný průchod: 52/52 Swift testů, 2/2 UI testy, nepodepsaný i podepsaný build a strict podpis PASS. 0.3.0 (4) je nainstalovaná a spuštěná bez odinstalace. Všech 136 položek před instalací zůstalo po instalaci i launchi shodných v cestě, typu a velikosti; pět nedokončených pokusů se nemazalo.
- Krátký fyzický smoke buildu 4 PASS podle Míly: Start nespadl, čas i ukazatel rostly, Stop fungoval a nový záznam šel přehrát. Účtenka potvrzuje normálně dokončený Komentář 10,7 s, 2 058 496 B, 48 kHz mono, jeden segment, bez přerušení, recovery a mezery. Všech 136 předchozích položek zůstalo beze změny; přibylo sedm očekávaných položek nového pokusu.
- T022 PASS ve dvou odlišných fázích otevřené části. Po obou nucených ukončeních zůstal relaunch v klidu, obnovené částečné nahrávky byly pravdivě označené a zachovaný rozsah přehratelný. Snímek prvního průchodu ukazuje tři části a 02:18 zachovaného rozsahu.
- T023 PASS podle Míly: v souvislém nejméně čtyřminutovém záznamu zazněly značky před a po čtyřech 55s hranicích jednou, ve správném pořadí, bez opakování, nevysvětlené mezery či useknutí. C01c 0.3.0 (4) je tím přijaté v prototypovém rozsahu.
- Profil hlavní aplikace platí do 22. září 18:16 CEST. G0/G1/G8, terénní připravenost a dlouhodobá spotřeba zůstávají nesplněné; plný databázový T061 se vrátí v C05a. Původní nahrávky i samostatný Camino Test zůstávají zachované.
- C02a zahájeno výslovným pokynem Míly. Lokální loopback přijímač pro syntetický soubor streamuje do soukromého stagingu, sám ověřuje velikost/SHA-256 a vytváří objekt i účtenku create-only. Identický retry neduplikuje; jiné bajty pod stejným ID jsou konflikt.
- C02a cílené automatické ověření 10/10 PASS. Následný privátní HTTPS smoke přes dočasnou cestu Tailscale Serve ověřil správný upload, serverový hash a délku, právě jeden objekt a účtenku, chybný hash, konflikt i idempotentní retry. Funnel zůstal vypnutý, Cockpit dostupný a původní Serve konfigurace byla po testu přesně obnovena. C02a je přijaté v prototypovém rozsahu; tento tehdejší smoke sám nedokládal fyzický iPhone, cizí síť ani úplné T043/T048/T051.
- C02b má druhý lokální checkpoint. Receiver obnovuje 8MiB části; samostatná aplikace `Camino Transfer Test` pro syntetickou dávku 96 MiB + 257 B používá jednu background `URLSession`, uploady ze souborů, trvalý journal, Keychain a nejvýše dvě připravené části. Nečte Fotky, mikrofon ani Camino Audio.
- Klient po relaunchi věří jen validnímu serverovému snapshotu, 100 % bytů drží jako `Ověřuji`, mobilní grant váže na jednu existující dávku a bez soukromé sítě nemá veřejný fallback. Swift core 19/19, T043 ovladač + oba receivery 28/28, T047/T043 workflow modul 11/11, UI 1/1 a plná projektová brána 1716/1716 PASS.
- T043 PASS v syntetickém rozsahu: Letový režim zachytil relaci `uploading` s 0/13 přijatými částmi; po obnově sítě vznikl jediný objekt daného Assetu, 13/13, 100 663 553 B a shodný SHA-256. Build 1 přitom odhalil zahozené souběžné impulsy a opakované ruční klepnutí; build `Camino Transfer Test` 0.4.0 (2) je koaleskuje a následná celá dávka doběhla automaticky bez dalšího klepnutí. Build 2 je strict podepsaný, nainstalovaný a spuštěný; profil platí do 24. září 2026 a Camino Audio zůstalo nedotčené.
- T043 receiver je zastavený, `/camino-c02b` odebraná, původní Serve přesně obnovený a Funnel vypnutý; všechny tři ověřené důkazy jsou zachované. Oddělený registrovaný T047 workflow používá vlastní stav a audit hashově ověřených částí i nedokončených relací.
- T047 PASS v rozsahu syntetického C02b: první dávka byla zamčená během přenosu a po odemčení se dokončila 13/13; u druhé dávky byl po 1/13 skutečně ukončen proces, serverový stav zůstal 1/13 bez druhého objektu a po ručním relaunchi se doplnily pouze chybějící části do 13/13. Živé potvrzení má 2 relace, 2 ověřené objekty/účtenky, každý 100 663 553 B, celkem 201 327 106 B.
- T047 receiver je ukončený, `/camino-c02b` odebraná, původní Serve přesně obnovený a Funnel vypnutý.
- Míla zvolil kvůli nedostupné cizí Wi-Fi pořadí T049 → T048. Oba testy mají oddělená registrovaná start/token/status/stop workflow a postup v `camino/tasks/C02b_T048_T049_FIELD_PLAN.md`.
- `Camino Transfer Test` 0.4.0 (3) omezuje mobilní i drahou síť u všech HTTPS požadavků na konkrétní povolenou dávku a rozlišuje mobilní rozhraní. Swift 20/20, Python workflow 13/13, UI simulátoru 1/1, podepsaný build, strict podpis a plná projektová brána 1718/1718 PASS. Build 3 se fyzicky spustil a T049 v syntetickém mobilním rozsahu prošel: bez grantu i po zrušení dialogu 0 %, 0/13 a serveru 0 relací; po grantu 13/13, jeden ověřený objekt/účtenka, 100 663 553 B a shodný SHA-256, na telefonu `Ověřeno na Macu`. Nová syntetická dávka grant nezdědila a při ruční synchronizaci zůstala na 0 %, 0/13, 0/2; serveru nepřibyla relace.
- Registrovaný stop T049 obnovil přesnou původní Serve konfiguraci, vypnul vlastní receiver/cestu a ponechal Funnel vypnutý. Jediný ověřený syntetický důkaz zůstal zachovaný. Camino Audio 0.3.0 (4) zůstává nainstalované a nedotčené.
- T048 prošel na fyzickém iPhonu v dostupném syntetickém rozsahu cizí Wi-Fi. Běžný přenos skončil 13/13 a ověřením; po přerušení Wi-Fi zůstaly klient i server na 2/13 bez objektu a po návratu se bez dalšího stisku doplnily jen chybějící části. S vypnutým tailnetem nevznikla serverová relace ani veřejný fallback; po obnovení Tailscale se bez dalšího stisku dokončila třetí dávka. Finále má 3 ověřené relace, objekty a účtenky, každý 100 663 553 B se shodným SHA-256. Captive portal zůstává NEOVĚŘENO, protože použitá síť jej neměla. Registrovaný stop vypnul receiver i vlastní Serve cestu, přesně obnovil původní Serve a ponechal Funnel vypnutý.
- T050 PASS v syntetickém fyzickém rozsahu na `Camino Transfer Test` 0.4.0 (3): první běh zachytil jen finále a nebyl vyhlášen PASS; druhý oddělený běh má video `Ověřuji` při 100 % a 13/13 současně se serverovým `verifying` a 0 objekty/účtenkami. Teprve potom vznikl jeden hashově ověřený objekt a účtenka o 100 663 553 B a telefon ukázal `Ověřeno na Macu`. Oba běhy jsou potvrzeně zastavené, původní Serve přesně obnovený, Funnel vypnutý a soukromé důkazy zachované mimo Git. Přípravná sada 32/32 a brána 1719/1719 PASS; kód se při fyzickém testu neměnil.
- Při návratu aplikace z Ovládacího centra se čekající mobilně povolená dávka podle Míly spustila bez klepnutí na `Synchronizovat nyní`. Kód volá při aktivaci `reconcile()`, takže je to vysvětlení odpovídající pozorování, ne důkaz absence dotyku z videa. Video také zachytilo krátké `Vyžaduje pozornost` a bezpečný retry před finálním PASS. Následné rozhodnutí a oprava jsou v dalším bodě.
- Míla zvolil vědomý první start nové dávky po mobilním grantu. Build `Camino Transfer Test` 0.4.0 (4) má trvalou bránu v journalu: grant sám, návrat aplikace ani změna sítě nezahájí dosud nespouštěnou dávku; `Synchronizovat nyní`/`Pokračovat` ji autorizuje. Po prvním startu zůstává retry a obnova; bez mobilního grantu zůstává automatická Wi-Fi. Starší journal zachovává obnovu. Na Macu Swift 22/22, simulátorový UI test, nepodepsaný iOS build a plná projektová brána 1719/1719 PASS.
- Mílou schválené p+n dorovnalo vzdálený soví commit se shodným obsahem běžným sloučením bez přepisu historie. Funkční balíček 17 commitů byl pushnut na GitHub po plné bráně 1719/1719. Řízené nasazení `4a965ccb` do Cockpitu má účtenku s novým PID, shodou kódového otisku a smoke 5/5. Závěrečný dokumentační checkpoint a konečný stav `main` se ověřují živým auditem, ne tímto historickým ID.
- Build 0.4.0 (4) byl 19. 9. podepsán místním vývojovým týmem a aktualizací stejného bundle ID nainstalován na připojený iPhone 14 Plus. Přísné ověření podpisu, shoda týmu s buildem 3, platný profil zahrnující iPhone a seznam aplikací s verzí 4 prošly; Camino Audio 0.3.0 (4) zůstává nainstalované. Oddělený podepsaný build 3 na Macu zůstal zachovaný. Cílený postup A/B a výsledek jsou v `camino/tasks/C02b_BUILD4_FIRST_START_FIELD_PLAN.md`.
- Cílený fyzický průchod buildu 4: část A PASS, protože mobilní grant, návrat z Ovládacího centra ani obnova sítě nespustily novou dávku (telefon 0/13, server 0 relací). V části B vědomý start vytvořil jednu relaci, Letový režim zachoval mezistav 1/13 bez finálního objektu a po nuceném ukončení a otevření aplikace s dostupnou sítí přenos bez dalšího klepnutí doběhl. Telefon potvrdil `Ověřeno na Macu`; server jednu ověřenou relaci/objekt/účtenku, 13/13, 100 663 553 B a shodný SHA-256. Otevření aplikace ještě bez sítě neproběhlo, proto úplný PASS B netvrdíme. Míla zvolil neopakovat další mobilní dávku kvůli přerušení spojení s chatem v Letovém režimu a spotřebě dat. Potvrzený stop přesně obnovil původní Serve, vypnul vlastní cestu/receiver a zachoval důkaz; Funnel je vypnutý. Kód se při testu neměnil.
- C03a je referenční doménový kontrakt v `camino/domain/` a `camino/docs/C03a_DOMAIN_CONTRACT.md`: stabilní offline ID Trip/Day/Moment/Asset, append-only metadata a textové revize, přesný čas s původním offsetem, nejistý import a volitelná poloha. Podle U15 vzniká samostatná Úvaha vždy `owner_only`, vložení do deníku vyžaduje vědomou prioritní revizi a kandidáty Vieweru vybírá jen poslední serverem přijatý stav; neznámý nebo konfliktní stav se zavře. Cílené syntetické testy 9/9 a plná brána 1728/1728 PASS. C03a není zatím iPhone/server/Viewer runtime a fyzické akceptační testy nejsou PASS.
- C03b má lokální verzovaný JSON kontrakt `/api/v1/` a soukromé SQLite úložiště pro metadata, manifesty Assetů a append-only revize. Souvislé operace jediného deklarovaného zařízení dostávají trvalé účtenky; shodné bajty jsou idempotentní. Konfliktní kandidát se zachová bez přepisu a blokuje referenční Viewer výběr. Řízená obnova mění epochu a porovnává inventář Momentů bez automatického odblokování. Schéma OpenAPI, 12 syntetických kontraktních testů a plná projektová brána 1740/1740 prošly. Jde o referenční kontrakt bez síťového listeneru a produkční integrace.
- C04a má první samostatnou iPhone aplikaci `camino/app/` s offline Core Data evidencí Trip/Day/Moment, oddělenou Zkouškou, hlavní obrazovkou, časovou značkou a dnešními Momenty. Výchozí režim běžných Momentů je podle D02 `diary`, volba trvá přes restart a nemění staré záznamy. Úvaha vzniká podle U15 vždy `owner_only`; soukromí Komentáře lze během nahrávání změnit pro celý Moment. Přijaté C01c audio jádro se používá přímo bez migrace jeho prototypových dat: trvalý audio záměr vzniká před mikrofonem, ověřené dokončené části se idempotentně navazují po restartu a neznámé soubory zůstávají zachované. Testy 8/8 Swift, 1/1 UI simulátoru a nepodepsaný iOS build prošly. Následná fyzická instalace a průběžná C04b přejímka jsou popsané níže; produkční synchronizace zůstává neověřená.
- C04b T013 fyzicky PASS podle Mílova potvrzení na integrované aplikaci: vědomě tichý klip má trvalý štítek a při odepřeném mikrofonu se běžné video samo nepřepnulo na tiché; tichý klip zůstal dostupný jen po výslovné volbě. Výsledek odpovídá návrhu a nevyžaduje změnu kódu.
- C04b T014 fyzicky PASS podle Mílova potvrzení: zámek telefonu, odchod z aplikace i přijatý krátký hovor ukončily rozběhnuté video bez samovolného pokračování. Zachované klipy byly přehratelné a pravdivě označené jako částečné; hovor se do videa nezaznamenal. Oprava kódu není potřeba.
- C04b T009 fyzicky PASS podle Mílova potvrzení: odmítnutá kamera zobrazila vysvětlení a `Zpět`, zatímco `Komentář` i místní deník dál fungovaly. Oprava kódu není potřeba.
- C04b T060 má bezpečnou fyzickou část PASS podle Mílova potvrzení: při běžném volném místě nebylo falešné varování, krátké video se normálně dokončilo a přehrálo a starší položky zůstaly zachované. Celý T060 zůstává částečný: skutečné nízké místo před/během audia, videa a textu nebylo na hlavním iPhonu vyvoláno.
- C04b low-space/thermal hardening je lokálně hotový: společná injektovatelná politika varuje pod 2 GiB, blokuje nový video Start pod 1 GiB, foto/audio pod 512 MiB a pod rezervou bezpečně dokončí běžící audio/video. Krátká značka se dál pokusí o skutečný zápis; starší originály se nemažou. Video při vážném tepelném stavu varuje a při kritickém nový Start blokuje nebo běžící klip ukončí bez skryté změny kvality. Swift 17/17, UI simulátoru 3/3, nepodepsané simulátorové i generic iOS buildy a plná projektová brána 1740/1740 PASS. Jde o syntetický důkaz; hardening zatím není na iPhonu a celý fyzický T060 zůstává částečný.
- C04d je hotové bez změny Core Data schématu. Deník přidal výběr dne, filtry, detail Momentu, odolný textový koncept, append-only historii revizí s předností lidské úpravy, vědomé uvolnění Úvahy, zamknutí, skrytí/obnovu, přesun kapitoly se zachovaným původním časem a samostatný soukromý doplněk navázaný na rodičovský Moment. Budoucí serverové operace mají trvalé pořadí a stav `čeká na server`; Důležité zůstává lokální, protože C03b v1 pro ně nemá operaci. Swift 22/22, UI simulátoru 4/4, nepodepsaný generic iOS build a plná brána 1740/1740 PASS. Zdroj `e3868100` byl pushnut na `origin/main`; podepsané Camino 0.1.0 (2) prošlo strict kontrolou, aktualizací stejného bundle ID, instalací a spuštěním na iPhonu 14 Plus / iOS 26.6.1 bez ztráty starších C04b dat.
- C05a má lokální produkčně orientovaný serverový checkpoint: přijatý C03b Asset manifest je autorita, FastAPI streamuje nejvýše 8MiB části do soukromého úložiště, SQLite/souborový journal bezpečně obnovuje mezery a stav `verified` vzniká až po serverovém ověření celé délky a SHA-256. Owner tokeny jsou odvolatelné, ukládá se jen jejich hash a správa nemá síťovou cestu. Proces odmítá veřejný bind a smí poslouchat jen na loopbacku. Registrovaný smoke `20260923T205907Z-e64b0346` prošel 12/12 kontrolami přes skutečné loopback HTTP: 1 048 699 B v 5 částech, retry, předčasná blokace finalizace, celý hash, idempotentní finalizace, odvolání obou tokenů a restart se zachovaným `verified`. Core + C03b 23/23, FastAPI 4/4, smoke workflow 4/4 a plná brána 1763/1763 PASS. Serve, Funnel, iPhone, push a nasazení zůstaly beze změny.
- C05b je dokončené v session-owned fyzickém rozsahu integrované aplikace. Zdroj `d4b49b61` byl pushnut, čisté profilové workspaces byly zarovnány, Cockpit řízeně nasazen se smoke 5/5 a podepsané Camino 0.1.0 (3) nainstalováno bez odinstalace. Zachování dat, T051, T047-A/B, dostupná část T048, T049, T050, T052, T053, T058 a pause jsou fyzicky PASS; captive portal T048 zůstává `NEOVĚŘENO`. Konečný redigovaný důkaz má 104 operací, 41 Momentů, 45/45 ověřených médií a 214 555 219 B. Registrovaný stop obnovil původní Serve, zastavil vlastní proces, odvolal token a ponechal Funnel vypnutý. Uzavírací oprava přímého workflow vstupu, portu 8767 a `copy_url` prošla plnou bránou 1770/1770.


## Zdroje a návaznost

- Kořen projektu: `camino/`, instrukce `camino/AGENTS.md`.
- Autoritativní podklady: `camino/CAMINO_podklady_v0.5/README_v0.5.md`,
  `CAMINO_funkcni_specifikace_v0.5.md`, `CAMINO_Codex_v0.5.md`, akceptační
  scénáře a novější `camino/docs/V05_PRIVACY_AMENDMENT.md`.
- Kanonický handoff: `memory/handoffs/workstreams/project-camino.md`.
- Kanonický TVBCP: `memory/tvbcp/workstreams/project-camino.md`.
- Původní balíčky v0.4/v0.5 se nemění; nové auditní a vývojové výsledky patří mimo ně.
- Katalogové přidání samo neotevírá soukromé vlákno. To vznikne až při otevření projektu.

## Pevná pravidla

Originály jsou neměnné, bez automatického mazání. Offline záznam nečeká na síť,
GPS ani AI. `Do deníku` je po doručení serveru způsobilé pro soukromý Viewer
Jany; `Jen pro mě` vylučuje Viewer, všechny filmy a rodinné výstupy. Samostatná
Úvaha začíná vždy `Jen pro mě`. Externí přepis není důkaz zálohy a lidskou
revizi AI nepřepíše.
Po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti
vyhodnotí stav, řekne, zda je potřeba vývoj, a rovnou dá přesné podmínky, postup
a kritéria PASS následujícího neprovedeného testu. Shoda s návrhem sama změnu
kódu nevyvolává; FAIL se nejdřív doloží a opraví v aktuálním rozsahu.

## Rizika a otevřeno

- C01a přijato, ale širší brány G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C01b přijato v prototypovém rozsahu. Vítr a plná integrace T021 v C04 čekají; jeden nevysvětlený nereprodukovaný tichý úsek z prvního T059 zůstává rizikem.
- C01c je přijaté v prototypovém rozsahu po T022/T023. Čtyři fyzicky poslechnuté 55s přechody nevykázaly mezeru ani opakování a dva pády doložily pravdivou obnovu; nejde však o dlouhodobý terénní nebo spotřební test ani o plný databázový T061.
- C02a je přijaté v prototypovém rozsahu po lokálních testech a privátním HTTPS smoke. Smoke byl spuštěn z téhož Macu přes tailnet DNS; nedokládá iPhone, cizí síť, přerušení velkého souboru ani trvalou službu. Standard-library receiver zůstává izolovaný experiment; produkční cíl je FastAPI v samostatném prostředí Camina.
- C02b má fyzický PASS T043, T047 a T050 v syntetickém rozsahu, syntetické mobilní části T049 a tří dostupných síťových podscénářů T048. Captive portal T048 zůstává NEOVĚŘENO; receiver není produkční služba ani záloha skutečných médií.
- Starší C02b T049 harness neměl kameru; integrované C05b T049 s novým skutečným videem je PASS. Serverový počet bajtů není měření spotřeby operátora a retry může přenést více dat.
- T050 prošlo díky souběžnému důkazu telefonu a serveru v 14s okně; soukromé video obsahuje soukromou adresu, proto se necommitovalo. Oprava neočekávaného startu je na iPhonu fyzicky ověřená v části A; offline znovuotevření během části B zůstalo neověřené. Krátké `Vyžaduje pozornost` před dřívějším retry má neznámou příčinu.
- Lokální zámek je v C04a uložený na telefonu, ale server jej vynutí až po přijetí revize; již vydanou cizí kopii neodvolá. C08 musí kontrolovat aktuální oprávnění při každém výdeji média. C04a zatím nemá synchronizaci C05 ani Viewer C08, takže U15 není ověřená provozní ochrana.
- C03b/C05 má fyzický důkaz identity zařízení, odvolatelného tokenu, privátního HTTPS, přijetí a hashové finalizace médií, T053 a T058. C06b stále musí dodat skutečnou druhou kopii a obnovu; porovnání po obnově zatím zahrnuje Momenty, ne celý inventář médií, a T044/T045 nejsou tímto uzavřené.
- Integrovaná C04d je fyzicky přijatá v dostupném lokálním rozsahu a C05b předává podporované revize do C03b API. T038 zůstává jen synteticky doložené bez produkční AI; Viewer části T040/T096 čekají na C08. T007 a plné T060 zůstávají částečné; hlavní iPhone se uměle nezaplňuje ani nezahřívá. Synchronizace není druhá záloha a hvězdička se bez C03b operace stále nesynchronizuje.
- C05b fyzický průchod dokládá zámek, force quit, ztrátu/obnovu tailnetu, mobilní dávku a UX na tomto iPhonu. Nedokládá captive portal, dlouhodobý spravovaný provoz, párování, druhou kopii ani obnovu; session-owned server není C06a služba ani C06b záloha.
- Testovací vzorky mají místní originál a session-owned ověřenou kopii na Macu; nejsou to ostrá média ani záloha. Žádná AI, Viewer export nebo automatické mazání.
- C05b fyzická přejímka proběhla na časově omezeném vývojovém podpisu. U01–U15 se bez nového rozhodnutí neotevírají.

## Další krok

Navázat C05c stavovým UX a potom samostatně rozhodnout o C06a spravované službě a C06b druhé kopii/obnově. Captive portal T048 doplnit jen při bezpečně dostupné síti; T038 až s reálnou opožděnou AI. Session-owned C05b Serve znovu nespouštět bez nového náhledu a potvrzení.

Historický doklad založení:
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

Hotovo:
- Přibližně 30:16 nahrávání v režimu Letadlo, převážně pod zámkem, proběhlo bez problému. Celý záznam se přehrál; T016 je podle uživatelského fyzického testu PASS.
- Přehrávání při zamčené obrazovce neběželo. Background přehrávání není kritériem T016 a nebyla zadána změna rozsahu.

Rozhodnutí a rizika:
- Velikost souboru nebyla sdělena. Verze aplikace, telefon a iOS nebyly v dnešní zprávě znovu čteny; výsledek navazuje na evidovanou instalaci 0.2.0 (2) na iPhone 14 Plus / iOS 26.6.1.
- C01b/G0/G1 zůstávají otevřené. Jediný soubor nepřerušeného úseku není segmentový journal ani garance 60s obnovy; C01c nezahájeno.

Další krok:
- Provést T018 s dostupnými sluchátky, poté T019–T021/T024/T059.

Technický důkaz:
- Uživatelské potvrzení z fyzického telefonu; audio ani soukromý obsah se nekopíroval. Kód beze změn, automatické testy se neopakovaly.

### 2026-09-16 19:46 CEST — T018 PASS, T019 dílčí důkaz

Hotovo:
- T018 PASS podle Míly: AirPods zobrazené jako aktivní mikrofon, několikaminutové záznamy ve stoje i za chůze pod zámkem, bez výpadků a celý poslech OK. Vítr nebyl přítomen.
- Snímek a živá technická metadata opravují T016 na 30:24,406 a 175 147 072 B; 48 kHz mono, dokončeno bez přerušení.
- Odchozí hovor uzavřel první část po 3:08,56 jako přerušenou. Pokračovat vytvořilo nový samostatný soubor 4:53,57 ve stejné session s pauzou 2:25,13. Grafické seskupení je očekávané, soubory se fyzicky neslepily.
- Pozdější záznam mikrofonem iPhonu byl samostatná nová session. Podle Míly byl v kapse výrazně tišší a méně kvalitní.

Rozhodnutí a rizika:
- T019 má jen dílčí důkaz odchozím hovorem; příchozí hovor jednou ignorovat a jednou přijmout čeká. Obsah audia nebyl nástrojem poslouchán.
- T020 nebyl proveden: není doloženo odpojení a opětovné připojení aktivního mikrofonu během běžícího záznamu. C01b/G0/G1 zůstávají otevřené, C01c nezahájeno.

Další krok:
- Dokončit T019, potom T020–T021/T024/T059.

Technický důkaz:
- Připojený iPhone 14 Plus, Camino Audio 0.2.0 (2); CoreDevice inventář a pouze technické `started.json`/`completed.json`. Žádný CAF se nekopíroval ani neposlouchal. Kód beze změn.

### 2026-09-16 20:02 CEST — Automatický návod k dalšímu testu

Rozhodnutí:
- Po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí PASS/FAIL/BLOCKED či dílčí stav, výslovně řekne, zda je potřeba vývoj, a rovnou přidá podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu.
- Pokud chování odpovídá návrhu, další vývoj se jen kvůli dokončenému testu nezahajuje. Při FAIL se nejdřív zachytí přesný projev, potom se opraví C01b a zopakuje dotčený scénář. C01c zůstává mimo rozsah.

Další krok:
- Dokončit T019 příchozím běžným telefonním hovorem jednou ignorovaným a jednou přijatým; potom automaticky předat postup T020.

Ověření:
- Jde pouze o projektové pracovní pravidlo; kód aplikace ani soukromá data se nemění.

### 2026-09-16 20:25 CEST — T019 PASS

Hotovo / důkaz:
- Míla potvrdil PASS ignorovaného i přijatého příchozího hovoru: obě části přehratelné, nic z hovoru v audu a žádné samovolné pokračování.
- Technická metadata potvrzují dvě přerušené první části 44,410 s a 26,798 s a jejich samostatná vědomá pokračování stejné session 21,551 s a 20,999 s, s pauzami 43,153 s a 112,272 s. Všechny jsou 48 kHz mono.
- Jeden dřívější běžně dokončený záznam bez přerušení a continuation byl od T019 oddělen. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- Chování odpovídá návrhu C01b, oprava ani nový build nejsou potřeba. Poslech a nepřítomnost hovoru potvrzuje člověk; nástroj ověřil jen technická metadata.
- T020–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T020 změnou skutečně aktivního vstupu během běžícího záznamu; potom automaticky předat T021.

### 2026-09-16 20:39 CEST — T020 PASS

Hotovo / důkaz:
- Odpojení aktivních AirPods přerušilo záznam; první část i všechny navazující části jsou podle Míly přehratelné. Pokračování použilo mikrofon iPhonu, nic se samo neobnovilo a AirPods se staly aktivním vstupem až při dalším vědomém spuštění.
- Metadata potvrzují tři samostatné části jedné session: 34,776 s přerušená, 25,944 s navazující a znovu přerušená, 18,215 s navazující a řádně dokončená; pauzy 28,002 s a 90,312 s, 48 kHz mono.

Rozhodnutí a rizika:
- T020 PASS. Bluetooth připojení není důkaz aktivního vstupu; AirPods se skutečnou route staly až po vědomé reaktivaci audio session. Oprava ani nový build nejsou potřeba.
- T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno. Žádný CAF se nekopíroval ani neposlouchal.

Další krok:
- Provést T021 v prototypovém rozsahu: za běžící Úvahy ověřit zákaz přehrávače a druhého recorderu a návrat z jiné aplikace bez zrušení záznamu. Video/Moment patří až do C04.

### 2026-09-16 21:27 CEST — T021 PASS v rozsahu C01b prototypu

Hotovo / důkaz:
- Míla potvrdil neaktivní volbu typu i přehrávání, nemožnost spustit druhý recorder, pokračování stejné Úvahy po návratu z jiné aplikace, růst času a celý poslech jedné nepřerušené části.
- Metadata poslední Úvahy: 56,350 s, 5 413 696 B, 48 kHz mono, `interrupted=false`, bez continuation. Dřívější samostatná Úvaha 31,717 s byla oddělena jako přípravný pokus.

Rozhodnutí a rizika:
- T021 PASS pouze v rozsahu C01b prototypu. Video/Moment se musí znovu prověřit po integraci v C04. Oprava ani nový build nejsou potřeba.
- T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno. Žádný CAF se nekopíroval ani neposlouchal.

Další krok:
- Provést T024, potom automaticky předat T059.

### 2026-09-16 21:43 CEST — Přijetí v0.5 a U15

Hotovo / důkaz:
- Původní balíček v0.5 byl importován beze změny; 6/6 položek interního manifestu odpovídá velikostí i SHA-256 a lokální ZIP je přesná kopie Downloads.
- Vznikl závazný U15 dodatek a read-only Viewer readiness audit. Živě ověřeno: Tailscale online, soukromý Serve bez Funnel, Cockpit smoke 5/5, AC bez systémového spánku, FileVault zapnutý.

Rozhodnutí a rizika:
- `Do deníku` je při zapnutém Vieweru po synchronizaci dostupné Janě celé. Samostatná Úvaha vzniká `Jen pro mě` a do deníku se vloží jen vědomou akcí. Původní v0.5 se kvůli manifestu nepřepisuje; rozpor řeší novější dodatek.
- Viewer ani jeho data/služby nebyly vytvořeny. U15 se implementuje v C03/C04, Viewer v C08c–C08f; C01b se tím nerozšiřuje ani nepřebuildovává. G8 zůstává NEPROVEDENO.

Další krok:
- Dokončit T024, potom T059; C01c nezahajovat před uzavřením C01b.

### 2026-09-16 21:48 CEST — Oprava profilového převzetí v0.5

Hotovo / důkaz:
- Whitespace preflight Human–Adam workspace nyní při fast-forwardu používá `.gitattributes` z `FETCH_HEAD`. Nový regresní test pokrývá atribut a importovaný Markdown v témže commitu; 192 souvisejících testů a rychlá kontrolní brána prošly.

Rozhodnutí a rizika:
- Ostatní ochrany synchronizace se nemění. Oprava neignoruje whitespace globálně, nemění remote a nepovoluje merge/divergenci.

Další krok:
- Po lokálním commitu bezpečně zopakovat dorovnání čistých profilů; věcný krok Camina zůstává T024.

### 2026-09-16 22:41 CEST — T024 PASS

Hotovo / důkaz:
- Po nuceném ukončení aplikace za rozpracované Úvahy Míla potvrdil očekávaný relaunch. Snímek ukazuje `Připraveno` 00:00, žádný automatický recorder, jednu neověřenou položku a dostupné přehrání zachovaných částí.
- Metadata potvrzují zachovanou dokončenou session 25,093 s + continuation 2,254 s a novější samostatný pokus s `started.json`, ale bez `completed.json`. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- T024 PASS; oprava ani nový build nejsou potřeba. Pád nastal v nové samostatné Úvaze, ne v continuation, ale kanonická kritéria T024 jsou splněná.
- Otevřený CAF není označený za zachráněný; C01c segmentace, journal a omezená ztráta zůstávají mimo tento důkaz. T059, C01b/G0/G1 zůstávají otevřené.

Další krok:
- Provést T059; C01c nezahajovat před uzavřením C01b.

### 2026-09-16 23:09 CEST — první T059: ochrana PASS, audio FAIL

Hotovo / důkaz:
- Před prvním odemknutím po restartu byl iPhone pro vývojové služby `unavailable`; soubory se nečetly. Po odemknutí Camino zůstalo `Připraveno 00:00`, nic samo nenahrávalo, počet neúplných položek zůstal 1 a testovací soubor byl přehratelný.
- Míla během zámku mluvil, ale v poslechu byl hlas slyšet jen před zámkem a po odemčení. Účtenka přitom ukazuje jediný dokončený Komentář 53,567 s, 5 146 528 B, 48 kHz mono, bez přerušení. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

Rozhodnutí a rizika:
- T059 je v prvním pokusu FAIL v audio části; ochrana/restart jsou PASS. Souvislá délka dokládá zápis rámců, nikoli slyšitelný signál. Příčina zůstává neurčená.
- Dřívější T016 pod zámkem prošel, proto se před řízenou reprodukcí nemění kód ani build. Token a fronta v C01b nejsou implementované. C01b/G0/G1 zůstávají otevřené, C01c nezahájeno.

Další krok:
- Zopakovat pouze audio část T059 s potvrzeným Mikrofonem iPhonu a přesnými značkami; při opakovaném FAIL zahájit diagnostiku a opravu C01b.

### 2026-09-16 23:21 CEST — T059 PASS po opakování; C01b přijato

Hotovo / důkaz:
- Řízené opakování zachytilo před zámkem, všechny tři značky pod zámkem i po odemčení; jedna nepřerušená část a nic nečekaného podle Míly.
- Metadata potvrzují dokončený Komentář 107,801 s, 10 352 992 B, 48 kHz mono, bez přerušení/continuation. Audio se nekopírovalo ani neposlouchalo nástrojem. Název vstupu nebyl ve výsledné odpovědi zopakován.

Rozhodnutí a rizika:
- T059 PASS po řízeném zopakování a C01b přijato v prototypovém rozsahu; vývoj ani nový build nejsou potřeba. První tichý úsek se nezopakoval, ale zůstává evidovaný jako nevysvětlené pozorování.
- C01c, G0/G1, ostrá terénní připravenost a plná integrace T021 v C04 nejsou tímto uzavřené. C01c se bez nového výslovného pokynu nezahajuje.

Další krok:
- Vyčkat na výslovný pokyn k C01c. Po jeho implementaci bude prvním fyzickým scénářem T022; současný build 0.2.0 pro něj není určen.

### 2026-09-17 07:59 CEST — C01c zahájeno, 0.3.0 nainstalováno

Hotovo / důkaz:
- C01c 0.3.0 (3) přidává jeden nepřerušený input tap, 55s segmenty, journal, obnovu platných částí a pravdivé označení chybějícího konce. Staré C01a/C01b soubory se nemigrují.
- 52/52 Swift testů, 2/2 UI testy dvou 15s částí, podepsaný build a strict podpis PASS. První UI pokus zabil runner před bootstrapem; po čistém restartu simulátoru opakování prošlo.
- Instalace a spuštění na iPhone PASS bez odinstalace. Technický inventář před/po: 111 položek, 28 zahájených, 27 dokončených a 28 legacy CAF; shodný hash cest, velikostí a typu. Audio se nekopírovalo ani neposlouchalo.
- Plná projektová brána PASS, 1685/1685 testů. První průchod měl jediné časovací selhání nesouvisejícího Human–Adam worker testu; cílené opakování 1/1 a následný celý průchod prošly.

Rozhodnutí a rizika:
- Automatické testy nepředstavují fyzický PASS T022/T023. Nový `AVAudioEngine` musí na telefonu znovu doložit route, background běh, kontinuitu a absenci opakování na hranici částí.
- Obnovený otevřený CAF se vždy označuje jako částečný s možným chybějícím koncem. Plný databázový T061 se vrátí v C05a.

Další krok:
- T022 na 0.3.0: nejméně 2:15 neutrálního souvislého zvuku se značkami, nucené ukončení během otevřené části, relaunch bez mikrofonu a celý poslech zachovaného rozsahu. Potom T023.

### 2026-09-17 11:32 CEST — Oprava pádu C01c při Start

Hotovo / důkaz:
- Pět shodných crash reportů určilo příčinu: tap callback zdědil `MainActor` a Swift 6 ho na real-time audio frontě ukončil přes `_swift_task_checkIsolatedSwift`.
- Build 0.3.0 (4) vytváří callback v `nonisolated` helperu. 52/52 Swift testů, 2/2 UI testy, oba arm64 buildy, strict podpis a rychlá statická brána PASS.
- Instalace a launch přes stávající aplikaci PASS. Všech 136 položek před instalací zůstalo shodných; nic se nemazalo, nekopírovalo ani neposlouchalo.

Rozhodnutí a rizika:
- Kontroly Swift 6 se nevypínají. Pět nedokončených pokusů z pádů zůstává zachováno.
- Automatické ověření nenahrazuje skutečný mikrofon; C01c a T022 zůstávají otevřené do krátkého fyzického smoke.

Další krok:
- Na buildu 4 provést 10–15s neutrální Start/Stop, potvrdit růst času/ukazatele a celý poslech. Při PASS pokračovat T022; při FAIL znovu netestovat a získat nový crash report.

### 2026-09-17 11:46 CEST — Krátký fyzický smoke buildu 4 PASS

Hotovo / důkaz:
- Míla potvrdil všechny tři požadované body: aplikace při Start nespadla, čas i ukazatel rostly a po Stop šel nový záznam přehrát.
- Technická účtenka potvrzuje jeden normálně dokončený Komentář 10,7 s, 2 058 496 B, 48 kHz mono, jeden segment, `interrupted=false`, `recovered=false` a bez mezery před segmentem.
- Všech 136 předchozích položek zůstalo shodných v cestě, typu a velikosti; přibylo sedm očekávaných položek nového dokončeného pokusu. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

Rozhodnutí a rizika:
- Oprava okamžitého pádu je fyzicky potvrzená; další vývoj před T022 není potřeba.
- Tento krátký smoke není T022 ani přijetí C01c. Obnova po nuceném ukončení a kontinuita segmentů zůstávají otevřené do T022/T023.

Další krok:
- Provést první průchod T022 na 0.3.0 (4), potom podle výsledku předat opakování v jiné fázi otevřeného segmentu nebo opravu.

### 2026-09-17 13:12 CEST — T022/T023 PASS; C01c přijato

Hotovo / důkaz:
- T022 prošlo ve dvou odlišných fázích otevřené části. Po obou nucených ukončeních se mikrofon sám nespustil, aplikace nabídla pravdivě označenou obnovenou částečnou nahrávku a celý zachovaný rozsah byl podle Míly přehratelný.
- Snímek prvního průchodu ukazuje `Připraveno 00:00`, tři obnovitelné části a 02:18 zachovaného přehratelného rozsahu. Druhý průchod splnil stejná kritéria při pozdějším pádu v otevřené části.
- T023 prošlo souvislým nejméně čtyřminutovým testem. Značky před a po čtyřech 55s hranicích byly podle Míly slyšet jednou, ve správném pořadí, bez opakování, nevysvětlené mezery a useknutí.

Rozhodnutí a rizika:
- C01c 0.3.0 (4) je přijato v prototypovém rozsahu. Další oprava ani nový build nejsou potřeba.
- Tento výsledek není G0/G1/G8, dlouhodobý terénní ani spotřební test. Plný databázový a serverový T061 zůstává C05a.

Další krok:
- Vyčkat na výslovný pokyn k C02a; C01c dále nerozšiřovat.

### 2026-09-17 14:11 CEST — C02a lokální syntetický přijímač

Hotovo:
- Vznikl minimální loopback přijímač syntetického souboru s bearer tokenem, proudovým zápisem, serverovým SHA-256 a create-only objektem i účtenkou.
- Shodný retry nevytvoří duplicitu; rozdílná data pod stejným ID jsou konflikt bez přepsání.

Rozhodnutí:
- C02a zůstává izolovaný standard-library prototyp bez nové závislosti ve sdíleném prostředí Samanthy. Produkční cíl F51 zůstává FastAPI v samostatném prostředí Camina.

Další krok:
- Po checkpointu samostatně autorizovat syntetický smoke přes soukromé HTTPS za Tailscale Serve.

Navrhované další kroky:
- Ověřit správný upload, chybný hash, identický retry a nepřítomnost Funnel či veřejné cesty. T043/T048/T051 ponechat otevřené pro klientskou frontu a navazující etapy.

Technický důkaz:
- `tests.test_camino_receiver` 10/10 PASS. Lokální HTTP pouze v dočasném adresáři; služba nebyla nasazena, Tailscale se neměnil a žádné reálné médium ani skutečný token se nepoužil.

### 2026-09-17 15:19 CEST — C02a privátní HTTPS smoke PASS

Hotovo:
- Dočasná soukromá HTTPS cesta Tailscale Serve předala syntetický soubor loopback přijímači. Server potvrdil vlastní délku a SHA-256, vytvořil právě jeden objekt a jednu účtenku; identický retry neduplikoval a chybné či konfliktní údaje nic nepřepsaly.
- Kořen Cockpitu zůstal dostupný, Funnel nebyl aktivní a po testu byla původní Serve konfigurace přesně obnovena. C02a je dokončené v prototypovém rozsahu.

Rozhodnutí:
- Žádné nové architektonické rozhodnutí. C02a zůstává izolovaný standard-library experiment; produkční cíl zůstává FastAPI v samostatném prostředí Camina.

Další krok:
- Vyčkat na výslovný pokyn k C02b.

Navrhované další kroky:
- V C02b ověřit velký soubor, souborové části, přerušení a chování iOS na cizí síti bez veřejného endpointu. T043/T048/T051 zatím neoznačovat za PASS.

Technický důkaz:
- Přes tailnet HTTPS: health 200; první upload 201; identický retry 200 s `created=false`; chybný hash 422; konflikt 409; úložiště 1 objekt + 1 účtenka se shodným hashem. Cockpit health 200, pouze tailnet, Serve stav po testu shodný s výchozím.

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

### 2026-09-19 23:25 CEST — C03a datový kontrakt a soukromí

Hotovo:
- Čistý referenční model stabilních offline ID Trip/Day/Moment/Asset,
  metadatových a textových revizí, časové provenience a polohy. U15 vynucuje
  soukromý vznik Úvahy a explicitní revizi pro vložení do deníku.
- Výběr Viewer kandidátů vychází jen z poslední serverem přijaté revize;
  neznámá či konfliktní politika se zavře a vynechané položky se nepočítají.

Rozhodnutí:
- Model zůstává oddělený od C01/C02 prototypů. C03a neprokazuje skutečné
  iPhone UI, serverovou persistenci, mediální endpoint ani fyzické T096.

Další krok:
- C03b verzované API, serializace, serverové potvrzení a konflikty.

Technický důkaz:
- Devět syntetických testů C03a a plná projektová brána 1728/1728 PASS.

### 2026-09-20 08:52 CEST — C03b lokální owner API a SQLite revize

Hotovo:
- Přesný JSON kontrakt v1, OpenAPI a referenční SQLite ukládají souvislé
  operace, metadata, manifesty, textové i metadatové revize a trvalé účtenky.
  Opakování shodných bajtů je idempotentní, konflikty jsou zachované a blokují
  výstupy. Po řízené změně epochy se jen porovná inventář Momentů.

Rozhodnutí:
- Míla zadal zkusit verzované API a ukládání revizí. Lokální kontrakt nemá
  síťový listener ani nepřepisuje izolované C01/C02 prototypy.

Další krok:
- Po samostatném zadání C04a napojit místní úložiště a hlavní obrazovku.

Navrhované další kroky:
- C05a/C06b zajistí produkční privátní server, skutečná média a obnovu;
  C08 ověří vynucení soukromí. T048 a plné T049 zůstávají oddělené.

Technický důkaz:
- 12/12 syntetických kontraktních testů, validní OpenAPI a plná projektová
  brána 1740/1740 PASS. Bez push, nasazení a iPhone instalace.

### 2026-09-20 09:30 CEST — C04a místní aplikace a propojení audia

Hotovo:
- Nový `camino/app/` bundle s Core Data Trip/Day/Moment, offline přípravou
  cesty, Zkouškou, časovou značkou a hlavní obrazovkou. D02 výchozí `diary`,
  perzistentní volba a neměnnost starých Momentů; U15 samostatná Úvaha
  `owner_only`. Komentář umožní změnit soukromí celého nahrávaného Momentu.
- Přijaté C01c audio jádro zůstalo beze změny. Záměr s ID cesty a soukromím
  se ukládá před mikrofonem; jen validovaná dokončená session se naváže na
  Moment. Restart vazbu doplní idempotentně, neznámá média se nemažou.

Rozhodnutí:
- Míla zadal pokračování C04a. Samostatné bundle ID a kontejner brání
  neřízené migraci prototypových dat. C03b síťové API se v této etapě
  nepředstírá jako připojené.

Další krok:
- C04b foto/video; před přijetím C04a fyzicky ověřit mikrofon, zámek,
  přerušení, obnovení a soukromí nové aplikace na iPhonu.

Technický důkaz:
- Swift 8/8, izolovaný UI test iPhone 14 Plus simulátoru 1/1,
  nepodepsaný generic iOS build PASS, plná projektová brána 1740/1740 PASS.
- Bez podepsané instalace na iPhone, push, nasazení a druhé zálohy.

### 2026-09-20 10:00 CEST — C04b foto a video

Hotovo:
- Kamera ukládá samostatné foto/video i výslovné přílohy k přesnému Momentu.
  Komentář ze záběru nebo detailu dědí jeho soukromí. Originály se automaticky
  nemažou; dokončené soubory se ověřují a známé záměry po restartu navazují.
- Video podporuje vědomě tichý režim, orientaci a označení částečného klipu.

Rozhodnutí:
- C04b zůstává místní offline etapou. Pro nové bundle ID chybí provisioning
  profil a Xcode účet; stará identita prototypu se kvůli jeho datům nepoužije.

Další krok:
- Zajistit podpis nového bundle ID, nainstalovat do iPhonu a fyzicky projít
  T007–T014/T060 na nové zkušební cestě.

Navrhované další kroky:
- C04d detail/revize a C05a produkční server. T048 odděleně na cizí Wi-Fi;
  plné T049 až s novým skutečným videem přeneseným integrovanou aplikací.

Technický důkaz:
- Swift 13/13, simulátorový UI test a plná brána 1740/1740 PASS; nepodepsaný
  iOS build PASS. Podepsané
  sestavení selhalo na chybějícím profilu. Instalace, fyzické testy, push a
  nasazení NEPROVEDENY.

### 2026-09-20 12:12 CEST — C04b podepsaná instalace

Hotovo:
- Nový integrovaný Camino bundle 0.1.0 (1) je vývojově podepsaný, ověřený,
  nainstalovaný a spuštěný na připojeném iPhonu 14 Plus. Starší Camino
  prototypy se nenahrazovaly.

Rozhodnutí:
- Fyzické T007–T014/T060 se hodnotí až po pozorování kamery, uložených
  souborů, přehrání, orientace a přerušení na telefonu. Spuštěný proces není
  důkaz jejich PASS.

Další krok:
- Na nové Zkoušce projít cílený test v `C04b_IPHONE_TEST_PLAN.md` a zapsat
  skutečné výsledky jednotlivých scénářů.

Navrhované další kroky:
- Po C04b QA navázat C04d a C05a; plné T049 až po skutečném přenosu videa.

Technický důkaz:
- `codesign --verify --deep --strict` PASS, profil má přesné bundle ID a
  připojený iPhone; instalace i launch `devicectl` PASS, proces běžel.
  Profil vyprší 27. 9. 2026. Fyzické scénáře jsou zatím NEOVĚŘENÉ; bez push.

### 2026-09-20 12:27 CEST — C04b první fyzická fotografie

Hotovo:
- Na iPhonu byla fotografie potvrzena jako místně uložená a zůstala v detailu
  Momentu po úplném zavření a opětovném otevření aplikace.

Rozhodnutí:
- Jde o fyzický důkaz úspěšného zápisu a restartu, nikoli celý T007:
  chybu dokončení zápisu jsme na zařízení nevyvolali.

Další krok:
- T008: dvě rychlé samostatné fotografie, pak komentář a další foto výslovně
  připojené k prvnímu Momentu.

Navrhované další kroky:
- Následně T011–T014 skutečné video a T009 odmítnutá kamera; T060 nízké
  místo bez nebezpečného zaplňování telefonu jen v bezpečném rozsahu.

Technický důkaz:
- Mílovo pozorování hlášky a snímku po restartu, na Macu nový proces aplikace.
  Obsah fotografie nebyl kopírován ani zapisován.

### 2026-09-20 — C04b T008 průběžný fyzický výsledek

Hotovo:
- Dva rychlé snímky se na iPhonu zobrazily jako dva samostatné řádky
  Fotografie. Míla potvrdil komentář u prvního z nich.

Rozhodnutí:
- Jde o dílčí fyzické ověření T008. Vazba další fotografie k prvnímu
  Momentu a trvalost po restartu dosud nejsou potvrzené.

Další krok:
- Přidat fotografii výslovně z detailu prvního Momentu, ověřit obě vazby
  a zopakovat kontrolu po úplném zavření a spuštění aplikace.

Navrhované další kroky:
- T011–T014 skutečné video, potom další bezpečné scénáře plánu.

Technický důkaz:
- Přímé pozorování Míly na fyzickém iPhonu, bez kopie médií nebo komentáře.

### 2026-09-20 — C04b T008 fyzicky PASS

Hotovo:
- Míla dokončil přidání další fotografie k prvnímu Momentu a potvrdil
  všechny vazby po úplném zavření a opětovném otevření aplikace. První Moment
  má dvě fotografie a komentář, druhý svou jedinou fotografii.

Rozhodnutí:
- T008 má fyzický PASS podle uživatelského pozorování na iPhonu 14 Plus.
  Předchozí průběžný zápis zůstává historií testu.

Další krok:
- T011: krátké skutečné video se zvukem, Stop, opětovné spuštění a ověření
  jediné položky, obrazu, zvuku a délky.

Navrhované další kroky:
- T012–T014, T009 a bezpečná část T060; poté C04d/C05a.

Technický důkaz:
- Mílovo potvrzení na fyzickém iPhonu, bez kopie fotografií nebo komentáře.
  Kontrolní brána 1740/1740 PASS. T007 chybový zápis zůstává neověřený na
  zařízení; bez push a nasazení.

### 2026-09-20 — C04b T011 fyzický výsledek

Hotovo:
- Míla potvrdil, že video po návratu funguje podle očekávání: přehrává obraz
  a zvuk, bez duplicit. Délku vidí v ovládání během přehrávání.

Rozhodnutí:
- T011 fyzicky PASS podle Mílova pozorování. Trvale zobrazená délka v
  detailu není požadavkem kanonického T011; její absence je drobná poznámka
  k UI. Aplikaci kvůli tomu nepřeinstalovávat.

Další krok:
- T012: krátké video na výšku a na šířku, přehrát obě po restartu a ověřit
  orientaci a ořez.

Navrhované další kroky:
- T013–T014, T009, bezpečná část T060; potom C04d/C05a.

Technický důkaz:
- Uživatelské pozorování na fyzickém iPhonu; kanonický T011 požaduje
  správný čas a zvuk, přehratelnost a bez duplicit. Bez kopie klipu, push
  a nasazení.

### 2026-09-20 — C04b T012 fyzický PASS

Hotovo:
- Míla potvrdil, že klipy na výšku i na šířku se po restartu aplikace
  přehrávají se správnou orientací a bez chybného ořezu.

Rozhodnutí:
- T012 fyzicky PASS podle Mílova potvrzení na iPhonu 14 Plus.

Další krok:
- T013: nejprve vědomé video bez zvuku s trvalým štítkem, potom odepření
  mikrofonu bez skrytého přepnutí běžného videa na tiché.

Navrhované další kroky:
- T014, T009 a bezpečná část T060; potom C04d/C05a.

Technický důkaz:
- Uživatelské pozorování po restartu, bez kopie klipů. Bez push a nasazení.

### 2026-09-20 — C04b T013 první fyzická část

Hotovo:
- Míla potvrdil vědomě zvolené tiché video a štítek Bez zvuku před Start,
  během záznamu i v detailu po restartu.

Rozhodnutí:
- T013 zatím částečný. Zbývá fyzicky ověřit, že při odepřeném mikrofonu
  běžné video nezačne tajně bez zvuku a tichý klip vyžaduje výslovnou volbu.

Další krok:
- Odepřít mikrofon v nastavení telefonu, znovu otevřít Camino a provést
  obě větve T013 bez mazání uložených médií.

Navrhované další kroky:
- T014, T009 a bezpečná část T060; potom C04d/C05a.

Technický důkaz:
- Mílovo pozorování na fyzickém iPhonu; bez kopie média a bez push.

### 2026-09-21 08:28 CEST — Dávkové p+n a čistý návratový bod

Hotovo:
- Všechny dokončené místní Camino commity od C03a přes C04b a zaznamenané
  fyzické výsledky do první části T013 byly připraveny a odeslány jako jeden
  kontrolovaný GitHub balíček. Ekvivalentní produkční soví změna byla zachována
  běžným merge; historie se nerebasovala ani nepřepisovala.
- Poslední ruční volba týmu v CaminoAudioUITests byla převedena na dědění
  ignorovaného `LocalSigning.xcconfig`. Lokální tým zůstává funkční, ale jeho
  identifikátor není ve sledovaném Xcode projektu.
- Human–Adam i Knihovna byly před synchronizací ověřené jako čisté, bez remote,
  na `main`, bez aktivního tahu a bez nejistého doručení. Po p+n jsou oba
  profily i zdrojový main zarovnané a Cockpit je řízeně nasazený na stejný head.

Rozhodnutí:
- Mílův pokyn „vše p+n, vyčistit repo pro možnost vývoje z Human-Adam“ zahrnul
  dávkový push, bezpečný fast-forward obou profilů a simple-main nasazení.
  Neznamenal mazání pracovních dat ani přepsání historie.
- Fyzická akceptace se nemění: T008, T011 a T012 jsou PASS; T007 a T013 jsou
  částečné. T009, T014, T060, T048 a plné T049 zůstávají otevřené.

Další krok:
- Z čistého Camino proudu v Human–Adam dokončit odepřený mikrofon v T013,
  potom T014, T009 a bezpečnou část T060. Následně C04d a C05a.

Technický důkaz:
- `plutil` ověřil projekt; `xcodebuild -showBuildSettings` pro UI test target
  potvrdil načtenou místní podpisovou hodnotu bez jejího výpisu. Plná projektová
  brána 1740/1740 PASS.
- GitHub batch receipt a simple-main deployment receipt jsou autoritou pro
  finální head, nový PID, kódový otisk a Cockpit smoke 5/5.

### 2026-09-21 20:46 CEST — T048 na cizí Wi-Fi a bezpečný stop

Hotovo:
- Na fyzickém iPhonu a skutečně jiné Wi-Fi prošel běžný soukromý přenos jedné
  nové syntetické dávky do ověřeného finále 13/13.
- Druhá dávka při vypnutí Wi-Fi zůstala současně na klientu i serveru 2/13 bez
  objektu či účtenky. Po návratu stejné Wi-Fi se bez dalšího stisku doplnily
  jen chybějící části a vznikl jediný další ověřený objekt a účtenka.
- Třetí dávka s vypnutým tailnetem nevytvořila serverovou relaci ani veřejnou
  náhradní cestu. Po obnovení Tailscale se bez dalšího stisku dokončila.
- Registrovaný stop odebral vlastní testovací cestu, ukončil receiver, přesně
  obnovil původní Serve a ponechal Funnel vypnutý.

Rozhodnutí:
- T048 má PASS v dostupném syntetickém rozsahu běžné cizí Wi-Fi, přerušení a
  návratu sítě a nedostupného/obnoveného tailnetu. Captive portal zůstává
  NEOVĚŘENO, protože použitá síť jej neměla; celý T048 proto není bez omezení
  označený za úplný PASS.
- Důkaz patří syntetickému receiveru a testovací aplikaci, nikoli produkčnímu
  serveru, záloze skutečných médií nebo Vieweru.

Další krok:
- Dokončit T013 s odepřeným mikrofonem, potom T014, T009 a bezpečnou část T060;
  následně C04d a C05a.

Technický důkaz:
- Finální audit: T048 zastavený, receiver/cesta neaktivní, Funnel vypnutý,
  3/3 relace ověřené, 39/39 částí, 3 objekty, 3 účtenky, 301 990 659 B a
  shodný hash. Kód se při testu neměnil a automatické testy se neopakovaly.

### 2026-09-21 21:15 CEST — C04b T013 fyzický PASS

Hotovo:
- Míla po dvouvětvém fyzickém postupu potvrdil T013 jako odpovídající
  předpokladu: při odepřeném mikrofonu se běžné video samo nepřepnulo na tiché
  a výslovně zvolený tichý klip zůstal dostupný a označený.

Rozhodnutí:
- T013 je fyzicky PASS. Pozorování odpovídá navrženému chování; oprava kódu
  není potřeba.
- T048 se znovu neotevírá: tři dostupné podscénáře jsou hotové, pouze captive
  portal zůstává NEOVĚŘENO do přirozeně vhodné sítě.

Další krok:
- T014: během krátkého videa odejít z aplikace nebo zamknout telefon a po
  návratu ověřit použitelný dokončený klip, nebo pravdivě částečný stav bez
  tvrzení, že kamera stále nahrává.

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

- C03b přijatý manifest Assetu je autorita uploadu. Nový FastAPI adaptér přidal
  autentizované upload session, stav, stream částí a finalizaci; veřejný bind
  odmítá a síťová správa tokenů neexistuje.
- Mediální SQLite/souborový journal je idempotentní, ověřuje délku i SHA-256,
  po pádu uzavírá validní části/objekt a neznámé bajty zachovává v karanténě.
  Poškozený hotový objekt okamžitě zruší stav `verified`.
- Cílený důkaz: core + C03b 23/23, FastAPI 4/4, validní OpenAPI a odmítnutí
  `0.0.0.0`. Plná projektová brána 1751/1751 PASS.

Rizika:
- Jde o lokální kódový checkpoint bez skutečných privátních dat, tokenu,
  spuštěné služby, Tailscale Serve, iPhone klienta, push a nasazení. T052 a
  T061 jsou syntetické; nejde o fyzické zaplnění disku ani řízený pád služby.

Další krok:
- Samostatně připravit privátní cesty/token a loopback smoke nad syntetickými
  daty. Potom lze zvlášť rozhodnout o privátním Serve a C05b.

### 2026-09-23 22:45 CEST — C05a registrovaný loopback smoke připraven

- Přidán jednorázový potvrzovaný workflow pouze pro `127.0.0.1`. Vytvoří nový
  zachovaný syntetický běh mimo repozitář, dva náhodné hashované tokeny a
  redigovanou privátní účtenku; ověřuje metadata, části, retry, blokaci časné
  finalizace, celý hash, opakovanou finalizaci, odvolání a restart.
- Workflow nemění Serve ani Funnel, nepřipojuje iPhone, nepushuje a nenasazuje.
  Samotný smoke zatím nebyl spuštěn; čeká na náhled přesného příkazu a nové
  samostatné potvrzení podle registru schopností.
- Bezpečnostní a registrační testy 4/4, společná cílená sada 30/30 a plná
  projektová brána 1763/1763 PASS. Oddělené C05a prostředí načte serverové
  závislosti.

### 2026-09-23 22:59 CEST — C05a loopback smoke PASS

- Míla samostatně potvrdil uložený registrovaný příkaz. Běh
  `20260923T205907Z-e64b0346` prošel 12/12 kontrolami přes skutečné HTTP na
  `127.0.0.1`: 1 048 699 B v 5 částech, autorizace, C03b metadata,
  idempotentní retry, blokace časné finalizace, serverový hash, opakovaná
  finalizace, odvolání obou tokenů a restart se zachovaným `verified` stavem.
- Vlastněný proces skončil. Syntetická data a redigovaná privátní účtenka jsou
  zachované; Serve, Funnel, iPhone, push ani nasazení se nezměnily.
- Další krok vyžaduje nové samostatné rozhodnutí o privátním Tailscale Serve;
  C05b iPhone klient následuje odděleně. Smoke není produkční přenos ani záloha.

### 2026-09-24 22:47 CEST — C05b fyzické přijetí a bezpečný stop

Hotovo:
- Podepsané Camino 0.1.0 (3) zachovalo starší data a fyzicky prošlo T051,
  T047-A/B, dostupnou část T048, T049, T050, T052, T053, T058 a trvalé pause.
- Registrovaný stop odebral jen `/camino-api`, zastavil vlastní proces, odvolal
  token a přesně obnovil původní Serve; Funnel zůstal vypnutý.

Rozhodnutí:
- C05b je přijato v session-owned fyzickém rozsahu. Captive portal T048 se
  nepovyšuje na PASS a zůstává `NEOVĚŘENO`.

Další krok:
- Navázat C05c; C06a spravovaná služba a C06b záloha/obnova vyžadují vlastní
  zadání a nesmějí se odvozovat z akceptačního běhu.

Navrhované další kroky:
- Captive portal doplnit jen při bezpečně dostupné síti; T038 až s reálnou AI.

Technický důkaz:
- Konečný stav po stopu: 104 operací, 41 Momentů, 45 Assetů, 45/45 ověřených
  médií, 214 555 219 B, 0 aktivních tokenů. Uzavírací plná brána 1770/1770 PASS.
