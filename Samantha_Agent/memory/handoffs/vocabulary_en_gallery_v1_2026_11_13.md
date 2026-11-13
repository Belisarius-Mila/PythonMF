Nazev: Vocabulary EN — galerie v1
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ne
Datum: 2026-11-13 12:52 CET

Aktualizace 2026-11-13: Navazující publikační registrace má kanonický handoff
handoffs/workstreams/project-vocabulary-en.md. Tento soubor zachovává detail
místní galerie a její přejímky. Vocabulary EN je nově místně katalogově
registrovaný proud, bez soukromého vlákna a bez založeného TVBCP.

Co se resilo:
Míla schválil výchozí galerii, Téma/stručné české ovládání, sousední Další,
náhodně jen explicitně, mobil 2 sloupce a přílohu 425 karet / 18 skupin.
Následně výslovně zadal realizaci místní první verze.

Co je hotove:
- Místní galerie a velká karta s neměnnou posloupností, návratem na poslední
  učené UID, fokusem, historií, obnovou po reloadu a explicitním zamícháním.
- Téma/slovní druh/náročnost/zdroj oddělené, popisky EN/CZ oddělené od směru.
- Katalog fixních identit s přesnými EN/CZ matches; CSV i audio obsah zachované.
- 384 náhledů / 7883044 B; původní obrázky, věty, L/HT a audio beze změny.
- EN83 má zachovaný původní sdílený trainer; nová galerie používá vlastní zdroje.
- 21 cílených Python testů OK, včetně 17 Node scénářů a 10 starších relevantních
  exportních kontrol. Nativní Safari desktop i úzký 2sloupcový pohled PASS.
- Finální plná brána PASS: 3685 testů / 566,387 s, 5 SKIP. Registry i SDK
  testový blokátor jsou opravené. 71 cílených SDK/galerie kontrol PASS.
- Míla přijal místní Mac galerii; zdroje 12/12 a náhledy 384/384 odpovídají
  uloženému manifestu. Původní CSV a audio manifest mají shodné SHA-256.

Co neni hotove:
- Skutečný iPhone a lidský poslech všech nahrávek; místní Mac UI Míla přijal 13. 11.
- Integrace do main, push a publikace Pages nejsou součástí tohoto pokynu.
- Slovní druhy/náročnost jsou první redakční návrh, víceznačnosti označené.
- Pět historických MMTX snapshot auditů selhává i na původních HEAD zdrojích:
  16 novějších dialogových slov není v dřívějším auditním seznamu a původní
  mapping receipt očekává 1055 položek. Jejich očekávání zůstala beze změny.

Dalsi krok:
Místní v1 je ověřená a Mac UI přijaté. Další krok je samostatné rozhodnutí
o integraci/vydání a fyzická iPhone přejímka. Před vydáním ověřit přesnou
registrovanou vazbu Vocabulary EN na publisher; nepoužívat odhadem jiný proud.

Navrhovane dalsi kroky:
- Fyzická iPhone přejímka včetně zvuku a návratu.
- Redakční kontrola nejednoznačných významů a didaktické náročnosti.
- Volitelné malé situační lekce; nejsou předstíranou součástí této verze.
- Samostatně dořešit aktuálnost celého MMTX obsahového auditu.

Zmenene nebo relevantni soubory:
- vocabulary_en_catalog.json; sync_vocabulary_en_to_docs.py;
  build_vocabulary_en_audio.py; GALLERY_AUTHORING.txt.
- vocabulary-en/index.html, gallery.js, model.js, gallery.css;
  data/vocabulary-en.json; assets/vocabulary-en-thumbs/.
- test_vocabularyen_gallery.py; test_vocabularyen_selection.js;
  test_vocabularyen_audio_library.py; cockpit_quality_gate.py.
- projects/vocabulary_en_web_cards.md; ACTIVE_PROJECTS.md; MEMORY_INDEX.md;
  LESSONS_LEARNED.md.

Ověření a důkazy:
- logs/vocabulary_en_gallery_targeted_final_20261113.log.
- Historická neúspěšná brána: logs/vocabulary_en_gallery_full_gate_verified_20261113.log.
- Finální zelená brána: logs/vocabulary_en_sdk_phase_full_gate_20261113.log;
  SHA-256 faf515a0bd8401844afd181c862527c8d81fbf4ad8aaeeb8f308925d65ec512b.
- data/private/vocabulary_en_sdk_phase_20261113/: zmrazené SDK zdroje,
  shodné i po bráně; full_gate_timings.json potvrzuje nulové chyby/selhání.
- logs/vocabulary_en_historical_audit_baseline_20261113.log.
- logs/vocabulary_en_gallery_gate_followup_20261113.log: chyba nového řádku
  registru opravená přesunem do samostatných terminálových projektů; všechny
  testy katalogu proudů OK. Tehdejší SDK startup error následně vyřešen
  oddělením inicializace od původního testovaného RPC limitu.
- Dočasný místní server náhledu po přejímce ukončen; postup nového spuštění
  je v GALLERY_AUTHORING.txt.
- Ignorované data/private/vocabulary_en_gallery_v1_20261113/source_manifest_final.json:
  SHA-256 12 zdrojů a 384 použitých náhledů, CSV/audio manifest a revize dat.
- Jeden nepoužitý pracovní náhled je uchovaný v private QA archivu. Po opravě
  chybného relativního základu je všech 384 použitých náhledů na místě a jejich
  otisky shodné. Žádný původní obrázek ani uživatelská data nebyly smazané.

Bezpecnost / neukladat:
Žádný placený modelový/TTS pokus, služba, zveřejnění ani změna Willova checkoutu.
Nekopírovat soukromá data, autosave, klíče a QA archiv do Gitu. Nový TVBCP ani
Cockpit proud nejsou založené. Historický obrázkový handoff z 6. 9. zůstává historií.


## 2026-11-13 — přejímka Míly a navazující SDK testová oprava

Místní Mac ovládání je přijaté Mílou. Fyzický iPhone a veřejná publikace
nejsou tímto souhlasem nahrazené. Pět historických MMTX auditů zůstává samostatně.
Příčinou SDK chyby byla aplikace krátkého RPC limitu již na inicializaci.
V syntetických testech oddělené fáze: standardní start 3 s, vlastní operace
beze změny 0,5/0,6 s. Produkční zdroje beze změny, žádný retry ani živý model.
71 cílených testů PASS / 22,124 s. Plná brána: PASS — 3685 testů / 566,387 s, 5 SKIP, 0 failures/errors.
Kanonický SDK zápis je zároveň v handoffu/TVBCP layer-human-adam-development.


### 2026-11-13 12:58 CET — Vocabulary EN: přesná vazba na Pages publisher

Hotovo: Vocabulary EN má vlastní katalogovou identitu project-vocabulary-en
a přesnou Pages kontrolní cestu vocabulary-en/. Veřejná aplikace zůstává
beze změny do samostatného vydání. Všech 425 karet obsahuje větu EN a český
překlad; po odhalení jsou viditelné. Dosavadní audio přehrává pouze slovíčka.

Rozhodnutí: Míla zadal pokračovat dalším krokem po přijetí místní v1.
Používá se existující Pages publisher. Žádný nový runtime, modelová role
ani TTS syntéza; registrace sama nezakládá soukromé vlákno ani TVBCP.

Další krok: Servisní rozhodnutí o integraci do novějšího main podle
připraveného předání. Místní registrace je uzavřená zelenou branou; merge,
push ani nasazení zatím neproběhly.

Navrhované další kroky: Po servisně schválené integraci načíst novou vazbu
i serverovým runtime a samostatně vydat galerii, potom fyzický iPhone.
TVBCP Vocabulary EN vytvořit jen po výslovné dohodě, před jeho Cockpit
checkpointem. Případné nahrávky vět jsou samostatný navazující rozsah.

Technický důkaz: Targeted 244 testů PASS / 24,880 s, včetně 18 Node scénářů. Plná brána
PASS — 3688 testů / 631,512 s, 5 SKIP, 0 failures/errors. Testy kontrolují správnou Pages cestu bez deploy
Cockpitu a nové přesměrování neumožňují odvodit z jiného proudu. Regresní
kontroly hlídají přesnou vazbu všech 425 Sentence/SentenceT a oba významy
orange v controlleru. Handoff: handoffs/workstreams/project-vocabulary-en.md.
