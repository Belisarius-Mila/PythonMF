# Cockpit hlavni obrazovka: co je opravdu denni

Datum: 2026-06-11
Rozsah: read-only faze 2 po UI cleanup experimentu. Cilem neni dalsi kodova zmena, ale rozhodnuti, co ma byt na hlavni obrazovce videt rano bez klikani a co ma byt dostupne pres jasne dvere.

## Kratke shrnuti

Hlavni obrazovka Cockpitu ma byt ranni rozhodovaci panel, ne mapa celeho systemu.

Doporuceny princip:

- `Denne` = ukazat bez klikani, pokud z toho plyne dnesni rozhodnuti nebo rychla akce.
- `Obcas` = nechat snadno dostupne v horni liste nebo jednim rozbalenim, ale netlacit jako ranni stav.
- `Servis` = ukazat na hlavni obrazovce jen jako semafor nebo varovani; detail schovat pod `Servis` / `Diagnostika`.
- `Archiv` = nemusi byt na prvni obrazovce, patri do projektu, reportu nebo vyhledavani.

Aktualni zivy stav pri auditu:

- Dokumenty: 0 novych PDF, 0 problemu, 0 dokumentu k revizi.
- Action queue: 1 akutni polozka.
- Pripomenuti: 1 otevrene, 0 aktivnich, 0 konfliktu.
- Zaloha: posledni uspesna 2026-06-07, stara 4 dny, tedy ma byt rano videt jako konkretni upozorneni.
- Git: cisty pracovni strom, ale lokalni vetev ceka na push.
- ScanDocu: bezi.

## Denne

Tyto prvky maji zustat na hlavni obrazovce bez rozbaleni.

### Ranni veta / hlavni semafor

Priklad:

```text
Samantha je vzhuru. Dnes zkontrolovat: zaloha. Dokumenty jsou klidne.
```

Ma nahradit potrebu cist technicke radky. Kdyz je vse v poradku, ma byt kratka. Kdyz neco hori, ma rict co a kam kliknout.

### Co ted delat

Tohle ma byt hlavni denni blok. Ma ukazovat jen rozhodovaci karty:

- dulezite pripomenuti,
- platebni konflikt,
- dokumentovy problem,
- nove PDF,
- dokument k revizi,
- dnesni nebo brzka pripominka,
- zaloha, pokud je po limitu.

Karta ma vzdy obsahovat:

- lidsky nazev,
- proc to resit,
- jedno hlavni tlacitko.

### Dnes

Nechat jako maly souhrn dokumentove fronty:

- nova PDF,
- k revizi,
- problemy.

Kdyz jsou vsechny hodnoty nula, karta muze byt klidna a mala. Kdyz je neco nenulove, teprve potom ma otevirat `Dokumenty`.

### Dulezita pripomenuti

Alert patri nahoru jen pri realne dulezitem vstupu. Pokud nejsou dulezita pripomenuti, nemaji zabirat prostor.

### Najit dokument

Patri na prvni obrazovku, protoze je to prakticka denni akce pro Milu i Janu. Vyhledavani je lepsi vstup nez proklikavani archivnich prehledu.

### Janička

Tlacitko `Janička` ma zustat viditelne v horni liste. Je to lidsky vstup bez technicke vrstvy.

## Obcas

Tyto prvky maji byt rychle dostupne, ale nemusi se tvarit jako denni stav.

### Knihovna

Nechat v horni liste. Je to casto uzitecne, ale neni to ranni varovani.

### E-maily

Nechat v horni liste nebo jako karta v `Co ted delat`, pokud jsou e-maily k rozhodnuti.

Pravidlo:

- kdyz nejsou e-maily k rozhodnuti, staci tlacitko `E-maily`,
- kdyz jsou nove nebo rozpracovane e-maily, patri karta do `Co ted delat`.

### ScanDocu a Revidovat dokumenty

Tyto akce nemaji byt stale primarni, pokud dokumentova fronta je nula.

Pravidlo:

- kdyz je nove PDF, hlavni karta ma ukazat `Zpracovat`,
- kdyz je dokument k revizi, hlavni karta ma ukazat `Revidovat`,
- kdyz je klid, ScanDocu muze byt jen tlacitko v dokumentovem detailu nebo horni liste.

### Hlasovy pokyn

Je denni jen v hlasovem rezimu. Jinak patri do obcasne vrstvy.

Doporuceni:

- na hlavni obrazovce nechat jen maly stav `Hlas: vypnuto / Adam posloucha / ceka pokyn`,
- velky textarea blok, nahravani a bridge detaily ukazovat az po kliknuti `Hlas`.

### Projekty

Tlacitko `Projekty` muze zustat v horni liste, ale projektove seznamy a handoffy nemaji byt na prvni obrazovce. Do `Co ted delat` patri jen projekt, ktery ma jasne `ceka na Milu`, `blokovano` nebo `[PRIPOMENOUT]` s dnesnim dopadem.

### Webove aplikace

Rozcestnik. Ne denni stav.

### Rychle poznamky / QN

Pokud QN nema aktivni vstup k rozhodnuti, patri mimo hlavni obrazovku. Pokud existuje novy hlasovy/textovy vstup, muze se objevit v `Co ted delat`.

## Servis

Tyto veci maji byt dostupne, ale na hlavni obrazovce jen jako semafor nebo varovani.

### Zaloha

Zaloha je servisni vec, ale kdyz je po limitu, stava se denni akci.

Doporuceni:

- hlavni obrazovka: `Zaloha: stara 4 dny - pripojit disk a spustit zalohu`,
- detailni cesta a technicky text az pod `Servis`.

### Git

Git nema byt denni karta, pokud je cisty. Kdyz je dirty nebo ahead, muze byt maly servisni signal:

- `Git: cisty, ceka push`,
- detail az pod `Servis`.

### Technicky stav Cockpitu

`Frontend`, `Tlacitka`, `API`, `Posledni chyba` patri pod `Technicky stav Cockpitu`, ne do denniho prehledu. Na hlavni obrazovce ma byt jen souhrn `Cockpit odpovida`.

### Diagnostika, Recovery, Restart, Terminal

Patri pod `Servis`.

Zustavaji dohledatelne, ale nemaji byt v hlavnim rannim proudu.

### Systémový souhrn a Kontrola nesrovnalostí

Patri do servisu, pokud jen informuji. Do `Co ted delat` patri pouze konkretni nalez:

- konflikt,
- nesrovnalost s navrzenou akci,
- dokument, ktery chce rozhodnuti.

### ScanDocu stav

`ScanDocu bezi/nebezi` je servisni signal. Dennim prvkem se stava az tehdy, kdyz existuje nove PDF nebo problemovy dokument.

### Voice bridge pokrocile

`TTY`, `screen`, `Codex relace`, `voice marker`, `effective_tty` patri jen do pokrocile diagnostiky hlasu.

## Archiv

Tyto veci nemaji byt na prvni obrazovce.

- archivovane projekty,
- historicke handoffy,
- dlouhe systemove reporty,
- raw autosave metadata,
- dlouhe tabulky PDF ve Downloads,
- dlouhy souhrn vaultu,
- historicke webove aplikace a prototypy,
- kompletni projektove registry.

Archiv nema znamenat "schovat tak, ze to nejde najit". Ma znamenat:

- najitelne pres `Projekty`, `Servis`, `Dokumenty` nebo vyhledavani,
- neviditelne v rannim rozhodovacim proudu, pokud z toho neplyne dnesni akce.

## Doporučena podoba hlavni obrazovky

### Bez klikani

1. Horni lista:
   - `Janička`
   - `Obnovit`
   - `Knihovna`
   - `E-maily`
   - `Připomenutí`
   - `Projekty`
   - `Servis`

2. Ranni veta:
   - `Samantha je vzhuru; zkontrolovat: zaloha.`

3. `Co ted delat`:
   - max 3 hlavni karty,
   - dalsi polozky az po `Zobrazit dalsi`.

4. `Dnes`:
   - mala dokumentova metrika,
   - rozbalit `Dokumenty` jen pri nenulove fronte.

5. `Najit dokument`:
   - ponechat primo.

### Po kliknuti `Dokumenty`

- nova PDF,
- ulozene dokumenty k revizi,
- problemy,
- intake,
- souvisejici dokumenty,
- klasifikace,
- terminy,
- dokumenty k revizi report.

### Po kliknuti `Servis`

- technicky stav Cockpitu,
- zaloha detail,
- git detail,
- ScanDocu stav,
- diagnostika,
- recovery centrum,
- restart,
- terminal,
- systemovy souhrn,
- kontrola nesrovnalosti,
- hlasove pokrocile detaily.

### Po kliknuti `Archiv` nebo pres projekty

- archivovane projekty,
- stare handoffy,
- systemove reporty,
- dlouhe historicke seznamy.

## Minimalni implementacni dalsi krok

Pokud se tento navrh potvrdi, nejmensi bezpecna kodova zmena by byla:

1. Prejmenovat kartu `Akce` na `Rychle akce`.
2. V horni liste pridat jedno tlacitko `Servis` a presunout tam servisni tlacitka.
3. Z velkeho `Hlasovy pokyn` udelat rozbalovaci sekci `Hlas` nebo ji ukazovat jen pri aktivnim hlasovem rezimu / cekajicim pokynu.
4. `Co ted delat` posunout vizualne pred hlasovy panel.
5. V `Stav` ponechat jen lidske radky:
   - Dokumenty,
   - Připomenutí,
   - Hlas,
   - Záloha,
   - Systém.
   Detaily `Projekty`, `QN`, `Git`, `Kontrola`, `ScanDocu` presunout do servisu nebo ukazat jen pri varovani.

Nezasahovat zatim do backendu ani potvrzovacich bran.
