# Vocabulary FR — klientský kontrakt v1.1

## 17.11.2026 — Konkrétní veřejná propagace v003 schválená

Míla výslovně zvolil zveřejnění finálního klientského payloadu v003 jako EN/IT.
Do docs/Git patří pouze5 klientských JSON a2520 médií; pracovní katalog,
CSV, plány, souhlasy a podrobné účtenky zůstávají soukromé. Původní v1.1 níže
je historický kontrakt před tímto konkrétním souhlasem. Ostatní datová,
zvuková a vlastnická pravidla jsou zachovaná. Doklad propagace a SHA manifest
private vocabulary_fr_jana_release_20261117/public_promotion_approval.json.


Současná autoritativní dohoda Míly a Data17.11.2026 je kontrakt v1.1 v Downloads.
Tento git-safe přehled neobsahuje skutečný katalog, soukromé cesty ani osobní stav.

- Data: obecné obsahové pomocníky/testy a uzavřený soukromý obsahový balíček.
- Will: docs/vocabulary-fr, klientské fixtures/testy, centrální registry,
  kanonický FR handoff, existující TVBCP a finální integraci.
- Stabilní vfr UID a numerické id přiděluje Data; nepřidělovat podle živého Order.
  Cíl464 karet/18 okruhů nepatří jako pevný počet do běhového klienta.
- Katalog schema2, language=fr, appName=VocabularyFR, translationLanguage=cs,
  parents/groups/items; fr/cz, sentenceFr/sentenceCz, genderFr a zbývající
  významová pole podle IT. revision je provenance.catalogSha256.
- Slovo/věta audio schema1, language=fr, kind words/sentences, status
  not-generated/partial/complete. fr/cz cesta je platný FR asset nebo null.
  Nezávisle ověřit každou cestu; identity UID/FR/CZ a vět musí přesně souhlasit.
  Chybějící/poškozená francouzština nikdy nenahradí FR akci českým zvukem.
  Český kanál funguje samostatně. FR hlas může být zatím null. Bez TTS fallbacku.
- Obrazové procvičování schema1/kind spelling-pictures. Neověřené dělení
  jen whole-word s jednou celou částí; francouzské slabiky neodvozovat z IT.
- Obrazy vět schema1/kind sentence-pictures/maxPictures5. sourceFr/sourceCz,
  sourceSentenceFr/sourceSentenceCz, reviewed a concepts s významovým UID,
  sourceFr/sourceCz/text/occurrence/start/end; pozice jsou UTF16. Bez živé inference.
- Lokální klíče vocabulary-fr.navigation.v1/last-card.v1/learners.v1;
  záloha kind vocabulary-fr.learner-backup/schema1. Žádný automatický import L/HT.
- Skutečný obsah zůstává mimo docs I Git, v uzavřeném soukromém payloadu
  s manifestem bundle ID/verze,464, otisk UID katalogu, source code commit,
  relativní path/size/SHA256 všech souborů; private a publicPromotionApproved=false.
  Přesný strojový formát manifestu musí potvrdit předávající balíček; klientský
  commit jeho parser nepředstírá. Předaný obsah ani complete audio nepovolují
  veřejnou promotion. Integrační náhled jen na127.0.0.1 mimo publikační strom.
- Existující projekt Vocabulary FR a desktopový launcher zůstávají. Webový
  cíl je připravený místně; samostatné p+n/restart/publikace vyžadují nový pokyn.

Důkaz aktuálního kroku: reports/vocabulary_fr_client_20261117.md,
handoffs/workstreams/project-vocabulary-fr.md a stávající FR TVBCP.
