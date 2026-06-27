# Cockpit function inventory audit

Datum: 2026-06-27
Rozsah: bod 1 z auditu Cockpitu - read-only inventura funkci, endpointu, UI ploch, servisnich skriptu a testu.

Bezpecnost:
- Report je git-safe souhrn.
- Nebyla ctena cela tela e-mailu, dokumentu, poznamek ani privatni archivni texty.
- Zive API bylo pouzito jen pro agregovany stav Cockpitu, voice bridge, git a zalohu.

## Aktualni provozni stav

Read-only overeni mimo Codex sandbox:

- `scripts/system_quick_check.py` proslo.
- `scripts/cockpit_smoke_check.py` proslo.
- Lokalni Cockpit odpovida na `/`, `/api/status`, `/api/recovery/status`.
- Voice bridge: `status=ok`, `effective_tty=ttys000`, `codex_tty_count=1`.
- Git: cisty `main...origin/main`.
- Zaloha: posledni recovery zaloha je v 3dennim intervalu, datum 2026-06-27.

Poznamka k diagnostice:
- Stejne kontroly uvnitr Codex sandboxu mohou vratit falesne `Operation not permitted`.
- Pro provozni audit Cockpitu se ma smoke/quick check spoustet mimo sandbox, pokud je cilem realny stav lokalni sluzby.

## Velikost a koncentrace

Hlavni soubory:

| Soubor | Radku | Role |
| --- | ---: | --- |
| `app/cockpit.py` | 18511 | HTTP server, HTML, JS, endpointy, akcni handlery, statusy |
| `tests/test_cockpit.py` | 6125 | jednotkove testy Cockpitu a souvisejicich workflow |
| `app/speech/terminal_bridge.py` | 567 | hlasovy terminal bridge |
| `tests/test_terminal_bridge.py` | 542 | testy hlasoveho bridge |

Zaver inventury:
- Cockpit je funkcni, ale `app/cockpit.py` je uz velky monolit.
- Riziko regresi roste hlavne kvuli tomu, ze UI, endpointy, servisni akce, voice bridge, dokumenty, e-mail, knihovna, lekarna a Janicka sdili jeden soubor a cast spolecnych helperu.

## HTTP routy

Staticky zmapovane v `app/cockpit.py`:

- GET-like routy: 33
- POST routy: 56
- Celkem zmapovanych cest: 89

### GET-like stranky a data

Hlavni HTML / cteci stranky:
- `/`
- `/email-processing/`
- `/janicka-kucharka/`
- `/lekarna-admin/`
- `/documents/read`
- `/documents/pdf`
- `/purchases/read`
- `/purchases/pdf`
- `/local-apps/*`

Status a prehledy:
- `/api/status`
- `/api/recovery/status`
- `/api/reminders`
- `/api/web-apps`
- `/api/projects/status`
- `/api/quick-notes/status`
- `/api/quick-notes/detail`
- `/api/urgent-reminders/status`
- `/api/quantitative-status`
- `/api/consistency-status`

Knihovna a lekarna:
- `/api/library/list`
- `/api/library/search`
- `/api/library/item`
- `/api/library/attachment`
- `/api/lekarna/search`
- `/api/lekarna/import/photos`

Dokumenty a e-maily:
- `/api/documents/search`
- `/api/documents/review-report`
- `/api/documents/case-detail`
- `/api/email-processing/overview`
- `/api/email-processing/pending-work`

Hlas a servis:
- `/api/voice-mode/latest-response`
- `/api/voice-mode/safe-readonly`
- `/api/dev-runner/actions`

### POST akcni routy

Servis / lokální aplikace:
- `/api/scandocu/open`
- `/api/terminal/open`
- `/api/desktop-apps/open`
- `/api/samantha/open`
- `/api/codex/open`
- `/api/cockpit/restart`

Hlas / Adam / bridge:
- `/api/speech/speak`
- `/api/speech/edge-tts`
- `/api/speech/transcribe`
- `/api/speech/voice-text`
- `/api/adam/status`
- `/api/adam/start`
- `/api/adam/restart`
- `/api/adam/stop`
- `/api/voice-mode/start`
- `/api/voice-mode/stop`
- `/api/voice-mode/approval`
- `/api/voice-mode/codex-approval/clear`
- `/api/voice-mode/safe-readonly/run`
- `/api/voice-bridge/marker`
- `/api/voice-bridge/terminate-stale`
- `/api/janicka/chat`
- `/api/janicka/chat/latest`

Allowlistovane vyvojove akce:
- `/api/dev-runner/run`

Projekty, pripominky, konzistence:
- `/api/projects/lifecycle`
- `/api/reminders/done`
- `/api/reminders/cancel-payment`
- `/api/reminders/source`
- `/api/urgent-reminders/done`
- `/api/consistency/resolve-finding`

Dokumenty:
- `/api/documents/open`
- `/api/documents/print/prepare`
- `/api/documents/print/run`
- `/api/documents/lifecycle`
- `/api/documents/reading-status`
- `/api/documents/classification-metadata`
- `/api/documents/classification-suggestion/accept`
- `/api/documents/due-reminder`
- `/api/documents/intake-email-scan`

Knihovna:
- `/api/library/archive`
- `/api/library/text`
- `/api/library/attachment/add`
- `/api/library/delete`
- `/api/library/read-state`
- `/api/library/export/prepare`
- `/api/library/export/send`

Lekarna:
- `/api/lekarna/retire/preview`
- `/api/lekarna/retire/apply`
- `/api/lekarna/import/draft`
- `/api/lekarna/import/apply`

E-mail processing:
- `/api/email-processing/decision`
- `/api/email-processing/read-message`
- `/api/email-processing/preview-attachment`
- `/api/email-processing/process-batch`
- `/api/email-processing/purge-trash`
- `/api/email-processing/new-headers`

## Hlavni UI plochy

Hlavni dashboard:
- horni akce: `Janička`, `Obnovit`, `Webové aplikace`, `Knihovna`, `Projekty`, `Připomenutí`, `E-maily`, `Servis`, `ScanDocu`, `Revidovat dokumenty`
- denni bloky: dokumenty, pripominky, hlas, zaloha, system, ScanDocu, projekty, kontrola, rychle poznamky, git
- akcni fronta: `Co ted delat`

Hlas:
- nahrani hlasoveho pokynu
- textovy fallback pro Adama
- stary watcher
- voice bridge diagnostika a prepinac cilove TTY
- safe read-only kontroly
- posledni Adamova odpoved
- approval karty pro hlas/Codex potvrzeni

Dokumenty:
- nove PDF
- ulozene dokumenty k revizi
- problemove dokumenty
- sjednoceny intake
- cases/vazby
- klasifikace
- kandidati terminu
- review report
- vyhledavani dokumentu a nakupnich PDF

Servis:
- terminal v projektu
- systemovy souhrn
- rychle poznamky
- recovery centrum
- diagnostika
- restart Cockpitu
- TTS stavu/vyberu
- frontend health
- dev runner
- downloads, backup, vault, consistency

Modaly a samostatne plochy:
- `Janička`
- `Janička chat`
- `Janička rodinné projekty`
- `Webové aplikace`
- `Knihovna`
- `Projekty a schopnosti`
- `Rychlé poznámky`
- `Důležitá připomenutí`
- `Recovery centrum`
- `Diagnostika`
- `Systémový souhrn`
- `Připomenutí`
- samostatna `Email Processing` stranka
- samostatna `Lekarna admin` stranka
- samostatne ctecky dokumentu/nakupu

## Interni registry v Cockpitu

### Safe read-only kontroly

`SAFE_READONLY_CAPABILITIES` obsahuje:

- `codex_sessions`
- `voice_bridge`
- `git_status`
- `backup_status`

Hodnoceni:
- Dobry vzor pro dalsi auditovatelne Cockpit schopnosti.
- Ma pevny allowlist a handler mapu.
- Pokud se bude Cockpit rozrustat, tohle je smer pro male, bezpecne servisni schopnosti.

### Dev runner

`DEV_RUNNER_ACTIONS` obsahuje:

- `cockpit_voice_tests`
- `cockpit_py_compile`
- `git_diff_check`

Hodnoceni:
- Dobry vzor: nespousti volny shell, ale pevne povolene argv prikazy.
- Pouzitelne pro rutinni kontrolu po upravach Cockpitu.

## Servisni skripty souvisejici s Cockpitem

Zakladni runtime:
- `scripts/start_cockpit.sh`
- `scripts/open_cockpit.py`
- `scripts/cockpit_server.py`
- `scripts/cockpit_launchd_runner.py`
- `scripts/install_cockpit_local_launchd.sh`
- `scripts/install_cockpit_tailscale_launchd.sh`

Kontroly:
- `scripts/cockpit_smoke_check.py`
- `scripts/system_quick_check.py`
- `scripts/backup_status.py`
- `scripts/autosave_status.py`
- `scripts/git_safety_check.py`
- `scripts/git_push_guard.py`
- `scripts/samantha_capability_audit.py`

Restart a remote approval:
- `scripts/restart_cockpit.py`
- `scripts/codex_approval_notice.py`

Voice / Adam / Codex relace:
- `scripts/adam_bridge_readiness_report.py`
- `scripts/adam_voice_pending.py`
- `scripts/adam_voice_reply.py`
- `scripts/codex_session_report.py`
- `scripts/mark_current_codex_tty.py`
- `scripts/speak_edge_open.py`
- `scripts/samantha_codex.sh`
- `scripts/samantha_screen_entry.sh`

## Testove pokryti

Relevantni testy:
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `tests/test_adam_voice_mode.py` pro cast hlasoveho provozu

Aktualne overeno v predchozim kroku po voice bridge oprave:
- `tests.test_terminal_bridge tests.test_cockpit`: 200 testu OK

Silne oblasti testu:
- knihovna
- lekarna admin
- dokumentove fronty, cases, search, tisk, lifecycle
- e-mail processing
- Janička chat
- voice bridge a terminal bridge
- safe read-only allowlist
- dev runner allowlist
- restart Cockpitu

Mezery pro dalsi audit:
- Neexistuje jeden generovany katalog vsech endpointu s rizikovou tridou.
- Neexistuje automaticky test, ktery porovna frontend volane endpointy proti backend routam.
- Neexistuje jednotny Cockpit route registry; routy jsou rucne rozesete v `do_GET` a `do_POST`.
- Manualni smoke test pokryva jen `/`, `/api/status`, `/api/recovery/status`, ne cele UI.

## Predbezne zavery bodu 1

1. Cockpit je provozne funkcni a aktualne zeleny.
2. Z pohledu architektury je nejvetsi riziko velikost a promichani odpovednosti v `app/cockpit.py`.
3. Existuji uz dobre vzory pro bezpecne male registry: safe read-only kontroly a dev runner.
4. Dalsi krok auditu ma byt bod 2: rizikova matice POST akci.
5. Pred refaktorem je rozumne nejdriv vytvorit katalog endpoint -> risk -> confirmation -> test coverage.

## Navazujici krok

Pokud Mila potvrdi pokracovani, dalsi krok je bod 2:

- projit vsech 56 POST rout,
- rozdelit je na read-only-pres-POST, local-open, local-service, private-write, print, send, delete/purge, external-AI,
- u kazde skupiny poznamenat aktualni potvrzovaci branu a testove pokryti.
