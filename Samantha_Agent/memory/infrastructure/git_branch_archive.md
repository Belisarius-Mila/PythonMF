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

## 2026-11-12 — Dokončené historické větve

Míla výslovně zadal p+n všech dokončených commitů včetně Datových a úplný
úklid repa. Přesná věta globální brzdy již zazněla v této relaci. Odstraněné
byly pouze níže vyjmenované refy, jejichž přesný tip je předkem main. Vzdálené
tipy byly znovu ověřené na GitHubu a jsou i předky origin/main72e1015c.
28 místních a11 vzdálených odkazů odstraněno, commity zůstávají v historii.
Před úklidem vytvořený a ověřený obnovitelný Git bundle a přesné účtenky:
data/private/email_followups_step4_20261112/ (mimo Git). Dva čisté pomocné
worktrees0729 a will-science mají pouze odpojenou dokončenou větev; všechny
jejich soubory včetně ignorovaných soukromých podkladů zůstaly zachované.
Aktivní Datova větev/worktree ebbd se nemění. Žádné mazání souborů/tagů,
reset, přepis historie nebo force push. Na GitHubu zůstává pouze main.
První vzdálený pokus prokazatelně selhal autentizací beze změn; dokončení
použilo již platné gh přihlášení podle LL-060 jen v jediném příkazu.

- `refs/heads/adam/email-followups-step1-20261111` → `0b6042ffa6890e89a331af34be1cc73e453c06d6`
- `refs/heads/adam/email-followups-ui-20261111` → `9d89446ba63f63d7ed6a08734269eba878c63324`
- `refs/heads/adam/human-adam-tool-compat-20261111` → `f6770814f3355899f30df5a1dfde9d9e3b59b121`
- `refs/heads/adam/interior-brief-release-81e34ae6` → `19703fdb5b842bf256ff095908f341da4e34aefe`
- `refs/heads/adam/interior-conversation-brief-20261110` → `448d2902c26bb68110acdf207ebf1b49c0176c4b`
- `refs/heads/adam/interior-empty-thumbnails-20261110` → `ba2f9bbc8748d3e6e9ce63e6d0aa8e014b247516`
- `refs/heads/adam/interior-proposal-titles-20261111` → `c7efd566ccf46b82da6ada5f8ff69e3f572831d1`
- `refs/heads/adam/interior-room-plan-20261110` → `4ea5b01ea327140868d06a0a65574c5ee941b894`
- `refs/heads/adam/interior-source-delete-20261110` → `748cec00c3ab4e4f873b911c5ceb3547e6659caf`
- `refs/heads/will/science-news-20261110` → `51a2cabeb587ca5a9db8ed5d9f591dec5c1947cd`
- `refs/heads/wip/development-branch-lifecycle-audit-20260719` → `92953398e583ac2bb9610ec0b013334a12dfa8b9`
- `refs/heads/wip/family-calendar-keychain-setup-20260723` → `59769f245f921b03d91df0425630a8aea21566c0`
- `refs/heads/wip/family-calendar-launchctl-load-20260724` → `9842ac54fb1308bd00ef5c90ef2d29ed3ec9c3da`
- `refs/heads/wip/family-calendar-launchctl-preview-20260723` → `4e0eddfdbd8a84394fefd654459eba55ca567837`
- `refs/heads/wip/family-calendar-planner-install-20260723` → `47548da933a573f25d224f9a14eb2f74e6f41957`
- `refs/heads/wip/family-calendar-planner-preview-20260723` → `57ad0ef3e11450c0567ca8bb45317300fe37e5a0`
- `refs/heads/wip/family-calendar-scheduled-runner-20260723` → `cf64d19be0489c887bc330d709bf3b6fb29bb48e`
- `refs/heads/wip/human-adam-plan-help-20260719` → `5052a4cb495c84786c4deb3170fe88c79111cc1a`
- `refs/heads/wip/human-adam-work-help-20260719` → `e1bc193da0eb92b84d7e602c7eddece7070859e8`
- `refs/heads/wip/human-adam-work-help-layout-20260719` → `20c64a742e40a561256472140d2f75ecff6401db`
- `refs/heads/wip/knihovna-direct-private-data-20260723` → `3783af622b3f0e787881b7fbbab4a74a25b3c902`
- `refs/heads/wip/project-bootstrap-phase0-20260719` → `dcdbbdd6e9134baf3b674d33bf66f5eb0e7b56b4`
- `refs/heads/wip/project-bootstrap-phase01-20260719` → `1735b2e44d92a92a49fd9618b2e741de38cbf878`
- `refs/heads/wip/project-continuity-help-20260719` → `19608fc2a6cdafec05801a428b6f522103508942`
- `refs/heads/wip/project-continuity-phase1-20260719` → `09c25f91eb2e6c7c22cfc640d2d4d4fc065b18c6`
- `refs/heads/wip/project-continuity-phase2-20260719` → `38046b475f5afbb3237f1bc485649d3b5c65f4af`
- `refs/heads/wip/project-continuity-phase3-20260719` → `33d0505b4e037eee767e8087e1d0554ea5f45ad0`
- `refs/heads/wip/project-continuity-phase4-20260719` → `34c60874640ec7e558a90426d9635bb9bca442d1`
- `refs/remotes/origin/wip/development-branch-lifecycle-audit-20260719` → `92953398e583ac2bb9610ec0b013334a12dfa8b9`
- `refs/remotes/origin/wip/human-adam-plan-help-20260719` → `5052a4cb495c84786c4deb3170fe88c79111cc1a`
- `refs/remotes/origin/wip/human-adam-work-help-20260719` → `e1bc193da0eb92b84d7e602c7eddece7070859e8`
- `refs/remotes/origin/wip/human-adam-work-help-layout-20260719` → `20c64a742e40a561256472140d2f75ecff6401db`
- `refs/remotes/origin/wip/project-bootstrap-phase0-20260719` → `dcdbbdd6e9134baf3b674d33bf66f5eb0e7b56b4`
- `refs/remotes/origin/wip/project-bootstrap-phase01-20260719` → `1735b2e44d92a92a49fd9618b2e741de38cbf878`
- `refs/remotes/origin/wip/project-continuity-help-20260719` → `19608fc2a6cdafec05801a428b6f522103508942`
- `refs/remotes/origin/wip/project-continuity-phase1-20260719` → `09c25f91eb2e6c7c22cfc640d2d4d4fc065b18c6`
- `refs/remotes/origin/wip/project-continuity-phase2-20260719` → `38046b475f5afbb3237f1bc485649d3b5c65f4af`
- `refs/remotes/origin/wip/project-continuity-phase3-20260719` → `33d0505b4e037eee767e8087e1d0554ea5f45ad0`
- `refs/remotes/origin/wip/project-continuity-phase4-20260719` → `34c60874640ec7e558a90426d9635bb9bca442d1`
