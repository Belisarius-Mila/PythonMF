Nazev: Adam Voice iPhone audio bridge - funkcni checkpoint
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-11

Co se resilo:
- Po nechtenem zavreni terminaloveho okna bylo potreba obnovit kontext dlouhe prace na Adam Voice / Mac / iPhone / SSH smeru.
- Autosave zachoval rozhodujici cast prace a podle nej se obnovil stav poslednich oprav.
- Cilem bylo stabilizovat cestu z iPhone Cockpitu pres Tailscale do aktualni Codex relace a dostat Adamovu odpoved zpet do iPhone Cockpitu vcetne audia.

Co je hotove:
- Funkcni cesta je potvrzena:
  1. iPhone otevre Cockpit pres Tailscale.
  2. Mila klepne na `Otevřít audiokanál`.
  3. Pokyn jde pres `Diktovat text` / `Odeslat Adamovi`.
  4. Cockpit doruci pokyn do aktualni Codex relace pres `local_tty`.
  5. Codex zapise strucnou odpoved zpet pres `scripts/adam_voice_reply.py --latest-command "..."`
  6. iPhone Cockpit odpoved prevezme pollingem a po odemceni audio kanalu ji umi prehrat na iPhonu.
- `managed_screen` / SSH screen cesta je ponechana jen jako explicitni experiment, protoze umela hlasit doruceno bez prokazatelne odpovedi z Codexu.
- Cockpit uz nesmi parovat novy pokyn se starou odpovedi; odpoved se bere jen pokud patri ke stejnemu textu pokynu a vznikla po odeslani.
- Remote/iPhone Cockpit uz pri blokovanem autoplay nepada na Mac TTS fallback; Mac nema mluvit misto iPhonu.
- Prvni skutecne klepnuti na iPhonu odemyka browser audio kanal; pozdejsi odpovedi se pokousi prehrat automaticky.
- Do UI bylo pridano tlacitko `Otevřít audiokanál` vlevo od `Odeslat Adamovi`; po uspesnem otevreni se meni na `Audiokanál otevřený`.
- Míla realne potvrdil, ze po odemceni audio kanalu se dalsi odpoved prehrala na iPhonu.
- Po handoff testu se ukazalo, ze delsi ukol muze odpovedet az po vyprseni puvodniho 120s pollingu. Cockpit polling na odpoved hlasoveho pokynu byl prodlouzen na 10 minut (`VOICE_REPLY_POLL_DURATION_MS = 600000`) a pokryty testem.
- Posledni kratky spojovaci test `slyšíš mě` byl zpracovan a odpoved `Ano, slyším tě.` byla zapsana do Cockpitu explicitne k danemu user textu.
- Relevantni commity:
  - `36ae38c Stabilize Cockpit voice reply routing`
  - `b9be2e0 Keep remote Cockpit speech on device`
  - `45b18f4 Unlock remote Cockpit voice playback`
  - `ed19364 Add Cockpit audio channel control`

Co neni hotove:
- Bezi vice Codex relaci nez je idealni; Cockpit proto hlasi varovani. Je potreba pozdeji udelat opatrny cleanup relaci, ne automaticke ukoncovani.
- `managed_screen` cesta nema spolehlivy readiness/response proof a nema byt vychozi transport.
- Branch byla po teto praci `ahead 14` pred finalnim checkpoint commitem; push nebyl soucasti tohoto handoffu.
- Posledni uspesna recovery zaloha byla stale starsi nez 3 dny, resit az po pripojeni externiho disku.

Dalsi krok:
- Pri dalsim testu z iPhonu pouzit ritual: obnovit Cockpit -> `Otevřít audiokanál` -> poslat kratky pokyn -> overit textovou odpoved a prehrani na iPhonu.

Navrhovane dalsi kroky:
- Okamzite: nechat funkcni `local_tty` cestu jako vychozi a nepokouset se ted znovu prepinat na `managed_screen`.
- Potom: read-only zkontrolovat bezici Codex relace a rucne rozhodnout, ktere stare relace lze bezpecne ukoncit.
- Volitelne: doplnit do Cockpitu zretelny stav `Audiokanál otevřený / zavřený`, `Cíl bridge`, `Poslední odpověď doručena na iPhone`.
- Pozdeji: navrhnout robustni managed screen/SSH transport jen s overitelnou pripravenosti a potvrzenim, ze odpoved skutecne vznikla.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `scripts/adam_voice_reply.py`
- `app/speech/terminal_bridge.py`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Neukladat cele hlasove prepisy, soukrome pokyny, telefonni cisla, e-maily, hesla, tokeny, API klice ani obsah private runtime souboru.
- `data/private/voice_inbox/` zustava private runtime oblast mimo git.
- `data/session_autosave/` jsou jen nouzove autosave logy a nesmi se commitovat.
