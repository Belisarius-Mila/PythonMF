# MMTX — oprava Benjiho v prvních pěti ilustracích šestky

**Vydané na Pages ab123bb6:** Terra job 27d6be4c4435a3fa50f12a059ddf0d8e completed, push/deployment confirmed, gate3457 PASS / 597,8 s. Pages run 42896378127 / deployment 7693545647. Aktuální veřejné soubory 327/327 přesné (10 529 491 B); čtyři staré URL404 a staré freddie_jump.webp503, jeho404 tedy neověřená. Ve vydaném zdroji všech deset starých cest odstraněno.

Benji stojí v obrazech 01, 02, 03, 031 a 04 vzpřímeně na dvou zadních nohách. Má dvě přední končetiny přirozeně použité jako ruce, dvě zadní nohy a žádnou pátou končetinu. Zachovává zlatobílou srst, visící uši, zelený šátek a hnědé zavazadlo. Vizuálně zkontrolováno všech pět úplných výstupů vestavěného image_gen; celkem pět editací, bez API/CLI fallbacku.

Ostatní postavy a děj zachované: jednička hledí na jezero, Ollie nabízí rybu v podběráku, 03 zachovává skok, 031 rozhovor s Freddiem napůl ve vodě a Dotty obrácenou k přátelům, 04 příchod k chatrči. Nejde o pixelově identickou maskovanou úpravu okolí, ale o vizuálně věrné editace původních ilustrací.

Původních pět WebP je na výslovný pokyn smazaných v docs i mirroru. Nových pět má příponu _benji_v2.webp, aby se nevracela původní cache. Katalog, úvodní obrázek i preload/prefetch vedou na nové názvy; HTML/JS mají novou cache verzi. PNG v Downloads nahradily pět původních kopií, včetně původní arrival_side_view_20261110_v1.png ověřené přes přesný SHA-256. Git historie se nepřepisuje.

WebP cwebp q90/method6, bez ořezu či přepočtu rozměrů. Obrázek 02 má nativně 1670 × 941 oproti dřívějšímu 1671 × 941, katalog uvádí skutečný rozměr; ostatní zůstávají 1672 × 941.

| Obraz | Nový WebP v obou webových složkách | Rozměr | PNG v Downloads |
| --- | --- | --- | --- |
| 01 | arrival_side_view_benji_v2.webp | 1672 × 941 | arrival_side_view_20261110_v1.png |
| 02 | ollie_dinner_benji_v2.webp | 1670 × 941 | MMTX_Cesta_k_jezeru_6_obrazek_02_Ollie.png |
| 03 | freddie_jump_benji_v2.webp | 1672 × 941 | MMTX_Cesta_k_jezeru_6_obrazek_03_Freddie_a_Dotty.png |
| 031 | freddie_conversation_benji_v2.webp | 1672 × 941 | MMTX_Cesta_k_jezeru_6_obrazek_031_Freddie_a_Dotty.png |
| 04 | old_hut_benji_v2.webp | 1672 × 941 | MMTX_Cesta_k_jezeru_6_obrazek_04_Stara_lod_a_chatrc.png |

Uloženo do docs/scene06_lake_arrival a MatysekANJ/web_mmtx/scene06_lake_arrival. Pět originálních nových PNG zůstává také ve standardním generated_images; projekt neodkazuje mimo repo. Přesné staré/nové otisky jsou v mmtx_scene06_benji_upright_assets_20261110.json a zadání v mmtx_scene06_benji_upright_prompts_20261110.md.

Ověření: 40 cílených testů OK / 24,849 s a rychlá statická brána OK. Všechny změněné webové soubory místně přes HTTP 8/8 byte exact; obě kopie celého příběhu shodné. Zachovaných 319 dřívějších veřejných souborů včetně všech 288 MP3 je beze změny. Safari skutečně zobrazilo opravený obraz 04 v přehrávači s celým Benjiho tělem a správnými čtyřmi končetinami. Stávající testy návaznosti používají nové názvy; žádné testy navíc kvůli samotné výměně obrázků.

Míla současně výslovně autorizoval nové p+n Terrou. Tento vývojový checkpoint předání ani nasazení ještě nepotvrzuje. Další krok: bezpečné převzetí do main, čisté profily, jedno registrované submit_release(wait=True) pro project-mmtx/Pages a ověření nové veřejné podoby i nepřítomnosti starých souborů.

## Výsledek vydání

Jediný request data-mmtx-benji-upright-e903dc7a-20261110-v1 předal dva commity včetně dřívějšího interiérového receipt19703fdb a integrace ab123bb6. Pět image_gen editací proběhlo úspěšně bez dalších pokusů. Před publikací main40 cílených OK / 31,873 s a statická brána OK; publikační worker3457 PASS / 597,8 s. Chráněné služby beze změny, main/origin aligned a oba profily čisté/aligned; 0 pending main commitů.

Veřejná kontrola327 aktuálních souborů HTTP200 a byte/SHA exact dokončila všechny GET v prvním běhu. Až následná oddělená kontrola starých URL narazila na HTTP503; úspěšné aktuální soubory se kvůli tomu neopakovaly. Následné omezené čtecí kontroly potvrdily staré arrival_side_view, ollie_dinner, freddie_conversation a old_hut HTTP404. Staré freddie_jump.webp stále vrací503; nelze tvrdit potvrzenou404, ale jeho původní zdroj je odstraněný a aplikace používá nový funkční WebP. Další p+n ani automatické opakování požadavků se neprovádí.

Skutečné Safari bylo ověřené místně před vydáním, po vydání GUI nešlo získat (cgWindowNotFound, browser host unavailable), takže produkční proklik zůstává Mílovi. Veřejná byte-kontrola je potvrzená. Fyzický iPhone rovněž otevřený.

Závěrečná účtenka a veřejné otisky jsou v sousedních release/public JSON. Tento poslední zápis je místní Data checkpoint; vydaný main se po publikaci nemění.

Produkce: https://belisarius-mila.github.io/PythonMF/scene06_lake_arrival/?release=ab123bb6#picture=2
