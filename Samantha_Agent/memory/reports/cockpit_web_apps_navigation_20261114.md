# Cockpit — aplikace z ikony a dostupný návrat


## 2026-11-14 14:26 CET — Otevírání aplikací z ikony Cockpitu a ruční návrat

Hotovo: Připravená místní oprava. Webové aplikace v katalogu používají
běžné odkazy do nového okna bez openeru. Pomocné otevření po asynchronním
dotazu už nerecykluje pojmenované popup okno přes about:blank; vždy
ponechá viditelný skutečný odkaz. Desktopové spouštění a ScanDocu zachované.
V hlavní liště a v dialogu Webové aplikace přidaný přímý GET formulář
Znovu otevřít Cockpit, který funguje bez JavaScriptu a drží stejný původ.
Nové načtení je výhradně na výslovný klik; upozornění uvádí ztrátu
neuloženého rozepsaného textu. Žádné resetování stránky při resume.

Rozhodnutí: Míla hlásí uváznutí ikony na poslední stránce a opakované
selhání startu Vocabulary EN z HTTPS Cockpitu. Live katalog stále vrací
stejnou veřejnou HTTPS GitHub Pages adresu. Samotné HTTP/HTTPS Cockpitu
nevysvětluje rozdílný výběr A; možný oddělený datový kontext Safari a
Home Screen aplikace. Přesný typ ikony, chování chyby a původní A na
Mílově zařízení zatím nepotvrzené. WebKit dokládá oddělení website data.

Další krok: Po checkpointu samostatně potvrdit nasazení do běžícího Cockpitu.
Předchozí p+n Vocabulary EN bylo Pages a tuto novou runtime opravu nepokrývá.

Navrhované další kroky: Fyzicky zopakovat otevřít Vocabulary → návrat →
znovu otevřít ze stejné ikony. Pokud původní A bude přístupné, exportovat
jeho zálohu z původního kontextu a teprve pak načíst do zvolené cesty.
Starou ikonu ani data webu nemazat. Obnova A není doložená.

Technický důkaz:30 cílených Python testů včetně4 nových Node scénářů
pro nativní odkazy, opakované otevření a neplatná/stará okna; GET bez
mutací a zachování manifestu. Finální log cockpit_web_navigation_targeted_final_20261114.log.
Oprava nemění localStorage/sessionStorage, klíče profilů, PWA identity,
Tailscale, HTTPS, data knihovny nebo knihovní API. Rozsah project-cockpit,
existující TVBCP tvbcp/workstreams/project-cockpit.md.

Podklady:
- https://webkit.org/blog/14787/webkit-features-in-safari-17-2/ — po přidání
  webové aplikace se další website data se Safari nesdílejí.
- https://webkit.org/blog/17333/webkit-features-in-safari-26-0/ — ikona může
  být webová aplikace nebo záložka podle Open as Web App.
- memory/reports/cockpit_home_icons_20261108.md — starší metadata sama
  neprokázala konkrétní resume chování a fyzická přejímka zůstala otevřená.

Prokázaná softwarová slabina: znovupoužití jmenovaného popupu, JS závislé
tlačítko místo nativního odkazu a chybějící ruční HTTP GET návrat při
rozbitém skriptu. Konkrétní příčina Mílova iPhonu z těchto testů neplyne.
Nejde o potvrzení opravy jeho zařízení nebo záchrany uloženého výběru A.

Závěrečné místní ověření:30 Python testů PASS /6,835s včetně4 nových
Node scénářů. Rychlá statická brána PASS a git diff --check bez chyb.
Nejde o fyzické ověření iPhonu ani o potvrzenou příčinu/obnovu výběru A.
Nové nasazení běžícího Cockpitu se samostatně potvrzuje; žádný restart,
push ani deploy touto lokální opravou neproběhl.


## 2026-11-14 15:14 CET — Jediný vstup do HTTPS Cockpitu v Safari

Hotovo: Místně připravené přesměrování starého vzdáleného HTTP vstupu
na již existující soukromou HTTPS adresu. Hlavní Cockpit i přehled kalendáře
nyní žádají režim běžného prohlížeče. Předchozí nativní odkazy aplikací
a ruční tlačítka Znovu otevřít Cockpit zůstávají součástí balíčku.

Rozhodnutí: Míla schválil vývoj jedné cesty: ikona jako záložka Safari →
HTTPS Cockpit. Přechod má nastat hned při vstupu, ne až při spuštění kamery
nebo uprostřed rozepsaného formuláře. P+n až po dokončení Willovy práce;
tento krok nepovoluje restart nebo změnu běžící síťové konfigurace.

Další krok: Po vlastním lokálním checkpointu počkat na dokončení Willovy
práce. Potom znovu auditovat společný main, integrovat oba vlastní commity
z větve data/cockpit-web-navigation-20261114 se zachováním nových Willových
změn a provést registrované p+n cíle Cockpit. Předchozí checkpoint 50f113f5
obsahuje nativní odkazy a ruční návrat; nynější navazující checkpoint HTTPS.
Žádný push, nasazení ani restart tímto krokem neproběhl.

Navrhované další kroky: Po nasazení jednorázově přidat hlavní HTTPS stránku
jako záložku Safari s vypnutým Otevřít jako webovou aplikaci; pokud se volba
na daném iOS ukazuje. Stará instalovaná ikona se tím sama nepřevede.
Nejprve ponechat starou ikonu a data kvůli původnímu výběru A. Ověřit na
iPhonu otevření Vocabulary → návrat → opětovné otevření, případně export
původního A a vědomé načtení do zvoleného kontextu. Obnova A není doložená.

Technický důkaz: 41 cílených Python testů PASS / 9,854 s, včetně skutečných
HTTP scénářů a předchozích Node navigačních testů. Finální plná brána
PASS: 3890 testů / 1013,138 s, 31 SKIP. Všech 13/13 finálních zdrojových souborů
obou vlastních kroků bajtově shodných se zmrazeným manifestem tohoto běhu.
Po této bráně už měněná pouze dokumentace a privátní účtenka, nikoli kód.

Kontrakt: Jen GET / s navigačními hlavičkami na vzdáleném Host :8770.
Dočasné 302 + no-store, query zachovaná, fragment ponechaný prohlížeči.
API, POST, lokální přístup, jiné porty a již použitý HTTPS host beze změny.
Cíl pochází výhradně z read-only Tailscale serve status --json: privátní
HTTPS 443 root proxy na 127.0.0.1:8770, bez Funnel a nejednoznačného cíle.
Host/forwarded hlavičky ani query cíl neurčují. CLI timeout 2 s, paměťová
cache 60 s, po chybě 10 s; bez ověřené konfigurace zůstane původní stránka.
Žádné automatické generování certifikátu nebo změny Serve. Skutečné
jméno tailnetu se nezapisuje do Gitu ani do cache souboru.

Identita hlavního manifestu id/start/scope / zachovaná, display=browser;
Apple capable=no na hlavním Cockpitu a kalendářovém přehledu. Samostatný
Nový úkol /calendar/task/ má dál vlastní identitu a standalone režim.
Žádné mazání nebo migrace místních dat, změny profilových klíčů,
knihovního formuláře, ISBN kamery či Willových souborů v main.

Meze: Testy prokazují serverový/klientský kontrakt, nikoli chování staré
ikony či fyzickou kameru Mílova iPhonu. iOS 26 může při Přidat na plochu
nabídnout webovou aplikaci jako výchozí i přes metadata; vypnout příslušnou
volbu je uživatelský krok. Nasazený runtime zatím tuto místní změnu nemá.
Důkazy: logs/cockpit_https_entry_targeted_final_20261114.log,
logs/cockpit_https_entry_full_gate_final_20261114.log a privátní zdrojový manifest
v data/private/cockpit_https_entry_20261114/.

Čtecí ověření skutečné konfigurace 14:57 CET: nový resolver přijímá
stávající privátní HTTPS Serve. Žádná změna sítě, hostname redigovaný;
privátní discovery_verification.json. První plný běh byl vědomě přerušen
před dokončením kvůli normalizaci lokální adresy s koncovou tečkou;
finální zdroje mají rozšířený lokální test a vlastní nový celý běh.
