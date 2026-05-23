# Large context intake

Priorita: 1
Pripomenout pri startu: ne
Datum: 2026-05-23

## Ucel

Bezpecny lokalni prostor pro velke podklady, ktere Mila nechce kopirovat do
chatu: dlouhe texty, exporty, archivy chatu, PDF, JSON/ZIP exporty nebo dalsi
materialy k prostudovani a pripadne k zapracovani do memory.

## Lokalni adresar

Mila muze vkladat velke podklady sem:

```text
Samantha_Agent/data/private/knowledge_inbox/incoming/
```

Pracovni mezivystupy patri sem:

```text
Samantha_Agent/data/private/knowledge_inbox/processed/
```

Kratke lokalni poznamky mimo git patri sem:

```text
Samantha_Agent/data/private/knowledge_inbox/notes/
```

Cela slozka `Samantha_Agent/data/private/` je ignorovana gitem. Do gitu patri
jen tento navod a pripadne bezpecne, redigovane shrnuti, pokud ho Mila vyslovne
schvali.

## Bezpecny inventar

Pred ctenim obsahu lze spustit read-only inventar:

```bash
.venv/bin/python scripts/samantha_knowledge_inbox.py
```

V Samanthě tomu odpovida tool:

```text
samantha_knowledge_inbox_inventory()
```

Inventar smi vypsat jen metadata: oblast, nazev souboru, typ, velikost a datum
zmeny. Nesmí cist ani vypisovat obsah souboru.

## Import ze Stazene/Downloads

Pokud Mila nechce rucne presouvat soubory, Samantha muze nejdriv vypsat
bezpecny inventar top-level souboru ve slozce Downloads:

```bash
.venv/bin/python scripts/samantha_downloads_to_knowledge_inbox.py --list
```

V Samanthě tomu odpovida tool:

```text
samantha_downloads_inventory()
```

Kopirovani je samostatny potvrzovany krok. Rucni CLI priklad:

```bash
.venv/bin/python scripts/samantha_downloads_to_knowledge_inbox.py --copy soubor.zip --confirm "Potvrzuji kopirovani do knowledge inbox"
```

V Samanthě tomu odpovida tool:

```text
copy_downloads_files_to_knowledge_inbox(relative_paths, user_confirmed=True, confirmation_text=...)
```

Pravidla:

- inventory ze Stazene/Downloads necte obsah, jen metadata top-level souboru;
- kopirovat se smi jen konkretne vybrane relativni soubory ze slozky Downloads;
- potvrzeni musi obsahovat vetu `Potvrzuji kopirovani do knowledge inbox`;
- kopirovani uklada jen do `data/private/knowledge_inbox/incoming/`;
- adresare a cesty mimo Downloads se odmitaji;
- pri shode nazvu se cil neprepisuje, vytvori se varianta s `_2`.

## Bezpecnostni pravidla

- Nikdy necommitovat puvodni velke podklady, exporty chatu, ZIPy ani soukrome
  soubory z `data/private/knowledge_inbox/`.
- Pred ctenim velkeho podkladu nejdriv vypsat jen bezpecny inventar: nazev
  souboru, typ, velikost, datum zmeny.
- Nezpracovavat cely archiv automaticky bez jasneho zadani rozsahu.
- Do memory zapisovat jen kratke redigovane operacni znalosti, ne cele chaty,
  osobni udaje, tokeny, hesla, API klice ani soukromy obsah.
- U dlouhych archivnich chatů preferovat davkove zpracovani: inventar -> vyber
  casti -> extrakce pouceni/projektovych faktu -> navrh memory diffu -> potvrzeni.

## Doporučený postup pro Codex/Samanthu

1. Mila vlozi soubor nebo archiv do `incoming/`.
2. Na pokyn typu "prostuduj knowledge inbox" nejdriv ukazat inventar a navrhnout
   rozsah zpracovani.
3. Pokud Mila potvrdi, vytvorit kratky pracovni souhrn do `processed/`.
4. Teprve po dalsim souhlasu zapracovat vybrane poznatky do `memory/`.
5. Po zapracovani udelat tematicky commit jen trackovanych memory/kod souboru,
   nikdy puvodnich privatnich podkladu.

## Archiv chatu se Samanthou/GPT

Pro budouci archiv nekolika let chatu platí zvlastni opatrnost:

- nejdriv ulozit surovy export jen do `incoming/`;
- nevkladat ho do promptu ani memory jako celek;
- zpracovavat po davkach a tematicky;
- vystupem maji byt strukturovane operacni znalosti, projekty, pravidla,
  rozhodnuti a handoffy, ne chat history.
