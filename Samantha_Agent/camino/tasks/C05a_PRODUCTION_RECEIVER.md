# C05a — produkční příjem, finalizace a obnova journalu

## Cíl

Připojit C03b metadata ke skutečným bajtům Assetu bez tvrzení přesně-jednou
síťového doručení. Server musí bezpečně opakovat session, části i finalizaci,
vlastním výpočtem ověřit celý SHA-256 a po restartu opravit doložitelné mezery
mezi SQLite a souborovým systémem.

## Pevné hranice

- C03b přijatý manifest Assetu je autorita ID, typu, délky a celkového hashe.
- Síťový proces smí naslouchat jen na loopbacku; soukromé HTTPS patří
  Tailscale Serve. Funnel ani veřejný fallback nejsou povolené.
- Token se zakládá a odvolává pouze místně. API ho nespravuje a databáze drží
  jen SHA-256 tokenu.
- Část je nejvýše 8 MiB, má přesnou délku a vlastní SHA-256. Shodný retry je
  idempotentní, odlišná identita je konflikt.
- Stav `verified` vznikne až po sestavení, serverovém výpočtu délky a SHA-256,
  bezpečném zápisu objektu a SQLite účtenky.
- Nedostatek místa vrací pravdivou blokaci; existující části a originály se
  nemažou. Neznámé či přerušené soubory se zachovají v karanténě.
- C05a neimplementuje iOS frontu C05b, čtyři uživatelské osy C05c, párovací UI,
  Viewer, zálohu, AI ani spravovaný launchd provoz.

## API

Metadata dál používají `C03b_OPENAPI_V1.json`. Mediální rozšíření stanoví
`C05a_MEDIA_OPENAPI_V1.json`:

- `POST /api/v1/assets/{asset_id}/upload-session`
- `GET /api/v1/assets/{asset_id}/upload-status`
- `PUT /api/v1/assets/{asset_id}/chunks/{chunk_index}`
- `POST /api/v1/assets/{asset_id}/finalize`

## Journal a obnova

Před příjmem bajtů vznikne řádek části `pending`. Po bezpečném přesunu části se
stav přepne na `stored`. Restart umí z `pending` + validního souboru dokončit
účtenku; nevalidní dříve potvrzená část blokuje Asset jako
`recovery_required`.

Finalizace zapisuje fáze `assembling` a `assembled`. Pokud proces skončí po
instalaci celého objektu, ale před databázovou účtenkou, další start objekt
znovu změří a uzavře jedinou účtenku. Bez validních bajtů se stav vrátí k
opakovatelnému `retry_required`; nic se nevydává za ověřené.

## Brána přijetí

- core testy: idempotence a ztracená odpověď T043/T044; chybějící, poškozené
  a konfliktní bajty T045/T046; nízké místo a chyba uprostřed zápisu T052;
  pád po instalaci části i celého objektu a osiřelé soubory T061;
- FastAPI testy v odděleném prostředí: autentizace před čtením těla, metadata,
  stream částí, finalizace, opakování odpovědi, stabilní chyby a kontrakt cest;
- hlavní projektová brána po přidání core testů;
- žádný fyzický nebo provozní PASS bez samostatného spuštění služby, privátního
  HTTPS a skutečného iPhone klienta.
