Nazev: Autosave cleanup, realne misto na SSD a navazani po restartu
Priorita: 1
Stav: ceka na retest
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

Co neni hotove:
- Nebyl dolozen restart celeho Macu; posledni read-only `kern.boottime` stale
  ukazoval beh systemu od 2026-07-23.
- Po skutecnem restartu chybi nove mereni volneho SSD, VM/swap, otevrenych
  smazanych souboru, CloudKit cache a autosave stavu.
- Cockpit stale potrebuje opravit matematiku reportu: oddelit logickou velikost
  kandidatu, fyzicky alokovane bloky a skutecnou zmenu volneho mista pred/po.
- Mila chce po restartu Samanthy pripomenout aktualizaci
  `AuditCockpit56_Mila.txt`. V aktualnim checkoutu existuje pouze
  `AuditCockpit56.txt`; pred zmenou je nutne vyjasnit, zda ma vzniknout novy
  soubor s `_Mila`, nebo jde o stavajici roadmapu. Nic neprejmenovavat naslepo.

Dalsi krok:
- Po restartu Macu spustit `samantha` a hned Mílovi pripomenout:
  `Aktualizovat AuditCockpit56_Mila.txt.`
- Potom pouze read-only zmerit skutecne volne misto a stav autosave/VM/CloudKit.
- Teprve z noveho vychoziho mereni navrhnout a implementovat opravu matematiky
  Cockpitu.

Navrhovane dalsi kroky:
- Vyjasnit cilovy nazev auditniho souboru a doplnit do nej potvrzeny vysledek.
- V Cockpitu zobrazovat vedle logicke velikosti fyzickou alokaci a namereny
  rozdil volneho mista; testy nesmi vydavat logicky soucet za zarucene
  uvolnitelne GiB.
- CloudKit cache nemazat automaticky ani naslepo. Pripadny zasah resit jako
  samostatne rizikove rozhodnuti az podle noveho mereni.

Zmenene nebo relevantni soubory:
- `scripts/autosave_codex_session.sh`
- `scripts/autosave_status.py`
- `scripts/cleanup_session_autosave.py`
- `app/autosave_service.py`
- `AuditCockpit56.txt`
- `memory/technical/session_recovery_rules.md`

Bezpecnost / neukladat:
- Do handoffu, memory ani gitu neukladat obsah autosave relaci, soukrome cesty
  uvnitr CloudKit cache ani citlive texty.
- Zadny dalsi cleanup, mazani cache nebo systemovy zasah bez noveho presneho
  rozsahu a odpovidajiciho potvrzeni.
- `data/session_autosave/` nikdy necommitovat.
