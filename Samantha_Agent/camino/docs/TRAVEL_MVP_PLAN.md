# Camino — minimalistický cestovní plán

Rozhodnutí Míly: 2026-09-25. Cesta 3.–17. října 2026; cílové zmrazení 2. října.
Stav: nový rozsah a pořadí vývoje, nikoli hotový Viewer nebo povolené nasazení.

Aktualizace M1 dne 25. 9.: lokální implementace a syntetické testy jsou
v [M1_VIEWER_REPORT.md](M1_VIEWER_REPORT.md). Prohlížečová přejímka ještě čeká;
M2/provoz nespouštěn. Zjištěná mezera původního API: pořadí částí dlouhého
audia není přenesené. M1 je proto přehrává odděleně s upozorněním, nikoli
automaticky spojené. Minimální oprava pořadí musí předcházet ostrému použití
vícedílných komentářů; nejde o skryté rozšíření M1 ani již hotový iPhone fix.

## Co nyní stavíme

Soukromou osobní aplikaci pro tuto cestu, ne produkt pro prodej. Zachováme
funkční záznam a přenos z iPhonu. Jana otevře v Cockpitu **Otevřít Camino**
a uvidí jednoduchý český HTML přehled doručených záznamů po dnech: text,
fotografie, přehrání komentáře a videa. Nemusí instalovat další naši aplikaci.
Použije již zamýšlený soukromý přístup; žádný veřejný web.

Tento dokument je novější rozhodnutí o rozsahu, pořadí a cestovní akceptaci.
V těchto věcech nahrazuje původní široké P0 a lineární pořadí C06 → C07 → C08
ve v0.5. U15 a ochrana dat zůstávají závazné. Importované podklady v0.5 se
nepřepisují. Detailní technické volby níže jsou Adamův návrh realizace tohoto
minimalistického cíle; nejsou tvrzením, že je Míla jednotlivě specifikoval.

## Nejmenší architektura

`iPhone → existující Camino API a archiv na Macu → viewer_safe → HTML pro Janu`

- Znovu použít C03/C05 a jejich ověřené přenosy. Žádný nový přenosový protokol,
  databázová migrace telefonu ani přepis recorderu kvůli Vieweru.
- Jedna malá serverová HTML šablona + CSS, nejvýše nezbytný JavaScript;
  žádný nový frontendový framework, CMS, víceuživatelský editor nebo cloud.
- Viewer dostane vlastní URL a read-only autorizaci oddělenou od owner API.
  Cockpit bude jen odkaz a stručný stav, ne úložiště ani generátor obsahu.
  Přímá záložka bude fungovat i při výpadku Cockpitu.
- Pro MVP může Viewer obsluhovat tentýž proces jako Camino API na loopbacku.
  Tím se výslovně zjednodušuje starší požadavek samostatného Viewer procesu
  (D11/F80); společný výpadek API a Vieweru je přijaté návrhové omezení.
- Jeden jednoduchý obnovitelný mediální proces/periodický běh, ne obecná AI
  job infrastruktura. Nové deriváty a HTML publikovat až po dokončení;
  neúspěch ponechá poslední platný výstup a pravdivý stav.
- Po přijetí změn automaticky doplnit příslušný den; pro malý objem stačí
  periodická kontrola revizí s pracovním intervalem 60 s. Bez pevné dvojice
  večerních/ranních rebuildů, WebSocketů a Mílovy ruční večerní redakce.
  Interval je návrh, ne garance doby zpracování videa.

## Obsah Vieweru a nepřekročitelné minimum

- Index dnů a jednoduchý detail dne v časovém pořadí. Jen dostupný lidský text;
  bez přepisu ukázat audio s přehrávačem, ne čekat na AI. Bez map a souhrnů.
- Jedna velikost očištěné foto kopie, lazy loading; jeden kompatibilní video
  proxy profil s posterem a posunem přehrávání; kompatibilní audio odvozenina
  zachovávající pořadí a mezery nahrávky. Originály neměnit ani veřejně vydávat.
- Použít pouze aktuální přijaté `diary` revize povolené cesty, neskryté,
  bez konfliktu. `Jen pro mě` nesmí do HTML, počtů, náhledů ani playlistu.
- Každý výdej HTML i média respektuje aktuální oprávnění. Po přijatém zámku
  nesmí stará URL vydat obsah; nestačí jej schovat v nové stránce. Text
  escapovat, necachovat soukromý obsah veřejně, žádné tokeny v URL.
- Jen soukromé HTTPS/Tailscale, samostatné read-only oprávnění Jany, žádný
  Funnel. Odkaz z Cockpitu není sám o sobě autorizace.
- Ukázat poslední aktualizaci a čekající povolená média; netvrdit, že server
  zná všechny záznamy telefonu. Již stažené cizí kopie nejdou odvolat.
- Originály, současné revize, hashové ověření a existující obnovu přenosu
  zachovat. Žádné automatické mazání. Méně funkcí není méně ochrany soukromí.

## Pořadí práce a podmínky hotovo

| Krok | Nejmenší výstup | Přijetí |
|---|---|---|
| M1 — Viewer lokálně (výběr C08c/d, minimum C06a) | Projekce, HTML dnů, foto/audio/video, read-only výdej; syntetická data bez živé služby | Cílené testy soukromí/autorizace a jeden prohlížečový smoke; všechny čtyři typy obsahu použitelné |
| M2 — cesta k Janě (minimum C06a/c + C08e/f) | Spravovaný Camino proces, privátní přístup, Cockpit odkaz a přímá URL; využít stávající upload | Jediný průchod iPhone → Mac → Jana z jiné sítě, krátce Safari MacBook+iPhone a návrat služby po ukončení procesu |
| M3 — jednoduchá záloha (minimum C06b) | Konzistentní databázový snapshot + neměnná média na ověřený jiný disk, verzované dávky bez automatického mazání | Obnovit jeden malý testovací den do nového cíle, porovnat hashe a otevřít médium; nikdy neobnovovat přes živá data |
| M4 — předodjezdový průchod (výběr C09) | Jeden běžný krátký venkovní pokus, kontrola místa, podpisu a stručný návod pro oba | RT1–RT6 níže s konkrétními omezeními, freeze nejpozději 2. 10. |

Bezprostřední další vývojový krok je M1, ne AI a ne opakování všech iPhone
testů. M1 nesmí čekat na neprovedenou širší akceptaci C05c; chybějící krátkou
kontrolu stavů spojíme s M2/M4. M1 zahrne všechny typy médií v jednoduché
podobě, nikoli plný C08 ani nový owner web. Po M1 žádné kosmetické rozšiřování.

Pro M3 nejdřív ověřit existující nezávislý cíl a kapacitu; žádný automatický
nákup ani domněnka, že záloha repozitáře obsahuje Camino. Stačí denní dávka
a ruční spuštění při potřebě místo složitého 15min plánovače. Při nedostupném
disku může Viewer dál fungovat, ale stav zůstane „další záloha neověřena“.
Chybějící cíl je konkrétní otevřená podmínka předcestovní ochrany, ne důvod
zablokovat lokální M1. Pro iPhone nepředstírat neimplementovanou zelenou osu.

## Co odkládáme

- C07: AI přepisy, korektury, rozpočtový worker a T038/T055 s reálnou AI.
  Lze je doplnit později nad uloženými zdroji, bez blokování Vieweru.
- C08a/b: bohatý owner archiv a automatické denní souhrny. Jana zatím čte
  napsané texty a poslouchá komentáře; mluvený komentář nebude automaticky text.
- C04c/e: rozšířený import a plný nouzový export, pokud nejsou už hotové;
  nepředstírat jejich existenci. Riziko: bez Macu a bez funkčního podpisu není
  doložená samostatná cesta vytažení všech dat z telefonu.
- QR párovací komfort, serverová hvězdička, složitý dashboard, obecné migrace,
  plná automatizace obnovy, nepoužité varianty kodeků a rozsáhlá optimalizace.
- P1 sdílení, P2 film/trasa, komerční produkt, App Store review, placené
  členství Apple a oficiální distribuční proces. Technický podpis iOS je
  nadále nutný; žádná „certifikace“ nenahrazuje jeho obnovu.
- Kompletní zátěžová matice, opakované dlouhé audio testy, úmyslné zaplnění
  telefonu, simulace všech havárií a captive portal bez dostupné vhodné sítě.
  Neprovedené scénáře zůstávají NEOVĚŘENO/ODLOŽENO, nikdy dodatečně PASS.

## Levnější testy a práce

- Jeden funkční celek na krok; předem určit jeho cílené testy, potom jedna
  stručná předávka a lokální commit. Neopakovat již úspěšné nezměněné testy.
- Dokumentace: odkazy, soulad stavů, `git diff --check` a rychlá statická brána;
  bez iOS buildu a bez kompletní aplikační sady kvůli samotnému textu.
- Běžné UI/HTML: jen dotčené testy a jeden smoke. iOS build/instalace jen při
  změně iOS části; serverový Viewer sám nevyžaduje nový podpis telefonu.
- Soukromí/autorizace: vždy malá automatická sada s tajnou syntetickou větou,
  zakázaným přístupem, novým zámkem a starou URL. Tuto ochranu neškrtáme.
- Změna persistence, záloh, závislostí či provozního workflow nadále spouští
  povinnou plnou projektovou bránu podle kořenového AGENTS. Totéž publikační
  brány při schváleném push/deploy. Tento plán je neobchází a nemění jejich kód.
- Fyzicky jeden sdružený průchod, ne každá větev zvlášť. Chybu opravit a
  zopakovat dotčenou část. Mikrofon/hovory znovu jen při zásahu do audia.
- Na další tah číst tento plán, aktuální krátký stav a dotčené soubory;
  nerozebírat znovu celé historické vlákno. Bez paralelních agentů a nových
  obecných frameworků. Úspora je v menším rozsahu, ne ve slibu konkrétního %.

### Cestovní přejímka RT1–RT6

1. **RT1 záznam/data:** offline krátké foto, video, audio a text, znovu otevřít
   a přehrát; staré záznamy dostupné. Dřívější relevantní PASS zůstávají důkazem.
2. **RT2 přenos/stavy:** jedna malá dávka, dokončení ověřené Macem; v témže
   průchodu zbývající C05c osy a pause. Neopakovat celý přijatý C05b.
3. **RT3 Jana:** Cockpit odkaz i přímá URL, jiná síť, Safari MacBook+iPhone,
   text/foto/audio/video a pozdě doručená položka po obnovení stránky.
4. **RT4 soukromí:** jeden `Jen pro mě` se nikde neobjeví; zveřejněný testovací
   Moment po doručení zámku zmizí a stará mediální URL je odmítnuta.
5. **RT5 provoz/záloha:** návrat spravovaného procesu, nezávislá kopie a jedna
   izolovaná obnova dne; písemně počítat s místním odemknutím po restartu Macu.
   Bez místního člověka po výpadku může být Viewer dočasně nedostupný.
6. **RT6 podpis:** další obnova SideStore před cestou a kontrola posunu data
   profilu + spuštění původní aplikace s daty. Nedělat z ní záruku do 17. 10.

Jde o přijetí zúženého cestovního MVP, nikoli úplných historických G0–G8.
Blokátory: ztráta dat, únik soukromého obsahu, nefunkční hlavní záznam/přenos,
nepoužitelný Viewer nebo neřešená instalace. Krátký výpadek Macu, ruční retry,
pomalejší video a chybějící AI jsou známá přijatelná omezení. Nepředstírat
záruku dostupnosti; bez odeslání zůstává jediná kopie nových dat v telefonu.

## Podpis a aktuální důkazy k 25. září

Míla potvrdil úspěšný SideStore import s odpojeným kabelem, otevření původního
Camina a zachování/přehrání dat. Protokol druhého pokusu v 20:27 potvrzuje
instalaci stejného ID `cz.pythonmf.camino.app` a nový profil do 2. 10. 20:27 CEST.
Datum je z podpisového/instalačního logu, ne extrakce profilu běžící aplikace.
První pokus s přidanou příponou selhal na limitu aplikací; nefunkční druhá
ikona pravděpodobně zůstala po něm. Nic nemažeme a nezaměňujeme ji s originálem.

Prozatím obnovovat opakovaným importem stejného IPA, přesné ID a **Append Team
ID vypnuto**, ne neověřeným Refresh All. Zdrojová inspekce použité SideStore
verze našla riziko změny ID při běžném Refresh; není to doložený runtime FAIL.
IPA ponechat lokálně v telefonu. Další kontrola 1. 10.; navržené rezervní dny
obnovy 6., 11. a 16. 10., vždy podle skutečně získané platnosti. Jde o návod,
ne vytvořené připomínky. Selhání SideStore/párování může vyžadovat Mac; při
problému nemaž aplikaci s daty. Před odjezdem volbu znovu prakticky zhodnotit.

## Oprávnění a nejbližší zadání

Tento krok mění pouze plán a související dokumentaci. Nenasazuje službu,
nespouští upload, nemění Serve/ACL, nepublikuje média a nic nekupuje.
Push, deployment, instalace služby a zpřístupnění skutečných dat zůstávají
odděleně potvrzované kroky. Další zadání: **M1 — lokální minimalistický Viewer
nad syntetickými daty**, bez nového iPhone buildu a bez AI.
