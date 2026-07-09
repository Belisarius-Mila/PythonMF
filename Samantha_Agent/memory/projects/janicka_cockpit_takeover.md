# Janička Cockpit / používání a převzetí Samanthy

## Stav

Založeno 2026-06-06 jako samostatný projekt.

Projekt vznikl po Mílove upřesnění, že nejde o hru, demo ani omezený
režim. Jde o vážný kontinuitní vstup do Samanthy pro Janu.

Stav UI k 2026-06-07 po auditu kódu:

- První MVP tlačítka `Janička` je implementované v hlavním Cockpitu.
- Tlačítko otevírá samostatnou netechnickou obrazovku / modal, ne nové okno.
- Obrazovka neduplikuje backendovou logiku; používá existující funkce
  Cockpitu a jen je překládá do lidských vstupů.
- Po skoku z Janičky je doplněná návratová cesta:
  - vnitřní modaly jako aplikace/projekty/připomenutí/recovery se po zavření
    vrací zpět na Janičku,
  - skok na dokumentové hledání nebo Adama ukáže plovoucí tlačítko
    `Zpět k Janičce`,
  - samostatná popup okna jako Lékárna nebo Email Processing nechávají
    Janičku otevřenou v hlavním Cockpitu.
- Přímé vstupy v první verzi:
  - Najít dokument,
  - Vytisknout dokument,
  - E-maily,
  - Lékárna,
  - Rodinné projekty,
  - Zeptat se Adama,
  - Připomenutí,
  - Nouzové převzetí,
  - Všechny aplikace,
  - Projekty a kuchařka.

Audit potvrzen v `app/cockpit.py`: modal `Janička` existuje, tlačítka jsou
napojená na existující Cockpit funkce a v této vrstvě nejsou uložená hesla,
tokeny ani konkrétní citlivé údaje.

První git-safe kuchařka pro Janu je založená v
`memory/projects/janicka_cockpit_kucharka.md`. Je to provozní návod k
aktuálnímu MVP, ne šifrovaný nouzový balík.

Od 2026-06-07 je kuchařka vystavená také jako čitelná lokální HTML stránka v
Cockpitu na `/janicka-kucharka/`. Tlačítko `Kuchařka` v modalu `Janička`
otevírá tuto stránku v samostatném okně; stránka je read-only a umí tisk.

Od 2026-06-07 tlačítko `Zeptat se Adama` v Janičce otevírá samostatný textový
chatový modal a backend endpoint `/api/janicka/chat`. První smoke test přes
lokální API vrátil odpověď `Ano, textový chat funguje.` Rodinné projekty jsou
zatím další část k doladění.

Po Mílově testu bylo 2026-06-07 upřesněno, že odpověď nesmí působit jako
anonymní AI bez znalosti projektu. Endpoint `/api/janicka/chat` proto před
každou odpovědí přikládá git-safe projektový kontext z kuchařky, projektu
Janička, aktivních projektů a memory indexu. Živý test na dotaz `co je Janička
Cockpit` vrátil věcnou odpověď s vazbou na Samanthu a Janu.

Další test ukázal, že dotaz `najdi poslední QN` se nesmí nechávat na obecném
modelu ani na starším vzestupně řazeném výpisu quick notes. Od 2026-06-07
Janička chat pro fráze typu `poslední QN` a navazující `detail` používá přímo
Cockpit Quick Notes status/detail. Živý test vrátil správně poslední aktivní
poznámku `QN #37` z `2026-06-05 05:14:45`, ne starší `QN #5`.

Po dalším Mílově testu bylo rozhodnuto, že odpovídat nemá separátní agent ani
model s přiloženou pamětí, ale přímo běžící Codex/Adam v pracovní relaci.
Janička chat proto od 2026-06-07 normální zprávy předává přes terminálový
Codex bridge do označené Codex relace a nevolá `ask_samantha()`. Okno zobrazí
stav předání a umí čekat na odpověď zapsanou zpět přes
`scripts/adam_voice_reply.py --user-text ... --route janicka_text_bridge`.

Následné upřesnění: Jana nebude umět spustit Codex ručně a má mít spuštěný jen
Cockpit. Proto vzniká managed Adam service:

- `app/adam_service.py` spravuje screen relaci `samantha_adam`,
  request/response frontu v `data/private/adam_text_bridge/` a prompt pro Codex.
- Cockpit má API `/api/adam/status`, `/api/adam/start`, `/api/adam/restart` a
  `/api/adam/stop`.
- `Jana Adam` při odeslání dotazu zkusí Adama spustit, založí `request_id`,
  doručí prompt do managed Codex relace a čeká na odpověď podle `request_id`.
- `scripts/adam_voice_reply.py` umí nově `--request-id`, aby Adam mohl odpověď
  zapsat zpět ke konkrétnímu dotazu z okna Janička.

Od 2026-07-01 po reálném testu zavření VS Code/Codexu je výchozí doručení
textového dotazu pro `Jana Adam` spravovaná screen relace `samantha_adam`, ne
viditelný Terminal/VS Code tab. Oprava řeší tři konkrétní body:

- start `samantha_adam` vypíná autosave resume prompt a work-context guard, aby
  se skrytá relace nezasekla před spuštěním Codexu,
- stav Adama se počítá podle skutečného Codex procesu uvnitř `samantha_adam`,
  ne jen podle existence screen relace nebo obecného voice markeru,
- dotaz se doručuje přes `screen -S samantha_adam -p 0 -X stuff`, s krátkou
  pauzou a samostatným Enterem; ověřený test vrátil odpověď do Cockpitu bez
  ručního zásahu.

Globální voice marker se při startu Janička Adama nepřepisuje; zůstává pro
běžný Mílův hlasový bridge. Explicitní helper pro viditelnou VS Code cestu
zůstává k dispozici, ale není výchozí.

## Základní shoda

Janička Cockpit není zvláštní omezený přístup.

Jana nemá být chráněná před Samanthou jako před nebezpečným systémem a nemá
mít uměle ořezaná práva jen proto, že není Míla. Není cílem vytvořit
„dětský režim“ ani izolovanou kopii. Cílem je vytvořit srozumitelný,
praktický a lidský vstup do hotových plodů práce.

Obecná bezpečnostní opatření mají platit pro celý systém:

- destruktivní akce potvrzovat,
- mazání a odesílání držet pod kontrolou,
- citlivá data neukládat do gitu,
- zálohy a obnovu dělat opakovatelně,
- návody psát tak, aby šly použít i bez Míly.

Tato bezpečnost nemá být speciální omezení pro Janu.

## Dva režimy

### 1. Jana používá Samanthu, když Míla dočasně nemůže

Tento režim je pro situace, kdy Míla z nějakého důvodu nemůže efektivně
pracovat v týmu Míla + Adam, ale Samantha jako praktický domácí systém má
dál sloužit.

Jana má mít normální přístup k užitečným částem:

- hledání dokumentů,
- čtení dokumentů,
- tisk dokumentů,
- hledání a čtení e-mailů,
- praktické použití Lékárny,
- spouštění připravených aplikací,
- práce s předem připravenými projekty a daty,
- rodinné projekty typu USA,
- dotazování Adama v lidské podobě bez nutnosti znát technické příkazy.

V tomto režimu Jana nemá dělat vývoj, experimenty s IT ani partizánské
technické akce. To ale řeší rozhraní, workflow a návody, ne zákaz přístupu.

Praktický směr:

- tlačítko `Janička` nahoře v Cockpitu,
- jasný rozcestník,
- velké praktické vstupy,
- minimum technických slov,
- jasné akce typu `Najít dokument`, `Vytisknout`, `Otevřít Lékárnu`,
  `Otevřít rodinný projekt`, `Zeptat se Adama`,
- průvodce, který vysvětluje kontext a další krok.

### 2. Jana plně přebírá Samanthu po Mílově smrti

Tento režim patří primárně do projektu Pozůstalost / rodinný nouzový balík.
Nejde jen o používání hotových funkcí, ale o vlastnictví a kontinuitu.

Jana musí mít možnost Samanthu převzít na 100 %:

- pochopit, co Samantha je,
- zjistit, kde jsou data,
- najít zálohy,
- obnovit systém na novém Macu,
- získat přehled o GitHub/repo vrstvě,
- předat technické pokračování další osobě,
- rozhodnout, zda se Samantha bude dál rozvíjet,
- případně ve spolupráci s někým dalším pokračovat ve vývoji.

Tento režim nemá být hlavní obsah tlačítka `Janička`, ale tlačítko má na něj
umět odkázat jako na nouzovou část.

## Vztah k pozůstalosti

Pozůstalost a Janička Cockpit jsou propojené, ale nejsou totéž.

Pozůstalost:

- řeší smrt, právní a praktické převzetí,
- řeší zálohy, obnovu, účty, repozitáře a šifrovaný nouzový balík,
- má obsahovat citlivé konkrétní údaje pouze v bezpečném private/šifrovaném
  uložení mimo git.

Janička Cockpit:

- je živé tlačítko v Cockpitu,
- pomáhá Janě používat Samanthu,
- rozcestníkuje hotové aplikace a workflow,
- má být příjemné, praktické a netechnické,
- nemá suplovat celý pozůstalostní balík.

Krátce: pozůstalost je nouzový plán, Janička Cockpit je každodenně použitelný
vstup.

## První návrh tlačítka

Tlačítko:

```text
Janička
```

Charakter:

- nahoře viditelné,
- teplé/růžové ladění,
- důstojné, ne infantilní,
- ne jako hra, ale jako laskavý vstup do systému.

První obrazovka může mít sekce:

- `Používat Samanthu`
- `Dokumenty a tisk`
- `E-maily`
- `Lékárna`
- `Rodinné projekty`
- `Zeptat se Adama`
- `Když Míla nemůže`
- `Nouzové převzetí`

## První MVP

Stav k 2026-06-07: MVP rozcestník je implementovaný. Následující seznam je
původní minimální rozsah, který už byl pro první verzi splněn.

Nejmenší užitečný krok:

1. Přidat do Cockpitu viditelné tlačítko `Janička`.
2. Otevřít jednoduchý rozcestník bez destruktivních akcí.
3. Nabídnout praktické vstupy:
   - Dokumenty,
   - Lékárna,
   - e-mailový přehled,
   - rodinné projekty,
   - Adamův hlas/textový vstup,
   - nouzová orientace.
4. Sepsat krátkou kuchařku pro Janu:
   - co Samantha umí,
   - co dělat při běžné potřebě,
   - kdy se ptát Adama,
   - kdy požádat technického člověka,
   - kde je pozůstalostní plán.

## Otevřené otázky

- Jaké konkrétní projekty mají být v první verzi nabídnuté Janě.
- Jak navázat na šifrovaný pozůstalostní balík, aniž by Cockpit ukazoval
  citlivá data v gitu nebo veřejné vrstvě.
- Kdo může být případná další technická osoba pro pokračování vývoje.
- Ručně ověřit s Janou, jestli názvy akcí v Janičce odpovídají tomu, co by
  sama hledala.
- Rozhodnout, které rodinné projekty mají být v Janičce zvýrazněné hned a
  které stačí nechat pod `Všechny aplikace`.

## Další krok

Ručně projít obrazovku `Janička` přímo s Janou nebo z její perspektivy:

- otevřít `http://127.0.0.1:8770`,
- kliknout na `Janička`,
- projít postupně Dokumenty, Lékárnu, E-maily, Rodinné projekty, Adama,
  Připomenutí a Nouzové převzetí,
- zapsat, která slova jsou pro Janu nejasná nebo příliš technická,
- podle toho upravit texty v UI a kuchařce.

Kuchařka už je dostupná přímo z tlačítka `Kuchařka`. `Zeptat se Adama` má
samostatný textový chat a po reálném testu funguje jako most do běžící Adamovy
Codex relace. Další krok je nechat kanál zatím stabilně používat a potom opravit
`Rodinné projekty`.

Poznámka z 2026-06-07: krátce se zkoušela skrytá `screen` relace
`samantha_adam`, aby se nepřepínal fokus z Cockpitu. Tato cesta ale uměla dotaz
označit jako doručený, aniž by ho Codex reálně převzal. Funkční stav je proto
výchozí terminálový bridge: před vložením se čistí vstup, cílí na označenou
nebo nalezenou Codex relaci a odpověď se zapisuje do Cockpitu přes
`scripts/adam_voice_reply.py --request-id ... --route janicka_text_bridge`.
Explicitní VS Code helper zůstává jen jako fallback/helper. Reálné testy dotazů
`Jak funguje Najít dokument?` a `Co mi můžeš říct o projektu Pozůstalost?`
prošly; poslední naměřené čekání bylo zhruba 44 sekund, což je přijatelné pro
odpověď skutečnou Codex relací.

## Aktuální checkpoint 2026-07-03

Po reálných testech z Janička Cockpitu se ukázalo, že samotná `screen` cesta
umí první dotaz doručit a vrátit odpověď, ale druhý dotaz se opakovaně ztrácel
nebo nebyl převzat Codexem. Aktuální implementace proto odděluje Janička chat
do light relace `samantha_janicka` a přidává více vrstev doručení:

- start light relace přečte jen projektová pravidla a relevantní memory, potom
  čeká bez vlastních návrhů,
- doručení přes `screen` se považuje za úspěšné až po ověření `Request ID`
  v hardcopy výstupu relace,
- při neověřeném screen doručení se zkusí přímý managed Codex TTY fallback,
- pokud macOS TTY vložení odmítne, dotaz zpracuje read-only `codex exec`
  worker a odpověď zapíše zpět do Janička request/reply store,
- Cockpit má servisní ovládání light relace přes
  `/api/janicka/light/status`, `/api/janicka/light/start` a
  `/api/janicka/light/stop`.

Tento stav je checkpointnutý v
`memory/handoffs/janicka_light_samantha_bridge_checkpoint_2026_07_03.md`.
Další krok je ruční retest více navazujících dotazů přímo z okna `Janička`.

## Aktuální checkpoint 2026-07-09 - nouzová záloha bez VS Code

Reálný test bez VS Code ukázal, že Janička light je použitelná pro běžné
odpovědi, ale při složitější práci může narazit na timeout nebo omezený rozsah.
Proto byla doplněna samostatná nouzová cesta:

- v Janičce je jako první karta `Když Adam light nestačí`,
- tlačítko `Otevřít plného Adama` volá pevný endpoint
  `/api/janicka/full-adam/open`,
- endpoint otevře Terminal s přímým interaktivním
  `codex --no-alt-screen -C ...`,
- startovní prompt říká Janě, že má psát normální větou a nemusí znát příkazy,
- bez potvrzení se nemá nic posílat, mazat, přesouvat, platit ani měnit,
- UI zobrazuje i ruční fallback pro případ, že automatické otevření Terminalu
  selže.

Na Macu jsou mimo git připravené viditelné launchery pro otevření Cockpitu a
podepsaná iPhone zkratka `Janička SOS.shortcut` je připravená k nasdílení Janě.
Zkratka sama Mac nespouští na dálku; je to navigační karta s kroky.

Checkpoint je uložený v
`memory/handoffs/janicka_full_adam_cockpit_recovery_ios_card_2026_07_09.md`.
Další krok je nasdílet/importovat zkratku na Janin iPhone a společně projít
celou cestu: iPhone karta -> Mac `Aplikace` -> `JANIČKA OTEVŘÍT COCKPIT`
-> `Janička` -> `Otevřít plného Adama`.

## Bezpečnost / neukládat

- Do tohoto git-safe projektu neukládat hesla, tokeny, recovery klíče,
  telefonní čísla, rodná čísla, celé e-maily ani citlivé konkrétní údaje.
- Citlivé údaje patří pouze do private/šifrovaného pozůstalostního balíku
  mimo git.
