# ScienceNews — implementace 03/K4

Pracovní proud: `project-knowledge-library`. Data vyvíjí jen ve větvi
`data/parallel-20261104`; integrace s e-mailem a kalendářem zůstává Willovi.
Schválený filtr a UI: `projects/vedecke_clanky.md`, strukturovaná kalibrace
`reports/science_news_calibration_20261108.json`.

## Uživatelské chování

- Ikona `ScienceNews` na pravém konci horních tlačítek Cockpitu otevře sekci
  Vědecké novinky v Knihovně. Zelená a pulzující znamená nevyřízené zprávy,
  šedá znamená žádnou nevyřízenou zprávu. Omezení pohybu vypíná animaci.
- Každá zpráva obsahuje český abstrakt, funkční původní HTTPS odkaz, datum,
  obor, význam a nejistoty. Cizí obsah se vykresluje jako text, nikoli HTML.
- `Přeložit celou zprávu` otevře samostatné okno. Při neaktivním překladači je
  tlačítko vypnuté s viditelným vysvětlením; již hotový překlad lze dál otevřít. Samotné čtení ani překlad
  nevyřizují zprávu. Obnovení okna pouze čte stav a nespouští nový modelový tah.
- `Uložit zprávu` vytvoří jednu kartu science/health_info a zapne sledování.
  Uloží abstrakt, odkaz a již dokončený překlad, pokud existuje. Běžící překlad
  se nejprve dokončí, aby se jeho výsledek neztratil při uložení.
- `Sledovat` zapne sledování bez archivace článku. `Nezařazovat` vyřídí jednu
  zprávu bez sledování; nevypíná celý vědní obor. Všechny tři volby po ověřeném
  dokončení skryjí zprávu z fronty. Sledování lze následně vypnout v přehledu.
- Síťová chyba nemaže kartu a neoznačí celý přehled za prázdný. Stav neověřený
  má zvláštní označení; poslední známé karty zůstávají zobrazené.

## Soukromá persistence a opakovatelnost

`app.science_news.ScienceNews` drží jeden atomický `state.json` pod
`data/private/science_news/`; čtení prázdného stavu nic nezakládá. Zápisy mají
stabilní sidecar zámek a používají sdílené persistence helpery. Nejde o další
kopii celé Knihovny. Zdrojové podklady, odpovědi, překlady a provozní účtenky
zůstávají mimo Git. Veřejná kalibrační sada a redigované výsledky testů v Gitu
neobsahují plné články ani obsah uživatelovy Knihovny.

Rozhodovací operace má trvalé request_id, před zápisem uložený záměr a dokončení
ověřené v obou systémech. Identita je v browseru uložená před POST i na HTTP
bez randomUUID; nedostupné úložiště blokuje zápis, nikoli čtení novinek.
Dvojklik, ztracená odpověď a reconnect stejného příkazu nesmějí založit druhou
kartu nebo přepnout původní volbu na jinou. Archivní karta má deterministické
ID a create-only obsah. Adapter sdílí existující zámek Knihovny a registr;
reconciliation nepřepisuje pozdější ruční editaci. Automatické mazání není.

DOI, případně původní URL, spojuje kopie stejného objevu. Jednou vyřízený objev
se automaticky nevrací. Podstatná nová revize sledovaného tématu může mít
samostatnou identitu události odvozenou od nového zdrojového textu a data.
Starší či totožný podklad není nová revize. Model navrhuje věcnou návaznost,
program dovolí jen vazbu na existující aktivní sledované téma. Samotná citace
podkladu neprokazuje pravdivost celého vědeckého závěru; editorial QA zůstává
součástí skutečné modelové zkoušky a uživatelského hodnocení.

## Zdroje a týdenní běh

`app.science_news_sources` čte osm konkrétních RSS/Atom kanálů: Nature,
Nature Ecology & Evolution, Nature Genetics, Nature Medicine, Nature
Computational Science, Nature Physics, Nature Astronomy a NASA. Aktuální
čtecí zkouška je v `reports/science_news_sources_20261109.json`. Výběr je
záměrně omezený, nikoli úplné pokrytí světové literatury; převládá jeden vydavatel.
Původní CERN RSS vracelo 404 a NIH 403; nejsou vydávány za funkční kanály ani
se neobchází jejich odmítnutí. Rozšíření o nové vydavatele má vlastní čtecí test.

Síťové načítání má pevný seznam hostů, ověření TLS pomocí již instalovaného
certifi, kontrolu přesměrování, velikostní a časové meze. XML nepovoluje DTD
a entity. Sběr zahrne posledních sedm dní a nejvýše 60 kandidátů, rozdělených
mezi zdroje. Přetečení a zdraví každého zdroje jsou evidované. Již zpracované
podklady se vyřadí před modelovým voláním. Prázdná dávka model nevolá.

`app.science_news_runner.tick` připravuje páteční vydání od 08:00
Europe/Prague, publikuje od 09:00. Nejvýše pět zpráv, žádná oborová kvóta ani
výplň. Role dostává pouze veřejné výňatky, přijatou kalibraci a relevantní
sledované vědecké položky, nikoli e-maily nebo soukromou knihovnu. Výstup má
pevné JSON schema; zdrojové identity, URL, datum a DOI přidává program.
Význam i nejistoty jsou povinné; citace musí doslova existovat v podkladu.

Slot má před předáním trvalý marker. Příprava, raw odpověď a výsledek přežijí
restart. Připravené vydání lze jednou publikovat bez dalšího modelového tahu.
Nejistý či přerušený modelový výsledek se automaticky neopakuje ani další týden;
nejprve vyžaduje ověření stejné účtenky. Pokud žádný zdroj nefunguje, nevznikne
úspěšný prázdný přehled. Částečný výpadek je vidět u vydání.

## Kompatibilita před budoucí aktivací role

Převzetí fb708be9 do main nemění `config/agent_roles.json`. Samotný nový známý
název parseru tedy nepřidává schválení ani nerozbíjí dosavadní instalované čtenáře.
Před budoucím přidáním bindingu ale ověřit také samostatný hodinový e-mailový
runtime a ostatní skutečné čtenáře sdíleného JSON. Nasazení parseru Cockpitu
samo nestačí; nekompatibilní instalovaná kopie by odmítla celý config. Případný
upgrade služby má vlastní registrovaný postup a oprávnění (LL-070).

## Model a překlad: připravené, dosud neaktivní

`science_news_model` používá existující sdílený App Server socket, jedno nové
ephemeral vlákno a nejvýše jeden tah pro konkrétní job. Transport kontroluje
model, effort, cwd, readOnly bez sítě, never approval, payload a output schema;
Standard je vynucen per turn bez změny globálního Fast. Shell, web, apps, MCP,
skills a další agenti jsou vypnuté. Neočekávané nástrojové události neprojdou.
Nejistota, neplatný výstup nebo chybějící usage nesmějí vyvolat další tah.

Parser zná `science_news_editor`. Od 2026-11-10 je v Datově vlastním
`config/agent_roles.json` připravené navázání na Sol/medium, s cenovou kontrolou
10. 11. a skutečnou zkouškou 9. 11. V provozu tato role dosud chybí; Will musí
přenést pouze nový science_news_editor záznam a zachovat všechny další role main.
Samotné nasazení role není aktivace: soukromý schválený rozpočet a LaunchAgent
se instalují odděleně. Souhlasy s jinými rolemi se na tuto aktivaci nepřenášejí.

`config/science_news_activation.example.json` je pouze vypnutý návrh:
15 kreditů rezervace na job a 100 za místní kalendářní měsíc pro výběry i
ručně vyžádané překlady dohromady. Nejde o schválený rozpočet ani cenovou nabídku
konkrétního modelu. Program předem kontroluje konzervativní odhad, drží rezervu
i při nejistotě a ověřuje skutečnou usage po dokončení. Limity nejsou tvrdý
upstream billing/output cap. Bez centrální role a privátní schválené aktivace
se klient ani modelový tah nespustí.

Připravený kandidát pro další schválení je `gpt-6.1-sol / medium / Standard`.
Čtecí dotaz na existující socket potvrdil přítomnost modelu i podporu medium,
bez vlákna nebo modelového tahu; důkaz `reports/science_news_model_preflight_20261109.json`.
Oficiální sazby byly znovu načteny 2026-11-09:
https://learn.chatgpt.com/docs/pricing#token-rates — Standard 50 / 2,5 / 250
kreditů za milion input / cached input / output tokenů. Nejde o procento
subscription limitu ani účetní doklad. Korpus 60 aktuálních kandidátů měl
40 066 UTF-8 B; jednoduchý byte proxy adapteru s přijímací mezí 16 000 výstupních
tokenů vychází 6,10565 kreditu. Není to skutečná tokenizace, součástí není
zaručený odhad protokolové režie a žádné modelové volání tento odhad neověřilo.
Návrh 15/job a 100/měsíc proto zůstává rezervací pro samostatné schválení,
nikoli slibem skutečné ceny. Konkrétní návrh a hash podkladů:
`reports/science_news_budget_proposal_20261109.json`; veřejné RSS podklady jsou
jen v soukromém preflight adresáři. Role binding zůstává nezměněný.

Plný překlad se připraví asynchronně pouze po tlačítku. Načtení zdrojové
stránky je omezeno na schválené hosty a výslovnou licenci dovolující odvozené
zpracování (CC BY/BY-SA/CC0). Redakční import může dodat jiný ověřeně oprávněný
nebo uživatelem poskytnutý text. Abstrakt, nedostupný/paywall text a neověřená
licence se nezaměňují za kompletní zdroj. Dlouhý text se odmítne před tahem,
nikoli tiše zkrátí. Neúplný výsledek není označen jako plný překlad. Shoda
obsahu a odborné terminologie potřebuje také skutečnou uživatelskou přejímku.

## Registrované vstupy

- GET `/api/science-news`: fronta, sledování, historie vydání a aktivace; bez modelu.
- POST `/api/science-news/decision`: item_id, action save/follow/dismiss, request_id.
- POST `/api/science-news/unfollow`: topic_id.
- POST `/api/science-news/translate`: item_id, explicitní uživatelský požadavek.
- GET `/science-news/translation?id=...`: samostatné čtecí okno.
- GET `/api/science-news/translation?id=...`: pouze stav a hotový překlad.

POST trasy jsou v COCKPIT_POST_ACTIONS a používají společnou kontrolu
Host/Origin. Opakované akce i neočekávané zdrojové odkazy mají vlastní testy.

`scripts/science_news.py status|preview|service-preview|tick` mají přesné argv
v shell registru. `status` nic nepíše, `preview` jen čte zdroje bez modelu,
`service-preview` jen vrací plist bez instalace. Ruční `tick` přes shell registr
potřebuje potvrzený workflow a samostatně platnou aktivaci; plánovač používá
jednou schválenou aktivaci s vlastními rozpočtovými a slotovými branami.
Redakční JSON lze do soukromé fronty
vložit pomocí `import --input ... --editor-reviewed`; neukládá články do Knihovny.

## Přesný další integrační krok

1. Will převezme pouze schválený Datův commit do svého aktuálního main;
   vyřeší případné malé konflikty v Cockpit trasách, šabloně a snapshotu assetů.
   Nemigrovat ani nepřepisovat sdílená provozní data nebo jiné modelové role.
2. Po samostatně schváleném p+n registrovaným postupem ověřit doručenou verzi
   UI/API a přejmout tři syntetické karty na Macu i iPhonu. Vyzkoušet všechny
   volby, reconnect a poslední zelená → šedá. Bez placeného editoru.
3. Připravit a schválit konkrétní model/effort/cenu pro science_news_editor a
   jeden malý živý editorial/translation test. Čistě syntetické testy nejsou
   živým důkazem kompatibility runtime ani kvality vědeckého výběru.
4. Teprve v kompatibilně nasazeném runtime navázat novou centrální roli, zapsat
   schválenou soukromou aktivaci a samostatně povolit instalaci LaunchAgentu
   z service-preview. Použít skutečný provozní checkout, nikoli Datův dočasný
   worktree. Aktivace zajistí log adresář před bootstrapem. Páteční 09:00 se
   počítá v Europe/Prague, takže přechody letního času nemění místní hodinu.

V této etapě bez p+n, role bindingu, placených tahů, bootstrapu/restartu služby,
zápisu do živé Knihovny a bez provedení rozhodnutí nad kalibrační sadou.


## Jediný překladový kandidátní pilot (2026-11-09)

Přesná karta: `reports/science_news_translation_preflight_20261109.json`.
`app.science_news_trial.preview()` je neplacená kontrola otisků včetně kódu a
kritických závislostí; nečte živou frontu ani nezakládá pokus.
`run` vyžaduje confirmed, přesné report/packet SHA-256 a approval_ref skutečného
souhlasu. Před vytvořením klienta atomicky uloží jediný pevný pokus; po unknown
ani attention neexistuje nový request ID či automatický retry. Katalog se čte
před tahem, bez náhrady modelu. Existující OneTurn vynutí jediný read-only
thread/turn, vypnuté nástroje a per-turn Standard; globální preference nemění.
Raw odpověď i usage se uloží před kontrolou doručení, formátu a ceny. Stav review
vyžaduje ještě lidské ověření úplnosti/významu; délka a complete=true nejsou důkaz
sémantické správnosti. Do živé zprávy nic nepřenáší a centrální roli neaktivuje.

Zdroj je vlastní redakční tělo tiskové zprávy NIH včetně nadpisu, data, podtitulku,
grantu a reference; mimo rozsah jsou institucionální boilerplate, navigace,
obrázky a samotný článek Nature. Přímé HTTP 403 není obcházeno; znění dodal
veřejný index oficiálního NIH webu a pravidla opětovného užití byla čtena na NIH FAQ.
Není přidána plošná automatická public-domain výjimka pro doménu.

Návrh jediné placené zkoušky: gpt-6.1-sol / medium / Standard, 90s timeout každého transportního čekání (nikoli celkový běhový strop), 3507 vstupních bajtů v plánovací proxy + 16000 přijatelných
výstupních tokenů => 4,17535 kreditu, navržená přijímací mez 5 kreditů.
Proxy není tokenizace, faktura ani tvrdý provider limit. Neurčitý timeout
blokuje druhý pokus i při neznámém účtování. Míla následně schválil tento přesný jeden pokus; provedení je oddělené od zmrazené přípravné karty.

Kreditový pilot před vytvořením vlákna ověří `account/read` bez refreshToken:
jen `type=chatgpt`; API klíč a neznámý účet blokují placený tah. Celý účet,
e-mail ani jiné identifikační údaje se do podkladů nebo účtenky nekopírují.


### Výsledek skutečné zkoušky 2026-11-09 23:32 CET

`reports/science_news_translation_trial_20261109.json`: jediný pokus dokončen,
state=review, usage 6980/1002 (input/output), 0,5995 Standard kreditu pod mezí 5.
Programová raw účtenka se nepřepisuje, Datovo následné porovnání je v samostatném
private `semantic_review.json` a text v `crispr-preklad-cs.txt` v témže adresáři.
Všech devět odstavců, reference, grant a numerické/klinické nejistoty prošly Datovou
kontrolou; Mílova čtenářská přejímka ještě chybí. Receipt review není samo aktivací.

Přípravný report se po běhu nemění: jeho hash je součástí konkrétního souhlasu i
účtenky a jeho pole prepared/0 paid zůstávají historickým plánem. Aktuální výsledek
vždy číst z výsledkového reportu/účtenky. Neměnit request ID, nezaložit nový pokus
ani při potřebě znovu zobrazit výsledek. Kód ani produkční data se při provedení
neměnily. Přenos hotového překladu do existující položky potřebuje vlastní omezenou
registrovanou operaci a oprávnění; model pro stejný zdroj se znovu nevolá.

6980 skutečných vstupních tokenů zahrnuje runtime/protokolovou režii; vstupní
byte proxy 3507 nebyla horní mez účtovaného vstupu. Cenu vyhodnocovat z jedinečné
usage účtenky a nebrat plánovací 4,17535 za fakturu či upstream billing limit.


### Převzetí pilotu do současného main (Will, 2026-11-09)

Převzaté 9abeb797 + 3ba4d063 jsou kód/UI a historický důkaz jediného hotového
pokusu. Převzetí ani p+n neopakují překlad a nepřipojují text do provozní karty.
Zmrazený report, jeho původní závislosti a private zdroje zůstávají u Data;
nezměněné otisky se nepřepočítávají pro nový main ani se nekopírují private
podklady. Čtecí preview na jiném kontextu může správně odmítnout chybějící
zdroje či odlišné závislosti; není to pokyn vytvořit nový placený pokus.
Přejímka a předání: `reports/science_news_two_commits_integration_20261109.md`.

## Uložení celého českého článku a aktivace — 2026-11-10

Míla zadal páteční spuštění a konkrétní uložení CRISPR. Článek je již v živé
Knihovně / Vědecké články s celým hotovým českým překladem, původním odkazem
a zapnutým sledováním. Zpětně ověřeno celé tělo, jobs modelu beze změny, fronta 0.
Neplacená registrovaná operace `science_news_cached_translation.attach_and_save`
kontroluje oba otisky, URL, rozhodnutí a rozpracované/nejisté operace. Po přenosu
použije původní durable save s archivním zámkem. Neexistuje nový placený pokus.

Nové uživatelské Uložit v UI i serverovém API vyžaduje dokončený český překlad.
Nejprve Přeložit celou zprávu, potom Uložit zprávu. Sledovat/Nezařazovat zůstávají
použitelné. Překlad sám nic nearchivuje. UI obnoví dostupnost po návratu do okna
nebo pravidelném čtení stavu. Jen explicitní translation_required a
operation_started=false uvolní UUID nezahájeného požadavku; jakákoli nejistota ho drží.

`science_news_model` před vláknem ověří účet ChatGPT. Měsíční kontrola počítá
skutečný odhad již dokončené spotřeby a plné rezervy nedokončených/nejistých úloh.
Návrh 15/job a 100/měsíc proto není omezením na šest dokončených úloh. Zůstává
rezervační/přejímací kontrolou, nikoli tvrdým provider billing cap.

### Přesné předání Willovi a spuštění

1. Převzít pouze nový Datův commit. V config/agent_roles.json doplnit pouze objekt
   science_news_editor; nepřevzít celý Datův soubor a neztratit další role main.
   Provozní parser tuto kombinaci již přijal v oddělené čtecí zkoušce.
2. Cíleně ověřit změnu v aktuálním main a samostatně autorizovaně nasadit. Musejí
   být nasazené science_news_model.py (účet/rozpočet), cockpit_science_news.py
   a science_news.js (české Uložit). Installer kontroluje i skutečně servírovaný
   guard z běžícího Cockpitu se správným cwd; samotné soubory nestačí.
3. V Data worktree neplaceně ověřit `science_news_activation.prepare(runtime_root=...)`
   pro doložený provozní cwd. Aktuální návrh je private pod science_news_activation,
   první vydání 13. 11. 2026 v 09:00 Europe/Prague, příprava od 08:00, max 5 zpráv.
   Pokud se změnily jinak schválené nasazené závislosti, obnovit pouze neplacený návrh
   po kontrole změn. Neopakovat jednorázový modelový pilot.
4. Míla výslovně potvrdí 15 kreditů/job, 100/měsíc a přesnou globální větu z
   global_safety_brake.md pro instalaci LaunchAgentu mimo projekt.
5. `science_news_activation.activate(proposal_sha256=..., confirmation=...)` nejprve
   ověří roli, otisky a servírované UI. Nepíše modelové role. Vytvoří jen privátní
   activation.json a jediný ~/Library/LaunchAgents/com.samantha.science-news.plist,
   s intervalem 60 sekund a RunAtLoad. Spouští provozní Python a science_news.py tick.
6. Před bootstrap zapíše trvalou účtenku; po nejistotě ověří stejnou službu a args,
   bootstrap znovu neposílá. Cizí konfigurace se nepřepisuje. Před prvním pátkem
   aktuální activated_at blokuje staré sloty; ověřit not_due a žádný placený catch-up.

Starý jednorázový pilot i jeho manifest zůstávají zmrazené. Po změně produkčního
adapteru může jeho preview právem odmítnout změněný kód: nepřepisovat staré otisky
kvůli opakování pokusu. Pro čtení/přenos použít immutable raw účtenku, výsledkový
report a jejich uložené hashované zdroje, jak provedl dnešní přenos.

Ověření: 112 cílených Python testů, 16 Node scénářů PASS; finální plná brána
2964 testů OK (5 SKIP), 547,271 s. Detaily a omezení v
reports/science_news_activation_20261110.json. První skutečné týdenní vydání
ani fyzická iPhone přejímka nové ochrany ještě neproběhly.
