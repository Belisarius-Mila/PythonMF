# REC-06 — jediný schválený číselný pilot dokončen; oddělený redakční návrh

2026-11-08, Data, pouze `data/parallel-20261104`. Mílovo „Schvaluji…“
navazuje na konkrétní kartu 741e71da…492f570, 20+1 Sol/medium/Standard,
plán 237,88715 / přijímací mez 240 kreditů. Jedno zavolání registrovaného
run, žádný další modelový pokus, nový job nebo opakování.

## Výsledek placeného jobu

**21/21 completed/delivered, 20/20 čtecích dávek přijato.** Nový číselný
wire prošel v celém skutečném korpusu i při syntéze. Nezávislý JSON Schema
validator ověřil všech 21 skutečných odpovědí. Celý original byl v každé
fázi, všech 532 dokumentů ve schváleném rozsahu právě jednou; 116 findings,
764 referencí v inspect, 730 podkladových řádků ve vstupu syntézy.

| Kontrola posledního tahu | Výsledek |
| --- | --- |
| Doručení / usage / tools / input | prošly |
| Input | 95 485 actual / 235 090 mez; reference request 90 971 |
| Output | **34 115 / 32 000 mez, nepřijato**; překročení 2 115 tokenů (6,61 %) |
| Čas | 686,537 s / 900 s, prošel |
| Celý běh | 1 566,841 s; 12:18:44–12:44:50 CET |
| Odhad ze všech skutečných usage | **174,8297 Standard kreditu / mez 240** |

Usage dohromady: input 3 207 934, cached input 0, output 57 732,
reasoning subset 5 290, total 3 265 666. Reasoning se k output nepřičítá
podruhé. Inspect 161,5267 + synthesis 13,303 = 174,8297 kreditu.
Je to odhad podle sazeb připnuté karty a usage, nikoli výpis účtu.

Formální výsledek je **attention / accepted=false**, důvod
`exact_pilot_receipt_acceptance_failed`. Výstupní mez se zpětně nezvyšuje.
Původní attempt, packet, run-result a 21 raw účtenek jsou zachované;
24 originálních finančních artefaktů má vlastní soukromý SHA manifest.
Kandidát přijatý původním jobem nevznikl. Provozní TXT/iCloud, role,
scheduler, služby, push, deploy ani main Data tímto krokem neměnil.

## Neplacené ověření skutečného obsahu

Syntéza má 48 částí: 19 unchanged, 28 documented a jednu unverified.
Všech **216 citací** odkazuje přesně na předanou povolenou evidenci;
všech 19 původních částí je doslovných. Poslední unverified odstavec však
nemá citaci, proto jej původní resolver odmítá (`invalid_evidence_count`).
Tvar poslaného schématu dovoluje prázdnou evidence, zatímco resolver ji
pro změněný odstavec vyžaduje. Nejde o další nevydané numeric ID.

Samostatná diagnostika po odstavcích dále ukázala:

- Slovní zkratky s lomítkem se místy vyhodnocují jako absolutní cesty
  (např. názvy zařízení či audio formátů).
- Dvě nové absolutní snapshot cesty model odvodil ze známého ID a kořene,
  ale celé nejsou doslovně v jeho citacích; takové nové instrukce se nepřijímají.
- Tři části mají pouze historické/mixed zdroje a potřebují unverified stav.
- Negativní sdělení o chybějícím auditu a nezaškrtnutý budoucí přejímací bod
  může konzervativní regex omylem číst jako provedené živé ověření.
- Některé relativní cesty odkazují na skutečné názvy zdrojů, ale nejsou
  doslovně v citovaném řádku. Pravidlo přesné evidence se nezměkčuje.

## Oddělený pracovní návrh bez dalšího modelu

Data vytvořil **samostatný redakční derivát**, nikoli opravenou raw odpověď
nebo dodatečně přijatý placený job. Obsahuje 47 částí / **93 361 B**.
SHA-256: `72aaa17bba9985ef54471bc1bc593714b28d5fdcd4d3980e71ee24abba9b658f`.

25 auditovaných redakčních operací: 21 textových úprav, tři přísnější
provenienční stavy a přesun necitovaného závěrečného disclaimeru mimo návrh
(do zachované raw a této dokumentace). Obyčejná lomítka jsou přepsaná slovy;
adresář a datový soubor vycházejí z již citované evidence. Dvě nedoložené
absolutní cesty a jejich nová přiřazení jsou odstraněné: návrh místo nich
vyžaduje přečíst přesnou cestu z dokončeného manifestu a připojeného úložiště.
Nevznikl nový příkazový allowlist, zdroj, citace ani dodatečný live fakt.

Všech 216 citací se zachovalo beze změny. 19 původních bloků je doslovných
a pokrývá všechny ne-whitespace znaky originálu v původním pořadí.
**Redakční derivát prošel nezměněným původním quality gate**; kontrola
uložených bajtů a opakovaná validace potvrdily tentýž SHA.
To není úplná sémantická přejímka, fyzický test nového Macu/iPhonu ani
povolení publikovat. Soukromý `editorial-candidate.txt`, jeho resolved answer,
rozpis editací a původní raw zůstávají pouze ve vlastní .venv; plný text
návodu ani citované soukromé podklady nejsou v Gitu.

## Souběžná změna main

Schválený modelový snapshot zůstává **6c610287**. Po zahájení posledního
modelového tahu vznikl na main commit **9c8584ee**, 12:34:42 CET. Při závěrečném
čtecím auditu je proto `_current` false, i když original i všechny připnuté
implementace zůstaly shodné. Kdyby výstupní mez prošla, původní běh by před
přijetím ověřoval také tuto změnu zdrojového headu.

Změnu Data přečetl pouze přes Git: jde o opravu odeslání úkolu v HTTP,
identity z getRandomValues a zachování editoru při selhání localStorage.
Nový report výslovně uvádí stejné backendy, kalendářové cíle, OS granty,
role a síť; žádná nová instalace služby či aplikace. Devět změněných dokumentů
je v result JSON. Nejsou dodatečně zahrnuté do původního placeného snapshotu
ani automaticky prohlášené za nový odsouhlasený manifest. Před publikací
přejímka musí rozlišit datovaný návrh a tento zvlášť přezkoumaný rozdíl.

## Ověření, doporučení a přesné předání

Kód se při běhu ani redakční revizi neměnil. Používá se ověření commitu
bef32ad2: 46 nových / plná brána 2 794 testů, 5 skipped. Neopakované nezměněné
unit testy nenahrazují skutečné účtenky: ty jsou nyní ověřené nezávislým
JSON Schema oraclem, resolverem a původním quality gate pro oddělený derivát.
Pět starých stavů/plánů, všech jejich 24 JSON i raw 6177159d…505b55a je shodných.

Doporučení: ponechat produkční transport. Přesný numeric protokol je živě
ověřený, ale automatická týdenní adopce zatím není přijatá. Příští neplacená
úprava kontraktu má sjednotit povinnou evidence podle statusu a používat
serverové zachování původního textu s vloženými doplňky, místo modelového
opakování celého návodu. Tato aktuální obsahová přejímka nepotřebuje nový
placený run ani další celé čtení modelem.

Bezprostřední krok: Míla a Will převezmou konkrétní redakční návrh výše,
rozpis 25 operací a zdrojový rozdíl vůči main. Projdou obsah doplňků,
zejména volbu záloh a kompatibilitu Camina; rozhodnutí o přijetí návrhu je
oddělené od trvale nepřijaté účtenky. Následné kopírování stejných schválených
bajtů do PythonMF a iCloud Dokumentů a týdenní aktivace vyžadují příslušné
samostatné oprávnění a dosavadní registrovaný postup. Nyní se neprovádějí.

Git-safe důkazy: tento report, `recovery_guide_anchor_exact_run_result_20261108.json`
a `recovery_guide_anchor_exact_editorial_review_20261108.json`.
Závěrečná statická brána a git diff --check OK.

## Změněné soubory (10)

- `recovery_guide_anchor_exact_run_20261108.md`,
  `recovery_guide_anchor_exact_run_result_20261108.json`,
  `recovery_guide_anchor_exact_editorial_review_20261108.json`.
- `ACTIVE_PROJECTS.md`, `MEMORY_INDEX.md`, `LESSONS_LEARNED.md`,
  `samantha_external_backup.md`, `recovery_guide_maintainer.md`,
  `handoffs/workstreams/project-samantha-infrastructure.md`,
  `tvbcp/workstreams/project-samantha-infrastructure.md`.

Změny jsou pouze Git-safe výsledkové dokumenty a projektová paměť; kód,
závislosti, role i produkční runtime beze změny. Plné soukromé výstupy se
necommitují. Jediný lokální commit na vlastní větvi, bez push/deploy.
