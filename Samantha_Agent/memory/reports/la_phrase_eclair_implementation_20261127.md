# La phrase éclair — první implementace

Nový samostatný režim Francouzštiny Jana pro dva vzdálené hráče. Míla výslovně
zadal vývoj po uzavřené přípravě372 vět a médií. Cíl zůstává stejný server,
pozvánky a autentizace; nevzniká nová služba, účet ani placená závislost.

## Uživatelský výsledek

V hlavní navigaci i u Pexesa je La phrase éclair. Zakladatel vybere10/20/30/50
kol a4/6/8/10/15 sekund (výchozí20 a6s). Spoluhráč po vstupu potvrdí nastavení.
Před startem oba klienti připraví obrázky, potom běží pevná2s příprava.
Česká věta zůstává viditelná. Osm zájmen a šest tvarů včetně duplicit mají
oba hráči ve stejném náhodném pořadí. Šest tvarů se nededuplikuje.

Dvě nezávislé volby, každá za1 bod. Chyba zamkne pouze příslušný sloupec na1s;
klik během blokace ji neprodlužuje, správný sloupec zůstává uzamčený do konce.
Oba hráči mohou získat2 body. Server dodrží celý limit i po vyřešení obou.
Body kola se přičtou a zveřejní atomicky až při výsledku. Klient během kola
vidí pouze vlastní potvrzené volby, nikoli soupeřovy.

Výsledek ukáže správnou větu a přípustnou variantu zvoleného zájmena. Jednou
za kolo se přehraje hotová FR nahrávka označená Vzor; ruční opakování dostupné.
Uznané elle/elles nejsou vydávané za jinou zvukovou nahrávku. Chyba audia
neblokuje další kolo. Hostitel nabídne další kolo, druhý hráč je potvrdí.
Po posledním výsledku skóre a remíza/vítěz bez časového rozstřelu; nová hra
použije stejnou místnost a pozvánku s novým náhodným plánem a nulovým skóre.

## Autorita a obnova spojení

Rooms používá stávající SQLite transakce a autentizaci, doplněný režim eclair.
Stavy waiting, eclair_loading, eclair_prepare, eclair_active, eclair_result,
eclair_wait_guest a finished jsou oddělené od původního Pexesa a duelu.
Server ověřuje hráče, fázi, kolo/stage, identitu požadavku, kartu, sloupec,
časové okno [startAt,deadlineAt), blokaci a již vyřešený sloupec. Nepoužívá
klientem tvrzený čas. Správnost duplicitních tvarů je podle NFC textové hodnoty,
apostrofy se sjednocují; diakritika se neodstraňuje. Varianty vět jsou redakční,
nesestavují se slepou záměnou zájmena nebo mechanickým spojováním segmentů.

Při síťové chybě se volby zamknou a tentýž hráč se vrací přes ready po1/2/4/8s,
pak po8s; online a viditelnost návrat urychlí. Aktivní čas na serveru pokračuje,
přerušené kolo se nepřetáčí. Odpovědi/next/rematch/create se automaticky
neopakují; po nejasném create/join se ručně ověří stejná původní identita.
Trvalé chyby přístupu a vypršení automatické pokusy zastaví. Audio má uloženou
identitu místnost+kolo před přehráním, aby poll/reconnect/reload nepřehrál vzor
znovu. Reload a návrat z bfcache vyžadují Pokračovat a zapnout zvuk.

## Soukromý korpus a média

Schválený zdroj je uzavřený v006 game-preparation. Nový deterministický builder
VocabularyFR/vocabulary_fr_eclair.py vytvořil soukromý approved-v1 bundle:
372 kol,62 slovesných skupin,494 přípustných variant,372 zvuků a178 skutečně
použitých obrázků (celkem550 různých mediálních souborů). Pole všech vět,
tvarů a variant jsou proti schválenému zdroji totožná. Všechny reference mají
ověřené soubory a SHA.13 jednoduchých typů vizuálů se vykresluje v UI;
záměrné textové úseky a oddělovače zůstávají v původním slovosledu.
Nevznikla žádná nová syntéza ani generování obrázků.

Klíč odpovědí je v data/private/vocabulary-fr-eclair/approved-v1, mimo docs/Git.
HTTP jej nepodává; klient dostane aktuální zadání a volby, řešení až po kole.
Média se podávají jen pod neprůhlednými SHA názvy /eclair-media/<hash>.<ext>
a mají podporu Range. Export služby přibalí schválený korpus pod private/,
odděleně od veřejných docs. Manifest chrání všechny soubory a nově se jeho
SHA váže také do neměnného aktivačního plánu; změna odmítne aktivaci před
jakýmkoli systémovým zásahem. Starý plán bez tohoto připnutí nesmí aktivovat
privátní Eclair obsah. Neznámý nebo změněný soubor se neprohlásí za hotové médium.
Chybějící obrázek má popisek; chybějící zvuk dovolí pokračovat textem.

## Ověření a jeho hranice

- Testy autoritativního enginu: hranice času, obě skóre, nezávislé blokace,
  duplicity, přehrané eventy, explicitní rod, zvratná slovesa/elize, pořadí
  potvrzení, celý20kolový remízový průchod, restart stejné místnosti a výpadek.
- Skutečný HTTP server a dva nezávislí klienti se syntetickým DOM/audio:
  celá20kolová hra, soupeřova potvrzení, správná varianta, audio jednou,
  reload, ruční opakování, ztracená odpověď bez replay, backoff1/2/4/8,
  trvalé odmítnutí, pomalé obrázky, blokované sessionStorage a nejisté create.
- Samostatná kontrola skutečného372-kolového korpusu; dvě autentizované HTTP
  relace proti skutečným datům získaly2:2, správnou větu/variantu, MP3 Range206,
  pokračovaly do druhého kola a ověřily původní Pexeso i duel. Běžící produkční
  služba f6d16ded zůstala beze změny. Pět lokálních klientských souborů přesně.
- Ověřený soukromý export, nepřístupnost klíče přes HTTP a pin manifestu.
- Finální programová brána, SHA, počet čekajících commitů a přesné účtenky:
  data/private/la_phrase_eclair_implementation_20261127/completion.json.
- Nativní browser host zde není dostupný. Fyzické vykreslení/poslech na dvou
  Macích a úzký telefon nejsou označené za ověřené. Automatický DOM není browser.

## Spuštění a další krok

Místní náhled z Samantha_Agent:

    .venv/bin/python -m app.vocabulary_fr_multiplayer --port 8793 --database data/private/la_phrase_eclair_preview/rooms.sqlite3 --eclair-bundle data/private/vocabulary-fr-eclair/approved-v1

Adresa je http://127.0.0.1:8793/vocabulary-fr/eclair.html. Dva panely znamenají
dvě hráčské relace, nikoli fyzické dva Macy. Preview se neinstaluje do launchd.

Vývoj je místní; publikace nové hry a aktualizace soukromé služby vyžadují
samostatné p+n a přesný aktivační plán. Dosavadní běžící523-kartová služba se
vývojem nerestartovala. Při pozdějším vydání přibalit soukromý approved-v1
korpus a ověřit health.games obsahuje eclair a eclair.roundCount=372.


## 2026-11-27 20:19 CET — Obnovení a dokončení La phrase éclair

Hotovo: Míla obnovil vývoj z uloženého checkpointu. Implementace, soukromý
372-kolový korpus a dosavadní důkazy zůstaly zachované. Doplněné ověření
nejistého založení po reloadu používá původní identitu i nastavení; ovládání
jasně ukazuje Ověřit původní vstup a zabraňuje změně původního požadavku.

Rozhodnutí: Pokračovat závěrečným ověřením a lokálním commitem. Samostatné
publikování a změna běžící herní služby zatím nejsou součástí tohoto dokončení.

Další krok: Po úspěšné programové bráně připravit samostatně autorizované p+n
nové hry a aktualizaci služby s privátním balíčkem; pak přejímka dvou Maců.
Navrhovane dalsi kroky: Fyzické vykreslení úzkého okna a poslech obou klientů.
Pripomenout pri startu: ne

Technický důkaz: Závěrečné přesné vstupy/brána/SHA a počet čekajících commitů
jsou v la_phrase_eclair_implementation_20261127/completion.json. Obnova
neopakuje výrobu médií a neaktivuje službu. Původní přerušení zůstává historické.

Závěrečná kontrola rozložení doplnila kompaktní herní režim pro notebooky:
při hře se schová hotová pozvánka a úvodní popis, zmenší se svislé mezery
a při nižším desktopovém okně výška karet. Oba sloupce zůstávají vedle sebe;
telefon zachovává větší dotykové plochy. Fyzické vykreslení zůstává k přejímce.


## 2026-11-27 21:35 CET — La phrase éclair vydaná a služba aktivovaná

Hotovo: Nová hra dostupná z Francouzštiny Jana pro dva hráče se372 větami,
hotovými obrázky a MP3. Zachovaná adresa a všech19 dosavadních místností,
přístupů, pozvánek i skóre. Dvě skutečné HTTPS relace získaly2:2 a po souhlasu
spoluhráče pokračovaly do druhého kola ve stejné místnosti.

Rozhodnutí: Míla zadal p+n a následně přesně potvrdil globální brzdu pro
připravenou systémovou aktivaci. Provedený původní plán jednou, bez nové výroby.

Další krok: Společná fyzická přejímka dvou Maců včetně zvuku a úzkého okna.
Navrhované další kroky: Žádný nový vývojový rozsah se tímto krokem nezavádí.

Technický důkaz: b19e6c1e,331 testů PASS; Pages job58d4ea7f, deployment8118125267,
workflow46059073466. Služba health pairs/duel/eclair,372 kol;5 klientských souborů
na obou původech přesně, MP3 Range206, odpovědní JSON nepřístupný404. SQLite
integrity OK a19 původních řádků/requestů/těl přesně proti konzistentní záloze.
Produkční API ověřilo oba hráče, potvrzení nastavení,2s přípravu/4s limit,
4 přijaté odpovědi, stav stejným tokenem a host/guest handshake do2.kola.
Soukromé účtenky la_phrase_eclair_release_20261127/completion.json;
finální dokumentační zápis nevyžaduje nový restart. Fyzický browser/zvuk otevřené.
