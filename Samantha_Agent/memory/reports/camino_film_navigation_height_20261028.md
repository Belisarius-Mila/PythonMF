# Camino — výška levého seznamu záběrů

Datum: 2026-10-28. Proud: project-camino.
Stav: místní implementace, čeká commit a výslovně zadané p+n Lunou.

## Zadání a rozsah

Míla požaduje, aby levý sloupec miniatur fotografií a videí využíval celou
dostupnou výšku okna a usnadnil orientaci. Po analýze výslovně zadal commit
a plynulé předání Luně k p+n. Tento krok realizuje pouze výšku a posouvání
seznamu. Dřívější kompaktní panel textu/hlasu zůstává samostatný návrh.

## Příčina a oprava

Nasazená stránka omezovala seznam pomocí max-height:60vh. Seznam tak končil
výrazně nad spodním okrajem okna; celý levý panel se navíc posouval s dlouhým
pravým editorem. Na úzké ploše platilo samostatné omezení 12rem.

- Desktopové okno střižny má plnou dostupnou výšku s původním vnějším
  odsazením. Levý panel je sticky pod skutečnou horní lištou.
- Výška se měří podle aktuální polohy panelu, spodního okraje dialogu
  a viditelného viewportu. Není odvozena od pevného procenta výšky.
- Nadpis a seznam tvoří flex sloupec; samotné miniatury se posouvají
  uvnitř zbývajícího prostoru. min-height:0 dovoluje skutečné posouvání,
  zarovnání mřížky nahoře zabrání roztahování malého počtu řádků.
- Výpočet reaguje na posun dialogu, velikost okna/viewportu, změnu hlavičky
  a obsahu nad seznamem. ResizeObserver zachytí i rozbalení projektů
  a zobrazení či zalomení stavové hlášky. Události se slučují do jednoho
  animation frame; stejné hodnoty se zbytečně znovu nezapisují.
- Prohlížeč bez ResizeObserver využije resize/scroll a přepočet po
  vykreslení editoru; bez RAF běží přepočet přímo.
- Při zavření, uspání panelu a skrytí karty se pozorování odpojí
  a čekající frame zruší. Návrat připojí právě jednu sadu posluchačů.
- Na úzké ploše do 720 px zůstává kompaktní seznam nad obsahem,
  aby nezabral celou obrazovku telefonu.

## Zachované funkce a data

Výpočet mění pouze dvě CSS proměnné rozložení. Nemění vybraný Asset ID,
draft, rozepsaný text ani pozici seznamu a nepřestavuje miniatury.
Nespouští save, render, proxy ani hlasové požadavky. Stávající návrat od
fotografie, souhlas/cena Orusu, původní text, historie/koš/import a celé
filmy zůstávají v dosavadních kontraktech. Žádné skutečné projekty či
média se vývojem neměnily; samostatná služba a iPhone nejsou cílem vydání.

## Ověření

Nový Node scénář ověřuje geometrii syntetického DOMu: dostupnou výšku
při otevření, zvětšení po scrollu, vyšší hlavičku, resize, mobilní režim,
visual viewport, zachování pozice a stejných uzlů miniatur, slučování
událostí, nulové další požadavky, skrytí/návrat, close/reopen/suspend,
starý callback a fallback bez ResizeObserver/RAF. Samostatně PASS.

Cílená sada: 102 PASS / 70,365 s (frontend, editor, foto vrstvy, Orus). Statická brána PASS; plnou publikační
bránu provede Luna v zadaném p+n. Složený HTML kontrakt aktualizovaný:
631713 znaků, 11870 řádků, SHA-256
3eb90bc9f8e36c18f7d7806c4fb5f8fab4c9c4e921f249d8ce0258ce275c98d3.

Skutečný prohlížeč není k ovládacím nástrojům připojený (apps/browsers
prázdné). Node geometrii nepovažujeme za fyzickou Safari přejímku.

## Přejímka po nasazení

1. Obnovit Cockpit, otevřít delší film a vybrat záběr uprostřed seznamu.
2. Na Macu ověřit, že seznam dosahuje téměř ke spodní hraně dialogu;
   samostatným kolečkem nad seznamem dojít až k poslední položce.
3. Posouvat pravý panel při editaci textu; vlevo zůstane dostupný seznam
   a jeho vybraný záběr. Otevřít/zavřít fotografii a ověřit návrat pozice.
4. Změnit velikost okna, rozbalit projekty a zobrazit delší hlášku;
   horní lišta ani spodní okraj nesmějí zakrýt položky seznamu.
5. Na úzké ploše ověřit dostupnost editoru pod kompaktním seznamem.

Fyzický výsledek je zatím NEOVĚŘENO. Navazující zjednodušení textu/hlasu
je popsané v camino_text_voice_ui_proposal_20261028.md.
