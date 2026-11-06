# Kalendářový agent — čtecí EventKit pilot, bod 1

Datum: 2026-11-07 00:01 CET
Proud: průběžný osobní agent / project-email-cases. Terminálový Will, hlavní checkout.

## Výsledek

Původní dokument Samantha_navrh_rozvoje_a_kontinualni_agent_2026-11-04.txt ve Stazene
má na konci úplný sedmibodový návrh. Původních 49 873 B je přesně zachovaných;
připojeno 6 871 B, UTF-8 read-back PASS. Originál i append proof jsou soukromě
zachované mimo Git. Míla autorizoval zahájení pouze bodu 1 a poté v macOS povolil
přístup samostatné aplikaci.

Nativní čtecí helper se skutečně sestavil a prošel 4 syntetickými kontrolami.
macOS 15.8.2; AppKit/EventKit, bez nové Python závislosti a bez AI/modelového tahu.
Bundle ID com.samantha.calendar-readonly-pilot, lokální ad-hoc podpis ověřený codesign.
Sestavení a soukromé výsledky jsou ve vlastní aplikační složce uživatele, aby
launchd nezávisel na přístupu k chráněné Ploše. Starší pokus ve workspace zůstal
zachovaný, nic nebylo smazáno.

Skutečná jednorázová launchd zkouška PASS: parent_pid=1, vlastní job prokázaný
přes launchctl print, po výsledku odstraněna pouze tato dočasná úloha. Nebyl
zapsaný trvalý LaunchAgent, změněná stávající služba, resetované TCC ani událost.
Helper rozpoznal 8 kalendářů, z toho 4 iCloud,
a přečetl omezené sedmidenní období. Názvy/ID kalendářů zůstávají v soukromé
odpovědi; názvy, místa, poznámky ani těla událostí se neexportují vůbec.

Důležitý výsledek: přímý proces spuštěný z kontextu Codexu hlásil write_only;
stejná aplikace po výslovném macOS souhlasu přes LaunchServices a v samostatném
launchd procesu hlásí full_access. Přímý terminálový stav tedy není důkaz
oprávnění servisního helperu. Úspěšná cesta je Python → vlastní krátká launchd
úloha → podepsaný EventKit helper → korelovaný soukromý JSON výsledek.

## Hranice a oprávnění

Swift zdroj obsahuje pouze stav oprávnění, requestFullAccessToEvents, čtení
metadat kalendářů a omezený event query. Neobsahuje save/remove/reset ani zápisové
kalendářové API. Apple vyžaduje pro čtení plný přístup; tento pilot ho v kódu
omezuje na čtení. Žádost o OS přístup má trvalou identitu před GUI startem;
nejistý start se automaticky neopakuje. Výsledek ověřuje schéma, request ID,
operaci, bundle ID, čtecí režim, časové okno a agregované počty.

Přístup je ověřen pro toto konkrétní sestavení a běžný opakovaný start.
Při aktualizaci nativního binárního souboru je nutné znovu ověřit podpis a TCC;
přenos oprávnění mezi různými ad-hoc sestaveními není prokázaný. Skutečné
odebrání oprávnění v Nastavení nebylo provedeno; odmítnutí a chybějící oprávnění
ověřují syntetické testy. Synchronizace konkrétních událostí na iPhone ani
čtení/zápis z živého e-mailového workeru nejsou touto zkouškou potvrzené.

## Ověření

44 cílených Python testů PASS, 4 nativní syntetické kontroly PASS. Skutečný
GUI grant a launchd čtecí přejímka PASS. Plná brána 2683 testů, 31 SKIP,
bez selhání PASS (512,463 s unit část), logs/calendar_access_full_gate_20261106.log.

Zdrojový Swift SHA-256: 0e51a18adc9bb76fb4feb54bbceb5efe64238c0e6dd78b59c06999dcefe9a713
Nativní binární SHA-256: ead568d37b53d179fd2566bb8cf7194de2e0802bb4dcad659136520a255dd255

Bezpečné provozní důkazy: logs/calendar_access_build_20261106.log,
calendar_access_direct_probe_20261106.log, calendar_access_service_probe_20261106.log
a calendar_access_targeted_20261106.log. Soukromé žádosti/odpovědi a podpisový
manifest zůstávají jen ve vlastní aplikační složce, mimo Git.

## Další krok

Bod 2: vybrat čtené kalendáře pro kolize a jeden budoucí cílový kalendář;
připravit čtecí přehled. Automatické posuzování, zápis událostí, nový model,
rozšíření hodinové služby a p+n nebyly tímto vývojovým krokem aktivované.
Nový samostatný TVBCP nebyl domluvený a nevzniká.

## Registrované lokální vstupy

`calendar_access_pilot_status` je pouze stav bez čtení událostí. Sestavení,
GUI žádost, přímý diagnostický probe a nativní service-probe mají samostatné
potvrzované záznamy v app/workflows/commands.py a app/capabilities/registry.py.
CLI: `.venv/bin/python scripts/calendar_access_pilot.py <action> --confirmed`,
pro status se `--confirmed` nepoužívá. Akce: build, status, authorize, probe,
service-probe. GUI žádost nepřehrávat ani neresetovat při nejistotě. Service-probe
vytváří a odstraňuje jen vlastní jednorázovou user launchd úlohu, bez trvalé
instalace nebo zásahu do existujících služeb. Přímý probe z Codexu není přejímka
servisního čtení. Provozní integrace do Samanthy zůstává další etapou.
