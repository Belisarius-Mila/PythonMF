# E-mail read-only OAuth integrace

- 2026-11-09 20:46 CET: Lokálně doplněné Splněno a Editovat v kalendáři i úvodní agendě. Splnění pouze skryje konkrétní položku v Cockpitu, kalendář a kolize se nemění. Editace mění název/datum/čas původního výskytu, ostatní údaje zachová. Python/HTTP/JS a nativní in-memory scénáře PASS; nový izolovaný podepsaný helper má 7 self-test kontrol. Mobilní headless Edge 390×844: náhled, Zrušit/znovu otevřít, editace a skrytí PASS. Plná brána 3320 testů OK (31 SKIP). Bez p+n, OS grantu a skutečné kalendářové mutace; další krok autorizovat p+n a jednou povolit úpravy na Macu. Report reports/calendar_complete_edit_20261109.md.


- 2026-11-09 14:03 CET: Lokálně propojený Archiv s potvrzenými archivacemi hodinového agenta. Společný seznam/hledání, detail, text, originál a vložené PDF fungují bez přesunu nebo přepisu uložených zpráv. Původní odkazy stabilní; agent má oddělené reference, nejednoznačná ID a úniky přes symlinky se odmítají. 30 cílených testů PASS; plná brána 3296 testů OK (31 SKIP). Skutečné uložené vyúčtování nalezené, PDF čitelné, souborové otisky před/po shodné. Bez p+n; další krok samostatně schválit nasazení a ověřit Archiv na Macu/iPhonu. Report reports/email_archive_bridge_20261109.md.


Aktuální provozní stav 2026-11-09 11:30 CET: hodinová služba obnovena registrovaným
upgradem f2d6ef79→617f3e0d. První kontrola9.11.11:00 completed v11:28:47,
7 nových zpráv (3 karty+4 přehled); HTTP3+3 viditelné,1 skrytá platným pravidlem.
Při přepnutí business stav/nastavení/role zachované; všechny původní položky
po dočtení beze změny. Terra/high, calendar_suggestions=false. Příčina byla
starý instalovaný parser proti nové recovery roli ve sdíleném JSON.
P+n dokončovacího provozního záznamu výslovně schválené; konečná účtenka
v logs/email_role_compat_release_20261109.log. Samostatný e-mailový TVBCP
není domluvený a nevzniká. Report reports/email_hourly_role_compat_20261109.md.


- 2026-11-08 18:22 CET: Lokálně doplněné volitelné kalendářové návrhy v jednom e-mailovém posouzení. Výchozí calendar_suggestions=false, běžící služba se nemění. Připravený návrh přebírá stejné Do kalendáře bez dalšího modelu/IMAP; existující návrhy, revize, zápisy a e-mailové koncepty se nepřepisují. 214 cílených testů PASS; závěrečná plná Cockpit brána 3199 testů OK (31 SKIP). Bez p+n/aktivace. Report reports/calendar_hourly_suggestions_20261108.md.

- 2026-11-08 17:30 CET: Lokálně doplněná samostatná identita hlavního Cockpitu; i kalendář při instalaci hlavní ikony odkazuje na start /. Nový úkol dál vlastní id/start /calendar/task/. Žádný reset při návratu ani změna rozepsaných dat. 36 cílených + statická brána PASS. Bez nového p+n, fyzická iPhone přejímka otevřená; původní mazání f51f3412 už Mílou přijaté. Report reports/cockpit_home_icons_20261108.md.

- 2026-11-08 14:56 CET: Lokálně doplněné Smazat z kalendáře u jednotlivé události a po uložení. Přesný nativní náhled, potvrzení, jeden výskyt, bez pozvánek s účastníky; trvalé markery bez opakování nejistého mazání. 112 cílených PASS, 15 nativních in-memory scénářů a podepsaný izolovaný self-test PASS. Plná brána 3174 testů OK (31 SKIP), logs/calendar_delete_full_gate_20261108.log. Původní reader/writer zachované; nový helper dosud bez OS grantu, bez p+n a bez skutečného mazání. Report reports/calendar_delete_20261108.md.

Nasazený základ před tímto lokálním krokem: 96648c64. Opravu HTTP zadání
úkolu 9c8584ee Míla potvrdil jako funkční; konečný důkaz předchozího vydání
je logs/data_rec06_final_verified_20261108.log. Starší stavy níže jsou historie.

Jednoduchá karta, navigace pod Komunikací a měsíční agenda jsou již
nasazené v 6d5b576b (Terra a751897cb82760aa9704339547dd78f2, plná brána
2896, smoke 5/5 a CI 42458143491 success; finální živý důkaz
logs/calendar_agenda_final_verified_20261108.log).

Rychlé Zadání úkolu je nasazené v 6c610287 (Terra job
d7ac821490a17273e18be1de270b9ba8, plná brána 2923, smoke 5/5,
CI 42474671842 success). Míla při prvním zadání nahlásil předodesílací
chybu uchování a zašednutí. Ta je reprodukovaná bez randomUUID;
lokální oprava používá silné getRandomValues a zachovává editovatelný
text při prokazatelném neodeslání. Částečně uložená identita se neopouští.
Přesné schéma Mílovy adresy zatím nepotvrzené, server při prvním auditu
neměl žádnou účtenku úkolu. Nové p+n opravy dosud nepovoleno; report
reports/calendar_task_storage_fix_20261108.md. Samotný formulář nadále
používá celý text, den/měsíc/rok, viditelně upravitelných 09:00,
Europe/Prague a alarmy 24 h/60 min. Bez AI a změny původního writeru.
Kanonický UI zápis: handoffs/workstreams/project-cockpit.md a
tvbcp/workstreams/project-cockpit.md.

Kalendář používá jednu kartu se čtyřmi poli: název, začátek,
typ a místo. Kliknutí Do kalendáře připraví návrh přes stávající Terra roli;
úpravy i kontrola kolizí probíhají automaticky. Výchozí pásmo Europe/Prague,
konec +1 hodina; výslovný konec/délka/pásmo mají přednost. Při posunu začátku
se zachová navržená délka, také vícedenní celodenní období. Dva alarmy 24 h/60 min.
Samostatný create-only EventKit writer zapisuje až po kliknutí Zapsat do
kalendáře. Nové kolize či změna cíle vyžadují další kliknutí na aktualizovanou
kartu. Ověřuje uložené údaje i alarmy; nejistý výsledek dovoluje pouze čtecí
obnovu původního zápisu, nikoli druhý create. Původní read-only Swift/bundle a
jeho OS souhlas zůstávají beze změny. Vlastní OS souhlas writeru již potvrzený
a první konkrétně schválená událost skutečně uložená a ověřená (jeden create,
čtecí recover, dva alarmy). Přehled Cockpitu obnovený; viz poslední záznam.
Dřívější jednoduchá karta a její nativní přejímka jsou již zahrnuté
v nasazeném 0850e6f3 (CI 42418270872 success). Původní report
calendar_simple_20261107.md zůstává historickým důkazem této etapy.
Nasazená měsíční agenda čte jen vybrané kalendáře, bez modelu a změn
helperů či oprávnění. Typ je přesný ověřený záznam Samanthy nebo soukromé
označení přes Typ; původní neznámé události se nehádají. Plná brána 2896 OK
(31 SKIP), posledních 347 cílených PASS, skutečné čtení čtyř kalendářů
a syntetická Safari přejímka PASS. Měsíční panel již nasazený v 6d5b576b; fyzická
přejímka iPhonu otevřená. Samostatný e-mailový TVBCP není domluvený.

Aktuální stav 6. 11.: Terra p+n e82a5d47 dokončené, nový editor živě ověřený.
Potvrzený upgrade na f2d6ef79 aktivoval zdvořilostní pravidlo i v hodinovém
agentu; úplný business stav zachovaný, první check already_completed.
Podrobnosti v posledním časovaném záznamu.

## 2026-11-05 22:06 CET — kompatibilita s Datovou hlasovou rolí

Po Mílově výslovném rozšíření p+n i na Datův projekt proběhl druhý potřebný
registrovaný upgrade vlastní hodinové kopie 2fe0481e → 11b4ce64. Vztahuje se
na stejný dříve potvrzený kompatibilitní servis; jiné služby se neměnily.
Instalovaný parser skutečně načetl Email/Interior i novou read_only_voice roli.
Installed/owned/loaded/enabled, úplný business otisk a nastavení před/po shodné,
e-mailová politika nezměněná, stará kopie i záloha zachované. První check
already_completed, 0 návrhů a 0 oznámení. Žádná nová hlasová či e-mailová modelová
zkouška; příští hodinové kontroly zůstávají běžným dříve schváleným provozem.
Důkaz logs/data_voice_email_compat_upgrade_20261105.log a
logs/data_voice_role_activation_20261105.log. Samostatný e-mailový TVBCP stále
není domluvený; nový nevzniká. Další krok: běžný provoz a uživatelská přejímka.



## 2026-11-05 21:22 CET — servisní kompatibilita modelových rolí

Vlastní hodinový agent je registrovaně přepnutý ac9f3bed → 2fe0481e pro podporu
nové interior_architect role. Celý business otisk, nastavení a e-mailová modelová
politika zůstaly shodné; starý release zachovaný, nový check already_completed
bez návrhů/oznámení. Instalovaný parser načetl nový JSON. Handoff continuous_personal_agent_2026_11_04.md;
důkaz logs/interior_ai_email_compat_upgrade_20261105.log. Nový TVBCP nevzniká.

## 2026-11-05 — nezobrazování opakované nedůležité pošty

Míla rozlišil „Příště nedůležité“ u důležitých karet a „Příště nezobrazovat“
u jednotlivých zpráv hodinového přehledu; výslovně schválil vývoj a Terra p+n.
Samostatná visibility_preferences používají účet, přesnou adresu a podobný
předmět. Filtruje se již posouzená nedůležitá pošta, včetně dosavadního
přehledu; důležitá odpovídající zpráva zůstává viditelná. Zrušení pravidla
obnoví přehled, nic se nemaže. Staré preference důležitosti se nekonvertují.
Celé posuzování, těla, upravené koncepty, UID pozice, notifikace a schránka
zůstávají zachované. Změna se provádí v Cockpitu, hodinová kopie ac9f3bed
ani její instalace/model se nemění; společné repository zachovává nová pole.
Ověření: 54 funkčních testů, 46 kontraktů a Node PASS; plná brána 2 528 testů,
2 497 PASS, 31 SKIP, bez selhání (511,548 s).
Report email_visibility_20261105.md; konečná účtenka a živý důkaz v
logs/email_visibility_release_20261105.log a email_visibility_verified_20261105.log.
Kanonický handoff: continuous_personal_agent_2026_11_04.md. Samostatný TVBCP
stále nebyl domluvený; fyzická uživatelská přejímka nové volby je otevřená.

## Řízené přepnutí a společné vydání s Datou — 2026-11-05 12:07 CET

- Míla výslovně zadal Terra p+n pro Willovy i Datovy commity. E-mailový
  kód c846775b a Data d50fccbd/c49da146 (v main 5ad99375/4a337100)
  jsou společně převzaté; integrační checkpoint ac9f3bed.
- Registrované pause/prepare/upgrade dokončily přepnutí vlastního hodinového
  agenta z 167e629f na ac9f3bed. Stará kopie a servisní záloha zůstaly.
  installed/owned/loaded/enabled=true, první skutečná kontrola
  already_completed, 0 modelových posouzení a 0 oznámení.
- Celý stav před/po má shodný SHA-256: karty, upravené koncepty, předvolby,
  zdrojové UID pozice, denní počítadla i doručovací fronta beze změny.
  Nainstalované moduly návrhu/podpisu se byte-for-byte shodují s ověřeným
  zdrojem. Podpis čte místní konfiguraci, model zůstává Terra/high.
- SDK pilot zůstává izolovaný. V main s Datovým interpretem 102 PASS +
  3 historické schema SKIP; všech 12 nových C případů skutečně PASS.
  Chybějící 3 schema testy zvlášť v původním prostředí s exporty PASS,
  jejich zdroj i syntetický peer shodný. Žádná instalace závislostí do produkce.
- Důkazy: logs/email_quality_upgrade_verified_20261105.log,
  logs/data_sdk_c_integration_20261105.log,
  logs/data_sdk_c_schema_verification_20261105.log. Uživatelské Mac/iPhone
  přejímky 1–3 Data zaznamenal jako PASS; bod 4 a skutečný technický reconnect
  jsou nadále otevřené, syntetické zkoušky je nenahrazují.
- Tento checkpoint zmrazí podklady pro registrované submit_release(wait=True)
  v project-email-cases; centrální vykonavatel a společný cíl se ověří auditem.
  Konečný stav publikace a její přesnou účtenku dokládá
  logs/email_data_quality_release_20261105.log a následné *_verified_*.log.
  Během vydání se Gitový snapshot nemění. Po vydání ověřit živé UI, CI,
  samostatnou službu a čistotu main i profilů; další plné posouzení nového
  e-mailu a fyzické kliknutí na novou volbu nejsou předem prohlášené za přijaté.

## Lokální oprava kvality konceptů a předvolby ostatní pošty — 2026-11-05 11:46 CET

- Míla upozornil na chybějící předvolbu u nedůležité pošty a na věcně
  chybný koncept s nepodloženým tvrzením o příloze. Read-only načtení
  konkrétní zprávy ověřilo shodu původního EML digestu i celého uloženého
  těla (1801 znaků textu, 13908 znaků HTML). Oba úplné formáty předává
  adaptér modelu; zkrácení vstupu se nepotvrdilo. Původní koncept se po
  uživatelské úpravě nezachoval, jeho přesné znění není zpětně doložitelné.
- Ve zdrojích je doplněná volba jednotlivé zprávy uvnitř rozbalení
  Příště nedůležité… v hodinovém řádku. Ukládá se stejná výslovná
  preference účet + odesílatel + podobný předmět. Řádek, těla, UID kurzory
  a schránka zůstávají zachované; smazání se dál neučí automaticky.
- Oba modelové adaptéry sdílejí pravidla: rozlišit hotové úkony od
  požadavků, zachovat termín, podklady a alternativy doručení, nezaměňovat
  běžnou odpověď za úřední podání. Editor posílá pouze text bez příloh;
  koncept nemá tvrdit, že něco přikládá nebo že už byla žádost podána.
  Požadované oslovení vychází z From/podpisu, při neznámé osobě obecné.
- Podpis se doplní programově jen novému konceptu podle lokálního
  SAMANTHA_EMAIL_REPLY_NAME. Jméno bylo ověřeno v uživatelem uloženém
  konceptu a nastaveno pouze v místním .env; Git obsahuje jen prázdný vzor.
  Uživatelské úpravy a potvrzené odchozí zprávy se tím nepřepisují.
- Dvě skutečné jednorázové zkoušky Terra/high: syntetická žádost a
  původní zpráva. Obě správně oddělily odpověď od podání, zachovaly termín,
  oslovení a podpis, bez tvrzení o příloze či dokončeném úkonu. Původní
  karta a koncept beze změny. Jde o dva ověřené případy, nikoli záruku
  bezchybnosti všech dalších e-mailů. Žádný SMTP ani Pushcut test.
- Aktuální centrální role i skutečný App Server potvrzují Terra/high.
  Katalog podporuje také xhigh/max; vyšší úroveň by vyžadovala samostatné
  srovnání kvality, času a spotřeby. Model ani jeho úroveň se neměnily.
- Ověření: plná brána 2476 testů, 2456 PASS a 20 SDK SKIP (406,1 s).
  Po poslední úpravě rozložení a registrace nového policy modulu navíc
  55 cílených kontrol PASS; finální statická brána PASS. Dvě živé zkoušky
  Terra/high PASS. Otisk změněné stránky byl aktualizován bez oslabení kontraktu.
  Důkazy: logs/email_proposal_diagnosis_20261105.log,
  logs/email_quality_live_review_20261105.log,
  logs/email_quality_full_gate_20261105.log. Soukromý náhled leží pouze
  pod data/private/continuous_agent/quality_preview_20261105.json.
- Stav vydání: pouze lokální změna, bez nového p+n. Běžící hodinový agent
  zůstává na 167e629f; pro zapnutí opravy je nutné schválené p+n Cockpitu
  a řízený upgrade jeho samostatné kopie. Starý uživatelský koncept se
  automaticky nepřegeneruje. Nový TVBCP nebyl domluven ani založen;
  jde o terminálový vývoj stávajícího e-mailového proudu.
- Předchozí vydání obou kroků skončila úspěšně: moje 3f3b5b25 / CI
  42006566022 a Data 6972ea5c / CI 42009849549. Datův vývoj zde neměněn.
  Další krok po lokálním checkpointu: samostatné p+n project-email-cases
  a řízený pause/prepare/upgrade hodinové kopie se zachováním dat a pozic.
  Nový p+n v tomto kroku nebyl zadán. CalDAV a archivní metadata zvlášť.

## Aktuální směr 2026-11-04 — průběžný osobní agent

- Stav 23:24 CET: příprava hodinového vstupu je vydaná po 77f7e12f,
  Terra p+n 742135a3ba9990edc0afe6734d125166, plná brána 2368 PASS,
  smoke 5/5, GitHub CI success. Trvalá služba ani modelová role neaktivované.
- Míla zvolil nejdřív notifikaci a výslovně Pushcut. Lokálně je hotová
  trvalá hodinová fronta nových důležitých karet, plain POST předdefinované
  notifikace a nastavení/test v Cockpitu. Text, zvuk i otevření odkazu
  se definují v iPhone aplikaci; backend nevyužívá placený dynamický obsah.
- Fronta je atomická s kartou, jeden pokus je zapsaný před sítí a nejistý
  výsledek se neopakuje. Staré/nevyřešené karty při zapnutí nezvoní zpětně,
  ignorované/vyřízené se před odesláním přeskočí. Těla zpráv se dál čtou celá.
- Cíleně 147 scénářů PASS včetně celého frontend kontraktu. První plná
  brána měla jediný FAIL ve starém otisku rozšířené stránky; fixture opraven,
  kontrola ponechaná. Míla výslovně schválil p+n, plnou bránu znovu provede
  registrovaný vydavatel podle LL-079. Skutečný webhook chybí,
  nastavení je vypnuté, živý Pushcut ani další model/SMTP se nevolaly.
  Fyzický tón/klepnutí a p+n nového kódu čekají. Postup a důkazy:
  `../reports/email_pushcut_20261104.md`.

- Stav 22:40 CET: paměť důležitosti je již vydaná po 592d247b; místní plná
  brána i GitHub CI 2352 PASS, živá stránka/stamp ověřené. Fyzické QA čeká.
- Pokračování připravuje samostatnou hodinovou službu: registrovaný čtecí
  readiness/náhled LaunchAgentu a opt-in `tick` s denním trvalým počítadlem
  modelových pokusů, kooperativním pozastavením a ochranou před souběhem.
  Vzor je vypnutý; 20 posouzení/den je pouze návrh, ne přijatý rozpočet.
- Vlastní role `continuous_email` je rozpoznávaná, ale centrální konfigurace
  se neměnila a role není aktivní. Bez schválení se model nekontaktuje;
  role p+n se automaticky nepřebírá. Celé zprávy a potvrzované akce zachované.
- Změna UIDVALIDITY nově zastaví zdroj před načtením historie, zachová
  kurzor a konkrétní chybu. Čerstvá místní readiness: iCloud inicializovaný,
  Seznam dosud ne; provozní konfigurace a vlastní role chybí. Žádný nový
  živý pokus/model/SMTP/archivace, žádná instalace služby ani p+n.
- Důkazy, omezení a další krok: `../reports/continuous_email_service_preparation_20261104.md`.
  Finální cílené ověření 112 PASS, nová servisní sada 15 PASS;
  plná Cockpit brána 2366 PASS (498,4 s), finální statická brána PASS.
  Starší neaktuální provozní formulace níže patří k předchozím milníkům.

- Stav 21:19 CET: Míla osobně úspěšně upravil/uložil koncept a odeslal
  skutečnou odpověď. Audit potvrzuje změnu návrhu, `smtp_sent` a kopii
  `saved`. Následně výslovně zadal implementovat „Příště nedůležité“.
- Nová lokální funkce ukládá výslovnou preferenci pro účet, přesnou adresu
  odesílatele a podobný předmět do existujícího soukromého JSON repository.
  UI zachová současnou kartu a nabízí zrušení preference v Předvolbách
  důležitosti. Ignorování/mazání/nečinnost se automaticky neučí.
- Celé tělo se dál načítá a posuzuje modelem. Shodné preference putují
  oběma modelovým adaptérům jako vodítko; nový významný obsah může model
  ponechat důležitý. Před posouzením se nic nefiltruje ani nepřepisuje verdikt.
- 78 e-mailových a 290 Cockpit/frontend scénářů PASS; plná brána persistence
  2352 testů PASS. Zatím bez nového p+n a fyzické přejímky nové volby,
  žádný nový placený model/SMTP pokus. Trvalý provoz zůstává vypnutý.

- Stav 21:02 CET: předchozí vzorky Míla označil za v pořádku a vybral
  konkrétní zprávu pro koncept. Třetí vzorek prošel jedním potvrzeným
  pokusem Terry/high: důležitá karta s editovatelným předmětem a krátkým
  poděkováním. Reakce je volitelná a byla výslovně vyžádaná pro tento pilot.
  Živé API ověřilo přesný návrh/tělo a 0 chyb; archiv/SMTP se nevolaly,
  staré položky i kurzor zachované. Následuje lidský test editoru a uložení
  konceptu, nikoli automatické odeslání nebo zapnutí služby.
- Paměť preferencí odesílatel/předmět navrhl Míla k diskusi. Doporučené
  rozlišení: nevyřízené zůstává důležité, vyřazení je místní úklid;
  budoucí „Příště nedůležité“ by bylo výslovné modelové vodítko. Nová
  funkce zatím není schválená ani implementovaná; staré akce se neučí.
- Oprava CI mezitím vydaná po `13b41716` (Terra bfdfc229, místní
  2339 PASS + smoke 5/5); GitHub run 41898753725 success, 2339 testů,
  23 skip. Dřívější otevřený CI nález v této historii je uzavřený.

- Dodatek 20:20 CET: na Mílův výslovný pokyn Terra lokálně opravila obě
  zjištěné chyby mediálních testů Camina. Běžné moduly 37/37 PASS,
  reprodukce prostředí bez binárek FAIL→PASS, skutečná integrace zachovaná.
  Vývoj je kanonicky zapsaný v `project-camino`; nový p+n/GitHub run opravy
  zatím neproběhly. Poté se vracíme k nedokončenému testu konceptu odpovědi.

- Stav 20:13 CET: oprava schématu je již nasazená po `d1e5e72c`
  (Terra p+n `2be778ce`, místní plná brána 2338 PASS, smoke 5/5,
  nezávislé ověření). Starší údaj „pouze lokální“ níže je překonaný.
- Míla osobně ověřil vyřazení první karty na Macu; stav `dismissed`
  potvrzený, originální e-mail tím není smazaný. Metadata/archiv/SMTP
  ani fyzický iPhone test tím přijaté nejsou.
- Další malý pilot: Terra/high jednou zpracovala 2 celé nové iCloud zprávy.
  Hromadná nabídka správně vytvořila hodinový řádek, technické upozornění
  důležitou kartu. Živé API: 1 karta, 1 řádek, 0 chyb, žádný koncept.
  Oba modelové výsledky potvrzené, běžné kurzory a staré vyřazení zachované.
- Třetí vzorek pro koncept čeká na Mílův výběr aktuální zprávy (odesílatel
  a předmět); žádost poslaná v konverzaci. Celkový limit malého pilota 3.
  Modelové role, hodinová služba, archivace ani SMTP se neaktivovaly.
- GitHub Actions run 41890802397 selhal ve dvou mediálních testech Camina
  kvůli nenalezeným ffmpeg/ffprobe na runneru. Místní publikační brána
  a vzdálená CI jsou různé důkazy; CI zůstává samostatně otevřená.

- Oprava a úspěšný pilot 19:35 CET: příčina prvního selhání je doložená
  syntetickým průchodem: `invalid_json_schema`, chybějící `important` a
  `reply_subject` v `required`. Adaptér nyní požaduje všechny vlastnosti
  výstupu, místní výchozí hodnoty pro staré návrhy zachovává.
  Regrese FAIL→PASS, 65 cílených scénářů a statická brána PASS.
- Jeden nový potvrzený pokus Terry/high nad stejnou celou zprávou vytvořil
  důležitou kartu s doporučením uložení, bez návrhu odpovědi. Živé API
  ověřilo přesnou shodu návrhu/těla a 0 chyb. Historie původního selhání
  i kurzor zachované; archiv/SMTP se nevolaly, služba zůstává vypnutá.
- Naměřeno 28 463 input + 221 output tokenů, bez cache, 5 724 ms;
  odhad 0,7392 Standard kreditu za tento pokus. Před trvalou aktivací
  posoudit režii vstupu a další vzorky. Další krok je Mílova přejímka karty
  a metadat, pak provozní profil/rozpočet. Oprava je lokální, bez dalšího p+n.

- Aktuální vydání 19:27 CET: Míla schválil Terra p+n a následný řízený
  pilot. P+n dokončené po `d9bf3a7c111a`, účtenka
  `c3a38a12547115a5ed292a3826a9e70e`, 2337 PASS, smoke 5/5;
  vzdálený main, živý code stamp i stránka nezávisle ověřené.
  Starší zmínky o odkladu p+n v milnících níže jsou překonané.
- První živý jednorázový pilot načetl jeden celý nejnovější iCloud e-mail
  a provedl jeden pokus Terry/high. App Server nepotvrdil jednoznačné
  doručení/dokončení (`AppServerContractError`), proto nevznikl potvrzený
  návrh; položka zůstala `analysis_failed`. Bez automatického opakování,
  bez archivu/SMTP a bez zapnutí hodinové služby. Spotřeba tohoto pokusu
  není doložená. Tento neúspěšný stav překonal nový pilot popsaný výše.
- Jednorázový pilot vybral schválenou Terru z centrální konfigurace;
  nevznikla nová trvalá role. Provozní profil, přejímka kvality a fyzické
  browser/iPhone ověření zůstávají otevřené. Úplný stav a důkazy jsou v handoffu.

- Třetí lokální krok: Odeslat připraví konečné potvrzení s konkrétním účtem
  a adresátem; až druhé tlačítko spustí SMTP. Odpověď zachovává návaznost na
  původní zprávu a respektuje Reply-To. Opakování nevytváří duplicitu,
  nejistý výsledek blokuje další pokus, chyba QUIT/kopie neruší SMTP přijetí.
- 64 cílených scénářů PASS pouze na umělých zprávách a falešném SMTP;
  plná Cockpit brána 2337 testů PASS.
  Živá přejímka a fyzický browser/iPhone test zůstávají otevřené.

- Druhý lokální krok: kontrola každou hodinu 7–22 v Europe/Prague, Terra přes
  App Server, ranní dočtení od posledního večerního cyklu. Produkční start
  vyžaduje explicitní inicializaci pozic; historie se automaticky nespouští.
- V Komunikaci je nový lokální vstup E-maily k řešení: důležité zprávy
  jednotlivě s celým tělem a návrhy, ostatní po hodinách pouze s hlavičkami.
  Ignorování/vyřazení je pouze místní. Koncept předmětu a odpovědi se upravuje
  ve vlastním editoru. Uložení je potvrzované; SMTP kód doplnil třetí krok,
  ale živý provoz zatím připojený ani aktivovaný není.
- 42 cílených testů i plná brána 2315 testů prošly. Vizuální browser QA je otevřená kvůli nedostupnému
  ovládacímu hostu. P+n Míla výslovně odložil; žádný provoz nebyl aktivovaný.

- Míla stanovil prioritu průběžného agenta pro e-maily a Apple/iCloud kalendář.
  Mac bude stále online. Čtení se týká celého obsahu e-mailů, nikoli jen hlaviček
  nebo zkrácených ukázek. Dosavadní omezení této historické reference nejsou
  novým požadavkem na jednotlivá potvrzení průběžného čtení.
- Agent má obsahově připravit reakci, odpověď a návrh uložení včetně metadat.
  Uložení provede až po Mílově potvrzení; původní heuristická klasifikace není
  pro tento cyklus autorem metadat. Automatické odesílání nebylo zadáno.
- Míla zapnul Kalendář na iCloudu, potvrdil sloučení a následně osobně potvrdil
  funkční synchronizaci na Macu i iPhonu. Programové CalDAV připojení dosud
  ověřené není. Tento směr je odlišný od rodinného registru narozenin a svátků.
- Základní lokální backend je v `app/email/continuous_agent.py` a
  `continuous_source.py`: úplný IMAP/MIME vstup, obnovení dávky, modelové návrhy,
  upravitelný návrh s otiskem a potvrzený archiv s původním EML. Model se volí
  explicitně. Míla zvolil Terru; první potvrzený živý běh je popsaný výše,
  trvalá role zatím nevznikla. Nová cesta je v `codex_proposer.py` a `hourly_agent.py`.
- Trvalý pracovní stav obsahuje identitu zdroje a návrhy; obchodní archiv se
  vytváří po potvrzení. Nový archiv je zatím oddělený, není integrován do UI
  existujícího archivu ani do importu jednotlivých příloh v dokumentovém vaultu.
- Přejímka prvního kroku a zbývající práce jsou v
  `../handoffs/continuous_personal_agent_2026_11_04.md`.
- Níže zůstává historický návrh a popis již existujících ručních nástrojů.

## Cil

Mila chce jit cestou bezpecne dlouhodobe integrace, ve ktere Samantha dokaze cist vybrane e-maily pres OAuth, ne pres Apple Mail GUI. Prvni verze ma byt read-only a bez moznosti odesilani, mazani nebo uprav zprav.

## Bezpecnostni pravidla

- Zacit pouze ctenim e-mailu, ne odesilanim.
- Nepouzivat trvaly pristup ke vsem akcim ve schrance, pokud staci uzsi opravneni.
- Tokeny, client secret, refresh tokeny ani skutecne adresy neschranovat v gitu ani v pameti.
- Tajemstvi patri pouze do lokalniho `.env`, macOS Keychainu nebo jineho lokalniho secret store.
- Do pameti se smi zapisovat jen architektura, rozhodnuti, obecne scope a provozni pravidla.
- Obsah e-mailu neukladat do dlouhodobe pameti automaticky; ukladat jen vyslovne schvalene shrnuti.
- Prvni implementace musi mit rucni potvrzeni Milou pred ulozenim jakehokoli poznatku z e-mailu do `memory/`.

## Doporuceny smer podle poskytovatele

### Gmail

Pro Gmail je potreba pocitat s tim, ze plny read-only scope `https://www.googleapis.com/auth/gmail.readonly` je podle oficialni dokumentace Google vedeny jako restricted scope. To je porad bezpecnejsi nez `https://mail.google.com/`, ale pro verejnou aplikaci by to mohlo znamenat verifikaci a dalsi pozadavky.

Pragmaticka prvni volba:

- Pro lokalni osobni prototyp pouzit OAuth klienta typu Desktop app.
- Scope drzet na `https://www.googleapis.com/auth/gmail.readonly`, pokud Samantha opravdu potrebuje telo zprav.
- Pokud staci jen hlavicky a metadata, zvazit `https://www.googleapis.com/auth/gmail.metadata`, protoze necte telo e-mailu.

### Outlook / Microsoft 365

Pro Microsoft Graph je vhodny delegovany uzivatelsky scope `Mail.Read`, ktery cte mailbox prihlaseneho uzivatele. Nezacinat application permissions, protoze ty typicky znamenaji pristup bez prihlaseneho uzivatele a mohou mit organizacni rozsah.

Pragmaticka prvni volba:

- Pouzit delegated OAuth flow.
- Scope: `Mail.Read`.
- Doplnek `offline_access` pouzit jen tehdy, pokud chceme obnovovat token bez opakovaneho prihlasovani.

## Navrh architektury v projektu

Minimalni struktura pro prvni verzi:

```text
app/email/
  __init__.py
  models.py          # normalizovany EmailSummary / EmailMessage
  provider_base.py   # spolecne rozhrani
  gmail_provider.py  # pozdeji Gmail API
  graph_provider.py  # pozdeji Microsoft Graph
scripts/
  email_oauth_login.py       # jednorazove prihlaseni a ulozeni tokenu mimo git
  email_list_recent.py       # test vypisu poslednich zprav bez ukladani obsahu
data/email/
  .gitkeep                   # lokalni cache jen pokud bude potreba
```

Prvni skript nema nic posilat do OpenAI ani zapisovat do pameti. Ma jen overit, ze OAuth funguje a ze lze vypsat napr. poslednich 10 predmetu, odesilatelu a casu.

## Hranice pro prvni implementaci

Prvni verze smi:

- vypsat posledni e-maily,
- hledat podle dotazu,
- nacist jeden konkretni e-mail po potvrzeni uzivatelem,
- vytvorit shrnuti v chatu.

Prvni verze nesmi:

- odesilat e-maily,
- mazat e-maily,
- oznacovat e-maily jako prectene,
- automaticky archivovat nebo stitkovat,
- automaticky zapisovat obsah nebo citlive detaily do pameti.

Poznamka 2026-05-26, upraveno 2026-06-29: read-only pravidla stale plati pro
hledani, triage, cteni, archivaci a praci s prilohami. Vyjimkou je samostatne
outbound workflow pro preposlani e-mailu, ktere neni automaticke: po jasnem
Milove pokynu se muze vytvorit lokalni draft v `data/email/outbox_drafts/`, ale
az po samostatnem presnem potvrzeni se draft odesle pres SMTP.

## Provozni pripominka: tydenni kontrola a zaloha

Mila chce, aby Samantha pri startu pripomnela e-mailovou udrzbu, pokud se dele
nez 7 dni neprovedla kontrola nebo zaloha dulezitych e-mailu.

Pravidlo:

- Pokud nebyla poslednich 7 dni spustena e-mailova triage, pripomenout:
  `Nebyly projity e-maily za poslednich 7 dni. Chces spustit Email Triage?`
- Pokud nebyla poslednich 7 dni provedena zaloha/archivace dulezitych e-mailu,
  pripomenout:
  `Dulezite e-maily nebyly poslednich 7 dni archivovany. Chces vybrat zpravy k zaloze?`
- Pripominka sama nesmi cist e-maily, stahovat prilohy, otevirat odkazy ani nic
  ukladat. Ma pouze upozornit a nabidnout dalsi krok.
- Technicky smer: pozdeji vest lokalni stav napr. v
  `data/email/activity_state.json` s poli `last_triage_at` a
  `last_archive_at`. Tento soubor patri do lokalnich dat, ne do memory.
- Do memory se nema zapisovat konkretni obsah e-mailu, UID, plne URL ani citlive
  udaje. Memory ma obsahovat jen toto obecne provozni pravidlo.

## iCloud Mail aktualni smer

Mila upresnil, ze hlavni ucet pro prvni prototyp je iCloud Mail pouzivany na iPhonu
a Macu. iPhone a Mac se maji chapat jako klienti; Samantha se nema napojovat na
lokalni aplikaci Mail jako primarni zdroj, ale na iCloud Mail server.

Pro iCloud Mail byl pripraven prvni read-only test:

- `scripts/icloud_list_recent.py`
- IMAP server: `imap.mail.me.com`
- port: `993`
- prihlaseni pres iCloud adresu a Apple app-specific password
- konfigurace v lokalnim `.env`
- vypis pouze poslednich hlavicek: datum, odesilatel, predmet
- bez cteni tela e-mailu
- bez zmeny stavu zprav diky `BODY.PEEK`

Konkretni iCloud adresa ani app-specific heslo se nesmi zapisovat do pameti. Adresa
smela byt pouzita pouze v lokalnim `.env`, ktery je ignorovany gitem.

Navazujici handoff k pokusu o nastaveni je v:

- `memory/handoffs/email_icloud_setup_conversation_2026_05_18.txt`

## Prakticky dalsi krok

Prvni poskytovatel je iCloud Mail. Nejblizsi krok je zprovoznit app-specific password
v lokalnim `.env` a spustit:

```bash
python3 /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/scripts/icloud_list_recent.py --limit 10
```

Az test projde, pridat normalizovane rozhrani do `app/email/` a teprve potom nastroj
pro Samanthu.

## Overene zdroje k 2026-05-18

- Google Gmail API scopes: `https://developers.google.cn/workspace/gmail/api/auth/scopes?hl=en`
- Microsoft Graph permissions reference: `https://learn.microsoft.com/en-us/graph/permissions-reference`
- Apple app-specific passwords: `https://support.apple.com/en-mide/102654`
- Apple iCloud Mail server settings: `https://support.apple.com/en-la/HT202304`

## Aktualni kanonicky stav 2026-05-23

Projekt je rozpracovany, ale zakladni read-only vrstvy uz existuji. Tento stav
prekryva starsi iCloud handoffy z 2026-05-18 a vetsinu implementacnich mezistavu
z 2026-05-19.

Hotove schopnosti:

- iCloud read-only workflow:
  - vypsat hlavicky,
  - hledat v hlavickach,
  - precist jedno konkretni telo podle UID az po potvrzeni,
  - fulltextove hledat v textu za rok bez vypisu tel,
  - vytvaret redigovane shrnuti a safe case.
- Email triage / case / archive vrstvy:
  - `run_email_triage_session`,
  - `save_selected_email_cases_from_uids`,
  - lokalni `EmailCaseVault`,
  - lokalni `EmailArchiveVault`,
  - samostatne potvrzene zobrazeni odkazu z archivu.
- Reminders napojeni:
  - z potvrzeneho e-mailoveho action case lze navrhovat a ukladat pripominky
    podle obecných pravidel reminders workflow.
- Seznam Mail:
  - `SeznamReadOnlyEmailProvider` existuje pro INBOX hlavicky a potvrzene cteni
    jednoho tela podle UID,
  - `list_recent_seznam_email_headers`,
  - `search_seznam_email_headers`,
  - `read_seznam_email_body_by_uid`,
  - `list_unified_email_headers` rozlisuje zdroj schranky.
- Potvrzene preposilani e-mailu:
  - `prepare_forward_email_by_uid` vytvori lokalni draft z jednoho konkretniho
    iCloud nebo Seznam UID po jasnem Milove pokynu; draft se uklada do ignorovane slozky
    `data/email/outbox_drafts/` a obsahuje puvodni zpravu jako `.eml`, pokud je
    dostupna,
  - `send_prepared_email_draft` odesle az existujici draft a vyzaduje druhe
    samostatne potvrzeni s `draft_id`, odesilacim tokenem z draftu a souhlasem
    s odeslanim; potvrzeni s plnym prijemcem zustava jen kompatibilni fallback,
  - iCloud SMTP pouziva `smtp.mail.me.com:587` se STARTTLS, Seznam SMTP pouziva
    `smtp.seznam.cz:465` se SSL/TLS; udaje zustavaji jen v lokalnim `.env`,
  - outbound workflow nesmi byt spojeno do jednoho kroku se ctenim e-mailu.
- Lokalni Seznam `.env` je vyplneny mimo git a memory.
- Read-only Seznam smoke test hlavicek 2026-05-23 prosel:
  - provider se prihlasil,
  - nacetl 2 hlavicky,
  - do vystupu ani memory nebyly vypsany predmety, odesilatele, telo ani URL.
- iCloud Mail byl 2026-05-24 znovu zprovoznen pres lokalni `.env` a Apple
  app-specific password pojmenovane v Apple uctu `Samantha Mail`.
  Read-only IMAP login prosel a smoke test posledni hlavicky fungoval.
  Skutecna iCloud adresa a app-specific password zustavaji pouze v lokalnim
  ignorovanem `.env`, ne v memory ani v gitu.
- Rodinne e-mailove kontakty jsou ulozene jen soukrome v
  `data/private/contacts/family_contacts.json`. Memory smi obsahovat jen tuto
  obecnou informaci, ne vypis adres. Pri citlivych dokumentech porad pred
  odeslanim overit prijemce a prilohu.
- Drivejsi Seznam pojistny worklist/prilohy existuji lokalne v
  `data/private/email_seznam/`:
  - 34 UID slozek priloh,
  - 129 lokalnich souboru priloh,
  - katalog podle metadat/nazvu priloh.
- Dokumentovy vault ma od 2026-05-26 lepsi klasifikaci pro auto dokumenty:
  Volvo/V40, faktury, zelene karty, servisni prohlidky, STK/technicke kontroly,
  splatnost a platnost se propisuji do `domain`, `document_type`,
  `related_asset` a tagu. Cilem je, aby dotazy typu "pojistky za Volvo V40",
  "vsechny faktury za Volvo" nebo "posledni prohlidka" fungovaly nad private
  document vaultem.

Aktualni dalsi krok:

- Sjednotit potvrzovaci formulace pro cteni tela podle zdroje schranky, napr.
  aby bylo vzdy jasne, zda jde o iCloud UID nebo Seznam UID.
- Seznam pojistne prilohy a dokumenty resit jen pres potvrzovane read-only nebo
  document-vault workflow.
- Neudelat automaticky fulltext, cteni tel, stahovani priloh, archivaci ani
  vypis plnych URL bez samostatneho potvrzeni.
- Preposilani delat pouze dvoukrokove: pripravit draft, ukazat `draft_id`, a
  teprve po dalsim potvrzeni odeslat. Nikdy neposilat rovnou po prvnim dotazu.
- Potvrzeni nemusi byt fyzicky u Macu. Pokud Mila pracuje pres iPhone, SSH nebo
  Cockpit, Samantha/Adam ma pro potvrzovany odesilaci krok vzdy vypsat presnou
  potvrzovaci vetu, kterou lze textove poslat zpatky. Takove vzdalené potvrzeni
  je platne, pokud je v aktualni zprave, obsahuje vsechny povinne identifikatory
  a nejde jen o neurcite `ano`.
- U preposlani e-mailu je preferovany lidsky tok jednokrokovy z pohledu
  potvrzeni: po jasnem pokynu typu "najdi a posli/preposli X Jane" Samantha
  pripravi lokalni draft/navrh, ale nic neodesle. Potom napise:
  `Pripravil jsem navrh. Pokud chces opravdu odeslat, zapiš tuto vetu: ...`.
  Presna veta pro odeslani ma preferovane obsahovat `draft_id`, odesilaci token
  ulozeny u draftu a jasny souhlas s odeslanim, napr.
  `Potvrzuji, odeslat draft <draft_id> kódem <token>.` Tento tvar neobsahuje
  plnou adresu a funguje i v textovém kanálu, kde se osobní údaje redigují.
- Potvrzeni s plnou e-mailovou adresou prijemce zustava kompatibilni fallback,
  ale nema se preferovat v hlasovem kanalu. Pokud potvrzovaci veta obsahuje
  osobni e-mailovou adresu nebo jiny citlivy udaj, ma se zobrazit/poslat textove
  pres SSH nebo Cockpit; nema se cist nahlas.
- Po incidentu 2026-05-28 s rodinnym preposlanim plati: SMTP uspech sam o sobe
  nestaci jako dohledatelny dukaz v klientovi. `send_prepared_email_draft`
  uklada po odeslani best-effort kopii do IMAP Odeslanych, vychozi provider je
  iCloud `Sent Messages`, aby Mila videl kopii v souhrnnem iCloud uctu. Metadata
  draftu musi rozlisovat `delivery_status=smtp_sent` a `sent_copy_status`.
- SMS pres macOS Messages je zatim jen pokus o odeslani. Pokud se nepodari
  stav spolehlive overit, nehlasit ji jako dorucenou ani hotovou; u dulezite
  komunikace zustava primarni e-mail s dohledatelnou kopii.
- SMS/RCS diagnostika 2026-05-28:
  - iMessage z Macu fungovala, ale SMS/RCS z Macu zustavaly ve fronte nebo
    koncily chybou;
  - pricina byla na iPhonu v `Zpravy -> Odesilani a prijem`: bylo zaskrtnute
    jen e-mailove Apple ID, ne telefonni cislo;
  - po zaskrtnuti telefonniho cisla rucni zprava z Macu odesla a test pres
    Samanthu na Android kontakt prosel jako RCS s `is_sent=1`, `is_delivered=1`,
    `error=0`;
  - provozni pravidlo: u SMS/RCS vzdy po pokusu cist `~/Library/Messages/chat.db`
    a hlasit odeslano jen pri `is_sent=1` nebo `is_delivered=1`; pri `error != 0`
    nebo dlouhem `is_sent=0` hlasit problem, ne uspech.
- Doplnene pouceni 2026-06-03: pred AppleScript odeslanim vzdy nejdriv aktivovat
  aplikaci Messages (`tell application "Messages" to activate`). Pokud odeslani
  timeoutuje a `chat.db` nepotvrdi novou odchozi zpravu, nepovazovat pokus za
  odeslany; aktivovat Messages, zopakovat stejnou historicky funkcni sluzbou
  pro kontakt a znovu overit stav v databazi.
- Pokud Mila rekne, ze je e-mail v "mailu" nebo ve sloucenem inboxu a prvni
  kontrolovana schranka ho nenajde, dalsi read-only krok je zkontrolovat i druhou
  nakonfigurovanou schranku pres unified/dual-mailbox workflow. Mila vidi oba
  ucty sloucene v klientovi, proto se nema spolehat jen na prvni odhad zdroje.

## Ad-hoc prehled novych e-mailu

Stav 2026-05-27:

- existuje pohodlny Samantha tool `show_new_email_overview`;
- pouziti: kdyz Mila rekne napr. "Udelej prehled novych e-mailu" nebo "zkontroluj
  nove e-maily" bez urceni schranky;
- tool vola sjednoceny read-only prehled iCloud + Seznam a prida bezpecne menu
  dalsich kroku podle UID;
- necte tela e-mailu, nestahuje prilohy, neotevira odkazy, nic neposila, nemaze,
  nepresouva ani neoznacuje jako prectene;
- dalsi prace stale vyzaduje explicitni UID a samostatne potvrzeni podle typu
  akce.

### Pevny rychly vstup pro 7denni prehled

Stav 2026-06-01:

Mila chce mit pevne zapamatovanou vetu:

```text
Prosím přehled emailů za posledních 7 dní
```

Kdyz tuto vetu napise bez dalsiho upresneni, Samantha to ma chapat jako
bezpecny read-only prehled e-mailovych hlavicek z poslednich 7 dni ve sloucenem
workflow iCloud + Seznam.

Vychozi rozsah:

- preferovat zpravy s PDF prilohami nebo signalem dokumentu/prilohy v hlavicce;
- rozdelit vystup do kategorii:
  - `faktury/e-shopy`,
  - `pojisteni/smlouvy`,
  - `urady/dane`,
  - `ostatni`;
- u kazde polozky ukazat jen bezpecne dohledavaci informace: zdroj/schranka,
  slozka, UID, datum, odesilatel/predmet podle aktualnich redakcnich pravidel,
  zda vypada na PDF/prilohu a kratky duvod dulezitosti;
- pokud neni dost informaci z hlavicek, jasne oznacit, ze jde jen o kandidatni
  zarazeni.

Bezpecnostni rozsah pevneho vstupu:

- necist cela tela e-mailu;
- nestahovat ani neukladat prilohy;
- neotevirat odkazy a nevypisovat plne URL;
- nic neposilat, nemazat, nepresouvat ani neoznacovat jako prectene;
- navazujici prace s konkretnim e-mailem nebo PDF vyzaduje explicitni UID a
  samostatne potvrzeni podle typu akce.

Pokud Mila popise konkretni akci ad hoc, napriklad ulozeni PDF z vybraneho UID,
Samantha ma postupovat podle bezneho potvrzovaneho e-mail/document-vault
workflow, ne podle tohoto zkraceneho prehledu.

## Automaticka read-only Email Triage

Stav 2026-05-27:

- pro skutecne rozdeleni dulezite/nedulezite se nema zustat jen u hlavicek;
- `run_email_triage_session` muze na Miluv bezny pokyn rovnou cist hlavicky a
  omezene telo kandidatnich e-mailu read-only;
- dlouhe potvrzeni ve stylu "Potvrzuji Email Triage..." uz neni vyzadovane ve
  vychozim rezimu;
- automaticka bezpecnostni politika je pevna: neotevirat odkazy, nestahovat
  prilohy, nic neodesilat, nemazat, nepresouvat a neoznacovat jako prectene;
- tool stale nic neuklada do EmailCaseVault, reminders ani memory; navazujici
  case, archivace, plne URL, pripominka nebo odeslani zustavaji samostatne
  potvrzovane kroky podle konkretniho UID.

## Unified triage pres iCloud + Seznam + spam

Stav 2026-05-28:

- preferovany tool pro Milovo "udelat triage e-mailu" je
  `run_unified_email_triage_session`;
- cte read-only omezena tela z obou nakonfigurovanych schranek:
  - iCloud,
  - Seznam;
- ve vychozim nastaveni zkousi k INBOXu pridat i spam/nevyzadanou postu pres
  zname slozky `Junk`, `Spam`, `Bulk Mail`; pokud spam slozka neni nalezena,
  vystup to uvede v nedostupnych zdrojich a pokracuje;
- kazda polozka ve vystupu nese `Zdroj: provider / slozka`, protoze UID samo
  o sobe neni unikatni napric schrankami a slozkami;
- velke, prazdne nebo necitelne zpravy se nesmi tiše zahodit: objevi se v sekci
  `Preskocene velke/necitene zpravy` s UID, zdrojem, slozkou, predmetem a
  duvodem, aby Mila mohl rozhodnout o samostatnem zpracovani;
- ostré cteni porad neotevira odkazy, nestahuje prilohy, nic neodesila, nemaze,
  nepresouva a neoznacuje jako prectene.
- scoring byl doladen pro realny provoz:
  - pojistky, faktury, platby, doruceni, klientské portaly a bezpecnost uctu maji
    vyssi vahu;
  - marketing, politicke pozvanky, knihkupectvi, newslettery a spam maji nizsi
    vahu;
  - low priorita se nepovazuje za deadline/action/case kandidat.
- report zobrazuje u polozek `UID`, zdroj/slozku a datum doruceni, aby se zpravy
  daly dohledat v klientovi.
- low sekce jsou zkracene limitem, aby chat nezaplavily newslettery a spam.
- otevreny navazujici ukol: plny triage report ukladat do lokalniho souboru v
  ignorovane slozce, napr. `data/email/triage_reports/`, a do chatu vracet jen
  prehled plus cestu k souboru.
- aktualni handoff:
  `handoffs/email_unified_triage_scoring_report_checkpoint_2026_05_28.md`.

Bezpecnostni hranice:

- Neukladat do memory ani gitu e-mailove adresy, hesla, app-specific passwords,
  tokeny, cela tela e-mailu, plne URL, prilohy ani privatni obsah.
- Lokalni citliva data zustavaji v `data/email/`, `data/private/email_seznam/`
  a `.env`; `data/email/archive/` i `data/email/outbox_drafts/` se necommituji.
- Vystupy do memory smi obsahovat jen architekturu, workflow, pocty a redigovany
  stav prace.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii, ale nepouzivat je jako aktivni
startovni stav projektu. Aktualni navazani je tento projektovy soubor a
`handoffs/email_seznam_readonly_provider_2026_05_22.md`.

Zaklad iCloud read-only:

- `handoffs/email_mail_permissions_2026_05_17.txt`
- `handoffs/email_icloud_setup_conversation_2026_05_18.txt`
- `handoffs/email_icloud_readonly_test_ok_2026_05_18.md`
- `handoffs/email_icloud_app_email_layer_2026_05_18.md`
- `handoffs/email_samantha_tool_headers_2026_05_18.md`
- `handoffs/email_samantha_e2e_headers_ok_2026_05_18.md`
- `handoffs/email_read_uid_test_ok_2026_05_18.md`
- `handoffs/email_samantha_read_body_tool_ok_2026_05_18.md`
- `handoffs/email_safe_workflow_confirmed_2026_05_18.md`
- `handoffs/email_readonly_workflow_handoff_2026_05_18.md`
- `handoffs/email_search_headers_ready_2026_05_18.md`

Case, odkazy, reminders a RIXO:

- `handoffs/email_case_workflow_ready_2026_05_19.md`
- `handoffs/email_samantha_headers_redacted_waiting_uid_2026_05_19.md`
- `handoffs/email_url_tool_e2e_ok_2026_05_19.md`
- `handoffs/email_rixo_insurance_phase1_ready_2026_05_19.md`
- `handoffs/email_rixo_insurance_phase1_implemented_2026_05_19.md`
- `handoffs/email_action_case_phase2_proposed_2026_05_19.md`
- `handoffs/email_action_case_phase2_core_done_2026_05_19.md`
- `handoffs/email_reminders_phase3b_done_2026_05_19.md`

Triage, case vault a archive vault:

- `handoffs/email_work_session_proposed_2026_05_19.md`
- `handoffs/email_triage_work_mode_proposed_2026_05_19.md`
- `handoffs/email_triage_work_mode_core_done_2026_05_19.md`
- `handoffs/email_triage_session_tool_done_2026_05_19.md`
- `handoffs/email_case_vault_save_tool_done_2026_05_19.md`
- `handoffs/email_activity_state_done_2026_05_19.md`
- `handoffs/email_archive_vault_proposed_2026_05_19.md`
- `handoffs/email_archive_vault_core_done_2026_05_19.md`
- `handoffs/email_archive_vault_tool_done_2026_05_19.md`
- `handoffs/email_archive_vault_no_urls_after_archive_2026_05_19.md`
- `handoffs/email_project_frozen_human_handoff_2026_05_19.md`

Pozdejsi rozsireni:

- `handoffs/email_fulltext_search_tool_2026_05_21.md`
- `handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md`
- `handoffs/email_seznam_readonly_provider_2026_05_22.md`

## Aktuální stav 2026-07-30

- Read-only prohlížeč Archivu e-mailu je vyjmutý z `cockpit.py` do samostatného
  backendového modulu se zachovanými URL, payloady a private hranicemi.
- Frontend hlavního Cockpitu, Email Processing a Archivu e-mailu je oddělený
  do statických souborů bez redesignu.
- Oprava redigovaného dohledání archivních příloh je implementovaná a obsažená
  v nasazeném `main` `20180e2`; Cockpit smoke prošel 5/5.
- Praktický test odhalil chybějící přílohu před opravou. Po nasazení zatím
  není doložený uživatelský post-fix retest stejného bezpečně dohledaného
  archivního záznamu.

Nejmenší další krok:

- V Archivu e-mailu zopakovat read-only otevření již známého redigovaného
  záznamu a potvrdit dostupnost stažené přílohy.
- Mazání, odesílání, přesun do koše a nové ukládání obsahu zůstávají mimo tento
  retest a za svými potvrzovacími hranicemi.

## 2026-11-04 19:27 CET — Terra p+n a první živý pilot

Hotovo: E-maily k řešení jsou nasazené. První řízený vstup načetl jeden celý
e-mail z iCloudu. Modelový výsledek není potvrzený; nevznikla karta ani
hodinový řádek, pouze viditelná chyba posouzení. Nic nebylo archivováno ani
odesláno a hodinový provoz zůstal vypnutý.

Rozhodnutí: Míla výslovně zvolil pořadí Terra p+n, potom řízený pilot.
Nejistý jednotlivý modelový pokus se automaticky neopakuje.

Další krok: Získat přesnou diagnostiku kontraktu App Serveru před novým pilotem.

Navrhované další kroky: Přijmout kvalitu návrhů a metadat, poté připravit
centrální modelovou roli a aktivaci služby; navázat notifikacemi a CalDAV.

Technický důkaz: Vydání `d9bf3a7c111a`, účtenka `c3a38a12`, plná brána
2337 PASS a smoke 5/5, nezávislá shoda živé stránky. Pilot: právě jeden
pokus, `AppServerContractError`, soukromý stav `analysis_failed`; živé API
potvrzuje jednu chybu a nula karet/řádků. Usage ani kořenová příčina nedoložené.

## 2026-11-04 19:35 CET — Oprava schématu a potvrzený živý výsledek

Hotovo: Terra přečetla stejný celý e-mail a úspěšně připravila důležitou
kartu s doporučeným uložením; odpověď nepovažovala za potřebnou. Karta
je v živém Cockpitu k Mílově přejímce. Nic se nearchivovalo ani neodeslalo.

Rozhodnutí: Míla zadal pokračovat opravou a řízeným pilotem. Jeden nový
modelový pokus následoval až po doložené příčině a regresní opravě;
hodinový provoz ani další p+n se nespouštěly.

Další krok: Mílova přejímka důležitosti a metadat na první skutečné kartě.

Navrhované další kroky: Provozní modelový profil/rozpočet s dalšími vzorky,
aktivace služby, notifikace a CalDAV.

Technický důkaz: Syntetický diagnostický průchod doložil HTTP 400
`invalid_json_schema` kvůli chybějícím výchozím polím v `required`.
Regrese FAIL→PASS, 65 cílených scénářů a statická brána PASS. Nový živý
modelový výsledek potvrzený, API má 1 přesně shodnou kartu a 0 chyb.
Spotřeba 28 463 vstup + 221 výstup tokenů, odhad 0,7392 Standard kreditu;
žádná cache. Oprava adaptéru je lokální, nasazený head zůstává d9bf3a7c.

## 2026-11-04 20:13 CET — Dva další živé vzorky a dílčí Mac QA

Hotovo: Po nasazení opravy Míla osobně ověřil vyřazení první karty na Macu.
Další dvě zprávy Terra celým obsahem jednou posoudila: reklama je hodinový
řádek, technické upozornění vlastní důležitá karta. Živé API ukazuje oba
výsledky a žádnou chybu. Původní vyřazení i běžné kurzory zůstaly zachované.

Rozhodnutí: Míla souhlasil s malým dalším pilotem. Pro koncept chybí jeho
výběr konkrétní aktuální zprávy; nejde o souhlas se skutečným odesláním.

Další krok: Vybraná zpráva pro koncept odpovědi a Mílova přejímka nových
dvou výsledků v Cockpitu.

Navrhované další kroky: Potvrzené uložení/editor, domluvený SMTP test,
provozní profil/rozpočet a služba, notifikace/CalDAV.

Technický důkaz: P+n d1e5e72c / 2be778ce, místní 2338 PASS + smoke 5/5.
Soukromá účtenka reprezentativního pilota potvrzuje oba modelové pokusy,
65 777 input (42 496 cached) + 454 output tokenů, odhad 0,691895 Standard
kreditu. GitHub CI run 41890802397 samostatně selhal ve 2 mediálních
testech Camina kvůli nenalezeným ffmpeg/ffprobe; tento nález nebyl opravován.

## 2026-11-04 21:02 CET — Koncept na uživatelem vybrané zprávě

Hotovo: Po přijetí předchozích vzorků Mílou připravila Terra na konkrétně
vybrané zprávě krátkou zdvořilou odpověď. V živém Cockpitu je karta
s předvyplněným předmětem a textem pro editor. Nic se neodeslalo ani
nearchivovalo, dřívější vyřazení se nezměnila.

Rozhodnutí: Míla výslovně vybral zprávu pro test konceptu; odpověď byla
připravená na tento pokyn, přestože je obsahově volitelná. Nápad na paměť
budoucí důležitosti je diskuse, nikoli schválená nová automatika.

Další krok: Mílova přejímka Upravit odpověď → Uložit koncept.

Navrhované další kroky: Potvrzené uložení, domluvený SMTP test,
provozní profil/rozpočet se službou, diskuse paměti preferencí.

Technický důkaz: Jeden modelový pokus Terra/high, potvrzený výsledek,
25 854 input + 278 output tokenů, bez cache. Živé API: karta/koncept/tělo
shodné, 0 chyb, 3 předchozí položky a zdrojový kurzor zachované.
Vývojový kód, trvalé role a služba se neměnily. Souběžný předchozí CI
nález uzavřel nový úspěšný vzdálený run 41898753725 po 13b41716.

## 2026-11-04 21:19 CET — Živé odeslání přijato a paměť důležitosti

Hotovo: Míla ověřil editor, uložení a skutečné odeslání odpovědi. Nová
lokální volba Příště nedůležité uchová preferenci pro podobné další zprávy
od stejného odesílatele; aktuální kartu zachová. Preferenci lze zrušit.

Rozhodnutí: Míla tuto funkci výslovně schválil. Preference je vodítkem
pro plné obsahové posouzení, nikoli náhradou čtení nebo automatickým
pravidlem odvozeným ze smazání či nečinnosti.

Další krok: Vydat samostatným p+n a fyzicky přijmout
nové tlačítko i zrušení preference.

Navrhované další kroky: Živé potvrzené uložení, provozní profil/rozpočet,
hodinová služba a notifikace/CalDAV.

Technický důkaz: Místní SMTP účtenka `smtp_sent`, kopie `saved`, návrh byl
uživatelem změněný. 78 e-mailových a 290 Cockpit/frontend scénářů PASS
pro novou funkci. Plná brána persistence 2352 testů PASS v příslušném logu.
Nová funkce nebyla nasazená a nevolal se další živý model ani SMTP.

## 2026-11-05 — Pushcut přijatý, řízená instalace připravená

Pushcut po b372355c vydaný: Terra p+n 9f34b5d5fa3be12a0124646c4d353050,
2386 PASS, smoke 5/5, GitHub CI 41927780373 success. Míla přijal doručení
na iPhone i otevření E-mailů k řešení. Private připojení je zapnuté/accepted.

Na pokyn dokončit řízenou instalaci vznikl instalátor vlastní kopie čistého
commitnutého main a per-user LaunchAgentu, heartbeat, pause/resume a ověření
obnovy bez přerušení aktivního posouzení. Model continuous_email Terra/high
schválen z předchozích živých zkoušek a cenového posouzení; katalog aktuálně
potvrzen bez fallbacku. Všechny nové celé zprávy, 07–22 Europe/Prague,
výchozí denní početní limit null. Dřívější 20/den nebylo schváleným limitem.

67 cílených testů PASS, plná brána 2403 PASS (377,5 s). Systémový zápis ani aktivace
zatím neproběhly: exact globální věta nebyla zadána. iCloud pozice zachovaná,
Seznam bude inicializován od aktuálního konce až při aktivaci. Nový modelový
tah/SMTP/archivace/ruční Pushcut test neběžel. Míla následně schválil převzetí Data a společné p+n včetně oprav do čistého
repozitáře. Bez nového TVBCP; produkční App Server a Data práce zachované. Další krok: dokončit
bránu/commit/konkrétní plán, systémové potvrzení, instalace/check/obnova
a první ostrá hodina. Viz reports/continuous_email_service_installation_20261105.md
a handoffs/continuous_personal_agent_2026_11_04.md.


Navazující noční integrace: Míla schválil převzetí Data a společné p+n včetně
oprav. Will převzal dva commity jako 1b6fd61e/ccece787, zkontroloval původní
App Server klient (excludeTurns/final_answer/strukturované chyby); SDK zůstává
offline. 192 společných cílených testů: 172 PASS, 20 volitelných SDK SKIP.
Živý handshake/katalog serveru 0.163.0 PASS. Odesílání ani e-mailové pozice
tímto krokem nebyly měněné; aktivace LaunchAgentu dál čeká na přesnou větu.

Společná integrační brána prošla 2462 testy: 2442 PASS, 20 volitelných SDK
SKIP (377,0 s), logs/data_email_integration_gate_20261105.log. P+n je
autorizované; konečný provozní výsledek doloží přesná účtenka a živý audit.


## 2026-11-05 08:55 CET — Hodinová služba aktivní, první ostrý cyklus a obnova ověřené

Hotovo: Po přesné globální větě je per-user e-mailový LaunchAgent skutečně
nainstalovaný, načtený a zapnutý. První cyklus 08:48:53–08:49:38 CET
zpracoval 6 zpráv: 3 důležité karty s těly a 3 nízké důležitosti v jednom
hodinovém řádku. Živé API potvrzuje 0 chyb; Pushcut přijal jeden provozní
požadavek. Fyzické přijetí tohoto nového oznámení se nepředpokládá z API.

Rozhodnutí: Míla přesnou větou schválil dříve připravenou instalaci a obnovu
vlastní služby. Platí jeho zadání všechny nové celé zprávy, Terra/high,
07–22 Europe/Prague bez výchozího denního početního limitu. Uložení a SMTP
zůstávají potvrzované; tento krok je neprovedl.

Další krok: Ověřit další automatickou hodinovou kontrolu a sledovat kvalitu
návrhů při běžném vyřizování v Cockpitu.

Navrhované další kroky: CalDAV a živá přejímka archivních metadat.

Technický důkaz: Běžící kopie b6375a33, installed/owned/loaded/enabled=true;
iCloud kurzor nezresetovaný, Seznam od aktuálního konce. V 08:52 CET vlastní
job vyložen/obnoven a potvrzen nový check already_completed, 0 opakovaných
posouzení a stejná data/počítadla. Důkazy email_service_activation_20261105_*.log.
Předchozí p+n 09e6c05f658a1ce16750dfd5cd15c514 potvrzené, 2462 testů (20 SDK
skipů), smoke 5/5; GitHub CI 41938993126 success. Žádný fyzický reboot Macu,
nový SMTP, archivace či smazání ve schránce. Nový TVBCP nebyl založen.


## 2026-11-05 10:37 CET — Oprava hodinového režimu po prázdném iCloud výsledku

Hotovo: Diagnostika přesně vysvětlila oznámení mimo celou hodinu. iCloud
vracel pro nulový počet nových UID úspěšné OK/[None], klient je mylně odmítal
jako chybu; nedokončená hodina se opakovala a v 10:19 přijala novou zprávu.
Lokální oprava prázdnou kontrolu řádně dokončí. Cíleně 118 testů PASS.

Rozhodnutí: Zachován Mílův původní hodinový režim. Dřívější pokyn opravovat
chyby a dokončit p+n do čistého repozitáře dál platí; přesná globální věta
pro tuto službu už byla zadána. Model a rozsah úplného čtení se nemění.

Další krok: Dokončit plnou bránu a řízeně přepnout pozastavenou službu na
opravenou kopii commitu, ověřit skutečný prázdný vstup a hodinové čekání.

Navrhované další kroky: Po provozním writebacku autorizované p+n; CalDAV
zůstává samostatný krok.

Technický důkaz: Read-only iCloud SEARCH OK/[None], Seznam OK/bytes s 0 UID;
regrese před opravou ERROR/FAIL, po opravě 118 PASS včetně 10:00/10:19/11:00.
Upgrade má testy zachování dat, zámku, cizí změny a návratu na starý job
pozastavený. Žádný SMTP, archivace nebo smazání zpráv; služba do výměny paused.

Technický výsledek před výměnou: plná brána 2473 testů, 2453 PASS a 20 SDK
SKIP (504,5 s), logs/email_empty_search_full_gate_20261105.log. Živé prázdné
sondy obou providerů prošly bez modelu/oznámení/posunu uložených kurzorů.


## 2026-11-05 10:47 CET — Opravený hodinový vstup je již v běžící službě

Hotovo: Řízený upgrade na 167e629f dokončený, nový check již úspěšný;
nainstalovaná kopie přímo ověřila prázdný iCloud i Seznam vstup. Business
stav má před/po shodný otisk, žádné nové posouzení ani oznámení při reloadu.
Stará kopie a konfigurační záloha zachované. Oprava prázdného výsledku už
platí v provozu; další nová pošta čeká na příští hodinový průchod.

Rozhodnutí: Míla výslovně určil nejprve p+n mého dokončeného kroku, potom
samostatně Datův nový commit 5363238b a dočištění repo. Data zatím není v main.

Další krok: Vydat mé commity s provozním zápisem a ověřit automatickou
11. hodinu, následně převzít a vydat Data.

Navrhované další kroky: Fyzická přejímka Datovy iPhone opravy po návratu Míly.

Technický důkaz: upgrade b6375a33 → 167e629f, installed/owned/loaded/enabled;
118 cílených PASS, plná brána 2473 (20 SDK SKIP); stejné kurzory/karty/
předvolby/počítadla; nové already_completed s 0 návrhy. Nainstalovaný kód
prošel živou prázdnou sondou obou providerů. Viz email_empty_search_upgrade*
a full_gate logy. Bez změny modelu, SMTP, archivace nebo mazání e-mailů.

## 2026-11-06 16:34 CET — Zdvořilostní odpovědi a prázdný editor (lokálně)

Hotovo: Společná politika obou modelových adaptérů vyžaduje návrh i při
zdvořilostním významu odpovědi, například poděkování za osobní/pracovní zprávu
nebo výsledek výběrového řízení. Odlišuje povinnou reakci od dobrovolné;
zprávu s navrženou odpovědí ponechá k lidskému posouzení jako important=true.
Reklama, newsletter ani zjevné no-reply samy o sobě zdvořilou reakci neodůvodňují.
Karta bez konceptu má Napsat odpověď s prázdným tělem a odvozeným Re: předmětem;
existující koncept dál nabízí Upravit odpověď. Otevření nic neukládá.

Rozhodnutí: Míla výslovně požaduje připravit odpověď vždy, pokud má i
zdvořilostní význam, a souhlasil s prázdným editorem. Vývoj je lokální;
push, nasazení Cockpitu ani upgrade samostatné hodinové služby nebyly zadané.
Model a role se nemění. Stávající živé návrhy se nepřegenerovávají.

Další krok: Samostatně schválit p+n a registrovaný upgrade vlastní hodinové
kopie; pouhý nový main její zmrazená pravidla nezmění. Lokální vývoj a plná
brána jsou dokončené; tento záznam je součástí lokálního checkpointu.

Navrhované další kroky: Podle původního pořadí Míly zvlášť analyzovat,
proč Human–Adam nedokázal diagnostiku konkrétního problému provést.

Technický důkaz: Regrese prázdného editoru před změnou FAIL, po změně PASS.
61 cílených Python testů včetně rozšířeného Node DOM scénáře PASS. Ověřené
ruční napsání/uložení/znovuotevření, ochrana rozepsaného textu, blokace
sending/delivery_unknown/smtp_sent a odmítnutí prázdného textu. Příprava bez
SMTP a odesílání až po samostatném potvrzení. Plná brána 2669 testů,
31 SKIP, bez selhání PASS (513,892 s unit část):
logs/email_courtesy_full_gate_20261106.log. Nové pravidlo nebylo zkoušené živým
modelem; fyzická Mac/iPhone přejímka je otevřená. Soukromý e-mail ani adresy
se do tohoto zápisu nekopírují. Nový e-mailový TVBCP se nezakládá.

## 2026-11-06 16:57 CET — Terra p+n editoru dokončené, hodinová pravidla čekají na servis

Hotovo: Cockpit má nové Napsat odpověď u karty bez konceptu. Terra p+n na
výslovný pokyn Míly dokončené pro e82a5d473198677c83deb805fd0b303ff8034671;
push i deployment confirmed, plná brána 2669 testů PASS / 482,1 s, smoke 5/5,
protected_services_unchanged=true. Živé HTML HTTP 200 se přesně shoduje se
zdrojem, SHA-256 de672549c799950265dba9bdb14e73755e1fb61a4c444cf34137528c32468247.
Fyzická přejímka otevření editoru na Macu/iPhonu zůstává samostatná.

Rozhodnutí: Míla schválil „ok terra p+n“. Samostatná hodinová služba dál
installed/owned/loaded/enabled na 11b4ce64; její proposal_policy je dosud
původní. P+n Cockpitu nepřepíná tento vlastní LaunchAgent. Žádný nový placený
modelový pokus ani přeposouzení staré karty se neprováděly.

Další krok: Pro aktivaci zdvořilostního pravidla v hodinovém agentu získat
přesnou globální potvrzovací větu podle global_safety_brake.md a service_control.py.
Potom registrované pause → prepare aktuálního čistého main → upgrade, se
zachováním karet, konceptů, předvoleb, UID pozic a modelové politiky; ověřit
business otisk a první check. Porovnání 11b4ce64..e82a5d47 v Python app kódu
mění pouze proposal_policy.py. Služba zatím nebyla pozastavená ani přepnutá.

Navrhované další kroky: Samostatná diagnostika dřívějšího selhání Human–Adam
podle Mílova původního pořadí.

Technický důkaz: Účtenka b3165b2afa348909c291ff989fd12207 completed,
logs/email_courtesy_release_20261106.log a email_courtesy_verified_20261106.log.
return_channel=caller; returned_to_adam=false není důvodem opakovat vydání.
Main/GitHub byly před tímto výsledkovým zápisem shodné, profily zarovnané,
Datův vlastní worktree čistý a zachovaný. Tento dokumentační checkpoint je
lokální pro příští balíček; neprovádí nové nasazení. Soukromý e-mail ani
přihlašovací údaje se do zápisu nekopírují. Nový TVBCP nevzniká.

## 2026-11-06 17:03 CET — Zdvořilostní pravidlo aktivní i v hodinové službě

Hotovo: Hodinový e-mailový agent nyní používá nové pravidlo zdvořilostních
odpovědí. Registrované pause → prepare → upgrade převedly vlastní LaunchAgent
z 11b4ce64 na f2d6ef79. Installed/owned/loaded/enabled=true; čerstvý import
z instalované kopie potvrdil nové pravidlo a byteovou shodu proposal_policy.py.
První dokončená kontrola already_completed, žádné nové placené posouzení.

Rozhodnutí: Míla po dokončeném Terra p+n výslovně poslal přesnou větu globální
brzdy pro tento servisní upgrade. Kód odpovídá již přijatému e82a5d47;
f2d6ef79 oproti němu přidává pouze dokumentační výsledek vydání.

Další krok: U dalších běžně posuzovaných zpráv ověřit praktickou kvalitu
zdvořilostních konceptů; původní již posouzená karta se nepřegenerovává.
Napsat odpověď je v nasazeném Cockpitu dostupné i bez původního konceptu.

Navrhované další kroky: Samostatně navázat na Mílův původní požadavek proč
Human–Adam nedokázal konkrétní e-mailový problém diagnostikovat.

Technický důkaz: Všech 12 servisních kontrol PASS. Úplný business stav před/po
shodný (karty, koncepty, předvolby, UID pozice, počítadla i doručovací fronty),
shodná nastavení a všechny role; předchozí release i nová servisní záloha
zachované. Otisk business stavu
338d2a91f2bb5402cda3848a2f383a76845e6d9c3012670b603b10783e5662a4.
Důkaz logs/email_courtesy_service_upgrade_20261106.log; úplný soukromý baseline
a redigovaný verified.json jen v ignorovaném service_audits/courtesy_policy_upgrade_20261106.
Bez SMTP, nového modelového probe či přeposouzení původní zprávy.
Předchozí p+n e82a5d47/b3165b2a a plná brána 2669 testů zůstávají platné;
servisní kód ani testy se v tomto kroku neměnily. Tento výsledkový zápis je
lokální pro příští balíček; nový TVBCP nevzniká.

## 2026-11-07 00:01 CET — Kalendářový agent, bod 1: čtecí přístup ověřený

Hotovo: Úplný sedmibodový návrh je připojený na konec zadaného soukromého TXT;
původní obsah zachovaný bajtově. V hlavním checkoutu je samostatný čtecí
EventKit pilot, registrované schopnosti a přesné CLI workflow. Míla povolil
nativní aplikaci přístup. Skutečná jednorázová launchd zkouška rozpoznala
8 kalendářů / 4 iCloud a ověřila sedmidenní okno; žádné události nezapsala.
Dočasný vlastní job už je odstraněný, trvalý LaunchAgent nevznikl.

Rozhodnutí: Míla schválil zahájení bodu 1, další body zůstávají návrhem.
Ověřená cesta používá samostatnou podepsanou aplikaci a soukromý request/result
kanál. Přímý kontext Codexu hlásí pouze write_only, samostatný launchd helper
full_access; nelze zaměňovat oprávnění různých exekučních kontextů.

Další krok: Bod 2 — vybrat čtené kalendáře a budoucí cílový kalendář, navrhnout
čtecí přehled. Bez implementace dalších etap a bez nového p+n v tomto kroku.

Navrhované další kroky: Samostatně zachované dřívější téma diagnostiky selhání
Human–Adam. Aktualizace nativního podpisu/TCC a fyzická iPhone přejímka mají
v dalších etapách vlastní ověření.

Technický důkaz: 44 cílených testů a 4 nativní kontroly PASS; reálná čtecí
launchd přejímka PASS. Plná brána 2683 testů / 31 SKIP, bez selhání PASS
(512,463 s unit část). Report
calendar_access_pilot_20261107.md a logs/calendar_access_*_20261106.log.
Osobní názvy kalendářů/ID zůstávají soukromě, texty událostí se neexportují.
Nový e-mailový TVBCP nevzniká. Hodinová služba a Cockpit se nepřepínaly.

## 2026-11-07 00:18 CET — Schválené společné Terra p+n s Datovým hlasovým panelem

Hotovo: Čtecí kalendářový bod 1 c0963d6b je připravený společně s Datovými
opravami E/F/G 4bf110fd, 73fdc08e, 975f0900. Obě historie a provozní výsledky
jsou zachované; střety byly pouze v dokumentaci.
Rozhodnutí: Míla zadal p+n Willových i Datových commitů přes Terru. Nevzniká
nové oprávnění k zápisům kalendáře, mikrofonu, placenému probe nebo upgradu
samostatné hodinové kopie; ta už má aktivní zdvořilostní pravidlo na f2d6ef79.
Další krok: Konečná účtenka logs/calendar_voice_release_20261107.log a živé
ověření calendar_voice_verified_20261107.log. Vydání není předběžným zápisem
potvrzené. Kalendářový bod 2 zůstává další etapa.
Navrhované další kroky: Mílova skutečná iPhone přejímka hlasového panelu.
Technický důkaz: Cílená integrace a statická brána dle příslušných logů;
plná publikační brána uvnitř Terry. Datův vlastní worktree se nemění.

## 2026-11-07 00:51 CET — Kalendářový bod 2: výběr a čtecí přehled

Hotovo: Cockpit má samostatnou cestu Kalendář (/calendar/). Soukromě ukládá
výběr čtených kalendářů a oddělený budoucí cíl. Přehled načítá 30 dní, ukazuje
poslední čas, celodenní i časové události a označí neúplné/zastaralé načtení.
Chybějící kalendář, odebrané oprávnění ani prázdný snímek nejsou důkazem volna.

Rozhodnutí: Míla autorizoval bod 2 a okamžité Terra p+n. Výběr je výchozí
prázdný; konkrétní kalendáře musí vybrat sám. Žádná událost, hodinová služba,
modelová role ani Datův worktree se nemění. Obsah přehledu se neposílá modelu.

Další krok: Po nasazení na Macu v Kalendář → Povolit přístup na Macu potvrdit
nové nativní sestavení, Obnovit kalendáře, zvolit výběr a Uložit výběr a načíst.
Následně porovnat skutečné události s Kalendářem na Macu a iPhonu. Bez této
přejímky není bod 2 uzavřený jako skutečný provozní přístup.

Navrhované další kroky: Bod 3, návrhy událostí z vybraných e-mailů, až jako
samostatný vývoj. Diagnostika dřívějšího selhání Human–Adam zůstává zachovaná.

Technický důkaz: 87 cílených testů a Safari QA nad izolovanými umělými daty
PASS; nativní sestavení a 4 syntetické kontroly PASS. Skutečné jednorázové
launchd čtení po změně cdhash hlásí not_determined / authorization_required,
nebyl automaticky spuštěn nový OS dialog. Staré binární sestavení, původní
oprávnění a žádosti jsou zachované. Plná brána: logs/calendar_overview_full_gate_20261107.log;
publikační autorita: calendar_overview_release_20261107.log a calendar_overview_verified_20261107.log.
Živé názvy, ID a události zůstávají soukromě; nový TVBCP nebyl domluvený.

## 2026-11-07 09:05 CET — Bod 3: návrhy událostí z vybraných e-mailů (lokálně)

Hotovo: Na vybrané důležité e-mailové kartě je v lokálním kódu Navrhnout událost.
Editor se otevře bez modelového tahu. Samostatné potvrzené tlačítko pošle jen
tuto zprávu schválenému e-mailovému modelu; odpověď obsahuje citace a navržené
položky. Uživatel může uložit i neúplný koncept, uvidí co chybí a co upravil.
Program kontroluje data, pásmo, délku, půlnoc, DST a nesoulad normalizace s
výslovným datem/časem v citaci. Termín úkolu není automaticky schůzka.
Formální ICS a rozpoznané opakování mají ruční zpracování bez placeného tahu.

Rozhodnutí: Míla zadal pokračování bodem 3. Will řeší jádro, validace a integraci;
vymezený editor připravila Luna registrovanou cestou, převzatý přesným digestem.
P+n bodu 3 není zadané. Žádné kalendářové zápisy, odesílání, zpětný průchod
pošty ani rozšíření hodinové služby. Modelové role a Datův worktree beze změny.

Další krok: Po lokálním dokončení samostatně rozhodnout o p+n a vybrat jeden
skutečný e-mail pro přejímku. Ranní OS souhlas bodu 2 stále není potvrzený;
přípravu návrhů neblokuje, budoucí kontrolu kolizí a zápis ano.

Navrhované další kroky: Bod 4 — kolize a konečné potvrzení, až po samostatném
zadání. Diagnostika dřívějšího selhání Human–Adam zůstává zachovaná.

Technický důkaz: Cílené testy viz calendar_draft_targeted_20261107.log, plná
brána calendar_draft_full_gate_20261107.log, finální stav calendar_draft_verified_20261107.log.
Jeden skutečný Terra tah nad umělým e-mailem PASS, 7171 vstupních / 214 výstupních
tokenů; správné datum, 10:00–11:00, Europe/Prague, místo a odkaz, žádný retry
a žádná skutečná pošta. Pojmenovaný omezený profil ověřen také prázdným vláknem
bez modelového tahu. Browserový kontrakt ověřuje rozepsané změny, opožděný GET,
revizi, nejistý POST a zákaz nového pokusu. Safari vrací cgWindowNotFound, takže
vizuální přejímka zůstává otevřená. Soukromé vstupy/účtenky nejsou v Gitu;
nový TVBCP nebyl domluvený a nevzniká.

## 2026-11-07 09:27 CET — Kalendářový vývoj ověřen a společné p+n schválené

Hotovo: Vývojová plná brána bodu 3 prošla: 2726 testů, 31 SKIP, bez selhání
(441,869 s unit část). Bodový čas termínu úkolu nevyžaduje konec ani délku
schůzky. Statická brána a cílené kontroly PASS.
Rozhodnutí: Míla nyní výslovně zadal p+n včetně Datova b4b72ab0, který ruší
placený hlasový pilot. Starší hlasové opravy A–G se samostatně nenasazují.
Další krok: Převzít přesný rušící commit a předat společný merge head Terře.
Navrhované další kroky: Vybraný skutečný e-mail a bod 4 kolizí samostatně.
Technický důkaz: logs/calendar_draft_full_gate_20261107.log; společné vydání
dle logs/calendar_draft_retirement_release_20261107.log a *_verified_*.log.
Tento zápis nepředstírá dokončené nasazení. Soukromé účtenky zůstávají private.

## 2026-11-07 — Will: společný balíček kalendáře 3 a zrušení hlasového pilotu

Míla výslovně schválil p+n včetně Datova rušícího `b4b72ab0`. Will jej
začlenil nad kalendářový `afb7c9cf`; starší hlasové opravy se samostatně
nenasazují. Bod 15/P2 je definitivně ukončen, historické přejímky E/F/G
ani iPhone Start již nejsou dalšími kroky. Data má dál vlastní worktree.

Při řešení konfliktů zůstaly všechny kalendářové a Ateliérové cesty i pět
ostatních rolí; odstraněná je pouze role read_only_voice a zapojení placeného
pilota. Na main se přebírá přesných 14 verzovaných odstranění; Datových deset
generovaných souborů se týkalo jen jeho worktree. Soukromé důkazy a audio se
nemažou. Běžné předčítání, nahrávání pokynů a audio Camina zůstávají zachované.
203 integračních testů PASS; po opravě zastaralého testu zakázané hlasové role
samostatně 10/10 PASS. Rychlá statická a plná publikační brána jsou podmínkou
vydání. Kalendářový vývoj před integrací: 2726 testů OK, 31 SKIP; jedno
syntetické živé modelové ověření PASS. Skutečný e-mail ani kalendář se neměnil.

P+n provede jediný registrovaný vykonavatel Terra pro project-email-cases
(společný Cockpit). Tento zápis vzniká před publikací; konečný provozní stav
určuje přesná účtenka a logs/calendar_draft_retirement_release_20261107.log,
čerstvé ověření logs/calendar_draft_retirement_verified_20261107.log.
Po dokončení ověřit 404 bývalého panelu/API, nové e-mailové UI a běžné audio.
Fyzická Mac/iPhone přejímka nového kalendářového editoru a oprávnění aktuálního
EventKit buildu zůstávají oddělené; bod 3 nevytváří kalendářové události.

## 2026-11-07 13:40 CET — bod 4, upozornění a odvozené časy

Hotovo: Editor doplňuje datum konce a počítá délku z časů v uvedeném pásmu,
včetně DST. Přes půlnoc se konec neposouvá bez pozdějšího data. Ručně zadaná
délka bez koncového času zachovává správné skutečné datum konce. Vícedenní
uživatelské datum se nepřepisuje. Původ výpočtu se odlišuje od citace modelu.
Upozornění jsou standardně 24 hodin a 60 minut před začátkem/termínem;
každé lze vypnout, volba se uchová. U celodenní schůzky se počítají od půlnoci
a koncové datum je výlučné. Celodenní termín bez hodiny vyžaduje pro náhled
upozornění upřesnit čas. Upozornění se zatím neplánují do OS: skutečný zápis
události a alarmů patří bodu 5.

Hotovo: Zkontrolovat kolize a zobrazit náhled načítá výhradně vybrané kalendáře
v přesném omezeném období návrhu, i mimo výchozích 30 dní přehledu. Konečný
náhled obsahuje celý interval, místo/odkaz, přesný cíl, čtené kalendáře, kolize
a konkrétní časy upozornění. Potvrzení vyžaduje kontrolu údajů/citací a zvlášť
přijetí kolizí, jsou-li přítomné. Znovu čte kalendáře; změněný obsah nebo
vypršení ukáže nový náhled bez přeneseného souhlasu. Revize, source digest,
výběr/cíl, upozornění, kolize a pětiminutová platnost brání použití starého
potvrzení. Chybějící oprávnění/cíl, neúplný výsledek či chyba čtení potvrzení
neumožní. Souběžné změny na jiném zařízení zamknout nelze. Potvrzení neprovádí
zápis kalendáře a není povolením obejít čerstvou kontrolu v budoucím bodu 5.

Rozhodnutí: Míla výslovně požádal o automatické datum/délku, obě výchozí
upozornění a pokračování vývoje. Pokračování znamená bod 4 podle přijatého
plánu, vykonavatel Will. Nové p+n tím nebylo zadáno.


Další krok: místní checkpoint po plné bráně; samostatně schválené p+n a fyzická
přejímka nového editoru. Navrhované další kroky: bod 5 — jediný skutečný zápis,
uložení obou alarmů do EventKitu a ověření výsledku; bod 6 — přejímka iPhonu.

Technický důkaz: 112 cílených testů PASS a dalších 45 finálních regresních
kontrol PASS včetně nových závodů/vypršení. Plná brána a finální checkpoint dle
logs/calendar_review_full_gate_20261107.log a calendar_review_verified_20261107.log.
Skutečné omezené čtení čtyř vybraných kalendářů PASS, cíl zapisovatelný,
build i uložený přehled beze změny; pouze agregáty v
logs/calendar_review_native_live_20261107.log. Žádný skutečný e-mail, nový
modelový tah, kalendářový zápis ani restart/službový upgrade. Hodinový agent,
role a Datův samostatný worktree beze změn. Nový e-mailový TVBCP nedohodnutý.

Doplnění ověření: skutečné Safari nad oddělenou syntetickou zprávou a kalendářem
prošlo změnou koncového času 11:00 → 11:01 (délka ihned 61), uložením, náhledem
obou konkrétních upozornění, kolizí a odděleným souhlasem k potvrzení. Screenshot
zkontrolovaný; původní panel obnovený a vlastněný QA server zastavený. Nejde o
přejímku skutečného e-mailu/iPhonu. Důkaz logs/calendar_review_safari_20261107.log.
Plná vývojová brána PASS: 2656 testů, skipped=31, 496,185 s unit část.
Poslední drobná CSS oprava skrytých souhlasových řádků ověřená následně
28 frontend/HTTP testy a znovu ve skutečném Safari; oba výchozí alarmy zaškrtnuté,
souhlasy před náhledem skryté. Změna persistence a potvrzování byla ověřená
plnou bránou; finální CSS pokrývají doplňkové kontroly a rychlá statická brána.

## 2026-11-07 14:04 CET — Will: společné schválené Terra p+n

Hotovo: Do hlavního checkoutu převzatý Datův commitovaný REC-01 až REC-04
rozsah 29de7f05, dc528b45, d8b3d066, e8bb4b12, d5651110 nad kalendářovým
9f7ce93e. Rozpracovaný REC-05 v Datově vlastním worktree zůstává zachovaný.
Konflikty zachovávají všechny současné role (Email/Ateliér) i přidaný parser
RECOVERY_ROLE, oba seznamy workflow a všechny testy. Centrální JSON beze změny:
recovery_document_maintainer není aktivovaný. Sdílený helper zachovává named
profile/disabled_features a doplňuje Datovo vypnutí plugins/skills. LL nového
REC proudu přeznačené na 106–108, aby nepřekryly existující záznamy.

Rozhodnutí: Míla výslovně zadal všechny hotové Willovy i Datovy commity pro
Terra p+n. Jde o společný runtime Cockpitu, předání project-email-cases; nový
plánovač, placený REC pilot, produkční TXT/iCloud publikace a nová role se
neaktivují. REC-04 writer zůstává jen pro izolované testovací kopie.

Další krok: jediný registrovaný submit_release(wait=True), zmrazený společný
merge head a Terra z centrálního auditu. Výsledek publikace se neodvozuje z
tohoto předběžného zápisu: autorita logs/calendar_recovery_release_20261107.log
a logs/calendar_recovery_verified_20261107.log a přesná runtime účtenka.

Navrhované další kroky: kalendářový bod 5 (jediný zápis včetně alarmů) až jako
další vývoj; REC-05/06 v Datově samostatném proudu, původní přejímky zachované.

Technický důkaz: 198 cílených integračních testů PASS. Plná společná brána,
smoke, přesné nasazení a CI jsou podmínkou vydání; zajišťuje registrovaný worker
a následná kontrola Willa. Žádná změna hodinové kopie, produkčního návodu,
iCloud cílů, služeb Camina či autosave mimo standardní chráněné vydání Cockpitu.

## 2026-11-07 14:18 CET — oprava přenositelnosti testu po publikační bráně

Hotovo: Test návrhu plist používá vlastní TemporaryDirectory s připraveným
interpretem a skriptem. Ověřuje pouze vytvoření specifikace bez změn fixture;
nový negativní scénář zachovává odmítnutí chybějícího Pythonu nebo skriptu.
Produkční launcher ani služby se nemění. 125 REC testů PASS.

Rozhodnutí: Původní přesná účtenka d525499100547f133a7214951cc661dd zůstává
zachovaná v attention/push_state=uncertain. Diagnostika doložila jedinou chybu
v plné bráně (2780 testů, 49 SKIP): lokální .venv chybí v izolovaném profilu.
GitHub živě stále 9730a662. V github_batch.py brána vyhazuje výjimku před
_push_exact_head, tedy tento pokus žádný Git push neprovedl; nasazení nezačalo.
Nejde o opakování nejasného síťového push. Po opravě vzniká nový commit a nový
přesný balíček podle stále platného Mílova p+n.

Další krok: nové registrované předání v2; autorita aktuálního vydání
logs/calendar_recovery_release_v2_20261107.log a calendar_recovery_verified_20261107.log.
Technický důkaz selhání: logs/calendar_recovery_gate_failed_fixture_20261107.log;
oprava: logs/calendar_recovery_fixture_fix_20261107.log. Produkční REC aktivace
zůstává vypnutá a Datův REC-05 ve vlastním worktree zachovaný.

## 2026-11-07 14:33 CET — Will: převzetí dodatečně dokončeného REC-05

Hotovo: První balíček 135f46e7 je potvrzeně pushnutý a nasazený (Terra job
10fcd19ea7f50889a1f1424679e70b9b, 2781 testů, smoke 5/5). Během jeho běhu
Data commitnul aa18a6e7. Will podle Mílova pokynu všechny commity přebírá i tento
REC-05 do navazujícího přesného vydání. Celý kalendář/REC-01 až REC-04 zůstává.
Nový plánovač má pouze sandboxové callbacky a produkční run/tick jsou stále
activation_required. Žádná role, služba, skutečný návod ani modelový pilot se
neaktivují. REC-06 má samostatné dosud otevřené předpoklady a oprávnění.

Hotovo: Zachovaná launcher X_OK kontrola. Fixture mají vlastní spustitelný
wrapper k aktuálnímu interpretu a odkaz na skutečný CLI pro minimal-PATH test;
žádná závislost na .venv izolovaného publikačního profilu. Validace produkce
není oslabená. 199 cílených testů PASS; skutečný read-only environment preview
v hlavním checkoutu PASS (bez launchd/auth přejímky, bez služby/modelu).
LL-100 z nového proudu přeznačen na LL-110, historické záznamy zachované.

Rozhodnutí: pokračuje původní výslovné p+n všech hotových commitů, nikoli
aktivace automatického běhu. Datův worktree zůstává oddělený.


Další krok: navazující Terra p+n, nová přesná účtenka a nejnovější GitHub CI.
Autorita výsledku logs/calendar_recovery_rec05_release_20261107.log a
logs/calendar_recovery_verified_20261107.log. Důkazy předání předchozího balíčku
zůstávají calendar_recovery_release_v2_20261107.log a *_verified_phase1_*.log.
Technický důkaz: logs/calendar_rec05_targeted_20261107.log a
calendar_rec05_environment_20261107.log. Plná brána posledního balíčku je
povinná u registrovaného workeru. Bez změny hodinové kopie, výběru kalendářů,
produkčních TXT/iCloud kopií nebo aktivace plánovače.

## 2026-11-07 19:26 CET — jednoduchý soukromý kalendář a potvrzený zápis

Hotovo: Jedna karta se čtyřmi poli, automatická příprava/ukládání/kontrola,
jedno tlačítko pro zápis a samostatný create-only helper s oběma alarmy.

Rozhodnutí: Míla schválil zjednodušení pro soukromé účely; výslovný konec
má přednost před hodinou. Bez nového p+n; poslední nasazení 2909ea5a.

Další krok: po samostatně schváleném p+n povolit přesný writer na Macu a
potvrdit jednu konkrétní skutečnou událost pro přejímku.

Navrhované další kroky: přejímka na iPhonu. Nový TVBCP nevzniká bez dohody.

Technický důkaz: report calendar_simple_20261107.md; úplná brána
logs/calendar_simple_gate_20261107.log a nativní build
logs/calendar_simple_native_20261107.log. Skutečný EventKit zápis ani nový
modelový tah nebyly spuštěny. Browser QA blokuje nedostupné okno/host; neprošla
fyzická přejímka. Hodinový e-mailový runtime, placený hlas a Data worktree se nemění.

## 2026-11-07 21:47 CET — první skutečný zápis do kalendáře macOS

Hotovo: Mílou konkrétně potvrzený test uložen do nastaveného cílového
kalendáře; začátek/konec, Praha i alarmy 24 h/60 min ověřené novým nativním
čtením. Jeden create, jeden čistě čtecí recover. Přehled Cockpitu obnovený,
obsahuje právě jednu odpovídající událost. Potvrzovací karta vyčištěná.

Rozhodnutí: Výslovné „ano“ potvrdilo dříve zobrazený test 8. 11. 2026
10–11. Událost zůstává uložená. Nejde o souhlas s dalším zápisem ani p+n.

Další krok: samostatně schválené p+n nové jednoduché karty; její kód je stále
pouze lokálně. Pro zobrazení uloženého testu stačí obnovit Kalendář v Cockpitu.

Navrhované další kroky: vizuální přejímka na Macu/iPhonu a kontrola přenosu
na druhé zařízení. Nový TVBCP není domluvený a nevzniká.

Technický důkaz: logs/calendar_writer_macos_acceptance_20261107.log.
GUI grant přesného writeru full_access; oba native požadavky parent_pid=1.
První read-back měl všechny potvrzené údaje i alarmy, ale prázdné event_id;
Python správně ponechal unknown. Původní identita následně dohledána čtecím
recover s neprázdným ID a stejnými údaji, bez druhého create. Privátní žádosti,
ID i kalendáře zůstávají mimo Git. Žádný modelový tah ani reálný e-mail,
změna hodinové kopie nebo Data worktree. Příčina přechodně prázdného ID nebyla
určena; samotné místní uložení není důkaz synchronizace na druhé zařízení.

## 2026-11-07 23:41 CET — Měsíční agenda pod připomenutími

Hotovo: Lokální Cockpit pod důležitými připomenutími ukazuje nejprve úkoly
a termíny z kalendářů, potom schůzky a další události na příštích 30 dní.
Poslední načtený přehled se zobrazí ihned a čerstvé čtení běží na pozadí;
obnovuje se při návratu a každé dvě minuty viditelné stránky. Nezpomaluje
hlavní status. Datum aktualizace, tlačítko Obnovit, šest položek a rozbalení
zbytku jsou součástí přehledu. Při chybě zůstanou starší údaje s upozorněním.

Rozhodnutí: Míla upřesnil kalendářové termíny a povolil samostatný vývoj.
Čteme pouze již vybrané kalendáře původním podepsaným helperem, bez změny
macOS oprávnění, bez modelového volání a bez zápisu událostí. Typ přebíráme
z ověřené účtenky Samanthy; starší událost lze přes Typ označit pouze pro
tento přehled. Neznámý typ se nehádá podle názvu ani délky, zůstává mezi
ostatními událostmi. Označení je vázané na přesný kalendář, název a čas;
po jejich změně může být potřeba zopakovat. Stejné duplicitní položky
nelze jednotlivě označit. Žádný nový TVBCP nevzniká.

Další krok: samostatně schválené p+n měsíční agendy. Lokální vývoj hotový,
běžící Cockpit tento nový panel ještě neobsahuje.

Navrhované další kroky: po nasazení Mílova přejímka na Macu/iPhonu.

Technický důkaz: plná brána 2896 testů OK (31 SKIP), finálních 347 cílených
PASS včetně skutečných HTTP ochranných scénářů a Node UI kontraktu. Živé
čtení čtyř vybraných kalendářů PASS, 7 událostí, žádný kalendářový zápis;
původní čtečka i writer beze změny. Safari na syntetických datech ověřilo
rozložení, změnu typu 1/8 → 2/7, zachování po obnově a rozbalení zbytku.
Fyzický iPhone nebyl ověřený. Report reports/calendar_agenda_20261107.md;
logs/calendar_agenda_gate_20261107.log, calendar_agenda_targeted_20261107.log,
calendar_agenda_live_read_20261107.log a calendar_agenda_browser_20261107.log.
Předchozí navigace i jednoduché zadávání již nasazené v 0850e6f3, účtenka
1b8a9680c8b54bf7c48895a8267dc924, CI 42418270872 success; staré čekání
na jejich p+n je historie. Nové p+n tímto povoleno není.

## 2026-11-08 11:54 CET — Rychlé Zadání úkolu s upravitelnou hodinou

Hotovo: Lokální karta Komunikace → Kalendář → Zadání úkolu má jediné
textové pole, tři volby den/měsíc/rok a viditelný čas předvyplněný na 09:00.
Text lze zadat klávesnicí nebo systémovým diktováním iPhonu. Jedno stisknutí
Zapsat úkol potvrzuje přesný text, datum, čas a zobrazený cílový kalendář.
Po ověřeném uložení se text vyprázdní a přehled se obnoví i během cooldownu.
Úkol se automaticky klasifikuje mezi termíny. Samostatný odkaz a manifest
ikony míří přímo na tuto kartu; přidání na plochu provede Míla v Safari.

Rozhodnutí: Míla přijal rychlý formulář a 09:00, výslovně doplnil možnost
hodinu změnit. Pásmo Europe/Prague, typ task_deadline, alarmy 24 h/60 min.
Celý text včetně popisu/místa se uloží do názvu; AI nic nerozděluje.
Současný ověřený writer ukládá termín jako minutovou událost; nejde o
nový zápis do Apple Připomínek. Kolize schůzek nejsou bránou úkolu.
Zvolený kalendář se připne revizí/ID a jeho existence/zápisovatelnost se
ověří nativně při zápisu. Žádný Swift rebuild, nový OS souhlas ani model.

Další krok: samostatně schválené p+n lokálně ověřené nové karty.
Živý Cockpit tuto novou kartu ještě neobsahuje.

Navrhované další kroky: po nasazení Mílova přejímka na iPhonu a jednorázové
Přidat na plochu. Skutečný testovací zápis touto kartou zatím nepotvrzený.

Technický důkaz: 378 cílených testů PASS a posledních 5 HTTP/UI PASS; plná brána 2923 testů OK (31 SKIP).
HTTP testy ověřují skutečné host/origin ochrany, formulář, start_url a PNG.
Node scénáře ověřují 09:00, změnu hodiny, přestupný únor, jediný submit,
ztracenou odpověď, restart, status/recover a stejnou identitu při explicitním
opakování nedoručeného požadavku. Soukromá trvalá účtenka vzniká před
nativní akcí; neznámý výsledek se nikdy nepřeklopí na nový create. Jeden
automatický read-only recover řeší opožděné eventIdentifier v rámci téhož
potvrzení; další obnova je ruční a pouze čtecí. Ověřený nativní reader/writer
beze změny, pouze čtecí kontext nového formuláře PASS. Žádný skutečný event
nebyl vytvořen. Browser host unavailable a Safari cgWindowNotFound: fyzická
Mac/iPhone přejímka je otevřená. Ikona vizuálně zkontrolovaná; vlastní
syntetický QA server ukončený, žádná karta prohlížeče nevznikla.
Důkazy: logs/calendar_task_targeted_20261108.log, calendar_task_gate_20261108.log,
calendar_task_live_read_20261108.log, calendar_task_ui_20261108.log.

## 2026-11-08 12:28 CET — Oprava chyby přípravy úkolu před odesláním

Hotovo: Lokální oprava dovolí použít rychlé zadání také v prohlížeči, kde
není dostupné crypto.randomUUID. Identita zadání vzniká přes silné
crypto.getRandomValues. Při prokazatelném selhání před odesláním se pole
neuzamknou, text/datum/čas zůstávají a lze zkusit odeslání znovu. Pokud
se identita stihla uložit, zachová se původní payload a ověřuje pouze
stejný ID. Při nedostupném či nejasném úložišti je blokované jen další
odeslání; text je přístupný pro zkopírování. Kalendářový backend beze změn.

Rozhodnutí: Míla ohlásil zašedlý formulář a zprávu Zadání se nepodařilo
bezpečně uchovat, Neodesláno, Obnov stránku. Nejde o potvrzenou chybu
macOS zápisu. Při prvním agregovaném serverovém auditu nebyla žádná
účtenka zadání. Stejný stav byl reprodukovaný v profilu bez randomUUID
s funkčním úložištěm. Konkrétní schéma adresy Mílova prohlížeče zatím
nepotvrzené; stejný catch původně schovával také chyby zápisu úložiště.
Předchozí obecná rada obnovit stránku mohla ztratit neuložený text; nová
zpráva jej ponechává. Žádný slabý Math.random ani obcházení idempotence.

Další krok: samostatně schválit p+n ověřeného nového opravného commitu. Současný živý základ 6c610287 byl skutečně
Terrou nasazený (d7ac821490a17273e18be1de270b9ba8, 2923, smoke 5/5,
CI 42474671842 success); neprohlašovat opravu za nasazenou.

Navrhované další kroky: po nasazení Mílův retest na stejné adrese.

Technický důkaz: red→green Node regrese HTTP bez randomUUID, test
chyby setItem s editovatelným formulářem a následným jediným POST,
částečného uložení s read-only status a stejným ID, absence silného RNG
bez odeslání. 26 cílených PASS; plná brána 2923 testů OK (31 SKIP).
Důkazy logs/calendar_task_storage_repro_before_20261108.log,
calendar_task_storage_node_20261108.log, calendar_task_storage_targeted_20261108.log,
calendar_task_storage_gate_20261108.log a calendar_task_storage_diagnosis_20261108.log.
Žádný skutečný kalendářový zápis ani změna helperů/grantů/modelů.
Čtecí inventář UI: žádné připojené browser tabs a žádné Safari okno;
přímá přejímka Mílova prohlížeče nebyla dostupná.

## 2026-11-08 14:56 CET — Mazání jednotlivé události z Cockpitu

### Hotovo
- Tlačítko Smazat z kalendáře v měsíční agendě a seznamu schůzek, i po
  úspěšném uložení úkolu nebo události z e-mailu. Potvrzení ukazuje přesnou
  událost; u opakování maže jen tento výskyt. Po ověření se přehled obnoví.
- Nová oddělená mazací část zachovává původní reader/writer. Změněné nebo
  nejednoznačné události a pozvánky s účastníky/organizátorem nemazá.

### Rozhodnutí
- Míla schválil vývoj navržené jednotlivé potvrzované operace. P+n nového
  kroku dosud nezadal. Žádné skutečné události se při vývoji nemažou.
- Nejistý pokus se neopakuje; serverová identita a nativní cílový zámek
  přežijí timeout/pád. Jen čtecí obnova původní účtenky.

### Další krok
- Samostatné p+n; poté jednorázové Povolit mazání na Macu a Mílova přejímka
  potvrzovacího okna, nejprve bezpečně přes Zrušit.

### Navrhované další kroky
- Přejímka vybraného odstranění na Macu/iPhonu. Pozvánky s účastníky řešit
  dál v aplikaci Kalendář; hromadné nebo celé série se nenabízejí.

### Technický důkaz
- 112 cílených testů PASS, 15 scénářů produkční Swift transakce s fake
  EventKit a reálný podpis/self-test v izolaci PASS. Plná brána dle
  logs/calendar_delete_full_gate_20261108.log (3174 OK /31 SKIP); report calendar_delete_20261108.md.
- Nový helper není provozně instalovaný/autorizovaný; původní instalované
  helpery shodné. Skutečný kalendářový zápis/mazání: 0. Bez push/nasazení.

## 2026-11-08 17:30 CET — Oddělení ikon hlavního Cockpitu a rychlého úkolu

### Hotovo
- Hlavní Cockpit a kalendář mají nově společné instalační údaje se startem
  v hlavním přehledu; Nový úkol zachovává vlastní identitu a start formuláře.
  Doplněná nápověda přidání obou ikon zvlášť přes Safari.

### Rozhodnutí
- Míla ohlásil obnovování poslední stránky při přechodu mezi ikonami. Způsob
  jejich vytvoření dosud nepotvrdil; pracovní předpoklad Safari.
- Není přidaný automatický reset při návratu do aplikace, který by mohl
  opustit rozepsaný formulář nebo aktivní operaci. Žádné mazání ikon/dat.

### Další krok
- Samostatné p+n a přejímka na iPhonu s novými odlišně pojmenovanými ikonami
  z přesných stránek / a /calendar/task/. Staré ikony zatím zachovat.

### Navrhované další kroky
- Zopakovat Mílův scénář kalendář → Nový úkol a úkol → hlavní; rozlišit
  novou instalaci, existující starou ikonu a obnovu již běžícího okna.

### Technický důkaz
- 36 cílených testů a statická brána PASS; žádná kalendářová mutace.
  Report cockpit_home_icons_20261108.md a logs/cockpit_icons_*_20261108.log.
- Živý audit: hlavní stránka i kalendář zatím bez manifestu, task s vlastním.
  iOS resume není místně reprodukované; metadata nejsou zárukou resetu okna.
- Předchozí f51f3412 nasazený, CI success a Míla potvrdil funkční mazání.
  Nesouvisející neversionovaný obnovovací TXT se nečte, nemění ani necommituje.


## 2026-11-08 18:22 CET — Hodinové kalendářové návrhy se zachováním ručního průchodu

### Hotovo
- Volitelný doplněk nového e-mailového posouzení připraví schůzku nebo termín
  s původním citačním kontraktem. Není potřeba druhý modelový průchod ani další
  načtení pošty pro otevření připraveného návrhu.
- Stejné tlačítko Do kalendáře předá výsledek do stejného čtyřpolového editoru.
  Původní kolize, výslovný zápis, alarmy 24 h/60 min a čtecí obnova se používají dál.
- Staré karty nemigrují a zůstávají na původní ruční cestě. Existující rozpracovaný,
  nejistý nebo zapsaný návrh má před doplňkem přednost a nelze jej importem přepsat.
- Chybná volitelná citace nezahodí e-mailový koncept; v přehledu zůstává viditelný
  agregovaný problém. Formální pozvánky/opakování dál vyžadují ruční zpracování.

### Rozhodnutí
- Míla schválil navázání na bod 7 s podmínkou zachovat fungující implementaci.
- Doplňující obálka je mimo EmailProposal i jeho potvrzovací digest; starý
  e-mailový editor, archiv a odesílání zachovávají svůj dosavadní kontrakt.
- Výchozí calendar_suggestions=false. Aktuální service.json, modelové role,
  instalovaná hodinová kopie, pomocníci EventKit a jejich OS souhlasy beze změny.
- Ikony c14f2524 jsou odložené, nejde o jejich nové p+n. Chráněný obnovovací TXT
  ani Datův worktree se nemění. Poslední živě ověřený Cockpit je f51f3412.

### Další krok
- Převzít lokální změnu; před zapnutím zvlášť přijmout ruční Mac/iPhone
  průchod a domluvit p+n/registrovaný upgrade vlastní hodinové kopie.

### Navrhované další kroky
- Po kompatibilním Cockpitu i službě teprve výslovně zapnout doplněk pro nové zprávy.
- Na vybraném skutečném e-mailu ověřit správnost návrhu a cenu celého posouzení.
- Změřením porovnat dobu/usage; jeden tah není důkaz stejné ani nižší ceny.

### Technický důkaz
- 214 cílených testů PASS, včetně 20 nových doménových/adapterových scénářů
  a HTTP průchodu, import → kolize → potvrzení → jeden syntetický zápis.
- Existující source_context přemístěný beze změny AST. Browser kontrakty e-mailu
  a kalendářové karty PASS. Závěrečná plná brána 3199 testů OK (31 SKIP); logs/calendar_hourly_full_gate_v2_20261108.log.
- Žádný skutečný modelový test, e-mailový send, kalendářový zápis/mazání, p+n
  nebo servisní aktivace. Skutečná modelová kvalita, spotřeba a fyzická přejímka otevřené.


## 2026-11-09 11:30 CET — Obnovený hodinový e-mailový agent po nekompatibilní roli

### Hotovo
- Vlastní hodinová kopie je registrovaně upgradovaná z f2d6ef79 na již
  publikovaný617f3e0d. Installed/owned/loaded/enabled a skutečný parser PASS.
- První skutečná kontrola dnešního slotu11:00 dokončena v11:28:47 CET:
  7 nových zpráv,3 karty k potvrzení a4 zprávy hodinového přehledu. Živé
  Cockpit overview API ověřilo3 karty a3 přehledové zprávy; poslední nedůležitá
  zpráva je skrytá již existující visibility předvolbou. Všech7 položek je ve
  stavu zachovaných, soukromý obsah se neopisuje.
- Při systémovém přepnutí celý business stav, nastavení a všechny role
  shodné s předchozím snapshotem. Po běžném dočtení jsou všechny původní
  položky beze změny; zdrojové pozice se posunuly až zpracováním nových zpráv.

### Rozhodnutí
- Míla potvrdil přesnou globální brzdu i následné p+n. Použity pouze
  registrované pause/prepare/upgrade; starý release a servisní záloha zachované.
- Příčina: sdílený agent_roles.json již obsahoval recovery_document_maintainer,
  ale parser instalované f2d6ef79 ji neznal. AgentRoleError byl reprodukovaný
  právě v instalované kopii, před IMAP a modelem. Poslední dokončený slot
  před opravou8.11.20:00. Runtime nezačal zpracovávat dnešní poštu až do opravy.
- Terra/high, oba poskytovatelé, bez denního stropu a calendar_suggestions=false
  zachované. Žádná změna přístupů ke schránkám nebo recovery služby.
- Nový kód nebyl potřeba. Dokončovací commit obsahuje pouze Git-safe provozní
  záznam; Python služby se po něm nemění a nevyžaduje druhé přepnutí runtime.

### Další krok
- Dokončit výslovně schválené registrované p+n tohoto záznamu v project-email-cases.
  Autorita výsledku je původní účtenka a logs/email_role_compat_release_20261109.log.

### Navrhované další kroky
- Míla obnoví přehled Cockpitu a převezme3 nové karty.
- Při další nové roli předem ověřit všechny skutečné runtime parsery sdíleného JSON,
  včetně hodinové služby; samotný kompatibilní main nestačí.

### Technický důkaz
- reports/email_hourly_role_compat_20261109.md; logs/email_role_compat_upgrade_20261109.log.
- Soukromé důkazy jen v service_audits/role_compat_upgrade_20261109_1127:
  baseline, připravený plán, switch_checks, verified, první dokončený běh a HTTP projekce.
- Všechny kontroly přepnutí true; aktuální7 modelových posouzení jsou běžný
  již schválený příjem čekající pošty, ne opakování nejistého starého pokusu.
- První health completed, chybové posouzení0, zdrojové pozice posunuté;
  všechny původní položky shodné. Fyzická Mac/iPhone přejímka nepředstíraná.


## 2026-11-10 10:58 CET — Potvrzení kalendářové úpravy po návratu upozornění v jiném pořadí

**Hotovo:** Původní reálná úprava je ověřená a bezpečnostní blokace se uvolnila bez dalšího zápisu. Oprava porovnává stejná upozornění bez závislosti na jejich pořadí, skutečnou změnu dál odmítá. Rozhraní umožní obnovit systémový přístup a ověřovací lišta je viditelná i po scrollu.

**Rozhodnutí:** Míla prioritně nahlásil bug při potvrzení původního systémového upgradu. Původní nejasný save se neopakuje. Již zadané nasazení Datova commitu pokračuje spolu s opravou kalendáře; páteční aktivace a rozpočet zůstávají oddělené.

**Další krok:** Dokončit společnou plnou bránu, lokální checkpoint a registrované Terra p+n.

**Navrhované další kroky:** Mílova přejímka editace další jím vybrané položky na používaném zařízení; automatiku ScienceNews povolit až samostatnou dohodou.

**Technický důkaz:** Native reálný recover: edited_verified, calendar_writes=false, jediná shoda obou ID, všechna zachovávaná pole stejná, alarm_order_normalized=true. Původní update byl jediný. Swift FAIL→PASS, 87 cílených a mobilní headless fixture PASS; společná plná brána PASS: 3406 testů / 31 SKIP (620,186 s). Pošta už kompatibilně upgradovaná s identickým business digestem a 95 položkami. Důkazy v reports/calendar_edit_alarm_order_recovery_20261110.md a reports/email_science_role_upgrade_20261110.md.
