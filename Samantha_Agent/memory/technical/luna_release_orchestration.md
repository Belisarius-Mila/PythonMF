# Předání p+n celého balíčku vykonavateli

Rozhodnutí Míly 2026-10-17: hlavní Adam dokončí vývoj a commity; po samostatném
p+n převezme Luna celý schválený balíček. Výsledek se vrací do stejné konverzace
hlavního Adama. Rozšíření téhož dne platí pro všechny kanonické vývojové
proudy portálu (aktuálně 33), včetně přímé terminálové relace.

## Technologie a rozsah

- Stávající Codex App Server, centrální role `release_executor` v
  `config/agent_roles.json`, krátké nové dočasné vlákno. Nemění se hlavní
  model uživatele ani komunikační architektura.
- Luna dostává pouze projekt, koncové commity rozsahu, počet commitů, režim
  a názvy chráněných služeb. Nedostává celou historii, přihlašovací údaje,
  soukromá data ani oprávnění opravovat kód či systém.
- Jediný read-only modelový tah přebírá přesný cíl strukturovanou odpovědí.
  Stávající serverové Python postupy provádějí plnou publikační bránu,
  přesný GitHub batch push a registrované nasazení: běžící runtime Samanthy
  s restartem a smoke 5/5, nebo společný Pages publisher s přesným deployment
  SHA a HTTP 200 konkrétní webové aplikace.
- Celý rozsah mezi GitHub main a lokálním main je jeden balíček. Počet
  commitů není omezený na jeden. Je-li main již přesně na GitHubu, proběhne
  plná brána a registrované nasazení bez dalšího push.
- Soukromý záznam a oddělený proces přežijí restart Cockpitu i zavření karty.
  Každý požadavek má vlastní účtenku; předchozí se nepřepisují ani nemažou.

## Použití

1. Dokončit vývoj, ověření, paměťový zápis a lokální commity.
2. Ve vybraném vývojovém proudu použít `p+n`, `p*n`, `vše p+n` nebo tlačítko
   v Práci. Otázky obsahující p+n nejsou příkazem. Archivovaný proud nelze
   použít k novému vývojovému předání.
3. Read-only audit ověří čistotu a zarovnání profilů, aktuální GitHub rozsah,
   cílové nasazení a dostupnost původního vlákna Adama.
4. Uživatelské potvrzení se vztahuje na zobrazený přesný balíček. API navíc
   vyžaduje `POTVRZUJI PREDANI P+N LUNE`, oba auditované commity,
   `expected_workstream_id`, `expected_deployment_target` a request ID.
   Navíc vyžaduje `expected_executor` z auditu: roli, model, úsilí a otisk
   schválené politiky. Stejný commit nelze po potvrzení přesměrovat na jiný
   projekt, cíl nebo model.
5. Výsledek je vidět ve stejné konverzaci. Po ostrém dokončení či překážce
   hlavní Adam dostane strojovou účtenku do původního vlákna. Jeho kontrolní
   tah má read-only sandbox bez sítě a nesmí opakovat vývoj ani publikování.

Zkouška bez publikování volá skutečnou Lunu a read-only ochranné kontroly;
nevolá push/deploy ani nový kontrolní tah hlavního Adama. Karta zobrazí výsledek.

V přímé terminálové/Codex relaci hlavní Adam volá přímo registrované
`submit_release(payload, wait=True)`. Nevytváří nativního modelového pomocníka.
Stejný vstup obsluhuje portál přes existující `/luna-release/start`, kde je
čekání asynchronní a návrat zůstává v původním vlákně. Jediná Luna převezme
balíček uvnitř workeru; její roli/model/úsilí vybírá program z centrálního JSON.
Krátký payload obsahuje confirmation=CONFIRMATION, client_message_id (stabilní
pro jeden požadavek), expected_workstream_id, expected_local_head (celý SHA
schváleného lokálního commitu) a dry_run (bool). Caller nedoplňuje origin,
cíl ani model. Existující UI smí předat úplné auditované údaje; zůstávají závazné.
Program audit provede a při zamčeném startu znovu ověří přesnou shodu. Celý
rozsah čekajících commitů se nemění; jiný projekt/head/model se odmítne.

Pro nativní spuštění použít jeden programový běh (např. functions.exec s
programovým await na exec session), ne opakované modelové dotazy. `wait=True`
vrací až bezpečnou konečnou účtenku nebo timeout, sleduje přesné job ID.
Samostatné `wait_for_release(job_id)` také nic nespouští znovu. Změna current
pointeru nemůže přesměrovat čekání. Stejná identita požadavku vrací původní
účtenku i po úspěšném push; změna projektu, headu, režimu, kanálu nebo původního
portálového vlákna je odmítnutá. Timeout zachovává stav a neprovádí retry.
`start_release` a `start_terminal_release` zůstávají kompatibilní interní/starší
vstupy. Pro nový běžný postup se používá pouze submit_release.
V terminálu se neposílá zpráva do jiné konverzace. Během p+n se main nemění.

GitHub HTTPS push může jednorázově použít již ověřené přihlášení GitHub CLI
podle LL-060; bez změny globální konfigurace, nového přihlášení, tokenu v argv
nebo opakování push. Ostatní remotes zachovávají dosavadní transport.

## Stav panelu publikace — 23. 10. 2026

Panel Práce rozlišuje aktuální, čekající, blokovaný a neověřený stav.
Aktuální potvrzený main/GitHub a nasazení nezobrazují běžné tlačítko p+n;
v uzavřených dalších akcích zůstává vědomé opakování a diagnostika.
Pracovní změny zdroje blokují publikaci i přepínání proudů. Místní Xcode
podpis proto patří do ignorovaného LocalSigning.xcconfig bez target override.

Prezentace porovnává snímek aktivního proudu s čerstvým GitHub auditem.
Cizí proud, rozporné heads a neúspěšný audit jsou neověřené; nezastoupí je
starý origin/main nebo poslední globální účtenka. Pages vyžadují vlastní
potvrzenou webovou účtenku stejného proudu/commitu, nikoli stav Cockpitu.
Po dokončení se starý snímek obnoví. Čtecí obnova je dostupná i při chybě
stavu vykonavatele. Render panelu sám nikdy nespustí předání.

Explicitní p+n z textu a samostatné opakování dál používají stejný
submit_release, přesný audit, potvrzení a původní bezpečnostní brány.
Podrobnosti: [report opravy](../reports/human_adam_workstream_pn_fix_2026_10_23.md).

## Výměna modelu společné role

- Jediným aktivním nastavením je `config/agent_roles.json`; název modelu
  není zapsaný zvlášť v projektech ani v pokynech pro nativního pomocníka.
- Preferovaný model má přednost. Jen pokud chybí nebo není kompatibilní
  s požadovaným úsilím/textem, vybírá se v pořadí ze schválených kandidátů.
  Default účtu, novější název ani katalogové `upgrade` neudělují oprávnění.
- Každý kandidát musí mít `cost_review` a `dry_run_evidence`. Jde o doložené
  lidské cenové posouzení, ne automatický výpočet ceny z katalogu. Současná
  Luna zachovává Mílou zvolenou rozpočtovou roli a doložené skutečné zkoušky.
- Nového kandidáta nejprve cenově posoudit a výslovně určit pro test. Volání
  `probe_release_executor_candidate(model, reasoning_effort)` dostane jen
  pevný syntetický vstup do dočasného read-only vlákna bez sítě. Nikdy nezmění
  nastavení role, nespustí job, push ani nasazení. Vrací redigovaný důkaz.
- Teprve po úspěchu zapsat kandidáta s oběma důkazy do centrálního nastavení,
  podle potřeby změnit preferenci, provést kontroly/commit a schválené p+n.
  Po tomto jediném nastavení ho používají všechny vývojové proudy.
- Audit i soukromá účtenka zmrazí roli/model/úsilí/otisk. Změna politiky před
  publikací nebo jiný model v odpovědi zastaví běh; uvnitř jobu se nepřepíná.
  Staré účtenky zůstávají čitelné; nový worker bez zmrazeného modelu nezačne.
- Výběr role neprovádí modelový tah. Chybí-li schválený kompatibilní model,
  předání se zastaví před publikováním a vrátí bezpečné vysvětlení.

## Registrované cíle

- Běžné proudy používají stávající společné nasazení runtime Samanthy/Cockpitu.
  To zahrnuje například infrastrukturu, Human–Adam, Knihovnu i editor filmu.
- `project-mmtx`, `project-to-be-to-have` a `project-colors-and-numbers`
  používají společný existující PythonMF Pages publisher. Poslední dva mají
  vlastní HTTP smoke cesty `to-be-to-have/` a `colors-numbers/`.
- Zdrojem jsou serverový katalog a registrované vazby `PAGES_PROJECT_PATHS`.
  Nový běžný proud nepotřebuje zvláštní seznam povolených ID; nový druh
  produkčního cíle musí mít registrovaný adapter. Neznámý cíl se zastaví.
- Nejde o univerzální vydávání samostatných klientů, instalaci na zařízení
  nebo aktualizaci služby Camino. Jejich specifické vydání zůstává samostatnou
  operací s vlastním oprávněním; běžné p+n tyto služby nepřepíná.
- Pravidla projektu, handoff/TVBCP a jeho cílené kontroly plní hlavní Adam
  před commitem. Luna přebírá hotový rozsah a server vynutí plnou publikační bránu.

## Ochrany

- Jen kanonický Cockpit. Uživatelské payloady nemohou měnit cíl služby,
  cestu workspace, model, callback URL ani cestu soukromé účtenky.
- Během předání jsou další Human–Adam mutace a samostatný restart zablokované.
  Interní kroky autorizuje soukromý token svázaný s úlohou a přesnou fází;
  veřejný stav token nikdy nevrací.
- Cíl nasazení pochází ze zmrazené účtenky, ne z nového obsahu main ani
  klientského payloadu. Původní brány odmítnou změnu před i během operace.
- Před/po se čtou vlastněný Camino proces, hash konfigurace a Serve,
  jediný čerstvý trvalý autosave a jeho nastavení. Žádná změna těchto služeb,
  originálů, filmů, záloh nebo sítí není součástí tohoto workflow.
- Stejné request ID nespustí druhou úlohu. Cross-process lease povolí právě
  jednoho vykonavatele. Při nejistém push se automaticky nepokračuje; po
  přerušení HTTP při restartu se pouze ověří nový proces, restart se neopakuje.
- `requested`/`uncertain` nejsou důkaz neprovedení. Push a nasazení mají
  samostatné potvrzené stavy. Chyba se vrací Adamovi se zachovanou účtenkou,
  bezpečným důvodem a fází; hlídání přerušeného procesu nepřepisuje souběžně
  dokončený výsledek.
- Návrat nezakládá nové vlákno a nesmí se znovu odeslat při nejistém doručení.
  Při chybě obnovy zůstává viditelný stav vyžadující ověření.

## Ověření a zavedení

- Skutečná Luna přijala syntetický sedmicommitový balíček a přesný SHA;
  samostatný suchý běh celého vykonavatele prošel i skutečnými read-only
  ochranami Camino/autosave. Bez publikování nebo změny hlavního modelu.
- Důkazy: `logs/luna_release_live_probe_20261017.log`,
  `logs/luna_release_live_dry_run_20261017.log` a testové logy.
- Skutečný návrat přes App Server prošel v oddělené syntetické konverzaci:
  stejný thread, potvrzené doručení, zachovaný testovací model a read-only tah;
  provozní konverzace se nezměnila. `logs/luna_release_live_return_20261017.log`.
- Testy pokrývají více commitů, změnu SHA, nonce/fáze, souběh, nejistý push,
  přerušení restartem, zachování původního vlákna, read-only návrat a souběžné
  dokončení při kontrole přerušeného procesu. Závěrečná regresní sada 27 testů
  PASS: `logs/luna_release_race_targeted_20261017.log`.
- První verze pro Cockpit: plná brána 1993/1993 PASS, bez přeskočení; unit část 267,315 s.
  `logs/luna_release_full_gate_20261017.log`.
- Obecné rozšíření: 286 cílených integračních testů PASS, včetně všech 33
  vývojových proudů, potvrzeného projektu/cíle, již odeslaného main,
  Pages bez restartu, HTTP cesty konkrétní aplikace a starého MMTX kontraktu.
  `logs/luna_general_integration_20261017.log`.
- Skutečná Luna a skutečné read-only ochrany prošly v oddělených syntetických
  suchých bězích pro `misc-unclassified-development` (5,29 s) a `project-mmtx`
  (5,19 s), po 7 commitech. Žádná produkční úloha ani publikace nevznikla.
  `logs/luna_general_live_dry_run_20261017.log`.
- Závěrečná plná brána obecného rozšíření: 2011/2011 PASS, bez přeskočení,
  unit část 263,223 s. `logs/luna_general_full_gate_20261017.log`.
- Míla následně schválil implementaci společné modelové role a p+n celého
  připraveného balíčku. První zavedení používá existující potvrzené GitHub/
  Cockpit operace; u runtime jobu s neprázdným balíčkem není potřeba nová
  interní route pro Pages nebo již zarovnaný main.
- Provozní výsledek publikování je mimo Git: autoritou je soukromá účtenka
  vykonavatele a poslední serverová deployment účtenka. Při navázání ověřit
  `GET /api/human-adam/luna-release/status`, `GET /api/human-adam/status`
  (pouze redigovaný deployment souhrn) a GitHub batch audit. Samotný tento
  vývojový checkpoint neprohlašuje budoucí nasazení za ověřené.
- Centrální modelová role: 169 integračních testů a plná brána 2024/2024
  PASS, bez přeskočení, unit část 265,823 s. Skutečný suchý běh role 6,8 s
  i samostatný kandidátský probe prošly bez publikování. Důkazy
  `logs/executor_role_integration_20261017.log`,
  `logs/executor_role_full_gate_20261017.log`,
  `logs/executor_role_live_probe_20261017.log`,
  `logs/executor_candidate_live_probe_20261017.log`.
- Fyzická iPhone/Safari přejímka zůstává samostatným krokem.

Implementace: `app/communication/luna_release.py`, `luna_release_worker.py`,
nové registrované routy Cockpitu, úzké napojení chatu a návrat do session hubu.
Kanonický stav a důkazy patří do handoffu/TVBCP `project-cockpit`.

## Schválený pilot měření p+n (2026-10-17)

- Číselné počítadlo jedné výslovně zvolené nativní relace čte registrované
  `app.release_usage.native_usage_snapshot(thread_id)`. Žádný prompt, odpověď
  nebo obsah jiných relací se nevrací. Změna modelu/nastavení či reset
  počítadel blokují výpočet rozdílu.
- App Server receipt zachycuje poslední `thread/tokenUsage/updated.total`
  jako `thread_token_usage`; jde o celou historii vlákna, ne delta tahu.
  Převzetí používá nové ephemeral vlákno s jediným tahem, takže jeho total
  je přesná spotřeba převzetí. Veřejné `model_usage` propustí jen čísla.
- Neznámá telemetrie se nevydává za nulu. Cached input je podmnožina vstupu
  a reasoning podmnožina výstupu; při přepočtu se nepřičítají podruhé.
- Standard sazby jsou časovaný odhad podle
  https://learn.chatgpt.com/docs/pricing#token-rates (17. 10. 2026), ne
  vyúčtování ani důkaz zbývajícího limitu účtu. Zrychlení není odhadováno.
- Míla pro pilot výslovně schválil výjimku: první UI balíček provede Adam
  přímo registrovanými GitHub/deploy kroky, druhý běžným předáním Luně.
  Výjimka nemění centrální roli ani pravidla dalších vydání.
- Měří se od hotového commitu do závěrečného read-only ověření včetně
  předání, pomocníka, modelového převzetí a kontroly hlavním Adamem.
  Společná příprava a psaní závěrečného reportu zůstávají mimo oba intervaly.
  Bezpečný souhrn je logs/pn_cost_comparison_20261017.log; raw logy zůstávají
  soukromé, nezveřejňují se a nekopírují se do Gitu.

Měřený UI krok A: identita dokončeného balíčku. 68 UI testů a skutečná
účtenka v Node VM PASS; přímé p+n a srovnání dokládají uvedené runtime logy.

Měřený krok A potvrzen: d9e6e287, plná brána 2032/2032 a smoke 5/5;
2 369 937 tokenů, Standard odhad 7,27533 kreditu. Krok B (UI doložených
kontrol) má 68 UI testů a Node VM PASS. Jeho p+n a úplné souhrny včetně
režie hlavního Adama se ověřují v runtime účtence a uvedeném finálním logu.

## Opakování přes skutečný asynchronní Cockpit

Míla 2026-10-17 schválil nový pilot C po terminálovém A/B. Pro jeden nový
dokumentační commit se použije registrovaný start_release hlavního Cockpitu
s návratem do jeho již existujícího vlákna project-cockpit. Jde o výslovně
zadaný test portálové cesty; běžné terminálové předávání se tím nemění.

Během čekání stav čte deterministický observer, hlavní model nedělá polling.
Započítá se úvodní předání, jednorázová Luna, skutečný read-only callback
Cockpit Adama i terminálová závěrečná kontrola. Nový benchmark nepoužívá
nativního modelového pomocníka navíc. Původní model Cockpitu se nepřepíná;
případný rozdíl proti terminálovému Sol 6.1 bude ve výsledku výslovný.
Aktuální výsledek je v logs/pn_async_comparison_20261017.log a runtime
účtence. Historické A/B zůstává beze změn v původním souhrnu.

Oprava pilotu C: ve službovém prostředí bez TERM se macOS Tailscale přepnul
do GUI a vracel ne-JSON výstup. Ochranné čtecí dotazy vynucují
TAILSCALE_BE_CLI=1 pouze v prostředí daného subprocessu; rodičovské
prostředí ani konfigurace sítě/Camino se nemění. Stav protection nyní
jednoznačně odděluje síťový audit od převzetí Lunou. Ověřeno skutečným
snapshotem s minimálním launchd prostředím a přesnou shodou baseline.
Zdroj: https://tailscale.com/docs/reference/tailscale-cli?tab=macos .
Schválený balíček C nyní obsahuje dokumentační commit i tuto opravu; počet
commitů a dodatečné náklady budou ve výsledku výslovné.

Oprava C ověřena: 43 cílených testů, skutečný minimální launchd audit a
plná brána 2034/2034 PASS (unit část 262,874 s). Publikační výsledek zůstává
samostatným živým důkazem v runtime účtence a finálním souhrnu.


## Omezený pilot rutinního kontrolora (17. 10. 2026)

Vedle role p+n existuje nezávislá role routine_reviewer, schválená pro jediný
typ report_documentation_review v app/routine_tasks.py. Jde o čtecí porovnání
veřejného katalogu app/system_reports.py a jeho pevné dokumentace. Nejde o
obecný směrovač vývoje, nový scheduler ani automatickou změnu kódu.

Přesný typ vybírá program bez modelového tahu. Neznámé typy vrací Adamovi;
spuštění vyžaduje existující souhlas. Registrovaný náhled je bezplatný, placené
spuštění je ve workflow registru s pevným argv. Jediný samostatný tah používá
read-only sandbox bez síťových nástrojů; per-thread vypíná shell, konektory,
MCP, další agenty, hooky, paměti, projektové instrukce a katalog dovedností.
Vlastní baseInstructions platí pouze v tomto prázdném kontextu; žádná historie
ani soukromý obsah se nepřenáší. Hlavní model a globální nastavení se nemění.

Pevný vstup do 12 000 bajtů, jeden tah, žádné automatické opakování. Nejvýše
tři nálezy s přesnou citací v dokumentaci; neplatná citace, změna role či
podkladů, chybějící spotřeba nebo překročení 16 000 tokenů / 1 Standard
kontrolora vrací attention. Tokenový/kreditní limit je kontrola přijetí po
dokončení, nikoli tvrdý limit fakturace. Runtime kontext je prázdný a privátní,
necommitovaný; zdroje, služby, Git, síť ani data Camina se auditem nemění.

První 165bajtový payload měl kvůli implicitnímu kontextu 18 337 tokenů a
neprošel limitem. Omezený kontext stejného zadání měl 10 995 tokenů. Úspěšný
skutečný audit devíti reportů: 4,95 s, 0,6515 Standard kontrolora a 0,64077
jednorázové převzetí hlavním Adamem. Celkem 1,29227 Standard, žádné nálezy,
nulová spotřeba hlavního modelu při čekání. Cache, práce zavedení a hranice
měření jsou zvlášť v logs/routine_pilot_report_20261017.log. Neexistuje
přímý srovnatelný kontrolní běh, takže úspora není prokázaná.

Model role: gpt-6.1-sol / medium, pouze config/agent_roles.json; skutečný
syntetický dry-run s doloženým rozporem v logs/routine_candidate_probe_20261017.log.
Standard sazby ověřené 17. 10. 2026: 50 vstup / 2,5 cached / 250 výstup za
milion tokenů, https://learn.chatgpt.com/docs/pricing#token-rates . Nastavení
vykonavatele p+n a jeho otisk jsou před/po totožné. Celkové náklady se sledují
včetně případného probuzení hlavního Adama; samotná levná role úsporu nedokazuje.

Aktivace je po pilotu odložená: starý běžící Cockpit vyžaduje v seznamu rolí
pouze release_executor. Centrální JSON byl proto po úspěšném experimentu
vrácen přesně do původního stavu a obyčejné p+n zůstává kompatibilní.
Bez role run_routine_task bezpečně vrátí attention; náhled pouze ukazuje
rezervovanou routu, nikoli dostupnost aktivního modelu. Nejprve samostatně
nasadit podporu více rolí; aktivace routine_reviewer v centrálním JSON je
až následný krok s novým otiskem a kontrolou. Pilotní vazba a její důkazy
jsou v logs/routine_pending_role_20261017.log, ne jako alternativní
produkční konfigurace. Nové nasazení během tohoto úkolu nebylo autorizované.


## Výslovně zadaný vývoj Lunou — 20. 10. 2026

Míla rozhodl: nejprve zprovoznit skutečný vývoj Lunou a používat jej vždy,
když o něj výslovně požádá. Výslovná volba má přednost před heuristikou
pro nabídku delšího levného úkolu i před původním pilotem jedné funkce.
Adam připraví zadání, vymezí zdroje a ověření, jednou zkontroluje a integruje
výsledek. Bez oznámené překážky vývoj nepřevezme sám ani nepoužije Sola.
Bezpečnostní brzda, writable grant, Git a p+n zůstávají samostatně řízené.

- `app.luna_development.preview/run/accept` je registrovaná terminálová cesta.
  Portál používá tentýž engine přes stávající SIMPLE_DEVELOPMENT IPC grant;
  model nesmí spouštět nový App Server ani získat síť kvůli předání.
- Požadavek má přesně `kind="explicit_project_change"`, `explicit_luna=true`,
  `request_id`, `goal`, `files`, `context`, `test_modules`. Root dodává pouze
  důvěryhodný volající/server. files/context mapují veřejné relativní cesty
  na seznamy `[první_řádek,poslední_řádek]`; prázdné files úseky povolují nový
  soubor. Nejvýše 12 editovatelných a 12 čtených souborů, 180 kB podkladů;
  větší úkol Adam rozdělí do navazujících předání. Nejde o limit jazyků.
- Zdroje musí být commitnuté, textové a bez odkazů, z app/tests/scripts/config/
  memory/docs/camino. Soukromá data a centrální nastavení modelu se nepředávají
  k úpravě. Přijímací unittest moduly 1–10 zůstávají nezměněné; model dostane
  pouze vybrané úseky, cíl a jejich názvy, žádnou historii či soukromá data.
- Jediný modelový tah bez nástrojů/MCP/hooků/pamětí vrátí přesné náhrady old/new.
  Program ověří jednoznačnost, nepřekrývání a rozsah; testy před/po běží
  v committed kopii nejvýše 64 MiB přes sandboxované command/exec. Model
  neprovádí příkazy. Nulové testy či chyba prostředí zastaví placený tah.
- Zmrazená centrální role simple_developer musí být skutečná Luna; žádný Sol
  fallback. Limit přijetí po tahu je 120 000 tokenů / 4 odhadované kredity
  Standard, nikoli fakturační strop. Neúspěch či nejistota se neopakují.
- Při jedné nepřesně citované kotvě old smí Adam po přečtení původního návrhu
  použít registrované `review_anchors(job_id, answer_digest, corrections, ...)`.
  Korekce mění pouze old, nikoli path/new od Luny. Zdroje/kontext/role musí
  zůstat shodné; nová izolace a obě testové fáze vážou aktuální čistý head.
  Vzniká deterministická navazující účtenka bez placeného modelu, s odkazem
  na původní návrh; nová spotřeba je nula, původní se nesčítá znovu.
  Portál povoluje nejvýše jednu takovou kontrolu ve stejném grantu.
- Přijetí ověří všechny původní soubory, head, roli a otisk kandidáta před
  prvním zápisem. Jednotlivé soubory se nahrazují atomicky; stav applying
  zachytí přerušené převzetí více souborů a vyžaduje kontrolu bez retry.
  Žádné mazání, commit, push či nasazení uvnitř vývojového enginu.

Skutečná zkouška gpt-6-luna/high 20. 10.: tři FAIL → tři PASS, návrh převzatý;
probe `3a1b667eeb634603be866357921150f5`. Odhad 0,02975 kreditu Standard.
Cena ověřena v oficiálním ceníku: 2,5 vstup / 0,25 cache / 12,5 výstup
kreditu za milion tokenů. Zdroj: https://learn.chatgpt.com/docs/pricing#token-rates.
Důkaz soukromý, redigovaný souhrn logs/luna_development_probe_20261020.log.
Centrální simple_developer byl 20. 10. registrovaně přepnut na gpt-6-luna/high;
release_executor zachovaný. Rozšířená portálová větev vyžaduje následné p+n.
Přepnutí již existující role používá activation_plan(probe, replace_existing=True)
a activate(plan, confirmed=True); zmrazí i původní konfiguraci a zachová
release_executor. Následující část popisuje původní pilot a jeho historii,
nikoli omezení výslovného vývoje přes nový engine.

První skutečný vícesouborový úkol 20. 10.: fotografie ve střižně, 5 souborů
Python/JS/HTTP/testy, původní návrh Luny převzatý po kontrole citace old.
Přejímací kontrakt 4 FAIL → 4 PASS, receipt 393b9e1a2d6920d7ed27d41c74473cea;
původní modelový job d67ea8e3a4c26b3c088fd33a821194e8. Nebyl nový modelový
tah při integraci; původní odhad 0,161725 Standard. Portálový IPC výběr nové
větve a role dostane běžící Cockpit týmž schváleným p+n.

## Jednoduchý vývoj (17. 10. 2026)

### Výběr vývojových kroků pro Lunu — dohoda 17. 10. 2026

- Hlavní Adam nejprve analyzuje zadání. Lunu navrhne pouze pro **delší**,
  zvládnutelný, jasně vymezený a ověřitelný vývoj s nízkým rizikem, kde lze
  čekat úsporu i po započtení přípravy, předání, kontroly a integrace.
  Opakovaná práce je vhodný kandidát, ale také musí být dostatečně dlouhá;
  samotné opakování ani nízké riziko u krátké změny nestačí.
- U složitějšího vývoje rozděleného do kroků už plán uvede, které kroky
  navrhuje pro Lunu a které provede hlavní Adam, s krátkým důvodem a způsobem
  ověření. Schválení takového plánu pokrývá navržené rozdělení; není třeba
  znovu potvrzovat každý nezměněný schválený krok.
- U ad hoc vývoje přijde po analýze jediná nabídka `Předat Luně: ano/ne`,
  pouze pokud jsou splněné předchozí podmínky. Drobné změny, nové kritické
  úpravy, nejasný rozsah a úkoly, u nichž by režie převážila přínos, řeší
  hlavní Adam bez nabídky. Neúspěšný či nejistý pokus se automaticky neopakuje.
- Pevný počet minut, řádků ani procento úspory zatím neurčujeme. Výchozí
  úsudek hlavního Adama se bude s Mílou zpřesňovat podle zkušeností a nákladů
  celého postupu, ne pouze podle sazby nebo spotřeby pomocníka.
- Každé samostatně autorizované p+n provádí Luna registrovaným společným
  vstupem. Rozdělení vývoje samo push ani nasazení nepovoluje.

Míla výslovně zvolil Lunu také pro uvedenou vývojovou práci. Jde o schválené
pravidlo výběru, nikoli o provedenou změnu modelu či rozšíření technického
rozsahu. Při tomto zápisu zůstává v `config/agent_roles.json` dosavadní
`simple_developer` se Solem; Lunu nelze vydávat za aktivní ani ji bez upozornění
nahradit Solem. Před prvním skutečným použitím Luny je nutné doložit cenové
posouzení a přijatou skutečnou vývojovou zkoušku a dokončit bezpečnou změnu
centrální role. Důkaz Luny pro p+n není vývojovou zkouškou. Následující omezení
jedné funkce nadále platí; širší kroky vyžadují vlastní rozšíření mechanismu.

Míla autorizoval dokončení vývojového předávání. První podporovaná třída je
jedna čistá vrcholová synchronní Python funkce v app/ s 1–3 existujícími
unittest moduly. Hlavní Adam při plánování jednou vybere cíl, funkci a testy;
program rozhodne způsobilost bez modelového klasifikátoru. Funkce do dvou
řádků zůstává Adamovi kvůli režii. Nejde o obecné převzetí libovolného vývoje.

Registrované app.simple_development.preview/run/accept používají čistý
commitovaný autorizovaný workspace; root je důvěryhodný kontext volajícího,
nikdy pole požadavku. Požadavek má přesně goal, path, function, test_modules.
Nejvýše 100 řádků / 12 000 bajtů funkce, zachovaná signatura, žádné importy,
vnější helpery, globální stav ani zápis do parametrů. Camino, Cockpit, role,
autosave, přenosy, perzistence, zálohy, bezpečnost, publikace, e-mail a kalendář
jsou vyloučené. Rozšíření rozsahu vyžaduje zvláštní vývojové rozhodnutí.

Program z committed app/tests vytvoří kopii nejvýše 32 MiB bez odkazů.
Původní testy spustí před i po opravě přes App Server command/exec bez modelu,
v sandboxu workspaceWrite jen pro kopii a její tmp, bez sítě a globálního tmp.
Chyba prostředí či nulový počet testů zastaví předání před placeným tahem.
Pomocník dostane pouze cíl, funkci a názvy testů, žádnou historii ani celý
projekt. Jediný datový tah používá centrální simple_developer, vypnuté nástroje,
MCP, konektory, hooky, paměti a implicitní projektové instrukce/dovednosti.
Testy se nemění; pouze vybraná funkce smí vytvořit diff. Účtenka obsahuje
zmrazenou roli/head/hash, testy, spotřebu a přesný otisk návrhu. Překročení
30 000 tokenů / 4 Standard je mez přijetí po dokončení, ne fakturační strop.
Chybějící důkaz, přerušení nebo drift znamenají attention bez automatického
opakování. Stejné zadání na stejném head má trvalé stejné job ID.

Hlavní Adam zkontroluje jednou diff a testovou účtenku a v již autorizovaném
tahu zavolá accept s přesným job ID a candidate_digest. Přenese se pouze
ověřená funkce, bez Gitu. Stejné přijetí je idempotentní, pozdější změnu
zdroje nepřepíše. V terminálu následuje obvyklý zápis a lokální commit;
v Human–Adam zůstává checkpoint a integrace výhradně Cockpitu.

### Cesta z portálu a dědění do nových proudů

Izolovaný editor s networkAccess=false nemůže ani HTTP na localhost.
Nespouštět v něm další App Server a nepovolovat síť kvůli předávání.
ProfileManager vystaví pouze při existujícím writable=true a aktivní schválené
roli krátkodobý blok SIMPLE_DEVELOPMENT s tokenem a soukromým kanálem.
app.simple_development_portal.request předá run nebo accept souborovým IPC.
Server určí root, projekt, thread i message ID a obslouží právě jeden úkol;
cizí/ukončený/čtecí tah, jiný návrh nebo model/root z payloadu odmítne.
Programové čekání neprobouzí hlavní model; po send včetně chyby se grant zruší.
Žádný nový daemon, plánovač, veřejná API operace ani síťové oprávnění.

Stejné společné AGENTS a ProfileManager se použijí i pro nově založené proudy.
Bez platného bloku úkol zůstává hlavnímu Adamovi. V přímém terminálu se použije
registrovaný run s root nastaveným na skutečný projektový adresář. Při čekání
využít jeden programový běh, případně functions.exec s programovým čekáním na
exec session; nevyvolávat model kvůli průběžným kontrolám.

### První zavedení po samostatném p+n

Při dokončení vývoje zůstal config/agent_roles.json původní, protože tehdejší
Cockpit uměl jen release_executor. První zavedení pod výslovným p+n používá
následující konfigurační fáze:

1. Dosavadní registrovanou cestou publikovat a nasadit připravené commity.
2. Na čistém main zavolat activation_plan s probe ID
   9396d97054df4e549a777d930622df1f a activate(plan, confirmed=True).
   Živý GET /api/human-adam/simple-development/capabilities musí doložit nový
   parser. Plán zmrazí commit, původní konfiguraci a přijatý skutečný důkaz.
   Starý runtime změnu odmítne před zápisem. Aktivuje se jen simple_developer;
   původní release_executor zůstane přesně zachovaný. routine_reviewer se tím
   nezapíná. Vazba bude pouze v centrálním config/agent_roles.json.
3. Zkontrolovat a lokálně commitnout tuto konfiguraci s povinným projektovým
   zápisem (bez dalších změn kódu), zarovnat bezpečné
   profily, provést nový audit přesného balíčku a dokončit autorizované p+n.
   Nový vývoj není zapotřebí; konfigurační fáze má samostatné ověření a účtenku.

Kandidát gpt-6.1-sol/medium má doložené cenové posouzení a skutečný suchý test.
První zkouška správně skončila attention kvůli nepovolenému zřetězení metod;
instrukce byly upřesněné a nový výslovný test prošel. Žádné automatické retry.
Tři nezměněné testy přešly FAIL → PASS; hlavní Adam jednou převzal přesný diff.
Úspěšný tah 11 093 tokenů / odhad 0,58125 Standard, první zastavený 0,55645.
Jsou to ceny pomocníka, ne celkové úspory. Vývojová práce, režie hlavního Adama
a jednorázová implementace se s cenou jedné opravy nesměšují; bez kontrolního
běhu úspora neprokázaná. Číselný souhrn v logs/simple_development_report_20261017.log.
Skutečná zkouška souborového IPC uvnitř networkAccess=false PASS; žádný modelový
tah ani rozšíření sítě. Fyzická přejímka portálu zůstává až po nasazení.


### Aktivace po skutečném nasazení 2026-10-17 19:55 CEST

Luna nasadila af5db5a3 / 7fa6d9e50f794ddf, full gate 2096 a smoke 5/5.
Registrovaná aktivace přijala probe 9396d97054df4e549a777d930622df1f a
nezměněný digest 51725aeaeb9504ed3dd015ca8a1f0622a801a8663029e11c05234892f138b703.
Role simple_developer je nyní v centrálním JSON, katalog ověřil gpt-6.1-sol/medium
a živý capabilities vrací enabled=true. routine_reviewer zůstává neaktivní;
release_executor beze změny. Konečnou publikaci konfiguračního checkpointu
dokládá logs/simple_development_release_phase2_20261017.log a účtenka 4935e2096cff56f7aa768ec9d3ab936e.
Předpoklad předchozích historických odstavců o neaktivní vývojové roli tím končí.


## Stav pro navázání a skutečné náklady — 2026-10-17 21:18 CEST

Obě fáze prvního zavedení jsou dokončené. Nasazený head a1437ec2,
stamp 7fa6d9e50f794ddf, finální účtenka 4935e2096cff56f7aa768ec9d3ab936e:
completed, push/deploy potvrzené, 2096 testů PASS a smoke 5/5. Aktuální handoff
má prioritu 1, ceka na retest a připomenutí při startu. Neopakovat bootstrap.
Další krok je fyzická přejímka vhodného drobného úkolu přes portál; další
vývoj ani nové p+n tím nejsou zadané. Dnešní uložení je pouze lokální dokumentace.

Odhad celého posledního p+n od přijetí pokynu po konečnou odpověď:

| Složka | Kredity Standard |
|---|---:|
| Hlavní Adam včetně aktivační práce, zápisů a kontrol | 14,62797 |
| Nativní pomocník Luna za obě fáze | 0,5673575 |
| Dvě samostatná převzetí balíčku Lunou | 0,128115 |
| Celkem | 15,3234425 |

Číselný interval hlavní relace: 2026-10-17 17:46:19.916–18:09:15.384 UTC,
3 530 781 input (z toho 3 494 528 cached), 16 316 output, 3 547 097 celkem.
Nativní pomocník: 1 343 599 input (1 287 040 cached), 8 336 output,
1 351 935 celkem. Samostatná převzetí: 49 426 tokenů, 0,0632825 a 0,0648325
Standard. Cached input a reasoning jsou podmnožiny, nepřičítají se podruhé.
Zdroj jsou pouze číselné záznamy vybraných relací a bezpečné účtenky obou fází;
žádný obsah promptů či soukromých dat. Přepočet Standard dle ceníku ověřeného
17. 10. 2026: https://learn.chatgpt.com/docs/pricing#token-rates . Nejde o fakturu,
změnu zůstatku ani procenta předplatného; rychlostní multiplikátory nejsou doložené.

Poslední běh zahrnoval jednorázovou aktivaci a dvě nasazení; úspora celku
není prokázaná. Dřívější asynchronní pilot 1,7030575 proti přímému 7,27533
(asi o 77 % méně) není měřením tohoto vydání. Podklady:
logs/simple_development_release_phase1_20261017.log,
logs/simple_development_release_phase2_20261017.log,
logs/pn_async_comparison_20261017.log. Při dalším běžném výslovném p+n zachytit
začátek měření před předáním a započítat všechny modelové role i finální převzetí.

Rozsah: p+n všech 33 registrovaných proudů; nový proud zdědí společný postup
po registraci svého cíle. Samostatný klient/služba Camino používá vlastní postup.
Sol zatím jen jedna čistá Python funkce s existujícími testy, ne obecný automatický
vývoj. Model a úsilí jsou výhradně v config/agent_roles.json; neaktivní
routine_reviewer není překážka aktivního simple_developer. Během čekání model
nehlídkuje. Nejistý krok se automaticky neopakuje.


## Jediný programový vstup — 2026-10-17 21:32 CEST

Míla schválil obecné odstranění nativní mezivrstvy Luny a ručního sestavování
předání. `submit_release` je společné pro všech 33 registrovaných proudů,
včetně Pages cílů, a dědí se přes společná AGENTS i do nově registrovaných
proudů. Povinný schválený lokální SHA brání přibrání jiného novějšího commitu;
program dopočítá origin, cíl a zmrazený model. Zachovává všechny původní plné,
bezpečnostní a publikační brány. Nepovoluje samostatná vydání Camina.

59 cílených testů PASS: kompaktní i úplný UI payload, TOCTOU, idempotence,
čekání na konkrétní účtenku, timeout bez retry, návrat původnímu volajícímu,
bez změn modelové politiky. Skutečný syntetický dry-run vykonal právě jeden
modelový tah Luny, jeden worker a nula odchozích zápisů; opakování stejné
identity nevolalo další model. Důkaz logs/release_single_entry_dry_20261017.log.
Worker 24 691 tokenů / odhad 0,0639475 Standard není cena celého budoucího p+n;
celková úspora není změřená. Camino/autosave před/po shodné. Plná brána
2109/2109 PASS (301,702 s unit testů); logs/release_single_entry_full_gate_20261017.log.
Tento krok je pouze lokální vývoj, bez push/nasazení; portál nový vstup použije
po příštím samostatném p+n. Pro nativní spuštění není potřebná nová HTTP route
ani konfigurační bootstrap. Historické benchmarky a jejich výsledky se nemění.

## Startovací zámek — místní oprava 2026-10-23 22:39 CEST

Kontrola stavu v prvních 30 sekundách od zařazení úlohy nezkouší worker
lease. Původní kontrola jej sice hned uvolnila, ale krátce mohla odmítnout
skutečný právě startující worker. Po startovací lhůtě zůstává kontrola
mrtvého workeru, opakované čtení účtenky i zákaz dalšího workeru stejné.
Nový regresní test vynutí nulový počet pokusů o lock během této lhůty.
Stav opravy: 57 cílených testů PASS, plná brána 2186 PASS (333,492 s unit část), opakovaný souběh 10/10 PASS. Publikační
překážka a přesná původní účtenka jsou v handoffu Camino i Cockpit.
