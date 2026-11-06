# Data → další krok: 15/P2 přirozený hlasový rozhovor

## Aktuální stav — 15/P2-F, čekání na mikrofon v iPhone Chromu

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
