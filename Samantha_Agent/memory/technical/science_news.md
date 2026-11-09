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
- `Přeložit celou zprávu` otevře samostatné okno. Samotné čtení ani překlad
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

Parser zná nový název role `science_news_editor`; `config/agent_roles.json`
zůstává nezměněný a nová role není navázána na žádný model. Vyžaduje vlastní
cenové posouzení a skutečnou schválenou malou zkoušku. Dřívější souhlasy s
recovery správcem nebo vývojovou rolí se nepřenášejí.

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
