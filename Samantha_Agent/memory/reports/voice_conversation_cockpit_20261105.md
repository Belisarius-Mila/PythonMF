# 15/P2-D — Čtecí hlas připojený ke zdrojům Cockpitu

> **ARCHIV — ZRUŠENO rozhodnutím Míly 2026-11-07.** Placený hlasový rozhovor
> není pro Agenta SDK Samantha relevantní. Níže je historický průběh, nikoli
> aktuální plán nebo povolení ke spuštění, adopci či nasazení. Aktuální stav:
> paid_voice_retirement_20261107.md a kanonický handoff Human–Adam.


Stav: lokální implementace v Data worktree, nikoli nasazená služba.

## Historický stav — 2026-11-05 22:06 CET, Datův čtecí hlas v Cockpitu

### Hotovo
- Datova větev a5e401e6 je pravidelným merge zachovaná v main 11b4ce64; vlastní Datův worktree zůstává čistý na původním headu. Novější e-mail, Ateliér a původní App Server klient zůstaly zachované. 05/P1 je uzavřená 17/17; SDK neadoptované.
- Terra p+n kompatibilního kódu dokončeno: účtenka 6e9bbb2a6f7dbcd6f9e3f11cc2b88909, push/deploy confirmed, plná brána 2668 testů / 0 chyb / 31 SKIP, smoke 5/5 a protected_services_unchanged=true. Předtím 239 integračních kontrol PASS.
- Vlastní hodinový e-mailový LaunchAgent registrovaně upgradovaný 2fe0481e → 11b4ce64. Installed/owned/loaded/enabled; úplný business otisk, nastavení a Email politika před/po shodné, stará kopie i záloha zachované. První check already_completed, bez nového modelového posouzení či oznámení.
- Teprve po skutečném ověření instalovaného parseru přidaná přesná schválená read_only_voice role z Datova a5e401e6. GPT-Live 1 bez reasoning_effort, všechny předchozí bindingy nezměněné. 141 následných cílených kontrol PASS.
- Živé neplacené GET panelu HTTP 200: připravený existující proud, mikrofon vypnutý, cenový souhlas přítomný a žádná změna trvalých voice účtenek. Ateliér dál hlásí enabled/image_generation=true.

### Rozhodnutí
- Míla autorizoval samostatné Terra p+n Datova vedlejšího proudu i úklid. Závěrečný konfigurační checkpoint obsahuje jen schválenou hlasovou roli a provozní zápisy; konečný stav jeho p+n určuje účtenka logs/data_voice_role_release_20261105.log. Potvrzené vydání vyžaduje completed + push/deploy confirmed stejného headu.
- Žádný další placený hlasový start, mikrofon, mazání/reset, force push ani restart sdíleného App Serveru. Původní 47s probe je spotřebovaný; nikdy jej neopakovat.

### Další krok a otevřená přejímka
- Po návratu Míly praktický poslech a zvlášť cenově potvrzený rozhovor do 60 s. Mikrofon, iPhone/WebRTC, přerušování a subjektivní latence zůstávají otevřené; celý bod 15 tím není uzavřený. Hlas čte jen hrubý stav a neschvaluje ani nemění úlohy.
- Technický důkaz: logs/data_voice_code_release_20261105.log, data_voice_email_compat_upgrade_20261105.log, data_voice_role_activation_20261105.log, data_voice_role_targeted_20261105.log, data_voice_live_precommit_20261105.log. Závěrečný provozní audit: logs/data_voice_final_verified_20261105.log; GitHub CI obou přesných headů v data_voice_code_ci_20261105.log a data_voice_role_ci_20261105.log. Žádný nový TVBCP.


Historický výchozí stav: lokální implementace v Data worktree. Aktuální stav určuje rušící report 7. 11. 2026.
Proud: `layer-human-adam-development`. Větev: `data/parallel-20261104`.
Pokyn Míly: „Připoj čtecí hlas do cockpitu...“

## 2026-11-05 21:44 CET — Willovo integrační převzetí

Míla po dokončení Ateliéru výslovně zadal p+n i za tento Datův vedlejší proud
a úklid repozitáře. Will slučuje větev a5e401e6 do novějšího mainu; zdrojové
voice moduly, frontend i nové testy jsou byteově shodné s Data. Jeho vlastní
worktree zůstává čistý a nedotčený. Starší SDK části jsou už v mainu přijaté;
novější příjem fotek, e-mail, Ateliér i přejímka 05/P1 zůstávají zachované.

239 společných cílených kontrol PASS; plná integrační brána 2668 testů,
0 chyb, 31 přeskočených PASS (390,060 s). Zachované Email/Interior bindingy jsou
ověřené také novým kontraktem audio role bez reasoning_effort. Registry má 132
záznamů, 33 vysoce rizikových: dvě nové externí hlasové schopnosti jsou explicitně
potvrzované. CI nyní zahrnuje i samostatné změny voice testů. Existující místní
projektový credential je nakonfigurovaný; konstrukční kontrola nevolala síť.

Hlasová role z a5e401e6 je záměrně odložená do druhé fáze: nejdřív plná brána
a kompatibilní runtime, potom ověřený upgrade vlastní e-mailové kopie a přidání
pouze schválené read_only_voice role. Živý sdílený JSON při merge zůstal byteově
shodný. Už spotřebovaný 47s placený probe se neopakuje; WebRTC/mikrofon/iPhone
zůstávají uživatelská přejímka. Konečné účtenky budou v logs/data_voice_code_release_20261105.log
a logs/data_voice_role_release_20261105.log. Canonical handoff a stávající TVBCP
Human–Adam aktualizované současně, žádný nový TVBCP.

## Uživatelský výsledek

Human–Adam → Další → Čtecí hlas otevře samostatný panel `/human-adam/voice/`.
Původní chat zůstává otevřený. Panel ukáže serverem vybraný pracovní proud,
AI a cloudové zpracování mikrofonu, odhad ceny 0,05 USD za minutu a cenový
souhlas pro jednu relaci do 60 sekund. Až zaškrtnutí souhlasu a kliknutí
Začít rozhovor žádá mikrofon a poté zakládá jednu relaci.

Hlas čte jen povolené stručné výroky o stavu skutečného existujícího vlákna.
Nepředává historii, odpovědi chatu, soukromé dokumenty, cesty ani chyby.
Plochý CanonicalSessionHub.snapshot se výslovně převádí do obálky session;
kontrakt ověřuje skutečnou metodu snapshot, nikoli jen napodobeninu service.status.
Odpojený backend se neoznačí za potvrzeně běžící práci.
Nepřipojený proud je potřeba nejprve připojit obvyklým tlačítkem Human–Adam;
hlas sám nevytváří hub, neobnovuje vlákno ani nespouští App Server.
Přepnutí proudu nebo výměna vlákna původní vazbu zneplatní. Již spuštěná
hlasová relace může dál vést obecný rozhovor, ale nedostane stav jiného proudu.

Stop uvolní mikrofon a ukončuje jen hlas. Ztišení řeči neukončuje úlohu.
Prohlížeč má vlastní limit 60 sekund a nezávislý serverový watchdog hlídá
session.close/hangup. Spotřeba je konečná pouze po serverovém session.closed.
Nový rozhovor po ukončení je samostatné kliknutí: server povolí vypršení
původní browser cookie jen po uzavřeném účtu s finální spotřebou. Následující
stránka znovu vyžaduje cenový souhlas a Start. Původní účtenka se nemaže.

## Kontrakt a hranice

- Nová centrální role `read_only_voice`, GPT-Live 1, bez reasoning_effort a bez
  fallbacku. Cena a skutečná zkouška jsou doložené přenositelným JSON z P2-C.
  Textové role dál používají dosavadní App Server resolver. Do e-mailové role
  se nezasahuje; při převzetí na main zachovat také Willovo `continuous_email`.
- Server fixuje roli/digest, workstream/thread a snapshot callback. Klient posílá
  jen SDP a přesný cenový souhlas, nikoli model, profil, oprávnění či backendový nástroj.
- Browser cookie je HttpOnly, SameSite=Strict a pro vzdálený host Secure.
  Identifikuje pokus, ne člověka. Přístup zdědí povolené Host a privátní síťovou
  důvěru Cockpitu; nejde o novou osobní autentizaci. POST vyžaduje přesný Origin,
  CSRF a omezené JSON tělo. Dvojité autorizační hlavičky jsou odmítnuté.
- Trvalá create-only rezervace před placeným API přežije restart procesu.
  Dvojí kliknutí, refresh ani nejasná odpověď nevytváří druhou relaci.
  Neznámé vytvoření/ukončení blokuje další pokus pro tuto browser identitu;
  ruční mazání cookie či účtenky není postup obnovy a nesmí obcházet nejistotu.
- Nejvýše 256 dočasných browser kontextů, platnost hodinu. Přepisy pouze v paměti
  stránky; serverová účtenka neobsahuje audio, SDP, přepisy ani klíč. Budoucí
  runtime ukládá účtenky do privátní `communication/voice_sessions`, tento vývoj
  do sdílených provozních dat nic nezapisoval.
- API klíč je pouze na serveru z již zavedeného prostředí; žádné načítání dotenv
  hlasovým modulem, žádný alternativní provider ani nový balíček. Key chybí →
  bezpečné odmítnutí. WebRTC POST vytvoří session; nepřidává se session.start.
- K dispozici je jen stav, nikoli předčítání celé poslední odpovědi, psaní,
  schvalování nástrojů nebo řízení úloh. Hlasové „ano“ nedává oprávnění.
- Tvrdý pád celého serverového procesu ukončí i watchdog. Neuzavřená privátní
  účtenka zůstane blokovaná a vyžaduje audit/ukončení známé relace; automatická
  obnova nebo nový create nejsou implementované. Retence privátních účtenek
  a víceuživatelské přihlášení jsou mimo tento omezený pilot.
- Samostatný panel na iPhonu vyžaduje HTTPS (typicky současný Tailscale vstup).
  Autoplay může vyžadovat ruční Play v audio ovladači. Serverový limit není
  poskytovatelův fakturační strop.

## Ověření

120 cílených testů PASS; zahrnují 19 nových integračních kontraktů a rozšířený
Node scénář pro souhlas, browser bootstrap a nový rozhovor. Testy používají
syntetické snapshoty a provider, skutečné routy se ověřují přes Handler bez
spouštění místní služby. Žádný skutečný mikrofon ani API klíč se nepoužil.
Statická brána PASS. Plná brána: 2467 testů za 408,517 s, OK (skipped=5).

Pokryté jsou vazby kompatibilního i lazy proudu bez cold konstrukce, změna
výběru/vlákna/hubu, schválení modelu a proof, přesný Origin/CSRF/cookie,
konkurenční dvojí start, restart po nejistém vytvoření, owned close, explicitní
nový pokus až po finální účtence a inertní načtení skutečného panelu/skriptů.
Starší kontrakty zachování úlohy/socketu, sidebandu a konečné spotřeby zůstávají.
Doplňkově skutečný Handler POST bez socketu PASS (dispatch a mez těla) a
code-first kontrola s původním JSON PASS (textová role funguje, hlas je vypnutý).

Konečné testovací logy zůstávají lokálně ignorované: voice-cockpit-targeted.log,
voice-cockpit-final-static.log, voice-cockpit-final-gate.log ve vlastní .venv.
Předchozí nehotový běh byl po nalezení nesouladu plochého snapshotu zastaven;
není dokladem. Výše uvedených 2467 testů je nový celý běh po opravě adaptéru.

V tomto kroku nula placených relací. P2-C dokládá primární WebSocket se
syntetickým vstupem; nedokládá živý WebRTC/sideband, mikrofon ani iPhone.
Tyto fyzické přejímky jsou stále otevřené.

## Přesné převzetí a další integrační krok pro Willa

1. Převzít hlasové základy A `0e97e4de`, B `3c78092a`, C `e5f5a8f4`
   a kódový commit P2-D do aktuálního
   main řízeným integračním postupem. Nepřepsat vlastní main, e-mailový proud
   ani jeho role; sloučit KNOWN_ROLES jako sjednocení existujících rolí +
   read_only_voice. Do tohoto nasazení ještě nevkládat druhý konfigurační commit.
2. Ověřit bránu a po samostatném oprávnění nasadit kompatibilní kód registrovaným
   p+n workflow. Dosavadní JSON bez hlasové role musí fungovat; hlasový panel
   bude bezpečně neaktivní. Nikdy nepřidat novou roli do starého běžícího parseru.
3. Teprve na prokazatelně kompatibilním runtime převzít samostatný konfigurační
   commit s rolí read_only_voice, při zachování všech dalších main rolí.
   Pro změnu JSON role není potřeba nový placený probe: důkaz z P2-C je již
   skutečný a role ho kontroluje. Samotný tento vývoj nezadává p+n ani aktivaci.
4. Po samostatném povolení této publikace ověřit routu bez placeného startu.
   Míla si pak v panelu sám odsouhlasí jednu novou <=60s iPhone relaci.
   Připojený proud nechat běžet s neškodnou úlohou: dotaz na stav, přerušení
   řeči, ztišení, Stop, refresh a zachování původního úkolu/vlákna. Zkontrolovat
   finální spotřebu a žádný druhý create v privátní účtence. Výpadek nesmí vést
   k pokusu naslepo; bez konečného důkazu nic automaticky neopakovat.

Read-only kontrola místního main v tomto kroku (`b9b59c7d`) nenašla hlasové
pilotní moduly; před skutečnou integrací znovu ověřit aktuální obsah a závislosti.
Není to důkaz živého deploymentu.

Lokální commit kódu a oddělený commit konfigurace nejsou push ani nasazení.
Živé služby, main a společné provozní soubory se při tomto kroku neměnily.

## Změněné soubory

Kód a testy: app/cockpit.py; app/capabilities/registry.py;
app/communication/agent_roles.py; app/communication/human_adam_ui.py;
app/communication/voice_conversation_cockpit.py (nový);
app/communication/voice_conversation_roles.py (nový);
app/communication/voice_conversation_gateway.py (upřesnění kontraktu a chybové zprávy);
app/frontend/voice_pilot/page.html; panel.js; cockpit.js (nový);
scripts/cockpit_quality_gate.py; tests/test_voice_conversation_cockpit.py (nový);
tests/voice_conversation_frontend.test.cjs.

Oddělená konfigurace: config/agent_roles.json (pouze přidaná read_only_voice).

Projektový zápis: memory/ACTIVE_PROJECTS.md; memory/MEMORY_INDEX.md;
memory/LESSONS_LEARNED.md; memory/technical/capability_routing_rules.md;
memory/handoffs/data_15_voice_conversation_pilot_20261105.md;
memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md;
memory/tvbcp/architektura_komunikace_samantha.txt; tento report (nový).

Protokolové podklady: [oficiální WebRTC průvodce](https://developers.openai.com/api/docs/guides/voice-webrtc?api=live)
a [serverové řízení hlasu](https://developers.openai.com/api/docs/guides/voice-server-controls?api=live).
Skutečný cenový/modelový důkaz je v voice_conversation_probe_20261105.json;
WebSocket zkouška se tím nepovažuje za WebRTC nebo iPhone přejímku.

## P2-E — selhání vstupní browserové kontroly, 2026-11-06

Míla hlásí nasazení a při iPhone přejímce v Chromu obecnou hlášku
„Hlas vyžaduje HTTPS nebo localhost a podporovaný prohlížeč“.
Hlášku vyvolá OR tří různých stavů ještě před gUM a placeným create;
nelze z ní určit konkrétní příčinu ani tvrdit, že Chrome hlas neumí.
Dotaz na protokol adresy je zatím otevřený. Živý deployment nebyl auditovaný.

Lokální oprava cockpit.js rozlišuje secure context (včetně odlišného textu
pro HTTP a neuznané HTTPS), chybějící getUserMedia a chybějící RTCPeerConnection.
Zablokuje i checkbox souhlasu, aby zaškrtnutí neslibovalo dostupný Start.
Neoslabuje kontroly, nespouští mikrofon ani relaci a nemění jinou logiku.

77 testů PASS; Node scénář ověřuje nezabezpečené HTTP, neuznaný secure
context na HTTPS, chybějící mediaDevices/metodu, chybějící RTC a úspěšný
preflight bez volání mikrofonu. Statická brána PASS.
Plná brána z P2-D se neopakuje pro tuto úzkou frontendovou opravu.
Změněné implementační soubory: cockpit.js a voice_conversation_frontend.test.cjs;
dále kanonický handoff, TVBCP, Data handoff, index, ACTIVE_PROJECTS a LL-096.

Při HTTP je řešením skutečný privátní HTTPS vstup s platným certifikátem.
Pouhá záměna http za https na původním portu není konfigurace TLS serveru.
Localhost na iPhonu znamená samotný iPhone. Aktuální HTTPS URL ani Tailscale
Serve mapování se nesmí odhadnout. Změnu proxy nebo služeb tento krok neprovádí.

Podklady: [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
a [Tailscale HTTPS](https://tailscale.com/docs/how-to/set-up-https-certificates).
[Google: mikrofon v Chromu na iPhonu](https://support.google.com/chrome/answer/2693767?co=GENIE.Platform%3DiOS&hl=en)
potvrzuje přístup webů k mikrofonu; skutečnou WebRTC přejímku tím nenahrazujeme.

## 2026-11-06 23:13 CET — 15/P2-E: iPhone blokuje hlas před mikrofonem

### Hotovo
Obecná hláška byla rozdělena na nezabezpečenou stránku, chybějící mikrofonní
API a chybějící WebRTC. Při HTTP vysvětluje nutnost privátní HTTPS adresy a to,
že Tailscale ani localhost jiného zařízení nenahradí secure context.

### Rozhodnutí
Míla hlásí nasazení, ale přejímka na iPhonu v Chromu selhala před žádostí
o mikrofon a vytvořením relace. Konkrétní HTTP/HTTPS zatím neověřené; nelze
označit Chrome za nepodporovaný. HTTPS kontrola se neobchází, síť se nemění.

### Další krok
Ověřit protokol adresy na iPhonu; při HTTP otevřít skutečný privátní HTTPS
vstup Cockpitu, případně připravit jeho samostatnou provozní konfiguraci.

### Navrhované další kroky
Po odstranění browserové blokace samostatná krátká hlasová přejímka a finální
serverová spotřeba. Nejasný placený požadavek neopakovat.

### Technický důkaz
77 cílených testů PASS (pilot, Cockpit adaptér, gateway a Node browserové
scénáře). Statická brána PASS. Žádný mikrofon, placený start,
restart, push nebo nasazení Datou. Síťová ani modelová konfigurace beze změny.

## P2-F — čekání na mikrofon po přechodu na HTTPS

Čtecí audit v předchozím diagnostickém kroku našel existující privátní Tailscale
Serve HTTPS root pro Cockpit, ověřil validní TLS, health 200 a voice bootstrap
200; Funnel vypnutý. Konfigurace a služby se neměnily. Soukromá URL/IP se zde
neopisuje. Míla po otevření tohoto vstupu vidí funkční souhlas/Start, pak čekání
na oprávnění mikrofonu. To odpovídá fázi getUserMedia před broker.create.
Není to důkaz zamítnutí ani potvrzení příčiny na telefonu.

První instrukce je Ukončit rozhovor, potom iOS Nastavení → Aplikace → Chrome →
Mikrofon a oprávnění pro konkrétní HTTPS stránku. Google výslovně upozorňuje,
že vypnutý mikrofon na úrovni aplikace může zabránit zobrazení webové žádosti.
MDN uvádí i možnost, že se žádost o mikrofon nikdy nevyřeší.

Lokální úprava conversation.js rozlišuje čekání na mikrofon při původním
20s timeoutu od připojování; rozliší bezpečně jména chyb NotAllowedError,
SecurityError, NotFoundError a NotReadableError bez raw chybových textů.
Page.html dostal trvalou nápovědu. Bez změny časových limitů, oprávnění,
provideru, modelu, serverových rolí nebo politiky jediného placeného pokusu.

77 cílených testů PASS. Rozšířený Node kontrakt potvrzuje konkrétní chybové
texty, neuniknutí soukromé chyby, žádný opakovaný prompt/create, timeout během
čekání a opožděné povolení, které uvolní stopu bez vytvoření relace.
Statická brána PASS. Změněné soubory: conversation.js, page.html,
voice_conversation_frontend.test.cjs a kanonický projektový zápis.
Žádný skutečný mikrofon, placená relace, push, restart nebo deploy Datou.
Fyzické získání mikrofonu a hlasový rozhovor zůstávají otevřené.

Podklady: [Google — Chrome na iPhonu](https://support.google.com/chrome/answer/2693767?co=GENIE.Platform%3DiOS&hl=en),
[MDN — getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

## 2026-11-06 23:24 CET — 15/P2-F: čekání na oprávnění mikrofonu

### Hotovo
Panel vysvětlí povolení mikrofonu a dosavadní timeout odliší od chyby spojení.
Zamítnutí, chybějící nebo nedostupný mikrofon mají vlastní bezpečné instrukce.

### Rozhodnutí
Míla se přes HTTPS dostal ke Start a hlásí čekání na mikrofon. To je před
placeným create, příčina na telefonu zůstává neověřená. Nastavení telefonu,
serverový backend, role a provozní síť se nemění; žádný automatický retry.

### Další krok
Nejprve ukončit původní čekání, pak ověřit oprávnění pro Chrome a konkrétní
HTTPS stránku. Teprve poté jeden nový ruční Start s cenovým souhlasem.

### Navrhované další kroky
Po získání mikrofonu pokračovat přejímkou hlasu, Stop a finální spotřeby.

### Technický důkaz
77 testů PASS včetně čekajícího/nepovoleného mikrofonu a opožděného povolení
po timeoutu bez create. Statická brána PASS; žádné placené volání ani nasazení.

## P2-G — konkrétní chyba časovačů před getUserMedia

Míla po HTTPS zkusil Chrome i Safari; oba zůstaly na čekání na mikrofon.
Čtecí HTTPS audit 3 skriptů potvrzuje původní nasazenou implementaci D,
nikoli místní E/F. Permissions-Policy má microphone=(self). Samotný audit
nezkouší zařízení nebo žádost o mikrofon a nezakládá relaci.

Nasazený conversation.js SHA-256:
013904da18d2af128f0f0e218f4f3f7ac9d4d3f607487bdfdba311022dea8780.
Nasazený cockpit.js SHA-256:
da8e3677baeb7aa9223a0562b4ff444b1fe329c236465cbcae8917326596416c.

Chyba: konstruktor bere default setTimer=setTimeout a clearTimer=clearTimeout,
ale pak volá this.setTimer/this.clearTimer. Nativní browserová metoda tak
obdrží this=VoiceConversation. Startup timer se volá před try/getUserMedia,
proto při odmítnutí receiveru zůstane connecting a původní text, není timer,
není žádost o mikrofon ani placený create. Starší testy vždy injektovaly fake
timer bez tohoto browserového kontraktu; Node globální timer ho také nevynucuje.

Oprava je pouze ve výchozích wrappech přes globalThis.setTimeout/clearTimeout.
Není třeba měnit iPhone nastavení, model, grant, provider nebo délku limitu
pro tuto konkrétní chybu. Případná další platformní příčina zbývá fyzicky ověřit.

Reprodukce před opravou: TypeError: Illegal invocation: timer receiver,
microphoneCalls=0, timers=0, state=connecting. Po opravě ve stejném VM kontraktu:
error=null, microphoneCalls=1, timers=1; synteticky zamítnutý mikrofon vede
na disconnected a uklizený timer, paidCalls=0. Test výslovně používá defaultní
časovače, kontroluje receiver a nemaškaráduje tuto cestu injekcí fake do konstruktoru.

77 cílených testů PASS, statická brána PASS. Plná brána z P2-D není živý
browserový důkaz a pro tuto úzkou opravu nebyla opakovaná. Pokus otevřít
izolovaný browserový test přes CUA skončil „browser access host unavailable“;
nebyl spuštěn skutečný browser/mikrofon ani placená session. VM test není
fyzická iPhone přejímka.

Změněné implementační soubory: conversation.js (výchozí timer wrappery)
a voice_conversation_frontend.test.cjs (receiver kontrakt); dále kanonický
handoff, TVBCP, Data handoff, ACTIVE_PROJECTS, MEMORY_INDEX, LL-096 a tento report.
Původní bezpečnostní hranice (Stop, pozdní oprávnění, jeden create) beze změny.

Další krok pro Willa: převzít E 4bf110fd, F 73fdc08e a tento G v pořadí do
aktuálního main, zachovat e-mailové změny a role. Teprve po samostatném
oprávnění použít registrovaný p+n workflow. Po nasazení ověřit zdrojový asset
obsahuje globální wrappery a bez modelového startu funguje načtení. Pak Míla
jedním výslovným Start ověří žádost o mikrofon. Pokud se neukáže, zaznamenat
novou konkrétní chybu/timeout; žádný automatický nový placený pokus.

Podklad vazby globálních timerů: [HTML Standard](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#dom-settimeout).

## 2026-11-06 23:30 CET — 15/P2-G: časovač zablokoval žádost o mikrofon

### Hotovo
Opravená výchozí vazba setTimeout i clearTimeout na globální browserový objekt.
Nový kontrakt reprodukuje chybné this, které starší fake časovač nepodchytil.

### Rozhodnutí
Stejné chování Chromu/Safari nepřipisovat bez důkazu nastavení telefonu.
Čtecí audit potvrzuje původní nasazený controller. Výchozí timer může skončit
výjimkou ještě před getUserMedia; synteticky reprodukováno. Fyzický iPhone
stále není přijatý. Žádné obcházení oprávnění nebo automatický placený retry.

### Další krok
Will převezme E/F/G v pořadí, po samostatně povoleném nasazení ověří nový
asset a s Mílou jednou zkusí žádost o mikrofon přes HTTPS.

### Navrhované další kroky
Po získání mikrofonu ověřit rozhovor, Stop, zachování úlohy a finální usage.

### Technický důkaz
77 testů PASS. Před opravou receiver kontrakt: TypeError, 0 mic calls,
state connecting; po opravě bez výjimky, 1 mic call a čistý disconnected při
syntetickém zamítnutí, 0 paid calls. Statická brána PASS. Bez push či deploy.
