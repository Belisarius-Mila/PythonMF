# C02b — experiment částí a pravdivého stavu přenosu

Zahájeno 2026-09-17 výslovným pokynem Míly. První checkpoint postavil lokálně
ověřitelný přenosový kontrakt a čistý stavový model klienta. Druhý checkpoint
přidal samostatnou nativní iOS testovací aplikaci. Není to ještě fyzický iPhone
test ani dokončené C02b.

## Cíl prvního checkpointu

- rozdělit syntetický soubor na výchozí části 8 MiB;
- po přerušení získat ze serveru skutečný seznam přijatých částí a doplnit jen
  chybějící;
- opakované stejné části a finalizaci zpracovat idempotentně;
- jiné bajty pod stejnou identitou odmítnout bez přepsání;
- sestavit jediný výsledný objekt a ověřit na serveru jeho délku a SHA-256;
- po ztracené odpovědi zjistit výsledek dotazem na stav;
- oddělit 100 % odeslaných bytů od serverového `verified`;
- bez dosažitelné soukromé sítě pravdivě čekat;
- omezit souhlas s mobilním přenosem na jednu již existující dávku.

## Serverový prototyp

`app/camino_chunk_receiver.py` rozšiřuje bezpečnostní hranice C02a o relaci a
části. Proces opět naslouchá jen na loopback IP, vyžaduje bearer token a přijímá
jen explicitně označený syntetický obsah.

Rozhraní prototypu:

- `POST /v1/c02b/synthetic-assets/{asset_id}/sessions` založí stabilní manifest;
- `PUT /v1/c02b/synthetic-assets/{asset_id}/chunks/{index}` přijme jednu část;
- `GET /v1/c02b/synthetic-assets/{asset_id}/status` vrátí přijaté a chybějící
  indexy i stav ověření;
- `POST /v1/c02b/synthetic-assets/{asset_id}/finalize` proudově sestaví soubor,
  ověří celkovou identitu a vydá create-only účtenku.

Přijatá část je uznána až po kontrole délky, serverovém SHA-256 a bezpečném
zápisu dat i vedlejší účtenky. Stav `verifying` je uložen před závěrečným
ověřením. Teprve dokončený serverový objekt a účtenka dovolí `verified`.

## Druhý checkpoint — nativní iOS harness

Samostatná aplikace `Camino Transfer Test` (`cz.pythonmf.camino.transfer.prototype`)
pracuje pouze se syntetickým 96MiB souborem. Nemá přístup k Fotkám, mikrofonu
ani datům Camino Audio. Používá:

- jednu background `URLSession` se stabilním identifikátorem a uploady výhradně
  ze souborů;
- trvalý JSON journal, syntetický zdroj a nejvýše dvě připravené 8MiB části;
- bearer token uložený v Keychain a pouze explicitní privátní HTTPS základ;
- serverový seznam přijatých částí jako autoritu po relaunchi;
- pravdivé stavy `Čeká na síť`, `Ověřuji` a `Ověřeno na Macu`;
- mobilní souhlas omezený na konkrétní již existující `batchID`.

Snapshot serveru je přijímán fail-closed: identita, počet částí i přesné
rozdělení přijatých/chybějících indexů musí odpovídat místnímu journalu.
`verified` s chybějící nebo cizí částí se odmítne.

Po uživatelském nuceném ukončení aplikace se neslibuje pokračování na pozadí.
Při dalším ručním spuštění se znovu vytvoří relace se stejným identifikátorem a
fronta se porovná se serverem. To odpovídá popsanému chování background session:
upload musí být souborový a uživatelský force quit zruší přenosy bez
automatického relaunchu. [Apple: background configuration](https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background%28withidentifier%3A%29),
[Apple: background downloads/uploads](https://developer.apple.com/documentation/foundation/downloading-files-in-the-background),
[Apple: předání background událostí](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/application%28_%3Ahandleeventsforbackgroundurlsession%3Acompletionhandler%3A%29).

## Hranice a zastavení

Tento checkpoint nepřidává čtení reálných videí, produkční FastAPI, databázi,
trvalou službu, Tailscale konfiguraci ani veřejný endpoint. Funnel se nezapíná.
Jediný syntetický zdroj zůstává zachovaný a současně existují nejvýše dvě
připravené části; nejde o důkaz chování skutečného velkého videa.

Podepsaný build 0.4.0 (2), strict podpis, instalace a spuštění na iPhonu prošly.
Dočasnou privátní cestu řídí potvrzovaný registrovaný workflow, který zachová
kořen Cockpitu, nezapne Funnel a po testu porovná původní Serve konfiguraci.

T043 fyzicky prošel na iPhonu přes privátní HTTPS. Při Letovém režimu klient
ukázal 5 % lokálních bytů, 0/13 serverem přijatých částí a 2/2 připravené;
Mac současně evidoval nedokončenou relaci s 0/13 částmi. Po obnovení sítě se
doplnilo 13/13, vznikl jediný objekt daného Assetu o 100 663 553 B a serverový
SHA-256 se shodoval. Průchod odhalil, že souběžný callback mohl být zahozen a
ruční tlačítko během automatické reconciliace působilo mrtvě. Build 2 impulsy
koaleskuje; následná celá dávka doběhla automaticky bez dalšího klepnutí.

T047 je PASS v rozsahu syntetického C02b experimentu: první dávka proběhla pod
zámkem; u druhé byl po 1/13 skutečně ukončen proces, audit po 20 s zůstal na
1/13 bez druhého objektu a po ručním relaunchi se doplnily pouze chybějící části
do 13/13. Dvě relace a dva objekty/účtenky jsou hashově ověřené, každý
100 663 553 B. T049 navíc prošel v syntetickém mobilním rozsahu: bez grantu
a po zrušení dialogu 0/13 bez serverové relace, po grantu jediná ověřená
relace/objekt/účtenka 13/13 a 100 663 553 B se shodným hashem. Další dávka
grant nezdědila, po ruční synchronizaci zůstala na 0/13 a server nepřijal
druhou relaci. Plné T049 s novým skutečným videem, T048 na cizí Wi-Fi a T050
se zadrženou finalizací zůstávají NEPROVEDENO.

Po T043 registrované ukončení zastavilo jen vlastněný receiver, odebralo pouze
`/camino-c02b`, zachovalo tři ověřené syntetické důkazy a přesně obnovilo Serve;
Funnel zůstal vypnutý. T047 má samostatný soukromý stav a nový prázdný běh.
Jeho audit kontroluje i nedokončené relace a hashově ověřené přijaté části.
Fyzický T047 je dokončený; registrovaný stop odebral jeho cestu, zastavil
receiver a přesně obnovil Serve. Stejně byl po syntetickém T049 bezpečně
zastaven jeho vlastní receiver, odebrána testovací cesta a obnovena přesná
původní Serve konfigurace při vypnutém Funnelu. Důkaz jediné ověřené dávky
zůstal zachovaný. T048 a T050 následují odděleně.

T050 má připravený samostatný soukromý běh s pevnou 14s prodlevou před
serverovým ověřením. Ta začíná až po 13/13 částech a stavu `verifying`, ale
nevytváří předčasný objekt ani účtenku a nevypíná následnou kontrolu hashe.
Příprava prošla 32/32 cílenými testy a plnou bránou 1719/1719; živá cesta
zůstává vypnutá a fyzický T050 je NEPROVEDENO. Postup je v
`C02b_T050_FIELD_PLAN.md`.
