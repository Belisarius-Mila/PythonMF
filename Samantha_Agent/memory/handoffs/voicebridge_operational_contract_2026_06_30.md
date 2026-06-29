Nazev: VoiceBridge provozni kontrakt a ochrana proti regresim
Priorita: 1
Stav: hotovo / chranit pri dalsich upravach
Pripomenout pri startu: ano
Datum: 2026-06-30

Co se resilo:
- Po predchozim uzavreni VoiceBridge se 2026-06-29 znovu rozpadla cast komunikacni cesty pres Cockpit nahravani hlasoveho pokynu.
- Textove pole v Cockpitu zustalo funkcni, ale nahravaci vetev nejdrive padala pri prepisu audia a po oprave prepisu dorucovala nektere pokyny duplicitne.
- Cilem tohoto handoffu je popsat komunikační cesty tak, aby dalsi Codex relace neopravovala VoiceBridge naslepo a aby se pred zmenami dal udelat presny smoke test.

Kanonicky tok - nahravany hlasovy pokyn z Mac Cockpitu:
- UI: Cockpit `Nahrát pokyn` zavola v HTML/JS funkce okolo `startVoiceRecording()` a `transcribeVoiceRecording()` v `app/cockpit.py`.
- Frontend diagnostika zapisuje bezpecne technicke udalosti do `data/private/voice_inbox/frontend_events.jsonl`, napr. `record_start_clicked`, `record_started`, `record_stop_clicked`, `transcribe_post_start`, `transcribe_post_result`.
- Backend endpoint je `POST /api/speech/transcribe`.
- Handler je `cockpit_transcribe_voice_action()` v `app/cockpit.py`.
- Audio se prepise pres `transcribe_audio_base64_isolated()`, ktere ulozi docasny audio soubor a spusti `.venv/bin/python app/speech/transcribe.py`.
- `app/speech/transcribe.py` ma pro realny CLI/VoiceBridge prepis pouzivat `curl` na OpenAI audio transcription API, ne OpenAI Python SDK. Duvod: Python/OpenAI SDK v tomto macOS provozu opakovane padalo na `[Errno 11] Resource deadlock avoided`.
- OpenAI API klic se nesmi predavat jako argument procesu viditelny v `ps`; curl konfigurace jde pres stdin.
- Po uspesnem prepisu se text uklada do `data/private/voice_inbox/latest_voice_command.md` a indexu `data/private/voice_inbox/index.jsonl`.
- Pokud bezi Adam Voice Mode watcher, nahravaci vetev nesmi dorucovat inline do terminalu. Jen ulozi pokyn do inboxu a vrati stav `watcher_will_deliver`.
- Watcher potom jako jediny vlastnik doruceni prevezme pokyn z inboxu a vlozi ho do Codex chatu.

Kanonicky tok - textovy pokyn z Cockpitu:
- UI textove pole vola `POST /api/speech/voice-text`.
- Handler je `cockpit_save_voice_text_action()` v `app/cockpit.py`.
- Text se ulozi do `latest_voice_command.md`.
- Pokud bezi watcher, textova vetev take jen ulozi do inboxu a vrati `watcher_will_deliver`.
- Inline doruceni je fallback jen v pripade, ze watcher nebezi nebo je v testu explicitne predan `terminal_bridge`.

Kanonicky tok - mezistav a finalni odpoved:
- Pri prijeti hlasoveho pokynu ma Codex nejdriv zapsat textovy mezistav:
  `.venv/bin/python scripts/adam_voice_reply.py --processing-started`
- Finalni kratky vysledek se zapisuje:
  `.venv/bin/python scripts/adam_voice_reply.py --latest-command "STRUČNÝ VÝSLEDEK"`
- Mac TTS pres `scripts/speak_edge_open.py` se nema spoustet soucasne s Cockpit audio kanalem, pokud si to Mila vyslovne nevyzada nebo pokud Cockpit audio neni k dispozici.
- Finalni odpoved nesmi nahlas cist tajemstvi, cele osobni udaje, cele e-maily ani dlouhe citlive texty.

Kanonicky tok - rizikove akce z hlasu:
- Read-only a bezne diagnosticke dotazy mohou jit plynule.
- Odesilani e-mailu/SMS, mazani, presuny do kose, platby, commity na prani, prace s tajemstvimi a podobne rizikove kroky vyzaduji samostatnou presnou potvrzovaci vetu.
- U e-mailu/SMS je povolene pripravit draft/navrh, ale skutecne odeslani az po samostatne presne vete od Mily.
- Potvrzovaci karta v Cockpitu je pomoc pro vzdaleny provoz; nema obchazet bezpecnostni pravidla.

Zakladni invarianty, ktere se nesmi rozbit:
- Jeden pokyn smi mit prave jednoho vlastnika doruceni do Codex chatu.
- Kdyz bezi watcher, vlastnik doruceni je watcher, ne inline bridge.
- Nahravaci vetev a textova vetev musi mit stejne pravidlo proti duplicite: `watcher_will_deliver`.
- `delivery_attempts.jsonl` se nema tvorit pro inline doruceni, pokud se doruceni nechava watcheru.
- `frontend_events.jsonl` nesmi obsahovat text pokynu; jen technicke kroky, status, delku textu, velikost audia, trvani a bezpecne chybove zpravy.
- `adam_voice_history.jsonl` muze obsahovat text pokynu v private datech, ale necommitovat ho.
- Nikdy necommitovat `data/private/voice_inbox/`, `data/private/cockpit/`, `data/session_autosave/`, drafty e-mailu ani jine soukrome datove soubory.
- `OPENAI_API_KEY` patri jen do lokalniho `.env` nebo prostredi, nikdy do gitu, dokumentace ani command-line argumentu.

Co bylo opraveno v incidentu 2026-06-29:
- `422db57 Isolate VoiceBridge transcription process`: prvni pokus izolovat prepis mimo Cockpit HTTP handler.
- `cca8d7b Harden VoiceBridge transcription diagnostics`: bezpecna backend/frontend diagnostika chyb prepisu a prime spousteni `app/speech/transcribe.py` misto `python -m`.
- `f6db098 Use curl for VoiceBridge transcription`: realny VoiceBridge prepis pres curl misto OpenAI Python SDK kvuli chybe `[Errno 11] Resource deadlock avoided`.
- `edce0c5 Avoid duplicate delivery for recorded VoiceBridge commands`: nahravaci vetev uz pri bezicim watcheru nedorucuje inline a nechava doruceni watcheru.

Jak diagnostikovat pristi problem:
- Nejdriv rozdelit cestu na kroky:
  1. UI klik/nahravani: `record_start_clicked`, `record_started`, `record_stop_clicked`.
  2. Upload audia: `transcribe_post_start` vcetne `audio_kb` a `recorded_seconds`.
  3. Prepis: `transcribe_post_result ok=true/false`.
  4. Ulozeni do inboxu: novy radek v `data/private/voice_inbox/index.jsonl`.
  5. Doruceni: radky v `adam_voice_history.jsonl`; u beziciho watcheru nema vznikat duplicitni inline pokus.
  6. Odpoved: `scripts/adam_voice_reply.py --latest-command` a Cockpit audio.
- Pokud `record_*` chybi, problem je ve frontendu/mikrofonu/prohlizeci.
- Pokud `transcribe_post_start` je a `transcribe_post_result` chybi, problem je HTTP request, server nebo timeout.
- Pokud `transcribe_post_result ok=false`, cist bezpecny detail v `frontend_events.jsonl`, zejmena `backend_transcribe_failed`.
- Pokud prepis je `ok=true`, ale pokyn neni v chatu, problem je inbox/watcher/doruceni.
- Pokud pokyn prijde dvakrat, hledat soucasne inline doruceni a watcher prevzeti; oprava ma drzet invariant `watcher_will_deliver`.

Minimalni retest po jakekoliv zmene VoiceBridge:
- Spustit jednotkove/regresni testy:
  `.venv/bin/python -m unittest tests.test_cockpit tests.test_speech_transcribe tests.test_adam_voice_mode tests.test_terminal_bridge tests.test_email_outbound_tools`
- Overit, ze Cockpit bezi lokalne i pres Tailscale:
  `curl -fsS http://127.0.0.1:8770/api/status`
  `curl -fsS http://100.89.150.6:8770/api/status`
- Rucny smoke test:
  1. Textove pole Cockpitu: kratky nerizikovy pokyn.
  2. Nahravani z Mac Cockpitu: kratky nerizikovy pokyn.
  3. Ocekavani: jeden prepis, jeden pokyn v chatu, jedna finalni odpoved, zadne inline+watcher dvojite doruceni.
- Po testu precist jen technicke logy, neopisovat citlive texty.

Zname rizikove body:
- Browser audio a autoplay mohou byt blokovane prohlizecem; to neni totéz jako selhani backendu.
- Mac/iPhone Cockpit mohou mit rozdilnou latenci v zobrazeni karet nebo stavu; hodnotit podle serverovych logu a realneho doruceni.
- Bezi-li vice Codex relaci, voice marker a cil bridge musi byt jasny; marker nemenit bez potvrzeni.
- Pokud se meni Cockpit frontend, je nutny hard reload/obnova stranky, jinak muze klient bezet na stare JS verzi.
- OpenAI SDK se pro realny hlasovy prepis nema vracet bez silneho duvodu a samostatneho testu, protoze se v tomto provozu projevila chyba `Resource deadlock avoided`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/transcribe.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `scripts/adam_voice_reply.py`
- `scripts/speak_edge_open.py`
- `scripts/restart_cockpit.py`
- `scripts/cockpit_server.py`
- `tests/test_cockpit.py`
- `tests/test_speech_transcribe.py`
- `tests/test_adam_voice_mode.py`
- `tests/test_terminal_bridge.py`
- `tests/test_email_outbound_tools.py`
- `memory/handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`

Bezpecnost / neukladat:
- Neopisovat ani neukladat do gitu plne texty hlasovych pokynu, e-maily, adresy, tokeny, hesla, API klice ani obsah soukromych dokumentu.
- Necommitovat private logy z `data/private/voice_inbox/` ani `data/private/cockpit/`.
- Pri hlasovem pokynu s rizikem odeslani/mazani/platby/tajemstvi vzdy pouzit presnou potvrzovaci vetu.

Dalsi krok:
- Pred dalsim zasahem do VoiceBridge nejdrive precist tento handoff a overit, ktera cast cesty je skutecne rozbita.
- Pri dalsim refaktoru zvazit automatizovany smoke test, ktery bez realneho audia overi invariant: "watcher running => no inline delivery".
