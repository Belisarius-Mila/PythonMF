# Data → Will: 05/P1 App Server / Python SDK, etapy A, B a C

## Přejímka 05/P1 uzavřená Willem — 2026-11-05 12:50 CET

- Míla výslovně potvrdil uživatelské body 1–4. Poslední technický reconnect nyní PASS, všech 17 živých kontrol. Starší otevřené přejímací položky níže jsou tím překonané.
- Současný klient a Unix WebSocket transport: A a B obnovily stejné existující idle vlákno; po zavření A čte B totožná metadata; znovupřipojené A vrací stejné vlákno i efektivní nastavení. Server handshake 0.163.0, původní procesy a socket nepřerušené.
- Resume pouze threadId + excludeTurns:true, bez přepsání instrukcí, modelu, provideru, cwd a oprávnění. Celý rollout i stav Cockpit session beze změny. Žádný turn/start, nové vlákno, replay, restart či placený modelový tah.
- Společné vydání 040fea77 a CI už potvrzené. SDK se neadoptuje. Kanonický handoff a TVBCP proudu layer-human-adam-development aktualizované společně; důkaz memory/reports/codex_p1_reconnect_20261105.md a logs/codex_p1_reconnect_verified_20261105.log.
- Will změnil jen hlavní checkout. Data zůstává ve vlastní větvi/worktree; nic se tam neintegrovalo ani nepřepisovalo. Další krok: čekat na Mílův úkol.

## Převzetí Willem k výslovně schválenému společnému p+n — 2026-11-05

- Zápis přejímky d50fccbd převzat jako 5ad99375, SDK pilot c49da146 jako
  4a337100. Kód pilotu/fixture/testů je byte-for-byte shodný se zdrojem Data;
  konflikty byly pouze v paměťových souhrnech. Novější e-mailové zápisy zachované.
- V hlavním checkoutu s Datovým odděleným interpretem 105 cílených testů:
  102 PASS, 3 historické schema SKIP kvůli checkout-relative .venv exportům.
  Všech 12 nových C testů skutečně PASS, ResourceWarning jako chyba.
  Běžné produkční prostředí novou volitelnou SDK knihovnu neinstaluje.
- Historické schema testy zvlášť v původním prostředí s exporty: 3 PASS;
  jejich zdroj i syntetický peer jsou shodné s main. Společná brána nově
  registruje také test_codex_sdk_socket_pilot; v produkční .venv zůstává
  volitelných 11 C případů SKIP, nikoli falešně deklarovaný PASS.
- Míla nyní výslovně autorizoval Terra p+n pro Willovy i Datovy commity.
  Předchozí omezení integrace/push v historických předáních tím jsou překonaná.
  SDK se neadoptuje, role a produkční transport zachované. Provozní výměna
  hodinového agenta patří k e-mailové opravě c846775b, nikoli k SDK pilotu.
- Důkazy: logs/data_sdk_c_integration_20261105.log,
  logs/data_sdk_c_main_tests_20261105.log. P+n a živé ověření teprve následují.

## Aktuální předání — 05/P1-C, 2026-11-05 11:58 CET

Míla schválil krok C a navazujícím „Funguje to!“ přijal bod 3 přejímky
(návrat na Mac / kontrola duplicit). Body 1–3 PASS podle uživatele; bod 4
a skutečný technický reconnect App Serveru zůstávají otevřené.

**C dokončeno lokálně: 105 cílených testů PASS (12 nových), statická brána
PASS.** Skutečné SDK 0.163.0 + CLI proxy 0.166.0 fungují nad syntetickým
proudovým Unix socketem, dva klienti zachovají společnou identitu vlákna,
uzavření proxy neukončí posluchač, nejisté výsledky se neopakují.
**CLI proxy není kompatibilní se současným Unix WebSocket transportem
Samanthy.** Pozitivní kontrola současným transportem nad stejnou fixture PASS.

Doporučení Data: ponechat modernizovaný původní klient, SDK neadoptovat.
Report a přesný další krok: `reports/codex_sdk_p1c_20261105.md`.
Nový kód pouze v samostatném pilotu, fixture a testech; produkce, závislosti,
role, sdílený socket a provozní data beze změn. Nula placených tahů.

Will má převzít testy a závěry C, zachovat novější paměť main a následně
samostatně ověřit bod 4 a read-only reconnect současného transportu bez
turn/start či restartu. Nyní žádný push, deploy, integrace ani živý audit.
Předání je souborové; přímý Willův agent zde není, převzetí nepotvrzené.
Data po lokálním commitu čeká.

## Předchozí přejímka — 2026-11-05 11:41 CET

Míla po úpravě potvrdil úspěšnou odpověď v Human–Adam na iPhonu a správnou
zkušební značku z předchozího tahu. Mac bod 1 OK, iPhone bod 2 nyní OK;
původní zmizení dotazu je po retestu uzavřené. UI oprava `5363238b` je
převzatá v main jako `6972ea5c`; původní A/B jako `1b6fd61e` a `ccece787`.

Zbývá bod 3 (návrat na Mac a duplicity), bod 4 (obnova stránky během práce)
a technický reconnect App Serveru. SDK se do produkce nepřevádí. Samotná
úspěšná odpověď tyto další scénáře neprokazuje.

Report `human_adam_iphone_send_failure_20261105.md` zachovává původní selhání,
reprodukci, 150 cílených testů a plnou bránu 2 374 testů s 5 PDF skipy.
Tento krok je pouze paměťový zápis výsledku od Míly: bez nových modelových
volání, runtime auditu, změny služeb, integrace, push nebo nasazení.

## Převzato Willem do main — 2026-11-05 00:53 CET

Míla výslovně schválil převzetí, kontrolu a společné p+n. Originály
607fc538 a 862b6225 byly převzaty jako 1b6fd61e a ccece787. Větev Data je
zachovaná a čistá. Společná cílená sada 192 testů: 172 PASS, 20 volitelných SDK SKIP,
živý handshake 0.163.0 a katalog úspěšné. Plná integrační brána prošla 2462 testy (2442 PASS, 20 SDK SKIP);
aktualizovaný kanonický handoff/TVBCP a log data_email_integration_gate_20261105.log.
SDK nadále není produkční závislost. P+n je autorizované, úspěch se doloží
přesnou účtenkou; starší omezení integrace níže jsou tímto pokynem překonaná.

## Předchozí lokální stav — 05/P1-B

Míla schválil pokračování 05/P1-B. Původní klient nyní žádá `excludeTurns:true`,
ověřuje připojený stabilní server od 0.163.0 před operací s vláknem, rozlišuje
final_answer a uchovává strukturované chyby bez jejich běžného logování.
SDK se neadoptuje; session hub, runtime, Cockpit a e-mailové moduly se nemění.
100 cílených testů PASS; úplná Cockpit brána PASS: 2 373 testů, 0 chyb a selhání,
5 přeskočených PDF testů bez ReportLabu.
Podrobnosti: `codex_appserver_p1b_20261104.md`; kanonický writeback je ve
stávajícím handoffu a TVBCP proudu `layer-human-adam-development`.

Další krok: Will převezme diff; integrace do main, nasazení a živá přejímka
zůstávají samostatně autorizované. Přímé převzetí Willem dosud nepotvrzené.

## Historický podklad — etapa A

Priorita: P1. Datum: 2026-11-04. Větev: `data/parallel-20261104`.
Rozsah: nové pilotní soubory, lokální commit; žádná integrace do main.

## Hotovo

- Ověřena globální CLI **0.166.0**, stabilní SDK **0.163.0** a jeho přibalená
  CLI **0.163.0**. Obě CLI pouze version/help/offline schema; služby nespouštěny.
- Izolovaný pilot skutečného SDK nad syntetickým stdio protějškem.
- **38 nových kontraktních testů**, s existujícími regresními moduly **79 PASS**.
- Rychlá statická brána PASS a samostatný pilot completed / `{"ok":true}`;
  úplná produkční a fyzická přejímka zůstává mimo rozsah etapy.
- Mapa stávajícího klienta, kompatibility a chybějících vlastností v reportu
  `codex_sdk_pilot_20261104.md`; přesné prostředí a schémata v přidruženém JSON.
- Žádný placený modelový tah, živý socket, změna sdílených dat, závislostí
  projektu, rolí, produkčního klienta, runtime, Cockpitu ani e-mailových modulů.

## Rozhodnutí a doporučení

Adopce SDK nebyla schválena ani provedena. Doporučení Data: **dílčí modernizace
původního klienta**, SDK zatím ponechat jako offline pilot.

SDK umí `include_turns=False` -> **`excludeTurns:true`**, phase, raw události,
JSON schema parametr a strukturované RPC chyby. Vysoká API nemá vlastní client
message ID ani trvalý delivery journal; jiné výchozí schvalování se nesmí převzít.
Turn failure z `run()` ztrácí strukturu; raw stream ji zachová. Unix socket jen
přes kandidátní `app-server proxy --sock`, živá kompatibilita zůstává neověřená.

## Rizika a otevřené body

- Syntetická kompatibilita není živá přejímka, entitlement modelu ani důkaz,
  jakou verzi nyní používá již běžící sdílená služba.
- Nikdy nepoužít výchozí `Codex()` jako náhradu sdíleného procesu.
- Zachovat `CanonicalSessionHub`, pending před akcí, `delivery_unknown`, přesný
  client ID a jediný recovery důkaz. Nejistá akce se nikdy automaticky neopakuje.
- Pilotní in-memory guard není určen do produktu a nepřežívá restart.
- Kanonický handoff/TVBCP nebyl měněn: zadání povoluje nové pilotní soubory.
  Jejich dorovnání patří do případného integračního kroku, ne do tohoto commitu.
- Přímý Willův agent není v této relaci dostupný. Toto je připravené souborové
  předání; skutečné převzetí není zatím potvrzené.

## Jeden další krok

Will převezme report a po samostatném rozhodnutí připraví **05/P1-B**: pouze
`codex_appserver.py` + testy — excludeTurns, final_answer a strukturované chyby,
bez SDK závislosti. Podrobný rozsah a přejímka jsou v reportu. Jeho e-mailový
agent tuto etapu nepotřebuje integrovat a může dál používat současný session hub.

Data po lokálním commitu čeká; push, nasazení, restart a integrace nejsou povoleny.
