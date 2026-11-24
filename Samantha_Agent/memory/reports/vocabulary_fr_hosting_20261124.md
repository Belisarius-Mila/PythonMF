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
