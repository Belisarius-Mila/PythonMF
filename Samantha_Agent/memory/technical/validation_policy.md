# Jednotná validační politika

## Rozhodnutí 15.11.2026

Míla výslovně schválil opravu běžného ověření a odmítl automatické plné
brány velkého projektu. Platí pro přípravu lokálního commitu, checkpoint,
push i nasazení. Nahrazuje předchozí požadavek plné sady pro nové soubory,
změny společné infrastruktury/politiky a prošlý plný základ.

**Plná sada je jen noční CI nebo výslovný ruční požadavek.** Nejde o vypnutí
testů: běžný krok musí projít vybranými doménovými a smluvními testy.

## Jeden runner pro celý postup

Autorita `validation_policy.py`, verze `validation-v3`; mapy v
`validation_domains.py`, testovací registr v `cockpit_quality_gate.py`.
Terminál používá registrovaný validate_project:
`.venv/bin/python scripts/validation_gate.py`. Stejný
`run_checkpoint_quality_gate` používá checkpoint, GitHub batch i deploy.
Samotný `--skip-unit-tests` je pouze diagnostika, není publikační důkaz.

Explicitní úplná diagnostika je `scripts/validation_gate.py --full`.
Přepínač obchází cache a skutečně provede celou sadu. Nízkourovňový
`cockpit_quality_gate.py` bez cílových modulů zůstává ruční úplný nástroj;
nepoužívat ho automaticky před commitem nebo p+n. Aktivní Git pre-commit
hook, který by samostatně spouštěl plnou sadu, při auditu nebyl nalezen.

## Výběr potřebných testů

Celý kandidát zahrnuje rozdíl od auditovaného origin/main, staged/unstaged
a neignorované nové soubory; rename zahrne obě cesty. Model nemůže pro
publikaci určit vlastní úzký seznam. Každá doména má i společný základ
HTTP bezpečnosti, serveru, atomické persistence, runtime policy a frontendu.

- Vocabulary **obsah** má vlastní sadu galerie/audio. Správné cesty zahrnují
  sourozenecké VocabularyEN CSV/katalog/Pict, docs/data/vocabulary-en*.json,
  obrázky, náhledy, audio i větné audio v docs/assets a příslušné inventární
  Python/Node testy. Nový obrázek/zvuk není nový programový kód.
- Změna autorského/exportního kódu přidává také authoring testy. Ostatní
  domény kalendáře, pošty, knihovny, Ateliéru, MMTX, filmu a dokumentů
  ponechávají své sady a skutečné Python konzumenty.
- Společná validace, vydání, persistence a zálohy mají výslovné smluvní
  sady. Změna atomického writeru netestuje automaticky všechny jeho
  tranzitivní uživatele. Tato vědomá změna omezuje úplnost integračního pokrytí.
- Nezařazený nebo dynamický konzument přidá společné smluvní kontroly,
  při čitelných importech také skutečné závislé testy. Nespustí plnou sadu.
  Změna fixture rozšíří její uživatele; pouhé spuštění testu nikoli.
- Syntaxe měněných Python souborů se kontroluje i mimo starý statický
  manifest. Vadné vstupy/syntaxe, starý načtený runtime nebo selhání testu
  skončí jasnou chybou; nepřepnou se potichu na čtvrthodinovou plnou bránu.
- Nový soubor ani chybějící/prošlá účtenka nevyžadují předchozí plný běh.
  Provedou se aktuální cílené testy. Počet testů není tvrdý strop.

Konkrétní poslední Datova dávka503 cest nově vybírá99 testů/9 modulů,
žádná cesta není nezařazená. Jde o tutéž dávku, která ve v2 vyvolala4000 testů.
Skutečné časy jsou v private completion.json podle aktuálního handoffu.

## Účtenka a rychlé otisky

Soukromá Git metadata obsahují atomické HMAC-SHA256 účtenky a místní klíč;
adresář700, klíč/účtenky600. Nepatří do commitu ani modelového payloadu.
Účtenka váže obsah/režimy souborů, prostředí, nástroje, verzi pravidel,
provedený recept a `covered_modules`. Cílený důkaz není plná regrese.

Úzká účtenka nemůže přeskočit moduly jiné čekající změny. Při doplnění
checkpointových dokumentů lze ověřit jen jejich rozdíl, pokud zachované
pokrytí a nové testy dohromady pokrývají celý současný kandidát. Platí
ověření vstupů před i po běhu; změna za běhu nedostane podpis. Po commitu
se stejný strom může svázat s přesným SHA a další kroky jej převezmou.

Účtenka sama platí24h od vlastního běhu. Neexistuje další expirační hodina
plného základu. Po expiraci se opakují jen potřebné cílené testy.
V1/v2 účtenky nejsou novým důkazem v3; první v3 ověření je také cílené.

Běžné soubory mají procesovou cache SHA podle cesty, zařízení, inode,
velikosti, mtime a **ctime**. Nemění-li se nic z toho, není třeba opakovaně
číst všechny stejné obrázky/zvuky. Zápis stejné velikosti a vrácení mtime
změní ctime a vynutí nový SHA. Metadata se kontrolují před/po; symlinky se
podle vlastních metadat necachují, externí/adresářové symlinky zůstávají
nepřípustné. Cache se nespoléhá jen na mtime/velikost a není ochranou proti
správci nebo nedůvěryhodnému procesu pod stejným účtem.

## Noční CI a praktické riziko

GitHub denně02:17 UTC a při workflow_dispatch spouští celou sadu. Běžné
push/PR používají stejnou cílenou mapu; neznámý/nedostupný base použije
smluvní kontroly. Žádná skrytá plná náhrada ani nový místní LaunchAgent.
CI nevydává místní HMAC účtenku a plná noční regrese neblokuje běžné p+n.

Omezení je vědomé: chybu v neočekávané vazbě mezi moduly může zachytit až
noční sada nebo skutečné použití. Žádné procento pravděpodobnosti nemáme
změřené. Ani4000 zelených testů neověřuje všechna macOS oprávnění, skutečné
doručení nebo iPhone. Cílené bezpečnostní/recovery testy zápisu do kalendáře,
pošty a persistence se zachovávají. Testovací PASS nenahrazuje živý smoke,
Git heads, oprávnění ani skutečnou lidskou přejímku.

Vývoj sám nepovoluje push/deploy. Běžící v2 backend získá v3 až po samostatně
povoleném nasazení; při příštím p+n nejprve registrovaně načíst ověřený nový
validator, aby práci neobsluhoval starý v2 fallback. Média ani historii Gitu
v tomto kroku nemigrujeme; Git testovací seed nadále používá nezávislé kopie.


## 2026-11-15 22:31 CET — Stejné podmínky terminálu a služby

Brána vždy předá podprocesu `validation_environment()`: pevný PATH se
stejným Python prostředím a běžnými systémovými/Homebrew nástroji,
PYTHONPATH relativní k ověřovanému projektu, hash seed0, UTF-8, locale C
a UTC. Otisk nástrojů používá právě tento PATH. NODE_BINARY a DEVELOPER_DIR
zůstávají výslovnými, otiskovanými volbami. Prostředí rodičovského Cockpitu
se nemění a shell/editor nemůže do podprocesu přidat jiný PYTHONPATH.

U souboru vlastněného efektivním UID se do otisku bere UID a owner/special
mode; group/other bity nejsou pro přístup tohoto vlastníka relevantní.
U cizího vlastníka zůstávají UID/GID a celé mode. Změna owner execute,
read/write, special bits či vlastníka se neztrácí. Žádný chmod workspace.
To sjednocuje čistý main a soukromý profil bez rozvolnění jeho práv.
HMAC, expirace, kontrola vstupů před/po a covered_modules platí dál.
