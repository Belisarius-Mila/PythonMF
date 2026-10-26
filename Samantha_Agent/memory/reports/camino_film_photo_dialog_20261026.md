# Camino — zvětšení fotografie přímo ve střižně

Stav: 2026-10-26 13:48 CET, místní UI krok; bez nového push/nasazení.
Pracovní proud: `project-camino`.

## Výsledek

Míla povolil pokračování dalším vývojovým krokem. Navazuje plánované vlastní
zvětšovací okno z UI analýzy z 25. 10.: kliknutí na centrální fotografii nebo
Otevřít fotografii zobrazí obrázek přímo nad střižnou. Zavření tlačítkem,
klávesou Esc či kliknutím mimo obsah vrátí stejný záběr, pozici seznamu,
scroll a rozepsané pole; při otevření/zavření se nepřestavují editovací pole.

Používá se nativní modalní dialog se jménem a popisem, explicitním fokusem
na Zavřít fotografii a návratem fokusu s preventScroll. Po automatickém
překreslení řádku lze fokus vrátit ke stálému ovladači fotografie. Prohlížeč
bez podpory dialogu nebo s odmítnutým showModal zachová dosavadní odkaz do
nové karty; Cmd/Ctrl/Shift/Alt kliknutí zachovává obvyklé chování odkazu.

## Výkon, data a soukromí

- Velká až 4096px fotografie se vytvoří v DOM a načte až po ručním kliknutí.
  Seznam nadále používá 256px miniatury a pracovní plocha 1600px náhled.
- Stejný existující chráněný read-only PNG endpoint, aktuální povolení,
  ověřování zdrojů a no-store/private. Backend ani datové kontrakty se nemění.
- Zavření odstraní src, obrázek a název. Skrytí karty, ztráta spojení,
  neplatný projekt/oprávnění, přepnutí či zavření filmu okno také vyčistí.
  Návrat do karty velkou fotografii automaticky neotevírá ani nestahuje.
- Každé otevření má nový obrazový uzel a vlastní identitu/epochu. Opožděné
  load/error a stará close událost nemohou změnit nový pohled. Po chybě
  zůstává viditelná hláška a obrázek se odstraní; pozdní load ji nepřepíše.
- Prohlížení nevolá save/source/render. Originály, osobní střihy, nahrávky,
  projektový koš, služba a iPhone se při vývoji neměnily. Žádný produkční render.

## Ověření

- 88 cílených Python kontrol PASS / 60,868 s: editor 44, foto vrstvy 23,
  frontend 21. Obsahují Node scénáře editoru/hlášek i historie hlasů/importu.
- Nové Node scénáře: velký obrázek až na kliknutí, zavření přes cancel/tlačítko,
  obnova fokusu/scrollu/navigátoru a stejného rozepsaného DOM pole, žádné nové
  save/source/render požadavky. Skrytí a odvolání oprávnění vyčistí dialog;
  pozdní události, staré close a pozdní load po chybě nemají vedlejší účinek.
  Ověřený fallback bez showModal, při jeho chybě a modifikované kliknutí.
- Struktura HTML vyvážená, jedinečná ID/ovladače; složený otisk aktualizovaný
  po kontrole HTML/CSS/JS. Rychlá kanonická statická brána: PASS.
- Po poslední CSS úpravě skrytí zavřeného dialogu dalších 21 frontendových
  kontrol znovu PASS / 2,579 s (opakované kontroly, nikoli nové testy).
- CUA inventář v tomto kroku: apps=[], browsers=[]. Skutečné rozložení,
  nativní Tab/fokus, Safari, Esc a dotykové ovládání na zařízení NEOVĚŘENO;
  syntetický DOM nenahrazuje fyzickou přejímku.

## Další krok

Samostatně zadané p+n přes registrovanou Lunu. Potom uložit rozpracovaný
střih, obnovit Cockpit a otevřít fotografii uprostřed delšího filmu, zavřít
ji tlačítkem a Esc; ověřit stejné pole/pozici, fokus, čitelnost a zavření na
úzkém displeji. Při skrytí karty nesmí zůstat velký obrázek ani se sám vrátit.

Předchozí funkční vydání d99093c1/Luna 51926adfe2cd519ff4d8d57a66916024 je
historicky potvrzené (gate 2243, smoke 5/5); nynější dialog v něm není.
Míla po něm zadal další vývoj, nové p+n se automaticky nespouští.

Čtecí `/usr/bin/say -v '?'` v tomto kroku nabízí jediný český hlas Zuzana.
Další hlas se neinstaloval, nastavení systému ani placená syntéza se neměnily.
Výběr příjemnějšího hlasu poslechem a praktická přejímka nahrávek/koše/importu
zůstávají samostatné otevřené kroky.
