# C05b — fyzický test privátní synchronizace na iPhonu

Stav 2026-09-23: plán je připravený; fyzické výsledky se ještě nesmí označit
PASS. Test zachovává existující C04b/C04d data a aplikace se instaluje jako
aktualizace stejného bundle ID bez odinstalace.

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

| Test | Úkon | PASS |
|---|---|---|
| Zachování dat | Po aktualizaci otevřít jeden starší Moment a místní médium. | Starší data i přehrávání zůstaly dostupné; žádná odinstalace/reset neproběhly. |
| T051 | Zastavit privátní službu, ale aplikaci ponechat. Vytvořit značku, krátký komentář, Úvahu, fotografii a krátké video; otevřít je. | Vše jde místně pořídit a číst. Stav říká, že Mac není dostupný, ale nevymýšlí proč a netvrdí úspěch. |
| T047-A | Spustit službu, vytvořit krátké médium, dát **Synchronizovat nyní** a zamknout iPhone během přenosu. Po chvíli odemknout a otevřít stav. | Originál a fronta zůstaly; klient porovnal Mac a dokončil nebo pravdivě čeká bez duplicity. |
| T047-B | U nového krátkého videa spustit synchronizaci a aplikaci během přenosu nuceně ukončit. Znovu ji otevřít. | Relaunch nejdřív porovná stav, doplní pouze chybějící části a žádný neověřený přenos neoznačí hotový. |
| T048 | Během čekající dávky vypnout Tailscale nebo přejít na síť bez dostupného tailnetu a potom ho obnovit. Captive portal testovat jen tehdy, je-li bezpečně k dispozici. | Žádný veřejný fallback; místní záznam funguje; po návratu následuje porovnání a pokračování. Nedostupný captive portal = `NEOVĚŘENO`, ne FAIL ani PASS. |
| T049 | S alespoň jedním čekajícím médiem otevřít mobilní dialog a zaznamenat počet/objem. Potvrdit, potom pořídit nové krátké video. | Povolení odpovídá zobrazené dávce; nové video se přes mobilní data nezačne přenášet a čeká na Wi‑Fi nebo nové povolení. |
| T050 | U vícečástového souboru sledovat přechod po poslední části. | Dokud server nedokončí celý hash, UI říká **Ověřuji**; `Vše známé je ověřeno na Macu` se ukáže až po serverovém `verified`. |
| T052 | Použít pouze řízenou testovací odpověď `insufficient_storage`; skutečný disk se nezaplňuje. | Telefon hlásí, že na Macu není místo, netvrdí úspěch a originál zůstává místně dostupný. Pokud fault režim není v tomto běhu připravený, výsledek je `NEOVĚŘENO`. |
| T053 | Po ověření krátkého videa změnit jeho soukromí nebo kapitolu a synchronizovat. | Přenese se jen metadata v souvislém pořadí; serverový počet/objem ověřených videí se nezvětší o kopii. |
| T058 | Jen v oddělené kopii serverového stavu otočit epochu jako po obnově a znovu synchronizovat. | Telefon ukáže nutné porovnání po obnově, nic nemaže, novější telefonní stav je v rozdílech a exporty zůstávají blokované. Bez oddělené kopie = `NEOVĚŘENO`. |
| Pozastavení | Klepnout **Pozastavit přenosy**, aplikaci ukončit a znovu otevřít; během pause pořídit místní značku. | Pause přežije relaunch, síťové úlohy nepokračují, značka funguje; až **Pokračovat v přenosech** povolí další průchod. |

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
