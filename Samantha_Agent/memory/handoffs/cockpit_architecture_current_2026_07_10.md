Nazev: Samantha Cockpit - hlavni architektura a postupna modernizace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-10

Co se resilo:

- Probehl hluboky read-only audit hlavni architektury Samantha Cockpitu se
  zamerenim na Cockpit, VoiceBridge, dokumenty, e-maily, provozni bezpecnost,
  vykon a testovani.
- Zamerne byly vynechany jednotlive rodinne, jazykove, lekarnicke a dalsi
  samostatne projekty.
- Mila schvalil smer postupne modernizace bez prepisu od nuly a s malymi,
  overitelnymi implementacnimi baliky.
- Tento soubor je prubezny aktivni handoff. Behem aktualni faze se ma
  aktualizovat, ne zakladat novy handoff po kazde male uprave.

Co je hotove:

- Hlavni audit je ulozen v koreni projektu jako `AuditCockpit56.txt`.
- Prvni vykonovy krok je implementovany a pushnuty v commitu `23abbaa`:
  - novy lehky GET `/api/live-status`,
  - trisekundovy frontend monitor uz nevola plny `/api/status`,
  - plny status se automaticky obnovuje jednou za pet minut,
  - draha VoiceBridge procesni diagnostika ma patnactisekundovou cache,
  - smoke check kontroluje take live status.
- Po zmene proslo 374 relevantnich testu.
- Lokalni i Tailscale Cockpit po nasazeni prosly smoke checkem.
- Kontrolni mereni ukazalo priblizne 2-6 ms pro cachovany live status oproti
  priblizne 1,07 s pro kontrolni plny status.
- `main` a `origin/main` jsou na commitu `23abbaa` synchronizovane.

Co neni hotove:

- Faze stabilizace neni uzavrena. Zbyva zejmena:
  - centralni limit velikosti requestu,
  - jednotne zpracovani chybneho JSON a neocekavanych vyjimek,
  - bezpecnostni HTTP hlavicky a kontrola Host/Origin,
  - bezpecny provozni log bez citlivych payloadu.
- Stale bezi dve samostatne Cockpit instance nad stejnymi file-based daty.
- Prime JSON/JSONL zapisy nemaji jednotny file lock a atomicky zapis.
- `app/cockpit.py` zustava monolit s backendem, HTML, CSS a JavaScriptem.
- VoiceBridge nema jeden explicitni stavovy model prikazu.
- Dokumentove a e-mailove workflow nemaji jednotnou repository/transakcni
  vrstvu.

Dalsi krok:

Pripravit a implementovat dalsi maly balicek faze stabilizace: centralni HTTP
request boundary pro `CockpitServer` - omezeni velikosti JSON tela, rizene 400
pro chybny payload, jednotna bezpecna 500 odpoved, zakladni bezpecnostni hlavicky
a testy. Nemenit pri tom business logiku dokumentu, e-mailu ani VoiceBridge.

Navrhovane dalsi kroky:

1. Dokoncit stabilizaci HTTP vrstvy a uzavrit ji samostatnym commitem.
2. Navrhnout prechod ze dvou serveru na jednu instanci s Tailscale proxy,
   rollbackem a zachovanim iPhone pristupu.
3. Zavest spolecnou atomickou file persistence a zamky; doplnit concurrency test.
4. Postupne rozdelit monolit pri zachovani endpointu:
   status/health -> voice -> documents -> email -> staticky frontend.
5. Zavadet explicitni stavove modely a repository vrstvy po oblastech, ne
   jednim velkym prepisem.

Handoff strategie pro tento program:

- `AuditCockpit56.txt` je hlavni roadmapa a zdroj architektonickych zaveru.
- Tento soubor je jediny prubezny aktivni handoff.
- Novy handoff nevytvaret po kazdem pracovnim dni ani drobne oprave.
- Pri dokonceni velke faze vytvorit jeden finalni checkpoint a tento current
  handoff prepnout na dalsi fazi.
- Pocitat nejvyse s peti finalnimi fazovymi checkpointy:
  1. stabilizace a HTTP bezpecnost,
  2. jedna instance a bezpecne ukladani,
  3. rozdeleni monolitu,
  4. VoiceBridge stavovy model,
  5. dokumenty, e-maily a zaverecne UI/testy.

Zmenene nebo relevantni soubory:

- `AuditCockpit56.txt`
- `app/cockpit.py`
- `scripts/cockpit_smoke_check.py`
- `tests/test_cockpit.py`
- `scripts/install_cockpit_local_launchd.sh`
- `scripts/install_cockpit_tailscale_launchd.sh`
- `reports/cockpit_function_inventory_audit_2026_06_27.md`
- `reports/cockpit_post_action_risk_matrix_2026_06_27.md`
- `handoffs/voicebridge_operational_contract_2026_06_30.md`

Bezpecnost / neukladat:

- Neukladat obsahy soukromych dokumentu, e-mailu ani hlasovych pokynu.
- Neukladat tokeny, hesla, API klice, cele e-mailove adresy ani private vault data.
- Pred zasahem do VoiceBridge znovu precist jeho provozni kontrakt a zachovat
  pravidlo jedineho vlastnika doruceni.
- Prechod na jednu instanci nesmi prerusit lokalni ani iPhone pristup; musi mit
  predem popsany rollback a smoke check.
- Existujici dokumenty pri budouci migraci nepresouvat ani nemazat bez
  samostatneho potvrzeni.
