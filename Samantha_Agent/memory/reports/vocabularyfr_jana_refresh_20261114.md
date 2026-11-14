# Vocabulary FR — Janina aktualizace14.11.2026


## 2026-11-14 10:36 CET — Janina nová slovíčka, věty a ilustrace

Hotovo: Na výslovný požadavek Míly doplněno18 dvojic Sentence/SentenceT
v aktivním Janině iCloud VocabularyFR.csv. Janin soubor má469 řádků
a všechny dvojice úplné. Zachované všechny původní neprázdné věty, pořadí,
FR hesla, L/HT, gender a další sloupce;4 české opravy: cette → tato/tahle,
porter → nosit/mít na sobě, jupe → sukně, bizarre → bizarní/divné.
Starý helper vázaný na Order nebyl aplikován. Zápis přes existující
vocabulary_csv_store se SHA kontrolou, ověřenou zálohou a atomickou výměnou.

Obrázky: Šest nových samostatných ilustrací přes vestavěný image_gen
(clothes, these, short, tshirt, strange, suitsyou); Adam zkontroloval výstupy
v rámci výslovného pověření vytvořit potřebné obrázky a aktualizovat mapping.
Čtvercové1254×1254 WebP,94 226–229 300 B, bez textu. Ostatní obrázky znovu
použité včetně jacket pro nosit/mít na sobě. Žádná původní ilustrace se
nepřepisovala ani nemazala. Nové soubory v obou Pict mají stejné SHA-256.

Mapping:1119 →1136 českých abecedních vazeb,17 nových klíčů. Zachované
všechny dosavadní vazby. Doplněné i nalezené starší mezery pro křehké,
pozvaného hosta, závody a pst. Kanonický Pict/mapping.json a Janina
distribuční kopie jsou bajtově shodné. Mílovo FR477 a IT471 hashově
beze změny; staré kořenové CSV ani VocabularyFR_Jana.csv se nepoužívají
a neměnily se.

Ověření:6 kanonických testů mappingu PASS, rychlá statická brána PASS.
Společný audit všech tří aktivních slovníků a skutečných desktopových/
Pythonista resolverů: FR Míla477 / FR Jana469 / IT Míla471, všechny věty úplné, skutečné desktopové i Pythonista resolvery bez chybějících obrázků;1517 obrazových cest dekódováno,0 chybějících mapování/souborů.
Foundation NSURL potvrdilo uploaded=true, uploading=false, upload_error=false
pro Janino CSV, mapping a všech6 nových obrázků (8 souborů). Fyzický reload
na Janině iPhonu je samostatná přejímka; samotný upload jej nedokazuje.

Soukromé plány, ověřené zálohy a účtenky:
data/private/vocabularyfr_refresh_20261114/. Nové ilustrace a prompty:
PictNew/generated/20261114_fr_jana_refresh_batch001/generation_report.json
a review.html. Generované obrázky a soukromé CSV zůstávají mimo Git přes
přesný lokální exclude. Do checkpointu patří mapping a bezpečné podklady.
Nesouvisející nezařazený agent_supervisor 2.md zůstává zachovaný.

Další krok: Jana znovu načte sdílená data v používané aplikaci. Nahrát/
synchronizovat VocabularyFR/VocabularyFR.csv a v Pict mapping.json plus
clothes.webp, these.webp, short.webp, tshirt.webp, strange.webp, suitsyou.webp.
Mapping patří pouze do Pict. Kód aplikací, instalace, Cockpit ani Pages se
neměnily; žádné p+n ani externí zpráva nebyly zadané či provedené.
