Nazev: Cockpit na iPhonu pres Tailscale a ikonu
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-05

Co se resilo:
- Mila chtel otevrit Samantha Cockpit na iPhonu jednim kliknutim.
- SSH tunel v Termiusu nebyl ergonomicky, proto byla zvolena jednodussi varianta pres Tailscale adresu Macu.
- Cilem bylo nemit Cockpit vystaveny do bezne lokalni site, ale zp pristupnit ho pres privatni Tailscale sit.

Co je hotove:
- Cockpit bezi i na Tailscale adrese Macu: `http://100.89.150.6:8770`.
- Byla nainstalovana launchd sluzba:
  `com.miloslavfalta.samantha.cockpit.tailscale`.
- Sluzba pouziva `RunAtLoad` a `KeepAlive`, takze se ma spoustet pri prihlaseni na Macu a udrzovat proces bezici.
- Pribyl verejny instalacni skript:
  `scripts/install_cockpit_tailscale_launchd.sh`.
- Skript ma vychozi host `100.89.150.6` a port `8770`, ale umoznuje override pres:
  `SAMANTHA_COCKPIT_TAILSCALE_HOST` a `SAMANTHA_COCKPIT_TAILSCALE_PORT`.
- Byla vytvorena podepsana Apple Shortcut zkratka `Otevrit Samantha Cockpit.shortcut`.
- Zkratka byla ulozena mimo git do:
  `/Users/miloslavfalta/Documents/Shortcuts Playground/Otevrit Samantha Cockpit.shortcut`
  a zkopirovana do iCloud Drive:
  `iCloud Drive/Shortcuts Playground/Otevrit Samantha Cockpit.shortcut`.

Co neni hotove:
- Nebyl proveden retest po restartu Macu.
- Nebylo potvrzeno, jestli Mila nakonec pouzil `.shortcut`, nebo jednodussi Safari akci `Pridat na plochu`.
- Nebyl zaveden samostatny auth/login pro Cockpit; bezpecnost ted stoji hlavne na Tailscale pristupu.

Dalsi krok:
- Na iPhonu s aktivnim Tailscale otevrit `http://100.89.150.6:8770`.
- Pro ikonu na plose je nejjednodussi v Safari pouzit Sdileni -> Pridat na plochu.
- Alternativne otevrit `.shortcut` z iCloud Drive v aplikaci Soubory a pridat ji do Apple Zkratek.

Navrhovane dalsi kroky:
- Okamzity retest: po restartu Macu zkontrolovat, ze URL `http://100.89.150.6:8770` stale odpovida.
- Volitelne zlepseni: pridat do Cockpitu jednoduchy read-only stavovy radek, ktery zobrazi, zda je pristup pres Tailscale.
- Volitelne bezpecnostni zlepseni: pred sirsi praci z iPhonu zvazit lehke lokalni overeni nebo jednorazovy access token pro Cockpit.

Zmenene nebo relevantni soubory:
- `scripts/install_cockpit_tailscale_launchd.sh`
- `/Users/miloslavfalta/Library/LaunchAgents/com.miloslavfalta.samantha.cockpit.tailscale.plist` mimo git
- `/Users/miloslavfalta/Documents/Shortcuts Playground/Otevrit Samantha Cockpit.shortcut` mimo git
- `iCloud Drive/Shortcuts Playground/Otevrit Samantha Cockpit.shortcut` mimo git

Overeni:
- `launchctl print gui/501/com.miloslavfalta.samantha.cockpit.tailscale` ukazal `state = running`, PID `99531`.
- HTTP kontrola `http://100.89.150.6:8770` vratila status `200`.
- `zsh -n scripts/install_cockpit_tailscale_launchd.sh` proslo.
- Shortcuts Playground validace XML zkratky prosla.
- Podepsana `.shortcut` mela nenulovou velikost `22153` bajtu.

Bezpecnost / neukladat:
- Do handoffu nejsou ulozena hesla, tokeny, API klice, obsah dokumentu ani obsah e-mailu.
- `.shortcut` a plist jsou lokalni/mimo git vystupy.
- Cockpit obsahuje citlive workflow pro dokumenty/e-maily; pristup pres iPhone ma zustat omezeny na Tailscale a duveryhodna zarizeni.
