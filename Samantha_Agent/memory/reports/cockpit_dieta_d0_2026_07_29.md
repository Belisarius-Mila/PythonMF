# Cockpit Dieta D0 - read-only mapa

Datum: 2026-07-29

Rozsah: statická mapa aktuálního `app/cockpit.py` a výběr jediného e-mailového řezu pro D1.

## Bezpečnost a způsob auditu

- Audit četl jen produkční kód, testy, git-safe projektovou dokumentaci a názvy cest.
- Nebyl čten private obsah e-mailů, dokumentů, příloh, poznámek ani archivů.
- Nebyl volán e-mailový provider ani zapisující HTTP endpoint.
- Nebyl proveden e-mailový nebo dokumentový zápis, reindex, přesun, mazání, nasazení ani restart.
- Jediným zápisem D0 je tento git-safe report. Produkční a testovací kód zůstal beze změny.

## 1. Aktuální měření monolitu

`app/cockpit.py`:

| Metrika | Aktuální stav | Poslední údaj v roadmapě | Rozdíl |
| --- | ---: | ---: | ---: |
| Fyzické řádky | 19 244 | 20 745 | -1 501 |
| Neprázdné řádky | 18 221 | 19 620 | -1 399 |
| Top-level funkce | 241 | neuvedeno | - |
| Top-level třídy | 2 | neuvedeno | - |
| Importy | 89 | neuvedeno | - |

Obě třídy patří HTTP vrstvě:

- `CockpitHttpError`
- `CockpitServer`

Aktuální `CockpitServer` obsahuje 59 porovnání GET cest a 72 porovnání POST cest.
`COCKPIT_POST_ACTIONS` má 72 rizikových karet. Architektonická baseline v quality
gate je stále horní pojistka 22 465 řádků, 332 funkcí a 2 tříd; není to současné
měření.

Vložený frontend:

| Konstanta | Řádky zdrojového bloku | Přibližná velikost |
| --- | ---: | ---: |
| `EMAIL_ARCHIVE_HTML` | 192 | 9 392 znaků |
| `EMAIL_PROCESSING_HTML` | 1 424 | 68 452 znaků |
| `COCKPIT_HTML` | 7 364 | 358 671 znaků |

Samotné tři HTML konstanty zabírají přibližně 8 980 zdrojových řádků. Jejich
přesun patří až do D2; D1 je nebude měnit.

## 2. Mapa odpovědností

| Oblast | Aktuální umístění | Vyhodnocení hranice |
| --- | --- | --- |
| HTTP infrastruktura | bezpečnostní hlavičky a kontroly host/origin; `CockpitServer`; GET/POST router; čtení JSON; JSON/HTML/binární odpovědi; content type | Patří v monolitu jako transportní vrstva nebo do budoucího neutrálního HTTP modulu. V D1 zůstává beze změny. |
| Registry | katalog desktop/web aplikací; statusové aliasy; metadata dokumentů; `DEV_RUNNER_ACTIONS`; `COCKPIT_POST_ACTIONS` | Katalogy a rizikový registr jsou konfigurační/policy data. POST registr musí zůstat synchronní s routerem a testy. |
| Tenké adaptéry | dekódování query/payloadu, převod typu, volání importované služby, společná HTTP odpověď | Toto je správná budoucí role `app/cockpit.py`. |
| Smíšené adaptéry | lokální funkce, které validují payload, ale zároveň třídí data, řídí workflow, zapisují více úložišť nebo spouštějí proces | Nejsou tenké. Doménová část patří do samostatných služeb; router má ponechat pouze kompatibilní volání. |
| Business logika | Lékárna import/publikace, recovery a projektové souhrny, e-mail processing, připomínky, části dokumentových workflow, tisk/lifecycle, deploy/sync/dev runner | Postupně vyjmout po jednom soudržném řezu. Nemíchat domény ani potvrzovací režimy. |
| Vložené HTML/CSS/JS | hlavní Cockpit, Email Processing, Archiv e-mailu; další generované stránky pro Lékárnu, dokumentovou čtečku a kuchařku | D2. V D1 žádný redesign ani přesun frontendu. |
| Servisní a procesní operace | ScanDocu, terminál, restart, Human-Adam deploy/verifikace, GitHub batch, main sync, dev runner, TTS a transkripce | Router je tenký jen u části volání. Procesní orchestrace, subprocess pravidla a deployment stav nemají dlouhodobě zůstávat v monolitu. |

Hrubé bloky současného souboru:

| Řádky | Odpovědnost |
| --- | --- |
| 1-557 | importy, cesty, katalogy, bezpečnostní a HTTP konstanty |
| 558-1 580 | knihovna, rodinný kalendář a Lékárna; adaptéry smíšené s business logikou |
| 1 583-3 079 | recovery, poznámky, připomínky, projekty a systémový audit |
| 3 082-4 516 | e-mail processing, rozhodnutí, provider čtení, archivace, import příloh, koš a purge |
| 4 519-6 225 | statusy, připomínky, e-mailové/dokumentové zdroje, Archiv e-mailu, dokumentové resolvery a čtečky |
| 6 228-6 916 | generované HTML pro Lékárnu a kuchařku |
| 6 919-7 825 | git/download status, dokumentové workflow, tisk, lifecycle a ScanDocu |
| 7 828-8 525 | servisní a procesní operace, deploy/sync/dev runner, terminál, audio a transkripce |
| 8 528-9 105 | registr POST akcí |
| 9 108-10 245 | HTTP server, router a společné odpovědi |
| 10 277-19 240 | vložené HTML/CSS/JavaScript |

## 3. Dokumentové routy a služby

Čtecí routy:

| URL | Cockpit call-site | Služba / repository hranice |
| --- | --- | --- |
| `GET /documents/read` | dokumentová HTML čtečka | bezpečný resolver indexovaného souboru; lokální HTML generátor |
| `GET /documents/pdf` | binární dokumentová odpověď | bezpečný resolver proti document vault indexu |
| `GET /api/documents/search` | přímé volání | `app.documents.search_service.search_document_index` |
| `GET /api/documents/review-report` | lokální wrapper | `app.documents.review_service` |
| `GET /api/documents/case-detail` | lokální wrapper | `app.documents.case_service` |

Zapisující nebo procesní routy:

| URL | Hlavní služba | Zachovávaná hranice |
| --- | --- | --- |
| `POST /api/documents/open` | bezpečný resolver + lokální open | bezpečné `document_id` |
| `POST /api/documents/print/prepare` | document vault print preflight | pouze příprava, bez tisku |
| `POST /api/documents/print/run` | document vault print job | přesná potvrzovací fráze |
| `POST /api/documents/lifecycle` | lokální lifecycle + index/manifest | přesná fráze; delete/purge riziko |
| `POST /api/documents/reading-status` | dokumentová transakce | private write, stávající backendová validace |
| `POST /api/documents/classification-metadata` | review service + transakce | private write, explicitní UI potvrzení |
| `POST /api/documents/classification-suggestion/accept` | review service + transakce | private write, explicitní přijetí návrhu |
| `POST /api/documents/due-reminder` | due-date service + reminders store | přesná potvrzovací fráze |
| `POST /api/documents/intake-email-scan` | hlavičky providerů + intake filtr | read-only přes POST; žádné tělo ani příloha |

Skutečné adaptéry jsou hlavně routy nad `search_service`, `case_service`,
`review_service`, `intake_service` a `transactions`. Lokální klasifikace,
lifecycle, tisková orchestrace, reminder orchestrace a e-mailový intake filtr
jsou business logika, i když jsou dnes pojmenované jako Cockpit actions.

## 4. E-mailová call-site mapa

### 4.1 Processing a Work Queue

| Route | Lokální služba / orchestrace | Model | Repository / externí hranice |
| --- | --- | --- | --- |
| `GET /api/email-processing/overview` | `empty_email_processing_overview` | slovníkový response model | bez repository |
| `GET /api/email-processing/pending-work` | `email_processing_pending_work_items` | normalizovaný work item, stable key, batch/category model | `read_email_work_decisions` |
| `GET /api/email-processing/pending-purge` | `email_processing_pending_purge_items` | purge work item | `pending_email_purge_items` |
| `POST /api/email-processing/decision` | `save_email_processing_decision` | work item, action, operation ID | `save_email_work_decision` |
| `POST /api/email-processing/done-flag` | `set_email_processing_done_flag` | provider/folder/UID/done | přímý Seznam provider; změna IMAP příznaku |
| `POST /api/email-processing/new-headers` | `new_email_headers_overview` | `EmailHeader` -> normalizovaný work item | iCloud/Seznam read-only provider + work model |
| `POST /api/email-processing/read-message` | `read_email_processing_message_detail` | `EmailMessage`, `EmailAttachmentMeta` | iCloud/Seznam read-only provider |
| `POST /api/email-processing/preview-attachment` | `preview_email_work_queue_attachment_action` | `EmailArchiveSource`, MIME část | read-only provider + lokální MIME parser |
| `POST /api/email-processing/process-batch` | `process_email_work_queue_batch` -> `process_email_work_queue_item` | work item -> `EmailArchiveSource` | provider read; `save_email_archive`; document import; activity state; work repository |
| `POST /api/email-processing/purge-trash` | `process_email_work_queue_purge_trash_batch` -> item | purge identity a confirmation | work repository -> provider permanent delete -> work repository |

Křížová document/e-mail route:

`POST /api/documents/intake-email-scan`
-> `document_intake_email_scan_status`
-> iCloud/Seznam hlavičky jako `EmailHeader`
-> knihovní/document intake filtry a work identity
-> pouze response; bez uložení těla nebo přílohy.

### 4.2 Archiv e-mailu

| Route | Lokální call-site | Model / repository |
| --- | --- | --- |
| `GET /email-archive/` | vrací `EMAIL_ARCHIVE_HTML` | frontend bez repository |
| `GET /api/email-archive/list` | `email_archive_list_status` | čte lokální `metadata.json`; implicitní archivní JSON schema |
| `GET /api/email-archive/detail` | `email_archive_detail_status` | metadata archivu a příloh; dohledání již stažených příloh |
| `GET /email-archive/file` | `respond_email_archive_file` -> `resolve_email_archive_file` | pevný allowlist souborů archivu |
| `GET /email-archive/incoming` | `respond_email_archive_incoming_file` -> `resolve_email_archive_incoming_file` | bezpečný read-only resolver document inboxu |

Prohlížeč archivu nemá vlastní repository. Z `archive_service` používá jen
výchozí kořen archivu; nevolá zapisující `save_email_archive`. Jeho čtecí schema
je dnes implicitně dáno soubory vytvořenými `archive_service`. Work model a work
repository se pro tento řez nehodí a D1 je nemá uměle zavádět.

## 5. Skutečné adaptéry versus business logika

V `app/cockpit.py` mají zůstat:

- dekódování a omezení query parametrů a JSON payloadů,
- mapování URL na jednu službu,
- volba HTTP statusu,
- společné JSON, HTML a binární odpovědi,
- bezpečnostní hlavičky, host/origin kontrola a centrální error boundary,
- rizikový registr POST akcí a jeho shoda s routerem.

Mimo monolit postupně patří:

- e-mailové stable identity, třídění, pending výběry a batch orchestrace,
- provider výběr a převod provider zprávy na archivní zdroj,
- archivace, import příloh, trash a purge workflow,
- read-only katalog a bezpečné resolvery Archivu e-mailu,
- dokumentové lifecycle, klasifikace, tisk a reminder orchestrace,
- recovery/projektové reporty, Lékárna import/publikace,
- restart, deploy, sync a dev-runner procesní orchestrace.

Pouhý název `*_action` neznamená adaptér. Pokud funkce sama rozhoduje pořadí
kroků, třídí doménová data, mění více úložišť nebo provádí rollback/cleanup, je
to business nebo process service.

## 6. Jediný doporučený D1 řez

### Read-only backend prohlížeče Archivu e-mailu

Vyjmout z `app/cockpit.py` do nového `app/email/archive_browser.py` pouze:

- `EMAIL_ARCHIVE_OPENABLE_FILES`,
- `email_archive_list_status`,
- `email_archive_detail_status`,
- `email_archive_file_label`,
- `read_email_archive_attachment_metadata`,
- `downloaded_email_archive_attachments`,
- `resolve_email_archive_dir`,
- `resolve_email_archive_file`,
- `resolve_email_archive_incoming_file`.

V `app/cockpit.py` ponechat:

- všech pět stávajících GET route větví,
- `respond_email_archive_file`,
- `respond_email_archive_incoming_file`,
- společný `respond_local_file_bytes`,
- `EMAIL_ARCHIVE_HTML` a celý jeho CSS/JavaScript.

Proč právě tento řez:

- je soudržný a pouze čtecí,
- nevolá e-mailové providery,
- nearchivuje, neimportuje, neposílá, nepřesouvá ani nemaže,
- nemění žádnou POST kartu ani potvrzovací režim,
- má už dva přímé testy a jasnou path-safety hranici,
- oddělí doménovou čtecí logiku od HTTP transportu bez současného UI redesignu.

Přímé závislosti nového modulu:

- standardní knihovna: `json`, `Path`, `quote`,
- `app.email.archive_service.DEFAULT_EMAIL_ARCHIVE_DIR`,
- `app.email.redaction.redact_email_addresses`,
- z `app.documents.vault`: `DEFAULT_DOCUMENTS_DIR`, `read_json_file`,
  `relative_to_project`, `safe_filename`, `safe_text`,
- úzká lokální mapa content types se stejnými výsledky jako dnešní společný
  Cockpit helper.

Modul nesmí importovat `app.cockpit`, provider, work repository ani zapisující
archivní/documentovou službu.

## 7. Přesný seznam souborů pro D1

Produkční soubory:

1. `app/email/archive_browser.py` - nový read-only doménový modul.
2. `app/cockpit.py` - import nového modulu a zachované tenké GET adaptéry.
3. `scripts/cockpit_quality_gate.py` - přidání nového modulu a testu do plné gate.

Testovací soubory:

1. `tests/test_email_archive_browser.py` - nový přímý test modulu.
2. `tests/test_cockpit.py` - zachování route/UI kompatibility; přesun dnešních dvou přímých doménových testů.
3. `tests/test_cockpit_quality_gate.py` - explicitní kontrola registrace nového modulu a testu v gate.

V D1 se nemají měnit `archive_service.py`, work model, work repository, provider
moduly, document služby ani vložený frontend.

## 8. Zachovávané URL a payloady

| URL | Vstup | Výstup, který se nesmí změnit |
| --- | --- | --- |
| `GET /email-archive/` | bez payloadu | stávající HTML |
| `GET /api/email-archive/list` | query `q`, `limit`; limit 1-500 | `ok`, `count`, `items`, `message`; item: `archive_id`, `uid`, `subject`, `sender`, `date`, `archived_at`, `links_count`, `attachments_count`, `relative_path` |
| `GET /api/email-archive/detail` | query `archive_id` | `ok`, `archive_id`, `uid`, `subject`, `sender`, `date`, `archived_at`, `relative_path`, `files`, `attachments`, `downloaded_attachments`, `message` |
| `GET /email-archive/file` | query `archive_id`, `file` | stejné binární tělo, content type, inline filename, no-store a content length |
| `GET /email-archive/incoming` | query `name` | stejné binární tělo, content type, inline filename, no-store a content length |

Při nenalezení musí zůstat HTTP 404 a JSON s `error=not_found` a bezpečnou
zprávou. Odesílatel zůstává redigovaný. Frontendové odkazy a názvy klíčů se
nesmí změnit.

## 9. Zachovávané bezpečnostní a potvrzovací hranice

- Všech pět cest řezu zůstává GET/read-only; žádná potvrzovací fráze se nepřidává.
- D1 nepřidá route do `COCKPIT_POST_ACTIONS` a nezmění žádnou existující kartu.
- Zůstávají centrální host/origin pravidla, bezpečnostní hlavičky a `no-store`.
- `archive_id` nesmí obsahovat `/`, `\`, začínat tečkou ani uniknout z kořene archivu.
- Archiv musí mít čitelná `metadata.json`.
- Otevíraný archivní soubor musí patřit do pevného allowlistu:
  `body.html`, `body.txt`, `original.eml`, `metadata.json`,
  `attachments/attachments.json`.
- Název stažené přílohy nesmí obsahovat cestu, začínat tečkou ani postrádat
  prefix `icloud_uid_`; výsledná cesta musí zůstat v povoleném inboxu.
- Symlink nesmí umožnit únik mimo povolený kořen.
- D1 nesmí zavolat provider, `save_email_archive`, document import, send, trash
  ani purge.

## 10. Přímé testy a rizika D1

Stávající přímé testy v `tests/test_cockpit.py`:

- `test_email_archive_list_and_detail_expose_local_readonly_files`
- `test_email_archive_file_resolvers_reject_path_traversal`

Nový modul má přímo pokrýt:

- prázdný/neexistující archiv,
- hledání, limit 1-500 a přesný response shape,
- redakci odesílatele,
- nečitelná nebo chybějící metadata,
- allowlist všech pěti archivních souborů,
- traversal a symlink únik pro archiv i přílohu,
- neplatné UID a neplatný prefix přílohy,
- stejné content types a URL,
- důkaz, že čtecí operace nic nevytvoří ani nezmění.

Hlavní rizika:

1. Embedded JavaScript spotřebovává přesné názvy polí a URL.
2. `downloaded_email_archive_attachments` je čtecí vazba do document inboxu.
3. `content_type_for_path` je dnes společný helper v `cockpit.py`; D1 nesmí kvůli
   němu rozšířit řez na obecný HTTP refaktor. Nový modul má použít úzkou
   explicitní mapu se stejným výsledkem.
4. Přesun importů může vytvořit kruhovou závislost; nový modul nesmí importovat
   `app.cockpit`.
5. Path safety musí zůstat založená na `resolve(strict=True)` a kontrole rodičů.
6. Nový test musí být přidán do plné gate; pouhé cílené spuštění nestačí.

## 11. Nejmenší implementační krok

Vytvořit `app/email/archive_browser.py` jen s allowlistem a osmi read-only
funkcemi, doplnit jejich přímé testy a registraci v quality gate. Potom v
`app/cockpit.py` nahradit původní definice importem, ale ponechat route větve,
HTTP respondéry i celý frontend beze změny.

Po implementaci spustit:

1. přímé testy nového modulu,
2. relevantní Cockpit route/HTTP testy,
3. rychlou statickou gate,
4. plnou Cockpit quality gate.

Nasazení, restart a smoke test jsou až samostatný potvrzený krok po D1; nejsou
součástí D0 ani samotné implementace.
