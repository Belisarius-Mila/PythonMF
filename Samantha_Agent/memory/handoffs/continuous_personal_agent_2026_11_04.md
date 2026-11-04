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
- 20 cílených syntetických testů PASS, samostatná regrese dosavadních iCloud
  a Seznam providerů 17/17 PASS. Plná Cockpit brána 2293 testů PASS včetně
  nového modulu, syntaxe Python/JS/shell a whitespace; bez změn živých služeb.
- Míla osobně potvrdil iCloud synchronizaci kalendáře na Macu i iPhonu.

## Co není hotové

- Výběr konkrétního modelu a jeho provozního rozpočtu, skutečná přejímka
  kvality odpovědí a metadat na konkrétních e-mailech.
- Napojení návrhů a potvrzení do Cockpitu, odmítnutí/odložení a ruční
  pokračování neúspěšného modelového posouzení.
- Import příloh do dokumentového vaultu a zobrazení nového archivu ve
  stávajícím archivním UI. První archiv je zatím samostatný lokální výsledek.
- Kalendářový adaptér, instalace `caldav`, připojovací a synchronizační test.
- Instalační/aktivační workflow, LaunchAgent a fyzická přejímka obnovy služby.
- Nový samostatný pracovní proud ani nový TVBCP nebyly domluvené či založené.
  Tento terminálový krok je zapsán u existující e-mailové oblasti; před
  převzetím do Human–Adam musí být určena schválená kanonická vazba.

## Další krok

Dokončit modelový profil a první ručně řízenou přejímku skutečného e-mailu;
potom připojit návrhy do Cockpitu. Za hotového provozního agenta tuto verzi
nevydávat a automatiku nespouštět.

## Navrhované další kroky

- CalDAV připojení ke stejnému iCloud kalendáři, který už používá iPhone.
- Přejímka kvality metadat, ne pouze jejich syntaktické správnosti.
- Instalace nepřetržité služby až po funkčním průchodu a ověření po restartu.

## Rizika a důkazy

- První scan backendu začíná nejstarší dostupnou zprávou. Před aktivací je
  nutné určit výchozí rozsah/historii; nepouštět bez vymezení a rozpočtu.
- Dlouhý e-mail se nezkracuje. Překročení kontextu modelu vede k viditelné
  chybě; dělené posouzení extrémně dlouhých zpráv zatím implementované není.
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
`cockpit_quality_gate.py`, `email_readonly_oauth.md`.

## Bezpečnost / neukládat

Do Git zápisů patří pouze technický a redigovaný stav. Živý obsah a přístupy
nepatří do tohoto handoffu; provozní data jsou pod ignorovaným `data/private/`.
