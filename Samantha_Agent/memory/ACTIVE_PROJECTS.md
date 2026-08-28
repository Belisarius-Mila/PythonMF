# Project Registry

Registr projektu a oblasti. Sloupec `Rezim` urcuje viditelnost: `active` je bezna aktivni prace, `paused` je pozastavene a `archived` se zobrazuje jen v archivnim filtru Cockpitu.

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Rodinný kalendář | 1 | active | Živý redigovaný read-only audit 2026-08-01 potvrdil `config_mode=enabled`, aktivní automatiku, připravený plánovač a nula blokujících stavů. Audit nic nezapsal, nečetl tajemství a nevolal transport; `partial` a `delivery_unknown` zůstávají fail-closed. | `projects/family_calendar.md` | `handoffs/workstreams/project-family-calendar.md`; `tvbcp/workstreams/project-family-calendar.md` | Bez nové aktivace nebo testovacího odeslání. První přirozený plánovaný výsledek sledovat pouze redigovaně; proměnlivý provozní stav vždy znovu ověřit živým read-only auditem. |
| Commitove odpoledne / git cleanup | A1+ | archived | Akutni cast splnena: velka memory/RAG cleanup davka byla commitnuta a pushnuta jako `ef15589 Clean up Samantha memory handoffs and RAG search`; repo bylo po pushi ciste. Pravidlo do odvolani zustava: pri delsim `git status` nebo zmene projektu navrhnout tematicky commitovy uklid. | `infrastructure/git_checkpoint_protocol.md` | `handoffs/git_commit_cleanup_a1_2026_05_23.md` | Drzet cisty stul; dalsi commitovy uklid navrhnout az pri novych rozpracovanych zmenach, bez `git add .`. |
| Rustova pravidla Samanthy / uklid handoffu | A1+ | archived | Prvni velka handoff compression davka hotova a pushnuta: Dokumenty, Lekarna, PictNew/VocabularyIT, Tomik/FamilyVideoOrganizer, E-mail, Samantha/RAG a automaticke ukoly maji kanonicky stav a stare mezistavy jsou presunute do historickych sekci. Systemove reporty a infrastructure operating model jsou zalozene. | `technical/samantha_growth_rules.md`; `infrastructure/operating_model.md` | `handoffs/memory_cleanup_commit_afternoon_checkpoint_2026_05_23.md` | Pri dalsim rustu drzet pravidlo: novy opakovatelny status/audit nejdrive nabidnout jako systemovy report; velke cleanupy koncit malym commitem a pushem. |
| MMTX | 1 | active | Checkpoint 2026-08-25 13:17 CEST. Hotovo: MMTX má samostatné přání Jane s pozměněnými texty, anglickou výslovností jména a vlastními zvukovými stopami.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený. Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené. Rizika: Žádné další doložené provozní riziko. | `projects/mmtx_story_hotspot_app.md`; `projects/matysek_english_game_concept.md`; `technical/matysek_f5tts_voice_workflow.md` | `handoffs/workstreams/project-mmtx.md`; `tvbcp/workstreams/project-mmtx.md`; `handoffs/mmtx_scene03_journey_to_lake_publish_2026_07_01.md` | Ručně ověřit hlasy a výslovnost Jane na iPhonu nebo Macu a poté použít ovládací prvky Cockpitu pro checkpoint a nasazení. |
| Samantha external backup | 1 | active | Poslední úspěšná recovery záloha je snapshot `20260802_153855`. Stavový soubor je sdílený z kanonického projektu všemi profilovými workspaces. K 2026-08-07 je záloha starší než tři dny, proto je správně aktivní provozní upozornění. Starý incident s neviditelným USB diskem je historický a dnešní stav nedokládá. | `projects/samantha_external_backup.md` | `handoffs/external_backup_disk_usb_not_detected_2026_07_14.md` (historický); `handoffs/cockpit_robustness_smoke_backup_bridge_2026_06_09.md` | Připojit šifrovaný externí disk a spustit pravidelnou recovery zálohu; potom znovu ověřit `backup_status.py`. |
| Janička Cockpit / používání a převzetí Samanthy | 1 | active | [PRIPOMENOUT] Janička je živý netechnický rozcestník k dokumentům, e-mailům, tisku, Lékárně, rodinným projektům, připomenutím a recovery. Stará light komunikace i nouzové otevírání plného Adama byly z Cockpitu odstraněny. Komunikace se vrátí až jako samostatný funkční Adam-R2; rozcestník do té doby neslibuje chat ani náhradní komunikační cestu. | `projects/janicka_cockpit_takeover.md`; `projects/janicka_cockpit_kucharka.md` | `handoffs/janicka_full_adam_cockpit_recovery_ios_card_2026_07_09.md`; `handoffs/janicka_cockpit_takeover_project_start_2026_06_06.md`; `handoffs/janicka_adam_text_bridge_functional_checkpoint_2026_06_07.md`; `handoffs/janicka_light_samantha_bridge_checkpoint_2026_07_03.md`; `handoffs/janicka_cockpit_family_projects_modal_2026_06_26.md` | Běžné nekomunikační vstupy Janičky ověřovat podle potřeby. Komunikační funkci už nerozvíjet v tomto projektu; navázat až samostatným projektem R2-Adam. |
| R2-Adam / Janička | 2 | active | R2-Adam má vlastní trvalý chat, soukromý kontext, TXT prostor, dokumentovou lištu a čtečku. E2 živě ověřilo úplný tok e-mail -> vault -> create-only TXT. E3 potvrdilo ruční revizi a backendovou dostupnost PDF; nasazená oprava odstraňuje diagnostickou obálku z lidského TXT bez změny staršího souboru. Smoke prošel 5/5. | `projects/janicka_r2_adam.md` | `handoffs/workstreams/project-r2-adam-janicka.md`; `tvbcp/workstreams/project-r2-adam-janicka.md` | Obnovit Archiv e-mailu a R2 čtečku a ručně ověřit otevření PDF i čistý začátek TXT. |
| Pozustalost / rodinny nouzovy balik | 1 | active | Zalozeno 2026-05-30 jako git-safe navrh bez citlivych dat. Technicke pravidlo 2026-05-31: nestavet druhy dokumentovy system; pouzit Document Management jako hlavni trezor, pridat pozustalostni metadata/tagy a finalni balik drzet jako samostatny sifrovany export. Soukrome prazdne sablony jsou zalozene mimo git v `data/private/pozustalost/`. | `projects/pozustalost_rodinny_plan_2026_05_30.txt` | `handoffs/pozustalost_start_2026_05_30.md` | Projit soukrome sablony a vyplnit nejdrive jen mapu oblasti bez cisel smluv, uctu, hesel a recovery klicu; konkretni citliva data ukladat jen do sifrovaneho uloziste mimo git. |
| Neuberk interier design / Kacenka | 2 | active | Designova prace je docasne prerusena. Soukromy projekt pro pudni hostovskou mistnost ma v `data/private/neuberk_interier_design/` aktualni stenove prekresy, pudorys a vizualni koncepty. Dne 2026-06-07 se ladil jizni pohled v6: opraveny pricny snizeny strop, sikmy tram smerujici k vychodni stene, komin u dveri a rozkladaci gauc za kominem. Aktualni soukromy kandidat je zapsany v indexu konceptu; git-safe stav je ulozeny bez soukromych rozmerovych detailu. | `projects/neuberk_interier_design.md` | `handoffs/neuberk_kacenka_south_wall_v6_geometry_checkpoint_2026_06_07.md` | Po navratu otevrit posledni soukromy kandidat v6 a porovnat ho s realnymi fotkami. Pokud Mila potvrdi geometrii, prejit na jednoduchy pudorysovy check: vejde se gauc za komin, zustane pruchod a nekoliduji dvere, topeni ani snizeny strop. |
| Samantha Agent/RAG | 1 | active | P0-P6 zavedly autoritu zdrojů a obsahové narovnání. P7 je od 2026-08-01 implementované a provozně obsažené v nasazeném Cockpitu: před tvrzením typu aktivní/běží/připraveno se použije dostupný redigovaný live audit, jinak odpověď přizná stáří a nejistotu paměti. | `samantha_core.md`; `tvbcp/workstreams/project-samantha-agent-rag.md` | `handoffs/workstreams/project-samantha-agent-rag.md` | Bez okamžité implementace. Při příštím dotazu na proměnlivý provozní stav ověřit, že odpověď skutečně použila live audit nebo uvedla stáří snapshotu. |
| Znalostni databaze / Knihovna clanku / Knowledge inbox | 2 | active | Checkpoint 2026-08-28 09:21 CEST. Hotovo: Knihy mají nové kategorie učebnice a cizojazyčná literatura a vlastní kategorii lze přidat i při editaci; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený. Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené. Rizika: Žádné další doložené provozní riziko. | `projects/vedecke_clanky.md`; `technical/large_context_intake.md`; `tvbcp/knihovna_cockpit.txt` | `handoffs/knowledge_library_article_editing_2026_07_16.md` | Nasadit změnu a ověřit přidání i výběr kategorie na iPhonu |
| Reminders / platebni SMS | 1 | active | Hotovy workflow: `inspect_payment_page_for_reminder` read-only overi splatnost z HTTPS platebni stranky/API bez opisovani plne URL/tokenu; `save_payment_sms_reminder` ulozi overovaci nebo ostrou platebni pripominku; `save_payment_case_document` ulozi lokalni fakturu/prilohu do `data/private/payment_cases/`. | `technical/general_reminders_workflow.md` | `handoffs/payment_sms_reminder_tool_done_2026_05_21.md` | Pri dalsi realne SMS overit live pres Samanthu. Pozdeji zvazit extrakci textu z PDF faktur nebo podporu JS/login stranek, ale jen read-only a s potvrzovaci branou. |
| Sprava dokumentu / private vault | 1 | active | Document vault a ScanDocu zůstávají hlavním soukromým dokumentovým systémem. Servisní obrazovka byla 2026-08-07 zjednodušená: nahoře ukazuje aktuální čekající inbox a stav trezoru, historické agregace jsou až v rozbalovacích technických podrobnostech. Změna je nasazená v Cockpitu; žádné dokumenty ani auditní stopy se nemazaly. Staré historické počty nejsou pracovní úkol. | `projects/document_management_private_vault.md`; `technical/private_document_vault_workflow.md` | `handoffs/document_email_attachments_scandocu_metadata_checkpoint_2026_06_16.md` (poslední věcný intake checkpoint); starší handoffy jsou historie | Až bude čas na terminálový test, projít jeden skutečný e-mail s PDF a JPEG: náhled, uložení do vaultu a metadata ve ScanDocu Review. |
| Cockpit Recovery centrum | 1 | active | Recovery, health, diagnostika, bezpečný restart, Tailscale přístup a pamatováček jsou funkční. Dne 2026-08-15 bylo po přesném potvrzení odstraněno 144 starých časovaných autosave souborů; zůstalo 12 nejnovějších časů, všechny `latest` kopie, jeden watcher a přibližně 1,30 GiB autosave dat. Restart a nové read-only měření jsou doložené. Opravený lokální report nyní odděluje logickou velikost, alokované bloky a skutečnou změnu volného místa; plná brána 1414/1414 prošla, nasazení zatím neproběhlo. | `infrastructure/codex_reconnect_recovery.md`; `infrastructure/klicove_prikazy_pamatovacek.md`; `technical/session_recovery_rules.md`; `LESSONS_LEARNED.md` | `handoffs/autosave_cleanup_ssd_space_recovery_2026_08_15.md`; `handoffs/workstreams/project-cockpit.md`; `handoffs/cockpit_startup_health_voicebridge_verified_2026_07_09.md` (historický základ) | Samostatně potvrdit nasazení a živě ověřit nový dry-run bez mazání. [PRIPOMENOUT] |
| Cockpit hlavni architektura / modernizace | 1 | active | Checkpoint 2026-08-19 22:05 CEST. Dokumenty mají jedinou frontu bez tří duplicitních oddílů; každý dokument nabízí přímo potřebné akce pro čtení a metadata. Plná Cockpit Quality Gate prošla 1446/1446. Nový checkpoint zatím není nasazený a čeká také v denním GitHub balíčku. | `../AuditCockpit56_2.txt`; `../AuditCockpit56.txt` (historická roadmapa); `reports/cockpit_dieta_d0_2026_07_29.md`; `reports/cockpit_quality_gate_2026_07_10.md`; `tvbcp/workstreams/project-cockpit.md` | `handoffs/workstreams/project-cockpit.md`; `handoffs/cockpit_architecture_current_2026_07_10.md` (historická roadmapa) | Samostatně potvrdit nasazení a potom na iPhonu ověřit jednu položku se čtením a jednu s doplněním metadat. |
| App-server rozhrani / novy Adam | 1 | active | Checkpoint 2026-08-16 16:47 CEST. Hotovo: Checkpoint a informace o nasazení jsou na mobilu schované pod horními Podrobnostmi, takže chat má více prostoru; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený. Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček. Rizika: Žádné další doložené provozní riziko. | `tvbcp/architektura_komunikace_samantha.txt`; `technical/project_tvbcp_rules.md`; `technical/global_safety_brake.md`; `technical/capability_routing_rules.md` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` | Samostatně potvrdit nasazení a vizuálně ověřit výšku chatu na iPhonu |
| Codex full access / Guard proti mazani | 1 | active | [PRIPOMENOUT] Míla rozhodl používat plnější lokální oprávnění kvůli provozní diagnostice. Lokální konfigurace a aktuální řízené prostředí se mohou lišit; vždy platí právě vložený `DEVELOPMENT_CONTROL` a skutečný sandbox relace. Základ Guardu proti mazání už existuje jako `technical/global_safety_brake.md`: pro `rm -rf`, hromadné mazání/přepisy, `git reset --hard`, force push, mazání větví/tagů, zásahy do private dat a podobné vysoké riziko vyžaduje přesnou potvrzovací větu. | `technical/codex_permissions_preferences.md`; `technical/global_safety_brake.md`; `infrastructure/git_checkpoint_protocol.md` | `handoffs/codex_full_access_voicebridge_guard_next_2026_06_29.md`; `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md`; `handoffs/adam_voice_global_safety_brake_2026_06_09.md` | Nevracet jako další krok „založit Guard“; základní pravidlo už je založené. Volitelný budoucí krok je jen programová enforcement vrstva/wrapper pro destruktivní shell příkazy, pokud se ukáže potřeba. |
| Mapovani projektu a schopnosti | 1 | active | Taxonomie a capability registry jsou zavedené. Systémový audit projektů/toolů/vrstev od 2026-08-07 před reportem porovnává Git stáří `ACTIVE_PROJECTS.md` s kanonickými handoffy/TVBCP. Novější kanonickou paměť výslovně označí jako drift a doporučí dorovnání; audit sám paměť nepřepisuje a nezakládá chybějící TVBCP. | `technical/project_capability_map.md`; `technical/system_project_audit_generator_design.md`; `technical/system_reports.md`; `technical/capability_routing_rules.md` | `handoffs/system_project_audit_generator_done_2026_06_23.md`; `handoffs/workstreams/project-samantha-agent-rag.md` | U každého nového Samantha toolu doplnit capability registry záznam a test. Při významném checkpointu v jednom kroku aktualizovat kanonický handoff, TVBCP a řádek `ACTIVE_PROJECTS.md`; kontrolní audit má po commitu hlásit nulový drift. |
| Samantha Infrastructure | 1 | active | Checkpoint 2026-08-26 09:35 CEST. Hotovo: Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček. Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem. | `infrastructure/operating_model.md`; `infrastructure/codex_reconnect_recovery.md`; `infrastructure/macos_network_recovery.md`; `technical/global_safety_brake.md`; `technical/session_recovery_rules.md` | `handoffs/autosave_status_and_voice_triage_fix_2026_06_12.md`; `handoffs/system_quick_check_git_safety_2026_06_09.md`; `handoffs/adam_voice_global_safety_brake_2026_06_09.md`; `handoffs/samantha_screen_scrollback_fix_2026_06_18.md` | Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav |
| iPhone Shortcuts / Mobile Input Layer | 2 | paused | Funkční capability: sdílená zkratka důležitých připomenutí i přímé Quick Notes doručují přes Tailscale do soukromého Cockpitu a iCloud zůstává fallbackem. Mílův živý test obou cest prošel; stejný Cockpit může používat Jana ve společném tailnetu. Starší QN předklasifikace zůstává zachovaná. | `technical/iphone_shortcuts_playground.md`; `tvbcp/workstreams/project-cockpit.md` | `handoffs/iphone_shortcuts_freeze_infrastructure_layer_2026_05_25.md`; `handoffs/workstreams/project-cockpit.md` | Bez dalšího vývoje. Při příští skutečné QN ověřit doručení a řešit jen konkrétní selhání nebo požadovanou potvrzovanou akci. |
| Nakupni pruzkum a archiv nakupu | 2 | active | Koncept ulozen jako lehky workflow/tool: Mila zada konkretni produkt nebo varianty, Adam/Samantha najde kamenne prodejce do 100 km od Mlade Boleslavi a overene e-shopy, vrati prime odkazy na produkt a po Milove objednani ulozi potvrzeni/fakturu do soukromeho archivu mimo git. | `technical/shopping_research_and_purchase_archive.md` | zatim neni | Pri prvnim realnem navazani zalozit soukromy `data/private/purchases/`, sablony `order_summary.md`/`warranty.md` a az po realnem pouziti zvazit intake z Downloads a systemovy report nakupni evidence. |
| Automaticke opakujici se ukoly / ColorsAndNumbers | 1 | active | GitHub Pages používají workflow artifact bez zápisu do `main`. Plánovaný běh 30. 7. 2026 uspěl a veřejné dnešní MP3 vrací HTTP 200. Soukromé fotografie nadále nesmí do repozitáře ani Pages. | `projects/automated_recurring_tasks.md` | `handoffs/colors_numbers_owl_pages_artifact_checkpoint_2026_07_27.md`; `handoffs/colors_numbers_private_photo_gallery_proposal_2026_07_13.md` | Bez okamžité změny. Sledovat příští přirozený běh a zasahovat jen při chybě audia, Pages deploymentu nebo neočekávané změně `main`. |
| macOS sit / Tailscale recovery | 1 | archived | Pending do instalace noveho pripojeni: technik T-Mobile ma v pondeli 2026-06-01 instalovat nove pripojeni pres pevnou linku/DSL. Predchozi domaci watchdog mel jen 81,88 % OK a casto selhal i ping na gateway `192.168.1.1`; pracovni Wi-Fi retest mel 319/320 OK. | `technical/macos_wifi_vpn_tailscale_recovery.md` | `handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md` | Do 2026-06-01 resit jen pokud se stav zhorsuje. Po instalaci nove linky udelat 30min watchdog retest a porovnat stabilitu; Mac stack resit az pokud budou padat i jine site nebo nova linka. |
| iCloud Mail read-only / Email Cases | 1 | active | Read-only e-mailové workflow, Work Queue, vyladěný Archiv e-mailu i UX2 pravdivé navigace jsou nasazené. Horní E-maily vedou na rozcestník Zpracování / Archiv a obě pracovní části zmizely z katalogu Webových aplikací. URL, payloady a bezpečnostní hranice se nezměnily; živě jsou dostupné obě původní stránky. | `projects/email_readonly_oauth.md` | `handoffs/cockpit_email_archive_browser_2026_07_09.md` | Ručně vizuálně ověřit obě volby v novém e-mailovém rozcestníku. Zápisy, mazání a odesílání zůstávají mimo rozsah. |
| Lekarna | 1 | active | Foto import ve Sprave Lekarny je po realnem testu 2026-07-09 end-to-end funkcni: fotka -> OpenAI OCR -> SUKL DLP -> online PIL dokument -> `PIL_Short` -> prijem na sklad -> web export -> sifrovany produkcni balicek -> automaticky commit/push. Testovaci SERTIVAN / sertralin byl prijat, overen v produkci a nasledne potvrzene vyrazen; v lokalnim CSV zustava jako auditni radek `vyradeno`, ale webovy export a produkce ho uz nezobrazuji. Export byl opraven tak, aby vyradene radky nesly do produkcni webove Lekarny. Webova aplikace Lekarna zustava archivovany vystup/varianta hlavni Lekarny, ne samostatny aktivni projekt. | `projects/lekarna_domaci_leky.md` | `handoffs/lekarna_photo_import_pil_publish_retire_verified_2026_07_09.md`; `handoffs/lekarna_import_manifest_editor_checkpoint_2026_07_06.md`; `handoffs/lekarna_photo_staging_tool_2026_06_12.md`; `handoffs/lekarna_status_po_doplneni_vitaminu_2026_05_21.md`; `handoffs/lekarna_web_app_hotovo_2026_05_20.md` | Neni nutny okamzity zasah. Pri dalsim realnem leku zopakovat cely tok a sledovat hlavne produkcni publikaci; volitelne doplnit UI overeni, ze GitHub Pages CDN uz servíruje novy sifrovany balik. |
| Tomik video iMovie / FamilyVideoOrganizer | 1 | active | Cockpit už otevírá lokální Family Video Organizer nad úplným ověřeným soukromým balíčkem, ne nad třízáznamovou ukázkou. Při neúplném balíčku bezpečně spadne na veřejnou šablonu. Generátor započítává i již zachované cílové video. Soukromá videa, data a náhledy zůstávají mimo Git. | `projects/tomik_video_imovie.md`; `LESSONS_LEARNED.md` | `handoffs/family_video_organizer_package_ready_2026_05_29.md` | Čekat na dceřin export JSON; po přijetí nejdřív provést read-only kontrolu a importovat až po samostatném potvrzení. |
| Family Memory Films / USA 2019 | 1 | active | Cisty seznam 15 filmu pouzitelnych dnu je odsouhlaseny; `2019-08-05` neni samostatny den filmu, ale smesny zdroj podle item-level review. Master prehled ve stylu `Tomik 2` je ulozen mimo git v `03_overview/usa_2019_tomik2_overview.md`. Predstrihovy formular `03_overview/film_selection_form.html` ma 2688 polozek, denni filtr, rating `A/B/C/skip`, volby pro kratky/dlouhy film, autosave, CSV export a prehravani videi. Adamuv prvni navrh ratingu je aplikovany: `A=406`, `B=913`, `C=1369`. | `projects/family_memory_films.md` | `handoffs/family_memory_usa_2019_tomik2_overview_checkpoint_2026_06_05.md` | Otevrit `http://127.0.0.1:8793/03_overview/film_selection_form.html`, rucne zkontrolovat Adamuv rating, povysit rodinne/emocni momenty podle potreby a stahnout `film_selection_review.csv`; pri navazani brat nejnovejsi `~/Downloads/film_selection_review*.csv` jako zdroj pravdy. Originaly nemazat, neprejmenovavat ani nepresouvat bez potvrzeni. |
| Webova aplikace Lekarna | 2 | archived | Hotovo / udrzba. Verejna GitHub Pages aplikace v `docs/lekarna/` funguje se sifrovanym datovym balikem, skutecnymi fotkami a `PIL_Short`; ChatGPT fallback ma kopirovaci panel a rucni odkaz pro prohlizece, ktere neotevrou novou zalozku. | `projects/lekarna_web_app.md` | `handoffs/lekarna_web_app_hotovo_2026_05_20.md` | Zadny aktivni vyvoj. Pri novem pozadavku nejdrive precist handoff; pri zmene dat znovu spustit export + sifrovani a commitnout jen encrypted bundle. |
| VocabularyFR Web Trainer | 2 | archived | Archiv: webovy MVP prototyp je hotovy a checkpointnuty v commitu `da93eba`; navazujici Janina macOS app / Pict opravy jsou uzavrene: app umi hledat externi `PythonMF/Pict`, Jana `mapping.json` ma 841 zaznamu, audit hlasi 346/347 konkretnich obrazku a jediny zamerne ponechany fallback `chez -> preposition`; oprava zameny `school.PNG`/hospital je pushnuta v `253c6cd`. | `projects/vocabularyfr_web_trainer.md` | `handoffs/vocabularyfr_web_trainer_checkpoint_2026_06_04.md`; `handoffs/vocabularyfr_jana_images_archive_2026_06_07.md` | Archiv: neukazovat mezi aktivnimi projekty. Pri navratu nejdrive spustit audit `.venv/bin/python scripts/audit_jana_vocabularyfr_pict_mapping.py` a overit iCloud sync `PythonMF/Pict/mapping.json`. |
| Media image resize utility | 1 | active | Obecna utilita pro zmensovani obrazku podle cilove velikosti v kB je hotova, otestovana a prvne pouzita na lekarne. Vychozi cil je 250 kB, preset `lekarna` je 100 kB. | `projects/media_image_resize_utility.md` | `handoffs/media_image_resize_utility_done_2026_05_20.md` | Pri dalsim projektu se nejdriv zeptat na cilovou velikost, pokud neni dana; pro slovniky pravdepodobne zacit preview s 250 kB. |
| MultiLO | 2 | active | Stabilizační cleanup obrazovek zůstává platný. Pro Janin Mac je připravený nový samostatný balíček s Pythonem 3.12 a Tk 8.6.13, který zachovává data v Application Support; lokální MultiLO je zároveň přidané mezi aplikace v Cockpitu. | `projects/multilo_stabilization_cleanup.md` | zatim neni | Na Janině Macu nahradit starou aplikaci novým balíčkem bez mazání Application Support a krátce ověřit start; další zásahy až podle reálného chování. |
| ToBeToHave | 2 | active | Checkpoint 2026-08-11 11:00 CEST. Hotovo: KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený. Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček. Rizika: Žádné další doložené provozní riziko. | `projects/to_be_to_have.md`; `WORKSTREAMS.md` | zatím nematerializováno; stabilní lazy cesta `handoffs/workstreams/project-to-be-to-have.md` | V Cockpitu otevřít KPTL Introduction, projít krátký vizuální a zvukový test kvízu a ověřit závěrečné skóre |
| Linux / instalace a konfigurace | 2 | active | Checkpoint 2026-08-28 14:12 CEST. Hotovo: Human–Adam nyní pro Linux bezpečně přehrává dočasný český zvuk vytvořený lokálně na Macu.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený. Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené. Rizika: Žádné další doložené provozní riziko. | `projects/linux_workstation.md`; `WORKSTREAMS.md` | zatím nematerializováno; stabilní lazy cesty `handoffs/workstreams/project-linux-workstation.md`; `tvbcp/workstreams/project-linux-workstation.md` | Po checkpointu a nasazení živě ověřit čtení odpovědi na Linuxu a regresi na iPhonu. |
| PictNew / Vocabulary image workflow | 2 | active | Od 2026-07-31 platí jeden český abecední obsah `Pict/mapping.json` pro `FR - Míla`, `FR - Jana` a `IT - Míla`. Každý zápis slovíček automaticky spouští společný audit přesně tří kanonických CSV, obou distribučních mappingů a obou knihoven `Pict`; u Jany navíc vždy kontrolu úplnosti `Sentence` a `SentenceT`, zatímco Míla si své věty píše sám. První živý průchod skončil 227/227, 389/389 a 463/463; aktuální sjednocený mapping má 969 položek a Janiny věty jsou 389/389. | `projects/pictnew_vocabulary_image_pipeline.md`; `technical/vocabulary_image_generation_workflow.md` | `handoffs/vocabularyit_mapping_applied_2026_05_20.md` | Při příští změně slovíček nejdříve použít povinný aktualizační kontrakt v projektové paměti; placené generování, přesun obrázků a mapping apply držet za stávajícími preview a potvrzovacími hranicemi. |
| Vocabulary FR | 2 | active | Dvě zdrojové bezpečnostní iterace jsou hotové: hlavní CSV má atomický zápis s konfliktním hashem a aplikace nyní používá vždy jediný datový adresář. Zdrojový běh používá projektový adresář, explicitní `--data-dir` přesně zadané umístění a budoucí `.app` Application Support; tiché kopírování při startu a ukončení bylo odstraněné. Starší přenosná data se bez ověření nemigrují. Nová verze zatím není zabalená ani nasazená k Janě. | `projects/vocabularyfr_web_trainer.md`; `projects/pictnew_vocabulary_image_pipeline.md`; `tvbcp/workstreams/project-vocabulary-fr.md` | `handoffs/workstreams/project-vocabulary-fr.md` | Připravit izolovaný testovací build a na pracovní kopii tří CSV ověřit start, zápis a restart; živou Janinu aplikaci ani data zatím neměnit. |
| Vocabulary IT | 2 | paused | AppIT má funkční vzájemně výlučné filtry posledních 20/50 slovíček s návratem k celému výběru a kombinací s HT. Lokální macOS spuštění z Cockpitu používá opravený Tk runtime. | `projects/pictnew_vocabulary_image_pipeline.md`; `tvbcp/workstreams/project-vocabulary-it.md` | `handoffs/workstreams/project-vocabulary-it.md` | Bez další změny. Při příštím zásahu zachovat stejný kontrakt filtrů a provést společný audit CSV, mappingů a obrázků. |
| Brainstorm / nápady | 2 | active | Obecný proud pro návrhy a rozvahy, které zatím nepatří konkrétnímu projektu. Kanonický handoff a TVBCP se vytvoří až při prvním potvrzeném checkpointu, ne samotným založením řádku. | `WORKSTREAMS.md` | zatím nematerializováno | Při prvním vývojovém checkpointu vytvořit kanonickou dvojici a současně automaticky nahradit tento souhrnný stav. |
| Miscellaneous / nezařazený vývoj | 2 | active | Nouzový obecný proud pro jednoznačně ohraničený vývoj, který zatím nemá vhodnější projekt. Kanonický handoff a TVBCP se vytvoří až při prvním potvrzeném checkpointu. | `WORKSTREAMS.md` | zatím nematerializováno | Upřednostnit konkrétní pracovní proud; pokud není, první potvrzený checkpoint vytvoří kanonickou dvojici a aktualizuje tento řádek. |
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
