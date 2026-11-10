# Nová šestá scéna MMTX — první obraz The Lake

První obraz používá přijatou boční variantu: všech pět přátel skutečně sleduje
jezero a mraky ve tvaru králičích uší. Zachovává všech sedm přesných anglických
replik nového scénáře; další obrazy zatím nejsou implementované.

## Ovládání

- První klepnutí spustí Benjiho. Next posouvá vždy jednu repliku až po dohrání MP3.
- Repeat zopakuje současnou větu; po poslední replice je dostupné Again.
- Při chybě MP3 se postup zastaví a nabídne Repeat, bez jiné hlasové služby.
- Zpět k mostu je přístupné i před odemknutím zvuku. Odchod zastaví přehrávání.
- V této etapě je zvuk i text anglicky; žádné české MP3 ani nové generování při čtení.

## Pevné anglické MP3

| Postava | Hlas |
| --- | --- |
| Benji | en-US-AndrewNeural |
| Fiona | en-US-JennyNeural |
| Sunny | en-US-MichelleNeural |
| Bunny | en-US-AnaNeural |
| Bruno | en-US-GuyNeural |

Registrované `generate_project_azure_audio_asset`, Azure, tempo −10 %, sedm
unikátních požadavků / 410 účtovaných SSML znaků, přijímací limit 500 znaků.
Sedm MP3 má dohromady 147 312 B. Soukromá trvalá účtenka před každým požadavkem;
nejistý požadavek blokuje další běh a hotový výsledek se znovu negeneruje.
Žádné přihlašovací údaje nejsou v balíčku ani veřejném manifestu.

Builder `MatysekANJ/build_scene06_opening_audio.py --check` ověřuje přesný text,
hlas, tempo, SHA-256, dekódování všech sedmi MP3 a oba shodné mirrory.
`--apply --provider azure` je samostatná explicitní generace; zkoušky/CI ji nevolají.

## Obraz a zdroje

- Přijatý PNG: 1672 × 941, SHA-256 `3b028eef9065528262c788b2d34e2369ea4800c5e7fe46a4c29b64dd9e649bbc`.
- WebP q90 bez změny rozměrů: 470 730 B, SHA-256 `232225a745973b186995bd1693abd0689563984c7a7d84ddf7874b6e60f2a8c3`.
- Publikační zdroj `docs/scene06_lake_arrival/`; shodný mirror
  `MatysekANJ/web_mmtx/scene06_lake_arrival/`. Jen 13 konkrétních veřejných souborů.
- Dřívější odstranění staré šestky a původního obrázku se nevrací. Nový obraz
  má samostatný název `arrival_side_view.webp`, sedm MP3 nové popisné názvy.

## Ověření a hranice

- 35 cílených testů PASS: nový přehrávač/builder, Azure, předchozí scéna 5 a Pages.
- Přehrávač: pořadí všech sedmi vět, blokování souběhu, chyba MP3 / explicitní
  Repeat, opožděné callbacky, konec, restart a odchod ze stránky.
- Rozpočet před sítí; trvalá rezervace před transportem; nejistý výsledek se
  neopakuje; hotové soubory se ověřují; cizí audio zastaví celý plán.
- Dekódování 7/7, shoda obou mirrorů, lokální HTTP 200 a přesné bajty všech
  13 veřejných souborů. Python/Node syntaxe a rychlá statická brána PASS.
- Skutečné místní Safari: viditelný první dialog Benji 1/7, konečný stav
  Bunny 7/7 a Again, bez chybového upozornění. Desktopové rozložení zkontrolované.
  Fyzický iPhone a Mílova hlasová přejímka nejsou tímto doložené.
- Plná místní brána: 2960 testů OK (5 SKIP), 452,596 s unit; konečné nové JS navíc ověřeno cílenou sadou po opravě bfcache.

## Publikace

Míla výslovně zadal Terra p+n a následné napojení ze scény 5 pro produkční
zkoušku. Vývoj zůstává v Datově větvi `data/parallel-20261104`; Willův checkout
ani jeho nesouvisející změny se během vývoje nepřepisují. Předchozí samostatné vydání MMTX do `51a2cabe` skončilo potvrzeně (jiný balíček).
Kanonický main má Willovy neuzavřené změny requirements a dva scénáře; zachovat je.
Tento report neprohlašuje novou šestku za publikovanou; vyžaduje převzetí
konkrétního hotového commitu do kanonického main a jeho vlastní účtenku p+n.

Bezprostřední další krok: převzít konkrétní ověřený commit; pak ověřit
uvolněný kanonický main a registrované předání pro `project-mmtx` / GitHub Pages.


### 2026-11-10 15:24 CET — Připravené napojení pětky a publikační blokátor

Hotovo:
- Po dokončení pětky je v Datově pracovní kopii viditelný vstup To the lake! do prvního obrazu nové šestky. Úprava vychází z Willova již schváleného ukončení staré šestky a zachovává odstranění neviditelné zkratky; obě kopie stejné.

Rozhodnutí:
- Mílovo zadání zahrnuje Terra p+n i produkční propojení. První obraz je ve vývojovém commitu `1c40b6db`; samotné propojení má samostatný následný commit, aby šlo dodržet pořadí živého vydání.

Další krok:
- Míla upřesní, zda hotové commity do kanonického main převezme Will, nebo Data. Zdrojové neuzavřené změny vlastníka ani profilový stav se neobcházejí.

Navrhované další kroky:
- Po převzetí: registrované Terra submit_release(wait=True), přesné potvrzení Pages, potom vydat propojení a zkontrolovat skutečné veřejné bajty a vstup z pětky. Fyzický iPhone a hlasy převezme Míla.

Technický důkaz:
- 37 cílených testů PASS; nově i skutečný cíl odkazu, jeho umístění až v původně skrytém dokončení a shoda HTML/CSS obou mirrorů. Plná místní brána 2960 OK (5 SKIP) zůstává důkazem nezměněné infrastruktury; nová markup změna byla ověřená cíleně. Žádné nové modelové/audio volání a žádná publikace této šestky. Registrovaný deploy audit: source main není čistý; batch audit: pracovní prostředí není připravené.


### 2026-11-10 16:12 CET — Druhý obraz ověřený, první nasazení Pages zrušené po timeoutu

Hotovo:
- Lokálně funguje příběhové spojení prvních dvou obrazů a všech 17 anglických MP3. Druhý obraz má schválený obrázek, přesných 10 replik a vlastní neměnné audio podklady.

Rozhodnutí:
- Druhý obraz je oddělený následující vývoj, není součástí prvního zmrazeného p+n. První p+n se neopakuje automaticky; Míla má konkrétní otázku na jediný nový pokus stejného fee535e5. Starý WIP Data je zaznamenaný samostatně v `06c34051` a do main se znovu nepřebírá. Willovo nesouvisející WIP zůstává zachované.

Další krok:
- Uložit konkrétní nový commit druhého obrazu a potvrdit čisté pracovní kopie; poté počkat na Mílovo rozhodnutí o novém pokusu nasazení.

Navrhované další kroky:
- Druhý obraz samostatně projít na Mílově zařízení a případně vydat po jeho pokynu. Produkční Pages po zrušeném nasazení zatím není přejímka nové šestky.

Technický důkaz:
- Plná místní brána 2972 OK (5 SKIP), 665,420 s unit; 57 cílených kontrol PASS, 17/17 MP3 decode, 27 HTTP souborů přesné. Skutečné Safari: obraz Ollie, Bunny 10/10, Again, viditelné postavy a podběrák. První Azure podklady beze změny. První Terra receipt `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deployment uncertain; GitHub Pages run `42839271179` po 600000 ms syncing_files deployment zrušil. Po zrušení HTML 404. Výsledkový report zachovává první neúspěšný běh bez přepisu.
