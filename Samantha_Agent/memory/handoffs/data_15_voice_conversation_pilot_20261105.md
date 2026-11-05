# Data → další krok: 15/P2 přirozený hlasový rozhovor

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
