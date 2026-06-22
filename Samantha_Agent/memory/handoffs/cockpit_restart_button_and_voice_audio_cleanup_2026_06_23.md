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
- `app/speech/edge_tts_open.py` uz docasne Edge TTS MP3 neotevira pres `open`,
  ale prehrava je primo pres `/usr/bin/afplay`, aby se neimportovaly do Apple Music.
- Z Apple Music knihovny a fyzickych souboru byly po vyslovnem potvrzeni Mily
  odstraneny stare `adam_voice_report_*` a `adam_voice_test` polozky; do gitu se
  tim neuklada zadny soukromy obsah.

Co neni hotove:
- Po prvnim commitu Míla rucne otestoval tlacitko a restart backendu probehl,
  ale Safari obnovilo stranku moc brzy a zobrazilo chybu pripojeni; pozdejsi
  rucni reload uz Cockpit otevrel. Tento follow-up je opraveny pollingem.
- Nebyl proveden dalsi realny klikaci retest po polling follow-up oprave; zmeny
  jsou overene cilenymi unit testy a syntaktickou kontrolou.
- Pokud iPhone Music stale ukazuje stare polozky, jde pravdepodobne o iCloud/iPhone
  cache/synchronizaci, protoze na Macu uz `adam*voice*` polozky v Music nejsou videt.

Dalsi krok:
- Po pristi prilezitosti rucne kliknout v Cockpitu na `Servis -> Restart Cockpitu`
  a overit, ze UI nejdriv ukazuje `Cekam na navrat Cockpitu...` a reload udela
  az po realnem navratu serveru, bez Safari chyby pripojeni.

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
