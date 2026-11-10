# MMTX — třetí část nové šestky: Jumping Practice

Mílův pokyn „pokračuj scénou 3“ rozšiřuje novou scénu 6 o Picture 3 ze
schváleného scénáře. Po poslední Bunnyho větě u Ollieho pokračuje Next picture
na Freddieho skok. Celá třetí část má osm přesných anglických replik.

## Dva obrazy jednoho rozhovoru

- Repliky 1–3: schválený obrázek 03, pochvala skoku a Dottyina rada.
- Od Bunnyho „Why are you practising?“ (4/8): schválený obrázek 031,
  Freddie napůl ve vodě a Dotty otočená k přátelům.
- Přechod 3/8 → 4/8 nabízí Next picture; čítač zůstává uvnitř stejné části.
  Repeat zachová odpovídající obraz, Again po 8/8 vrátí začátek celé šestky.
- V katalogu je změna obrazu deklarovaná pomocí `image_changes/from_line`.
  Oba obrázky zachovávají rozměry 1672 × 941, WebP q90/method 6.
- Na úzkém displeji je dialog pod oběma obrázky. V rozhovoru na desktopu je
  nahoře uprostřed, aby zůstaly viditelné postavy na břehu i Freddie ve vodě.

| Podklad | Bajty | SHA-256 |
| --- | ---: | --- |
| Schválený PNG 03 | 2982385 | `b89b33732946d632ff85cfe9db91fddaafdd6fb02291acf8befc2cb23e4c0501` |
| Schválený PNG 031 | 2851287 | `423750c04aca6c1f45e05b9d19b6b46ab5b407355035c44511b95858126dbda8` |
| `freddie_jump.webp` | 487350 | `8b00ffe515a1cae62c515647a831cc9bf2f07193226ed1d7d7dcb2b147bbce25` |
| `freddie_conversation.webp` | 458912 | `41c72db7ec82950206a0f9da2431d88400762c36e14e2c9c91bd339a58bc7ebb` |

## Anglické audio a ochrana předchozí práce

Osm nových unikátních Azure požadavků, 458 účtovaných SSML znaků z limitu
500, tempo −10 %, celkem 146016 B MP3. Freddie používá `en-US-GuyNeural`,
Dotty `en-US-JennyNeural`; obě hlasová ID jsou převzatá z původní hlasové
mapy. Bunny a Fiona zachovávají dosavadní hlasy.

Nové soubory jsou pojmenované `audio/en/p03_*.mp3`, texty v `dialogue_03.json`
a veřejné otisky v `audio_manifest_03.json`. Builder používá samostatnou
privátní trvalou účtenku `audio_receipt_picture_03.json`, rezervuje pokus
před transportem a nejistý požadavek automaticky neopakuje. Soukromé účtenky
ani konfigurace poskytovatele nejsou součástí commitu.

Porovnání SHA-256 potvrdilo 23 nezměněných původních podkladů (17 MP3,
oba první obrázky, oba dialogy a oba manifesty) a obě původní raw účtenky.
Žádná starší řeč se znovu negenerovala. Public a mirror mají shodné bajty.

## Ověření

- 59 cílených kontrol PASS; po posledním CSS doplnění ještě 21 relevantních
  testů PASS. Přesné texty/hlasy, dekódování 25/25 MP3, mirrory, celý přehrávač
  v Node VM, návaznost 2 → 3, přepnutí 03 → 031, Repeat/chyby, pozdní callbacky,
  restart, Back/Forward a zachování dřívějších podkladů i obou účtenek.
- Lokální HTTP vrátilo přesné bajty všech 39 skutečných veřejných souborů.
  Pomocné soubory `.lock` jsou ignorované a nepublikují se.
- Ruční Safari průchod začal na prvním obrazu. Třetí část nebyla v tomto
  kroku vizuálně převzatá; otevřená zůstává přejímka obou nových obrazů a
  hlasů na Mílově zařízení včetně fyzického iPhonu.
- Plná místní brána třetí části: 2974 testů OK (5 SKIP), 620,446 s unit;
  rychlá statická brána a `git diff --check` také PASS.

## Vydání a další krok

Třetí část vznikla lokálně v Datově větvi `data/parallel-20261104`. Nové p+n
ani opakování prvního nasazení nebylo spuštěné. Druhá i třetí část jsou mimo
zmrazený první balíček `fee535e5` a nejsou tímto krokem publikované.

Historická první účtenka `4b261f77c13a77e845684bbbd90cc876` zůstává attention:
push confirmed, Pages deployment uncertain po timeoutu při syncing_files.
Míla pokračováním třetí částí neschválil nový pokus nasazení. Nezměněný
report prvního běhu zůstává `mmtx_scene06_first_release_20261110.json`.

Willův main ani jeho bezpečně zaparkované WIP se při tomto vývoji nemění.
Servisní commit `06c34051` se do main nepřebírá podruhé. Pro případné další
vydání je potřeba samostatné rozhodnutí o rozsahu, integraci a p+n.

Další krok: místní přejímka třetí části, potom další vývoj nebo samostatně
autorizované vydání podle Mílova pokynu.
