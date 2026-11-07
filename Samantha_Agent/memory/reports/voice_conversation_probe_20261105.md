# 15/P2-C — skutečný jednorázový probe GPT-Live 1

> **ARCHIV — ZRUŠENO rozhodnutím Míly 2026-11-07.** Placený hlasový rozhovor
> není pro Agenta SDK Samantha relevantní. Níže je historický průběh, nikoli
> aktuální plán nebo povolení ke spuštění, adopci či nasazení. Aktuální stav:
> paid_voice_retirement_20261107.md a kanonický handoff Human–Adam.


Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Výchozí commit: `3c78092a`. Proud: `layer-human-adam-development`.

## Výsledek

**Technická hlasová zkouška PASS.** Míla po volbě kandidáta výslovně schválil
také jednu skutečnou syntetickou zkoušku do 60 sekund s odhadem ceny 0,05 USD.
Byl odeslán právě **jeden session.start**, bez mikrofonu, soukromých dat,
textového backendového modelu, nástrojových akcí či App Server tahu.
Produkční role ani Cockpit se tím neaktivovaly.

| Metrika | Skutečný výsledek |
| --- | --- |
| Model | gpt-live-1 |
| Transport | primary WebSocket, žádná spuštěná místní služba |
| Vstup | syntetické ticho PCM16LE / 24 kHz a pevný český technický pokyn |
| Spuštění modelu | 1; společný create-only záznam před odesláním |
| session.started / session.closed | obojí potvrzené |
| Finální usage.seconds | **47,0 s** |
| Přepočet při 0,05 USD/min | **0,039167 USD**, odhad podle potvrzené délky, nikoli faktura |
| Celkový běh technického pokusu | 51,766 s |
| První audio od začátku pokusu | 4,648 s; zahrnuje připojení a startup, není to latence běžné odpovědi |
| Přijaté PCM | 2 139 840 B, obsahuje nenulový zvuk a průběžné tiché úseky |
| Kontrolní přepis | obsahoval český kontrolní marker hlas/pilot; text se do Gitu neukládá |
| Poslechová MP3 ukázka | 1,995667 s po lokálním odstranění krajního ticha, 8 493 B, full decode PASS |

API účtuje dobu hlasové relace, nikoli jen délku slyšitelné věty. Proto
krátká ukázka sama neodpovídá 47 sekundám spotřeby. Cena neobsahuje další
backendový model: žádný takový model v této zkoušce nakonfigurovaný nebyl.

Hlasová přejímka iPhonu, přerušování skutečné řeči, rozpoznávání mluveného
vstupu, subjektivní kvalita češtiny a WebRTC/sideband nad skutečným backendem
zůstávají otevřené. Marker a nenulové PCM nejsou důkaz přirozeného rozhovoru.

## První připojení a oprava TLS

První transportní pokus skončil po 0,163 s, **před pokusem o session.start**.
Nevznikl modelový start, session ID ani audio; jeho původní proof zůstal
zachovaný. Původní zachycení nezapsalo přesný typ výjimky, proto z něho
nelze zpětně tvrdit konkrétní traceback.

Neplacená místní kontrola následně prokázala, že výchozí TLS store tohoto
Pythonu neobsahuje CA soubor, CA adresář ani jedinou CA. To je samostatně
ověřená překážka bezpečného TLS. Bezplatný GET katalogu přes stávající
OpenAI SDK (bez retry) potvrdil přítomnost gpt-live-1. Žádný modelový tah
se tím nespustil.

Provider nyní explicitně používá CA bundle již instalovaného certifi,
stejně jako dosavadní OpenAI/httpx klient. Bundle obsahuje 118 CA; nadále
je povinné ověření certifikátu i hostname. Změna je pouze v novém voice
provideru, nikoli v systému, globálním Pythonu, společné .venv či klíčích.

Po opravě následovalo druhé **transportní připojení**, ale teprve první
modelový start v rámci původního schválení. Nový pokus musel ověřit hash
původního proof, totožnost grantu a jednoznačné `session_start_attempted:false`.
Před session.start vznikl společný create-only záznam v původním privátním
autorizačním adresáři. V případě byť nejistého modelového startu se další
spuštění blokuje napříč oběma adresáři. Žádný nejistý modelový požadavek
se neopakoval a původní záznam se nepřepisoval ani nemazal.

## Soubory a ověření

- Nový `voice_conversation_probe.py`: registrovaná jednorázová operace s
  explicitním grantem, syntetickými bindingy, primárním WebSocketem, časovým
  dohledem, tichým vstupem, kontrolou audia a finální spotřeby.
- `voice_conversation_gateway.py`: primární transport a explicitní ověřovaný
  TLS kontext pro HTTPS, WebSocket i sideband. Žádné nové SDK ani závislosti.
- `registry.py` a `capability_routing_rules.md`: samostatný vstup
  `probe_voice_candidate`, přesný souhlas, hlasové schválení blokované.
- Nový `test_voice_conversation_probe.py`: syntetické kontrakty jednoho
  startu, chybného spojení, nejasného odeslání, finální spotřeby, soukromí
  a pokračování jen po prokázaném stavu před modelovým startem.
- `test_capability_audit.py`: nový registrovaný vstup zvyšuje počet rizikových
  schopností z 30 na 31; očekávání upravené.
- `voice_conversation_probe_20261105.json`: přenositelný allowlist metrik,
  ceny a kontrolních hashů zdrojů/důkazů; bez klíče, session ID, přepisu a audia.
- `cockpit_quality_gate.py`: probe modul a jeho testy ve standardní bráně.
- Kanonický handoff, TVBCP, index, aktivní proud, Data handoff a relevantní
  reporty dorovnané ve stejném kroku. Žádný nový TVBCP.

**97 cílených testů PASS**, bez skipů; zahrnují 16 nových probe testů.
Python syntax a rychlá statická brána PASS. **Plná povinná brána PASS:
2448 testů, žádná selhání/chyby, 5 přeskočených PDF testů bez ReportLabu.**

Privátní důkaz a syntetická zvuková ukázka jsou pouze ve vlastní ignorované
`.venv/voice-candidate-probe/`, nikoli v Gitu či sdílených datech. Dva
transportní adresáře mají společný autorizační záznam jediného modelového
startu. Proof neobsahuje klíč, transcripty ani session ID; privátní journal
drží potřebné session ID pro původní případ. Zdrojový WAV zůstal zachovaný.

WAV SHA-256: `ce0d4ea86ee30f07a3d5cffde5084b3868e775a2d1d153f53677a94c1605b920`.
První proof SHA-256: `d9adbd299072befca3513db99c72c70e7b19fc7d72bd06d94e64fe309ecd2440`.
Hashy jsou kontrolní důkaz, nikoli identifikátory soukromého vlákna.
Přenosný JSON umožní pozdější kontrolu i mimo pracovní .venv; nenahrazuje
fyzický poslech a není potvrzením produkčního nasazení.

## Zdroje a další krok

- [WebSocket protokol](https://developers.openai.com/api/docs/guides/voice-websockets?api=live):
  primary endpoint, jediný session.start, PCM16/24 kHz, průběžné audio.
- [Úvodní promluva](https://developers.openai.com/api/docs/guides/live-conversations#greet-before-the-caller-speaks):
  developer input, následný commentary append a aktivní vstupní audio.
- [Finální usage](https://developers.openai.com/api/docs/guides/live-conversations#usage-and-graceful-close):
  konečné sekundy až ze session.closed, bez falešného potvrzení při výpadku.
- [Cena GPT-Live](https://developers.openai.com/api/docs/pricing): 0,05 USD/min
  hlasu po sekundách, další backend se účtuje zvlášť.

Nejbližší krok: Míla poslechne přiloženou ukázku; poté připravit integrační
etapu read-only pilotu do aktuálního Cockpitu. Ta musí mít kompatibilní
centrální voice roli bez předstíraného reasoning_effort, důvěryhodnou vazbu
na vybraný proud, kontrolu mikrofonu a spotřeby a vlastní iPhone přejímku.
Úspěšný probe sám neaktivuje produkční roli ani neautorizuje další placené
relace. Tento souhlas byl pro jedinou zkoušku a modelový start byl využitý.

Veškerý vývoj jen ve worktree Data. Žádný start/restart živé služby,
změna sdílených dat, push, deploy nebo integrace do main. Main a Willův
e-mailový proud zůstávají oddělené. Pro převzetí je základem A `0e97e4de`,
poté B `3c78092a` a tento navazující krok.
