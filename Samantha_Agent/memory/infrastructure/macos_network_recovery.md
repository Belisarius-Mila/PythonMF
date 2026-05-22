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

## Aktualni diagnostika reconnectu 2026-05-21

Pro opakovane Codex/ChatGPT reconnecty vznikl read-only monitor:

```bash
.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5
```

Zachyceny dulezity stav: Wi-Fi mela IPv4, ping na IP adresu i DNS fungovaly, ale
HTTPS na OpenAI/ChatGPT timeoutovalo. To ukazuje spis na kolisavy lokalni nebo
trasovy HTTPS/routing/VPN problem nez na samotny GPT Pro ucet.

Detailni handoff:

```text
memory/handoffs/network_https_reconnect_diagnostic_2026_05_21.md
```

## Bezpecnost

Do memory neukladat hesla, tokeny, VPN konfigurace, privatni SSH konfiguraci ani
zbytecne verejne IP adresy.
