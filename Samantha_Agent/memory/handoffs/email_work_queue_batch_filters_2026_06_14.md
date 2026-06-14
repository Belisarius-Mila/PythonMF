Nazev: Email Work Queue - blokove davkove filtry
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-14

Co se resilo:
- Po zařazení větší dávky e-mailových dokumentů vzniklo riziko, že Cockpit Work Queue bude zpracovávat smíchaných 149 položek najednou.
- Mila chtěl obecný přepínač pro budoucí dávkové zpracování, ne jednorázový filtr jen pro dnešní VAK / Finanční správu / faktury nad 2000 Kč.

Co je hotove:
- Backend u každé položky e-mailové fronty generuje obecné `batch_groups`.
- Podporované skupiny vznikají z metadat a tagů položky: Finanční správa, VAK, Faktury nad 2000 Kč, Faktury / e-shopy, S PDF přílohou, Velké PDF a Ostatní.
- Popup `Email Work Queue` má blokové přepínače.
- Levý seznam ukazuje jen aktuální blok.
- Tlačítko `Zpracovat dávku` posílá ke zpracování jen viditelné položky aktuálního bloku, ne celou frontu.
- Potvrzovací dialog ukazuje název bloku a počet položek.
- U faktur nad 2000 Kč se v seznamu ukazuje max nalezená částka.
- Cockpit byl restartovaný a lokální smoke check prošel.

Co neni hotove:
- Neproběhl ruční klikací test přímo v prohlížeči po restartu.
- Není doplněný detailní filtr podle libovolného textu, pouze blokové přepínače.

Dalsi krok:
- V Cockpitu otevřít `Email Work Queue`, zvolit nejdřív `Finanční správa`, potom `VAK`, a ručně otestovat, že dávkové zpracování pracuje jen s vybraným blokem.

Navrhovane dalsi kroky:
- Okamžitě: zpracovat malý blok `Finanční správa` ručně po položkách, vybrat PDF přílohy a uložit.
- Potom: zpracovat `VAK`.
- Nakonec: faktury nad 2000 Kč jet po menších dávkách podle částky a smyslu dokumentu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`

Bezpecnost / neukladat:
- Změna neukládá těla e-mailů ani PDF do gitu.
- Soukromá fronta a reporty zůstávají v `data/private/`.
