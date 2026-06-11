Nazev: Znalostni databaze - recepty, rucni texty a obrazkove prilohy
Priorita: 2
Stav: rozpracovane, stabilni checkpoint
Pripomenout pri startu: ano
Datum: 2026-06-11

Co se resilo:
- Sjednoceni smeru `Knihovna clanku / Knowledge inbox` do jedne znalostni databaze.
- Import receptu od Samanthy z private exportu do Cockpit Knihovny.
- Vstup pro texty bez URL, aby bylo mozne ukladat recepty, poznamky a ChatGPT vystupy jako samostatne znalostni karty.
- Datovy model a Cockpit UI pro obrazkove prilohy u znalostnich karet.

Co je hotove:
- V Cockpitu je v `Knihovna -> Recepty` 23 importovanych receptovych/varnych polozek ze souboru `samantha_recepty_kb_export.json`.
- `app/article_archive.py` podporuje `manual_text` karty a nove take `attachments`.
- Detail karty vraci `attachment_count`, `attachment_types`, `attachment_roles` a pri detailu i seznam priloh.
- Cockpit umi u karty zobrazit prilohy pres bezpecny lokalni endpoint `/api/library/attachment`.
- Cockpit ma akci `Připojit obrázek`: vybrat kartu v seznamu, vybrat obrazek, doplnit popisek/tagy/poznamku a ulozit.
- Backend funkce `attach_article_image(...)` uklada original, vytvari citelnou JPEG kopii a thumbnail, a aktualizuje `metadata.json` i `registry.jsonl`.
- CLI fallback je `scripts/attach_article_image.py`.
- Lokalni i Tailscale Cockpit byly restartovane a endpointy odpovidaji.

Co neni hotove:
- Neni jeste otestovana realna rodinna fotka/skener rucne psaneho receptu.
- Neni doladena cilova citelnost/velikost readable kopie pro realne rukopisy.
- Neni hotovy specialni filtr v UI pro `rodinny-recept`, `rucne-psany`, `ma-obrazek` a `prepis-overit`; zatim jsou to tagy a fulltext/metadatova priprava.
- Neni hotovy hromadny import baliku rodinnych receptu.

Dalsi krok:
- Až Mila se Samanthou pripravi prvni prepis a fotku rucne psaneho receptu, ulozit jednu testovaci kartu a v Cockpitu k ni pripojit obrazek.

Navrhovane dalsi kroky:
- Okamzite: vybrat jednu realnou testovaci kartu, pripojit fotku a zkontrolovat, jestli readable kopie zustava dobre citelna.
- Pokud readable kopie nebude idealni, doladit rozmer/kvalitu pro rukopisy.
- Dalsi male UI zlepseni: pridat v Knihovne filtr `Rodinné ručně psané`, `S obrázkem`, `K ověření`.
- Dalsi datovy krok: po potvrzeni prvni realne karty pripravit jednoduchy importni postup pro vic rodinnych receptu.
- Pozdeji: stejnou priloha-vrstvu pouzit pro dulezite clanky, grafy, screenshoty a obrazkove poznamky.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `scripts/attach_article_image.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `memory/projects/vedecke_clanky.md`
- `data/private/article_archive/` - soukromy archiv, mimo git
- `data/private/knowledge_inbox/` - soukromy inbox/exporty, mimo git

Overeni:
- `.venv/bin/python -m py_compile app/article_archive.py app/cockpit.py scripts/attach_article_image.py`
- `.venv/bin/python -m unittest tests.test_article_archive tests.test_cockpit`
- Vysledek: 119 testu OK.
- Cockpit local i Tailscale restartovany.
- HTML beziciho Cockpitu obsahuje `libraryAttachmentFileInput`, `/api/library/attachment/add` a `Připojit obrázek`.

Bezpecnost / neukladat:
- Soukrome receptove exporty, realne fotky rukopisu a obsah rodinnych receptu patri do `data/private/` a ne do gitu.
- Do handoffu ani gitu neukladat plne soukrome rodinne texty, fotky, tokeny, hesla ani citliva metadata.
- Git staging delat po konkretnich souborech, nepouzivat `git add .`.
