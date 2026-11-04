# Průběžný osobní agent — nasazení a první živý pilot

Nazev: Průběžný osobní agent pro e-maily a Apple/iCloud kalendář
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-11-04

## Aktuální stav 2026-11-04 19:35 CET

- Po Mílově „jdi na to“ byl jedním syntetickým diagnostickým průchodem
  doložen skutečný důvod: HTTP 400 `invalid_json_schema`. Modelový výstup
  vyžaduje všechny vlastnosti v `required`; generované Pydantic schéma
  vynechávalo `important` a `reply_subject` kvůli místním výchozím hodnotám.
- `CodexEmailProposer` nyní pro výstup požaduje všechny kořenové vlastnosti.
  Lokální model a jeho výchozí hodnoty se nemění, staré návrhy zůstávají
  kompatibilní. Regresní test ověřil FAIL před úpravou a PASS po ní, včetně
  požadavků na vnořené objekty. Celkem 65 cílených scénářů PASS a rychlá
  statická Cockpit brána PASS (`logs/continuous_email_schema_static_20261104.log`).
- Následoval právě jeden nový živý pokus Terry/high nad stejnou úplnou
  iCloud zprávou se shodným otiskem. Modelový výsledek je potvrzený:
  důležitá zpráva, doporučené uložení, odpověď nenavržená. Karta je ve
  stavu `awaiting_confirmation`; živé API ověřilo 1 kartu, 0 hodinových
  řádků, 0 chyb a přesnou shodu návrhu i celého textu s výsledkem pilota.
- Původní selhání je zachované v `assessment_history` a první soukromé
  účtence. Nový pokus má samostatnou soukromou účtenku
  `pilot_20261104_2.json`; kurzor běžného zdroje nebyl posunutý.
  Nic se nearchivovalo ani neodeslalo a hodinová služba zůstala vypnutá.
- Potvrzená spotřeba tohoto nového pokusu: 28 463 vstupních tokenů,
  0 cached, 221 výstupních, 28 684 celkem; modelový tah 5 724 ms.
  Při ověřených Standard sazbách jde o 0,7392 kreditu, nikoli částku v Kč.
  Jeden vzorek není odhad celého provozu; před aktivací posoudit režii
  základních instrukcí/nástrojů, dávkování a další reálné zprávy.
- Oprava adaptéru je zatím pouze lokální. Nasazený Cockpit zůstává na
  `d9bf3a7c111a`; jeho již nasazené API a stránka čtou novou kartu ze
  společného soukromého stavu. V této navazující etapě se p+n neopakovalo.
- Skutečnou kvalitu důležitosti a metadat ještě musí přijmout Míla na kartě
  v Komunikace → E-maily k řešení. Živé odesílání/archivace ani fyzická
  browser/iPhone přejímka tím nejsou doložené. Trvalá role se neměnila.

## Předchozí milník 2026-11-04 19:27 CET

- Míla výslovně schválil pořadí „nejdříve terra p+n a pak řízený pilot
  Terry“. Původní odklad p+n níže je tím překonaný; trvalá aktivace schválená
  ani provedená není.
- Registrované p+n v proudu `project-email-cases` dokončila Terra/high:
  4 commity publikované a nasazené po `d9bf3a7c111a`. Účtenka
  `c3a38a12547115a5ed292a3826a9e70e`, plná brána 2337 PASS, smoke 5/5.
  Nezávisle ověřený vzdálený main, živý code stamp `deeec06862f3711e`
  a přesná shoda nasazené stránky E-maily k řešení se zdrojem.
  Bezpečný důkaz: `logs/continuous_email_release_20261104.log`.
- Následný jednorázový pilot načetl celý jeden nejnovější e-mail z iCloudu
  přes read-only IMAP a vyvolal právě jeden modelový pokus Terry/high přes
  nasazený adaptér. Žádný archiv, SMTP, notifikace ani běžící hodinová služba.
- Pilot neprošel: `CodexAppServerClient.send_text` skončil
  `AppServerContractError`: „Turn nebyl jednoznačně potvrzen jako doručený
  a dokončený.“ Není potvrzený návrh, klasifikace ani usage; nelze tvrdit,
  že model zprávu dokončil nebo že pokus nic nestál. Kořenová příčina není
  doložená; dostupné logy ji nerozlišily. Žádný automatický opakovaný pokus.
- Soukromý stav obsahuje právě jednu položku `analysis_failed`, žádnou
  kartu ani hodinový řádek; živé API ukazuje `assessment_errors=1`.
  Scheduler má `completed` pro dokončení vstupního průchodu, nikoli pro
  úspěch modelové analýzy. Jednorázový kurzor zůstal u vybrané zprávy;
  při další aktivaci jej nemazat ani nepřesouvat bez vědomého rozhodnutí.
- Soukromá účtenka a chyba jsou pod `data/private/continuous_agent/`;
  neobsahovat je v Git zápisech. Nová trvalá modelová role nevznikla:
  jednorázový pilot použil centrálně schválenou Terru/high, nikoli fallback.
- Oficiální Standard sazby byly znovu ověřené: 25 vstup / 1,25 cached /
  125 výstup kreditů za milion tokenů, https://learn.chatgpt.com/docs/pricing.
  Provozní odhad čeká na úspěšný pilot s doloženou spotřebou.
- Browser/iPhone přejímka zůstává otevřená. Důkazy HTTP a testy ji
  nenahrazují. Níže uvedené lokální milníky jsou historie před tímto vydáním.

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

- Terra je Mílou zvolená a jeden skutečný modelový průchod je potvrzený.
  Zbývá provozní posouzení, centrální modelový profil a skutečná přejímka
  kvality odpovědí a metadat na reprezentativních zprávách.
- Živá SMTP přejímka na konkrétní schválené testovací zprávě a příjemci;
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
- P+n je dokončené podle aktuálního stavu výše. Hodinový provoz není
  zapnutý; součástí této etapy nebylo skutečné odesílání.
- Nový samostatný pracovní proud ani nový TVBCP nebyly domluvené či založené.
  Tento terminálový krok je zapsán u existující e-mailové oblasti; před
  převzetím do Human–Adam musí být určena schválená kanonická vazba.

## Další krok

Mílova přejímka první skutečné karty a jejích metadat v Cockpitu. Pak
provozní modelový profil a rozpočet s ohledem na naměřenou režii; další
pilot musí být vědomě vymezený. Trvalá aktivace a další p+n zůstávají
samostatnými kroky.

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
- Původní syntetická přejímka adaptéru neodhalila neplatné strict schéma.
  Nyní je doložená reprodukce, oprava a jeden potvrzený živý výsledek;
  reprezentativnost a kvalita návrhů zatím přijaté nejsou.
  Kalendář se nečetl a žádný e-mail se neodeslal ani nearchivoval.
  Publikování/nasazení doložené výše není aktivací hodinového agenta.
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
