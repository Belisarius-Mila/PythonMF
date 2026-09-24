# C05b — fyzický test privátní synchronizace na iPhonu

Stav 2026-09-24: fyzický průchod integrovaného Camino 0.1.0 (3) na iPhonu
14 Plus je dokončený. Zachování dat, T051, T047-A/B, dostupná část T048, T049,
T050, T052, T053, T058 a Pozastavení jsou PASS. Captive portal v T048 zůstává
`NEOVĚŘENO`, protože nebyl bezpečně dostupný. Aktualizace proběhla pod stejným
bundle ID bez odinstalace.

## Před startem

1. Ověřit, že podepsaný build prošel strict codesign kontrolou a že se po
   instalaci otevřou starší Momenty a média.
2. Registrovaným workflow spustit session-owned C05a a privátní Serve cestu
   `/camino-api`; read-only stav musí ukázat `server_alive=true`,
   `private_route_exact=true`, `funnel_enabled=false`.
3. Na iPhonu otevřít **Nabídka → Uložení a přenosy**. Z Macu vložit nejprve
   privátní URL, potom samostatně token, klepnout **Uložit připojení**.
4. Používat jen nový neosobní syntetický obsah. Starší soukromý obsah neotvírat
   kvůli testu a nic z něj nekopírovat do protokolu.

## Průchod

| Test | Úkon | Výsledek |
|---|---|---|
| Zachování dat | Po aktualizaci otevřít jeden starší Moment a místní médium. | **PASS** — starší data i přehrávání zůstaly dostupné; žádná odinstalace ani reset neproběhly. |
| T051 | Zastavit privátní službu, ale aplikaci ponechat. Vytvořit značku, krátký komentář, Úvahu, fotografii a krátké video; otevřít je. | **PASS** — vše šlo místně pořídit a číst; klient pravdivě hlásil nedostupný Mac bez určení neznámé příčiny. |
| T047-A | Spustit službu, vytvořit krátké médium, dát **Synchronizovat nyní** a zamknout iPhone během přenosu. Po chvíli odemknout a otevřít stav. | **PASS** — originál i fronta zůstaly, klient nejdřív pravdivě čekal a následně server dokončil 40/40 médií bez duplicitní relace. |
| T047-B | U nového krátkého videa spustit synchronizaci a aplikaci během přenosu nuceně ukončit. Znovu ji otevřít. | **PASS** — relaunch obnovil přenos; server přešel přesně z 40 na 41 relací a 41 ověřených médií, bez duplicity. |
| T048 | Během čekající dávky vypnout Tailscale nebo přejít na síť bez dostupného tailnetu a potom ho obnovit. Captive portal testovat jen tehdy, je-li bezpečně k dispozici. | **PASS v dostupném rozsahu** — při vypnutém Tailscale server zůstal na 41 médiích a Funnel byl vypnutý; po návratu tailnetu synchronizace sama doběhla přesně na 42. Captive portal **NEOVĚŘENO**. |
| T049 | S alespoň jedním čekajícím médiem otevřít mobilní dialog a zaznamenat počet/objem. Potvrdit, potom pořídit nové krátké video. | **PASS** — dávka ukázala 2 metadata, 1 médium a 8,6 MB. Pozdější video o 8,2 MB grant nezdědilo, zůstalo čekat na Wi‑Fi a server měl 44 Assetů, ale jen 43 relací/ověřených médií. |
| T050 | U vícečástového souboru sledovat přechod po poslední části. | **PASS** — iPhone ukázal **Ověřuji → Ověřeno**; server současně přešel z `43 verified + 1 uploading` na 44/44 až po dokončení finalizace. |
| T052 | Použít pouze řízenou testovací odpověď `insufficient_storage`; skutečný disk se nezaplňuje. | **PASS** — telefon hlásil nedostatek místa a originál zachoval. Server měl 45 relací, ale jen 44 ověřených médií; po vypnutí fault režimu stejná relace bezpečně doběhla na 45/45. |
| T053 | Po ověření krátkého videa změnit jeho soukromí nebo kapitolu a synchronizovat. | **PASS** — přibyla jen jedna metadatová operace; 45 relací, 45 ověřených médií a 214 555 219 B zůstalo beze změny. |
| T058 | Jen v oddělené kopii serverového stavu otočit epochu jako po obnově a znovu synchronizovat. | **PASS** — telefon ukázal nutné porovnání po obnově, místní obsah zůstal dostupný a server zachoval 41 Momentů a 45/45 médií s `reconciliation_required=1`, `exports_blocked=1`. |
| Pozastavení | Klepnout **Pozastavit přenosy**, aplikaci ukončit a znovu otevřít; během pause pořídit místní značku. | **PASS** — pause přežil relaunch, server během něj zůstal na 103 operacích; až **Pokračovat v přenosech** přeneslo jednu čekající značku jako operaci 104 bez nového média. |

## Po testu

1. Read-only workflow stavem zapsat jen počty operací, ověřených médií a bajtů;
   žádné URL, tokeny ani obsah.
2. Každý řádek označit `PASS`, `FAIL` nebo `NEOVĚŘENO` s přesnou hranicí.
3. Po dokončení registrovaným stopem odebrat jen `/camino-api`, zastavit
   vlastněný proces a odvolat token. Ověřit přesné obnovení Serve a vypnutý
   Funnel.

Automatické testy a serverový audit nenahrazují pozorování na iPhonu. Zámek,
force quit, mobilní data, síťový přechod a skutečné UX lze označit PASS jen po
tomto fyzickém průchodu.

Závěrečný registrovaný stop: `phase=stopped`, `server_alive=false`,
`private_route_exact=false`, `funnel_enabled=false`, `active_tokens=0`.
Zachovaný redigovaný důkaz má 104 operací, 41 Momentů, 45 Assetů,
45/45 ověřených médií a 214 555 219 B. Původní Serve konfigurace byla obnovena
přesně; URL, tokeny ani obsah nejsou v Gitu.
