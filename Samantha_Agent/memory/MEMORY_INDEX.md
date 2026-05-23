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
- `projects/email_readonly_oauth.md` - plán bezpečné read-only OAuth integrace e-mailu pro Samanthu, bez ukládání tokenů nebo obsahu e-mailů do gitu či paměti.
- `projects/document_management_private_vault.md` - priorita 1 projekt soukrome spravy dokumentu mimo git; MVP tooly jsou implementovane pro PDF import, due date kandidaty, private index, vyhledavani a potvrzene remindery.
- `projects/samantha_external_backup.md` - návrh offline zálohování `PythonMF`/Samanthy na externí disk: safe/recovery profily, šifrovaný kontejner, dry-run skript a 3denní připomínka.
- `projects/automated_recurring_tasks.md` - [PRIPOMENOUT] automatické opakující se úkoly: `scripts/daily_3am.py`, GitHub Actions workflow a ColorsAndNumbers soví TTS tasky; `owl_230526.mp3` byl vygenerován v commitu `c8647de`, další kontrola je nedělní `owl_240526.mp3`.
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
- `handoffs/memory_cleanup_commit_afternoon_checkpoint_2026_05_23.md` - historicky checkpoint commitoveho odpoledne: Dokumenty, Lekarna, PictNew/VocabularyIT, Tomik/FamilyVideoOrganizer, E-mail, Samantha/RAG a automaticke ukoly byly zkomprimovane a commitnute v `ef15589`.
- `handoffs/automated_recurring_tasks_cloud_2026_05_20.md` - historicky mezistav automatickych ukolu: obecna denni rutina ve 3:00, macOS `launchd`, GitHub Actions skeleton a bezpecnostni pravidla.
- `handoffs/colors_numbers_owl_tts_startup_prompt_2026_05_22.md` - historicky mezistav automatickych ukolu: jednorazovy ColorsAndNumbers soví TTS task pro 2026-05-23 a denni startovni dotaz.
- `handoffs/lekarna_web_app_hotovo_2026_05_20.md` - Webova aplikace Lekarna je uzavrena jako hotova; verejna aplikace bezi se sifrovanym balickem a dalsi vyvoj je priorita 2 az podle casu nebo urgentnich pozadavku.
- `handoffs/lekarna_status_po_doplneni_vitaminu_2026_05_21.md` - Lekarna: aktualni stav po kokpitu, doze vitaminu, obrazku doporuceni, fotkach Kozliku/Vigantolvitu a oprave fallbacku; Silymarin stale nema vlastni fotku.
- `handoffs/family_video_organizer_ui_prototype_2026_05_22.md` - FamilyVideoOrganizer: prvni lokalni webovy UI prototyp je v `docs/family-video-organizer/`, umi tabulku, filtry, autosave, export JSON a video modal; dalsi krok je realny soukromy datovy balicek mimo git.
- `handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md` - aktualni network/reconnect stav: domaci watchdog ukazal 29 vypadku za 30 minut a casto selhal i ping na gateway `192.168.1.1`; pracovni Wi-Fi retest mel 319/320 OK, takze dalsi krok je domaci router/Wi-Fi/ruseni/linka a retest po zasahu.
- `handoffs/network_https_reconnect_diagnostic_2026_05_21.md` - historicky network mezistav: prvni HTTPS failure diagnostika a vznik `scripts/network_watchdog.py`; prekryto novejsim handoffem `network_domaci_wifi_router_vs_mac_2026_05_21.md` a kanonickym stavem v `infrastructure/macos_network_recovery.md`.
- `handoffs/payment_sms_reminder_tool_done_2026_05_21.md` - Platebni SMS workflow je hotovy: `inspect_payment_page_for_reminder` read-only overi splatnost z HTTPS stranky/API bez plne URL/tokenu, `save_payment_sms_reminder` ulozi overovaci nebo platebni pripominku a `save_payment_case_document` ulozi lokalni fakturu/prilohu do `data/private/payment_cases/`.
- `handoffs/document_vault_next_physical_print_and_downloads_intake_2026_05_22.md` - [PRIPOMENOUT] pri jakemkoli dalsim vstupu do projektu dokumenty nejdriv napsat presnou vetu o nutnosti fyzicky overit tisk alespon jednoho dokumentu a vyzvat Milu k odpovedi `Ok`; dalsi plan je potvrzovany intake dokumentu ze slozky Stazene/Downloads do inboxu.
- `handoffs/media_image_resize_utility_done_2026_05_20.md` - Obecna utilita `app/media/image_resize.py` je hotova a overena na lekarne; dalsi krok je pri pouziti na slovniky nejdriv udelat preview a zvolit cilovou velikost.
- `handoffs/vocabularyit_mapping_applied_2026_05_20.md` - VocabularyIT/PictNew finalni stav aktualni vlny: `Pict/mapping.json` byl po schvalenem preview aktualizovan, audit je cisty a git checkpoint existuje jako `851b347 Apply VocabularyIT picture mapping updates`.
- `handoffs/samantha_agent_rag_search_memory_ranking_2026_05_19.md` - historicky RAG mezistav: `search_memory` ma vylepseny ranking a vystup; aktualni kanonicky stav je v `samantha_core.md`.
- `handoffs/session_recovery_autosave_2026_05_18.txt` - handoff ke konverzaci o navazovani po vypadku, `screen`, prikazu `samantha`, `codex resume` a autosave session logu po 10 minutach.
- `handoffs/test_kratky_handoff_2026_05_18.md` - testovaci handoff s prioritou 3 bez pripomenuti pri startu, overeni pravidla pro kratky handoff.
- `handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md` - Seznam e-mail: prvnich 500 vysledku pro pojisteni/smlouvy ma worklist, 34 UID slozek a 129 lokalne stazenych priloh v `data/private/email_seznam/`; navazovat jen podle potvrzovaneho read-only/document workflow.
- `handoffs/email_seznam_readonly_provider_2026_05_22.md` - aktualni e-mailovy stav: iCloud read-only vrstvy existuji, Seznam Mail read-only provider a `Unified Inbox` jsou implementovane, lokalni Seznam `.env` je vyplneny a smoke test hlavicek 2026-05-23 prosel bez vypisu predmetu/adres.
- `handoffs/iphone_shortcuts_najit_auto_done_2026_05_23.md` - hotovy checkpoint iPhone zkratek: Shortcuts Playground plugin pro Codex je nainstalovany, `Najit auto v3.shortcut` funguje u Mily i Jany a kanonicke pouceni je v `technical/iphone_shortcuts_playground.md`.
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
- `technical/project_capability_map.md` - [PRIPOMENOUT] potvrzena taxonomie projektu v `PythonMF` a priorita 1 pro prvni nizkorizikove workflow kandidaty: `PictNew` read-only audit a `VocabularyEN` sync do `docs/`.
- `technical/vocabulary_image_generation_workflow.md` - [PRIPOMENOUT] pozlacený kanonický workflow pro slovníkové obrázky: audit/request, dry-run, potvrzené placené generování po dávkách, review, kopie do `Pict/`, mapping až po samostatném potvrzení a git checkpoint.
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
