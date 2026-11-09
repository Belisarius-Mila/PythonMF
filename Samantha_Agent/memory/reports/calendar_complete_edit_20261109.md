# Splněno a Editovat v kalendáři Cockpitu

Stav 2026-11-09 20:46 CET: lokálně implementováno; bez push/nasazení. Kanonický proud `project-cockpit`, existující handoff i TVBCP aktualizované. Nový TVBCP nevzniká.

## Uživatelský výsledek

- Splněno v přehledu kalendáře i úvodní agendě trvale skryje konkrétní položku pouze v Cockpitu, včetně obnovení stránky/restartu. Událost v nativním kalendáři zůstává, nadále platí pro kontrolu kolizí. Opakování jiného dne zůstane viditelné. Backend umí soukromé označení i vrátit; samostatný seznam splněných se nezavádí.
- Editovat otevře předvyplněné okno s názvem, dnem/měsícem/rokem a časem Praha. Uložit změny upraví původní událost, Zrušit nic nezapisuje. Neplatný/dvojznačný čas zachová editovatelný formulář.
- Zachová se délka, kalendář, poznámky, místo, pásmo, URL a upozornění. Celodenní položka zachová počet kalendářových dní i přes DST. U opakování se upravuje pouze tento výskyt. Pozvánky s účastníky/organizátorem se nezasílají ani neupravují; použije se aplikace Kalendář.

## Technické hranice

Soukromé splnění sdílí atomické revizované označení agendy. Doménový CalendarOverview zůstává úplný; filtrování je jen na prezentačních API. Duplicitní/neaktuální obsah nedostane tlačítko k nejednoznačné změně. Vlastní editace přenese známý typ a případné soukromé označení na nový obsah.

Nový CalendarEdit helper má vlastní bundle/grant. Zdroj ani build původní čtečky, create-only writeru a delete helperu se nemění. Python trvale zaznamená původní identitu a změny před native voláním. Nativní fsync žurnál a přesný fingerprint opět ověří údaje před jediným save(.thisEvent); read-back vyžaduje shodu konkrétních ID a nezměněných ostatních údajů. Žádný create/remove.

Nejasný výsledek dovolí jen recovery původní identity. Pending/unknown přežije restart a blokuje jinou editaci i smazání; edit/delete navíc sdílí procesový zámek. Nové nativní ID po přesunu/detach nevytvoří retry slot. Když nelze výsledek doložit, následuje ruční servis, nikdy druhý zápis. Model se nevolá a obsah kalendáře se modelu neposílá.

## Ověření

- Cílené Python/HTTP/JS sady PASS: soukromé splnění, restart, opačné časové offsety, zrušení, duplicity, stale/revision/expiry, DST, jiné kalendáře, origin/query/confirmation, souběh a nejistý výsledek bez druhé mutace.
- Skutečný Swift transakční kód proti in-memory EventKit PASS: úprava/nezměněné poznámky a alarmy, replay/recovery, další platná editace se zachováním staré účtenky, změna mezi náhledem a save, pozvánka, unknown/no-commit a opožděný committed výsledek, recurring detach s novými ID a pouze thisEvent, recovery bez žurnálu.
- Izolovaný skutečný SDK build + ad-hoc podpis + self-test 7 kontrol PASS. Původní build manifesty beze změny. Bez žádosti o OS grant a bez otevření reálného kalendáře. `logs/calendar_edit_native_build_final_20261109.log`.
- Nativní testovací složky musely použít kanonický zápis Foundation po vytvoření (stejná /var vs /private/var vlastnost jako u předchozího delete harnessu). Produkční ochrany cest zůstaly přísné.
- Headless Edge, skutečný DOM a syntetický HTTP server: viewport 390×844, předvyplnění, Zrušit → znovu otevřít, editace původní fixture a skrytí přes Splněno PASS; bez vodorovného přetékání. Screenshot zkontrolovaný. `logs/calendar_edit_browser_receipt_20261109.log`. CUA browser host nebyl dostupný, použit izolovaný headless profil již přítomného Edge.
- Původní asset kontrakty se nezrušily; přepočítané jsou pouze dvě skutečně změněné stránky a očekávaný seznam modulů.
- Plná brána 3320 testů OK (31 SKIP), 667,751 s unit testů: `logs/calendar_edit_full_gate_20261109.log`. Cílené logy `calendar_edit_all_targeted_20261109.log`, `calendar_edit_frontend_final_20261109.log`, `calendar_edit_native_final_20261109.log`.

## Další krok a rizika

Samostatně potvrdit p+n. Po nasazení vybrat Editovat → Povolit úpravy na Macu a přijmout nový EventKit grant pro tento helper. Vývoj to neudělal za uživatele. Potom na Mílou vybrané položce ověřit název, datum/čas a iCloud synchronizaci, Splněno a zobrazení po restartu/na iPhonu. Do té doby jde o ověřenou implementaci a syntetické přejímky, nikoli skutečnou nativní mutaci ani fyzickou iPhone přejímku. Obsahy osobních událostí nejsou v reportu ani commitu.
