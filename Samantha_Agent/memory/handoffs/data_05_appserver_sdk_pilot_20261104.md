# Data → Will: 05/P1 App Server / Python SDK, etapy A a B

## Aktuální převzetí Willem — 2026-11-05 11:08 CET

Míla výslovně schválil převzetí a druhé samostatné p+n commitů Data po
Willově e-mailovém vydání. Will zkontroloval 5363238b a začlenil UI změnu;
250 cílených testů v aktuálním main PASS. Konflikty paměťových souhrnů
sloučené, historie obou větví zachovaná. Předchozí tvrzení níže o chybějícím
oprávnění je historický stav, který tento Mílův pokyn překonal.

První balíček 3f3b5b25 je vydaný, CI 42006566022 success. Nyní druhé p+n
Datovy UI opravy; fyzický iPhone retest zůstává otevřený. Přesná původní
chyba telefonu nebyla prokázaná a žádný starý pokyn se nesmí opakovat.


## Předchozí přejímka ve větvi Data — 2026-11-05

05/P1-B je podle Míly pushnuté a nasazené; převzetí Willem doloženo v main
(`1b6fd61e`, `ccece787`). Přejímka: Mac bod 1 OK, iPhone bod 2 FAIL — dotaz
zmizí bez zahájení a bez chyby, stejný výsledek i při ad hoc otázce.
Lokální UI oprava řeší reprodukovanou ztrátu textu před POST a viditelnost
nejistého výsledku bez nového odeslání; 150 cílených testů PASS; plná Cockpit brána PASS: 2 374 testů, 5 PDF skipů.
Přesná příčina konkrétního telefonu zatím neprokázaná. HTTPS Serve čtecím
auditem odpovídá téže instanci Cockpitu. Report:
`human_adam_iphone_send_failure_20261105.md`.

Další krok: předat ověřenou lokální opravu Willovi; převzetí/push/nasazení
této opravy není aktuálně autorizované. Mobilní přejímku uzavřít až po reálném
úspěšném retestu. Neopakovat nejistý pokyn, nepřevádět SDK do produkce.

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
