# Samantha Agent - projektove instrukce

Tyto instrukce plati pro praci ve slozce `Samantha_Agent/`.

## Identita a komunikace

- Odpovidej cesky.
- Uživatel je Míla.
- Vysvetluj prakticky, vecne a krok za krokem.
- Kdyz navrhujes reseni, popis konkretni dalsi krok, ne jen obecnou teorii.

## Prace s pameti

- Pred praci si vzdy precti `Samantha_Agent/memory/MEMORY_INDEX.md`.
- Relevantni kontext hledej ve slozce `Samantha_Agent/memory/`.
- Pokud v pameti chybi dulezity kontext, upozorni na to a pokracuj s rozumnym predpokladem.
- Pri startu nove SSH/Codex relace zkontroluj pravidla v `memory/technical/session_recovery_rules.md`.
- Pokud `MEMORY_INDEX.md` obsahuje polozky oznacene `[PRIPOMENOUT]`, upozorni na ne pri navazovani prace nebo kdyz se Mila pta, na cem pokracovat.
- Pri startu nove relace vzdy zkontroluj stav zalohy pres
  `.venv/bin/python scripts/backup_status.py`. Pokud je posledni uspesna zaloha
  starsi nez 3 dny nebo chybi, upozorni na to v prvni odpovedi kazdy den, dokud
  neprobehnou nova uspesna zaloha. Pripominka sama nic nekopiruje, nemaze ani
  necte tajemstvi.
- Autosave nouzove obnovy ma bezet pri startu pres `samantha`: kazdych 10 minut uklada TXT/JSONL do `data/session_autosave/`.
- Soubory v `data/session_autosave/` jsou jen nouzova obnova, nikdy je necommituj.

## Rychle prikazy pro handoff

Kdyz Mila napise kratkou vetu jako:

- `uloz handoff`
- `uloz rozpracovano`
- `prerus praci`
- `uloz to jako prioritu 1`
- `uloz handoff a pripomen mi to`

znamena to: vytvorit bezpecny rucni handoff z aktualniho kontextu a aktualizovat
registr aktivnich projektu.

Postup:

1. Nejdrive z aktualni konverzace a dostupnych souboru navrhni kratky handoff.
2. Pokud neni jasne tema, priorita, stav nebo dalsi krok, zeptej se na chybejici
   udaje maximalne 3 kratkymi otazkami.
3. Pokud je z vety jasna priorita, pouzij ji. Jinak se zeptej na prioritu `1`, `2`
   nebo `3`.
4. Pokud Mila rika, ze se k tomu chce brzy vratit, nastav `Pripomenout pri startu: ano`.
5. Vytvor soubor v `Samantha_Agent/memory/handoffs/` s nazvem podle tematu a data,
   napr. `email_prace_rozdelano_2026_05_18.md`.
6. Aktualizuj `Samantha_Agent/memory/ACTIVE_PROJECTS.md`: oblast, priorita, stav,
   memory soubor, handoff a dalsi krok.
7. Aktualizuj `Samantha_Agent/memory/MEMORY_INDEX.md`, pokud ma byt handoff dohledatelny
   primo z indexu nebo pripomenuty pri startu.
8. Do handoffu nikdy neukladej hesla, tokeny, app-specific passwords, API klice,
   rodna cisla, cele e-maily ani jina citliva data bez vyslovneho souhlasu.

Minimalni struktura handoffu:

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

`Navrhovane dalsi kroky` pouzivej hlavne u hotovych nebo pozastavenych projektu:
kratce oddel okamzity dalsi krok od volitelnych navazujicich zlepseni, aby Mila
pri dalsim navazani videl, kam se da rozumne pokracovat.

## Bezpecnost a soubory

- Nikdy nemaz soubory bez vyslovneho souhlasu Mily.
- Neupravuj soubory mimo rozsah aktualniho ukolu, pokud to neni nutne.
- API klice, tokeny a jina tajemstvi nikdy neukladej do gitu.
- Skutecny `OPENAI_API_KEY` patri pouze do lokalniho `.env`, ne do `.env.example`, dokumentace ani commitu.

## Technicke preference

- Preferuj Python jako hlavni implementacni jazyk.
- Agents SDK bude zaklad budoucicho Samantha agenta.
- Strukturu projektu drz jednoduse a citelne:
  - `app/` pro aplikacni kod,
  - `scripts/` pro pomocne skripty,
  - `data/` pro lokalni data,
  - `memory/` pro dlouhodoby kontext agenta.
- Automatizace v projektech se nema resit ad hoc shell prikazy v chatu.
  Pouzij pravidlo z `memory/technical/capability_routing_rules.md`: lidsky
  pokyn -> pochopeny zamer -> registrovana schopnost/tool/workflow ->
  bezpecnostni rozsah -> potvrzeni podle rizika.
- Shellove postupy patri do workflow registry, Pythonove operace do bezpecnych
  toolu s testy a potvrzovacimi branami podle citlivosti.

## Styl prace

- Nejdriv si ujasni cil ukolu a dostupny kontext.
- Potom navrhni nebo proved nejmensi uzitecny krok.
- Pri zmenach souboru popis, co menis a proc.
- Po dokonceni shrn vysledek a pripadne dalsi prakticky krok.
