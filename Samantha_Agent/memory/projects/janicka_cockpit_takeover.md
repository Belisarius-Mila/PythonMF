# Janička Cockpit / používání a převzetí Samanthy

## Stav

Založeno 2026-06-06 jako samostatný projekt.

Projekt vznikl po Mílove upřesnění, že nejde o hru, demo ani omezený
režim. Jde o vážný kontinuitní vstup do Samanthy pro Janu.

Stav UI k 2026-06-06:

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
- Jak oddělit běžné používání od nouzového převzetí bez strašení.
- Jak formulovat kuchařku tak, aby byla pro Janu použitelná, ne technická.
- Jak navázat na šifrovaný pozůstalostní balík, aniž by Cockpit ukazoval
  citlivá data v gitu nebo veřejné vrstvě.
- Kdo může být případná další technická osoba pro pokračování vývoje.

## Další krok

Ručně otestovat první MVP obrazovku `Janička` v Cockpitu a podle pocitu
upravit pořadí, texty a první sadu vstupů.

Potom založit první verzi kuchařky pro Janu.

## Bezpečnost / neukládat

- Do tohoto git-safe projektu neukládat hesla, tokeny, recovery klíče,
  telefonní čísla, rodná čísla, celé e-maily ani citlivé konkrétní údaje.
- Citlivé údaje patří pouze do private/šifrovaného pozůstalostního balíku
  mimo git.
