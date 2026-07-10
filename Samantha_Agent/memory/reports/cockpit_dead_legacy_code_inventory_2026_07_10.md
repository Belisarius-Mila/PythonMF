# Cockpit: read-only inventura mrtvého a legacy kódu

Datum: 2026-07-10

Rozsah: Samantha Cockpit, launcher, VoiceBridge, reminders a Quick Notes

Režim: statická read-only analýza; bez změny aplikačního kódu a bez čtení private obsahů

## Výsledek

Cockpit není zaplněný velkým množstvím náhodně mrtvého kódu. Hlavní problém je
stále velikost a provázanost monolitu, ne stovky osiřelých funkcí.

- `app/cockpit.py` má 22 454 řádků a 331 top-level Python funkcí.
- Duplicitní top-level Python definice: 0.
- Z produkčních vstupů, serverové třídy a produkčních importů je staticky
  dosažitelných 323 z 331 funkcí.
- Osm nedosažitelných funkcí v monolitu tvoří tři malé historické větve.
- V kontrolovaných VoiceBridge a persistence modulech nebyla nalezena žádná
  top-level funkce, která by se v repozitáři vyskytovala jen jako definice.
- Backend má 42 přesných GET cest a 67 přesných POST cest.
- Všech 67 POST cest je právě jednou v `COCKPIT_POST_ACTIONS`; každá karta ukazuje
  na skutečně volaný handler. Chybějící nebo přebývající karta: 0.
- Tři hlavní HTML dokumenty obsahují dohromady 303 deklarací JavaScript funkcí
  a 4 arrow funkce. Nebyla nalezena duplicitní deklarace ani funkce, jejíž jméno
  by se v příslušném dokumentu objevilo jen v definici.
- Nebyl nalezen duplicitní HTML `id`, chybějící cíl `getElementById()` ani
  proměnná s DOM prvkem, která by zůstala jen deklarovaná.

Statická analýza sama nedokáže prokázat, že endpoint nepoužívá externí Shortcut,
starý bookmark nebo ruční API klient. Proto se níže oddělují přímé kandidáty
Python kódu od API tras, které potřebují poslední provozní ověření.

## Aktualizace po Cleanup R1

Cleanup R1 byl 2026-07-10 opatrně realizován přesně v auditovaném rozsahu:

- odstraněn nepoužívaný `resolve_openable_document_pdf`,
- odstraněn nepoužívaný launcher helper `wait_until_ok`,
- odstraněny `write_reminders_store` a `_write_reminders_store`, které obcházely
  novou transakční cestu a neměly klienta,
- odstraněny dva původně nalezené nepoužívané importy z `app/cockpit.py` a
  následně osiřelý import `atomic_write_json` z reminders store.

Výsledný diff aplikačního kódu má 2 upravené importní řádky a 39 odstraněných
řádků. Přímé hledání nepotvrdilo žádnou zbývající referenci. Syntax, cílených
20 launcher/reminders testů a celý Cockpit quality gate s 458 testy prošly.
Po kontrolovaném restartu mají lokální i Tailscale adresa stejný PID a code
stamp; oba pětibodové smoke checky prošly.

Kód je pushnutý v commitu `9192e53`. GitHub Actions Cockpit Quality Gate běh
č. 6 pro tento commit skončil úspěšně:
`https://github.com/Belisarius-Mila/PythonMF/actions/runs/29107547605`.

Aktuální `app/cockpit.py` má 22 439 řádků a 330 top-level funkcí. Starý
e-mailový parser, lokální Janička větev, pět podezřelých API cest a veškeré
explicitně zachované kompatibilní vrstvy zůstaly beze změny. Z původních 255
řádků funkčních kandidátů tak zůstává 227 řádků, které vyžadují samostatné
rozhodnutí nebo ruční ověření.

## Jak byla inventura provedena

1. Python AST mapa top-level funkcí, volání, importů a duplicit.
2. Kořeny dosažitelnosti: `run_cockpit_server`, top-level serverové třídy,
   produkční importy z `app/` a `scripts/` a modulové vazby.
3. Porovnání GET/POST dispatcherů, `COCKPIT_POST_ACTIONS`, HTML/JavaScript
   endpointů a přesných literálů v testech.
4. Mapa JavaScript deklarací, HTML `id`, `getElementById`, query selectorů a
   proměnných navázaných na DOM.
5. Samostatná kontrola hlavních VoiceBridge/persistence modulů a launcheru.

Nečetly se e-maily, dokumenty, Quick Notes, reminders, hlasové texty ani jiné
private obsahy. Neprobíhal browser smoke test ani volání měnících endpointů.

## 1. Prokazatelně používané nebo strukturálně konzistentní

### HTTP a UI

- Všech 67 POST endpointů má rizikovou kartu a karta odpovídá skutečnému
  handleru v `do_POST`.
- V UI nebyl nalezen endpoint bez odpovídající backend cesty.
- Stránky e-mailového archivu používají některé odkazy nepřímo: URL souborů
  vytváří backend v odpovědi a frontend čte hodnotu `url`. Nepřítomnost
  doslovného `/email-archive/file` v JavaScriptu proto není mrtvá cesta.
- `/email-processing/`, `/email-archive/` a `/lekarna-admin/` jsou aktivní přes
  katalog webových aplikací, i když nemusí být doslova ve statickém HTML.
- `/janicka-kucharka/` má přímou UI vazbu.

### JavaScript a DOM

- `EMAIL_ARCHIVE_HTML`: 7 deklarovaných funkcí, žádná definition-only, žádný
  chybějící DOM cíl.
- `EMAIL_PROCESSING_HTML`: 45 deklarovaných funkcí, žádná definition-only,
  všech 28 HTML `id` má přímou JavaScript vazbu.
- `COCKPIT_HTML`: 251 klasických a 4 arrow funkce, žádná definition-only,
  žádné duplicitní funkce nebo `id` a žádný chybějící DOM cíl.
- Patnáct ID bez přímého `getElementById` není mrtvý kód: většinou jde o titulky
  používané přes `aria-labelledby` a statické panely. Jeden dynamický e-mailový
  identifikátor je očekávaný template string, ne statické HTML ID.
- Page-local duplicity `escapeHtml`, `renderDetail` a `returnToCockpit` jsou
  malé izolované helpery samostatných dokumentů. Nejde o runtime kolizi.

### VoiceBridge a persistence

V následujících modulech nebyla nalezena top-level funkce vyskytující se pouze
jako definice a nebyly nalezeny duplicitní definice:

- `app/speech/adam_voice_mode.py` — 39 funkcí,
- `app/speech/terminal_bridge.py` — 18 funkcí,
- `app/quick_notes.py` — 20 funkcí,
- `app/urgent_reminders.py` — 16 funkcí,
- `app/file_persistence.py` — 9 funkcí,
- `app/cockpit_code_stamp.py` — 2 funkce.

To neznamená, že jsou tyto moduly ideálně jednoduché; znamená to pouze, že
v nich tato statická kontrola nenašla jasně osiřelé top-level větve.

## 2. Legacy, které je stále potřeba zachovat

- `email_processing_legacy_item_id`, pole `legacy_id` a související lookupy jsou
  aktivní kompatibilní vrstva pro dříve uložená e-mailová rozhodnutí. Odstranění
  by mohlo vrátit zpracované položky do fronty nebo odpojit stará rozhodnutí.
- Starší potvrzovací věta při přesunu e-mailu do koše je přijímána vedle nové
  věty. Je to vědomá kompatibilita existujících rozpracovaných položek.
- Launcher fallback porty jsou aktivně testované a chrání start Cockpitu při
  obsazeném nebo neodpovídajícím výchozím portu.
- Janička „starý Adam fallback“ je v UI schovaný jako servisní cesta, ale je
  stále explicitně ovladatelný a testovaný. Není to mrtvá větev.
- `scripts/open_cockpit.py` exportuje alias `CODE_STAMP_PATHS`, který runtime
  přímo nečte, ale regresní test přes něj hlídá shodu launcheru se sdíleným
  manifestem. Nyní jej ponechat; případné odstranění až spolu s úpravou testu.
- Samostatný `urgent_reminders/index.json` je aktivní datová větev, nikoli
  historický zbytek. Míla ji ručně ověřil; chybí jí zamčená transakce, což je
  persistence riziko, ne důvod k odstranění.

## 3. Silné kandidáty na odstranění z Python kódu

Níže uvedené funkce nemají produkčního volajícího v repozitáři. Celkem jde o
255 řádků funkcí. Před odstraněním má vzniknout samostatná malá změna s testy;
tento audit nic nemaže.

### Starý textový e-mailový přehled — 137 řádků

- `parse_email_processing_items` (`app/cockpit.py:3381`)
- `latest_email_processing_overview` (`app/cockpit.py:3708`)

Větev parsuje starý soukromý týdenní Markdown přehled. Aktuální
`/api/email-processing/overview` vrací prázdný pracovní stav a nové položky se
načítají přes providerové hlavičky a Work Queue. Obě funkce volají jen jedna
druhou a přímé unit testy; produkční endpoint je nepoužívá.

Klasifikace: silný legacy kandidát. Odstranit pouze společně s odpovídajícími
historickými testy a po potvrzení, že starý Markdown import už nemá být ruční
recovery vstup.

### Staré Janička lokální odpovědi — 90 řádků

- `janicka_chat_memory_context` (`app/cockpit.py:11457`)
- `janicka_quick_note_chat_answer` (`app/cockpit.py:11486`)
- `_latest_quick_note_number_from_history` (`app/cockpit.py:11516`)
- `_format_janicka_quick_note_summary` (`app/cockpit.py:11527`)
- `_format_janicka_quick_note_detail` (`app/cockpit.py:11543`)

Současný `janicka_chat_action` předává dotaz spravované Samantha/Adam službě a
tyto lokální zkratky nevolá. `janicka_chat_memory_context` drží jen přímý unit
test; Quick Notes větev nemá produkčního volajícího ani přímý test hlavní
funkce.

Klasifikace: silný kandidát celé větve. Před odstraněním jednou ručně ověřit
Janička light chat a dotaz na Quick Notes, protože současná služba musí umět
stejný uživatelský záměr bez tohoto lokálního fallbacku.

### Nahrazený PDF resolver — 12 řádků

- `resolve_openable_document_pdf` (`app/cockpit.py:7076`)

Funkce nemá žádného volajícího ani test. Aktivní cesty používají obecnější
`resolve_openable_document_file`, který podporuje PDF i obrázky.

Klasifikace: velmi silný kandidát na přímé odstranění.

### Launcher helper — 6 řádků

- `wait_until_ok` (`scripts/open_cockpit.py:249`)

Nemá volajícího ani test. Aktivní launcher používá stabilnější
`wait_until_ready`, který vyžaduje dva po sobě jdoucí úspěchy.

Klasifikace: velmi silný kandidát na přímé odstranění.

### Nevyužitá full-replacement reminders API — 10 řádků

- `write_reminders_store` (`app/reminders/store.py:161`)
- `_write_reminders_store` (`app/reminders/store.py:168`)

Obě funkce volají pouze jedna druhou; nemají produkčního ani testového klienta.
Aktivní zápisy reminders používají zamčené transakce. Veřejný full replacement
by navíc obcházel nový read-modify-write invariant.

Klasifikace: velmi silný kandidát na odstranění obou funkcí společně.

### Nevyužité importy

- `DELETE_CONFIRMATION_PHRASE` v `app/cockpit.py` — import není v modulu čten.
- `COCKPIT_CODE_STAMP_PATHS` v `app/cockpit.py` — import není v modulu čten;
  `cockpit_code_stamp()` používá vlastní sdílený default.

Klasifikace: velmi silní kandidáti. Nezaměňovat druhý import s testovaným
launcher aliasem `CODE_STAMP_PATHS`, který je popsán výše.

## 4. API kandidáti, které ještě nelze označit za bezpečně mrtvé

Tyto cesty nemají aktivní odkaz v současném UI. Repozitář však neobsahuje
registr externích Shortcuts, bookmarků a ručních klientů, takže samotná absence
frontendového literálu nestačí k odstranění.

### Pravděpodobně nahrazené GET endpointy

- `GET /api/voice-mode/safe-readonly` — UI má allowlist napevno a volá jen
  `POST /api/voice-mode/safe-readonly/run`.
- `GET /api/dev-runner/actions` — UI má tři tlačítka napevno a volá jen
  `POST /api/dev-runner/run`.

Obě metadata funkce mají přímé unit testy, ale přesná GET cesta není v UI ani v
testu dispatchingu. Kandidát: endpoint a metadata wrapper; vlastní allowlisty a
POST run handlery jsou aktivní a musí zůstat.

### Pravděpodobně nahrazené POST endpointy

- `POST /api/samantha/open`
- `POST /api/codex/open`
- `POST /api/documents/open`

První dvě cesty nemají UI ani přímé funkční testy. Dokumentová cesta má test
bezpečného lokálního otevření, ale současné UI používá browser reader přes
`/documents/read` a `/documents/pdf`.

Kandidát: nejdřív potvrdit, že tyto tři cesty nepoužívá macOS Shortcut, starý
dashboard nebo servisní bookmark. Bez tohoto ověření jde o „nejasné“, ne o
schválené odstranění.

## 5. Testové a architektonické mezery odhalené inventurou

### GET cesty nemají obdobu POST registry

POST registry je úplná a strojově ověřitelná. GET dispatcher je stále ruční
řetězec podmínek. Doporučený budoucí krok je malý `COCKPIT_GET_ROUTES` manifest
nebo alespoň generovaný kontraktní test, který oddělí:

- HTML stránky,
- read-only JSON,
- bezpečné file response,
- dynamickou `/local-apps/` větev.

### Přesný route literál chybí v testech u 25 ze 109 cest

To neznamená 25 netestovaných funkcí: řada handlerů má přímé unit testy nebo je
odkazována nepřímo. Znamená to, že změna samotného dispatch stringu nemusí být
zachycena. Mezi důležitější mezery patří některé Library, Email Archive,
Documents lifecycle/classification, VoiceBridge marker a Lekarna manifest
retry cesty. Root a HTML stránky nebo backendem generované file URL tvoří
samostatnou, méně závažnou část tohoto seznamu.

### Testy mohou udržovat produkčně nedosažitelnou větev

Starý e-mailový Markdown parser a `janicka_chat_memory_context` mají přímé testy,
ale nemají produkčního volajícího. Test sám proto není důkazem potřebnosti.
Budoucí cleanup má u každé takové položky nejdřív určit vlastníka a recovery
účel, ne pouze zachovat kód proto, že je zelený test.

### Monolit zůstává hlavní riziko

Statická HTML/JavaScript kontrola je nyní čistá, ale 368 kB hlavního HTML stringu
a 22 tisíc řádků Pythonu ztěžuje přesnou analýzu scope, browser testování i
bezpečné odstraňování. Inventura podporuje původní roadmapu postupného rozdělení,
nikoli jednorázový přepis.

## Doporučené pořadí případné realizace

1. **Cleanup R1 bez změny chování — hotovo:** odstraněny auditované helpery a
   tři nepoužívané importy; quality gate i oba smoke checky prošly.
2. **Cleanup R2 s ručním retestem:** ověřit Janička light chat + Quick Notes a
   odstranit pětifunkční lokální Janička větev, pokud služba záměr pokryje.
3. **Cleanup R3 po rozhodnutí o recovery:** potvrdit, zda se ruší import starého
   týdenního Markdown e-mailového přehledu; potom odstranit parser, overview a
   jejich historické testy.
4. **API deprecation kontrola:** výslovně projít externí Shortcuts a servisní
   launchery pro pět podezřelých endpointů. Teprve poté odstranit cestu, registry
   kartu, handler a test jako jeden atomický balík.
5. **Navazující persistence krok — hotovo:** samostatný urgent-reminders index
   je zamčený a krytý dvouprocesovými testy. Cleanup R2/R3 a API deprecation
   mohou počkat na příslušné ruční nebo recovery rozhodnutí; další persistence
   oblastí jsou dokumentové registry po malých skupinách.

## Rizika a hranice závěru

- Dynamické Python callbacky a jména předávaná řetězcem mohou statickou analýzu
  skrýt. U uvedených kandidátů byl proto proveden i textový průchod repozitářem.
- Externí klient mimo git může používat endpoint, i když v projektu není odkaz.
- Analýza neprokazuje browserové chování; pouze konzistenci deklarací a vazeb.
- Žádný kandidát v tomto reportu není souhlasem k mazání. Každá implementační
  dávka vyžaduje samostatné Milovo rozhodnutí a normální git checkpoint.
