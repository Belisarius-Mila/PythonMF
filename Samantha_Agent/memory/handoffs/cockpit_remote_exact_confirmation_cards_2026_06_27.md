Nazev: Cockpit remote exact confirmation cards
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-27

Co se resilo:
Pri testovani Cockpitu a VoiceBridge se ukazala mezera v remote potvrzovani rizikovych akci. Pokud Adam vyzaduje presnou potvrzovaci vetu, Mila ji v Cockpitu nemusi videt, a z iPhonu ji pak nemuze jednoduse opsat, zkopirovat nebo odeslat.

Co je hotove:
- Problem je identifikovany jako samostatny vyvojovy pozadavek.
- Pozadavek je zapsany bez citlivych textu, adresatu, e-mailu nebo obsahu priloh.

Co neni hotove:
- Cockpit zatim nema plnohodnotnou kartu pro exact confirmation fraze u rizikovych hlasovych pokynu.
- Neni hotovy endpoint pro odeslani potvrzovaci vety primo z Cockpitu.
- Nejsou doplnene testy, ze rizikova akce zustane blokovana, dokud neprijde presna veta.

Dalsi krok:
Navrhnout a implementovat v Cockpitu potvrzovaci kartu pro rizikove remote akce. Karta ma ukazat shrnuti akce, riziko, presnou kopirovatelnou potvrzovaci vetu a textove pole nebo tlacitkovy tok pro jeji odeslani z Macu i iPhonu.

Navrhovane dalsi kroky:
- Definovat maly datovy model `approval_request` pro exact confirmation pozadavky.
- V Cockpitu zobrazit aktivni approval kartu vcetne kopirovatelne presne vety.
- Pridat endpoint pro odeslani potvrzovaci vety z Cockpitu.
- Napojit voice/Cockpit tok tak, aby rizikova akce neprobehla bez presneho potvrzeni.
- Otestovat minimalne externi odeslani, mazani/purge, tisk a pripadne platby.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/terminal_bridge.py`
- `scripts/adam_voice_reply.py`
- `memory/reports/cockpit_post_action_risk_matrix_2026_06_27.md`
- `memory/technical/global_safety_brake.md`
- `memory/technical/codex_remote_approval_notice.md`

Bezpecnost / neukladat:
Do gitu ani pameti neukladat plne citlive hlasove pokyny, texty e-mailu, obsah PDF priloh, cele adresy, tokeny ani hesla. Approval karta ma ukazovat jen nezbytne shrnuti akce a potvrzovaci vetu.
