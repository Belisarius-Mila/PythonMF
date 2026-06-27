# Cockpit POST action risk matrix

Datum: 2026-06-27
Rozsah: bod 2 z auditu Cockpitu - read-only rizikova matice POST endpointu.

Bezpecnost:
- Report je git-safe souhrn.
- Nebyla ctena cela tela e-mailu, dokumentu, poznamek ani privatni archivni texty.
- Hodnoceni vychazi ze staticke kontroly `app/cockpit.py`, `tests/test_cockpit.py`,
  `tests/test_terminal_bridge.py` a `tests/test_adam_voice_mode.py`.

## Pouzite rizikove tridy

| Trida | Vyznam | Ocekavana brana |
| --- | --- | --- |
| `read_only_via_post` | POST jen kvuli payloadu/UI; nema trvaly zapis ani externi efekt. | allowlist nebo validace vstupu; bez potvrzeni OK. |
| `local_open` | Otevre lokalni aplikaci, terminal, PDF nebo okno. | allowlist konkretni aplikace/cesty; UI klik staci. |
| `local_service` | Spusti, zastavi nebo restartuje lokalni proces. | minimalne UI confirm; u rizikovejsich akci potvrzeni v payloadu. |
| `voice_local_outbound` | Prevod/predani hlasoveho nebo textoveho pokynu do Codexu/Adama. | triage ve voice bridge; rizikove pokyny musi skoncit v approval flow. |
| `private_write` | Zapisuje do lokalnich soukromych dat, indexu, front nebo pameti. | podle dopadu: UI confirm nebo presna potvrzovaci veta. |
| `external_ai` | Odesila data/fotky do externi AI sluzby. | presna potvrzovaci veta nebo explicitni potvrzeni s jasnym textem. |
| `external_send` | Odesila ven e-mail/PDF nebo jinou zpravu. | presna potvrzovaci veta. |
| `print` | Posila dokument na tiskarnu. | preflight + presna potvrzovaci veta navazana na print job. |
| `delete_or_purge` | Vyrazuje, presouva do kose nebo trvale maze. | presna potvrzovaci veta; u trvaleho mazani idealne jeste silnejsi brana. |
| `dev_runner` | Spousti vyvojove kontroly. | pevny allowlist argv prikazu, zadny volny shell. |

## Souhrn podle rizika

| Trida | Pocet | Stav |
| --- | ---: | --- |
| `read_only_via_post` | 9 | vetsinou v poradku; nektere endpointy jsou POST jen kvuli filtru/detailu |
| `local_open` | 7 | hlavni ochrana je allowlist nebo pevna lokalni cesta |
| `local_service` | 8 | cast ma confirm, cast start/stop bez confirmu |
| `voice_local_outbound` | 3 | ochrana je hlavne v terminal bridge triage, ne primo v Cockpit route |
| `private_write` | 21 | nejsirsi skupina; cast ma silnou frazi, cast jen boolean/UI confirm, cast nema explicitni gate |
| `external_ai` | 1 | ma presnou potvrzovaci frazi pro OpenAI backend |
| `external_send` | 1 | ma presnou potvrzovaci frazi z pripraveneho exportu |
| `print` | 2 | prepare je bezpecny mezikrok; run ma presnou frazi |
| `delete_or_purge` | 3 | silnejsi brany; e-mail purge byl zpevnen na presnou potvrzovaci frazi |
| `dev_runner` | 1 | dobry allowlistovy vzor |

Celkem: 56 POST endpointu.

## Matice endpointu

| Endpoint | Trida | Efekt | Aktualni brana | Pokryti |
| --- | --- | --- | --- | --- |
| `/api/scandocu/open` | `local_service` | spusti lokalni ScanDocu server, pokud nebezi | pevna cesta ke skriptu a portu; bez confirmu | neprime pres Cockpit UI/status |
| `/api/terminal/open` | `local_open` | otevre Terminal v projektu | pevna cesta `PROJECT_ROOT`; bez confirmu | neprime |
| `/api/speech/speak` | `local_open` | lokalni macOS hlasovy vystup | payload text; bez confirmu | UI pritomnost |
| `/api/speech/edge-tts` | `local_open` | vygeneruje/vrati TTS audio | payload text; bez confirmu | UI pritomnost |
| `/api/speech/transcribe` | `voice_local_outbound` | prepise audio, ulozi pokyn, preda do Codexu | hlasovy transport + terminal bridge triage; route nema vlastni confirm | UI pritomnost + voice tests |
| `/api/speech/voice-text` | `voice_local_outbound` | ulozi textovy hlasovy pokyn a preda do Codexu | terminal bridge triage; route nema vlastni confirm | UI pritomnost + voice tests |
| `/api/janicka/chat` | `voice_local_outbound` | predava Janička dotaz do spravovaneho Adama/Codex kontextu | managed Adam/route logika; bez potvrzeni v route | prime testy Janička chat |
| `/api/janicka/chat/latest` | `read_only_via_post` | cte posledni Codex odpoved pro Janičku | cteci helper; bez confirmu | prime testy latest reply |
| `/api/adam/status` | `read_only_via_post` | cte stav Adam sluzby | bez confirmu | UI pritomnost |
| `/api/adam/start` | `local_service` | spusti Adam screen/sluzbu | pevny workflow; bez confirmu | UI pritomnost |
| `/api/adam/restart` | `local_service` | restartuje Adam sluzbu | `confirmed` boolean z UI confirmu | UI pritomnost |
| `/api/adam/stop` | `local_service` | zastavi Adam sluzbu | `confirmed` boolean z UI confirmu | UI pritomnost |
| `/api/voice-mode/start` | `local_service` | spusti voice watcher | pevny argv workflow; bez confirmu | UI pritomnost |
| `/api/voice-mode/stop` | `local_service` | zastavi voice watcher PID | kontrola beziciho PID; bez confirmu | UI pritomnost |
| `/api/voice-mode/approval` | `private_write` | ulozi rozhodnuti k cekajicimu hlasovemu pokynu | rozhodnuti approve/reject v payloadu; bez dalsi fraze | voice mode tests |
| `/api/voice-mode/codex-approval/clear` | `private_write` | vycisti kartu cekani na Codex potvrzeni | `confirmed` boolean | UI pritomnost |
| `/api/voice-mode/safe-readonly/run` | `read_only_via_post` | spusti allowlistovanou read-only kontrolu | `SAFE_READONLY_CAPABILITIES` allowlist | prime testy allowlistu |
| `/api/dev-runner/run` | `dev_runner` | spusti allowlistovany vyvojovy prikaz | `DEV_RUNNER_ACTIONS` pevny argv allowlist | prime testy allowlistu |
| `/api/desktop-apps/open` | `local_open` | otevre allowlistovanou desktop aplikaci | `DESKTOP_APP_CATALOG` allowlist | prime testy allowlistu |
| `/api/voice-bridge/marker` | `private_write` | prepise voice marker TTY | validuje TTY proti aktivnim Codex relacim; bez confirmu v route | castecne pres bridge testy |
| `/api/voice-bridge/terminate-stale` | `local_service` | ukonci stare Codex procesy mimo chraneny TTY | preview + `confirmed` boolean | prime testy confirmation |
| `/api/cockpit/restart` | `local_service` | restartuje Cockpit server | `confirmed` boolean + kontrola aktualniho procesu | prime testy confirmation/safe process |
| `/api/projects/lifecycle` | `private_write` | meni stav projektu v `ACTIVE_PROJECTS.md` | `confirmed` boolean | prime testy lifecycle |
| `/api/samantha/open` | `local_open` | otevre Samantha chat v Terminalu | pevny terminal command; bez confirmu | neprime |
| `/api/codex/open` | `local_open` | otevre Codex CLI v Terminalu | pevny terminal command; bez confirmu | neprime |
| `/api/reminders/done` | `private_write` | oznaci pripominku jako splnenou | helper vklada vlastni potvrzovaci text, UI bez rucni fraze | UI pritomnost + neprime |
| `/api/reminders/cancel-payment` | `private_write` | zrusi platebni pripominku, muze pracovat s evidenci | bez explicitni confirm v route | neprime |
| `/api/urgent-reminders/done` | `private_write` | oznaci urgentni pripominku jako splnenou | bez explicitni confirm v route | UI pritomnost |
| `/api/consistency/resolve-finding` | `private_write` | zapise vyreseni consistency nalezu | `confirmed` boolean uvnitr helperu | prime testy confirmation |
| `/api/reminders/source` | `read_only_via_post` | cte zdroj pripominky/detail | bez confirmu; vraci redigovane/safe detaily | prime testy zdroju |
| `/api/documents/open` | `local_open` | otevre PDF dokument | safe document id/cesta | UI pritomnost |
| `/api/documents/print/prepare` | `print` | pripravi kopii do tiskove fronty | preflight tiskarny; bez finalniho tisku | prime print tests |
| `/api/documents/print/run` | `print` | posle print job na tiskarnu | presna veta `Potvrzuji, vytiskni print job ...` | prime print tests |
| `/api/documents/lifecycle` | `delete_or_purge` | presun dokumentu do archivu/kose | presna veta pro archiv/kos | prime lifecycle tests |
| `/api/documents/reading-status` | `private_write` | zapise stav cteni dokumentu | bez explicitni confirm | UI pritomnost |
| `/api/library/archive` | `private_write` | stahuje URL a uklada clanek do knihovny | validace URL/kategorie; bez confirmu | prime helper tests |
| `/api/library/text` | `private_write` | uklada vlozeny text do knihovny | validace textu; bez confirmu | prime helper tests |
| `/api/library/attachment/add` | `private_write` | pripoji obrazek k polozce knihovny | helper vola potvrzeno pevnou frazi; UI bez rucni fraze | prime helper tests |
| `/api/library/delete` | `delete_or_purge` | vyradi polozku knihovny do soukromeho kose | `user_confirmed` + potvrzovaci text | prime helper tests |
| `/api/lekarna/retire/preview` | `read_only_via_post` | ukaze nahled vyrazeni leku | bez zapisu; vraci potvrzovaci frazi | prime helper tests |
| `/api/lekarna/retire/apply` | `private_write` | zapise vyrazeni leku | `user_confirmed` + presna potvrzovaci fraze | prime helper tests |
| `/api/lekarna/import/draft` | `external_ai` | OCR/fotky z Downloads, pri OpenAI backendu ven do API | presna fraze pro OpenAI vision draft | prime helper tests |
| `/api/lekarna/import/apply` | `private_write` | prijme navrh na sklad, kopiruje/renamuje/zapisuje CSV | presna potvrzovaci fraze | prime helper tests |
| `/api/library/read-state` | `private_write` | zapise stav cteni clanku | bez explicitni confirm | prime helper tests |
| `/api/library/export/prepare` | `private_write` | pripravi PDF export knihovny lokálně | bez odeslani; vraci potvrzovaci text | UI pritomnost |
| `/api/library/export/send` | `external_send` | odesle PDF export e-mailem | `user_confirmed` + presna potvrzovaci veta | UI pritomnost + helper gate |
| `/api/documents/classification-metadata` | `private_write` | zapisuje metadata dokumentu/indexu/manifestu | UI confirm; route nema `confirmed` parametr | prime metadata tests |
| `/api/documents/classification-suggestion/accept` | `private_write` | prijme automaticky navrh metadata dokumentu | `confirmed` boolean | prime suggestion tests |
| `/api/documents/due-reminder` | `private_write` | vytvori pripominku z dokumentu/e-mail archivu | `confirmed` boolean, helper pak pouzije vlastni frazi | prime due reminder tests |
| `/api/documents/intake-email-scan` | `read_only_via_post` | nacte kandidatni e-maily pro intake | read-only scan, limity/days/known ids | prime scan tests |
| `/api/email-processing/decision` | `private_write` | ulozi pracovni rozhodnuti k e-mailu | bez explicitni confirm; nejde o fyzicky zasah do mailu | UI pritomnost |
| `/api/email-processing/read-message` | `read_only_via_post` | nacte telo vybraneho e-mailu read-only | provider/UID/max chars limit | prime detail tests |
| `/api/email-processing/preview-attachment` | `read_only_via_post` | nacte preview prilohy read-only | provider/UID/part id | UI pritomnost |
| `/api/email-processing/process-batch` | `private_write` | uklada e-maily/PDF lokalne; u kose muze presunout e-mail do kose | davkovy UI confirm; pro trash presna potvrzovaci veta | prime batch/trash tests |
| `/api/email-processing/purge-trash` | `delete_or_purge` | trvale maze e-maily z kose provideru | presna potvrzovaci veta podle poctu e-mailu v davce | prime purge tests |
| `/api/email-processing/new-headers` | `read_only_via_post` | nacte nove hlavicky e-mailu | read-only limity/days/known ids | prime header tests |

## Silne ochrany

- `SAFE_READONLY_CAPABILITIES` a `DEV_RUNNER_ACTIONS` jsou dobry vzor: pevny registr,
  zadny volny shell ani volne capability id.
- Tisk ma spravny dvoukrok: prepare nevytiskne, run vyzaduje presnou frazi navazanou na print job.
- Dokument lifecycle ma presnou frazi pro archiv i kos.
- Lekarna import/apply a retire/apply maji explicitni potvrzovaci fraze.
- Knihovni PDF send ma pripraveny export a rucni opis potvrzovaci vety.
- E-mail batch trash ma presnou frazi podle poctu polozek.
- Voice bridge terminate-stale ma preview, chrani aktualni TTY a ukoncuje jen nezachranene relace.

## Slabsi mista

1. `app/cockpit.py` nema jeden katalog endpoint -> risk -> gate -> tests. Matice je zatim dokumentacni, ne vynucovana kodem.
2. Nektere `private_write` akce nemaji explicitni backend confirm:
   - `/api/reminders/done`
   - `/api/reminders/cancel-payment`
   - `/api/urgent-reminders/done`
   - `/api/documents/reading-status`
   - `/api/library/archive`
   - `/api/library/text`
   - `/api/library/read-state`
   - `/api/email-processing/decision`
3. Nektere akce spoléhaji na UI `window.confirm`, ale backend bere jen boolean:
   - `/api/projects/lifecycle`
   - `/api/cockpit/restart`
   - `/api/adam/restart`
   - `/api/adam/stop`
   - `/api/voice-mode/codex-approval/clear`
   - `/api/documents/classification-suggestion/accept`
   - `/api/documents/due-reminder`
4. Voice input routy nemaji potvrzeni primo v Cockpitu; bezpecnost stoji na terminal bridge
   triage. To je prijatelne, ale melo by to byt explicitne uvedene v budouci capability registry.
5. `local_service` start/stop akce maji rozdilnou uroven bran. Start bez confirmu je prakticky,
   ale restart/stop by mely mit sjednoceny audit zaznam.

## Doporučení pro bod 3

1. Zalozit maly kodovy registr `COCKPIT_POST_ACTIONS` s poli:
   `path`, `label`, `risk`, `writes`, `external_effect`, `confirmation`, `handler_name`,
   `test_level`.
2. Pridat test, ktery porovna routy v `do_POST` proti registru. Prvni verze muze jen hlidat,
   ze kazda POST cesta ma zaznam.
3. Pridat frontend/backend kontrakt test: endpointy volane z HTML/JS musi existovat v backendu.
4. Pro nejrizikovejsi endpointy postupne prejit z boolean confirmu na pojmenovanou potvrzovaci
   branu:
   - `exact_phrase`
   - `ui_confirm_only`
   - `allowlist_only`
   - `none_readonly`
5. `/api/email-processing/purge-trash` uz byl zpevnen: ostrou akci povoli jen
   `confirmed: true` spolecne s presnou frazi podle poctu e-mailu v davce.

## Navazujici krok

Bod 3 by mel byt maly, mechanicky a testovatelny:

- Nevytahovat hned `do_POST` z monolitu.
- Nejdrive jen pridat registry metadata a test, ze 56 POST cest ma rizikovou kartu.
- Teprve potom resit refaktor handleru nebo UI.
