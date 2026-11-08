# REC-06 — skutečný malý anchor test: obsah a cena prošly, čas nikoli

2026-11-07, Data, pouze vlastní `data/parallel-20261104`.

Míla výslovně přijal kartu `566899e7…ddd8cb3`: nejvýše dva tahy
gpt-6.1-sol / medium / Standard, celý původní návod a dva dokumenty,
plán 14,72415 a přijímací mez 15 Standard kreditů (nikoli tvrdý billing cap).
Před run byla ověřena shoda karty, aktuální zdroje/kód a protokol; původně
neexistoval nový attempt. Registrované `recovery_guide_anchor_trial.run`
bylo zavoláno **jednou**. Žádný retry, reset, refresh ani třetí tah.

## Výsledek

**Řadič vrátil attention / accepted=false.** Obě odpovědi jsou jednoznačně
completed/delivered. První inspect byl přijat a teprve potom odeslána syntéza.
Syntéza překročila schválenou časovou mez 300 000 ms; další akce se neodesílá.
Původní limit ani stav uzavřeného jobu nebyly dodatečně přepsané.

| Fáze | Input | Output | Délka | Odhad Standard kreditů |
| --- | ---: | ---: | ---: | ---: |
| inspect | 37 212 | 262 | 9,008 s | 1,9261 |
| synthesize | 32 390 | 19 837 | 400,240 s | 6,57875 |
| Celkem | 69 602 | 20 099 | 409,248 s obou tahů | **8,50485** |

Cached input 0, reasoning output 132 je podmnožinou outputu, total 89 701
tokenů. Oba input/output limity i celková cenová mez 15 prošly. Celý job
trval přibližně 6 min 54 s včetně lokální režie. Cena je výpočet ze skutečné
spotřeby podle schválených Standard sazeb, nikoli fakturační účtenka.

## Co bylo skutečně ověřeno

- Nový modelový source/anchor kontrakt proběhl v obou fázích na existujícím
  serveru 0.163.0 přes sdílený Unix socket. Dvě samostatná ephemeral vlákna,
  jeden turn na každém, jedna klientská connection; produkční klient beze změny.
- Inspect vrátil právě oba požadované řádky pro restart/mikrofon a
  odeslané byty/serverové verified. Přesné citace doplnil program z katalogu;
  žádná normalizace původních nepřesných modelových quote.
- Po dokončení byla **bez dalšího modelového volání** samostatně znovu
  vyhodnocena již doručená syntéza přes stejný `_synthesis` a původní quality
  gate. Prošla. Obsahuje tři odstavce: celý original a dva unverified dodatky
  s přesnými povolenými evidencemi. Původní text je doslovně shodný i včetně
  vnějšího whitespace; neproběhla oprava či přepis raw odpovědi.
- Nežádoucí typy nástrojových událostí nebyly pozorovány ani v jednom tahu.
  Není to obecný důkaz absolutní izolace veškerého čtení nebo budoucích běhů.
- Oba tahy používaly v guardu `serviceTierForTurn=default`, medium, never
  approvals, read-only/network false a přesné schema/payload. Centrální role,
  serverová konfigurace, globální CLI a závislosti se neměnily.

**Obsahová revalidace není zpětné přijetí celého testu.** Stav jobu zůstává
attention; jeho příštější zavolání nesmí vytvořit nový modelový pokus.

## Důkazy a izolace

- `recovery_guide_anchor_trial_result_20261107.json`: bezpečné číselné
  metriky, konkrétní nesplněný gate, SHA requestů/raw účtenek/kandidáta,
  unikátní thread/turn ID a výsledek offline revalidace. Žádný text návodu.
- Schválený snapshot `7e0e6b6f…90fb738`, katalog `6b105182…cabb79a`,
  zdrojový main `0850e6f3`, 75 100 bytů (original + dva celé dokumenty).
- Raw 01 SHA `6f8b5922…4b6ae8`, raw 02 `bea9fa82…bffc4`; jedinečné turny
  `01a1b816-be53-7263-bf1a-c1dea63617ae` a
  `01a1b816-e9d2-7d43-bd00-2fe9f6d492e9`. Raw zůstávají jen v soukromé .venv.
- Starý úplný v2 job, jeho dva raw turn soubory a oba attempt markery mají
  stejné hashe jako před přípravou nového pilotu. Starých 21,013 a nových
  8,50485 se nesčítá jako cena jedné úlohy.
- Žádný publikovaný kandidát/TXT, zápis iCloud, změna role či týdenní služby,
  spuštění/restart živé služby, push, nasazení nebo integrace do main.
- Kód se od schválené otestované karty neměnil: předchozí 50 cílených a plná
  brána 2 668 OK / 5 skipped. Tyto jednotkové testy se zbytečně neopakovaly.
  Finální statická brána a git diff --check také OK.

## Doporučený další krok

Nový citační protokol má skutečný pozitivní důkaz na tomto malém rozsahu;
nepřijetí neznamená chybu citací, rozpočtu ani nejisté doručení. Není důvod
opakovat oba placené tahy jen kvůli známému časovému překročení. Výsledek
patří zachovat jako známou dokončenou účtenku s přesně oddělenými kritérii.

Nejmenší další vývoj je **neplaceně připravit úplný anchor pilot a jeho novou
cenovou kartu**, se samostatným časovým plánem inspect/synthesis opřeným o
naměřených 400,240 s. Jde o budoucí plán, ne dodatečné zvýšení starého limitu.
Nový celý manifest, dělení dávek, vstupní/synthesis rezervy a cena se musí
znovu přepočítat; žádný další model automaticky. Celý korpus, obsahová
přejímka Macu/iPhonu, dvě cílové kopie/upload a týdenní aktivace zůstávají otevřené.

Případná optimalizace délky výstupu je samostatná možnost: z 63 144 bytů textů
odstavců bylo 62 778 bytů (99,4 %) nezměněným originalem a jen 366 novými
dodatky. To podporuje zvážení programového skládání nezměněných částí, ale
takový kontrakt nyní nebyl implementován ani modelově ověřen. Měřená data
sama neprokazují, že celou latenci způsobila právě délka kopírovaného textu.

## Změněné soubory tohoto kroku

- memory/ACTIVE_PROJECTS.md
- memory/LESSONS_LEARNED.md
- memory/MEMORY_INDEX.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/projects/samantha_external_backup.md
- memory/technical/recovery_guide_maintainer.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- memory/reports/recovery_guide_anchor_trial_result_20261107.json
- memory/reports/recovery_guide_anchor_trial_run_20261107.md
