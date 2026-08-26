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

# Handoff pracovniho proudu: Samantha Infrastructure

Nazev: Samantha Infrastructure
Pracovni proud: project-samantha-infrastructure
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-08-26

Co se resilo:
- Zalozeni kanonicke dvojice handoff + TVBCP pro infrastrukturu Samanthy.
- Strucny popis soucasne komunikacni, bezpecnostni, pametove a provozni
  architektury bez kopirovani historie z TVBCP Human-Adam.

Co je hotove:
- Hlavnim uzivatelskym rozhranim je Cockpit bezici na Macu; z iPhonu je
  dostupny pres soukromou Tailscale cestu.
- Codex app-server bezi lokalne pres privátní Unix socket. Neni primo vystaven
  do Tailscale ani do verejne site.
- Kazdy pracovni proud ma vlastni kontinuitu vlakna, pracovního kontextu,
  handoffu, TVBCP a izolovaneho workspace. Human-Adam a Knihovna zustavaji
  docasne kompatibilnimi adaptery; ostatni proudy pouzivaji lazy backend.
- Jeden aktivni tah, `client_message_id`, persistovany stav a
  `delivery_unknown` chrani proti soubehu a automatickemu opakovani nejasne
  doruceneho pokynu.
- `DEVELOPMENT_CONTROL` uděluje zapis pouze pro jeden vymezeny tah. Capability
  registry urcuje dostupne operace a jejich bezpecnostni rozsah.
- Adam provadi jen autorizovanou zmenu a testy. Checkpoint, lokalni commit,
  GitHub balik a nasazeni jsou oddelene kroky ovladane potvrzenymi prvky
  Cockpitu.
- Projektova pamet rozlisuje TVBCP, handoff, autosave a redigovany live status.
  Promenlivy provozni stav se overuje zive; historicky snapshot jej nenahrazuje.
- Pri selhani Cockpitu nebo app-serveru zustava plnohodnotna terminalova
  recovery cesta pres `samantha`, Git, autosave a projektovou pamet.

Co neni hotove:
- Pred timto dokumentacnim krokem byl lokalni `main` napred pred GitHubem a
  bezici Cockpit pouzival starsi overeny commit. Push ani nasazeni nejsou
  soucasti tohoto kroku.
- Code stamp soucasneho deploymentu nebyl v dodanem live statusu overeny.
- WebMCP neni soucasti architektury Cockpitu. Pripadny read-only pilot zatim
  nebyl navrzen ani implementovan.
- Upgrade instalovaneho Codex CLI a regresni overeni app-server protokolu jsou
  samostatny budouci provozni krok, nikoli blokator soucasne architektury.

Dalsi krok:
- Potvrzenym checkpointem overit novou kanonickou dvojici a zachytit jeji prvni
  casovany stav; GitHub balik a nasazeni ponechat oddelene.

Navrhovane dalsi kroky:
- Az po vyreseni soucasneho rozdilu mezi `main` a deploymentem zvazit jeden
  necitlivy read-only WebMCP pilot nad existujicim stavem pracovniho proudu.
- Upgrade Codex CLI provest samostatne s cilenym testem stdio i Unix-socket
  app-server transportu.

Zmenene nebo relevantni soubory:
- `memory/tvbcp/workstreams/project-samantha-infrastructure.md`
- `memory/tvbcp/architektura_komunikace_samantha.txt`
- `memory/infrastructure/operating_model.md`
- `memory/WORKSTREAMS.md`
- `memory/ACTIVE_PROJECTS.md`
- `app/communication/local_runtime.py`
- `app/codex_appserver.py`
- `app/communication/session_hub.py`
- `app/communication/human_adam_workstream_catalog.py`
- `app/communication/human_adam_workstream_memory.py`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice, soukromy obsah ani identifikatory vlaken.
- App-server nevystavovat primo do site; vzdalene zpristupnovat pouze rizeny
  Cockpit.
- Nezaměnovat checkpoint, push a nasazeni a zadny z techto kroku nespoustet bez
  odpovidajiciho potvrzeni.
- Pri `delivery_unknown` pokyn automaticky neopakovat.

### Automatický checkpoint 2026-08-26 09:35 CEST

- Pracovní proud: `project-samantha-infrastructure`
- Hotovo: Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/memory/handoffs/workstreams/project-samantha-infrastructure.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-samantha-infrastructure.md`
- Commit: `Založit kanonickou paměť Samantha Infrastructure`
- Další krok: Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav
