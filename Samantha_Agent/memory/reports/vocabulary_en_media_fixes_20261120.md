## 2026-11-20 16:57 CET — Opravy nurse, live a let

Hotovo: nurse má vlastní ilustraci dospělé zdravotní sestry v modré
profesionální uniformě; let (nechat/dovolit) má maminku dovolující dítěti
pomoci se zaléváním, žádné letadlo. Obě pevné imageStemOverride v katalogu
zachovávají UID, texty, osobní A–D i sdílený mapping. Vestavěný image_gen,
nové projektové WebP a vlastní obsahově adresované náhledy; původní média
zachovaná. live = žít/bydlet má novou Aria -10% MP3 s krátkým infinitivem
„to live“, který určuje slovesnou výslovnost /lɪv/. Nápis live, CZ zvuk,
obrázek domu i věta stejné. Oprava generátoru je omezená na přesný význam.

Rozhodnutí: Míla doložil tři chyby fotografiemi v Downloads. Místní oprava
je součástí zadání; nové p+n nezadal. Předchozí pexeso6×4 již vydané v
49ad325e, job b3340ff6b43053a637c96e0ec5ce7b47 dokončený, neopakovat.
Zachovaná vazba TVBCP na architektura_komunikace_samantha.txt.

Další krok: Dokončit programovou doménovou bránu a jeden lokální commit.
Přesný konečný head/bránu určuje private/vocabulary_en_media_fixes_20261120/
completion.json. Následně Mílovo posouzení obrázků a poslech, samostatné
p+n přes Terru až na pokyn. Fyzický telefon zůstává otevřený.

Navrhované další kroky: Další nalezené chyby opravovat stejně podle přesného
významu; neupravovat globální českou vazbu let=flight ani sestra=sister.
Technický důkaz:15 audio testů PASS, nový test rozlišuje sloveso a přídavné
jméno live i opakovaný build bez nové výroby. Jen dva image UID a EN audio69
se změnily; všechna původní MP3 hashově zachovaná, větné audio/mapa/CSV stejné.
Nová MP3 plně dekódovaná FFmpeg, přehrání afplay i Safari; nativní Safari
ukázalo oba nové obrázky. Finální brána v gate.log; bez push/deploy.

Obrazové podklady a finální prompty (vestavěný image_gen):

1. VocabularyEN/Pict/nurse-professional.webp — Single square educational
vocabulary illustration of an unmistakably adult female nurse, about35,
wearing professional light blue hospital scrubs, visible stethoscope and a
small plain blank ID badge; friendly adult face and natural proportions,
waist-up three-quarter view in a softly simplified bright clinic, holding a
plain medical clipboard. Warm polished painterly children's storybook art,
gentle daylight, clear subject and uncluttered background. No writing,
borders, letters, labels, logos or watermark; adult healthcare professional.

2. VocabularyEN/Pict/let-allow-help.webp — Single square illustration for
English LET = allow/give permission, Czech nechat/dovolit. Adult mother
in a sunny garden gives a smiling child permission to help water flowers;
looks at the child with an approving smile and an open welcoming palm.
Child reaches for one watering can beside one flower pot. The intended
sentence is Please let me help you. Warm polished painterly children's
storybook art, natural proportions, clear interaction and simple composition.
No airplane, flight, airport, writing, letters, labels, speech bubbles,
logos, watermark or border.

Plné generované PNG zůstávají v původním generated_images; projekt používá
WebP kopie a export docs. Původní sister/flight ani stará MP3 se nemažou.
