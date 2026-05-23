# Samantha growth rules

Priorita: A1+
Pripomenout pri startu: ano
Datum: 2026-05-23

## Ucel

Preventivni pravidla pro rust projektu Samantha Agent. Cilem je, aby projekt mohl
vyrust klidne na nasobky dnesni velikosti, ale nezacal se zpomalovat kvuli
chaosu v pameti, commitech, soukromych datech nebo duplicitnich workflow.

Tato pravidla nabidnout hned po velkem commitovem uklidu, ktery je veden jako
A1+ ukol `Commitove odpoledne / git cleanup`.

## Maximalni priorita po commitovem uklidu

Po velkem commitovem uklidu maji byt hned nabidnuty tyto tri veci:

1. Cisty stul.
   Dokoncit tematicke commity, oddelit rozpracovane oblasti, vyresit co patri do
   gitu a co zustava soukrome nebo odlozene.

2. Pouzit uklid jako lekci.
   Vyhodnotit, kde nam vznikl chaos: prilis mnoho handoffu, promichane zmeny,
   duplicitni workflow, nejasne statusy nebo necommitnute soubory.

3. Nastavit jasnejsi rezim dalsiho vyvoje.
   Domluvit, jak budeme udrzovat poradek, cistotu, efektivitu a navazatelnost:
   tematicke commity, projektove compact/status soubory, testy a handoff
   kompresi po projektech.

## Deset pravidel rustu

1. Jedna oblast, jeden commit.
   Nesmichavat dokumenty, e-mail, video, infrastrukturu a memory do jednoho
   commitu, pokud to neni jedna uzavrena logicka zmena.

2. Kazdy vetsi projekt ma status soubor.
   Handoff je snapshot. Kanonicky projektovy status rika, co je aktualne hotove,
   co je riziko a jaky je dalsi krok.

3. Private data nikdy jako vedlejsi efekt.
   Soukroma data patri do `data/private/` nebo jine explicitne ignorovane
   oblasti. Skripty maji jasne oddelit git-safe vystupy od soukromych vystupu.

4. Workflow misto rucnich prikazu.
   Jakmile se stejna cinnost dela podruhe, ma vzniknout skript, tool, workflow
   karta nebo testovatelna funkce. Chat nema byt misto pro trvale shell postupy.

5. Kazdy novy tool ma test.
   Minimalne test nad fake daty. U soukromych dat, e-mailu, dokumentu, tisku a
   mazani je test povinny.

6. Pamet nesmi rust jako skladka.
   `MEMORY_INDEX.md` ma ukazovat na aktualni kanonicke zdroje. Stare handoffy
   mohou zustat kvuli auditu, ale nesmi prebijet aktualni stav.

7. Nejdrive najdi existujici schopnost.
   Pred implementaci noveho toolu hledat podobny pattern v `app/`, `scripts/`,
   `memory/technical/` a testech.

8. Pravidelny commitovy uklid.
   Jakmile `git status` zacina byt delsi nez par obrazovek, navrhnout tematicky
   commitovy uklid. Toto je samostatny A1+ ukol do odvolani.

9. Zadny velky refaktor bez checkpointu.
   Pred presuny souboru, prejmenovanim, hromadnymi upravami nebo architektonickou
   zmenou musi byt cisty nebo jasne pochopeny git stav.

10. Vystupni kontrakty.
    U dulezitych workflow musi byt jasne: vstup, potvrzovaci veta, co se cte,
    co se zapisuje, kam se to ulozi, co se smi smazat a co se nesmi commitovat.

## Pravidlo pro bobtnani handoffu

Stare handoffy nejsou automaticky k nicemu: mohou byt auditni stopa. Nesmime je
ale nechat ridit aktualni praci, pokud uz existuje novejsi status nebo handoff.

Plosne cisteni handoffu je mozne, ale pouze ve ctyrech krocich:

1. Audit bez zapisu:
   vypsat vsechny handoffy, datum, oblast, zda jsou v `MEMORY_INDEX.md`, zda maji
   `[PRIPOMENOUT]`, a zda jsou pravdepodobne prekryte novejsim souborem.

2. Navrh konsolidace:
   pro kazdou oblast urcit jeden aktualni kanonicky status nebo handoff. Stare
   handoffy oznacit jako `ponechat`, `archivovat`, `vyjmout z indexu`, nebo
   `navrhnout ke smazani`.

3. Potvrzeni Milou:
   pred fyzickym mazanim ukazat presny seznam souboru. Bez vyslovneho potvrzeni
   se nic nemaze.

4. Bezpecne provedeni:
   preferovat nejdrive archivaci nebo odstraneni z `MEMORY_INDEX.md`. Fyzicke
   smazani az po potvrzeni a idealne po git checkpointu.

## Navrhovany dalsi krok po velkem commitu

Po commitovem odpoledni nabidnout:

```text
Mame hotovy velky commitovy uklid. Chces ted probrat A1+ rustova pravidla
Samanthy a hlavne audit/uklid bobtnajicich handoffu?
```

Bezpecnost:

- Nemazat handoffy bez potvrzeni.
- Neuvadet do memory citliva data, cele e-maily, tokeny, hesla ani plne soukrome
  URL.
- Pri uklidu pameti rozlisit aktualni projektovy stav od historicke auditni
  stopy.

## Handoff compression per project

Cilene prochazeni a zkracovani handoffu se ma delat po jednotlivych projektech,
ne globalne naslepo.

Postup:

1. Vybrat projekt.
   Napriklad `Dokumenty`, `E-mail`, `Tomik video`, `Lekarna`.

2. Najit vsechny souvisejici handoffy.
   Podle nazvu souboru, `MEMORY_INDEX.md`, obsahu a odkazu z
   `ACTIVE_PROJECTS.md`.

3. Rozdelit je na:
   - aktualni,
   - starsi platne,
   - prekryte novejsim stavem,
   - testovaci nebo duplicitni,
   - archivni auditni stopu.

4. Vytvorit nebo aktualizovat kompaktni projektovy status.
   Ten ma obsahovat jen podstatne body pro navazani pri vyvoji zpet:
   rozhodnuti, hotova workflow, dulezite soubory, bezpecnostni pravidla, otevrene
   otazky a historicke milniky jen bodove.

5. Stare handoffy nejdrive vyjmout z bezne navigace.
   Preferovat odstraneni z `MEMORY_INDEX.md` nebo presun do archivu. Fyzicke
   mazani az po potvrzeni presneho seznamu.

Prvni doporuceny pilot:

- `Sprava dokumentu / private vault`, protoze ma jasne workflow a soucasne uz
  vzniklo vice handoffu.
- Druhy kandidat je `E-mail`, kde je nejvetsi historicke vrstveni.
