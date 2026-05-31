# Character consistency brief

Datum: 2026-05-31
Ucel: oprava obrazku a dialogu podle Mily

## Hlavni oprava

Puvodni obrazky jsou hezke, ale nemaji dostatecnou konsekventnost:

- Benji a Bunny musi vypadat jako ve stavajicich scenach `BenjiBunnyScene`,
  `ForestSchool1` a navazujicich MMTX scenach.
- Bruno, Fiona a Sunny maji zustat jmenem i charakterem.
- Vsechny cestovni sceny maji drzet stejny vzhled postav a podobne cestovni
  obleceni.
- Ve scenach 1-5 nesmi byt zadna jina zvirata.
- Jen zaverecna scena u jezera muze mit dalsi lesni hosty.
- Dialogy ve scenach 1-5 musi stavet jen na petici hrdinu.

## Referencni vzhled Benji a Bunny

Benji:

- mily hnedy/bily pejsek,
- velke kulove oci,
- bily pruh na tvari a bily hrudnik,
- pratelky usmev,
- cestovni brasna nebo batuzek,
- vzhled ma navazovat na `docs/BenjiBunnyScene.png` a `docs/ForestSchool1.PNG`.

Bunny:

- svetly bily/sedy kralik,
- dlouhe ruzove usi,
- velke oci a mekky vyraz,
- zeleny batuzek nebo cestovni vesticka,
- vzhled ma navazovat na `docs/BenjiBunnyScene.png` a `docs/ForestSchool1.PNG`.

Bruno:

- jezevec,
- zeleny kabatek,
- mala lucerna,
- klidny, ochranitelsky, trochu starsi.

Fiona:

- liska,
- ruzovy/fialovy kabatek nebo sala,
- mala cestovni brasna,
- chytra, pozorna, vede smer.

Sunny:

- veverka,
- zluty kabatek,
- tyrkysova sala,
- orisky,
- hrava a rychla.

## Pravidla pro nove prompty

Do kazdeho promptu pro scenu 1-5 vlozit:

```text
Only these five heroes are present: Benji, Bunny, Bruno, Fiona, Sunny.
No other animals, no background animals, no birds, no frogs, no bears, no monkeys, no humans.
Keep the same character designs, clothing colors, accessories, and proportions across all journey scenes.
```

Pro scenu 6:

```text
The same five heroes remain prominent and consistent. Additional forest guests may appear only in the background near the lake.
```

## Dialogove pravidlo

Sceny 1-5:

- dialogy mohou rikat jen Benji, Bunny, Bruno, Fiona a Sunny,
- Owl muze zustat jen jako technicka ceska/anglicka napoveda mimo pribehovy
  dialog, pokud ji pozdeji budeme potrebovat v UI,
- zadna jina zvirata nereknou zadnou vetu,
- veta `They are friends` se vztahuje k petici hrdinu, ne k cizim zviratum.

Scena 6:

- dalsi lesni zviratka mohou byt v obraze, ale zustanou jen jako tichy vizualni
  hoste v pozadi; dialog a interakce zustanou na hlavni petici.
