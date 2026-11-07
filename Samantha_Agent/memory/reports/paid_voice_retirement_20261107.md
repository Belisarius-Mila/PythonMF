# Zrušení placeného hlasového rozhovoru 15/P2

Datum rozhodnutí: 2026-11-07 08:55 CET. Proud: layer-human-adam-development.
**Placený hlasový rozhovor není pro Agenta SDK Samantha relevantní.**
Míla požaduje úplné chirurgické odstranění kódu. Žádná náhrada, další placené
zkoušky nebo pokračování A–G. 05/P1 klient a SDK pilot tím nejsou rušeny.

## Stav provedení

Přesná globální brzda pro tento rozsah potvrzená. Odstraněno 14 verzovaných
souborů pilotu, 9 jejich .pyc a starý lokální reprodukční skript, celkem 10
generovaných souborů. Prázdný adresář panelu odstranil git apply. Osm návazných
souborů upraveno přesně podle předem ověřeného návrhu. Žádná jiná služba,
modelová role, klient ani audio funkce se nezměnily.

113 skutečných cílených testů PASS (role, registry audit, vyřazení panelu,
HTTP server/security, Human–Adam UI). Doplňková kontrola skutečné třídy
Handler bez serveru ověřila 5/5 bývalých GET/POST cest jako 404 bez čtení
akčního payloadu. Plná brána 2377 testů za 429,882 s, OK (skipped=5). Dřívějších 26
overlay testů zůstává dokladem předběžného přezkoušení, nikoli náhradou této brány.

## Odstraněné soubory

- `app/communication/voice_conversation_cockpit.py`
- `app/communication/voice_conversation_gateway.py`
- `app/communication/voice_conversation_pilot.py`
- `app/communication/voice_conversation_probe.py`
- `app/communication/voice_conversation_roles.py`
- `app/frontend/voice_pilot/cockpit.js`
- `app/frontend/voice_pilot/conversation.js`
- `app/frontend/voice_pilot/page.html`
- `app/frontend/voice_pilot/panel.js`
- `tests/test_voice_conversation_cockpit.py`
- `tests/test_voice_conversation_gateway.py`
- `tests/test_voice_conversation_pilot.py`
- `tests/test_voice_conversation_probe.py`
- `tests/voice_conversation_frontend.test.cjs`

Dále přesně vymezených 9 .pyc pilotu v app/communication/__pycache__ a
tests/__pycache__, plus vlastní .venv/reproduce_voice_timer.cjs. Žádný celý
__pycache__, prostředí .venv, SDK balíček nebo jiný hlasový modul se nemaže.
Po odstranění čtyř frontendových souborů byl odstraněn pouze prázdný adresář
app/frontend/voice_pilot; neznámý obsah by krok zastavil.

## Návazné úpravy

- `app/capabilities/registry.py`
- `app/cockpit.py`
- `app/communication/agent_roles.py`
- `app/communication/human_adam_ui.py`
- `config/agent_roles.json`
- `scripts/cockpit_quality_gate.py`
- `tests/test_capability_audit.py`
- `tests/test_cockpit_voice_frontend_retirement.py`

Odebral se jen import/instanciace a routing placeného panelu, jedno menu,
dvě pilotní capability a jejich count v auditu, role read_only_voice,
její speciální parserová větev a pilotní položky quality gate. Generické
extra_headers zavedené výhradně pro tento panel nemají dalšího volajícího ve
větvi Data a byly vrácené na původní podobu. Přidané jsou tři negativní
regresní testy k existujícímu testu vyřazení hlasového frontendu.

## Co zachovat

- Současný App Server/SDK klient a jeho testy, lokální runtime, sdílený socket.
- Běžné nahrávání pokynů a přepis /api/human-adam/transcribe, speech/speak,
  ostatní TTS, diktafon, předčítání, audio Camina a Matýska.
- Willovu e-mailovou práci a všechny jiné centrální modelové role.
- Historické reporty a původní veřejný JSON důkazu P2-C; reporty mají výrazný
  archivní štítek. Původní proof JSON a privátní účtenky/claimy/spotřeba/audio
  se nepřepisují ani nemažou. Nejsou to aktivní runtime moduly.
- Git historie a původní commity se nepřepisují. Zrušené A–G se samostatně
  nepřebírají ani nenasazují.

## Ověření návrhu před potvrzením

- 26 testů PASS v read-only překryvné kopii (role, capability audit, vyřazení
  frontendu včetně 3 nových kontrol). Overlay nahrazuje jen navržené moduly
  a čtení cest; původní soubory zůstaly nedotčené.
- Python/JSON syntax všech navržených zdrojů PASS, git apply --check PASS.
- Přesně 2 capability odebrané; všechny ostatní role bitově zachované jako JSON
  hodnoty. V navrženém gate/registry/roles nejsou odkazy na runtime pilotu.
- Tyto předběžné kontroly samy nebyly důkazem skutečného odstranění. Po
  potvrzení následovala aplikace návrhu a 113 skutečných cílených testů;
  konečný výsledek plné brány je uvedený v aktuálním stavu.

## Přesný další krok

Předat tento lokální rušící commit Willovi k převzetí do aktuálního main.
Samostatně povolené publikování/nasazení musí vyřadit starý běžící panel;
nevydávat historické opravy E/F/G. Soukromý execution-receipt.json v ignorovaném
.venv/paid-voice-retirement-review zaznamenává skutečné odstranění; potvrzuje
neexistenci zdrojů, shodu osmi úprav a nepřítomnost cizích mazání.

Pro převzetí na novější main: zachovat continuous_email i interior_architect
a další budoucí role, odčíst jen 2 hlasové capability od tamního počtu
(v Data 31→29, místní main při přípravě 33→31). Sloučit odstranění s novějšími
routami a testy, nepřepsat celý soubor starší verzí z Data. Nepřebírat
starší opravy E/F/G jen kvůli tomuto odstranění. Při konfliktu modify/delete
u souboru pilotu je zamýšleným výsledkem smazání placeného pilotu, nikoli
obnovení jeho starší verze. Po samostatně
povoleném p+n ověřit odstranění na nasazeném Cockpitu bez placených tahů.

V tomto kroku žádný push, deploy, restart služby, změna sdílených provozních
dat, běžící relace ani placený modelový start. Zrušení projektu neprokazuje,
že panel už zmizel ze staršího běžícího runtime.

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
