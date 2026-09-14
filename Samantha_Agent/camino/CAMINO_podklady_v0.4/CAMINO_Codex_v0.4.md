# Camino — předání a postupná zadání pro Codex v0.4

**Aktuální funkční zdroj:** `CAMINO_funkcni_specifikace_v0.4.md`  
**Akceptace:** `CAMINO_akceptacni_testy_v0.4.md`  
**Stav:** zadání, nikoli implementace. V tomto balíčku se neprovedl build, párování ani test telefonu.

## 1. Způsob práce

Pracuj vždy na jednom zadaném kroku. Nepřeváděj dlouhou specifikaci na pokyn vyrobit celou aplikaci najednou. Zachovej pravidla U01–U11 a funkční význam F01–F73. Návrhové hodnoty D a technické parametry lze změnit na základě důkazu, s krátkým ADR; nevracej technický výběr uživateli jako dotazník.

Před začátkem si přečti `AGENTS.md`, hlavní specifikaci a konkrétní úkol. Soubor AGENTS je krátké projektové vedení; úplná specifikace zůstává zvlášť. Používání `AGENTS.md` dokumentuje OpenAI: `https://developers.openai.com/codex/guides/agents-md/`.

Testovací data jsou syntetická. Všechny běžné testy mají mock AI. Neodesílej skutečné audio poskytovateli ani nekupuj členství bez samostatného provozního kroku. Souhlas s AI obsahem není schválená částka.

Hardware, k němuž nemáš přístup, označ NEOVĚŘENO. Nespouštěj linuxový audit a nepopisuj jeho výsledek jako stav Mílova Macu. Nedokládej zkoušku zámku, Bluetooth nebo hovoru úspěšným unit testem. Audit nesmí bez dovolení změnit bezpečnostní nastavení, veřejnou síť, účty ani data.

## 2. Etapy a malé části

Pořadí C00–C11 zachovává v0.3. Uvnitř etapy jde o několik samostatných předávek, nikoli jeden obří commit.

| Úkol | Konkrétní výsledek | Hlavní vazba na testy | Co v tomto kroku ještě nedělat |
|---|---|---|---|
| C00 | Read-only audit vývojového Macu, iPhonu, instalace a odděleně domácího serveru. | Podklady pro T079, G0 | Žádné nákupy, migrace ani plná aplikace. |
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
| C06a | Spravovaný start serveru, autorizační režim, soukromý web a stav. | T003,T048,T078 | Bez úprav soukromí/obsahu přes web v P0. |
| C06b | Snapshot záloh, identita cíle, hash doklady a skutečná obnova. | T054–T058,T064 | Kopie do jiné složky stejného disku nestačí. |
| C06c | Zabezpečený restart, logy bez obsahu, upgrade/migrace/rollback. | T059,T078,T079 | Žádné plošné vypnutí FileVault nebo ochrany dat. |
| C07a | Trvalý worker, mock adaptéry, cache klíče, náklady a chybové stavy. | T065,T066,T069 | Žádná skutečná placená volání. |
| C07b | Česká sada přepisu a jemné korektury; skutečný pilot až po nastavení limitu. | T042,T067,T068,T071 | Bez automatické transkripce všeho ve videích. |
| C07c | Ochrana lidských revizí, zdrojová provenience a data jako inertní text. | T010,T038,T055,T069 | Bez nástrojových oprávnění jazykového modelu. |
| C08a | Denní šablona, místní cache a statické HTML/Markdown archivy. | T026,T040,T064,T071 | Nepopisovat z fotek neznámé události. |
| C08b | Dávkové souhrny, maximální čekání, neaktuální výsledky a pozdní vstupy. | T027–T030,T038,T057,T070 | Bez tlačítka Uzavřít den a bez povinného schvalování. |
| C09 | Reálný den, vyhodnocení chyb, kapacity, instalace a zmrazení vydávaného rozsahu. | Celé relevantní P0, zejména T079,T080 | Nezakrýt kritický FAIL grafickým vylepšením. |
| C10a | Povolený seznam zdrojů a nezávislý výběrový text. | T072,T074 | Nikdy nepoužít celý osobní souhrn. |
| C10b | Očištěné kopie fotografií, náhled, finální kontrola a systémové sdílení. | T073–T076 | Žádné autonomní odesílání nebo tvrzení doručení. |
| C11a | Ověřený import skutečného exportu hodinek. | T077, F67 | Žádná domyšlená stopa mezi foto body. |
| C11b | Výběr a verzovaná časová osa s vlastním zvukem, titulky a kontrolou soukromí. | T077, F68,F69 | Bez klonování hlasu, soukromých vstupů a vymyšlených záběrů. |
| C11c | Normalizace pracovních kopií, render, kontrola a export filmu. | T012,T077, F70 | Originály neproměňovat nevratnou kompresí. |

Testy T019–T021 u klientské integrace se znovu provedou po změnách zvukových funkcí, nejen jednou v izolovaném prototypu. Prototyp neprokazuje, že pozdější galerie či přehrávač nic nerozbily.

## 3. První zadání připravené k vložení do Codexu — C00

### Cíl

Prostuduj v0.4 a vytvoř doložený read-only audit, z něhož půjde vybrat funkční cestu k nativní iPhone aplikaci a soukromému Mac serveru. Zatím neimplementuj celou aplikaci a neměň uživatelův systém.

### Vstupy

`AGENTS.md`, `CAMINO_funkcni_specifikace_v0.4.md`, `CAMINO_akceptacni_testy_v0.4.md`, tento plán. Starší v0.3 slouží jen jako historie. Známe kontext iPhonu 14 a dříve zmiňovaného Intel MacBooku; aktuální systémy a domácí server nejsou doložené touto specifikací.

### Povolené činnosti

Zjisti, v jakém skutečném prostředí běžíš. Na dostupném Macu lze použít read-only příkazy jako `sw_vers`, `uname -m`, `xcodebuild -version` a `xcrun --sdk iphoneos --show-sdk-version`. Nejsi-li na Macu, označ místní prostředí správně a stav Mílova zařízení NEOVĚŘENO. Nedostupné zařízení nenahrazuj odhadem.

Z oficiálních aktuálních podkladů ověř kompatibilitu nástrojů, dostupných systémů a cílového telefonu. Zvol nejjednodušší legitimní instalaci s platností přes cestu a rezervu; nepředpokládej, že je povinný App Store, TestFlight nebo nejnovější macOS. Přijatelnost případného členství byla potvrzena, nákup nebyl zadán.

Pokud je skutečně autorizovaný přístup na domácí Mac, zjisti jeho roli, systém, cílové úložiště, dostupnou zálohu, stávající Tailscale a chování po restartu/uspání. Bez přístupu pouze zapiš, jaký nedestruktivní test chybí. Nezakládej smyšlenou adresu serveru a nevyžaduj od uživatele výběr API frameworku.

### Zakázané činnosti

Žádná aktualizace systému, instalace velkých nástrojů, platba, změna účtů, otevření veřejných portů, Funnel, změna FileVault, mazání souborů nebo přesun osobních dat. Žádné reálné API klíče ani uživatelské audio do testů. Neoznačuj auditní čtení tabulky kompatibility za úspěšný test iPhonu.

### Předávka

Vytvoř `docs/ENVIRONMENT_AUDIT.md` s rolemi vývojový Mac / iPhone / domácí Mac, stavem OVĚŘENO / NEOVĚŘENO / BLOKUJE, důkazem a dopadem. Nepiš sériová čísla, tokeny nebo podrobný soukromý síťový profil do výstupu.

Do `docs/DECISIONS.md` navrhni cestu nástrojů a instalace. Do `tasks/C01a_AUDIO_PROTOTYPE.md` připrav malý další úkol se Start/Stop, skutečným vstupem a lokálním přehráním, v rozsahu zjištěného prostředí. Při chybějícím telefonu odděl automatizovatelnou přípravu od neprovedených manuálních testů.

Uživateli shrň, co je doložené, co chybí a jaký jediný následující malý krok navazuje. Nevracej produktový dotazník U01–U11.

## 4. Pravidla každé další předávky

Každý úkol obsahuje cíl, vstupní předpoklady, co změnit, co nezměnit, chyby a obnovu, soukromí, automatické testy, manuální testy a podmínku přijetí. Jeden krok nesmí potají implementovat další tři.

Výstup uvádí skutečně změněné soubory, skutečně spuštěné testovací příkazy, jejich výsledky, nová omezení a neprovedené zkoušky. Přidej stručný důvod každé změny návrhového parametru; změna invariantu ochrany dat není běžné ladění.

Před migrační či provozně rizikovou změnou je nutný zachovaný stav a návratový postup. Generátor testů ani automatický agent nesmí sám zrušit FAIL jen proto, aby build vypadal zelený. Důkazy testů patří do samostatného reportu, ne jako nepodložené tvrzení do funkční specifikace.
