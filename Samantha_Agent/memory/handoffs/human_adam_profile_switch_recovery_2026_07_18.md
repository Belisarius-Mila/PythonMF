Nazev: Human–Adam – obnova přepínání pracovních profilů
Priorita: 1
Stav: čeká na retest
Pripomenout pri startu: ano
Datum: 2026-07-18

Co se resilo:

- Human–Adam po předchozí obnově znovu fungoval, ale tlačítko pro přepnutí mezi
  profily Human–Adam a Knihovna zdánlivě nereagovalo.
- Přepnutí trvale blokovaly historické záznamy nejistého doručení, přestože po
  nich následovaly další potvrzeně dokončené tahy.
- Chybová zpráva se navíc na menší obrazovce mohla zobrazit mimo viditelnou část.

Co je hotove:

- Kontrola nejistého doručení nyní vyhodnocuje jen stav od posledního potvrzeně
  dokončeného tahu; starší nejistota zůstává v historii, ale už netvoří trvalou
  provozní blokaci.
- Nová nevyřešená nejistota po posledním dokončeném tahu přepnutí nadále
  bezpečně blokuje.
- Chyby přepnutí profilu se posunou do viditelné části stránky, aby byly patrné
  také na iPhonu.
- Doplněné testy ověřují obě pořadí dokončeného a nejistého tahu i UI oznámení.
- Plná Cockpit quality gate prošla: 768 testů, syntaxe i `git diff --check` jsou
  v pořádku.

Co neni hotove:

- Oprava ještě nebyla načtena restartem do běžícího Cockpitu.
- Přepnutí Human–Adam → Knihovna → Human–Adam je potřeba ověřit živým testem.

Dalsi krok:

- Po tomto checkpointu synchronizovat oba izolované pracovní profily s novým
  `main`, řízeně restartovat Cockpit a provést živý test přepnutí oběma směry.

Navrhovane dalsi kroky:

- Pokud živý test ukáže jinou skutečnou překážku, použít nově viditelnou hlášku
  k cílené diagnostice; bezpečnostní brány přepínače neoslabovat.

Zmenene nebo relevantni soubory:

- `human_adam_profiles.py`
- `human_adam_ui.py`
- `test_human_adam_profiles.py`
- `test_human_adam_ui.py`

Bezpecnost / neukladat:

- Neukládat texty zpráv, identifikátory vláken, soukromé cesty ani private data.
- Historické provozní události nemažou; mění se pouze jejich vliv na aktuální
  možnost bezpečně přepnout profil.
