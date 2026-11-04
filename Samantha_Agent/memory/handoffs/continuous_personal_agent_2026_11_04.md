# Průběžný osobní agent — první lokální backend

Nazev: Průběžný osobní agent pro e-maily a Apple/iCloud kalendář
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-11-04

## Co se řešilo

Po diskusi celkového návrhu Míla určil e-maily a kalendář jako první prioritu
a souhlasil se zahájením vývoje. Celé zprávy mají být průběžně čtené a
obsahově posouzené agentem. Agent připravuje návrhy odpovědi a uložení,
metadata volí podle obsahu a ukládá až po potvrzení. Nevracet předem
odsouhlasený rozsah čtení k potvrzování jednotlivých zpráv.

## Co je hotové lokálně

- Třetí vývojový krok 2026-11-04 18:55 CET: editor má Odeslat a druhé
  potvrzení přesného příjemce, účtu, předmětu a konečného textu. První
  tlačítko pouze připraví potvrzení; SMTP se volá až po druhém.
- Odpověď respektuje jednoznačné Reply-To (jinak From), přidává vlastní
  Message-ID a návaznost In-Reply-To/References. Použije zdrojový účet;
  změna účtu, příjemce nebo textu původní potvrzení zneplatní.
- Stav `sending` se persistuje před síťovým pokusem. Úspěšné SMTP přijetí
  zůstává platné i při chybě QUIT nebo ukládání kopie do Odeslané pošty.
  Nejistý/přerušený pokus se automaticky neposílá znovu. Opakované i souběžné
  potvrzení nevytvoří druhé odeslání; jiné karty lze mezitím vyřizovat.
- Karta se po archivaci zachová, pokud ještě čeká navržená odpověď. U již
  uložené zprávy lze měnit pouze koncept odpovědi, ne přepisovat archivní
  metadata. Uložené zprávy zůstanou v historii i po místním vyřazení karty.
- 64 cílených scénářů PASS včetně falešného SMTP, HTTP cest a JS editoru.
  Žádný živý SMTP/IMAP ani placený model se při této přejímce nevolal.
  Plná Cockpit brána 2337 testů PASS; důkaz v
  `logs/continuous_email_reply_gate_20261104.log`.

- Druhý vývojový krok 2026-11-04 18:29 CET: hodinový plánovač 7:00 až 22:00
  v Europe/Prague, včetně ranní návaznosti na večerní pozici, dočtení celé dávky
  po stránkách a pokračování po výpadku. Dokončená hodina se znovu neposuzuje.
- První aktivace hodinového plánovače vyžaduje explicitní výchozí pozici
  schránek. `initialize_from_now` načte pouze UIDVALIDITY/UIDNEXT, nikoli
  historii těl; zatím nebyl živě spuštěn. Produkční vstup má používat
  `HourlyEmailScheduler`, nikoli nízkoúrovňový intervalový testovací cyklus.
- `CodexEmailProposer` podporuje Mílou zvolenou Terru přes existující lokální
  App Server socket, oddělené dočasné vlákno a strukturovaný výsledek.
  Živý model se v této etapě nevolal a centrální role/config se neměnily.
- Lokální stránka `/emails-to-resolve/` má vstup v nabídce Komunikace:
  důležité zprávy jako jednotlivé karty se záhlavím, shrnutím, důvodem,
  celým tělem a agentními metadaty; ostatní jako jeden řádek za kontrolní
  hodinu s datem, časem, odesílateli a předměty.
- Akce Ignorovat / Smazat z Cockpitu mění jen místní stav. Ve schránce se nic
  nemaže a vyřazená identita se po restartu znovu nenabízí.
- Koncept odpovědi se otevírá ve vlastním editoru, lze upravit předmět a text
  a uložit novou verzi. Běžící kontrola ani automatická obnova stránky
  nepřepisují rozepsaný editor. Odesílání doplnil třetí lokální krok výše.
- Potvrzený místní archiv je napojený na kartu; před uložením se znovu načte
  očekávaný zdroj. Přerušené uložení má v kartě možnost opětovného ověření.
- 42 cílených scénářů PASS: hodinové hranice včetně letního času, noční
  návaznost, stránkování, chyby, místní vyřazení, HTTP a JS editor/obnova.
  Plná Cockpit brána 2315 testů PASS; důkaz v
  `logs/continuous_email_hourly_gate_20261104.log`. Starší důkaz 2293 níže
  patří prvnímu backendovému milníku.
- Vizuální browser QA je otevřená: ovládací host prohlížeče v této relaci
  hlásil nedostupnost. Izolovaný syntetický HTTP náhled byl korektně ukončen;
  živý Cockpit nebyl restartovaný ani nasazený.

- Průběžný Python cyklus nezávislý na otevřeném Cockpitu, s možností ukončení.
- iCloud a Seznam vstup používá `BODY.PEEK[]`, úplný MIME obsah a identitu
  účtu, složky, UIDVALIDITY a UID. Zprávy se netřídí starými heuristikami.
- Nová cesta neomezuje počet znaků textu ani HTML. Dosavadní náhledové cesty
  zůstaly beze změny. Původní EML zachovává i vložené přílohy.
- Trvalý stav návrhů, postup po dávkách, viditelné chyby zdroje a přerušené
  modelové pokusy bez automatického opakování placeného posouzení.
- Strukturovaný modelový návrh shrnutí, reakce a metadat; upravitelný návrh
  dostává nový otisk. Úplný zdroj se před potvrzeným uložením znovu ověřuje.
- Potvrzený lokální archiv zachovává EML a přesná agentní metadata.
  Zveřejnění připravené složky je atomické; hotový archiv lze po přerušení
  převzít podle účtenky bez další kopie.
- Registrované workflow `continuous_email_agent_status` a
  `continuous_email_agent_synthetic_test`. Status je čtecí, test používá
  dočasná umělá data a falešný model. CLI nemá živý aktivační vstup.
- První milestone: 20 cílených syntetických testů PASS, samostatná regrese dosavadních iCloud
  a Seznam providerů 17/17 PASS. Plná Cockpit brána 2293 testů PASS včetně
  nového modulu, syntaxe Python/JS/shell a whitespace; bez změn živých služeb.
- Míla osobně potvrdil iCloud synchronizaci kalendáře na Macu i iPhonu.

## Co není hotové

- Terra je Mílou zvolená. Zbývá provozní cenové posouzení/pilot, centrální
  modelový profil a skutečná přejímka kvality odpovědí a metadat.
- Živá SMTP/IMAP přejímka na konkrétní schválené testovací zprávě a příjemci;
  syntetická přejímka odesílacího kódu není důkaz skutečného doručení.
- Ruční audit nejistého odeslání podle původního Message-ID. Automatický
  retry není povolený; UI jej při nejistotě nenabízí.
- Ruční pokračování neúspěšného modelového posouzení a odložení karet.
- Import příloh do dokumentového vaultu a zobrazení nového archivu ve
  stávajícím archivním UI. První archiv je zatím samostatný lokální výsledek.
- Kalendářový adaptér, instalace `caldav`, připojovací a synchronizační test.
- Instalační/aktivační workflow, LaunchAgent a fyzická přejímka obnovy služby.
- Upozornění na iPhonu jen při nových důležitých zprávách. Text má být
  „Zkontroluj e-maily v Cockpitu“. Cockpit se otevře klepnutím na oznámení;
  samovolné otevření přes jinou aplikaci se neslibuje. Specifický tón a
  konkrétní notifikační cesta ještě vyžadují výběr a zkoušku na telefonu.
- Míla výslovně odložil p+n na později. Lokální vývoj není instalací ani
  zapnutím hodinového provozu; součástí této etapy není skutečné odesílání.
- Nový samostatný pracovní proud ani nový TVBCP nebyly domluvené či založené.
  Tento terminálový krok je zapsán u existující e-mailové oblasti; před
  převzetím do Human–Adam musí být určena schválená kanonická vazba.

## Další krok

Připravit centrální modelový profil Terry s provozním posouzením a dohodnout
konkrétní zprávu/příjemce pro řízený živý pilot. Poté notifikace a kalendář;
p+n ani hodinový provoz se bez dalšího pokynu nespouští.

## Navrhované další kroky

- CalDAV připojení ke stejnému iCloud kalendáři, který už používá iPhone.
- Přejímka kvality metadat, ne pouze jejich syntaktické správnosti.
- Instalace nepřetržité služby až po funkčním průchodu a ověření po restartu.

## Rizika a důkazy

- Nízkoúrovňový scan bez kurzoru začíná nejstarší zprávou; hodinový vstup
  takovou neinitializovanou schránku odmítne. Budoucí aktivace musí vytvořit
  výchozí pozice bez nechtěného zpracování celé historie a stanovit rozpočet.
- Dlouhý e-mail se nezkracuje. Překročení kontextu modelu vede k viditelné
  chybě; dělené posouzení extrémně dlouhých zpráv zatím implementované není.
- Těla důležitých zpráv jsou zatím součástí místního JSON stavu karet.
  Před trvalým provozem ověřit odezvu přehledu na větší dávce; případné
  samostatné úložiště těl a stránkování odvodit z výsledku tohoto měření.
- Výsledek jednotlivého modelového pokusu je synteticky ověřený adaptérem,
  nikoli skutečným placeným modelem. Živé e-maily ani kalendář se při testech
  nečetly a nic nebylo odesláno, instalováno, publikováno nebo nasazeno.
- Projektový Python je `3.12.0rc3`; stabilní prostředí služby je doporučená
  příprava před trvalým provozem. Současné závislosti prošly `pip check`.
- Předchozí kontrola zálohy: poslední úspěch 2026-10-30; nová záloha se v této
  etapě nespouštěla. Aktuální stav vždy znovu ověřit registrovaným reportem.

## Relevantní soubory

`continuous_agent.py`, `continuous_source.py`, `continuous_email_agent.py`,
`test_continuous_email_agent.py`, `icloud_provider.py`, `commands.py`,
`cockpit_quality_gate.py`, `email_readonly_oauth.md`, `hourly_agent.py`,
`codex_proposer.py`, `cockpit_email_agent.py`, `agent_reply.py`,
`test_agent_reply.py`, `frontend/email_agent/`.

## Bezpečnost / neukládat

Do Git zápisů patří pouze technický a redigovaný stav. Živý obsah a přístupy
nepatří do tohoto handoffu; provozní data jsou pod ignorovaným `data/private/`.
