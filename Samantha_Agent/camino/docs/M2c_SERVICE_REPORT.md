# M2c — provozní ovládání a vědomé povolení Vieweru

2026-09-26, Europe/Prague. **Lokální implementace, nikoli nasazení.**

## Výsledek a hranice

- Registrované `camino_service_*`: `status`, `install`, `start`, `stop`,
  `enable_viewer`, `disable_viewer`, `copy_reader`. Zapisující karty vyžadují
  potvrzení; CLI také `--confirm`. Žádná karta neprovádí push, instalaci iOS,
  změnu Serve/Funnel nebo odhalení tokenu ve výstupu.
- Jeden LaunchAgent `cz.pythonmf.camino.service`, loopback `127.0.0.1:8767`,
  prefix `/camino-api`. `install` vytvoří vypnutou definici; až `start` ji
  povolí a načte. `KeepAlive` žádá návrat procesu, prodleva 30 s omezuje smyčku
  při chybné konfiguraci. `stop` ji zakáže i pro další přihlášení a odpojí.
  Vlastnictví se ověřuje přes přesnou definici a cestu načtené úlohy.
- Zastavení nemění síť, neruší owner/reader tokeny a nic nemaže. Při ukončení
  může probíhající převod dobíhat; launchd má 330 s pro ukončení. Dokončení
  je potřeba ověřit stavem, ne jen přijetím požadavku na stop.
- Před upgradem SQLite metadat z verze 1/2 na **3** vzniká konzistentní kopie
  přes SQLite backup API, `quick_check`, SHA-256 a dokončovací účtenka. Kopie
  obsahuje potvrzený WAL. Neúspěšná kopie bez účtenky nezpustí migraci.
  Snímky jsou create-only v `pre-upgrade-snapshots` vedle metadata DB;
  nic se automaticky nemaže. Není to nezávislá záloha M3.
- Schéma 3 přidává jen `viewer_permissions`; v1 zároveň dostane audio layout
  z M2b. Server ID, epocha, kurzor, původní Trip, přesné upload operace a média
  zůstávají. Návrat starého serveru nad schéma 3 není podporovaný rollback.
- Souborový zámek drží nový server po celou dobu běhu. Provozní změny odmítají
  načtenou službu i otevřené DB starého procesu (kontrola `lsof`). Starý server
  musí být před přechodem zastaven; zámek jej zpětně nenaučí spolupracovat.
- Povolení cesty je samostatné offline rozhodnutí. Neopravujeme neměnný
  `create_trip` payload; jeho byte-exact retry se nezmění. Runtime vyžaduje
  explicitní novou grant položku, nestačí historické `viewer_enabled=true`.
  `Jen pro mě`, skryté položky, konflikt a obnova stále blokují výdej.
- Reader má oddělenou DB a náhodné heslo, Basic username `jana`. Odvolání
  zavře cestu a zneplatní reader tokeny. Znovupovolení vytvoří nové heslo;
  staré soukromé soubory zachová, ale neaktivuje. Kopírování pouze do schránky,
  nikdy do URL, Gitu ani výstupu. Již stažené cizí kopie nelze odvolat.
- Start a start po pádu read-only kontrolují Serve/Funnel. Při veřejném
  Funnelu nebo neznámém výsledku se nespustí. Samotný loopback není důkaz
  soukromí, pokud by jej už přeposílala veřejná proxy.

## Nasazovací postup — až po samostatném schválení

1. Zvolit ověřený, stabilní checkout nasazeného kódu a trvalé izolované Python
   prostředí s `camino/server/requirements.txt`; dosavadní `/private/tmp`
   prostředí je jen pro testy. FFmpeg musí být v `/usr/local/bin` nebo
   `/opt/homebrew/bin`. Cockpit nasazení a jeho `CAMINO_VIEWER_URL` jsou oddělené.
2. Registrovaně zastavit původní C05b službu a ověřit vlastnictví dat, přijaté
   položky a stav bez zapisovatele. **Nevytvářet nový prázdný archiv ani
   neměnit epochu.** Výběr skutečného zdroje a konkrétní cesty není tímto
   lokálním krokem proveden ani odsouhlasen.
3. Připravit soukromý adresář `~/Library/Application Support/PythonMF/Camino/Service`
   (700) a jeho `config.json` (600). Vyžaduje přesně následující pole; příklad
   používá zástupné hodnoty, není spustitelná živá konfigurace:

   ```json
   {
     "metadata_db": "/PRIVATE/EXISTING/metadata.sqlite",
     "auth_db": "/PRIVATE/EXISTING/owners.sqlite",
     "media_db": "/PRIVATE/EXISTING/media.sqlite",
     "media_root": "/PRIVATE/EXISTING/originals",
     "viewer_media_root": "/PRIVATE/SEPARATE/viewer-copies",
     "python": "/PERSISTENT/VENV/bin/python",
     "code_root": "/APPROVED/RELEASE/Samantha_Agent",
     "trip_id": "EXISTING_CANONICAL_UUID",
     "server_id": "EXISTING_CANONICAL_UUID",
     "epoch": "EXISTING_CANONICAL_UUID"
   }
   ```

   Databáze musí již existovat, soukromé cesty musí být kanonické, bez symlinků
   a mimo Git; originály a odvozeniny oddělené. Server ID/epocha/cesta se
   porovnají read-only. Existující owner DB musí mít aktivní token; byl-li
   dříve odvolán, nejdřív výslovně připravit nový přes existující offline
   `camino.server.admin`, nikoli znovu oživit starý token. Telefonu potom
   předat nové owner připojení; reader token k němu nikdy nepoužívat.
4. Schválit `camino_service_install`. Nevytváří Reader, nemigruje DB,
   nespouští proces. Případný starý nebo odlišný plist nepřepíše.
5. Samostatně schválit `camino_service_enable_viewer` pro vybranou cestu.
   V zastaveném stavu nejprve snapshot/upgrade, pak zavření brány, příprava
   hesla a teprve nakonec grant. Selhání nechává bránu zavřenou.
6. Schválit `camino_service_start`, provést `camino_service_status`.
   Stav rozlišuje konfiguraci, vlastněnou definici, načtení a běžící proces;
   **nepotvrzuje HTTPS, worker ani doručení dat**. Start bez Viewer grantu
   může obsluhovat owner API, nevydává však Janin obsah.
7. Samostatně nastavit/ověřit privátní Serve `/camino-api` na port 8767 se
   zachováním kořene Cockpitu; žádný Funnel. Tyto karty proxy neinstalují.
   Neznovuspouštět C05b acceptance start kvůli URL — založil by jiný běh.
   V tomto kroku nebyla připravena ani spuštěna živá proxy konfigurace.
8. V nasazeném Cockpitu nastavit `CAMINO_VIEWER_URL` na soukromou HTTPS
   adresu s `/camino-api/viewer/`; bez hesla/query. Po potvrzeném `copy_reader`
   předat Janě heslo soukromě, vyčistit schránku po použití. Její zařízení
   potřebuje odpovídající přístup do tailnetu; odkaz jej nezajišťuje.
9. Nejdřív server, potom samostatně schválená podepsaná aktualizace stejné
   iPhone aplikace z M2b. Jeden sdružený průchod podle M2b reportu a RT3/RT4.

Při odvolání: `stop` → ověřit zastavení → `disable_viewer` → případně `start`
jen owner API. Při opětovném povolení opět zastavit, povolit, spustit a předat
nové heslo. Nedělat souběžné operace. Konfiguraci neměnit za běhu.

Po přihlášení vlastníka se povolená služba může spustit; po restartu se
počítá s místním odemknutím/přihlášením. Spánek, síť a dostupnost Macu tento
LaunchAgent neřeší. Ani funkční proces není záruka nepřetržité dostupnosti.

## Ověření

- Plná projektová brána **1806/1806 PASS** (246,374 s jednotkové sady);
  syntaxe, bezpečnostní statika a whitespace PASS. Po závěrečné drobné
  úpravě CLI zopakovaný dotčený runtime modul a předcommitová statická brána.
- Cílená M2c offline sada: **17/17 PASS**. Layout/projekce společně s první
  verzí M2c sady 30/30 PASS; poslední test navíc chrání cizí načtenou službu.
- Izolovaný HTTP/worker/owner server: **22/22 PASS**, včetně odvolání cesty,
  zamítnutí staré URL a zachování zákazu `Jen pro mě` po opětovném grantu.
- Po drobné opravě pořadí CLI validace znovu celý dotčený runtime modul
  **7/7 PASS**, včetně nového testu, že help/chybný bind nezamykají ani
  nemigrují DB. Nedotčené HTTP/media testy se znovu neopakovaly.
- Skutečné launchd operace jsou v testech nahrazené; plist, přesné argv,
  potvrzení, stav a vlastnictví jsou synteticky ověřené. **Návrat skutečného
  procesu po pádu ani přihlášení tím nejsou PASS.**
- Neopakoval se Swift/iOS build: M2c nemění telefon. Předchozí M2b výsledky
  zůstávají historickým důkazem, ne novou fyzickou akceptací.
- Žádná skutečná DB migrace, kopie osobních dat, token, instalace LaunchAgentu,
  deployment, push, Serve/Funnel nebo iPhone změna nebyla provedena.

Další krok: schválit nasazovací přípravu a konkrétní existující zdroj dat;
pak krátké živé ověření včetně start/stop/návratu procesu. M3 a M4 zůstávají.

## Navazující příprava 26. 9.

Míla schválil přípravu nad stávajícím archivem a poté p+n. Registrované
`camino_service_prepare` ověří zastavený C05b zdroj, jedinou naplněnou cestu,
hash každého ověřeného média a všechny tři DB zkopíruje přes SQLite backup API.
Připraví neměnný release z čistého commitu, trvalé izolované prostředí podle
requirements a soukromou konfiguraci. Neodvolaný owner token zachová, jinak
vytvoří nový, ale nikdy neoživuje odvolaný. Bez readeru, migrace, startu či sítě.
Existující/neúplný adresář přípravy se automaticky nepřepisuje ani nemaže.

Živý audit zdroje: 104 operací, 41 Momentů, 45 ověřených médií, 214 555 219 B;
metadata/media SQLite quick_check OK, schéma 1. Dvě cesty, ale pouze jedna
obsahuje Momenty. Žádný konflikt. Po T058 trvají `reconciliation_required=1`
a `exports_blocked=1`; příprava ani nasazení je nesmí odblokovat. Viewer
není připravený pro Janu, dokud nebude vyřešená autorizovaná obnova s telefonem.

Nová instalace LaunchAgentu a změna Tailscale konfigurace podléhají přesné
větě z `global_safety_brake.md`; samotné p+n ji nenahrazuje. Běžný registrovaný
push a restart existujícího Cockpitu mohou proběhnout nezávisle.
Přípravná a provozní offline sada po doplnění: 20/20 PASS. Plná publikační
brána a skutečný výsledek přípravy se evidují až po provedení.
