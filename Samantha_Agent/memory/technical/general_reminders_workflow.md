# General reminders workflow

Zalozeno: 2026-05-21

## Smysl

Mila potrebuje jednoduse ukladat dulezite veci z SMS, e-mailu, telefonu,
papiru nebo bezne konverzace tak, aby se neztratily a aby je Samantha pri startu
ukazala ve spravnem kontextu.

## Kam co patri

### 1. Konkretni ukol s datem nebo terminem

Pouzit lokalni reminders store:

```text
data/reminders/reminders.json
```

To je spravne misto pro veci typu:

- zavolat,
- objednat,
- zaplatit,
- zkontrolovat,
- poslat dokument,
- odpovedet,
- vyridit do konkretniho data.

Tyto pripominky se pri startu Samanthy ukazuji v sekci `AKTIVNI PRIPOMINKY`,
pokud jsou prosle, dnesni nebo do 14 dnu.

Minimalni pole:

```json
{
  "id": "sms-kratky-popis-YYYY-MM-DD",
  "title": "Kratky lidsky nazev ukolu",
  "notes": "Bezpecne shrnuti, co udelat. Neopisovat cele SMS, pokud obsahuje citlive udaje.",
  "due_date": "YYYY-MM-DD",
  "priority": "high|medium|low",
  "status": "open",
  "source": {
    "type": "sms",
    "uid": "manual",
    "date": "YYYY-MM-DD",
    "sender": "[redigovano nebo kratky popis]"
  }
}
```

Bezpecnost:

- neukladat cele SMS, pokud obsahuji citlive udaje,
- neukladat plne URL,
- neukladat rodna cisla, hesla, tokeny, cele adresy nebo zdravotni detaily,
- staci bezpecny akcni vytah a pripadne redigovany zdroj.

### 2. Dulezita vec bez terminu

Pokud neni deadline, nepatri automaticky do reminders JSON. Nejdriv se zeptat:

- ma se to pripominat pri kazdem startu,
- nebo je to jen kontext k projektu,
- nebo se ma z toho udelat konkretni ukol s datem.

Moznosti:

- projektovy kontext: `memory/projects/...`
- technicke nebo procesni pravidlo: `memory/technical/...`
- kratky aktualni stav/navazani: `memory/handoffs/...`
- obecny aktivni smer: `memory/ACTIVE_PROJECTS.md`

### 3. Projektovy handoff

Pouzit `memory/handoffs/`, kdyz jde o rozpracovanou oblast, kde je potreba
navazovat:

- co se resilo,
- co je hotove,
- co neni hotove,
- dalsi krok,
- priorita,
- zda pripomenout pri startu.

### 4. Opakujici se automaticka rutina

Pouzit projekt `Automaticke opakujici se ukoly`, pokud se ma neco spoustet
opakovaně, napriklad denne/tydne:

- fronta v JSON/CSV,
- allowlist cest,
- idempotentni skript,
- logy,
- testy,
- volitelne GitHub Actions nebo macOS launchd.

## Jak ma Samantha postupovat pri SMS pripomince

Kdyz Mila napise neco jako:

```text
uloz to z SMS jako pripominku
```

Samantha ma:

1. Rict, ze to chape jako ulozeni bezpecne lokalni pripominky.
2. Pokud chybi obsah, termin nebo priorita, zeptat se maximalne na 3 kratke veci:
   - co presne pripomenout,
   - do kdy nebo kdy zobrazit,
   - priorita high/medium/low.
3. Ulozit jen bezpecne shrnuti, ne cele SMS.
4. Pouzit `source.type = "sms"`.
5. Pokud ma byt videt pri startu hned, nastavit `due_date` na dnesek nebo datum
   do 14 dnu.
6. Pokud jde jen o projektovy kontext bez terminu, ulozit do memory/handoffu
   misto reminders JSON.

Pro platebni SMS, faktury, pojistky a smlouvy ma Samantha pouzit tool:

```text
save_payment_sms_reminder
```

Ten uklada jen bezpecna metadata do `data/reminders/reminders.json`. Vyžaduje
samostatne potvrzeni obsahujici id pripominky a souhlas s ulozenim. Tool neotvira
odkazy, nic neplati a neuklada plne URL/tokeny; z odkazu smi ulozit jen domenu.

Pokud je potreba nejdrive zjistit skutecnou splatnost z platebni stranky nebo
faktury podle HTTPS odkazu, pouzit samostatny read-only tool:

```text
inspect_payment_page_for_reminder
```

Ten vyzaduje samostatne potvrzeni s domenou odkazu a souhlasem s read-only
kontrolou platebni stranky/faktury. Tool smi jen nacist textovou/HTML stranku a
vypsat bezpecny vytah: domenu, cislo pojistky/smlouvy/faktury, castku, splatnost
a pocatek pojisteni/sluzby, pokud je najde. Nesmí platit, odesilat formular,
prihlasovat se, stahovat prilohy ani ukladat plne URL/tokeny.

Spravny dvoukrokovy postup:

1. `inspect_payment_page_for_reminder` overi splatnost z odkazu.
2. Pokud najde `verified_due_date`, az dalsim samostatne potvrzenym krokem pouzit
   `save_payment_sms_reminder` s `verified_due_date`.
3. Pokud splatnost nenajde, ulozit jen ukol overit splatnost.

Pokud k platebnimu pripadu existuje lokalni priloha nebo faktura, pouzit:

```text
save_payment_case_document
```

Ten kopiruje uz existujici lokalni soubor do soukromeho archivu:

```text
data/private/payment_cases/<case_id>/documents/
```

Pouziti vyzaduje samostatne potvrzeni obsahujici `case_id`, presny nazev souboru
a jasny souhlas s ulozenim faktury/prilohy/dokumentu. Tool smi kopirovat jen
lokalni soubor z projektove `data/` nebo `/private/tmp`; nesmi sam stahovat URL,
cist e-mail znovu ani otevirat prilohy. `data/private/` je mimo git.

## Pojistky, faktury a platby

U SMS/e-mailu typu "zaplatte hned" se nesmi automaticky brat datum SMS jako
splatnost. U plateb, pojistek, faktur a podobnych zavazku plati:

1. Rozhodujici je overena splatnost z faktury, platebni stranky, smlouvy nebo
   dokumentu pojistovny.
2. Pokud SMS jen rika "zaplatit pred pocatkem pojisteni", zjistit:
   - cislo smlouvy/pojistky,
   - castku,
   - skutecnou splatnost,
   - datum pocatku noveho pojisteni.
3. `due_date` v reminders JSON nastavit na skutecnou splatnost, ne na datum SMS.
4. Do `notes` napsat rozdil mezi marketingovou urgenci a overenym terminem.
5. Plne platebni URL s tokenem neukladat do memory ani reminders; ulozit maximalne
   domenu do `links`, napr. `app.rixo.cz`.
6. Pokud skutecna splatnost neni overena, nevytvaret "zaplatit dnes" jako hotovy
   fakt. Vytvorit radeji pripominku typu:
   "Overit splatnost platby / faktury" s blizkym terminem.
7. Pokud skutecna splatnost overena je, ulozit platebni pripominku s
   `verified_due_date`; pokud je znamy pocatek noveho pojisteni/sluzby, ulozit i
   `verified_start_date`.

Priklad:

```text
SMS: zaplatit pojistku hned.
Platebni stranka/faktura: splatnost 2026-07-31, pojistka plati od 2026-08-01.
Reminder due_date: 2026-07-31.
Notes: zaplatit pred splatnosti; SMS byla urgence, ne finalni splatnost.
```

U RIXO realne overeno 2026-05-21:

- platebni API muze mit obecne `dueDate` shodne s pocatkem pojisteni,
- pro ulozeni pripominky je dulezitejsi `terms.dueDatePaymentGateway`,
- pokud Mila chce platit bankovnim prevodem, muze byt rozhodujici drivejsi
  `terms.dueDateBankTransfer`.

## Aktualni doporuceni

Pro nove "dulezite veci" pouzivat primarne reminders JSON, pokud z nich plyne
konkretni akce. Memory ma zustat pro kontext a pravidla, ne pro dlouhy seznam
malých osobnich ukolu.
