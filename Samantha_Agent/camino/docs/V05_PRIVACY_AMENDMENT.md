# Camino v0.5 — závazný dodatek k soukromí a Vieweru

Datum rozhodnutí: 16. září 2026

Tento dodatek zaznamenává novější výslovné rozhodnutí Míly. Má přednost před
rozpornými staršími větami v původním importovaném balíčku v0.5. Balíček
`CAMINO_podklady_v0.5/` a jeho lokální ZIP zůstávají byte-for-byte zachované,
aby šel ověřit jejich původní manifest.

## U15 — význam Do deníku a výchozí soukromí Úvahy

- `Jen pro mě` je soukromý obsah vlastníka. Nesmí vstoupit do Camino Vieweru,
  viewer-safe souhrnu, seznamu médií, odvozenin, cache ani počtů pro Janu.
- `Do deníku` je obsah celé cesty určený pro deník. Je-li pro cestu zapnutý
  Camino Viewer, je celý tento obsah po doručení aktuální revize na server
  automaticky způsobilý pro Janin read-only Viewer. Nejde o veřejné zveřejnění
  ani o jednorázové P1 sdílení dalším lidem.
- Nová samostatná `Úvaha` vždy začíná jako `Jen pro mě`, bez ohledu na naposledy
  použitý režim nových běžných Momentů.
- Úvahu lze vědomou akcí `Vložit do deníku` převést na `Do deníku`. Rozhraní
  před potvrzením řekne, že po synchronizaci může být úvaha včetně povoleného
  původního audia dostupná Janě ve Vieweru.
- Zpětná změna na `Jen pro mě` platí lokálně okamžitě. Server ji může vynutit až
  po přijetí revize; do té doby telefon ukazuje `Čeká na server`. Již zobrazenou
  nebo uloženou kopii na Janině zařízení nelze odvolat.

## Nahrazené významy v původní v0.5

Tento dodatek nahrazuje rozporné formulace v původním `AGENTS.md`, U05, D02,
F02, F10, F15 a F61, podle nichž bylo `Do deníku` stále pouze soukromé nebo se
nesmělo automaticky objevit v rodinném výstupu. Pro P0 Camino Viewer platí U13,
U15 a F74–F86 ve významu tohoto dodatku. P1 jednorázové sdílení dalším členům
rodiny nadále vyžaduje samostatnou vědomou akci.

## Závazný implementační kontrakt

1. Datový model odliší alespoň `owner_only` a `diary`; neznámý stav je
   fail-closed a do Vieweru nesmí.
2. Tvorba samostatné Úvahy nastaví `owner_only` přímo v doménové logice, ne jen
   předvoleným přepínačem v UI.
3. Akce `Vložit do deníku` vytvoří novou revizi soukromí a prioritní metadata
   operaci. Nepřepisuje originální audio ani dřívější revize.
4. Viewer generuje obsah pouze z aktuální serverové `viewer_safe` projekce
   Momentů v režimu `diary`. Owner souhrn není vstup Vieweru.
5. Media endpoint kontroluje aktuální serverovou povolenost při každém vydání;
   stará URL nesmí obejít pozdější známý zámek.
6. UI vždy rozliší místní změnu od serverem přijaté změny a připomene hranici
   již zkopírovaných cizích kopií.

## Dopad na etapy a testy

- C01b zůstává izolovaným audio prototypem bez finálního modelu Momentu. Tento
  dodatek nemění formát jeho dosavadních testovacích nahrávek ani nevyžaduje
  nový build před T024/T059.
- C03a zafixuje stav a revize soukromí; C04a/C04d implementují bezpečný výchozí
  stav Úvahy a akci `Vložit do deníku`; C08c–C08f implementují Viewer.
- Vedle existujících T005, T015, T042, T081, T085, T092 a T095 vznikne T096:
  při globálním režimu `Do deníku` založit Úvahu, ověřit `Jen pro mě` na telefonu
  i nepřítomnost ve Vieweru, potom použít `Vložit do deníku`, doručit revizi a
  ověřit text i povolené původní audio ve Vieweru.
