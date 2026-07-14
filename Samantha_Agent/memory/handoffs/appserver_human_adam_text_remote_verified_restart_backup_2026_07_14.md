Nazev: Human–Adam – ověřená vzdálená textová práce před restartem a zálohou
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-14

Co se resilo:

- Přechod běžné komunikace a vzdáleného vývoje na jedno kanonické app-server
  vlákno obsluhované rozhraním Human–Adam v Cockpitu.
- Bezpečný izolovaný workspace, WIP checkpoint, audit přesných cest, plná brána,
  fast-forward na `main`, push, řízený restart a návrat do stejného vlákna.
- Opravy vyčištění textového vstupu, krátkých názvů souborů, prostředí Pythonu a
  Node.js při nasazení, viditelné trvalé účtenky a barev nasazovacích tlačítek.

Co je hotove:

- Vzdálený end-to-end vývoj a samoobslužné nasazení byly opakovaně ručně
  potvrzeny na iPhonu.
- Neúspěšná brána je fail-closed a nemění `main`; úspěšné nasazení vyžaduje
  fast-forward, push a čisté zarovnání workspace.
- Trvalá účtenka se zobrazuje jen pro stav `deployed`, ve stejném vlákně a ve
  sticky hlavičce. Mezistav se jako úspěch nikdy nezobrazuje.
- Poslední nasazený bod je `5bac508`; lokální `main`, `origin/main` a izolovaný
  workspace jsou zarovnané. Tracked workspace je čistý.
- Poslední plná brána prošla: 703 testů. Autosave watcher běží v jediné instanci
  a před handoffem měl čerstvý snapshot.

Co neni hotove:

- Recovery záloha je zastaralá; poslední úspěšná je z 2026-07-09. Externí disk se
  dříve téhož dne po USB varování v macOS vůbec neenumeroval.
- Není implementována časomíra a bezpečně viditelný průběh dlouhého tahu.
- Nová hlasová vrstva stejného app-server vlákna ještě nezačala.
- Legacy VoiceBridge/watcher zůstává zmrazený; zatím se nemaže.

Dalsi krok:

1. Restartovat Mac.
2. Novou terminálovou relaci spustit přes `samantha`, ne holým `codex`.
3. Spustit `backup_status.py` a read-only ověřit, zda se externí disk enumeruje a
   je dostupný očekávaný recovery cíl.
4. Pokud je disk normálně připojený, spustit existující kanonický recovery backup
   workflow a ověřit nový úspěšný stav. Pokud disk stále není vidět, neprovádět
   mount, First Aid, inicializaci ani mazání; nejdřív jiný datový kabel, přímý
   port a stabilní napájení.
5. Po záloze ověřit Cockpit, stejné Human–Adam vlákno, Git a účtenku.

Navrhovane dalsi kroky:

- Nejprve doplnit klientskou časomíru dlouhého tahu a jednoznačný stav po návratu
  stránky bez periodického blikajícího refreshování a bez opakovaného odeslání.
- Potom přidat hlasový vstup: nahrát, přepsat, zobrazit k editaci a výslovně
  odeslat stejnou kanonickou textovou cestou; žádné TTY ani watcher doručování.
- Následně přidat explicitní přehrání odpovědi a až po opakovaných testech
  rozhodnout o odstranění starých komunikačních větví.

Zmenene nebo relevantni soubory:

- `memory/tvbcp/architektura_komunikace_samantha.txt`
- `app/communication/human_adam_service.py`
- `app/communication/human_adam_deploy.py`
- `app/communication/human_adam_ui.py`
- `app/communication/session_hub.py`
- `scripts/human_adam_takeover.py`
- `scripts/cockpit_quality_gate.py`
- `memory/projects/samantha_external_backup.md`
- `memory/handoffs/external_backup_disk_usb_not_detected_2026_07_14.md`

Bezpecnost / neukladat:

- Neukládat obsah konverzací, celý identifikátor vlákna, soukromé cesty, tokeny,
  klíče ani obsah private dat.
- V živém repozitáři zůstává jeden původní untracked uživatelský soubor; zachovat
  jej a neuvádět jeho název v handoffu.
- Soubory `data/session_autosave/` nikdy necommitovat.
