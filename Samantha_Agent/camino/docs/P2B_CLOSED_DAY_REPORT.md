# Camino P2-B — uzavření dne 6. 10. 2026

Stav 12. 10. 2026: **skutečný projekt z konečných Mac dat uložený a ověřený; nový Cockpit přehled lokálně**.
P2-A/IPHONE1 má Mílův PASS; P2-A/MAC1 zůstává na fyzické přehrání.
Míla výslovně zahájil P2-B a oznámil, že data prvního dne jsou na Macu
kompletní. To je vstupní tvrzení, nikoli ještě důkaz telefonu.

## Současná místní data

Registrovaný read-only audit služby potvrdil běžící owner službu, ale její
`status` sám neověřuje doručení dat. Přímý redigovaný read-only audit
autoritativních SQLite a originálů našel pro 6. 10. jednu kapitolu,
11 Momentů (1 značka, 7 video Momentů, 3 Úvahy) a 34 příloh
(11 foto, 9 audio, 14 video). Všech 34 má ověřenou účtenku, souhlasí
manifest a úplné soubory na Macu při čtení prošly velikostí i SHA-256.
Osm Momentů `diary` obsahuje 30 povolených příloh: 11 foto, 14 video a
5 audio. Tři `owner_only` Úvahy se 4 audio přílohami jsou mimo film.
Žádné soukromé ID, obsah ani cesta originálů nejsou v tomto reportu.
Read-only průchod nového P2-B validátoru nad skutečným Mac archivem prošel
a sestavil pouze v paměti výběr: 30 zdrojů, 25 obrazových záběrů a
5 zvukových voleb. Nevznikl manifest ani projekt.

## Implementace

- iPhone po výslovném potvrzení znovu objeví lokální den, vyžaduje prázdnou
  synchronizační frontu, přijatý kurzor a žádný aktivní upload ani rozpracované
  pořízení nebo textový koncept ve dni. Znovu hashuje vybrané původní soubory,
  kontroluje serverový stav a odešle přes HTTPS owner token přesný inventář.
- Mac odmítne jiný server/epochu/kurzor/autora, neúplné revize, chybějící
  položky, neověřené účtenky a změněné originály. Pod zámkem uloží create-only
  manifest, projekt a účtenku do soukromého úložiště mimo Git. Opakovaný
  identický požadavek vrací stejný projekt; jiné vstupy nebo zastaralý projekt
  odmítne.
- Projekt řadí povolené foto/video podle času pořízení a přijatého pořadí.
  Všechna videa začínají na nule a končí na původní délce. Audio je uložené
  jako samostatná volba, bez automatického střihu nebo přimíchání. Originály
  zůstávají beze změny. Kontrola projektu po restartu ověřuje aktuální
  inventář dne, soukromí a SHA-256 před budoucím renderem nebo vydáním.
- Opakovaný požadavek se stejným stavem dne používá stejné ID, takže ztracenou
  odpověď lze bezpečně zopakovat. iPhone si ID uloženého projektu pamatuje a
  po restartu znovu načte jeho platnost z Macu.

Formát P2-B je oddělený od syntetického P2-A rendereru. V tomto kroku
nevzniká MP4 ani editor; zde uložený projekt je vstup pro P2-C/D.

## Ověření a hranice

Syntetický owner HTTP test pokrývá zákaz anonymního přístupu, čekající
frontu, chybějící médium, úplné ověřené doručení, vyloučení soukromého
audia, idempotenci, znovunačtení úložiště a zneplatnění po změně soukromí.
iOS Debug Simulator build ověřuje Swift 6 kompilaci, nikoli fyzické chování.
Plná brána včetně nového API testu prošla **1876/1876**. iOS Debug Simulator
build po poslední změně Swift kódu prošel bez podpisu.

Historický stav před p+n 11. 10.: projekt 6. 10. **neexistoval**, nové API nebylo nasazené, nová
aplikace nebyla nainstalovaná a čerstvý důkaz z telefonu ještě nebyl přijatý.
Push, nasazení a instalace jsou oddělené kroky. Po jejich samostatném
schválení se na iPhonu spustí **Uložení a přenosy → Film → Ověřit a uzavřít
den**; pak se přes owner API ověří uložený projekt a 30 povolených zdrojů.

## Příprava iPhone balíčku 11. 10. 17:46 CEST

Podepsaný Release build verze 17 ze zdroje `cde61193` zastavil macOS
CodeSign s `errSecInternalComponent`; kontrola login Keychain hlásí
`User interaction is not allowed`. Je přítomna jedna platná podpisová
identita, ale její privátní klíč není v této vzdálené relaci dostupný.
Účet ani klíče se neměnily.

Nepodepsaný Release iPhoneOS build 17 prošel. Místní balíček
`Camino-P2B-17-20261011-unsigned.ipa` ve Stahování má 1 226 501 B,
SHA-256 `d4611113245932fd9ff5c19f085235d209c45b08da65a0f132e6d8ab251b1a34`;
ZIP kontrola PASS, binárka v IPA má stejný hash jako výchozí sestavení,
bundle ID zůstává `cz.pythonmf.camino.app`. Balíček **není podepsaný ani
nainstalovaný**. Zda jej SideStore na iPhonu přijme a přepodepíše,
zůstává fyzicky neověřené. Distribuce balíčku neproběhla.

## Schválené p+n — průběžný stav 11. 10. 18:03 CEST

Míla schválil push a řízené nasazení serveru. Před nasazením se ukázalo, že
výběr souborů do neměnného serverového releasu nezahrnoval nový modul P2-B a
jeho pomocnou knihovnu. Commit `2fada468` je do releasu doplnil. Plná brána
znovu prošla 1876/1876; izolovaný `git archive` release úspěšně importoval
server i P2-B pouze ze svých souborů. Audit GitHub balíčku ověřil čistý
fast-forward pěti commitů z `1208ea21` na `2fada468`, bez private cest.

Samotný HTTPS push zastavil macOS Keychain `-25308`; uložené přihlášení `gh`
je neplatné a SSH klíč GitHub nepřijal. Probíhá nové přihlášení GitHub CLI
přes jednorázový kód na Mílově iPhonu. K 18:03 není push ani upgrade
potvrzený, běžící služba stále nehlásí `film_closed_day_v1`. Před upgradem
read-only audit doložil 578 operací, 75 Momentů a 202 ověřených médií.
Stávající Tailscale Serve cestu neprovádíme znovu: existuje, ale schází její
vlastnická účtenka pro registrovaný síťový audit. Po přihlášení je další
krok přesný push, kontrolovaný stop/upgrade/start a přímý živý HTTP/HTTPS
audit při zachování archivních počtů. iPhone app ani skutečný den tím
nebudou nainstalované či uzavřené.

Aktualizace 18:10 CEST: jednorázový GitHub kód vypršel bez potvrzení.
Závěrečný audit stále ukazuje čistý lokální `main` se šesti commity před
`origin/main` (`1208ea21` → `7e43c42b`). Push ani nasazení neproběhly;
služba a Serve zůstaly beze změny. Po novém přihlášení není třeba znovu
vyrábět film, serverový kód ani IPA; je třeba znovu ověřit přesný Git stav,
pushnout a nasadit podle schváleného p+n.

## Dokončené p+n — 2026-10-12 16:45 CEST

Míla potvrdil běžnou funkčnost Camina po poledním znovunačtení posledního
buildu a zadal dokončení P2-B s prioritou zachování aplikace. Přesně potvrdil
globální brzdu pro vlastní LaunchAgent a dokončil GitHub device přihlášení.
Přesný fast-forward `1208ea21` → `e95568b7` byl odeslán. Pro push se pouze
v daném příkazu použil helper GitHub CLI místo nedostupného Keychain;
žádné tajemství nešlo do argv, výstupu nebo Gitu. GitHub CLI samo uložilo
přihlášení do místního souboru s ověřenými soukromými právy.

Před zastavením prošlo 71/71 cílených serverových, přenosových, obnovovacích,
Viewer a servisních testů. Izolovaný archiv přesného releasu se načetl
produkčním Pythonem v režimu `-I`; závislosti a zdroje API/domény,
autentizace, médií, obnovy i Vieweru jsou shodné s běžícím předchůdcem.
Schéma DB zůstává 3. Kód odpovídá plně ověřenému `2fada468` (1876/1876);
pozdější commity do `e95568b7` jsou pouze dokumentační, proto se nezměněná
plná místní brána neopakovala.

Registrované stop/upgrade/start přepnuly vlastní službu z `16de4d0b7973`
na `e95568b7999e`. Upgrade zachoval původní konfiguraci, LaunchAgent a
čtyři konzistentní DB snapshoty s ověřenými SHA-256 účtenkami. Mimo
`code_root` jsou konfigurační hodnoty shodné, včetně původních cest
archivu a přístupových DB. Běžící služba má vlastněnou definici a Viewer
grant je zachovaný. Neproběhla instalace telefonu ani restart Cockpitu.

Redigovaný audit před přepnutím a po startu je přesně shodný: **624 operací,
82 Momentů, 216 ověřených originálů, 1 673 901 399 B a tři cesty**.
Všech 216 původních souborů prošlo úplným SHA-256; identita serveru, epocha,
kurzor i otisk cest jsou zachované, oba recovery/export flagy jsou false.
Serve otisk je před/po shodný, privátní route zůstala stejná a Funnel off.
Registrovaný síťový status má nadále chybějící vlastnickou účtenku existující
route; nic se nepřenastavovalo a skutečné HTTPS bylo ověřené přímo.

Živé loopback i HTTPS kontroly: owner health/state 200,
`film_closed_day_v1` přítomné, nakonfigurované filmové API odmítá anonymní
POST (401) a pro neexistující syntetické ID vrací `project_missing` (404).
Viewer a mapa 200; foto, původní povolené audio a video proxy dne 6. 10.
vracejí Range 206, 16/16 požadovaných B a správné MIME. Anonymní Viewer 401,
soukromý owner-only mediální zdroj 404. Cockpit smoke 5/5 PASS.

**Hranice:** serverový publikační blokátor je odstraněný, ale skutečný den
nebyl uzavřený a žádný reálný filmový projekt nebyl vytvořený. Mílovo hlášení
běžné funkčnosti aplikace neuvádí číslo buildu ani fyzický P2-B test. Telefon
dnes zůstal beze změny. Další je na fungujícím telefonu ověřit
**Uložení a přenosy → Film → Ověřit a uzavřít den** pro 6. 10. a potom
ověřit skutečnou účtenku a aktuální povolené zdroje. P2-A/MAC1 zůstává
na fyzickém přehrání po návratu; P2-C/D nejsou zahájené.

### GitHub kontrolní prostředí — oprava po prvním pushi

GitHub běh `38264584628` pro `e95568b7` skončil 16 chybami prostředí:
15 testů odmítl starší Xcode Git s `unknown option: --attr-source=FETCH_HEAD`
a nový serverový test se nenačetl kvůli `ModuleNotFoundError: httpx`.
Workflow instaloval jen kořenové závislosti a jeho macOS 14 vybíral starý
Apple Git přes `xcrun`, i když byl jiný Git v PATH.

Oprava mění pouze `.github/workflows/cockpit-quality-gate.yml`: runner
macOS 15, explicitní Xcode 26.3 (shodné s ověřeným místním toolchainem),
čerstvý preflight skutečně vybraného Gitu s `--attr-source`, instalaci
kořenových i serverových závislostí a jejich společný cache klíč/trigger.
Běžící služba zůstává na ověřeném `e95568b7999e`; tato oprava nemění
Camino aplikaci ani serverový kód a nevyžaduje další nasazení.
YAML a shell syntaxe prošly. Čerstvá plná místní brána prošla
**1876/1876 PASS** (246,151 s testů). [GitHub běh 38266173656](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38266173656)
pro commit `31927650` dokončil bránu s **success**: 1876 testů OK,
10 podmíněně přeskočených, 211,019 s testů. Preflight potvrdil skutečně
vybraný Apple Git 2.50.1 a podporu `--attr-source`; oba requirements
se úspěšně nainstalovaly. Oprava CI je ověřená. Dostupnost použitého
Xcode 26.3 byla předem ověřená v oficiálním
[runner image přehledu](https://github.com/actions/runner-images/blob/main/images/macos/macos-15-Readme.md).

Závěrečné redigované čtení filmového úložiště potvrdilo 0 projektů;
skutečný den nadále čeká na explicitní telefonní uzavření.
Běžící serverový kód je mezi `e95568b7` a `31927650` přesně shodný.
Závěrečná dokumentace a CI oprava nevyžadují další restart služby.

## Konečná Mac sada — vlastnické potvrzení a Cockpit přehled

Míla upřesnil, že 6. 10. považuje za konečnou sadu na Macu a v Cockpitu
vidí jen syntetický Film P2-A. Zadání dalšího potvrzování v telefonu nebylo
jeho záměrem. Po vysvětlení zadal pokračování vytvořením projektu z Mac
sady a přehledem v Cockpitu. Tím pro tento den výslovně přijal původ
`owner_confirmed_mac`; nezávislý důkaz nulové telefonní fronty se netvrdí.
Původní telefonní API zůstává odděleně zachované, bez změny aplikace.

Nový `app/camino_film_workshop.py` používá jen SQLite `mode=ro` adaptéry.
Neinstancuje zapisující RevisionStore/MediaStore, nemigruje schéma,
nerecoveruje uploady a neovládá službu. Sdílený P2-B validátor kontroluje
aktuální revize, serverové flagy, úplnost přijaté Mac sady, manifesty,
verified session/receipt a SHA-256 všech originálů dne. Filmové soubory
mají vlastní soukromý kořen mimo Git a mimo všechny archivní adresáře;
obsahují `mac-confirmation.json`, neměnný manifest, projekt a účtenku.
Opakování stejného inventáře používá stejný projekt, předchozí revize se
nepřepisují. Změna zdrojů/soukromí zneplatní přehled; neplatný stav
nevydává staré počty, názvy ani položky. Originály se nekopírují ani nemění.

Registrované `camino_mac_film_status/create` a Cockpit GET/POST mají
samostatnou potvrzovací bránu. UI Film Camino ukazuje skutečný projekt,
počty a chronologickou obrazovou osu, syntetické P2-A je pod samostatným
rozbalením. Seznam se znovu ověřuje po návratu do popředí a po minutě;
staré odpovědi se nepoužijí a chyba/soukromí smaže starý přehled.
Nejde o editor ani render a nové HTTP cesty nevydávají původní média.

Skutečný projekt 6. 10. byl autorizovaně uložen a je validní: **30 zdrojů,
11 fotografií, 14 celých videí, 5 zvukových voleb, 25 obrazových položek**.
Foto má výchozí 3 s, žádné automatické video zkrácení; osa **200 475 ms**.
Archiv před/po je přesně shodný: 624 operací, 82 Momentů, 216 originálů,
1 673 901 399 B, stejné identity/epoch/cursor a všechny SHA-256.
Běžící Camino nadále používá `e95568b7999e`, telefon a síť beze změny.

12/12 nových syntetických bezpečnostních/HTTP/JS testů a 82/82 souvisejících
prošly. Oddělený loopback náhled Cockpitu vrátil 200, nový vstup/panel,
odlišený syntetický test a skutečný projekt 30/25/5. CUA nemá prohlížeč,
proto vizuální UI/Safari přejímka je NEOVĚŘENO. Závěrečná plná brána **1888/1888 PASS** (297,270 s testů);
nové zdrojové soubory, push a nasazení Cockpitu nejsou publikované.
Další je lokální checkpoint a po samostatném souhlasu pouze Cockpit p+n.
