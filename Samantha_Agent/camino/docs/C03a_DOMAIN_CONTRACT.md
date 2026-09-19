# C03a — datový kontrakt, revize, čas a soukromí

Stav: referenční doménový model a syntetické testy, 19. září 2026. Autoritativní
jsou v0.5 a novější dodatek U15. Tento zápis a `camino/domain/model.py` fixují
význam dat; neznamenají integraci do iPhonu, serveru ani Vieweru.

## Identita a vlastnictví

- P0 má jednoho autora a jeden hlavní zapisující iPhone. ID vzniká offline jako
  kanonické UUID a zůstává stejné při opakovaném odeslání. Název souboru ani
  pořadí fronty nejsou identita.
- `Trip` vlastní `JourneyDay`; `Moment` patří jedné cestě a jedné kapitole.
  Dva rychlé snímky jsou dva Momenty. Další explicitně připojený `Asset` má
  vlastní ID a `moment_id` cílového Momentu. Samostatný soukromý dovětek je nový
  `Moment` typu `reflection` s `related_moment_id`; původní Moment se nepřepíše.
- `Asset` drží typ, původ, počet bajtů, případný SHA-256 a délku audia/videa z
  mediální časové osy. Obsah a hash se po dokončení považují za neměnný
  originál; změna soukromí a kapitoly je metadatová revize Momentu.
- `TextRevision` drží roli, obsah, zdrojová ID a rodičovskou revizi. Rozpracovaný
  `TextDraft` je oddělený a nesmí se stát čtenářskou revizí bez uložení.
  Později doručený AI text nepřepíše již uloženou lidskou revizi.

F38 vyjmenovává také `RecordingSession`, `UploadSession`, `ProcessingJob`,
`BackupReceipt`, `ExportRevision`, `MediaDerivative` a `ViewerBuild`. Jejich
identita a význam zůstávají podle F38; tento modul je nevytváří ani neprohlašuje
za hotové. `RecordingSession` náleží integraci C04, přenosové objekty C02/C03b,
serverové revize C05 a Viewer/odvozeniny C08. C03b stanoví verzi drátového API,
serializaci, chybové odpovědi a migrační hranice.

## Revize a konflikt

- První lokální Moment má revizi 1. Každá přijatá metadatová operace nese
  jedinečné ID, `device_sequence`, cílový Moment a `expected_revision`.
  Přesný retry vrátí stejný stav; stejné ID s jiným obsahem a stará očekávaná
  revize jsou konflikt. Historie verzí je append-only; žádná varianta se
  automaticky nemaže.
- `PrivacyChange`, `HiddenChange` a `ChapterChange` mění jen svůj příslušný
  atribut. Přesun kapitoly zachová zachycený čas, polohu a původní revizi.
  Zámek a skrytí mají přednost ve frontě před mediální prací.
- Server nesmí rozhodovat pořadí podle hodin telefonu. Přijetí operací,
  řešení konfliktních variant a obnova staršího inventáře patří C03b/C05.
  Při sporu o soukromí se uplatní přísnější varianta; nejasnost nesmí sama
  zveřejnit obsah.

## Čas a poloha

- `CaptureTime` uchovává UTC v milisekundách, místní čas při zachycení,
  tehdejší offset, dostupné ID pásma, zdroj a příznak nejistoty. Výchozí
  kapitola je datum **začátku** v místním čase. Serverové `received_at_utc_ms`
  je samostatná hodnota, nikoli náhradní čas pořízení. Import bez spolehlivého
  času a offsetu má nejistotu a ručně přiřazenou kapitolu; offset se nedopočítá.
- Syntetický příklad opakované hodiny: `2026-10-25T02:30:00` s offsetem +120
  odpovídá 00:30 UTC, tentýž místní údaj s offsetem +60 odpovídá 01:30 UTC.
  Oba patří do kapitoly 25. října, ale nejsou týž okamžik. Nahrávka začínající
  20. září v 23:55 a trvající 10 minut zůstává v kapitole 20. září.
- Poloha je volitelná a její nepřítomnost neblokuje záznam. Bod z cache starší
  než 120 s se nepřipojí jako aktuální; horizontální přesnost nad 100 m je
  označena jako přibližná. Neodvozuje se z ní trasa ani kilometráž.

## Soukromí U15

- Soukromí patří celému Momentu, tedy i všem jeho Assetům a textům. Známé
  hodnoty jsou `owner_only` (`Jen pro mě`) a `diary` (`Do deníku`). Neznámá
  hodnota se pro Viewer zavře. Nová samostatná Úvaha je v doménové logice vždy
  `owner_only`, i když je běžný výchozí režim `diary`.
- Úvahu může odemknout jen vědomá akce `insert_reflection_into_diary`. Vytvoří
  novou metadatovou revizi s prioritní operací; původní audio ani historie se
  nepřepisují. Běžný Moment potřebuje vědomé `unlock`. Přepnutí zpět na
  `owner_only` je lokálně okamžité a vytváří revizi `lock`.
- Referenční výběr pro Viewer bere pouze **nejnovější serverem přijatou** revizi
  každého Momentu v povolené cestě: musí být `diary` a nesmí být skrytá.
  Konfliktní údaje stejné revize se zavřou. Výstup vrací jen povolená ID,
  žádné počty nebo metadata vynechaných soukromých položek. Owner souhrn,
  lokální neodeslaná změna ani koncept nejsou zdroj Vieweru.
- Po místním zámku, dokud server nepřijme jeho revizi, musí telefon zobrazit
  `Čeká na server`; referenční `server_revision_pending` porovnává lokální a
  přijatou revizi, soukromí i skrytí. Teprve přijatá revize může omezit serverový Viewer. Již
  zobrazenou či uloženou cizí kopii nelze odvolat. C08 musí při každém vydání
  média znovu kontrolovat aktuální serverové oprávnění; stará URL nesmí obejít
  později přijatý zámek.

## Důkaz a navazující práce

`tests/test_camino_domain.py` používá výlučně syntetická ID, texty, časy a
souřadnice. Kryje privátní výchozí Úvahu, explicitní uvolnění, starší a
konfliktní serverové revize, retry, revize kapitoly, opakovanou hodinu,
půlnoc, nejistý import, polohu a koncept. Neprokazuje fyzické T005/T008,
T027–T032/T039/T041 ani T096. C04/C05/C08 musí model převést do skutečné
persistence, API a UI a tyto scénáře ověřit na zařízení a soukromé trase.
