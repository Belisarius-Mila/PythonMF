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

Funkční rozsah: e-mailové ruční hlídání aae687fb + Datovy HA-01/02/03.
Ateliér4ea5b01e už je patch-equivalentně převzatý jako58a18e68; nyní se
připojuje jen jeho stará historie. Stejně se historicky uzavírá příprava
UI8f64dca7/9d89446b, jejíž přijímací kontrakty plní dokončené aae687fb.
Nevzniká rollback současných souborů, nové placené generování ani další feature.
Funkční app/scripts/tests jsou stejné proti merge8d05aac2; jediná odchylka
od Datovy implementace je testový očekávaný důvod bezpečného odmítnutí hluboké
JSON list obálky pro různé Python verze.201 integračních testů PASS;
Python3.11 stejný jednotlivý bezpečnostní test PASS. Finální plná lokální brána PASS: 3602 testů,31 SKIP, 507.039 s.


Autorita výsledku: původní účtenka jobu `4242cf7f5bdb6b88724e635cde31b443`,
`data/private/combined_release_20261112/release_receipt.json`.
Terminálový návrat se posuzuje odděleně od portálového returned_to_adam.


## 2026-11-12 10:58 CET — Finální společný balíček pro jedno Terra p+n

**Hotovo:** Funkčně nové ruční e-mailové UI aae687fb a Datovy HA-01/02/03
5d9c1497,7b77aba2,045936f9 jsou společně na main. Zbývající staré větve
jsou propojené pouze historicky: půdorys4ea5b01e má přesně stejný stable
patch-id jako již převzatý58a18e68 (c13a5067bd2855a44a068dc7e249c8981335f2d8).
Současné názvy návrhů, bezpečnostní úpravy a ostatní novější kód Ateliéru
zůstávají zachované. Přípravné commity8f64dca7/9d89446b mají dokončenou
náhradu v aae687fb: všechny kontrakty přešly do kanonického UI, které navíc
nemá nepotvrzený automatický výchozí termín. Historické propojení nepřenáší
žádný starší zdroj ani nepřepisuje dnešní implementaci.

**Rozhodnutí:** Výslovné Mílovo p+n všech hotových commitů se provede jednou
registrovaným submit_release(wait=True), v aktuálním project-email-cases,
společný cíl Cockpit Samanthy. Request combined-finished-work-20261112-v1,
job4242cf7f5bdb6b88724e635cde31b443. Schválený head se doplní až po finálním
lokálním merge commitu a zarovnání čistých profilů. Žádná změna modelové
politiky, automatického monitoru, systémové služby nebo placený vývojový pilot.

**Další krok:** Dokončit finální celkovou bránu, lokální checkpoint a jediné
p+n; výsledek jednou ověřit z původní účtenky a živého HTTP.

**Navrhované další kroky:** Lidská Mac/iPhone přejímka; e-mailová etapa3 a
Human–Adam HA-04 až jako další vývoj. Samostatný e-mailový TVBCP zůstává
nedohodnutý; aktualizují se existující správné handoffy a Cockpit/Layer TVBCP.

**Technický důkaz:**201 integračních testů PASS; zvlášť shodná bezpečnostní
regrese v Python3.11 PASS. Nový dispatcher ověřen skutečným initialize a
model/list na sdíleném serveru0.167.0 bez nového thread/start/turn/start.
Historické merge ponechávají app/scripts/tests bytewise stejné proti8d05aac2.
Finální plná lokální brána PASS: 3602 testů,31 SKIP, 507.039 s.
Výsledková autorita: reports/combined_finished_work_release_20261112.md a
původní privátní job/receipt. Zápis vzniká před publikací, není účtenkou
nasazení. Při nejistotě se původní job dohledá, nepodává se nový požadavek.
