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

## Hranice důkazu

- Soukromé HTTPS přes Tailscale Serve nebylo spuštěno ani změněno.
- Služba nebyla nasazena a nebyl použit skutečný token ani reálné médium.
- Test proběhl pouze přes lokální HTTP server v dočasném adresáři.
- C02a proto zůstává rozpracované do autorizovaného privátního HTTPS smoke.
- T043, T048 a T051 nejsou tímto výsledkem PASS. Chunkování, obnovení přenosu,
  klientská fronta, databáze a produkční autorizace patří do dalších etap.

## Další krok

Po checkpointu samostatně autorizovat dočasné spuštění přijímače za Tailscale
Serve a provést C02a smoke s neosobním syntetickým souborem: shoda délky a
SHA-256, jedna účtenka, kontrolní chybný hash, identický retry a potvrzení, že
Funnel ani veřejná cesta nejsou aktivní.
