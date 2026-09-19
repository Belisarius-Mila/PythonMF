# C02b — cílená fyzická zkouška prvního startu buildu 4

Stav 2026-09-19 22:11 CEST: `Camino Transfer Test` 0.4.0 (4) prošel částí A
na iPhonu 14 Plus. Z části B je doložen vědomý start, přerušení a automatické
dokončení po opětovném otevření aplikace s dostupnou sítí. Otevření aplikace
ještě bez sítě neproběhlo, proto celý plán B není PASS. T049 je zastavené;
syntetický důkaz zůstal zachovaný. T050 se neopakovalo.

## Rozsah a bezpečný začátek

- Testuje se pouze nová syntetická dávka 100 663 553 B / 13 částí. Žádná
  fotografie, video, audio ani soukromý text se nečte. Opakování částí může
  spotřebovat více mobilních dat než samotná dávka.
- Staré T049/T050 běhy jsou zastavené a důkazy se nemažou. Před testem se
  read-only ověří jejich stav, vypnutý Funnel a dostupnost soukromého tailnetu.
- Pro nový izolovaný běh se po samostatném pokynu použije registrované
  `camino_c02b_t049_start`; vytvoří novou soukromou účtenku a jedinou Serve
  cestu `/camino-c02b`. Potom se zvlášť spustí registrované
  `camino_c02b_t049_copy_token`. URL a token zůstávají mimo Git i tento zápis.
- Na iPhonu před vytvořením dávky vypnout Wi-Fi, ponechat mobilní data a
  Tailscale. Otevřít build 4, uložit novou soukromou konfiguraci a ověřit,
  že předchozí dávka je dokončená. Pokud je starý journal nedokončený nebo
  neplatný, novou dávku nezakládat a nic neresetovat; nejprve ho auditovat.

## A — grant bez prvního startu

1. Založit **novou** syntetickou dávku v buildu 4. Musí mít vypnuté mobilní
   povolení, 0 % a 0/13. Nový serverový běh má 0 relací, 0 objektů a 0 účtenek.
2. Zapnout `Povolit mobilní data jen této dávce`, zkontrolovat náhled jedné
   dávky a vědomě potvrdit grant. **Neklepat** na `Synchronizovat nyní` ani
   `Pokračovat`.
3. Počkat, otevřít Ovládací centrum a vrátit se do aplikace. Samostatně
   vypnout a znovu zapnout mobilní spojení, nechat tailnet znovu dostupný.
   Po každém impulsu zkontrolovat telefon i registrovaný read-only
   `camino_c02b_t049_status`.
4. PASS A: po grantu, návratu i obnově sítě stále 0 %, 0/13, žádná nová
   serverová relace, objekt ani účtenka. Jakýkoli upload před vědomým
   klepnutím je FAIL; stav zachovat pro diagnostiku.

## B — vědomý start a automatická obnova již zahájené dávky

1. Klepnout jednou na `Synchronizovat nyní`. Tím se první start trvale
   autorizuje. Server musí založit právě jednu relaci této nové dávky.
2. Jakmile server potvrdí alespoň jednu, ale méně než 13 částí, zapnout
   Letový režim. Po ustálení ověřit neúplnou relaci bez finálního objektu a
   účtenky. Když se přenos dokončí dříve, než vznikne mezistav, část B je
   NEOVĚŘENO; nezpětně ji neoznačovat za PASS.
3. S vypnutou sítí aplikaci nuceně ukončit a znovu otevřít. Nesmí tvrdit
   `Ověřeno na Macu`; stará přijatá data zůstávají na serveru. Pak obnovit
   mobilní data a tailnet. **Neklepat podruhé** na synchronizaci ani
   `Pokračovat`.
4. PASS B: po návratu soukromé sítě se stejná relace sama porovná se serverem
   a doplní jen chybějící části. Finále má 13/13, právě jeden objekt a
   účtenku, 100 663 553 B a shodný serverový SHA-256. Telefon ukáže
   `Ověřeno na Macu` až po serverovém potvrzení. Ztráta dávky, druhá relace,
   falešné ověření nebo nutnost dalšího klepnutí znamenají FAIL.

## Uzavření a hranice výsledku

- Po zaznamenání telefonu a serverového stavu se samostatně potvrzeným
  `camino_c02b_t049_stop` odebere pouze vlastní testovací cesta a receiver.
  Read-only audit musí potvrdit přesnou obnovu původního Serve, vypnutý
  Funnel a zachování syntetických důkazů.
- PASS A+B uzavírá pouze regresi prvního startu a obnovy v C02b harnessu.
  Neznamená T048 na cizí Wi-Fi, plné T049 s novým skutečným videem,
  produkční server ani zálohu médií. Při FAIL nic nemazat ani nepřepisovat;
  zachovat journal, soukromý běh a přesný mezistav.

## Výsledek průchodu 2026-09-19

- A PASS: po grantu, návratu z Ovládacího centra a obnovení mobilního spojení
  telefon ukazoval 0 %, 0/13; server měl 0 relací, objektů a účtenek.
- B částečně ověřeno: první vědomý stisk založil jednu relaci. Letový režim
  zastavil přenos při 1/13 bez objektu a účtenky. Během výpadku došlo k dalšímu
  stisku synchronizace; po návratu sítě přenos dosáhl 8/13, znovu se přerušil,
  a po nuceném ukončení a znovuotevření s dostupnou sítí se bez dalšího stisku
  dokončil. Server potvrdil jedinou relaci, 13/13, jeden objekt a účtenku,
  100 663 553 B a shodný SHA-256; Míla na telefonu viděl `Ověřeno na Macu`.
- Neověřeno: znovuotevření aplikace se stále vypnutou sítí a pravdivý stav UI
  v tomto okamžiku. Mílův chat používal mobilní spojení iPhonu, takže Letový
  režim přerušil také živé navádění. Po dohodě se další přenos jen kvůli tomuto
  mezikroku neprováděl; plný PASS B se netvrdí.
- Potvrzený stop obnovil přesný původní Serve, odebral vlastní cestu a receiver,
  ponechal Funnel vypnutý a zachoval ověřený syntetický důkaz. Kód se neměnil.
