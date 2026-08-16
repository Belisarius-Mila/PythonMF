Nazev: Autosave cleanup, realne misto na SSD a navazani po restartu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-08-15

Co se resilo:
- `data/session_autosave/` znovu obsahovalo mnoho casovanych kopii jedne dlouhe
  Codex relace a SSD hlasilo malo volneho mista.
- Po Milove presne potvrzene globalni brzde probehl omezeny cleanup pouze
  casovanych autosave souboru.
- Nasledna kontrola vysvetlovala, proc odhad logicke velikosti neodpovidal
  skutecne zmene volneho mista na APFS.

Co je hotove:
- Smazano bylo 144 starych casovanych autosave souboru. Smazani je nevratne.
- Zachovano zustalo 12 nejnovejsich casu, tedy 12 JSONL a 12 TXT souboru, a
  vsechny soubory `latest`.
- Autosave adresar po cleanupu zabiral priblizne 1,30 GiB a dry-run hlasil nula
  dalsich kandidatu.
- Watcher byl rizene restartovan, bezel v jedine instanci, `latest` ukladal po
  deseti minutach a historicky par nejvyse jednou za hodinu.
- Bylo overeno, ze cleanup pocital odhad ze souctu logickych velikosti souboru.
  U APFS copy-on-write kopii to neni spolehlivy odhad fyzicky uvolnitelnych
  bloku ani skutecne zmeny `df`.
- Read-only rozpad ukazal, ze velkou samostatnou polozkou je CloudKit cache a
  dalsi promennou cast tvori VM/swap a otevrene jiz smazane soubory. Tyto udaje
  jsou casove promenlive a po restartu se musi znovu zmerit.
- CloudKit cache, iCloud data, APFS snapshoty ani jina data mimo omezeny autosave
  cleanup nebyla mazana.
- Restart Macu byl nasledne potvrzen a read-only mereni ukazalo vyrazny navrat
  volneho mista po poklesu docasne CloudKit cache a VM/swap. Autosave zustal
  priblizne na puvodni velikosti.
- Matematika autosave cleanupu je lokalne opravena: report oddeluje logickou
  velikost kandidatu, soucet fyzicky alokovanych bloku a skutecnou zmenu volneho
  mista namerenou pred a po potvrzenem uklidu.
- Dry-run uz neslibuje odhad uvolneni. Vyslovne uvadi, ze alokovane APFS bloky
  mohou byt sdilene a skutecny vysledek je znamy az po mereni.
- Cilenych sest testu a plna Cockpit Quality Gate 1414/1414 prosly. Realny
  dry-run hlasil nula kandidatu a nic nesmazal.

Co neni hotove:
- Opravena matematika zatim neni nasazena do beziciho Cockpitu; nasazeni,
  restart a zivy UI retest zustavaji samostatnou potvrzovanou akci.
- Rucni kontrola citelnosti tri metrik na Macu a iPhonu zustava otevrena.

Dalsi krok:
- Samostatne potvrdit nasazeni opraveneho reportu do Cockpitu a po restartu
  zive overit dry-run text bez skutecneho mazani.

Navrhovane dalsi kroky:
- Novy celkovy audit je samostatny `AuditCockpit56_2.txt`; Mílova drive
  uvazovana pracovni verze s `_Mila` neni relevantni.
- Po nasazeni rucne zkontrolovat citelnost tri oddelenych metrik na Macu i iPhonu.
- CloudKit cache nemazat automaticky ani naslepo. Pripadny zasah resit jako
  samostatne rizikove rozhodnuti az podle noveho mereni.

Zmenene nebo relevantni soubory:
- `scripts/autosave_codex_session.sh`
- `scripts/autosave_status.py`
- `scripts/cleanup_session_autosave.py`
- `app/autosave_service.py`
- `app/frontend/cockpit/app.js`
- `tests/test_cockpit.py`
- `tests/test_cockpit_frontend.py`
- `tests/test_safety_quick_checks.py`
- `AuditCockpit56.txt`
- `AuditCockpit56_2.txt`
- `memory/technical/session_recovery_rules.md`

Bezpecnost / neukladat:
- Do handoffu, memory ani gitu neukladat obsah autosave relaci, soukrome cesty
  uvnitr CloudKit cache ani citlive texty.
- Zadny dalsi cleanup, mazani cache nebo systemovy zasah bez noveho presneho
  rozsahu a odpovidajiciho potvrzeni.
- `data/session_autosave/` nikdy necommitovat.
