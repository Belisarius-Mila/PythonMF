Nazev: Network / Codex reconnect - HTTPS failure diagnostika
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Mila hlasi opakovane reconnecty Codexu/ChatGPT pri intenzivni praci.
- Problem se nesmi dal brat jako drobna neprijemnost, protoze vyrazne brzdi praci.
- Cilem bylo rozlisit OpenAI vypadek, bezny Wi-Fi problem, DNS problem a lokalni
  HTTPS/routing/VPN problem.

Co je hotove:
- Overen oficialni OpenAI status/history: v danou chvili neni zjevny plosny
  vypadek, ale v historii existuji podobne incidenty typu Codex stream
  disconnecting intermittently.
- Vytvoren diagnosticky skript `scripts/network_watchdog.py`.
- Skript zapisuje do `logs/network_watchdog/` CSV, JSONL a summary.
- `logs/network_watchdog/` je pridano do `.gitignore`.
- Zachyceny dulezity lokalni stav 2026-05-21 16:01:
  - Wi-Fi mela IPv4 `192.168.1.14`.
  - IP ping na `1.1.1.1` prosel cca 68 ms.
  - DNS resolve prosel.
  - HTTPS na `status.openai.com` i `chatgpt.com` timeoutovalo.
  - Pocet `utun` rozhrani byl 8.
  - VPN procesy ze zakladniho seznamu nebyly aktivni.
- Nasledujici dvouminutove mereni 16:08-16:10 bylo cele OK: 22/22 probe OK,
  OpenAI HTTPS cca 207-343 ms, ChatGPT HTTPS cca 95-226 ms, ping obcas vyskoky
  cca 160-194 ms.

Pracovni diagnoza:
- Nejpravdepodobnejsi neni plosny OpenAI vypadek ani samotny GPT Pro ucet.
- Problem vypada jako kolisavy lokalni/trasovy HTTPS problem: Wi-Fi/IP/DNS mohou
  fungovat, ale TCP/HTTPS na webove sluzby se kratce zasekne.
- To je presne typ problemu, ktery muze rozbit dlouhy Codex stream, i kdyz bezne
  nacteni webu obcas vypada pouzitelne.
- Podezrele zustava vice `utun` rozhrani a predchozi zlepseni po
  `SAMANTHA_DISABLE_VPN=1 samantha`.

Co neni hotove:
- Neni jeste potvrzeno, zda za vypadky muze router/Wi-Fi, macOS network stack,
  Tailscale/VPN historie, DNS resolver routeru, nebo poskytovatel pripojeni.
- Neni jeste delsi mereni behem realne prace.
- Neni jeste porovnani proti hotspotu nebo kabelu/jine Wi-Fi.

Dalsi krok:
- Pri dalsi praci spustit v samostatnem terminalu:
  `.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5`
- Behem prace nechat bezet a pri reconnectu zkontrolovat aktualni summary/log.
- Pokud se znovu objevi `HTTPS_FAILURE` pri `ip_ping_ok=True` a `dns_resolve_ok=True`,
  resit primarne macOS/router/VPN/Tailscale/HTTPS trasu, ne OpenAI ucet.
- Prakticky test rozliseni: zopakovat watchdog na domaci Wi-Fi a pak na iPhone
  hotspotu. Pokud hotspot drzi, je podezrely router/domaci sit; pokud pada oboji,
  je podezrely Mac/VPN/network stack.

Zmenene nebo relevantni soubory:
- `scripts/network_watchdog.py`
- `.gitignore`
- `logs/network_watchdog/` - lokalni diagnosticke logy, necommitovat
- `memory/infrastructure/macos_network_recovery.md`
- `memory/technical/macos_wifi_vpn_tailscale_recovery.md`

Bezpecnost / neukladat:
- Do memory neukladat verejne IP, VPN konfigurace, tokeny, hesla ani privatni
  sitove detaily.
- Diagnosticke logy zustavaji lokalne v `logs/network_watchdog/` a jsou
  ignorovane gitem.
