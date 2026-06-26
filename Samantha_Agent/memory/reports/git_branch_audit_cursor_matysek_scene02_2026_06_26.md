# Audit neintegrovane vetve cursor/matysek-scene02-mossy-stump-prototype

Datum: 2026-06-26
Zaklad: `main`
Auditovana vetev: `cursor/matysek-scene02-mossy-stump-prototype`
Remote vetev: `origin/cursor/matysek-scene02-mossy-stump-prototype`

## Proc audit vznikl

Na teto vetvi vznikla funkcionalita `Lekarna - sprava`, ale nebyla sloucena do
`main`. Commit byl pushnuty, jen zustal na vedlejsi vetvi. Po publikaci z
`main` se proto funkcionalita ztratila z bezneho provozniho stavu.

Hlavni pouceni: jedna vetev nesmi dlouhodobe obsahovat nesouvisejici praci.
Tato vetev smichala MMTX, Lekarnu, Cockpit, voice bridge, ColorsAndNumbers,
PTKL, Knihovnu a Quick Notes.

## Stav podle gitu

- `main` byl pri auditu cisty a zarovnany s `origin/main`.
- Pri prvnim auditu zustavala lokalni i remote varianta:
  - `cursor/matysek-scene02-mossy-stump-prototype`
  - `remotes/origin/cursor/matysek-scene02-mossy-stump-prototype`
- Lokalni vetev ma navic commit `4fdd9f2 Publish MMTX lake path fix`.
- `git cherry -v main cursor/matysek-scene02-mossy-stump-prototype` oznacil
  jako patch-ekvivalentne prevedene jen tri commity:
  - `6b7a5ce Update encrypted pharmacy web bundle`
  - `94a2a4e Sort pharmacy medicine lists alphabetically`
  - `a39ecd2 Bump ColorsAndNumbers app cache for June 25 owl`
- Po selektivnim prevodu bezpecnych casti a archivnim rozhodnuti byly 2026-06-26
  lokalni i remote vetev smazane.

## Uz prevedeno na main

- Voice bridge stale session fix:
  - puvodne `217a1d4 Hide stale processed voice pending messages`
  - puvodne `0d7f58b Avoid stale Codex voice delivery targets`
  - prevedeno 2026-06-26 cherry-pickem do `main`.
- Cockpit restart / voice playback cleanup:
  - puvodne `a8e1626 Fix Cockpit restart and voice playback`
  - puvodne `9734843 Wait for Cockpit before restart reload`
  - puvodne `2137fa5 Document Cockpit restart retest`
  - prevedeno 2026-06-26, konflikt v `ACTIVE_PROJECTS.md` byl sloucen rucne bez vraceni stareho MMTX navazani.
- Quick Notes:
  - puvodne `dbdf27f Use action preclassification for Quick Notes triage`
  - prevedeno 2026-06-26.
- Knihovna / knowledge workflow:
  - puvodne `ccc5740 Add library read-state workflow`
  - puvodne `6a3ac25 Improve library read queue visibility`
  - puvodne `5084ec4 Add library source URL button`
  - prevedeno 2026-06-26; konflikty s Lekarna admin testy byly sloucene rucne.
- Systemovy projektovy audit:
  - puvodne `bebd37c Add project audit system report generator`
  - generator preveden 2026-06-26.
- Lekarna sprava / import:
  - puvodne `bfd7dd3 Add pharmacy admin import workflow`
  - prevedeno do `main` jako `a3e3811 Restore pharmacy admin cockpit app`
- Lekarna web bundle:
  - `6b7a5ce Update encrypted pharmacy web bundle`
  - ekvivalent je na `main` jako `f721fa8 Update encrypted pharmacy web bundle`
- Abecedni razeni Lekarny:
  - `94a2a4e Sort pharmacy medicine lists alphabetically`
  - ekvivalent je na `main` jako `2ae8dc7 Sort pharmacy medicine lists alphabetically`
- ColorsAndNumbers cache bump:
  - `a39ecd2 Bump ColorsAndNumbers app cache for June 25 owl`
  - ekvivalent je na `main` jako `8f059f1 Bump ColorsAndNumbers app cache for June 25 owl`
- MMTX cesta k jezeru:
  - lokalni commit `4fdd9f2 Publish MMTX lake path fix`
  - provozni oprava byla publikovana na `main` jako `c803126 Publish MMTX scene 2 lake path`
  - neni patch-ekvivalentni podle gitu, ale tematicky patri mezi uz prevedene/nahrazene.

## Jeste prevest nebo samostatne posoudit

Tyto polozky nejsou bezpecne mergeovatelne jako celek. Pokud jsou stale
potreba, prenest je po samostatnych tematickych vetvich nebo cherry-pickem
po rucnim review.

- Lekarna admin UX navazujici opravy:
  - `82b215b Simplify pharmacy import publishing workflow`
  - `ab26b4b Fix pharmacy admin import visibility`
  - `441c50b Force pharmacy admin to open import workflow`
  - `cdc0dfd Avoid stale pharmacy admin popup state`
  - `4d33743 Make pharmacy admin default to import only`
  - duvod: pri cherry-picku 2026-06-26 konfliktovaly s aktualni bezpecnejsi obnovou Lekarna spravy; neprenaset vcelku.
- Knihovna / health info cast:
  - `92b0366 Checkpoint library health info and MMTX scene 2` pouze cast tykajici se knihovny
  - duvod: commit micha health info checkpoint s MMTX prototypem; prenaset jen po samostatnem review ChatGPT importu.
- Systemovy projektovy audit - Cockpit tlacitko:
  - `7cde624 Add Cockpit project audit report access`
  - duvod: generator je prevedeny, ale Cockpit tlacitko pri cherry-picku tahalo duplicitni starou Lekarna admin stranku; doplnit pozdeji ciste, pokud bude potreba.
- PTKL prototyp:
  - `8200d58 Add PTKL to be to have audio prototype`
  - `78621b5 Add PTKL app to cockpit catalog`
  - duvod: velke mnozstvi assetu a audia; prenaset jen pokud projekt pokracuje.

## Zahodit nebo archivovat

Neznamena fyzicky smazat bez souhlasu. Znamena neprebirat automaticky do
`main` a nechat jako historickou branch-only praci, dokud Mila nerozhodne jinak.

- Stare denni ColorsAndNumbers owl/audionahravky:
  - `019e0d9 Update June 25 owl speech`
  - `e21b44b Fix June 25 owl speech typo`
  - `9c2cc5b Update ColorsAndNumbers owl audio for June 25`
  - `e787da9 Fix June 25 owl speech cache reference`
  - duvod: `main` ma novejsi navazujici audio commity a cache bump.
- Handoff/memory housekeeping vztazene k uzavrenym stavum:
  - `a541428 Document verified Samantha backup snapshot`
  - `b3884ed Mark old cockpit recovery handoffs historical`
  - `d800f8e Hide completed recovery handoffs`
  - `b74a7ac Add pharmacy web sort handoff`
  - `cf5d41d Record pharmacy sort publication`
  - duvod: prebirat jen po rucnim porovnani memory, ne jako soucast smesne vetve.
- Puvodni MMTX Scene 2 prototyp a assety:
  - `7965783 Add standalone Scene 2 Mossy Stump Rest web prototype.`
  - `92b0366 Checkpoint library health info and MMTX scene 2` pouze cast tykajici se prototypu
  - `a208e8c Integrate MMTX scene 2 after scene 1`
  - duvod: `main` ma publikovanou navazujici opravu cesty k jezeru; starsi prototyp a velke audio/obrazky neprebirat bez samostatneho MMTX review.
- Cockpit audit priorita:
  - `8f9292c Prioritize cockpit functionality audit`
  - duvod: stav se prekryl aktualnim branch guard auditem.

## Navrhovany dalsi krok

1. Nemergovat celou vetev.
2. Vetev byla po auditu a selektivnim prevodu smazana lokalne i na `origin`.
3. `scripts/git_safety_check.py` ma branch guard s archivnim registrem:
   - nezname neintegrovane vetve dal hlasi jako riziko,
   - aktivni archivovane vetve umi brat jako vedome osetrene, pokud je nekdy bude potreba docasne ponechat.
4. Pokud se bude nekdy vracet PTKL, MMTX prototyp nebo Lekarna UX, zalozit novou
   cistou tematickou vetev a netahat znovu celou smichanou historii.
