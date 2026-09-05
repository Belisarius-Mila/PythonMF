Nazev: VocabularyEN — 49 nových obrázků připraveno ke kontrole
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-09-06 00:07 CEST

## Co se resilo

Dokončení přerušeného zadání vyrobit 49 ilustrací k doplněné slovní zásobě
MMTX ve webové angličtině. Jde o terminálovou práci VocabularyEN, nikoli
vývoj v jiném Human–Adam pracovním proudu.

## Co je hotove

- Na disku ověřeno 47 obrázků; dogenerovány pouze wide a wish vestavěným image_gen.
- Hotovo 49/49 WebP v PictNew/generated/20260905_en_dialogue_batch001/.
- Pět souborů nad 300 000 B zkomprimováno z původních PNG; předchozí WebP
  zachovány v podadresáři originals. Největší finální obrázek má 297 090 B.
- review.html obsahuje všech 49 obrázků, EN, CZ, Sentence a SentenceT.
- generation_report.json eviduje velikosti, rozměry a SHA-256. Úplné prompty
  zůstávají v requests.json; průběh dokládají jednotlivé receipt soubory.
- Technicky ověřeny všechny dekódované obrázky, odkazy galerie, kontrolní
  součty a páry vět. Adam vizuálně prošel čtyři společné náhledy; číslovky
  mají správných 10, 11 a 12 předmětů. Rychlá statická brána prošla.
- Galerie byla otevřena lokálně. Browser bridge není dostupný, proto
  automatický vizuální proklik HTML není doložen.

## Co neni hotove

- Mílovo vizuální schválení, kopie do Pict a případná změna mappingu.
- Synchronizace těchto ilustrací do webu, push a publikace Pages.
- Kandidátní obrázky nejsou dosud součástí produkční knihovny.

## Dalsi krok

Míla projde review.html. Po schválení konkrétní sady ověřit kolize názvů
v Pict a připravit kopii a náhled vazeb; mapping měnit až podle samostatné
autorizace z vocabulary_image_generation_workflow.md.

## Navrhovane dalsi kroky

Po začlenění ověřit CSV -> obrázky -> docs a poté na pokyn publikovat.
Členy, zájmena a abstraktní významy posuzovat společně s větou.

## Zmenene nebo relevantni soubory

- PictNew/generated/20260905_en_dialogue_batch001/
- memory/projects/vocabulary_en_web_cards.md
- memory/reports/vocabulary_en_mmtx_audit_2026_09_05.md

## Bezpecnost / neukladat

Autosave ani plnou historii relace necommitovat. Žádné mazání, push,
publikace ani nasazení nebyly součástí dokončení této kandidátní sady.
