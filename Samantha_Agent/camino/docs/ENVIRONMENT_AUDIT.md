# Camino C00 — audit skutečného prostředí

Checkpoint 2026-09-14 23:26 CEST: kanonická projektová paměť, handoff a TVBCP byly
dorovnány po recovery záloze. Starší výroky níže o nezapsané paměti a chybějící
instalaci popisují průběh C00; aktuální instalaci dokládá XCODE_INSTALLATION.md.

**Navazující instalace:** Xcode 26.3 Universal byl po samostatném zadání
nainstalován, první nastavení je dokončené a iPhone SDK 26.2 ověřené příkazem.
Původní blokace B01 chybějícími nástroji je vyřešena; B02 fyzické přejímky trvá.
Aktuální instalační důkaz je v
[XCODE_INSTALLATION.md](XCODE_INSTALLATION.md). Původní měření C00 níže jsou historie.

Datum: 14. září 2026, uzávěrka podkladů 22:01 CEST.
Následné doplnění od Míly: cílový **iPhone 14 Plus, iOS 26.6.1**.
Jde o uživatelem potvrzený údaj; původní místní měření se neopakovala.
Další upřesnění od Míly: domácí server je tentýž Intel MacBook Pro 2020,
macOS 15.7.9, 16 GiB RAM. Vývoj a domácí server jsou dvě role jednoho stroje.
Po tomto upřesnění znovu ověřeny Xcode/SDK, standardní umístění aplikace a volno:
stále pouze CLT, chybí iPhone SDK, Xcode nenalezen, volno 28,7 GiB.
Výchozí specifikace: **v0.4**. Stav: **C00 dokončen v dostupném rozsahu; G0 není splněna.**
Výchozí Git HEAD: `17621bb48781165cb2a9b1e9b8a01a7f70ba98ac`, větev `main`, při zahájení čistá.

## Rozsah a význam výsledků

Přečteny společné a projektové `AGENTS.md`, celá funkční specifikace v0.4,
plán včetně celého C00, akceptační scénáře a existující projektový handoff.
V0.3 a v0.2 nejsou výchozím zadáním. Produktová rozhodnutí U01–U11 zůstávají uzavřená.

- **OVĚŘENO:** konkrétní místní měření nebo výslovně označený údaj z oficiální dokumentace.
- **NEOVĚŘENO:** chybí přístup, měření nebo zkouška. Není to tvrzení, že zařízení či funkce neexistuje.
- **BLOKUJE:** doloženě chybí podmínka konkrétní další činnosti; dopad je uveden zvlášť.

Byly provedeny pouze informační příkazy, čtení veřejných oficiálních podkladů
a vytvoření tří dokumentů C00. Nebyl zahájen build, nahrávání ani placené AI.
Žádné instalace, účty, párování, síťové nastavení, bezpečnostní nastavení nebo osobní data se neměnily.
Povolení zápisů pouze do nových projektových dokumentů má v tomto kroku přednost
před běžným aktualizováním centrální paměti a lokálním commitem: ty neproběhly.
Dosavadní README, handoff a TVBCP proto zachovávají historický stav před C00;
aktuální audit a předání tvoří tyto tři dokumenty. Metadatový semafor byl `free`.

## 1. Tři odlišné role

| Role | Skutečně dostupné prostředí | Stav | Důkaz a dopad |
|---|---|---|---|
| Vývojový Mac | Intel MacBook Pro, `MacBookPro16,3`, macOS 15.7.9 | OVĚŘENO | Přímé `sw_vers`, `uname`, `sysctl`; jde o počítač vykonávající tuto relaci, nikoli Linuxový kontejner vydávaný za Mac. |
| Cílový iPhone | **iPhone 14 Plus, iOS 26.6.1**, následně potvrzeno Mílou | Model/verze potvrzeny uživatelem; fyzická zkouška NEOVĚŘENO | Původní USB inventura nezjistila iPhone/iPad/iPod; Xcode nástroje pro správu zařízení chybějí. Tento výsledek nepopírá Mílův údaj a nedokazuje nedostupnost telefonu jiným způsobem. |
| Domácí Mac server | Tentýž místní Intel MacBook Pro 2020, určený Mílou také jako domácí server | Role POTVRZENA UŽIVATELEM; místní hardware/OS OVĚŘENO | Měření E01–E12 se vztahují na tento stroj v obou rolích. Připravenost serverových služeb Camino tím doložena není; pro C01a nejsou potřeba. |

Apple přiřazuje `MacBookPro16,3` modelu **13palcový MacBook Pro 2020 se dvěma
Thunderbolt 3 porty** a uvádí Sequoiu jako jeho nejnovější podporovaný systém.
Jde o identifikaci modelu z veřejného katalogu, nikoli čtení sériového čísla.
[Apple: identifikace MacBooku Pro](https://support.apple.com/en-us/108052).

## 2. Vývojový Mac — místní důkazy

| ID | Spuštěný příkaz / způsob čtení | Zjištění | Výsledek a dopad |
|---|---|---|---|
| E01 | `sw_vers` | macOS 15.7.9, build `24G830` | OVĚŘENO |
| E02 | `uname -m`; `sysctl -n hw.model`; `sysctl -n machdep.cpu.brand_string` | `x86_64`; `MacBookPro16,3`; Intel Core i5-8257U 1.40 GHz | OVĚŘENO, skutečný Intel; nejde o odhad podle jména workspace. |
| E03 | `sysctl -n hw.memsize` | 17 179 869 184 bajtů = 16 GiB RAM | OVĚŘENO; výkon buildu nezměřen. |
| E04 | Python `shutil.disk_usage('.')` | Svazek workspace celkem 233,5 GiB, volno 28,7 GiB | OVĚŘENO na společném vývojovém/serverovém Macu. Nejde o kapacitu telefonu ani o již vybraný cílový svazek archivu Camino. |
| E05 | `xcode-select -p`; existence proměnné `DEVELOPER_DIR` | Aktivní `/Library/Developer/CommandLineTools`; bez override | OVĚŘENO; nic se nepřepínalo. |
| E06 | `xcodebuild -version` | Exit 1: nástroj vyžaduje Xcode, aktivní jsou pouze CLT | BLOKUJE iOS build. Není to chyba aplikace. |
| E07 | `xcrun --no-cache --sdk iphoneos --show-sdk-version` | Exit 1: iPhone SDK nenalezeno | BLOKUJE sestavení pro telefon v aktuálním prostředí. |
| E08 | `xcrun --no-cache --find simctl`; totéž pro `devicectl` | Oba exit 72, nástroj nenalezen | Simulátor ani Xcode inventura/párování zařízení neprovedeny. |
| E09 | Názvy `Xcode*.app` v `/Applications` a `~/Applications` | Žádná nalezená aplikace | OVĚŘENO v těchto dvou umístěních. Nestandardní instalace jinde se plošně nehledala. |
| E10 | `pkgutil --pkg-info com.apple.pkg.CLTools_Executables` | CLT `26.3.0.0.1.1771626560` | OVĚŘENO; CLT nejsou plný Xcode. |
| E11 | `swift --version`; `clang --version` | Swift 6.2.4, target `x86_64-apple-macosx15.0`; Apple clang 17.0.0 | OVĚŘENO spuštění nástrojů; žádný zdroj nebyl kompilován. |
| E12 | `xcrun --no-cache --sdk macosx --show-sdk-version` | macOS SDK 26.2 | OVĚŘENO; vyšší číslo SDK není změna běžícího macOS a není iOS SDK. |

Pomocný `sysctl -n sysctl.proc_translated` vrátil exit 1 / neznámý klíč.
Nebyl použit jako důkaz Rosetty; Intel je doložen modelem a procesorem E02.

**Kapacita pro instalaci:** 28,7 GiB je skutečné volno, nikoli potvrzení, že
stačí na archiv Xcode, jeho rozbalení, iOS komponenty, build cache a bezpečnou
rezervu systému. Instalační rozpočet zatím **NEOVĚŘENO**. Nic se nečistilo.
Před případnou instalací se má porovnat skutečná velikost vybraného balíčku
a potřebných komponent s novým měřením volného místa. Simulátor lze pro první
zkoušku skutečného telefonu odložit; iPhone SDK vynechat nelze.

## 3. Další dostupné nástroje — pouze na vývojovém Macu

| Nástroj | Místní ověření | Význam pro Camino |
|---|---|---|
| Git | `git --version`: 2.50.1, Apple Git-155 | Zdrojové řízení dostupné; v C00 bez zápisu do Gitu. |
| Python z PATH | `python3 --version`: 3.11.5 | Dostupný interpret, nikoli hotové prostředí domácího serveru. |
| Existující prostředí Samanthy | `.venv/bin/python --version`: 3.12.0rc3 | Existuje, ale pro nový produkční server se nepřebírá release candidate ani cizí závislosti. |
| Node / npm | `node --version`: 24.15.0; `npm --version`: 11.12.1 | Dostupné, pro nativní C01a nejsou potřeba. |
| FFmpeg / FFprobe | `ffmpeg -version`; `ffprobe -version`: 8.1 | Spustitelné; žádná média nebyla zpracována. |
| Homebrew | `shutil.which('brew')` nalezl spustitelnou cestu | Jen existence; verze, aktualizace a instalace neprováděny. |
| Docker, CocoaPods, XcodeGen, libimobiledevice CLI | `shutil.which` nenašel `docker`, `pod`, `xcodegen`, `ideviceinfo` | Pouze nedostupnost v PATH. Nejde o požadavky C01a a nic se nedoinstaluje. |
| Tailscale | Aplikace v `/Applications`, Info.plist verze 1.102.3; zabalené CLI odpovědělo na `status --json` | Lokálně `BackendState=Running`, `Self.OS=macOS`, `Self.Online=true`. Globální příkaz v PATH chybí, aplikace přesto běží. |

Tailscale výstup byl omezen na stav místního klienta. Jména, IP adresy, DNS,
identity účtů a seznam peerů nejsou součástí auditu. Stav místního klienta
nedokazuje dosažitelnost tohoto Macu z jiné sítě, konfiguraci Serve ani Camino API.
Nebylo provedeno zapnutí Serve/Funnel nebo změna tailnetu.

## 4. iPhone — hranice přístupu

Read-only `ioreg -a -r -c IOUSBHostDevice` byl v paměti filtrován na třídu
USB produktu iPhone/iPad/iPod; výsledek **0 zařízení**. Sériová čísla a párovací
záznamy nebyly vypsány ani uloženy. Telefon nebyl párován ani odemykán.

| Co chybí | Stav | Jaký důkaz doplnit v příštím autorizovaném kroku |
|---|---|---|
| Model a verze iOS | POTVRZENO UŽIVATELEM: iPhone 14 Plus, iOS 26.6.1 | Nežádat znovu stejný údaj. Při připojení doplnit technický build iOS a přímý doklad; build zatím NEOVĚŘENO, bez UDID v reportu. |
| Kabelové spojení, důvěra a dostupný run destination | NEOVĚŘENO | Pozdější řízené připojení k vývojovému Xcode; neodvozovat z modelu telefonu. |
| Apple Account, členství, podpis a platnost profilu | NEOVĚŘENO | Pozdější kontrola v určeném účtu; pouze výsledek a expirace, žádná tajemství. |
| Developer Mode | NEOVĚŘENO | Kontrola na telefonu; případné zapnutí je samostatná změna se souhlasem. |
| Volné místo, mikrofon, sluchátka a audio vstup | NEOVĚŘENO | Metadata kapacity a C01a/C01b s výslovně určenou testovací řečí. |
| Build, instalace, spuštění a přehrání Camino | NEPROVEDENO | Skutečný podepsaný prototyp na tomto telefonu. |
| Zámek, hovor, změna vstupu, pád, baterie a terén | NEPROVEDENO | Příslušné fyzické scénáře; nejsou nahrazené unit testy ani zvukem Macu. |

## 5. Oficiální cesta sestavení a instalace

**Dokumentačně doložený kandidát:** Xcode **26.3**, jeho iOS SDK **26.2**,
Swift **6.2.3**, na stávajícím macOS 15.7.9. Apple uvádí pro Xcode 26.3
macOS od 15.6 a on-device debugging od iOS 15. Tyto údaje potvrzují možnost
volby nástrojů, nikoli úspěšné párování cílového iPhonu 14 Plus s iOS 26.6.1.
[Apple: Xcode 26.3 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26_3-release-notes).

Xcode 26.4.1–26.6 v aktuální tabulce vyžadují Tahoe 26.2; Xcode 27 ještě novější
macOS. Pro tento Mac nejsou výchozí volbou. Číslo SDK, minimální deployment
target a verze systému fyzického telefonu jsou tři odlišné věci. Starší SDK
neznamená samo o sobě zákaz běhu na každém novějším iOS; rozhodne skutečný
build/install/run a ověření použitých API.
[Apple: matice Xcode, macOS a SDK](https://developer.apple.com/xcode/system-requirements).

Podrobné rozhodnutí, instalační postup a podmínky platnosti jsou v
[DECISIONS.md](DECISIONS.md). **Legitimní cesta je navržena; instalace platná
po celou konkrétní cestu zatím není doložena.** Neznáme skutečné podpisové
artefakty ani termín návratu a nelze z nich vypočíst rezervu.

## 6. Domácí Mac server — role upřesněna, služby Camino nepřejaty

V původním C00 nebylo doloženo, který počítač tuto roli převezme. Míla následně
výslovně určil tento místní MacBook; nešlo tedy o nutnost hledat jiný server.
Dosavadní místní inventura platí pro stejný hardware v obou rolích. Zůstává
oddělené ověření úložiště, zálohy a provozní připravenosti služeb Camino.
Žádný název ani adresa služby se nevymýšlí. Nečetly se SSH klíče ani hesla.

| Oblast | Stav | Chybějící nedestruktivní audit / pozdější provozní test |
|---|---|---|
| Identita, OS, CPU, RAM, architektura | OVĚŘENO; role potvrzena Mílou | Tentýž stroj, viz E01–E03; není třeba opakovat měření na domnělém druhém počítači. |
| Python a FFmpeg | Místní verze OVĚŘENO, prostředí Camino NEOVĚŘENO | Viz tabulka nástrojů; izolované serverové závislosti Camino dosud nejsou připravené. |
| Cílové úložiště, kapacita a oprávnění | NEOVĚŘENO | Metadata určeného svazku, volno a read-only přehled oprávnění; skutečný test zápisu až zvlášť se syntetickým souborem. |
| Nezávislá záloha a její identita | NEOVĚŘENO | Redigovaná metadata existujícího zálohovacího cíle a doklad poslední obnovy. Druhá složka téhož disku nestačí. |
| Tailscale, Serve, HTTPS, síťová pravidla | Místní klient OVĚŘENO; Camino HTTPS a pravidla NEOVĚŘENO | Klient 1.102.3 při auditu Running/Online; zbývá oddělený audit konfigurace, bez automatického zřizování. |
| Napájení, uspávání, FileVault a spravovaný start | NEOVĚŘENO | Nejprve read-only konfigurace a existující provozní doklady. Samotná nastavení nepotvrzují úspěch po restartu. |
| Restart, spánek/probuzení, odemknutí a jiná síť | NEPROVEDENO | Skutečný řízený provozní test až po samostatném oprávnění a zajištění dostupnosti obsluhy; v C00 se server nerestartuje ani neuspává. |
| Přenos a obnova celého dne | NEPROVEDENO | C02/C05/C06: syntetické soubory, hash potvrzení, nezávislá kopie a skutečná obnova. |

Preferované soukromé HTTPS přes Serve a API na localhostu odpovídá v0.4.
Dokumentace Serve popisuje přístup uvnitř tailnetu a uplatnění přístupových
pravidel; není to důkaz existující konfigurace.
[Tailscale: Serve](https://tailscale.com/docs/features/tailscale-serve).

## 7. Skutečné překážky a možnost pokračovat bez serveru

| Překážka | Dopad teď | Dopad na pozdější vydání |
|---|---|---|
| B01: aktivní prostředí bez plného Xcode a iPhone SDK | BLOKUJE iOS build a instalaci C01a | Nutné zprovoznit kompatibilní nástroje samostatně. |
| B02: neprovedené párování, instalace a ověření podpisu na iPhonu 14 Plus / iOS 26.6.1 | BLOKUJE fyzické přijetí C01a; model a verze už nejsou chybějící údaj | T079 a G0 zůstávají nesplněné. |
| B03: stroj již určen, chybí ověření serverových služeb, úložiště a zálohy Camino | **Neblokuje offline C01a** | Příslušné serverové, přenosové a provozní brány zůstávají nesplněné. |
| R01: 28,7 GiB volného místa | Riziko instalace; nedostatek nebyl prokázán výpočtem konkrétního balíčku | Vyžaduje nový kapacitní rozpočet před instalací. |
| R02: platnost profilu a offline ověřování podpisu | Neomezuje sepsání ani mock logiku | Blokuje prohlášení připravenosti na pouť, dokud není doložena platnost a fyzické zkoušky. |

Po novém zadání lze bez serveru a bez telefonu připravit čistou Swift logiku
prototypu a mock testy. Swift nástroj je dostupný, ale samotný build takového
balíčku v C00 **neproběhl**. Nativní UI, mikrofon a přejímka čekají na B01/B02.
Není důvod stavět dočasnou webovou náhradu nebo instalovat server kvůli C01a.

## 8. Uzavření C00

- Provedené kontroly: informační příkazy E01–E12, verze nástrojů, omezená USB
  inventura, redigovaný stav místního Tailscale, čtení oficiálních podkladů.
- Integrita původního balíčku: **15/15 SHA-256 shod podle původního manifestu**.
- Kontrola výstupů: tři nové UTF-8 dokumenty, funkční místní odkazy a kontrola
  whitespace; všechny dříve existující projektové soubory shodné s auditním
  snapshotem. Git nehlásí změnu žádného sledovaného souboru; HEAD beze změny.
- Build a automatické testy aplikace: **NEPROVEDENO**, aplikace zatím nevznikla.
- T015/T017/T025 a T079: **NEPROVEDENO**; fyzická část blokovaná B01/B02.
- G0: **BLOKUJE / částečné podklady**, nikoli PASS. Ostatní G1–G7 nepřejímány.
- Jediné nové soubory: tento audit, `docs/DECISIONS.md`, `tasks/C01a_AUDIO_PROTOTYPE.md`.
- Jediný následující krok: **samostatně zadat přípravu a ověření vývojové cesty
  Xcode 26.3 → iPhone 14 Plus / iOS 26.6.1**, včetně kapacity, párování a podpisu.
  Instalace či změna Developer Mode vyžadují nové konkrétní oprávnění.
  C01a je připravené zadání, ne spuštěná práce.

## Navazující požadavek — instalace Xcode, 14. září 2026

Po C00 Míla výslovně zadal ověření místa a následnou instalaci Xcode 26.3.
Instalace je tedy autorizovaná; není nutné znovu žádat tentýž souhlas.
Implementace C01a, změny telefonu a placené členství tím zadány nejsou.

- Nové měření: na svazku `/Applications` přibližně 28,7 GiB volných.
- Xcode nebyl nalezen v systémových ani uživatelských Applications ani
  Spotlight dotazem na bundle ID `com.apple.dt.Xcode`.
- Ve standardní složce Downloads není archiv začínající názvem Xcode.
- Oficiální požadavek HEAD na Apple archiv `Xcode_26.3.xip` vrátil HTTP 302
  na stránku `developer.apple.com/unauthorized/`, bez velikosti vlastního archivu.
- Oficiální katalog stažení přesměroval na přihlášení Apple Account.
  Dostupné ovládání počítače hlásí nulový počet prohlížečů a aplikací; není
  možné zde provést přihlášení přes uživatelské rozhraní. Přihlašovací údaje,
  cookies nebo klíče nebyly čteny ani kopírovány.
- **BLOKUJE: přístup k oficiálnímu instalačnímu archivu.** Kapacitní rozpočet
  archivu + rozbalené aplikace + komponent a rezervy zůstává NEOVĚŘENO;
  samotných 28,7 GiB není důkaz, že místa je dost nebo málo.
- Nic nebylo staženo, nainstalováno ani smazáno. C01a zůstává nezahájené.

Potřebný uživatelský úkon: přihlásit se do
[Apple Developer Downloads](https://developer.apple.com/download/all/?q=Xcode%2026.3)
a stáhnout oficiální archiv Xcode 26.3 do Downloads. Apple uvádí, že přístup
ke starším nástrojům vyžaduje účet, nikoli placené členství:
[Xcode Resources](https://developer.apple.com/xcode/resources/).
Po zpřístupnění archivu navázat již schválenou kontrolou kapacity, podpisu
a instalací; nepřeskakovat ověření volného prostoru před rozbalením.
