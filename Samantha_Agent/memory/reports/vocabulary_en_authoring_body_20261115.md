# Vocabulary EN — autorský vstup a části těla, 15. 11. 2026

Schválené pravidlo: memory/technical/vocabulary_en_authoring_rules.md.
Je uložené před implementací. Následuje skutečná první verze a její dávka.

## Použití přes Data

Přidej shoulder — rameno s obrázkem a větou.
Doplň deset hlavních částí těla včetně obrázků, vět a audia.
Přidej tyto položky: vložený seznam nebo CSV EN/CZ.

Data vyloží zadání a doplní redakční pole, která ověřitelný Python postup
vyžaduje. Samostatný nový LLM interpret, veřejný editor ani formulář nebyly
potřeba. Přirozený chat není předstíraný volný textový parser v Pythonu.
Nová pravidla nevyžadují, aby Míla pracoval v terminálu.

## Implementované operace

- VocabularyAuthoring.preview: read-only náhled, přesné duplicity a staré
  aliasy, vyřazené karty, jiné významy a chybějící redakční pole.
- VocabularyAuthoring.prepare: přesná identita úkolu, oddělená příprava,
  rezervované UID, ověřené převzaté obrázky, nynější registrovaný TTS,
  připnuté obrazové vazby a kompletní manifesty.
- VocabularyAuthoring.apply: pouze přesný připravený digest, kontrola
  výchozích souborů i připravených bajtů, jeden zapisující autor, dohledatelná
  obnova přerušeného zápisu. Dokončený request se znovu neaplikuje.
- VocabularyAuthoring.status: čtení jedné původní účtenky.

Registrované capabilities: vocabulary_authoring_preview/prepare/apply/status.
První verze obsluhuje jeden určený autorský workspace a jeho privátní úložiště
dávek. Při souběhu nad stejným zdrojem přípravy rezervují různá ID; zastaralá
druhá aplikace se odmítne. Nezávislé kopie slovníku se automaticky neslučují.

Nové karty se do osobních A–D přidávají výběrem uživatele, nikoli automaticky.
CSV neimportuje technická ID, WS, L ani HT z neověřených seznamů. Duplicita
se nepřidává; změna významu se neprovádí přepsáním existujícího UID.

## Skutečně zařazené karty

| UID | EN | CZ | Věta EN | Věta CZ |
|---|---|---|---|---|
| ven-0443 | head | hlava | I nod my head. | Kývám hlavou. |
| ven-0444 | face | obličej | I wash my face. | Myji si obličej. |
| ven-0445 | ear | ucho | This is my ear. | Tohle je moje ucho. |
| ven-0446 | nose | nos | Touch your nose. | Dotkni se nosu. |
| ven-0447 | mouth | ústa | Open your mouth. | Otevři ústa. |
| ven-0448 | neck | krk | This is my neck. | Tohle je můj krk. |
| ven-0449 | arm | paže | Raise your arm. | Zvedni paži. |
| ven-0450 | hand | ruka | I wash my hands. | Myji si ruce. |
| ven-0451 | leg | noha | I stand on one leg. | Stojím na jedné noze. |
| ven-0452 | foot | chodidlo | Put your foot on the floor. | Polož chodidlo na podlahu. |

Všechny jsou podstatná jména, typ Slovíčka, topic-02 Tělo a zdraví,
pracovní náročnost1/draft. Původní eyes a hair zůstávají bez změny.
Arm je paže, hand ruka, leg noha a foot chodidlo. Pravidelný plurál hands
v příkladové větě netvoří další duplicitní kartu.

## Obrázky a skutečná zadání

Vestavěný image_gen podle skillu imagegen,9 nových ilustrací; převzatý
Pict/hand.webp beze změny. Zdrojové kopie jsou v VocabularyEN/Pict/ven0443.png
ažven0452.png s výjimkou ruky ven0450.webp. Webové kopie jsou v
docs/assets/vocabulary-en/ a odvozené náhledy v vocabulary-en-thumbs/.
Níže jsou skutečné prompty; všechny mají konkrétní viditelný předmět.

### VocabularyEN/Pict/ven0443.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos, speech bubbles or watermark. Not a medical diagram, not photorealistic. Show a child's complete HEAD in side profile, including hair, skull outline, ear and jaw. Emphasize the entire head from top of hair down to under the chin. The short neck and shoulders are pale grey and secondary. No pointing hands, no thought bubbles. The concept is the whole head, not just the face.

### VocabularyEN/Pict/ven0444.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos, speech bubbles or watermark. Not a medical diagram, not photorealistic. Show the FACE of a friendly child from directly in front. The oval area containing forehead, eyes, nose, cheeks, mouth and chin is gently highlighted in warm skin color. Hair, ears, neck and shoulders are desaturated light grey. All facial features have equal emphasis. Crop to a simple head-and-shoulders portrait. The target concept is the facial area, not the whole head.

### VocabularyEN/Pict/ven0445.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos, speech bubbles or watermark. Not a medical diagram, not photorealistic. A clear close-up of one human EAR in side view, warm natural skin color, realistic simple anatomy. Only a small portion of the adjacent cheek and hair is visible in very pale grey. The single ear is large, central, easy to recognize, no other subjects.

### VocabularyEN/Pict/ven0446.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show a frontal close-up of the central human NOSE, highlighted warm skin color with a clear subtle orange outline. Surrounding cheeks and a little of the eyes and mouth are very pale grey and secondary. The nose is central and unmistakable, without exaggerated size or distortions.

### VocabularyEN/Pict/ven0447.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show a friendly child's MOUTH in a close-up of the lower face. Lips and the mouth opening are highlighted in warm natural color with a subtle orange outline. A gentle relaxed slightly open smile, a few natural teeth may be visible but not emphasized. Nose, cheeks and chin are pale grey. No tongue sticking out, no medical details.

### VocabularyEN/Pict/ven0448.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show the human NECK between the lower jaw and shoulders. Highlight the complete visible neck region in warm skin color and a subtle orange outline, while head, chin, shoulders and the simple t-shirt are pale grey. Neutral front three-quarter view, natural proportions, calm classroom image, no jewelry or scarf obscuring the neck.

### VocabularyEN/Pict/ven0449.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show one complete human ARM from shoulder through upper arm, elbow and forearm down to the wrist, all highlighted warm natural skin color. The hand is visible but pale grey and clearly excluded from the highlighted region; the shoulder connection and small clothed torso fragment are also pale grey. A relaxed slightly bent arm, natural proportions, modest plain short-sleeved t-shirt. The contrast must distinguish arm from hand.

### VocabularyEN/Pict/ven0451.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show one complete human LEG from below the hip through thigh, knee and lower leg to the ankle, highlighted warm natural skin color. The foot is visible but pale grey and excluded from the highlight. A small fragment of modest simple shorts and the other leg are muted grey. Natural standing pose, entire leg visible, clear contrast between leg and foot.

### VocabularyEN/Pict/ven0452.png

Use case: scientific-educational. Asset type: one square vocabulary illustration for learners with cognitive disabilities. Friendly clean classroom illustration, large clear shapes, natural human anatomy, plain ivory background. Only the named body part has warm natural skin color and a subtle orange outline; surrounding parts are pale muted grey. No words, letters, numbers, labels, logos or watermark. Non-photorealistic, simple and calm. Show one human FOOT in a clear side three-quarter view from ankle to all five toes. The whole foot is highlighted warm natural skin color with a subtle orange outline. A short lower-leg segment above the ankle is pale grey, clearly outside the highlight. Natural relaxed bare foot on a simple neutral floor, no shoes, no text, anatomically correct five toes.

### VocabularyEN/Pict/ven0450.webp

Převzatý již existující Pict/hand.webp; bez nové generace nebo úpravy.


## 2026-11-15 08:27 CET — Autorský vstup a první dávka částí těla

Hotovo: Jeden interní autorský postup přijímá jednotlivou položku, seznam
i CSV. Připraví obsah a média v odděleném prostoru, rezervuje stabilní UID
a zařadí přesný ověřený balíček. Stav dávky je dohledatelný; opakované
zařazení vrací původní účtenku. Přirozené zadání interpretuje Data v chatu.
První skutečná dávka má10 částí těla ven-0443 ažven-0452,9 nových ilustrací,
1 převzatý obraz ruky a40MP3. Celkem452 záznamů/442 aktivních,423 Slovíček
a19 Interakcí;18 témat a všechny původní osobní identity zachované.

Rozhodnutí: Míla nejprve schválil zápis návrhu jako pravidla a potom vývoj
a doplnění10 částí těla. Pravidlo technical/vocabulary_en_authoring_rules.md
bylo uložené před vytvořením implementace; původní SHA a čas jsou v soukromé
rule_receipt.json. Jedna karta/jeden význam, bez automatického převzetí
A–D nebo Benji. Nové p+n zadané nebylo. Nový TVBCP není sjednaný.

Další krok: Dokončit plnou bránu, porovnat finální zdroje a vlastní checkpoint.
Navrhované další kroky: Samostatné Terra Pages p+n a přejímka těla na telefonu;
podle potřeby pozdější interní formulář, další tematické dávky a idiomy.
Oxford stále čeká na Mílův odeslaný dotaz.

Technický důkaz:90 cílených Python PASS /46,101s včetně56 Node scénářů.
Ověřený skutečný process exit po prvním zdrojovém zápisu, obnova stejné dávky,
souběh dvou příprav se samostatnými ID, cizí změny, změněný připravený soubor
i jeho změna uprostřed aplikace a zákaz opakování nejistého externího zvuku.
Všech442 původních položek exportu přesně shodných,2568 původních médií
bajtově shodných,40 nových MP3 dekódovaných ffmpeg. Skutečná dávka
body-parts-20261115-v1 je applied;75 změněných souborů a kontrolovaný replay
bez dalšího přidání/generování. Finální plná brána3936 PASS /1017,426s unit část,31 SKIP; soukromá autorita
výsledku je data/private/vocabulary_authoring_body_20261115/verification.json
a checkpoint.json. Vizuální iPhone přejímka není automatickými testy doložená.


## 2026-11-15 08:39 CET — Finální uzavření autorského vstupu a dávky těla

Hotovo: Schválené pravidlo uložené před implementací, jednotný interní
autorský postup a skutečná dávka10 částí těla, kompletní obrázky/věty/audio.
452 záznamů/442 aktivních; všech442 původních karet přesně zachovaných.
Rozhodnutí: Mílovo schválení místního vývoje platí; nové rozhodnutí nevzniklo.
Další krok: Samostatně schválené Terra Pages p+n.
Navrhované další kroky: Přejímka těla a osobních výběrů na telefonu, další
tematické dávky, pozdější interní formulář.
Technický důkaz: Plná brána3936 PASS /1017,426s unit část,
31 SKIP,0 failures/errors;90 cílených Python včetně56 Node PASS.
Všech82/82 finálních zdrojů/testů/dat/médií shodných se zelenou branou;
2568 původních médií zachovaných,40 nových MP3 dekódovaných. Skutečná dávka
body-parts-20261115-v1 applied jednou, replay bez generování nebo zápisu.
Browser host nebyl dostupný; fyzická telefonní přejímka zůstává následná.
Soukromý checkpoint.json potvrzuje výsledný commit a shodu commitovaných
bajtů. Nový TVBCP nebyl sjednaný ani založený.


## 2026-11-15 09:31 CET — Obnovení a příprava předání Terře

Hotovo: Po restartu obnoven hotový autorský vstup a deset částí těla.
V odděleném integračním worktree je zachovaných všech82 zdrojů zelené brány
a12 nezávislých souborů současného main bajtově shodných. Sdílené indexy
zachovávají záznamy Vocabulary EN i Knihovny. Dávka se znovu negenerovala.
Rozhodnutí: Míla výslovně zadal Terra p+n Vocabulary EN. Společný publisher
vydává celý main; čtyři další Willovy commity nejsou touto větou automaticky
schválené. O rozsahu společného push je položena konkrétní otázka.
Další krok: Po potvrzení rozsahu převzít připravenou integraci, zarovnat
jen čisté nedivergentní profily a zavolat jediné submit_release(wait=True).
Navrhované další kroky: Fyzická přejímka částí těla a A–D na telefonu.
Technický důkaz: Zdroj e2276615 + předání acb6e0a8, integrační základ072ab251.
47 cílených Python testů PASS/31,471s a rychlá statická brána PASS.
Předchozí Knihovna jobfff30ae477f38401ae8e582208e9a582 je attention/neaktivní;
živý GitHub audit stálee780fe98 a5 čekajících commitů před integrací.
Pages vydání nesmí restartovat Cockpit. Nový TVBCP není sjednaný.
