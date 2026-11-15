# Vocabulary IT — významové úpravy a export v2


### 2026-11-15 21:51 CET — Schválené významy, nové ilustrace a bezpečný export

Hotovo: Schválených24 hlavních významů je zapracovaných a26 dalších významů
má vlastní kartu/větu, vit-0472–0497. Web497 aktivních karet, starý slovník
zůstává471 řádků. Zachované původní identifikační aliasy; gli jako člen a
niente jako nic nepřevzaly cizí reakci/zájmeno. Běžná slovesná spojení jako
avere ragione zůstávají Slovíčky, Forza/Pronto/Congratulazioni jsou Interakce.
Existující487 vazeb/397 souborů přesně připnutých; další10 obrazů hotových
jako pracovní kandidáti ve PictNew/generated/20261115_it_web_review.
Samostatný HTML přehled10 obrázků je i v Downloads, vložené obrázky fungují
bez závislosti na jiném místním adresáři. Nový exportér vytváří JSON v2,
obrázky do900px a miniatury do240px. Skutečný náhled497 karet/814 assetů.

Rozhodnutí: Míla „Se vším souhlasím, pokračuj…“ schválil významové návrhy
a pokračování. Nové významy se přidávají jen do webového katalogu, původní
CSV se nemigruje. Nové ilustrace byly technicky i obrazově zkontrolované
Adamem; přejímku Mílou tím nenahrazujeme. Kandidátní sada se nedostává do
sdíleného Pict ani mappingu. Původní obrazové knihovny a staré IT/EN výstupy
zůstávají zachované. Datum přidání mají jen26 skutečně nových webových karet.
Obtížnost je vlastní návrh, nikoli CEFR; zbývající stará metadata nejsou plně revidovaná.

Další krok: Míla vizuálně přijme připravenou desetici v
Vocabulary_IT_kontrola_10_obrazku_2026-11-15.html (Downloads); potom dokončit
obrazové vazby a vlastní IT galerii (bod4). Kopírování do sdíleného Pict má
podle vocabulary_image_generation_workflow.md předcházet vizuální schválení.

Navrhované další kroky: Vlastní IT galerie s návratem na kartu a filtry;
oddělené profily A–D; samostatně schválený zvukový vzorek/slova/věty;
italská hra a pozdější samostatně autorizované vydání.

Technický důkaz: Cílené katalogové/exportní/doménové testy ověřují zachování
471 UID/CSV/rodů/L/HT,26 webových významů, odmítnutí změněných dat/case/hash,
změny během konverze, zákaz kandidáta ve finálním režimu, bezpečné cesty,
neměnné assety a přepnutí JSON až nakonec včetně simulace přerušení.
Celý náhled a technická přejímka souborů jsou private/vocabulary_it_export_20261115;
finální programová brána v gate.json/gate.log. Plná sada nezadaná.
Soukromý původní snímek777 vstupů je beze změny. Vestavěný image_gen,10/10,
max103360 bajtů/kandidát; prompty a SHA jsou v generation_report.json.
Není hotová nová galerie, profily, audio ani vydání. Lokální brána proti
společnému77b5f652, žádná automatická integrace souběžného main.

Soubory
- vocabulary_it_catalog.json a content_review.json: schválené významy, explicitní26 UID.
- vocabulary_it_catalog.py: původní CSV identity plus webText samostatných významů.
- vocabulary_it_export.py: čtecí audit, paměťová příprava, neměnné assety, JSON poslední.
- PictNew/generated/20261115_it_web_review:10 kandidátů, přesné prompty/report/review.html.
- Private web_preview: skutečný náhled dat, nikoli nasazená nebo nová koncová aplikace.
- Downloads: původní analýza doplněná o výsledek, významový TXT aktualizovaný,
  Vocabulary_IT_kontrola_10_obrazku_2026-11-15.html se všemi10 obrázky vloženými.

Rozsah a omezení
Publikační režim exportu zde znamená pouze finální datové/obrazové podklady,
nepovoluje p+n a nepotvrzuje hotové audio nebo UI. Náhled má mode=preview,
imageReviewComplete=false; neobsahuje L/HT ani osobní volby. JSON nevydává
migrační datum za historické datum přidání. Při chybě nemaže původní assety.

Podpora další ilustrace ponechává původní uzavřený manifest beze změny:
audit připustí v novém pracovním zdroji jen přesně nové připnuté soubory,
jejich hash/case znovu ověří. Neuvedená přebývající ilustrace zůstává chybou.
Původní zmrazený adresář se nikdy nedoplňuje; nyní additionalPinnedImages=0.
Aktuální celkový náhled má přesně497 platných textů a814 dekódovatelných
referencovaných assetů; všechny obsahové názvy/SHA a rozměry odpovídají.
