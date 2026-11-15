# Jednotná validační politika

Rozhodnutí Míly 15.11.2026: potřebné kontroly vynucuje program. Běžná úprava
nemá opakovat tisíce nesouvisejících testů. Schválená druhá etapa zavádí
balíčky domén a závislostí, denní plnou CI regresi a izolované Git fixture.

## Jediná autorita a použití

Autoritou je `app/communication/validation_policy.py`, verze `validation-v2`.
Pevná mapa zdrojů, testů a přechodů mezi doménami je pouze v
`validation_domains.py`; testovací moduly pocházejí z kanonického
`cockpit_quality_gate.py`. Checkpoint, GitHub batch, Luna a deploy používají
stejný `checkpoint_quality_gate.run_checkpoint_quality_gate`. Terminál volá
registrovaný `validate_project`: `.venv/bin/python scripts/validation_gate.py`.
Příkaz nic nepushuje, nenasazuje ani nerestartuje. Důvod výběru je v jeho
soukromém logu; model ani payload nemůže vybrat vlastní testy nebo rychlý režim.
Samotný `--skip-unit-tests` je diagnostika, nikoli publikační důkaz.

## Výběr kontrol

Porovnává se celý kandidát od auditovaného origin/main včetně staged,
unstaged a neignorovaných nových souborů. Rename zahrnuje obě cesty.
Stejný strom lze po commitu svázat s jeho přesným SHA. Prázdný diff sám
nedovoluje přeskočit testy: potřebuje přesně odpovídající podepsaný důkaz.

Každý cílený běh má malý společný základ: HTTP bezpečnost, server, atomická
persistence, runtime policy a funkční kompozice frontendu. K němu program
přidá doménu a skutečné konzumenty změněného Python kódu/testovacích fixture.
Podporované oblasti a jejich účel:

| Doména | Povinné doménové pokrytí |
| --- | --- |
| calendar | čtení, zápis, úprava, mazání, úkoly, e-mailový kalendář a HTTP/UI |
| library | knihy, archiv, umístění, fotografie a odpovídající UI |
| frontend | známé společné styly/PWA a navazující archiv/fotografie |
| email_followups | hlídání, posouzení, monitor a HTTP/UI |
| email_agent | průběžná pošta, návrhy, preference, hodinový běh a HTTP/UI |
| interior | Ateliér, AI/protokol, názvy, aktivace a HTTP/UI |
| science | vědecké zprávy a jejich rozhraní |
| vocabulary | registrované slovíčkové moduly a jejich frontendy |
| camino_film | filmový editor, export a Mac klient |
| documents | registrované dokumentové operace a e-mailový archiv |
| human_adam_ui | pracovní panel a živý stav |
| mmtx | registrované MMTX aplikace a jejich testy |

Python importy se čtou ze skutečného textu, i relativní a tranzitivní.
Změna fixture rozšíří testy jejích uživatelů; samotné spuštění testu takové
rozšíření nedělá. Explicitní hranice kompozice/čtecích adaptérů mají vlastní
konzumentské testy (hlavní aplikace, Cockpit/frontend, e-mailový proposer,
dohlížitel a aktivace Ateliéru). Změna adaptéru samotného výjimku nemá.
Swift/JavaScript/protokolové vazby jsou v pevné doménové mapě, nejsou odvozovány
z Python importů. Mapa není univerzální analýza všech runtime vazeb.

Plná sada se zvolí při neznámém souboru/konzumentovi, neověřitelné závislosti,
chybě parsování, dynamickém importu v měněném Python modulu nebo chybějícím
testovacím modulu. Vyžadují ji nové spustitelné cesty před prvním plným
ověřením a změny společného workflow, konfigurace rolí, závislostí, CI,
checkpointu, publikace, záloh, sdílené persistence/transakcí a samotné politiky.
Příklady: drobná změna calendar_writer má doménovou sadu; vocabulary_authoring
s dynamickým importem či followups se sdíleným servisním konzumentem plnou.
Více domén spojí všechny potřebné testy. Cíl přibližně300 testů/minuta není
strop: bezpečnostní pokrytí se kvůli číslu nikdy nezkracuje.

## Důvěryhodná místní účtenka

Cílený místní běh vyžaduje úspěšný plný základ v témže prostředí, nejvýše24h
starý. Chybějící/prošlý základ vyvolá plnou bránu, i když noční GitHub CI prošla.
Řetězení cílených kontrol tuto lhůtu neprodlužuje. Přechod v1→v2 vyžaduje nový
plný základ. Po checkpointovém zápisu lze ověřit jen změněnou doménu/dokumenty,
pokud jsou všechny ostatní chráněné bajty a režimy přesně shodné. Nová
spustitelná cesta tím tuto podmínku neobchází.

Soukromá metadata společného Gitu obsahují `samantha-validation`, náhodný
lokální klíč a atomické HMAC-SHA256 účtenky. Adresář700, klíč/účtenky600;
nepatří do stromu, commitu ani payloadu modelu. Účtenka váže SHA-256 skutečných
vstupů/režimů, politiku, recept, prostředí Pythonu, verze/RECORD závislostí a
otisky nástrojů. Vstupy se porovnají před i po testech/převzetí; stejná
velikost/mtime změnu neskryje. Cache importů také vychází ze skutečného textu.
Starý načtený modul politiky, mapy či registru nemůže převzít nový rychlý důkaz.

Vadná, podvržená, prošlá nebo nekompatibilní účtenka se nepoužije; běh musí
doložit alespoň jeden test. Externí/adresářové symlinky nemají cache.
Ochrana neřeší nedůvěryhodný proces pod stejným účtem nebo správce Macu.
Ignorovaná soukromá provozní data nejsou vstupem syntetických testů; živý smoke,
Git heads, oprávnění a chráněné služby se vždy ověřují zvlášť.

## GitHub CI a provoz

`validation_ci.py` vybírá stejnou doménovou politiku nad celým rozdílem proti
neměnnému SHA události push/PR, včetně mělkého checkoutu. Chybějící/neplatný
základ znamená plnou sadu. Workflow nemá path filtry, které by neznámou změnu
potichu přeskočily. Každý den02:17 UTC a při workflow_dispatch běží plná sada;
běžný push ji nezruší, protože má jinou concurrency group. Plán začne platit
teprve po samostatně povoleném pushnutí na výchozí větev. Místní LaunchAgent
se nezřizuje. GitHub CI nevydává místní publikační účtenku ani nepřebírá HMAC.

Rezerva plné místní brány je1500s. Timeout uchová částečný log a nedovoluje
opakovat publikaci. První vydání změny samotné politiky projde plnou branou;
běžící backend novou politiku získá až samostatně povoleným nasazením.
Historické quick účtenky zůstávají čitelné, nejsou novým důkazem bez testů.

Testovací Git šablona se inicializuje jednou za proces; každá fixture dostane
samostatnou úplnou kopii včetně .git/index, refs a objektů, bez hardlinků.
Zápisy do jedné kopie se nesmějí objevit v jiné ani v šabloně. Provozní Git,
média, zálohy a soukromá data tento mechanismus nepoužívají.
