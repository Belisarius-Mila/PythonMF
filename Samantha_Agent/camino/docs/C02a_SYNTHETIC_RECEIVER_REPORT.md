# C02a — report minimálního syntetického přijímače

Datum: 2026-09-17

## Výsledek

Vznikl lokální prototyp přijímače pro jediný syntetický soubor. Naslouchá pouze
na loopback IP, vyžaduje bearer token a syntetický marker, streamuje tělo do
soukromého stagingu a před potvrzením sám ověří délku a SHA-256.

Konečný objekt i JSON účtenka jsou create-only. Identický retry vrátí existující
ověřený výsledek bez druhého souboru. Stejné ID s jinými bajty je konflikt a
nepřepíše první objekt. Chybný hash ani neúplný vstup nevytvoří ověřený objekt.
Klientský název souboru, token, obsah a soukromé cesty se neukládají do logu.

## Ověření

- `tests.test_camino_receiver`: 10/10 PASS.
- Pokryto: autorizace, úspěšný příjem, serverový hash, idempotence, konflikt,
  chybný hash, limit velikosti, povinný syntetický marker, traversal, neúplný
  stream, symlink a odmítnutí veřejného bindu.
- Kód je registrovaný v kanonické rychlé/plné projektové bráně.

## Privátní HTTPS smoke

Dne 2026-09-17 proběhl autorizovaný C02a smoke přes dočasnou cestu Tailscale
Serve `/camino-c02a`. Přijímač dál naslouchal pouze na náhodném loopback portu;
HTTPS ukončil Serve. Použitý token vznikl jen pro tento běh, nebyl vypsán ani
uložen do Gitu. Přenášel se pouze neosobní syntetický obsah.

- health přes tailnet HTTPS: `200`, scope `c02a_synthetic_only`;
- první upload: `201`, stav `verified`, serverová délka i SHA-256 shodné;
- identický retry: `200`, `created=false`, bez druhého objektu či účtenky;
- chybný očekávaný hash: `422 hash_mismatch`, bez ověřeného výsledku;
- jiná data pod stejným ID: `409 asset_identity_conflict`, bez přepsání;
- výsledné úložiště: právě jeden objekt a jedna účtenka, oba se shodným
  serverovým SHA-256;
- kořenová HTTPS cesta Cockpitu zůstala během testu dostupná (`200`);
- Funnel nebyl aktivní; status uváděl pouze tailnet;
- dočasná cesta byla po testu odebrána a celá Serve konfigurace se přesně
  shodovala se stavem před testem.

## Hranice důkazu a stav C02a

- C02a je dokončené v omezeném prototypovém rozsahu minimálního syntetického
  přijímače a privátního HTTPS smoke.
- Přijímač nebyl ponechán jako trvalá služba a dočasná Serve cesta už není
  aktivní.
- HTTPS smoke byl vyvolán z téhož Macu přes jeho tailnet DNS; neověřuje iPhone,
  cizí síť, chování po přerušení ani vzdálenou ACL matici.
- Nebylo použito reálné médium, produkční token ani produkční datové umístění.
- T043, T048 a T051 nejsou tímto výsledkem PASS. Chunkování, obnovení přenosu,
  klientská fronta, databáze a produkční autorizace patří do dalších etap.

## Další krok

Vyčkat na výslovný pokyn k C02b: experiment velkého souboru, souborových částí
a chování iOS na cizí síti bez veřejného alternativního endpointu.
