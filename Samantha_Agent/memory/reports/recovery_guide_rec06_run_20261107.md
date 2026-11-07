# REC-06 — skutečný běh manifestu v2 a převzetí známé první účtenky

**Konečný výsledek: pilot neprošel doslovným citačním kontraktem.**
Proběhly 2 jedinečné SDK tahy, oba completed/delivered, dohromady odhad
**21,013 Standard kreditu**. Druhá dávka obsahuje dvě citace s modelově
změněným prvním písmenem. Zbývajících 13 tahů ani syntéza nezačaly;
celý návrh TXT nevznikl. Žádný dokončený SDK tah se neopakoval.
Číselný důkaz: `recovery_guide_rec06_full_result_20261107.json`.

Míla výslovně přijal manifest v2 včetně kalendáře, model Sol/medium a původní
jednorázovou revizi 15 tahů s přijímací mezí 200 Standard kreditů bez tvrdého
fakturačního capu. Zdrojový snapshot zůstává `90e85eb7…f27ab8ad`, main 4a33af2a.

## První skutečný tah

První SDK tah je **jednoznačně dokončený a doručený**, nikoli delivery_unknown.
Zdrojová kontrola prošla. Výsledek byl odmítnut kvůli úzkému nesouladu:
`covered` obsahuje všech 36 přiřazených dokumentů **a navíc original_guide**.
Původní instrukce říkala uvést každý zdroj a model považoval původní návod
za další zdroj; controller očekával jen samostatné dokumenty.

Neplacená kontrola uložené odpovědi prokázala:

- všech 36 očekávaných zdrojových cest je právě jednou;
- všech 36 citací je přesný neprázdný podřetězec příslušného zmrazeného souboru;
- navíc je právě jeden original_guide se skutečnou přesnou citací z původního TXT;
- žádná neznámá cesta, chybějící dokument ani zaznamenaný nástrojový typ;
- správný finální JSON, potvrzený start, completed, delivered a jedna user položka.

Spotřeba: **190 761 input, cached 0, 3 628 output (reasoning podmnožina 49)**,
celkem **194 389 tokenů**. Odhad **10,44505 Standard kreditu**, čas **78 142 ms**.
Nejde o fakturační účtenku. Model nebyl opakován a další SDK tah tehdy nezačal.

Raw receipt SHA-256: `1727d71f99509e600ab5caa64f1b2b52da028f65206a610dead32853c28b2e26`.
První turn: `01a1b7a6-1282-7f20-83d1-520c89973061`.
Původní controller/attempt i raw odpověď zůstávají zachované.

## Úzká deterministická oprava

Nové `normalize_inspection()` v izolovaném pilotním adaptéru smí vyjmout
pouze jeden přesný original_guide z výčtu samostatných dokumentů. Musí přitom
sedět celá množina očekávaných dokumentů, jejich jedinečnost, přesné citace
i schéma. Notes se nemění, žádné texty se nedoplňují a raw odpověď se nepřepisuje.
U chybějící/duplicitní/neznámé cesty nebo nepřesné citace zůstane původní chyba.
Stejná kontrola se použije i pro další původně schválené dávky.

To není obsahové přijetí nového obnovovacího TXT ani přijetí Mac/iPhone nastavení.
Jde o kontrolu přesného existujícího důkazu čtení a opravu počítání covered.

## Pokračování stejné schválené úlohy

Nové `app.recovery_guide_receipt_recovery.prepare()/resume()` je explicitní
cesta pouze pro tento prokázaný případ, nikoli automatický retry handler:

1. Povolena jediná dokončená první účtenka, žádný druhý SDK tah. Vyžaduje
   potvrzené doručení, známou přijatelnou spotřebu, nezměněné vstupy, přesný
   payload a výhradně nadbytečný original_guide. Neznámý či nedokončený tah
   tuto cestu nesmí použít.
2. Zmrazí původní approval digest v2, SHA původního raw výsledku, přesnou
   normalizaci a novou implementaci. Ostatní původní kód/role nesmějí změnit hash.
3. Pod stejným job/request a zámkem vytvoří jediný continuation marker.
   První odpověď se načte lokálně; **žádný nový thread/turn pro dávku 1**.
4. SDK reviewer začne na indexu 2. Zbývá pouze **14 původně schválených SDK
   tahů**, celkem maximálně původních 15. Žádné nové zdroje nebo publikace.
5. Nový navazující controller zahrne známých 10,44505 jednou. Jeho součet
   se nesčítá se starým historickým částečným ledgerem; oba patří témuž jobu.
   Celková přijímací mez zůstává 200, zbývající allowance **189,55495**.
6. Z aktivního časového rozpočtu odečte již spotřebovaný první modelový tah.
   Opakované resume jen čte stejnou účtenku; žádný druhý continuation běh.
   Při nejistotě dalšího SDK tahu nepokračuje a nikdy ho neposílá znovu.

Pokračování nepřidává další placený pokus. Dokončuje pouze dosud nespuštěné
kroky už přijatého manifestu v2 a rozpočtu. Původní run i refresh zůstávají
uzavřené; nepřepisuje se jejich attention marker a nevytváří se nový placený job.
Schválení konečného kandidáta, publikace, role a týdenního běhu dál zůstávají zvlášť.

Checkpoint: `recovery_guide_rec06_known_receipt_20261107.json`, otisk
`82e75dfdf08573497d2a842682bca52009c9067da68399082becd91aab613642`.
Soukromý packet/účtenky jsou pouze ve vlastní `.venv/recovery_rec06_full_pilot`.

## Ověření před pokračováním

13 nových testů: známý první tah jen lokálně, SDK až na dalším indexu,
spotřeba jednou, zachované raw soubory, opakovaný vstup bez dalšího SDK,
odmítnutá nejistota/telemetrie/změna zdrojů/extra placený tah/nástroje,
přesná jediná normalizace a snížený zbytkový čas. Cílená sada 47 testů OK.
Plná brána: 2 618 testů OK, 5 skipped.

Změněný produkční klient, runtime, role JSON, závislosti, živé služby a
provozní TXT: žádné. Žádný push/nasazení. Další skutečný výsledek se doplní
z jediné navazující účtenky, bez nového modelového odeslání již dokončené dávky.

## Konečný výsledek kontrolovaného pokračování

První dokončená odpověď byla skutečně převzata lokálně: existuje záznam
`receipt-replay.json` typu existing_completed_receipt_no_sdk_call. SDK reviewer
začal indexem 2 a použil client message ID `rec06-full-corpus-01-2`. Raw první
účtenka má stále stejný SHA-256, UUID obou SDK tahů i vláken jsou rozdílné.
Soubor třetího SDK tahu neexistuje.

Druhý tah je dokončený a doručený, obsahuje všech 65 očekávaných zdrojů,
žádný neznámý ani chybějící. Z 65 citací je 63 doslovných; dvě jsou:

| Zdroj | Modelová citace začíná | Skutečný zdroj začíná |
| --- | --- | --- |
| Camino C01c_RECOVERABLE_AUDIO.md | `Restart aplikace` | `restart aplikace` |
| Camino C02b_CHUNK_TRANSFER_EXPERIMENT.md | `Oddělit 100 %` | `oddělit 100 %` |

Zbytek obou citací je shodný. Neplacený diagnostický návrh ukazuje jediný
odpovídající zdrojový úsek a řádek; **nebyl aplikován na raw odpověď ani
použit pro přijetí dávky**. Změna case není chybějící dokument nebo jiný
významový závěr, ale nesplňuje slíbenou doslovnost. Na rozdíl od vyjmutí
nadbytečného original_guide by zde přijetí vyžadovalo změnu samotné citace.
Toto pravidlo v živém pilotu nebylo oslabeno a další placené čtení nepokračovalo.

| Metrika | Celý skutečný běh |
| --- | --- |
| SDK tahy | 2 jedinečné, 0 retry |
| Dokončené odpovědi | 2, obě delivered |
| Dokumenty v doručených odpovědích | 101 ze zamýšlených 530 |
| Doslovné dokumentové citace v raw odpovědích | 99 ze 101 |
| Controller přijal celé dávky | 36 dokumentů; druhou dávku nepřijal atomicky |
| Celkový input / cached input | 379 845 / 0 |
| Celkový output | 8 083, reasoning podmnožina 109 |
| Total tokens | 387 928 |
| Známá cena prvního / druhého tahu | 10,44505 / 10,56795 Standard kreditu |
| Celkový odhad Standard kreditů | **21,013**, nikoli součet dvou kopií ledgeru |
| Neodeslané plánované tahy | 13, včetně syntézy |
| Kandidát / provozní zápis / aktivace | žádné |

Držet oddělené kopie ledgeru: původní controller má historických 10,44505;
navazující controller má celkem 21,013 včetně první známé ceny právě jednou.
Pro celkovou spotřebu se používá suma **jedinečných SDK účtenek**, ne součet
historického a navazujícího controlleru. Jde o odhad podle známých sazeb,
nikoli poskytovatelem potvrzenou fakturační účtenku.

Druhý tah trval 93 959 ms. Konfigurovaných 90 s je timeout čekání na další
zprávu, nikoli tvrdý limit celého tahu; průběžné události umožňují delší tah.
Celkový aktivní čas obou SDK tahů byl 172 101 ms. Limity se nepřepisovaly.

## Doporučení a přesný další integrační krok

**Týdenní automatiku zatím neaktivovat.** Přenos, strukturovaný JSON,
oddělená ephemeral vlákna, známá tokenová telemetrie a zastavení bez retry se
prokázaly na dvou skutečných dávkách. Celé pokrytí 530 dokumentů, kvalitní
syntéza, aplikační dossier, Mac/iPhone přejímka a obě kopie nebyly dokončené.

Připravit další vývoj pouze offline v novém pilotním souboru, například
`app/recovery_guide_anchors.py`, a odpovídajících testech:

1. Ze zmrazeného textu vytvořit katalog přesných odstavcových/řádkových
   úseků. Anchor ID připnout ke zdrojové cestě, SHA-256 a rozsahu znaků.
   Plný text všech vybraných dokumentů zůstane vstupem modelu.
2. V pilotním schématu **inspect i synthesis** nechat model odkazovat na
   povolené source/anchor ID. Doslovnou citaci vrátí důvěryhodný resolver
   přímo jako source.text[start:end], se shodou hashe a rozsahu.
3. Resolver odmítne cizí ID, nesoulad zdroje, změněné bajty, chybný rozsah,
   duplicity a neúplné pokrytí. Stávající doslovný validátor se zachová;
   poznámky ani obsah kandidáta se automaticky neopravují.
4. Neplaceně otestovat zde uložené kapitalizace, original_guide navíc,
   syntetické chybné ID a pozměněné zdroje. Přepočítat přidaný vstup/schema.
   Jakýkoli nový placený trial předložit zvlášť jako konkrétní novou zkoušku;
   zbývající původní rezerva není automatické oprávnění k placenému retry.

Jde o návrh další implementace, nikoli už ověřený anchor adaptér. Předání
Willovi je v kanonickém handoffu a TVBCP. V tomto kroku se měnily pouze
izolované pilotní soubory, testy a projektová evidence; produkční klient,
runtime, kalendář/e-mail, role, služby a provozní TXT zůstaly bez zásahu.
