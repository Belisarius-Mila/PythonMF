# 15/P2-A — čtecí hlasový rozhovor, neaktivovaný základ pilotu

Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Výchozí commit: `95ed9cdb`. Proud: `layer-human-adam-development`.
Zdroj zadání: bod 15 návrhu `Samantha_navrh_rozvoje_a_kontinualni_agent_2026-11-04.txt`
v Downloads. Celý bod 15 není dokončený; toto je jeho první vývojový krok.

Aktuální navazující stav: Míla schválil kandidáta GPT-Live 1; serverový broker
je připravený v 15/P2-B. Placená zkouška čeká na samostatné potvrzení.
Viz `voice_conversation_p2b_20261105.md`; následující report je historický základ A.

## Co je připravené

Samostatný protokolový adaptér a WebRTC controller, které lze po doplnění
důvěryhodného serverového připojení použít pro dobrovolně zahájený čtecí
rozhovor. Běžný Human–Adam, jeho přepis do editoru a předčítání se nemění.
V pilotu existuje jen úzké čtení hrubého stavu aktuální práce: pracuje,
dokončení potvrzené, nejistý výsledek nebo neúspěch. Není to zatím čtení
dokumentů, práce s poštou, hlasové zadávání vývoje ani změny běžící úlohy.

Nové soubory:

- `app/communication/voice_conversation_pilot.py`: konfigurace protokolu
  GPT-Live s client delegation; jen konstrukce JSON, žádný síťový klient.
  Čtecí adaptér dostává serverem pevně navázaný snapshot a vlákno.
- `app/frontend/voice_pilot/conversation.js`: WebRTC životní cyklus, viditelný
  stav mikrofonu, ztišení přehrávání, konečný timeout, úklid pozdních výsledků,
  ukončení a potvrzení spotřeby. Chybějící broker blokuje i žádost o mikrofon.
- `app/frontend/voice_pilot/panel.js`, `page.html`: samostatný panel s českými
  popisky, AI disclosure, přepisem a ovládáním. Výchozí stav je neaktivní.
  Není routovaný z Cockpitu, automaticky nevolá mikrofon ani žádné API.
- `tests/test_voice_conversation_pilot.py`,
  `tests/voice_conversation_frontend.test.cjs`: syntetické kontraktní testy.

**Nic nebylo aktivováno ani nasazeno.** Žádný placený modelový tah, přístup
k mikrofonu, připojení k živému socketu, změna provozních dat nebo služby.
Requirements, společná `.venv`, stávající role i produkční zdroje beze změn.

## Proč tento směr

Návrh bodu 15 požaduje nejprve dobrovolný čtecí rozhovor, češtinu, iPhone,
přerušování, měření latence, skutečné spotřeby a zachování souhlasu v backendu.
GPT-Live umožňuje klientské předávání do vlastního backendu. Proto je
kandidátem hlasového rozhraní; nejde o změnu textového App Server modelu.
O připojení kandidáta, jeho roli a placené zkoušce zatím nebylo rozhodnuto.

Základ pilotu drží tyto kontrakty:

| Oblast | Implementace a důkaz | Zbývající přejímka |
| --- | --- | --- |
| Současný backend | Jen injektovaný snapshot stejného vlákna; žádný send, steer, cancel, connect či založení vlákna | Důvěryhodná integrace se skutečně vybraným pracovním proudem |
| Běžící práce po odpojení hlasu | Reálná metoda CanonicalSessionHub.snapshot nad syntetickým stavem; aktivní úloha zůstala identická | Živá dlouhá úloha a obnova prohlížeče |
| Oprávnění | Žádné zápisové callbacky ani modelové nástroje. „Ano“ a transcript jsou data | Fyzická zkouška nejasného českého souhlasu; budoucí zápisové akce vyžadují vlastní návrh |
| Kontext a soukromí | Jen hrubý stav; neexportuje historii, odpovědi, instrukce, cesty ani výjimky. store:false. Přepis pouze v omezené paměti relace | Volba a potvrzení přenosu živého mikrofonu do OpenAI; ověření politik účtu |
| Mikrofón | Žádost jen po spuštění; Stop uvolní vstup, pozdní oprávnění zastaví tracky | Safari/iPhone a skutečný HTTPS kontext |
| Přerušení | Lokální ztišení výstupu zachová mikrofon i backend; model GPT-Live podporuje full duplex | Skutečné barge-in, ozvěna, čeština a latence nebyly měřeny |
| Reconnect | Žádná automatická náhradní relace či opakování vytvoření; pozdní známé session ID předáno brokeru k jednorázovému úklidu | Server musí dohledat nejisté vytvoření a vynutit globální rozpočet; stav v pilotu nepřežívá restart |
| Události | started, transcripty, client delegation, cumulative usage, closed; limity paměti a deduplikace | Skutečná kompatibilita účtu a serverového sidebandu |
| Spotřeba | usage.seconds je kumulativní; konečná jen z platného session.closed. Výpadek bez něj zůstává nepotvrzený | Skutečná provider účtenka; zde pouze simulace |
| Autentizace / síť | Není přidaná žádná route ani credential path. Prohlížeč může poslat jen session.close; backendové appends patří serverovému sidebandu | Chybí autentizovaný broker, CSRF/origin brána, serverový watchdog a napojení HTTP routeru |
| Modelové role | Žádná aktivace ani změna config/agent_roles.json. Builder vyžaduje explicitně předaný model | Cenově schválený kandidát, skutečný syntetický probe a centrální role až po kompatibilním runtime |

## Ověřená dokumentace a cena — 2026-11-05

- [GPT-Live](https://developers.openai.com/api/docs/guides/live): hlas a vlastní
  backend mohou běžet nezávisle, WebRTC pro prohlížeč/mobil, klíč na serveru.
- [Client delegation](https://developers.openai.com/api/docs/guides/live-delegation):
  delegation událost obsahuje ID a metadata, nikoli zadání; transcript se
  zpracovává zvlášť. Oprávnění a provedení vlastní aplikace. Výsledek se
  vrací jako session.commentary.append se stejným delegation_id.
- [WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc?api=live):
  POST /v1/live/sessions, JSON session + transport, odpověď session.id a
  transport.sdp; po HTTP se znovu neposílá session.start. Audio je na media
  tracks, nikoli output_audio.delta v data channelu.
- [Vytvoření relace a oprávnění frontendu](https://developers.openai.com/api/reference/resources/live/methods/create):
  server nastaví allowed_client_events. Limity délky hovoru v tomto requestu
  nejsou konfigurovatelné; náš časovač není providerový fakturační strop.
- [Životní cyklus a spotřeba](https://developers.openai.com/api/docs/guides/live-conversations#usage-and-graceful-close):
  konečné usage.seconds se čtou ze session.closed; dřívější síťové uzavření
  konečnou spotřebu nepotvrzuje. Hlasový disconnect neruší klientský backend.
- [Cena](https://developers.openai.com/api/docs/pricing): **gpt-live-1 0,05 USD/min**,
  po sekundách, backend a nástroje zvlášť. Pro tento čtecí status pilot není
  navržen další generativní backendový tah, takže nevzniká jeho modelová cena.
- [Inicializace WebRTC](https://developers.openai.com/api/docs/guides/voice-latency-cost?api=live#webrtc-initialization-charges):
  vytvoření účtuje 15 sekund při inicializaci, započtených do běžící relace;
  není to dalších 15 sekund navíc. I nepovedený start tedy může mít cenu.

Příklad: běžící hlas 60 s ≈ 0,05 USD, 5 minut ≈ 0,25 USD. Nejde o zaručený
strop: watchdog a dohledání nejistého vytvoření musí být serverové. Neopakovat
POST při timeoutu. Přístup účtu k GPT-Live nebyl živě ověřen; přítomnost API
klíče by sama přístup ani financování nedokazovala. Není důvod klíč měnit
nebo předávat do chatu.

Izolované prostředí má openai 2.54.0 bez openai.resources.live. Nic se
neinstalovalo; protokolové typy zde SDK nevyžadují. Další integrace může
použít nový SDK pouze v izolaci, nebo odpovídající validovaný HTTP adaptér.
Současné App Server SDK a jeho role se k hlasu nepřepínají.

## Ověření

**132 cílených testů PASS, 0 skipů**, z toho **26 nových Python testů** včetně
jednoho Node kontraktu s řadou browserových scénářů. Další moduly: stávající
Human–Adam UI, session hub a přepis řeči. ResourceWarning je chybou.
Python compile, syntax všech tří nových JS/CJS souborů a rychlá statická
Cockpit brána PASS. Plná produkční brána se kvůli odděleným neaktivním
souborům neopakovala. Fyzický iPhone ani živý hlas nejsou přijaté.

```sh
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python -W error::ResourceWarning -m unittest tests.test_voice_conversation_pilot tests.test_human_adam_ui tests.test_communication_session_hub tests.test_speech_transcribe -v
node --check app/frontend/voice_pilot/conversation.js
node --check app/frontend/voice_pilot/panel.js
node --check tests/voice_conversation_frontend.test.cjs
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python scripts/cockpit_quality_gate.py --skip-unit-tests
```

## Další krok 15/P2-B a živá přejímka

Nejprve Míla vybere hlasového kandidáta a rozpočet. Navržený kandidát je
gpt-live-1, první syntetická hlasová zkouška do 60 sekund (odhad 0,05 USD
za běžící hlas). Nesmí používat soukromá data ani aktivovat produkční roli.
Je třeba samostatně ověřit dostupnost a skutečné finální usage. Tato zpráva
ani implementace nejsou souhlasem k placené zkoušce.

Pak doplnit důvěryhodný broker se serverovým sidebandem, jediným pokusem
vytvoření, nezávislým watchdogem, jednoznačným přidělením proudu a obnovou
nejistoty. Před aktivací nové role nasadit kompatibilní parser. Původní
HUB/task journal zůstává vlastníkem práce, nikoli hlasové spojení.

Živá přejímka má prokázat: výslovný start a viditelný mikrofon, českou
otázku na stav, přesné přerušení slyšitelné řeči, zachování úlohy po konci
hlasu, žádný druhý požadavek při výpadku, správné odmítnutí hlasového
„ano, odešli e-mail“, stav při blokovaném autoplay, skutečnou odezvu na
iPhonu a finální sekundy/cenu. Doplnění úlohy během práce je pozdější
autorizovaná etapa; do čtecího pilotu nepatří.

Main oproti této pracovní větvi pokročil zejména v cockpit.py a rolích.
Neproběhl merge/rebase ani zásah do Willova e-mailového proudu. Při pozdější
integraci přenést nové pilotní soubory a věcný stav paměti do aktuálního main,
nepřepsat jeho novější souhrny. Bez push, nasazení nebo startu služby Data.
