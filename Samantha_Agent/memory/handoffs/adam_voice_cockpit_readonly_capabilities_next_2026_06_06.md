Nazev: Adam Voice / Cockpit remote approvals and read-only capability registry
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-06

Co se resilo:
- Remote-first smer Adam Voice Mode: hlasovy pokyn z Cockpitu/iPhonu ma doputovat do spravne Codex relace, vysledek se ma vratit do Cockpitu a jit prehrat na zarizeni, ze ktereho Mila pracuje.
- Omezeni soucasne cesty: terminalove potvrzovani a macOS audio jsou pouzitelne u Macu, ale pri vzdalenem iPhone/SSH provozu Mila nemusi videt zadost o povoleni a nemusi slyset odpoved.
- Overilo se, ze plne vypnuti sandboxu neni spravny smer. Lepsi je explicitni Cockpit approval centrum a allowlist read-only schopnosti.

Co je hotove:
- Cockpit umi zobrazit posledni Adamovu odpoved a prehrat ji pres browser audio, tedy i na iPhonu pres Tailscale Cockpit.
- Adam Voice Mode uklada posledni odpoved do private runtime souboru `data/private/voice_inbox/last_adam_response.json`.
- Cockpit ma zakladni approval kartu pro cekajici hlasovy pokyn a endpoint `/api/voice-mode/approval`.
- `scripts/adam_voice_reply.py` podporuje `--latest-command`, aby Codex mohl po dokonceni terminaloveho pokynu zapsat finalni strucny vysledek zpet do Cockpitu.
- Terminal bridge preferuje oznaceny TTY marker a pri chybe oznaceneho TTY nema potichu spadnout na jinou Codex relaci s falesnym uspechem.
- Pravidla bridge byla zmirnena pro read-only formulace typu `promysli` nebo `posli odpoved`; skutecne mazani, commit, push, platby, hesla a tokeny zustavaji rucne potvrzovane.
- SMS/e-mail pokyny jsou rozlisene jako `outbound_confirmation`, ne jako obycejny blok. Priprava navrhu muze byt budoucne schvalovana oddelene od finalniho odeslani.
- Relevantni testy prosly: `.venv/bin/python -m unittest tests.test_adam_voice_mode tests.test_cockpit tests.test_voice_inbox tests.test_terminal_bridge tests.test_messages_outbound_tools` -> `Ran 146 tests ... OK`.

Co neni hotove:
- Neni implementovana samostatna Cockpit registry bezpecnych read-only schopnosti.
- Neni implementovany Cockpit workflow pro read-only akce typu `stav Codex relaci`, `git status`, `posledni handoff`, `spocitat radky kodu`, `stav testu`, `stav voice inboxu`.
- Neni hotova plna dvoukrokova karta pro SMS/e-mail: nejdrive pripravit navrh, potom finalne odeslat az po konkretni potvrzovaci vete.
- Neni hotove tlacitko / rezim `Janička`, ktery by vazne resil kontinuitu pouziti Samanthy pri Milove nedostupnosti.

Dalsi krok:
- Priorita 1: implementovat Cockpit read-only capability registry a approval centrum.
- Minimalni MVP:
  - datovy model pro approval requesty v `data/private/voice_inbox/`;
  - allowlist schopnosti s pevnymi ID, nazvem, popisem a rizikovou tridou;
  - endpoint pro vytvoreni/zobrazeni/schvaleni read-only akce;
  - exekucni vrstvu jen nad registrovanymi Python funkcemi, ne nad volnym shell textem;
  - vysledek ulozit jako posledni Adamovu odpoved a prehrat v Cockpitu;
  - testy pro bezpecne schvaleni, odmitnuti a zakaz neregistrovane akce.

Navrhovane dalsi kroky:
- Po MVP registry doplnit konkretni read-only schopnosti:
  - stav bezicich Codex relaci;
  - stav voice markeru;
  - git status bez citlivych dat;
  - posledni handoff;
  - pocet radku kodu / testovacich radku;
  - stav Cockpitu a Tailscale Cockpitu;
  - stav zalohy.
- Teprve potom rozpracovat `Janička` rezim jako navazani na rodinny nouzovy balik, ne jako samostatnou hracku.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `app/speech/voice_inbox.py`
- `scripts/adam_voice_reply.py`
- `tests/test_adam_voice_mode.py`
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `tests/test_voice_inbox.py`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do handoffu nejsou ulozena hesla, tokeny, API klice, cele e-maily, telefonni cisla ani jina citliva data.
- Private runtime soubory ve `data/private/voice_inbox/` zustavaji mimo git.
- Sandbox nevypinat jako obecne reseni; misto toho stavet allowlist konkretne registrovanych schopnosti a schvalovaci brany podle rizika.
