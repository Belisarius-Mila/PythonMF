# Plná sada mimo běžný commit a p+n — 15.11.2026

Míla po dvacetiminutovém vydání pověřil Adama opravou a výslovně zpochybnil
povinnou plnou bránu velkého projektu. Potvrdil také rozsah přípravy commitu.
Adam v tomto autorizovaném rozsahu zvolil plnou sadu pouze v noční CI a na
výslovný ruční požadavek. Nahrazuje předchozí povinnost full u infrastruktury,
validačních pravidel, nových souborů a prošlého plného základu. Ani tento
vývojový krok nevyvolává4000 testů; ověřuje se vlastními smluvními sadami.

## Co je změněné

- Výchozí runner vybírá domény, závislé testy a smluvní kontroly. Stejný
  runner volá lokální validate_project, jednoduchý checkpoint, GitHub batch,
  nasazení a již zarovnané Pages vydání. Aktivní Git hook s jinou plnou
  bránou při auditu nebyl nalezen. D3 fast-feedback už doporučuje správný
  validation_gate.py; opraven i jeho odkaz na odstraněný HTML hash test.
- Neznámé/dynamické vazby výběr doplní o základní smluvní sadu; nové soubory
  nemají full bootstrap. Sdílená persistence, zálohy, vydání a validace mají
  vlastní sady, nikoli všechny tranzitivní konzumenty celého projektu.
- Opraven skutečný VocabularyEN/docs obsah včetně nových obrázků, zvuků,
  náhledů a inventárních Python/Node testů. Změna autorského programu
  přidá authoring testy; samotná obsahová dávka je nevyžaduje.
- Samostatná cílená účtenka nepotřebuje plný základ. Expiruje po24h od
  vlastního běhu; obnovení spustí jen aktuální cílené testy. Verzev3 odlišuje
  nové účtenky. covered_modules brání úzkému důkazu přeskočit jinou změnu.
  Dopis checkpointu může otestovat pouze nové dokumenty při zachovaném pokrytí.
- Procesová SHA cache používá path/dev/inode/size/mtime/ctime. Nezměněné
  soubory se znovu nečtou, změny stejné velikosti/mtime zneplatní ctime.
  Vstupy před/po, HMAC, oprávnění metadat a kontroly symlinků zůstávají.
- Explicitní --full opravdu spustí celou sadu bez cache. GitHub schedule
  a workflow_dispatch jsou plné; běžný push/PR má cílenou politiku. Chyba
  vstupů, syntaxe či starý runtime selže jasně, nikoli skrytým full fallbackem.

## Důkazy a měření

Původní Datova dávka d141d030..134793cb:503 cest,9 modulů/99 testů,
žádná nezařazená cesta. Skutečný běh99/0 chyb,37,190s unit a53,881s celkem
včetně statických kontrol/výběru. Dávky, obrázky ani zvuky se negenerovaly
znovu; používá se skutečných522 záznamů a dříve hotové artefakty.

42 cílených regresí pravidel/cache PASS /11,421s v průběhu vývoje.
Nové/regresní scénáře zahrnují first-run bez plného základu, expiraci,
nový zdroj, celý čekající balíček, chybějící modul, explicitní full pouze
s fake runnerem, zákaz použití úzké účtenky na jinou doménu, stejnémtime/size,
sdílení mezi klony, změnu během testů, CI a platnost D3 cílů.

Změření capture_inputs na celém skutečném stromu:15,098s první a2,142s
opakované v témže procesu. Po restartu procesu je první cache opět studená;
nejde o slíbenou celkovou délku p+n, které zahrnuje síťové a nasazovací kroky.

Závěrečný cílený běh registrovaného validation_gate.py nad finálním kandidátem,
přesné počty/časy, manifest a lokální commit jsou v soukromé
`data/private/validation_focused_20261115/completion.json`. Tento verzovaný
popis se po závěrečném ověření nemění; krok uzavírá skutečná PASS účtenka.

## Přínos a přijaté omezení

Plná sada umí zachytit známou regresi vzdáleného konzumenta změněného API.
Nemůže zachytit scénář, který nemá test, ani sama ověřit živá macOS oprávnění,
skutečný zápis/doručení či fyzický telefon. Počet4000 není záruka těchto věcí.

Bez plné sady před každým vydáním může některá mezimodulová regrese uniknout
do běžného použití a zachytí se později; pravděpodobnost neumíme vyčíslit.
Cílené testy a bezpečnostní/recovery smlouvy omezují tento dopad, neodstraňují ho.
To je konkrétní kompromis za kratší vývoj a publikaci. Noční CI nenahrazuje
lidskou přejímku a její případná chyba nevrátí již provedené vydání automaticky.

Jde o místní vývoj. Není to nové p+n, restart, změna modelu, přesun médií ani
zásah do kalendáře/pošty. Při příštím schváleném p+n načíst registrovaně
nový ověřený validator; starý běžící v2 nemá tyto nové výchozí režimy.
