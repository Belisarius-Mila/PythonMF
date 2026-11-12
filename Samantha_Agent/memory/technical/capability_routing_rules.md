# Capability routing rules

## ScienceNews — 03/K4 (2026-11-09)

Proud `project-knowledge-library`, pravidla `science_news.md`. Čtení fronty:
`app.cockpit_science_news.science_news_overview`; vyřízení zprávy:
`science_news_decision_action` s explicitní akcí save/follow/dismiss a stabilním
request_id; vypnutí sledování: `science_news_unfollow_action`; překlad celého
ověřeně oprávněného textu: `science_news_translate_action`. Čtení stavu překladu
nikdy nespouští nový modelový tah. Trasy jsou registrované v COCKPIT_POST_ACTIONS.

`app.science_news_cached_translation.attach_and_save` je neplacený přenos jednoho
předem ověřeného celého českého překladu a výslovně zadané uložení. Volající
předá konkrétní store (fronta i archiv), item_id, původní URL, ověřené zdrojové
znění a překlad, oba SHA-256, oprávnění, stabilní request_id a confirmed=True.
Kontroluje existující rozhodnutí/operace a nejisté překlady; nepřepisuje cizí
kartu ani text. Použije sdílený archivní zámek a stávající idempotentní save,
který zapne sledování. Nespouští model, nic nemaže a neaktivuje plánovač.

`app.science_news_activation.prepare(runtime_root=...)` zapisuje pouze neplacený
soukromý návrh v pracovním stromu. `activate(proposal_sha256=..., confirmation=...)`
vyžaduje přesnou větu z global_safety_brake.md a schválení navržených 15 kreditů/job,
100/měsíc (dokončená usage + rezervy nedokončených, nikoli upstream billing cap).
Předem musí být nasazená přesná role, cenová kontrola účtu a skutečně servírovaná
UI ochrana ukládání celého českého překladu. Instalace jediného LaunchAgentu
má trvalou účtenku před bootstrap; nejistý bootstrap se podruhé neodesílá.
Není to oprávnění k push/deploy ani k přepisování cizích modelových rolí.

Samostatný jednorázový kandidátní pilot: `app.science_news_trial.preview()` je
neplacené čtení zmrazeného zdroje, vstupu, kódu, cen a jejich SHA-256.
`app.science_news_trial.run(confirmed=True, approved_report_sha256=...,
approved_packet_sha256=..., approval_ref=...)` vyžaduje výslovný souhlas s touto
konkrétní zkouškou. Použije jen gpt-6.1-sol/medium Standard, sdílený socket,
prázdný ephemeral read-only kontext bez nástrojů. Před spojením zapíše jedinou
trvalou účtenku. Neznámý/vadný/opožděný výsledek neopakuje, hotový pouze vrátí.
Přijímací mez 5 kreditů není provider billing cap. Nemění role JSON, neaktivuje
editor ani plánovač, nečte historii a nepíše do živé fronty ani archivu.
Podklady a účtenka zůstávají v Datově private worktree; nejde o veřejný Cockpit endpoint.

Kreditový pilot před vytvořením vlákna ověří `account/read` bez refreshToken:
jen `type=chatgpt`; API klíč a neznámý účet blokují placený tah. Celý účet,
e-mail ani jiné identifikační údaje se do podkladů nebo účtenky nekopírují.

Shell registr má přesné `science_news_status`, `science_news_preview`,
`science_news_service_preview` a samostatně potvrzovaný `science_news_tick`.
Preview nevolá model a náhled služby ji neinstaluje. Scheduled tick lze spouštět
až po samostatné aktivaci role, ceny, zkoušky, rozpočtu a plánovače. Vývoj ani
kalibrační souhlas tyto brány nenahrazují; nejisté joby se neopakují.

Zalozeno 2026-05-19.

## Smysl

Samantha ma prijimat bezne lidske pokyny a prevadet je na bezpecne registrovane
schopnosti. Toto pravidlo plati pro vsechny soucasne i budouci projekty.

## Obecny postup

1. Pochopit zamer z bezne cestiny.
2. Pojmenovat, jak Samantha pokyn pochopila.
3. Vybrat registrovanou schopnost/tool/workflow.
4. Strucne rict bezpecnostni rozsah:
   - co bude cist,
   - co bude zapisovat,
   - co urcite nebude delat.
5. Pokud jde o zapis, obnovu, odesilani, mazani, citlive cteni nebo shellovy
   workflow prikaz, vyzadat potvrzeni podle pravidel dane schopnosti.
6. Spustit pouze registrovanou schopnost, ne ad hoc improvizovany prikaz.

## Volba miry rezie

Pred novym ukolem ma Samantha nebo Codex zvolit primerenou miru workflow rezie:

- maly, rychly a snadno opakovatelny ukol: primy krok bez manifestu,
- stredni ukol s vice soubory nebo vystupy: lehky manifest/log/summary,
- dlouhy, sitove citlivy, hromadny, drahy nebo soukromy ukol: plne
  checkpointovane workflow podle `memory/technical/session_recovery_rules.md`.

Cilem je nepretezovat male ukoly zbytecnou strukturou, ale u delsi prace mit
navazatelnost po reconnectu, padu Codexu nebo castecne chybe.

## Typy schopnosti

### Python tools

Pouzivat pro bezpecne aplikacni operace uvnitr Samanthy, napr. e-maily,
reminders, memory, lokalni vaulty a obnovu souboru.

Tool musi mit vlastni bezpecnostni pravidla a testy. Pokud pracuje s citlivymi
daty, musi mit potvrzovaci gate.

### System reports

Pouzivat pro kratke ad hoc systemove prehledy, ktere Mila potrebuje spustit
opakovaně a nechce si pamatovat jejich presne nazvy.

Aktualni registrovane reporty:

| Zamer v bezne reci | Registrovana schopnost | Bezpecnostni rozsah |
| --- | --- | --- |
| Smazat jednu konkrétní událost z kalendáře | `app.calendar_delete.CalendarDeletion.execute` přes `/api/calendar/delete` | prepare jen čte, přesná časově omezená serverová identita; delete vyžaduje konkrétní potvrzení, scope/revizi a shodnou nativní identitu. Pouze jeden výskyt bez účastníků/organizátora, trvalý marker bez retry; status/recover nemazají. Nikdy hromadné mazání ani automatické mazání při testu. |
| Jednou připravit a povolit samostatný mazací helper | `app.calendar_delete.CalendarDeleteHelper.build(confirmed=True)/authorize_current(confirmed=True)` | pouze výslovné tlačítko na Macu, nový oddělený podepsaný helper a OS souhlas. Původní reader/writer se nemění. Syntetický build/self-test v izolovaném adresáři nepřistupuje ke kalendářům. |
| Označit položku kalendáře Splněno | `CalendarAgenda.execute(action="set_completed")` přes `/api/calendar/agenda` | Jen soukromý filtr Cockpitu, trvalá revize a přesný výskyt; nativní kalendář ani kontrola kolizí se nemění. |
| Editovat název, datum a čas jedné události | `CalendarEditing.execute` přes `/api/calendar/edit` | Serverový náhled a potvrzené změny původní události, zachované ostatní údaje; pouze tento výskyt bez účastníků, samostatný helper a explicitní OS povolení. Trvalý claim před zápisem, při nejistotě jen read-only recovery, společná blokace edit/delete. |
| Náhled smazání jednoho podkladu Ateliéru | `InteriorAtelier.deletion_preview` přes `/api/interior/delete-preview` | read-only přesný podklad/místnost, počet a velikost vlastněných souborů, sdílení a dopad; bez modelu a smazání |
| Trvale smazat jeden podklad Ateliéru | `app.interior_cleanup.delete_source` přes `InteriorAtelier.execute(action="delete_source")` a `/api/interior/action` | přesná globální věta + token rozsahu, žádné libovolné cesty; neukončená AI blokuje, sdílené objekty/texty/externí kopie zachované. Trvalý záznam před unlink, stejné potvrzení dokončí zbývající soubory bez nového modelu. Pouze explicitně potvrzené smazání, žádný automatický úklid. |
| "Jaky je stav Samanthy?", "health check", "mame cisty stul?" | `samantha_health_check(mode="quick")` | cte memory index, aktivni projekty a git status; nezapisuje |
| "Kvantitativni status", "kolik mame souboru/radku?", "objemovy rust" | `samantha_quantitative_status(save=False)` | cte agregovane souborove statistiky mimo soukroma data; bez `save=True` nezapisuje |
| "Uloz kvantitativni snapshot" | `samantha_quantitative_status(save=True)` | ulozi jen agregovanou JSONL datovou vetu bez nazvu souboru a soukromeho obsahu |
| "Jake mame systemove reporty?" | `samantha_system_reports()` | vypise registr reportu; nezapisuje |
| "Kdo provede p+n?" | `app.communication.luna_release.resolve_release_executor()` | read-only centrální schválená role a aktuální katalog, bez modelového tahu; stejný výběr pro portál i nativní delegaci |
| "Otestuj cenově posouzeného nástupce vykonavatele" | `app.communication.luna_release.probe_release_executor_candidate(model, reasoning_effort)` | jen výslovně určený kandidát, pevný syntetický read-only vstup; nezmění roli, nepřevezme skutečný balíček a nepublikuje |
| "Připrav balíček pro Lunu" | `app.communication.luna_release.audit_release(...)` | read-only rozsah commitů, aktivní projekt a registrovaný cíl; v přímé relaci bez argumentu `service`; bez modelového tahu a publikování |
| "p+n přes Lunu" | `app.communication.luna_release.submit_release(...)` | jeden programový vstup pro všechny proudy; potvrzený projekt a lokální head, origin/cíl/role z auditu. Bez nativního modelového prostředníka. Původní brány, terminál wait=True a stejný volající, portál asynchronně do původního vlákna; opakování stejné identity vrací původní účtenku |
| "Počkej na tuto účtenku p+n" | `app.communication.luna_release.wait_for_release(job_id)` | programové čekání připnuté k job ID, bez modelu, publikace a retry; timeout stav nepřepíše |
| "Co Samantha umi?", "audit schopnosti", "kde jsou workflow rezervy?" | `samantha_capability_audit()` | cte registr toolu a workflow; nezapisuje |
| "Je Rodinny kalendar pripraveny na automatiku?", "readiness kalendare" | `family_calendar_delivery_readiness()` | cte jen validaci private konfigurace, agregovane dorucovaci stavy, metadata planovace a existenci Keychain polozky; necte heslo, nezapisuje, nerecoveruje a neodesila |
| "Udelej aktualni systemovy audit", "audit projektu/toolu/vrstev", "na cem dnes navazat?" | `samantha_project_audit(mode="quick", save=False)` | cte jen git-safe pametove registry a systemove reporty; necte private vault, e-maily ani soukrome dokumenty |
| "Uloz aktualni systemovy audit" | `samantha_project_audit(mode="full", save=True)` | zapise git-safe textovy report do `memory/reports/`; bez private obsahu |
| "Co je v knowledge inboxu?", "velke podklady", "archiv chatu k prostudovani" | `samantha_knowledge_inbox_inventory()` | vypise jen metadata souboru v private inboxu; necte obsah |
| "Co mam ve Stazenych pro knowledge inbox?", "najdi podklady v Downloads" | `samantha_downloads_inventory()` | vypise jen metadata top-level souboru ve Stazenych; necte obsah |
| "Prekopiruj vybrane soubory ze Stazenych do knowledge inboxu" | `copy_downloads_files_to_knowledge_inbox(...)` | kopiruje jen vybrane relativni soubory z Downloads do private inboxu az po potvrzeni |
| "Chci iPhone zkratku", "vytvor Apple Shortcut", "stav Shortcuts Playground" | `iphone_shortcuts_playground_status()` nebo `prepare_iphone_shortcut(...)` | status je read-only; private request draft se zapisuje az po potvrzeni a realny `.shortcut` se musi rucne overit |
| "Stav pameti", "priority", "pripomenuti" | `memory_status()` | cte jen bezpecnou lokalni memory diagnostiku; nezapisuje |
| "Náhled rutinní kontroly dokumentace" | `app.routine_tasks.route_routine_task("report_documentation_review")` | přesný typ a role bez modelového tahu; neznámý typ vrátí Adamovi |
| "Prověř dokumentaci reportů Solem" | `app.routine_tasks.run_routine_task("report_documentation_review", confirmed=True)` | po souhlasu jeden čtecí modelový tah nad pevnými veřejnými podklady; bez změn zdrojů, opakování a publikace |
| "Ověř kandidáta rutinního kontrolora" | `app.routine_tasks.probe_routine_reviewer(model, reasoning_effort)` | jen po cenovém posouzení a výslovné volbě modelu; pevný syntetický vstup, neschvaluje ani nemění roli |
| Připrav jednorázovou kalibraci správce obnovy | `app.recovery_guide_trial.prepare()` | neplacená pevná syntetická karta, čtecí RPC; zapisuje jen kartu ve vlastní .venv, nespouští thread/turn/službu |
| Spusť konkrétně schválenou kalibraci správce obnovy | `app.recovery_guide_trial.run(approved_digest=...)` | jeden kandidátní Sol/medium Standard tah nad pěti syntetickými záznamy; přesný souhlas, trvalý slot bez retry, žádný skutečný TXT/korpus/publikace/aktivace; přijímací meze nejsou tvrdý fakturační strop |
| Připrav úplný čtecí pilot obnovy | `app.recovery_guide_full_pilot.prepare(project_only=False)` | čte celý původní TXT a vybrané Git bloby připnutého main; neplacená neměnná karta ve vlastní .venv, bez thread/turn/služby; scope lze výslovně zúžit před přijetím |
| Obnov přípravu úplného pilotu po změně zdrojů, ještě před jakýmkoli pokusem | `app.recovery_guide_full_pilot.prepare(project_only=False, refresh=True)` | jen bez attempt/controller/turns; zachová starou kartu i limit, uloží nový manifest pod vlastním digestem; všechny verze sdílejí jeden job, žádné resetování nebo přijetí nové karty modelem |
| Převzít prokázanou první účtenku s přesně nadbytečným original_guide a dokončit schválené zbývající kroky | `app.recovery_guide_receipt_recovery.prepare()/resume(approved_digest=...)` | pouze jednoznačně completed/delivered první tah s přesnými citacemi a známou spotřebou; lokální převzetí, SDK až od dávky 2, stejný job/zdroje/200 limit; bez retry nejistoty, resetu nebo obsahového přijetí návodu |
| Spusť přesně schválený úplný čtecí pilot obnovy | `app.recovery_guide_full_pilot.run(approved_digest=...)` | konkrétní souhlas s rozsahem, marží a cenou; jedna úloha s předem plánovanými dávkami/syntézou, Standard per-turn, trvalé markery bez retry i další týden; jen kandidát, žádná publikace TXT, aktivace role/služby nebo tvrdý fakturační cap |
| Připravit / aplikovat konkrétní aktivaci týdenního správce | `app.recovery_guide_activation.prepare/activate` | prepare pouze inertní privátní balíček bez role/služby/provozních TXT/modelu. activate jen přesný SHA a globální brzda pro tuto konkrétní instalaci a navržený rozpočet; roli/politiku, dvě přijaté kopie a upload ověří před jediným bootstrap. Nejistý bootstrap se znovu neposílá, cizí změny blokují; první placený slot musí být budoucí |
| Stav / běh propojeného správce obnovy | `app.recovery_guide_runtime_live.entry("status"/"run"/"tick")`; workflow `recovery_guide_run` / `recovery_guide_tick` | status bez zápisu/tokenizeru/socketu/modelu; run/tick pouze s již přijatou privátní aktivací, rozsahem, kontextem, přesnou centrální rolí a rozpočtem. Ruční workflow vyžaduje potvrzení; služba se neinstaluje. Jeden společný slot, raw před kontrolou, žádný retry nejistoty |
| Připravit / potvrdit konkrétní týdenní publikaci | `app.recovery_guide_runtime.RecoveryRuntime.prepare_acceptance/accept` | výhradně trusted dossier/ReviewContext, přesný binding a identita již vytvořeného jobu; nový konsolidovaný gate i aplikační přejímka, žádný model ani implicitní publikace. Další tick dokončuje pouze přijaté stejné bajty na pevných cílech |
| Připravit nebo ověřit sjednocenou týdenní revizi návodu | `app.recovery_guide_consolidation.prepare/schema/validate` | čisté API nad zmrazeným snapshotem a trusted datem, úplné dispozice bloků, přesné citace, ochrana procedur/soukromí a jediný čtenářský text; žádný model, transport, souborový zápis nebo publikace. Výchozí `maintainer.run` kontrakt používá; staré pevné piloty explicitně legacy, bez resetu či fallbacku |
| Offline katalog a kontrakt přesných citací správce obnovy | `app.recovery_guide_anchors.Catalogue`; `app.recovery_guide_anchor_protocol.inspection_request/resolve_inspection/synthesis_request/validate_synthesis` | čisté Python API nad callerem určeným zmrazeným snapshotem; ID pouze s SHA katalogu/requestu, úplné čtení a původní quality gate; bez SDK, zápisů, oprávnění k placenému tahu či publikaci |
| Ověřit anchor regresi na uloženém REC-06 v2 | `app.recovery_guide_anchor_audit.audit_saved()` | čte jen pevný historický packet, dvě raw účtenky a již doložené case návrhy ve vlastní .venv/projektovém reportu; vytváří fixture, nepřijímá staré notes a nemění job/receipt; žádný model ani retry |
| Připravit malou cenovou kartu anchor protokolu | `app.recovery_guide_anchor_trial.prepare(refresh=False)` | neplacené čtecí RPC nad existujícím sdíleným socketem, celý původní TXT a dva pevné Git dokumenty; karta jen ve vlastní .venv. Explicitní refresh jen před jakýmkoli attempt/context/turn; bez role/služby/modelu |
| Spustit přesně přijatý malý anchor test | `app.recovery_guide_anchor_trial.run(approved_digest=...)` | trusted souhlas s konkrétní kartou/cenou a nejvýše dvěma Sol/medium Standard tahy; jeden job napříč revizemi, žádný retry/resume/reset, pouze privátní raw receipts. Přijímací meze nejsou fakturační cap; žádný celý korpus, publikace TXT či aktivace |
| Spočítat neplacený plán celého anchor korpusu | `app.recovery_guide_anchor_full_plan.prepare(refresh=False)`; `measure/inspection/validate_inspection/synthesis` | celé připnuté veřejné Git zdroje + původní TXT, reference tokenizer jen ve vlastní izolaci, čtecí runtime projection; immutable soukromý plán a offline bounded kontrakty. Žádný run, thread/turn, placený souhlas, writer, aktivace či obnovení starých jobů |
| Připravit exekuční kartu celého anchor pilotu / číst přesný stav | `app.recovery_guide_anchor_full_pilot.prepare(plan_digest=..., refresh=False)` / `status()` | prepare pouze neplacený audit/čtecí RPC, pevný soukromý packet; refresh jen před attempt/context/turn. status pouze čte vlastní atomic receipt, bez zápisu, modelu či RPC; žádná role/aktivace/publikace |
| Spustit přesně přijatý celý anchor pilot | `app.recovery_guide_anchor_full_pilot.run(approved_digest=...)` | trusted konkrétní souhlas s celým manifestem a cenou; jeden pevný job přes všechny revize, raw před přejímkou, Standard per-turn, žádný reset/resume/retry ani po nejistotě/novém týdnu. Pouze soukromý kandidát, žádný operating TXT/iCloud/role/služba; přijímací rezervy nejsou billing/output/wall-clock cap |
| Neplacená validace uvnitř celého anchor adapteru | `app.recovery_guide_anchor_full_worker.perform/dispatch` | pouze izolovaný tokenizer proces a private pipe: přesné requesty, všechny raw dávky, bounded citace/findings a původní quality gate; žádný transport, model, zápis nebo oprávnění k akci |
| Offline přesné source/citation domény a nové nacenění | `app.recovery_guide_anchor_exact_schema.ReferenceIndex/inspection/resolve_inspection/synthesis/validate_synthesis/schema_stats`; `app.recovery_guide_anchor_exact_plan.prepare/measure` | nové číselné request-local reference s přesným integer rozsahem zdroje, původní resolver/quality/budget kontroly; celé veřejné Git texty a original jen ve vlastní privátní .venv. Žádný model/run, oprava staré raw odpovědi, obnovení jobu či publication grant |
| Připravit aktuální kartu přesného číselného pilotu / číst stav | `app.recovery_guide_anchor_exact_pilot.prepare(plan_digest=..., refresh=False)` / `status()` | neplacený audit přesné revize plánu a pouze čtecí RPC existujícího sdíleného socketu. Vlastní pevný job odlišný od uzavřeného string-ID pilotu; immutable karta, refresh jen před pokusem. status bez zápisu a RPC |
| Spustit nově schválený přesný číselný pilot | `app.recovery_guide_anchor_exact_pilot.run(approved_digest=...)` | nový konkrétní souhlas s kartou, celým korpusem a cenou; 20 inspect + 1 synthesis dle zmrazeného plánu, Sol/medium/Standard. Jeden job bez reset/resume/retry, raw uložené před validací, přesná request-local mapa. Pouze soukromý kandidát, žádné provozní kopie/iCloud, role, služba či aktivace; staré souhlasy nepřenášet, rezerva není tvrdý billing limit |
| Offline worker přesného číselného pilotu | `app.recovery_guide_anchor_exact_worker.perform/dispatch` | izolovaný tokenizer, reprodukce všech wire/schema/map hashů, úplná historie všech dávek, interní decode a nezměněný quality gate. Žádný model, transport, zápis, oprava raw či pravomoc publikovat |
| "Předej vývoj Luně" (výslovně, i více souborů / jiné jazyky) | `app.luna_development.preview/run/accept` | výslovná volba před heuristikou; pouze vybrané veřejné zdroje, izolované testy, přesný diff a kontrolované převzetí bez Gitu/publikace. Portál přes existující SIMPLE_DEVELOPMENT grant |
| Opravit jedinou nepřesnou citaci původního textu v návrhu Luny | `app.luna_development.review_anchors` | ruční kontrola přesného původního answer digest, změna pouze old; zachovaný new od Luny, nová izolace a testy bez dalšího modelového tahu, žádná změna caller zdrojů |
| Jedna vhodná čistá Python funkce v povoleném vývoji | `app.simple_development.preview/run/accept` | bezplatné deterministické směrování, jedna izolovaná oprava a jednorázové převzetí; root pouze skutečný autorizovaný workspace, role pouze centrální konfigurace |
| Stejná oprava přes Cockpit | `app.simple_development_portal.request` | jen s aktuálním serverovým blokem SIMPLE_DEVELOPMENT; lokální souborový kanál zachová síťový sandbox, server ověří writable tah/projekt/vlákno a nejvýše jeden úkol; bez Git operací |
| Zkouška vývojové role a první aktivace | `app.simple_development_activation.probe_candidate/accept_probe/activation_plan/activate` | skutečný syntetický FAIL → PASS; aktivace pouze po nasazení kompatibilního runtime, čistém main a kontrole přesného důkazu; nemění release_executor ani služby |

Kdyz pri praci vznikne novy opakovatelny ad hoc status, audit nebo report,
Samantha se ma zeptat: "Udelame z toho novy systemovy report?" Pokud Mila
souhlasi, pridat ho do `app/system_reports.py`, `memory/technical/system_reports.md`
a podle potreby do testu.

### Shell workflow registry

Pouzivat pro lokalni prikazy, ktere maji byt spoustene pres shell, napr. zaloha,
build, export, audit nebo davkovy projektovy skript.

Shell workflow musi byt registrovany v:

```text
Samantha_Agent/app/workflows/commands.py
```

Samantha smi spustit jen presne ulozene `argv`. Pred zapisujicim workflow ma
ukazat presny shell a cekat na potvrzeni.

## Priklady

Pokyn:

```text
Najdi e-maily za poslednich 7 dni.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako bezpecny vypis e-mailovych hlavicek za poslednich 7 dni.
Pouziji read-only e-mailovy tool. Prectu jen UID, datum, odesilatele a predmet.
Nebudu cist tela, otevirat odkazy, stahovat prilohy, mazat, presouvat ani
oznacovat jako prectene.
```

Pevny rychly vstup:

```text
Prosím přehled emailů za posledních 7 dní
```

Samantha ho ma mapovat na sjednoceny read-only prehled iCloud + Seznam za
poslednich 7 dni. Vychozi razeni: hlavne zpravy s PDF prilohami nebo signalem
dokumentu/prilohy; kategorie `faktury/e-shopy`, `pojisteni/smlouvy`,
`urady/dane`, `ostatni`; vystup jen hlavicky a kratky duvod dulezitosti.
Bez dalsiho potvrzeni necist cela tela, nestahovat prilohy, neotevirat odkazy,
neukladat PDF, nic neposilat, nemazat, nepresouvat ani neoznacovat jako prectene.

Pokyn:

```text
Zalohuj data projektu.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako recovery zalohu PythonMF/Samantha na externi disk.
Spustila bych tento presny shell prikaz: ...
Potvrzujes spusteni?
```

## Bezpecnostni pravidla

- Nikdy nemapovat lidsky pokyn primo na libovolny shell.
- Pokud neni zamer jasny, zeptat se kratce, misto spusteni.
- Pokud existuje vice kandidatu, vypsat je a nechat Milu vybrat.
- U e-mailu nerozsirovat rozsah cteni bez potvrzeni.
- U obnovy souboru vzdy nejdriv preview, potom potvrzeni.
- U backupu a jinych shell workflow nejdriv ukazat presny prikaz, potom cekat
  na potvrzeni.
- Nove projekty maji pri pridani automatizace dostat bud Python tool, nebo
  shell workflow kartu; ne skryty ad hoc postup.

### 2026-11-07 08:55 CET — zrušený placený hlasový pilot 15/P2

Placený hlasový rozhovor není pro Agenta SDK Samantha relevantní. Schopnosti
probe_voice_candidate a create_voice_candidate_session jsou vyřazené z nabídky;
jejich zdrojový kód i registrace byly po přesném potvrzení odstraněné.
Žádné další placené relace, testy nebo automatická náhrada. Běžné nahrávání
pokynů, předčítání a audio Camina toto rozhodnutí nemění.

## Návrh z e-mailu: kolize a konečný náhled (2026-11-07)

`email_calendar_draft_review` a `email_calendar_draft_confirm` používají
`app.email.calendar_review.CalendarReview.execute` přes explicitní tlačítka
editoru. Čtou jen uložený návrh a vybrané kalendáře v jeho přesném omezeném
intervalu; zapisují pouze soukromý náhled/potvrzení. Bez modelu a kalendářového
zápisu. Revize, zdroj, cíl, upozornění, čerstvé kolize a platnost 5 minut jsou
svázané; změna vyžaduje nový lidský souhlas. Samotné potvrzení není zápisem
události ani oprávněním přeskočit kontroly v budoucím bodu 5.

## 2026-11-11 21:41 CET — ruční evidence hlídaných e-mailových záležitostí

Registrované schopnosti email_followups_read a email_followups_write používají
app.email.followups.EmailFollowups.overview/execute. Cockpit má GET/POST
/api/email-agent/followups a evidovanou private_write akci s výslovným uložením
nebo přepnutím lifecycle. Kořen úložiště vlastní server; payload ho neurčuje.
Příkaz vyžaduje stabilní operation_id a pro změnu očekávanou revizi. Replay
kontroluje totožný otisk a vrací aktuální revizi. Jen ruční metadata a historie;
žádný IMAP, model, monitor, send či kalendářový zápis. API hlásí automatické
monitorování jako nepřipojené. Nasazení/aktivace v této etapě nebyly provedené.


## 2026-11-12 08:32 CET — Závislost hodinové pošty na sdíleném App Serveru

Registrované tick/prepare/upgrade/resume používají schválený modelový výběr.
Po ověření e-mailové role může nově spustit pouze chybějící sdílený Unix runtime
přes LocalAppServerProcessController; start serializuje společný souborový zámek
s Human–Adamem. Funkční server se pouze převezme, nereagující/cizí socket se
bez samostatného zotavení nemění. Samotný start a katalog nevytvářejí vlákno
ani modelový tah. Status/readiness jsou nadále bez zápisu a bez připojení.
Příprava navíc ověří místní podmínky před startem závislosti. Automatické
e-mailové posuzování zůstává pouze součástí původně aktivovaného hodinového
provozu se stejnými rezervami, kurzory a ochranou nejistého výsledku.


## 2026-11-12 — Výslovné zobrazení uloženého zdroje hlídání

Stejná čtecí schopnost email_followups_read při GET /api/email-agent/followups?id=
vrací navíc source_message (jen sender/subject/date/body_text). Čte jediný
snapshot existující cache, ověří účet/provider/složku/UIDVALIDITY/UID/content_digest
proti původní vazbě; chybějící či jiný zdroj vrací null. Žádný IMAP, cesta od
klienta, model ani souborový zápis. Obecný přehled těla neobsahuje, žádná kopie
těla nevzniká v evidenci followups. Frontend používá pouze textContent.


## 2026-11-12 — Serverově vlastněná práce Human–Adam (HA-04)

`human_adam_work_start` používá `HumanAdamProfileManager.submit_work`: POST
/api/human-adam/work/start, explicitní message/client_message_id/workstream_id,
confirmed=true a původní write_intent. Nepřijímá root, model ani sandbox od
klienta. Rychlé202 je doklad přijetí, nikoli modelového doručení. Stávající
/api/human-adam/send je kompatibilní wait nad stejným vlastněným workerem.

`human_adam_work_read` používá WorkController.view přes GET /api/human-adam/work:
projekt a jediné operation_id/client_message_id, nezáporný cursor. Jen malé
metadata, bez Git auditu, raw payloadů, modelu či změny receipt. Mezery vyžadují
resync; odpověď má server_generation. Read při chybě úložiště nesmí předstírat
prázdný přehled. Nový běh se nikdy neodvozuje od absence ve snímku.

`human_adam_work_recover` je výslovné POST /api/human-adam/work/recover s přesným
projektem/operation_id a confirmed=true. Aktualizuje pouze projekci podle
původních cached důkazů a hlásí writes_performed pravdivě. Nevolá nový model,
reconnect ani původní operaci. Chybějící doklad zůstává neověřený. Placené
pilotní tahy, steer/interrupt, fyzická přejímka a p+n mají vlastní oprávnění.
