# Výběr média z Fotek do okamžiku

Implementace 2026-10-03, pouze iOS. Nasazení na telefon a fyzická přejímka
jsou samostatný následující krok. Serverový kód ani živá data se nemění.

## Ovládání a hranice

V horním menu detailu existujícího okamžiku je **Vybrat z Fotek**. Systémový
výběr přijme jednu fotografii nebo video. Zavření výběru nic nezapisuje.
Během načítání je viditelný stav; čekání na poskytovatele/iCloud lze zrušit.
Během dokončování se změny stejného okamžiku dočasně zablokují. Kopírování,
konverze a hashování probíhají mimo hlavní vlákno, videa se nenačítají do Data.

- Datum, GPS, kapitola a soukromí cílového okamžiku zůstávají stejné.
- Originál ve Fotkách se nikdy neupravuje ani nemaže. Camino archivuje
  připravenou importní kopii. Nejde o bezeztrátový export knihovny Fotek.
- JPEG se kopíruje beze změny bajtů. HEIC/PNG a další podporované statické
  obrázky se připraví jako JPEG v původním rozlišení (kvalita 0,95), se
  zachováním orientace. Limit je 100 megapixelů; alfa má bílé pozadí.
  Live Photo se vloží jako statická fotografie, animovaný obrázek jako první
  snímek. Převod do JPEG a omezení Live Photo jsou uvedeny v aplikaci.
- Video se převede do MOV pomocí AVAssetExportPresetPassthrough, bez
  překódování obrazové/zvukové stopy. Nepodporovaný formát skončí chybou;
  skrytý převod do nižší kvality se neprovádí. Video bez zvukové stopy je
  platný import a není označeno jako neúplná nahrávka.
- Načtení souboru uloženého pouze na iCloudu potřebuje jeho dostupnost.
  Příprava místního souboru nečeká na Mac ani GPS.

## Uložení, kompatibilita a obnova

Před vznikem trvalého záměru se ověří kapacita, připraví kopie, ověří média
a spočítá SHA-256. Teprve poté vznikne existující MediaIntent a soubor se
přes Pending přesune do Originals; Asset se potvrdí v transakci. Pád po
přesunu souboru se obnovuje stávající rekonciliací. Příprava před záměrem
nemůže vytvořit prázdný Moment. Dočasné kopie vznikají v systémovém tmp;
normální dokončení i chyba odstraní jen adresář daného importu. Pád procesu
před dokončením může zanechat dočasnou kopii pro úklid systémem.

Původ `photo_picker` se ukládá transakčně v existujícím SettingRecord;
Core Data model ani schéma přenosového journalu se nemigrují. Starší média
zůstávají camera/recording. Nové create_asset používá existující serverový
kontrakt photo_picker; již přijaté obálky se nepřepisují. Obnova hotového
importovaného videa nepřidává značku přerušeného natáčení. Skrytý/smazaný
cílový Moment nemůže přijmout novou přílohu.

## Ověření

SwiftPM: 63 testů, včetně 5 nových testů importu:

- JPEG beze změny zdroje/bajtů a vlastností parent Momentu, původ po reopen,
  synchronizační payload photo_picker;
- PNG/HEIC → JPEG, rozměry a EXIF orientace;
- tiché MP4 → dokončené MOV, zdroj zachován, žádná chybějící kopie;
- chybný vstup, nedostatek kapacity, zrušení a smazaný parent bez nových
  pending záměrů/Assetů;
- reopen a dvojí rekonciliace kompletního pending videa bez duplikace či
  falešného příznaku partial.

Po závěrečné úpravě kontroly rezervy cílená sada médií 14/14 PASS; plná
projektová brána 1847/1847 a rychlá statická kontrola PASS.

Generic iOS build ověřuje také PhotosPicker/FileRepresentation a Swift 6
izolaci callbacků. Samotné sestavení nepotvrzuje fyzickou přejímku.

Po instalaci nového buildu přes SideStore, po jednom PASS/FAIL:

1. Otevřít existující okamžik, Vybrat z Fotek, vložit běžnou HEIC fotografii;
   zobrazí se nahoře mezi médii, původní fotografie ve Fotkách zůstane.
2. Krátké video se zvukem: přehrávání obrazu/zvuku v telefonu a po přenosu
   na Mac ve Vieweru. Ověřit také orientaci na výšku.
3. Zrušení výběru a načítání iCloud položky, potom úspěšný opakovaný výběr.
4. Větší video, návrat po zamčení/aplikaci a import v owner_only okamžiku;
   soukromá položka se nesmí objevit ve Vieweru.

Tyto fyzické body jsou NEOVĚŘENO. Neměnit podpis/instalaci ani služby bez
příslušného následného kroku; GitHub push nebyl zadán.

Technický podklad Apple: [reprezentace položky ve PhotosPicker](https://developer.apple.com/documentation/photosui/phpickerconfiguration-swift.struct/preferredassetrepresentationmode).
Zvolená current omezuje dodatečné převody systémem; kompatibilní importní
kopii připravuje Camino výslovně podle uvedených pravidel.
