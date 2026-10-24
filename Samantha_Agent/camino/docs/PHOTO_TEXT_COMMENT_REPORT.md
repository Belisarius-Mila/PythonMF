# Text a komentář přímo u fotografie — 24. 10. 2026

## Rozsah a stav

Místní vývoj podle schváleného návrhu Míly. Není tím doložený push, nasazení
ani fyzická přejímka Safari/iPhonu. Dřívější vývoj více projektů zůstává
součástí čekajícího balíčku. Skutečný osobní střih ani originály se při vývoji
neupravovaly; všechny zápisové a mediální zkoušky používají syntetická data.

Původní panel odmítal delší text limity 140 znaků pro titulek a 1000 pro
samostatnou kartu. Chyba byla mimo místo kliknutí. Karta byla nový obraz
za záběrem, nikoli vrstva přes fotografii; prodloužení fotografie to neřešilo.
Původní DOM test vynechával kontejnery textů/karet, tedy tuto interakci neověřoval.

## Nový postup

U fotografie otevři **Text a komentář**. Napiš vlastní text nebo převezmi
celý přijatý text deníku; stejný přenos nabízí spodní sekce. Přenos otevře
příslušnou fotografii a posune k ní stránku. Text se ukládá průběžně do
filmové revize, včetně textu dosud bez zvoleného zobrazení. Vyčkej na potvrzení
uložení před zavřením stránky. Neodeslaný koncept při výpadku zůstává jen
v otevřené kartě; násilné zavření není bezpečné uložení.

- **Pouze uložit text:** celý text zůstane u fotografie bez změny obrazu či zvuku.
- **Statický text:** čitelný panel přes fotografii. Dlouhý text, který se
  do okna nevejde při minimální velikosti písma, nelze exportovat; vyber
  úryvek nebo plynulý režim. Písmo se nezmenšuje do nečitelné velikosti.
- **Plynulý text:** posun spodem dovnitř a vrchem ven přes vymezené okno.
  Náhled i MP4 používají stejný renderer. Dílčí náhled uprostřed fotografie
  zachovává správnou pozici celého textu. Odhad minimální doby vychází
  z pomalejšího z limitů 2,5 slova/s a 15 znaků/s. Nedostatečná délka
  blokuje export, nikoliv uložení rozepsaného textu. Prodloužení je výslovné.
- **Přečíst jako komentář:** nejdřív vytvoř místní čtení hlasem Zuzana,
  poslechni a zvol **Použít čtení ve filmu**. Poslechová verze se ukládá,
  samotné vytvoření ji do filmu nezařadí. Skutečná změřená délka se ukáže
  u fotografie; při přesahu nejprve vědomě prodluž fotografii nebo zkrať text.
  Změna textu staré čtení odpojí. Neprovádí se tiché krácení ani externí TTS.

Původní nahrávku lze u fotografie poslechnout, prodloužit pro ni obraz
nebo ji připojit. Ruční trim zůstává v poslechovém panelu. Nově připojený
hlas má vazbu na identitu fotografie; přesuny a délky předchozích obrazů
jej neposunou jinam. Starší komentáře bez vazby si zachovají absolutní čas.
Překrytí hlasů nebo přesah z vlastní fotografie server odmítá.

**Náhled fotografie s textem a zvukem** vytváří skutečný dílčí render,
nikoli simulaci přes HTML. Výsledky jsou v přehledu exportů. Chyby ukládání,
režimu a zadání náhledu jsou také u ovládání fotografie.

## Kontrakt a soukromí

Volitelné `shots[].photo_text` nese text, režim, původ textu a odkaz na
odvozené čtení. Původní revize bez tohoto pole zůstávají platné. Nahrávka
může mít `photo_asset_id`; čas se rozřeší až nad skutečnou časovou osou
včetně samostatných karet. Nic se nevkládá do neměnného archivního manifestu.

Text fotografie má nejvýše 6000 znaků; obraz 0,1–300 s. Samostatné karty
zůstávají zvláštní volbou (32 karet, 1000 znaků, výchozí délka 5 s).
Delší čtení než 300 s lze uchovat pro poslech, ale před jeho použitím
je nutný kratší autorem vybraný text. Není podporované rozlití přes další snímky.

Čtení je soukromá odvozenina projektu v `narrations/<request-id>/`, nikoli
nový původní Asset. Má otisk manifestu, fotografie, přesného textu a jeho
původu, změřenou délku a SHA-256 zvuku. Síťový výdej vyžaduje uloženou vazbu
na aktuální fotografii a nové ověření oprávněnosti. Podporuje GET/HEAD/Range,
`private, no-store`; neexistuje veřejný odkaz. Zámek soukromí nebo změna
textu zablokují staré audio i export. Neprobíhá automatické mazání.

Místní `/usr/bin/say` přijímá celý text přes stdin, nikoli argument procesu;
nepoužívá chatovou TTS funkci s limitem 1500 znaků. Poté se ověří AAC a celé
dekódování. Jeden projekt dovolí jednu souběžnou generaci a nejvýše 64 verzí,
zvuk do 32 MiB. FFmpeg/FFprobe se dohledají také pod službovým PATH,
bez změny prostředí běžícího Cockpitu. Po nejisté odpovědi se generace automaticky neopakuje;
server používá přesnou identitu požadavku. Přerušené soubory se nevydávají.
Pracovní AIFF a starší odvozeniny zůstávají soukromě zachované; jejich
úklid není součástí smazání jednotlivého MP4 exportu.

## Ověření

- 72 cílených Python testů PASS (editor, Mac projekty a 13 nových testů).
- Nový DOM test skutečně obsahuje texty a karty; ověřuje přenos 3022 znaků
  na 25s fotografii, místní chybu karty, vlastní úpravu a reload, režimy,
  výslovné prodloužení, poslech versus zařazení, přesun a souběh změny textu
  s generováním hlasu. Dřívější editorový DOM test také PASS.
- Skutečné syntetické statické a plynulé MP4 náhledy v 720p i 1080p,
  u plynulého textu náhled uprostřed dlouhé fotografie; úplné dekódování PASS.
- Skutečné místní namluvení celých 3022 znaků, delší než 25 s, bez tichého
  zkrácení i pod omezeným službovým PATH; kontrola délky a skutečný neprázdný zvuk v MP4 PASS.
- Ochrana originálů, přesná vazba textu/hlasové verze, změna soukromí během
  generování, vadný soubor, symlink, cizí zdroj, POST origin, GET/HEAD/Range PASS.
- Snímky syntetických výstupů vizuálně zkontrolované; pohyb textu zůstává v okně.
- Plná společná brána: 2206 testů PASS (450,207 s unit část).
- Po závěrečném drobném doladění vyřazení čtení a odstranění browserového
  krácení při vložení nadlimitního textu: 22 frontendových kontrol PASS.
  Aktualizovaný kontrolní otisk složené stránky; závěrečná statická brána PASS.

Další krok: samostatné p+n registrovanou Lunou, poté fyzicky ověřit
předání textu a poslech na Safari/iPhonu. Konkrétní film uživatele vyrobit
teprve jeho vědomým ovládáním z přijatého střihu.


## Pokus p+n a testové prostředí — 2026-10-24 11:20 CEST

Registrovaná Luna převzala oba commity, účtenka
`570b4fc7ce1e29b96fac6a9b4f1654b2`. Publikační brána skončila jedním
ERROR v novém DOM testu (2206 celkem, 15 skipped, 405,950 s): test hledal
Node pouze v omezeném PATH služby. V terminálovém prostředí byl Node dostupný.
Push účtenka označuje jako uncertain; přímý čtecí audit GitHubu po běhu stále
ukazuje původní e11d949a, nasazení nezačalo. Nejde o vydanou funkci.

Úzká oprava testu používá společný `node_binary()` s existujícími absolutními
fallbacky a v testu přímo vynucuje službové PATH. Produkční kód, Node instalace,
prostředí služeb ani filmová data se neopravují. Nový placený běh se neopakuje
automaticky; vyžaduje samostatné potvrzení připraveného balíčku.

Ověření opravy: 21 cílených kontrol PASS (původně selhávající DOM scénář
přímo pod omezeným PATH a kontrakty frontendu). Statická brána pod stejným
PATH PASS. Před novým pokusem zůstává přesný balíček lokálně, bez dalšího push.
