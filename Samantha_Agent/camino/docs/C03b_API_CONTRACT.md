# C03b — verzované API a trvalé revize

Stav: lokální referenční kontrakt v1, 20. září 2026. Autoritativní jsou Camino
v0.5 a novější U15. Strojově čitelná část je `C03b_OPENAPI_V1.json`; přesný
význam objektů určuje `C03a_DOMAIN_CONTRACT.md` a `camino/domain/codec.py`.

## Rozsah první verze

`CaminoV1Contract` přijímá metodu, cestu, autentizační hlavičku a bajty JSON.
Nemá síťový listener. Konstruktor vyžaduje autentizační funkci a kontroluje ji
před čtením jakýchkoli dat. C05 připojí skutečný privátní HTTPS server,
odvolatelné tokeny a provozní audit. Žádná nová služba, Serve cesta ani Funnel
se tímto krokem nespouští.

| V1 cesta | Význam |
| --- | --- |
| `GET /api/v1/state` | Identita serveru, epocha, poslední souvislé číslo změny, blok výstupů. |
| `POST /api/v1/operations` | Jedna sekvenční create nebo metadata/text revize; trvalá účtenka. |
| `GET /api/v1/changes?epoch=…&cursor=…` | Nejvýše 100 přijatých změn po kurzoru vlastníka. |
| `GET /api/v1/moments/{id}` | Aktuální přijatá metadata Momentu. |
| `GET /api/v1/moments/{id}/text` | Přijatá historie textu bez lokálních konceptů. |
| `POST /api/v1/reconcile` | Po obnově epochy jen porovná inventář Momentů; samo neodblokuje výstupy. |

Požadavek na operaci obsahuje přesně `contract_version=1`, `epoch`,
`operation_id`, `device_id`, `device_sequence`, `kind`, `expected_revision` a
`payload`. První trvale přijatá operace sváže jediný
zapisující telefon a jiný zapisovatel dostane `409 writer_mismatch`. Výměna
telefonu vyžaduje budoucí řízené párování, ne přepsání tohoto ID.
Všechna ID jsou kanonická UUID. `device_sequence` začíná jedničkou a server
potvrzuje pouze souvislou řadu bez přeskočení. `expected_revision=null` platí
jen pro create; metadata a text mají aktuální očekávanou revizi Momentu.
Neznámé klíče, duplicitní JSON klíče, neznámý typ, jiné schéma nebo tělo nad
1 MiB se odmítnou. V1 se nebude potichu rozšiřovat o nové významy polí;
neslučitelná změna dostane novou verzi kontraktu.

| `kind` | Přesný `payload` |
| --- | --- |
| `create_trip` | Všechna pole `Trip` včetně `viewer_enabled` a případného `start_date`. |
| `create_day` | Všechna pole `JourneyDay`; rodičovská cesta už existuje. |
| `create_moment` | Všechna pole `Moment` v revizi 1 včetně provenience a případné polohy; Úvaha smí vzniknout jen `owner_only`. |
| `create_asset` | Všechna pole `Asset`; jde o manifest, nikoli potvrzení souborových bajtů. |
| `update_metadata` | `moment_id`, `change`; změna je `privacy` s `new_privacy` a `user_action`, `hidden` s booleanem, nebo `chapter` s existujícím `day_id`. |
| `append_text` | Všechna pole `TextRevision`; koncept se neposílá jako publikovaná revize. |

Všechny volitelné položky jsou v JSON přítomné s `null`, nikoli vynechané.
`camino/domain/codec.py` je jediný převod mezi v1 JSON a modelem C03a.
Server nevěří klientskému názvu souboru jako cestě na disk.

## Potvrzení, konflikt a obnova

- Stejný `operation_id` se stejnými **bajty požadavku** vrátí uloženou účtenku
  bez další revize. Stejné ID s odlišnými bajty vrátí `409
  operation_id_conflict`. Nové ID create nad stejným objektem a totožným
  původním obsahem vrátí `reused=true` bez duplicity; jiný obsah je konflikt.
- SQLite v jedné transakci uloží projekci objektu, každou revizi, přesné bajty
  operace, hash požadavku, účtenku a souvislý kurzor. Zápis používá
  `BEGIN IMMEDIATE`, `foreign_keys=ON`, `synchronous=FULL` a schéma verze 1.
  Databáze musí být mimo zdrojový repozitář a mít práva pouze pro vlastníka;
  otevření širšího oprávnění se odmítne. Test pádu při zápisu účtenky
  potvrzuje rollback současně se změnou revize a kurzoru.
- Nesprávná očekávaná revize, opakované ID s jinými bajty nebo jiný obsah pod
  existující identitou vrátí stálý kód `409`. Konfliktní kandidát se zachová
  v privátní databázi, výstupy se zablokují a revize se nepřepíše. Další
  rozhodnutí o variantách patří řízenému porovnání v C05; neprobíhá automatické
  odemčení ani smazání. Referenční Viewer výběr při bloku vrací prázdnou sadu.
- Po obnově staršího serverového snapshotu musí řízená obnova zavolat
  `rotate_epoch_for_restore()`: vznikne nová epocha, výstupy zůstanou blokované
  a starý klientský kurzor dostane `409 epoch_mismatch`. `reconcile` pouze
  porovná ID, revizi a soukromí Momentů; vrátí chybějící či rozdílné položky.
  Samotné porovnání neodstraňuje média telefonu ani neobnovuje exporty.
- Chybové tělo má `error.code`, `error.message` a nanejvýš aktuální číslo
  revize. Neobsahuje interní stack trace, soukromý obsah ani token.
  Neautorizovaný požadavek dostane `401` ještě před rozborem cesty a JSON.

## Hranice vůči dalším etapám a testům

C03b skutečně ukládá metadata a textové revize na syntetické databázi a má
kontraktní testy pro idempotenci, posloupnost, konflikty, restart, rollback a
změnu epochy. Není to produkční databáze Camina ani úplný F50 API. T053 je
doložené pouze pro metadata/text bez opětovného zápisu manifestu videa; T046
pouze na kontraktní vrstvě. T058 má jen model změny epochy a porovnání
Momentů, bez skutečné obnovy médií a inventáře Assetů. T044/T045 ztracené
potvrzení finalizace a poškozené části zůstávají C02/C05. Fyzické testy iPhonu,
serverová autentizace a soukromý HTTPS provoz jsou NEOVĚŘENO.

Další F50 operace se verzují v téže rodině `/api/v1/`, až je příslušná etapa
implementuje: párování/odvolání (C06), upload session, části, finalizace,
stav ověřeného Assetu (C05), owner čtení média, autorizovaný Viewer a kontrola
exportu (C08/P1). Zápis `verified` pro Asset nevzniká pouhým přijetím manifestu.
