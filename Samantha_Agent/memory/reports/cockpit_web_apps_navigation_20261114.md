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
