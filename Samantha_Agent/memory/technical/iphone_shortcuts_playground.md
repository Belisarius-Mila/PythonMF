# iPhone Shortcuts Playground workflow

Priorita: 2
Pripomenout pri startu: ne
Datum: 2026-05-23

## Ucel

Pripravit Samanthu na tvorbu Apple Shortcuts / iPhone zkratek pres MacStories
Shortcuts Playground.

Klasifikace potvrzena 2026-05-24:

- `iPhone Shortcuts / Mobile Input Layer` je `Infrastructure capability`.
- Neni to samostatny kanonicky projekt.
- Jednotliva zkratka neni Samantha tool; je to mobilni vstupni kanal nebo akcni
  tlacitko.
- Samantha tool je az lokalni Python schopnost, ktera zkratku obsluhuje, napr.
  `list_quick_notes`, `show_quick_note_detail` nebo budouci
  `classify_quick_note`.
- Bezpecna veta: zkratky smi posilat vstupy do fronty a spoustet lokalni
  iPhone utilitu, ale rizikove akce na Macu nebo ven z domu vyzaduji potvrzeni.

Zdroj inspirace byl soukromy podklad v knowledge inboxu
`zkratkystahnoutzgit.txt`; puvodni clanek ani soukromy soubor se neukladaji do
memory jako plny text.

Primarni verejne zdroje:

- MacStories landing page: `https://www.macstories.net/shortcuts-playground/`
- MacStories detailni clanek: `https://www.macstories.net/stories/introducing-shortcuts-playground/`
- GitHub repo: `https://github.com/viticci/shortcuts-playground-plugin`

## Co je overene k 2026-05-23

Podle MacStories Shortcuts Playground umi z prirozeneho jazyka pripravit realny
Apple Shortcut pro Claude Code nebo Codex. Vystupem je `.shortcut` soubor, ktery
se na Macu uklada do `~/Documents/Shortcuts Playground/` a ma se otevrit a
zkontrolovat v aplikaci Zkratky.

Shortcuts Playground podle autora pouziva dokumentaci akci, validacni loop a
Apple `shortcuts` CLI pro podpis/konverzi. Neni to oficialni Apple funkce a
vystup je nutne rucne overit.

## Lokální stav

Aktualizace 2026-05-23:

- Codex marketplace `shortcuts-playground` byl zaregistrovan.
- Plugin `shortcuts-playground@shortcuts-playground` byl nainstalovan a je
  `installed, enabled`, verze `1.0.1`.
- Apple `/usr/bin/shortcuts` CLI existuje.
- Codex CLI existuje.
- Vystupni slozka `~/Documents/Shortcuts Playground/` vznikla pri prvnim buildu.
- Prvni realny `.shortcut` byl vygenerovany:
  `~/Documents/Shortcuts Playground/Najit auto.shortcut`.
- Archivovany unsigned XML:
  `~/Documents/Shortcuts Playground/2026-05-23/Najit auto-113654.xml`.
- XML validace prosla a podepsany `.shortcut` ma nenulovou velikost.
- Rucni import na iPhone probehl pres iCloud, ale prvni verze se pri volbe
  `Ulozit polohu auta` zasekla na nacitani.
- Pravdepodobna pricina: kombinace `Get Current Location` a rucniho predani
  polohy do `Set Parked Car` muze na iPhonu cekat na polohove opravneni nebo
  se zaseknout v systemove Maps/Parked Car akci.
- Byla vygenerovana jednodussi druha verze:
  `~/Documents/Shortcuts Playground/Najit auto v2.shortcut`.
- Archivovany unsigned XML v2:
  `~/Documents/Shortcuts Playground/2026-05-23/Najit auto v2-114745.xml`.
- V2 vynechava `Get Current Location`; vetev ulozeni vola primo nativni
  `Set Parked Car`, vetev navigace pouziva `Get Parked Car Location` a
  `Get Directions`.
- XML validace v2 prosla a podepsany `.shortcut` ma nenulovou velikost.
- Rucni test v2 na iPhonu: ulozeni polohy zacalo fungovat, ale navigacni vetev
  neotevrela Mapy.
- Byla vygenerovana treti verze:
  `~/Documents/Shortcuts Playground/Najit auto v3.shortcut`.
- Archivovany unsigned XML v3:
  `~/Documents/Shortcuts Playground/2026-05-23/Najit auto v3-122655.xml`.
- V3 meni navigacni vetev: `Get Parked Car Location` -> `Get Maps Link` ->
  `Open URL`. Tím se obchazi problematicke primé `Get Directions`.
- Pri prvnim podpisu v3 se objevila docasna chyba Apple `NSURLErrorDomain 500`;
  opakovany podpis prosel. XML validace v3 prosla a podepsany `.shortcut` ma
  nenulovou velikost.
- Rucni import a test v3 na Milove iPhonu: funguje. Ukladani polohy i otevreni
  auta v Mapach pres Maps link je potvrzene.
- Sdileni na iPhone Jany pres Zkratky/AirDrop/iCloud bylo resene. U Jany se
  zkratka nejprve dlouho nacitala; v Polohovych sluzbach se aplikace Zkratky
  nezobrazovala, protoze jeste nemela zaregistrovany pristup k poloze. Po
  rucnim spusteni/povoleni zacala zkratka fungovat i u Jany.
- Zkratka `Rychlá poznámka pro Samanthu.shortcut` byla vytvorena 2026-05-23.
  Uklada markdown poznamky do iCloud Drive `Shortcuts/Samantha Inbox`. Samantha
  ma navazujici tooly `list_quick_notes` a `show_quick_note_detail`, ktere
  poznamkam prideluji stabilni cisla v soukromem indexu
  `data/private/quick_notes/index.json`.

Samantha ma tool:

```text
iphone_shortcuts_playground_status()
```

Ten je read-only a kontroluje:

- Apple `shortcuts` CLI;
- Codex CLI;
- pritomnost Shortcuts Playground pluginu v lokalnim Codex prostredi;
- vystupni slozku `~/Documents/Shortcuts Playground/`;
- soukromou slozku pro request drafty.

Samantha ma tool:

```text
prepare_iphone_shortcut(...)
```

Ten umi pripravit prompt/request pro Shortcuts Playground. Bez potvrzeni vraci jen
nahled. Po potvrzeni ulozi private draft do:

```text
Samantha_Agent/data/private/iphone_shortcuts/requests/
```

Potvrzovaci veta:

```text
Potvrzuji pripravu iPhone zkratky
```

## Bezpecnostni pravidla

- Samantha nesmi tvrdit, ze `.shortcut` je hotovy, pokud neprobehl realny build
  pres Shortcuts Playground.
- Vystup `.shortcut` se musi pred instalaci rucne otevrit a zkontrolovat v Apple
  Shortcuts.
- Bez vyslovneho zadani nevytvaret zkratky, ktere mazou data, odesilaji zpravy,
  plati, meni ucty, posilaji soukrome udaje nebo pouzivaji API klice.
- API klice, tokeny a credentials nikdy neukladat do request draftu.
- Private request drafty a hotove zkratky necommitovat.

## Povinný import postup pro Milu

Kdyz Mila pozada o novou iPhone zkratku a Samantha vytvori podepsany `.shortcut`
soubor, ma v odpovedi vzdy ukazat tento postup a jen dosadit skutecny nazev
zkratky:

1. Na Macu otevri Finder.
2. Jdi do:

```text
/Users/miloslavfalta/Documents/Shortcuts Playground/
```

3. Dvakrat klikni na:

```text
Nazev zkratky
```

4. Mela by se otevrit aplikace Zkratky na Macu a nabidnout import.
5. Pridej zkratku do knihovny.

## Dalsi prakticky krok

1. Pri dalsi nove zkratce vyjit z overeneho pipeline:
   prompt -> XML plist -> validator Craig loop -> `sign_shortcut.sh` -> import
   postup pro Milu -> rucni test na iPhonu.
2. U zkratek s polohou na dalsich iPhonech nejdrive overit, ze aplikace Zkratky
   uz pozadala o polohu a je videt v Polohovych sluzbach.
3. Pro mapy preferovat robustni vetev `Get Maps Link` -> `Open URL` pred primym
   `Get Directions`, pokud se ma jen otevrit cil v Apple Mapach.
4. U zkratky `Rychlá poznámka pro Samanthu` pouzivat dotazy:
   `zobraz rychle poznamky`, `ukaž detail poznámky č. 7` nebo navazne
   `z té poznámky č. 7 uděláme tool`.
