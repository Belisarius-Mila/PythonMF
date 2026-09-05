Nazev: VocabularyEN — 49 schválených obrázků, publikace
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-09-06 00:24 CEST

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

- Žádný otevřený krok schváleného p+n. Volitelná je běžná ruční zkouška
  na Mílově zařízení.

## Dalsi krok

Používat publikovanou webovou angličtinu; při otevřené starší kartě obnovit stránku.

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

## 2026-09-06 00:15 CEST — schválení a začlenění

- Hotovo: Míla schválil obrázky a zadal p+n. Všech 49 bylo bez kolizí
  zkopírováno do Pict a synchronizováno do docs s preserve-extra-assets.
- Rozhodnutí: přesný anglický název souboru má přednost, proto nebylo
  potřeba měnit mapping. Změnilo se právě 49 očekávaných přiřazení;
  ostatní pole všech 425 karet zůstala zachována.
- Technický důkaz: všech 49 hashů v docs odpovídá schválené sadě;
  slovník má 361 přímých přiřazení a 64 přes mapping, žádný fallback.
  Audio audit potvrdil 845 MP3 a 850 odkazů pro 425 slovíček.
  Prošlo 15 importních/mapovacích testů a čtyři testy losování karet.
- Úplná brána prošla: 1518 testů, syntax i whitespace OK.
- Další krok: push, Pages a veřejný HTTP audit.

## 2026-09-06 00:24 CEST — publikace ověřena

- Hotovo: 49 schválených ilustrací i předchozí doplnění 120 hesel jsou
  veřejně dostupné; web má 425 karet. Publikováno z d22f25a4.
- Rozhodnutí: existující vazby ostatních kartiček zůstaly zachované,
  včetně společné ilustrace man pro brother, son a he. Statistiky
  361 direct / 64 mapping znamenají nulový automatický fallback,
  nikoli jedinečný vlastní obrázek pro každé starší heslo.
- Další krok: běžná ruční zkouška na cílovém zařízení; p+n je dokončeno.
- Technický důkaz: úplná brána 1518/1518, cíleně 15 importních/mapovacích
  testů a čtyři JavaScript testy. Pages run 33995717491 má success a
  headSha d22f25a40751b110a61b32013a7f3fa72a5e5ef0; deployment
  6286494824 má success. Veřejný manifest 425 karet, app.js a audio
  manifest jsou bajtově shodné s lokálními soubory. Všech 49 veřejných
  WebP prošlo HTTP a SHA-256 porovnáním se schválenou sadou.
- Důkaz: reports/vocabulary_en_images_publish_2026_09_06.json.
- Web: https://belisarius-mila.github.io/PythonMF/vocabulary-en/
