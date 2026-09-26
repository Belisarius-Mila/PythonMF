# M2 — dokončení obnovy po T058

2026-09-26. Lokální implementace pro **shodné úplné kopie**. Není nasazená;
živý archiv zůstává blokovaný. T058 PASS dokazoval zachycení změny epochy,
nikoli dokončení obnovy. Tento krok doplňuje chybějící potvrzení shody.

## Co je doplněno

- iPhone: tlačítko **Ověřit a dokončit obnovu** v Uložení a přenosy → Mac,
  pouze při požadované reconciliaci. Vyžaduje dostupnou neměřenou síť,
  uložené připojení a žádné rozpracované background upload úlohy.
- Server hlásí schopnost `identical_recovery_v1`. Starý server telefon
  neobchází; UI požádá o aktualizaci. Nový owner-only endpoint
  `POST /api/v1/recovery/complete` má stávající autentizaci a JSON limit 1 MiB.
- Důkaz obsahuje server ID, aktuální epochu, writer ID, kurzor, seřazená ID
  operací s pořadím a SHA-256 původních přesných obálek, inventář Momentů
  (revize/soukromí) a manifesty médií (ID/velikost/hash). Neobsahuje texty deníku.
- Server pod media zámkem a SQLite `BEGIN IMMEDIATE` ověří přesnou návaznost
  celého přijatého journalu, absenci konfliktů, shodu inventářů a všechny
  skutečné mediální soubory proti ověřeným účtenkám. Teprve pak atomicky
  uvolní oba příznaky. Nemění epochu, writer, operace, data ani Viewer grant.
- Telefon před požadavkem ověří skutečné místní soubory a znovu projde
  inventář kvůli změnám vzniklým během hashování. Účtenku váže hash přesného
  požadavku, server ID, epocha a kurzor. Novou epochu uloží až po potvrzení.
- Přijaté historické obálky zůstávají byte-exact ve staré epoše; nové operace
  už používají novou. Pause a mobilní grant se nemění. Nový přenos se tímto
  tlačítkem nespouští. Uložení journalu používá existující atomickou persistenci.
- Ztracená serverová odpověď nebo neúspěšné uložení telefonu: kontrolu lze
  zopakovat, dokud je serverová epocha/kurzor/inventář stejný. Nejde o slepé
  „odemkni“, opakuje se ověření. Neznámý výsledek UI neoznačí za dokončení.

## Záměrně nepodporované rozdíly

Chybějící přijatá operace, nový dosud neposlaný záznam/změna, jiné soukromí,
neověřené médium, rozdílný hash nebo konflikt **nevedou k odblokování**.
Stejně tak cizí server/writer, novější obnova nebo mezera v pořadí.
Tato malá varianta nedělá automatický merge ani replay ze starší zálohy.
Při rozdílu se obě kopie zachovají a následuje cílené servisní řešení; ne mazání
telefonních dat či ruční vypnutí flagů. Nejde o plnou obnovu zálohy C06b/M3.

## Ověření

- Doménová/serverová syntetická sada obnovy: 9/9 PASS.
- Swift core + audio link: 39/39 PASS, včetně 3 nových scénářů obnovy,
  nezměněných obálek, nové epochy, pause, neplatné účtenky a ztracené odpovědi.
- Izolované HTTP/Viewer/runtime testy: 24/24 PASS, včetně owner-only obnovy,
  chybějících médií, capability a idempotentního opakování požadavku.
- Nepodepsaný iOS build PASS. Plná projektová brána **1827/1827 PASS**
  (345,543 s jednotkové sady), syntaxe a whitespace PASS. Fyzická akceptace
  nebyla provedena. První Swift build byl opakován, protože se jeho testovací
  zdroj změnil během sestavování; konečný kompletní běh 39/39 PASS.
- Živý read-only audit 13:42: HTTP 200, stejná identita, oba blokující flagy
  stále true, nová capability není nasazená; HTTPS/Cockpit PASS, Funnel off.

## Jeden navazující fyzický průchod — až po samostatném nasazení

1. Nejprve nový pevný server release nad stejným archivem; potvrzená kopie
   databází, stejný server ID/epocha. Nestačí nasadit pouze Cockpit.
2. Potom podepsaná aktualizace **téže** aplikace bez odinstalace. Soukromě
   předat připravené owner připojení; token nikdy do dokumentace ani výstupu.
3. Telefon na Wi‑Fi/Tailscale, starší záznam a médium dostupné. Nezakládat
   kvůli této kontrole další testovací záznam před porovnáním. Klepnout na
   **Ověřit a dokončit obnovu**. Při rozdílu zastavit postup a nic neodstraňovat.
4. Při potvrzené shodě: iPhone hlásí dokončení, server současně oba flagy=false,
   staré počty/hash/identita zachované. Ukončit a otevřít appku; stav se zachová.
   Bylo-li zapnuté pause, stále drží. Poté výslovně pokračovat a přenést jednu
   novou neosobní značku; ostatní originály se neposílají znovu.

Viewer pro Janu zůstává samostatným následným rozhodnutím. M3 nezávislá záloha
a M4 předcestovní přejímka nadále zbývají. Není proveden push, aktualizace
služby, podpis/instalace iPhonu, změna sítě ani živé odblokování.

## Navazující nasazovací příprava 26. 9.

- Míla schválil pokračování server + aktualizace téže appky. Nové registrované
  `camino_service_upgrade` pracuje jen nad zastavenou vlastní službou: nový
  neměnný Git release z čistého commitu, beze změny dependencies/venvu,
  uchované staré konfigurace/plist a konzistentní snapshoty všech databází.
  Identita, počty a mediální hashe se porovnají před/po. Nic se nemaže,
  grant/token/flag/Serve se nemění. Služba zůstává vypnutá až do `start`.
- Při neúplném přepnutí konfigurace/plistu zůstane launchd vypnutý; obě
  definice a snapshoty jsou v soukromém `Service/upgrades`. Žádný automatický
  rollback databází nebo nový pokus přes rozpor vlastnictví. Zachovat stav
  a cíleně dokončit/vrátit jen ukazatele kódu podle soukromé účtenky.
- Cílená sada ovládání 24/24 PASS, včetně shody dat/flagů, zachování starého
  plistu, odmítnutí cizí/běžící služby a změněných dependencies.
- Camino 0.1.0 (5) se stejným bundle ID je sestavené a strict podepsané;
  profil zahrnuje telefon, ale je to starší profil do **27. 9. 12:10 CEST**.
  Proto žádná přímá instalace, která by zkrátila dosavadní SideStore platnost.
- Připravený `Camino-Recovery-5-20260926.ipa` ve Stahování (1 024 375 B), ZIP
  integrita ověřená. SHA-256: `ea294065a3889aed3d53f0f017f53c5b2fb9588a05e2016aece0db78a3b142a4`.
  Určeno k novému podpisu/importu přes již ověřený SideStore postup se stejným
  ID, **Append Team ID vypnuto**, bez odinstalace Camina. Nová platnost až
  podle výsledku SideStore; není předem slibovaná.
- Kabelová read-only inventura aplikací selhala na CoreDevice 12040
  (developer disk image nebylo možné připojit). Nic neopravováno silou,
  žádná instalace, odinstalace či zásah do telefonu nebyly provedené.
- Konečný výsledek nasazení a plné brány je uveden až v navazujícím bloku.
- Přednasazovací plná brána **1830/1830 PASS** (237,917 s jednotkové sady),
  syntaxe a whitespace PASS. Po změně pouze dokumentace rychlá statická brána.

### Skutečné nasazení 2026-09-26 17:23 CEST

- Push registrovaně dokončen: 3 commity, plná brána **1830/1830 PASS**;
  `origin/main` je na `6865bcab`. Cockpit nasazený na tomto commitu,
  deploy-verification a smoke **5/5 PASS**.
- Vlastní Camino služba byla řízeně zastavena, upgrade přepnul pouze immutable
  `code_root` na `6865bcab` a vytvořil soukromou účtenku se snapshoty metadata,
  auth a media DB i starého plistu/configu. Poté znovu spuštěna.
- Živě: služba `loaded=true/running=true`, privátní HTTPS přesná, Cockpit
  zdravý, Funnel vypnutý, ostatní Serve konfigurace zachovaná. API state 200,
  identita shodná, `identical_recovery_v1` dostupné.
- Archiv po přepnutí přesně odpovídá přípravě: 104 operací, 41 Momentů,
  45 ověřených médií / 214 555 219 B. `exports_blocked=true` a
  `reconciliation_required=true` zůstaly beze změny; Viewer grant=false.
- IPA build 5 se stejným bundle ID je připravený pro SideStore. Přímá instalace
  přes CoreDevice nebyla provedena: developer disk image chyba 12040. IPA má
  ověřený ZIP a strict podpis, ale novou platnost musí vytvořit SideStore.
- Další ruční krok: v SideStore importovat `Camino-Recovery-5-20260926.ipa`,
  ponechat stejné ID a vypnutý Append Team ID, aplikaci neodinstalovávat.
  Potom otevřít novou Camino, ověřit připojení a klepnout na **Ověřit a dokončit
  obnovu**. Při rozdílu nic nemazat; při shodě zkontrolovat oba flagy=false.
