# C02b — experiment částí a pravdivého stavu přenosu

Zahájeno 2026-09-17 výslovným pokynem Míly. Tento první checkpoint staví
lokálně ověřitelný přenosový kontrakt a čistý stavový model klienta. Není to
ještě fyzický iPhone test ani dokončené C02b.

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

## Klientský stavový model

Swift package `camino/prototypes/transfer` zatím neprovádí síť. Definuje
reconciliaci lokální fronty se serverovým snapshotem:

- po relaunchi je autoritativní serverový seznam přijatých částí;
- bez sítě nebo snapshotu se nepoužije staré lokální zelené potvrzení;
- lokálních 100 % bytů stále znamená `Ověřuji`, dokud server nepotvrdí objekt;
- `Ověřeno na Macu` vzniká pouze ze serverového `verified`;
- povolení mobilních dat platí jen pro stejné `batchID`.

## Hranice a zastavení

Tento checkpoint nepřidává `URLSession`, iOS UI, čtení reálných videí,
produkční FastAPI, databázi, trvalou službu, Tailscale konfiguraci ani veřejný
endpoint. Funnel se nezapíná. Nevzniká druhá kopie celého videa na klientu;
skutečné souborové úlohy a omezení nejvýše několika připravených částí musí
doložit další klientský checkpoint.

T043 a T047–T050 zůstávají fyzicky NEPROVEDENO. Automatické testy dokazují jen
serverový kontrakt a čistou logiku pravdivých stavů.
