# iPhone Shortcuts Playground workflow

Priorita: 2
Pripomenout pri startu: ne
Datum: 2026-05-23

## Ucel

Pripravit Samanthu na tvorbu Apple Shortcuts / iPhone zkratek pres MacStories
Shortcuts Playground.

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
- Rucni import a test v2 na iPhonu jeste nejsou potvrzene.

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

## Dalsi prakticky krok

1. Rucne otevrit `Najit auto v2.shortcut` v Apple Shortcuts.
2. Zkontrolovat akce:
   menu `Ulozit polohu auta` / `Navigovat k autu`, polohove opravneni,
   ulozeni parked car a otevreni Apple Map.
3. Otestovat na iPhonu: nejdriv ulozit polohu, potom navigovat.
4. Pokud import nebo logika selze, vzit archivovane XML a opravit shortcut.
5. Teprve po realnem testu rozsirovat workflow na dalsi uzitecne zkratky.
