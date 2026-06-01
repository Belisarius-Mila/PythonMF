Nazev: Samantha Cockpit - globalni klavesova zkratka pres hotkey agenta
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-01

Co se resilo:
- Mila chtel spoustet nebo otevrit Samantha Cockpit co nejsnadneji globalni
  klavesovou zkratkou.
- Drivejsi cesta pres Apple Shortcuts a Finder/Automator Services byla
  nespolehliva: sluzba `Otevrit Samantha Cockpit` existovala a macOS mel ulozenou
  klavesu `Ctrl + Option + C`, ale stisk klaves nic nespoustel.
- Proto byla zvolena jina cesta: maly lokalni macOS hotkey agent pres Swift/Carbon
  `RegisterEventHotKey`, spusteny jako uzivatelsky `launchd` agent.

Co je hotove:
- Pridan zdroj hotkey agenta:
  `scripts/samantha_cockpit_hotkey.swift`.
- Pridan instalacni skript:
  `scripts/install_cockpit_hotkey_agent.sh`.
- Agent vola existujici `scripts/start_cockpit.sh`, takze pouziva stejnou
  idempotentni logiku jako prikaz `cockpit`: pokud Cockpit bezi, jen otevrit
  `http://127.0.0.1:8770`; pokud nebezi, spustit.
- Agent byl zkompilovan do soukrome ignorovane slozky:
  `data/private/cockpit/hotkey/SamanthaCockpitHotkey`.
- Byl nainstalovan LaunchAgent:
  `~/Library/LaunchAgents/com.miloslavfalta.samantha.cockpit-hotkey.plist`.
- `launchctl print gui/501/com.miloslavfalta.samantha.cockpit-hotkey` ukazal
  `state = running`.

Co neni hotove:
- Nic zasadniho. Zkratka byla rucne overena Milou.

Dalsi krok:
- Pouzivat `Ctrl + Option + Cmd + C` jako hlavni rychle otevreni Cockpitu.
- Alternativy zustavaji `cockpit` v Terminalu a URL `http://127.0.0.1:8770`.

Navrhovane dalsi kroky:
- Ponechat hotkey agenta jako hlavni cestu a Finder Services uz nepouzivat.
- Pokud by se problem vratil, zkontrolovat logy:
  `data/private/cockpit/hotkey.out.log`
  `data/private/cockpit/hotkey.err.log`
  `data/private/cockpit/hotkey_agent.log`
- Pri potrebe znovu nainstalovat:
  `scripts/install_cockpit_hotkey_agent.sh`
- Pokud bude treba agenta vypnout:
  `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.miloslavfalta.samantha.cockpit-hotkey.plist`

Zmenene nebo relevantni soubory:
- `scripts/samantha_cockpit_hotkey.swift`
- `scripts/install_cockpit_hotkey_agent.sh`
- `scripts/start_cockpit.sh`
- `scripts/open_cockpit.py`
- `~/Library/LaunchAgents/com.miloslavfalta.samantha.cockpit-hotkey.plist`
- `data/private/cockpit/hotkey/SamanthaCockpitHotkey`

Bezpecnost / neukladat:
- Agent neobsahuje hesla, tokeny ani citliva data.
- `data/private/cockpit/` je soukroma ignorovana slozka; binarku ani logy
  necommitovat.
- Agent pouze otevira lokalni URL a vola existujici startovaci skript Cockpitu.
