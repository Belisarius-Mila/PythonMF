Nazev: Cockpit restart button and Adam voice audio cleanup
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
- Mila nahlasil, ze v Cockpitu v sekci Servis nefunguje tlacitko `Restart Cockpitu`
  a hlasi chybu.
- Soucasne se resila prakticka chyba hlasoveho vystupu: docasne Adamovy MP3 se
  oteviraly pres vychozi macOS aplikaci a koncily v Apple Music knihovne.

Co je hotove:
- `scripts/restart_cockpit.py` uz po SIGTERM ceka jen na zanik puvodniho PID.
  Nevyzaduje, aby byl port kratce volny, protoze launchd runner muze novy Cockpit
  nastartovat okamzite a port znovu obsadit drive, nez helper stihne kontrolu.
- `app/cockpit.py` spousti restart worker s kratkou prodlevou `--delay 2.0`,
  aby HTTP odpoved stihla odejit do UI pred ukoncenim serveru.
- Frontend restart tlacitka uz pri prerusenem fetch spojeni behem restartu
  nezobrazi tvrdou chybu; oznami preruseni spojeni a po chvili stranku obnovi.
- Follow-up po rucnim testu: jednorazovy reload byl stale prilis brzy a Safari
  obcas skoncilo na chybe `nelze se pripojit k serveru`. Frontend proto misto
  pevneho reload timeoutu opakovane kontroluje `/api/status` a stranku obnovi
  az ve chvili, kdy Cockpit znovu odpovida.
- Finalni provozni zjisteni: lokalni Cockpit na `127.0.0.1:8770` uz mel novou
  verzi, ale Tailscale instance na `100.89.150.6:8770` jeste servirovala starou.
  Po restartu Tailscale Cockpitu a rucnim refreshi Safari Mila potvrdil, ze
  restart funguje na Macu i na iPhonu.
- `app/speech/edge_tts_open.py` uz docasne Edge TTS MP3 neotevira pres `open`,
  ale prehrava je primo pres `/usr/bin/afplay`, aby se neimportovaly do Apple Music.
- Z Apple Music knihovny a fyzickych souboru byly po vyslovnem potvrzeni Mily
  odstraneny stare `adam_voice_report_*` a `adam_voice_test` polozky; do gitu se
  tim neuklada zadny soukromy obsah.

Co neni hotove:
- Nic k tomuto bloku. Po restartu Tailscale instance a refreshi stranky Mila
  potvrdil rucni test na Macu i iPhonu jako funkcni.
- Pokud iPhone Music stale ukazuje stare polozky, jde pravdepodobne o iCloud/iPhone
  cache/synchronizaci, protoze na Macu uz `adam*voice*` polozky v Music nejsou videt.

Dalsi krok:
- Zadny okamzity krok; oprava je overena rucne. Pri dalsim nasazeni Cockpitu
  pamatovat, ze lokalni a Tailscale instance jsou dva bezici procesy a po zmene
  serveroveho HTML musi obe nacist novy kod.

Navrhovane dalsi kroky:
- Pokud se chyba vrati, precist `data/private/cockpit/restart.log` a zkontrolovat
  aktualni PID pres `lsof -nP -iTCP:8770 -sTCP:LISTEN`.
- Nevracet Edge TTS prehravani na macOS `open`; pro systemovy zvuk pouzivat
  `say` nebo `afplay`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/restart_cockpit.py`
- `tests/test_cockpit.py`
- `tests/test_restart_cockpit.py`
- `app/speech/edge_tts_open.py`
- `scripts/speak_edge_open.py`
- `tests/test_speech_edge_tts_open.py`
- `tests/test_speak_edge_open.py`
- `memory/projects/tts_edge_audio_tools.md`

Bezpecnost / neukladat:
- Neukladat do gitu obsah `data/private/`, Music knihovnu, hlasove prepisy,
  soukrome MP3, tokeny ani cele hlasove pokyny.
- Mazani v Apple Music bylo provedeno jen po presne potvrzene vete od Mily a
  pouze pro polozky se jmeny `adam_voice_report_*` a `adam_voice_test`.
