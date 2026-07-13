Nazev: App-server Adam Remote - izolovana zapisujici Work Cell v0
Priorita: 1
Stav: ceka na rucni iPhone retest
Pripomenout pri startu: ano
Datum: 2026-07-13

Co se resilo:
- Mila potvrdil, ze read-only LAB pres Tailscale funguje jako spojeni spolehlive,
  ale cil je skutecna vzdalena tvoriva prace, ne jen chat.
- Runtime audit nainstalovaneho Codex app-serveru potvrdil efektivni model
  `GPT-5.6-Sol`, podporu reasoning `low` az `ultra` a lokalni konfiguraci `high`.
- Puvodni LAB klient vsak kazdy turn explicitne prepisoval na `low`, read-only
  sandbox a zakaz nastroju. To vysvetluje plossi obsah bez dukazu slabsiho modelu.

Co je hotove:
- Puvodni read-only LAB zustava beze zmeny jako overena komunikacni a
  diagnosticka cesta.
- Nova `RemoteWorkspaceManager` pripravuje samostatny lokalni clone celeho
  `PythonMF` z commitnuteho `main` pres `--no-hardlinks`.
- Clone neobsahuje ignorovana `data/private/` ani nezarazene soubory hlavniho
  stromu a po vytvoreni nema zadny Git remote.
- Adam Remote pouziva explicitni model z runtime konfigurace, reasoning `high`,
  sandbox `workspace-write`, sit vypnutou a approval policy `never`; eskalace
  mimo izolovany workspace tedy nema kam projit.
- Developer instrukce vyzaduji AGENTS, MEMORY_INDEX, relevantni handoff, zakazuji
  sit, push, zmenu remote, destruktivni git a praci mimo izolovanou kopii.
- Cockpit ma samostatne tlacitko a modal `Adam Remote`, skutecny profil modelu,
  stav oddeleneho Git stromu, seznam zmenenych souboru, Context Capsule, pracovni
  chat, rucni TVBCP zapis a potvrzovany lokalni WIP checkpoint bez pushnuti.
- Checkpoint pred commitem odmita private, autosave, `.env` a binarni/media
  soubory; neznamou nebo castecne vytvorenou cilovou slozku nikdy neprepisuje
  ani nemaze.
- App-server klient ma obecny execution profil; vychozi parametry stareho LAB
  zustaly zpetne kompatibilni.
- Cileny blok dokoncil 263 testu a plna Cockpit quality gate 644 testu bez chyby.
- Zivy canary pres skutecny app-server uspesne dokoncil zapis s profilem
  `gpt-5.6-sol`, reasoning `high`, `workspace-write` a vypnutou siti.
- Kontrolni soubor vznikl pouze v ignorovanem private prostoru izolovane kopie,
  mel presny ocekavany obsah a v hlavnim projektu nevznikl.
- Po canary zustala izolovana Git kopie cista, bez Git remote; zdrojovy HEAD se
  nezmenil a odpovidal zakladnimu commitu kopie.
- Cockpit byl pote restartovan s aktualnim code stampem, karta `Adam Remote` je
  dostupna lokalne i pres Tailscale a ulozeny thread se uspesne znovu pripojil.
- Nasazeny status znovu potvrdil `GPT-5.6-Sol`, reasoning `high`,
  `workspace-write`, vypnutou sit, cisty workspace a prazdny seznam Git remote.
- Pri prvnim iPhone retestu Mila nahlasil neukoncene opakovane nacitani. Server
  ani Tailscale nebyly spadle, ale frontend nemel timeout hlavniho ani Remote
  statusu a start mohl soubezne spustit dva e-mailove intake scany bez timeoutu.
- Stabilizacni oprava nastavuje hlavni status na 15 s, Remote status na 12 s,
  e-mailovy scan na 30 s a deduplikuje soubezny Remote refresh i e-mailovy scan.
  Plna Cockpit quality gate po oprave znovu prosla vsech 644 testu.
- Oprava je nasazena s code stampem `6402cd5e478fab4a`; Tailscale mereni po
  restartu: HTML 0,03 s, health 0,005 s, hlavni status 1,65 s a Remote status
  1,09 s. Ulozeny Remote thread je znovu pripojeny.
- Nasledny retest na Macu i iPhonu ukazal, ze timeouty nebyly hlavni pricinou:
  novy Remote UI blok mel v renderovanem JavaScriptu neescapovany novy radek,
  ktery zpusobil syntaktickou chybu celeho Cockpit skriptu. Serverove endpointy
  proto odpovidaly, ale frontend se vubec nespustil.
- Escapovani je opravene a quality gate nove kontroluje primo kompletni
  renderovany JavaScript prikazem `node --check -`. Gate po teto oprave prosla
  645 testu a samostatne hlasi `javascript syntax: OK`.
- Oprava je nasazena s code stampem `a493500b971eb5de`; stejna JavaScript
  kontrola prosla i nad HTML zive stazenym z Tailscale adresy. Remote thread je
  pripojeny, workspace cisty a bez Git remote. Ceka se na novy iPhone retest.
- Mila pote z iPhonu uspesne dokoncil nekolik Remote turnu a tri rucne ulozil do
  TVBCP. Dulezity navod k ovladani a rozhodnuti o dalsim vyvoji byly doplneny do
  private TVBCP; protokol se necommitoval.
- Nova potvrzovana akce `Aktualizovat z main` synchronizuje pouze cisty
  izolovany workspace z commitnuteho lokalniho `main` pres fast-forward a bez
  trvaleho Git remote, site, merge commitu nebo pushnuti.
- Akce fail-closed odmita dirty workspace, jinou vetev, divergenci, zmenu main
  behem pripravy, private/env/media cestu a vsechny mazaci, prejmenovaci nebo
  netypicke Git zmeny. Po aktualizaci overi shodu HEAD, cisty strom a zadny
  remote. Pracovni turn je pri zastaralem zakladu v UI zablokovany.
- Osm realnych Git testu pokryva fast-forward i odmitnuti nepotvrzeneho, dirty,
  diverged a mazaciho scenare; HTTP/UI testy pokryvaji novou routu a tlacitko.
  Plna gate ma 650 testu a `javascript syntax: OK`.

Co neni hotove:
- Chybi kratky rucni iPhone retest nasazeneho Cockpit rozhrani a prvni maly
  realny ukol, pri kterem se zkontroluje viditelny diff pred checkpointem.
- Cockpit zatim nezobrazuje jednotlive tool eventy ani nema interaktivni approval
  round-trip. Proto v0 nema sit ani opravneni mimo izolovany workspace.
- Automaticky prenos WIP commitu z kopie na hlavni `main` zatim neni povoleny;
  nejdrive se ma zobrazit diff a predani ma zkontrolovat hlavni Adam.

Dalsi krok:
- Nasadit `Aktualizovat z main`, synchronizovat cisty workspace, aktualizovat
  Context Capsule a z iPhonu provest maly nedestruktivni ukol; pred checkpointem
  rucne zkontrolovat seznam zmen a diff.

Navrhovane dalsi kroky:
- Rucne z iPhonu zadat prvni maly realny kodovy ukol a overit zmeny/testy/TVBCP.
- Dodelat asynchronni tool-event timeline a potvrzovaci kartu pro rizikove akce.
- Pridat kontrolovane tlacitko `Predat hlavnimu Adamovi`, ktere pripravi diff,
  handoff a navrh prevzeti na `main`, ale nic samo nepushne ani neslouci.
- Voice rezim B pozdeji smerovat do stejneho app-server threadu jako alternativni
  vstup/vystup, ne do TTY/screen bridge.

Zmenene nebo relevantni soubory:
- `app/codex_appserver.py`
- `app/codex_appserver_lab.py`
- `app/remote_work_cell.py`
- `app/cockpit.py`
- `tests/test_codex_appserver.py`
- `tests/test_remote_work_cell.py`
- `tests/test_cockpit.py`
- `scripts/cockpit_quality_gate.py`

Bezpecnost / neukladat:
- Necommitovat skutecny remote workspace, remote state, runtime thread/turn ID,
  obsah chatu, TVBCP, `data/private/`, autosave, `.env`, tokeny ani API klice.
- Hlavni nezařazeny soubor `AuditCockpit56_M.txt` nepatri do clonu ani commitu.
- Zadny automaticky push, merge, cherry-pick, mazani nebo prepis hlavniho stromu.
