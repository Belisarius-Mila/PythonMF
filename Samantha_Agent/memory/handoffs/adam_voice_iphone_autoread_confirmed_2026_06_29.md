Nazev: Adam Voice iPhone autoread potvrzen
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-29

Co se resilo:
- Stabilizace VoiceBridge po testech z Cockpitu na iPhonu.
- Mezistavy maji byt jen textove a nemaji se cist nahlas.
- Finalni Adamova odpoved se ma v Cockpitu zobrazit a automaticky precist, pokud je otevreny audiokanal.

Co je hotove:
- Otevreni Cockpit audiokanalu automaticky spousti watcher.
- Terminal prompt uz rika nepoustet Mac TTS soucasne s Cockpit audiem.
- Mezistav `Zprava vlozena do chatu a zahajeno zpracovani.` se zapisuje pres `scripts/adam_voice_reply.py --processing-started`.
- Neoverene/pending transportni stavy se neukladaji jako posledni finalni Adamova odpoved.
- Finalni odpoved pres `scripts/adam_voice_reply.py --latest-command` umi zavrit odpovidajici pending pokyn jednim zapisem.
- Cockpit frontend spousti automaticke cteni i pro novou finalni odpoved zachycenou beznym refreshem, pokud je audiokanal otevreny.
- Realny iPhone test VB 013 potvrdil, ze finalni odpoved se precetla nahlas.

Co neni hotove:
- Obcas se stejny testovaci pokyn objevil v chatu dvakrat. Nebylo dale reseno, protoze posledni cilem bylo overit autoread a ten prosel.

Dalsi krok:
- Pokud se duplicity budou opakovat i pri normalnim pouziti, zkoumat samostatne cestu Cockpit -> screen/Codex delivery a deduplikaci podle command signature.
- Jinak VoiceBridge v tomto stavu zmrazit a vratit se k dalsimu planovanemu tematu.

Navrhovane dalsi kroky:
- Okamzite: commit + push aktualnich oprav autoreadu a tohoto handoffu.
- Volitelne pozdeji: pridat diagnosticky citac duplicitnich doruceni, pokud Mila uvidi stejnou zpravu opakovane i mimo testy.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `scripts/adam_voice_reply.py`
- `tests/test_adam_voice_mode.py`
- `tests/test_terminal_bridge.py`
- `memory/handoffs/adam_voice_iphone_autoread_confirmed_2026_06_29.md`

Overeni:
- Pred handoffem proslo `python -m unittest tests.test_cockpit tests.test_adam_voice_mode tests.test_terminal_bridge` s vysledkem 248 testu OK.
- `py_compile` dotcenych Cockpit souboru prosel; zustava starsi nesouvisejici warning v HTML stringu.
- Cockpit bezi lokalne i pres Tailscale a watcher bezi.

Bezpecnost / neukladat:
- Neopisovat dlouhe hlasove pokyny ani citlive texty.
- Mac TTS nespoustet soucasne s Cockpit audiem, pokud o to Mila vyslovne nepozada nebo Cockpit audio neni dostupne.
- Commitovat jen git-safe kod, testy a memory; `data/private/` a autosave logy necommitovat.
