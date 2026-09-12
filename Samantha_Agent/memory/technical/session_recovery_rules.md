# Session recovery rules

Tento soubor popisuje, jak navazovat po vypadku spojeni, aby Mila neztratil kontext
prace se Samantha Agent.

Načítej část odpovídající situaci: start nové relace, obnova SSH/Codexu,
dlouhá práce, autosave nebo ruční handoff. Běžné pokračování stejného úkolu
nevyžaduje opakované čtení celého návodu ani opakování startovací diagnostiky.

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

Pokud chce Mila rovnou predat nove relaci startovni pokyn, lze ho napsat za
prikaz:

```bash
samantha "Nyni prechazime k tematu spravy dokumentu."
```

Pri vzniku nove `screen` relace se tento text vlozi do startovniho promptu Codexu.
Pokud uz `screen` relace bezi a prikaz se jen pripojuje, wrapper pokyn vypise pred
attachnutim, ale nevklada ho automaticky do beziciho Codexu, aby omylem neposlal
text do spatneho terminaloveho stavu. V takovem pripade ho Mila po pripojeni vlozi
rucne.

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
- prevezme volitelny startovni pokyn z prikazu `samantha "..."`,
- pred predanim rizeni vypise kratky read-only report bezicich Codex relaci pres
  `scripts/codex_session_report.py`, vcetne aktualniho TTY, stari
  relaci a kandidatu na rucni ukonceni,
- spusti Codex v `~/Desktop/PythonMF/Samantha_Agent`,
- spusti autosave do `data/session_autosave/`: poslední záznam obnovuje
  standardně každých 10 minut, historické kopie vytváří nejvýše jednou za hodinu,
- pred pripojenim ke `screen` relaci spusti lehky `scripts/network_preflight.sh`,
- diky tomu ma Codex nacist `AGENTS.md` a `memory/MEMORY_INDEX.md`.

Při skutečném startu nové relace zkontroluj stav recovery zálohy:

```bash
.venv/bin/python scripts/backup_status.py
```

Pokud vystup hlasi, ze posledni uspesna zaloha chybi nebo je starsi nez 3 dny,
ma to byt receno v prvni odpovedi kazdy den, dokud nova uspesna zaloha neaktualizuje
`data/backup/activity_state.json`. Pripominka sama nic nekopiruje, nemaze ani
necte tajemstvi.

Při pouhém pokračování stejné relace neopakuj startovací diagnostiku bez
známek problému; denní upozornění na starou nebo chybějící zálohu zůstává.
Při startu Codex CLI podle možnosti spusť nebo otevři Cockpit přes
`scripts/start_cockpit.sh`. Pokud už běží na `http://127.0.0.1:8770`, otevři
existující adresu a neukončuj běžící relaci. Stav autosave ověř přes
`.venv/bin/python scripts/autosave_status.py`; samotná kontrola nic neuklízí.

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

Interval obnovy `latest_session.jsonl` a `latest_session.txt` je výchozí
600 sekund. Změnit se dá proměnnou:

```bash
SAMANTHA_AUTOSAVE_SECONDS=300 samantha
```

Historické soubory `session_YYYYMMDD_HHMMSS.jsonl/txt` mají samostatný interval
`SAMANTHA_AUTOSAVE_HISTORY_SECONDS`, standardně 3600 sekund. Retence níže
se vztahuje na tyto historické dvojice, nikoli na každý desetiminutový zápis.

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

## Retence a uklid autosave

`data/session_autosave/` je jen nouzova lokalni obnova, ne archiv historie.
Proto se ma pravidelne redukovat timestampovana kopie starych snapshotu.

Bezpecny dry-run:

```bash
.venv/bin/python scripts/cleanup_session_autosave.py
```

Vychozi pravidlo:

- `latest_session.jsonl` a `latest_session.txt` obnovovat kazdych 10 minut,
- novy timestampovany JSONL/TXT snapshot vytvorit nejvyse jednou za hodinu,
- automaticky ponechat jen nejnovejsich 12 casovych snapshotu,
- nikdy nemazat `latest_session.jsonl`, `latest_session.txt`, `latest_info.txt`
  ani jine soubory, ktere neodpovidaji tvaru `session_YYYYMMDD_HHMMSS.jsonl/txt`,
- necist obsah autosave souboru, jen nazvy a velikosti.

Autosave stav hlasi volne misto na SSD. Pod 30 GiB jde o varovani a pod 15 GiB
o kriticky stav.

Ostre provedeni vyzaduje explicitni potvrzeni:

```bash
.venv/bin/python scripts/cleanup_session_autosave.py --apply --confirm 'SMAZAT STARE AUTOSAVE'
```

Pokud Mila zada uklid autosave obecne, nejdrive spustit dry-run a ukazat pocet
souboru a odhad uvolneneho mista. Ostry `--apply` spustit az po jasnem souhlasu,
protoze jde o mazani lokalnich nouzovych logu.

## Ruční handoff a předání práce

Tato sekce je kanonický postup a šablona pro `ulož handoff`, `ulož rozpracováno`,
`přeruš práci`, `ulož to jako prioritu 1`, `ulož handoff a připomeň mi to` i
obdobný pokyn. Po důležitém úkolu nebo před ukončením dlouhé práce také zachovej
obnovitelný projektový stav. Povinnou dvojici handoff + TVBCP při vývoji řídí
`project_tvbcp_rules.md`; ruční handoff ji nenahrazuje a nepovoluje nový TVBCP.

1. Z aktuálního kontextu a relevantních podkladů sestav stručný stav.
2. Najdi vazbu projektu/pracovního proudu v registru a jeho existující
   kanonický handoff. Aktualizuj jej; nezakládej paralelní aktuální handoff.
   Pokud vhodný handoff neexistuje a vazba není sporná, vytvoř soubor v
   `memory/handoffs/` pojmenovaný podle tématu a data, např.
   `email_prace_rozdelano_2026_09_12.md`, a zaregistruj jej. Chybějící či
   nejednoznačnou vazbu v Human–Adam vyřeš nebo viditelně označ jako blokátor.
3. Použij prioritu `1`, `2` nebo `3` z pokynu či platného projektového kontextu.
   Pokud téma, priorita, stav nebo další krok zůstávají nejasné, zeptej se jen
   na chybějící údaje, nejvýše třemi krátkými otázkami. Prioritu bez podkladu
   nevymýšlej. Slovní priority ze starších handoffů zpětně nepřepisuj; nové
   zápisy používají výhradně číselné hodnoty.
4. Při požadavku na brzký návrat nastav `Pripomenout pri startu: ano`.
5. Aktualizuj příslušný řádek `memory/ACTIVE_PROJECTS.md`: oblast, prioritu,
   stav, memory soubor, handoff a další praktický krok. Případný TVBCP
   propojuj podle `project_tvbcp_rules.md`.
6. V `memory/MEMORY_INDEX.md` zajisti dohledatelnost nového či změněného odkazu
   a požadované připomenutí. Existující platný odkaz není nutné znovu přepisovat.
   Pro připomenutí přidej do popisu `[PRIPOMENOUT]` a krátké téma.
7. Při navazování připomeň relevantní označené položky; při dotazu na další
   práci zohledni připomenutí z indexu. Historické zápisy zachovej.

Minimální struktura (při aktualizaci existujícího handoffu zachovej jeho
kompatibilní strukturu a doplň odpovídající údaje):

```text
Nazev:
Priorita: 1|2|3
Stav: rozpracovane|ceka na rozhodnuti|ceka na retest|hotovo
Pripomenout pri startu: ano|ne
Datum:

Co se resilo:
Co je hotove:
Co neni hotove:
Dalsi krok:
Navrhovane dalsi kroky:
Zmenene nebo relevantni soubory:
Bezpecnost / neukladat:
```

`Navrhovane dalsi kroky` oddělují u hotového či pozastaveného projektu volitelné
navazující zlepšení od bezprostředního dalšího kroku. Ukládej jen podstatný,
bezpečný stav; chat ani nouzové autosave logy do handoffu nekopíruj.

## Bezpecnost

Do handoffu neukladat hesla, tokeny, app-specific passwords, rodna cisla, citlive
dokumenty ani plny obsah e-mailu bez vyslovneho souhlasu Mily.
