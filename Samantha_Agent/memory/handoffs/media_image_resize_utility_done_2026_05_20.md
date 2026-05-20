Nazev: Media image resize utility - obecna utilita hotova a overena na lekarne
Priorita: 1
Stav: hotovo, pripravene pro dalsi projekty
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Vytvoreni obecne utility pro zmensovani obrazku podle cilove velikosti v kB.
- Rozhodnuti nedelat jednorazovy lekarnicky skript, ale sdilenou schopnost pro
  dalsi projekty, napriklad slovniky.
- Nastaveni obecneho defaultu cca 250 kB a preset `lekarna` cca 100 kB.
- Prvni ostre pouziti na fotkach leku.

Co je hotove:
- Pridan modul `app/media/image_resize.py`.
- Pridany Samantha tooly:
  - `preview_zmenseni_obrazku`,
  - `apply_zmenseni_obrazku`.
- Pridan CLI wrapper `scripts/resize_images.py`.
- Pridany testy `tests/test_media_image_resize.py`.
- Do `requirements.txt` pridany a do `.venv` nainstalovany:
  - `Pillow`,
  - `pillow-heif`.
- Apply workflow:
  - vyzaduje potvrzovaci vetu `Potvrzuji zmenseni obrazku`,
  - akceptuje i diakritickou variantu v potvrzeni,
  - pred prepisem zalozi zalohu originalu do `data/media/image_resize_backups/`,
  - nic nemaze,
  - pracuje jen uvnitr `Samantha_Agent`.
- Optimalizovan algoritmus pro male cilove velikosti: nejdrive zmensuje rozmery
  a az potom ladi kvalitu, protoze prvni HEIC beh byl prilis pomaly.
- Preset `lekarna` uspesne zmensil 40 fotek z cca 46.14 MB na cca 3.70 MB.

Co neni hotove:
- Neni zatim pridany preset pro slovniky; u jinych projektu se ma Samantha nejdriv
  zeptat na cilovou velikost, pokud ji Mila neurci.
- Neni zatim implementovana automaticka aktualizace odkazu pri prevodu pripon
  mezi formaty; aktualni workflow zachovava puvodni nazvy a pripony.
- Neni zatim commit/push aktualnich zmen.

Dalsi krok:
- Podle Milovy dalsi zadosti se vratit k `../Samantha_GIT_PUSH.txt`.
- Pro slovniky nejdriv zjistit konkretni slozku a cilovou velikost; pokud Mila
  neurci jinak, navrhnout preview s `target_kb=250`.
- Pri dalsim pouziti vzdy nejdriv pustit preview, pak apply az po potvrzeni
  `Potvrzuji zmenseni obrazku`.

Zmenene nebo relevantni soubory:
- `app/media/__init__.py`
- `app/media/image_resize.py`
- `app/media/tools.py`
- `scripts/resize_images.py`
- `tests/test_media_image_resize.py`
- `requirements.txt`
- `app/samantha_agent.py`
- `memory/projects/media_image_resize_utility.md`
- `memory/MEMORY_INDEX.md`
- `data/media/image_resize_backups/20260520_025659/`
- `data/media/image_resize_backups/20260520_030427/`

Overeni:
- `.venv/bin/python -m unittest tests.test_media_image_resize` proslo: 5 testu OK.
- `.venv/bin/python -m unittest tests.test_media_image_resize tests.test_lekarna_service`
  proslo: 24 testu OK.
- Preview po zmenseni lekarny ukazalo 40 obrazku, celkem cca 3.70 MB a
  `Kandidatu ke zmenseni: 0`.

Bezpecnost / neukladat:
- Nemazat originalni zalohy bez vyslovneho Milova souhlasu.
- U novych projektu s fotografiemi se ptat na cilovou velikost, pokud neni jasna.
- Nepouzivat workflow mimo `Samantha_Agent` bez samostatneho bezpecnostniho
  rozhodnuti.
