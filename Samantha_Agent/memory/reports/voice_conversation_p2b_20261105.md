# 15/P2-B — schválený kandidát a neaktivovaný serverový broker

> **ARCHIV — ZRUŠENO rozhodnutím Míly 2026-11-07.** Placený hlasový rozhovor
> není pro Agenta SDK Samantha relevantní. Níže je historický průběh, nikoli
> aktuální plán nebo povolení ke spuštění, adopci či nasazení. Aktuální stav:
> paid_voice_retirement_20261107.md a kanonický handoff Human–Adam.


Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Výchozí commit: `0e97e4de`. Proud: `layer-human-adam-development`.

Aktualizace: Míla následně schválil i jednu placenou zkoušku; skutečný probe
PASS s 47 sekundami je v `voice_conversation_probe_20261105.md`. Následující
report zachovává historický stav B před tímto schválením.

## Oprávnění a stav

Míla schválil kandidáta **GPT-Live 1**. Schválení modelu není automaticky
schválení placené zkoušky ani aktivace produkční role. Samostatná otázka na
jednu zkoušku do 60 sekund s odhadem 0,05 USD za běžící hlas zůstává pending.
Při této etapě se žádné API volání ani čtení klíče neprovedlo. Potvrzení se
nesmí odvozovat z uplynulého času, modelového přepisu ani předvolené volby.

Připravený je broker pro jednu kandidátní relaci. Není připojený do HTTP
serveru Cockpitu a neaktivuje se importem. Celý bod 15 stále není hotový:
zbývá živá zkouška, centrální produkční role, napojení do aktuálního Cockpitu
a fyzická hlasová přejímka na iPhonu. Předchozí 05/P1 zůstává uzavřený.

## Implementace a soubory

- Nový `app/communication/voice_conversation_gateway.py`: jeden serverový grant
  pevně váže vlastníka, schváleného kandidáta, vlákno/proud a dobu 15–60 s.
  Bez explicitního `confirmed_live_test=True` odmítne relaci vytvořit.
  Toto je jednorázový kandidátní probe, nikoli alternativní konfigurace role.
- `VoiceAttemptJournal` vytváří privátní záznam **před** síťovým požadavkem.
  Tentýž grant se neopakuje ani po restartu. Závod dvou procesových objektů
  má jediného vítěze díky create-only atomickému zápisu. Rezervace se nemaže.
- HTTP adaptér vyžaduje serverem ověřeného vlastníka, přesný HTTPS/localhost
  Origin a CSRF token. Prohlížeč dodá pouze SDP; nemůže vybrat model, thread,
  grant či operaci backendu. Host musí skutečné ověření uživatele zajistit
  sám; principal z JSON nebo libovolné klientské hlavičky nestačí.
- Provider používá pevné HTTPS/WSS endpointy OpenAI, jeden pokus, konečné
  timeouty a odmítá HTTP přesměrování. Nečte žádný env ani konfigurační soubor;
  klíč dostává až od důvěryhodného serveru. Transportní debug logger je
  potlačený, výjimky jsou obecné a bez serverového obsahu.
- Sideband obsluhuje backendové předávání. Reflektované audio události
  nemají event_id, proto se vyřazují ještě před protokolovým parserem.
  Neukládá se audio ani transcripty; do receipt nepatří SDP, klíč či backendový
  text. Adresář 0700, receipt 0600. Root úložiště musí dodat host explicitně.
- Snapshot reader má vlastní krátký limit a nejvýše jedno nedokončené čtení.
  Hlasová konverzace dostává jen hrubý ověřený stav, nikoli historii nebo
  instrukce. Výpadek nikdy nevolá send, steer, cancel, restart či nový thread.
- Nezávislý serverový supervisor ukončí hlas po časovém limitu i bez browseru,
  čeká na session.closed a teprve potom označí konečnou spotřebu za potvrzenou.
  Neznámý výsledek zůstává v journalu; hangup známé relace není doklad final usage.
- `app/frontend/voice_pilot/panel.js`: připravený same-origin broker pro
  session/close, CSRF, konečný timeout a jediný pokus o vytvoření. Samotné
  načtení stránky ani skriptu stále nespouští mikrofon a nevytváří relaci.
- `app/capabilities/registry.py`: nový záznam `create_voice_candidate_session`,
  externí operace s přesným potvrzením, hlasové schválení blokované. Nemění
  se config/agent_roles.json ani žádná stávající role.
- `tests/test_voice_conversation_gateway.py` a rozšířený
  `tests/voice_conversation_frontend.test.cjs`: syntetické kontrakty brokera,
  persistence, souběhu, autentizace, expirace a browserového HTTP klienta.
- `tests/test_capability_audit.py`: očekávaný počet rizikových schopností
  zvýšený z 29 na 30 kvůli novému přesně potvrzovanému kandidátnímu vstupu.
- `scripts/cockpit_quality_gate.py`: oba hlasové moduly a jejich testy i JS
  syntax jsou přidané do standardní brány. Dosavadní kontroly zachované.

## Základní scénáře a hranice

| Scénář | Očekávaný výsledek |
| --- | --- |
| Jen schválený kandidát, bez testového grantu | Žádný provider call, žádná rezervace |
| Cizí principal / Origin / CSRF / podvržený model | Odmítnutí před čtením snapshotu a před placeným požadavkem |
| Neplatný SDP nebo změněné vlákno | Žádné vytvoření relace |
| Stejný grant dvakrát, souběžně nebo po restartu | Nejvýše jeden create; po restartu nový pokus blokovaný |
| Timeout při vytvoření bez session ID | creation_unknown; nic automaticky neopakovat |
| Známé session ID, neplatná odpověď nebo chyba attach | Jednorázový úklid známé relace; finalization_unknown |
| Browser zmizí | Serverový watchdog běží dál, úloha Adama zůstává beze změny |
| Reflektované audio bez event_id | Zahodit, neukládat, nespouštět další akci |
| Stejné delegation ID opakovaně | Jediný čtecí callback, žádné zápisové nástroje |
| Chybí finální usage | Spotřeba zůstává nepotvrzená i po úspěšném hangup |
| Restart hosta s aktivním receipt | Nezakládat další hlas; explicitní audit původního receipt. Automatické přebírání relace není implementované |

Serverový časovač není providerový fakturační hard limit: zahrnuje latenci
ukončení a nemůže vynutit stop při pádu hosta nebo nedostupnosti sítě.
Grace period pro finální událost je 5 s, následný známý hangup je best effort.
U neznámého vytvoření bez ID nelze relaci tímto brokerem automaticky dohledat.
Tyto stavy nesmí být prezentované jako potvrzený konec nebo nulová cena.

## Oficiální kontrakty

- [Serverové řízení a sideband](https://developers.openai.com/api/docs/guides/voice-server-controls?api=live):
  attach na `wss://api.openai.com/v1/live/sessions/{session_id}/attach`, stejné
  projektové ověření, žádné nové session.start. Audio zůstává na primárním
  spojení. Reflektované audio události jsou bez event_id.
- [WebRTC vytvoření](https://developers.openai.com/api/docs/guides/voice-webrtc?api=live):
  JSON POST /v1/live/sessions; modelová konfigurace a klíč na serveru,
  browser obdrží pouze identitu relace a SDP odpověď.
- [Finální usage](https://developers.openai.com/api/docs/guides/live-conversations#usage-and-graceful-close):
  cumulative usage.seconds, finalizace až po session.closed. Klientský backend
  může pokračovat po ukončení hlasu.
- [Hangup endpoint](https://developers.openai.com/api/docs/guides/voice-sip?api=live#transfer-or-end-the-call):
  POST /v1/live/sessions/{session_id}/hangup pro známou relaci. Jeho skutečné
  chování pro kandidátní WebRTC relaci zůstává součástí živé přejímky;
  zde ověřeno pouze synteticky, ne jako živý providerový důkaz.
- Cena a initialization charge zůstávají popsané v reportu 15/P2-A; nic se
  neinstalovalo ani nepřepnulo na nový SDK.

## Ověření a další krok

32 nových Python testů brokera. S předchozím pilotem a capability moduly
**91 cílených testů PASS**, bez skipů, s ResourceWarning jako chybou.
První plná brána dokončila 2 429 testů s jedním selháním: audit měl původní
pevný počet 29 rizikových schopností místo nových 30. Očekávání je opravené
v test_capability_audit.py; všech 88 cílených testů včetně auditu PASS.
Plná povinná Cockpit brána **PASS: 2429 testů, 0 selhání/chyb a 5 PDF skipů**
(ReportLab není instalovaný). Python/JS syntax, whitespace a pip check PASS.

Plná brána zahrnula 29 původních brokerových testů. Tři dodatečné kontroly
(null ID, úklid transportu a case-insensitive HTTP hlavičky bez duplicit)
pokrývá konečná cílená sada 91 testů; broker má nyní celkem 32 testů. Logy jsou pouze
v ignorované `.venv`: voice-gateway-target-final.log a
voice-gateway-full-gate-final.log; původní selhání počitadla je zachované
ve voice-gateway-full-gate.log. Nejde o důkaz živého modelu nebo iPhonu.

Nejbližší krok: dokončit ověření, zapsat schváleného kandidáta a ponechat
placené vytvoření zablokované do výslovného potvrzení zkoušky. Kandidátní
volba sama nezměnila oprávnění k modelovým tahům.

Po přijaté skutečné syntetické zkoušce se teprve připraví kompatibilní
centrální hlasová role a napojení do aktuálního HTTP hosta Cockpitu. Stávající
produkční backend a modelové role se nepřepínají. Main mezitím pokročil;
převzetí musí zachovat novější e-mailový proud i jeho paměť. Bez push,
deploy, živé služby nebo sdílených provozních dat v této etapě Data.

Při převzetí je B závislé na základu A `0e97e4de` (protokolový adaptér,
controller a panel). Pokud A ještě není v cílové větvi, převzít nejprve A,
poté B. Žádné přepsání aktuálních modelových rolí ani integrace do main se
v této pracovní větvi neprovádí.
