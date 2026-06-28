Nazev: Cockpit remote exact confirmation cards
Priorita: 1
Stav: hotovo MVP
Pripomenout pri startu: ano
Datum: 2026-06-27

Co se resilo:
Pri testovani Cockpitu a VoiceBridge se ukazala mezera v remote potvrzovani rizikovych akci. Pokud Adam vyzaduje presnou potvrzovaci vetu, Mila ji v Cockpitu nemusi videt, a z iPhonu ji pak nemuze jednoduse opsat, zkopirovat nebo odeslat.

Co je hotove:
- Problem je identifikovany jako samostatny vyvojovy pozadavek.
- Pozadavek je zapsany bez citlivych textu, adresatu, e-mailu nebo obsahu priloh.
- Dne 2026-06-28 byl implementovan MVP: `codex_approval_notice.py set` umi volitelne `--confirmation-text`, runtime stav ho vraci pres `voice_mode.codex_approval` a Cockpit karta `Codex čeká na potvrzení` umi vetu zobrazit, zkopirovat a odeslat Adamovi pres textovy hlasovy bridge.
- Cileny test `tests.test_adam_voice_mode tests.test_cockpit` prosel: 212 testu OK.

Co neni hotove:
- MVP neresi vzdalené zmacknuti interniho Codex systemoveho povoleni; to stale musi Mila rozhodnout v Codex UI/terminalu.
- Konkretni rizikove tooly porad musi mit vlastni potvrzovaci brany; Cockpit karta jen spolehlive prenasi presnou textovou vetu z remote UI.
- Chybi rucni test z iPhonu na realne karte s presnou vetou.

Dalsi krok:
Rucne otestovat z Macu a iPhonu: vytvorit testovaci approval kartu s bezpecnou potvrzovaci vetou, zkontrolovat zobrazeni, kopirovani a odeslani pres Cockpit. Po testu kartu vycistit.

Navrhovane dalsi kroky:
- Pri dalsim Cockpit auditu projit, ktere konkretni rizikove POST akce maji uzivatelum vracet presnou potvrzovaci vetu.
- Pozdeji zvazit obecny `approval_request` model pro vsechny kanaly, pokud zacnou potvrzovaci karty pribyvat.
- Otestovat minimalne externi odeslani, mazani/purge, tisk a pripadne platby.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `scripts/codex_approval_notice.py`
- `tests/test_adam_voice_mode.py`
- `memory/reports/cockpit_post_action_risk_matrix_2026_06_27.md`
- `memory/technical/global_safety_brake.md`
- `memory/technical/codex_remote_approval_notice.md`

Bezpecnost / neukladat:
Do gitu ani pameti neukladat plne citlive hlasove pokyny, texty e-mailu, obsah PDF priloh, cele adresy, tokeny ani hesla. Approval karta ma ukazovat jen nezbytne shrnuti akce a potvrzovaci vetu.
