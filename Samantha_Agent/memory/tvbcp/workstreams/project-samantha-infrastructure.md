<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-26 09:35 CEST

### Hotovo
- Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

### Další krok
- Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav

### Rozhodnutí
- Samantha Infrastructure bude mít vlastní stručný handoff a TVBCP; podrobná historie komunikace zůstává v existujícím TVBCP architektury komunikace

### Navrhované další kroky
- Po vyřešení rozdílu mezi main a deploymentem zvážit necitlivý read-only WebMCP pilot
- Upgrade Codex CLI provést samostatně s regresním testem app-server transportů

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `36bfcb473ec1`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `3e4729b7ecf1` · je starší než ověřený main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-25T10:56:19+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Samantha Infrastructure

Pracovni proud: `project-samantha-infrastructure`
Typ: `Project`
Rezim: `active`
Priorita: `1`

## Cil a hranice

Cilem proudu je udrzovat jednoduchou, odolnou a obnovitelnou infrastrukturu,
ve ktere Samantha bezpecne funguje na Macu i z iPhonu a terminal zustava
plnohodnotnou vyvojovou a nouzovou cestou.

Tento git-safe TVBCP zachycuje pouze kanonicka rozhodnuti, podstatne milniky,
rizika a dalsi smer infrastruktury. Detailni historie komunikacni vrstvy zustava
v `memory/tvbcp/architektura_komunikace_samantha.txt`; zde se neduplikuje.
Dokument nesmi obsahovat hesla, tokeny, API klice, private obsah ani
identifikatory vlaken.

## Soucasna architektura

### Rozhrani a runtime

- Cockpit na Macu je hlavni rozhrani pro beznou praci, stav, potvrzeni a
  rizene operace. iPhone pouziva stejny soukromy Cockpit pres Tailscale.
- Codex app-server bezi pouze lokalne a komunikuje pres privátní Unix socket.
  Tailscale zpristupnuje Cockpit, nikoli samotny app-server.
- Terminalovy start `samantha` zustava nezavislym vyvojovym, diagnostickym a
  recovery rozhranim pro pripad poruchy Cockpitu nebo app-serveru.

### Pracovni proudy a komunikace

- Organizacni jednotkou je `Project`, `Tool`, `Layer` nebo `Misc`. Kazdy proud
  ma vlastni dlouhodobou kontinuitu vlakna, handoff, TVBCP a izolovany workspace.
- Human-Adam a Knihovna jsou docasne kompatibilni adaptery; ostatni proudy
  pouzivaji jednotny lazy backend.
- V jednom vlakne probiha nejvyse jeden aktivni tah. Doručení se koreluje pres
  `client_message_id`; stav `delivery_unknown` je fail-closed a nesmi vest k
  automatickemu opakovani pokynu.

### Opravneni a private data

- Kazdy modelovy tah dostava explicitni `DEVELOPMENT_CONTROL`. Bez zapisoveho
  opravneni se workspace ani Git nemeni.
- Capability registry urcuje dostupnou operaci, jeji riziko, datovy rozsah a
  potrebne potvrzeni. Pracovni proud urcuje vecny kontext, ne obchazeni
  bezpecnostnich pravidel.
- Private data zustavaji mimo Git. Do handoffu, TVBCP, logu a odpovedi se
  propousti jen nezbytny redigovany dukaz.

### Vyvoj, Git a nasazeni

- Adam smi v zapisovacim tahu provest pouze vymezenou zmenu a relevantni testy.
- Checkpoint a lokalni commit, GitHub balik a nasazeni do Cockpitu jsou tri
  oddelene stavy. Spousti je pouze Míla potvrzenymi ovladacimi prvky Cockpitu.
- Lokalni `main` muze byt ciste napred pred `origin/main`; jde o cekajici
  GitHub balik, nikoli automaticky o chybu nebo povoleni k pushi.
- Nasazeni vyzaduje samostatnou branu, rizeny restart, overeni serveroveho
  stavu a smoke test. Git commit sam o sobe neni dukaz nasazeni.

### Pamet, zivy stav a recovery

- TVBCP drzi rozhodnuti a dlouhodoby smer. Handoff drzi obnovitelny soucasny
  stav. Autosave je pouze nouzova technicka obnova.
- Promenlive tvrzeni jako `bezi`, `aktivni` nebo `nasazeno` se opira o
  redigovany live audit; historicka pamet musi priznat sve stari a nejistotu.
- Recovery nejdrive overi doruceni, Git, workspaces, app-server a autosave.
  Nejasny pokyn se neposila znovu a neodpovidajici socket nebo proces se nemeni
  bez dukazu vlastnictvi.

## Kanonicka rozhodnuti

- Zachovat jeden Macem hostovany soukromy Cockpit a nevytvaret druhy vzdaleny
  app-server ani paralelni kopii aplikace pro iPhone.
- App-server ponechat na lokalnim Unix socketu a nevystavovat jej primo pres
  Tailscale ani verejnou sit.
- Zachovat jeden aktivni tah, presnou korelaci doruceni a fail-closed
  `delivery_unknown`.
- Zachovat explicitni zapisove opravneni pro jeden tah a capability-based
  bezpecnostni rozsah.
- Zachovat checkpoint, GitHub push a nasazeni jako samostatne potvrzovane
  operace s vlastnim dukazem.
- WebMCP muze byt pozdeji pouze tenkou vrstvou nad existujici logikou a
  opravnenimi Cockpitu; nesmi vytvorit druhou bezpecnostni autoritu.

## Otevrene kroky a rizika

- Stav pred zalozenim dokumentu: lokalni `main` byl ciste napred pred GitHubem,
  bezici Cockpit pouzival starsi overeny commit a jeho code stamp nebyl
  potvrzeny. Tento dokumentacni krok nic nepushuje ani nenasazuje.
- Pred upgradem Codex CLI je nutny cileny regresni test stdio a Unix-socket
  app-server transportu; samotne zastarani `codex mcp-server` soucasny runtime
  nezasahuje, protoze jej Samantha nepouziva.
- WebMCP je dostupnostne omezeny a website-provided tools jsou neduveryhodny
  vstup. Pripadny pilot musi byt necitlivy, read-only a musi znovu pouzit
  existujici autorizaci Cockpitu.
- Event-triggered ulohy ChatGPT nejsou soucasti kanonicke infrastruktury.
  Nepripojovat osobni e-mail nebo externi sluzbu bez konkretniho prinosu a
  samostatneho rozhodnuti o opravnenich.

## Chronologicke zaznamy

Prvni casovany zaznam prida potvrzeny checkpoint tohoto dokumentacniho kroku.

### 2026-08-26 09:35 CEST – Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky

Hotovo:
- Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Samantha Infrastructure bude mít vlastní stručný handoff a TVBCP; podrobná historie komunikace zůstává v existujícím TVBCP architektury komunikace

Další krok:
- Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav

Navrhované další kroky:
- Po vyřešení rozdílu mezi main a deploymentem zvážit necitlivý read-only WebMCP pilot
- Upgrade Codex CLI provést samostatně s regresním testem app-server transportů

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-samantha-infrastructure`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.
