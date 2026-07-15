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

## Cockpit HTTPS pro mikrofon – 2026-07-15

Vzdálený Cockpit má vedle původního tailnetového TCP portu `8770` také soukromý
Tailscale Serve HTTPS vstup na portu `443`, který proxyuje jedinou lokální
instanci `127.0.0.1:8770`. Tailscale Funnel není zapnutý a Cockpit není veřejně
dostupný.

HTTPS je nutné pro browserové `navigator.mediaDevices.getUserMedia`; Tailscale
šifrovaný TCP tunel s HTTP URL není pro Chrome/Safari webový `secure context`.
Tailnetové HTTPS certifikáty byly zapnuty po Mílově výslovném souhlasu s tím, že
název stroje a anonymizovaný DNS název certifikátu budou v public Certificate
Transparency registru. Konkrétní tailnetový hostname do gitové paměti neukládat.

Kanonická konfigurace a kontrola je v
`scripts/migrate_cockpit_single_instance.py --apply`. Workflow:

- před změnou ověří Tailscale DNS a povolené certifikáty;
- zachová TCP forward `8770` a přidá private HTTPS `443`;
- HTTPS health kontroluje systémovým `curl`, protože Python.org CA store na
  tomto Macu nemusí přijmout systémově platný certifikát;
- vyžaduje shodný PID a code stamp lokální i HTTPS instance;
- při chybě konfigurace listener odstraní; každý Tailscale subprocess má pevný
  časový limit.

Ověření 2026-07-15: lokální a HTTPS health odpověděly HTTP 200 se stejným PID a
code stampem, Serve status ukázal HTTPS `443` do lokálního Cockpitu a původní TCP
`8770` zůstal zachovaný.
