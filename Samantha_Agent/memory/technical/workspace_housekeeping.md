# Úklid dočasných pracovních kopií

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
