# Názvy z telefonu, přílohy a přehled dne — B01/B02/B03

27. 9. 2026. Lokální implementace na výslovný pokyn Míly. Nasazení serveru,
push, nový podpis a fyzická aktualizace telefonu jsou samostatné kroky.

## B03 — názvy příloh a přehled dne, 27. 9. 2026

Míla fyzicky potvrdil názvy Momentů a jejich přenos v buildu 7. To není PASS
mobilní regrese B01 ani všech dalších scénářů. Následně schválil tento poslední
společný funkční balíček; po jeho aktualizaci chce delší běžné testování,
sběr připomínek do bufferu a žádné další rychlé vydávání kosmetických verzí.
Ztráta dat, únik soukromí či nefunkční záznam/přenos zůstávají důvodem k opravě.

Lokálně implementováno (zatím bez nasazení, podpisu a instalace):

- Každá fotografie, video a celý hlasový komentář mají vlastní nepovinný
  název vedle názvu celého Momentu. Stejné Přidat/Upravit název, 160 znaků,
  prázdné pole název odstraní. Funguje i u starších již přenesených příloh.
- Názvy jsou nové metadata revize, ne změny souborů, create manifestů či
  audio layoutu. Přejmenování nepřidává přenos již ověřených médií.
  Jeden komentář = audio session; technické segmenty nemají jednotlivé názvy.
- Telefon řadí okamžiky podle zachyceného UTC času sestupně; shodné časy mají
  stabilní ID tie-break. Přejmenování starší položku neposouvá. Seznam přidává
  počty Foto / Video / Audio, audio po session, ne po segmentech.
- Viewer zachovává současné pořadí od rána k večeru. Každý Moment je nativní
  rozbalovací karta s názvem, časem a počty. Výchozí stav zavřený, nic se samo
  nepřehrává ani neotvírá nejnovější položku. Úvodní seznam dnů se nemění.
- Názvy, počty i HTML vznikají až z povolené projekce; zamčené/skryté zdroje
  se nezobrazí ani v záhlaví. Titulky jsou escapované. Starší audio bez layoutu
  má poctivé označení neověřeného seskupení, ne vymyšlený počet komentářů.

### Kompatibilita B03 a pořadí nasazení

Volitelná pole v dosavadním místním JSON journalu a serverovém JSON těle;
bez Core Data či SQLite schématové migrace. Nová revize attachment_title
obsahuje druh cíle, jeho stabilní ID a název. Server ověřuje příslušnost
fotografie/videa nebo audio session k danému Momentu. Neznámý/cizí cíl odmítne.
U nové session musí její neměnný audio layout dorazit před názvem. Planner
doplňuje tuto závislost, nepřepisuje již připravené přesné obálky ani účtenky.

Nový feature gate attachment_title_v1 zastaví odesílání čekajících názvů
příloh na starý server; lokální data zůstanou. Nejdříve server, potom telefon.
Návrat na starší aplikaci/server po těchto revizích není podporovaný.
Mac editor ani zpětná synchronizace nevznikly; Jana je pouze čtenář.
Živé nasazení 403180320849/build 7 z následující historické sekce se tímto
lokálním vývojem nemění. Build 8 bude samostatná aktualizace stejné aplikace.

### Ověření B03

- Swift jádro 49/49 PASS: přílohy nezávisle, reopen, retry, clear, cizí cíl,
  revize, stabilní řazení a staré obálky; již verified média zůstávají verified.
- Python doména/projekce/audio layout 31/31 PASS.
- Izolované HTTP/media testy 15/15 PASS; skutečné Swift zprávy → ASGI API →
  reopen → Viewer 1/1 PASS. Dvojí replay nepřidává revize, více audio segmentů
  je jeden komentář, privátní/skryté názvy ani počty neunikají.
- Generic iOS Debug build 0.1.0 (8), CODE_SIGNING_ALLOWED=NO: PASS.
- Simulátor iPhone 14 Plus: 2/2 UI testy PASS. Názvy foto/audio příloh,
  reopen a pořadí (49,101 s); původní název Momentu/reopen/vymazání (43,344 s).
  Izolovaná fixture používá foto metadata bez originálu a syntetické tiché
  audio; nejde o fyzickou kameru/mikrofon ani nový podepsaný balíček.
- Závěrečná plná projektová brána: 1838/1838 PASS (380,509 s jednotková sada).
- Browser automatizace v této relaci není dostupná. Syntetický HTML náhled
  vygenerovaný; HTML kontrola 13 zavřených karet, 3 médií, názvů, počtů,
  pořadí a nepřítomnosti soukromé věty PASS. Interaktivní Safari/Janina
  zařízení zatím NEOVĚŘENO. Generátor: camino.server.tests.viewer_preview.
- Logy v /private/tmp: camino-attachments-swift.log, camino-attachments-python.log,
  camino-attachments-http.log, camino-attachments-ui.log,
  camino-attachments-build-final.log, camino-attachments-full-gate.log.
- Fyzický build 8 a nová mobilní regrese NEPROVEDENO. Žádný push, nasazení,
  podpis, IPA import, změna tokenů/Tailscale ani práce nad osobním archivem.

### Přejímka a následné klidnější testování

1. Aktualizace stejné app bez odinstalace; staré záznamy a názvy zůstanou.
2. Jeden Moment se dvěma fotografiemi, videem a hlasovým komentářem: různé
   názvy offline, změna a vymazání, zavřít/otevřít. Název Momentu se nemění.
3. Odeslat a porovnat Viewer. Změnit už přenesený název a ověřit nulový nový
   mediální objem; nový název musí dorazit i bez opětovného videa.
4. V telefonu nové nahoře, přejmenovaný starý zůstává dole; ve Vieweru ráno
   nahoře. Safari Mac+iPhone: rozbalit/sbalit delší den, přehrát audio/video.
5. Jen pro mě a doručený zámek/skrytí: pryč celý obsah, názvy i počty.
   Připojit dosud neověřenou B01 mobilní dávku a nový záznam bez zděděného grantu.

Potom několik běžných delších použití stejné verze. Drobnosti shromažďovat,
neinstalovat další build po každé připomínce. M3 nezávislá záloha a M4
předcestovní kontrola zůstávají; nejsou prohlášené za hotové ani zrušené.

## Historie B01/B02: nasazení serveru 27. 9. 20:35 CEST

Míla schválil pokračování nasazením, podpisem a instalací a následně potvrdil
novou přesnou globální brzdu. Registrovaný stop/upgrade/start dokončený;
server release 403180320849 obsahuje implementaci B01/B02 z 7dcee1c8.
Živý HTTPS API stav potvrzuje moment_title_v1, Viewer a všech 6 denních stránek
HTTP 200. Anonymní přístup a záměna owner/reader odmítnuté HTTP 401.
Před/po shodná metadata, serverová identita i owner/reader tokeny. Zachováno
51 Momentů / 155 operací / 58 hashově ověřených médií (263 578 290 B),
oba recovery flagy=false. Upgrade uchoval DB snapshoty a starou konfiguraci.
Soukromá HTTPS trasa zdravá, Funnel off; Tailscale ani Cockpit se nepřepínaly.

Camino 0.1.0 (7), zdroj 7dcee1c8, podepsaný generic iOS build PASS.
Strict codesign PASS, stejné ID cz.pythonmf.camino.app, stejný tým a pokrytí
zařízení jako build 6. Profil do 4. 10. 2026 18:07 CEST. Pro zvolenou instalaci
přes SideStore se podepisuje znovu; jeho výslednou expiraci je třeba odečíst
po importu, nejde o záruku provozu do 17. 10.

Ve Stahování: Camino-Names-7-20260927.ipa, 1 065 916 B, SHA-256
`8837340d63fcc3caecb095a07a39a1ef46ebcaa04d00613f8bbe794b6c413a87`.
ZIP integrita a přesná shoda všech 5 souborů s podepsanou app PASS.
První zabalení přidalo AppleDouble metadata; finální balíček vznikl bez nich
a prošel úplnou kontrolou. Původní build 6 IPA se neměnil.

**Server je připravený; nyní lze importovat.**
SideStore: LocalDevVPN, zelené Device Reachability, import buildu 7,
Customize AppID ponechat zapnuté; pro tento import zkontrolovat původní ID
a odškrtnout Append Team ID. Žádná odinstalace. Po importu kontrola starých
dat a Přidat/Upravit název; pro přenos přepnout na Tailscale.
Import a fyzický přenos názvu stále NEPROVEDENO. Žádný push.

## Historický rozsah a rozhodnutí B01/B02

- Jeden nepovinný název celého Momentu: označený okamžik, samostatná fotografie,
  video, komentář i úvaha. Připojená média patří pod tento název; samostatné
  přejmenování každého souboru/úseku nahrávky nyní neimplementujeme.
- V detailu Přidat/Upravit název, jeden řádek do 160 Unicode skalárů,
  Uložit/Zrušit, prázdné pole název odstraní. Ukládání funguje offline,
  nezdržuje pořízení. Seznam i detail zobrazí název, původní čas/typ zůstávají.
- Tok je **iPhone → Mac → Viewer**, bez přenosu oprav z Macu do telefonu.
  Jana je nadále jen čtenář. Webový editor teď nevzniká.
- Adamova volba pro případné pozdější dokončení: malý owner editor na Macu,
  oddělený od čtecího přístupu Jany. Jeho ruční název bude lokální přepis
  zobrazení s předností před telefonním názvem; další příjem z telefonu jej
  nesmaže. Možnost vrátit se k názvu telefonu. Implementace až podle času/kreditů.

## Uložení a kompatibilita

- Telefon přidává volitelná pole do existujícího JSON journalu v SettingRecord,
  nikoli atributy Core Data. Starý journal chybějící název chápe jako prázdný.
- Uložení vytvoří atomickou metadata operaci title a novou revizi. Retry
  stejného ID je idempotentní; jiné tělo pod stejným ID a stará revize selžou.
  Smazání názvu je další revize, originály ani GPS se nemění.
- Původní create_moment payload zůstává nezměněný i po pojmenování. Dříve
  uložené přesné obálky se nepřegenerují. Server umí historický objekt bez
  title; prázdný title do wire nepřidává, aby se nerozbilo porovnání identit.
- Server oznamuje moment_title_v1. Telefon před odesláním čekajícího názvu
  vyžaduje podporu a na starém serveru srozumitelně žádá aktualizaci Macu;
  názvy zůstávají lokálně. **Nejdříve nasadit server, potom aktualizovat telefon.**
- Viewer vydává jen povolené názvy přes existující diary/nonhidden projekci,
  escapuje HTML; zámek či skrytí odstraní i název. Reader nesmí zapisovat.
- Návrat na starší aplikaci po vytvoření title operací není podporovaný:
  starý dekodér tuto operaci nezná. Pro případ obnovy zachovat existující kopie;
  nikdy neodinstalovávat aplikaci kvůli aktualizaci.

## B01 — pravdivý stav po mobilním přenosu

Po ověření posledního média se grant správně ruší. Dosavadní synchronize
i networkChanged potom bez kontroly práce hlásily čekání na Wi-Fi.
Nová společná rozhodovací funkce zachová dříve potvrzenou kopii jen při
známé identitě serveru, úplném pokrytí místních Momentů, nulové čekající práci,
bez chybějících audio metadat a bez recovery flagu. Nejde o nové živé spojení.
Nové médium/pending metadata, ztracená účtenka či obnova nejsou zelené;
další dávka nezdědí mobilní souhlas. Hlášení čekání uvádí počty čekající práce.

## Ověření B01/B02

- Swift jádro: 47/47 PASS, včetně názvu po znovuotevření, retry, vymazání,
  odmítnutí neplatného názvu/revize, stabilního create payloadu a mobilního stavu.
- Python doména/projekce: 21/21 PASS, včetně historické identity, revizí a soukromí.
- Izolované HTTP Viewer testy: 14/14 PASS, včetně escaping a zákazu reader zápisu.
- Skutečné Swift obálky → izolované ASGI API → znovuotevření DB → Viewer:
  1/1 PASS, včetně opakovaného odeslání a druhého názvu.
- Simulátor iPhone 14 Plus: 1/1 UI test PASS (53,6 s): zadání, uložení,
  ukončení/znovuotevření, kontrola názvu a jeho vymazání.
- Generic iOS Debug build 0.1.0 (7) PASS, CODE_SIGNING_ALLOWED=NO.
  Výstup v /private/tmp/camino-names-device-derived; není podepsanou instalací.
- Plná projektová brána: **1836/1836 PASS**, jednotková sada 445,116 s.
  Logy: /private/tmp/camino-names-full-gate.log, camino-names-swift.log,
  camino-names-http.log, camino-title-wire.log, camino-names-ui.log
  a camino-names-device-build.log (všechny ve stejném dočasném adresáři).
- Fyzický iPhone/import, živý přenos názvu a skutečná mobilní regrese:
  **NEPROVEDENO**. Server nasazený a ověřený výše, telefon se zatím nezměnil.

## Původní krátká fyzická přejímka B01/B02

1. Aktualizovat tutéž aplikaci bez odinstalace; stará data jsou dostupná.
2. Offline pojmenovat jeden okamžik, změnit název, zavřít/otevřít aplikaci.
3. Malou dávku povolit přes mobilní data a odeslat: úplná kopie potvrzená Macem,
   žádné falešné Čeká na Wi-Fi; název správně ve Vieweru.
4. Další nový záznam bez nového souhlasu čeká. Soukromý název do Vieweru nejde;
   po doručení zámku zmizí i dříve zobrazený název. Vymazání názvu vrátí typ/čas.
5. Bez dostupného Macu nesmí nový název ani médium vypadat jako potvrzené.

Žádná nová matice mikrofonu/hovorů: recorder se neměnil. M3/M4 zůstávají.
