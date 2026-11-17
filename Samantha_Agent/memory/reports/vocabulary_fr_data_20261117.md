# Vocabulary FR — Data, soukromý obsahový balíček v1.1

Stav obsahového předání: `ready_for_integration` podle kontraktu v1.1; přesný
kódový commit a uzavřený soukromý balíček dokládá navazující soukromá účtenka.
Will je jediný zapisovatel kanonického FR handoffu, TVBCP, ACTIVE/INDEX a projektové
paměti. Tento report je podklad pro jeho společné uzavření, nikoli jeho náhrada.

Hotovo:

- Trvalý registr 464 UID; zdrojových 469 záznamů je zachovaných. Pět schválených
  duplicit má explicitní vazbu na ponechaný význam. Řazení ani CSV Order nemění UID.
- Stejných 18 témat jako IT, slovní druhy, druh výrazu, významové konflikty a
  navazující tvary. Obtížnost 1–3 je přiznaný interní návrh, ne CEFR.
- Oddělené původní identity a 56 redakčně upravených karet: překlepy, gramatický
  rod, neúplné či nesprávné překlady a několik příkladů. Původní CSV se nepřepisuje.
- Vizuálně zkontrolovaných 464 karet; 345 odlišných obrazů. Opraveno 34 explicitních
  obrazových výběrů. Abstraktní vodítka zůstávají označena jako mnemonic/contextual;
  nejde o tvrzení, že všechny obrázky doslovně zobrazují význam.
- Obrazové vazby všech 464 vět: 898 vazeb, 1–5 na větu. Ruční významová kontrola
  odstranila i falešné shody stejně psaných tvarů a složených výrazů. Přesné texty,
  UID a UTF-16 pozice se ověřují při exportu; klient nic živě neodvozuje.
- Bezpečný počáteční režim psaní celého slova: žádné nepřezkoumané francouzské
  slabikování. Konflikty zahrnují sdílené obrazy, homografy, tvary a další významové
  či zvukové blízkosti. Nejde o úplný fonetický slovník.
- Převzaté české MP3 pokrývají 161 slovních karet a 7 vět; jde o 166 různých
  souborů, všechny plně dekódované bez chyby. Převzetí kontroluje přesný text,
  hlas, rychlost, původní identitu a bajtový otisk. Žádná nová výroba ani platba.
- FR kanály jsou explicitně null, oba manifesty partial; galerie/text jsou
  použitelné. Hlasová hra či smyčka potřebující FR musí přiznat nedostupnost.
- Obecné pomocníky, privátní výstupní pojistku a čtecí ověření uzavřeného balíčku
  pokrývá 27 syntetických testů. Kontrola skutečných dat je samostatný důkaz.

Soukromí a předání:

- Janin skutečný katalog, vstupy, exporty, WebP i MP3 jsou mimo Git a docs.
  Commit obsahuje obecný kód, syntetické testy, WEB_FOUNDATION.txt, tento
  redigovaný report a přesně převzatou Willovu registraci testu ve dvou registrech. Osobní příznaky zůstaly samostatně, mimo předávaný payload.
- Zdrojové obrázky jsou připnuté z rezidentního kanonického lokálního Pict.
  U dataless cloudových protějšků netvrdíme nově ověřenou bajtovou totožnost.
- Uzavřený balíček má přesný kódový commit, catalog/content/manifest SHA a soupis
  všech souborů s velikostmi. publicPromotionApproved=false. Uzavřená verze se
  nepřepisuje; případná oprava vytvoří novou verzi.
- Přesné otisky, soukromé umístění a výsledky programové brány patří do soukromé
  předávací účtenky vytvořené po checkpointu. Integrátor musí otisky porovnat.

Další krok a otevřené přejímky:

1. Will převezme přesný kódový commit včetně své registrace testu a soukromý
   balíček. Provede integrační přejímku v soukromém
   stagingu na 127.0.0.1. Aktualizuje společné kanonické dokumenty.
2. Výběr finálního FR hlasu a samostatně schválená výroba nahrávek; v tomto kroku
   se nepřidává Azure adaptér ani automatický TTS fallback.
3. Fyzická přejímka klienta a schválení zveřejnění konkrétního soukromého obsahu
   zůstávají otevřené. Žádný push, upload, publikace, nasazení ani restart.

Podrobnosti obecného formátu a příkazy: VocabularyFR/WEB_FOUNDATION.txt.

Aktuální důkaz po převzetí Willovy registrace:

- Původní blokátor registrace je vyřešený: přesně převzatý Willův patch
  se třemi registračními řádky ve dvou souborech. Jeho SHA-256 souhlasí
  s předáním. Centrální pravidla Data znovu nenavrhoval.
- Programová brána validation-v3 proti výchozímu 31c670bb: PASS, cílený výběr,
  261 testů včetně nových 27 syntetických obsahových testů. Před commitem
  se programově ověří také finální podoba reportu; účtenka je součástí
  soukromého předání.
- Skutečný soukromý export ověřen samostatně: 464 karet, 345 obrazů,
  898 větných vazeb a 856 mediálních souborů. Všech 166 různých MP3 plně
  dekódováno; zdrojový CSV hash zůstal zachovaný.
- Zmrazených 352 vstupních souborů má uzavřený manifest. Finální balíček
  je navázaný na přesný kódový commit a jeho vlastní otisk; při integraci
  se ověřuje přesná předávací účtenka, nikoli tento obecný report.
