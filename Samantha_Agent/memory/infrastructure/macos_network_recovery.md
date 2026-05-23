# macOS Network Recovery

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Kratky rozcestnik pro obnovu internetu na Macu pri rozbitem Wi-Fi, DHCP, VPN nebo
Tailscale routovani.

Detailni postup je v:

```text
memory/technical/macos_wifi_vpn_tailscale_recovery.md
```

Offline karta pro pripad bez internetu:

```text
NETWORK_RECOVERY_CARD.txt
scripts/network_recovery_card.sh
```

## Kdy pouzit

- Wi-Fi vypada pripojena, ale internet nejde.
- `ipconfig getifaddr en0` nevraci IP adresu.
- Je podezreni na konflikt VPN, Tailscale nebo `utun` rozhrani.
- Hotspot nebo domaci Wi-Fi se chova nestabilne.

## Rychly postup

0. Pri startu Samanthy pouzit diagnostiku:

```bash
samantha
```

nebo pro pokus o ukonceni znamych VPN procesu pred startem:

```bash
SAMANTHA_DISABLE_VPN=1 samantha
```

1. Overit Wi-Fi rozhrani:

```bash
networksetup -listallhardwareports
```

2. Overit IP:

```bash
ipconfig getifaddr en0
```

3. Zastavit VPN/Tailscale procesy a obnovit DHCP:

```bash
sudo killall Tailscale
sudo killall WireGuard
sudo killall NEIKEv2Provider
sudo ifconfig en0 down
sudo ifconfig en0 up
sudo ipconfig set en0 DHCP
```

4. Test:

```bash
ping 8.8.8.8
ping google.com
```

## Aktualni kanonicky stav reconnectu 2026-05-23

Pro opakovane Codex/ChatGPT reconnecty vznikl read-only monitor:

```bash
.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5
```

Aktualni zaver po porovnani domaci a pracovni site:

- nejde primarne o globalni OpenAI vypadek ani GPT Pro ucet;
- domaci 30min watchdog mel 131/160 OK a 29 `NO_IP_CONNECTIVITY`;
- pri domacich vypadcich casto selhal i ping na gateway `192.168.1.1`, zatimco
  Mac mel stale Wi-Fi IPv4;
- pracovni Wi-Fi retest mel 319/320 OK a jeden nepresvedcivy non-OK vzorek;
- nejpravdepodobnejsi hlavni pricina je domaci Wi-Fi/router/AP/ruseni/linka;
- Mac/macOS Wi-Fi stack zustava mozny, hlavne pokud by zacaly padat i jine site,
  ale po A/B mereni je mene pravdepodobny nez domaci prostredi.

Aktualni dalsi krok:

1. Doma udelat jeden nizkorizikovy zasah:
   - restart routeru/AP,
   - jine pasmo 2.4/5 GHz nebo sednout bliz k routeru,
   - pokud je k dispozici, Ethernet/USB-C adapter.
2. Hned potom spustit watchdog:

```bash
cd ~/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5
```

3. Vyhodnotit posledni summary:

```bash
ls -lt logs/network_watchdog | head
```

Interpretace:

- Pokud po domacim zasahu watchdog drzi, hlavni vinik je domaci
  Wi-Fi/router/linka/ruseni.
- Pokud porad pada ping na gateway, vinik je velmi pravdepodobne spojeni
  MacBook-router/AP/ruseni, ne OpenAI.
- Pokud gateway drzi, ale pada internet/HTTPS, resit router WAN, DNS, provider
  nebo filtraci.
- Pokud zacnou padat i jine site, presunout podezreni na Mac/macOS Wi-Fi stack,
  VPN/Tailscale/routing historii nebo obecny systemovy problem.

Historicke handoffy:

```text
memory/handoffs/network_https_reconnect_diagnostic_2026_05_21.md
memory/handoffs/network_domaci_wifi_router_vs_mac_2026_05_21.md
```

## Bezpecnost

Do memory neukladat hesla, tokeny, VPN konfigurace, privatni SSH konfiguraci ani
zbytecne verejne IP adresy.
