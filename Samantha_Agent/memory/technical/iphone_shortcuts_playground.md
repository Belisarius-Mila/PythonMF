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

1. Nainstalovat nebo zprovoznit Shortcuts Playground plugin pro Codex.
2. Spustit `iphone_shortcuts_playground_status()`.
3. Pripravit prvni velmi jednoduchou testovaci zkratku bez citlivych akci.
4. Rucne ji otevrit v Apple Shortcuts a overit import.
5. Teprve potom rozsirovat workflow na uzitecne zkratky pro Milu.
