# 15/P2-D — Čtecí hlas připojený ke zdrojům Cockpitu

Stav: lokální implementace v Data worktree, nikoli nasazená služba.
Proud: `layer-human-adam-development`. Větev: `data/parallel-20261104`.
Pokyn Míly: „Připoj čtecí hlas do cockpitu...“

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
