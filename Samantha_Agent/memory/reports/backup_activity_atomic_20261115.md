# Atomické uložení evidence zálohy — 2026-11-15 11:18 CET

Proud: project-samantha-infrastructure. Stav: místně dokončeno a ověřeno.
Míla schválil opravu; vývoj provedl hlavní Adam. Externí disk nebyl potřeba.

## Výsledek

Závěrečné uložení activity_state.json používá existující atomic_write_text.
Hotový text se uloží do samostatného dočasného souboru, zapíše na disk
fsync a atomicky nahradí položku v novém snapshotu přes os.replace.
Starší hardlinkované snapshoty si ponechají původní inode, obsah a mtime;
nová kopie má vlastní inode. Následný copystat zachovává režim a časy
kanonické evidence. Produkční změna je jen v app/backup/incremental.py, společné
ukládání v app/file_persistence.py se neměnilo.

## Ověření

- Dvě nové regrese před opravou FAIL a po opravě PASS. Volají skutečný
  run_backup v dočasném projektu se dvěma staršími hardlinkovanými kopiemi.
  Před závěrečným uložením výslovně potvrzují tři odkazy na stejný inode.
- Úspěšný běh zachová starší bajty/inode/mtime/režim, nová evidence má
  stejné bajty, režim a mtime jako zdroj, správný target a jediný link.
- Vynucené selhání nahrazení nechá původní úplný JSON i starší soubory
  neporušené; chyba se propaguje a dočasný soubor nezůstane.
- 43 cílených testů záloh, Camina a persistence PASS.
- Celá kanonická brána: 3940 testů, 0 chyb, 31 SKIP;
  jednotková část 780.013 s. Statické kontroly PASS.
  Dva otisky finálního kódu a testů stále shodné se začátkem plné brány.

## Hranice a další krok

Hotové místně pro příští spuštění registrovaného zálohovacího CLI, které
načítá modul z main v novém procesu. Žádná další ostrá záloha, čtení nebo
změna skutečných starých snapshotů v tomto vývojovém kroku neproběhly.
Předchozí ověřené recovery20261115_100224 a Camino20261115_102018-a9791da6
zůstávají platné; dnešní vývojový checkpoint je pozdější než tato záloha.

Další krok: při příští pravidelné recovery záloze převzít novou účtenku a
ověřit starší evidenci. Tato přejímka skutečného nového snapshotu zatím
neproběhla. Push a runtime deploy jsou samostatné kroky.

Důkaz mimo Git: data/private/backup_activity_atomic_20261115/full_gate.log,
unit_timings.json a source_manifest.json. Žádný soukromý obsah ani tajemství
nepatří do tohoto reportu. Zkoušky používají jen dočasné syntetické soubory.
