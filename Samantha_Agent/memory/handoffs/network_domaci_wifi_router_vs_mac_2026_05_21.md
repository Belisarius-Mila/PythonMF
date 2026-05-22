Nazev: Network / Codex reconnect - domaci Wi-Fi router vs Mac rozliseni
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Mila hlasi opakovane reconnecty Codexu/ChatGPT pri praci ve VS Code / Samantha.
- Problem je kriticky, protoze realne brzdi praci a opakovane prerusuje dlouhe tasky.
- Cilem je uz netestovat od zacatku, ale presne rozlisit:
  - OpenAI/ChatGPT problem,
  - domaci Wi-Fi/router/linka,
  - MacBook/macOS network stack,
  - zbytky VPN/Tailscale/routovani,
  - DNS/HTTPS problem.

Co je hotove:
- Vznikl a byl opakovane pouzit `scripts/network_watchdog.py`.
- Watchdog loguje:
  - Wi-Fi zarizeni a IPv4,
  - default interface/gateway,
  - pocet `utun` rozhrani,
  - detekovane VPN procesy,
  - DNS nameservery,
  - ping na gateway,
  - ping na `1.1.1.1`,
  - DNS resolve,
  - HTTPS HEAD na `https://status.openai.com/`,
  - HTTPS HEAD na `https://chatgpt.com/`,
  - verdikt sondy.
- Logy jsou v `logs/network_watchdog/` a jsou ignorovane gitem.
- `logs/network_watchdog/` bylo pridano do `.gitignore`.

Klicova evidence z domaci Wi-Fi:
- Predchozi zachyceny stav 2026-05-21 kolem 16:01:
  - Mac mel IPv4 `192.168.1.14`.
  - Ping na `1.1.1.1` prosel cca 68 ms.
  - DNS resolve prosel.
  - HTTPS na `status.openai.com` a `chatgpt.com` timeoutoval.
  - Verdikt: `HTTPS_FAILURE`.
  - `utun_count=8`, VPN procesy podle zakladniho seznamu prazdne.
- Delsi domaci mereni `network_watchdog_20260521_161956_summary.md`:
  - 238 sond.
  - 216 OK.
  - 10 `NO_IP_CONNECTIVITY`.
  - 9 `HTTPS_FAILURE`.
  - 3 `OPENAI_STATUS_HTTPS_FAILURE`.
  - Vypadky byly prerusovane mezi cca 16:21 a 16:38.
- Po doplneni gateway pingu probehl kratky test `network_watchdog_20260521_173612_summary.md`:
  - 12 sond.
  - 12 OK.
  - Gateway odpovidala, internet i HTTPS OK.
- Rozhodujici 30min domaci mereni `network_watchdog_20260521_174112_summary.md`:
  - Started: `2026-05-21T17:41:12`.
  - Finished: `2026-05-21T18:11:12`.
  - Probes: 160.
  - Verdikty:
    - 131 OK.
    - 29 `NO_IP_CONNECTIVITY`.
  - Nejvetsi souvisly vypadek:
    - `2026-05-21T17:44:03` az `2026-05-21T17:58:46`.
    - cca 14 min 44 s.
  - Dalsi kratke vypadky:
    - `17:41:18` az `17:41:37`.
    - jednorazove kolem `17:43:42`.
    - jednorazove kolem `18:02:01`.
    - jednorazove kolem `18:10:59`.
  - Pri vsech sondach mel Mac stale Wi-Fi IPv4 `192.168.1.14`.
  - Default gateway byla `192.168.1.1`.
  - DNS nameserver byl `192.168.1.1`.
  - `utun_count=8`.
  - VPN procesy podle seznamu prazdne.
  - Z 29 non-OK sond:
    - 29x selhal ping na `1.1.1.1`.
    - 25x selhal i ping na gateway `192.168.1.1`.
    - 17x selhal DNS resolve.
    - 24x selhal OpenAI HTTPS.
  - 23x selhal ChatGPT HTTPS.

Klicova evidence z pracovni Wi-Fi:
- Pracovni retest `network_watchdog_20260521_204353_summary.md`:
  - Started: `2026-05-21T20:43:54`.
  - Finished: `2026-05-21T21:13:54`.
  - Probes: 320.
  - Verdikty:
    - 319 OK.
    - 1 `NO_IP_CONNECTIVITY`.
  - OK pomer: 99,69 %.
  - Jediny non-OK vzorek:
    - `2026-05-21T21:12:42`.
    - Mac mel IPv4 `10.0.0.110`.
    - Default gateway byla `10.0.0.1`.
    - Gateway ping byl OK.
    - DNS resolve byl OK.
    - OpenAI HTTPS byl OK `200`.
    - ChatGPT HTTPS byl OK `403`.
    - Selhal jen ping na `1.1.1.1`.
  - To nevypada jako realny rozpad Wi-Fi k routeru; spise jednorazova ztrata ICMP/kratky paketovy vykyv.
- Rucni pozorovani po doběhu watchdogu:
  - V `2026-05-21 21:33` se podle Mily na pracovni siti Wi-Fi odpojila tak, ze ji musel rucne znovu nahodit.
  - Watchdog uz v tu dobu nebezel, posledni pracovni log skoncil v `21:13:54`, takze tento vypadek neni zachycen v CSV/JSONL.
  - Tato informace znamena, ze Mac/macOS/Wi-Fi roaming nebo konkretni pracovni Wi-Fi stale nelze uplne vyloucit.
  - Zaroven ale 30min mereni v praci zustava mnohem cistsi nez domaci mereni.

Pracovni diagnoza:
- Toto uz nevypada primarne jako globalni vypadek OpenAI ani problem GPT Pro uctu.
- Nejdulezitejsi fakt: behem rozhodujiciho mereni casto nesel ani ping na domaci gateway
  `192.168.1.1`, zatimco Mac mel stale pridelenou Wi-Fi IPv4.
- Pracovni Wi-Fi retest je oproti domacimu mereni temer cisty: 319/320 OK proti domacim
  131/160 OK.
- To silne posouva podezreni smerem k domacimu prostredi:
  - domacimu Wi-Fi spojeni MacBook <-> router/AP,
  - routeru/AP samotnemu,
  - lokalnimu Wi-Fi/radiovemu ruseni,
  - domaci lince za routerem.
- MacBook/macOS Wi-Fi stack zustava mozny, zvlast kvuli rucnimu pracovnimu odpojeni
  Wi-Fi v 21:33. Po porovnani mereni je ale porad mene pravdepodobny nez domaci
  Wi-Fi/router/ruseni jako hlavni pricina Codex reconnectu. VPN/routing zbytky jsou
  mene pravdepodobne, protoze `utun_count=8` byl v obou prostredich, ale pracovni
  Wi-Fi mereni bylo temer ciste.
- Samotny ChatGPT stream muze vypadavat jako dusledek nizsi vrstvy: kdyz se rozpadne
  spojeni k routeru nebo verejne IP, dlouhy Codex stream spadne/reconnectuje.

iPhone hotspot stav:
- Mila zkusil iPhone hotspot.
- Fotky ve `~/Downloads`:
  - `IMG_8908.PNG`: iPhone ma zapnuty Osobni hotspot, `Povolit pripojeni ostatnim`
    zapnuto, `Maximalizovat kompatibilitu` zapnuto, iPhone na 5G.
  - `IMG_8909.JPG`: Mac hlasi chybu:
    `Zapínání osobního hotspotu na „iPhone“ selhalo. Zkontrolujte, zda je zařízení zapnuté a v dosahu počítače.`
- Hotspot test se tedy zatim nepovedl, protoze selhalo uz spojeni MacBook <-> iPhone,
  ne samotny internet pres iPhone.
- iPhone hotspot se prozatim odklada.
- Pokud se k nemu vratit:
  - nechat na iPhonu otevrenou obrazovku Osobni hotspot,
  - vypnout/zapnout hotspot,
  - vypnout/zapnout Wi-Fi na Macu,
  - pripadne pouzit USB kabel a `iPhone USB`, coz je pro diagnostiku jeste cistsi.

Nejblizsi dalsi krok:
- Pracovni A/B test uz probehl a silne ukazuje na domaci Wi-Fi/router/ruseni/linku.
- Doma udelat jeden nizkorizikovy zasah a hned pote opakovat watchdog:
  - restartovat domaci router/AP,
  - vyzkouset jine pasmo 2.4/5 GHz nebo sedet bliz routeru,
  - pokud je k dispozici, vyzkouset Ethernet/USB-C adapter,
  - potom spustit znovu:

```bash
cd ~/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5
```

- Potom vyhodnotit posledni summary:

```bash
ls -lt logs/network_watchdog | head
```

Jak vyhodnotit pracovni test:
- Pokud po domacim zasahu watchdog bezi stabilne:
  - hlavni vinik je domaci Wi-Fi/router/linka/ruseni.
- Pokud doma porad pada ping na gateway:
  - vinik je velmi pravdepodobne Wi-Fi spojeni/router/AP/ruseni, ne OpenAI.
- Pokud doma gateway drzi, ale pada internet/HTTPS:
  - resit router WAN, DNS, provider nebo filtraci.
- Pokud zacnou padat i jine site:
  - podezreni se presouva na MacBook/macOS network stack, Wi-Fi chip, VPN/Tailscale/routing
    historii nebo obecny systemovy problem.
  - dalsi kroky: novy macOS network location, reset Wi-Fi sluzby, docasne vypnuti Tailscale/VPN,
    test jineho Mac uzivatele nebo safe mode, podle recovery protokolu.
- Pokud se v praci znovu rucne odpoji Wi-Fi, idealni je spustit dalsi 30min watchdog
  prave tam, pripadne ho nechat bezet dele pri realne praci, aby se zachytil fyzicky
  disconnect nebo ztrata IPv4/gateway.

Seznam e-mail soubezny stav:
- Pri teto relaci vznikl rychly read-only skript `scripts/seznam_email_search.py`.
- Mila spustil hledani v uctu `miloslav.falta2@seznam.cz` pres IMAP.
- Hledani za roky 2011-2026 v INBOXu naslo:
  - `INBOX: 1998 kandidatu`.
  - ulozeno bylo 500 vysledku kvuli vychozimu limitu.
- Vystupy:
  - `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.csv`
  - `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.md`
- Chyba `zsh: command not found: --folders` byla jen dusledek zalomeni prikazu na dalsi radek bez `\`.
- Pokud bude potreba vice vysledku:
  - spustit prikaz na jednom radku a zvysit `--limit`, napr. `--limit 2500`.
- Pokud bude potreba ulozit prilohy:
  - pouzit `save-attachments` podle `folder` a `uid` z CSV/Markdown vystupu.

Co neni hotove:
- Neni jeste hotovy USB/iPhone tethering test.
- Neni jeste rozhodnuto, jestli restartovat nebo prekonfigurovat domaci router.
- Neni jeste zachycen pracovni manualni Wi-Fi disconnect ve watchdog logu.

Zmenene nebo relevantni soubory:
- `scripts/network_watchdog.py`
- `logs/network_watchdog/network_watchdog_20260521_174112_summary.md`
- `logs/network_watchdog/network_watchdog_20260521_174112.csv`
- `logs/network_watchdog/network_watchdog_20260521_174112.jsonl`
- `memory/infrastructure/macos_network_recovery.md`
- `memory/technical/session_recovery_rules.md`
- `memory/handoffs/network_https_reconnect_diagnostic_2026_05_21.md`
- `scripts/seznam_email_search.py`
- `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.csv`
- `data/private/email_seznam/seznam_pojisteni_smlouvy_2011_2026.md`

Bezpecnost / neukladat:
- Do memory neukladat hesla k e-mailu, app-specific passwords, tokeny, plne obsahy e-mailu
  ani privatni sitove konfigurace.
- `logs/network_watchdog/` a `data/private/email_seznam/` zustavaji lokalni a necommitovat.
- Pri praci se Seznam e-mailem neukladat obsah e-mailu do memory; vystupy zustavaji v `data/private/`.
