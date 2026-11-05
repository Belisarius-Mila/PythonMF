# Data → Will: 05/P1 App Server / Python SDK, etapy A, B a C

## Přejímka uzavřena — 2026-11-05 13:03 CET

Míla sdělil, že Will úspěšně dokončil technickou část přejímky (bod 2
předchozího dvoubodového postupu). Uživatelské body 1–4 už byly přijaté;
**přejímka 05/P1 je uzavřená**. Data nepřevzal technickou účtenku ani
neprovedl nový vlastní živý audit; jde o zápis potvrzení předaného Mílou.

Ponechat modernizovaný původní klient; SDK se neadoptuje. Pro 05/P1 nyní
není požadován další krok. Míla přechází k novému zadání. Jen dokumentační
zápis a lokální commit ve větvi Data, bez publikování či zásahu do provozu.

## Předchozí přejímka — 2026-11-05 12:41 CET

Míla oznámil nasazení C a potvrdil obnovu Safari během odpovědi na iPhonu
jako zcela úspěšnou. „Jednička“ z posledního návodu je původní bod 4:
**uživatelská přejímka bodů 1–4 PASS**. Nový živý audit nasazení Data neprovedl.

Zbývá pouze technický reconnect pro Willa podle reportu C: dvě spojení ke
stávajícímu socketu, stejný thread/model/oprávnění/cwd, zavření prvního a
ověření druhého. Bez restartu, turn/start či opakování zprávy. Po doložení
uzavřít přejímku 05/P1. SDK se neadoptuje. Tento zápis jen ve větvi Data;
bez změn kódu či služeb, nového push, deploy nebo integrace ze strany Data.

## Předchozí předání — 05/P1-C, 2026-11-05 11:58 CET

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
