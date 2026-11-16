# Úklid dočasných pracovních kopií

## Schválená v2 — 2026-11-16

Míla po konkrétním auditu schválil širší úklid, zobrazení velikostí vpravo,
vývoj i p+n. Navazuje na potvrzenou globální brzdu v této relaci. Souhlas
platí pro níže vymezený rozsah, nikoli pro všechny soukromé či externí zálohy.

V2 je samostatný registrovaný PublishedCleanup.prepare/activate; běžné nasazení
kódu nepřepne již aktivní v1. Prepare potřebuje čistý publikovaný main,
zmrazí kořeny, otisky kopií, kód i limit zachování. Activate vyžaduje jeho
SHA-256, globální větu a referenci konkrétního souhlasu. Stávající LaunchAgent
se nepřepisuje ani nerestartuje. Policy_version2 se ukládá atomicky.

- Jen explicitně uzavřené přímé data-* worktrees stejného repozitáře;
  main, stálý Data a provozní profily zůstávají chráněné. Před reuse cancel.
- Po ověřeném push/deploy registrovaný vykonavatel spustí již autorizovaný
  úklid označených kopií; hodinový tick je záloha. Neoznačená nová práce
  se podle pouhé nečinnosti automaticky neuzavírá.
- Vyžaduje čistý main shodný s origin/main a začleněný HEAD kopie. Obsah
  dosažitelný z historie main se znovu nekopíruje; jeho blob/path reference
  zůstává v kompaktním manifestu. Samotná čistota Gitu neprokazuje soukromá data.
- Odlišné pracovní i připravené verze se uchovají zvlášť ve verificovaném
  soukromém content-addressed archivu, nejvýše100MiB unikátů na kopii.
  Komprimovaný manifest drží cesty, módy a reference. Jednotlivé obsahy,
  hashe a soukromé cesty se nezveřejňují a nepatří do Gitu.
- Teprve po ověření archivu a novém otisku kopie se normalizují zachované
  změny přes git restore na původní HEAD a provede git worktree remove
  bez force. Větve se nemažou. Chyba po zahájení odstranění zůstane attention,
  bez automatického opakování; evidence má přesnou fázi selhání.
- .build je regenerovatelná cache uvnitř dočasné kopie. Navíc lze odstranit
  jen .build pod dvěma zkontrolovanými starými archivy:
  private/ssd_cleanup_20261115/preserved a
  private/focused_pn_cleanup_20261115/retired_worktree_data.
  Ostatní archivované soubory a aktivně používané cache zůstávají.
- Autosave: latest/previous + dva nejnovější hodinové časy. Staré číslované
  varianty latest/previous_session/info se odstraňují jen podle přesné masky;
  obsah se nečte. Chybějící či stará současná obnova blokuje retenci.
  Nepublikovaný nový vývoj odloží úklid pracovních kopií, nikoli retenci.

Cockpit vpravo uvádí GiB i u ponechaných kopií a zachovaných archivů;
neověřená velikost zůstává neověřená. Jde o alokované bloky se zohledněním
hardlinků, ne příslib skutečného zisku. Ten změří disk_usage před/po.
Aktuální živý plán, aktivace a úklid mají oddělené soukromé účtenky ve
workspace_housekeeping. Nejasné případy a větší unikáty zůstávají ke kontrole.

Následující část uchovává původní v1; účinnou verzi určuje activation.json.

## Čtecí karta v Cockpitu — 2026-11-16

Servis → Provoz → Úklid pracovních kopií má místně připravenou kartu:
stav plánovače, poslední běh, skutečná změna volného místa a seznam čekajících,
ponechaných a neuzavřených kopií s českými důvody. GET /api/workspace-housekeeping
vrací jen redigovaný stav; ?refresh=1 žádá nové čtecí ověření. POST ani parametry
pro mazání nejsou podporované. Registrovaná schopnost workspace_housekeeping_status.
GET nic nezapisuje a nikdy nevolá tick/retire/activate ani model.

Pomalé SHA-256/Git/procesové ověření běží v jediném pozadí v rámci serveru,
výsledek se nejvýše5min drží v paměti. Načítání není nulový počet kopií;
stará nebo neověřená data jsou označená. Obnova přehledu je čtecí tlačítko,
automatické načítání/poll pouze při otevřeném Servis → Provoz.
Prázdná fronta nezamlčí neuzavřené kopie mimo frontu. Nezobrazují se absolutní
cesty, soukromé obsahy, jednotlivé hashe ani aktivační údaje.
Tato karta nemění schválenou aktivaci ani rozsah pravidelného mazání.
Kód karty a provozní nasazení jsou samostatné; stav vydání je v aktuálním
handoffu/development.json, samotný tento návod nedokládá nasazení.

Proud: project-samantha-infrastructure. Autor: Adam. Návrh schválen Mílou
16.11.2026 („Jdeme na Wille, Warp 5.“); aktivace služby je samostatná.

## Rozsah

Pro běžné pokračování používej stálou pracovní kopii Data. Další úplný worktree
vytvářej jen pro potřebnou izolaci; po začlenění dokončené práce do main ho
výslovně uzavři. Čistý Git sám nedokládá dokončení práce.

Registrované Python operace jsou v app.worktree_cleanup.Housekeeping:

- preview(): pouze čte Git, metadata, otevřené soubory; shodu potřebných
  ignorovaných kopií ověřuje lokálním SHA-256 bez výpisu obsahu či jednotlivých hashů.
- retire(name, expected_head=...): označí přesný čistý začleněný worktree jako
  dokončený, zmrazí identitu/head/branch/inventář; nemaže. Běží hodinová ochranná lhůta.
- cancel(name): zruší označení před dalším použitím. Při nejasném mazání se
  práce neobnovuje do původního adresáře; stav musí nejprve ručně ověřit Adam.
- tick(): bez dřívější aktivace nic nemaže. Zpracovává pouze uzavřené kopie,
  znovu ověří celý rozsah a maže výhradně přes git worktree remove bez force.

Povoleny jsou jen přímé `data-*` linked worktrees pod ~/.codex/worktrees,
patřící ke stejnému hlavnímu repozitáři. Main, stálý Data v ebbd, provozní profily,
worktrees v data/private a ostatní adresáře jsou mimo rozsah. Větve se nemažou.
Používaný/locked/dirty/nezačleněný či od uzavření změněný worktree zůstává.
Ignorované soubory jsou buď regenerovatelné cache podle pevného seznamu v kódu,
nebo musí mít přesně ověřenou pravidelnou kopii na stejné relativní cestě v main.
Neznámá data a symlinky úklid blokují. Neprovádí se automatické přesouvání soukromých dat.

## Autosave

Tentýž hodinový tick drží 12 nejnovějších časů historických JSONL/TXT snapshotů.
Latest, previous a všechny nestandardní názvy zůstávají. Bez čerstvé ne-prázdné
aktuální a předchozí obnovy se historie nezmenšuje. Obsah autosave se nikdy nečte.
Soubory se znovu ověřují před unlink; symlinkovaný adresář ani soubory se nepoužijí.
Běžící autosave watcher a jeho LaunchAgent se nemění ani nerestartují.

## Aktivace

Pevné shell workflow jsou workspace_housekeeping_preview/prepare/status:
`.venv/bin/python scripts/workspace_housekeeping.py preview|prepare|status`.
Prepare zapisuje pouze soukromý návrh, digest přesného zdroje a rozsahu; nic neaktivuje.
Registrované scripts.workspace_housekeeping.activate vyžaduje shodný
proposal_sha256 a přesnou větu z global_safety_brake.md:

`Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.`

Jde o nový LaunchAgent a trvalé oprávnění k popsanému mazání, nikoli opakování
dříve schváleného jednorázového úklidu. Starý souhlas k jinému rozsahu se nepřenáší.
Po schválení se instaluje jediný nový com.samantha.workspace-housekeeping,
StartInterval3600/RunAtLoad, bez KeepAlive. Existující plist/job se nepřepisuje.
Před bootstrap se ukládá pokus a souhlas; nejasná aktivace se neopakuje.
Případná ruční obnova či deaktivace služby podléhá samostatnému konkrétnímu pokynu.

Private workspace_housekeeping/state.json uchovává stav uzavřených kopií;
latest.json má poslední výsledek, důvody blokování a skutečnou změnu volného místa
před/po. Přerušené či nepotvrzené mazání přechází do attention a automaticky
se neopakuje. Pouhá nízká kapacita SSD nikdy nerozšíří schválený rozsah.
OS swap, CloudKit, zálohy, rodinná média a Gitové větve se neuklízejí.

## Ověření a omezení

Syntetické testy používají vlastní dočasné Git repozitáře a skutečné odstranění
jen těchto fixtures. Živý preview ani prepare nemažou. Před aktivací se předloží
aktuální náhled; existující problematické kopie vyžadují zachování dat/uzavření práce.
Otevřené soubory ověřuje lsof; chyba auditu blokuje. Všichni autoři musí před
opětovným použitím uzavřené kopie zavolat cancel; dokončení není pouze čas nečinnosti.
Součet st_blocks není příslib uvolnění kvůli APFS; důkazem je rozdíl disk_usage.
