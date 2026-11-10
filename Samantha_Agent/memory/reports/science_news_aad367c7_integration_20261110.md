# Izolované převzetí ScienceNews a nutná kompatibilita pošty

Stav: 2026-11-10 10:09 CET. Míla výslovně požádal nasadit Datův nový commit `aad367c7e7d8abb84ce37e8a716c371043fa3d90`.

## Co je připravené

- Izolovaná větev `will/science-news-20261110` nad již vydaným `8c83e93b`. Hlavní main i Datův worktree zůstávají beze změny; hlavní config stále neobsahuje science_news_editor.
- Celý český překlad je podmínkou Uložit v UI i serveru. Prokazatelně nezahájená validace uvolní request ID, nejistá starší operace nikoli. Existující follow/dismiss fungují dál.
- Jednorázové vložení již hotového překladu a návrh aktivace mají samostatné registrované operace. V tomto převzetí se neprovádějí: žádný nový překlad, uložení článku, opakování Datova save ani instalace pátečního LaunchAgentu.
- Připravovaná role science_news_editor je přidaná pouze v izolované pracovní kopii. Všechny dosavadní role jsou JSON-shodné s main. Přijímací report Data zůstává beze změny; soukromý text ani provozní účtenky nebyly kopírovány.
- Pět konfliktů vyřešeno v aktuálním/chronologickém handoffu, technické paměti a snapshotu zachováním aktuálních funkcí i obou historií. Nový Datův odkaz LL-114 je sjednocen s již přiděleným LL-121.
- 134 cílených testů PASS; zahrnují 16 Node scénářů, HTTP ochranu překladu, cached save, účet ChatGPT, rozpočtové rezervy, aktivační idempotenci a e-mailový service controller (vše s fixture runnerem).
- Plná izolovaná brána PASS: 3405 testů / 31 SKIP (641,430 s); log: `logs/science_news_aad367c7_full_gate_20261110.log`.
- První plný běh měl 3405 testů / 31 SKIP a jedinou chybu prostředí: recovery status správně odmítl symlink `.venv` (`state_alias_refused`). Symlink vytvořený pro validaci je zachován v ignorovaném logs; izolované `.venv` je nyní skutečný adresář, sdílí jen interpret/knihovny, žádný provozní stav. Žádný produkční kód ani aktivace recovery nebyly upraveny. Čtyři cílené ClockAndLaunchd testy následně PASS (0,644 s); opakovaná celá brána PASS: 3405 testů / 31 SKIP (641,430 s). První výsledek zůstává v `logs/science_news_aad367c7_full_gate_first_attempt_20261110.log`, oprava prostředí v `logs/science_news_aad367c7_environment_recheck_20261110.log`.

## Doložená překážka nasazení

Skutečná vlastněná hodinová služba je installed/owned/loaded/enabled na `617f3e0d8669255238d2dd56c93cfbf037dc1a4a`. Její `config/agent_roles.json` je symlink na živý soubor hlavního checkoutu. Samostatný proces se skutečným instalovaným parserem a dočasným kandidátním JSON skončil AgentRoleError: science_news_editor není v jeho KNOWN_ROLES. Živý config, nastavení služby, IMAP a modely přitom nebyly změněny nebo volány. Doklad `logs/science_news_aad367c7_role_compat_20261110.log` v hlavním checkoutu.

Převzetí nové role přímo na main by proto zopakovalo doložený výpadek hodinové pošty. Plná brána hlavního parseru tuto skutečnost nenahrazuje.

## Přesné pořadí dokončení

1. Po novém výslovném systémovém potvrzení registrovaně pozastavit vlastní poštovní službu, zachovat její stav/nastavení/politiky, připravit a provést upgrade **617f3e0d → již publikovaný 8c83e93b**. Běžící modely a existující pošta se nepřepisují; starý release a servisní záloha se zachovají. Controller při busy workeru selže před přepnutím. Příprava/upgrade se neopakují při nejasném výsledku.
2. Ověřit vlastnictví, health, zachování dřívějších položek/nastavení/rolí a načtení kandidátního JSON skutečně nově instalovaným parserem. Teprve po tomto důkazu může být science binding zveřejněný.
3. Fast-forward čistého hlavního main na připravený merge checkpoint, zarovnání pouze čistých profilových kopií a již požadované registrované Terra p+n pro `project-knowledge-library` přes `submit_release(wait=True)`. Následně účtenka, HTTP/servírovaná ochrana, GitHub a CI.
4. Páteční služba stále zůstává vypnutá. Její 15 kreditů/job, 100/měsíc a vlastní instalace vyžadují samostatnou dohodu; souhlas s kompatibilitou pošty je nezapíná.

## Potřebné oprávnění

`EmailServiceController.upgrade` výslovně vyžaduje přesnou globální větu, protože mění vlastněný systémový LaunchAgent mimo projekt. Předchozí potvrzení pro dřívější opravu pošty nebylo paušální povolení tohoto nového přepnutí. Zdroj: `memory/technical/global_safety_brake.md` (systémová konfigurace/LaunchAgents) a `app/email/service_control.py`.

Před žádostí bude viditelná karta podle `codex_remote_approval_notice.md`. Do té doby zůstává živá pošta zapnutá na původní kompatibilní konfiguraci a nasazení aad367c7 není tvrzené.


## Aktualizace 2026-11-10 10:58 CET

Systémové potvrzení přijato, registrovaný upgrade pošty 617f3e0d→8c83e93b dokončen a živě ověřen. Teprve potom main převzal 31a59e0c a nový binding. Původní blokátor výše je vyřešený. Navazuje společné vydání s prioritní kalendářovou opravou; páteční automatika se nezapíná. Důkazy reports/email_science_role_upgrade_20261110.md a reports/calendar_edit_alarm_order_recovery_20261110.md.
