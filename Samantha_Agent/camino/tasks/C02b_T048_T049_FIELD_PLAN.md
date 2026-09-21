# C02b — oddělené fyzické testy T048 a T049

Stav 2026-09-21: T049 prošel v syntetickém mobilním rozsahu a je bezpečně
ukončený; plný T049 se skutečným novým videem zůstává otevřený. T048 na cizí
Wi-Fi prošel v dostupném syntetickém rozsahu: běžný přenos, přerušení a návrat
Wi-Fi i nedostupný a obnovený tailnet mají fyzický PASS. Přihlašovací portál
zůstává NEOVĚŘENO, protože použitá síť jej neměla. T048 je registrovaně
ukončený, receiver i testovací Serve cesta jsou vypnuté a Funnel zůstal
vypnutý. T048 a T049 mají
vlastní soukromý běhový stav, ale používají stejnou jedinou cestu
`/camino-c02b`; nikdy nesmějí běžet současně. Každý start,
zkopírování tokenu a stop prochází samostatně potvrzovaným registrovaným
workflow. Start se tímto dokumentem nespouští.

## Pořadí kvůli nedostupné cizí Wi‑Fi

Následující kroky T049 jsou zachovaný postup již provedené syntetické části;
nový běh se bez samostatného zadání nespouští.

Nejdříve lze provést **T049 v syntetickém rozsahu** na skutečných mobilních
datech iPhonu. Mac zůstává na své dostupné síti a přijímač běží pouze na
loopbacku za soukromým Tailscale Serve. Předem ověřit, že iPhone má dostupná
mobilní data a svůj autorizovaný tailnet; nepoužívat veřejný endpoint ani
vypnutou HTTPS kontrolu. Přenos jedné syntetické dávky má 100 663 553 B
(96 MiB + 257 B). Opakování částí může spotřebovat více dat; po dobu testu
měřit spotřebu také v nastavení iPhonu, pokud je dostupná.

1. Adam zobrazí náhled přesného `camino_c02b_t049_start`. Po samostatném
   potvrzení spustí receiver, ověří soukromou trasu a předá URL a potom token
   postupem `camino_c02b_t049_copy_token`; token se nikam neloguje.
2. Na telefonu vypnout Wi‑Fi (ne Letový režim), ponechat mobilní data a
   Tailscale. V `Camino Transfer Test` 0.4.0 s novým ověřeným buildem uložit
   soukromou konfiguraci. Novou syntetickou dávku vytvořit bez mobilního
   povolení. Zkontrolovat `Čeká na Wi‑Fi`, vypnutý přepínač a nulový nový
   serverový přenos. `Synchronizovat nyní` nesmí zákaz obejít.
3. Přepnout `Povolit mobilní data jen této dávce`. Před potvrzením musí být
   vidět 1 soubor, přesná velikost, možné opakované bajty a omezení jen na
   tuto dávku. Zrušení ponechá zákaz. Po vědomém potvrzení spustit
   `Synchronizovat nyní`; případný výpadek řešit obnovením/reconciliací,
   nikoli vytvářením další kopie téhož Assetu.
4. Adam read-only auditem zkontroluje 13/13 přijatých částí, jediný nový
   objekt a účtenku, 100 663 553 B a shodu serverového SHA-256. Na telefonu
   musí být `Ověřeno na Macu` až po serverové účtence.
5. Vytvořit **další** syntetickou dávku na stále mobilní síti. Její přepínač
   musí být opět vypnutý a nová relace nesmí přenášet data ani po stisku
   `Synchronizovat nyní`. Tím je ověřen jen zástupný případ „nové médium“.
   Plný T049 vyžaduje budoucí aplikaci schopnou pořídit skutečné nové video;
   samostatný harness k Fotkám ani kameře přístup nemá.
6. Po samostatném potvrzení provést `camino_c02b_t049_stop` a doložit přesnou
   obnovu Serve a vypnutý Funnel; syntetické důkazy zůstanou zachované.

T049 se nesmí označit za plný PASS jen podle syntetické dávky. Bez nového
podepsaného a na iPhonu nainstalovaného buildu po změně síťové politiky se
fyzický průchod nespouští.

## T048, až bude dostupná jiná Wi‑Fi

Před T048 musí být T049 nebo jiný běh registrovaně ukončený. Adam pak po
samostatném potvrzení spustí `camino_c02b_t048_start`, předá novou URL/token
a použije pouze novou syntetickou dávku. Postupně ověří:

- cizí Wi‑Fi s dostupným tailnetem: běžný dokončený privátní upload;
- přihlašovací portál, pokud je skutečně dostupný: před přihlášením čekání,
  po přihlášení pokračování bez nové kopie;
- přechod mezi povolenou Wi‑Fi a nedostupnou sítí: pravdivé čekání a návrat
  jen k chybějícím částem;
- nedostupný tailnet: žádná veřejná alternativní trasa, po obnově soukromého
  spojení pokračování.

Adam u každého bodu zaznamená klientský mezistav a serverový počet částí;
finále vyžaduje jednu hashově ověřenou relaci/objekt/účtenku pro daný Asset.
Chybějící captive portal nebo cizí Wi‑Fi znamená **NEOVĚŘENO** v příslušné
části, ne domyšlený PASS. Po testu se samostatně potvrdí
`camino_c02b_t048_stop` a přesná obnova Serve; Funnel zůstává vypnutý.

Oba testy používají pouze syntetický receiver. Neprokazují produkční server,
zálohu skutečných médií ani Camino Viewer.
