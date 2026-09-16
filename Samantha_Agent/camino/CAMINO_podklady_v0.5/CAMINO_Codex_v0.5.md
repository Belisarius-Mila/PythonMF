# Camino — předání a postupná zadání pro Codex v0.5

**Aktuální funkční zdroj:** `CAMINO_funkcni_specifikace_v0.5.md`  
**Akceptace:** `CAMINO_akceptacni_testy_v0.5.md`  
**Stav:** zadání, nikoli implementace. V tomto balíčku se neprovedl build, párování ani test telefonu.

## 1. Způsob práce

Pracuj vždy na jednom zadaném kroku. Nepřeváděj dlouhou specifikaci na pokyn vyrobit celou aplikaci najednou. Zachovej pravidla U01–U14 a funkční význam F01–F86. Návrhové hodnoty D a technické parametry lze změnit na základě důkazu, s krátkým ADR; nevracej technický výběr uživateli jako dotazník.

Před začátkem si přečti `AGENTS.md`, hlavní specifikaci a konkrétní úkol. Soubor AGENTS je krátké projektové vedení; úplná specifikace zůstává zvlášť. Používání `AGENTS.md` dokumentuje OpenAI: `https://developers.openai.com/codex/guides/agents-md/`.

Testovací data jsou syntetická. Všechny běžné testy mají mock AI. Neodesílej skutečné audio poskytovateli ani nekupuj členství bez samostatného provozního kroku. Souhlas s AI obsahem není schválená částka.

Hardware, k němuž nemáš přístup, označ NEOVĚŘENO. Nespouštěj linuxový audit a nepopisuj jeho výsledek jako stav Mílova Macu. Nedokládej zkoušku zámku, Bluetooth nebo hovoru úspěšným unit testem. Audit nesmí bez dovolení změnit bezpečnostní nastavení, veřejnou síť, účty ani data.

## 2. Etapy a malé části

Pořadí C00–C11 zachovává v0.3. Uvnitř etapy jde o několik samostatných předávek, nikoli jeden obří commit.

| Úkol | Konkrétní výsledek | Hlavní vazba na testy | Co v tomto kroku ještě nedělat |
|---|---|---|---|
| C00 | Read-only audit vývojového Macu, iPhonu, instalace a domácího serveru včetně Tailscale, uspávání, `launchd`, Cockpitu a Viewer readiness. | Podklady pro T079,T089–T091,G0,G8 | Žádné nákupy, změny napájení/ACL, Funnel ani plná aplikace. |
| C01a | Malý offline audio prototyp: Start/Stop, skutečný vstup, soubor a přehrání. | T015,T017,T025 | Bez AI, galerie a finálního datového modelu. |
| C01b | Pokračování audia se zámkem, přerušení a vědomé pokračování. | T016,T018–T021,T024,T059 | Bez vzdáleného ovládání libovolnými sluchátky. |
| C01c | Obnovitelné části a journal; doložení kontinuity a rozsahu ztráty po chybě. | T022,T023,T061 | Neoznačovat neuzavřený úsek za zachráněný. |
| C02a | Minimální přijímač syntetického souboru a porovnání hashe přes soukromé HTTPS. | Základ T043,T048,T051 | Ještě ne plný produkční upload server. |
| C02b | Experiment velkého souboru, souborových částí a chování iOS na cizí síti. | T043,T047–T050 | Žádný veřejný alternativní endpoint. |
| C03a | Datové objekty, revize, časové příklady a politika soukromí. | T005,T008,T027–T032,T039,T041 | Nepřidávat více autorů nebo sdílenou editaci. |
| C03b | Verze kontraktu API a kontraktní testy včetně chyb, epochy a idempotence. | T044–T046,T053,T058 | Kontrakt nevytváří falešný důkaz chování telefonu. |
| C04a | Místní úložiště, hlavní obrazovka, zachycení Momentu a integrace audio modulu. | T001–T010,T015,T024–T026 | Bez placené AI a rodinného exportu. |
| C04b | Foto a video: ukládání, připojení, orientace, tiché video a přerušení. | T007–T014,T060 | Bez komplexního fotoaparátu a editoru klipů. |
| C04c | Import, správná reprezentace, nejistý čas a deduplikace. | T033–T037 | Žádné skryté smazání ve Fotkách. |
| C04d | Dnes, detail, textový koncept, zámek, skrytí a lokální čtení. | T019–T021,T026,T030,T038–T041 | Web jako druhý editor není P0. |
| C04e | Nouzový export bez serveru a bez duplicitní kopie celé cesty. | T062–T064 | Nesmí být zaměněn s rodinným výběrem. |
| C05a | Produkční příjem částí, manifest, ověřená finalizace a obnova journalu. | T043–T046,T052,T061 | Bez tvrzení přesně-jednou síťového doručení. |
| C05b | iOS fronta, priority, pauza, jednorázová mobilní dávka a znovuporovnání. | T047–T053,T058 | Žádné skryté povolení dat pro budoucí média. |
| C05c | Čtyři stavové osy a uživatelské texty chyb. | T050,T051,T054,T055 | Přepis není záloha. |
| C06a | Spravovaný základ serveru, autorizační režim, owner web/stav a bezpečný webový základ pro Viewer. | T003,T048,T078,T091 | Bez Viewer obsahu, úprav soukromí nebo veřejného endpointu. |
| C06b | Snapshot záloh, identita cíle, hash doklady a skutečná obnova. | T054–T058,T064 | Kopie do jiné složky stejného disku nestačí. |
| C06c | Zabezpečený restart, logy bez obsahu, upgrade/migrace/rollback. | T059,T078,T079 | Žádné plošné vypnutí FileVault nebo ochrany dat. |
| C07a | Trvalý worker, mock adaptéry, cache klíče, náklady a chybové stavy. | T065,T066,T069 | Žádná skutečná placená volání. |
| C07b | Česká sada přepisu a jemné korektury; skutečný pilot až po nastavení limitu. | T042,T067,T068,T071 | Bez automatické transkripce všeho ve videích. |
| C07c | Ochrana lidských revizí, zdrojová provenience a data jako inertní text. | T010,T038,T055,T069 | Bez nástrojových oprávnění jazykového modelu. |
| C08a | Osobní denní šablona, místní cache a přenositelný HTML/Markdown archiv vlastníka. | T026,T040,T064,T071 | Owner archiv není Viewer pro Janu; může obsahovat `Jen pro mě`. |
| C08b | Dávkové owner souhrny, maximální čekání, neaktuální výsledky a pozdní vstupy. | T027–T030,T038,T057,T070 | Bez tlačítka Uzavřít den; owner souhrn se nesmí použít jako Viewer-safe text. |
| C08c | `viewer_safe` projekce, Janin denní souhrn a atomický generátor index/den HTML. | T081,T087,T088,T092,T093 | Bez mediálních originálů, bez čtení owner souhrnu, bez veřejné sítě. |
| C08d | Viewer mediální deriváty: foto thumbnail/preview, video poster+proxy+Range, povolené audio. | T082–T086,T094 | Originály neměnit ani běžně neservírovat; žádná GPS/EXIF v kopiích. |
| C08e | Tailscale Serve přístup, přímá URL, Cockpit link/health a `launchd` provozní služba. | T089–T092 | Žádný Funnel, veřejný port, auto-login ani vypnutí FileVaultu. |
| C08f | Vzdálený Viewer test s Janiným MacBookem/iPhonem a privacy fixture. | T095,G8 | Neprohlásit PASS bez skutečné jiné sítě/zařízení. |
| C09 | Reálný den, vyhodnocení chyb, kapacity, instalace, Viewer a zmrazení vydávaného rozsahu před 2. 10. | Celé relevantní P0, zejména T079–T095 | Nezakrýt kritický FAIL grafikou; po freeze nepřidávat kosmetický scope. |
| C10a | Povolený seznam zdrojů a nezávislý výběrový text. | T072,T074 | Nikdy nepoužít celý osobní souhrn. |
| C10b | Očištěné kopie fotografií, náhled, finální kontrola a systémové sdílení. | T073–T076 | Žádné autonomní odesílání nebo tvrzení doručení. |
| C11a | Ověřený import skutečného exportu hodinek. | T077, F67 | Žádná domyšlená stopa mezi foto body. |
| C11b | Výběr a verzovaná časová osa s vlastním zvukem, titulky a kontrolou soukromí. | T077, F68,F69 | Bez klonování hlasu, soukromých vstupů a vymyšlených záběrů. |
| C11c | Normalizace pracovních kopií, render, kontrola a export filmu. | T012,T077, F70 | Originály neproměňovat nevratnou kompresí. |

Testy T019–T021 u klientské integrace se znovu provedou po změnách zvukových funkcí, nejen jednou v izolovaném prototypu. Prototyp neprokazuje, že pozdější galerie či přehrávač nic nerozbily.

## 3. První zadání připravené k vložení do Codexu — C00

### Cíl

Prostuduj v0.5 a vytvoř doložený **read-only audit skutečného prostředí**, který ověří dvě paralelní cesty: (1) nativní iPhone aplikaci a legitimní instalaci platnou přes celou pouť, (2) domácí Mac jako soukromý server s Tailscale a připraveností pro read-only Camino Viewer pro Janu. **Release cíl je nejpozději 2. října 2026.** Zatím neimplementuj celou aplikaci a neměň uživatelův systém.

Pokud už z dřívějšího C00 existují auditní dokumenty, nepřepisuj je naslepo ani neopakuj drahé/rušivé kroky. Ověř jejich datum a důkaz, zachovej platná zjištění a doplň pouze delta audit pro nové požadavky v0.5.

### Vstupy

`AGENTS.md`, `CAMINO_funkcni_specifikace_v0.5.md`, `CAMINO_akceptacni_testy_v0.5.md`, tento plán a případné existující `docs/ENVIRONMENT_AUDIT.md` / `docs/DECISIONS.md`. Starší v0.4/v0.3 jsou historie. Známe iPhone 14 a informaci, že Xcode je nainstalovaný; konkrétní verze/systém musí audit doložit. Domácí server nesmí být automaticky ztotožněn s vývojovým Macem.

Uživatel chce během pouti nechat domácí MacBook zapnutý jako server. Jana má používat vlastní MacBook/iPhone a stávající Cockpit může sloužit jako rozcestník. To jsou provozní požadavky, nikoli důkaz, že Tailscale/ACL/uspávání/launchd už jsou správně nastavené.

### Povolené read-only činnosti

1. **Vývojový Mac / Xcode** — zjisti `sw_vers`, `uname -m`, `xcodebuild -version`, `xcrun --sdk iphoneos --show-sdk-version`, dostupnost podepisování bez výpisu tajných certifikátových dat a volné místo. Z aktuálních oficiálních podkladů ověř kompatibilitu Xcode/macOS/iOS a cestu instalace na cílový telefon. Nevyžaduj App Store, pokud není pro náš soukromý scénář potřeba.

2. **iPhone** — pokud je skutečně připojený a autorizovaný, zjisti pouze to, co jde bezpečně doložit pro build/deploy. Bez zařízení označ manuální části NEOVĚŘENO. Nepoužívej simulátor jako důkaz background audia, zamčení, mikrofonu nebo Tailscale na telefonu.

3. **Domácí Mac server** — pokud je tento Mac skutečně dostupný a autorizovaný, dolož: macOS/architekturu, volné místo, očekávané datové umístění, existenci/způsob druhé zálohy, `fdesetup status`, čitelné nastavení napájení/uspávání (`pmset -g custom` nebo ekvivalent), a zda stávající serverové procesy závisejí na otevřeném Terminálu.

4. **Tailscale** — pokud je nainstalovaný, použij read-only stav/verzi a stav Serve (např. `tailscale status`, `tailscale serve status` podle dostupné verze). Nezapisuj tailnet, ACL, Serve konfiguraci ani DNS. Zaznamenej, zda existuje soukromá cesta, kterou lze později použít pro FastAPI/Viewer. **Funnel je zakázaný.**

5. **Cockpit** — pokud je jeho projekt/konfigurace v dostupném workspace nebo na serveru, najdi pouze bezpečný integrační bod pro: `Otevřít Camino`, stav backend/worker/Viewer, poslední synchronizaci a poslední Viewer build. Cockpit nesmí být jediná cesta k Vieweru a nesmí získat právo měnit Camino obsah.

6. **Spravovaný start** — zmapuj, zda již existují relevantní `launchd` služby a jaký bude nejjednodušší budoucí model backend/worker/Viewer. V C00 žádný plist nevytvářej ani nenačítej. Zvlášť popiš očekávané chování po restartu před/po přihlášení a co je třeba fyzicky otestovat s FileVaultem.

7. **Janina zařízení** — bez skutečného autorizovaného přístupu pouze definuj testovací matici Safari macOS / Safari iOS z jiné sítě. Nevyžaduj po uživateli technické volby. Neprohlašuj vzdálený přístup za funkční bez zkoušky.

### Zakázané činnosti

Žádná aktualizace systému, instalace velkých nástrojů, nákup, změna Apple/Tailscale účtů, vytvoření nebo změna ACL/Serve, otevření veřejných portů, Funnel, změna `pmset`, změna FileVaultu, auto-login, instalace `launchd` služby, restart stroje, mazání/přesun osobních dat nebo zásah do produkčního Cockpitu. Žádné reálné AI klíče ani osobní média v testech. Nevypisuj sériová čísla, tokeny, přesné tailnet identity, soukromé IP nebo jiné tajné údaje do reportu.

### Povinná předávka

Vytvoř nebo bezpečně aktualizuj:

- `docs/ENVIRONMENT_AUDIT.md` — role **vývojový Mac / iPhone / domácí Mac**, stav `OVĚŘENO / NEOVĚŘENO / BLOKUJE`, stručný důkaz a dopad.
- `docs/VIEWER_READINESS.md` — Tailscale, Serve, Cockpit, napájení/uspávání, restart/launchd, Safari Mac/iPhone a konkrétní chybějící zkoušky pro G8. Žádná tajemství.
- `docs/DECISIONS.md` — doporučená cesta nástrojů, instalace a serverové architektury; Viewer má zůstat samostatná read-only služba, Cockpit jen link/health.
- `tasks/C01a_AUDIO_PROTOTYPE.md` — nejmenší další implementační krok: Start/Stop, skutečný vstup, lokální soubor, přehrání. Viewer se ještě neimplementuje před ověřením audio základu.

Pokud audit zjistí, že některá Viewer část lze provést nezávisle na iOS prototypu, pouze ji zapiš do backlogu pro C08c–C08f; neskákej dopředu a nevytvářej celý Viewer v C00.

### Závěrečné shrnutí pro uživatele

Česky uveď: co je skutečně doložené, co je NEOVĚŘENO, zda něco **blokuje termín 2. října**, a **jeden následující malý krok**. Nevracej produktový dotazník U01–U14. Neptej se uživatele na framework, databázi, media codec, šablonovací knihovnu ani launchd strukturu; to jsou technická rozhodnutí projektu.

## 4. Pravidla každé další předávky

Každý úkol obsahuje cíl, vstupní předpoklady, co změnit, co nezměnit, chyby a obnovu, soukromí, automatické testy, manuální testy a podmínku přijetí. Jeden krok nesmí potají implementovat další tři.

Výstup uvádí skutečně změněné soubory, skutečně spuštěné testovací příkazy, jejich výsledky, nová omezení a neprovedené zkoušky. Přidej stručný důvod každé změny návrhového parametru; změna invariantu ochrany dat není běžné ladění.

Před migrační či provozně rizikovou změnou je nutný zachovaný stav a návratový postup. Generátor testů ani automatický agent nesmí sám zrušit FAIL jen proto, aby build vypadal zelený. Důkazy testů patří do samostatného reportu, ne jako nepodložené tvrzení do funkční specifikace.
