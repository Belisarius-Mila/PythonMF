# C05b — trvalá iOS fronta a privátní přenos

Datum zahájení: 2026-09-23

## Cíl

Připojit integrovanou iPhone aplikaci k přijatému C03b/C05a kontraktu bez
oslabení offline-first chování. Telefon musí trvale evidovat přesné operace a
média, posílat metadata před audio/fotografií/videem, po přerušení vždy nejdřív
porovnat serverový stav a nikdy nevydat pouhé odeslání bajtů za ověřený úspěch.

## Rozsah

- Trvalý journal s identitou zařízení, epochou, kurzorem, přesnými bajty
  obálky operace, serverem přijatými částmi a stavem každého média.
- Stabilní ID create operací a audio Assetů; změna metadat nevytvoří nový
  upload již ověřeného videa.
- Pořadí metadata → audio → fotografie → video a nejvýše dvě připravené
  8MiB části; implementace C05b používá jednu.
- Background `URLSession` pro část média. Relaunch, zámek, výpadek i force quit
  vedou k novému stavovému porovnání; přesně-jednou síťové doručení se netvrdí.
- `Synchronizovat nyní`, trvalé pozastavení a jednorázové mobilní povolení pro
  přesně zobrazenou dávku. Nové záznamy povolení nezdědí.
- Token pouze v Keychain, pouze HTTPS, žádný veřejný fallback. Místní záznam a
  čtení nezávisí na serveru.
- Změna epochy vyvolá inventární porovnání a fail-closed servisní stav bez
  automatického mazání či odblokování exportů.
- Session-owned C05a služba pro fyzické přijetí běží jen na loopbacku za
  privátní cestou Tailscale Serve `/camino-api`; Funnel zůstává zakázaný.

## Mimo rozsah

- C05c čtyři uživatelské stavové osy a širší informační architektura.
- C06a trvale spravovaná služba, párovací UI a běhový dohled.
- C06b druhá kopie, obnova a produkční odblokování po obnově.
- Viewer, sdílení, veřejná URL, Funnel a automatické mazání originálů.

## Akceptace

| Test | Požadovaný důkaz |
|---|---|
| T047 | Po zámku i force quit se zachová originál a journal; další běh nejdřív porovná server a bezpečně doplní chybějící části. |
| T048 | Při nedostupném tailnetu, cizí Wi‑Fi nebo síťovém přechodu se ukáže čekání bez veřejného fallbacku; místní záznam funguje a přenos po návratu pokračuje porovnáním. Captive portal zůstane `NEOVĚŘENO`, pokud není bezpečně dostupný. |
| T049 | Dialog ukáže přesný počet a objem právě zobrazené dávky; později pořízené video mobilní povolení nezdědí. |
| T050 | Po přijetí všech částí zůstává stav `Ověřuji`, dokud server nepotvrdí délku a celkový SHA-256. |
| T051 | Při vypnutém Macu lze pořizovat a číst všechny místní typy; klient nevymýšlí příčinu síťové nedostupnosti. |
| T052 | Serverový nedostatek místa nevyrobí úspěch a originál zůstane v telefonu. Fyzický test používá řízenou serverovou chybu, ne zaplnění skutečného disku. |
| T053 | Pozdější metadata mají souvislé pořadí a nevyvolají opakovaný plný upload ověřeného videa. |
| T058 | Změna epochy provede inventární porovnání, ochrání novější telefonní data a ponechá výstupy blokované pro servisní rozhodnutí. |

## Povinné hranice důkazu

Automatické testy dokazují model journalu, pořadí, přesné retry, omezení dávky,
serverovou pravdu, změnu epochy, sestavení aplikace a registrovaný provozní
obal. Nedokazují zámek, force quit, skutečný síťový přechod, mobilní data ani UX
na konkrétním iPhonu. Tyto body lze uzavřít jen podle
`C05b_IPHONE_TEST_PLAN.md`.
