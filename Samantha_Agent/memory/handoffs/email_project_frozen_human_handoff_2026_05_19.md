# Handoff: E-mailovy projekt pozastaven - lidsky prehled

Nazev: iCloud Mail / Email Cases - pozastaveno po zakladni funkcni vrstve
Priorita: 1
Stav: pozastaveno / rozpracovany zaklad
Pripomenout pri startu: ano
Datum: 2026-05-19

## Proc se projekt pozastavuje

Mila potrebuje rychleji dotahnout jine oblasti. E-mailovy projekt ma uz solidni
technicky zaklad, ale v bezne praxi zatim porad pusobi tezkopadne: umi vyhledat,
precist, ulozit pripominku, ulozit bezpecny case a archivovat dulezity e-mail,
ale jeste nevede Milu dostatecne lidsky celou praci od nalezu e-mailu az po
vyreseni veci na webu nebo odeslani odpovedi.

Projekt se proto nema zahazovat. Ma zustat jako priorita 1 k pripomenuti, ale
do dalsi aktivni prace se ma navazat az po precteni tohoto handoffu.

## Co uz Samantha s e-maily umi lidsky

### 1. Najit e-maily

Samantha umi read-only pracovat s iCloud Mail pres IMAP:

- vypsat posledni hlavicky,
- hledat v hlavickach podle dotazu,
- spustit triage za poslednich N dni,
- pri triage najit dulezite zpravy, deadliny, akcni kroky a newslettery.

Pri tom nema mazat, presouvat, oznacovat jako prectene, odesilat, otevirat odkazy
ani stahovat prilohy.

### 2. Precist konkretni e-mail po potvrzeni

Po konkretnim UID a potvrzeni umi Samantha precist telo e-mailu read-only a
vytvorit:

- bezpecne shrnuti,
- action case,
- navrh ukolu,
- metadata odkazu,
- metadata priloh,
- navrh odpovedi v zakladnim pracovnim pripadu.

### 3. Ulozit pripominku

Samantha umi z navrhu ukolu ulozit lokalni pripominku do:

```text
data/reminders/reminders.json
```

Pripominky umi:

- vypsat,
- zobrazit detail,
- pripominat pri startu, pokud se blizi deadline do 14 dni,
- oznacit jako hotove po potvrzeni.

### 4. Pripomenout e-mailovou udrzbu

Existuje lokalni soubor:

```text
data/email/activity_state.json
```

Ten sleduje:

- `last_triage_at`,
- `last_archive_at`.

Samantha ma pri startu pripomenout, pokud se dele nez 7 dni neprovedla triage
nebo archivace dulezitych e-mailu.

### 5. Ulozit bezpecny case

Samantha umi ulozit vybrane e-maily jako bezpecne pripady do:

```text
data/email/cases/
```

To je vhodne pro pracovni prehled a navazovani. Case ale neni kompletni zaloha:
neobsahuje cele telo e-mailu, plne URL ani kompletni prilohy.

### 6. Archivovat kompletni dulezity e-mail

Samantha umi po vyslovnem potvrzeni archivovat jeden dulezity e-mail do:

```text
data/email/archive/
```

Archiv uklada:

- `metadata.json`,
- `body.txt`,
- `body.html`, pokud existuje,
- `links.json` s plnymi URL,
- `attachments/attachments.json` s metadaty,
- `original.eml`.

Toto je lokalni citlivy archiv. Nesmí se commitovat do gitu a nema se ukladat do
memory.

### 7. Pracovat s lokalnim archivem

Byly pridany nastroje:

- `list_email_archives`,
- `show_email_archive_summary`,
- `show_email_archive_links`.

Seznam a souhrn archivu nemaji vypisovat cele telo ani plne URL. Plne odkazy z
archivu se maji zobrazit az po samostatnem potvrzeni.

## Co se pri posledni praci zjistilo

Pri realne archivaci jednoho bezpecnostniho e-mailu archiv vznikl spravne.
Vznikly soubory typu:

- `metadata.json`,
- `body.txt`,
- `body.html`,
- `links.json`,
- `original.eml`,
- `attachments/attachments.json`.

Soucasne se ukazalo dulezite UX/bezpecnostni pravidlo:

- samotna archivace nema rovnou vypisovat plne URL,
- plne URL patri az do samostatne potvrzeneho kroku nad archivem.

Podle posledniho stavu uz byly implementovany lokalni nastroje pro archiv:
seznam archivu, bezpecny souhrn a samostatne potvrzene zobrazeni odkazu.

## Co zatim neumi prakticky dost dobre

Projekt zatim neumi dostatecne lidsky workflow typu:

```text
Projdi e-maily za posledni tyden.
Vyber dulezite.
Tyto tri uloz kompletne.
Z tohoto jednoho udelej ukol.
Otevri odkaz.
Vypln formular.
Navrhni odpoved.
Po mem schvaleni ji odesli.
```

Technicky existuji jednotlive casti, ale nejsou jeste spojene do pohodlneho
pracovniho rezimu.

## Nejdulezitejsi chybejici smery

### 1. Lidsky workflow nad triage vysledkem

Cil:

- Samantha projde e-maily za poslednich 7 dni,
- zobrazi prehled dulezitych veci,
- Mila oznaci, co chce ulozit nebo resit,
- Samantha sama navrhne dalsi kroky pro kazdy dulezity e-mail.

Potrebny smer:

- lepsi textovy vystup triage,
- jednoduche volby typu `uloz 1, 2, 4 jako case`,
- `archivuj 1 a 2 kompletne`,
- `pracuj s polozkou 3`.

### 2. WorkMode nad ulozenym case nebo archivem

Cil:

- otevrit ulozeny pripad,
- ukazat co se resi,
- navrhnout dalsi akci,
- podle potreby ukazat odkazy,
- navrhnout odpoved,
- vytvorit pripominku,
- dovest Milu ke splneni ukolu.

### 3. Prilohy

Zatim jsou prilohy hlavne metadata nebo soucast `original.eml`.

Chybi:

- samostatne potvrzene ulozeni konkretni prilohy jako souboru,
- bezpecny seznam priloh v archivu,
- cteni PDF/DOCX prilohy,
- vytazeni platebnich udaju, smluvnich bodu nebo instrukci.

### 4. Odkazy a webove akce

Zatim se odkazy umi vypsat po potvrzeni, ale neoteviraji se a nezpracovavaji.

Chybi:

- otevrit vybrany odkaz v browseru po potvrzeni,
- precist stranku,
- vysvetlit co web chce,
- vyplnit formular,
- zastavit se pred finalnim odeslanim,
- nikdy neodeslat formular bez potvrzeni.

### 5. Odpovedi a odesilani e-mailu

Zatim lze smerovat k navrhu odpovedi, ale neni hotovy pohodlny workflow:

- navrhnout odpoved,
- upravit ji s Milou,
- pripravit odeslani,
- pred odeslanim ukazat komu, predmet a telo,
- odeslat az po finalnim potvrzeni.

Odesilani musi zustat samostatna, vysoce potvrzovana vrstva.

## Bezpecnostni hranice pro navazani

Vzdy plati:

- neukladat cele e-maily do memory,
- neukladat plne URL do memory,
- neukladat hesla, tokeny, app-specific passwords ani API klice,
- archive/cases/reminders jsou lokalni data, ne git obsah,
- neotevirat odkazy bez potvrzeni,
- nestahovat/spoustet prilohy bez potvrzeni,
- neodesilat e-maily bez finalniho potvrzeni,
- nemazat, nepresouvat ani neoznacovat jako prectene bez noveho navrhu a potvrzeni.

## Jak lidsky navazat, az se projekt rozmrazi

Prvni otazka pro Samanthu/Codex:

```text
Precti email_project_frozen_human_handoff_2026_05_19.md.
Chci rozmrazit e-mailovy projekt a pokracovat smerem k lidskemu workflow.
Nejdriv mi rekni, co uz umime a jaky je nejmensi dalsi prakticky krok.
```

Nejmensi rozumny dalsi krok:

```text
Navrhni a implementuj WorkMode nad ulozenym archivem/case:
- vybrat ulozeny archiv nebo case,
- ukazat lidsky souhrn,
- vypsat mozne akce,
- navrhnout dalsi krok,
- plne URL jen po potvrzeni,
- nic neotevirat a nic neposilat.
```

Druhy navazujici krok:

```text
Navrhni browser workflow pro jeden potvrzeny odkaz:
- otevrit odkaz,
- precist web,
- navrhnout postup,
- pripadne vyplnit formular,
- zastavit pred finalnim odeslanim.
```

## Stav pri pozastaveni

Projekt je pouzitelny jako bezpecny read-only zaklad a lokalni archiv dulezitych
e-mailu. Neni jeste pohodlny jako skutecny osobni e-mailovy asistent.

Melo by se k nemu vratit pozdeji s prioritou 1, ale nyni ho lze bezpecne
pozastavit a pokracovat na jinych projektech.
