# Ateliér — iPhone JPEG s pomocnou MPO vrstvou

Datum: 2026-11-05. Autor: Will. Proud: project-neuberk-kacenka.

## Příčina

Míla vybral tři fotografie a příjem skončil před prvním uložením hláškou
„Nepodporovaný formát nebo příliš velké rozlišení obrázku“. Screenshot
v Dokumentech potvrdil UI a nula uložených podkladů. Odpovídající tři JPEG
byly nalezené ve Stažených; jejich obsah se do Gitu ani reportu nekopíruje.

Všechny tři jsou JPEG/MPO se dvěma obrazy, 4032 × 2268 px (9 144 576 px),
2 118 002 až 2 375 158 bajtů. Limity 6 MiB a 32 milionů pixelů splňují.
Pillow je rozpoznává jako MPO a hlásí více snímků; nejde o běžnou animaci.
Původní whitelist a kontrola jednoho snímku proto platnou fotografii odmítaly.

## Oprava

- Přijmout JPEG/MPO a před validací i dekódováním výslovně zvolit hlavní
  obraz seek(0). Pomocné vrstvy se do pracovního náhledu nepřenášejí.
- Celý původní soubor zůstane byte po bytu zachovaný; original má MIME
  image/jpeg. Náhled a miniatura jsou statické metadata-free PNG.
- EXIF orientace se respektuje. Limit bajtů/pixelů, ověření obsahu,
  bezpečné adresování a odmítání animovaných PNG/WebP zůstávají.
- Chybová hláška rozlišuje nepodporovaný formát a velké rozlišení.

## Ověření

- Nová syntetická MPO regrese před opravou FAIL, po opravě PASS.
- 30 cílených testů PASS. Nový dvouvrstvý vzorek ověřuje hlavní modrý obraz
  místo pomocného červeného, otočení 240 × 160 na 160 × 240, shodu celého
  originálu, MIME, statické odvozeniny, odstranění EXIF a zachovaný pixel limit.
- Všechny tři skutečné fotografie úspěšně dekódované: preview 1400 × 788,
  thumbnail 256 × 144, jeden snímek, bez EXIF. SHA zdrojových souborů stejné.
- Izolovaný příjem všech tří přes execute(add_source), restart repository
  a čtení originálů PASS. Živý projekt nebyl při testu změněn.
- Plná brána PASS: 2 530 testů, 2 499 PASS, 31 SKIP, bez selhání; unit
  493,044 s, celá unit fáze 497,7 s. Python/JavaScript/shell syntaxe a whitespace PASS.

Místní důkazy: logs/interior_mpo_before_20261105.log,
interior_mpo_targeted_20261105.log, interior_mpo_real_photos_20261105.log,
interior_mpo_batch_20261105.log, interior_mpo_full_gate_20261105.log.

Oprava je lokální; tento diagnostický pokyn nezadal nové p+n. Nasazení
vyžaduje samostatný pokyn podle AGENTS.md. Fyzická přejímka nahrání těchto
fotografií v nasazeném Safari zatím není uzavřená. Data/worktree, App Server,
e-mailová služba, originály a uživatelská data se neměnily.
