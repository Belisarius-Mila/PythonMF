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

Podepsaný build 0.4.0 (1), strict podpis, instalace a spuštění na iPhonu prošly.
Dočasnou privátní cestu řídí potvrzovaný registrovaný workflow, který zachová
kořen Cockpitu, nezapne Funnel a po testu porovná původní Serve konfiguraci.
T043 a T047–T050 přesto zůstávají fyzicky NEPROVEDENO: instalace a launch samy
nedokládají background přenos, přerušení, zámek, force quit ani cizí síť.
