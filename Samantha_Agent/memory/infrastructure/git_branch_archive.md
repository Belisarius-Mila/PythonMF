# Git branch archive

Tento soubor drzi rozhodnuti o vetvich, ktere byly po auditu uzavrene. Aktivni
archivovane neintegrovane vetve se zapisují jako odrazkove radky s presnym nazvem
v backticku; `scripts/git_safety_check.py` je pak bere jako vedome osetrene.

## Aktivni archivovane neintegrovane vetve

Zadne.

## Smazane vetve

- smazano 2026-07-19: `ready/active-profile-connect-sync-20260718`
- smazano 2026-07-19: `ready/thread-rotation-api-20260719`
- smazano 2026-07-19: `ready/thread-rotation-api-20260719-v2`
- smazano 2026-07-19: `wip/active-profile-connect-sync-20260718`
- smazano 2026-07-19: `wip/global-development-semaphore-20260719`
- smazano 2026-07-19: `wip/thread-rotation-20260718`
- smazano 2026-07-19: `wip/thread-rotation-api-20260719`
- smazano 2026-07-19: `origin/wip/global-development-semaphore-20260719`
- smazano 2026-07-19: `origin/wip/thread-rotation-20260718`
- smazano 2026-07-19: `origin/wip/thread-rotation-api-20260719`
- smazano 2026-07-13: `wip/voicebridge-freeze-2026-07-12`
- smazano 2026-07-13: `origin/wip/voicebridge-freeze-2026-07-12`
- smazano 2026-06-26: `cursor/matysek-scene02-mossy-stump-prototype`
- smazano 2026-06-26: `origin/cursor/matysek-scene02-mossy-stump-prototype`

Rozhodnuti 2026-07-19:

- Vsechny tri pomocne worktrees byly pred odstranenim ciste, bez staged,
  unstaged i untracked souboru.
- Active-profile sync je zachovany v historii `main` bodem `afb82e3`.
- Finalni profilova rotace je zachovana v `main` bodem `424d003`; starsi backend
  a API checkpointy mely v relevantnim kodu a testech stejny vysledny obsah.
- Globalni vyvojovy semafor je zachovany v `main` bodem `90ed06c` a jeho
  deploymentovy zaznam bodem `7515d91`.
- Pred smazanim byly lokalni `main` a `origin/main` shodne. Lokalni i vzdalene
  refy byly smazany az po presnem potvrzeni globalni brzdy; `main`, tagy,
  soukroma data ani jine pracovni plochy se nemenily.

Rozhodnuti 2026-07-13:

- WIP vetev obsahovala fail-closed zmrazeni stareho VoiceBridge a overeny
  read-only zaklad noveho app-server LABu.
- Cela jeji historie byla sloucena do `main` merge commitem `581f985` a
  `main` byl pred smazanim overen proti `origin/main`.
- Lokalni i vzdaleny WIP ref byly po vyslovnem potvrzeni globalni brzdy smazany;
  zadne soubory, tagy ani commity se nemazaly.

Audit:

- `memory/reports/git_branch_audit_cursor_matysek_scene02_2026_06_26.md`

Rozhodnuti 2026-06-26:

- Prevedeno na `main`: voice bridge stale session fix, Cockpit restart/voice cleanup, Quick Notes preclassification, Knihovna read-state/queue/source URL a generator systemoveho projektoveho auditu.
- Uz drive nahrazeno na `main`: jadro `Lekarna - sprava`, sifrovany web bundle, abecedni razeni, ColorsAndNumbers cache bump a MMTX cesta k jezeru.
- Neprebirat vcelku: MMTX prototyp a velke assety, PTKL prototyp a audio, stare ColorsAndNumbers denni audio, memory housekeeping a konfliktní Lekarna UX follow-upy ze stare smichane vetve.
- Lokalni i remote vetev byly po tomto rozhodnuti smazane; detail zustava v auditnim reportu.
