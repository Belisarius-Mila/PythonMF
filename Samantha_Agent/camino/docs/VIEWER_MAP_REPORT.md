# Viewer — minimalistický odkaz na místo (U16)

27. 9. 2026. Lokální implementace; nasazení a grant pro Janu jsou oddělené.

## Výsledek

- Existující český HTML Viewer zachovává dny, texty, foto a audio/video.
  Nově povolený Moment s GPS nabízí **Otevřít místo v mapě**, odhad přesnosti
  a upozornění, že kliknutím předá bod Apple Mapám. Nad 100 m označí polohu
  jako přibližnou. Starší Moment bez bodu odkaz nemá; nic se nedoplňuje.
- `viewer_snapshot` přidává jen `map_point` (šířka, délka, přesnost) až po
  stávající kontrole grantu, `diary`, skrytí, konfliktu a obnovy. Čas GPS
  měření, owner-only body a obsah nejsou součástí nové projekce.
- Externí HTTPS URL obsahuje pouze souřadnice na šest desetinných míst
  a konstantní popisek. Žádný token, název cesty, ID ani text deníku.
  `noopener noreferrer`, `no-referrer`, vypnutí DNS prefetch a původní CSP;
  žádná vložená mapa, mapový skript, automatické načtení nebo nový framework.
- Po doručení zámku/skrytí další HTML odkaz neobsahuje. Již otevřenou nebo
  zkopírovanou externí mapu nelze odvolat. Mediální kontrola starých URL
  a odstranění EXIF/GPS z odvozených médií se nemění.
- Bez změny iOS, podpisu, databázového schématu, owner API nebo originálů.

Formát `ll` + pevný `q` vychází z [Apple Map Links](https://developer.apple.com/library/archive/featuredarticles/iPhoneURLScheme_Reference/MapLinks/MapLinks.html).
Konkrétní otevření mapy v Safari/Mapách zůstává fyzickým testem.

## Ověření

- Projekce `tests.test_camino_viewer`: **9/9 PASS** (3 nové GPS privacy testy).
- HTTP Viewer + GPS API v izolovaném prostředí: **16/16 PASS**, včetně
  2 nových HTML/link testů a skutečné syntetické Swift JSON fixture.
- Audio layout a runtime regrese: **13/13 + 7/7 PASS**.
- Celkem cíleně **45/45 PASS**. Ověřeno: owner-only bod nepřítomen, nula
  je platná souřadnice, prázdná GPS bez odkazu, skrytí/neznámé soukromí,
  grant/obnova/konflikt, odvolání readeru, auth, referer, přesný allowlist URL,
  staré mediální URL po zámku, Range a nezměněné originály/očištěné kopie.
- Rychlá statická brána a `git diff --check` PASS.
- Syntetický samostatný HTML náhled vygenerovaný přes `viewer_preview`.
  **Vizuální/browser smoke NEOVĚŘENO:** prohlížeč není dostupný (`iab`
  nedostupný, seznam prohlížečů prázdný). Nenahrazovat jej HTML testem.
- Plná sada ani iOS build se kvůli HTML/projekci neopakovaly. Před schváleným
  nasazením zůstává povinná publikační brána. Žádné reálné GPS odeslání mapám.

## Aktuální provozní hranice

Živý registrovaný audit tohoto kroku: Camino služba vlastněná a běžící,
privátní HTTPS dostupné, Funnel vypnutý, Viewer grant **false**.
Cockpit `/api/status`: `camino_viewer.configured=false` — odkaz není nastavený.
Míla požádal pokračovat Viewerem. Souhlas s nasazením/grantem vyžádán,
zatím bez potvrzení. Nastavení odkazu a případný restart běžícího Cockpitu
vyžadují zahrnout do schváleného provozního kroku. Žádná služba nyní neměněná.

Další: potvrdit nasazení Camino serveru, grant pro Janu a nastavení odkazu
v Cockpitu včetně potřebného restartu. Nad původním archivem použít
registrované stop → upgrade → enable-viewer → start, privátní status a
ověření dat. Současný owner token neměnit. Reader má samostatné heslo;
předat ho jen soukromě, nikdy do URL/chatu/Gitu. Bez další změny Serve/Funnel.
Potom jediný společný průchod RT3/RT4 (Jana Mac/iPhone, média, odkaz/mapa,
testovací zámek), nikoli opakování celé iPhone sady. M3/M4 zůstávají.
