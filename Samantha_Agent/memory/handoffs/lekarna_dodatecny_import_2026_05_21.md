Nazev: Lekarna - dodatecny import dvou fotek
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Po importu vitaminu byly doplneny jeste dve pozde dodane fotky z `data/lekarna/photo_imports/`.
- Jedna polozka patri do osobni krabicky Míla, druha do velke krabice v horni koupelne.
- Soucasne byl zalozen intake checklist pro pristi foto import, aby bylo jasne, co ma Mila dodat a jake kroky ma Codex spustit.

Co je hotove:
- Vytvoren manifest `data/lekarna/photo_imports/lekarna_photo_import_manifest_20260521_tetradin_cinfamucol.csv`.
- Po potvrzeni byly zmenseny 2 fotky na cca 100 kB.
- Po potvrzeni byl aplikovan import manifestu do `data/lekarna/domaci_leky.csv`.
- Evidence ma 65 polozek.
- Lokalni private web export `docs/lekarna/private-data/lekarna.json` byl pregenerovan.
- Verejny sifrovany bundle `docs/lekarna/encrypted-data/lekarna.enc.json` byl po Milove lokalnim zadani hesla pregenerovan.
- Overeno: `missing_sources=0`, `tests.test_lekarna_service` prosel.
- Zalozen `memory/technical/lekarna_photo_import_intake.md`.

Co neni hotove:
- Git-safe commit/push stale ceka na samostatne rozhodnuti kvuli soubeznym nesouvisejicim zmenam.

Dalsi krok:
- Cilene commitnout jen git-safe soubory; necommitovat `data/lekarna/` ani `docs/lekarna/private-data/`.

Zmenene nebo relevantni soubory:
- `data/lekarna/domaci_leky.csv` soukrome, necommitovat.
- `data/lekarna/Leky_v_Krabickach/` soukrome fotky, necommitovat.
- `data/lekarna/photo_import_20260521_075034.md` soukromy import report, necommitovat.
- `data/media/image_resize_backups/20260521_075023/` soukroma zaloha, necommitovat.
- `docs/lekarna/private-data/lekarna.json` soukromy lokalni export, necommitovat.
- `memory/technical/lekarna_photo_import_intake.md`.

Bezpecnost / neukladat:
- Neukladat hesla ani sifrovaci klice do chatu, memory nebo gitu.
- Zdravotni inventar a fotky zustavaji v soukromych ignorovanych slozkach.
