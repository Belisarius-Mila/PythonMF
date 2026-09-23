# C05a — report produkčního přijímače

Datum lokálního checkpointu: 2026-09-23

## Výsledek

C05a má lokální produkčně orientovaný serverový základ pro příjem částí,
ověřenou finalizaci a obnovu journalu. FastAPI adaptér navazuje na přijatý C03b
manifest Assetu; klient nemůže změnit ID, typ, délku ani celkový SHA-256 pouze
požadavkem na upload. Síťové doručení zůstává alespoň-jednou a žádný stav se
nevydává za přesně-jednou doručení.

Server používá oddělené soukromé SQLite databáze pro metadata, média a
odvolatelné owner tokeny a samostatný souborový kořen mimo zdrojový repozitář.
Token se po síti nespravuje a ukládá se jen jeho SHA-256. Proces odmítne veřejný
bind; povolený je pouze loopback. Soukromé HTTPS přes Tailscale Serve nebylo
v tomto kroku zapnuto.

## Trvalost a pravdivost

- Session vzniká z již přijatého manifestu. Shodné opakování je idempotentní;
  odlišná identita vrací konflikt bez přepsání.
- Část má přesnou délku, index a vlastní SHA-256. Do stavu `stored` se dostane
  až po bezpečném zápisu a přesunu souboru.
- `verified` vznikne až po sestavení všech částí, serverovém výpočtu délky a
  celkového SHA-256, bezpečné instalaci objektu a SQLite účtence.
- Stavový dotaz znovu ověřuje hotový objekt. Pokud se po finalizaci změní nebo
  zmizí, server ihned přejde do `recovery_required` a starou účtenku nevydá.
- Restart opraví validní část zapsanou mezi souborem a SQLite i validní objekt
  nainstalovaný před účtenkou. Neznámé, přerušené nebo konfliktní bajty se
  zachovají v karanténě; C05a nic automaticky nemaže.
- Nedostatek místa a chyba uprostřed zápisu nevrátí úspěch a nepoškodí již
  ověřený objekt.

## Kontrakt a provozní hranice

`C05a_MEDIA_OPENAPI_V1.json` přidává k C03b přesně pět autentizovaných cest:
health, vytvoření session, stav, upload části a finalizaci. FastAPI běží v
samostatném prostředí Camino; připnuté přímé závislosti jsou v
`server/requirements.txt`. Sdílené prostředí Samanthy nebylo změněno.

Tento checkpoint nevytvořil skutečné privátní adresáře ani token, nespustil
trvalou službu, nezměnil Tailscale Serve, nepushoval, nenasadil a nepřipojil
iPhone. Neimplementuje C05b iOS frontu, C05c uživatelské stavové osy, Viewer,
párovací UI ani zálohu.

## Důkaz

- Core + C03b regrese: 23/23 PASS.
- FastAPI přes ASGI v odděleném prostředí, varování jako chyby: 4/4 PASS.
- OpenAPI JSON: validní; deklarované cesty přesně odpovídají aplikaci a nemají
  přednastavený server.
- Veřejný bind `0.0.0.0`: správně odmítnut, exit 2.
- Příprava registrovaného loopback smoke: 4/4 bezpečnostních a registračních
  testů PASS; oddělené C05a prostředí načte FastAPI, Uvicorn a aplikaci.
- Plná projektová brána po přidání workflow: syntaxe Python/JavaScript/shell a
  1763/1763 testů PASS.

| Scénář | Lokální C05a důkaz | Co ještě chybí |
|---|---|---|
| T043 | doplnění chybějících částí, jediný objekt a shodný hash | produkční iPhone + privátní služba; fyzický syntetický důkaz z C02b se nepovyšuje na C05a provoz |
| T044 | opakovaná finalizace po ztracené odpovědi vrátí tutéž účtenku bez duplicity | reakce skutečného C05b klienta |
| T045 | poškozená/vynechaná část a chybný celkový hash nikdy nedostanou `verified` | provozní přenos skutečného média |
| T046 | shodný retry je idempotentní, odlišné bajty pod stejnou identitou jsou konflikt | end-to-end produkční spojení |
| T052 | syntetické nízké místo i chyba uprostřed zápisu fail-closed, bajty se zachovají | fyzický test vhodného serverového úložiště |
| T061 | syntetický pád po instalaci části i objektu a osiřelé soubory se obnoví nebo karantenizují | řízený procesní pád a restart budoucí služby |

## Další krok

Registrovaný `camino_c05a_loopback_smoke` je připravený pro jednorázový běh v
odděleném C05a prostředí. Vytvoří pouze syntetická data mimo repozitář,
vlastněný loopback proces a redigovanou účtenku v ignorovaném privátním stavu;
oba náhodné tokeny odvolá. Serve, Funnel, iPhone, Git, push a deployment
nemění. Příprava workflow prošla cílenými testy, ale skutečný smoke zatím
neproběhl a čeká na samostatné potvrzení přesného registrovaného příkazu.

Teprve po přijatém loopback smoke lze zvlášť potvrdit privátní Tailscale Serve
a C05b iPhone klienta. Do té doby se místní stav `čeká na server` nesmí
označit jako přijatý serverem.
