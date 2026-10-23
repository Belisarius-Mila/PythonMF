# Větší fotografie ve střižně — 23. 10. 2026

Míla schválil opravu po vysvětlení rozdílu mezi rozlišením originálu a
výstupního filmu. Jde o lokální vývoj, vydání zůstává samostatný krok.

## Příčina

Fotografie v exportu dne 14. 10. měla 5918 × 3860 pixelů. Originál existuje,
SHA-256 souhlasí s uzavřeným manifestem, hlavní obraz i ICC → sRGB se načtou.
Náhled i film ji odmítaly kvůli původnímu limitu 4096 pixelů na vstupu.
Čtecí kontrola podkladů neúspěšného exportu našla pouze tento blokující zdroj.
Dřívější úspěšný krátký náhled fotografii neobsahoval. Vývoj více projektů
renderer neměnil a nebyl nasazený.

## Oprava

Náhled a pracovní PNG filmu používají společné zpracování:

1. Omezený vstup nejvýše 64 MiB, 64 milionů pixelů a 16384 pixelů na stranu.
   Rozměry se kontrolují před plným dekódováním, limity Pillow se nevypínají.
2. Jen hlavní obraz (seek 0) včetně dosavadní podpory MPO, EXIF orientace
   a bezpečného převodu platného ICC profilu do sRGB.
3. Lanczos se zachováním poměru stran, bez ořezu a zvětšování. Webový PNG
   náhled se vejde do 4096 × 4096; filmová pracovní kopie do cílového profilu.
4. Očištění metadat; originál a uzavřený manifest zůstávají beze změny.

Výstupy zůstávají 1280 × 720 a 1920 × 1080. Pro skutečnou fotografii má
webový obraz 4096 × 2672, filmová kopie 1104 × 720 nebo 1656 × 1080;
zbytek snímku tvoří postranní pruhy. Video nad 4096 pixelů a nepodporované
HDR se dál odmítají. Nejde o přidání 4K/6K výstupu.

Před vydáním PNG zůstávají kontroly projektu, povolenosti, velikosti,
SHA-256, bezpečné cesty a opakovaná validace po dekódování. Neplatné,
cizí a soukromé zdroje mají dál stejnou obecnou HTTP odpověď bez úniku dat.
Filmový worker nezveřejní neúplný nebo neověřený výsledek.

## Ověření

- 54 cílených filmových testů PASS: GET/HEAD, odvolání soukromí během
  dekódování, MPO/orientace, velká fotografie s ICC, limity souboru/pixelů,
  oba skutečné filmové profily, počet snímků a zachovaný celý rám.
- Syntetický obraz 5918 × 3860 s barevnými okraji: 720p i 1080p po 30
  snímcích, celé dekódování, okraje i pruhy v dekódovaném videu PASS.
- Konkrétní fotografie: načtení PNG a samostatné jednosekundové QA renderování
  720p/1080p PASS, 30 snímků a úplné dekódování. SHA-256 originálu a obsah
  všech dosavadních souborů filmového projektu (střihy/jobs) před/po shodný.
  QA výstupy jsou jen v odděleném private adresáři, žádný nový export v projektu.
- Rychlá statická brána a dalších 18 testů jejího nastavení PASS.

Důkazy jsou pouze v data/private/camino_large_photo_20261023/. Plnou
publikační bránu provede registrovaná Luna při samostatně zadaném p+n.
Po nasazení zbývá zopakovat finální export uložené revize dne 14. 10.
a fyzická přejímka; samostatné QA záběry nejsou přejímkou celého filmu.
