Nazev: Vocabulary EN — galerie v1
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-11-13 10:53 CET

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
- Plná brána: NEZELENÁ: 3685 testů / 910,695 s, 5 SKIP; 1 chyba registru (opravena), 2 SDK startup timeouty. Následně 36 cílených kontrol: 35 OK, 1 SDK inicializace s limitem 0,5 s stále ERROR.

Co neni hotove:
- Mílova ruční přejímka, skutečný iPhone a lidský poslech všech nahrávek.
- Celková brána není zelená: zůstává nezměněný syntetický SDK startup timeout
  s limitem 0,5 s. Bez změny limitů/SDK kódu; před vydáním samostatně vyřešit.
- Integrace do main, push a publikace Pages nejsou součástí tohoto pokynu.
- Slovní druhy/náročnost jsou první redakční návrh, víceznačnosti označené.
- Pět historických MMTX snapshot auditů selhává i na původních HEAD zdrojích:
  16 novějších dialogových slov není v dřívějším auditním seznamu a původní
  mapping receipt očekává 1055 položek. Jejich očekávání zůstala beze změny.

Dalsi krok:
Převzít místní první verzi s Mílou, následně samostatně rozhodnout o vydání.

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
- logs/vocabulary_en_gallery_full_gate_verified_20261113.log.
- logs/vocabulary_en_historical_audit_baseline_20261113.log.
- logs/vocabulary_en_gallery_gate_followup_20261113.log: chyba nového řádku
  registru opravená přesunem do samostatných terminálových projektů; všechny
  testy katalogu proudů OK. Z 36 kontrol jediný error v SDK startup fixture.
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
