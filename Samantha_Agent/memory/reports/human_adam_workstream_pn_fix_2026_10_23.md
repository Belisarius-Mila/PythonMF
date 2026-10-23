# Human–Adam: přepínání proudů a pravdivý panel p+n

## Rozsah — 23. 10. 2026

Míla schválil oba body analýzy a p+n výsledných commitů Lunou. První commit
`a50a9007` sjednocuje lokální Xcode podpis. Druhý krok upravuje pouze
prezentaci a obnovu stavu p+n; registrovaný audit, potvrzení, vykonavatel,
push/deploy a ochrany Camina/autosave zůstávají stejné.

## Xcode a přepnutí

Oba profily i GitHub byly zarovnané; blokoval je jediný soubor
camino/app/Camino.xcodeproj/project.pbxproj ve zdrojovém main. Dvě hodnoty
DEVELOPMENT_TEAM duplikovaly již existující ignorovaný LocalSigning.xcconfig.
Target overrides jsou odstraněné, původní skupina se dvěma existujícími
referencemi i celé ostatní uspořádání zachované. Původní soubor pro obnovu
zůstal jen v private; žádný podpisový údaj se nově neukládá do Gitu.

Debug i Release přes showBuildSettings potvrzují stejný účinný místní tým
a bundle ID. Po commitu a bezpečném zarovnání čistých profilů skutečné
registrované přepnutí Camino → MMTX → Camino prošlo. Nebyla poslaná žádná
zpráva ani modelový tah. Kontrola čistého main se neoslabuje.

## Panel p+n

- **Aktuální:** potvrzený main/GitHub a odpovídající nasazení; běžné tlačítko
  p+n se skryje. Opakování je samostatná volba v uzavřených dalších akcích.
- **Čeká publikace / nasazení:** tlačítko předá přesný balíček dosavadní cestou.
- **Blokované:** pracovní změny main, nečisté/nezarovnané profily, divergence,
  GitHub napřed, aktivní tah nebo nejisté doručení mají konkrétní vysvětlení.
- **Neověřené:** chybějící, cizí nebo rozporné důkazy neslibují aktuální stav;
  dostupná zůstává čtecí obnova. Při čistém GitHubu a neověřeném cíli lze
  v dalších akcích vědomě vyžádat audit a případné p+n s původním potvrzením.

Stav vychází z registrovaného read-only snímku tohoto proudu a čerstvého
GitHub batch auditu se shodnými heads. Výpadek auditu nelze nahradit starým
origin/main. MMTX/Pages nepřebírají stav společného Cockpitu; lze použít jen
odpovídající potvrzenou webovou účtenku tohoto proudu pro přesný commit.
Poslední globální účtenka je označená názvem svého proudu.

Novější dokončená účtenka zneplatní starý pracovní snímek. Po ukončení
portálového běhu se otevřený panel znovu načte; čtecí obnova zůstává dostupná
i po výpadku stavu Luny. Žádný render panelu sám nevytváří předání.
Výslovný textový p+n i ruční opakování dál procházejí původním serverovým
auditem a přesným potvrzením; nový modelový polling ani retry nevznikají.

## Ověření a vydání

- Xcode struktura, plutil, Debug/Release build settings a původní místní
  xcconfig PASS; nevzniká nová IPA ani telefonní migrace.
- Skutečné Camino → MMTX → Camino před UI nasazením PASS.
- Cílená sada Human–Adam UI, live status a release submission: 93 testů PASS.
  Závěrečný běh znovu 93 PASS. Jeden meziběh narazil na souběh čtecí kontroly
  a startu testového workeru při získání neblokujícího zámku; samostatný test
  i následná celá cílená sada prošly. Backend zámků se touto změnou neupravuje.
  Existující Node VM scénář rozšířen o aktuální/pending/blocked/neověřený
  stav, špinavý zdroj při čistých klonech, cizí proud, odlišný Pages cíl,
  selhání čerstvého auditu, obnovu po chybě a zneplatnění starého snímku.
- JavaScript syntaxe PASS. Plná publikační brána a finální nasazení až přes
  přesnou novou účtenku Luny; následovat má opakované živé přepnutí.
- Fyzický proklik Safari není Node VM scénář a zatím není doložený.

Technické účtenky bez výpisu podpisových hodnot zůstávají pouze v
`data/private/human_adam_switch_release_20261023/`.
