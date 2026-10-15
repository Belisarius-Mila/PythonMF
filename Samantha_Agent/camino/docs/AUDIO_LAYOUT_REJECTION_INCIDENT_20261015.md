# Camino — odmítnutý popis zvukového záznamu 15. 10. 2026

Stav: cílená oprava klienta/serveru a IPA19 místně připravené; nenasazeno.
Plná projektová brána 1936/1936 PASS (349,213 s); cílené audio varianty také PASS.

## Zjištění

Dnešní bezpečný log opakovaně zachytil operaci 879, HTTP 404 `not_found`,
`kind=create_audio_layout`, veřejná odpověď `requested object is missing`.
Dosavadní server `d5d19b4b9ddd` běží a obě owner HTTP/HTTPS cesty jsou zdravé.
Kurzor je 878, archiv bez blokace exportů a bez požadavku na reconciliaci.
Jde o jinou operaci než včerejší název smazané fotografie/video přílohy.

V této větvi původní projekce vrací StoreNotFound pouze pro chybějící audio
manifest. Skutečný neúspěšný paket se neukládá a jeho soukromá identita
není známá. Zatím nepotvrzené, zda Míla od posledního přenosu smazal zvuk
nebo Moment; otázka je položená, odpověď se nenahrazuje předpokladem.

Zopakovaná příčina v buildu 18: smazání celé zvukové session potlačí dosud
neodeslanou deklaraci jejího Assetu, ale ponechá `create_audio_layout`.
Dodatečný optional backfill může layout také vložit až po potlačení smazaného
obsahu. Server takový odkaz správně odmítne a souvislá fronta se zastaví.
Druhá regrese prokázala, že staré potlačení mohlo odstranit už přidělený
paket; takový paket může být na Macu přijatý se ztracenou odpovědí.

## Vymezená oprava

- Neposlaný layout smazané session potlačit společně se zdroji. Znovu použít
  čerstvé místní tombstony i po pozdním vložení audio layoutů a po hashování.
- Nikdy neodstraňovat metadata s přidělenou sekvencí/přesnou obálkou. Přijatá
  historie zůstává beze změny; nedochází k přeskočení nebo přečíslování fronty.
- Již zamítnutý layout lze výslovně stornovat pouze po skutečném 404,
  s odpovídajícím místním záznamem o smazání stejné session/Momentu,
  čerstvým důkazem stejného serveru/epochy a kurzoru právě před paketem.
  Vyžaduje feature `deleted_audio_layout_repair_v1` a oba bezpečnostní flagy false.
- Před dalším POST klient atomicky uloží původní přesnou obálku, tombstone
  a důkaz. Stejné ID, kind, sekvence a null expected_revision zůstávají.
- Wrapper `cancel_deleted_audio_layout` patří do payloadu stávajícího kindu
  `create_audio_layout`. Server ověří striktní/bounded JSON, shodu všech osmi
  polí obálky, clip/Moment, původní validní layout, skutečně chybějící zdroj,
  všechny přítomné zdroje i vazby session. Originál musí ve stejné transakci
  selhat právě na chybějícím manifestu. Existující layout ani plně deklarované
  zdroje se takto stornovat nesmějí; fotografie, cizí audio a větvení se odmítají.
- Přijatý ledger uchová storno s originálem. Nevytváří se Moment, Asset,
  playback layout ani nová Moment revize. Schéma zůstává 3, bez migrace,
  mazání, změny identity, obnovy smazaného zvuku nebo oslabení běžné validace.

## Důkazy a balíček

- Dvě nové regrese před opravou selhaly přesně na osiřelém layoutu a ztrátě
  přidělené obálky. Po opravě všech 74 Swift testů PASS, šest nových audio testů.
- 24 cílených testů skutečných Swift → API obálek, storna, retry/reopen,
  rollbacku, negativních kontrol i dosavadního audio/title chování PASS.
- Dosavadní vydání `d5d19b4b9ddd` přečetlo syntetickou projekci po stornu
  a přesně zopakovalo šest přijatých paketů bez změny stavu. Živá DB se
  pro tento test nepoužila. Izolovaný import v Pythonu služby, schéma 3 PASS.
- Arm64 Release build 0.1.0 (19), `cz.pythonmf.camino.app`, PASS.
  `Camino-SyncRepair-19-20261015-unsigned.ipa`, 1 259 687 B, SHA-256
  `6d532538e18c333f3cfdae2de64c081a29c5e0c07c7ed822f66e97ebae5bf3cf`.
  ZIP CRC, Info.plist a přesná binárka po rozbalení PASS. IPA je nepodepsaný
  pro SideStore; fyzická instalace a telefonní přenos NEPROVEDENO.
- Model databáze, LocalStore, kamera, audio capture/link a Info.plist jsou
  shodné s přijatým buildem 18. Mění se pouze synchronizace a serverová validace.
- Živý úplný audit zachoval všech 264 originálů / 2 068 743 342 B,
  878 operací, 123 Momentů, tripy a flags false. Serve shodný, Funnel off,
  Cockpit smoke 5/5. Recovery záloha stále 27. 9., autosave zastavený;
  dnešní upozornění předané, bez úklidu nebo zásahu do těchto systémů.

Místní ignorované účtenky: `camino_deleted_audio_baseline_20261015.log`,
`camino_deleted_audio_regression_before_20261015.log`,
`camino_deleted_audio_swift_targeted_20261015.log`,
`camino_deleted_audio_api_targeted_20261015.log`,
`camino_deleted_audio_full_swift_20261015.log`,
`camino_deleted_audio_old_release_compat_20261015.log`,
`camino_deleted_audio_full_gate_20261015.log`,
`camino_deleted_audio_ios_build_20261015.log`, `camino_deleted_audio_ipa_20261015.log`.

## Další krok

Po konkrétním potvrzení nasadit pouze Camino server přes registrované
stop/upgrade/start, se čtyřmi DB snapshoty a úplným archivním porovnáním.
Nový IPA19 dodat do iCloud Dokumentů create-only, dosavadní balíčky zachovat.
Stávající náhradní Viewer download zůstává IPA18; pro tento krok se nepoužije.
Poté SideStore aktualizace původního Camina bez odinstalování a jeden sync.
Pokud pro odmítnutý zvuk místní tombstone chybí, automatické storno se neprovede;
je nutná další diagnostika původního odkazu, žádné obecné obcházení 404.
Cockpit, síť, kamera, film a původní média zůstávají mimo zásah.
