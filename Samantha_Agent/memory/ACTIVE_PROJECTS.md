# Project Registry

Registr projektu a oblasti. Sloupec `Rezim` urcuje viditelnost: `active` je bezna aktivni prace, `paused` je pozastavene a `archived` se zobrazuje jen v archivnim filtru Cockpitu.

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Rodinný kalendář | 1 | active | Potvrzovaná aktivační apply brána je implementovaná a obsažená v nasazeném `main`. Současný živý režim nebyl při P6a čten ze soukromé konfigurace a zůstává neověřený; `partial` a `delivery_unknown` zůstávají fail-closed. | `projects/family_calendar.md` | `handoffs/workstreams/project-family-calendar.md`; `tvbcp/workstreams/project-family-calendar.md` | Provést pouze redigovaný read-only audit živého režimu, readiness a plánovače. Aktivační apply neopakovat podle staré paměti a nic skutečně neodesílat kvůli testu. |
| Commitove odpoledne / git cleanup | A1+ | archived | Akutni cast splnena: velka memory/RAG cleanup davka byla commitnuta a pushnuta jako `ef15589 Clean up Samantha memory handoffs and RAG search`; repo bylo po pushi ciste. Pravidlo do odvolani zustava: pri delsim `git status` nebo zmene projektu navrhnout tematicky commitovy uklid. | `infrastructure/git_checkpoint_protocol.md` | `handoffs/git_commit_cleanup_a1_2026_05_23.md` | Drzet cisty stul; dalsi commitovy uklid navrhnout az pri novych rozpracovanych zmenach, bez `git add .`. |
| Rustova pravidla Samanthy / uklid handoffu | A1+ | archived | Prvni velka handoff compression davka hotova a pushnuta: Dokumenty, Lekarna, PictNew/VocabularyIT, Tomik/FamilyVideoOrganizer, E-mail, Samantha/RAG a automaticke ukoly maji kanonicky stav a stare mezistavy jsou presunute do historickych sekci. Systemove reporty a infrastructure operating model jsou zalozene. | `technical/samantha_growth_rules.md`; `infrastructure/operating_model.md` | `handoffs/memory_cleanup_commit_afternoon_checkpoint_2026_05_23.md` | Pri dalsim rustu drzet pravidlo: novy opakovatelny status/audit nejdrive nabidnout jako systemovy report; velke cleanupy koncit malym commitem a pushem. |
| MMTX | 1 | active | Aktivni vyukova aplikace pro Matyska; webovy smer v `docs/` ma hotove sceny az po `HouseBunny` a ForestSchool je napojena na 12 lekci. Forest Journey story bible a obrazky jsou odsouhlasene a prvni implementacni pruchod `Scene 1 - Clearing Meeting` je zapojeny jako webova scena `clearingMeeting`. Dne 2026-06-02 vznikl lokalni F5-TTS wrapper pro hlasy a dne 2026-06-03 byly zafixovane reference Benji, Bunny, Bruno, Fiona a Sunny. Sunny je po castingu zafixovany na `young_nova`; dve Sunny repliky v prvni scene jsou nasazene do produkcniho `docs/` i mirroru. Zaverecny prompt prvni sceny je opraven na anglickou vetu `Great. Open the door or run again.` s navazujici ceskou vetou jen ve finale. Dne 2026-06-26 byla Forest Journey scena 2 `Sunny's Lost Nuts` upravena bez velkeho start tlacitka, s kompaktnim layoutem bez samostatneho zahlavi/zapati a s hlavni napovedou jen cesky; prvni klik do sceny odemyka audio a pak bezi anglicke MP3 repliky. Dne 2026-06-29/30 Mila potvrdil, ze tento retest a navazujici opravy sceny 2 uz byly vyresene. Dne 2026-06-30 vznikla Forest Journey scena 3 `Journey to the Lake` jako samostatny webovy modul se 6 obrazovymi fazemi: rozcesti s havranem, kun u statku a pumpa s Fioninou hadankou; scena 2 na ni prechazi pres dokoncovaci bublinu `Next: Journey to the Lake`. Tentyz den byly do sceny 3 nasazene Edge Neural MP3 pro vsechny anglicke dialogy, UI instrukce, napovedy a slovnicek; ceske napovedy a preklady zustavaji pres fallback. Dne 2026-07-01 Mila potvrdil rucni webovy retest sceny 3 jako splneny; scena je funkcne OK, jen Benjiho hlas ma neblokujici rezervy. | `projects/mmtx_story_hotspot_app.md`; `projects/matysek_english_game_concept.md`; `technical/matysek_f5tts_voice_workflow.md` | `handoffs/matysek_forest_journey_voice_strategy_2026_06_01.md`; `handoffs/matysek_f5tts_bunny_voice_tool_checkpoint_2026_06_02.md`; `handoffs/matysek_scene_01_clearing_meeting_review_2026_06_01.md`; `handoffs/matysek_scene_01_sunny_voice_and_ending_2026_06_03.md`; `handoffs/mmtx_scene02_start_help_cleanup_2026_06_26.md`; `handoffs/mmtx_scene03_journey_to_lake_publish_2026_07_01.md` | Nevracet webovy retest sceny 3 jako dalsi krok. Dalsi mala MMTX davka: bud Benji-only poslechovy recast, nebo nova Forest Journey scena podle dalsiho zadani. |
| Samantha external backup | 1 | active | Recovery zaloha `20260729_154354` je uspesna a prakticky overena: 55 798 souboru, 0 preskocenych, manifest i recovery navod pritomny a restore drill `AGENTS.md` ma shodny SHA-256. Prvni pokus prerusilo odpojeni sifrovaneho kontejneru; APFS kontrola byla cista a nedokonceny snapshot bez manifestu zustal bezpecne ignorovany. | `projects/samantha_external_backup.md` | `handoffs/external_backup_disk_usb_not_detected_2026_07_14.md`; `handoffs/appserver_human_adam_text_remote_verified_restart_backup_2026_07_14.md`; `handoffs/cockpit_robustness_smoke_backup_bridge_2026_06_09.md` | Pri beznem startu dal kontrolovat `backup_status.py`; novou pripominku zobrazit az kdyz posledni uspesna zaloha prekroci tri dny nebo chybi. |
| Janička Cockpit / používání a převzetí Samanthy | 1 | active | [PRIPOMENOUT] Janička je živý netechnický rozcestník k dokumentům, e-mailům, tisku, Lékárně, rodinným projektům, připomenutím a recovery. Stará light komunikace i nouzové otevírání plného Adama byly z Cockpitu odstraněny. Komunikace se vrátí až jako samostatný funkční Adam-R2; rozcestník do té doby neslibuje chat ani náhradní komunikační cestu. | `projects/janicka_cockpit_takeover.md`; `projects/janicka_cockpit_kucharka.md` | `handoffs/janicka_full_adam_cockpit_recovery_ios_card_2026_07_09.md`; `handoffs/janicka_cockpit_takeover_project_start_2026_06_06.md`; `handoffs/janicka_adam_text_bridge_functional_checkpoint_2026_06_07.md`; `handoffs/janicka_light_samantha_bridge_checkpoint_2026_07_03.md`; `handoffs/janicka_cockpit_family_projects_modal_2026_06_26.md` | Běžné nekomunikační vstupy Janičky ověřovat podle potřeby. Komunikační funkci už nerozvíjet v tomto projektu; navázat až samostatným projektem R2-Adam. |
| R2-Adam / Janička | 2 | active | R2-Adam má vlastní trvalý chat, soukromý kontext, TXT prostor, dokumentovou lištu a čtečku. E2 živě ověřilo úplný tok e-mail -> vault -> create-only TXT. E3 potvrdilo ruční revizi a backendovou dostupnost PDF; nasazená oprava odstraňuje diagnostickou obálku z lidského TXT bez změny staršího souboru. Smoke prošel 5/5. | `projects/janicka_r2_adam.md` | `handoffs/workstreams/project-r2-adam-janicka.md`; `tvbcp/workstreams/project-r2-adam-janicka.md` | Obnovit Archiv e-mailu a R2 čtečku a ručně ověřit otevření PDF i čistý začátek TXT. |
| Pozustalost / rodinny nouzovy balik | 1 | active | Zalozeno 2026-05-30 jako git-safe navrh bez citlivych dat. Technicke pravidlo 2026-05-31: nestavet druhy dokumentovy system; pouzit Document Management jako hlavni trezor, pridat pozustalostni metadata/tagy a finalni balik drzet jako samostatny sifrovany export. Soukrome prazdne sablony jsou zalozene mimo git v `data/private/pozustalost/`. | `projects/pozustalost_rodinny_plan_2026_05_30.txt` | `handoffs/pozustalost_start_2026_05_30.md` | Projit soukrome sablony a vyplnit nejdrive jen mapu oblasti bez cisel smluv, uctu, hesel a recovery klicu; konkretni citliva data ukladat jen do sifrovaneho uloziste mimo git. |
| Neuberk interier design / Kacenka | 2 | active | Designova prace je docasne prerusena. Soukromy projekt pro pudni hostovskou mistnost ma v `data/private/neuberk_interier_design/` aktualni stenove prekresy, pudorys a vizualni koncepty. Dne 2026-06-07 se ladil jizni pohled v6: opraveny pricny snizeny strop, sikmy tram smerujici k vychodni stene, komin u dveri a rozkladaci gauc za kominem. Aktualni soukromy kandidat je zapsany v indexu konceptu; git-safe stav je ulozeny bez soukromych rozmerovych detailu. | `projects/neuberk_interier_design.md` | `handoffs/neuberk_kacenka_south_wall_v6_geometry_checkpoint_2026_06_07.md` | Po navratu otevrit posledni soukromy kandidat v6 a porovnat ho s realnymi fotkami. Pokud Mila potvrdi geometrii, prejit na jednoduchy pudorysovy check: vejde se gauc za komin, zustane pruchod a nekoliduji dvere, topeni ani snizeny strop. |
| Samantha Agent/RAG | 1 | active | P0-P6 zavedly audit formální i obsahové pravdivosti, autoritu zdrojů, kanonickou dvojici proudu, opravu mode driftu, nefiltrované první hledání, jednoznačné aliasy a narovnání prokazatelně zastaralých aktivních souhrnů. P5 je nasazená na `20180e2` a smoke prošel 5/5. | `samantha_core.md`; `tvbcp/workstreams/project-samantha-agent-rag.md` | `handoffs/workstreams/project-samantha-agent-rag.md` | Směr pravdivé paměti je funkčně uzavřený. Pokračovat jedním úplným tokem e-mail -> private vault -> R2 TXT; embeddings zatím nepřidávat. |
| Znalostni databaze / Knihovna clanku / Knowledge inbox | 2 | active | Sloucena oblast podle Milovy korekce 2026-06-11: Knihovna clanku neni samostatny dlouhodoby projekt, ale prvni funkcni MVP vstup do sirsi zive znalostni databaze. Dne 2026-06-10 vznikl lehky soukromy archiv webovych clanku pro recepty, vedecke clanky a ostatni prakticke texty; Cockpit modal `Knihovna` umi vlozeni URL, vyber kategorie, tagy, ulozeni do `data/private/article_archive/`, fulltextove hledani a cteni TXT. Dne 2026-06-11 byl doplnen vstup `Ulozit text` pro recepty, poznamky a ChatGPT vystupy bez URL a importovano 23 receptovych polozek od Samanthy. Tentyz den byl doplnen datovy model `attachments`, endpointy `/api/library/attachment` a `/api/library/attachment/add`, Cockpit zobrazeni priloh a akce `Pripojit obrazek`, ktera k vybrane karte ulozi original, citelnou JPEG kopii a thumbnail. Dne 2026-06-19 bylo doplneno potvrzovane `Vyřadit z knihovny`, ktere polozku netvrde nemaze, ale presouva ji do soukromeho kose a vyrazuje z registru. Dne 2026-06-20 pribyla kategorie `Samantha / AI nástroje` (`ai_tools`) pro Codex, Agents SDK, OpenAI novinky a budoucí schopnosti Samanthy; prvni soukrome clanky jsou Codex Cookbook a Agents SDK. Dne 2026-06-23 pribylo v detailu clanku tlacitko `Otevřít na webu`, ktere u URL clanku otevre `canonical_url` nebo `source_url`; Mila rucne potvrdil funkcnost v Cockpitu. Dne 2026-07-01 byla opravena archivace webu se starsim ceskym kodovanim, preferovani hlavniho obsahu clanku a UI potvrzeni po ulozeni URL; rozbite soukrome GVT zaznamy byly podle Milova pokynu odstraneny natvrdo mimo git a carbonara byla presunuta do receptu. Dne 2026-07-16 pribyla v commitu `2597e14` editace nazvu, textu, kategorie, tagu a zdrojovych udaju existujici karty, uprava popisku prilohy a potvrzovane odebrani prilohy do soukromeho kose. ChatGPT export je v Knowledge inboxu rozpracovany: read-only index 826 konverzaci je hotovy a aktualni receptova kandidatni sada je uzavrena; 21 receptovych polozek bylo ponechano v knihovne a knihovna ma 44 receptu. Knowledge inbox v `data/private/knowledge_inbox/` zustava sirsi bezpecny intake pro velke podklady, chat exporty a soubory, ktere se maji nejdriv read-only zanalyzovat a az po potvrzeni rozdelit do tematickych knowledge karet. | `projects/vedecke_clanky.md`; `technical/large_context_intake.md` | `handoffs/article_archive_cockpit_library_2026_06_10.md`; `handoffs/knowledge_database_text_input_and_system_audit_2026_06_11.md`; `handoffs/knowledge_database_recipe_attachments_cockpit_checkpoint_2026_06_11.md`; `handoffs/knowledge_database_library_safe_delete_2026_06_19.md`; `handoffs/chatgpt_export_knowledge_import_checkpoint_2026_06_19.md`; `handoffs/knowledge_library_open_source_url_button_2026_06_23.md`; `handoffs/knowledge_library_encoding_and_backup_cleanup_2026_07_01.md`; `handoffs/knowledge_library_article_editing_2026_07_16.md` | Bez okamzite vyvojove akce; pri pristi bezne editaci overit znovuotevreni stejne karty se zachovanymi prilohami. Samostatne obnoveni prilohy z kose resit jen podle realne potreby. |
| Reminders / platebni SMS | 1 | active | Hotovy workflow: `inspect_payment_page_for_reminder` read-only overi splatnost z HTTPS platebni stranky/API bez opisovani plne URL/tokenu; `save_payment_sms_reminder` ulozi overovaci nebo ostrou platebni pripominku; `save_payment_case_document` ulozi lokalni fakturu/prilohu do `data/private/payment_cases/`. | `technical/general_reminders_workflow.md` | `handoffs/payment_sms_reminder_tool_done_2026_05_21.md` | Pri dalsi realne SMS overit live pres Samanthu. Pozdeji zvazit extrakci textu z PDF faktur nebo podporu JS/login stranek, ale jen read-only a s potvrzovaci branou. |
| Sprava dokumentu / private vault | 1 | active | [PRIPOMENOUT] Hlavni cesta je ScanDocu pro PDF z Downloads a Cockpit na `http://127.0.0.1:8770` jako lokalni ovladaci vrstva. Cockpit umi pracovni dokumentovou frontu, hledani, detail, potvrzovane akce tisk / archiv / kos, `Dokumenty k revizi`, cases/vazby, klasifikaci, terminy a detail case v2 s `case_health`. Dne 2026-06-13 byl opraven workflow e-mailovych PDF priloh: technicky typ `email-attachment-pdf` se bere jako slaba metadata, nova rucne zadana oblast se neztraci na `other`, klasifikacni panel umi `case_id`, ScanDocu revize nastavuje `reading_status=ok` a Cockpit fronta neukazuje dokumenty, ktere uz ScanDocu povazuje za zrevidovane. Konkretni zrevidovany e-mailovy PDF dokument UID 14438 byl po Milove potvrzeni oznacen ve vaultu jako OK. Dne 2026-06-14 byla doplnena citelna ASCII slug logika pro ceska manualni metadata (`Daňové přiznání` -> `danove-priznani`) a popisky pro danove priznani / pojistne prilohy; po potvrzenych soukromych opravach klasifikace hlasi 27/27 dokumentu kompletni metadata. Dne 2026-06-15 byly Kanta prilohy s castkami zarazene do private vaultu jako dokumenty k revizi a ScanDocu Review bylo opraveno pro ne-PDF prilohy: `.doc`/`.xls` se uz neposilaji do PDF iframe, ale maji download panel. Dne 2026-06-16 Email Work Queue umi nahledovat a ukladat PDF i obrazkove prilohy, ScanDocu umi znovu otevrit dokument vraceny do `needs_review`, aktivni private oblast `petkovy-65` byla sjednocena na `petkovy-56` a klasifikace hlasi 167/167 kompletni metadata. | `projects/document_management_private_vault.md`; `technical/private_document_vault_workflow.md` | `handoffs/cockpit_dashboard_terminal_launch_checkpoint_2026_05_29.md`; `handoffs/cockpit_global_hotkey_agent_2026_06_01.md`; `handoffs/document_management_cockpit_voice_command_inbox_2026_05_29.md`; `handoffs/email_processing_cleanup_and_documents_next_2026_06_03.md`; `handoffs/document_management_morning_action_plan_2026_06_04.md`; `handoffs/document_management_cockpit_case_health_checkpoint_2026_06_04.md`; `handoffs/document_vault_email_pdf_review_metadata_fix_2026_06_13.md`; `handoffs/document_metadata_and_tts_audio_checkpoint_2026_06_14.md`; `handoffs/scandocu_kanta_nonpdf_review_checkpoint_2026_06_15.md`; `handoffs/document_email_attachments_scandocu_metadata_checkpoint_2026_06_16.md` | Otestovat v Cockpitu jeden realny e-mail s PDF + JPEG prilohami: nahled, ulozeni do vaultu a doplneni metadat ve ScanDocu Review. OCR pro obrazkove prilohy resit az samostatnym potvrzenym krokem. |
| Cockpit Recovery centrum | 1 | active | [PRIPOMENOUT] Recovery/health/diagnostika/akcni fronta/bezpecny restart Cockpitu jsou hotove MVP a smoke check 2026-06-09 prosel lokalne i pres Tailscale. Dne 2026-06-11 vznikl read-only audit obsahu oken Cockpitu (`reports/cockpit_ui_content_audit_2026_06_11.md`), faze 1 mirny UI cleanup a faze 2 audit hlavni obrazovky (`reports/cockpit_main_screen_daily_audit_2026_06_11.md`). Faze 2 implementace je nasazena a Mila ji rucne potvrdil. Dne 2026-06-23 bylo opraveno tlacitko `Restart Cockpitu`. Dne 2026-07-07 byl opraven start pres globalni hotkey pri mrtve obsazenem portu `8770`. Dne 2026-07-09 byla stabilita startu a diagnostiky dotazena: start/restart/launchd pouzivaji rychly `/api/server/health`, `/api/status` ma timing sekci, lokalni i Tailscale smoke checky prosly a Mila rucne overil `Ctrl+Option+Command+C` na `http://127.0.0.1:8770` bez `Load failed`. Dne 2026-07-18 vznikl git-safe pamatovacek klicovych prikazu a read-only Cockpit modal v Servisu i Recovery centru; jediny Markdown zdroj se nacita pres fail-closed parser, prikazy nelze spoustet, menit ani kopirovat a plna brana prosla 776 testy. | `infrastructure/codex_reconnect_recovery.md`; `infrastructure/klicove_prikazy_pamatovacek.md`; `technical/session_recovery_rules.md`; `reports/cockpit_ui_content_audit_2026_06_11.md`; `reports/cockpit_main_screen_daily_audit_2026_06_11.md` | `handoffs/cockpit_command_cheatsheet_2026_07_18.md`; `handoffs/cockpit_startup_health_voicebridge_verified_2026_07_09.md`; `handoffs/cockpit_recovery_center_priority_2026_06_03.md`; `handoffs/cockpit_development_priorities_2026_06_03.md`; `handoffs/cockpit_health_status_buttons_2026_06_04.md`; `handoffs/cockpit_action_queue_2026_06_04.md`; `handoffs/cockpit_safe_restart_2026_06_04.md`; `handoffs/cockpit_restart_button_and_voice_audio_cleanup_2026_06_23.md`; `handoffs/cockpit_hotkey_fallback_port_2026_07_07.md`; `handoffs/cockpit_robustness_smoke_backup_bridge_2026_06_09.md`; `handoffs/cockpit_ui_cleanup_experiment_checkpoint_2026_06_11.md`; `handoffs/cockpit_main_screen_phase2_cleanup_2026_06_11.md` | Rizene restartovat Cockpit a vizualne overit `Servis -> Pamatovacek` i odkaz z Recovery centra na Macu nebo iPhonu. |
| Cockpit hlavni architektura / modernizace | 1 | active | Cockpit Dieta D0-D3 i UX2 pravdivé navigace jsou nasazené. E-maily mají vlastní rozcestník pro zpracování a archiv, ScanDocu je uvnitř Dokumentů a tyto pracovní schopnosti už nejsou v katalogu Webových aplikací. Všechny původní URL a backendové operace zůstaly zachované. Plná brána 1246/1246, řízené nasazení, smoke 5/5 a živá kontrola všech tří navigačních hranic prošly. `app/cockpit.py` má při měření 30. 7. 2026 10 027 fyzických a 9 354 neprázdných řádků. | `../AuditCockpit56.txt`; `reports/cockpit_dieta_d0_2026_07_29.md`; `reports/cockpit_quality_gate_2026_07_10.md` | `handoffs/cockpit_architecture_current_2026_07_10.md`; `handoffs/cockpit_email_archive_browser_2026_07_09.md` | Ručně vizuálně ověřit tři cesty: E-maily -> Zpracování, E-maily -> Archiv a Dokumenty -> ScanDocu. Další informační přesuny otevírat jen podle konkrétní uživatelské zkušenosti. |
| App-server rozhrani / novy Adam | 1 | active | Human–Adam, kanonické pracovní proudy, globální operace panelu Práce a odstranění aktivní legacy komunikace jsou dokončené. Human–Adam a Knihovna zůstávají dočasnými kompatibilními adaptéry nad existujícími vlákny a workspaces; jejich oprávněné schopnosti se zachovávají, ale profilové postavení není cílová architektura. Aktuální `main` je nasazený. | `tvbcp/architektura_komunikace_samantha.txt`; `technical/project_tvbcp_rules.md`; `technical/global_safety_brake.md`; `technical/capability_routing_rules.md` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` | Bez okamžité implementační akce. Adaptéry otevřít jen při konkrétním problému nebo před samostatně plánovanou migrací; předčasně je neodstraňovat. |
| Codex full access / Guard proti mazani | 1 | active | [PRIPOMENOUT] Míla rozhodl používat plnější lokální oprávnění kvůli provozní diagnostice. Lokální konfigurace a aktuální řízené prostředí se mohou lišit; vždy platí právě vložený `DEVELOPMENT_CONTROL` a skutečný sandbox relace. Základ Guardu proti mazání už existuje jako `technical/global_safety_brake.md`: pro `rm -rf`, hromadné mazání/přepisy, `git reset --hard`, force push, mazání větví/tagů, zásahy do private dat a podobné vysoké riziko vyžaduje přesnou potvrzovací větu. | `technical/codex_permissions_preferences.md`; `technical/global_safety_brake.md`; `infrastructure/git_checkpoint_protocol.md` | `handoffs/codex_full_access_voicebridge_guard_next_2026_06_29.md`; `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`; `handoffs/adam_voice_global_safety_brake_2026_06_09.md` | Nevracet jako další krok „založit Guard“; základní pravidlo už je založené. Volitelný budoucí krok je jen programová enforcement vrstva/wrapper pro destruktivní shell příkazy, pokud se ukáže potřeba. |
| Mapovani projektu a schopnosti | 1 | active | Taxonomie potvrzena Milou: projekty jsou jen kanonicke zive oblasti, varianty/vystupy nejsou samostatne projekty a asset knihovny/build/tmp/archivy nejsou projekty. Od 2026-06-07 je `ACTIVE_PROJECTS.md` prakticky registr projektu se sloupcem `Rezim`; archivovane projekty zustavaji dohledatelne, ale Cockpit je skryva z aktivniho pohledu. Dne 2026-06-23 vznikl opakovatelny systemovy audit projektu/toolu/vrstev jako registrovany system report, CLI `scripts/samantha_project_audit.py` a Samantha tool `samantha_project_audit`; capability audit po doplneni mapovani hlasi 81/81 toolu a 0 nemapovanych. Dne 2026-06-27 je skutecny capability registry v kodu kompletni pro aktualni Samantha agent tooly: registry ma 84 zaznamu, runtime prompt pouziva registry policy, audit hlasi `Registry-covered agent tools: 81/81`, kriticke/action-write mezery 0, action/review mezery 0, read-only/low-risk mezery 0 a `Agent tools missing capability records: None`. | `technical/project_capability_map.md`; `technical/system_project_audit_generator_design.md`; `technical/system_reports.md`; `technical/capability_routing_rules.md` | `handoffs/system_project_audit_generator_done_2026_06_23.md`; `handoffs/capability_registry_priority_gaps_closed_2026_06_26.md`; `handoffs/capability_registry_complete_2026_06_27.md` | Téma capability registry je uzavrene pro aktualni tooly. Udrzovat pravidlo: kazdy novy Samantha tool musi dostat capability registry zaznam a test. Pozdeji zvazit programovou enforcement branu podle registry. Bezprostredni dalsi krok mimo tema je recovery zaloha. |
| Samantha Infrastructure | 1 | active | Current infrastructure stack: macOS, VS Code, Codex CLI, GitHub, SSH, Tailscale a OpenAI/GPT workflow. Kriticka operacni znalost je rozdelena do `memory/infrastructure/`: operating model, macOS network recovery, Codex reconnect recovery, Git checkpoint protocol, SSH setup a Tailscale setup. Sitovy reconnect stav ma samostatny aktivni radek `macOS sit / Tailscale recovery`. Od 2026-06-09 existuje rucni `scripts/git_safety_check.py` pro staged private/autosave/env ochranu a `scripts/system_quick_check.py` pro read-only souhrn git/backup/Cockpit/Adam bridge/autosave. Od 2026-06-12 existuje `scripts/autosave_status.py`, ktery read-only hlasi stari session autosave snapshotu a zda bezi watcher; quick check ho pouziva. Téhož dne bylo doplněno pravidlo `technical/global_safety_brake.md`: beznou praci neblokovat, ale destruktivni/systemove vysoke riziko vyzaduje presnou potvrzovaci vetu. Dne 2026-06-18 dostal start `samantha` vlastni `screen` konfiguraci pro vetsi scrollback a napovedu ke scrollovani. | `infrastructure/operating_model.md`; `infrastructure/codex_reconnect_recovery.md`; `infrastructure/macos_network_recovery.md`; `technical/global_safety_brake.md`; `technical/session_recovery_rules.md` | `handoffs/autosave_status_and_voice_triage_fix_2026_06_12.md`; `handoffs/system_quick_check_git_safety_2026_06_09.md`; `handoffs/adam_voice_global_safety_brake_2026_06_09.md`; `handoffs/samantha_screen_scrollback_fix_2026_06_18.md` | Bezny start nove Codex relace: `samantha`, ne holy `codex`, aby bezely screen, autosave, preflight, session report a voice marker flow. Po scrollback uprave rucne otestovat novy start; kdyz bezne scrollovani nestaci, pouzit `Ctrl+A`, potom `Esc`. Pri reconnectu nebo ranni kontrole spustit `.venv/bin/python scripts/system_quick_check.py`; pri autosave pochybnostech `.venv/bin/python scripts/autosave_status.py`; pred commitem lze spustit `.venv/bin/python scripts/git_safety_check.py`; pred rizikovou praci: git checkpoint protocol a globalni brzda jen pro vysoce rizikove kroky. |
| iPhone Shortcuts / Mobile Input Layer | 2 | paused | Zmrazeno jako funkcni Infrastructure capability: `Najit auto v3.shortcut` funguje u Mily i Jany, `Lékárna Jana.shortcut` funguje a `Rychlá poznámka pro Samanthu.shortcut` uklada poznamky. Samantha umi Quick Notes nacist jako ocislovany seznam/detail a od 2026-06-19 ma read-only akcni inbox s automatickou predklasifikaci na pripominku, projekt, tool/workflow, ukol, citlivou akci, archiv/znalostni databazi nebo napad. Dne 2026-06-23 byl Cockpit Quick Notes stav sjednocen s akcni predklasifikaci: fallback uz neukazuje `Nezařazeno`; QN #42 typu knihovna / URL clanek se zobrazuje jako `archiv/znalostní databáze`. Puvodni seznam 7 dalsich kandidatu je ulozen ve zmrazovacim handoffu. | `technical/iphone_shortcuts_playground.md` | `handoffs/iphone_shortcuts_freeze_infrastructure_layer_2026_05_25.md`; `handoffs/quick_notes_action_inbox_preclassification_2026_06_19.md`; `handoffs/quick_notes_triage_no_unclassified_2026_06_23.md` | Nepokracovat bez vyslovneho navratu. Pri navratu pouzit read-only `quick_notes_action_status`, rucne vybrat jednu QN a teprve pak implementovat jednu potvrzovanou akci: mark done, navrh pripominky, projektovy handoff, dokument do trezoru nebo archiv nakupu. |
| Nakupni pruzkum a archiv nakupu | 2 | active | Koncept ulozen jako lehky workflow/tool: Mila zada konkretni produkt nebo varianty, Adam/Samantha najde kamenne prodejce do 100 km od Mlade Boleslavi a overene e-shopy, vrati prime odkazy na produkt a po Milove objednani ulozi potvrzeni/fakturu do soukromeho archivu mimo git. | `technical/shopping_research_and_purchase_archive.md` | zatim neni | Pri prvnim realnem navazani zalozit soukromy `data/private/purchases/`, sablony `order_summary.md`/`warranty.md` a az po realnem pouziti zvazit intake z Downloads a systemovy report nakupni evidence. |
| Automaticke opakujici se ukoly / ColorsAndNumbers | 1 | active | GitHub Pages používají workflow artifact bez zápisu do `main`. Plánovaný běh 30. 7. 2026 uspěl a veřejné dnešní MP3 vrací HTTP 200. Soukromé fotografie nadále nesmí do repozitáře ani Pages. | `projects/automated_recurring_tasks.md` | `handoffs/colors_numbers_owl_pages_artifact_checkpoint_2026_07_27.md`; `handoffs/colors_numbers_private_photo_gallery_proposal_2026_07_13.md` | Bez okamžité změny. Sledovat příští přirozený běh a zasahovat jen při chybě audia, Pages deploymentu nebo neočekávané změně `main`. |
| macOS sit / Tailscale recovery | 1 | archived | Pending do instalace noveho pripojeni: technik T-Mobile ma v pondeli 2026-06-01 instalovat nove pripojeni pres pevnou linku/DSL. Predchozi domaci watchdog mel jen 81,88 % OK a casto selhal i ping na gateway `192.168.1.1`; pracovni Wi-Fi retest mel 319/320 OK. | `technical/macos_wifi_vpn_tailscale_recovery.md` | `handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md` | Do 2026-06-01 resit jen pokud se stav zhorsuje. Po instalaci nove linky udelat 30min watchdog retest a porovnat stabilitu; Mac stack resit az pokud budou padat i jine site nebo nova linka. |
| iCloud Mail read-only / Email Cases | 1 | active | Read-only e-mailové workflow, Work Queue, vyladěný Archiv e-mailu i UX2 pravdivé navigace jsou nasazené. Horní E-maily vedou na rozcestník Zpracování / Archiv a obě pracovní části zmizely z katalogu Webových aplikací. URL, payloady a bezpečnostní hranice se nezměnily; živě jsou dostupné obě původní stránky. | `projects/email_readonly_oauth.md` | `handoffs/cockpit_email_archive_browser_2026_07_09.md` | Ručně vizuálně ověřit obě volby v novém e-mailovém rozcestníku. Zápisy, mazání a odesílání zůstávají mimo rozsah. |
| Lekarna | 1 | active | Foto import ve Sprave Lekarny je po realnem testu 2026-07-09 end-to-end funkcni: fotka -> OpenAI OCR -> SUKL DLP -> online PIL dokument -> `PIL_Short` -> prijem na sklad -> web export -> sifrovany produkcni balicek -> automaticky commit/push. Testovaci SERTIVAN / sertralin byl prijat, overen v produkci a nasledne potvrzene vyrazen; v lokalnim CSV zustava jako auditni radek `vyradeno`, ale webovy export a produkce ho uz nezobrazuji. Export byl opraven tak, aby vyradene radky nesly do produkcni webove Lekarny. Webova aplikace Lekarna zustava archivovany vystup/varianta hlavni Lekarny, ne samostatny aktivni projekt. | `projects/lekarna_domaci_leky.md` | `handoffs/lekarna_photo_import_pil_publish_retire_verified_2026_07_09.md`; `handoffs/lekarna_import_manifest_editor_checkpoint_2026_07_06.md`; `handoffs/lekarna_photo_staging_tool_2026_06_12.md`; `handoffs/lekarna_status_po_doplneni_vitaminu_2026_05_21.md`; `handoffs/lekarna_web_app_hotovo_2026_05_20.md` | Neni nutny okamzity zasah. Pri dalsim realnem leku zopakovat cely tok a sledovat hlavne produkcni publikaci; volitelne doplnit UI overeni, ze GitHub Pages CDN uz servíruje novy sifrovany balik. |
| Tomik video iMovie / FamilyVideoOrganizer | 1 | active | Realny lehky balicek pro dcerino rozhodovani je pripraven mimo git a podle Mily byl 2026-05-29 uz dceri poslany: generator `scripts/tomik_family_video_package.py` vytvari `videos-data.js`, 651 nahledu a ZIP bez MP4; UI umi Safari fallback pro vyber MP4, zelene tlacitko `Slozka s videi`, zamykani radku kliknutim, autosave a export JSON. | `projects/tomik_video_imovie.md` | `handoffs/family_video_organizer_package_ready_2026_05_29.md` | Cekat na dcerin export JSON rozhodnuti/poznamek; po prijeti udelat read-only kontrolu a import do short/family vyberu delat az po samostatnem potvrzeni. |
| Family Memory Films / USA 2019 | 1 | active | Cisty seznam 15 filmu pouzitelnych dnu je odsouhlaseny; `2019-08-05` neni samostatny den filmu, ale smesny zdroj podle item-level review. Master prehled ve stylu `Tomik 2` je ulozen mimo git v `03_overview/usa_2019_tomik2_overview.md`. Predstrihovy formular `03_overview/film_selection_form.html` ma 2688 polozek, denni filtr, rating `A/B/C/skip`, volby pro kratky/dlouhy film, autosave, CSV export a prehravani videi. Adamuv prvni navrh ratingu je aplikovany: `A=406`, `B=913`, `C=1369`. | `projects/family_memory_films.md` | `handoffs/family_memory_usa_2019_tomik2_overview_checkpoint_2026_06_05.md` | Otevrit `http://127.0.0.1:8793/03_overview/film_selection_form.html`, rucne zkontrolovat Adamuv rating, povysit rodinne/emocni momenty podle potreby a stahnout `film_selection_review.csv`; pri navazani brat nejnovejsi `~/Downloads/film_selection_review*.csv` jako zdroj pravdy. Originaly nemazat, neprejmenovavat ani nepresouvat bez potvrzeni. |
| Webova aplikace Lekarna | 2 | archived | Hotovo / udrzba. Verejna GitHub Pages aplikace v `docs/lekarna/` funguje se sifrovanym datovym balikem, skutecnymi fotkami a `PIL_Short`; ChatGPT fallback ma kopirovaci panel a rucni odkaz pro prohlizece, ktere neotevrou novou zalozku. | `projects/lekarna_web_app.md` | `handoffs/lekarna_web_app_hotovo_2026_05_20.md` | Zadny aktivni vyvoj. Pri novem pozadavku nejdrive precist handoff; pri zmene dat znovu spustit export + sifrovani a commitnout jen encrypted bundle. |
| VocabularyFR Web Trainer | 2 | archived | Archiv: webovy MVP prototyp je hotovy a checkpointnuty v commitu `da93eba`; navazujici Janina macOS app / Pict opravy jsou uzavrene: app umi hledat externi `PythonMF/Pict`, Jana `mapping.json` ma 841 zaznamu, audit hlasi 346/347 konkretnich obrazku a jediny zamerne ponechany fallback `chez -> preposition`; oprava zameny `school.PNG`/hospital je pushnuta v `253c6cd`. | `projects/vocabularyfr_web_trainer.md` | `handoffs/vocabularyfr_web_trainer_checkpoint_2026_06_04.md`; `handoffs/vocabularyfr_jana_images_archive_2026_06_07.md` | Archiv: neukazovat mezi aktivnimi projekty. Pri navratu nejdrive spustit audit `.venv/bin/python scripts/audit_jana_vocabularyfr_pict_mapping.py` a overit iCloud sync `PythonMF/Pict/mapping.json`. |
| Media image resize utility | 1 | active | Obecna utilita pro zmensovani obrazku podle cilove velikosti v kB je hotova, otestovana a prvne pouzita na lekarne. Vychozi cil je 250 kB, preset `lekarna` je 100 kB. | `projects/media_image_resize_utility.md` | `handoffs/media_image_resize_utility_done_2026_05_20.md` | Pri dalsim projektu se nejdriv zeptat na cilovou velikost, pokud neni dana; pro slovniky pravdepodobne zacit preview s 250 kB. |
| MultiLO | 2 | active | Stabilizace navratu do kokpitu probehla; cleanup screenu a nahrazeni rizikovych `CTkEntry` za `tk.Entry` jsou popsane, dalsi prace ceka na rucni retest. | `projects/multilo_stabilization_cleanup.md` | zatim neni | Provest rucni retest navratu do kokpitu podle checklistu a dalsi zmeny delat az po potvrzeni stability. |
| PictNew / Vocabulary image workflow | 2 | active | Od 2026-07-31 platí jeden český abecední obsah `Pict/mapping.json` pro `FR - Míla`, `FR - Jana` a `IT - Míla`. Každý zápis slovíček automaticky spouští společný audit přesně tří kanonických CSV, obou distribučních mappingů a obou knihoven `Pict`; aktuální sjednocený mapping má 958 položek. | `projects/pictnew_vocabulary_image_pipeline.md`; `technical/vocabulary_image_generation_workflow.md` | `handoffs/vocabularyit_mapping_applied_2026_05_20.md` | Při příští změně slovíček nejdříve použít povinný aktualizační kontrakt v projektové paměti; placené generování, přesun obrázků a mapping apply držet za stávajícími preview a potvrzovacími hranicemi. |
| TTS / české audio nástroje | 1 | active | Aktivní oblast obsahuje obecné vytváření českých MP3 přes `scripts/generate_tts.py` a `scripts/tts_gui.py`, lokální předčítání a obecné předčítání odpovědí v Cockpitu. Starý terminálový komunikační transport, watcher, TTY marker a jeho Cockpit ovládání byly vyřazeny a nejsou součástí TTS toolu. Mikrofon Human–Adam patří projektu Human–Adam. | `projects/tts_edge_audio_tools.md`; `technical/global_safety_brake.md`; `technical/codex_remote_approval_notice.md`; `technical/codex_permissions_preferences.md` | `handoffs/autosave_status_and_voice_triage_fix_2026_06_12.md`; `handoffs/adam_voice_bridge_end_to_end_checkpoint_2026_06_05.md`; `handoffs/adam_voice_iphone_autoread_confirmed_2026_06_29.md`; `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`; `handoffs/voicebridge_operational_contract_2026_06_30.md` | Při další potřebě ověřit jen konkrétní obecnou TTS funkci. Historické komunikační handoffy používat pouze jako archivní důkaz, ne jako provozní návod. |
| Tax | 3 | active | Danove priznani 2025 ma pripraveny vypocet, checklist a pravidla pro neukladani citlivych udaju. | `projects/tax_priznani_2025.md` | zatim neni | Pred odeslanim overit aktualni adresu, specialni danove situace a finalni hodnoty proti originalnim podkladum. |
| Test handoffu | 3 | archived | Hotovo; jen overeni, ze pravidlo pro kratky handoff funguje. | zatim neni | `handoffs/test_kratky_handoff_2026_05_18.md` | Zadny dalsi krok neni potreba, pokud Mila nechce test zopakovat nebo upravit pravidla. |

## Aktualni navazani

- 2026-07-27 12:05 CEST: Priorita 1, Human–Adam / uzavření dávkového UI.
  Panel `Práce` nyní vede v pořadí lokální vývoj, případné nasazení do Cockpitu
  a až potom denní GitHub balíček. Nový dynamický souhrn říká, zda lze pokračovat
  vývojem, zda lokální kód čeká na nasazení a kolik commitů čeká na GitHub.
  Nápověda používá stejné tři kroky, přesné názvy tlačítek a již neslibuje
  automatický push po každém tahu. Cílených 58 a úplných 1272 testů prošlo.
  Fáze je v lokálním denním balíčku; zbývá samostatné nasazení a ruční vizuální
  plus jeden malý vzdálený přijímací test. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-27 11:19 CEST: Priorita 1, Human–Adam / dávkový GitHub režim.
  Lokální `main` je přes den autorita, jednotlivé commity se zachovávají a
  GitHub čeká na ruční denní balíček. Běžné změny mají rychlou lokální bránu,
  rizikové změny úplnou; večerní balíček provede jednu úplnou bránu a jeden
  push. Divergence blokuje jen balíček, nikoli další lokální checkpoint nebo
  lokální nasazení. Úplná brána prošla 1269 testy. Zbývá bootstrap commit,
  push a samostatně potvrzené nasazení do Cockpitu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-27 08:25 CEST: Priorita 1, Human–Adam / fáze 9.3e a servisní
  převzetí po sovím commitu. Živé diagnostiky, přehled Codex relací a stav
  starého Adam fallbacku už nezávisí na Voice Bridge markeru. Ochrana Janička
  relací používá vlastní registry spravovaných relací a při jejich
  nedostupnosti selže uzavřeně. Runtime VoiceBridge modul a private data
  zůstávají zachované. Automatická integrace správně zastavila devítisouborový
  WIP, když GitHub postoupil sovím commitem `c10dfa0`; cesty se nepřekrývaly.
  Servisní převzetí vytvořilo obnovitelný WIP checkpoint, fast-forwardnulo
  sovu a změny začlenilo nad ni. Před integrací bylo nalezeno a opraveno sedm
  regresí přímého runtime testu. Cílených 313 a úplných 1254 testů prošlo.
  Zbývá doplnit checkpointový commit, push, zarovnat profily a samostatně
  potvrzeně nasadit nový `main`. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-27 01:21 CEST: Priorita 1, Human–Adam / přesné ověření shody
  `Git/main` a běžícího Cockpitu. Dosavadní checkpoint `28885b957d34` je
  zarovnaný s GitHubem, serverově nasazený a Human–Adam je připojený. Zavádějící
  hláška `aktuální Git/main nelze ověřit` vznikala proto, že redigovaný status
  celé `source_head` správně nevydával, ale UI ji přesto očekávalo. Status nyní
  poskytuje pouze allowlistovaný 12znakový `source_head_short`; UI jej porovná
  s deployment receipt a neplatnou hodnotu ponechá fail-closed. Cílených 83,
  širších 338 a úplných 1252 testů prošlo. Zbývá commit/push, jediné potvrzené
  nasazení do Cockpitu a vizuální kontrola zelené shody. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-27 00:54 CEST: Priorita 1, Human–Adam / falešný timeout po úspěšném
  nasazení. Browser po 60 sekundách tvrdil, že nový Cockpit nepřišel, ale
  serverová receipt následně prokázala `deployed` pro `3df4410`, nový proces,
  1250 testů a smoke 5/5; runtime byl dosažitelný a Human–Adam připojený.
  Klient nyní čeká nejvýše 120 sekund, přechodné `profil právě provádí jinou
  operaci` nepovažuje za konečný neúspěch a před varováním read-only ověří
  přesnou receipt auditovaného commitu. Neznámý výsledek zakáže slepé
  opakování; terminálový fallback doporučí jen při skutečně nedostupném
  serveru. Cílených 294 a úplných 1251 testů prošlo. Zbývá commit/push,
  potvrzené nasazení a jeden živý restartovací test. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 23:29 CEST: Priorita 1, Human–Adam / jednoznačné rozlišení Gitu
  a běžícího Cockpitu. Automatická účtenka už neoznačuje commit/push jako celé
  nasazení: samostatně uvede nový `Git/main` a serverově ověřený commit
  načtený v Cockpitu. Stavový banner při rozdílu oranžově hlásí čekající
  nasazení, při shodě je zelený. Nápověda i tlačítka výslovně popisují jeden
  audit a jedno potvrzené nasazení do Cockpitu pro každý nový runtime commit;
  souběh Cockpitu a terminálového Adama zakazují. Potvrzovací věta nově jmenuje
  cíl `aktuální main do Cockpitu`; backendová brána, řízený restart a smoke se
  nemění. Cílených 171 a úplných 1278 testů prošlo. Zbývá commit/push a
  přechodové nasazení větou z právě běžící starší UI; potom platí nový text.
  Handoff: `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 20:36 CEST: Priorita 1, Human–Adam / obnova vlastněného WIP bez
  dokončovací účtenky. Před každým zapisovacím tahem nyní vznikne soukromý
  provizorní ownership marker svázaný s pracovním proudem, klientem, výchozím
  commitem a otiskem změněných cest. Pokud model platnou účtenku nevrátí,
  dokončený tah už nezůstane bez doložitelného původu: panel `Práce` nabídne
  samostatně potvrzované dokončení přes stejnou kanonickou plnou bránu,
  checkpoint, push a kontrolu zarovnání. Posun `main`, změna otisku, cizí WIP
  nebo nejisté doručení zůstávají fail-closed. Marker neobsahuje obsah souborů,
  zprávy, private cesty ani tajemství. Cílených 429 a úplných 1275 testů
  prošlo. Zbývá commit/push, samostatně potvrzené nasazení a živý test s
  úmyslně chybějící účtenkou. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 17:52 CEST: Priorita 1, Human–Adam / opakovaný Git index lock.
  Tři shodné incidenty potvrdily, že automatický read-only `git status`
  zbytečně obnovoval Git index a po přerušené transakci mohl zanechat pouze
  plný `index.lock`. Fáze 1–3 zakazují volitelné Git zámky při statusu,
  klasifikují chybějící index jako samostatný fail-closed stav a regresními
  testy dokazují nulový zápis indexu. Plná brána prošla 1267 testy. Oprava
  čeká na commit/push; současný recovery kandidát se smí obnovit až po přesné
  globální brzdě a potom lze společně nasadit i hotfix Důležitých připomenutí.
  Handoff: `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 16:37 CEST: Priorita 1, Cockpit hlavni architektura / dieta.
  Kanonicky handoff i hlavni TXT roadmapa byly obnoveny podle aktualniho
  mereni. `app/cockpit.py` ma 20 745 fyzickych a 19 620 neprazdnych radku;
  cely rozsah quality gate ma 57 079 produkcnich a 34 139 testovacich
  neprazdnych radku. Cilem neni plosne mazani ani prepis, ale postupne
  oddelovani odpovednosti pri zachovani endpointu, potvrzovacich bran a
  private datovych cest. Nejmensi dalsi krok je read-only Dieta D0: aktualni
  mapa odpovednosti a call-site zavislosti monolitu a vyber jedine soudrzne
  e-mailove skupiny pro naslednou Fazi 1.4. Handoff:
  `handoffs/cockpit_architecture_current_2026_07_10.md`; roadmapa:
  `../AuditCockpit56.txt`.
- 2026-07-26 10:09 CEST: Priorita 1, Human–Adam / fáze 8.3b. Stejný redigovaný
  živý snapshot z fáze 8.1 nyní vstupuje také do modelového kontextu r-Adama,
  vždy právě jednou před vývojová oprávnění. Serializer propouští jen pevně
  povolené stavy, krátké Git otisky, počty a booleovské důkazy; neplatný nebo
  neúplný stav skončí jako `unverified` a výpadek read-only GitHub auditu
  nezablokuje konverzaci. UI, persistence, reconnect, synchronizace a write
  oprávnění se nemění. Plná brána prošla 1237 testy. Běžící Cockpit zůstává
  ověřený na `6854fd2`; 8.3b čeká na samostatně potvrzené nasazení a následný
  krátký živý read-only test. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 09:07 CEST: Priorita 1, Human–Adam / fáze 8.3a. Panel `Práce`
  dostal prvního přímého UI konzumenta společného redigovaného snapshotu z 8.1:
  odděleně ukáže main/GitHub, nasazení, profilové workspaces a runtime.
  Neúplný nebo neshodný důkaz skončí jako `Neověřeno`; načtení nespouští
  prepare, sync, reconnect ani zápis a nepropouští soukromé cesty, zprávy,
  odpovědi, PID či identifikátory vláken. Fáze 8.1 a 8.2 jsou nasazené na
  `a1e75ba`; 8.3a čeká na commit/push a samostatně potvrzené nasazení. Plná
  brána prošla 1232 testy. Po nasazení zbývá vizuální test panelu; fáze 8.3b
  později předá stejný snapshot r-Adamovi. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 07:57 CEST: Priorita 1, Human–Adam / checkpointová projekce
  živého stavu. Fáze 8.2 napojuje společný redigovaný generátor z fáze 8.1 na
  potvrzovaný checkpoint a promítá do handoffu a TVBCP stručné Hotovo /
  Otevřeno / Rizika / Další krok. Předchozí serverově doložené nasazení se
  uzavře jako hotové, nový checkpoint zůstane otevřený do vlastního důkazu a
  proud bez deployment capability nedostane falešný blocker. Neúplné důkazy
  selžou uzavřeně; private cesty, zprávy, odpovědi a PID se neukládají. Plná
  brána prošla 1228 testy. Zbývá commit/push, čerstvý audit kvůli možnému
  sovímu commitu a potvrzené společné nasazení fází 8.1 a 8.2. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-26 00:35 CEST: Priorita 1, Human–Adam / živý stav pracovního proudu,
  fáze 8.1. Vznikl společný čistě read-only generátor, který z předaných
  bezpečných snapshotů skládá redigovaný stav `main`/`origin/main`,
  deploymentu, profilových workspace a runtime. Sám neprovádí I/O, sync,
  reconnect ani zápis do handoffu/TVBCP; chybějící nebo rozporný důkaz končí
  jako `unverified`. Nových testů 9/9, širší sousední sada 115/115. Další krok
  je checkpointová projekce; UI a r-Adam se zapojí až potom a nasazení počká
  na první aktivní konzumní vrstvu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-25 10:32 CEST: Priorita 1, Human–Adam / obecné ruční dorovnání
  čistého `main` s GitHubem. Po neúspěšném auditu nasazení umí panel Práce
  samostatně ověřit, zda je `origin/main` jednoznačným potomkem čistého
  lokálního `main`. Při bezpečném stavu ukáže cílový commit, počet commitů a
  změněné cesty a nabídne potvrzované tlačítko. Apply znovu ověří oba přesné
  commity, použije pouze fast-forward a dorovná oba čisté profily. WIP, aktivní
  nebo nejistý tah, dirty stav, lokální náskok, divergence a závod na GitHubu
  zůstávají fail-closed. Řešení je obecné, bez soví výjimky. Cílených 426 a
  úplných 1227 testů prošlo. Zbývá commit/push, potvrzené nasazení a pozdější
  živý test při přirozeném vzdáleném posunu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-25 00:14 CEST: Priorita 1, Human–Adam / servisní integrace rotace
  bez kotvy. Přednasazovací audit zachytil čtyřsouborový WIP na starším základu
  bez ownership markeru; `main` mezitím postoupil a dvě cesty se překrývaly.
  Míla výslovně potvrdil servisní začlenění. Přenesené plus/minus řádky přesně
  odpovídají zachovanému WIP: kontrola rotace už není rušena změnou revize
  volitelné kotvy, nadále ji však váže identita auditovaného vlákna. Cílených
  92 a úplných 1216 testů prošlo. Zbývá checkpoint/push, bezpečné zarovnání
  profilů, potvrzené nasazení a ruční retest.
- 2026-07-24 23:23 CEST: Priorita 1, Human–Adam / fáze 2 handoffu a
  potvrzovaná integrace. Budoucí automatický checkpoint bude v témže jediném
  commitu aktualizovat markerově ohraničený `Aktuální stav` v handoffu i TVBCP;
  starší chronologické bloky zůstanou beze změny jako snapshoty. Souhrn smí
  vycházet jen z ověřeného zarovnání `main == origin/main` a poslední
  deployment účtenky, ne z odhadu starých textů. Pro odložený Human–Adam WIP je
  implementovaná samostatně potvrzovaná integrační brána. Vyžaduje soukromý
  ownership marker svázaný s pracovním proudem, base commitem a otiskem seznamu
  změněných cest; marker neobsahuje obsah souborů ani chat a zůstává mimo Git.
  Při posunu `main`, neshodě markeru, cizím WIP nebo divergenci je integrace
  fail-closed a vyžaduje servisní rozhodnutí; automatický merge ani rebase
  nevznikl. Cílených 446 testů a úplná Cockpit Quality Gate s 1216 testy
  prošly. Zbývá checkpoint/push, potvrzené nasazení a úplný živý souběžný test.
- 2026-07-24 22:49 CEST: Priorita 1, Human–Adam / aktuální autoritativní
  souhrn. Míla ručně dokončil celý test rotace bez připnuté kontextové kotvy:
  kotvu pozastavil, provedl rotaci, ověřil zachování starého vlákna a
  kontinuitu přes handoff a TVBCP. Funkce je tím provozně ověřená. Starší
  položky níže jsou chronologické snapshoty; jejich text `čeká na nasazení`
  nevyjadřuje dnešní stav, pokud jej uzavřel pozdější commit, nasazení nebo
  ruční důkaz. Automatický Human–Adam checkpoint zapisuje do handoffu správný
  stav vývojového kroku v okamžiku checkpointu, ale následný terminalový push,
  nasazení a ruční retest starší blok automaticky neaktualizují. Aktuální
  otevřený vývoj zůstává potvrzovaná integrační brána odloženého WIP; samostatně
  zbývá skutečný živý test izolovaného vývoje při současném terminálovém WIP.
  Handoff: `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, Human–Adam / recovery hranice automatického připojení.
  Post-deployment UI guard nyní stejně jako backend prochází historii odzadu:
  poslední potvrzený `completed` uzavře starší nejistoty, zatímco novější
  `pending`, `delivery_unknown` nebo `recovery_required=true` zůstávají
  fail-closed. Pět přímých JavaScriptových scénářů, 457 širších testů a úplná
  Quality Gate s 1201 testy prošly. Další krok je nasazení a živé ověření
  automatického připojení nad existující historií. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, Human–Adam / read-only audit čekající integrace.
  Panel `Práce` nyní rozlišuje dirty zdrojový `main`, čistý společný základ,
  posun `main` s překryvem změněných cest a fail-closed blokaci cizím nebo
  rozvětveným WIP. Audit nic necommitne, neslučuje ani nepřepisuje a výslovně
  neprokazuje vlastnictví změn. Cílených 168, širších 457 a úplných 1201 testů
  prošlo. Další krok je nasazení, kontrola čistého stavu a teprve potom návrh
  samostatně potvrzované integrační brány. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, Human–Adam / návrat po samoobslužném nasazení.
  Ověřené nasazení nyní obnoví stránku i při selhání `sessionStorage` a po
  návratu Cockpitu bezpečně znovu připojí Human–Adam pouze tehdy, když není
  aktivní tah, nejisté doručení ani nedostupný runtime. Běžné otevření stránky
  se automaticky nepřipojuje. Cílených 191 testů a celá Cockpit Quality Gate
  s 1195 testy prošly. Další krok je commit, push, potvrzované nasazení a jeden
  živý test malý vývoj -> nasazení -> další pokyn. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, lepsi projektove TVBCP – faze 1. Pravidla,
  automaticka dokoncovaci uctenka a checkpointovy generator nyni pro nove
  appendovane zaznamy uprednostnuji `Hotovo`, `Rozhodnuti`, jeden
  `Dalsi krok` a zachovane `Navrhovane dalsi kroky`; technicky dukaz je az
  posledni kratka sekce. Starsi zaznamy se neprepisuji. Stare tripolove
  uctenky zustavaji kompatibilni, plany maji limit ctyr polozek a citlive
  hodnoty jsou odmitnuty. Proslo 227 sirsich testu a cela Cockpit Quality Gate
  s 1194 testy. Dalsi krok je nasazeni a jeden zivy append-only test noveho
  formatu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, Human–Adam / vyvojove prostredi. Je pripraven uzky
  rez soubezne izolovane prace pri terminalovem WIP: zapisovaci tah smi
  editovat a testovat pouze v cistem workspace zarovnanem s poslednim commitem,
  ale nedostane automatickou dokoncovaci uctenku a checkpoint, commit, push,
  merge, rebase, reset i nasazeni zustavaji odlozene do cisteho `main` a auditu
  konfliktu. Rezim je omezen na Human–Adam; Knihovna, spinavy nebo nezarovnany
  peer zustavaji fail-closed. Cilenych 190 testu a cela Cockpit Quality Gate s
  1192 testy prosly. Zmena ceka na commit, push a potvrzovane nasazeni; teprve
  potom ma nasledovat zivy test. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-24: Priorita 1, Human–Adam / vyvojove prostredi. Odeslani z aktivniho
  profilu nove pred samotnym tahem bezpecne dorovna cisty, necinny a duveryhodny
  izolovany workspace, pokud je pouze za zdrojovym `main`. Spinavy workspace,
  aktivni tah, nejiste doruceni, spinavy zdrojovy `main` nebo divergence
  zustavaji fail-closed. Cilenych 187 testu a cela Cockpit Quality Gate s 1189
  testy prosly. Tato oprava resi zbytecne rucni `Pripojit` po cistem terminalovem
  commitu a pushi; neresi soubezne dva zapisujici vyvojare. Nasledujici
  prednostni vyvoj je izolovana soubezna prace Human–Adam pri terminalovem WIP:
  editace a testy mohou bezet ve vlastnim workspace, ale checkpoint, push a
  zacleneni zustanou blokovane do cisteho `main` a auditu konfliktu. Bez
  automatickeho rebase, resetu, merge nebo mazani. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-21: Priorita 1, univerzalni pracovni proudy faze 4.5g-c1 az c2f1.
  Verejna zavadejici `active_profile_*` metadata a cely osirely
  deployment-completion surface byly po oddelenych auditech odstraneny.
  Aktualni deployment autoritou je pouze simple-main receipt; stary modul
  `human_adam_deploy.py` i jeho test jsou pryc. Checkpoint `23a219e` prosel
  vzdalenou CI, plnou lokalni branou s 969 testy, restartem a smoke `5/5`.
  Main, Human–Adam i Knihovna jsou ciste a zarovnane; Mila potvrdil funkcni
  panel `Prace`. Zaverecny read-only audit nenasel zadny zivy import, endpoint
  ani reader stareho subsystému. Ignorovane bytecode cache, osirela private
  diagnosticka data a historicky nazev gate logu zustavaji mimo tento
  dokumentacni krok. Dalsi vyvoj otevirat novym samostatnym read-only auditem;
  interni kompatibilni identity, schema 1 a private data zatim nemenit. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, univerzalni pracovni proudy faze 4.3. Vsech 29 proudu
  ma jednu kanonickou git-safe vazbu na handoff a TVBCP. Human–Adam a Knihovna
  zachovavaji stavajici dokumenty; ostatni pouzivaji jedine stabilni cesty a
  jejich kostry vzniknou transakcne az prvnim potvrzenym checkpointem po zelene
  brane. Gate failure nic nevytvori, commit failure nove kostry odstrani a
  puvodni prace zustane viditelna. Lazy checkpoint navic vyzaduje pripojene
  vlakno bez aktivniho tahu a nejisteho doruceni. UI, API, menu, zive profily a
  soukroma vlakna se nezmenily. Plna brana prosla 943 testy. Dalsi krok je faze
  4.4 – seskupene menu a bezpecne prepnuti/synchronizace/pripojeni ciloveho
  proudu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, univerzalni pracovni proudy faze 4.2. Neverejny
  backend vede 29 katalogovych slotu; Human–Adam a Knihovna zustavaji
  rezervovane pro migraci faze 4.5 a zbyvajicich 27 proudu muze lazy zalozit
  nebo obnovit vlastni soukrome Codex vlakno nad jednim sdilenym cistym
  workspace a runtime. Pri nacteni katalogu nevznika zadny adresar, klient ani
  vlakno. Prepnuti vyzaduje potvrzeni a blokuje aktivni tah, nejiste doruceni,
  necisty nebo nesynchronni workspace. UI, API, handoff/TVBCP vazby a zive
  profily se nezmenily. Plna brana prosla 930 testy. Dalsi krok je faze 4.3 –
  jeden kanonicky handoff a TVBCP kazdeho proudu a jejich bezpecne pouziti pri
  checkpointu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, univerzalni katalog pracovnich proudu faze 4.1.
  Validovany git-safe katalog ma po Milove rucni kontrole 29 proudu: 23
  projektu, 4 tooly a 2 `Misc`; 26 je aktivnich a iPhone Shortcuts / Mobile
  Input, Vocabulary FR a Vocabulary IT jsou pozastavene. Vsech 28 zivych radku
  tohoto registru zustava pokryto pres kanonicka slouceni. Human–Adam je
  kanonicky projekt s docasnymi runtime aliasy; UI, profily, workspace ani vlakna
  se nezmenily. Cilenych 107 testu, plna brana 922 testu za 248,040 sekundy a
  zivy smoke 5/5 prosly. Dalsi krok po checkpointu a zelenem CI je faze 4.2 –
  lazy soukroma vlakna nezavisla na dvou pevnych profilech. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Transformace Human–Adam faze 1.5. Mila rucne potvrdil vizualni
  roundtrip faze 1.4. Novy private completion protokol po uspesnem zapisovacim
  tahu skryje technickou JSON uctenku, odvodí z ni commit/souhrn/dalsi krok a
  spusti existujici direct-main backend: plna brana, handoff + TVBCP, commit,
  push a zarovnani aktivniho i ostatnich cistych profilu. Chybejici nebo
  neplatna uctenka, neuspesna brana, konflikt a opakovane doruceni zustavaji
  fail-closed bez druheho commitu. UI ani API cesta se nezmenily. Cilena sada
  59 cilenych testu vcetne UTC runner regrese a finalni plna Cockpit brana 880
  testu za 239,849 sekundy prosly.
  Faze je commitnuta a pushnuta v `4bfd7fc`; skutecna GitHub Cockpit Quality
  Gate skoncila `success`. Faze zatim neni nasazena. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Faze 1.4 je na `main` v `6f17852`, nasazena po rizenem restartu na
  code stamp `7a4440b979d98690`; smoke prosel 5/5. Zivy endpointovy roundtrip
  kanonickymi ID Human–Adam -> Knihovna -> Human–Adam prosel a oba workspaces
  skoncily ciste, zarovnane, bez remote/WIP a aktivniho tahu. Aktivni zustal
  Human–Adam. Mila nasledne rucne potvrdil i vizualni kliknuti pres stejne menu
  na Knihovnu a zpet na Human–Adam. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, transformace Human–Adam faze 1.4. Stavajici vyberove
  menu je bez zmeny HTML/CSS vzhledu napojene na koordinator: status poskytuje
  katalog proudu, stejny endpoint prijima `workstream_id` a puvodni
  `profile_id` zustava vratnym fallbackem. Viditelne nazvy, potvrzeni i rozlozeni
  zustaly stejne; profilove ID je dal oddelene pro prechodny semafor a nasazeni.
  Cilena sada 93 testu, plna brana 871 testu za 170,754 sekundy a
  prednasazovaci smoke 5/5 prosly. Zmena jeste neni nasazena ani rucne
  prokliknuta. Po checkpointu faze 1.4 nasleduje nasazeni, restart a rucni
  roundtrip obema smery. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, transformace Human–Adam faze 1.3. Vznikl neveřejny
  koordinator pracovnich proudu se dvema zkušebnimi vazbami: `Layer`
  Human–Adam a `Project` Knihovna. Vyber proudu pouziva stavajici bezpecne
  prepnuti profilu, automaticky fast-forwarduje cisty cil z lokalniho `main` a
  zachovava samostatne vlakno, TVBCP, handoff i workspace. Roundtrip obema smery
  prosel; neznamy proud a nečista prace zustavaji fail-closed. Cilena sada ma 38
  testu, plna brana prosla 870 testy za 179,167 sekundy a smoke je 5/5. API, UI
  a runtime se nezmenily. Po checkpointu faze 1.3 je dalsi krok pripravit
  napojeni existujiciho vyberu bez zmeny vzhledu. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, `Layer` Human–Adam / vyvojove prostredi. Faze 1.2
  napojila neaktivni direct-main backend na profilovy manager a kanonickou vazbu
  Human–Adam: ID proudu, typ `Layer`, nazev, handoff a TVBCP uz nejsou volnym
  vstupem klienta. Aktivni profil je po celou operaci zamceny a ostatni profily
  vstupuji do peer kontroly. Knihovna bez terminalove registrace vlastniho proudu
  konci fail-closed. Tri nove testy prosly v cilene sade 34 testu; plna brana
  prosla 866 testy za 235,895 sekundy. API, UI a runtime se nezmenily. Po
  checkpointu faze 1.2 je dalsi krok domluvit presny rozsah nejmensi integracni
  vrstvy bez prepnuti UI. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, `Layer` Human–Adam / vyvojove prostredi. Faze 1.1
  pripravila samostatny neaktivni backend jednoducheho checkpointu: stateless
  preflight, plna brana, automaticky TVBCP + handoff, jeden commit na profilovem
  `main`, push stejneho objektu, fast-forward zdrojoveho `main` a zarovnani bez
  nove vetve a bez persistentniho semaforu. UI, API a zivy runtime nejsou
  prepnute. Sedm novych integracnich testu proslo za 33,252 sekundy, plna brana
  prosla 863 testy za 239,055 sekundy a smoke je 5/5. Dalsi krok je checkpoint a
  push faze 1.1; potom profilove napojeni backendu bez aktivace UI. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-20: Priorita 1, `Layer` Human–Adam / vyvojove prostredi. Body 0.1 az
  0.5 zalozily zaznam v `WORKSTREAMS.md`, potvrdily stavajici TVBCP, zapsaly
  kanonicky jednoduchy model: vlastni vlakno, kontext, TVBCP a handoff pro kazdy
  proud; bezny vyvoj primo na `main` bez WIP vetvi, prevzeti a semaforu. Read-only
  baseline potvrdil Cockpit smoke 5/5, hlavni UI, bezici app-server, zachovane
  vlakno Knihovny a dva ciste profilove workspaces. Oba profily pouze cekaji na
  synchronizaci novych pametovych checkpointu ze zdrojoveho `main`.
  Regresni baseline prosla kompilaci, JavaScriptem obou UI, shell syntaxi, 856
  testy za 198,475 sekundy a naslednym zivym smoke testem 5/5.
  Existujici oblast `App-server rozhrani / novy Adam` zustava docasnym
  kompatibilnim mostem kvuli soucasne profilove konfiguraci Cockpitu. Nebyla
  provedena zadna funkcni zmena. Dalsi krok je checkpoint a push kroku 0, potom
  synchronizace aktivniho profilu a prvni potvrzena implementacni faze. Handoff:
  `handoffs/human_adam_layer_workstream_start_2026_07_20.md`.
- 2026-07-19: Priorita 1, App-server rozhrani / novy Adam. Mila rucne potvrdil
  obsah napovedy `Prace -> ?`, ale maly vnitrni rolovaci box byl hur citelny nez
  velke zobrazeni v `Plan`. Ergonomicka oprava v izolovane vetvi
  `wip/human-adam-work-help-layout-20260719` odstranuje vlastni vyskovy limit a
  vnitrni scrollbar; roluje se cely velky panel `Prace`. Cilenych 50 UI testu i
  cela Cockpit brana prosly. Commit `20c64a7` je v `main`, rizeny restart na PID
  `33066`, petibodovy smoke test i zive HTML jsou zelene; zbyva pouze rucni
  vizualni retest.
  Handoff:
  `handoffs/human_adam_work_help_and_wip_lifecycle_2026_07_19.md`.
- 2026-07-19: Priorita 1, App-server rozhrani / novy Adam. Mila schvalil navrat
  k postupnemu zaziti uz naprogramovanych funkci. Prvni krok, staticka napoveda
  pod tlacitkem `?` v okne `Plan`, je nasazeny jako `5052a4c`; plna brana prosla
  825 testy, rizeny restart a petibodovy smoke test jsou zelene. Nyni zbyva
  rucne otevrit napovedu a projit ji bez zbytecne rotace. Potom nekolik dni
  bezne pouzivat soucasne workflow; audit aktualnosti handoffu se nema vyvijet
  drive. Handoff:
  `handoffs/human_adam_plan_help_and_adoption_2026_07_19.md`.
- 2026-07-19: Priorita 1, App-server rozhrani / novy Adam. Prvni read-only faze
  rizeni zivotniho cyklu WIP vetvi je hotova v izolovane vetvi. Samostatne jadro,
  CLI, workflow registrace, GET endpoint a male ovladani v panelu `Prace`
  klasifikuji vetve bez zmen Git referenci; pripojeny nebo rozpracovany worktree
  nikdy neni kandidat k uklidu. Plna Cockpit brana prosla 824 testy. Zbyva
  potvrzene prevzeti checkpointu do `main`, nasazeni, restart a zivy read-only
  test. Handoff: `handoffs/development_branch_lifecycle_phase1_wip_2026_07_19.md`.
- 2026-07-19: Priorita 1, App-server rozhrani / novy Adam. Commit `90ed06c`
  nasadil trvaly globalni vyvojovy semafor pro Human-Adam, Knihovnu a terminal,
  read-only modelovy guard a blokaci checkpointu/nasazeni pri cizim WIP. Plna
  brana prosla 815 testy, Cockpit byl rizene restartovany a read-only smoke test
  i stav `free` prosly. Zbyva rucni interaktivni retest. Navazujici napad na
  verzovany terminalovy deployment guard nebo kontrolovany `pre-push` hook je
  ulozeny, ale nema se instalovat automaticky. Handoff:
  `handoffs/global_development_semaphore_wip_2026_07_19.md`.
- 2026-07-19: Priorita 1, App-server rozhrani / novy Adam. V izolovane WIP vetvi
  je hotovy cely rez bezpecne rucni rotace dlouheho profiloveho vlakna: backend,
  profilove zamknute audit/apply API a ovladani v panelu `Plan`. Puvodni vlakno
  ani lokalni historie se nemazou a rotace vyzaduje pripojeni, aktivni kotvu,
  presnou potvrzovaci vetu a nulovou nejistotu doruceni. Cela Cockpit quality
  gate prosla 804 testy. Stav ceka na potvrzene prevzeti do `main`, nasazeni,
  vizualni kontrolu a zivy profilovy test. Handoff:
  `handoffs/human_adam_thread_rotation_backend_wip_2026_07_19.md`.
- 2026-07-18: Zdánlivě ztracený TVBCP WIP byl bezeztrátově obnoven, auditován a
  nasazen jako `ebd47b9`. Nová oprava rozlišuje přímo auditovatelný checkpoint od
  zachovaného rozvětveného WIP, ukáže jeho počet a cesty a audit ponechá
  fail-closed. Plná brána prošla 766 testy; po checkpointu/pushi zbývá restart a
  běžný smoke test. Handoff:
  `handoffs/human_adam_preserved_wip_visibility_2026_07_18.md`.
- 2026-07-17: Human–Adam má připravenou atomickou ochranu očekávané revize
  soukromé kotvy a oddělený redigovaný registr posledních 20 selhání pro každý
  profil. Plná brána prošla 764 testy; po checkpointu/pushi zbývá řízené nasazení
  a živý konfliktový retest Mac/iPhone. Handoff:
  `handoffs/human_adam_revision_failure_history_2026_07_17.md`.
- 2026-07-17: Znalostni databaze / Knihovna ma implementovany druhy pracovni
  profil r-Adama s vlastnim vlaknem, izolovanym workspace, TVBCP a deployment
  uctenkou. Atomicke prepnuti je fail-closed pri tahu, nejistem doruceni,
  rozpracovanych zmenach, WIP checkpointu, divergenci nebo nasazeni. Plna brana
  prosla 734 testy. Commit/push `6a2e205`, restart a zivy smoke test Human–Adam
  -> Knihovna -> Human–Adam prosly; oba workspaces jsou ciste, bez Git remote a
  aktivni zustal Human–Adam. Dalsi knihovni ukol lze zahajit vyberem profilu
  `Knihovna`. Handoff:
  `handoffs/human_adam_knihovna_profile_2026_07_17.md`.
- 2026-07-14: Externí recovery disk se po USB varování neenumeruje jako USB,
  Thunderbolt ani disk a ve `/Volumes` není. Poslední úspěšná záloha je z
  2026-07-09. Bez enumerace nespouštět mount/First Aid; nejdřív jiný datový kabel,
  přímý jiný port a stabilní napájení. Handoff:
  `handoffs/external_backup_disk_usb_not_detected_2026_07_14.md`.
- 2026-07-15: Samostatne panely App-server LAB a Adam Remote byly vyraceny z Cockpitu vcetne UI, API a sluzeb. Historicke handoffy zustavaji jen jako evidence; izolovany Git workspace pokracuje vyhradne jako vnitrni, otestovana soucast Human–Adam.
- 2026-07-09: Janička nouzova zaloha ma checkpoint `handoffs/janicka_full_adam_cockpit_recovery_ios_card_2026_07_09.md`. Stav: v Janičce je prvni karta `Když Adam light nestačí` / `Otevřít plného Adama`, ktera otevre primy interaktivni Codex v Terminalu bez VS Code a bez `samantha` wrapperu; na Macu jsou viditelne launchery pro Cockpit a iPhone zkratka `Janička SOS` je pripravena k nasdileni. Dalsi krok: zkratku importovat na Janin iPhone a rucne projit celou cestu s Janou.
- 2026-07-09: Cockpit / VoiceBridge / Janicka stabilita ma checkpoint `handoffs/cockpit_voice_janicka_stability_checkpoint_2026_07_09.md`. Stav: hlavni VoiceBridge rozlisuje Adam relaci, managed relace a orphaned Janicka relace; Janicka okno umi nabidnout uklid starych relaci; recoverable `Load failed` ve frontend statusu se po uspesnem health checku cisti; automaticka odpoved watcheru je explicitne oznacena jako automaticka, ne jako prevzeti v Codex chatu. Dalsi krok: po commitu/pushi ukoncit dlouhou relaci, zavrit VS Code, spustit Cockpit bez VS Code a rucne otestovat `Janicka` -> `Zeptat se Adama`.
- 2026-07-01: MMTX Scene 3 `Journey to the Lake` ma dodatecne opravy po rucnim retestu: `journey_lake_3a.png` je ve finalni verzi `20260701fix8` potvrzeny spravny kandidat, Benji/Bunny maji pevne Edge MP3 bez browser fallbacku (`Andrew`/`Ana`), Bruno je prepnuty z Edge `Guy` na lokalni hlubsi `Daniel`, start sceny prednacita prvni audio repliky a verze jsou zvednute na `20260701voice5`; pumpovaci hadanka nezvyraznuje Fionu predem, kruhova sipka opakuje aktualni obrazovou fazi, havran ma mensi hotspot a ceske `Krá krá`, leva cesta ma mensi hotspot mimo Benjiho, pred studnou je pulzujici hotspot dveri statku a slovnicek je rozsireny na 35 polozek vcetne `come`/`but`, novych MP3 a opravene vyslovnosti `live` jako `liv`. Webovy retest Scene 3 Mila potvrdil jako splneny; Benjiho hlas ma rezervy, ale scena je jinak OK.
- 2026-06-22: Cockpit / Knihovna / e-mail intake ma hotovy checkpoint `handoffs/cockpit_purchase_pdf_and_library_export_email_filter_2026_06_22.md`. Stav: hledani dokumentu umi najit soukromy nakupni archiv `data/private/purchases`, nakupni vysledek ma vlastni PDF ctecku `/purchases/read`/`/purchases/pdf` a exporty z Knihovny s prefixem `[SamanthaLibraryExport]` se uz nenabizeji ve fronte e-mailoveho/document intake zpracovani. Dalsi krok: commit + push jen kodu/testu/memory bez private dat, potom rucne overit v Cockpitu `dolphin` a e-mailovy refresh.
- 2026-06-22: Knihovna / zdravotni informace ma rozpracovany checkpoint `handoffs/knowledge_library_health_info_checkpoint_2026_06_22.md`. Stav: kategorie `health_info` je v backendu, Cockpitu a testech; existuje importni skript pro zdravotni kandidaty z ChatGPT exportu. Dalsi krok: read-only dry-run, rucni vyber smysluplnych clanku a neopisovat citlive zdravotni texty do chatu/gitu.
- 2026-06-23: Cockpit restart a Adam voice audio cleanup maji checkpoint `handoffs/cockpit_restart_button_and_voice_audio_cleanup_2026_06_23.md`. Stav: restart worker uz nebere rychly launchd restart jako chybu, UI pri prerusenem spojeni obnovi stranku a Edge TTS uz nepousti MP3 pres Apple Music. Dalsi krok: rucni klikaci retest `Servis -> Restart Cockpitu`.
- 2026-06-23: Knihovna ma checkpoint `handoffs/knowledge_library_read_state_to_read_2026_06_23.md`. Stav: clanky umi pracovni stav `K precteni` / `Hotovo`, Cockpit ma zalozku `K přečtení` napric kategoriemi a konkretni soukromy clanek o kratkozrakosti u deti je lokalne oznaceny k precteni. Dalsi krok: rucni UI retest v Cockpitu.
- 2026-06-26: ChatGPT export / Cestovani mista ma checkpoint `handoffs/chatgpt_travel_places_library_checkpoint_2026_06_26.md`. Stav: nova kategorie Knihovny `Cestování / místa` (`travel_places`) je v kodu, testech a pushnuta; soukromy kandidatni report je v private Knowledge inboxu a 4 ocistene cestovni karty jsou vlozene do private article archive se stavem `K přečtení`. Dalsi krok: rucne v Cockpitu overit zalozku `Cestování / místa`, 4 karty, fulltext a stav `K přečtení`.
- 2026-06-26: Capability registry ma checkpoint `handoffs/capability_registry_priority_gaps_closed_2026_06_26.md`. Stav: skutecny registry model a registry v kodu jsou na `main`, posledni commit `daf29b8` zavrel tri prioritni mezery a audit hlasi `Capability registry records: 28`, `Registry-covered agent tools: 25/81`, `Priority missing capability records: None`. Audit je rozdeleny podle rizika: kriticke/action-write mezery 0, action/review 14, read-only nebo low-risk 42. Dalsi krok: rozhodnout, kterou z tech dvou zbyvajicich vrstev registrovat jako dalsi malou davku.
- 2026-06-27: Capability registry ma finalni checkpoint `handoffs/capability_registry_complete_2026_06_27.md`. Stav: posledni commit `6e041a0 Complete low risk capability registry coverage` je pushnuty na `main`; audit hlasi `Capability registry records: 84`, `Registry-covered agent tools: 81/81`, vsechny missing vrstvy 0 a `Agent tools missing capability records: None`. Navazujici recovery zaloha a restore drill probehly 2026-06-27.
- 2026-06-27/28: Cockpit / VoiceBridge exact confirmation MVP je v `handoffs/cockpit_remote_exact_confirmation_cards_2026_06_27.md`. Stav: karta `Codex čeká na potvrzení` umi zobrazit presnou potvrzovaci vetu, zkopirovat ji a odeslat Adamovi z Cockpitu/iPhonu pres textovy hlasovy bridge; `codex_approval_notice.py set` ma `--confirmation-text`; cileny test `tests.test_adam_voice_mode tests.test_cockpit` prosel 212 OK. Dalsi krok: rucni iPhone/Mac test bezpecne testovaci karty a pak pokracovat v Cockpit auditu.
- 2026-06-29: VoiceBridge full-access blok ma finalni checkpoint `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`. Stav: mezistavy VoiceBridge jsou textove, finalni odpoved se zapisuje jednou a cte v browseru, neoverene GUI doruceni se uz nehlasi jako jiste, watcher start kontroluje rychly pad a tokenove potvrzovani e-mailovych draftu proslo realnym testem. Guard proti mazani neni novy automaticky dalsi krok: zakladni pravidlo uz existuje v `technical/global_safety_brake.md`; pripadna programova enforcement vrstva je jen volitelne budouci zprisneni.
- 2026-06-30: VoiceBridge ma provozni kontrakt `handoffs/voicebridge_operational_contract_2026_06_30.md`. Stav: popsane jsou kanonicke cesty textoveho pokynu, nahravaneho pokynu, prepisu audia, inboxu, watcher doruceni, mezistavu, finalni odpovedi, rizikovych potvrzeni, diagnostiky a minimalniho retestu. Tento handoff ma byt prvni cteni pred dalsim zasahem do hlasove komunikace.
- 2026-06-30: Cockpit autosave cleanup ma checkpoint `handoffs/cockpit_session_autosave_cleanup_2026_06_30.md`. Stav: skript `cleanup_session_autosave.py`, Cockpit endpoint a servisni tlacitko jsou hotove; dry-run po restartu Cockpitu hlasi cca 14.23 GiB k uvolneni. Ostry cleanup realneho `data/session_autosave/` zatim nebyl spusten a ma zustat potvrzovany.
- 2026-06-22: Quick Notes / dulezita pripomenuti maji checkpoint `handoffs/quick_notes_cockpit_refresh_regression_2026_06_22.md`. Stav: zkratky soubory dorucuji, regrese byla ve viditelnosti/refresh vrstve Cockpitu a obcasnem iCloud deadlocku; QN endpoint ma retry a frontend 30s monitor. Dalsi krok: pri dalsi nove QN sledovat, zda se otevreny Cockpit obnovi sam bez rucniho refresh.
