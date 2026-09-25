# M2b — pořadí a mezery audia pro Viewer

2026-09-25. Lokální implementace a automatické ověření; bez push,
nasazení, podpisu nebo instalace na skutečný iPhone.

## Výsledek

- Telefon čte existující dokončené účtenky C01a/C01b/C01c. Posílá pořadí
  checkpointů, návaznost pokračování, zaznamenanou pauzu, chybějící úsek/konec.
  Nepoužívá pořadí UUID, doručení ani nástěnný čas jako náhradu návaznosti.
- Nová neměnná operace `create_audio_layout` je oddělená od `create_asset`.
  Původní ID médií, hashe, bajty, přijaté obálky a stavy ověřených uploadů
  zůstávají stejné. Doplnění pořadí starých záznamů nevyvolá jejich reupload.
  Recorder, jeho formát a Core Data schéma telefonu se nemění.
- Telefon operaci přidá do existující trvalé fronty až po serverové schopnosti
  `audio_layout_v1`. Starý server bez `features` dál dostává původní metadata
  a média. Při downgradu s již čekající novou operací zůstane fronta zachovaná
  a čeká na kompatibilní server; nic se nepřečísluje ani nezahazuje.
- Server kontroluje skutečné audio Assety stejného Momentu, unikátní indexy,
  výslovnou diskontinuitu, návaznost ve stejné session, větvení a cykly.
  Potvrzení layoutu/účtenky/kurzoru je jedna transakce; Moment revision neroste.
  Jiný obsah pod již přijatým clip ID je konflikt a blokuje výstupy.
- Viewer řadí klipy podle zaznamenaných předchůdců a úseky podle indexů.
  Nový malý lokální skript po dohrání přejde pouze na následující dostupný
  souvislý checkpoint stejného klipu. Nepřeskakuje chybějící médium ani mezeru.
  Najednou hraje nejvýše jedno audio. Bez JavaScriptu zůstávají ruční ovladače.
- Pauza mezi vědomými pokračováními je viditelně označená naměřenou délkou
  nebo „délka neznámá“; další klip spustí Jana ručně. Nevyrábíme ticho a
  netvrdíme, že úseky tvoří jeden fyzický soubor. Chybějící konec a neznámá
  návaznost jsou označené. AAC části nejsou gapless spojený export.
- Pokud prohlížeč automatické přehrání odmítne, ukáže se ruční pokračování.
  Safari politika/UX je stále fyzicky neověřená. Staré záznamy bez layoutu
  mají pravdivou výstrahu o chybějícím pořadí a jdou přehrát jednotlivě.
- Pořadí je doložené uvnitř jedné session. Více samostatných nahrávek téhož
  Momentu netvoří společnou časovou osu; jejich čísla jsou pořadím zobrazení.
- U15 se nemění: layout se dostane do projekce až po filtru Momentů. Soukromé
  části nejsou v HTML/playlistu/počtech; mediální endpoint znovu kontroluje
  aktuální povolenost i pro navazující požadavek přehrávače.

## Kompatibilita a budoucí nasazení

- JSON API zůstává v1; stávající významy polí se nemění. Nový explicitní typ
  operace je vyjednané rozšíření podle `features`, nikoli další upload protokol.
  Přesná pole a limity jsou v `C03b_OPENAPI_V1.json` a `domain/audio_layout.py`.
- Metadatová SQLite používá schéma 2: při otevření schématu 1 přidá pouze
  tabulku `audio_layouts` v transakci; staré řádky/media nepřepisuje.
  **Před prvním ostrým otevřením pořídit konzistentní záložní kopii DB.**
  V tomto kroku proběhl upgrade pouze nad syntetickým testovacím souborem.
- Nasadit nejdřív nový server, potom podepsanou aktualizaci stejné aplikace.
  Starý server schéma 2 odmítne; rollback vyžaduje samostatný bezpečný postup,
  nikoli spuštění starého binárního kódu nad novou DB.
- Žádná skutečná cesta nebyla zapnutá pro Viewer, skutečné čtecí oprávnění
  nevzniklo. M2c musí připravit registrovaný start/status/stop, záložní kopii
  metadat před upgradem a vědomé povolení cesty/čtenáře. Publikace i služba
  zůstávají odděleně schvalované. M3 nezávislá záloha tím není nahrazená.

## Ověření

- SwiftPM 36/36 PASS, z toho 3 nové scénáře: pořadí segmentů/stejná ID,
  legacy pokračování a neplatný čas pauzy, backfill bez reuploadu a zachování
  přesných obálek přes restart/jednání se starým či downgradovaným serverem.
- Nepodepsaný generic iOS Debug build PASS (`CODE_SIGNING_ALLOWED=NO`).
  Nevznikla instalace ani nový podpis; fyzický mikrofon není tímto testovaný.
- Python projekce/kontrakt/layout 26/26 PASS (8 nových). Pokryté: upgrade
  syntetické DB v1, nezměněné originály/manifesty, rollback celé operace,
  idempotence, konflikt, soukromí, pořadí, pauzy, cyklus a odvolání výdeje.
- Izolovaná HTTP/server sada 21/21 PASS, včetně 3 nových reálných syntetických
  mediálních scénářů: opačné doručení, pozdě doručený prostřední úsek,
  neznámý předchůdce a díra, privátní layout a staré URL po zámku.
- Node test ověřuje navázání jen na explicitního souseda, zákaz skoku přes
  mezeru, restart úseku od začátku a ruční fallback při odmítnutí autoplay.
- Plná projektová brána PASS: 1 789/1 789 testů (216,626 s), Python,
  JavaScript/shell syntaxe a whitespace OK. Samostatný JS přehrávač prošel
  také `node --check`; nový kontrakt je platný JSON.

## Jeden krátký fyzický průchod až po schváleném nasazení

1. Po aktualizaci telefonu otevřít existující audio. Synchronizovat jeho nová
   metadata; server musí mít layout a původní objekty se stejnými hashovými
   účtenkami, bez nového přenosu již ověřených audio bajtů.
2. Ve Vieweru na Safari Mac/iPhone vybrat jeden existující vícedílný záznam.
   Posunout první úsek těsně před konec a ověřit správné pokračování, případně
   pravdivý ruční fallback. Zkontrolovat jednu zaznamenanou pauzu/nejistotu.
3. V rámci společného RT3/RT4 zamknout tentýž testovací Moment, doručit změnu
   a ověřit odmítnutí staré mediální URL. Neopakovat mikrofon/hovory C01c,
   recorder se neměnil. Není-li vhodný starý záznam, teprve pořídit krátký nový.

Stav této fyzické přejímky: **NEPROVEDENO**. Dokončený kód není tvrzení,
že nasazený iPhone už pořadí posílá nebo že Jana službu otevře.
