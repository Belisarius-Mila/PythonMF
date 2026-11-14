# Společné vydání Cockpitu — 2026-11-14 15:39 CET

Míla výslovně schválil úplné p+n přes Terru. Integrované oba Datovy commity
50f113f5/a356e51d a oba knihovní34b34a54/b5f7ee7e. Společný cíl je registrovaný
runtime Cockpit, projekt project-cockpit. Kontrolní otisk složeného frontendu
přepočítaný po sloučení;361 cílených integračních testů PASS.
Samostatné Datovy worktrees zachované. Síťová konfigurace, místní výběry A,
živé knihy ani aktivace e-mailového agenta se při integraci nemění.

Autoritativní stav tohoto vydání určuje jediná trvalá účtenka požadavku
all-local-cockpit-20261114-total-v1 a privátní souhrn
data/private/combined_release_20261114/runtime_receipt.json.
Při obnově chybějící účtenka neznamená neprovedený push/deploy: ověřit stejný
job a živý stav, nic automaticky neopakovat. Tento zápis sám není potvrzením
publikace. Po potvrzeném vydání zbývá fyzický iPhone pilot knih a nové
otevírání aplikací; původní ikonu/data ani výběr A nemazat.

Integrační ověření:361 cílených testů PASS včetně HTTPS vstupu, PWA,
navigačních Node scénářů, knihovní persistence, katalogu a obou forem.
Plnou publikační bránu provede registrovaný release worker před push.
Předchozí knihovní samostatný běh měl jediný syntetický RPC timeout; celý
jeho nezměněný modul následně42 PASS. Nejde o náhradu nové publikační brány.

## 2026-11-14 16:02 CET — Dokončení živého HTTPS přesměrování

První společné p+n potvrzené:9b846f75, Terra job79c8b5b1ddac34d3714b0cd826f6b7ab,
push/deploy confirmed,3899 testů PASS/661,2s, smoke5/5 a chráněné služby beze změny.
Živý HTML odpovídá zdroji a ISBN vrací Beletrie. Následná živá kontrola starého
HTTP vstupu odhalila chybějící CLI režim Tailscale pod launchd. Terminálový
resolver fungoval; bez TERM/TERM_PROGRAM/TAILSCALE_BE_CLI reálná GUI binárka
vrátila exit0 a neplatný JSON. S explicitním CLI režimem validní JSON.

Oprava: pouze čtecí subprocess serve status --json dostane ve vlastní kopii
prostředí TAILSCALE_BE_CLI=1. Rodičovské prostředí, Serve, síť, certifikáty,
PWA identity, soukromá data a aktivace agentů beze změny.90 cílených testů PASS,
včetně skutečného procesu v minimálním syntetickém prostředí a ochrany rodiče.
LL-072 je opakovatelný podklad; nepřenášet celé terminálové nastavení do služby.

Dokončení opravy má vlastní nový registrovaný požadavek
all-local-cockpit-20261114-https-cli-v1 a privátní autoritativní účtenku
data/private/combined_release_20261114/https_cli_fix_receipt.json.
Původní úspěšný job se neopakuje. Stav nové opravy a finální živé HTTP302,
HTTPS, HTML a katalogové ověření určují tato účtenka a live_verification.json.
Při nejistotě číst stejný job, nikoli znovu spouštět vydání. Fyzický iPhone
pilot a případná obnova A zůstávají samostatné, původní data/ikonu nemazat.
