# Camino — rozhodnutí z auditu C00

Aktualizace 2026-09-15 08:19 CEST: C01a ověřilo spárovaný iPhone, zapnutý Developer Mode
a DDI. Skutečný Xcode build však blokuje platform support iOS 26.2 navzdory
přítomnému SDK. [Aktuální důkaz a rozsah](C01a_AUDIO_PROTOTYPE_REPORT.md).

Checkpoint 2026-09-14 23:26 CEST: kanonická projektová paměť, handoff a TVBCP byly
dorovnány po recovery záloze. Starší výroky níže o nezapsané paměti a chybějící
instalaci popisují průběh C00; aktuální instalaci dokládá XCODE_INSTALLATION.md.

Navazující provedení: [instalační doklad Xcode 26.3](XCODE_INSTALLATION.md).
Aplikace je již nainstalovaná, první nastavení dokončené a iPhone SDK 26.2 dostupné;
níže uvedené návrhy C00 se nesmějí zaměnit za aktuální instalační stav.

Datum původního auditu: 14. září 2026. Aktuální autorita produktu: v0.5 se
závazným dodatkem U15 v `V05_PRIVACY_AMENDMENT.md`.
Místní důkazy a limity: [ENVIRONMENT_AUDIT.md](ENVIRONMENT_AUDIT.md).
Tento dokument obsahuje technické návrhy, nikoli souhlas s instalací,
nákupem, změnou účtů nebo zahájením další etapy.

## ADR-C00-01 — nástroje na skutečném vývojovém Macu

**Návrh:** zachovat současný macOS a použít Xcode 26.3 s dodávaným iOS SDK
26.2. Doložená systémová kompatibilita je v auditu, skutečný build dosud ne.
Nepřebírat Swift z CLT jako verzi budoucího Xcode: jde o odlišné toolchainy.

Starší Xcode je dostupný přes oficiální Apple Developer Downloads po přihlášení
k Apple Account; samotné stahování podle Apple nevyžaduje placené členství.
Stažení konkrétního archivu v této relaci **NEPROVEDENO**.
[Apple: Xcode Resources](https://developer.apple.com/xcode/resources/).

Na tomto Intel Macu nepoužívat Xcode 27: jeho release notes uvádějí běh jen
na Apple silicon. Nákup jiného Macu z C00 nevyplývá; nejprve ověřit vhodnost
starší kompatibilní sady pro konkrétní iOS.
[Apple: Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

Pro první fyzickou zkoušku stačí nezbytné iOS komponenty. Simulátor je volitelný;
pokud později bude potřeba na Intelu, vybrat kompatibilní univerzální runtime,
nikoli automaticky variantu pouze pro arm64.
[Apple: dodatečné komponenty Xcode](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components).

**Podmínky realizace:** nové oprávnění k instalaci, přepočet místa pro archiv,
rozbalenou aplikaci, komponenty a cache, ověření staženého Apple balíčku.
Žádné mazání pro uvolnění místa, neoficiální patchování macOS nebo vypnutí
ochran. Pokud je nutné volit toolchain pro jednotlivý příkaz, preferovat
procesový `DEVELOPER_DIR` před nevyžádanou globální změnou `xcode-select`.
První spuštění a případné licenční/komponentové kroky nejsou součástí auditu.

Míla po auditu potvrdil cílový **iPhone 14 Plus s iOS 26.6.1**. Tento údaj
je vstupem návrhu, nikoli důkazem úspěšné instalace. Xcode 26.3 zůstává
kandidátem k přímému ověření build/install/run na tomto telefonu; shoda
čísel SDK a iOS se nevyžaduje pouze pro jejich číselnou shodu. Minimální
deployment target zafixovat podle potřebných API, nikoli automaticky na 26.6.1.
Nežádat znovu model a verzi; při připojení doplnit technický build systému.

## ADR-C00-02 — krátký prototyp a instalace na pouť mají jiné podmínky

| Cesta | Zjištěná vlastnost | Rozhodnutí |
|---|---|---|
| Xcode → vlastní telefon, Personal Team | Bez členství lze místně testovat; provisioning vyprší po 7 dnech. | Vhodný kandidát pro krátké C01a, pokud není již vhodné členství. Není výchozí dlouhodobá instalace na pouť. [Apple: Personal Team](https://developer.apple.com/help/account/basics/about-your-developer-account). |
| Apple Developer Program → Ad Hoc → registrovaný vlastní iPhone | Distribuce podepsané aplikace na určené zařízení bez veřejného App Store; vyžaduje App ID, distribuční certifikát a profil. | **Preferovaný kandidát pro soukromé P0**, podmíněný skutečnou expirací a offline zkouškami níže. [Apple: Ad Hoc](https://developer.apple.com/help/account/provisioning-profiles/create-an-ad-hoc-provisioning-profile). |
| TestFlight | Build je použitelný nejvýše 90 dnů a prochází App Store Connect. | Záložní možnost, není povinná ani bezčasová. Nepřidává se kvůli jednomu telefonu automaticky. [Apple: TestFlight](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/). |

U10 již připouští roční poplatek. Tento souhlas není nákup; členství uživatele
ani jeho expirace nebyly čteny. Žádný účet se nezakládal, nic se neplatilo.
Cena se zde neodhaduje a rozpočet AI U11 není pro offline prototyp potřeba.

### Pozdější konkrétní instalační postup — zatím nespouštět

1. Ověřit nainstalovaný Xcode, iPhone SDK a skutečný model/verzi iOS; zaznamenat
   přesné verze. Připojit vlastní telefon datovým kabelem a ověřit důvěru.
2. Ve správném Apple týmu nastavit jednoznačné bundle ID a signing. Pro krátký
   prototyp lze použít Personal Team; neexportovat identitu účtu nebo klíče do Git.
3. Je-li potřeba Developer Mode, uživatel jej zapne na telefonu a potvrdí
   restart/aktivaci. Jde o výslovnou bezpečnostní změnu mimo C00.
   [Apple: Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device).
4. V C01a zvolit skutečný telefon jako run destination, sestavit, nainstalovat
   a vědomě spustit prototyp. Uchovat redigovaný build/install/run výsledek.
5. Pro pozdější P0 vytvořit Archive a export pro registrované zařízení
   (Ad Hoc / odpovídající volba exportu dané verze Xcode). Soukromě uchovat IPA,
   vazbu na commit a podpisové metadata. Instalovat místně přes Xcode nebo
   Apple Configurator; veřejný instalační web není potřeba.
   [Apple: distribuce na registrovaná zařízení](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).
6. Před odjezdem splnit samostatnou bránu platnosti a upgradu níže. Samotné
   vytvoření IPA, členství nebo zelený build tuto bránu neuzavírá.

### Platnost instalace a offline režim — skutečná provozní podmínka

Nelze nyní slíbit „vydrží rok“. Rozhoduje konkrétní vydaný profil, certifikát,
stav členství a pravidla autorizace aplikace na telefonu. Do provozního
reportu později patří **pouze expirace a výsledek ověření**, nikoli klíče,
celé profily nebo UDID. Při obnovení profilu může být nutné nové podepsání
a instalace; zachování dat musí prokázat T079.
[Apple: obnova provisioning profilu](https://developer.apple.com/help/account/provisioning-profiles/edit-download-or-delete-profiles).

Pro týmy vytvořené po 6. 6. 2021 Apple popisuje ověření vývojově a Ad Hoc
podepsané aplikace službou PPQ při prvním spuštění s internetem. Zvláštní
offline profil má jen sedmidenní platnost; Apple samostatně řeší potřebu běhu
bez připojení déle než 30 dnů po prvním spuštění. **Ad Hoc tedy není automatický
důkaz neomezeného offline spuštění.** Před cestou je nutné potvrdit pravidla
pro skutečný tým a artefakt, ne zaměnit platnost certifikátu za offline garanci.
[Apple: provisioning a PPQ](https://developer.apple.com/help/account/provisioning-profiles/provisioning-profile-updates).

Projektová brána, nikoli tvrzení Apple:

- Návrh rezervy je **14 kalendářních dnů po plánovaném návratu**. Jde o nový
  technický návrh pro C09, ne odhad termínu nebo délky cesty. Při plánování vydání
  může být upraven záznamem důvodu; povinná rezerva z F71 nesmí zmizet.
- Nejbližší relevantní konec platnosti profilu/certifikátu/členství musí přesahovat
  návrat i rezervu. Termíny zatím nejsou doloženy: výsledek **NEOVĚŘENO**.
- Ověřit první autorizované spuštění online, potom opakované spuštění a lokální
  záznam bez sítě, včetně skutečného restartu a odemknutí telefonu. Plán zkoušek
  musí odpovídat zamýšlenému nejdelšímu offline intervalu, nejen minutovému testu.
- Ověřit instalaci upgradu se stejnou identitou aplikace, zachování testovacích
  souborů a návrat po neúspěšném upgradu. Kvůli podpisu aplikaci neodinstalovávat
  bez ověřené kopie. Neměnit systémové hodiny kvůli simulaci expirace.
- Nesplnění znamená **BLOKUJE připravenost na pouť**, nikoli důvod předstírat PASS
  nebo ihned kupovat nový hardware. Distribuční cestu lze znovu technicky posoudit
  podle doložené překážky; produktová rozhodnutí se tím neotevírají.

## ADR-C00-03 — audio nejprve samostatně, bez serveru

**Návrh:** nativní Swift/SwiftUI, AVFoundation/AVFAudio, žádné externí balíčky.
Pro nejmenší C01a použít izolovaný adaptér `AVAudioRecorder` a lokální
`AVAudioPlayer`. Recorder poskytuje zápis souboru a měření úrovně; skutečný
vstup číst z aktivní audio session. Prototyp tím neprokazuje kontinuitu segmentů.
[Apple: AVAudioRecorder](https://developer.apple.com/documentation/avfaudio/avaudiorecorder),
[Apple: aktuální audio route](https://developer.apple.com/documentation/avfaudio/avaudiosession/currentroute).

Pracovní formát krátkého experimentu: nekomprimované PCM v CAF, mono, cílově
48 kHz / 16 bitů. Skutečný formát se zaznamená a ověří dekódováním; není to
nezměnitelný P0 formát ani slib všech vstupů. Bezeztrátový krátký vzorek
zjednoduší poslech a kontrolu. Dlouhá audia, kodek a bezešvé části se rozhodnou
měřením v C01c; adaptér lze nahradit například AVAudioEngine bez změny významu
uživatelských stavů. **Nedělat segmentaci opakovaným Stop/Start recorderu.**

Veškerá logika stavu se oddělí od iOS adaptérů, aby šly chybové větve ověřit
bez mikrofonu. V C01a žádné Core Data schéma celého produktu, API, upload,
Tailscale, AI, galerie nebo rodinné výstupy. Jednoduchá prototypová evidence
souboru není finální datový kontrakt C03. Podrobnosti a brána přijetí jsou v
[C01a_AUDIO_PROTOTYPE.md](../tasks/C01a_AUDIO_PROTOTYPE.md).

## ADR-C00-04 — jeden Mac, dvě odlišné role

Míla po C00 potvrdil, že domácí server je tentýž místní Intel MacBook Pro 2020,
macOS 15.7.9, 16 GiB RAM. Není vyžadován druhý Mac; vývoj a domácí server
zůstávají odlišné role s vlastními provozními podmínkami.

Preferovaný návrh v0.4 Swift/SwiftUI/Core Data → soukromé HTTPS →
Python/FastAPI/SQLite a soubory se nemění. Verze serverových závislostí se
zafixují v samostatném prostředí Camino na tomto stroji. Cizí prostředí Samanthy
se nekopíruje; jeho Python 3.12.0rc3 není nová produkční volba pro Camino.

Nepřipravené serverové služby Camino nebrání offline prototypu. Neprohlašovat
místní Tailscale za hotové soukromé HTTPS ani dostupný disk za nezávislou zálohu.
Instalace Xcode i budoucí vývoj spotřebovávají kapacitu stejného Macu; rezervu
proto posuzovat společně s jeho dosavadním provozem. Postup doplnění serverových
důkazů je v auditu. C02 a další serverové úkoly se tím nespouštějí.

## Předání

C00 provedl jen audit a vytvoření tří dokumentů. Nic výše není provedená
instalace nebo hotová funkce aplikace. Jediný další krok je samostatně zadaná
příprava a ověření cesty **Xcode 26.3 → cílový iPhone**. C01a se automaticky
nespouští. Centrální paměť, historické podklady, Git HEAD a index zůstaly beze změny;
ve workspace přibyly pouze tři dosud necommitnuté dokumenty C00.

## ADR-V05-01 — celý deník pro Janu, Úvaha bezpečně soukromá

**Rozhodnutí Míly 16. září 2026:** `Jen pro mě` zůstává vlastníkovi. Celý obsah
`Do deníku` může po synchronizaci vstoupit do soukromého read-only Camino
Vieweru pro Janu. Nová samostatná `Úvaha` vždy začíná jako `Jen pro mě`; do
deníku se převede pouze vědomou akcí `Vložit do deníku`.

Toto rozhodnutí má přednost před rozpornými staršími větami v importované v0.5,
ale původní balíček se kvůli ověřitelnosti manifestu nemění. Přesný význam,
hranice odvolání a dopad na C03/C04/C08 stanoví
[V05_PRIVACY_AMENDMENT.md](V05_PRIVACY_AMENDMENT.md).

Současný C01b prototyp zkoumá bezpečný audio základ a nemá finální Moment ani
politiku Vieweru. Přidání do jeho provizorních JSON účtenek by nevytvořilo
správnou produktovou ochranu a zbytečně by zneplatnilo rozběhnuté fyzické testy.
Implementace doménového pravidla proto patří do C03a/C04a/C04d; samotný Viewer
do C08c–C08f. Do té doby žádné současné testovací audio není sdílené.

## ADR-C02A-01 — izolovaný loopback přijímač před produkčním serverem

**Rozhodnutí:** První C02a důkaz odděluje bezpečné přijetí a serverový hash od
produkční serverové architektury. Malý proces používá standardní knihovnu
Pythonu, naslouchá výhradně na loopback IP a přijímá pouze explicitně označená
syntetická data. Tailscale Serve má v pozdějším autorizovaném smoke ukončit
soukromé HTTPS; proces se sám nevystavuje do sítě.

Sdílené prostředí Samanthy FastAPI neobsahuje. Přidat jej jen kvůli tomuto
experimentu by smíchalo závislosti dvou provozních rolí, proti ADR-C00-04.
Produkční cíl F51 proto zůstává Python/FastAPI v samostatném prostředí Camina;
C02a standard-library server není rozhodnutí opustit FastAPI.

Přijímač streamuje do soukromého stagingu, sám počítá velikost a SHA-256 a
konečný objekt i účtenku vytváří create-only. Shodný retry je idempotentní;
jiné bajty pod stejným ID jsou konflikt. Klientský název se nepoužije jako
serverová cesta. Token, obsah ani cesty se nelogují.

Tento krok neimplementuje chunkování, URLSession, SQLite, produkční párování ani
obnovu po síťovém přerušení. Samotné lokální testy nebyly důkazem soukromého
HTTPS; samostatný autorizovaný smoke 2026-09-17 tuto síťovou vrstvu doložil a
po testu přesně obnovil původní Serve konfiguraci. Ani společně tyto důkazy
nejsou T043/T048/T051 nebo vzdálený klientský test; hranice zůstávají viditelné
v reportu C02a.

## ADR-C02B-01 — serverová pravda před background klientem

**Rozhodnutí:** První checkpoint C02b nejdřív zafixuje obnovitelný kontrakt
částí a čistou klientskou reconciliaci. Skutečné souborové úlohy `URLSession`,
trvalá iOS fronta a fyzické síťové scénáře navážou až na testovaný kontrakt.

Výchozí část má 8 MiB. Server potvrzuje jen bezpečně zapsané části, vrací jejich
skutečný seznam a konečný stav vydá až po vlastním ověření sestaveného souboru.
Lokálních 100 % bytů není serverová účtenka. Po relaunchi nebo ztracené odpovědi
se klient znovu dotáže; bez dosažitelné soukromé sítě čeká a nepoužije Funnel
ani jiný veřejný endpoint.

Čistý Swift model není vydáván za hotový iOS přenos. T043 a T047–T050 zůstávají
otevřené do fyzického testu skutečného klienta.

## ADR-C02B-02 — oddělený souborový iOS harness bez osobních médií

**Rozhodnutí:** Druhý checkpoint používá samostatnou aplikaci a bundle ID.
Vytváří jedině syntetickou 96MiB dávku, nemá oprávnění k Fotkám či mikrofonu a
nesdílí kontejner s Camino Audio. Tím lze fyzicky měřit přenos bez dotyku
ostrých médií.

Upload jedné části je `URLSession` background task z připraveného souboru.
Stabilní identifikátor session dovolí po relaunchi převzít systémové události;
trvalý journal se přesto vždy porovná se serverem. Uživatelský force quit se
neinterpretuje jako příslib pokračování: Apple uvádí, že zruší background
přenosy a aplikaci kvůli nim automaticky znovu nespustí. [Apple: background
configuration](https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background%28withidentifier%3A%29),
[Apple: background transfers](https://developer.apple.com/documentation/foundation/downloading-files-in-the-background).

Jeden zdroj se neduplikuje celý. Současně jsou připravené nejvýše dvě 8MiB
části a serverový snapshot musí přesně odpovídat manifestu. Token patří do
Keychain, URL musí být HTTPS a žádný veřejný alternativní endpoint neexistuje.
Síťová, dokončovací a uživatelská žádost o reconciliaci se koaleskují: impuls,
který přijde během právě čekajícího průchodu, vyvolá ještě jeden průchod místo
tichého zahození. Dostupná povolená Wi-Fi smí spustit automatický přenos;
`Synchronizovat nyní` je ruční provozní záloha. Simulátor ani arm64 build samy
nejsou fyzický PASS T043/T047–T050.

T047 používá nový prázdný soukromý receiver oddělený od zachovaného důkazu
T043. Zámek a force quit jsou dvě různé dávky. Read-only audit počítá relace,
stav poslední relace a hashově ověřené serverové části, takže po force quit lze
nejdřív doložit skutečný mezistav a až potom ručně spustit klientskou
reconciliaci.
