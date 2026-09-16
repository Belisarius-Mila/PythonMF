# Camino Viewer — delta audit připravenosti domácího Macu

Datum auditu: 16. září 2026, 21:42 CEST

Tento read-only audit doplňuje C00 o nové požadavky v0.5. Nezměnil Tailscale,
Serve, napájení, FileVault, `launchd`, Cockpit ani uživatelská data. Neobsahuje
tailnet identity, adresy, tokeny ani soukromý obsah.

## Závěr

Současný Mac má použitelný základ pro pozdější Camino Viewer: na napájení je
nastaven bez systémového spánku, Tailscale je online, soukromý HTTPS Serve bez
Funnel už předává provoz do živého Cockpitu a Cockpit má spravovaný start.
Camino backend, worker, Viewer, viewer-safe úložiště, samostatná autorizace a
Viewer `launchd` služba však dosud neexistují. G8 je proto **NEPROVEDENO**.

Nový požadavek neblokuje dokončení probíhajícího C01b. Blokuje pouze tvrzení,
že P0 nebo Camino Viewer jsou připravené na cestu.

## Ověřený stav

| Oblast | Stav | Důkaz a dopad |
|---|---|---|
| Domácí/vývojový Mac | OVĚŘENO | Tentýž Intel MacBook Pro `MacBookPro16,3`, macOS 15.7.9, x86_64, 16 GB RAM. Dvě role jednoho stroje zůstávají oddělené provozním významem. |
| Volné místo | OVĚŘENO JAKO OKAMŽITÝ STAV | Datový svazek hlásil přibližně 62 GiB volných. Není to kapacitní rozpočet celé cesty ani nezávislá záloha. |
| Tailscale klient | OVĚŘENO | Verze 1.102.4, backend `Running`, místní uzel online, MagicDNS dostupné. Přesná identita a adresy nebyly zaznamenány. |
| Tailscale Serve | ČÁSTEČNĚ OVĚŘENO | HTTPS 443 je nakonfigurované na loopback Cockpitu 8770. Funnel není povolený. Samostatná cesta/URL a oprávnění Vieweru nejsou vytvořené. |
| Cockpit | OVĚŘENO PRO SOUČASNÝ PROVOZ | Read-only smoke kontrola `home`, `server_health`, `live_status`, `status` a `recovery` prošla 5/5. Ve zdrojích zatím není Camino link ani Viewer health. |
| Spravovaný start Cockpitu | OVĚŘENO | Uživatelské `launchd` jednotky Cockpitu a Tailscale bridge jsou načtené s `RunAtLoad` a `KeepAlive`. Camino/Viewer jednotka nebyla nalezena. |
| Napájení a spánek | ČÁSTEČNĚ OVĚŘENO | Na AC je `sleep=0`, `disksleep=0`, displej může zhasnout; na baterii je `sleep=1` a Low Power Mode. Dlouhý běh, zavření víka, výpadek napájení a tepelná zátěž nebyly fyzicky prověřené. |
| FileVault a restart | ČÁSTEČNĚ OVĚŘENO | FileVault je zapnutý. Současné služby jsou uživatelské LaunchAgents; dostupnost před přihlášením a návrat Vieweru po skutečném restartu nebyly testované. |
| Záloha | NEOVĚŘENO PRO CAMINO | Registrovaný stav zálohy repozitáře je v třídenním intervalu, ale nejde o nezávislou zálohu budoucích médií a databáze Camino. |
| Janina zařízení a jiná síť | NEPROVEDENO | Nebyla ověřena autorizace zařízení, Safari na jejím MacBooku/iPhonu ani přístup mimo domácí Wi-Fi. |

## Nejmenší cílová architektura

1. Camino backend, worker a Viewer poběží jako samostatné procesy na loopbacku;
   Cockpit zůstane pouze stavovým panelem a odkazem.
2. Tailscale Serve zpřístupní jen explicitní Viewer cestu/službu uvnitř
   autorizovaného tailnetu. Současný root Cockpitu se bez samostatného kroku
   nepřepisuje; Funnel a veřejný port zůstávají zakázané.
3. Viewer čte pouze fyzicky/logicky oddělenou `viewer_safe` projekci. Owner
   deník ani jeho souhrn nejsou Viewer vstup.
4. Nový build vznikne mimo aktivní strom a po validaci se atomicky aktivuje.
   Média se vydají až po aktuální serverové kontrole povolenosti.
5. Služby dostanou vlastní health a spravovaný start až v C06/C08e, po určení
   skutečných cest, úložiště, oprávnění a návratu po restartu.

## Otevřené brány

- **C06a:** lokální serverový základ, oddělená autorizace owner/Viewer a
  ne-citlivý health kontrakt.
- **C06b/C06c:** nezávislá záloha, obnova, migrace a restart se zapnutým
  FileVaultem.
- **C08c:** viewer-safe projekce, samostatný Janin souhrn a atomické HTML.
- **C08d:** očištěné foto deriváty, video poster/proxy/Range a povolené audio.
- **C08e:** Tailscale Serve změna, přímá URL, Cockpit link/health a `launchd`.
- **C08f/G8:** skutečná jiná síť a Janin MacBook+iPhone; soukromá fixture,
  pozdní rebuild a návrat po ukončení procesu.

Žádná z těchto změn nebyla tímto auditem provedena. Nejbližší implementační
krok projektu zůstává T024/T059 v C01b; Viewer se nestaví uvnitř C00 ani C01b.
