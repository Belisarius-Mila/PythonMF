# Týdenní obnova: jeden průběžně sjednocovaný návod

Lokální vývoj Data, 2026-11-08 15:11 CET, větev data/parallel-20261104.
Žádný placený tah, služba, role, provozní TXT, push nebo nasazení.

## Výsledek

Míla výslovně požaduje, aby každý týden vznikala souvislá aktualizace kapitol,
ne další doplnění za původním textem. Nový integrovaný kontrakt je výchozí
v `maintainer.plan/run` a jeho App Server revieweru, nikoli pouze v promptu
či této dokumentaci. Transportní klient a produkční runtime se nemění.

`recovery_guide_consolidation.py` vytváří request připnutý k celému původnímu
textu, zdrojovému snapshotu, findings, verzi kontraktu a trusted datu.
Dynamické uzavřené schéma vydává jen keep/rewrite/insert/retire. Server:

- keep kopíruje původní blok přesně; rewrite nahradí jeho obsah v kapitole;
- vyžaduje právě jednu dispozici každého starého bloku, zachované pořadí
  kapitol, témat, bezpečnostních kontrol a chráněných procedur;
- dovolí doloženě vyřadit pouze historickou zálohovací/verzovací poznámku,
  nikoli potřebný příkaz či bezpečnostní ochranu;
- kontroluje neprázdné citace změn/vyřazení, autoritu a SHA zdrojů, tajemství,
  příkazy a technické literály; historie není živý důkaz;
- sám vloží jediný řádek Nejnovější update dokumentu z ddmmyyyy;
- odmítne vrstvy DOPLNĚNÍ/dodatků, pevná stará snapshot ID/statistiky,
  druhé datum či kapitoly; audit dispozic uloží odděleně od čtenářského TXT.

Opakovaný týden pracuje s poslední přijatou verzí. Beze změn po úplném
čtení lze vrátit keep a aktualizovat datum revize. Datum nic netvrdí o
čerstvosti zálohy ani nasazení. Každý návrh stále vyžaduje obsahovou přejímku:
programové kontroly neumějí prokázat věcnou správnost libovolného přepisu.

## Kompatibilita a bezpečnost

Původní quality.validate zachovává 75% retenční pravidlo i ostatní původní
kontroly. Sdílená obsahová kontrola má zvláštní integrovaný režim; rozlišuje
skutečný pokyn zapnout zrušený placený hlas od zákazu „nepovoluje nový pokus“.
Původní jednorázové full_pilot a receipt_recovery výslovně volí legacy_format,
nejsou automatickým fallbackem týdenní větve. Numerický exact pilot se nemění.

Trvalý marker před odesláním, slot, rezervace/cena a nemožnost automatického
retry zůstávají. Neplatná syntéza je attention; další volání stejného slotu
jen přečte účtenku. Původní uzavřený placený job zůstává attention bez opravy
raw, resetu, změny ceny nebo převzetí nového formátu. 24 artefaktů SHA shodných; dalších24 JSON z pěti starších uzavřených
jobů je také beze změny.

## Ověření

- 30 nových kontraktních testů: přepis v kapitole, vyřazení historie, dvě
  navazující revize, serverové datum, úplnost, evidence a bezpečnostní zápory.
- 153 cílených testů PASS včetně původních jednorázových/recovery cest.
- Plná projektová brána 2 824 testů OK, 5 skipped; závěrečná statická brána a git diff --check OK.
- Skutečný již dodaný návod 75 415 B/SHA381963c3…82543c8: dva offline průchody
  s fixture daty 15./22.11.2026, všech 17 kapitol a 340 bloků zachovaných přesně
  v layoutu, jediný update, bez dodatků/stálých snapshot ID. Schémata a odpovědi
  prověřil nezávislý Draft202012Validator. Výstupy zůstaly jen v paměti procesu;
  do reportu se uložily pouze agregace/hash. Žádné budoucí datum do Downloads.
- Stávající čtenářský soubor v Downloads i oba starší soukromé podklady beze změny.

## Přesný další integrační krok

Will převezme lokální commit a zapojí nový request/schema/validate do
navazujícího týdenního adapteru. Ze stávajícího scheduleru předá poslední
přijatý návod, zmrazený korpus a trusted datum. Teprve ověřený kandidát se
samostatnou obsahovou přejímkou může přejít do existujícího dvoucílového
writeru pod stejným request ID a SHA; iCloud upload i fyzický iPhone jsou
samostatné důkazy. Zachovat cenové schválení, roli, Standard a no-retry;
změna wire/schema vyžaduje čerstvý neplacený tokenový/cenový plán, nikoli
znovupoužití staré placené karty.

CLI run/tick, produkční scheduler a role zůstávají neaktivované. Tento krok
připravuje a vynucuje formát ve výchozím generátoru; netvrdí živý týdenní běh
ani hotové propojení s produkčním číselným adapterem a writerem.

## Změněné soubory

- Kód: recovery_guide_consolidation.py (nový), recovery_guide_maintainer.py,
  recovery_guide_quality.py; v recovery_guide_full_pilot.py a
  recovery_guide_receipt_recovery.py pouze explicitní volba původního formátu.
- Ověření: test_recovery_guide_consolidation.py (nový), test_recovery_guide.py,
  test_recovery_guide_preflight.py, test_recovery_guide_quality.py;
  cockpit_quality_gate.py registruje nový modul.
- Zápis: tento report a jeho JSON, recovery_guide_maintainer.md,
  capability_routing_rules.md, samantha_external_backup.md, ACTIVE_PROJECTS.md,
  MEMORY_INDEX.md, LESSONS_LEARNED.md a kanonický handoff/TVBCP
  project-samantha-infrastructure.md.
