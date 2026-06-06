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
- pred predanim rizeni vypise kratky read-only report bezicich Codex relaci pres
  `scripts/codex_session_report.py`, vcetne aktualniho TTY, bridge markeru, stari
  relaci a kandidatu na rucni ukonceni,
- pri vzniku nove `screen` relace se pred spustenim Codexu zepta, jestli ma
  nastavit voice marker na tuto relaci; vychozi odpoved je `ano`, `ne` ponecha
  dosavadni marker beze zmeny,
- spusti Codex v `~/Desktop/PythonMF/Samantha_Agent`,
- spusti automaticky autosave posledni Codex session kazdych 10 minut do
  `data/session_autosave/`,
- pred pripojenim ke `screen` relaci spusti lehky `scripts/network_preflight.sh`,
- diky tomu ma Codex nacist `AGENTS.md` a `memory/MEMORY_INDEX.md`.

Pri startu nebo navazani ma Codex/Samantha take zkontrolovat stav recovery zalohy:

```bash
.venv/bin/python scripts/backup_status.py
```

Pokud vystup hlasi, ze posledni uspesna zaloha chybi nebo je starsi nez 3 dny,
ma to byt receno v prvni odpovedi kazdy den, dokud nova uspesna zaloha neaktualizuje
`data/backup/activity_state.json`. Pripominka sama nic nekopiruje, nemaze ani
necte tajemstvi.

Preflight je diagnosticky: ve vychozim rezimu nic nevypina, jen vypise stav
VPN/Tailscale procesu, `utun` rozhrani, IP adresu a ping test. Pro pokus o
ukonceni znamych VPN procesu pred startem lze pouzit:

```bash
source ~/.zshrc
SAMANTHA_DISABLE_VPN=1 samantha
```

nebo:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_clean.sh
```

Pokud by preflight sam zpusoboval problem, lze ho docasne preskocit:

```bash
SAMANTHA_PREFLIGHT=0 samantha
```

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

## Prevence zapomenutych Codex relaci

Pri startu pres `samantha` se ma zobrazit read-only prehled bezicich Codex relaci.
Report nema nic ukoncovat automaticky. Pokud ukazuje relaci navic, Mila muze dat
presny pokyn ve tvaru:

```text
Ukonci relaci ttysXXX
```

Codex ma pred ukoncenim znovu overit `ps`, zkontrolovat, ze na danem TTY opravdu
bezi Codex v `Samantha_Agent`, a ukoncit jen odpovidajici Codex procesy, ne jine
prace ani soukrome datove procesy.

## Rucni prevzeti voice markeru

Kdyz bezi vice Codex relaci a Mila v terminalu napise:

```text
Prosím převezmi voice marker
```

nebo podobnou jasnou vetu o prevzeti voice markeru touto relaci, Codex nema marker
prepisovat hned. Nejdrive se zepta presne:

```text
Mám převzít voice marker? y/n
```

Teprve po odpovedi `y` nebo `ano` spusti:

```bash
.venv/bin/python scripts/mark_current_codex_tty.py
```

Pri odpovedi `n` nebo `ne` marker nemeni. Duvod: pri vice paralelnich relacich je
prepnuti voice bridge cile zamerne, ale stale ma byt potvrzene jednim jednoduchym
krokem.

## Pravidlo pro nestabilni spojeni a dlouhe ukoly

Kdyz spojeni nebo Codex opakovane reconnectuje, priorita neni pokracovat v dlouhe
interaktivni praci, ale stabilizovat relaci a zmenit zpusob spousteni ukolu.

Postup:

1. Mila nejdrive zkusi start pres:

```bash
samantha
```

2. Pokud reconnecty pokracuji nebo preflight hlasi VPN/tunely/sitovy problem,
   pouzit cisty start:

```bash
SAMANTHA_DISABLE_VPN=1 samantha
```

nebo:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_clean.sh
```

3. Pokud jde o dlouhy ukol, Codex ho nema poustet jako dlouhy interaktivni tool
   call v chatu. Ma vytvorit nebo pouzit skript, ktery:

- zapisuje prubeh do `logs/` nebo projektove pracovni slozky,
- zapisuje hotovy stav do souboru,
- je idempotentni nebo umi preskocit uz hotove vystupy,
- nemaze data bez vyslovneho souhlasu,
- lze po reconnectu zkontrolovat bez opakovaneho premysleni celeho ukolu.

4. Po dokonceni duleziteho mezikroku ulozit kratky handoff nebo aktualizovat
   relevantni memory soubor, ale neukladat citliva rodinna/media data.

Kdy toto pravidlo pouzit:

- kdyz se behem par minut objevi opakovany reconnect,
- kdyz chat/tool call visi dlouho bez vystupu,
- pred videi, velkymi importy, sifrovanim/exporty nebo hromadnymi operacemi,
- kdyz Mila pise, ze se se spojenim neda pracovat.

## Pravidlo primereneho checkpointovani

Checkpointovane workflow se nema pouzivat na kazdou drobnost, aby nevznikala
zbytecna rezie. Codex ma pred delsi praci rychle rozhodnout podle rizika:

### Bez checkpointovaneho workflow

Pouzit primou upravu nebo jeden kratky prikaz, kdyz plati vsechny podminky:

- ukol je maly a snadno opakovatelny,
- cte nebo meni jednotky souboru,
- doba behu je radove sekundy az nizke minuty,
- nevznika mnoho vystupu,
- pripadny pad nezpusobi ztratu drahe prace,
- nejde o citliva data, mazani, presun nebo hromadny zapis.

Priklady:

- mala oprava textu nebo jedne funkce,
- jeden cilovy test,
- kratky read-only dotaz,
- mala dokumentacni uprava.

### Lehky checkpoint

Pouzit manifest, log nebo kratky stavovy vystup, kdyz je ukol stredni:

- pracuje s vice soubory, ale ne stovkami,
- trva nekolik minut,
- vytvari vystupy, ktere stoji za kontrolu,
- muze selhat na jednotlivych polozkach.

Minimalni forma:

- seznam vstupu,
- vystupni slozka,
- kratky log nebo summary,
- kontrola po dokonceni.

### Plne checkpointovane workflow

Pouzit skript po davkach se stavovym souborem, kdyz plati aspon jedna podminka:

- ukol muze trvat dele nez cca 5-10 minut,
- pracuje s desitkami az stovkami souboru nebo zaznamu,
- pouziva sit, TTS, OCR, generovani obrazku, PDF export, video/media operace,
  sifrovani nebo GitHub Actions,
- zpracovava citlive nebo soukrome dokumenty,
- vysledek je drahy casove, kreditove nebo pracovne,
- spojeni je nestabilni nebo uz doslo k reconnectu,
- Mila vyslovne chce moznost navazat po padu.

Minimalni forma:

- vstupni manifest,
- stavovy soubor s hotovymi a chybovymi polozkami,
- davkove zpracovani,
- idempotence: hotove polozky se pri restartu preskoci,
- validace po davce,
- finalni summary,
- zadne mazani bez potvrzeni.

Prakticky vychozi postup:

1. Nejdriv vytvorit nebo nacist manifest.
2. Zpracovat malou davku.
3. Zapsat vystupy a stav.
4. Zkontrolovat pocty, existenci souboru a chyby.
5. Teprve potom pokracovat dalsi davkou.

Toto pravidlo ma byt pouzito pragmaticky: checkpointovani je ochrana pred
ztratou prace, ne povinna ceremonie u malych zmen.

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
- navrhovane dalsi kroky, pokud je projekt hotovy nebo pozastaveny a je uzitecne
  oddelit povinny dalsi krok od volitelnych zlepseni.

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
