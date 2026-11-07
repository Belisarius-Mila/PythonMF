# Data → další krok: 15/P2 přirozený hlasový rozhovor

## Aktuální stav — placený hlasový rozhovor zrušen, zdroje odstraněné

### Rozhodnutí
- Míla 2026-11-07 rozhodl o kompletním zrušení placeného hlasového rozhovoru.
  **Placený hlasový rozhovor není pro Agenta SDK Samantha relevantní.**
  Bod 15/P2 je ukončen bez náhrady; žádné další placené zkoušky, adopce role,
  nasazování oprav E/F/G ani iPhone přejímka tohoto pilotu se neplánují.

### Hotovo
- Provedené přesné odstranění: 14 souborů pilotu, 10 jeho generovaných souborů,
  dvě capability, pouze role read_only_voice a zapojení do Cockpitu/brány.
- 26 testů návrhu v nedestruktivním overlay PASS, Python/JSON syntax návrhu
  a git apply --check PASS. Skutečné odstranění ověřené, 113 cílených testů PASS; plná brána 2377 testů OK (skipped=5).
- Historické reporty označené jako archivní. Původní důkazy spotřeby a účtenky
  se nemění; jejich existence neopravňuje k novému spuštění.

### Další krok
- Předat rušící commit Willovi k převzetí do aktuálního main; push/nasazení
  vyžadují samostatný pokyn. Starší opravy E/F/G se už nepřebírají.
  Přesná globální brzda pro tento rozsah byla potvrzená.

### Navrhované další kroky
- Po samostatně schváleném převzetí/nasazení ověřit zmizení placeného panelu
  a jeho API, zachování normálního Human–Adam, předčítání a audia Camina.

### Technický důkaz
- reports/paid_voice_retirement_20261107.md;
  .venv/paid-voice-retirement-review/manifest.json a remove-paid-voice.patch.
- Bez push, nasazení, restartu, placené relace nebo zápisu sdílených provozních dat.


## Historický stav — 2026-11-07 00:18 CET, společná integrace Willa a Daty

### Hotovo
- Do novějšího main s Willovým čtecím EventKit pilotem c0963d6b jsou převzaté
  Datovy commity 4bf110fd, 73fdc08e a 975f0900. Browserové assety a Node kontrakt
  jsou byteově shodné s Datovým 975f0900; jeho vlastní worktree se nemění.
- Hlasový panel rozlišuje HTTP/API/WebRTC, bezpečně vysvětluje čekání a chyby
  mikrofonu a opravuje receiver výchozích setTimeout/clearTimeout přes globalThis.
- E-mailová zdvořilostní politika, Ateliér, modelové role a samostatná hodinová
  služba zůstávají zachované. Kalendářový pilot je nadále pouze čtecí.

### Rozhodnutí
- Míla výslovně autorizoval převzetí a Terra p+n Willových i Datových commitů.
  Společné vydání přes registrované submit_release(wait=True), připnuté k Terře
  a výslednému schválenému merge headu; bez dalšího mikrofonu či placeného probe.
- Původní 47s hlasový probe je spotřebovaný a neopakuje se. Žádný restart
  sdíleného App Serveru, změna sítí nebo update vlastní e-mailové kopie.

### Další krok
Dokončit registrované společné p+n; autoritou jsou přesná účtenka a následné
živé ověření v logs/calendar_voice_release_20261107.log a
calendar_voice_verified_20261107.log. Potom Mílův samostatný iPhone Start a
poslech; fyzická přejímka mikrofonu/WebRTC/ceny se tímto kódem nepředstírá.

### Navrhované další kroky
Kalendářový bod 2 (výběr kalendářů a čtecí přehled) až jako další vývojový krok.

### Technický důkaz
Node browserový kontrakt a 114 cílených testů PASS, statická brána PASS dle
logs/calendar_voice_integration_targeted_20261107.log a
calendar_voice_integration_static_20261107.log. Plnou publikační bránu provede
vykonavatel. Soukromá data, žádosti o oprávnění a původní e-mail nepatří do Gitu.

## Historický stav — 15/P2-G, oprava browserového časovače před mikrofonem

- Míla hlásí stejné čekání na mikrofon v Chromu i Safari přes HTTPS.
- Nalezena konkrétní chyba panelu: nativní setTimeout/clearTimeout se ukládaly
  do instance a volaly s this=VoiceConversation místo browserového globálu.
  Výjimka při startup timeru vzniká před try/getUserMedia, takže zůstane hláška
  o čekání, aniž by se žádost o mikrofon vůbec provedla. Předchozí fake timer
  tento chybný receiver toleroval. Příčina na fyzickém iPhonu zbývá potvrdit.

### Hotovo
- Dva výchozí wrappery volají časovače přes globalThis. Nový VM kontrakt ověřuje
  defaultní cestu s browserovým receiverem, žádost o mikrofon a bezpečný úklid.
- Před/po synteticky: výjimka + 0 getUserMedia → bez výjimky + 1 getUserMedia;
  zamítnutí končí bezpečně bez create. Čtecí audit serveru ověřil starý asset.

### Rozhodnutí
- Žádné další pokusy na telefonu před nasazením opravy. Nelze zatím tvrdit,
  že příčinou je systémové nastavení nebo nepodporovaný Chrome/Safari.
- Bez změny časových limitů, grantu, jediného create, modelové role a služeb.

### Další krok
- Will převezme lokální opravy E/F/G (E a F jsou 4bf110fd a 73fdc08e), po
  samostatně povoleném p+n ověří zdroj a provede s Mílou jeden iPhone start.

### Navrhované další kroky
- Ověřit, že se žádost opravdu ukáže; až po získání mikrofonu rozhovor, Stop
  a finální spotřeba. Nejasný placený požadavek neopakovat.

### Technický důkaz
- 77 cílených testů PASS včetně regresního receiver testu; statická brána PASS.
  Browserový host pro skutečný UI test není dostupný, fyzická přejímka otevřená.
- Data nezapnul mikrofon, API ani živou službu, nic nepushnul a nenasadil.


## Historický stav — 15/P2-F, čekání na mikrofon v iPhone Chromu

- Po přechodu na ověřený privátní HTTPS vstup se panel otevře, souhlas aktivuje
  Start a Míla hlásí čekání na oprávnění mikrofonu bez dalšího postupu.
  Přejímka se dostala za původní blokaci HTTP; mikrofon/rozhovor nepřijaté.
- Doporučený první krok je Ukončit rozhovor, potom ověřit iOS Nastavení →
  Aplikace → Chrome → Mikrofon a oprávnění konkrétní HTTPS stránky.
  Skutečný stav přepínače/příčina čekání na telefonu zatím není potvrzená.

### Hotovo
- Lokálně srozumitelná žádost a nápověda v panelu, rozlišení čekání na mikrofon
  od připojování a bezpečné texty pro zamítnutý/nenalezený/nedostupný mikrofon.
  Dosavadní limit 20 s, explicitní Start a zákaz opakování create zůstávají.

### Rozhodnutí
- Žádné automatické opakování mikrofonu ani placené relace; nastavení telefonu,
  běžící služby a role se tímto vývojem nemění. Oprava dosud není nasazená.

### Další krok
- Míla ověří systémové a webové oprávnění Chromu, potom po ukončení původního
  čekání provede jeden nový vědomý start v HTTPS panelu.

### Navrhované další kroky
- Po skutečně získaném mikrofonu ověřit rozhovor, Stop a finální spotřebu.

### Technický důkaz
- 77 cílených testů PASS včetně timeoutu, Stop a opožděného mikrofonu bez create;
  statická brána PASS. Bez placeného volání, push, restartu či nasazení Datou.


## Historický stav — 15/P2-E, iPhone: upřesnění blokace mikrofonu

- Míla hlásí nasazení P2-D. V Chromu na iPhonu vidí při otevření panelu
  obecnou hlášku HTTPS/localhost/prohlížeč; hlasový rozhovor nepřijal.
  Nezávislý živý audit nasazení v tomto kroku neproběhl.
- Původní hláška spojuje chybějící secure context, mikrofonní API a WebRTC.
  HTTP je pravděpodobná příčina, konkrétní protokol iPhonu zatím není potvrzený.
  Tailscale šifruje síť, ale HTTP stránka tím nezíská browserový secure context.
- Lokální oprava rozlišuje tři příčiny, vysvětluje HTTP/Tailscale a localhost
  a při blokaci deaktivuje i cenový souhlas. Kontroly nevolají mikrofon ani API.
- 77 cílených testů PASS včetně rozšířeného Node browserového kontraktu.
  Statická brána PASS. Dřívější plná brána P2-D (2467/5 skipů)
  není novou fyzickou přejímkou. Hlas, modelové role a provozní síť se nemění.

### Hotovo
- Rozlišení secure_context / microphone_api / webrtc a výstižná další instrukce;
  nepodporované prostředí neumožní zaškrtnutím vyvolat placenou relaci.

### Rozhodnutí
- HTTPS požadavek se neobchází, síťové služby se nekonfigurují ani nerestartují.
  Pouhé nasazení není dokončená iPhone přejímka.

### Další krok
- Zjistit http:// versus https:// na iPhonu; při HTTP použít ověřený privátní
  HTTPS vstup Cockpitu. Konkrétní URL ani existenci TLS proxy neodhadovat.

### Navrhované další kroky
- Po odstranění blokace Mílův výslovně spuštěný krátký rozhovor a ověření Stop,
  zachování backendové úlohy a finální serverové spotřeby.

### Technický důkaz
- voice_conversation_cockpit_20261105.md; voice-https-preflight-tests.log v místní .venv.
- Jen Data worktree; bez push, nasazení, změny provozních dat a placené relace.


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

## Historický stav — 15/P2-D, čtecí hlas v Cockpitu (lokálně)

- Míla zadal připojení čtecího hlasu. Human–Adam má vstup Další → Čtecí hlas;
  oddělený panel je napojený na skutečný existující hub vybraného proudu.
- Cenový souhlas před jednou <=60s relací, centrální read_only_voice role bez
  reasoning_effort a s již skutečným důkazem P2-C. Nový rozhovor až po serverovém
  closed/final usage; refresh/restart/nejasný create nikdy nezaloží druhý pokus.
- 120 cílených testů PASS včetně 19 nových kontraktů a rozšíření Node scénáře;
  statická brána PASS. Plná brána 2467 testů OK (skipped=5). Report voice_conversation_cockpit_20261105.md.
- Jen vlastní worktree data/parallel-20261104: žádný push, deploy, restart,
  zápis sdílených provozních dat ani další placený modelový start. iPhone/WebRTC
  a skutečný mikrofon jsou stále otevřená přejímka; 05/P1 zůstává uzavřená.

### Hotovo
- Serverová vazba na původní vlákno, routy, mikrofon/Stop/spotřeba a explicitní
  nový rozhovor. Jen stručný allowlist stavu, žádné odpovědi/historie nebo akce.
- Ochrana Origin/CSRF/browser cookie, trvalý jediný create a nezávislý watchdog.
  Cookie je identita pokusu v síťové důvěře Cockpitu, nikoli osobní přihlášení.

### Rozhodnutí
- Souhlas s kandidátem a jeho skutečný probe doplnil pokyn připojit čtecí hlas.
  Kód je připravený odděleně od centrální role kvůli starému přísnému parseru.
  Vývoj neudělil oprávnění k push, nasazení ani dalšímu placenému testu Datou.

### Další krok
- Will převezme kód do aktuálního main se zachováním e-mailové práce a rolí;
  nasazení kompatibilního kódu musí předcházet aktivaci samostatné voice role.

### Navrhované další kroky
- Po samostatně povoleném p+n ověřit neplacené načtení panelu; až pak Mílův
  výslovně potvrzený <=60s iPhone/WebRTC rozhovor a finální spotřeba.
- Bez konečného serverového closed/final usage neopakovat placený pokus.

### Technický důkaz
- reports/voice_conversation_cockpit_20261105.md; handoffs/data_15_voice_conversation_pilot_20261105.md.


## Aktuální stav — 2026-11-05 19:11 CET, 15/P2-C

Míla schválil kandidáta i jednu skutečnou syntetickou zkoušku do 60 s.
**Technický probe GPT-Live 1 PASS:** jediný session.start, session.closed,
finální usage 47 s, přepočteně 0,039167 USD. První audio 4,648 s od začátku
pokusu; český marker a nenulové PCM potvrzené. 97 cílených testů PASS,
plná brána 2448 testů PASS s 5 PDF skipy.

První TLS připojení skončilo před session.start. Výchozí Python CA store
byl prázdný; explicitní existující certifi bundle opravil ověřování, bez
zásahu do systému. Druhé spojení použilo tentýž schválený grant, hash
původního proof a společný create-only model-start claim. Model nebyl
spuštěný dvakrát a žádný nejistý modelový požadavek se neopakoval.

Souhlas pro jednu zkoušku je využitý. **Žádný další placený modelový start
z tohoto grantu.** Nespouštět probe znovu, neuvolňovat claim ani nemazat
původní proof. Role, SDK, produkční backend a služby beze změn.

Mílův poslech je otevřený. Ukázka a privátní důkazy jsou ve vlastní
.venv/voice-candidate-probe/20261105-approved-1847-tls-fixed/ (listen.html,
synthetic-speech-preview.mp3, synthetic-output.wav, proof.json). Nepřenášet
session ID, klíč či audio do Gitu. Report reports/voice_conversation_probe_20261105.md.
Přenositelný bezpečný výtah metrik a hashů je vedle reportu v JSON; z něj
se nesmí odvozovat přijetí iPhonu, skutečného rozhovoru či produkční role.

Další krok: poslech, poté integrační read-only pilot do aktuálního Cockpitu
s kompatibilní centrální voice rolí. iPhone/WebRTC/sideband nad skutečným
backendem nejsou přijaté. Podkladem A 0e97e4de, B 3c78092a a tento krok;
main a Willovy e-mailové změny zachovat. Bez push, deploy nebo restartu.

## Historický stav — 2026-11-05 13:43 CET, 15/P2-B

Míla schválil kandidáta GPT-Live 1. Samostatná otázka na jednu placenou
syntetickou zkoušku do 60 sekund s odhadem 0,05 USD za běžící hlas zůstává
pending. Kandidáta znovu neschvalovat, placenou relaci zatím nevytvářet.

Připravený je neaktivovaný broker, sideband/watchdog, auth/Origin/CSRF adaptér
a trvalá rezervace grantu před jediným create. 91 cílených testů PASS;
plná brána 2429 testů PASS, 5 PDF skipů. Bez API volání, čtení klíče,
změny rolí/SDK, připojení do Cockpitu nebo publikování. Nová kandidátní
operace je registrovaná a hlasové testy jsou součást standardní brány.

Po potvrzení rozpočtu a délky provést jeden skutečný syntetický probe.
Nejistý výsledek neopakovat. Teprve po přijetí probe centrální role,
kompatibilní runtime a integrace do aktuálního Cockpitu; skutečná iPhone
přejímka zůstává otevřená. Podrobnosti: reports/voice_conversation_p2b_20261105.md.

B závisí na základu A `0e97e4de`; při převzetí obou kroků nejdříve A,
poté B. Zachovat novější main a Willův e-mailový proud. Poslední tři
kontroly zavření/HTTP jsou zahrnuté v 91 cílených testech; plný běh měl 2 429
testů před přidáním těchto tří případů. Žádný skutečný modelový důkaz.

## Historický základ 15/P2-A

Stav: první neaktivovaný základ 15/P2-A, celý bod 15 není dokončený.
Datum: 2026-11-05. Větev: data/parallel-20261104. Proud: layer-human-adam-development.

Hotovo:
- Načtený bod 15 návrhu z Downloads, aktuální hlasové UI a související paměť.
- Nový čtecí protokolový adaptér, WebRTC controller a samostatný neaktivní panel.
  Žádná změna současného backendu, HTTP routeru, rolí ani závislostí.
- 132 cílených testů PASS včetně 26 nových a Node browserového kontraktu;
  Python/JS syntax a rychlá statická brána PASS. Nula placených volání.

Rozhodnutí a hranice:
- Míla chce implementovat bod 15. Navržený první krok je čtecí hlas nad
  stávajícím backendem, bez ztráty běžících úloh a bez hlasového schválení akcí.
- GPT-Live s client delegation je kandidát, nikoli aktivovaný model či role.
  Hlasová cena ověřena 0,05 USD/min; skutečný přístup účtu neověřený.
- Pilot umí jen hrubý stav práce, ne volné hlasové zadávání či změny úlohy.

Otevřeno:
- Volba hlasového kandidáta a rozpočtu pro placený syntetický probe.
- Autentizovaný broker, serverový sideband/watchdog, trvalá evidence nejistého
  vytvoření, centralizovaná schválená role a připojení do Cockpitu nejsou hotové.
- SDK openai 2.54.0 nemá Live modul; nebylo upgradováno. Žádné klíče se nečetly.
- Čeština, přerušování, iPhone, skutečná latence a spotřeba zůstávají živá přejímka.

Další krok:
- Míla vybere kandidáta a rozpočet; návrh jednorázové zkoušky gpt-live-1 do
  60 sekund, odhad 0,05 USD za běžící hlas. Není to fakturační hard limit.
  Bez tohoto rozhodnutí nevytvářet placenou relaci ani novou produkční roli.

Důkaz a obnova:
- Report reports/voice_conversation_p2a_20261105.md obsahuje API zdroje,
  kontrakty, soubory, testy, omezení a přesný plán 15/P2-B.
- Kanonický handoff a TVBCP jsou stávající Human–Adam dokumenty. Přejímka
  předchozího 05/P1 zůstává uzavřená. Žádný nový TVBCP se nezakládá.
- Veškerá práce jen ve worktree Data; bez živých služeb, sdílených dat,
  push, deploy či integrace. Main mezitím pokročil; jeho novější paměť
  a Willovu e-mailovou integraci při budoucím převzetí zachovat.

## 2026-11-05 19:28 CET — 15/P2-D: připojení čtecího hlasu do Cockpitu (lokálně)

### Hotovo
Human–Adam dostal samostatný čtecí hlasový panel nad vybraným existujícím
vláknem. Mikrofon a jedna <=60s relace začínají až po cenovém souhlasu a Start.
Stop hlasu neruší úlohu, nový rozhovor vyžaduje serverově potvrzený konec.

### Rozhodnutí
Míla zadal „Připoj čtecí hlas do cockpitu...“. Přijatý GPT-Live 1 a skutečný
probe P2-C umožňují centrální read_only_voice roli; kód a konfigurace jsou
oddělené kvůli kompatibilitě starého runtime. Žádný push ani deploy zadán nebyl.

### Další krok
Will převezme kód do aktuálního main a zachová své e-mailové změny i role;
nejdříve samostatně povolené nasazení kompatibilního parseru, pak hlasová role.

### Navrhované další kroky
Po nasazení neplacená kontrola panelu, poté Mílův zvlášť potvrzený iPhone
rozhovor do 60 s s kontrolou úlohy, vlákna, Stop a finální serverové spotřeby.

### Technický důkaz
120 cílených testů PASS, z toho 19 nových integračních kontraktů; statická
brána PASS, plná brána 2467 testů OK (skipped=5). Report voice_conversation_cockpit_20261105.md.
Žádná nová placená relace, mikrofon ani změna živých služeb/provozních dat.

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

## 2026-11-07 08:55 CET — zrušení placeného hlasového rozhovoru

### Hotovo
Připravený přesný návrh vyřazení celého placeného pilotu 15/P2 včetně
frontendového panelu, brokeru/probe, role, API, capability a vlastních testů.

### Rozhodnutí
Míla projekt kompletně ruší: „není pro Agenta SDK Samantha relevantní“.
Starší kroky A–G jsou historické, nejsou pokynem pokračovat nebo je nasadit.

### Další krok
Po přesném potvrzení globální brzdy odstranit vymezené soubory a projít
skutečné cílené testy i plnou bránu. Zatím jde o ověřený návrh, ne hotové smazání.

### Navrhované další kroky
Později samostatně autorizované převzetí/nasazení odstranění do aktuálního
main; zachovat jeho novější role a Willovu práci. Bez další hlasové přejímky.

### Technický důkaz
14 verzovaných souborů a 10 generovaných souborů vymezených manifestem;
8 návazných souborů v návrhu upravených. 26 overlay testů a statické kontroly
návrhu PASS. Žádná změna živého runtime, placený start nebo mazání zdrojů.

## 2026-11-07 09:22 CET — placený hlasový rozhovor odstraněn po potvrzení

### Hotovo
Placený panel, jeho API, broker/probe, role a vlastní testy jsou odstraněné.
Odstraněno přesně 14 verzovaných a 10 generovaných souborů, prázdný adresář
panelu a osm navazujících úprav. Ostatní hlasové funkce a Camino zachované.

### Rozhodnutí
Placený hlasový rozhovor není pro Agenta SDK Samantha relevantní. Míla zrušil
projekt bez náhrady a přesnou globální brzdu pro tento rozsah potvrdil.
Historické A–G nejsou pokynem k pokračování, adopci nebo vydání.

### Další krok
Will převezme pouze rušící commit do aktuálního main se zachováním novějších
rolí a e-mailové práce; publikování/nasazení podléhá samostatnému oprávnění.

### Navrhované další kroky
Po povoleném nasazení neplaceně ověřit nedostupnost panelu/API a zachování
běžného Human–Adam, nahrávání pokynů a předčítání. Žádný další placený probe.

### Technický důkaz
113 cílených testů PASS, plná brána 2377 testů za 429,882 s OK (skipped=5).
Importy pěti modulů nedostupné; 5/5 bývalých GET/POST cest v Handler testu
vrací 404 bez akčního payloadu. Whitelist mazání shodný, App Server, lokální
runtime, e-mail, Camino a původní JSON důkazu P2-C beze změny. Bez push/deploy.

## 2026-11-07 — Will: společný balíček kalendáře 3 a zrušení hlasového pilotu

Míla výslovně schválil p+n včetně Datova rušícího `b4b72ab0`. Will jej
začlenil nad kalendářový `afb7c9cf`; starší hlasové opravy se samostatně
nenasazují. Bod 15/P2 je definitivně ukončen, historické přejímky E/F/G
ani iPhone Start již nejsou dalšími kroky. Data má dál vlastní worktree.

Při řešení konfliktů zůstaly všechny kalendářové a Ateliérové cesty i pět
ostatních rolí; odstraněná je pouze role read_only_voice a zapojení placeného
pilota. Na main se přebírá přesných 14 verzovaných odstranění; Datových deset
generovaných souborů se týkalo jen jeho worktree. Soukromé důkazy a audio se
nemažou. Běžné předčítání, nahrávání pokynů a audio Camina zůstávají zachované.
203 integračních testů PASS; po opravě zastaralého testu zakázané hlasové role
samostatně 10/10 PASS. Rychlá statická a plná publikační brána jsou podmínkou
vydání. Kalendářový vývoj před integrací: 2726 testů OK, 31 SKIP; jedno
syntetické živé modelové ověření PASS. Skutečný e-mail ani kalendář se neměnil.

P+n provede jediný registrovaný vykonavatel Terra pro project-email-cases
(společný Cockpit). Tento zápis vzniká před publikací; konečný provozní stav
určuje přesná účtenka a logs/calendar_draft_retirement_release_20261107.log,
čerstvé ověření logs/calendar_draft_retirement_verified_20261107.log.
Po dokončení ověřit 404 bývalého panelu/API, nové e-mailové UI a běžné audio.
Fyzická Mac/iPhone přejímka nového kalendářového editoru a oprávnění aktuálního
EventKit buildu zůstávají oddělené; bod 3 nevytváří kalendářové události.
