# Nedokončená média: kontrola a potvrzený úklid

## Zjištění z telefonu

Míla 24. 10. 2026 doložil hlášku se dvěma rozpracovanými médii. Read-only
inventář telefonu a soukromá kopie Core Data SQLite/WAL (quick_check OK)
potvrdily dva video intenty z 13. října. Nemají odpovídající soubor v Pending
ani Originals, přijatý Asset ani vytvořený Moment; nepatří k cestě v koši.
Jsou to prázdné pozůstatky pokusů, nikoli důkaz dvou uložených videí.
Instalovaný klient byl read-only dotazem potvrzen jako 0.1.0 (22).

Živá databáze telefonu nebyla přes souborové rozhraní přepisována. Úklid
provede nová aplikace svými transakcemi po Mílově potvrzení. Soukromé kopie,
inventáře a redigovaný audit jsou jen v ignorovaném private úložišti.

## Oprava

- U hlášky otevři **Zkontrolovat a odstranit pokusy**. Stejná možnost zůstává
  dostupná i bez aktivní cesty.
- **Odstranit prázdné pokusy (2)** ukáže výslovné potvrzení s volbami
  **Zrušit** a **Odstranit natrvalo**. Bez potvrzení se nic neodstraní.
- Jednotlivý nedokončený soubor má datum, projekt a velikost. Lze odstranit
  pouze jeho vlastní ověřené pending/original soubory a nepřijatý intent.
- Přijaté Assety/Momenty se nesmažou. Nově přijatý nebo změněný soubor
  zneplatní staré potvrzení. Symlinky, cizí hardlinky a adresáře se odmítnou.
  Projekty držené sedmidenním košem tímto úklidem nelze obejít.
- Nejprve se ověří celý vybraný rozsah, potom se odstraní příslušné soubory
  a v jedné Core Data transakci nepřijaté intenty a jejich vlastní pomocná
  metadata. Pád mezi unlinkem a transakcí ponechá intent k novému ověření;
  čerstvý seznam umožní úklid dokončit.
- Zavření přípravy videa během GPS čekání už nevytvoří nový intent.
  Odmítnutý start a neúspěšné dokončení bez souboru ruší prázdný intent.
  Neprázdný soubor zůstává zachovaný ke kontrole. Obnova neběží souběžně
  s rozpracovaným zápisem a model ji nespouští při otevřené kameře.

Historický spouštěcí děj obou pokusů nelze ze zbytků zpětně prokázat.
Zdroj obsahoval cestu, kde odmítnutý start kamery ponechal uložený intent;
tato cesta je opravená. Budoucí přerušení mohou zanechat nedokončený soubor,
proto zůstává ruční kontrola a odstranění. Neznámé soubory a nedostupné
přijaté Assety se tímto úklidem automaticky nemažou.

## Ověření

- Swift/Core Data 95 testů PASS, z toho osm nových: dva prázdné pokusy a
  restart, odmítnutý start, potvrzený poškozený soubor, zachování cizích
  souborů/Assetů/textu/front, změna souboru po kontrole, přijetí po kontrole,
  ochrana projektového koše, symlink/adresář a dokončení po přerušení unlinku.
- Skutečný izolovaný UI scénář PASS (31,631 s): Zrušit zachová pokusy,
  potvrzení vyčistí dva prázdné, samostatné potvrzení poškozený testovací
  soubor; po restartu zůstane původní Moment. Regrese projektové navigace
  samostatně PASS (88,193 s).
- Plná projektová brána 2232 PASS; unittest část 465,698 s, krok 476,5 s.
- První UI ověření opravilo předpoklad testu o všech řádcích lazy seznamu.
  Chybějící cancel v adaptivním popupu vedl k výslovnému alertu. Finální
  úspěšný běh vynutil novou kompilaci aktuálního testu; stará cache předtím
  použila již odstraněnou aserci. Ověřované Swift zdroje se od finálního
  běhu do balíčku nemění.

## Balíček a další krok

- Podepsaná IPA `Camino-Projects-Trash-23-20261024.ipa`, 0.1.0 (23), bundle `cz.pythonmf.camino.app`, 1103371 B.
- SHA-256 `4fda1647f88c66525d5dc43091c4f9d82c502ddff7df48b92c41887dfae3c603`, profil do 2026-10-29T19:01:14Z.
- Archive/export, strict codesign čisté extrakce, ZIP/CRC a nové UI texty v Release PASS; simulátorový seed v Release nepřítomný. Shodné create-only kopie Downloads/iCloud Dokumenty, cloud upload potvrzený. Starší IPA zachované.
- Zdrojový rodič 588e0f10, přesné SHA osmi Swift souborů v privátní účtence; vývojový commit dohledatelný podle Add confirmed cleanup for unfinished Camino media.

Telefon zůstává na potvrzeném buildu 22. Aktualizuj stejnou aplikaci bez
odinstalace. Potom otevři **Zkontrolovat a odstranit pokusy → Odstranit
prázdné pokusy (2) → Odstranit natrvalo**. Dva skutečné prázdné intenty
zatím nebyly odstraněné; fyzický úklid a přejímka se neoznačují za PASS.
Odmítnutý start na skutečné kameře se tímto simulátorovým testem nepotvrdil.
Samostatná služba/Cockpit ani jejich data se tímto krokem nepřepínají;
nový push a p+n neproběhly. Poslední ověření a zápis: 2026-10-24 21:15 CEST.

## Následné p+n — 2026-10-24 21:44 CEST

Všech pět čekajících commitů 0a18db30→3590c288 je publikovaných a Cockpit
nasazený registrovanou Lunou. Účtenka a2500be19e301dc26e6db4cd9fb597a8:
completed, push/deployment confirmed, full gate 2232 PASS / 454,2 s, smoke
5/5 a protected_services_unchanged=true. Živá kontrola před výsledkovým
checkpointem potvrdila GitHub/main 0/0, health OK, stamp 7ae887842f089e5c
a PID 41492. Funkční kód IPA odpovídá vydanému 3590c288.

return_channel=caller; returned_to_adam=false znamená nepotvrzený automatický
portálový návrat. Účtenku převzal a ověřil původní terminálový Adam; úspěšné
p+n se neopakuje. Samostatná služba a telefon se běžným p+n neaktualizují.
Fyzická instalace 23 a odstranění dvou řádků v telefonu zůstávají neověřené.
Tento následný zápis je lokální dokumentační checkpoint pro další balíček.
