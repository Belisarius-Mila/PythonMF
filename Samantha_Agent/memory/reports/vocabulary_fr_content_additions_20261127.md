# Vocabulary FR — nová slovíčka a média před La phrase éclair, 27. 11. 2026

## Dokončená výroba a místní integrace

Míla přijal372 herních vět a potom výslovně zadal nové slovníkové karty,
věty a MP3 nejprve do Janiny iCloudové VocabularyFR a následně do webu.
„Schvaluji výrobu všeho!“ pokrývá obě nabízené zvukové varianty dohromady,
strop0,50 USD bez daně a potřebné nové obrazové podklady. Hra se nevyvíjela.

-42 nových karet vfr-0482 až vfr-0523:40 navržených hesel, oddělený druhý
  význam carte a billet de train z opravené věty. Každá má vlastní FR/CZ příklad.
- Nový webový obsah523 karet /18 okruhů /1206 obrazových vazeb /2092 úplných
  zvukových referencí. Všech481 předchozích klientských karet zachovaných přesně.
- Janin sdílený CSV469→528: původních469 řádků včetně všech vět, pořadí a L/HT
  zachovaných přesně, přidáno17 dosavadních webových a42 nových karet.
  Mílovo FR477 i IT471 jsou hashově beze změny.
-531 úspěšných nových Azure MP3, Henri/Vlasta−10 %, bez opakovaného požadavku.
  Rezervováno28305 účtovaných znaků včetně SSML; odhad0,424575 USD bez daně
  při připnuté retail sazbě15 USD/1M, pod schváleným stropem0,50 USD.
  Jde o výrobní odhad, nikoli ověřené konečné vyúčtování účtu.
- Všechny nové MP3 mají úplné dekódování, délku, hash a trvalou účtenku.
  Původní správné nahrávky jsou převzaté podle hlasu, textu a SHA, bez výroby.
-372 kanonických herních vět včetně audia uložených odděleně jako neveřejná
  příprava LaPhraseEclair; nedostávají se do veřejného klientského korpusu hry.
-11 ilustrací přes vestavěný imagegen vytvořených a Adamem vizuálně
  zkontrolovaných. Abstraktní hesla a čísla mají jednoduché grafické podklady.
  Jízdenka má vlastní grafiku, nikoli stejný obrázek jako train.
- Při skutečné redakci odstraněny falešné větné shody lit→postel a livre→kniha
  v pozici slovesa. Procvičování vylučuje rovněž dva nové znovu použité obrazy,
  aby se nesoutěžilo mezi stejnou ilustrací pod jiným obrazovým otiskem.

## Desktop a sdílená instalace

Desktop umí volitelné Audio/manifest.json vedle aktivního CSV. Rozlišuje přesný
text a FR/CZ kanál, ověřuje hash a při nedostupnosti vrací dosavadní systémový
hlas. Nevyrábí nic za běhu. Všech168 nových slovníkových referencí je v reálné
sdílené kopii dohledatelných. Lokální cache má2241 textových klíčů /2063 MP3.

Pictures/manifest.json rozlišuje přesnou dvojici FR/CZ a má59 explicitních
obrazových vazeb. Tím se obejde např. anglické the pro thé a rozliší dvě carte.
Původní obecný obrázkový resolver zůstává náhradou. Jde o desktopový Mac,
fyzická Pythonista/iPhone přejímka se tím nepotvrzuje.

Nová x86_64 .app sestavená registrovaným builderem v odděleném adresáři,
PyInstaller6.22.3, Python3.12.0rc3/Tk8.6.13. Skutečný bundle check:528 řádků,
107 sloves,107 načtených ilustrací a psaný recall OK; strict podpis před
přenosem PASS, deep podpis po ditto PASS. Přesné zdroje má build MANIFEST.

Nová aplikace, Audio, Pictures a LaPhraseEclair jsou v Janině sdílené složce.
Původní .app i CSV zůstávají v datované Zaloha_pred_aktualizaci_20261127.
Zápis CSV použil vocabulary_csv_store se zálohou a kontrolou původního SHA.
Žádný soubor se nemazal. Starý pomocník vázaný na CSV Order nebyl aplikován.

Pict:59 nových souborů v obou knihovnách,39 nových českých klíčů; všech1136
původních vazeb zachovaných, výsledných1175 klíčů kanonicky abecedně.
Mílovy a Janiny mapping.json jsou bajtově shodné. Nová média jsou vytvořená
pro tento školní obsah; zdrojové CSV, L/HT, pracovní katalogy a účtenky nejsou v Git.

## Ověření

-12 cílených testů lokálních médií/builderu a6 kanonických testů mappingu PASS.
- Společný audit skutečných desktopových resolverů: FR Míla477, FR Jana528,
  IT Míla471; žádný chybějící obrázek ani neúplná věta. Dekódováno768 různých
  rezidentních obrazů;282 starších iCloud placeholderů ověřeno jen metadaty,
  nedošlo k nucenému opětovnému stahování neměněných souborů.
- Skutečný model.js/practice.js přijal523 karet,2092 zvukových referencí,
  1206 obrazových vazeb a523 otázek se4 slučitelnými možnostmi. Posledních42
  odpovídá novým kartám. Vyloučení dvou znovu použitých obrazů ověřeno zvlášť.
- HTTP přes localhost ověřilo všech248 změněných klientských souborů proti
  uzavřené v006.243 nových médií,2622 původních souborů převzatých beze změny.
- Browser access host byl nedostupný; fyzický proklik v prohlížeči ani poslech
  na Janině Macu se nepředstírá. Dva pilotní klipy skutečně přehrané přes afplay;
  všechny nové klipy prošly úplným technickým dekódováním, nikoli lidskou
  akustickou certifikací531 položek.
- Programovou doménovou bránu, finální commit a čekající počet určuje
  privátní completion.json; dřívější přípravný commit24e4acf8 měl239 testů PASS.

## iCloud a vydání — otevřené hranice

Původní synchronizace následně doběhla: Foundation potvrzuje2743/2743 položek
s dostupnými samostatnými metadaty uploaded=true,0 uploading a0 chyb, včetně
celého balíčku .app, CSV a obou manifestů. Vnitřní spustitelný soubor .app nemá
samostatná upload metadata; nahrání jeho celého balíčku je potvrzené zvlášť.
Úvodní přechodná chyba NSCocoaErrorDomain4355 odezněla bez zásahu do účtu,
DNS či služeb a bez opakovaného kopírování. Důkaz icloud-upload-confirmed.json.
Jde o potvrzení nahrání do iCloudu, nikoli fyzického spuštění na Janině Macu.

Web523 je integrovaný místně v docs; tento výrobní pokyn neprovedl Git push,
Pages publikaci ani restart soukromého herního serveru. Neveřejná herní příprava
zůstává mimo docs. Před živým vydáním je nutné výslovné p+n; pro soukromou
herní službu také přesný upgrade s jejími platnými systémovými oprávněními,
protože připnutý serverový katalog musí získat stejná nová média a UID.
Nezaměňovat místní dokončení, iCloud upload, Pages a upgrade herní služby.

Další krok: po p+n vydat
schválený klientský přírůstek registrovanou cestou a případný serverový upgrade
se zachováním místností/SQLite. Jana aplikaci znovu otevře až s dosynchronizovanými
médii a provede skutečný poslech. Teprve potom navázat implementací nové hry.

## Soukromé důkazy

Kanonický pracovní kořen data/private/vocabulary_fr_content_additions_20261127:
user-authorization.json, production-plan/approval.json, produced-audio/ledger.json,
current-bundle.json, bundle-ready-v006, sealed-verification.json,
editorial-media-review.json, client-smoke.json, http-smoke.json,
shared-source-audit.json, local-media-verification.json,
icloud-apply-receipt.json, icloud-upload-status-final.json, web-integration.json.
Starší v005 jsou neměnné. v006 pouze dokončuje obrazové/quiz vazby; audio se
kvůli tomu znovu nevyrábělo. Různý typ apostrofu v jedné převzaté staré větě
je zaznamenaný v plánu jako čistě typografická normalizace bez syntézy.
