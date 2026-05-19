# Tailscale Setup

Priorita: 2
Pripomenout pri startu: ne
Datum: 2026-05-20

## Ucel

Kratky operacni kontext pro Tailscale jako soucast vzdaleného pristupu. Tento
soubor nema obsahovat tajemstvi ani privatni konfiguraci.

## Kdy byt opatrny

- Po restartu Macu po sitovem incidentu nespoustet Tailscale jako prvni krok.
- Nejdrive overit obycejnou Wi-Fi, DHCP a web.
- Pri podezreni na konflikt VPN/Tailscale pouzit recovery protokol:

```text
memory/infrastructure/macos_network_recovery.md
memory/technical/macos_wifi_vpn_tailscale_recovery.md
```

## Diagnostika

```bash
ifconfig | grep utun
ipconfig getifaddr en0
ping 8.8.8.8
ping google.com
```

## Bezpecnost

Do memory neukladat auth key, node key, privatni IP mapy ani citlive casti
Tailscale konfigurace.
