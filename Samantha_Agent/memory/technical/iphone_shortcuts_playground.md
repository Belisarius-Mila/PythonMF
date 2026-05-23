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
- Vystupni slozka `~/Documents/Shortcuts Playground/` zatim nevznikla.
- Prvni realny `.shortcut` jeste neni vygenerovany ani rucne otestovany.
- Pro plne nacteni pluginu je pravdepodobne potreba nova Codex relace.

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

1. V nove Codex relaci overit, ze je Shortcuts Playground plugin skutecne nacteny.
2. Spustit `iphone_shortcuts_playground_status()`.
3. Pripravit nebo pouzit request pro prvni zkratku `Najit auto`.
4. Vygenerovat `.shortcut` pres Shortcuts Playground.
5. Rucne ji otevrit v Apple Shortcuts a overit import, oprávneni a logiku.
6. Teprve potom rozsirovat workflow na dalsi uzitecne zkratky pro Milu.
