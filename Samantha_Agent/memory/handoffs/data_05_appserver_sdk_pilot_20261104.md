# Data → Will: 05/P1 App Server / Python SDK, první etapa

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
