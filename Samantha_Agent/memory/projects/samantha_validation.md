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
