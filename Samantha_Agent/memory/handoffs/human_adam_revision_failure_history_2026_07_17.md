Nazev: Human–Adam – ochrana revize kotvy a redigovaný registr selhání
Priorita: 1
Stav: čeká na retest
Pripomenout pri startu: ano
Datum: 2026-07-17

Co se resilo:

- Ochrana soukromé kontextové kotvy proti přepsání novější revize ze starší
  otevřené karty na Macu nebo iPhonu.
- Trvalá postmortem stopa neúspěšných fází auditu a nasazení, kterou pozdější
  úspěšný pokus nesmaže.

Co je hotove:

- Každá změna kotvy posílá očekávanou revizi a server ji kontroluje uvnitř
  atomické zamčené transakce.
- Stará karta při konfliktu nic nepřepíše, zachová rozepsaný návrh a vyžádá
  výslovné obnovení aktuálního stavu.
- Human–Adam a Knihovna mají oddělený soukromý registr posledních 20 selhání.
- Registr ukládá pouze čas, profil, úplný WIP commit, fázi a povolenou kategorii
  chyby. Neukládá chybovou zprávu, log, zdrojový text, thread ID ani cestu.
- Zachyceny jsou audit, quality gate, receipt, vzdálená kontrola, push,
  fast-forward, zarovnání workspace a restart.
- Rozlišené bezpečné typy zahrnují syntaktickou chybu, neúspěšný test, timeout,
  procesní chybu brány a chybu konkrétní fáze nasazení.
- Úspěšné nasazení starší záznamy nemaže; zápis registru je atomický a omezený.
- Cílená sada 84 testů prošla.
- Plná Cockpit quality gate prošla: 764 testů, Python/JavaScript/shell syntaxe a
  `git diff --check` jsou v pořádku.
- Implementace, testy a tento handoff jsou součástí jednoho potvrzeného Git
  checkpointu na `main` a mají být pushnuté na `origin/main`.

Co neni hotove:

- Nový checkpoint ještě nebyl nasazen do běžícího Cockpitu ani živě otestován na
  Macu a iPhonu.
- Historický registr se záměrně nezobrazuje v UI; je to soukromá provozní stopa
  pro bezpečnou diagnostiku. Sticky diagnostika poslední fáze zůstává beze změny.

Dalsi krok:

- Řízeně nasadit checkpoint, restartovat Cockpit a ověřit běžný krátký tah.
- Na Macu a iPhonu otevřít stejnou kotvu, uložit novější revizi na jednom zařízení
  a potvrdit, že starší karta na druhém zařízení dostane konflikt bez přepsání.

Navrhovane dalsi kroky:

- Registr pouze pozorovat při prvním přirozeném selhání; nevyrábět kvůli němu
  záměrně rizikový neúspěšný push nebo restart.
- UI přehled historie přidávat jen tehdy, pokud terminálová postmortem stopa v
  praxi nebude stačit.

Zmenene nebo relevantni soubory:

- `human_adam_deploy.py`
- `human_adam_profiles.py`
- `human_adam_service.py`
- `human_adam_ui.py`
- `test_human_adam_deploy.py`
- `test_human_adam_profiles.py`
- `test_human_adam_service.py`
- `test_human_adam_ui.py`

Bezpecnost / neukladat:

- Neukládat obsah kotvy, celý chat, chybové zprávy, gate logy, thread ID,
  soukromé cesty, tokeny ani privátní data do Git registru nebo handoffu.
- Soubory registru patří pouze do `data/private/communication/` mimo Git.
- Při konfliktu revize neprovádět automatické sloučení ani opakovaný zápis.
