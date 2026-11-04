# E-mail read-only OAuth integrace

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
