# Camino P2-B — uzavření dne 6. 10. 2026

Stav 11. 10. 2026: **lokálně vyvinuté, skutečný den neuzavřený**.
P2-A/IPHONE1 má Mílův PASS; P2-A/MAC1 zůstává na fyzické přehrání.
Míla výslovně zahájil P2-B a oznámil, že data prvního dne jsou na Macu
kompletní. To je vstupní tvrzení, nikoli ještě důkaz telefonu.

## Současná místní data

Registrovaný read-only audit služby potvrdil běžící owner službu, ale její
`status` sám neověřuje doručení dat. Přímý redigovaný read-only audit
autoritativních SQLite a originálů našel pro 6. 10. jednu kapitolu,
11 Momentů (1 značka, 7 video Momentů, 3 Úvahy) a 34 příloh
(11 foto, 9 audio, 14 video). Všech 34 má ověřenou účtenku, souhlasí
manifest a úplné soubory na Macu při čtení prošly velikostí i SHA-256.
Osm Momentů `diary` obsahuje 30 povolených příloh: 11 foto, 14 video a
5 audio. Tři `owner_only` Úvahy se 4 audio přílohami jsou mimo film.
Žádné soukromé ID, obsah ani cesta originálů nejsou v tomto reportu.
Read-only průchod nového P2-B validátoru nad skutečným Mac archivem prošel
a sestavil pouze v paměti výběr: 30 zdrojů, 25 obrazových záběrů a
5 zvukových voleb. Nevznikl manifest ani projekt.

## Implementace

- iPhone po výslovném potvrzení znovu objeví lokální den, vyžaduje prázdnou
  synchronizační frontu, přijatý kurzor a žádný aktivní upload ani rozpracované
  pořízení nebo textový koncept ve dni. Znovu hashuje vybrané původní soubory,
  kontroluje serverový stav a odešle přes HTTPS owner token přesný inventář.
- Mac odmítne jiný server/epochu/kurzor/autora, neúplné revize, chybějící
  položky, neověřené účtenky a změněné originály. Pod zámkem uloží create-only
  manifest, projekt a účtenku do soukromého úložiště mimo Git. Opakovaný
  identický požadavek vrací stejný projekt; jiné vstupy nebo zastaralý projekt
  odmítne.
- Projekt řadí povolené foto/video podle času pořízení a přijatého pořadí.
  Všechna videa začínají na nule a končí na původní délce. Audio je uložené
  jako samostatná volba, bez automatického střihu nebo přimíchání. Originály
  zůstávají beze změny. Kontrola projektu po restartu ověřuje aktuální
  inventář dne, soukromí a SHA-256 před budoucím renderem nebo vydáním.
- Opakovaný požadavek se stejným stavem dne používá stejné ID, takže ztracenou
  odpověď lze bezpečně zopakovat. iPhone si ID uloženého projektu pamatuje a
  po restartu znovu načte jeho platnost z Macu.

Formát P2-B je oddělený od syntetického P2-A rendereru. V tomto kroku
nevzniká MP4 ani editor; zde uložený projekt je vstup pro P2-C/D.

## Ověření a hranice

Syntetický owner HTTP test pokrývá zákaz anonymního přístupu, čekající
frontu, chybějící médium, úplné ověřené doručení, vyloučení soukromého
audia, idempotenci, znovunačtení úložiště a zneplatnění po změně soukromí.
iOS Debug Simulator build ověřuje Swift 6 kompilaci, nikoli fyzické chování.
Plná brána včetně nového API testu prošla **1876/1876**. iOS Debug Simulator
build po poslední změně Swift kódu prošel bez podpisu.

Skutečný projekt 6. 10. nyní **neexistuje**: nové API není nasazené, nová
aplikace není nainstalovaná a čerstvý důkaz z telefonu ještě nebyl přijatý.
Push, nasazení a instalace jsou oddělené kroky. Po jejich samostatném
schválení se na iPhonu spustí **Uložení a přenosy → Film → Ověřit a uzavřít
den**; pak se přes owner API ověří uložený projekt a 30 povolených zdrojů.
