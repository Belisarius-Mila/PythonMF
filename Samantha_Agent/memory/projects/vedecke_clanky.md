# Znalostní databáze / Knihovna článků

Aktuální stav: 2026-11-10 10:58 CET: Systémové potvrzení přijato a blokátor nové role je uzavřený: registrovaný upgrade pošty 617f3e0d→8c83e93b ověřen,95 položek i business digest/nastavení/role identické. Skutečný nový parser načítá live science binding. Zadané nasazení pokračuje se související kalendářovou opravou; páteční automatika vypnutá.

Aktuální integrační stav: 2026-11-10 10:09 CET: Datův `aad367c7` je převzatý a testovaný pouze na izolované větvi `will/science-news-20261110`; živý main/pošta/role zůstávají beze změny. 134 cílených testů PASS; před nasazením nutný kompatibilní upgrade hodinové pošty a jeho systémové potvrzení. Podrobnosti `reports/science_news_aad367c7_integration_20261110.md`.

Aktuální převzetí: 2026-11-09 23:38 CET: Will převzal oba Datovy commity `9abeb797` a `3ba4d063` nad vydaný `32c4ed20`. UI vysvětluje neaktivní překlad, již hotový překlad zůstává dostupný; zmrazená příprava a výsledkový report pilotu zachované. 116 cílených testů PASS, plná brána PASS: 3381 testů / 31 SKIP; následné Terra p+n výslovně schválené. Report `reports/science_news_two_commits_integration_20261109.md`. Níže uvedené starší attention není aktuální stav vydání 32c4ed20 (completed/CI success).

Aktualizace vydání: Terra p+n bd828212 skončilo attention po launcher restartu během brány; GitHub stále 5ea9af40. Automaticky načtený lokální 1395956d není potvrzené vydání. Oprava launcher guardu 77 cílených PASS, plná brána PASS: 3370 testů / 31 SKIP (546,298 s); po checkpointu čekat nový výslovný pokyn. Model/plánovač/import neaktivní. Report `reports/science_news_release_interruption_20261109.md`.

Aktuální integrační stav 2026-11-09 21:46 CET: fb708be9 přebíraný do main nad5ea9af40, 161 cílených a izolovaný mobilní browser PASS; plná brána3365 testů OK (31 SKIP). Terra p+n výslovně schválené pro kód/UI, nikoli aktivaci modelu/plánovače nebo provozní import. Report `reports/science_news_integration_20261109.md`.

## 03/K4 — vědecký zpravodaj: zadání 2026-11-08, kalibrace přijata 2026-11-09

Míla upřesnil a schválil směr osobního vědeckého zpravodaje namísto obecného
hlídání změn webových stránek. Základní implementaci Míla potvrdil jako nasazenou a částečně převzal na pilotních
zprávách. Překlad ani automatický redaktor ještě nejsou aktivované. Vývoj zůstává v Datově worktree na
`data/parallel-20261104`; e-mailový a kalendářový agent patří Willovi.

### Uložení v češtině a páteční aktivace — 2026-11-10 09:20 CET

Míla zadal páteční aktivaci a uložení konkrétního CRISPR článku v češtině.
Článek je skutečně uložen ve Vědeckých článcích s celým českým překladem a odkazem;
sledování zapnuté, fronta pilotů prázdná, žádný nový modelový tah. Budoucí Uložit
v UI i API vyžaduje celý dokončený český překlad; abstrakt sám nestačí.

Připraven `science_news_activation.prepare/activate`: první návrh 13. 11. 09:00
Europe/Prague, příprava 08:00, Sol/medium Standard, 15 kreditů/job a 100/měsíc.
Potvrzení mezí a globální věty pro systémový LaunchAgent ještě chybí. Vlastní
role binding je pouze lokální návrh; Will musí nasadit nový commit do aktuálního
main se zachováním dalších jeho rolí. Installer před zápisem ověří role/kód/servírované UI,
nejistý bootstrap neopakuje. Účet musí být ChatGPT, dokončené úlohy se započtou
skutečnou vykázanou spotřebou, neukončené drží plné rezervy.
112 cílených testů PASS (16 Node scénářů); Finální plná brána: 2964 testů OK (5 SKIP), 547,271 s, syntaxe a whitespace OK.
Důkaz `reports/science_news_activation_20261110.json`, kanonický handoff a TVBCP.

### Schválený pilot překladu — 2026-11-09 23:32 CET

Míla schválil jediný připravený tah Sol/medium Standard. Zkouška na účtu ChatGPT
prošla: 6980 input + 1002 output tokenů, 0,5995 kreditu podle usage pod přijímací
mezí 5. Jediný pokus bez retry; celý český text je private jako
`data/private/science_news_trial_20261109/crispr-preklad-cs.txt`.
Datova věcná kontrola PASS: všech devět odstavců, čísla, grant/DOI i rozlišení
buněčné linie a plánovaného AAV. Mílova čtenářská přejímka ještě chybí.

Výsledkový report `reports/science_news_translation_trial_20261109.json` má otisky,
usage a přesné hranice. Přípravný report zůstává zmrazenou historickou kartou.
Vzorek neprokazuje týdenní výběr, automatické získání celého zdroje ani plošné
licence. Živá fronta/archiv, role a automatika se nezměnily. Pro tuto zprávu již
nevolat model; po převzetí a samostatném oprávnění připojit hotový výsledek.

### Přejímka překladu — 2026-11-09 23:10 CET

Po schváleném jednorázovém importu tří pilotních zpráv Míla nahlásil nefunkční
překlad. Čtecí kontrola ukázala jednu zbývající CRISPR zprávu bez plného textu,
neaktivovanou roli i aktivaci; nevyřízené rozhodnutí ani archiv se nyní nemění.
Lokální UI vypíná tlačítko s vysvětlením, zatímco hotový překlad zůstává čitelný.
74 cílených testů (včetně 12 Node případů) PASS; finální plná brána 2940 testů OK (5 SKIP), syntaxe a whitespace OK.

Připraven zmrazený podklad celé vlastní tiskové zprávy NIH (bez boilerplate),
nikoli studie Nature. Ověřeno veřejné oficiální znění a NIH FAQ; přímý fetch 403
se neobchází a doménová licence se automaticky nepředpokládá. Cenový návrh
jediné zkoušky: Sol/medium Standard, byte proxy 4,17535, přijímací mez 5 kreditů,
nikoli tvrdý upstream cap. Report `reports/science_news_translation_preflight_20261109.json`.
Jednorázový kandidátní vstup je připraven; před pokusem zbývá přesný souhlas;
placené tahy, binding a aktivace v tomto kroku nula. Podrobnosti a další krok
jsou v kanonickém handoffu a TVBCP.

### Potvrzené zájmy a výběr

- Astrofyzika, částicová fyzika, evoluce, paleontologie, antropologie, genetika,
  lékařské vědy a AI.
- U AI pouze nové technologie a podstatně nové principy; vyřadit pouhé škálování,
  ladění, nové verze a lepší výsledky modelů založených na téže technologii.
- Hledat kandidáty na průlomové objevy: změna dosavadního vysvětlení, zásadní
  nový mechanismus nebo otevření významné nové možnosti. Dílčí taxonomické
  doplnění samo nestačí; nález s širším dopadem na evoluční výklad může projít.
- Významnost a sílu důkazů posuzovat odděleně. Recenzování není záruka pravdy;
  preprint nebo nepotvrzené tvrzení označit jako předběžné. Nerozhodovat jen
  podle titulku, prestiže vydavatele, počtu mediálních zpráv či modelového skóre.
- U lékařských věd rozlišit laboratorní, zvířecí a lidská data a doložený
  klinický přínos. Zachovat nejistotu a rozdíl mezi korelací a příčinou.
- Každý kandidát má původní zdroj, datum publikace/oznámení, odkaz na studii
  nebo DOI, pokud existuje, vysvětlení novosti, důkazů, omezení a relevance.
  Nedohledaný primární zdroj se přizná. Opravy a vyvrácení dřívějších kandidátů
  se mají znovu předložit; mediální kopie jednoho objevu sloučit.

### Potvrzené ukládání

Teprve po dohodě s Mílou o důležitosti konkrétní zprávy připravit český překlad
zprávy a uložit jej spolu s původním odkazem do existující Knihovny. Použít
`science` / Vědecké články, pro zdravotně zaměřené zprávy `health_info` /
Zdravotní informace; případné přesahy řešit tematickými tagy. Nesměrovat nové
vědecké technologie AI automaticky do provozní kategorie Samantha / AI nástroje.

Překlad zachovává původní tvrzení a nejistoty, vlastní komentář je oddělený.
Rozsah zdrojového textu, dostupnost a oprávnění k jeho překladu se ověří před
plným převodem; nedostupný plný text se nevymýšlí a shrnutí se nevydává za
překlad. Pokud plný překlad není možný, navrhnout jasně označené vlastní české
zpracování s odkazem. Původní studii nepovažovat automaticky za text zprávy,
kterou Míla chtěl přeložit. Obsah a přílohy patří do soukromého archivu mimo Git.

Uložení má vlastní trvalou identitu objevu/operace. Dvojklik ani ztracená odpověď
nesmějí vytvořit druhou kartu či přepsat starší ruční poznámky; nejistý výsledek
nejdříve dohledat. Ověření současného archive_text_entry ukázalo použitelný
vstup pro český text, ale nezaručuje samo splnění těchto transakčních požadavků.

### Navržený malý pilot

1. Připravit omezený seznam kvalitních zdrojů napříč všemi osmi oblastmi,
   upřednostnit oficiální API/kanály a dohledání původních studií. Automatické
   načítání respektuje podmínky konkrétního zdroje, licencování a limity.
2. Ručně posoudit malou kalibrační sadu, orientačně 10–15 kandidátů včetně
   senzačního titulku, dílčího nálezu, preprintu a duplicitních zpráv. S Mílou
   označit přijmout/odmítnout a proč; teprve potom odvodit filtr pro automatiku.
3. Týdenní přehled nejvýše pěti zpráv celkem, bez povinných kvót na obor a bez
   výplně, pokud žádná zpráva neprojde. U každé stručně co zjistili, proč je to
   významné, jaké jsou důkazy a co zatím nevíme. Týdenní četnost a limit pěti
   zpráv navazují na návrh, se kterým Míla souhlasil.
4. Po schválení jedné položky ověřit celý průchod český překlad/zpracování →
   jedna karta ve správné kategorii → čtení a původní odkaz v Knihovně.
   Přejímka zahrne opakované potvrzení a ztracenou odpověď bez druhého zápisu.
5. Až po kalibraci navrhnout konkrétní běhovou roli, měření a limit nákladů,
   plánování a ovládání zastavení. V tomto kroku bez placených modelových tahů,
   změn rolí, plánovaných služeb, zápisu článků do živé Knihovny či nasazení.

Technický podklad ověřen 2026-11-08 v lokálním kódu i Git objektu main:
`app/article_archive.py` má obě kategorie a `archive_text_entry`. Nejde o živý
audit služby ani fyzickou přejímku. Referenční dokumentace zdrojů:
https://github.com/arXiv/arxiv-docs/blob/develop/source/help/api/user-manual.md
a https://pmc.ncbi.nlm.nih.gov/tools/openftlist/ (oprávnění se liší podle článku).

Kalibrační sada v1 byla na Mílův pokyn připravena 2026-11-08:
`memory/reports/science_news_calibration_20261108.json`. Obsahuje 12 skutečných
případů z března až listopadu 2026 napříč všemi osmi oblastmi; širší časové
okno je záměrná kalibrace, nikoli týdenní přehled. Každá položka odděluje
vlastní české shrnutí, význam, omezení, dostupný rozsah primárního podkladu
a Datův návrh přijmout/sledovat/vynechat. Tři výslovně syntetické kontroly
navíc ověřují duplicitu, zavádějící titulek a záměnu buněčného experimentu za
klinickou léčbu. Nejde o další skutečné zprávy.

Zdroje ověřeny webovou rešerší: experimentální spolupráce, původní publikace
a abstrakty v PubMed/arXiv. U K03/K04 nebyl dohledán jednoznačný aktuální paper,
u části Nature/NIH selhalo přímé otevření; přesný rozsah opory a nejistota jsou
uvedeny po položkách. Žádná položka tím nezískává statut potvrzeného průlomu.
Při přípravě byly všechny Mílovy verdikty a důvody `null`; přijetí filtru
2026-11-09 je zaznamenané níže. Archivace konkrétních položek není schválená.
Veřejné podklady a vlastní krátká shrnutí jsou Git-safe; bez úplných textů,
soukromého obsahu, placených API tahů, služeb a zápisů do živé Knihovny.

### Přijatá kalibrace a doručování — 2026-11-09

Míla přijal Datův filtr bez změny. Zapsané user_verdict:
- Přijmout: K01, K02, K05, K06, K08.
- Sledovat, čekat na silnější výsledek: K03, K09, K11.
- Vynechat: K04, K07, K10, K12.

Požadovaný termín je každý pátek v 09:00 v `Europe/Prague`, s přepočtem letního
a zimního času. Přehled má být v tento čas připravený, sběr a posouzení tedy
začnou dříve. Nejbližší kalendářní pátek je 2026-11-13; není to příslib vydání
před dokončením a samostatnou aktivací. Limit zůstává nejvýše pět zpráv celkem,
bez výplně a bez automatického překladu/archivace kalibračních položek.

Míla upřesnil konkrétní ovládání: ikona `ScienceNews` v pravém horním rohu
Cockpitu vedle stávajících tlačítek otevře novinky v Knihovně. Původní návrh
karty na hlavní stránce tím nahrazuje. Dokud existuje nevyřízená zpráva, ikona
je zelená a pulzuje; po vyřízení všech zešedne a přestane pulzovat. Pouhé
přečtení nebo otevření překladu položku nevyřizuje. Při omezení pohybu zachovat
význam stavu bez animace; chyba načtení nesmí předstírat prázdný seznam.

Každá zpráva se zobrazí jako český abstrakt s funkčním odkazem na původní zdroj,
datem, oborem, významem a nejistotami. Tlačítka a jejich význam:
- `Přeložit celou zprávu`: překlad v samostatném okně; sám nic neukládá,
  nezapíná sledování a neodebírá zprávu ze seznamu. Platí dříve stanovené
  ověření dostupnosti textu a oprávnění, žádná tichá záměna překladu za shrnutí.
- `Uložit zprávu`: uložit do `science` / `health_info` a implicitně sledovat.
- `Sledovat`: zapnout sledování příslušného objevu/tématu bez archivace článku.
- `Nezařazovat`: vyřídit tuto zprávu bez archivace a sledování; nejde o zákaz
  celého oboru ani jiných budoucích objevů.

Poslední tři akce po úspěšném dokončení odstraní položku z nevyřízeného seznamu.
Uložený článek zůstane v běžné Knihovně. Překlad je volitelný, ne podmínka
uložení; uložit lze český abstrakt se zdrojovým odkazem a případný hotový
oprávněný překlad uchovat u stejné položky. Sledování má předkládat podstatné
navazující výsledky, potvrzení, vyvrácení a opravy, nikoli mediální duplicity.
Sledované položky musí být dohledatelné pro kontrolu a pozdější vypnutí.

Vyřízení je trvalé a musí přežít refresh i iPhone reconnect. Chyba nebo nejistý
výsledek položku neschová; ověří se stejná operace bez druhého zápisu. Uložit
je dokončeno až po ověření archivace i implicitního sledování. Nulový výběr
nenahrazovat výplní; odlišit jej od neúspěšného sběru zdrojů. Externí notifikace
ani e-mail se tímto nezadávají. Jde o schválený návrh budoucího ovládání,
nikoli o provedení rozhodovacích akcí nad 12 kalibračními položkami.

Předimplementační ověření 2026-11-09: lokální `page.html` měl Knihovnu a obě
kategorie, ale tehdejší vyhledání `science_news` / Vědecké novinky v app/scripts/config
ještě nedoložilo implementaci zpravodaje. Následný vývoj je popsaný níže.
Nejde o živý audit; nový plánovač, placený modelový tah, centrální binding role
ani zápis do provozní knihovny v tomto kroku neproběhly.
Strukturovaný návrh a potvrzení jsou v kalibračním JSON jako
`calibration_acceptance`, `delivery_plan` a `interaction_spec`.

Lokální implementace 2026-11-09: fronta, idempotentní volby a archiv, sledování,
ScienceNews UI a čtecí překladové okno, RSS sběr a týdenní adapter jsou hotové.
115 cílených testů PASS; osm kanálů ověřeno čtením. Plná brána 2929 testů OK (5 SKIP), syntaxe a whitespace OK.
Podrobnosti `technical/science_news.md`, report `reports/science_news_implementation_20261109.md`.
Modelová role je pouze podporovaná parserem, centrální binding/aktivace neexistují;
provozní role JSON se nezměnil. Bez placených tahů, zásahu do živé Knihovny nebo služeb.
Další krok: Willova integrace přesného commitu, samostatné p+n a fyzická Mac/iPhone
přejímka; konkrétní model, cenové posouzení a malá živá zkouška před aktivací.
Kalibrační souhlas není provedením akcí nad 12 kalibračními položkami.

## Cíl

Projekt slouží jako širší osobní znalostní databáze. První hotový vstup je
Knihovna článků v Cockpitu; původní vědecké články zůstávají jednou kategorií
uvnitř této oblasti.

Směr potvrzený 2026-06-11:

- `Knihovna článků / web article archive` a `Knowledge inbox / živá znalostní
  databáze` patří k sobě;
- Knihovna článků je první funkční MVP vstup pro URL a webové texty;
- Knowledge inbox je širší bezpečný intake pro velké podklady, chat exporty a
  soubory, které se mají nejdřív read-only zanalyzovat a až po potvrzení
  rozdělit do tematických knowledge karet.

Vědecká část slouží jako lokální knihovna průlomových nebo jinak důležitých
vědeckých článků z různých oborů.

Ukládat se sem mohou:

- PDF článků,
- odkazy na články,
- obrázky, grafy a screenshoty,
- česká shrnutí,
- poznámky Míly,
- důvody, proč je článek důležitý nebo průlomový.

## Umístění dat

Hlavní složka:

```text
data/vedecke_clanky/
```

Praktické webové články, které mohou časem zmizet z internetu, se ukládají jako
soukromý fulltextový archiv mimo git:

```text
data/private/article_archive/
```

Velké podklady a exporty pro budoucí znalostní databázi se ukládají mimo git do:

```text
data/private/knowledge_inbox/
```

Základní soubory a složky:

```text
data/vedecke_clanky/README.md
data/vedecke_clanky/registry.csv
data/vedecke_clanky/inbox/
data/vedecke_clanky/articles/
data/vedecke_clanky/images/
data/vedecke_clanky/links/
data/vedecke_clanky/notes/
data/vedecke_clanky/exports/
```

## Evidence

Hlavní evidence je:

```text
data/vedecke_clanky/registry.csv
```

Každý článek nebo odkaz má mít jeden řádek v `registry.csv`.

Důležité položky:

- ID,
- název,
- obor,
- rok,
- autoři,
- DOI,
- URL,
- lokální soubor,
- obrázky,
- krátké české shrnutí,
- důvod významnosti,
- stav,
- tagy,
- datum přidání,
- informace, zda bylo provedeno internetové doplnění.

## Pravidlo pro internet

Při každém ukládání nových dat se vždy nejdřív zeptat:

```text
Chceš, abych k tomu hledal na internetu doplňující informace?
```

Bez výslovného potvrzení internet nepoužívat.

Pokud Míla hledání povolí, lze doplnit:

- DOI,
- autory,
- rok publikace,
- časopis nebo konferenci,
- oficiální stránku článku,
- abstrakt,
- související práce,
- popularizační vysvětlení,
- praktický význam objevu.

## Doporučený postup

1. Uložit dodaný soubor do `inbox/`, nebo odkaz do `links/`.
2. Zeptat se na internetové doplnění.
3. Přidat řádek do `registry.csv`.
4. Pro důležité články vytvořit poznámku podle `notes/TEMPLATE.md`.
5. Roztřídit PDF/text do `articles/` a obrázky do `images/`.
6. V poznámce držet hlavně české shrnutí a praktický význam článku.

## Stav

Projekt byl založen 2026-05-18.

2026-06-10 byl doplněn lehký soukromý archiv webových článků:

- `scripts/archive_article_url.py` uloží URL, zdrojové HTML, prostý text a metadata.
- `scripts/search_article_archive.py` hledá ve fulltextu uložených článků.
- `scripts/read_article_archive.py` zkusí živou URL a při nedostupnosti použije lokální TXT fallback.
- Cockpit má read-only okno `Knihovna` se záložkami `Recepty`, `Vědecké články`,
  `Samantha / AI nástroje`, `Ostatní`, seznamem od nejnovějších položek a
  fulltextovým hledáním ve vybrané kategorii.
- Vstup přes Cockpit: do okna `Knihovna` lze vložit URL, vybrat kategorii, doplnit
  volitelné tagy a uložit článek automaticky do soukromého archivu.

První uložený praktický článek je návod k lepení spárovky z Nářadí Praha. Plný
text i HTML jsou jen v `data/private/article_archive/` a nepatří do gitu.

2026-06-11 byla doplněna infrastruktura pro ručně vložený text bez URL:

- `app/article_archive.py` umí `archive_text_entry(...)` a ukládá položky se
  `source_type = manual_text`, `source_label`, `source_note`, kategorií a tagy.
- Cockpit `Knihovna` má vedle `Uložit URL` také vstup `Uložit text`.
- Ručně vložený recept nebo výstřižek se ukládá do stejného soukromého archivu
  a je dohledatelný stejným fulltextovým hledáním jako URL články.
- CLI fallback je `scripts/archive_text_entry.py`, použitelný pro TXT soubor od
  historické Samanthy/ChatGPT.
- Recepty bez URL mají být označené zdrojem typu například `ChatGPT historický
  chat` a poznámkou, že jde o vložený nebo syntetizovaný text bez původní URL.

2026-06-11 byl doplněn datový model pro přílohy znalostních karet:

- Každá položka v `data/private/article_archive/articles/<id>/metadata.json`
  může mít volitelné pole `attachments`.
- Příloha je relativní cesta pod soukromým archivem, typicky:
  `attachments/original/`, `attachments/readable/`, `attachments/thumbs/`.
- API Knihovny vrací u položek `attachment_count`, `attachment_types` a
  `attachment_roles`; detail položky vrací i seznam příloh.
- Cockpit umí přílohy v detailu zobrazit a servíruje je přes bezpečný lokální
  endpoint `/api/library/attachment`, ne přes absolutní cestu na disku.
- První cílové použití: ručně psané rodinné recepty, kde textová karta drží
  přepis a příloha drží čitelný scan/fotku rukopisu.
- Doporučené tagy pro tyto položky: `rodinny-recept`, `rucne-psany`, `scan`,
  `ma-obrazek`, případně `prepis-overit`.
- Doporučený `source_label`: `Rodinný ručně psaný recept`.

2026-06-11 byl doplněn i první zápisový průchod pro obrázkové přílohy:

- Backend funkce `attach_article_image(...)` připojí obrázek k existující kartě,
  uloží originál, vytvoří čitelnou JPEG kopii a thumbnail.
- CLI fallback je `scripts/attach_article_image.py`.
- Cockpit `Knihovna` má akci `Připojit obrázek`: nejdřív vybrat kartu v seznamu,
  potom vybrat lokální obrázek, případně doplnit popisek/tagy/poznámku a uložit.
- Při připojení přes Cockpit se automaticky přidávají tagy
  `rodinny-recept`, `rucne-psany`, `scan`, `ma-obrazek`, `prepis-overit`.
- Endpoint pro zápis je `/api/library/attachment/add`; pro čtení příloh zůstává
  `/api/library/attachment`.

2026-06-20 byla doplněna kategorie `Samantha / AI nástroje`:

- Interní klíč kategorie je `ai_tools`.
- Kategorie slouží pro čitelné články o Codexu, Agents SDK, OpenAI novinkách,
  Realtime/voice směru a budoucích schopnostech Samanthy.
- Nové funkcionality OpenAI se mají ukládat jako samostatné články s datem,
  praktickým významem pro Samanthu a poznámkou, že před implementací je nutné
  ověřit aktuální oficiální dokumentaci.
- První soukromé položky jsou `Codex Cookbook: praktická kuchařka pro práci s kódem`
  a `Agents SDK jako budoucí schopnosti Samanthy`.

2026-07-01 byla opravena archivace webových článků se starším českým kódováním:

- `app/article_archive.py` nově respektuje deklarované HTML kódování a fallbacky
  `utf-8`, `windows-1250`, `iso-8859-2`.
- Extrakce preferuje hlavní obsah v blocích jako `div#clanek`, `article` a
  `main`, aby se do textu nedostávaly navigace, reklamy a související bloky.
- Cockpit po uložení URL jasně otevře uloženou položku a ukáže status
  `Otevřeno: ...`, aby opakované uložení stejné URL nevypadalo jako nečinnost.
- Rozbité soukromé položky z testu GVT článku byly podle Milova pokynu
  odstraněny natvrdo mimo git; čistý záznam byl znovu uložen do soukromého
  archivu se správnou češtinou.
- Položka `Špagety ala carbonara` byla v soukromé knihovně přesunuta z
  `Ostatní` do `Recepty`.

2026-07-05 byl ručně zpracován vědecký článek Science Advances o Wnt/DVL3:

- DOI: `10.1126/sciadv.aed8899`.
- V soukromé Knihovně vznikla jedna hlavní karta ve `Vědecké články`, ne více
  samostatných duplicitních článků.
- Fulltext karty tvoří české rozšířené komentované zpracování `Bod zlomu v
  buňce`; originální anglický článek a obě české PDF verze jsou uložené jako
  soukromé PDF přílohy stejné karty.
- Kód Knihovny nově správně servíruje PDF přílohy jako `application/pdf`; oprava
  je v commitu `3f1f470`.

Další krok:

1. Až Míla se Samanthou připraví první přepis ručně psaného receptu a fotku,
   uložit nejdřív jednu testovací kartu.
2. Připojit první reálnou fotku/skener přes Cockpit a ručně zkontrolovat
   čitelnost čitelné kopie i thumbnailu.
3. Podle výsledku doladit cílovou velikost/rozměr čitelné kopie pro rukopisy.
4. U většího balíku receptů udělat read-only rozbor: počet receptů, navržené
   názvy, kategorie, tagy a stav `prepis-overit`.
5. Až po potvrzení rozdělit balík na jednotlivé receptové karty.

## Pracovní profil Knihovna 2026-07-17

Pro další vývoj Knihovny vznikl druhý pracovní profil v rozhraní Human–Adam.
Profil `Knihovna` má vlastní trvalé app-server vlákno, vlastní izolovaný workspace
bez Git remote, samostatnou účtenku nasazení a projektový TVBCP
`memory/tvbcp/knihovna_cockpit.txt`. Původní profil Human–Adam zůstává oddělený.

Přepnutí je potvrzované a fail-closed při aktivním nebo nejistém tahu,
rozpracovaných změnách, čekajícím checkpointu, divergenci nebo nasazení. Soukromý
archiv článků se do izolovaného workspace nekopíruje a jeho obsah nesmí být v
gitovém TVBCP, testech ani logu. Implementace prošla plnou bránou 734 testů, ale
zatím není commitnutá, pushnutá, nasazená ani ručně otestovaná v živém Cockpitu.

Nejbližší krok: po nasazení přepnout z Human–Adam na Knihovnu, ověřit správný
prázdný thread a TVBCP, poslat jeden neškodný pokyn bez změny soukromých dat a
při čistém workspace se vrátit do původního profilu.

Nasazení a živý test byly dokončeny 2026-07-17 v commitu `6a2e205`. Knihovna má
vlastní potvrzené vlákno a čistý workspace bez Git remote; správný TVBCP i jeden
read-only tah prošly. Návrat obnovil původní Human–Adam vlákno a oba workspaces
zůstaly čisté a zarovnané. Další knihovní práci lze zahájit přímo výběrem profilu
`Knihovna`; žádný další technický krok není nutný.


## Fotografie v Knihovně 2026-09-12 21:35 CEST

Fotografie se hned po výběru lokálně zmenší na JPEG nejvýše 1 MiB. Kartu lze
uložit a pokračovat v psaní během přípravy i přenosu více fotografií; cílová
karta je pevně navázaná na uložení. Stejná příprava se používá pro obálku,
fotografie ISBN a OCR (samotné AI rozpoznání se nespouští výběrem).
HEIC nebo nepodporovaný worker využije Mac; původní snímek v telefonu se nemění.
Fronta potřebuje otevřenou stránku; neúspěšný přenos lze opakovat jednotlivě bez
duplicit. Editor mimo Knihy správně skrývá ISBN, rok, autora a umístění.
Důkazy, rizika a nasazení patří do kanonické dvojice
`handoffs/knowledge_library_article_editing_2026_07_16.md` a `tvbcp/knihovna_cockpit.txt`.


## Rozpočet ilustračních fotografií 2026-09-12 22:25 CEST

Míla schválil přibližně 0,3 MiB za celý uložený obrázek. Nová reprezentace:
jeden hlavní JPEG do 285 KiB / 1600 px a náhled do 20 KiB / 320 px. Pole
original_file a readable_file odkazují na stejný fyzický soubor; při měření se
cesty musí deduplikovat. Tři fotografie mají nejvýše 0,894 MiB. PDF se nemění.
Dočasné OCR/ISBN/rozpoznávání obálky používá samostatnou přípravu do 1 MiB /
2400 px a nevytváří trvalou velkou obrazovou kopii.

Registrované Python operace jsou v `app/library_photo_compaction.py`:
- `prepare_library_photo_compaction`: výstupy a otisky do odděleného private
  pracovního adresáře, žádný přepis aktivního archivu;
- `apply_library_photo_compaction`: přesná věta globální brzdy, ověření
  nezměněných podkladů, ověřená záloha, aktualizace příloh a registru, odstranění
  starých aktivních kopií až po kontrole nových;
- `restore_library_photo_compaction`: potvrzený návrat z ověřené zálohy,
  včetně přerušeného procesu; odmítne přepsat následnou uživatelskou změnu.

Aktuální připravený plán je dohledatelný přes
`data/private/library_photo_compaction/latest_prepared.json`. Před použitím se
musí znovu ověřit stav; změna knihovny vyžaduje novou přípravu. Záloha zůstává
mimo aktivní archiv a její velikost se nesmí vydávat za již uvolněné místo.
Dokončení a případný blokátor se vždy zapisují do kanonického handoffu i TVBCP.


## Převod skutečného archivu 2026-09-12 22:44 CEST

Míla potvrdil globální brzdu a převod byl proveden: všech 22 existujících
ilustrací v 11 kartách nyní zabírá 6 251 688 B místo 61 988 739 B. Aktivní
archiv má 44 nových JPEGů místo 66 starých souborů. Kontrola SHA-256 potvrdila
zachování 299 ostatních souborů, neobrazových polí metadat a shodu 121 karet
s registrem. Všechny výstupy splňují 285 + 20 KiB, rozměry i dekódování.
Jednorázová záloha 62 233 053 B je ověřená a zachovaná. Míla výslovně nařídil
její pozdější smazání; provést pouze pro backup tohoto převodu po jeho kontrole
výsledku, bez mazání jiných záloh a bez zavádění automatického úklidu.
Soukromé účtenky a autorizace jsou u plánu přes `latest_prepared.json`;
aktuální další krok je také v kanonickém handoffu a TVBCP.


## Dokončené odstranění zálohy 2026-09-12 23:09 CEST

Na navazující výslovný pokyn byla odstraněna pouze jednorázová záloha převodu:
188 souborů / 62 233 053 B. Kontrolní součty potvrdily zachování všech 357
současných souborů aktivní knihovny a 50 ostatních souborů přípravy/dokladů.
Původní velké obrázky už z tohoto backupu obnovit nelze; kompaktní archiv zůstává.
Registrovaný `delete_library_photo_compaction_backup` v `app/library_photo_compaction.py`
vyžaduje potvrzení, kontroluje přesný plán a otisky, odmítá nečekané soubory a
symlinky, uchovává účtenku a dovoluje bezpečně dokončit přerušené mazání.
Kontrola registru se vztahuje na převáděné karty, aby následné změny jiných karet
neblokovaly úklid. Automatický úklid není zaveden. Důkazy a aktuální stav patří
do kanonického handoffu a TVBCP.
