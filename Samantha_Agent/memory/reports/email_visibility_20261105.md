# Samostatné nezobrazování nedůležitých e-mailů

Datum: 2026-11-05. Proud: project-email-cases. Autor: Will.

Míla schválil vývoj a bezprostřední Terra p+n. U důležitých karet zůstává
„Příště nedůležité“; u jednotlivé zprávy ostatní pošty nově „Příště
nezobrazovat“. Vedle předvoleb důležitosti je samostatný seznam pravidel
nezobrazování s možností zrušení.

Pravidlo je výslovné, vratné a omezené na účet, přesnou adresu a podobný
předmět. Ukládá se atomicky v doplňujícím visibility_preferences společného
soukromého repository. Dvojklik nevytváří druhé pravidlo. Nejednoznačná
adresa, předmět bez slov, neúspěšné posouzení ani důležitá karta pravidlo
nevytvoří. Klient dodává jen ID; důvěryhodná hlavička pochází z repository.

Přehled filtruje pouze status hourly_summary s výslovným important=false.
Vyřadí odpovídající starší i budoucí nedůležité zprávy z textu, messages i
ids hodinové skupiny. Prázdná hodina zmizí, nesouvisející zprávy zůstanou.
Po zrušení pravidla se dříve skryté řádky obnoví. Důležité karty, archivní
účtenky, chyby posuzování a upravené odpovědi filtr nepotlačuje.

Žádné mazání ani přepis položek, návrhů, UID kurzorů, modelových verdiktů,
notifikací nebo schránky. Staré importance_preferences se nepřevádějí.
Posuzování dostává dál celé tělo a může budoucí podobnou zprávu označit
jako důležitou; ta se zobrazí. Nejde o filtr před modelem ani o úsporu jeho
volání. Žádný skutečný e-mail se při vývoji neposuzoval, neposílal či nemazal.

Implementace je v odděleném modulu visibility_preferences.py, Cockpit
adaptéru a frontendu. Dvě registrované POST akce mají capability záznamy.
Hodinový worker ani jeho modul continuous_agent.py se nemění; společné
repository zachovává doplňující pole. Živá služba má source_head ac9f3bed,
installed/owned/loaded/enabled=true. Její systémové přepnutí není potřeba.

## Ověření

- 54 funkčních Python testů PASS, včetně 7 nových doménových a 2 HTTP testů.
- 46 frontendových/capability/route kontraktů PASS.
- Node: rozlišené volby, dvojklik jedno pravidlo, bezpečný text, zachování
  důležité karty, zrušení pravidla a úplná regrese editoru/SMTP/Pushcut PASS.
- Plná brána: 2 528 testů, 2 497 PASS, 31 SKIP, bez selhání. Unit 511,548 s,
  celá unit fáze 516,8 s; syntaxe Python/JavaScript/shell a whitespace PASS.
- Logy: email_visibility_targeted_20261105.log,
  email_visibility_contract_20261105.log, email_visibility_full_gate_20261105.log.

Handoff, projektová paměť, index a aktivní projekt se dorovnávají ve stejném
kroku. Nový TVBCP nebyl domluvený ani založený; původní otevřená vazba zůstává
viditelná. Fyzické kliknutí na Macu/iPhonu není tímto automatickým testem
doložené. Konečná publikační účtenka: logs/email_visibility_release_20261105.log;
následný čtecí důkaz: logs/email_visibility_verified_20261105.log.
