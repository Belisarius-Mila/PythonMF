# Session recovery rules

Tento soubor popisuje, jak navazovat po vypadku spojeni, aby Mila neztratil kontext
prace se Samantha Agent.

## Dve vrstvy navazani

1. `screen` chrani bezici terminalovou relaci pri vypadku SSH z iPhonu nebo jineho
   klienta. Pokud SSH spadne, Codex muze bezet dal na Macu.
2. Projektova pamet v `memory/` chrani dlouhodoby kontext, kdyz spadne samotny Codex
   nebo je potreba zacit novy chat.

## Doporučený start

Pro beznou praci pouzit:

```bash
samantha
```

V novem SSH terminalu, pokud prikaz `samantha` jeste neni znamy, nejdriv nacist
shell konfiguraci a pak spustit Samanthu:

```bash
source ~/.zshrc
samantha
```

Funkce `samantha` ma spustit projektovy skript:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_codex.sh
```

Skript:

- pripoji existujici `screen` relaci `samantha_codex`, pokud uz bezi,
- jinak zalozi novou `screen` relaci,
- spusti Codex v `~/Desktop/PythonMF/Samantha_Agent`,
- spusti automaticky autosave posledni Codex session kazdych 10 minut do
  `data/session_autosave/`,
- diky tomu ma Codex nacist `AGENTS.md` a `memory/MEMORY_INDEX.md`.

## Po vypadku SSH

Po novem SSH prihlaseni spustit:

```bash
samantha
```

Pokud terminal hlasi, ze `samantha` nezna, pouzit:

```bash
source ~/.zshrc
samantha
```

Pokud bezi screen relace, prikaz se na ni pripoji a bude videt presne stejna bezici
konverzace.

Rucni varianta:

```bash
screen -ls
screen -r samantha_codex
```

Odpojeni bez ukonceni:

```text
Ctrl+A, potom D
```

## Kdyz spadne Codex, ne jen SSH

Pouzit:

```bash
codex resume --last
```

Nebo presne session ID, pokud je zname:

```bash
codex resume <SESSION_ID>
```

Pri vyzve na adresar vybrat session directory `~/Desktop/PythonMF/Samantha_Agent`.

## Automaticky autosave

Pri spusteni pres `samantha` bezi na pozadi:

```bash
scripts/autosave_codex_session.sh --watch
```

Interval je vychozi 600 sekund. Zmenit se da promennou:

```bash
SAMANTHA_AUTOSAVE_SECONDS=300 samantha
```

Autosave uklada technicke kopie posledniho Codex session logu a citelny textovy
snapshot do:

```text
data/session_autosave/
```

Typicke soubory:

- `latest_session.jsonl` - presny technicky log pro nouzovou obnovu.
- `latest_session.txt` - citelny textovy vytah uzivatelskych a asistentskych zprav.
- `session_YYYYMMDD_HHMMSS.jsonl` - casovana technicka kopie.
- `session_YYYYMMDD_HHMMSS.txt` - casovana textova kopie.

Dulezite: tyto soubory mohou obsahovat citlive udaje z konverzace. Proto jsou
ignorovane v `.gitignore` a nemaji se commitovat ani kopirovat do `memory/` bez
rucni kontroly.

## Povinnost pri dulezite praci

Po dulezitem ukolu nebo pred ukoncenim dlouhe prace ulozit kratky handoff do:

```text
memory/handoffs/
```

Staci napsat kratky prikaz:

```text
uloz handoff
```

nebo napr.:

```text
uloz to jako prioritu 1 a pripomen mi to
```

Codex ma podle pravidel v `AGENTS.md` vytvorit handoff z aktualniho kontextu,
zeptat se jen na nejasne udaje a aktualizovat `ACTIVE_PROJECTS.md`.

Aktualizovat take registr aktivnich projektu:

```text
memory/ACTIVE_PROJECTS.md
```

V registru upravit prioritu, stav, odkaz na memory soubor, odkaz na pripadny
handoff a dalsi prakticky krok.

a pridat odkaz do:

```text
memory/MEMORY_INDEX.md
```

Handoff ma obsahovat:

- dobry nazev, ze ktereho je poznat projekt i stav,
- metadata `Priorita`, `Pripomenout pri startu` a `Stav`,
- co se resilo,
- jaky je aktualni stav,
- jake soubory byly zmeneny,
- co je dalsi prakticky krok,
- co se nesmi zapsat do pameti nebo gitu.

Doporuceny zacatek handoffu:

```text
Nazev: Emailova komunikace - projekt rozdelany k dokonceni
Priorita: dulezite
Pripomenout pri startu: ano
Stav: rozdelane
Datum: YYYY-MM-DD
```

Hodnoty `Priorita` pouzivat stridme:

- `kriticke` - je potreba pripomenout hned pri dalsim startu, hrozi ztrata navaznosti.
- `dulezite` - rozdelany projekt nebo ukol, ktery ma byt videt v dalsim navazani.
- `normalni` - bezny handoff pro dohledani.
- `archiv` - hotovo, jen historicky zaznam.

Pokud je `Pripomenout pri startu: ano`, pridat i jasnou vetu do popisu v
`memory/MEMORY_INDEX.md`, napriklad:

```text
[PRIPOMENOUT] emailova komunikace - rozdelany projekt k dokonceni
```

Pri startu nove relace po precteni `MEMORY_INDEX.md` aktivne upozornit Milu na
polozky oznacene `[PRIPOMENOUT]`, pokud jsou relevantni k aktualnimu dotazu nebo
pokud se pta, na cem se ma pokracovat.

## Bezpecnost

Do handoffu neukladat hesla, tokeny, app-specific passwords, rodna cisla, citlive
dokumenty ani plny obsah e-mailu bez vyslovneho souhlasu Mily.
