# Editace kalendáře — ověření upozornění a obnova přístupu

Stav 2026-11-10 10:58 CET. Prioritní bug nahlásil Míla během potvrzení kompatibilního upgradu pošty a nasazení Datova commitu. Kanonický proud opravy `project-cockpit`; společný runtime dále obsahuje převzatý ScienceNews checkpoint `31a59e0c`.

## Prokázaná příčina a původní úprava

Nativní save původní operace proběhl jednou a za 0,32 s vrátil edit_unknown. Nebyl to timeout. Přehled se později sám obnovil, ale Python záznam unknown správně dál blokoval jiné mutace. Samostatný read-only inspect ověřil, že konkrétní změněná položka existuje a oba nativní identifikátory odpovídají uložené transakci.

Příčina je nyní doložená přímo novým read-backem: kalendář vrátil dvě stejná upozornění v opačném pořadí. Původní verifier porovnával serializované pole pořadově. Opravené ověření používá seřazenou multimnožinu časových hodnot upozornění (počet i duplicity zachované), všechna ostatní pole porovnává přesně. Přesná calendar/event/item identita, konkrétní obsah a čas výskytu, trvalý žurnál a zákaz druhého save zůstávají.

Nový helper pouze dočetl tutéž původní operaci: status edited_verified, calendar_writes=false, identity_matches=1, replacement_matches=1, preserved_fields_match=true, mismatch_fields=[], alarm_order_normalized=true. Původní operace má v žádostech stále jediný update; žádná druhá nativní mutace neproběhla. Pending/unknown je v okamžiku auditu 0. Doklad `logs/calendar_edit_native_live_recovered_20261110.log` a `logs/science_calendar_post_adoption_audit_20261110.log`; žádný soukromý název/obsah/poznámka ani kalendářové ID se neopisuje.

Dokumentace pro význam časových hodnot: [Apple EKAlarm.relativeOffset](https://developer.apple.com/documentation/eventkit/ekalarm/relativeoffset), [Apple EKCalendarItem.alarms](https://developer.apple.com/documentation/eventkit/ekcalendaritem/alarms). Konkrétní změna pořadí je vlastní živý důkaz, nikoli tvrzení o garantovaném pořadí z dokumentace.

## Oprava a oprávnění

- Swift kontrola normalizuje jen pořadí alarmů při porovnání současného obsahu i historického žurnálu. Změna skutečné hodnoty alarmu zůstává unknown; další save ani nová identita nejsou dovoleny. Diagnostika nativní účtenky obsahuje jen booleany, počty a názvy neshodných polí.
- Nové sestavení vyžádalo macOS grant. Jediná registrovaná authorize žádost pro přesný nový binární soubor byla skutečně potvrzena (full_access) a až potom proběhl read-only recovery. Karta čekání je vyčištěná. Žádná změna TCC databáze ani obejití oprávnění.
- Backend zachová nevyřešenou transakci při ztrátě oprávnění a vrátí needs_authorization. UI nabídne Povolit přístup na Macu a následně dočtení stejného request_id. UUID se při povolování nezapomene, nevyšle se nový update.
- Ověřovací lišta je viditelná i po scrollu dole ve viewportu a po ověření se skryje. Pořád se nesmí běžná nejistota vydávat za potvrzený výsledek.

## Ověření

- Nový skutečný Swift harness nad fake EventKit nejdřív FAIL při převrácení alarmů, po opravě PASS. Souběžně testuje reálnou změnu alarmu (stále unknown), nové legitimní editace, historii předchozích účtenek, opakovaný/detached výskyt, chybu/no-commit a nulový další zápis při recovery.
- 87 cílených Python/HTTP/JS/native testů PASS (20,724 s). SDK build a podpis skutečného helperu + self-test 7/7 PASS bez kalendářového zápisu.
- Skutečný headless Edge, syntetický HTTP fixture, viewport 390×844: viditelnost lišty po scrollu, oprávnění se zachováním UUID, read-only ověření stejné identity a dvě následné různé editace PASS. Test nezapisuje reálný kalendář. Screenshot byl zkontrolovaný; `logs/calendar_recovery_browser_receipt_20261110.log`.
- Společná plná brána PASS: 3406 testů / 31 SKIP (620,186 s); log: `logs/calendar_edit_recovery_full_gate_20261110.log`. Závěrečné UI vysvětlení navíc ověřeno 26 cílenými frontend/HTTP testy PASS (4,355 s) a znovu skutečným headless browserem; před commitem navazuje rychlá statická brána.

## Navazující nasazení

Míla dodal přesnou globální větu. Registrovaný upgrade vlastní hodinové služby 617f3e0d→publikovaný 8c83e93b proběhl před zveřejněním ScienceNews bindingu: business digest i všech 95 položek identické, nastavení/role zachované, health already_completed. Nový instalovaný parser úspěšně načetl nejprve kandidátní a po fast-forwardu i skutečný live JSON včetně ScienceNews; tím je dříve doložený blokátor uzavřen. Report `reports/email_science_role_upgrade_20261110.md`.

Po dokončení brány bude jeden lokální checkpoint opravy/provozního zápisu, zarovnání čistých profilů a společné zadané Terra p+n pro aktuální runtime. Výsledek publikace bude v `logs/science_calendar_release_20261110.log`; tento předpublikační zápis ho nepředjímá. Páteční služba a její rozpočet zůstávají vypnuté/neaktivované. Další skutečné uživatelské editace a fyzická Mac/iPhone přejímka zůstávají uživateli; oprava sama žádnou další položku kalendáře neměnila.
