Nazev: iPhone zkratky / Najit auto
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-23

Co se resilo:
- Mila chtel, aby Samantha umela pripravovat iPhone / Apple Shortcuts zkratky.
- Podklad prisel pres private knowledge inbox jako `zkratkystahnoutzgit.txt`.
- Bylo zprovozneno MacStories Shortcuts Playground pro Codex.
- Prvni realna zkratka byla `Najit auto`.

Co je hotove:
- Codex marketplace `shortcuts-playground` je zaregistrovany.
- Plugin `shortcuts-playground@shortcuts-playground` je nainstalovany a enabled,
  verze `1.0.1`.
- Samantha ma tooly:
  - `iphone_shortcuts_playground_status()`
  - `prepare_iphone_shortcut(...)`
- Systemovy report `iPhone shortcuts status` je registrovany.
- V memory je technicky kanonicky workflow:
  `technical/iphone_shortcuts_playground.md`.
- Import postup po vytvoreni zkratky je povinny:
  Finder -> `/Users/miloslavfalta/Documents/Shortcuts Playground/` -> dvojklik
  na zkratku -> aplikace Zkratky -> pridat do knihovny.

Overena zkratka:
- Finální fungující verze je:
  `/Users/miloslavfalta/Documents/Shortcuts Playground/Najit auto v3.shortcut`
- Archivovane XML:
  `/Users/miloslavfalta/Documents/Shortcuts Playground/2026-05-23/Najit auto v3-122655.xml`
- V3 pouziva:
  - menu `Ulozit polohu auta` / `Otevrit auto v Mapach`
  - `Set Parked Car` pro ulozeni
  - `Get Parked Car Location` -> `Get Maps Link` -> `Open URL` pro otevreni Map
- U Mily je import na iPhone a funkcnost potvrzena.
- U Jany se zkratka po sdileni nejdrive dlouho nacitala, protoze Zkratky nebyly
  videt v Polohovych sluzbach. Po rucnim spusteni/povoleni polohy zacala
  zkratka fungovat.

Co nebylo hotove / pouceni:
- Verze v1 se zasekla pri `Get Current Location` -> `Set Parked Car`.
- Verze v2 uz ukladala polohu, ale navigacni vetev pres `Get Directions`
  neotevirala Mapy.
- Pro mapy je pro tento typ zkratky robustnejsi `Get Maps Link` -> `Open URL`.
- Pri podpisu v3 se jednou objevila docasna chyba Apple `NSURLErrorDomain 500`;
  opakovany podpis uspel.

Dalsi krok:
- Zadny urgentni dalsi krok.
- Pri dalsi nove iPhone zkratce pouzit overeny pipeline:
  prompt -> XML plist -> validator Craig loop -> `sign_shortcut.sh` -> import
  postup pro Milu -> rucni test na iPhonu.

Navrhovane dalsi kroky:
- Pozdeji pridat helper pro generovani plist z vyssi urovne, pokud se budou
  zkratky tvorit casto.
- U zkratek s polohou na cizim iPhonu nejdrive overit, zda aplikace Zkratky uz
  pozadala o polohu a objevila se v Polohovych sluzbach.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/app/iphone_shortcuts.py`
- `Samantha_Agent/scripts/samantha_iphone_shortcuts.py`
- `Samantha_Agent/tests/test_iphone_shortcuts.py`
- `Samantha_Agent/memory/technical/iphone_shortcuts_playground.md`
- `Samantha_Agent/app/samantha_agent.py`
- `Samantha_Agent/app/system_reports.py`
- `Samantha_Agent/app/capability_audit.py`

Bezpecnost / neukladat:
- Hotove `.shortcut` soubory a archivovana XML jsou mimo git v
  `~/Documents/Shortcuts Playground/`.
- Soukrome podklady z knowledge inboxu ani rootovy `zkratkystahnoutzgit.txt`
  necommitovat.
- Zkratky mazajici data, posilajici zpravy, pracujici s ucty, platbami nebo API
  klici delat jen s explicitnim zadanim a rucnim testem.
