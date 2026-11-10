# MMTX — dokončení nové šesté scény, části 4–10

Míla zadal dokončit všechny zbývající části nové scény 6 podle schváleného
scénáře. Hotový místní celek má 10 příběhových částí, 11 schválených ilustrací
(včetně 03/031) a 67 pevných anglických MP3. Scéna končí Benjiho plánem a
poděkováním zvířat; sedmá scéna se nyní nevytváří ani neodhaduje.

## Příběh a přehrávač

| Část | Obsah | Nové EN MP3 | SSML znaky |
| --- | --- | ---: | ---: |
| 4 | The Old Hut | 7 | 401 |
| 5 | Dinner by the Fire | 7 | 462 |
| 6 | The Meeting Begins | 8 | 489 |
| 7 | Logan’s Idea | 8 | 560 |
| 8 | Everyone Wants to Help | 6 | 311 |
| 9 | Silence | 0 | 0 |
| 10 | Benji’s Plan | 6 | 347 |

- Části 4–10 navazují na první tři. Dialogy odpovídají přesnému schválenému
  anglickému scénáři, včetně jmen mluvčích, interpunkce a pořadí.
- Tichá část 9 má nulový počet replik a explicitní `silent: true`. Zobrazí
  schválenou ilustraci bez řečové bubliny a bez vytvoření Audio. Repeat je
  vypnuté, Next picture ručně pokračuje k Benjimu. Žádný vypravěč, syntetické
  „ticho“, prázdná MP3, automatický časovač ani placený požadavek.
- Části 4–10 umisťují dialog a spodní ovládání do běžného toku pod obrázek.
  Dlouhé repliky se mohou zalomit a nezakrývají tváře, postavy ani mapu.
  Dosavadní rozložení částí 1–3 zůstává zachované.
- Rozdělení 03 → 031 před Bunnyho otázkou 4/8 zůstává. Opakování, chyba MP3,
  ochrana před pozdními callbacky a návrat přes historii mají stejné zásady.
- Again se objeví až po poslední replice části 10 a vrací začátek šestky.
  Vazba z dokončené scény 5 a návrat k mostu zůstávají zachované.

## Hlasy a jednorázová výroba

42 nových unikátních Azure požadavků, 2570 SSML znaků z předem zmrazeného
celkového limitu 4000, tempo −10 %, 784368 B nových MP3. Před prvním požadavkem
byly ověřené všechny vstupy, dílčí rozpočty a nepřítomnost předchozích účtenek.
Každá část má vlastní trvalou účtenku; neznámý výsledek se neopakuje a zastaví
zbytek dávky. Celá dávka skončila complete. Žádný požadavek se neopakoval.

Logan zachovává Christophera podle původní hlasové mapy. Stávající postavy
zachovávají dosavadní hlasy. Nové vazby v rámci již povolené sady hlasů:
Old Stag → Guy, Woodpecker → Andrew, Animals → Andrew. Skupinové repliky jsou
jedna srozumitelná stopa, bez dalších generovaných nebo vrstvených hlasů.

Všech 35 původních podkladů (25 MP3, čtyři obrázky, tři dialogy a tři manifesty)
a všechny tři původní raw účtenky zůstaly SHA-256 shodné. Starší řeč se znovu
negenerovala. Veřejná data a mirror mají stejné bajty. Soukromé raw účtenky,
zmrazený rozpočet a konfigurace poskytovatele nejsou v commitu.

## Schválené ilustrace

Zdrojové PNG z Downloads byly exportované beze změny rozměrů do WebP q90,
method 6. Závěrečný zdroj je výslovně opravený `10_Benjiho_plan_potok_do_jezera`;
potok na mapě je připojený do jezera. Žádná další obrazová generace se nevolala.

| Část | WebP | Rozměry | B |
| --- | --- | --- | ---: |
| 4 | `old_hut.webp` | 1672 × 941 | 588338 |
| 5 | `dinner_fire.webp` | 1672 × 941 | 528130 |
| 6 | `meeting_begins.webp` | 1672 × 941 | 663540 |
| 7 | `logan_idea.webp` | 1672 × 941 | 600612 |
| 8 | `everyone_helps.webp` | 1671 × 941 | 616574 |
| 9 | `silence.webp` | 1670 × 941 | 601852 |
| 10 | `benji_plan.webp` | 1670 × 942 | 556394 |

Zdrojové a výsledné SHA-256 pro příští integraci:

- 4: PNG `f7a5ff33bd9cbe20f9db6e83d233028d39082397075915be639099b64ee5f8ba`, WebP `043ef54172f518ff750b7ea6a33e8736fbcc9d48a4049a0ce31c80dd791f6a3d`.
- 5: PNG `dd34bac89eaeeaf9862bc90afa503bb2dd0572e21b286bb61353f628b1935cf4`, WebP `467fe6cb6cfa91731040b76c8b768ce2ef6a026da86c00be6544004f0d254ad2`.
- 6: PNG `5a25974f1beea7d0677601e286f4b57b7fc60fdcb38217a36af6ad01b9883733`, WebP `3818fd13d3e1eb424d32ab09f842e387def6f949d4dadd7224efb4e158484ed7`.
- 7: PNG `d553f291d145d8cf3d3f7ed12c2efb86411da0a10edfaee632da17bec8b0cd84`, WebP `8d08ecd8427f3ff0d9a3526c53e2b1537490cc8b0fda21116195002a47313882`.
- 8: PNG `39f9da46052df350e38cdb0de1d64aa4a9deb559a2c0784d05253cb55a245903`, WebP `aa2387b3a44b1e57e9dde2ed0406057e5e312e4cb882508c993677c3fd49d2bd`.
- 9: PNG `4d75d5675d9d2ba976148806a12891a0e02fa581972f7678f2d60076811271d9`, WebP `2cd5a34fae281fdc142eb6d7f6497eca79cc6ce7331fe4fb23205f193e723166`.
- 10: PNG `924261584024a62d7630d488ba8dfbb231d0b7c55fabcf793cee962ec1cd4e85`, WebP `49e2e1ba1a04f5defac772b5876ce5f32cf664c02679793f3651414edf974e22`.

## Ověření a meze přejímky

- 52 cílených testů PASS. Přesné texty částí 4–10 jsou porovnané s otisky
  nezávisle zmrazenými ze schváleného scénáře; ověřené hlasové vazby a 67/67
  skutečných MP3 včetně dekódování a shody s manifesty.
- Node VM prošel všech 67 replik, všechny obrazové přechody a samostatný
  tichý krok. Ověřil chybu/Repeat na setkání, nepřítomnost Audio v tichu,
  vypnutý Repeat, ruční pokračování, pozdní callback, Back/Forward v tichu,
  závěrečné dokončení a Again až po části 10.
- Syntetický audio builder ověřil zachování prvních tří obrazů i účtenek a
  nulové nové požadavky při opětovné kontrole dokončených nových částí.
  Reálná generace se pro tento test neopakovala.
- Lokální HTTP 101/101 skutečných veřejných souborů vrátilo přesné bajty;
  pomocné `.lock` jsou ignorované a nepublikují se.
- Skutečné Safari zobrazilo soukromé statické vizuální testy produkčního
  HTML/CSS: závěrečná mapa na desktopu, tichý obraz bez bubliny a mapa i
  nejdelší Loganova replika v iframe s viewportem 390 CSS px. Obsah i ovládání
  zůstaly viditelné. Tyto testy nejsou živý průchod přehrávačem ani poslech.
- Plná místní brána dokončené šestky: 2978 testů OK (5 SKIP), 444,963 s unit;
  rychlá statická brána a `git diff --check` také PASS.
- Mílovo hodnocení nových hlasů a fyzický průchod na iPhonu zůstávají otevřené.

## Oddělení vývoje a vydání

Vše vzniklo v Datově worktree na `data/parallel-20261104`, bez změn Willova
main a zaparkovaného WIP. Nový vývoj se ukládá vlastním checkpointem.

Případná integrace nových obrazů přebírá věcné commity `3cdc5c26` (část 2),
`99e59145` (část 3) a následující dokončovací commit (části 4–10). Servisní
`06c34051` se do main nepřebírá podruhé; první část i odkaz z pětky tam již
byly integrované vlastními ekvivalentními commity.

Tento pokyn neprovedl p+n ani opakování prvního nejistého nasazení. Historická
účtenka `4b261f77c13a77e845684bbbd90cc876` a report prvního běhu se nepřepisují.
Další krok: místní přejímka hotové šestky a samostatně určené vydání podle Míly.
