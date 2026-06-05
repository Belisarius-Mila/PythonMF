Nazev: Family Memory Films / USA 2019 - obnova po ukoncenem terminalu
Priorita: 1
Stav: ceka na rucni review
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Mila ukoncil terminal behem prace nad fotografiemi a videi z USA 2019.
- Bezel druhy skript nad nahledovymi fotkami: `scripts/family_memory_prepare_review.py`.
- Provedena read-only obnova stavu z pameti, git statusu, skriptu a soukromych vystupu.

Co je hotove:
- Read-only intake katalog pro `/Users/miloslavfalta/Desktop/USA` je hotovy.
- Vystupy jsou v `data/private/family_memory_films/usa_2019/01_intake/`.
- Katalog obsahuje 2742 medialnich souboru: 1642 fotek, 1100 videi, 33.10 GiB.
- Review prep po padu/ukonceni terminalu dobehl do konce.
- Vystupy jsou v `data/private/family_memory_films/usa_2019/02_review/`.
- Existuje vsech 2742 ocekavanych nahledu podle manifestu.
- Existuje 81 blokovych contact sheetu a 29 dennich contact sheetu.
- `blocks.csv` ma 81 casovych bloku.
- `README_REVIEW.md`, `blocks.csv` a `thumbnail_errors.csv` byly prepsany po dobehu procesu kolem 22:00.
- Pro rucni kontrolu dni vznikl `day_review.csv` a lidsky HTML formular `day_review_form.html`.
- Dne 2026-06-05 byla aktivni verze `day_review.csv` obnovena z Milova posledniho
  stazeneho souboru `/Users/miloslavfalta/Downloads/day_review-2.csv`, protoze
  obsahoval Milovy opravy, vcetne spravnych datumu uvedenych na konci poznamek
  u spatne datovanych dni.
- Pozdeji 2026-06-05 byla aktivni verze aktualizovana z
  `/Users/miloslavfalta/Downloads/day_review-4.csv`: vsech 29 radku ma vyplnene
  `ok`, `title` a `priority`, kratke nazvy dni jsou sjednocene, kontrolni souhrn
  je 23x A, 1x B, 5x C a 10 radku s `ok=ne`.
- Ze schvaleneho denniho review vznikl `02_review/block_review.csv` a
  `02_review/block_review_form.html` pro pohodlne rucni rozhodovani po 81
  blokovych contact sheetech. CSV ma predvyplnene opravy datumu, kratke nazvy,
  stav `use_in_film` a zachovava poznamky v soukromych datech mimo git.
- Formular je dostupny pres lokalni server jako
  `http://127.0.0.1:8789/block_review_form.html`; server pri kontrole vracel
  200 OK pro HTML i `block_review.csv`.
- Pro smesne bloky `2019-08-05_B01` a `2019-08-05_B02` vzniklo detailni
  item-level review:
  `data/private/family_memory_films/usa_2019/02_review/mixed_2019_08_05/`.
  Obsahuje 14 contact sheetu, `mixed_2019-08-05_review.csv` pro 280 videi a
  `mixed_2019-08-05_form.html`. Vychozi bezpecny stav byl `ne`; prvni
  konzervativni vizualni pruchod priradil 226 videi k jasnym dnům a 54 nechal
  mimo zpracovani. Cele bloky `2019-08-05_B01/B02` zustavaji v `block_review.csv`
  jako `roztřídit` s poznamkou, ze se maji resit po jednotlivych videich.

Co neni hotove:
- Neni hotovy rucni review contact sheetu.
- Bloky jeste nejsou Milou rucne potvrzene v `block_review_form.html`.
- Neni navrzen storyboard filmu.
- Vedlejsi duplicitni JPG soubory s koncovkou typu ` 2.jpg` byly po Milove potvrzeni smazany; kontrola po uklidu hlasi 2742 JPG, 0 chybejicich a 0 prebyvajicich oproti manifestu.
- 10 videonahledu je problemovych a ma placeholder; duvod je zapsany v `thumbnail_errors.csv`.

Dalsi krok:
- Otevrit `http://127.0.0.1:8789/block_review_form.html`.
- Projit blokove contact sheety, hlavne filtr `Jen roztřídit` a smesny den
  `2019-08-05`; po upravach stahnout `block_review.csv`.
- Pro detail smesneho dne otevrit
  `http://127.0.0.1:8789/mixed_2019_08_05/mixed_2019-08-05_form.html`,
  zkontrolovat hlavne radky s `confidence=stredni` a pripadne radky `ne`.
- Pri navazani vzit nejnovejsi `~/Downloads/block_review*.csv` jako zdroj pravdy,
  aby se neprepsaly Milovy rucni poznamky.
- Pokud Mila stahne detailni smesne CSV, vzit nejnovejsi
  `~/Downloads/mixed_2019-08-05_review*.csv` jako zdroj pravdy.

Navrhovane dalsi kroky:
- Okamzite: projit `block_review_form.html`, opravit `correct_day`,
  `use_in_film`, `title` a `notes` u spornych bloku.
- Okamzite pro smes `2019-08-05`: zkontrolovat detailni formular po jednotlivych
  videich, ponechat jasne prirazene kusy a nejasne nechat `ne`.
- Potom: z potvrzeneho blokoveho CSV navrhnout 8-12 hlavnich kapitol filmu do
  30 minut.
- Volitelne: pripravit dalsi formular pro storyboard/kapitoly.

Zmenene nebo relevantni soubory:
- `memory/projects/family_memory_films.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `scripts/family_memory_intake.py`
- `scripts/family_memory_prepare_review.py`
- `scripts/family_memory_prepare_block_review.py`
- `scripts/family_memory_prepare_mixed_review.py`
- `data/private/family_memory_films/usa_2019/01_intake/`
- `data/private/family_memory_films/usa_2019/02_review/`

Bezpecnost / neukladat:
- Do gitu neukladat fotky, videa, nahledy, realne manifesty, GPS metadata ani soukrome poznamky k jednotlivym rodinnym souborum.
- Originaly v `/Users/miloslavfalta/Desktop/USA` nemazat, neprejmenovavat a nepresouvat bez vyslovneho potvrzeni.
- Pri dalsich upravach denniho review vzdy nejdrive importovat nebo nacist Milovu
  posledni stazenou/upravenou CSV verzi, aby se neprepsaly rucni poznamky.
- Stejne pravidlo plati pro `block_review.csv`: po Milove stazeni/uprave brat
  nejnovejsi soubor z `~/Downloads/block_review*.csv` jako zdroj pravdy.
- Stejne pravidlo plati pro detailni smesne CSV:
  `~/Downloads/mixed_2019-08-05_review*.csv`.
