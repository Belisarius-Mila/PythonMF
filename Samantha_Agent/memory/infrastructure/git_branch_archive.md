# Git branch archive

Tento soubor drzi rozhodnuti o vetvich, ktere byly po auditu uzavrene. Aktivni
archivovane neintegrovane vetve se zapisují jako odrazkove radky s presnym nazvem
v backticku; `scripts/git_safety_check.py` je pak bere jako vedome osetrene.

## Aktivni archivovane neintegrovane vetve

Zadne.

## Smazane vetve

- smazano 2026-06-26: `cursor/matysek-scene02-mossy-stump-prototype`
- smazano 2026-06-26: `origin/cursor/matysek-scene02-mossy-stump-prototype`

Audit:

- `memory/reports/git_branch_audit_cursor_matysek_scene02_2026_06_26.md`

Rozhodnuti 2026-06-26:

- Prevedeno na `main`: voice bridge stale session fix, Cockpit restart/voice cleanup, Quick Notes preclassification, Knihovna read-state/queue/source URL a generator systemoveho projektoveho auditu.
- Uz drive nahrazeno na `main`: jadro `Lekarna - sprava`, sifrovany web bundle, abecedni razeni, ColorsAndNumbers cache bump a MMTX cesta k jezeru.
- Neprebirat vcelku: MMTX prototyp a velke assety, PTKL prototyp a audio, stare ColorsAndNumbers denni audio, memory housekeeping a konfliktní Lekarna UX follow-upy ze stare smichane vetve.
- Lokalni i remote vetev byly po tomto rozhodnuti smazane; detail zustava v auditnim reportu.
