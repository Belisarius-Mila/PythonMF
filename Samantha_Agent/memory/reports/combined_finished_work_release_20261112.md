# Společné vydání hotové práce Will + Data

Datum: 2026-11-12 10:55 CET


## 2026-11-12 10:55 CET — Will přebírá HA-01 až HA-03 do společného vydání

**Hotovo:** Lokálně převzaté Datovy tři hotové commity5d9c1497,7b77aba2 a045936f9
nad e-mailové UI aae687fb. Kód se spojil bez konfliktů; paměť zachovává obě
historie v časovém pořadí. Oprava startu pošty, její zámek i modelové role
jsou přesně zachované. Jedinou integrační úpravou je přenositelnost diagnostické
asertace hlubokého neobjektového JSON mezi Python3.11/3.12; obě cesty stále
odmítnou rámec, uzavřou spojení a probudí čekající RPC. Produkční dispatcher
zůstává Datovou verzí.

**Rozhodnutí:** Míla výslovně zadal společné p+n všech hotových Willových i
Datových commitů. Balíček zahrne také odložený hotový Ateliér4ea5b01e. Jediné
registrované vydání má request `combined-finished-work-20261112-v1`, job `4242cf7f5bdb6b88724e635cde31b443`,
project-email-cases→společný Cockpit. Vykonavatele určí centrální Terra role.
Nejde o aktivaci dalších služeb ani placený vývojový/modelový pilot.

**Další krok:** Převzít Ateliér, dokončit celkovou bránu a zmrazit přesný
commit pro jediné registrované p+n.

**Navrhované další kroky:** Po vydání fyzická přejímka Human–Adam na Macu/iPhonu;
HA-04 až po samostatném zadání. E-mailový automatický monitor zůstává další etapa.

**Technický důkaz:**201 cílených testů PASS, samostatný test také v Datově
Python3.11 PASS. Skutečný nový klient přes stávající Unix WebSocket: initialize
amodel/list,10 modelů, CLI/server0.167.0, žádný thread/start ani turn/start;
uzavřené jen vlastní spojení, sdílený socket zachovaný. Toto není důkaz
modelového tahu, reconnectu dlouhé práce ani fyzické přejímky. Plná brána
poběží nad finálním společným balíčkem; meziběh před rozšířením na Ateliér
se nevydává za úspěšnou závěrečnou kontrolu. Soukromé důkazy
`data/private/combined_release_20261112/`.

## Stav finálního balíčku

INTEGRATION_PENDING

Autorita výsledku: původní účtenka jobu `4242cf7f5bdb6b88724e635cde31b443`,
`data/private/combined_release_20261112/release_receipt.json`.
Terminálový návrat se posuzuje odděleně od portálového returned_to_adam.
