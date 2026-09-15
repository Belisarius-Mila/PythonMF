<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

Aktualizováno: 2026-09-15 13:37 CEST

- C01a rozpracováno: izolovaný audio prototyp, 25 testů logiky a syntetického CAF audia OK; přímá kompilace/linkování pro arm64 iOS 17 / SDK 26.2 prošly.
- iPhone 14 Plus / iOS 26.6.1 build 23G83 přímo ověřen: paired, wired, tunnel connected, Developer Mode enabled, DDI available.
- Xcode 26.3: 2026-09-15 ve 13:34 CEST na výslovný pokyn zahájeno stahování iOS 26.2 + iOS 26.3.1 Simulator. Xcode uvádí 10,47 GB; průběh potvrzen na 185 MB (2 %). Dokončení instalace a nový build zatím neověřeny. Při poslední kontrole bylo 0 platných podpisových identit.
- Celý C01a BLOCKED: instalace, ruční UI/poslech a fyzické T015/T017/T025 NEPROVEDENO. C01b nezahájeno.

### Vzkaz pro pokračování

- Restart a následný schválený úklid dokončeny. Před zahájením instalace bylo na SSD 85,79 GiB volných. Dřívější přesun USA neopakovat.
- Stahování běží v Xcode; další instanci nespouštět. Po dokončení stahování ověřit instalaci iOS Platform Support v Xcode Components a zopakovat nepodepsaný build C01a. Potom dořešit signing, instalaci na iPhone a fyzickou přejímku T015/T017/T025.
- Předchozí push a nasazení se týkaly `e4e667b5`; tento zápis je místní.

### Rizika

- Bez funkčního Xcode buildu, podpisu a fyzické přejímky nelze prototyp označit za přijatý; G0/G1 nesplněné.
- Pouze krátké foreground audio; žádná segmentace, záchrana po pádu během zápisu ani pokračování pod zámkem.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Stahování ještě není důkaz dokončené instalace ani funkčního buildu; po instalaci znovu ověřit volné místo. U01–U11 se neotevírají.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Camino

Nazev: Camino
Pracovni proud: project-camino
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-09-15 13:37 CEST

Co se resilo:
První implementace C01a a ověření připravenosti telefonu; skutečný Xcode build odhalil další blokaci.

Co je hotove:
Kód C01a, 25 automatických testů a přímá iOS kompilace; párování, Developer Mode a DDI ověřeny.

Co neni hotove:
Platform support, Xcode build aplikace, signing, instalace a hardwarová přejímka. C01a BLOCKED, G0/G1 nesplněné.

Dalsi krok:
Po dokončení stahování ověřit instalaci iOS Platform Support v Xcode Components a zopakovat nepodepsaný build C01a. Potom dořešit signing, instalaci na iPhone a fyzickou přejímku T015/T017/T025.

Navrhovane dalsi kroky:
Po vyřešení kapacity a doplnění iOS Platform Support dokončit Xcode build, podpis a fyzickou přejímku existujícího C01a prototypu.

Zmenene nebo relevantni soubory:
`camino/`, `memory/projects/camino.md`, katalog, registry a kanonický TVBCP.

Bezpecnost / neukladat:
Žádná reálná média, osobní texty, přesná GPS, klíče nebo citlivé síťové údaje v Gitu.

### 2026-09-14 21:22 CEST — Založení Camina před meziúkolem

Hotovo:
- Samostatný katalogový projekt, vlastní paměť, handoff a TVBCP; podklady v0.4 uchované.

Rozhodnutí:
- Míla zadal založení projektu a integraci do Human–Adam, commit, push a nasazení.
- Vývoj se dnes tímto krokem nezahajuje; nejdřív meziúkol, potom C00.
- Potvrzené U01–U11 z podkladů se znovu neotevírají. Návrhy D01–D10 nejsou nová uživatelská rozhodnutí.

Další krok:
- Vyřešit Mílův meziúkol; při návratu ke Caminu začít C00.

Navrhované další kroky:
- Po C00 připravit jen malý audio prototyp C01a podle skutečně ověřeného prostředí.

Technický důkaz:
- Manifest 15/15 shodných SHA-256; ZIP odpovídá všem 16 rozbaleným souborům.
- Testy integrace a stav publikace: viz `memory/reports/camino_registration_2026_09_14.md`.
- Testy aplikace a manuální hardware zkoušky NEPROVEDENO.

Ověření založení: 56/56 testů integrace (54 + 2 profilové testy) a rychlá statická brána OK.
Publikační plná brána a finální nasazení se ověřují registrovaným živým auditem;
tento zápis předchází schválenému push a nasazení.

### 2026-09-14 23:26 CEST — C00, Xcode a checkpoint po recovery záloze

Hotovo:

- C00 a samostatně schválená instalace Xcode dokončeny; projektové předání dorovnáno na skutečný stav.
- Před úklidem vznikla ověřená recovery záloha `20260914_231439`; dokumenty Camina zachované a porovnané pomocí SHA-256.

Rozhodnutí:

- Míla zadal nejdřív ostrou zálohu, potom úklid repozitáře. Úklid tvoří lokální dokumentační checkpoint bez mazání; push ani nasazení nejsou součástí tohoto kroku.
- U01–U11 beze změny. C01a se automaticky nezahajuje.

Další krok:

- Po výslovném zadání C01a připojit odemčený iPhone a ověřit rozpoznání, kompatibilitu a podpis pro malý audio prototyp.

Navrhované další kroky:

- Nahrát, bezpečně dokončit a přehrát krátký neutrální vzorek na skutečném telefonu; server není vstupní podmínka.

Technický důkaz:

- `camino/docs/ENVIRONMENT_AUDIT.md`, `DECISIONS.md`, `XCODE_INSTALLATION.md` a `camino/tasks/C01a_AUDIO_PROTOTYPE.md`.
- Instalační kontroly Xcode/first launch/iPhone SDK prošly; build a fyzické audio testy NEPROVEDENO.
- Recovery: 63 295 souborů, 28 892 kopírováno, 34 360 hardlinků, 43 symlinků, 0 přeskočeno; zkušební obnova AGENTS.md se shodným SHA-256.
- Závěrečná plná kontrolní brána checkpointu: 1684/1684 testů OK; syntaxe a Git safety check OK. Nejde o testy aplikace Camino.

### 2026-09-15 08:19 CEST — C01a: první prototyp, telefon připraven, build blokován

Hotovo:

- Malý prototyp Start/Stop, skutečný vstup, místní evidence a přehrání; 25 testů logiky a syntetického audia prošlo.
- Míla připravil důvěru a Developer Mode; přímý audit potvrdil párování, spojení a vývojové služby telefonu.

Rozhodnutí:

- Na Mílův pokyn pokračovat ve vývoji zahájeno pouze C01a. Žádná placená AI ani další etapa.
- Přímá kompilace není náhrada Xcode buildu, instalace nebo fyzického poslechu. Celý krok zůstává BLOCKED.

Další krok:

- V Xcode → Settings → Components ověřit a zpřístupnit Platform Support iOS 26.2, potom zopakovat build připraveného CaminoAudio projektu.

Navrhované další kroky:

- Po sestavení připravit podpis, nainstalovat prototyp a ručně ověřit neutrální vzorky Komentář/Úvaha. Žádná automatická aktivace mikrofonu.

Technický důkaz:

- `camino/docs/C01a_AUDIO_PROTOTYPE_REPORT.md`, `camino/prototypes/audio/README.md`.
- 25/25 XCTest OK; arm64/iOS kompilace/link exit 0, bez warnings; project.pbxproj lint OK.
- Xcode build exit 70: platform support iOS 26.2 chybí; platné signing identity 0. Fyzické testy NEPROVEDENO.
- Plná společná brána před checkpointem: 1684/1684 testů OK; nové Swift testy jsou samostatných 25/25 výše.

### 2026-09-15 13:34 CEST — Zahájení instalace podpory iOS

- Míla po dokončeném úklidu výslovně zadal spuštění instalace.
- Xcode Components: spuštěn balíček iOS 26.2 + iOS 26.3.1 Simulator; živě potvrzen postup stahování 185 MB z 10,47 GB (2 %). Úvodní odhad před spuštěním byl 8,39 GB.
- Před spuštěním 92 116 107 264 B volných (85,79 GiB). Instalační doklad je soukromý, mimo Git.
- Dokončení instalace, nový Xcode build, signing a fyzická přejímka zatím neověřeny; C01a zůstává BLOCKED.
- Další krok: Po dokončení stahování ověřit instalaci iOS Platform Support v Xcode Components a zopakovat nepodepsaný build C01a. Potom dořešit signing, instalaci na iPhone a fyzickou přejímku T015/T017/T025.
