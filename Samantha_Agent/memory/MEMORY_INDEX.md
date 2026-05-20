# Memory Index

Tento soubor je rozcestnik dlouhodobe pameti pro Samantha Agent.

- `ACTIVE_PROJECTS.md` - registr aktualne rozpracovanych oblasti, priorit, stavu, handoffu a dalsich kroku.

## Core

- `samantha_core.md` - zakladni kontext: kdo je Mila, co je Samantha Agent, aktualni stav prostredi a dlouhodoby cil.
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
- `projects/email_readonly_oauth.md` - plán bezpečné read-only OAuth integrace e-mailu pro Samanthu, bez ukládání tokenů nebo obsahu e-mailů do gitu či paměti.
- `projects/samantha_external_backup.md` - návrh offline zálohování `PythonMF`/Samanthy na externí disk: safe/recovery profily, šifrovaný kontejner, dry-run skript a 3denní připomínka.
- `projects/automated_recurring_tasks.md` - [PRIPOMENOUT] obecná rutina pro automatické opakující se úkoly: `scripts/daily_3am.py`, macOS launchd, GitHub Actions/cloud směr a bezpečnostní pravidla pro budoucí TTS/git tasky.
- `../RECOVERY_FROM_BACKUP.md` - lidský a Codex návod pro obnovu Samanthy z externí zálohy na novém Macu.

## Infrastructure Recovery

- `infrastructure/macos_network_recovery.md` - [PRIPOMENOUT] rozcestnik pro DHCP failure, VPN/Tailscale recovery, network plist reset, hotspot/Wi-Fi repair a offline `NETWORK_RECOVERY_CARD.txt`.
- `infrastructure/codex_reconnect_recovery.md` - [PRIPOMENOUT] reconnect loop handling, navazani pres `samantha`/`screen`, `codex resume`, safe recovery after stream failure a pravidlo nejdrive cist git status + memory.
- `infrastructure/git_checkpoint_protocol.md` - [PRIPOMENOUT] commit pred rizikovymi operacemi, push pred reconnect recovery, zakaz `git add .`, ochrana cizich zmen a citlivych dat.
- `infrastructure/ssh_setup.md` - SSH/screen workflow pro vzdalenou praci se Samanthou bez ukladani privatnich SSH tajemstvi.
- `infrastructure/tailscale_setup.md` - Tailscale provozni poznamky, opatrny start po sitovem incidentu a odkazy na macOS network recovery.

## Handoffs

- `handoffs/automated_recurring_tasks_cloud_2026_05_20.md` - [PRIPOMENOUT] obecná denní rutina ve 3:00 je založená; další vývoj priorita 1 směrem GitHub Actions/cloud, potom první reálný task adapter s allowlistem a testy.
- `handoffs/dnesni_checkpoint_lekarna_pictnew_git_2026_05_20.md` - [PRIPOMENOUT] denni checkpoint 2026-05-20: Lekarna, media image resize, PictNew batche 001-004 a cilene ulozeni dnesni prace do gitu; dalsi krok je vizualni kontrola batchu 002-004 a batch 005 jen po potvrzeni.
- `handoffs/lekarna_audit_tool_done_2026_05_19.md` - [PRIPOMENOUT] Lekarna ma druhy read-only Samantha tool `audit_domaci_lekarna`, ktery vraci checklist polozek k fyzicke kontrole: expirace, umisteni, `nutno_overit`, zbytky bez krabicky, jistota cteni, antibiotika a redeni krve; dalsi krok je live test pres Samanthu a az potom navrh potvrzovaneho zapisoveho workflow.
- `handoffs/lekarna_import_vyrazeni_resize_done_2026_05_20.md` - [PRIPOMENOUT] Lekarna: import novych JPEG/WhatsApp fotek, umisteni, soft-delete workflow pro vyrazeni leku a zmenseni fotek na cca 100 kB jsou hotove; dalsi krok je vratit se k Milovu `Samantha_GIT_PUSH.txt`.
- `handoffs/lekarna_pil_short_done_web_app_start_2026_05_20.md` - [PRIPOMENOUT] Lekarna: `PIL_Short` nebo vysvetlujici status je doplnen pro vsech 56 radku, workflow je zdokumentovane a zacina samostatny projekt webove aplikace pro Janicku; dalsi krok je rozhodnout git-safe export poli.
- `handoffs/lekarna_web_app_cockpit_prototype_2026_05_20.md` - Webova aplikace Lekarna: drivejsi cockpit prototyp v `docs/lekarna/`, nasledne prekryto hotovo handoffem.
- `handoffs/lekarna_web_app_hotovo_2026_05_20.md` - Webova aplikace Lekarna je uzavrena jako hotova; verejna aplikace bezi se sifrovanym balickem a dalsi vyvoj je priorita 2 az podle casu nebo urgentnich pozadavku.
- `handoffs/media_image_resize_utility_done_2026_05_20.md` - [PRIPOMENOUT] Obecna utilita `app/media/image_resize.py` je hotova a overena na lekarne; dalsi krok je pri pouziti na slovniky nejdriv udelat preview a zvolit cilovou velikost.
- `handoffs/vocabularyit_pict_csv_audit_2026_05_20.md` - [PRIPOMENOUT] VocabularyIT/PictNew: prompt je upraveny a schvaleny na batchi 001; batch 002, 003 a 004 jsou technicky hotove 10/10 v `PictNew/generated/20260520_it_batch002/` az `batch004/` a cekaji na vizualni kontrolu; batch 005 ani presun do `Pict/` nespoustet bez dalsiho potvrzeni.
- `handoffs/vocabularyit_batches_005_011_generated_2026_05_20.md` - [PRIPOMENOUT] VocabularyIT/PictNew: batche 005 az 011 jsou technicky hotove 10/10 v `PictNew/generated/20260520_it_batch005/` az `batch011/` a cekaji na vizualni kontrolu; batch 012 ani presun do `Pict/` nespoustet bez dalsiho potvrzeni.
- `handoffs/vocabularyit_batches_012_013_generated_2026_05_20.md` - [PRIPOMENOUT] VocabularyIT/PictNew: batche 001 az 013 jsou zkopirovane do `Pict/`; batch 013 mel poslednich 5 polozek requestu, dalsi krok je samostatne potvrzena aktualizace `Pict/mapping.json` se zalohou.
- `handoffs/vocabularyit_mapping_applied_2026_05_20.md` - [PRIPOMENOUT] VocabularyIT/PictNew: `Pict/mapping.json` byl po schvalenem preview aktualizovan, CSV jsou srovnane, audit je cisty; dalsi krok je cilene ulozit relevantni zmeny do gitu bez `git add .`.
- `handoffs/pictnew_next_image_generation_phase_2026_05_20.md` - [PRIPOMENOUT] přesný snapshot pro další fázi PictNew: později navázat na nové anglické názvy obrázků, porovnání CSV vs `Pict/mapping.json` vs `Pict/`, doplnění mappingu a nové obrázky podle kanonického workflow.
- `handoffs/lekarna_readonly_tool_done_2026_05_19.md` - [PRIPOMENOUT] Lekarna ma prvni bezpecny read-only Samantha tool `search_domaci_leky` nad `data/lekarna/domaci_leky.csv`; dalsi krok je rucni live test pres Samanthu a doladeni synonym/rankingu.
- `handoffs/samantha_agent_rag_memory_store_2026_05_19.md` - [PRIPOMENOUT] Samantha Agent ma prvni lokalni RAG-like vrstvu nad markdown pameti: kompakni startup kontext, `app/memory_store.py`, tooly `search_memory` a `memory_status`, jednoduchy in-memory index/cache; live testy prosly, dalsi krok je zlepsit ranking/vystup `search_memory`.
- `handoffs/samantha_agent_rag_search_memory_ranking_2026_05_19.md` - [PRIPOMENOUT] `search_memory` ma vylepseny ranking a vystup: lepsi tokenizace nazvu souboru, jeden snippet za soubor, utlumení starych handoffu, deleni tabulek/odrazek a zkracovani snippetů; dalsi krok je live retest pres Samanthu.
- `handoffs/session_recovery_autosave_2026_05_18.txt` - handoff ke konverzaci o navazovani po vypadku, `screen`, prikazu `samantha`, `codex resume` a autosave session logu po 10 minutach.
- `handoffs/test_kratky_handoff_2026_05_18.md` - testovaci handoff s prioritou 3 bez pripomenuti pri startu, overeni pravidla pro kratky handoff.
- `handoffs/email_mail_permissions_2026_05_17.txt` - handoff k odesílání e-mailů přes Apple Mail, nutnosti potvrdit macOS oprávnění, nastavení Automation/Full Disk Access a dlouhodobé SMTP alternativě.
- `handoffs/email_icloud_setup_conversation_2026_05_18.txt` - průběh nastavování iCloud Mail read-only testu pro Samanthu, s redigovanou adresou a bez hesel.
- `handoffs/email_icloud_readonly_test_ok_2026_05_18.md` - iCloud Mail read-only test mimo Codex sandbox prošel OK; navazujici krok byla bezpečná vrstva `app/email/`.
- `handoffs/email_icloud_app_email_layer_2026_05_18.md` - první read-only vrstva `app/email/` pro iCloud Mail hlavičky je hotová; ruční SSH test nového `scripts/email_list_recent.py` prošel.
- `handoffs/email_samantha_tool_headers_2026_05_18.md` - Samantha má read-only tool `list_recent_email_headers` pro iCloud Mail hlavičky; navazujici end-to-end test probehl.
- `handoffs/email_samantha_e2e_headers_ok_2026_05_18.md` - Samantha end-to-end test e-mailových hlaviček prošel; navazujici test cteni jednoho e-mailu podle UID probehl.
- `handoffs/email_read_uid_test_ok_2026_05_18.md` - read-only čtení jednoho e-mailu podle UID prošlo; navazujici Samantha tool byl doplnen.
- `handoffs/email_samantha_read_body_tool_ok_2026_05_18.md` - Samantha tool pro read-only čtení těla e-mailu podle UID prošel end-to-end testem; navazujici bezpecny workflow byl overen.
- `handoffs/email_safe_workflow_confirmed_2026_05_18.md` - [PRIPOMENOUT] bezpečný e-mailový workflow hlavičky -> UID -> potvrzení -> redigované shrnutí je ověřený; další krok je read-only vyhledávání e-mailů podle dotazu.
- `handoffs/email_readonly_workflow_handoff_2026_05_18.md` - [PRIPOMENOUT] aktuální handoff k iCloud Mail read-only workflow; další krok je read-only vyhledávání e-mailů podle dotazu bez automatického čtení těl a bez ukládání do memory.
- `handoffs/email_search_headers_ready_2026_05_18.md` - [PRIPOMENOUT] read-only vyhledávání v e-mailových hlavičkách je navržené a ruční test skriptu prošel; další krok je připojit/ověřit `search_email_headers` jako Samantha tool a otestovat hledání přes Samanthu.
- `handoffs/email_case_workflow_ready_2026_05_19.md` - [PRIPOMENOUT] Email Case workflow umi po potvrzenem UID vytvorit redigovany pracovni pripad; dalsi krok je end-to-end test `build_email_case_from_uid` primo pres Samanthu a potom volitelny tool pro plne URL jen na vyzadani.
- `handoffs/email_samantha_headers_redacted_waiting_uid_2026_05_19.md` - [PRIPOMENOUT] Samantha read-only vypsala e-mailové hlavičky s redigovanou adresou, po Milově potvrzení vytvořila pracovní případ a po samostatném potvrzení vypsala plné URL přes `show_email_case_links`; další krok je případné zlepšení prezentace odkazů bez ukládání URL do memory.
- `handoffs/email_url_tool_e2e_ok_2026_05_19.md` - [PRIPOMENOUT] iCloud Mail read-only URL tool `show_email_case_links` prošel end-to-end přes Samanthu po samostatném potvrzení; další krok je případné zlepšení prezentace odkazů bez ukládání plných URL do memory.
- `handoffs/email_rixo_insurance_phase1_ready_2026_05_19.md` - [PRIPOMENOUT] iCloud Mail workflow je ověřený a je navržená Phase 1 pro `RIXO Insurance Case` z více potvrzeně přečtených e-mailů; další krok je implementovat čisté modely/service/testy nad fake `EmailMessage`, bez ukládání obsahu e-mailů.
- `handoffs/email_rixo_insurance_phase1_implemented_2026_05_19.md` - [PRIPOMENOUT] RIXO Insurance Case Phase 1 je implementovaná a testy prošly; další krok je ruční end-to-end retest přes Samanthu s více konkrétně potvrzenými UID.
- `handoffs/email_action_case_phase2_proposed_2026_05_19.md` - [PRIPOMENOUT] po testu NIBE je navržená Email Action Case Phase 2: z jednoho potvrzeně přečteného e-mailu vytvořit bezpečný návrh připomínky do lokálního reminders JSON; další krok je implementovat modely/service/testy bez ukládání těla e-mailu.
- `handoffs/email_action_case_phase2_core_done_2026_05_19.md` - [PRIPOMENOUT] Email Action Case Phase 2 má hotový čistý core nad fake `EmailMessage`; další krok je tool pro návrh úkolu z potvrzeného UID a až potom samostatně potvrzované uložení do reminders JSON.
- `handoffs/email_reminders_phase3b_done_2026_05_19.md` - [PRIPOMENOUT] reminders Phase 3B je hotová: Samantha má tooly pro bezpečný výpis otevřených připomínek, detail připomínky a samostatně potvrzené označení jako hotové; další krok je ruční end-to-end test přes Samanthu.
- `handoffs/email_work_session_proposed_2026_05_19.md` - [PRIPOMENOUT] navržený `Email Work Session` režim pro jedno UID: jedním potvrzením povolit čtení těla, action case, plné URL jako výstup, bezpečnou připomínku a metadata příloh; další krok je čistý model/service/testy nad fake `EmailMessage` bez IMAPu.
- `handoffs/email_triage_work_mode_proposed_2026_05_19.md` - [PRIPOMENOUT] navržený `Email Triage and Work Mode`: jedním souhlasem triage e-mailů za posledních 7 dní, bezpečný `EmailCaseVault` v `data/email/cases/` a `WorkMode` pro jeden případ; další krok je čistý vault/model/service nad fake daty bez IMAPu.
- `handoffs/email_triage_work_mode_core_done_2026_05_19.md` - [PRIPOMENOUT] první čistý `Email Triage and Work Mode` core je hotový: triage nad fake `EmailMessage`, safe `EmailCaseVault` do explicitní složky a `WorkMode` nad safe case; další krok je samostatný Samantha tool pro realnou triage až po jasném potvrzení.
- `handoffs/email_triage_session_tool_done_2026_05_19.md` - [PRIPOMENOUT] Samantha tool `run_email_triage_session` je hotový: po jasném potvrzení read-only projde iCloud e-maily za posledních N dní a vrátí bezpečný triage souhrn bez ukládání; další krok je ruční e2e test přes Samanthu a potom samostatně potvrzované uložení vybraných case kandidátů.
- `handoffs/email_case_vault_save_tool_done_2026_05_19.md` - [PRIPOMENOUT] Samantha tool `save_selected_email_cases_from_uids` je hotový: po samostatném potvrzení se všemi UID read-only načte vybrané e-maily a uloží bezpečné case JSON do `EmailCaseVault`; další krok je ruční e2e test a potom WorkMode tool nad uloženým case.
- `handoffs/email_activity_state_done_2026_05_19.md` - [PRIPOMENOUT] lokální `data/email/activity_state.json` sleduje `last_triage_at` a `last_archive_at`; Samantha při startu připomene e-mailovou triage nebo archivaci, pokud jsou starší než 7 dní.
- `handoffs/email_archive_vault_proposed_2026_05_19.md` - [PRIPOMENOUT] navržený `EmailArchiveVault` pro kompletní lokální zálohu důležitého e-mailu po výslovném potvrzení UID; další krok je čistý archive service nad fake e-mailem, `.gitignore` pro `data/email/archive/`, až potom provider raw read-only metoda a Samantha tool.
- `handoffs/email_archive_vault_core_done_2026_05_19.md` - [PRIPOMENOUT] čistý `EmailArchiveVault` core je hotový: service ukládá metadata, body txt/html, links, attachment metadata a volitelný raw EML do explicitní složky; další krok je provider raw read-only metoda a samostatně potvrzovaný Samantha tool.
- `handoffs/email_archive_vault_tool_done_2026_05_19.md` - [PRIPOMENOUT] `EmailArchiveVault` má read-only provider metodu a Samantha tool `archive_email_by_uid`; další krok je ruční e2e test archivace jednoho konkrétního UID a potom samostatná práce s uloženým archivem.
- `handoffs/email_archive_vault_no_urls_after_archive_2026_05_19.md` - [PRIPOMENOUT] po realném testu UID 13964 je upřesněno, že `archive_email_by_uid` nesmí po archivaci nikdy vypisovat plné URL; další krok je samostatně potvrzovaný `show_archive_links` tool nad lokálním archivem.
- `handoffs/email_project_frozen_human_handoff_2026_05_19.md` - [PRIPOMENOUT] lidský zmrazovací handoff k e-mailovému projektu: co už Samantha s e-maily umí, co zatím neumí prakticky, bezpečnostní hranice a doporučený směr po rozmrazení.
- `handoffs/stories_batch_2026_05_14.md` - batch více pohádek z jednoho chatu, rozdělený do samostatných story memory souborů.
- `handoffs/chatgpt_handoff_2026_05_14.md` - kompaktní předání po dlouhém ChatGPT vlákně, včetně promptu pro Codex a promptu pro nový ChatGPT chat.
- `handoffs/mmtx_web_handoff_2026_05_14.md` - handoff k webové verzi MMTX v `docs/`, hotovým scénám OwlGarden a HouseBunny, audio strategii a mirroru.

## Technical Rules

- `technical/naming_conventions.md` - názvosloví: Samantha je běžný ChatGPT, Codex je pracovní agent v projektu, Codex CLI je terminálový nástroj.
- `technical/story_memory_rules.md` - pravidla pro ukládání pohádek do memory: ukládat plný finální text, ne jen shrnutí, a sledovat clean verzi pro předčítání.
- `technical/codex_permissions_preferences.md` - preference pro navrhovani trvalych Codex povoleni u rutinnich prikazu, vcetne TTS a git publikace.
- `technical/session_recovery_rules.md` - pravidla pro navazani po vypadku SSH/Codexu: pouzivat `screen`, prikaz `samantha`, `codex resume` a handoff soubory.
- `technical/capability_routing_rules.md` - obecne pravidlo pro vsechny projekty: lidsky pokyn -> pochopeny zamer -> registrovana schopnost/tool/workflow -> bezpecnostni rozsah -> potvrzeni podle rizika.
- `technical/lekarna_pil_short_workflow.md` - [PRIPOMENOUT] kanonicky workflow pro doplnovani `PIL_Short`: SÚKL DLP sparovani, statusy jistoty, prakticky nealarmisticky vytah, zaloha CSV a testy.
- `technical/workflow_command_registry.md` - pravidlo, ze lidske workflow pokyny se maji mapovat na predem schvalene presne prikazy v registru, ne na ad hoc shell vymysleny modelem.
- `technical/project_capability_map.md` - [PRIPOMENOUT] potvrzena taxonomie projektu v `PythonMF` a priorita 1 pro prvni nizkorizikove workflow kandidaty: `PictNew` read-only audit a `VocabularyEN` sync do `docs/`.
- `technical/vocabulary_image_generation_workflow.md` - [PRIPOMENOUT] pozlacený kanonický workflow pro slovníkové obrázky: audit/request, dry-run, potvrzené placené generování po dávkách, review, kopie do `Pict/`, mapping až po samostatném potvrzení a git checkpoint.
- `technical/macos_wifi_vpn_tailscale_recovery.md` - [PRIPOMENOUT] priorita 1: recovery protokol pro macOS Wi-Fi/DHCP/VPN/Tailscale vypadky po rozbitem routovani nebo tunnel rozhranich.
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
