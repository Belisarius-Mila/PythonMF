Nazev: Capability registry - dalsi maly krok po uklidu MMTX a git push guardu
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ne
Datum: 2026-06-26

Co se resilo:
- Mila odsouhlasil filozofii robustnejsi Samanthy bez zbytecne byrokracie:
  bezne read-only a nizkorizikove akce maji byt plynule, tvrdsi potvrzeni maji
  byt jen u veci, ktere se spatne vraci zpet.
- Konkretne bylo potvrzeno trvale pravidlo pro git:
  `git push origin main` muze po commitu probehnout bez dalsiho dotazu, pokud
  projde guard.
- Pred zmenou tematu byl uklizen aktualni stav po MMTX scene 2: repo bylo ciste
  na `main` a `origin/main`.

Co je hotove:
- Commit `6820aca Add routine main push guard` je pushnuty na `main`.
- Pribyl read-only skript `scripts/git_push_guard.py`.
- `memory/infrastructure/git_checkpoint_protocol.md` obsahuje pravidlo:
  push na `main` po commitu smi bez dalsiho dotazu, pokud guard projde.
- `memory/technical/codex_permissions_preferences.md` obsahuje stejnou preferenci
  pro low-friction provoz.
- Finalni kontrola po pushi hlasila cisty strom a `work_context_guard.py` hlasi
  `safe to switch topic`.

Co neni hotove:
- Skutecny capability registry v kodu jeste neexistuje.
- Zatim existuji jen starsi capability audit/mapovani a nova git push guard
  rutina.

Dalsi krok:
- Implementovat prvni maly capability registry bez velkeho prepisu:
  - datovy model capability zaznamu,
  - registry pro nekolik existujicich schopnosti,
  - read-only audit/test duplicit a rizikovych potvrzovacich pravidel.

Navrhovane dalsi kroky:
- Zacit soubory:
  - `app/capabilities/models.py`
  - `app/capabilities/registry.py`
  - `app/capabilities/policies.py`
- Prvni registry zaznamy:
  - `git_push_main_after_guard`
  - `work_context_guard`
  - `git_safety_check`
  - `quick_notes_action_status`
  - `send_prepared_email_draft` jen jako metadata, bez zmeny chovani.
- Prvni test:
  - zadne duplicitni `capability_id`,
  - rizika typu `external_send` nebo `destructive` musi mit potvrzovaci politiku,
  - `git_push_main_after_guard` musi vyzadovat predchozi zeleny guard.

Zmenene nebo relevantni soubory:
- `scripts/git_push_guard.py`
- `memory/infrastructure/git_checkpoint_protocol.md`
- `memory/technical/codex_permissions_preferences.md`
- `memory/technical/capability_routing_rules.md`
- `memory/technical/project_capability_map.md`
- `app/capability_audit.py`

Bezpecnost / neukladat:
- Do registry neukladat tajemstvi, tokeny, cele e-maily ani soukrome texty.
- Registry ma popisovat tridy schopnosti a rizika, ne konkretni citliva data.
- Push bez dalsiho dotazu zustava povoleny jen pro normalni `git push origin main`
  po zelenem guardu; force push, jina vetev, mazani vetvi/tagu a private data
  zustavaji blokovane.
