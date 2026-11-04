# Řízená instalace hodinového e-mailového agenta

Stav 2026-11-05: vývoj autorizovaný, systémová instalace zatím neprovedená.

## Připravený postup

1. Registrované prepare uvnitř ignorovaných private dat vytvoří kopii
   čistého commitnutého main, manifest, otisk plánu a vypnutou konfiguraci.
   Ověří schválený model v katalogu a připojený otestovaný Pushcut.
2. Install po přesné větě globální brzdy znovu ověří zdroj, roli, nastavení
   a otisk kopie. IMAP metadata ověří UIDVALIDITY, zachová existující iCloud
   pozici; Seznam začne od aktuálního konce bez čtení starých těl.
3. Kopie kódu vznikne v uživatelském Application Support/SamanthaEmailAgent/
   releases/HEAD. .env, private data a centrální role jsou odkazy na kanonický
   projekt. Python zůstává projektový venv. Živý vývoj nemění kopii kódu.
4. Vytvoří nový uživatelský LaunchAgents plist
   com.miloslavfalta.samantha.continuous-email; existující cíl/job nepřepíše.
   RunAtLoad, začátek hodiny, minutová kontrola, Prague, explicitní child PATH.
5. Bootstrap/enable/kickstart jen vlastního jobu; čekání na čerstvý heartbeat.
   Při chybě instalace vypne konfiguraci, vyloží vlastní job a ponechá
   data/runtime k servisní kontrole. Nejisté modelové pokusy neopakuje.
6. Verify-restart znovu nahraje pouze vlastní nepracující job a ověří nový
   heartbeat. Aktivní posouzení nepřeruší. Fyzický reboot Macu neprovádí.

Terra/high, iCloud i Seznam, všechny nové celé zprávy, 07–22 Europe/Prague.
Výchozí denní početní limit null; explicitní limit zůstává možný. Nedokončené
dávky navazují další minutu, dokončená hodina se neopakuje. Per-user služba
vyžaduje přihlášený účet; uspaný/vypnutý Mac nepracuje. Po wake/přihlášení
má navázat. Odeslání odpovědí a ukládání zůstává potvrzované v Cockpitu.

## Důkazy

- 67 cílených testů PASS: skutečný izolovaný Git, falešný launchctl/IMAP/model,
  zachování kurzorů, ochrana cizí služby, změny zdroje, chyby startu/obnovy,
  zámek aktivního posouzení, redigovaný heartbeat, více než 20 zpráv,
  potvrzovací brány registru a dosavadní Pushcut/role.
- logs/email_service_install_targeted_20261105.log
- logs/email_service_model_catalog_20261105.log: Terra/high, fallback=false,
  jen katalog, žádný placený modelový tah.
- logs/email_service_install_gate_20261105.log: plná brána 2403 PASS (377,5 s).
- Následný reálný čtecí audit odhalil zdvojený prefix `git archive` ve
  vnořeném projektu. Opravené relativní cesty, instalační fixture nyní
  kopíruje skutečné vnoření; 13 instalačních regresí PASS. Viz LL-096,
  logs/email_service_install_nested_regression_20261105.log. Finální plná
  brána v logs/email_service_install_gate_final_20261105.log: 2403 PASS (388,8 s).
- Readiness: role/socket dostupné, iCloud inicializovaný, Seznam ne;
  installed/loaded/enabled=false. Pushcut configured/enabled=true, accepted.
- Předchozí vydání b372355c: p+n 9f34b5d5fa3be12a0124646c4d353050,
  push/deployment confirmed, 2386 PASS, smoke 5/5, CI 41927780373 success.
  Míla přijal skutečné doručení Pushcutu i otevření Cockpitu klepnutím.

## Otevřeno

Systémová věta dosud nezadaná. Po ní nainstalovat a ověřit check/obnovu,
v provozním okně první ostrý průchod. Registrace launchctl není tento důkaz.
Míla následně výslovně schválil převzetí Datových commitů a společné p+n včetně oprav do čistého repozitáře. Nový TVBCP nebyl domluvený ani založený.
Servisní příkazy jsou registrované lokálně pro terminál. Jejich dostupnost
v dříve nasazené kopii registru Cockpitu bez dalšího p+n není potvrzená;
stávající karty a Pushcut používají sdílený kanonický private stav.
Záloha 2026-10-30 je starší než tři dny; nová se nespouštěla.
Python 3.12.0rc3 zůstává; update není součástí tohoto kroku.
Na napájení už je automatické uspání vypnuté (pmset sleep=0); neměnilo se.
CalDAV a živá přejímka archivních metadat jsou další samostatné kroky.
