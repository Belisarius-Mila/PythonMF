# Úklid SSD a recovery záloha — 2026-11-15 10:34 CET

Proud: project-samantha-infrastructure. Stav: dokončeno a ověřeno.
Míla zadal úklid před zálohou a výslovně potvrdil globální brzdu pro přesný rozsah.

## Výsledek

- Odstraněno osm schválených čistých pracovních kopií se všemi commity v main;
  Gitové větve zachované, aktivní Data a jeho další větve nedotčené.
- Před odstraněním zachováno a ověřeno SHA-256 15 048 potřebných ignorovaných
  souborů a odkazů mimo obnovitelné cache; soukromé účtenky zůstávají mimo Git.
- Odstraněno přesně 18 schválených starých autosave souborů; aktuální a předchozí
  obnova i nejméně 12 časových snapshotů zachované. Při závěru jich bylo 13.
- Skutečný zisk SSD 12,66 GiB: 23,03 → 35,69 GiB v měřeném intervalu úklidu.
  Při dokončení zálohy volno 34.29 GiB; souběžný provoz pokračoval.

## Dokončená šifrovaná záloha

- Projektový snapshot `20261115_100224`: 139 871 souborů, 67 586 nově
  kopírovaných, 72 096 hardlinků a 189 symlinků; 0 přeskočených.
  Nově kopírovaných 8 794 670 962 B projektové části.
- Živé Camino `20261115_102018-a9791da6`: 1 647 souborů / 5 167 041 733 B,
  čtyři SQLite DB, 316 originálů / 2 379 212 189 B. Registrovaný program ověřil
  všechny soubory, DB integritu i mediální účtenky před dokončením.
- Skutečně připojený šifrovaný cíl ověřen před/po. Na něm při závěru
  381.60 GiB volných. Manifesty a recovery návod existují.
- Pět reprezentativních SHA-256 odpovídá zmrazenému začátku běhu; čtyři
  necitlivé soubory skutečně obnovené do nového soukromého dočasného adresáře.
  Soukromá .env ověřená pouze shodou; její obsah ani hash do tohoto zápisu nepatří.
- Codex auth.json a nouzové data/session_autosave vyloučené. Git connectivity
  kontrola PASS. Camino opět vlastněné/running a owner health PASS; Cockpit
  stejný PID/stamp, jeden zdravý čerstvý autosave watcher. backup_status potvrzuje 15.11.

## Souběh a hranice

Výchozí main byl2779af14. Během běhu Data přidal čistě dokumentační0601ecba
k dokončenému Vocabulary EN vydání. Pět kontrolovaných souborů ve snapshotu
odpovídá výchozím hashům; aktuální MEMORY_INDEX se mezitím změnil. Kopie Gitu
již obsahuje0601ecba i jeho předka2779af14, mezi nimi pouze pět memory souborů.
Nejde o atomický obraz všech souběžně měněných projektových souborů ani celého Macu.
Kód a produkční média tento souběžný commit nemění. Tento výsledkový zápis je
následný lokální dokumentační checkpoint a není součástí předchozího snapshotu.

## Otevřená oprava před další zálohou

Při tomto běhu potvrzeno, že nová kopie data/backup/activity_state.json sdílela
inode se33 staršími snapshoty (34 hardlinků včetně nové kopie). Zálohovací program
po record_backup_completed přepisuje cíl přes wb; bez oddělení by změnil starou evidenci.
V novém snapshotu proto před dokončením atomicky nahrazena pouze tato položka
samostatnou kopií se stejnými bajty. Obsah i mtime všech33 starších souborů
před/po shodné, nový cíl má jeden link a aktuální správnou evidenci.
Produkční kód zálohování se neměnil. Před dalším během trvale opravit atomické
nahrazení cíle; dnešní mitigaci nepovažovat za nasazenou opravu programu.

Soukromé důkazy: data/private/ssd_cleanup_20261115/receipt.json a completion.json;
data/private/backup_recovery_20261115/verification.json, activity_state_isolation.json,
execute.log, snapshot_git_connectivity.log. Žádný nový push nebo deploy v tomto kroku.
