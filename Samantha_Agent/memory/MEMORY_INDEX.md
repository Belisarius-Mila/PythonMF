# Memory Index

Tento soubor je rozcestnik dlouhodobe pameti pro Samantha Agent.

- `ACTIVE_PROJECTS.md` - registr projektu a oblasti vcetne rezimu `active` / `paused` / `archived`, priorit, stavu, handoffu a dalsich kroku.
- `WORKSTREAMS.md` - kanonicky registr 30 pracovnich proudu: 24 projektu, 4 tooly a 2 `Misc`. Faze 4.2 pridala lazy soukroma vlakna, faze 4.3 jejich handoff/TVBCP vazby, faze 4.5e jednotny backendovy registr a faze 4.5f jednu perzistentni autoritu `active_workstream_id` ve schematu 2. Human–Adam a Knihovna jsou docasne kompatibilni adaptery nad svymi puvodnimi session a workspaces; ostatnich 28 proudu pouziva lazy private-thread backend. Faze 4.5g-d2 doplnila chybejici samostatny proud Rodinny kalendar s jednorazovou direct-main autorizaci.
- `projects/family_calendar.md` - Rodinný kalendář jako samostatný projekt mimo Knihovnu; aktivační apply brána je implementovaná, ale současný soukromý režim je neověřený. Další krok je pouze redigovaný read-only audit režimu, readiness a plánovače.

## Core

- `LESSONS_LEARNED.md` - stručný registr ověřených řešení opakovaných nebo
  zobecnitelných problémů. Při podobném problému se prohledává před návrhem
  nového řešení; obsahuje soví lokální preview a obecnou kontrolu konzistence
  slovníkových aplikací, mappingů a obrázků na cílovém zařízení.
- `samantha_core.md` - zakladni kontext: kdo je Mila, co je Samantha Agent, aktualni stav prostredi, souhrn vrstvy pameti/RAG a dlouhodoby cil.
- `handoffs/workstreams/project-samantha-agent-rag.md` - kanonicky aktualni handoff proudu Samantha Agent / RAG; P0-P6 audit, autorita zdroju, nefiltrovane prvni hledani, jednoznacne aliasy a obsahove narovnani. P5 je nasazena a Smer 2 je funkcne uzavreny.
- `tvbcp/workstreams/project-samantha-agent-rag.md` - kanonicky rozhodovaci dokument pravdive pameti a RAG; precedence zdroju, fail-honest fallback a odklad embeddings.
- `contacts.md` - prakticke kontakty, ktere Mila vyslovne povolil ulozit do pameti.

## Reports

- `../AuditCockpit56.txt` - hlavni roadmapa architektury Samanthy a Cockpitu.
  Cockpit Dieta D0-D3 i pravdiva pamet P0-P6 jsou uzavrene; prvni otevreny
  vecny smer je jeden uplny tok e-mail -> private vault -> R2 TXT.
- `reports/cockpit_quality_gate_2026_07_10.md` - git-safe popis kanonicke lokalni a GitHub Actions pojistky; Faze 2.4, e-mailova navigace a docasny TVBCP VoiceBridge protokol maji 611 testu. Realny redigovany outbox pilot overil 22 auditu/delivered, budoucí purge identita prezije zavreni Work Queue a obe e-mailova okna maji explicitni navrat do Cockpitu.
- `reports/cockpit_persistence_write_map_2026_07_10.md` - git-safe mapa runtime persistence; Faze 2.4 ma repository/idempotency, e-mailovy decision adapter, lease/retry/ack a realny redigovany auditni pilot. Stare nekompletni purge zaznamy se neobnovuji; budoucí trash davky persistuji bezpecnou technickou identitu.
- `reports/cockpit_dead_legacy_code_inventory_2026_07_10.md` - [PRIPOMENOUT] read-only inventura mrtveho a legacy kodu Cockpitu bez cteni private obsahu: POST registry a JavaScript/DOM vazby jsou konzistentni; Cleanup R1 odstranil jen 39 radku jednoznacnych helperu/importu a prosel 458 testy i obema smoke checky. Stary e-mailovy parser, Janicka vetev a pet API cest zustavaji do samostatneho rozhodnuti.
- `reports/systemovy_audit_projekty_tooly_vrstvy_2026_07_09.txt` - systemovy audit k 2026-07-09: projekty, tooly, vrstvy, provozni poznamka, backup warning, capability audit a doporuceni pro vyber dalsi prace; report je git-safe a necetl private vault/fulltexty.
- `reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_30_161548.txt` - [PRIPOMENOUT] aktualni systemovy audit k 2026-06-30 16:15: projekty, tooly, vrstvy, priority, provozni stav, capability gaps a navrh nejmensiho dalsiho kroku; audit vznikl z cisteho gitu a bez hlavních health varovani.
- `reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_30_151531.txt` - historicky systemovy audit k 2026-06-30 15:15: projekty, tooly, vrstvy, priority, provozni stav, capability gaps a tehdejsi navrh nejmensiho dalsiho kroku.
- `reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_23.txt` - historicky systemovy audit: projekty, tooly, vrstvy, tehdejsi priority, provozni stav, capability gaps a navrh tehdejsiho nejmensiho dalsiho kroku.
- `reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_11.txt` - historicky strukturovany audit podle QN #40 a QN #13: projekty, tooly a vrstvy serazene podle priorit 1-3, odhad rozpracovanosti v %, dalsi kroky a navrh tehdejsiho itinerare.
- `reports/cockpit_ui_content_audit_2026_06_11.md` - kratky read-only audit obsahu oken Cockpitu: co je denni, obcasne, servisni a archivni; duplicity, technicke nazvy a navrh prvniho UI cleanupu.
- `reports/cockpit_main_screen_daily_audit_2026_06_11.md` - faze 2 Cockpit auditu: rozdeleni hlavni obrazovky na `denne`, `obcas`, `servis`, `archiv` a navrh, co ma byt rano videt bez klikani.
- `reports/cockpit_function_inventory_audit_2026_06_27.md` - Cockpit audit bod 1: git-safe inventura endpointu, UI ploch, internich registru, servisnich skriptu a testoveho pokryti; Cockpit je provozne zeleny, hlavni riziko je monoliticky `app/cockpit.py`, dalsi krok je rizikova matice POST akci.
- `reports/cockpit_post_action_risk_matrix_2026_06_27.md` - Cockpit audit bod 2: rizikova matice 56 POST endpointu podle trid read-only, local-open/service, private-write, print, send, delete/purge, external-AI a dev-runner; hlavni dalsi krok je kodovy registr `COCKPIT_POST_ACTIONS` a test, ze kazda POST cesta ma rizikovou kartu.
- `reports/git_branch_audit_cursor_matysek_scene02_2026_06_26.md` - audit smesne neintegrovane vetve `cursor/matysek-scene02-mossy-stump-prototype`: co uz bylo prevedeno na `main`, co jeste prenest samostatne a co archivovat; vzniklo po regresi `Lekarna - sprava`.

## Projects

- `projects/lekarna_domaci_leky.md` - projekt Lekarna: evidence domacich leku v `data/lekarna/`, vyhledavani podle potizi, audit lekarnicky a opakovatelny foto import workflow pres manifest.
- `projects/lekarna_web_app.md` - Webova aplikace Lekarna: publikovana GitHub Pages aplikace se sifrovanym balickem, cockpit UI, hadim dotazem, MP3 napovedou a ChatGPT copy fallbackem; dalsi vyvoj priorita 2.
- `projects/media_image_resize_utility.md` - obecna bezpecna utilita pro zmensovani obrazku podle cilove velikosti v kB; vychozi cil 250 kB, preset Lekarna 100 kB, preview + potvrzeny apply se zalohou.
- `projects/tax_priznani_2025.md` - daňové přiznání 2025, výpočty, checklist formuláře a pravidlo neukládat citlivé údaje.
- `projects/pictnew_vocabulary_image_pipeline.md` - opakovatelný audit a generování obrázků ke slovíčkům FR/IT přes `mapping.json`, `Pict/` a `PictNew/`.
- `projects/tts_edge_audio_tools.md` - české TTS/MP3 nástroje přes edge-tts, dávkový CSV režim a ruční GUI.
- `projects/vocabulary_en_web_cards.md` - webové obrazové kartičky EN z `VocabularyEN.csv`, sync do `docs/`, learner MVP a workflow pro chybějící obrázky.
- `projects/vocabularyfr_web_trainer.md` - VocabularyFR web trainer pro Janu: webový MVP prototyp z desktopové Tkinter aplikace s CSV editací, audio cache, obrázky a auto smyčkou; checkpoint prototypu je commit `da93eba`.
- `projects/fraška_dante_esa_concept.md` - koncept eseje o frašce, dantovské ose, egu, smíření a nově definovaných pojmech.
- `projects/pohadkova_knizka_gpt_canva.md` - domácí dětská knížka z GPT pohádek, Canva sazba, stylová bible a workflow pro ilustrace.
- `projects/vedecke_clanky.md` - širší znalostní databáze / knihovna článků: původně knihovna průlomových vědeckých článků v `data/vedecke_clanky/`, od 2026-06-10 Cockpit `Knihovna` a soukromý fulltextový archiv webových článků v `data/private/article_archive/`; podle korekce 2026-06-11 patří dohromady s Knowledge inboxem jako jeden směr osobní znalostní databáze; 2026-07-01 byla opravena archivace staršího českého HTML kódování a UI potvrzení uložení URL.
- `projects/matysek_english_game_concept.md` - koncept anglické hry pro pětiletého Matýska bez čtení, se scénami, hlasem a příběhem.
- `projects/mmtx_story_hotspot_app.md` - nový směr MMTX: příběhová Pygame hotspot aplikace s houbami, barvami a dynamickým číslováním.
- `projects/multilo_stabilization_cleanup.md` - stabilizace MultiLO návratu do kokpitu, cleanup screenů, pending after callbacky a `tk.Entry` v psacích režimech.
- `projects/email_readonly_oauth.md` - e-mailová integrace Samanthy: read-only hledání, triage a archivace, oddělený prohlížeč Archivu e-mailu a nasazená oprava redigovaného dohledání příloh. Další krok je úzký post-fix read-only retest.
- `projects/document_management_private_vault.md` - priorita 1 projekt soukrome spravy dokumentu mimo git; aktualni vstup je ScanDocu pro GPT PDF z Downloads a prototyp Samantha Cockpit jako ovladaci vrstva, mimo git-safe data.
- `projects/samantha_external_backup.md` - offline zálohování `PythonMF`/Samanthy na externí disk: poslední úspěšná recovery záloha je 2026-07-29 ve snapshotu `20260729_154354`; Pythonový inkrementální běh dokončil 55 798 souborů bez přeskočení a restore drill `AGENTS.md` potvrdil shodný SHA-256.
- `projects/janicka_cockpit_takeover.md` - Janička Cockpit je aktivní netechnický rozcestník k existujícím funkcím. Stará light komunikace a nouzové otevírání plného Adama jsou vyřazené; komunikace se vrátí až jako samostatný funkční Adam-R2.
- `projects/janicka_r2_adam.md` - funkční samostatný R2-Adam pro Janičku: vlastní chat, soukromý kontext, TXT prostor, dokumentová lišta, čtečka a potvrzovaná práce s úplnými sadami read-only zdrojů. E2 živě ověřilo úplný tok e-mail -> vault -> create-only R2 TXT; další krok je ScanDocu kontrola importovaného PDF a krátká přejímka čtečky z pohledu Jany.
- `projects/janicka_cockpit_kucharka.md` - první git-safe kuchařka pro Janu k používání Janičky v Cockpitu: dokumenty, tisk, e-maily, Lékárna, rodinné projekty, Adam, připomenutí, nouzové převzetí a bezpečnostní hranice bez citlivých údajů.
- `projects/pozustalost_rodinny_plan_2026_05_30.txt` - [PRIPOMENOUT] priorita 1 rodinný nouzový balíček / pozůstalost: git-safe návrh struktury pro šifrovaný private balík; technicky nestavět druhý dokumentový systém, ale použít Document Management jako hlavní trezor, pozůstalostní metadata/tagy a samostatný šifrovaný export; soukromé šablony jsou mimo git v `data/private/pozustalost/`.
- `projects/neuberk_interier_design.md` - projekt Neuberk interiér design: soukromý pracovní prostor pro fotky, plánky, rozměry a návrhy interiéru domu; první místnost je půdní hostovská místnost `Kačenka` pro dcery s dětmi, první čistý překres jedné stěny je hotový mimo git v `data/private/neuberk_interier_design/`.
- `projects/automated_recurring_tasks.md` - automatické opakující se úkoly a ColorsAndNumbers soví TTS; GitHub Pages workflow artifact je živá publikační autorita, plánovaný běh 30. 7. uspěl a `main` se už workflow nemění.
- `handoffs/colors_numbers_owl_pages_artifact_checkpoint_2026_07_27.md` - historický checkpoint odstranění sovího zápisu do `main`; krok přepnutí Pages byl později dokončen a současný stav je v projektovém souboru.
- `projects/tomik_video_imovie.md` - [PRIPOMENOUT] projekt priorita 1 pro rodinny iMovie sestřih z malych videi od dcery, tema vnuk Tomik druhy rok; workflow, soukromi, storyboard a exportni checklist.
- `projects/family_memory_films.md` - obecna platforma pro trideni rodinnych fotek/videi a pripravu vzpominkovych filmu; prvni dataset je USA 2019 na plose Macu, cisty seznam 15 dnu je odsouhlaseny, master prehled `Tomik 2` je ulozen mimo git, predstrihovy formular `03_overview/film_selection_form.html` ma autosave, CSV export, rating fotek/videi a prehravani videi a Adamuv prvni navrh ratingu je aplikovany.
- `../START_HERE_RECOVERY.md` - krátký kořenový startovací soubor pro iPhone/GitHub: kam kliknout, když původní Mac nejde zapnout.
- `RECOVERY_CARD_NEW_MAC.md` - polopatická nouzová karta pro obnovu Samanthy na novém Macu z GitHubu a externí recovery zálohy.
- `RECOVERY_FROM_BACKUP.md` - podrobnější lidský a Codex návod pro obnovu Samanthy z externí zálohy na novém Macu.

## Infrastructure Recovery

- `infrastructure/klicove_prikazy_pamatovacek.md` - Mílův stručný git-safe
  pamatováček: návrat k jediné relaci Adam–Codex, bezpečné převzetí připojeného
  `screen`, Cockpit, read-only Git stav, záloha, autosave a seznam příkazů, které
  bez Adama nepoužívat.
- `infrastructure/operating_model.md` - kratky provozni rozcestnik pro bezny start prace, systemove reporty, git checkpointy, reconnect recovery, sitove incidenty a kvantitativni metriky.
- `infrastructure/macos_network_recovery.md` - [PRIPOMENOUT] rozcestnik pro DHCP failure, VPN/Tailscale recovery, network plist reset, hotspot/Wi-Fi repair, network watchdog a aktualni diagnozu domaci Wi-Fi/router vs Mac.
- `infrastructure/codex_reconnect_recovery.md` - [PRIPOMENOUT] reconnect loop handling, navazani pres `samantha`/`screen`, `codex resume`, safe recovery after stream failure a pravidlo nejdrive cist git status + memory.
- `infrastructure/git_checkpoint_protocol.md` - [PRIPOMENOUT] dokonceny krok
  ulozit jako presne omezeny lokalni commit, jednotlive kroky pres den
  nepushovat a GitHub uzavrit jednim potvrzenym dennim balickem; cisty
  `GitHub batch pending` neblokuje zmenu tematu. Dale plati zakaz `git add .`,
  ochrana cizich zmen a citlivych dat a read-only `scripts/work_context_guard.py`.
- `infrastructure/git_branch_archive.md` - archiv vedome neintegrovanych vetvi po auditu; `git_safety_check.py` je nema hlasit jako necekany provozni dluh, ale nezname neintegrovane vetve dal varuje.
- `infrastructure/ssh_setup.md` - SSH/screen workflow pro vzdalenou praci se Samanthou bez ukladani privatnich SSH tajemstvi.
- `infrastructure/tailscale_setup.md` - Tailscale provozni poznamky, opatrny start po sitovem incidentu a odkazy na macOS network recovery.

## Project TVBCP

- `tvbcp/knihovna_cockpit.txt` - nový projektový TVBCP pro druhý
  pracovní profil r-Adama `Knihovna`: vlastní trvalé vlákno, izolovaný workspace,
  deployment receipt a bezpečnostní hranice soukromého archivu. Commit `6a2e205`
  je nasazený a živý test Human–Adam → Knihovna → Human–Adam prošel se zachovanou
  historií, čistými workspaces a potvrzeným read-only tahem.

- `tvbcp/architektura_komunikace_samantha.txt` - aktivni kanonicka
  smlouva Layeru `Human–Adam / vyvojove prostredi`, propojena s
  `WORKSTREAMS.md` a handoffem `human_adam_layer_workstream_start_2026_07_20.md`.
  P6b potvrzuje, ze Human–Adam a Knihovna jsou docasne kompatibilni adaptery;
  jejich zmena neni bez konkretniho problemu aktualni prioritou.
  Od 2026-07-20 ma prednost jednoduchy model: kazdy proud ma vlastni vlakno,
  kratky kontext, TVBCP a handoff; bezny vyvoj jde po jednom cistem kroku primo
  na `main`, bez WIP vetvi, prevzeti a globalniho semaforu. Zachovava zakladni
  UI, reconnect, recovery a skutecne bezpecnostni hranice. Historicky zachycuje
  take dohodu Mily a Adama pro jednoho trvaleho Adama a sdilene app-server vlakno,
  role Cockpitu Mac/iPhone a terminalu, failover, rotaci relace, stihly
  `cockpit.py`, hlas, TVBCP, handoff a autosave. Textove Human–Adam UI, projektovy
  TVBCP, panel `Prace`, izolovany WIP a samoobsluzne nasazeni jsou opakovane
  overene z iPhonu. Audit token, plna fail-closed brana, fast-forward, push,
  rizeny restart, navazani stejneho vlakna a trvala uctenka `deployed` funguji.
  Casomira dlouheho tahu i hlasovy prepis s editaci a explicitnim odeslanim jsou
  nasazene. Bod `170fef2` resi atomicky soubeh s dennim sovim workflow: po brane
  znovu overi GitHub a pushne checkpoint pred lokalnim fast-forwardem; potvrzene
  odmitnuti vrati text do editoru, nejiste doruceni ho k opakovani nevraci.
  Private Tailscale Serve HTTPS cesta je aktivni pro Chrome/iPhone mikrofon,
  ukazuje na stejny lokalni Cockpit a verejny Funnel je vypnuty. Plna brana ma
  721 testu po odstraneni samostatnych panelu App-server LAB a Adam Remote;
  zachovan je i oddeleny Human–Adam checkpoint kompaktniho rozlozeni
  tlacitek nahravani a odeslani. Na iOS tlacitko nahravani bezpecne fokusuje
  editor pro diktovani klavesnice, zatimco Mac nahravaci workflow zustava stejny.
  Adam sam nesmi spoustet Git checkpoint/commit/push/nasazeni a TVBCP aktualizuje
  jen na vyslovny Miluv pokyn. Po prvnim neuspesnem iPhone testu zvuku se
  audiokanal odemyka skutecnym tichym Web Audio zdrojem pri uzivatelskem gestu,
  rozpoznava i stav `interrupted` a ma prime tlacitko `Zvuk: vyzkouset`;
  chyba zvuku nikdy nemeni stav doruceni.

## Handoffs

- `handoffs/human_adam_layer_workstream_start_2026_07_20.md` - [PRIPOMENOUT]
  priorita 1: transformace verejneho modelu na kanonicke pracovni proudy je po
  fazich 4.5g-c1 az c2f funkcne uzavrena. Zavadejici verejna
  `active_profile_*` metadata, osirely deployment-completion endpoint, UI
  karta, action surface, legacy readery a jejich servisni vazby byly odstraneny
  v oddelenych bezpecnych krocich. Deployment evidence nyni vlastni pouze
  simple-main receipt; `human_adam_deploy.py` a jeho test uz nejsou v Gitu ani
  importovatelne. Nasazeny checkpoint `23a219e` prosel vzdalenou Cockpit Quality
  Gate, lokalni branou s 969 testy, novym procesem a smoke `5/5`; Mila nasledne
  potvrdil funkcni panel `Prace`. Zaverecny read-only audit potvrdil ciste a
  zarovnane main, Human–Adam i Knihovna a zadny zivy call-site stareho modulu.
  Historicke TVBCP zaznamy zustavaji chronologii. Ignorovane `.pyc` cache, sest
  osirelych private JSON sad s locky a nazev `human_adam_deploy_gate.log` nebyly
  mazany ani prejmenovany. Interni kompatibilni identity, schema 1, private
  session a workspaces zustavaji chranene. Dne 2026-07-24 byl pripraven
  a nasazen bezpecny auto-sync cisteho a necinneho aktivniho workspace pred
  odeslanim i uzky rez soubezne izolovane prace pri terminalovem WIP. Ten
  povoluje jen editaci a testy v cistem zarovnanem Human–Adam workspace a
  blokuje automaticky checkpoint, commit, push i integraci do cisteho `main` a
  auditu konfliktu. Skutecny zivy test teto soubezne vetve pri soucasnem
  terminalovem WIP jeste chybi. Faze 1 lepsiho TVBCP je nasazena a zive
  vytvorila novy append-only format `Hotovo`, `Rozhodnuti`, `Dalsi krok`,
  `Navrhovane dalsi kroky` a kratky technicky dukaz. Read-only audit cekajici
  integrace i sjednocena recovery hranice automatickeho pripojeni jsou nasazene.
  Mila dne 2026-07-24 rucne dokoncil rotaci bez pripnute kotvy vcetne zachovani
  stareho vlakna a kontinuity z handoffu/TVBCP. Starsi handoff bloky zustavaji
  historickymi snapshoty; jejich `ceka na nasazeni` se po terminalovem
  nasazeni automaticky neuzavira. Faze 2 je implementovana: dalsi potvrzeny
  checkpoint aktualizuje v jednom commitu markerove ohraniceny `Aktualni stav`
  z overeneho `main == origin/main` a posledni deployment uctenky, zatimco
  chronologii neprepise. Potvrzovana integracni brana odlozeneho WIP vyzaduje
  private ownership marker svazany s pracovnim proudem, base commitem a
  otiskem path-level zmen. Posun `main`, cizi WIP, divergence nebo neshoda
  markeru zustavaji servisnim rozhodnutim bez automatickeho merge/rebase.
  Cilenych 446 a uplnych 1216 testu proslo. Dne 2026-07-25 prednasazovaci audit zachytil
  starsi ctyrsouborovy WIP rotace bez kotvy bez ownership markeru. Mila
  vyslovne potvrdil servisni zacleneni; patch byl radkove shodny, cilene testy
  92/92 a plna brana 1216/1216 prosly. Kontrola rotace je vazana na identitu
  vlakna, nikoli na revizi volitelne kotvy. Zbyva checkpoint/push, zarovnani
  profilu, nasazeni a rucni retest. Dne 2026-07-25 pribyla obecna
  samoobsluzna brana pro rucni dorovnani cisteho lokalniho `main` z
  `origin/main`: read-only audit ukaze presny cil a zmenene cesty, potvrzeny
  apply znovu overi oba commity, pouzije pouze fast-forward a synchronizuje
  ciste profily. WIP, aktivni nebo nejisty tah, dirty stav, lokalni naskok,
  divergence a zmena GitHubu ji blokuji. Cilenych 426 a uplnych 1227 testu
  proslo. Zivy soubezny test pote uspesne prosel od terminaloveho WIP pres
  validni ownership marker a potvrzenou integraci az po commit, push a
  nasazeni `cba953e`; oba profilove workspaces zustaly ciste. Napoveda
  `Prace -> ?` nyni popisuje i odlozeny tah a rucni dorovnani po sovim commitu.
  Navazujici zpresneni odstranilo pevne pojmenovanou Knihovnu z obecne
  napovedy; pravidlo soukromeho archivu se zobrazi jen pri capability
  `private_archive_direct` aktivniho proudu. Cilenych 66 testu proslo; zbyva
  commit/push a potvrzene nasazeni tohoto zpresneni.

- `handoffs/human_adam_work_help_and_wip_lifecycle_2026_07_19.md` - [PRIPOMENOUT]
  priorita 1: obsah napovedy `Prace -> ?` byl rucne potvrzeny, ale maly vnitrni
  rolovaci box byl hur citelny. Ergonomicka oprava ve vetvi
  `wip/human-adam-work-help-layout-20260719` odstranuje vlastni `max-height` a
  vnitrni scrollbar; roluje se cely velky obsahovy panel jako u `Plan`. Cilenych
  50 UI testu i plna Cockpit brana prosly. Commit `20c64a7` je v `main`, rizeny
  restart na PID `33066`, petibodovy smoke test i zive HTML jsou zelene; zbyva
  pouze rucni vizualni retest.

- `handoffs/human_adam_plan_help_and_adoption_2026_07_19.md` - [PRIPOMENOUT]
  priorita 1: staticka napoveda `?` v okne `Plan` je implementovana bez API a
  bez moznosti menit profil, kotvu, vlakno, TVBCP nebo Git. Obsahuje beznou
  praci, sestikrokovou rotaci, reseni blokeru a nouzovy navrat. Plna Cockpit
  brana prosla 825 testy; commit `5052a4c`, rizeny restart a petibodovy smoke
  test jsou zelene. Zbyva rucni proklik napovedy. Potom podle navodu projit
  cvicne overeni a nekolik dni zazit soucasne workflow; teprve potom zahajit
  read-only kontrolu aktualnosti handoffu.

- `handoffs/development_branch_lifecycle_phase1_wip_2026_07_19.md` - [PRIPOMENOUT]
  priorita 1: prvni read-only faze rizeni zivotniho cyklu WIP vetvi ma
  samostatne auditni jadro, CLI, workflow registraci, GET endpoint a male
  ovladani v panelu `Prace`. Pripojeny nebo rozpracovany worktree je vzdy
  chraneny, neoveritelny stav selhava uzavrene a zadny uklid se neprovadi.
  Plna Cockpit brana prosla 824 testy; zbyva potvrzene prevzeti do `main`,
  nasazeni, restart a zivy read-only test.

- `handoffs/global_development_semaphore_wip_2026_07_19.md` - [PRIPOMENOUT]
  priorita 1: commit `90ed06c` nasadil trvaly globalni vyvojovy semafor pro
  Human-Adam, Knihovnu a terminal, read-only modelovy guard a fail-closed
  checkpoint/nasazeni pri cizim WIP. Plna brana prosla 815 testy, rizeny restart
  a read-only smoke test jsou zelene; zbyva rucni interaktivni retest. Navazujici verzovany terminalovy
  deployment guard nebo kontrolovany `pre-push` hook je zapsany k samostatnemu
  navrhu a nesmi se instalovat automaticky.

- `handoffs/human_adam_thread_rotation_backend_wip_2026_07_19.md` - [PRIPOMENOUT]
  priorita 1: izolovany WIP obsahuje hotovou bezpecnou rucni rotaci dlouheho
  profiloveho vlakna vcetne profilove zamknuteho API a ovladani v panelu `Plan`.
  Stare vlakno a historie zustavaji zachovane; audit je fail-closed a apply
  vyzaduje aktivni kotvu i presnou vetu. Plna brana prosla 804 testy. Zbyva
  potvrzene prevzeti do `main`, nasazeni, vizualni kontrola a zivy profilovy test.

- `handoffs/human_adam_profile_switch_recovery_2026_07_18.md` - [PRIPOMENOUT]
  priorita 1: přepínání Human–Adam / Knihovna už nemá trvale blokovat stará
  nejistá doručení, pokud po nich proběhl potvrzeně dokončený tah. Nová nejistota
  zůstává fail-closed a UI ukáže chybu ve viditelné části i na iPhonu. Plná brána
  prošla 768 testy; zbývá synchronizace profilů, restart a živý test oběma
  směry.

- `handoffs/human_adam_preserved_wip_visibility_2026_07_18.md` - [PRIPOMENOUT]
  priorita 1: TVBCP checkpoint, který při souběhu vypadal jako ztracený, byl
  bezeztrátově obnoven a nasazen jako `ebd47b9`. Nová backend/UI oprava odlišuje
  přímo auditovatelný WIP od zachovaného rozvětveného WIP, ukáže jeho počet a
  cesty, ale audit ponechá fail-closed. Plná brána prošla 766 testy; po
  checkpointu/pushi zbývá restart a běžný smoke test.

- `handoffs/human_adam_revision_failure_history_2026_07_17.md` - [PRIPOMENOUT]
  priorita 1: očekávaná revize chrání soukromou kotvu před přepsáním ze starší
  karty a oddělené private registry Human–Adam/Knihovna drží posledních 20
  redigovaných selhání bez zpráv, logů a soukromých textů. Plná brána prošla 764
  testy; po checkpointu/pushi zbývá řízené nasazení a živý Mac/iPhone retest.

- `handoffs/human_adam_knihovna_profile_2026_07_17.md` -
  implementovaný dvouprofilový pilot Human–Adam / Knihovna s atomickým přepnutím
  vlákna, workspace, TVBCP a deploymentu; plná brána 734 testů, commit/push
  `6a2e205`, restart i živý smoke test obou směrů prošly. Aktivní zůstal Human–Adam.

- `handoffs/janicka_ra2_private_context_proposal_2026_07_15.md` - aktivní návrh
  priority 2 pro R2-Adam v Cockpitu Janička: vlastní trvalé app-server vlákno,
  soukromý kompaktní kontext mimo Git, zákaz změn a mazání zdrojových dat a
  budoucí nový TXT export s náhledem a dvoukrokovým odesláním Janě; implementace
  ještě nezačala.
- `handoffs/cockpit_command_cheatsheet_2026_07_18.md` - [PRIPOMENOUT] read-only
  pamatováček klíčových příkazů je připravený v Servisu i Recovery centru a
  rozlišuje také `/new` od úplného ukončení přes `/exit` nebo `/quit`;
  plná Cockpit brána prošla 776 testy, zbývá řízený restart a vizuální retest na
  Macu nebo iPhonu.
- `handoffs/appserver_human_adam_text_remote_verified_restart_backup_2026_07_14.md` - [PRIPOMENOUT]
  priorita 1 před restartem Macu: vzdálená textová práce a samoobslužné nasazení
  jsou opakovaně ověřené až po sticky účtenku, bod `5bac508` a 703 testů. Po
  startu přes `samantha` nejdřív ověřit externí disk a provést zastaralou recovery
  zálohu; potom pokračovat časomírou dlouhého tahu a hlasovým vstupem.
- `handoffs/samantha_communication_architecture_checkpoint_2026_07_13.md` - [PRIPOMENOUT]
  priorita 1 checkpoint nove kanonicke komunikace: jeden trvaly Adam a app-server
  thread, Cockpit Mac/iPhone pro beznou praci, terminal pro vyvoj a nezavisly
  failover, projektovy TVBCP a pravidlo po prijeti nove cesty odstranit legacy
  watcher/TTY/duplicitni komunikacni vetve misto udrzovani fallbacku fallbacku.
- `handoffs/external_backup_disk_usb_not_detected_2026_07_14.md` - [PRIPOMENOUT]
  externi recovery disk se 2026-07-14 neenumeroval na USB/Thunderbolt ani jako
  disk; neprovadet First Aid, dokud jej macOS neuvidi. Posledni zaloha je z
  2026-07-09; dalsi krok je jiny datovy kabel, primy jiny port a napajeni.
- `handoffs/appserver_remote_work_cell_v0_2026_07_13.md` - historicky checkpoint vyrazeneho panelu Adam Remote. Jeho bezpecny izolovany Git workspace byl zachovan pod Human–Adam; samostatna sluzba, API a UI byly 2026-07-15 odstraneny.
- `handoffs/colors_numbers_private_photo_gallery_proposal_2026_07_13.md` - pozastaveny navrh tlacitka `Foto` a lokalni galerie nejvyse tri fotografii v obrazovce `Numbers`; kvuli verejnemu repozitari/GitHub Pages se doporucuje pouze lokalni `IndexedDB`, komprese a odstraneni EXIF/GPS, bez commitovani rodinnych fotografii. Nic neimplementovat bez noveho rozhodnuti Mily.
- `handoffs/appserver_lab_thread_registry_context_capsule_2026_07_13.md` - historicky checkpoint vyrazeneho read-only App-server LAB. Samostatna sluzba, probe, API, tlacitko a modal byly 2026-07-15 odstraneny; bez dalsiho retestu.
- `handoffs/appserver_lab_lifecycle_verified_2026_07_13.md` - historicky zaklad read-only LAB: automaticky 50/50 reliability probe a Miluv rucni lifecycle test s disconnect/resume/restart; vsech 7 pokynu bylo dokoncenych bez chyby nebo duplicity. Navazujici stav registru a capsule je v `handoffs/appserver_lab_thread_registry_context_capsule_2026_07_13.md`.
- `handoffs/cockpit_architecture_current_2026_07_10.md` - [PRIPOMENOUT] jediny
  prubezny handoff modernizace Cockpitu. Faze 2.1 az 2.4 jsou historicky hotove;
  aktualni priorita 1 je Cockpit dieta. Mereni 2026-07-26 ukazuje 19 620
  neprazdnych radku v `app/cockpit.py` a 91 218 produkcnich plus testovacich
  radku v cele gate. Dalsi krok je pouze read-only Dieta D0, potom jeden
  potvrzeny e-mailovy rez Faze 1.4.
- `handoffs/janicka_full_adam_cockpit_recovery_ios_card_2026_07_09.md` - historický checkpoint odstraněné nouzové cesty `Otevřít plného Adama`; aktuální komunikace Janičky čeká na samostatný Adam-R2.
- `handoffs/cockpit_email_archive_browser_2026_07_09.md` - Cockpit Archiv e-mailu: read-only prohlizec EmailArchiveVault na `/email-archive/`, katalog Webove aplikace, bezpecne otevreni lokalniho HTML/textu/originalniho EML, metadat a stazenych priloh; dalsi krok je rucni UI retest na znamych archivovanych UID.
- `handoffs/cockpit_voice_janicka_stability_checkpoint_2026_07_09.md` - historický checkpoint odstraněné komunikační cesty a tehdejší diagnostiky Janičky; aktuální stav je v `projects/janicka_cockpit_takeover.md`.
- `handoffs/cockpit_startup_health_voicebridge_verified_2026_07_09.md` - Cockpit stabilita overena: start/restart/launchd pouzivaji rychly `/api/server/health`, `/api/status` ma timing sekci, hotkey `Ctrl+Option+Command+C` otevrel `127.0.0.1:8770` bez `Load failed`, diagnostika byla OK a zaverecny VoiceBridge test z Cockpitu prosel end-to-end bez Mac TTS.
- `handoffs/lekarna_photo_import_pil_publish_retire_verified_2026_07_09.md` - Lekarna foto import end-to-end overen: OpenAI OCR, SUKL DLP, online PIL, `PIL_Short`, prijem na sklad, automaticky encrypted bundle commit/push, testovaci SERTIVAN prijat a vyrazen; export uz vynechava radky `vyradeno`.
- `handoffs/git_commit_cleanup_a1_2026_05_23.md` - A1+ commitovy uklid: velka memory/RAG davka je commitnuta a pushnuta jako `ef15589`; pravidlo do odvolani je navrhovat tematicke commity pri dalsich vetsich rozpracovanych zmenach.
- `handoffs/cockpit_recovery_center_priority_2026_06_03.md` - historicky Cockpit Recovery centrum MVP: read-only navazani po padu Samanthy/Codexu s poslednim `session_*` autosave timestampem, git statusem, handoffem a postupem `samantha` / `codex resume --last`; prekryto aktualnim radkem `Cockpit Recovery centrum` v `ACTIVE_PROJECTS.md`.
- `handoffs/cockpit_development_priorities_2026_06_03.md` - historicky seznam 6 priorit vyvoje Cockpitu; vsech 6 MVP bodu je hotovych a prekrytych aktualnim radkem `Cockpit Recovery centrum` v `ACTIVE_PROJECTS.md`.
- `handoffs/cockpit_health_status_buttons_2026_06_04.md` - historicky Cockpit health stav tlacitek: panel `Frontend` / `Tlačítka` / `API` / `Poslední chyba`, globalni frontend error handlery a lehky probe `/api/status` + `/api/recovery/status`; prekryto aktualnim stavem Cockpitu.
- `handoffs/cockpit_diagnostics_modal_2026_06_04.md` - historicky Cockpit diagnosticky modal: tlacitko `Diagnostika`, mereni endpointu z prohlizece, frontend/tlacitka stav a posledni frontend/API chyby; prekryto aktualnim stavem Cockpitu.
- `handoffs/cockpit_action_queue_2026_06_04.md` - historicka Cockpit akcni fronta `Co ted delat` jako MVP: `/api/status` vraci `action_queue`, UI ukazuje prioritizovane karty; prekryto aktualnim stavem Cockpitu.
- `handoffs/cockpit_safe_restart_2026_06_04.md` - historicky Cockpit bezpecny restart jako MVP: tlacitko `Restart Cockpitu`, endpoint `/api/cockpit/restart`, worker `scripts/restart_cockpit.py`; pozdeji znovu opraveno restart tlacitko 2026-06-23.
- `handoffs/cockpit_restart_button_and_voice_audio_cleanup_2026_06_23.md` - Cockpit restart button fix: restart worker uz nevyzaduje kratce volny port, protoze launchd muze okamzite nastartovat novy server; UI restartu toleruje preruseny fetch a obnovi stranku. Soucasne Edge TTS docasne MP3 prehrava pres `afplay`, aby se neimportovaly do Apple Music.
- `handoffs/cockpit_hotkey_fallback_port_2026_07_07.md` - Cockpit global hotkey / start fallback: hotkey fungoval, ale port `8770` byl mrtve obsazeny starymi Python procesy; `open_cockpit.py` ted umi nouzove spustit lokalni Cockpit na dalsim volnem portu, typicky `8771`; po restartu Macu retestovat navrat na standardni `8770`.
- `handoffs/cockpit_session_autosave_cleanup_2026_06_30.md` - Cockpit autosave cleanup a provozni oprava: retence ponechava posledni 3 dny, 12 nejnovejsich snapshotu a latest soubory; managed relace watcher nespousteji, watcher ma singleton lock a rychle ukonceni sleepu, Cockpit ukazuje watcher count. Zivy nadbytecny Janička watcher byl ukoncen bez mazani snapshotu; aktualne bezi jeden watcher.
- `handoffs/cockpit_remote_exact_confirmation_cards_2026_06_27.md` - historický checkpoint vzniku potvrzovací karty; karta zůstává obecná, tehdejší transport potvrzení je vyřazený.
- `handoffs/cockpit_audit_live_2026_06_28.md` - [PRIPOMENOUT] zivy handoff aktualniho Cockpit auditu: potvrzovaci karty, dokumentovy panel, ScanDocu/JPEG revize a ergonomicke opravy jsou hotove a pushnute; dalsi krok je pokracovat rucnim auditem po blocich a tento handoff prubezne aktualizovat.
- `handoffs/codex_full_access_voicebridge_guard_next_2026_06_29.md` - historicky full-access navazovaci handoff: vypnuti Codex sandboxu, dokonceni VoiceBridge testu a puvodni plan Guardu proti mazani; prekryto aktualnim stavem v `ACTIVE_PROJECTS.md` a pravidlem `technical/global_safety_brake.md`.
- `handoffs/voicebridge_full_access_email_confirmation_closed_2026_06_29.md` - VoiceBridge full-access blok je uzavreny: textove mezistavy, browser autoread, neoverene GUI doruceni bez falesneho uspechu, watcher start kontrola a tokenove potvrzovani e-mailovych draftu prosly realnym testem; puvodni plan zalozit Guard je prekryty existujicim `technical/global_safety_brake.md`.
- `handoffs/voicebridge_operational_contract_2026_06_30.md` - historický provozní kontrakt odstraněné komunikační cesty; slouží pouze jako archivní důkaz a není aktuálním návodem.
- `handoffs/cockpit_managed_codex_sessions_2026_07_03.md` - Cockpit sprava managed Codex relaci: prehled ukazuje celkem / bezne / spravovane relace; `Adam managed` a `Janička light` se nepocitaji do limitu beznych relaci ani cleanup kandidatu. Stop Janičky overuje skutecne ukonceni a managed relace uz nespousteji vlastni autosave watcher.
- `handoffs/cockpit_robustness_smoke_backup_bridge_2026_06_09.md` - Cockpit robustnost v uspornem rezimu: pridany read-only `cockpit_smoke_check.py`, strukturovany `backup_status` v `/api/status` a read-only `adam_bridge_readiness_report.py`; lokalni i Tailscale Cockpit po restartu prosly smoke checkem.
- `handoffs/cockpit_ui_cleanup_experiment_checkpoint_2026_06_11.md` - Cockpit UI cleanup experiment: audit obsahu je commitnuty jako `157425e`, mirny UI uklid jako `ed2f520`; Cockpit restartovany lokalne i pres Tailscale, `tests.test_cockpit` a smoke check prosly a Mila potvrdil, ze iPhone Cockpit funguje dobre; dalsi krok je read-only rozdeleni hlavni obrazovky na `denne`, `obcas`, `servis`, `archiv`.
- `handoffs/cockpit_main_screen_phase2_cleanup_2026_06_11.md` - Cockpit hlavni obrazovka faze 2: `Co ted delat` je presunute nad hlas, `Hlas` je rozbalovaci, `Servis` je jedno hlavni misto pro servisni akce/stav/prehledy a karta `Stav` ma lidstejsi denni radky; testy a lokalni/Tailscale smoke check prosly a Mila rucne potvrdil, ze Cockpit vypada dobre; navazujici problem je samostatne e-mailove workflow po zpracovani 1 e-mailu.
- `handoffs/cockpit_codex_session_false_duplicate_fix_2026_06_17.md` - Cockpit/voice bridge oprava falešného varování `Codex relace: 2`: detekce už neleze od duplicitního child Codex procesu ke `screen` rodiči na jiném TTY; po bezpečném restartu lokální i Tailscale instance Cockpit hlásí jednu relaci `ttys000`, bridge `ok` a Míla potvrdil UI stav jako OK.
- `handoffs/samantha_screen_scrollback_fix_2026_06_18.md` - Samantha start pres `screen`: pridan projektovy `scripts/samantha_screenrc`, vetsi scrollback, vypnuti alternate screenu a startovni napoveda `Ctrl+A` potom `Esc`; dalsi krok je rucni retest noveho startu `samantha`.
- `handoffs/system_quick_check_git_safety_2026_06_09.md` - mala infrastrukturalni robustnost: pridany `git_safety_check.py` pro staged private/autosave/env ochranu a `system_quick_check.py` pro read-only souhrn git/backup/Cockpit/Adam bridge/autosave; testy prosly.
- `handoffs/system_project_audit_generator_done_2026_06_23.md` - opakovatelny generator systemoveho auditu projektu/toolu/vrstev je hotovy jako CLI, Samantha tool a registrovany system report; `--save` uklada git-safe report bez private dat a neprepisuje existujici denni audit.
- `handoffs/capability_registry_next_checkpoint_2026_06_26.md` - Capability registry dalsi krok: po uklidu MMTX a pushnuti `git_push_guard.py` je potvrzena filozofie low-friction osobniho provozu; dalsi maly krok je registry model + par existujicich schopnosti + read-only audit/test potvrzovacich pravidel.
- `handoffs/capability_registry_priority_gaps_closed_2026_06_26.md` - Capability registry prioritni mezery zavrene a audit rozdeleny podle rizika: registry ma 28 zaznamu, capability audit hlasi `Priority missing capability records: None`, kriticke/action-write mezery 0, action/review 14 a read-only nebo low-risk 42.
- `handoffs/capability_registry_complete_2026_06_27.md` - Capability registry plne pokryti: registry ma 84 zaznamu, runtime prompt pouziva registry policy a capability audit hlasi `Registry-covered agent tools: 81/81`, vsechny missing vrstvy 0 a `Agent tools missing capability records: None`; dalsi prakticky krok je recovery zaloha.
- `handoffs/autosave_status_and_voice_triage_fix_2026_06_12.md` - Autosave/auto-safe checkpoint: pridany read-only `scripts/autosave_status.py`, `system_quick_check.py` hlasi watcher i stari snapshotu a voice triage uz neblokuje slovo `stisknout` jako `tisk`.
- `handoffs/article_archive_cockpit_library_2026_06_10.md` - Cockpit knihovna článků: URL vstup, kategorie Recepty/Vědecké články/Ostatní, soukromý TXT/HTML archiv mimo git, fulltextové hledání, čtení a HTTPS fallback přes systémový `curl` při Python certifikační chybě.
- `handoffs/knowledge_database_text_input_and_system_audit_2026_06_11.md` - [PRIPOMENOUT] dnešní checkpoint ke znalostní databázi: systémový audit QN #40/#13, sloučení Knihovna článků + Knowledge inbox, Cockpit vstup `Uložit text` pro recepty/ChatGPT texty bez URL a CLI fallback `scripts/archive_text_entry.py`.
- `handoffs/knowledge_database_recipe_attachments_cockpit_checkpoint_2026_06_11.md` - [PRIPOMENOUT] znalostní databáze / recepty: 23 importovaných receptových položek od Samanthy, datový model příloh, Cockpit zobrazení a akce `Připojit obrázek`, backend `attach_article_image(...)` a CLI fallback `scripts/attach_article_image.py`; další krok je jedna reálná ručně psaná rodinná karta s fotkou/skenerem.
- `handoffs/knowledge_database_library_safe_delete_2026_06_19.md` - Knihovna / recepty: Cockpit má potvrzované `Vyřadit z knihovny`, backend přesouvá položku do soukromého koše `data/private/article_archive/trash/articles/` a odstraňuje ji z registru; další krok je ruční UI retest na jedné bezpečné položce.
- `handoffs/chatgpt_export_knowledge_import_checkpoint_2026_06_19.md` - [PRIPOMENOUT] ChatGPT export / Knowledge inbox import: soukromý read-only index 826 konverzací je hotový, aktuální receptová kandidatní sada je uzavřená, 21 receptových položek bylo ponecháno v knihovně a knihovna má 44 receptů; další recepty hledat už jen novým širším scanem exportu; neukládat texty chatů ani receptů do gitu.
- `handoffs/knowledge_database_library_pdf_export_cleanup_2026_06_22.md` - [PRIPOMENOUT] Knihovna: rozpracované necommitnuté změny pro PDF export článků, potvrzované odeslání e-mailem, lepší automatické čištění balastu při URL importu a CLI cleanup tool; vyčištěn jeden vědecký článek v private archivu, další krok je git safety kontrola a tematický commit jen kódu/testů bez private dat.
- `handoffs/cockpit_purchase_pdf_and_library_export_email_filter_2026_06_22.md` - Cockpit hotový checkpoint: hledání dokumentů umí najít nákupní archiv `data/private/purchases`, nákupní výsledek má vlastní PDF čtečku `/purchases/read`/`/purchases/pdf`, exporty z Knihovny s prefixem `[SamanthaLibraryExport]` se už nenabízejí v e-mailové/document intake frontě.
- `handoffs/cockpit_email_intake_cache_fix_2026_06_08.md` - historicky Cockpit e-mail intake cache fix: oprava klientské cache po zpracování e-mailových dokumentů; překryto aktuálním stavem `iCloud Mail read-only / Email Cases` v `ACTIVE_PROJECTS.md`.
- `handoffs/knowledge_library_read_state_to_read_2026_06_23.md` - Knihovna: pridany pracovni stav clanku `K precteni` / `Hotovo`, zalozka `K přečtení` napric kategoriemi a backend filtr `read_state`; soukromy clanek o kratkozrakosti u deti je lokalne oznaceny k precteni.
- `handoffs/knowledge_library_open_source_url_button_2026_06_23.md` - Knihovna: v detailu clanku pribylo tlacitko `Otevřít na webu`, ktere u URL clanku otevre `canonical_url` nebo `source_url` v nove zalozce; Mila rucne potvrdil, ze v Cockpitu funguje.
- `handoffs/knowledge_library_encoding_and_backup_cleanup_2026_07_01.md` - Knihovna článků: oprava archivace českého `windows-1250` HTML, preferování hlavního obsahu článku, jasnější UI potvrzení po uložení URL, soukromý cleanup rozbitých GVT záznamů, přesun carbonary do receptů a navazující recovery záloha `20260701_203915`.
- `handoffs/knowledge_library_article_editing_2026_07_16.md` - Knihovna v Cockpitu: commit `2597e14` přidal editaci názvu, textu, kategorie, tagů a zdrojových údajů článku, úpravu popisku přílohy a potvrzované přesunutí přílohy do soukromého koše; soukromé texty ani přílohy nejsou v Gitu.
- `handoffs/chatgpt_travel_places_library_checkpoint_2026_06_26.md` - ChatGPT export / Cestovani mista: nova knihovni kategorie `Cestování / místa` (`travel_places`) je pushnuta, soukromy kandidatni report je v private Knowledge inboxu a 4 ocistene cestovni karty jsou vlozene do private knihovny se stavem `K přečtení`.
- `handoffs/email_icloud_pdf_metadata_review_fix_2026_06_12.md` - historicky e-mailovy PDF intake fix: opraveno iCloud/Seznam parsovani hlavicek a iCloud BODYSTRUCTURE metadat priloh; překryto pozdějšími document/email checkpointy a aktuálním stavem `iCloud Mail read-only / Email Cases`.
- `handoffs/document_vault_email_pdf_review_metadata_fix_2026_06_13.md` - dokumentovy vault / e-mailove PDF revize: opraveno zachovani nove rucne zadane oblasti, `email-attachment-pdf` jako slaby technicky typ, doplneno `case_id` v Cockpit metadatech, ScanDocu revize nastavuje `reading_status=ok` a Cockpit uz nema ukazovat dokumenty, ktere ScanDocu povazuje za zrevidovane.
- `handoffs/document_metadata_and_tts_audio_checkpoint_2026_06_14.md` - ranni checkpoint: ceske manualni metadata dokumentu se slugguji do citelnych ASCII hodnot, Cockpit ma popisky pro danove priznani a pojistne prilohy, vault po potvrzenych opravach hlasi 27/27 kompletnich klasifikaci a TTS pravidlo rika spoustet skutecne Mac audio mimo Codex sandbox.
- `handoffs/scandocu_kanta_nonpdf_review_checkpoint_2026_06_15.md` - ScanDocu Review / Kanta checkpoint: Kanta prilohy s castkami jsou v private vaultu jako dokumenty k revizi, oblasti pro Kanta bloky jsou registrovane, ne-PDF prilohy se ve ScanDocu uz neposilaji do PDF iframe a misto toho maji download panel; dalsi krok je projet Kanta frontu v Review.
- `handoffs/cockpit_iphone_tailscale_shortcut_2026_06_05.md` - Cockpit je dostupny z iPhonu pres Tailscale adresu Macu, launchd sluzba `com.miloslavfalta.samantha.cockpit.tailscale` bezi s `RunAtLoad`/`KeepAlive`, verejny instalator je `scripts/install_cockpit_tailscale_launchd.sh` a podepsana iPhone zkratka je ulozena mimo git v iCloud Drive.
- `handoffs/cockpit_voice_input_auto_inbox_2026_06_05.md` - Cockpit hlasovy vstup na Macu: rychly prepis pres `/api/speech/transcribe` se po nahrani automaticky uklada do private inboxu `data/private/voice_inbox/latest_voice_command.md` pro pozdejsi prevzeti Codexem/Samanthou; nic se samo nespousti.
- `handoffs/adam_voice_terminal_bridge_checkpoint_2026_06_05.md` - historický checkpoint odstraněného terminálového mostu; neslouží jako aktuální návod.
- `handoffs/adam_voice_bridge_target_tty_checkpoint_2026_06_05.md` - historický checkpoint odstraněného cílení na TTY marker; bez aktuálního dalšího kroku.
- `handoffs/adam_voice_bridge_end_to_end_checkpoint_2026_06_05.md` - historický end-to-end checkpoint odstraněné komunikační cesty.
- `handoffs/adam_voice_bridge_iphone_text_fallback_checkpoint_2026_06_06.md` - historický checkpoint odstraněného iPhone textového fallbacku.
- `handoffs/adam_voice_remote_cockpit_next_step_2026_06_06.md` - historický směr vzdáleného Cockpitu; komunikační transport je vyřazený, obecná potvrzovací karta zůstává.
- `handoffs/adam_voice_cockpit_readonly_capabilities_next_2026_06_06.md` - historický checkpoint; obecný capability registr zůstává, komunikační transport je vyřazený.
- `handoffs/adam_voice_ttys001_readiness_blocker_2026_06_07.md` - historický blocker odstraněného TTY transportu.
- `handoffs/adam_voice_global_safety_brake_2026_06_09.md` - Adam Voice smer: bezna hlasova/read-only prace ma byt defaultne povolena a globalni brzda se ma pouzit jen pro uzky okruh vysoce rizikovych destruktivnich/systemovych kroku; pravidlo je v `technical/global_safety_brake.md`.
- `handoffs/adam_voice_bridge_tty_switcher_2026_06_10.md` - historický checkpoint odstraněného TTY přepínače.
- `handoffs/adam_voice_iphone_audio_bridge_checkpoint_2026_06_11.md` - historický checkpoint odstraněného iPhone audio transportu.
- `handoffs/adam_voice_bridge_cleanup_and_cockpit_controls_2026_06_12.md` - historický cleanup odstraněných ovládacích prvků.
- `handoffs/adam_voice_cockpit_dev_runner_checkpoint_2026_06_12.md` - historický checkpoint; obecný servisní runner a potvrzovací karta zůstávají, komunikační transport ne.
- `handoffs/adam_voice_bridge_freeze_email_return_2026_06_12.md` - historický checkpoint zmrazení později odstraněné komunikační cesty.
- `handoffs/adam_voice_iphone_autoread_confirmed_2026_06_29.md` - historický důkaz tehdejšího iPhone autoreadu; odstraněný transport se neobnovuje.
- `handoffs/janicka_cockpit_takeover_project_start_2026_06_06.md` - historicky start projektu Janička Cockpit / používání a převzetí Samanthy; části o neimplementovaném tlačítku jsou překryté aktuálním stavem v `projects/janicka_cockpit_takeover.md`.
- `handoffs/janicka_adam_text_bridge_functional_checkpoint_2026_06_07.md` - Janička Adam text bridge funkční checkpoint: skrytá `screen` cesta se ukázala jako nespolehlivá, výchozí stav je terminálový bridge s vyčištěním vstupu, cílením na označenou nebo nalezenou Codex relaci a odpovědí přes `scripts/adam_voice_reply.py --request-id ... --route janicka_text_bridge`; explicitní VS Code helper zůstává jako fallback a reálné testy `Najít dokument` a `Pozůstalost` prošly.
- `handoffs/janicka_light_samantha_bridge_checkpoint_2026_07_03.md` - historický checkpoint odstraněné light relace Janičky; komunikace čeká na Adam-R2.
- `handoffs/janicka_chat_ui_fallback_simplification_2026_07_03.md` - historický UI checkpoint odstraněného chatu a fallbacku Janičky.
- `handoffs/janicka_cockpit_family_projects_modal_2026_06_26.md` - [PRIPOMENOUT] Janička Cockpit: tlačítko `Rodinné projekty` teď otevírá netechnický mezikrok se dvěma volbami, `Rodinný výběr videí a fotek` a `Přehled projektů`; testy prošly, lokální Cockpit byl restartovaný a smoke check prošel; další krok je ruční UI retest s Janinou perspektivou.
- `handoffs/memory_cleanup_commit_afternoon_checkpoint_2026_05_23.md` - historicky checkpoint commitoveho odpoledne: Dokumenty, Lekarna, PictNew/VocabularyIT, Tomik/FamilyVideoOrganizer, E-mail, Samantha/RAG a automaticke ukoly byly zkomprimovane a commitnute v `ef15589`.
- `handoffs/automated_recurring_tasks_cloud_2026_05_20.md` - historicky mezistav automatickych ukolu: obecna denni rutina ve 3:00, macOS `launchd`, GitHub Actions skeleton a bezpecnostni pravidla.
- `handoffs/colors_numbers_owl_tts_startup_prompt_2026_05_22.md` - historicky mezistav automatickych ukolu: jednorazovy ColorsAndNumbers soví TTS task pro 2026-05-23 a denni startovni dotaz.
- `handoffs/lekarna_web_app_hotovo_2026_05_20.md` - Webova aplikace Lekarna je uzavrena jako hotova; verejna aplikace bezi se sifrovanym balickem a dalsi vyvoj je priorita 2 az podle casu nebo urgentnich pozadavku.
- `handoffs/lekarna_status_po_doplneni_vitaminu_2026_05_21.md` - Lekarna: aktualni stav po kokpitu, doze vitaminu, obrazku doporuceni, fotkach Kozliku/Vigantolvitu a oprave fallbacku; Silymarin stale nema vlastni fotku.
- `handoffs/lekarna_photo_staging_tool_2026_06_12.md` - Lekarna foto staging tool: novy Samantha tool `stage_lekarna_photo_import` umi vzit fotky ze Stazenych, zkopirovat je do soukrome slozky, vytvorit manifest a ponechat finalni zapis do evidence na potvrzenem `apply`.
- `handoffs/lekarna_import_manifest_editor_checkpoint_2026_07_06.md` - Lekarna import checkpoint: Sprava Lekarny dostala editor automatickeho manifestu a validacni brzdu kvality pred prijmem; slabsi testovaci prijem byl po Milove potvrzeni odstranen a dalsi krok je cisty test s jinym lekem.
- `handoffs/matysek_forest_school_scene_navrh_2026_05_26.md` - historicky Matysek MMTX ForestSchool navrh: rozpracovani webove sceny `forestSchool` v `docs/` a mirroru; prekryto aktualnim radkem `MMTX` v `ACTIVE_PROJECTS.md`.
- `handoffs/matysek_forest_school_checkpoint_2026_05_26.md` - historicky ForestSchool checkpoint po doladeni prvni petky obrazku, demo hlasu a odmen; prekryto aktualnim radkem `MMTX` v `ACTIVE_PROJECTS.md`.
- `handoffs/matysek_forest_school_post_commit_checkpoint_2026_05_26.md` - historicky post-commit checkpoint ForestSchool po pushi `9850298`; prekryto pozdejsim ForestSchool portal stavem a aktualnim radkem `MMTX`.
- `handoffs/matysek_forest_school_lessons_voices_checkpoint_2026_05_27.md` - historicky ForestSchool checkpoint k obrazkum lekci 2-12 a novym Benji/Bunny hlasum; prekryto pozdejsim napojenim 12 lekci a aktualnim radkem `MMTX`.
- `handoffs/matysek_forest_school_portal_resize_checkpoint_2026_05_27.md` - historicky ForestSchool portal/resize checkpoint: 12 lekci, mapa, portal a komprimovane predmetove PNG; prekryto aktualnim radkem `MMTX`.
- `handoffs/matysek_forest_journey_voice_strategy_2026_06_01.md` - historicky Forest Journey voice strategy checkpoint; kanonicke hlasove pouceni zustava v `technical/matysek_f5tts_voice_workflow.md` a aktualni dalsi krok je v `ACTIVE_PROJECTS.md`.
- `handoffs/matysek_f5tts_bunny_voice_tool_checkpoint_2026_06_02.md` - historicky F5-TTS Bunny tool checkpoint; aktualni technicke pravidlo zustava v `technical/matysek_f5tts_voice_workflow.md`.
- `handoffs/matysek_scene_01_clearing_meeting_review_2026_06_01.md` - historicky Forest Journey scena 1 review checkpoint; stav scen a dalsi MMTX krok jsou prekryte aktualnim radkem `MMTX` v `ACTIVE_PROJECTS.md`.
- `handoffs/matysek_scene_01_sunny_voice_and_ending_2026_06_03.md` - historicky Forest Journey scena 1 Sunny/ending checkpoint; produkcni retest a dalsi prace jsou prekryte aktualnim radkem `MMTX` v `ACTIVE_PROJECTS.md`.
- `handoffs/mmtx_scene02_start_help_cleanup_2026_06_26.md` - MMTX Forest Journey 2 / Sunny's Lost Nuts: odstranene velke start tlacitko, kompaktny layout bez samostatneho zahlavi/zapati, prvni klik do sceny odemyka audio a hlavni vstupni napoveda je jen cesky v `docs/` i mirroru `MatysekANJ/web_mmtx/`.
- `handoffs/mmtx_scene03_journey_to_lake_publish_2026_07_01.md` - MMTX Forest Journey 3 / Journey to the Lake: publikacni checkpoint sceny 3 s havranem, konem, pumpou, 6 obrazovymi fazemi, napojenim ze sceny 2, MP3 hlasy a rozsirenym slovnickem.
- `handoffs/family_video_organizer_ui_prototype_2026_05_22.md` - FamilyVideoOrganizer: prvni lokalni webovy UI prototyp je v `docs/family-video-organizer/`, umi tabulku, filtry, autosave, export JSON a video modal; dalsi krok je realny soukromy datovy balicek mimo git.
- `handoffs/family_video_organizer_package_ready_2026_05_29.md` - FamilyVideoOrganizer: realny lehky ZIP pro dceru byl podle Mily 2026-05-29 poslany; generator `tomik_family_video_package.py` vytvari `videos-data.js`/nahledy, UI ma Safari fallback, zelene tlacitko videi a zamykani radku; dalsi krok je pockat na dcerin export JSON.
- `handoffs/family_memory_usa_2019_review_recovery_2026_06_04.md` - [PRIPOMENOUT] Family Memory Films / USA 2019: po ukoncenem terminalu byl dohledan a nechan dobehnout review prep; intake ma 2742 souboru, review ma 2742 ocekavanych nahledu, 81 blokovych a 29 dennich contact sheetu, 10 problemovych videonahledu s placeholderem; vedlejsi ` 2.jpg` duplicity byly po potvrzeni smazany; po Milove denni editaci vznikl blokovy `block_review.csv` a `block_review_form.html`; pro smes `2019-08-05` vzniklo item-level review 280 videi, prvni pruchod priradil 226 a 54 nechal mimo zpracovani; pri navazani brat nejnovejsi `~/Downloads/block_review*.csv` a `~/Downloads/mixed_2019-08-05_review*.csv` jako zdroj pravdy.
- `handoffs/family_memory_usa_2019_tomik2_overview_checkpoint_2026_06_05.md` - [PRIPOMENOUT] Family Memory Films / USA 2019: master prehled ve stylu `Tomik 2` je hotovy mimo git, predstrihovy formular `film_selection_form.html` je vygenerovany a Adamuv prvni rating `A=406`, `B=913`, `C=1369` je aplikovany; dalsi krok je rucni korekce ve formulari a pri navazani brat nejnovejsi `~/Downloads/film_selection_review*.csv` jako zdroj pravdy.
- `handoffs/pozustalost_start_2026_05_30.md` - [PRIPOMENOUT] Pozůstalost / rodinný nouzový balíček založen jako priorita 1: další krok je projít návrh s Mílou a Janou, vybrat MVP, založit soukromé šablony mimo git a právní část ověřit s notářem.
- `handoffs/backup_usb_hub_restart_checkpoint_2026_06_03.md` - záloha Samanthy: původní hub selhal, přes přímější propojku a Pythonový fallback vznikl úspěšný snapshot `20260603_175327`; potvrzeně byly smazány nedokončené snapshoty `20260603_162647`, `20260603_163709` a starý nafouknutý `20260529_225518`.
- `handoffs/neuberk_interier_design_start_2026_05_31.md` - Neuberk interiér design / Kačenka: založen soukromý prostor mimo git pro fotky, plánky, rozměry a návrhy; další krok je dodat podklady a vyplnit brief místnosti.
- `handoffs/neuberk_kacenka_zapadni_stena_prekres_2026_06_03.md` - Neuberk / Kačenka: soukromý pracovní a čistý překres jedné stěny je hotový mimo git; další krok je složit dostupné podklady do jednoduchého 2D pochopení místnosti.
- `handoffs/neuberk_kacenka_library_concept_pause_2026_06_04.md` - Neuberk / Kačenka: práce na designu je dočasně přerušená; mimo git jsou hotové soukromé stěnové/půdorysné podklady a první vizuální koncept knihovny, čtecího koutku, dětského koutku a gauče u dveří; další krok je zkontrolovat poslední koncept proti půdorysu.
- `handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md` - aktualni network/reconnect stav: domaci watchdog ukazal 29 vypadku za 30 minut a casto selhal i ping na gateway `192.168.1.1`; pracovni Wi-Fi retest mel 319/320 OK, takze dalsi krok je domaci router/Wi-Fi/ruseni/linka a retest po zasahu.
- `handoffs/network_https_reconnect_diagnostic_2026_05_21.md` - historicky network mezistav: prvni HTTPS failure diagnostika a vznik `scripts/network_watchdog.py`; prekryto novejsim handoffem `network_domaci_wifi_router_vs_mac_2026_05_21.md` a kanonickym stavem v `infrastructure/macos_network_recovery.md`.
- `handoffs/payment_sms_reminder_tool_done_2026_05_21.md` - Platebni SMS workflow je hotovy: `inspect_payment_page_for_reminder` read-only overi splatnost z HTTPS stranky/API bez plne URL/tokenu, `save_payment_sms_reminder` ulozi overovaci nebo platebni pripominku a `save_payment_case_document` ulozi lokalni fakturu/prilohu do `data/private/payment_cases/`.
- `handoffs/mobile_document_scan_shortcuts_and_processing_2026_05_26.md` - [PRIPOMENOUT] dokumentovy vault: iPhone zkratka `Skenovat dokument pro Samanthu v4` uklada vice stran do `SamanthaDocumentInbox`, zkratka pro zpracovani vytvari `process_request.json`, `scan_mobile_document_inbox` a `prepare_mobile_document_batch` jsou implementovane a realny batch `scan_B` byl pripraven do pracovního PDF; dalsi krok je potvrzovany finalni import do vaultu.
- `handoffs/mobile_document_processing_raw_bw_classification_2026_05_27.md` - [PRIPOMENOUT] dokumentovy vault: hlavni nova cesta je ScanDocu pro GPT PDF z Downloads; prototyp Samantha Cockpit bezi a oprava samostatneho okna ScanDocu je overena; dalsi krok je ranni realny test dalsiho dokumentu.
- `handoffs/document_management_scandocu_reimport_checkpoint_2026_05_28.md` - [PRIPOMENOUT] dokumentovy vault: ScanDocu umi revidovat uz ulozene dokumenty, lepe cte metadata vozidel a preskakuje stare sifrovane varianty po ulozeni odemcene kopie; dalsi krok priorita 1 je po nove kopii v Downloads pokracovat dokument po dokumentu ve znovuukladani/revizi uz ulozenych priloh.
- `handoffs/document_management_cockpit_voice_command_inbox_2026_05_29.md` - dokumentovy vault/cockpit: koncept hlasoveho nebo textoveho command inboxu z iPhonu pres iCloud, read-only intent routing pro dokumenty/e-maily/statusy a potvrzovaci brany pro tisk, archivaci, mazani a odesilani.
- `handoffs/document_management_morning_action_plan_2026_06_04.md` - [PRIPOMENOUT] ranni akcni plan dokumentu po stabilizaci Cockpitu: zacit read-only mapovanim zero-text/OCR a re-review kandidatu, potom panel/report `Dokumenty k revizi`; navazujici oblasti jsou jednotny intake Downloads/e-mail/mobilni sken, cases/vazby, ergonomie klasifikace a due-date -> reminders.
- `handoffs/cockpit_web_apps_checkpoint_2026_05_29.md` - Samantha Cockpit: pridane tlacitko Webove aplikace, katalog aplikaci, samostatne popup otevirani aby zavreni aplikace nezavrelo Cockpit; lokalni commity Cockpitu a UTF-8 opravy jsou hotove, dalsi krok je pripadny push.
- `handoffs/cockpit_dashboard_terminal_launch_checkpoint_2026_05_29.md` - historicky Samantha Cockpit dashboard/terminal launch checkpoint: provozni dashboard, stavovy panel, akcni tlacitka, Samantha chat a Codex CLI; tehdejsi repo nesoulad je uzavreny a checkpoint zustava jen jako historicky popis funkce.
- `handoffs/cockpit_global_hotkey_agent_2026_06_01.md` - Samantha Cockpit: globalni klavesova zkratka pres vlastni Swift/Carbon hotkey agenta a LaunchAgent; Finder Services cesta byla nespolehliva, novy agent funguje po rucnim testu `Ctrl + Option + Cmd + C`.
- `handoffs/document_vault_next_physical_print_and_downloads_intake_2026_05_22.md` - dokumentovy vault: fyzicky tisk byl Milou overen na TXT dokumentu o zkratkach; dalsi plan je klasifikace/vazby mezi dokumenty a potvrzovany intake ze slozky Stazene/Downloads do inboxu.
- `handoffs/media_image_resize_utility_done_2026_05_20.md` - Obecna utilita `app/media/image_resize.py` je hotova a overena na lekarne; dalsi krok je pri pouziti na slovniky nejdriv udelat preview a zvolit cilovou velikost.
- `handoffs/vocabularyit_mapping_applied_2026_05_20.md` - VocabularyIT/PictNew finalni stav aktualni vlny: `Pict/mapping.json` byl po schvalenem preview aktualizovan, audit je cisty a git checkpoint existuje jako `851b347 Apply VocabularyIT picture mapping updates`.
- `handoffs/vocabularyfr_web_trainer_checkpoint_2026_06_04.md` - VocabularyFR Web Trainer pro Janu: webový MVP prototyp je hotový a commitnutý jako `da93eba Add VocabularyFR web trainer prototype`; další krok je deploy/checklist pro předání `VocabularyFR/web/` Janě a rozhodnutí macOS helper vs. Pythonista/iCloud test.
- `handoffs/vocabularyfr_jana_images_archive_2026_06_07.md` - VocabularyFR pro Janu archiv: macOS app/Pict opravy, 39 novych obrazku, mapping 841 zaznamu, finalni audit 346/347 konkretnich obrazku, jediny fallback `chez -> preposition` a oprava `school.PNG`/hospital.
- `handoffs/neuberk_kacenka_south_wall_v6_geometry_checkpoint_2026_06_07.md` - Neuberk Kacenka: checkpoint jizniho pohledu v6; soukrome koncepty maji opraveny pricny snizeny strop, tram smerujici k vychodni stene, komin u dveri a gauc za kominem; dalsi krok je rucni porovnani posledniho kandidata s realnymi fotkami a potom pudorysovy check.
- `handoffs/samantha_agent_rag_search_memory_ranking_2026_05_19.md` - historicky RAG mezistav z kvetna; aktualni kanonicky stav je v `handoffs/workstreams/project-samantha-agent-rag.md` a `tvbcp/workstreams/project-samantha-agent-rag.md`.
- `handoffs/session_recovery_autosave_2026_05_18.txt` - handoff ke konverzaci o navazovani po vypadku, `screen`, prikazu `samantha`, `codex resume` a autosave session logu po 10 minutach.
- `handoffs/test_kratky_handoff_2026_05_18.md` - testovaci handoff s prioritou 3 bez pripomenuti pri startu, overeni pravidla pro kratky handoff.
- `handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md` - Seznam e-mail: prvnich 500 vysledku pro pojisteni/smlouvy ma worklist, 34 UID slozek a 129 lokalne stazenych priloh v `data/private/email_seznam/`; navazovat jen podle potvrzovaneho read-only/document workflow.
- `handoffs/email_seznam_readonly_provider_2026_05_22.md` - aktualni e-mailovy stav: iCloud read-only vrstvy existuji, Seznam Mail read-only provider a `Unified Inbox` jsou implementovane, lokalni Seznam `.env` je vyplneny a smoke test hlavicek 2026-05-23 prosel bez vypisu predmetu/adres.
- `handoffs/email_outbound_sms_triage_next_2026_05_28.md` - historicky e-mailovy outbound/SMS triage checkpoint: e-mail outbound uklada kopii do iCloud Sent Messages, `send_confirmed_sms_rcs` ma potvrzovaci branu a kontrolu `is_sent/is_delivered/error`; překryto aktuálním e-mailovým stavem a VoiceBridge potvrzovacím kontraktem.
- `handoffs/email_processing_cleanup_and_documents_next_2026_06_03.md` - historicky Email Processing cleanup checkpoint: Work Queue ma oddelene zpracovani, presun do kose a trvale smazani z kose; překryto aktuálním stavem `iCloud Mail read-only / Email Cases`.
- `handoffs/document_management_cockpit_case_health_checkpoint_2026_06_04.md` - [PRIPOMENOUT] Document Management / Cockpit checkpoint: hotove `Dokumenty k revizi`, cases/vazby, klasifikace, terminy v dokumentech a detail case v2 s pripominkami, terminovymi kandidaty, konflikty a `case_health`; dalsi krok je rucni UI retest detailu case a potom rozhodnout OCR/re-review vs. sjednoceny intake.
- `handoffs/email_processing_cockpit_decision_ui_2026_06_01.md` - historicky Email Processing decision UI checkpoint: 7denni e-mailovy prehled jako rozhodovaci karty; potvrzovaci hranice cteni/stahovani/mazani zustavaji v aktualnim e-mailovem stavu.
- `handoffs/email_work_queue_detail_checkpoint_2026_06_01.md` - historicky Email Work Queue detail checkpoint: read-only detail, batch ulozeni do EmailArchiveVault a PDF import do private document vaultu; překryto aktuálním stavem e-mailové oblasti.
- `handoffs/email_work_queue_batch_filters_2026_06_14.md` - Email Work Queue ma obecne blokove filtry pro davkove zpracovani: Finanční správa, VAK, Faktury nad 2000 Kč, Faktury/e-shopy, PDF, velke PDF a Ostatni; davkove zpracovani posila jen aktualne vybrany blok.
- `handoffs/scandocu_email_workqueue_owl_checkpoint_2026_06_15.md` - ScanDocu Review a e-mailovy checkpoint 2026-06-15: Work Queue filtruje odchozi slozky a lepe klasifikuje faktury vs. Financni spravu; ScanDocu ma `Jina oblast...`, soukromy registr oblasti a opravu dlouhych review tokenu; sovi text pro 2026-06-16 je aktualizovany.
- `handoffs/document_email_attachments_scandocu_metadata_checkpoint_2026_06_16.md` - Document Vault checkpoint: Email Work Queue umi ukladat a nahledovat PDF i obrazkove prilohy, ScanDocu umi znovu otevrit dokument vraceny do `needs_review`, oblast `petkovy-65` byla v aktivnich private datech sjednocena na `petkovy-56` a klasifikace hlasi 167/167 kompletni metadata.
- `handoffs/email_work_queue_batch_tomorrow_2026_06_01.md` - historicky Email Work Queue batch checkpoint: batch endpoint, PDF prilohy do document vault fulltextu a kos s potvrzovaci vetou; překryto aktuálním stavem e-mailové oblasti.
- `handoffs/email_weekly_overview_resume_2026_06_01.md` - historicky Email management read-only prehled hlavicek a soukromy resume detail; navazovani pres konkretni UID je překryto aktuálními e-mailovými workflow pravidly.
- `handoffs/iphone_shortcuts_najit_auto_done_2026_05_23.md` - hotovy checkpoint iPhone zkratek: Shortcuts Playground plugin pro Codex je nainstalovany, `Najit auto v3.shortcut` funguje u Mily i Jany a kanonicke pouceni je v `technical/iphone_shortcuts_playground.md`.
- `handoffs/iphone_shortcuts_quick_notes_continue_2026_05_23.md` - [PRIPOMENOUT] zitrejsi navazani na iPhone zkratky: quick notes zkratka funguje, Samantha umi ocislovany seznam/detail poznamek a dalsi krok je vybrat dalsi malou zkratku nebo akci z poznamky.
- `handoffs/iphone_shortcuts_freeze_infrastructure_layer_2026_05_25.md` - aktualni zmrazovaci handoff pro iPhone Shortcuts / Mobile Input Layer: doplneny puvodni seznam 7 kandidatu na zkratky, stav hotovych zkratek, bezpecnostni hranice a pravidlo nepokracovat bez vyslovneho navratu.
- `handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md` - doslovne ulozeny feedback k QN #13 systemova mapa, QN #10 ziva znalostni databaze a QN #4/#6 bezpecny akcni inbox; ceka na brzké zapracovani.
- `handoffs/quick_notes_action_inbox_preclassification_2026_06_19.md` - Quick Notes akcni inbox: read-only predklasifikace QN na pripominku/projekt/tool/ukol/citlivou akci/archiv/napad, CLI `--status` a Samantha tool `quick_notes_action_status`; dalsi krok je rucne vybrat prvni potvrzovanou akci.
- `handoffs/quick_notes_triage_no_unclassified_2026_06_23.md` - Quick Notes Cockpit triage fix: stav QN uz pri fallbacku neukazuje `Nezařazeno`, ale pouzije novou akcni predklasifikaci; QN #42 typu knihovna / URL clanek se zobrazuje jako `archiv/znalostní databáze`.
- `handoffs/stories_batch_2026_05_14.md` - batch více pohádek z jednoho chatu, rozdělený do samostatných story memory souborů.
- `handoffs/chatgpt_handoff_2026_05_14.md` - kompaktní předání po dlouhém ChatGPT vlákně, včetně promptu pro Codex a promptu pro nový ChatGPT chat.
- `handoffs/mmtx_web_handoff_2026_05_14.md` - handoff k webové verzi MMTX v `docs/`, hotovým scénám OwlGarden a HouseBunny, audio strategii a mirroru.

## Technical Rules

- `technical/project_tvbcp_rules.md` - kanonicke pravidlo projektovych TVBCP:
  zalozit jen po dohode Mily a Adama pro vetsi projekt nebo ulohu; drzet
  rozhodnuti, milniky, testy a rizika, ne plny chat; male opravy vlastni TVBCP
  nepotrebuji.

- `technical/naming_conventions.md` - názvosloví: Samantha je běžný ChatGPT, Codex je pracovní agent v projektu, Codex CLI je terminálový nástroj.
- `technical/system_project_audit_generator_design.md` - navrh opakovatelneho generatoru systemoveho auditu projektu, toolu a vrstev: vstupy, bezpecnostni hranice, MVP sekce, datovy model, registrace a testy.
- `technical/samantha_growth_rules.md` - [PRIPOMENOUT] A1+ deset preventivnich pravidel pro rust Samanthy, tri maximalne prioritni body po commitovem uklidu a handoff compression per project; po velkem commitu nabidnout cisty stul, pouceni z uklidu a jasnejsi rezim vyvoje.
- `technical/samantha_cultural_metaphors.md` - kulturni/prakticke metafory pro Samanthu, vcetne `samyce/samice`: agent ma hledat lidsky zamer i pri preklepu nebo nepresnem vstupu.
- `technical/story_memory_rules.md` - pravidla pro ukládání pohádek do memory: ukládat plný finální text, ne jen shrnutí, a sledovat clean verzi pro předčítání.
- `technical/codex_permissions_preferences.md` - preference pro navrhovani trvalych Codex povoleni u rutinnich prikazu, vcetne TTS a git publikace.
- `technical/session_recovery_rules.md` - pravidla pro navazani po vypadku SSH/Codexu: `screen`, `samantha`, `codex resume`, handoff soubory a primerene checkpointovani dlouhych ukolu bez zbytecne rezie u drobnosti.
- `technical/capability_routing_rules.md` - obecne pravidlo pro vsechny projekty: lidsky pokyn -> pochopeny zamer -> registrovana schopnost/tool/workflow -> bezpecnostni rozsah -> potvrzeni podle rizika + volba miry workflow rezie.
- `technical/global_safety_brake.md` - globalni brzda pro uzky okruh vysoce rizikovych destruktivnich/systemovych akci; bezna hlasova a read-only prace ma zustat plynula, ale mazani, tajemstvi, reset/force push, private data, system config a podobne kroky vyzaduji presnou potvrzovaci vetu.
- `technical/codex_remote_approval_notice.md` - [PRIPOMENOUT] pravidlo pro vzdalenou praci z iPhonu/SSH: pred systemovym Codex potvrzenim zapsat lidskou kartu `Codex čeká na potvrzení` do Cockpitu pres `scripts/codex_approval_notice.py set` vcetne `--risk`; karta ukazuje co chce Codex udelat, proc, riziko a co ma Mila udelat; nejde o vzdalené zmacknuti interniho Codex tlacitka.
- `technical/system_reports.md` - prehled dostupnych systemovych reportu Samanthy, jejich ucelu, spusteni a pravidel pro pridavani dalsich reportu.
- `technical/large_context_intake.md` - pravidla a lokalni ignorovany adresar pro velke podklady k prostudovani, vcetne budoucich exportu chatu, bez commitovani soukromych dat.
- `technical/media_review_form_workflow.md` - [PRIPOMENOUT] znovupouzitelny workflow pro lokalni formular nad fotkami/videi: thumbnails, editace CSV, autosave do `localStorage`, tlacitko `Přehrát video` pres read-only lokalni server, export/autosave CSV a pravidlo brat nejnovejsi stazene CSV jako zdroj pravdy.
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
- `NETWORK_RECOVERY_CARD.txt` - offline nouzova karta pro pripad, ze nejde internet a nejde se dostat do ChatGPT; lze vypsat pres `scripts/network_recovery_card.sh`.

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
