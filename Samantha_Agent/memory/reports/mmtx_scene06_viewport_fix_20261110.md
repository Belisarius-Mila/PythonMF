# MMTX — viditelné pokračování od čtvrtého obrazu

Míla při skutečném proklikávání oznámil zastavení na začátku čtvrtého obrazu.
Lokální HTTP protokol potvrdil načtené celé dialogy 1–10, obrázek chatrče a
první MP3 části 4. Dosavadní rozložení od části 4 skládalo obrázek v plné šířce,
dialog a Next pod sebe bez omezení výškou okna; ovládání mohlo skončit pod
viditelnou plochou. Původní headless testy prokazovaly návaznost, nikoli
viditelnost skutečného tlačítka. Předchozí označení celé přejímky bylo příliš široké.

## Oprava

Části s `layout: below` nyní mají výšku 100svh a tři řádky: zmenšitelný obraz,
přirozeně vysoký dialog a přirozeně vysoké ovládání. Obrázek se vejde pomocí
object-fit: contain bez ořezu; dialog a Next mají své místo uvnitř okna.
Tichý devátý obraz zachovává skrytou bublinu a samostatný řádek ovládání.
Spodní okraj respektuje safe-area-inset-bottom.

Přidaný odkaz `#picture=4` otevře vybraný obraz bez automatického zvuku; musí
následovat Tap and listen. Platné odkazy 1–10 vybírají první repliku dané části,
neplatná hodnota bezpečně vrací obraz 1. Again nadále vrací začátek celé šestky.
Verze CSS/JS/dat je `20261110viewport2` a oba mirrory mají stejné bajty.

Žádné texty, obrázky, MP3, manifesty, poskytovatel ani účtenky se nemění.
Žádné nové syntézy, opakování placených požadavků ani p+n neproběhlo.

## Ověření

- 53 cílených testů PASS včetně celého průchodu 67 replik, ticha, callbacků,
  historie a nových přímých vstupů 4, 9, 10 i bezpečných fallbacků. Přímý vstup
  před kliknutím nevytváří Audio a zachovává blokování Next během řeči.
- Skutečné Safari načetlo běžný přehrávač přes lokální HTTP od obrazu 4;
  zobrazená první replika 1/7, celý obraz, dialog i celé tlačítko Next uvnitř
  obrazovky. Při následném pozorování už živý průchod dosáhl části 5,
  Bruno 5/7. Další uživatelské proklikávání nebylo přerušované reloadem.
- Rychlá statická brána a git diff --check: PASS.
- Poslední plná brána 2978 OK (5 SKIP) patří předchozímu dokončení dca70ad9.
  Pro tuto omezenou frontendovou opravu se neopakuje; aktuální důkaz je 53
  cílených kontrol a skutečný přehrávač. Fyzický iPhone zůstává otevřený.

Další krok: Mílova přejímka zbývajícího průchodu a samostatné zadání p+n.
Při budoucí integraci přebrat i tento navazující opravný commit po dca70ad9.
