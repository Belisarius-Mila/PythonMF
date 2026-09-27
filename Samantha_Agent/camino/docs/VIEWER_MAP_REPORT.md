# Viewer — minimalistický odkaz na místo (U16)

27. 9. 2026. Implementace i následné výslovně schválené nasazení.

## Uživatelské potvrzení 27. 9. 15:27 CEST

Míla po předání Vieweru hlásí „Zdá se, že vše funguje skvěle...“.
Základní funkčnost uživatelsky potvrzená; RT3 částečně, nikoli celý PASS.
Zpráva neurčuje zařízení, síť ani jednotlivé přehrání/mapový klik.
Zbývá krátká zkouška s Janou a fyzický RT4: jeden testovací záznam změnit
na Jen pro mě, synchronizovat a ověřit skrytí ve Vieweru. Potom M3/M4.
Pouze dokumentační zápis, bez změny kódu, dat nebo provozu.

## Nasazeno 27. 9. 15:17 CEST

- Míla schválil nasazení, Do deníku včetně GPS pro Janu a odkaz/restart
  Cockpitu; následně potvrdil přesnou globální brzdu pro přepnutí LaunchAgentu.
  Současná data označil za testovací a nahraditelná, pokud nejsou potřeba pro
  další zkoušky. Nic se v tomto kroku nemaže; není to plošný souhlas s mazáním.
- Přednasazovací plná brána **1833/1833 PASS** (314,386 s jednotkové sady).
  Registrovaný stop → upgrade na **125fddbbcb56** → enable-viewer → start.
  Snapshoty DB a předchozí konfigurace uchované soukromě. První start vrátil
  OSError; po ověření uvolněného portu opakovaný start uspěl. Bez force kill.
- Archiv po nasazení: 48 Momentů / 140 operací / 49 ověřených médií /
  228 226 831 B. Identita, hashe všech původních tabulek i médií a owner token
  shodné s výchozím stavem; oba recovery flagy=false. Nový pouze grant/reader
  a očištěné odvozeniny. Owner připojení telefonu beze změny.
- Camino běží, grant=true, privátní HTTPS ověřené, Funnel off; Serve se
  neměnil. Reader HTTPS 200, 6 dnů / 35 povolených Momentů / 5 mapových odkazů.
  Mapové body odpovídají povoleným zdrojům, ID owner-only/skrytých zdrojů
  v HTML nepřítomná, no-store/no-referrer platí. Bez reálného otevření mapy.
- Automatický worker dokončil přípravu: 34 povolených zdrojových médií,
  **49/49 mediálních URL HEAD 200**, žádné čekající hlášení. Video Range
  206/16 B ověřené. První kontrola zachytila běžící převod, nikoli ztrátu dat.
- Nepřihlášený Viewer, owner Bearer na Vieweru i reader na owner API vrací
  **401**. Soukromé HTML ani souřadnice nebyly vypisované do výstupu.
  Pro HTTPS audit použit existující systémový TLS context; původní holý
  Python neměl správný CA řetězec. Kontrola certifikátu se nevypínala.
- Ignorovaná místní konfigurace Cockpitu obsahuje privátní Viewer URL,
  předchozí konfigurace soukromě uchovaná, ostatní hodnoty beze změny.
  Registrované nasazení stejného **125fddbbcb56**, PID 72621→8376,
  **smoke 5/5**, `camino_viewer.configured=true`. Jeho rychlá brána je
  oddělená od předem dokončené plné sady 1833/1833. Bez push.
- Přihlášení `jana`; nové reader heslo vložené registrovaně do schránky
  Macu, nikdy do URL/chatu/Gitu. Jde o jiné oprávnění než token telefonu.
- Při nasazení **RT3/RT4 a vizuální Safari/mapový klik zbývaly**. HTTP audit
  není důkaz přehrání na Janině zařízení ani přístupu z jiné sítě.
  Následné uživatelské potvrzení a jeho hranice jsou uvedené výše.

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

## Historická provozní hranice před souhlasem s nasazením

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
