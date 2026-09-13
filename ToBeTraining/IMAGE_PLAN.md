# Kontextové obrázky ToBeToHave

Výběr 2026-09-13. Originály Pict pouze čteny, web má vlastní optimalizované
kopie. Každá ze 107 otázek i 24 skládání má konkrétní `image` v `data.json`.
Pole `origin` dokumentuje zdroj a `alt` skutečný obsah obrázku.

## Vlastní ilustrace

| Soubor | Kontext | Proč vznikl nový obrázek |
| --- | --- | --- |
| black-dog.webp | Is the dog black? / Do I have a dog? / dog in the garden / four legs | Pes v Pict je světlý. Nový je celý černý, má viditelné čtyři nohy a stojí v zahradě. |
| white-cat.webp | Is the cat white? / Does she have a cat? / cat in the garden | Kočka z Pict není bílá. Nová bílá kočka sedí v zahradě. |
| pink-dress.webp | Is her dress pink? | Šaty v Pict nejsou jednoznačně růžové. |
| black-bag.webp | Is her bag black? | Taška v Pict je hnědá. Nový batoh je černý. |
| green-eyes.webp | Are my eyes green? / You have green eyes. | Oči v Pict jsou hnědé. |
| siblings.webp | Is your brother tall? / Is your sister small? / He is tall. | Pict tall zobrazuje žirafu. Nová ilustrace ukazuje vysokého bratra a malou sestru. |
| prague.webp | Are they in Prague? / Does she go to Prague today? | Obecné velkoměsto nenahrazuje Prahu. Zobrazen Karlův most, Vltava a Hradčany. |
| two-sisters.webp | He has two sisters. / věta o sedmileté dívce | Ilustrace ukazuje právě dvě dívky. |
| male-teacher.webp | Is your teacher nice? / Is his father a teacher? | Zdrojové odpovědi používají he; obrázek učitelky by mátl. |
| school-friends.webp | Are we good students? / Are they happy? / školní lekce | Více usměvavých školáků místo jedné studentky. |
| tall-men.webp | Are the men tall? | Právě dva vysocí dospělí muži; bez záměny za děti nebo zvířata. |

## Použité zadání nových ilustrací

Přesná anglická zadání jsou v `image_prompts.json`.
Vytvořeno vestavěným nástrojem ImageGen, nikoli CLI/API skriptem. Společné
zadání: samostatná kontextová ilustrace pro výuku angličtiny, barevný dětský
knižní styl, zaoblené tvary, měkké kvašové stínování, přehledné siluety,
kompozice na šířku přibližně 4:3, středový objekt s dostatkem okrajů.
Bez textu, popisků, vodoznaku, rámečku a UI. Subjekt každého zadání:

1. Jeden přátelský černý pes, celé tělo a všechny čtyři nohy, slunná zahrada
   se sedmikráskami, bez dalších zvířat.
2. Jedna celá bílá kočka sedící v květinové zahradě, bez dalších zvířat.
3. Jedny růžové šaty na dřevěném ramínku, jednoduché krémové pozadí pokoje.
4. Jeden černý školní batoh u dřevěné lavice ve školní chodbě, bez log.
5. Blízký portrét přátelského fiktivního mladého člověka s jasně zelenými
   duhovkami; obě oči dobře viditelné, neutrální pozadí.
6. Velmi vysoký dospívající bratr a jeho malá mladší sestra vedle sebe
   na stejné rovině v zahradě, celá těla, přirozený výškový rozdíl.
7. Pohádkový pohled na Prahu: Karlův most, Vltava, červené střechy,
   Pražský hrad a svatovítská katedrála; bez osob v popředí.
8. Přesně dvě usměvavé sestry v zahradě, celá těla, žádné jiné osoby.
9. Dospělý muž učitel s knihou vedle zelené tabule, jednoduchá třída,
   bez nápisů na tabuli a bez dalších lidí.
10. Přesně čtyři veselí školáci (dva chlapci a dvě dívky) s batohy před
    barevnou školou, přirozené postoje, celé postavy.
11. Přesně dva vysocí dospělí muži vedle sebe na parkové cestě, celé
    postavy, přátelští, bez měřicích značek a dalších osob.

Všechny nové výstupy byly vizuálně prohlédnuty v kontaktních náhledech.
WebP export má maximálně 1200 × 1000 px; kvalita se snižovala z 92 pouze
pokud soubor přesáhl 262 144 B. Původní PNG zůstala zachovaná.

## Pict a meze nápovědy

Ze stávajícího Pict vybrány mimo jiné škola, zahrada, domov, město, otevřené
okno, modrá/šedá obloha, slunce, přátelé, kniha, kolo, červené auto, kino
a restaurace. Byly posouzeny skutečné obrázky, nikoli pouze názvy souborů.

Tematický obrázek místa nevyjadřuje automaticky osobu ani časový údaj
ve větě. U věku pomáhá samostatný věkový štítek z přesného textu otázky.
Obrázky nejsou vyhodnocováním YES/NO: uživatel trénuje obě odpovědi.
Případnou další sadu doslovných scén pro jednotlivé osoby lze navrhnout
až po vizuální revizi prototypu Mílou.
