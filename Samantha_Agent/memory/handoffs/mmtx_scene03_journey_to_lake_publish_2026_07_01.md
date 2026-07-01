Nazev: MMTX Scene 3 Journey to the Lake publish
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-01

Co se resilo:
- Dodelani, retest a publikace webove Forest Journey sceny 3 `Journey to the Lake`.
- Scena navazuje ze `Scene 2 - Sunny's Lost Nuts` pres dokoncovaci bublinu `Next: Journey to the Lake`.

Co je hotove:
- Scene 3 je zalozena v `docs/scene03_journey_to_the_lake/` a mirroru `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/`.
- Obsahuje 6 obrazovych fazi: rozcesti, havran, kun u statku, rozhovor s konem, pumpa a pumpovani vody.
- Jsou nasazene anglicke MP3 pro dialogy, UI instrukce, napovedy a slovnicek.
- Benji/Bunny maji pevne MP3 hlasy bez browser fallbacku, Bruno je prepnuty na hlubsi lokalni `Daniel`.
- Prvni audio repliky se prednacitaji, aby zacatek nespadal do browser fallbacku.
- Havran ma mensi klikaci pole a ceske citoslovce `Krá krá`.
- Pumpovaci hadanka predem nezvyraznuje Fionu.
- Slovnicek ma 35 polozek vcetne `come`, `but` a opravene vyslovnosti `live` jako `liv`.
- Scene 2 ma dokoncovaci bublinu, ktera otevre Scene 3.

Co neni hotove:
- Dalsi Forest Journey scena zatim neni zalozena.
- Benjiho hlas ma podle Mily jeste rezervy, ale je to volitelne poslechove doladeni,
  ne blokace sceny.

Dalsi krok:
- Pri dalsi male MMTX davce bud udelat Benji-only poslechovy recast, nebo prejit
  na dalsi Forest Journey scenu podle noveho zadani.

Navrhovane dalsi kroky:
- Pokud se objevi konkretni zvukova chyba, nejdrive zkontrolovat HTTP 200 pro
  konkretni MP3 a cache verze `script.js`.
- Pokud jde jen o charakter Benjiho hlasu, pripravit kratkou sadu kandidatu a
  nemenit zbytek sceny.

Aktualizace po webovem retestu 2026-07-01:
- Mila potvrdil, ze Scene 3 na webu rucne otestoval; hlas Benjiho ma rezervy,
  ale jinak je scena OK. Stary auditni dalsi krok "rucne otestovat MMTX na webu"
  je splneny a nema se vracet jako aktualni prace.

Zmenene nebo relevantni soubory:
- `docs/scene02_sunnys_lost_nuts/`
- `docs/scene03_journey_to_the_lake/`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/`
- `MatysekANJ/web_mmtx/scene03_journey_to_the_lake/`
- `Samantha_Agent/memory/projects/mmtx_story_hotspot_app.md`
- `Samantha_Agent/memory/technical/matysek_f5tts_voice_workflow.md`
- `Samantha_Agent/memory/ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Handoff neobsahuje zadne private udaje, tokeny, hesla ani citlive texty.
