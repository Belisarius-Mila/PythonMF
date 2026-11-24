## 2026-11-24 14:10 CET — Oddělené HTTPS nasazení pexesa: připravený večerní pilot

Hotovo: Připravený registrovaný provozní postup pro samostatnou FR službu.
Do soukromého běhového adresáře kopíruje výhradně schválený commit veřejného
FR klienta, médií a serveru. Ověřený cloudflared otevře dočasnou HTTPS adresu;
herní služba poslouchá jen na 127.0.0.1:8791. Nebyla změněna VPN, firewall,
LaunchAgents ani provoz Cockpitu/Camina. Pro Safari doplněné dílčí HTTP požadavky na média (Range/206/416/HEAD).
Skutečné spuštění ještě čeká na finální bránu.

Rozhodnutí: Míla nyní výslovně schválil zprovoznění adresy a nasazení služby.
Pro večerní pilot použít dočasný Cloudflare Quick Tunnel bez účtu či domény,
oddělený od stávajícího privátního Tailscale. Adresa se po novém spuštění změní,
Mac musí zůstat zapnutý, online a neuspaný. Nejde o trvalý hosting.

Další krok: Po doménové bráně a commitu spustit přesný pilot jednou,
ověřit skutečné HTTPS soubory a partii dvěma klienty. Neopakovat nejistý start.
Navrhované další kroky: Předat odkaz a otestovat dva fyzické Macy; trvalou adresu
řešit samostatně podle výsledku večerní zkoušky.

Technický důkaz: Nové testy ověřují oddělení souborů, ověřený konektor,
nezměnitelnost exportu, explicitní souhlas, totožnost procesů a obnovu nejistoty
bez druhého startu. Přesné finální počty, brána, SHA a provozní účtenka jsou
v private vocabulary_fr_hosting_20261124/completion.json. Předběžný živý audit
potvrdil zdravý jediný Cockpit a soukromé HTTPS; Funnel zůstává vypnutý.

## 2026-11-24 14:25 CET — Pexeso na dálku: dočasná HTTPS adresa skutečně nasazená

Hotovo: Francouzština Jana běží na oddělené dočasné HTTPS adrese. Dva klienty
přes veřejný internet ověřily společný plán, oba poslechové protokoly,
neshodu i shodu, správné skóre a šedá místa, odměnu a návrat po přerušení.
Přesná URL a provozní procesy zůstávají v soukromé účtence a TXT Downloads.
Původní osobní označení se mezi odlišnými adresami automaticky nepřenášejí.

Rozhodnutí: Platí výslovné schválení adresy a nasazení. Jde o večerní pilot
přes Cloudflare Quick Tunnel, nikoli trvalou adresu nebo automatický start
po restartu. Mac musí zůstat zapnutý, online a neuspaný. Změna Tailscale,
Funnel, firewallu, LaunchAgents, Cockpitu či Camina nebyla provedena.

Další krok: Míla a Jana otevřou nový odkaz, zakladatel založí partii a pošle
součástí hry vygenerovanou pozvánku. Ověřit zvuk a hraní na dvou fyzických Macích.
Navrhované další kroky: Po této přejímce vybrat trvalý hosting a stabilní
adresu. Večerní pilot není důkaz fyzického spojení Německo–domov.

Technický důkaz: 694 doménových testů PASS, 74 cílených kontrol PASS;
54/54 veřejných HTTPS souborů bajtově přesných, včetně skutečných
obrázků a MP3. Veřejné MP3 Range/206 ověřené; lokálně také suffix/open-range,
416 a HEAD. Dva samostatné HTTP klienty prošly partii s neshodou/shodou,
FR odměnou, skóre, šedými místy a pause/resume. Neplatný původ, třetí hráč
ani soukromé routy nejsou přijaty. Stejný zdravý Cockpit PID a přesně stejná
Serve konfigurace před/po. Grafické ovládání prohlížeče nebylo dostupné;
fyzická GUI přejímka zůstává otevřená. Přesný runtime SHA, veřejná URL,
procesy, finální head a účtenka: private vocabulary_fr_hosting_20261124/completion.json.
