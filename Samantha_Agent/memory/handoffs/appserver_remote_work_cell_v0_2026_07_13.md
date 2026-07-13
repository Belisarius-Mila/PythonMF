Nazev: App-server Adam Remote - izolovana zapisujici Work Cell v0
Priorita: 1
Stav: ceka na live canary a rucni retest
Pripomenout pri startu: ano
Datum: 2026-07-13

Co se resilo:
- Mila potvrdil, ze read-only LAB pres Tailscale funguje jako spojeni spolehlive,
  ale cil je skutecna vzdalena tvoriva prace, ne jen chat.
- Runtime audit nainstalovaneho Codex app-serveru potvrdil efektivni model
  `GPT-5.6-Sol`, podporu reasoning `low` az `ultra` a lokalni konfiguraci `high`.
- Puvodni LAB klient vsak kazdy turn explicitne prepisoval na `low`, read-only
  sandbox a zakaz nastroju. To vysvetluje plossi obsah bez dukazu slabsiho modelu.

Co je hotove:
- Puvodni read-only LAB zustava beze zmeny jako overena komunikacni a
  diagnosticka cesta.
- Nova `RemoteWorkspaceManager` pripravuje samostatny lokalni clone celeho
  `PythonMF` z commitnuteho `main` pres `--no-hardlinks`.
- Clone neobsahuje ignorovana `data/private/` ani nezarazene soubory hlavniho
  stromu a po vytvoreni nema zadny Git remote.
- Adam Remote pouziva explicitni model z runtime konfigurace, reasoning `high`,
  sandbox `workspace-write`, sit vypnutou a approval policy `never`; eskalace
  mimo izolovany workspace tedy nema kam projit.
- Developer instrukce vyzaduji AGENTS, MEMORY_INDEX, relevantni handoff, zakazuji
  sit, push, zmenu remote, destruktivni git a praci mimo izolovanou kopii.
- Cockpit ma samostatne tlacitko a modal `Adam Remote`, skutecny profil modelu,
  stav oddeleneho Git stromu, seznam zmenenych souboru, Context Capsule, pracovni
  chat, rucni TVBCP zapis a potvrzovany lokalni WIP checkpoint bez pushnuti.
- Checkpoint pred commitem odmita private, autosave, `.env` a binarni/media
  soubory; neznamou nebo castecne vytvorenou cilovou slozku nikdy neprepisuje
  ani nemaze.
- App-server klient ma obecny execution profil; vychozi parametry stareho LAB
  zustaly zpetne kompatibilni.
- Cileny blok dokoncil 263 testu a plna Cockpit quality gate 644 testu bez chyby.

Co neni hotove:
- Skutecna lokalni Remote Work Cell se zalozi az z commitnuteho/pushnuteho stavu,
  aby neklonovala starsi implementaci.
- Zivy `GPT-5.6-Sol` canary musi potvrdit nastrojovy zapis pouze uvnitr izolovane
  kopie a nulovou zmenu hlavniho stromu.
- Cockpit zatim nezobrazuje jednotlive tool eventy ani nema interaktivni approval
  round-trip. Proto v0 nema sit ani opravneni mimo izolovany workspace.
- Automaticky prenos WIP commitu z kopie na hlavni `main` zatim neni povoleny;
  nejdrive se ma zobrazit diff a predani ma zkontrolovat hlavni Adam.

Dalsi krok:
- Commitnout a pushnout git-safe implementaci, pripravit skutecnou Remote Work
  Cell, zalozit prvni thread a provest bezpecny zapisovy canary bez citlivych dat.

Navrhovane dalsi kroky:
- Rucne z iPhonu zadat prvni maly realny kodovy ukol a overit zmeny/testy/TVBCP.
- Dodelat asynchronni tool-event timeline a potvrzovaci kartu pro rizikove akce.
- Pridat kontrolovane tlacitko `Predat hlavnimu Adamovi`, ktere pripravi diff,
  handoff a navrh prevzeti na `main`, ale nic samo nepushne ani neslouci.
- Voice rezim B pozdeji smerovat do stejneho app-server threadu jako alternativni
  vstup/vystup, ne do TTY/screen bridge.

Zmenene nebo relevantni soubory:
- `app/codex_appserver.py`
- `app/codex_appserver_lab.py`
- `app/remote_work_cell.py`
- `app/cockpit.py`
- `tests/test_codex_appserver.py`
- `tests/test_remote_work_cell.py`
- `tests/test_cockpit.py`
- `scripts/cockpit_quality_gate.py`

Bezpecnost / neukladat:
- Necommitovat skutecny remote workspace, remote state, runtime thread/turn ID,
  obsah chatu, TVBCP, `data/private/`, autosave, `.env`, tokeny ani API klice.
- Hlavni nezařazeny soubor `AuditCockpit56_M.txt` nepatri do clonu ani commitu.
- Zadny automaticky push, merge, cherry-pick, mazani nebo prepis hlavniho stromu.
