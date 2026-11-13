# Codex Reconnect Recovery

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Postup pro navazani prace po vypadku SSH, reconnect loopu, padu Codexu nebo
zaseknuti streamu.

Detailni pravidla jsou v:

```text
memory/technical/session_recovery_rules.md
```

## Zakladni pravidlo

Nejdriv zjistit, co je realne rozpracovane:

```bash
git status --short --branch
git --no-pager log -3 --oneline --decorate
```

Pak cist relevantni memory:

```text
memory/MEMORY_INDEX.md
memory/ACTIVE_PROJECTS.md
memory/handoffs/
```

## Po vypadku SSH

Pouzit:

```bash
samantha
```

Pokud prikaz neni znamy:

```bash
source ~/.zshrc
samantha
```

Rucne:

```bash
screen -ls
screen -r samantha_codex
```

## Network preflight pri startu

`scripts/samantha_codex.sh` spousti `scripts/network_preflight.sh` pred pripojenim
ke `screen` relaci. Preflight kontroluje:

- bezici zname VPN/Tailscale procesy,
- pocet `utun` tunelovych rozhrani,
- IPv4 adresu na Wi-Fi rozhrani,
- zakladni ping na IP a DNS jmeno.

Vychozi rezim jen diagnostikuje a nic nevypina.

Pro pokus o ukonceni znamych VPN procesu pred startem lze pouzit:

```bash
source ~/.zshrc
SAMANTHA_DISABLE_VPN=1 samantha
```

nebo primo:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_clean.sh
```

Preflight lze nouzove preskocit:

```bash
SAMANTHA_PREFLIGHT=0 samantha
```

## Po padu Codexu

Pouzit:

```bash
codex resume --last
```

nebo konkretni session ID:

```bash
codex resume <SESSION_ID>
```

## Pri zaseknutem nastroji

- Zkontrolovat, zda stale bezi proces, ktery Codex spustil.
- Ukoncit jen vlastni diagnosticky proces, ne uzivatelske aplikace.
- Nepouzivat destruktivni git prikazy.
- Pred dalsi praci shrnout, co je rozpracovane a co bylo overeno.

## [PRIPOMENOUT] Cockpit Recovery centrum

Priorita 1 pro pristi praci na Cockpitu: pridat read-only Recovery centrum pro
navazani po padu Samanthy/Codexu. Cilem je, aby Mila nemusel lovit terminalovy
postup v pameti.

Minimalni obsah:

- posledni autosave timestamp z `data/session_autosave/` bez vypisu citliveho
  obsahu logu,
- kratke git status summary,
- posledni relevantni handoff nebo odkaz na `MEMORY_INDEX.md`,
- doporuceny dalsi prikaz: `samantha`, pripadne `codex resume --last`,
- jasne upozorneni, ze recovery panel je read-only a nic neprepisuje.

Kanonicky handoff:

```text
memory/handoffs/cockpit_recovery_center_priority_2026_06_03.md
```

## Pravidlo pro dlouhe ukoly pri nestabilnim spojeni

Pri opakovanych reconnectech nepokracovat dlouhymi interaktivnimi tool cally.
Dlouhe prace spoustet jako samostatne skripty s logem a stavovym vystupem.

Konkretne:

- pred dlouhym ukolem spustit `samantha` nebo pri problemech `SAMANTHA_DISABLE_VPN=1 samantha`,
- dlouhe davky psat do skriptu v `scripts/` nebo projektove lokalni slozce,
- prubeh zapisovat do `logs/` nebo soukrome pracovni slozky,
- vystupy delat navazovatelne a opakovatelne,
- po reconnectu nejdriv precist vystupni soubor/log a az potom pokracovat.

To plati hlavne pro videa, media importy, exporty, sifrovani balicku a hromadne
operace nad soubory.

## Bezpecnost

Autosave v `data/session_autosave/` je nouzovy log a nesmi se commitovat.

## 2026-11-11 19:19 CET — příkazy selhávají ještě před čtením souboru

Chyba `failed to decode code-mode IPC frame: unknown field result_buffered_for_ns`
není doklad chybějících souborových práv. Nejprve ověřit konkrétní poslední
nástrojový výsledek, živý serverInfo.version (nejen codex --version) a neplacené
čtení přes command/exec. Na serveru 0.163.0 při CLI 0.167.0 přímé čtení prošlo.

HumanAdamService předává jen svým hubům config_overrides s vypnutým code_mode
a code_mode_host. Hub je kopíruje při startu, resume i výslovné rotaci; jiné
klienty ani globální config nemění. Tyto přepínače nepovolují přístup, zápis,
síť, nový modelový tah ani retry. Při živé opravě nečinného vlákna se přesná
nastavení před/po porovnají; historie a soukromá session zůstávají zachované.

2026-11-11: lokální kód a živá mitigace původního vlákna jsou oddělené.
Míla navazující Terra p+n samostatně schválil; konečný výsledek určuje přesná
soukromá účtenka jobu 444fe9352557c64a4082aed426d9dd0c. Skutečné použití
nástroje modelem musí potvrdit další uživatelský tah. Důkazy: kanonický handoff Human–Adam a
`data/private/human_adam_tool_compat_20261111/`.

Protokol per-thread config: [oficiální OpenAI dokumentace App Serveru](https://learn.chatgpt.com/docs/app-server).

### 2026-11-12 08:37 CET — HA-01: společná čtecí projekce stavu

Hotovo: Human–Adam má místní přídavný stavový kontrakt pro budoucí přehledné UI. Spojení, probíhající model, navazující kontrola, publikace a starší incidenty mají vlastní význam a rozsah. Starý nebo cizí doklad se nevydává za aktuální tah.

Rozhodnutí: Míla zadal HA-01 podle plánu z 11.11. Používá se nová čistá Python projekce nad existujícími zdroji, bez jejich nahrazení a bez nových mutací. ID jsou stabilní čtecí reference, revision je obsahový otisk, nikoli pořadový event cursor. Vlastníci provedení a doménové účtenky zůstávají autoritou.

Další krok: Po dokončení HA-01 navázat HA-02 — přehlednější rozhraní nad společnou projekcí.

Navrhované další kroky: HA-03 ažHA-05 pro skutečné události, serverově vlastněnou práci a živou kartu; poté doplnění/zastavení. Žádné p+n nebylo zadáno.

Technický důkaz: 29 nových HA-01 testů OK / 2,411 s. Závěrečná plná brána 3543 testů OK / 620,369 s, 5 SKIP; statické a syntaktické kontroly OK. Ověřené nezměněné bajty/mtime zdrojů, korelace a pozdní snímky, přesný head/target/smoke při dodatečném důkazu. Main a služby nedotčené. Report human_adam_ha01_work_state_20261112.txt.


### 2026-11-12 09:36 CET — HA-02: čitelný chat a tři pohledy Práce

Stav: Lokálně implementováno na data/parallel-20261104 nad HA-01 5d9c1497; bez integrace, push nebo nasazení. Celková brána 3544 testů OK / 584,986 s, 5 SKIP; finální prezentační úpravy ověřené cíleně a v prohlížeči, statická brána OK.

Rozhodnutí: Míla zadal HA-02 podle auditního plánu. Společná projekce HA-01 je zdrojem aktuálního souhrnu; Práce odděluje probíhání, výsledky/publikaci a servis. Dosavadní mutační brány zůstaly. Nový stream, worker, App Server protokol, steer/interrupt a účtování celé úlohy se neimplementují v tomto kroku.

Další krok: Posoudit balíček HA-01/02 a fyzickou přejímku až po samostatném vydání; případně HA-03 na další zadání.

Rizika: Browser QA je syntetické a neprokazuje iPhone/Safari, reálnou klávesnici nebo živou relaci. UI používá dnešní snímky a dosavadní obnovu, ne nový event cursor. Omezený Markdown není úplný renderer.

Technický důkaz: 271 cílených testů OK / 9,976 s; 200 browser PASS na skutečných viewports 390x844, 430x932, 1280x900, 390x480 a 430x500. Vizuálně zkontrolované snímky hlavního okna i pohledů Práce. Čtecí generace/scopes, bezpečné odkazy, zachování DOM/fokusu/předčítání/scrollu, celý sbalený text a nulový POST v browser fixture. Rozpracované běhy ukončené před posledními opravami odolnosti; celková brána 3544 testů OK / 584,986 s, 5 SKIP. Následné prezentační úpravy návratu fokusu z Další a neověřených os zdrojů ověřené finální cílenou sadou (271 / 9,976 s), browser QA (200) a statickou bránou. Důkazy logs/ha02_*.log a data/private/ha02_ui_qa_20261112/. Report human_adam_ha02_ui_20261112.txt.

### 2026-11-12 10:36 CET — HA-03: oddělené RPC a události App Serveru

Stav: Lokálně implementováno na data/parallel-20261104 nad HA-02 7b77aba2. Finální cílená sada 287 testů OK / 4,783 s; statická brána OK. Plná regresní brána: 3587 testů OK / 532,005 s, 5 SKIP. Bez integrace, push, nasazení, skutečného App Server spojení či placeného pokusu.

Rozhodnutí: Míla zadal HA-03 podle plánu z 11.11. Jeden wire reader předává data bounded dispatcheru: RPC má vlastní slot podle ID, odběry samostatné fronty a scope/generation. Konkrétní validátory, explicitní kompatibilní plan/usage varianty, přesné vazby a close všech čekajících operací. Dosavadní receive guard zůstává v cestě včetně item/started a neznámých item payloadů. Chybné usage zneplatní staré měření, ne jinak potvrzené doručení. Read-only protocol diagnostika je mimo perzistentní session; sama nepřipojuje runtime ani neověřuje živou podporu features.

Další krok: HA-04 — trvalá serverová identita dlouhé práce, snímek/historie/cursor a obnova po reloadu, až na další zadání. UI živé karty je HA-05. Samostatně posoudit integraci/vydání balíčku a následnou živou Mac/iPhone přejímku.

Rizika: Testy jsou syntetické a nepřipojily skutečný sdílený App Server; historický 05/P1 není nové živé ověření změněného klienta. Validation pokrývá spotřebované core fields, nikoli všechna pole schématu. Již běžící callback nelze násilně zastavit; pozdější použití jeho výsledku musí ověřit generation. sequence je pořadí publikace a received_sequence původní wire pořadí, nikoli trvalý cursor. Nové odběry zatím nejsou napojené do živé UI karty. Main, služby, role a mutační oprávnění zachované.

Technický důkaz: Širší průběžná sada 475 testů OK / 62,471 s; finální jádro 287 OK / 4,783 s. Testy skutečného klienta nad vlastním Unix WebSocket listenerem a stdio Python fixture: RPC/event souběhy, plan před ACK, thread-only usage, cizí/stará generace, count/byte/callback limity, výpadek před/po ACK bez replay, jeden přijatý user item/start/final, CanonicalSessionHub delivery_unknown a ScienceNews guard. Offline CLI 0.167.0/schema; původní minimum serveru 0.163.0. Report human_adam_ha03_dispatcher_20261112.txt, logy ha03_* a ignorované otisky zdrojů; žádné soukromé payloady v Git-safe zápisu.


## 2026-11-12 10:55 CET — Will přebírá HA-01 až HA-03 do společného vydání

**Hotovo:** Lokálně převzaté Datovy tři hotové commity5d9c1497,7b77aba2 a045936f9
nad e-mailové UI aae687fb. Kód se spojil bez konfliktů; paměť zachovává obě
historie v časovém pořadí. Oprava startu pošty, její zámek i modelové role
jsou přesně zachované. Jedinou integrační úpravou je přenositelnost diagnostické
asertace hlubokého neobjektového JSON mezi Python3.11/3.12; obě cesty stále
odmítnou rámec, uzavřou spojení a probudí čekající RPC. Produkční dispatcher
zůstává Datovou verzí.

**Rozhodnutí:** Míla výslovně zadal společné p+n všech hotových Willových i
Datových commitů. Balíček zahrne také odložený hotový Ateliér4ea5b01e. Jediné
registrované vydání má request `combined-finished-work-20261112-v1`, job `4242cf7f5bdb6b88724e635cde31b443`,
project-email-cases→společný Cockpit. Vykonavatele určí centrální Terra role.
Nejde o aktivaci dalších služeb ani placený vývojový/modelový pilot.

**Další krok:** Převzít Ateliér, dokončit celkovou bránu a zmrazit přesný
commit pro jediné registrované p+n.

**Navrhované další kroky:** Po vydání fyzická přejímka Human–Adam na Macu/iPhonu;
HA-04 až po samostatném zadání. E-mailový automatický monitor zůstává další etapa.

**Technický důkaz:**201 cílených testů PASS, samostatný test také v Datově
Python3.11 PASS. Skutečný nový klient přes stávající Unix WebSocket: initialize
amodel/list,10 modelů, CLI/server0.167.0, žádný thread/start ani turn/start;
uzavřené jen vlastní spojení, sdílený socket zachovaný. Toto není důkaz
modelového tahu, reconnectu dlouhé práce ani fyzické přejímky. Plná brána
poběží nad finálním společným balíčkem; meziběh před rozšířením na Ateliér
se nevydává za úspěšnou závěrečnou kontrolu. Soukromé důkazy
`data/private/combined_release_20261112/`.


## 2026-11-12 10:58 CET — Finální společný balíček pro jedno Terra p+n

**Hotovo:** Funkčně nové ruční e-mailové UI aae687fb a Datovy HA-01/02/03
5d9c1497,7b77aba2,045936f9 jsou společně na main. Zbývající staré větve
jsou propojené pouze historicky: půdorys4ea5b01e má přesně stejný stable
patch-id jako již převzatý58a18e68 (c13a5067bd2855a44a068dc7e249c8981335f2d8).
Současné názvy návrhů, bezpečnostní úpravy a ostatní novější kód Ateliéru
zůstávají zachované. Přípravné commity8f64dca7/9d89446b mají dokončenou
náhradu v aae687fb: všechny kontrakty přešly do kanonického UI, které navíc
nemá nepotvrzený automatický výchozí termín. Historické propojení nepřenáší
žádný starší zdroj ani nepřepisuje dnešní implementaci.

**Rozhodnutí:** Výslovné Mílovo p+n všech hotových commitů se provede jednou
registrovaným submit_release(wait=True), v aktuálním project-email-cases,
společný cíl Cockpit Samanthy. Request combined-finished-work-20261112-v1,
job4242cf7f5bdb6b88724e635cde31b443. Schválený head se doplní až po finálním
lokálním merge commitu a zarovnání čistých profilů. Žádná změna modelové
politiky, automatického monitoru, systémové služby nebo placený vývojový pilot.

**Další krok:** Dokončit finální celkovou bránu, lokální checkpoint a jediné
p+n; výsledek jednou ověřit z původní účtenky a živého HTTP.

**Navrhované další kroky:** Lidská Mac/iPhone přejímka; e-mailová etapa3 a
Human–Adam HA-04 až jako další vývoj. Samostatný e-mailový TVBCP zůstává
nedohodnutý; aktualizují se existující správné handoffy a Cockpit/Layer TVBCP.

**Technický důkaz:**201 integračních testů PASS; zvlášť shodná bezpečnostní
regrese v Python3.11 PASS. Nový dispatcher ověřen skutečným initialize a
model/list na sdíleném serveru0.167.0 bez nového thread/start/turn/start.
Historické merge ponechávají app/scripts/tests bytewise stejné proti8d05aac2.
Finální plná lokální brána PASS: 3602 testů,31 SKIP, 507.039 s.
Výsledková autorita: reports/combined_finished_work_release_20261112.md a
původní privátní job/receipt. Zápis vzniká před publikací, není účtenkou
nasazení. Při nejistotě se původní job dohledá, nepodává se nový požadavek.


## 2026-11-12 12:07 CET — HA-04: trvalé serverové přijetí a návrat ke stejné práci

**Hotovo:** Backend ukládá přijetí a stejnou identitu práce před samostatným
prováděním. Nový start vrací rychle202, staré send zachovává čekající odpověď.
Práci lze dohledat i po ztraceném HTTP spojení; opakování stejného požadavku
nezakládá druhý modelový tah. Snímek a omezené události mají cursor/resync.
Po pádu backendu se obnovuje pouze původní důkaz, nikoli provedení.

**Rozhodnutí:** Míla výslovně zadal HA-04 a následně rovnou p+n. Kritickou
implementaci provedl Adam přímo. Původní oprávnění/dokončovací kód zůstávají
autoritou; model/hodnoty role se nemění. Ukládá se pouze již přijaté zadání
v private server cache, žádné nové browserové drafty. Živá karta je HA-05.

**Další krok:** Dokončit plnou lokální kontrolu, jeden commit a jediné Terra
p+n podle registrovaného postupu. Původní request/job viz report.

**Navrhované další kroky:** HA-05 — propojit živou kartu a automatické čtecí
sledování s tímto backendem. Pak skutečný omezený modelový pilot a fyzická
Mac/iPhone přejímka, až ve vlastním schváleném rozsahu.

**Technický důkaz:**325 cílených PASS: identity/fingerprint, dvojklik/dva klienti,
čtení/reload, cursor/gap/retence, generační a terminální ochrana, poškozený
zdroj, selhání zápisu/startu workeru, wake při shutdown, skutečný syntetický
process crash a legacy HTTP disconnect; RPC probe jen fake. Původní tělo
ProfileManager.send je po extrakci AST-shodné, včetně oprávnění/dokončení.
Pevná child-job vazba odmítne pozdější cizí doklad bez falešného Hotovo.
Finální plná lokální brána PASS: 3635 testů / 573,186 s, 31 SKIP; finální zdroj včetně child-job ochrany a oprav registrů.
Důkazy `data/private/ha04_20261112/`, bezpečný report
`reports/human_adam_ha04_server_work_20261112.md`. Bez skutečného modelového
tahu HA-04, živé UI přejímky nebo aktualizace vlastní hodinové poštovní kopie.

### 2026-11-12 12:29 CET — HA-05: živá karta a automatické čtecí sledování

Hotovo: Human–Adam lokálně zobrazuje aktuální práci v hlavičce a živý plán, veřejné komentáře, doloženou aktivitu a časy pod Práce / Probíhá. Čtecí sledování s cursorem obnoví stejnou práci po načtení, vypořádá gap/resync a zastaví se na konci. Editor, fokus/selection, starší chat i řeč zůstávají stabilní. Ztracené přijetí řeší pouze GET původní identity, nikoli další odeslání.

Rozhodnutí: Míla zadal HA-04 Willovi a Data pokračuje HA-05. Po stabilním 72e1015c byl jen Datův checkout fast-forwardován na HA-04, vlastní změny bezpečně uchované a vrácené. Veřejný filtr je nyní napojený za dosavadní thread/turn/owner/generation guard; důkaz doručení ani jednorázové oprávnění se nemění. Nové rozhraní nepřijímá raw reasoning ani tool args. Willovy soubory, procesy a jeho samostatné vydání nejsou měněné.

Další krok: HA-06 — doplnění pokynu do přesné práce na další zadání.

Navrhované další kroky: Případné vydání HA-05 a fyzickou Mac/iPhone/živou modelovou přejímku samostatně schválit. Pozdější HA-07/08 jsou zastavení a spotřeba celého průchodu; nejsou předstíranou součástí tohoto kroku.

Technický důkaz: 417 cílených testů OK / 17,214 s. Skutečný HA-04 public producer, observer a wire dispatcher ověřily plán před ACK, cizí turn/generaci, commentary-only a nezměněné doručení; retence kompaktního veřejného obsahu zachová trvalý ID soubor a idempotenci. 18 Node scénářů, 11 veřejných testů, 140 skutečných browser kontrol na pěti velikostech; ustálené popředí 723–733 ms ve fixtures, aktivní mobilní/desktop karta vizuálně zkontrolovaná. Plná brána 3648 testů OK / 534,548 s, 5 SKIP. Report human_adam_ha05_live_ui_20261112.txt. První plný UI běh ukončen při přijetí HA-04; závěrečná brána ověřuje celou spojenou verzi. Žádný skutečný App Server/model/služba ani p+n.

Doplnění ověření téhož kroku: po plné bráně už jen frontendová preflight blokace odeslání před připojením; 417 cílených / 17,214 s a finální statická brána OK, finální browser QA zopakované. Backend/payload/persistence proti plné bráně nezměněné.

### 2026-11-12 13:45 CET — HA-06: doplnění pokynu do původní práce bez nového tahu

Hotovo: V Práce / Probíhá je samostatné doplnění pokynu se stavem přijetí, odmítnutí či neověřeného doručení. Při konci tahu nebo chybě zůstává text rozepsaný. Hlavní draft, starší chat, fokus/výběr a řeč zůstávají stabilní. Deset doplnění míří do stejné práce; nevyvolá nový start.

Rozhodnutí: Míla výslovně zadal HA-06. Doplnění dědí pouze původní autoritu běžícího tahu. Trvalá identita a otisk před RPC, přesný expectedTurnId a owner/scope/connection/policy guard; žádný override ani automatický retry. Klientský proof dál vyžaduje právě jeden původní user item, výjimka je jen pro přesně evidované opt-in command IDs. Starší peer bez ověřeného korelačního schématu nedostane spekulativní RPC. Nová oprávnění ani souhlas s p+n nevznikají.

Další krok: HA-07 — zastavení s přesným výsledkem na další zadání.

Navrhované další kroky: HA-05 je podle Mílova vzkazu nasazený. Vydání HA-06 a skutečnou modelovou/Mac/iPhone přejímku samostatně schválit. U peer>=0.167 je ještě otevřené živé ověření metody/echo client ID; starší fallback recovery zůstává striktní a může ponechat delivery_unknown. Tento stav nepovolí další start.

Technický důkaz: 479 finálních cílených OK / 28,096 s; statická brána OK. 16 backendových a 4 HTTP scénáře s produkčním klientem/dispatcherem/Hubem/observerem/repository a syntetickým wire. Klientská, integrační a HTTP série deseti doplnění vždy jeden turn/start, původní sandbox/model; duplicitní příkaz, cizí tah/scope/generace, storage/caller/HTTP failure, restart, retence a závod dokončení bez replay. 15 Node scénářů a 130 skutečných browser kontrol na pěti velikostech PASS, mobilní/desktop formulář vizuálně zkontrolovaný. Plná brána PASS: 3669 testů / 585,097 s, 5 SKIP. Report human_adam_ha06_exact_append_20261112.txt; schéma/důkazní otisky mimo Git. Bez skutečné App Server relace, služby, placeného modelu nebo změny Willova checkoutu.


### 2026-11-12 18:03 CET — HA-06: uzavření ověření a lokální předání

Hotovo: Doplnění přesné běžící práce je lokálně dokončené a ověřené, připravené
k předání z Datovy větve. HA-05 je podle Mílova dnešního vzkazu již nasazený.

Rozhodnutí: Míla zadal porovnat finální zdroje s existující zelenou branou
a dokončit vlastní handoff, TVBCP i lokální checkpoint. Produkční zdroje ani
testy se při uzavření neměnily; shodná plná sada se neopakovala.

Další krok: Předat lokální checkpoint HA-06 k samostatnému rozhodnutí o integraci
a vydání; tento pokyn sám neschvaluje push ani nasazení HA-06.

Navrhované další kroky: HA-07 pouze na další zadání. Živá metoda/echo klientského
ID a fyzická Mac/iPhone přejímka zůstávají otevřené v samostatném rozsahu.
Striktní fallback po výpadku dál může ponechat delivery_unknown a neopravňuje retry.

Technický důkaz: Finální zelená logs/ha06_full_gate_final_20261112.log má
3669 testů / 585,097 s, 5 SKIP a Cockpit quality gate: OK. Všech 18 finálních
zdrojů/testů v ha06_source_receipt.json má shodné SHA-256; jejich poslední změny
předcházejí finálnímu běhu včetně opravy pořadí action inventáře. Bez dalších
změn kódu, nového modelového tahu, zásahu do main, Willova checkoutu či služeb.
Bezpečný manifest a otisk zeleného logu jsou v human_adam_ha06_exact_append_20261112.txt.


### 2026-11-13 12:43 CET — Testový SDK pilot: oddělení inicializace od RPC deadline

Hotovo: Místní Mac přejímku Vocabulary EN Míla přijal. Navazující testová oprava
odstraňuje nesprávné měření CLI/SDK inicializace do krátkého limitu určeného
pro záměrně mlčící RPC. Obchodní doručení ani oprávnění se nemění.

Rozhodnutí: Míla výslovně zadal pokračovat po přejímce galerie. Oprava se
omezuje na test_codex_sdk_socket_pilot.py: nejprve dokončit handshake s existující
standardní 3s mezí, potom nastavit původní 0,5/0,6s limit testované operace.
WebSocket negativní kontrola dál používá původní 1s inicializační limit.
Žádný limit produkčního klienta, approval, ledger či retry kontrakt se neupravuje;
SDK zůstává neadoptovaný syntetický pilot, není náhradou současného transportu.

Další krok: Místní oprava je ověřená plnou zelenou branou a uzavírá se
checkpointem tohoto zápisu. Integrace a vydání zůstávají samostatné; před
vydáním ověřit přesnou registrovanou vazbu Vocabulary EN na publisher.

Navrhované další kroky: Případné samostatné vydání již přijaté galerie a fyzická
iPhone přejímka. Historický MMTX obsahový audit má vlastní otevřený rozsah.

Technický důkaz: Tři pouze syntetická připojení měla inicializaci 1,1645 /
0,1965 / 0,1962 s; metody pouze initialize, initialized, thread/read. 71 cílených
testů PASS / 22,124 s s ResourceWarning jako chybou, včetně původního jediného
turn/start a delivery_unknown bez opakování. Plná brána: PASS — 3685 testů / 566,387 s, 5 SKIP, 0 failures/errors.
Finální log má SHA-256 faf515a0bd8401844afd181c862527c8d81fbf4ad8aaeeb8f308925d65ec512b.
Logy vocabulary_en_sdk_phase_targeted_final_20261113.log a
vocabulary_en_sdk_phase_full_gate_20261113.log; zdrojové otisky a měření
v ignorovaném data/private/vocabulary_en_sdk_phase_20261113/. Bez živého
App Serveru, modelové inference, nového vlákna, restartu, změny role či p+n.
