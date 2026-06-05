Nazev: Adam Voice Bridge - end-to-end hlasovy pokyn do Codexu a hlasova odpoved
Priorita: 1
Stav: rozpracovane / funkcni end-to-end checkpoint
Pripomenout pri startu: ano
Datum: 2026-06-05

Co se resilo:
- Navazalo se na hlasovy vstup v Cockpitu, ktery uklada prepis do private voice inboxu.
- Cilem bylo, aby Mila mohl v Cockpitu zapnout hlasovy mod, namluvit pracovni pokyn, ten se dostal primo do aktivniho Codex chatu, Adam ho zpracoval a vysledek se precetl nahlas.
- Nejdriv se ukazalo, ze Cockpit spoustel Adam Voice Mode watcher bez terminal bridge, takze pokyny zustavaly jako pending v inboxu.
- Potom se ukazalo, ze VS Code fallback vkladal do terminalu ridici text `Terminal: Focus Terminal` nebo `>workbench.action.terminal.focus` misto skutecneho pokynu.
- Nakonec se ukazalo, ze macOS `say`/`scripts/speak_text.py` technicky vraci uspech, ale u Mily nebyl slyset; slyset byla cesta Edge TTS MP3 otevrena pres macOS prehravac.

Co je hotove:
- `start_adam_voice_mode_action` v Cockpitu ted defaultne spousti watcher s `--terminal-bridge`; vypnout ho jde explicitne pres `terminal_bridge=False` nebo env `ADAM_VOICE_TERMINAL_BRIDGE=0|false|no|ne`.
- Adam Voice Mode pri uspesnem doruceni pres terminal bridge oznaci shodny pending pokyn jako `processed_by_terminal_bridge`, aby Cockpit nedrzel falesne cekajici stav.
- Hlasovy prompt predany do Codexu obsahuje bezpecnostni instrukci: normalne zpracovat read-only pokyn, ale pri riziku zmeny dat/odesilani/mazani/commitu/platby/tajemstvi si vyzadat rucni potvrzeni.
- Hlasovy prompt nove obsahuje i instrukci pro vystup: napsat vysledek do chatu a precist strucnou verzi pres `.venv/bin/python scripts/speak_edge_open.py "STRUČNÝ VÝSLEDEK"`.
- Byl pridan helper `app/speech/edge_tts_open.py`, ktery vygeneruje Edge TTS MP3 do `/private/tmp` a otevre ho pres macOS `open`.
- Byl pridan CLI skript `scripts/speak_edge_open.py`.
- VS Code fallback uz nevklada ridici texty, ale aktivuje VS Code, vycisti aktualni vstup pres `Ctrl+U`, vlozi skutecny prompt, pocka `0.25 s` a pak posle Enter.
- Stejna `0.25 s` pauza pred Enterem je i v Terminal.app AppleScript ceste.
- Realne testy v chatu potvrdily:
  - hlasovy pokyn se dostal primo do Codex chatu,
  - Adam ho zpracoval,
  - vysledek se precetl pres Edge TTS MP3,
  - posledni test dokazal zjistit pocet `.shortcut` zkratek.

Aktualni vysledek posledniho hlasoveho testu:
- Ve slozce `/Users/miloslavfalta/Documents/Shortcuts Playground/` je 11 hotovych `.shortcut` zkratek.
- V repozitari je jeste jeden oddeleny `generated_shortcuts/Adam_GITHUB.shortcut`; fyzicky napric obema misty tedy 12 `.shortcut` souboru.
- Smysluplny pocet hotovych Shortcuts Playground zkratek je 11.

Co neni hotove:
- Automatika je funkcni, ale stale zavisi na GUI vstupu do VS Code/Terminalu. Pokud fokus neni ve spravnem terminalu, fallback muze selhat nebo dorucit do jineho vstupu.
- Edge TTS potrebuje sitovy pristup k `speech.platform.bing.com`; bez site skript selze a je nutne pouzit fallback nebo opakovat s povolenou siti.
- V teto session je aktualni runtime marker pro cilovy Codex TTY stale private soubor `data/private/voice_inbox/current_codex_tty.json`; po nove Codex/VS Code relaci se musi marker znovu nastavit.
- Neni udelana hlubsi integrace do samotneho Codex klienta; cteni vysledku je resene instrukci v promptu a explicitnim TTS skriptem, ktery Adam po zpracovani zavola.

Dalsi krok:
- Udelat jeden finalni realny hlasovy smoke test po commitu/pushi: jednoduchy read-only dotaz ma byt namluven v Cockpitu, automaticky vlozen a odeslan do Codexu bez rucniho Enteru, Adam ma odpovedet a precist vysledek pres `scripts/speak_edge_open.py`.

Navrhovane dalsi kroky:
- Pokud finalni smoke test projde, ulozit do projektu `tts_edge_audio_tools.md` kratky provozni navod:
  1. otevrit Cockpit,
  2. zapnout hlasovy mod,
  3. zkontrolovat watcher/bridge stav,
  4. namluvit read-only pokyn,
  5. pri rizikovem pokynu cekat na rucni potvrzeni.
- Dodelat UI indikaci v Cockpitu, zda watcher bezi s terminal bridge zapnutym, nejen ze watcher bezi.
- Zautomatizovat nastaveni aktualniho Codex TTY markeru pri startu relace, aby se po novem otevreni VS Code/Codexu nezapomnelo preznacit cilove TTY.
- Pokud bude potreba vetsi robustnost, nahradit GUI paste/Enter cestu specializovanym adapterem, ktery umi komunikovat primo s Codex/VS Code terminalem bez AppleScript focus problemu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `app/speech/edge_tts_open.py`
- `scripts/speak_edge_open.py`
- `tests/test_adam_voice_mode.py`
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `tests/test_speech_edge_tts_open.py`
- `memory/handoffs/adam_voice_bridge_target_tty_checkpoint_2026_06_05.md`

Overeni:
- `Ran 120 tests in 13.284s - OK`
- Realny hlasovy test: pocet `.shortcut` zkratek byl zjisten read-only a vysledek byl preceten pres Edge TTS MP3.

Bezpecnost / neukladat:
- Do gitu ani pameti neukladat private voice inbox obsah, cele hlasove prepisy s citlivymi detaily, API klice, tokeny, hesla, osobni identifikatory ani private runtime marker mimo obecny popis.
- Necommitovat `data/private/voice_inbox/`, `data/session_autosave/`, hotove `.shortcut` soubory mimo git ani private iCloud/Shortcuts vystupy.
