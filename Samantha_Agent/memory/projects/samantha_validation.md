# Samantha — ověření a rychlost vydání

Proud `project-samantha-infrastructure`; kanonická pravidla
`../technical/validation_policy.md`, existující infrastrukturní handoff/TVBCP.

15.11.2026: Míla pověřil Adama další opravou a odmítl automatické plné brány
při vývoji/commitu/p+n velkého projektu. Místní politika validation-v3 má
cílené domény a smluvní sady pro sdílené komponenty. Plná regrese je pouze
noční CI nebo výslovný ruční `validation_gate.py --full`. Nevyžaduje se
plný základ pro nový soubor, změnu pravidel ani po expiraci účtenky.

Opravené skutečné cesty VocabularyEN CSV/katalog/obrázky a docs/data,
docs/assets včetně zvuků, vět a náhledů. Poslední Datova dávka503 cest
nově vybírá99 testů/9 modulů, žádná nezařazená cesta. Skutečně PASS:
99 testů/37,190s unit;53,881s celý diagnostický běh včetně statických kontrol
a výběru. Nejde o měření nového ostrého p+n ani o živou přejímku telefonu.
42 regresí selektoru/účtenek PASS před závěrečnou cílenou integrací.

Podpis je dál v soukromých Git metadatech, přesné vstupy a zaznamenané
covered_modules. Úzká účtenka nemůže přeskočit testy jiné čekající změny.
Po24h se opakuje cílená sada, nikdy automaticky celý projekt. Procesová
SHA cache přidává do klíče inode/device/ctime; stejná velikost/mtime změnu
neskryjí. Měření úplného capture obsahu/prostředí15,098s první /2,142s opakované.

Přijatý kompromis: méně okamžitě ověřených kombinací; chyba jiného konzumenta
sdílené funkce se může projevit až v noci nebo při použití. Četnost neznáme.
Bezpečnostní/recovery smluvní testy zůstávají, plná sada není důkaz živých
oprávnění, doručení nebo iPhone. Nenahrazovat tento závěr tvrzením nulového rizika.

Poslední skutečné společné vydání v2+kalendář+Data je95037bfe, oba cíle
potvrzené: Cockpit5/5, Pages7805060201, veřejný JSON522 karet přesně shodný.
7 commitů, full775,3s, navazující34,3/38,4s, vydání od předání1204,9s.
Účtenky95bf90ef2edd436f2ce26616a88621a9 /cba6543a65c27fa456db0a2b817e8f3e
v private all_pending_release_20261115/. Tento historický výsledek není nový živý audit.

V3 je nový místní vývoj bez p+n/restartu. Závěrečné cílené ověření, skutečné
počty/časy, zdrojové otisky a commit jsou pouze v
`data/private/validation_focused_20261115/completion.json`.
Report `../reports/validation_focused_20261115.md`; žádný nový model, přesun
médií, změna soukromých dat, role nebo kalendářový zápis.


## 2026-11-15 22:31 CET — Opětovné převzetí již ověřených testů

Hotovo: Terminál a serverová brána používají stejné skutečné testovací
prostředí. Soukromá kopie se shodným obsahem nezneplatní účtenku jen kvůli
omezenějším právům ostatních uživatelů. Na souborech se žádná práva nemění.
Rozhodnutí: Míla upřednostnil odstranění opakovaných testů před HA-09.
Zůstává HMAC,24h platnost, přesný obsah a pokrytí modulů. Změna nástrojů,
závislostí, vlastníkových práv, spustitelnosti nebo obsahu vyžaduje nový důkaz.
Další krok: Po cílené bráně lokální commit a ověření převzetí v čistém
profilu přes skutečný runner bez opakování testů. Nasazení vyžaduje samostatné p+n.
Navrhované další kroky: Po vydání HA-09 — propojit checkpoint a Terra p+n
s původním zadáním. Míla dnes potvrdil iPhone přejímku opravy HA-05.
Technický důkaz: Poslední ostré p+n znovu provedlo665 testů/234,6s.
Otisk prostředí terminálu se lišil od launchd;2027 souborů mělo při shodném
HEAD jiné group/other bity (644/600 a755/700). Nové regrese před opravou
selhaly;53 cílených testů po opravě PASS. Kanonický PATH, importy,
locale, UTC a hash seed se skutečně předávají podprocesu. Výslovný Node
nebo Xcode zůstává součástí otisku. Účtenka ignoruje group/other bity jen
pro soubor vlastněný stejným efektivním uživatelem; UID, owner/special bity
a veškerá práva cizího vlastníka zůstávají v otisku.
Finální důkaz: data/private/validation_reuse_fix_20261115/completion.json.
Rizika: Staré účtenky jiného formátu se nepřebírají. První ověření nové
politiky musí proběhnout; fyzické/runtime ověření nenahrazuje testovací cache.
Tento vývoj sám nezahrnuje push, restart ani HA-09.
