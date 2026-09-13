# Cockpit — zrychlení spouštění Gitu a rozsah testovací brány

Navazuje na `4e498bc0`. Měření na Macu, Python 3.12.0rc3, dne 13. 9. 2026.

## Co se změnilo

Při měření jednoduchého Git dotazu vyšel medián přes `/usr/bin/git` přibližně
33 ms a přes Git vybraný pomocí `xcrun --find git` přibližně 12 ms. Obě cesty
vrátily `git version 2.50.1 (Apple Git-155)`. Výsledek byl podobný s timeoutem
60 s i bez něj; každá ze čtyř kombinací měla 30 vzorků. Významnou část nákladu
tedy tvoří systémové spouštění Gitu, nikoli samotná složitost testů.

`human_adam_workspace.py` nyní na Macu jednou při importu zjistí vybraný Git.
Přesnou absolutní cestu použije pro společné Git operace a vytvoření klonu.
Nevolí jinou instalaci podle PATH a nemění nastavení Xcode ani systému.
Nejde o cache Git stavu: příkazy, jejich počet, argumenty, timeouty, prostředí,
kontroly čistoty a ověření po zápisu zůstávají zachované.

Když zjištění cesty selže, přesáhne 5 s, vrátí neplatnou/neexistující/neproveditelnou
cestu nebo program neběží na Macu, zůstává původní `/usr/bin/git`.
Volba nástroje platí po dobu procesu; po změně vybraného Xcode/toolchainu je
potřeba proces restartovat. Systémovou aktualizaci nástrojů tento krok neprovádí.
Ostatní samostatná volání Gitu mimo správu workspace se zatím nemění.

## Srovnání stejné sady

**1655 testů před i po, všechny prošly bez chyby, selhání nebo skipu.**
Testovací část plné brány klesla z **453,732 s na 340,302 s**:
**úspora 113,430 s (1 min 53 s), tedy 25,0 %**. Nový testovací podproces
včetně startu/importů zabral 345,3 s; i ostatní kontroly kanonické brány prošly.

| Skupina | Testů | Před (s) | Po (s) |
| --- | ---: | ---: | ---: |
| `simple_main_checkpoint` | 28 | 121.40 | 82.27 |
| `simple_main_deploy` | 18 | 89.80 | 52.25 |
| `human_adam_takeover` | 13 | 63.39 | 42.15 |
| `human_adam_workspace` | 35 | 51.60 | 34.09 |

Čtyři Git skupiny: 326.20 → 210.76 s. Zbytek testů a režie
runneru: 127.53 → 129.55 s. Naměřená úspora se tedy
soustředí v upravených skupinách, nikoli v náhodně rychlejším zbytku sady.
Manifest i počty testů v jednotlivých modulech byly ověřené jako shodné;
sousední JSON uchovává bezpečné součty a metodiku.

Oba běhy mají stejný kanonický manifest i testový kód, včetně pěti nových
rychlých kontrol resolveru. Běžely postupně, ne souběžně. Baseline pouze
v diagnostickém procesu nastavil `_GIT_EXECUTABLE = '/usr/bin/git'`; další
běh použil novou automatickou volbu v kanonické plné bráně. Nevynechal se
žádný test, nezměnil se timeout a nepoužilo se paralelní spouštění.

Srovnávají se přímo časy unittest části. Importy a další kontroly plné brány
jsou navíc; výchozí diagnostický běh sám neopakuje statickou část. Jeden pár
úplných běhů je důkaz pro tento Mac a tuto sadu, nikoli garantovaná úspora
na jiných počítačích. Na Linuxu toto zrychlení očekávat nelze.

## Musí běžet všechny testy?

Nemusí běžet všechny při každé běžné změně. Už existuje rychlá statická brána
plus explicitní malé sady v `cockpit_fast_feedback.py`: `frontend`,
`email-archive` a `http-security`. Například:

```sh
.venv/bin/python scripts/cockpit_fast_feedback.py frontend
```

V porovnávacím běhu stálo 265 testů samotného Cockpitu jen 5,56 s;
94 testů čtyř Git skupin 326,20 s. Počet testů sám o sobě není měřítkem ceny.

Výběr se řídí změněnou oblastí a konkrétní vazbou. Samotná statická kontrola
není funkční test. Změny workflow, persistence, checkpointu, push/deploy,
záloh nebo odchozích operací podle projektových pravidel vyžadují plnou
bránu. GitHub batch nadále vyžaduje vlastní plnou bránu nad přesným headem.

Není prokázáno, že je každý jednotlivý test nezastupitelný. V omezené statické
kontrole 94 metod čtyř nejdražších modulů nebyly doslova shodné AST bloky
metod; to nenahrazuje audit sémantických duplicit. Kontrolované scénáře
zahrnují rozdílné chyby: rozpracovanou práci, divergenci, výpadek push,
nezdařený checkpoint, chybějící index nebo hromadné mazání. Jejich vysoká
cena sama neznamená, že jsou zbytečné. Žádný test zde nebyl odstraněn.

Případné další úspory: u konkrétní domény hledat překryv testů se stejným
vstupem, kontrolami a selháním; levné jednotkové testy doplnit menším počtem
skutečných integračních cest až po doložení stejného pokrytí. Rozšiřování
cílených sad je samostatná malá změna podle příštího vývojového řezu.

## Ověření a dodání

- Sedm cílených testů prošlo: volba nástroje, neplatná cesta, chybějící nástroj,
  timeout, Linux fallback, zachované argumenty a dvě skutečné deploy cesty.
- Kanonická plná brána 1655/1655 prošla. Výchozí porovnávací sada také 1655/1655.
- AST porovnání potvrzuje zachování celé původní workspace logiky a všech
  30 původních workspace testů. Změna dvou executable pozic, žádné úpravy brány.
- Auditní TXT, kanonický handoff a TVBCP jsou aktualizované. Nový lokální
  commit se přidává do odložené společné dávky; push/nasazení neproběhly.
- Běžící Cockpit zatím nový kód nemá; jeho zrychlení po nasazení nebylo měřené.

## Reprodukce porovnání

Výchozí varianta používá původní launcher pouze v diagnostickém procesu:

```sh
PYTHONPATH=. .venv/bin/python - <<'PYCODE'
from app.communication import human_adam_workspace as workspace
from scripts.cockpit_quality_gate import TEST_MODULES
from scripts.cockpit_test_timing import main
workspace._GIT_EXECUTABLE = '/usr/bin/git'
raise SystemExit(main(['--output', '/tmp/git-launcher-before.json', *TEST_MODULES]))
PYCODE
```

Po jejím dokončení spustit novou variantu samostatně:

```sh
PYTHONPATH=. .venv/bin/python scripts/cockpit_quality_gate.py --unit-test-timings /tmp/git-launcher-after.json
```

Oba příkazy používají aktuální testový kód; při pozdější změně sady se budou
měnit i výsledky. Pro zdejší naměřené hodnoty platí stav tohoto commitu.
