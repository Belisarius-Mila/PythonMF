Nazev: App-server LAB - overeny textovy a lifecycle zaklad
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-13

Co se resilo:
- Po opakovane nespolehlivosti terminaloveho VoiceBridge byl stary transport
  zmrazen fail-closed a vznikl izolovany read-only LAB nad `codex app-server`.
- Cilem prvni etapy bylo dokazat prime textove predani bez simulace klavesnice,
  Terminal tabu, TTY markeru nebo AppleScriptu.
- Cockpit audit a optimalizace, samostatna aplikace i hlasova vrstva zustaly
  behem teto etapy zmrazene.

Co je hotove:
- Existuje fail-closed stdio transport pro `codex app-server` s explicitnim
  overenim `thread/start`, `thread/resume`, `turn/start`, `turn/started`, jedne
  user polozky, dokonceneho turnu a finalni odpovedi.
- Cockpit ma izolovany panel `App-server LAB` s novym vlaknem, resume,
  simulovanym odpojenim, restartem app-serveru a odeslanim textu.
- Kazdy pokyn ma viditelny cas kliknuti, prijeti Cockpitem, prijeti Adamem,
  potvrzeni turnu a dokonceni odpovedi.
- LAB ma soukromy stav mimo git, idempotentni client message ID a redigovane
  lifecycle dukazy bez obsahu konverzace.
- Automaticky reliability probe dokoncil 50 z 50 turnu bez chyby a duplicity,
  vcetne restartu po 25. turnu.
- Quality gate po lifecycle doplneni dokoncil 627 testu bez chyby.
- Mila rucne otestoval nove vlakno, odpojeni, resume, restart app-serveru a
  navazujici komunikaci. Interni kontrola potvrdila 7 z 7 dokoncenych pokynu,
  7 unikatnich turnu, prave jednu user polozku na turn, vsech pet casu a zadnou
  duplicitu ani chybu.
- Pri rucnim testu se menila identita spojeni i PID procesu a rostla generace
  spojeni, ale zustalo zachovano stejne vlakno. Lokalni a Tailscale metadata se
  shodovala.
- Stary Voice watcher zustal vypnuty a sam se nezapnul.

Co neni hotove:
- LAB zatim neni plnohodnotny Adam ani finalni UI Janičky.
- Neni hotovy Thread Registry ani kompaktní Context Capsule pro rizene predani
  mezi relacemi.
- Neni implementovane nahravani hlasu, prepis, prehrani odpovedi ani finalni
  TVBCP vrstva nad novym transportem.
- Neni overena obnova po restartu celeho Cockpitu nebo Macu ani dlouhodoby
  nekolikahodinovy provoz.
- Stary VoiceBridge kod zatim nebyl odstranen. Je zmrazeny jako nouzovy legacy
  kod a ma byt odstranen az po nahrade a dukladnem testu nove cesty.

Dalsi krok:
- Navrhnout a implementovat nejmensi Thread Registry + Context Capsule slice:
  stabilni identita vlakna, lidsky nazev/role, stav, posledni potvrzeny turn a
  kratke git-safe schema kontextu bez soukromeho fulltextu.

Navrhovane dalsi kroky:
- Automaticky otestovat create/resume/restart a idempotenci registru.
- Rucne overit volbu a navazani dvou oddelenych LAB vlaken z iPhonu.
- Teprve potom stavet plnohodnotny textovy chat Janičky bez VS Code.
- Hlas a TVBCP pridat jako dalsi samostatne vertikalni vrstvy nad overenym
  app-server transportem.
- Legacy VoiceBridge odstranit az po souhlasu Mily a uspesnem nahradnim retestu;
  zadne soubory nemazat automaticky.

Zmenene nebo relevantni soubory:
- `app/codex_appserver.py`
- `app/codex_appserver_lab.py`
- `app/cockpit.py`
- `scripts/codex_appserver_reliability_probe.py`
- `scripts/cockpit_quality_gate.py`
- `tests/test_codex_appserver.py`
- `tests/test_codex_appserver_reliability_probe.py`
- `tests/test_cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `scripts/samantha_screen_entry.sh`

Bezpecnost / neukladat:
- Necommitovat LAB state, texty otazek a odpovedi, thread/turn runtime logy,
  `data/private/`, `data/session_autosave/`, `.env`, tokeny ani API klice.
- Samostatna aplikace ma zustat private a zmrazena do vyslovneho rozhodnuti.
- Handoff zamerne neobsahuje text zadneho rucniho testu ani runtime identifikatory.
