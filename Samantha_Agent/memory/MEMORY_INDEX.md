# Memory Index

Tento soubor je rozcestnik dlouhodobe pameti pro Samantha Agent.

- `ACTIVE_PROJECTS.md` - registr aktualne rozpracovanych oblasti, priorit, stavu, handoffu a dalsich kroku.

## Core

- `samantha_core.md` - zakladni kontext: kdo je Mila, co je Samantha Agent, aktualni stav prostredi, kanonicky stav Samantha Agent/RAG a dlouhodoby cil.
- `contacts.md` - prakticke kontakty, ktere Mila vyslovne povolil ulozit do pameti.

## Projects

- `projects/lekarna_domaci_leky.md` - projekt Lekarna: evidence domacich leku v `data/lekarna/`, vyhledavani podle potizi, audit lekarnicky a opakovatelny foto import workflow pres manifest.
- `projects/lekarna_web_app.md` - Webova aplikace Lekarna: publikovana GitHub Pages aplikace se sifrovanym balickem, cockpit UI, hadim dotazem, MP3 napovedou a ChatGPT copy fallbackem; dalsi vyvoj priorita 2.
- `projects/media_image_resize_utility.md` - obecna bezpecna utilita pro zmensovani obrazku podle cilove velikosti v kB; vychozi cil 250 kB, preset Lekarna 100 kB, preview + potvrzeny apply se zalohou.
- `projects/tax_priznani_2025.md` - daňové přiznání 2025, výpočty, checklist formuláře a pravidlo neukládat citlivé údaje.
- `projects/pictnew_vocabulary_image_pipeline.md` - opakovatelný audit a generování obrázků ke slovíčkům FR/IT přes `mapping.json`, `Pict/` a `PictNew/`.
- `projects/tts_edge_audio_tools.md` - české TTS/MP3 nástroje přes edge-tts, dávkový CSV režim a ruční GUI.
- `projects/vocabulary_en_web_cards.md` - webové obrazové kartičky EN z `VocabularyEN.csv`, sync do `docs/`, learner MVP a workflow pro chybějící obrázky.
- `projects/fraška_dante_esa_concept.md` - koncept eseje o frašce, dantovské ose, egu, smíření a nově definovaných pojmech.
- `projects/pohadkova_knizka_gpt_canva.md` - domácí dětská knížka z GPT pohádek, Canva sazba, stylová bible a workflow pro ilustrace.
- `projects/vedecke_clanky.md` - knihovna průlomových vědeckých článků v `data/vedecke_clanky/`, evidence PDF, odkazů, obrázků, shrnutí a pravidlo ptát se před internetovým doplněním.
- `projects/matysek_english_game_concept.md` - koncept anglické hry pro pětiletého Matýska bez čtení, se scénami, hlasem a příběhem.
- `projects/mmtx_story_hotspot_app.md` - nový směr MMTX: příběhová Pygame hotspot aplikace s houbami, barvami a dynamickým číslováním.
- `projects/multilo_stabilization_cleanup.md` - stabilizace MultiLO návratu do kokpitu, cleanup screenů, pending after callbacky a `tk.Entry` v psacích režimech.
- `projects/email_readonly_oauth.md` - e-mailová integrace Samanthy: read-only hledání/čtení/triage/archivace, Seznam+iCloud provider a od 2026-05-26 samostatné dvoukrokové potvrzené přeposlání přes lokální SMTP draft.
- `projects/document_management_private_vault.md` - priorita 1 projekt soukrome spravy dokumentu mimo git; aktualni vstup je ScanDocu pro GPT PDF z Downloads a prototyp Samantha Cockpit jako ovladaci vrstva, mimo git-safe data.
- `projects/samantha_external_backup.md` - [PRIPOMENOUT] offline zálohování `PythonMF`/Samanthy na externí disk: poslední úspěšná recovery záloha je 2026-06-03 ve snapshotu `20260603_175327`; proběhla přes Pythonový inkrementální nástroj bez `rsync/mmap`; potvrzený úklid nedokončených snapshotů a starého nafouknutého snapshotu uvolnil místo zhruba z `54Gi` na `24Gi`; při příští recovery záloze připomenout restore drill do `/private/tmp`.
- `projects/pozustalost_rodinny_plan_2026_05_30.txt` - [PRIPOMENOUT] priorita 1 rodinný nouzový balíček / pozůstalost: git-safe návrh struktury pro šifrovaný private balík; technicky nestavět druhý dokumentový systém, ale použít Document Management jako hlavní trezor, pozůstalostní metadata/tagy a samostatný šifrovaný export; soukromé šablony jsou mimo git v `data/private/pozustalost/`.
- `projects/neuberk_interier_design.md` - projekt Neuberk interiér design: soukromý pracovní prostor pro fotky, plánky, rozměry a návrhy interiéru domu; první místnost je půdní hostovská místnost `Kačenka` pro dcery s dětmi, podklady jsou mimo git v `data/private/neuberk_interier_design/`.
- `projects/automated_recurring_tasks.md` - automatické opakující se úkoly: `scripts/daily_3am.py`, GitHub Actions workflow a ColorsAndNumbers soví TTS tasky; `owl_230526.mp3` byl vygenerován v commitu `c8647de` a kontrola 2026-05-26 potvrdila existenci `owl_240526.mp3`.
- `projects/tomik_video_imovie.md` - [PRIPOMENOUT] projekt priorita 1 pro rodinny iMovie sestřih z malych videi od dcery, tema vnuk Tomik druhy rok; workflow, soukromi, storyboard a exportni checklist.
- `../RECOVERY_FROM_BACKUP.md` - lidský a Codex návod pro obnovu Samanthy z externí zálohy na novém Macu.

## Infrastructure Recovery

- `infrastructure/operating_model.md` - kratky provozni rozcestnik pro bezny start prace, systemove reporty, git checkpointy, reconnect recovery, sitove incidenty a kvantitativni metriky.
- `infrastructure/macos_network_recovery.md` - [PRIPOMENOUT] rozcestnik pro DHCP failure, VPN/Tailscale recovery, network plist reset, hotspot/Wi-Fi repair, network watchdog a aktualni diagnozu domaci Wi-Fi/router vs Mac.
- `infrastructure/codex_reconnect_recovery.md` - [PRIPOMENOUT] reconnect loop handling, navazani pres `samantha`/`screen`, `codex resume`, safe recovery after stream failure a pravidlo nejdrive cist git status + memory.
- `infrastructure/git_checkpoint_protocol.md` - [PRIPOMENOUT] commit pred rizikovymi operacemi, push pred reconnect recovery, zakaz `git add .`, ochrana cizich zmen a citlivych dat.
- `infrastructure/ssh_setup.md` - SSH/screen workflow pro vzdalenou praci se Samanthou bez ukladani privatnich SSH tajemstvi.
- `infrastructure/tailscale_setup.md` - Tailscale provozni poznamky, opatrny start po sitovem incidentu a odkazy na macOS network recovery.

## Handoffs

- `handoffs/git_commit_cleanup_a1_2026_05_23.md` - A1+ commitovy uklid: velka memory/RAG davka je commitnuta a pushnuta jako `ef15589`; pravidlo do odvolani je navrhovat tematicke commity pri dalsich vetsich rozpracovanych zmenach.
- `handoffs/cockpit_recovery_center_priority_2026_06_03.md` - [PRIPOMENOUT] priorita 1 pro pristi praci na Cockpitu: navrhnout a implementovat read-only Recovery centrum pro navazani po padu Samanthy/Codexu, s poslednim autosave timestampem, git statusem, handoffem a postupem `samantha` / `codex resume --last`.
- `handoffs/memory_cleanup_commit_afternoon_checkpoint_2026_05_23.md` - historicky checkpoint commitoveho odpoledne: Dokumenty, Lekarna, PictNew/VocabularyIT, Tomik/FamilyVideoOrganizer, E-mail, Samantha/RAG a automaticke ukoly byly zkomprimovane a commitnute v `ef15589`.
- `handoffs/automated_recurring_tasks_cloud_2026_05_20.md` - historicky mezistav automatickych ukolu: obecna denni rutina ve 3:00, macOS `launchd`, GitHub Actions skeleton a bezpecnostni pravidla.
- `handoffs/colors_numbers_owl_tts_startup_prompt_2026_05_22.md` - historicky mezistav automatickych ukolu: jednorazovy ColorsAndNumbers soví TTS task pro 2026-05-23 a denni startovni dotaz.
- `handoffs/lekarna_web_app_hotovo_2026_05_20.md` - Webova aplikace Lekarna je uzavrena jako hotova; verejna aplikace bezi se sifrovanym balickem a dalsi vyvoj je priorita 2 az podle casu nebo urgentnich pozadavku.
- `handoffs/lekarna_status_po_doplneni_vitaminu_2026_05_21.md` - Lekarna: aktualni stav po kokpitu, doze vitaminu, obrazku doporuceni, fotkach Kozliku/Vigantolvitu a oprave fallbacku; Silymarin stale nema vlastni fotku.
- `handoffs/matysek_forest_school_scene_navrh_2026_05_26.md` - [PRIPOMENOUT] Matysek MMTX Forest School: soukromy navrh je v `data/private/matysek_english/`, webova scena `forestSchool` je rozpracovana v `docs/` a mirroru `MatysekANJ/web_mmtx/`; dalsi krok je rucni test URL `?scene=forestSchool`.
- `handoffs/matysek_forest_school_checkpoint_2026_05_26.md` - [PRIPOMENOUT] aktualni checkpoint ForestSchool po doladeni: demo Bunny/Benji, lokalni hlasy, mochomurkove odmeny, neopakovani predmetu, prvni petka obrazku a dalsi krok rucni test + vyber dalsich predmetu.
- `handoffs/matysek_forest_school_post_commit_checkpoint_2026_05_26.md` - [PRIPOMENOUT] post-commit checkpoint ForestSchool: relevantni zmeny jsou pushnute jako `9850298 Add Matysek Forest School scene`; dalsi krok je rucni test a vyber dalsich predmetu.
- `handoffs/matysek_forest_school_lessons_voices_checkpoint_2026_05_27.md` - [PRIPOMENOUT] aktualni ForestSchool checkpoint: obrazky lekci 2-12 jsou vygenerovane a nasazene do `docs/` i mirroru, Benji/Bunny maji nove mladsi/detske anglicke hlasy, dalsi krok je commit/push a napojeni lekci do JS.
- `handoffs/matysek_forest_school_portal_resize_checkpoint_2026_05_27.md` - [PRIPOMENOUT] aktualni ForestSchool checkpoint: 12 lekci je napojenych, mapa lekci umi skok na lekci, rozcestnik ma portal ForestSchool, predmetove PNG jsou zmensene na 420x420 px pod 250 kB a posledni push je `734f614 Add Forest School portal and compress assets`; dalsi krok je rucni retest v prohlizeci.
- `handoffs/matysek_forest_journey_voice_strategy_2026_06_01.md` - [PRIPOMENOUT] Matysek Forest Journey: stary Bunny hlas z puvodni sceny je konzistentni jen pro existujici MP3 a neumi nove vety typu `We are friends.`; nove `echo` kandidaty nesedely, proto je dalsi krok pred programovanim rozhodnout hlasovou strategii cele kapitoly a sepsat vsechny budouci Bunny vety pro sceny 1-6.
- `handoffs/matysek_f5tts_bunny_voice_tool_checkpoint_2026_06_02.md` - [PRIPOMENOUT] Matysek English F5-TTS Bunny tool: lokalni F5 CLI po virtualenv patchi funguje, reference nad ~12 s se klipuje a dava spatny vysledek, 12s a puvodni kratka reference zni Mile podobne; dalsi krok je pouzit wrapper `scripts/matysek_f5tts_generate.py` s puvodni kratkou referenci a generovat male davky Bunny vet.
- `handoffs/matysek_scene_01_clearing_meeting_review_2026_06_01.md` - [PRIPOMENOUT] Matysek forest journey: story bible a obrazky jsou odsouhlasene; aktualni prace je prvni scena `Clearing Meeting`, Mila muze rucne upravit `scene_01_clearing_meeting.md` a dalsi krok je diff + finalni scenar s anglickou hlasovou napovedou, blikajici sipkou u aktivni postavy a ceskou souhrnnou napovedou vpravo nahore.
- `handoffs/matysek_scene_01_sunny_voice_and_ending_2026_06_03.md` - [PRIPOMENOUT] Matysek Forest Journey scena 1: Sunny hlas je zafixovan na `young_nova`, dve Sunny MP3 jsou nasazene do `docs/` i mirroru, zaverecny prompt je `Great. Open the door or run again.` a ceska veta je doplnena jen do finale; dalsi krok je rucni produkcni retest.
- `handoffs/family_video_organizer_ui_prototype_2026_05_22.md` - FamilyVideoOrganizer: prvni lokalni webovy UI prototyp je v `docs/family-video-organizer/`, umi tabulku, filtry, autosave, export JSON a video modal; dalsi krok je realny soukromy datovy balicek mimo git.
- `handoffs/family_video_organizer_package_ready_2026_05_29.md` - FamilyVideoOrganizer: realny lehky ZIP pro dceru byl podle Mily 2026-05-29 poslany; generator `tomik_family_video_package.py` vytvari `videos-data.js`/nahledy, UI ma Safari fallback, zelene tlacitko videi a zamykani radku; dalsi krok je pockat na dcerin export JSON.
- `handoffs/pozustalost_start_2026_05_30.md` - [PRIPOMENOUT] Pozůstalost / rodinný nouzový balíček založen jako priorita 1: další krok je projít návrh s Mílou a Janou, vybrat MVP, založit soukromé šablony mimo git a právní část ověřit s notářem.
- `handoffs/backup_usb_hub_restart_checkpoint_2026_06_03.md` - záloha Samanthy: původní hub selhal, přes přímější propojku a Pythonový fallback vznikl úspěšný snapshot `20260603_175327`; potvrzeně byly smazány nedokončené snapshoty `20260603_162647`, `20260603_163709` a starý nafouknutý `20260529_225518`.
- `handoffs/neuberk_interier_design_start_2026_05_31.md` - Neuberk interiér design / Kačenka: založen soukromý prostor mimo git pro fotky, plánky, rozměry a návrhy; další krok je dodat podklady a vyplnit brief místnosti.
- `handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md` - aktualni network/reconnect stav: domaci watchdog ukazal 29 vypadku za 30 minut a casto selhal i ping na gateway `192.168.1.1`; pracovni Wi-Fi retest mel 319/320 OK, takze dalsi krok je domaci router/Wi-Fi/ruseni/linka a retest po zasahu.
- `handoffs/network_https_reconnect_diagnostic_2026_05_21.md` - historicky network mezistav: prvni HTTPS failure diagnostika a vznik `scripts/network_watchdog.py`; prekryto novejsim handoffem `network_domaci_wifi_router_vs_mac_2026_05_21.md` a kanonickym stavem v `infrastructure/macos_network_recovery.md`.
- `handoffs/payment_sms_reminder_tool_done_2026_05_21.md` - Platebni SMS workflow je hotovy: `inspect_payment_page_for_reminder` read-only overi splatnost z HTTPS stranky/API bez plne URL/tokenu, `save_payment_sms_reminder` ulozi overovaci nebo platebni pripominku a `save_payment_case_document` ulozi lokalni fakturu/prilohu do `data/private/payment_cases/`.
- `handoffs/mobile_document_scan_shortcuts_and_processing_2026_05_26.md` - [PRIPOMENOUT] dokumentovy vault: iPhone zkratka `Skenovat dokument pro Samanthu v4` uklada vice stran do `SamanthaDocumentInbox`, zkratka pro zpracovani vytvari `process_request.json`, `scan_mobile_document_inbox` a `prepare_mobile_document_batch` jsou implementovane a realny batch `scan_B` byl pripraven do pracovního PDF; dalsi krok je potvrzovany finalni import do vaultu.
- `handoffs/mobile_document_processing_raw_bw_classification_2026_05_27.md` - [PRIPOMENOUT] dokumentovy vault: hlavni nova cesta je ScanDocu pro GPT PDF z Downloads; prototyp Samantha Cockpit bezi a oprava samostatneho okna ScanDocu je overena; dalsi krok je ranni realny test dalsiho dokumentu.
- `handoffs/document_management_scandocu_reimport_checkpoint_2026_05_28.md` - [PRIPOMENOUT] dokumentovy vault: ScanDocu umi revidovat uz ulozene dokumenty, lepe cte metadata vozidel a preskakuje stare sifrovane varianty po ulozeni odemcene kopie; dalsi krok priorita 1 je po nove kopii v Downloads pokracovat dokument po dokumentu ve znovuukladani/revizi uz ulozenych priloh.
- `handoffs/document_management_cockpit_voice_command_inbox_2026_05_29.md` - dokumentovy vault/cockpit: koncept hlasoveho nebo textoveho command inboxu z iPhonu pres iCloud, read-only intent routing pro dokumenty/e-maily/statusy a potvrzovaci brany pro tisk, archivaci, mazani a odesilani.
- `handoffs/cockpit_web_apps_checkpoint_2026_05_29.md` - Samantha Cockpit: pridane tlacitko Webove aplikace, katalog aplikaci, samostatne popup otevirani aby zavreni aplikace nezavrelo Cockpit; lokalni commity Cockpitu a UTF-8 opravy jsou hotove, dalsi krok je pripadny push.
- `handoffs/cockpit_dashboard_terminal_launch_checkpoint_2026_05_29.md` - Samantha Cockpit: dashboard Dnes/Stav/Akce, git status, tlacitka Samantha chat a Codex CLI; puvodni stav branch ahead 6 je prekryty, Cockpit commity jsou podle `git log` na `origin/main` a aktualni `HEAD` i `origin/main` jsou `e123d52 Add emotion management tool notes`.
- `handoffs/cockpit_global_hotkey_agent_2026_06_01.md` - Samantha Cockpit: globalni klavesova zkratka pres vlastni Swift/Carbon hotkey agenta a LaunchAgent; Finder Services cesta byla nespolehliva, novy agent funguje po rucnim testu `Ctrl + Option + Cmd + C`.
- `handoffs/document_vault_next_physical_print_and_downloads_intake_2026_05_22.md` - dokumentovy vault: fyzicky tisk byl Milou overen na TXT dokumentu o zkratkach; dalsi plan je klasifikace/vazby mezi dokumenty a potvrzovany intake ze slozky Stazene/Downloads do inboxu.
- `handoffs/media_image_resize_utility_done_2026_05_20.md` - Obecna utilita `app/media/image_resize.py` je hotova a overena na lekarne; dalsi krok je pri pouziti na slovniky nejdriv udelat preview a zvolit cilovou velikost.
- `handoffs/vocabularyit_mapping_applied_2026_05_20.md` - VocabularyIT/PictNew finalni stav aktualni vlny: `Pict/mapping.json` byl po schvalenem preview aktualizovan, audit je cisty a git checkpoint existuje jako `851b347 Apply VocabularyIT picture mapping updates`.
- `handoffs/samantha_agent_rag_search_memory_ranking_2026_05_19.md` - historicky RAG mezistav: `search_memory` ma vylepseny ranking a vystup; aktualni kanonicky stav je v `samantha_core.md`.
- `handoffs/session_recovery_autosave_2026_05_18.txt` - handoff ke konverzaci o navazovani po vypadku, `screen`, prikazu `samantha`, `codex resume` a autosave session logu po 10 minutach.
- `handoffs/test_kratky_handoff_2026_05_18.md` - testovaci handoff s prioritou 3 bez pripomenuti pri startu, overeni pravidla pro kratky handoff.
- `handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md` - Seznam e-mail: prvnich 500 vysledku pro pojisteni/smlouvy ma worklist, 34 UID slozek a 129 lokalne stazenych priloh v `data/private/email_seznam/`; navazovat jen podle potvrzovaneho read-only/document workflow.
- `handoffs/email_seznam_readonly_provider_2026_05_22.md` - aktualni e-mailovy stav: iCloud read-only vrstvy existuji, Seznam Mail read-only provider a `Unified Inbox` jsou implementovane, lokalni Seznam `.env` je vyplneny a smoke test hlavicek 2026-05-23 prosel bez vypisu predmetu/adres.
- `handoffs/email_outbound_sms_triage_next_2026_05_28.md` - [PRIPOMENOUT] aktualni e-mailovy handoff: e-mail outbound uklada kopii do iCloud Sent Messages, `send_confirmed_sms_rcs` ma potvrzovaci branu a kontrolu `is_sent/is_delivered/error`, plne triage reporty se ukladaji lokalne mimo git a pojistna PDF maji dohledana pravidla k heslum bez ulozeni skutecnych hodnot.
- `handoffs/email_processing_cleanup_and_documents_next_2026_06_03.md` - [PRIPOMENOUT] Email Processing v Cockpitu je uspokojive uzavreny: Work Queue ma oddelene zpracovani, presun do kose a trvale smazani z kose, nove nacitani filtruje historicky dokoncene polozky a priste se ma pokracovat obecnym zpracovanim dokumentu.
- `handoffs/email_processing_cockpit_decision_ui_2026_06_01.md` - [PRIPOMENOUT] Email Processing v Cockpitu: 7denni e-mailovy prehled se zobrazuje jako rozhodovaci karty po sekcich s volbami `Zpracovat`, `Ignorovat` a `Kos`; `Nacist nove hlavicky` pridava jen novejsi zpravy primo do hlavniho seznamu; skutecne cteni/stahovani/mazani musi zustat potvrzovane.
- `handoffs/email_work_queue_detail_checkpoint_2026_06_01.md` - [PRIPOMENOUT] Email Work Queue checkpoint: detail e-mailu se nacita read-only, `Zpracovat davku` uklada e-maily do EmailArchiveVault, vybrane PDF prilohy importuje do private document vaultu vcetne fulltextoveho indexu, `Neukladat` uzavira bez provider callu a `Kos` vyzaduje presnou potvrzovaci vetu; dalsi krok je rucni realny test male davky a potom opatrny test jedne zcela bezpecne zpravy do kose.
- `handoffs/email_work_queue_batch_tomorrow_2026_06_01.md` - [PRIPOMENOUT] zitrejsi navazani na Email Work Queue: batch endpoint je hotovy, PDF prilohy jdou do document vault fulltextu, kos ma potvrzovaci vetu a dalsi krok je maly realny test bez mazani, potom opatrny test jedne bezpecne zpravy do kose.
- `handoffs/email_weekly_overview_resume_2026_06_01.md` - [PRIPOMENOUT] Email management: rozpracovany 7denni read-only prehled hlavicek, soukromy resume detail s UID je mimo git v `data/private/email_session_handoffs/weekly_email_overview_2026_06_01_private.md`; dalsi krok je vybrat konkretni UID a az po potvrzeni nacist e-mail/PDF.
- `handoffs/iphone_shortcuts_najit_auto_done_2026_05_23.md` - hotovy checkpoint iPhone zkratek: Shortcuts Playground plugin pro Codex je nainstalovany, `Najit auto v3.shortcut` funguje u Mily i Jany a kanonicke pouceni je v `technical/iphone_shortcuts_playground.md`.
- `handoffs/iphone_shortcuts_quick_notes_continue_2026_05_23.md` - [PRIPOMENOUT] zitrejsi navazani na iPhone zkratky: quick notes zkratka funguje, Samantha umi ocislovany seznam/detail poznamek a dalsi krok je vybrat dalsi malou zkratku nebo akci z poznamky.
- `handoffs/iphone_shortcuts_freeze_infrastructure_layer_2026_05_25.md` - aktualni zmrazovaci handoff pro iPhone Shortcuts / Mobile Input Layer: doplneny puvodni seznam 7 kandidatu na zkratky, stav hotovych zkratek, bezpecnostni hranice a pravidlo nepokracovat bez vyslovneho navratu.
- `handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md` - doslovne ulozeny feedback k QN #13 systemova mapa, QN #10 ziva znalostni databaze a QN #4/#6 bezpecny akcni inbox; ceka na brzké zapracovani.
- `handoffs/stories_batch_2026_05_14.md` - batch více pohádek z jednoho chatu, rozdělený do samostatných story memory souborů.
- `handoffs/chatgpt_handoff_2026_05_14.md` - kompaktní předání po dlouhém ChatGPT vlákně, včetně promptu pro Codex a promptu pro nový ChatGPT chat.
- `handoffs/mmtx_web_handoff_2026_05_14.md` - handoff k webové verzi MMTX v `docs/`, hotovým scénám OwlGarden a HouseBunny, audio strategii a mirroru.

## Technical Rules

- `technical/naming_conventions.md` - názvosloví: Samantha je běžný ChatGPT, Codex je pracovní agent v projektu, Codex CLI je terminálový nástroj.
- `technical/samantha_growth_rules.md` - [PRIPOMENOUT] A1+ deset preventivnich pravidel pro rust Samanthy, tri maximalne prioritni body po commitovem uklidu a handoff compression per project; po velkem commitu nabidnout cisty stul, pouceni z uklidu a jasnejsi rezim vyvoje.
- `technical/samantha_cultural_metaphors.md` - kulturni/prakticke metafory pro Samanthu, vcetne `samyce/samice`: agent ma hledat lidsky zamer i pri preklepu nebo nepresnem vstupu.
- `technical/story_memory_rules.md` - pravidla pro ukládání pohádek do memory: ukládat plný finální text, ne jen shrnutí, a sledovat clean verzi pro předčítání.
- `technical/codex_permissions_preferences.md` - preference pro navrhovani trvalych Codex povoleni u rutinnich prikazu, vcetne TTS a git publikace.
- `technical/session_recovery_rules.md` - pravidla pro navazani po vypadku SSH/Codexu: `screen`, `samantha`, `codex resume`, handoff soubory a primerene checkpointovani dlouhych ukolu bez zbytecne rezie u drobnosti.
- `technical/capability_routing_rules.md` - obecne pravidlo pro vsechny projekty: lidsky pokyn -> pochopeny zamer -> registrovana schopnost/tool/workflow -> bezpecnostni rozsah -> potvrzeni podle rizika + volba miry workflow rezie.
- `technical/system_reports.md` - prehled dostupnych systemovych reportu Samanthy, jejich ucelu, spusteni a pravidel pro pridavani dalsich reportu.
- `technical/large_context_intake.md` - pravidla a lokalni ignorovany adresar pro velke podklady k prostudovani, vcetne budoucich exportu chatu, bez commitovani soukromych dat.
- `technical/iphone_shortcuts_playground.md` - workflow pro budouci tvorbu Apple Shortcuts/iPhone zkratek pres MacStories Shortcuts Playground, vcetne status toolu, request draftu a rucniho overeni vystupu.
- `technical/shopping_research_and_purchase_archive.md` - priorita 2 koncept lehkeho nakupniho workflow/toolu: pruzkum kamennych prodejen do 100 km od Mlade Boleslavi, overene e-shopy, prime odkazy na produkty a soukromy archiv objednavek/faktur pro zaruku.
- `technical/general_reminders_workflow.md` - obecne pravidlo pro SMS/e-mail/telefon/papir pripominky: konkretni ukoly s datem patri do `data/reminders/reminders.json`, projektovy kontext do memory/handoffu a opakovane rutiny do automatickych ukolu.
- `technical/private_document_vault_workflow.md` - workflow pro vkladani, trideni, indexaci, due date extrakci a vyhledavani soukromych dokumentu v `data/private/documents/`; MVP tooly uz existuji.
- `technical/lekarna_pil_short_workflow.md` - kanonicky workflow pro doplnovani `PIL_Short`: SÚKL DLP sparovani, statusy jistoty, prakticky nealarmisticky vytah, zaloha CSV a testy.
- `technical/lekarna_photo_import_intake.md` - kanonicky vstupni checklist pro nove fotky lekarna: co ma Mila dodat, kam patri polozky, potvrzovaci vety a bezpecny postup importu.
- `technical/workflow_command_registry.md` - pravidlo, ze lidske workflow pokyny se maji mapovat na predem schvalene presne prikazy v registru, ne na ad hoc shell vymysleny modelem.
- `technical/project_capability_map.md` - [PRIPOMENOUT] potvrzena taxonomie `Project` / `Tool` / `Infrastructure capability`; iPhone Shortcuts jsou Mobile Input Layer, ne samostatny projekt; priorita 1 pro prvni nizkorizikove workflow kandidaty zustava `PictNew` read-only audit a `VocabularyEN` sync do `docs/`.
- `technical/vocabulary_image_generation_workflow.md` - [PRIPOMENOUT] pozlacený kanonický workflow pro slovníkové obrázky: audit/request, dry-run, potvrzené placené generování po dávkách, review, kopie do `Pict/`, mapping až po samostatném potvrzení a git checkpoint.
- `technical/matysek_f5tts_voice_workflow.md` - [PRIPOMENOUT] lokalni F5-TTS workflow/tool pro Matysek English Bunny hlas: wrapper `scripts/matysek_f5tts_generate.py`, pravidlo reference do ~12 s, presny `ref_text`, CPU casy a pouceni z porovnani 20s/12s/puvodni kratke reference.
- `technical/macos_wifi_vpn_tailscale_recovery.md` - priorita 1: recovery protokol pro macOS Wi-Fi/DHCP/VPN/Tailscale vypadky po rozbitem routovani nebo tunnel rozhranich.
- `../NETWORK_RECOVERY_CARD.txt` - offline nouzova karta pro pripad, ze nejde internet a nejde se dostat do ChatGPT; lze vypsat pres `scripts/network_recovery_card.sh`.

## Stories

- `stories/pohadka_viridana_2026_05_14.md` - finální pohádka Matýsek, Martínka a robot Piškot na planetě Viridana.
- `stories/pohadka_robot_piskot_pribeh_kamarada_z_budoucnosti_2026_05_14.md` - příběh o robotu Piškotovi jako kamarádovi z budoucnosti.
- `stories/pohadka_o_matyskovi_martince_a_piskotovi_na_planete_tisice_zazraku_2026_05_14.md` - výprava Matýska, Martínky a Piškota na Planetu Tisíce Zázraků.
- `stories/pohadka_o_velke_vyprave_na_mars_2026_05_14.md` - marťanská výprava Matýska, Martínky a Piškota.
- `stories/pohadka_o_ceste_na_arkturion_modrou_planetu_ledu_2026_05_14.md` - zimní dobrodružství na Arkturionu a záchrana Velkého světla.
- `stories/pohadka_o_akvapolis_meste_pod_morem_2026_05_14.md` - podmořské město Akvapolis a krystal srdce oceánu.
- `stories/pohadka_o_silvanoru_planete_kde_mluvi_stromy_2026_05_14.md` - Silvanor, planeta věčného lesa a Strom Života.
- `stories/pohadka_o_saffronii_planete_zpivajiciho_pisku_2026_05_14.md` - Saffronia a rytmus zpívajícího písku.
- `stories/pohadka_lunaris_misto_kde_se_uci_naslouchat_tichu_2026_05_14.md` - Lunaris, měsíční svět ticha, času a pozorného naslouchání.

## Aktualni stav

- Mila buduje osobniho AI agenta Samantha.
- Codex CLI uz funguje v projektu `PythonMF`.
- Node.js, npm, Python 3.12 a OpenAI API key jsou pripravene.
- Skutecne API klice ani jine citlive udaje se do pameti ani do gitu nezapisuji.

## Planovany smer

1. Vytvorit lokalni pamet pro Samantha Agent.
2. Postavit prvni verzi agenta nad OpenAI Agents SDK.
3. Pozdeji pridat RAG nad exporty z ChatGPT.
