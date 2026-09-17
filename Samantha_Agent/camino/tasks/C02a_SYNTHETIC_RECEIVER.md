# C02a — minimální přijímač syntetického souboru

Zahájeno 2026-09-17 výslovným pokynem Míly po přijetí C01c. Jde o izolovaný
přenosový prototyp. Není to produkční upload server, klientská fronta, záloha ani
důkaz úplných T043/T048/T051.

## Cíl

Připravit nejmenší serverovou cestu, která u neosobního syntetického souboru:

- přijme stabilní identitu, očekávanou délku a SHA-256;
- data čte proudově do soukromého dočasného souboru;
- velikost a SHA-256 vypočítá na přijímači;
- vytvoří konečný objekt a účtenku pouze při úplné shodě;
- stejné ID a stejné bajty přijme idempotentně bez druhého objektu;
- stejné ID a jiné bajty odmítne bez přepsání;
- nikdy se nevystaví přímo mimo loopback.

## Prototypový kontrakt

Proces běží pouze na `127.0.0.1`. Budoucí soukromé HTTPS ukončuje Tailscale
Serve a předává požadavek na tento loopback. Funnel, veřejný port a vlastní VPN
nejsou součástí C02a.

Přijímač vyžaduje:

- `PUT /v1/c02a/synthetic-assets/{asset_id}`;
- `Authorization: Bearer …` s lokálním tajemstvím mimo Git;
- `Content-Length`;
- `X-Camino-Synthetic: 1`;
- `X-Camino-Expected-SHA256` jako 64 hexadecimálních znaků.

Ověřený objekt vznikne create-only pod bezpečným serverovým jménem odvozeným ze
zvalidovaného ID. Klientský název souboru se nepoužívá. Chybný hash, neúplné
tělo, symlinkovaná interní složka nebo konflikt identity nedostanou stav
`verified`. Token, obsah a cesty se nelogují.

## Technické omezení C02a

Prototyp používá pouze standardní knihovnu Pythonu, aby nepřidával FastAPI do
sdíleného prostředí Samanthy. Produkční serverový základ z F51 zůstává
Python/FastAPI v odděleném prostředí Camina a bude zafixován v navazujícím
serverovém kroku. Tento přijímač neobsahuje databázi, chunkování, background
URLSession ani produkční autorizaci zařízení.

## Automatické ověření

- úspěšný syntetický upload a serverem vypočtený hash;
- idempotentní opakování bez přepisu a duplicity;
- jiný obsah pod stejným ID jako konflikt;
- chybný hash bez konečného objektu a účtenky;
- neúplný, příliš velký a neoznačený vstup;
- traversal, neplatný hash a symlinkovaná interní složka;
- povinný token a odmítnutí veřejného bindu.

## Další fyzická předávka

Po samostatně autorizovaném spuštění služby a privátní HTTPS cesty se použije
jen syntetický soubor. Odesílatel a přijímač nezávisle spočítají velikost a
SHA-256; shoda, jedna účtenka a nepřítomnost veřejné cesty tvoří C02a smoke.
Potom se kontrolovaně zopakuje chybný hash a identický retry.

Tento smoke ještě není T043 s přerušením velkého videa, T048 na cizí síti ani
T051 s vypnutým serverem. Ty vyžadují klientskou frontu a další etapy.

## Zastavení

Žádná reálná média, osobní identifikátory, veřejný endpoint, změna Tailscale,
push nebo nasazení nejsou součástí tohoto vývojového kroku. Neshoda hashe se
neopravuje přepsáním očekávané hodnoty.
