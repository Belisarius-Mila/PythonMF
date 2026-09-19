# C02b — fyzický test T050 se zadrženým serverovým ověřením

Stav 2026-09-19: oddělené testovací workflow je připravené, fyzický T050 je
NEPROVEDENO. Tento plán sám nespouští přijímač ani Serve.

## Hranice a příprava

- Jen syntetický soubor v `Camino Transfer Test` 0.4.0 (3), žádná osobní média
  ani Camino Audio. Použije se jeden nový soukromý běh T050; T049 je zastavené
  a T048 nesmí běžet současně.
- Přijímač má pouze pro T050 pevnou prodlevu 14 sekund mezi zapsáním stavu
  `verifying` a sestavením/ověřením výsledného objektu. Je kratší než 20s
  timeout klientského požadavku. Nejde o vypnutí hashové kontroly ani o
  předčasnou účtenku; po prodlevě musí proběhnout obvyklá kontrola délky a
  SHA-256.
- Mac zůstává na své dostupné síti. iPhone potřebuje autorizovaný tailnet a
  soukromou HTTPS cestu. Bez Wi-Fi lze použít mobilní data jen po vědomém
  povolení této konkrétní dávky; jedna dávka má 100 663 553 B a retry může
  přenést více. Funnel i veřejný fallback zůstávají zakázané.
- Na iPhonu může zůstat druhá, dosud neodeslaná dávka z T049. Po nové soukromé
  konfiguraci ji lze použít, pokud ukazuje 0/13 a mobilní grant je vypnutý;
  jinak nevytvářet nebo nepřepisovat média naslepo a stav nejprve ověřit.

## Řízený průchod

1. Adam ověří, že T049 je `stopped`, T048 neaktivní a `/camino-c02b` volná.
   Zobrazí náhled `camino_c02b_t050_start`; až po samostatném potvrzení spustí
   vlastní loopback receiver, ověří privátní HTTPS trasu a zkopíruje URL do
   Mac schránky. Token předá zvláštním potvrzeným
   `camino_c02b_t050_copy_token`; token se nikam neloguje.
2. Míla uloží novou URL/token v testovací aplikaci. Na dostupné povolené Wi-Fi
   lze synchronizovat rovnou; na mobilních datech nejprve vědomě povolí jen
   tuto dávku. Před spuštěním zkontrolovat jediný syntetický soubor a 0/13.
3. Při přenosu sledovat poslední části. Jakmile telefon ukáže 100 % a
   `Ověřuji`, nic dalšího nemačkat a ideálně pořídit snímek bez tokenu. Adam
   současně read-only statusem doloží serverové `verifying`, 13/13 částí a
   dosud 0 objektů/účtenek. Tato souběžná dvojice je jádrem T050.
4. Po doběhnutí prodlevy Mac musí doložit jedinou ověřenou relaci, objekt i
   účtenku o 100 663 553 B se shodným SHA-256. Teprve poté smí telefon ukázat
   `Ověřeno na Macu`. Pokud se 14s okno nepodaří současně zachytit, T050
   zůstává NEOVĚŘENO; samotný konečný výsledek nestačí.
5. Po samostatném potvrzení `camino_c02b_t050_stop` zastaví jen vlastní
   receiver, odebere jen testovací Serve cestu a porovná přesnou obnovu
   původního Serve. Funnel zůstane vypnutý; syntetický důkaz se nemaže.

PASS vyžaduje fyzicky pozorované `Ověřuji` při 100 % a současný serverový
`verifying` bez objektu/účtenky, následované jediným hashově ověřeným finále.
Předčasné `Ověřeno na Macu`, chybný hash, duplicita nebo veřejný fallback jsou
FAIL. Nedostupná síť či nezachycené krátké okno nejsou PASS.
