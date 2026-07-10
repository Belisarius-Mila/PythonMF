# Cockpit persistence write map — 2026-07-10

## Rozsah a bezpečnost

Tato git-safe inventura mapuje runtime zápisy v `app/` podle zdrojového kódu.
Nečetla ani neopisuje obsah soukromých dokumentů, e-mailů, hlasových pokynů nebo
private vaultu. Jde o lexikální mapu zápisových míst, ne o migraci dat.

## Hlavní zápisové oblasti

- Cockpit provoz: HTTP event logy, servisní logy, pomocné command/marker soubory.
- VoiceBridge: status, poslední odpověď, pending stav, historie a potvrzovací
  karty v `app/speech/adam_voice_mode.py` a navazujícím Cockpit kódu.
- Dokumenty: JSON/JSONL registry, metadata, auditní rozhodnutí, fulltext a
  lifecycle události v `app/documents/`.
- E-maily: activity state, case indexy, archivní metadata, drafty a outbound
  provozní stav v `app/email/`.
- Připomínky: reminders store, query stav a platební case metadata v
  `app/reminders/`.
- Další runtime registry: článek/knihovna, Quick Notes, urgent reminders,
  backup activity state, Adam service a kvantitativní metriky.

## Potvrzené společné riziko

Přímé `write_text`, `open("w")`, `open("a")` a `json.dump` postupy nemají jeden
společný stabilní mezipo-procesový zámek. Samotné spuštění jedné Cockpit serverové
instance snížilo počet souběžných zapisovatelů, ale pomocné skripty a další
procesy mohou stále zapisovat do stejných runtime souborů.

Rizika jsou:

- částečný JSON při pádu během přepisu,
- ztracený read-modify-write update,
- promíchané nebo neúplné JSONL řádky,
- nesoulad mezi manifestem, indexem a navazujícím stavem.

## První implementovaný řez

Nová sdílená vrstva `app/file_persistence.py` poskytuje:

- stabilní sidecar `.lock` soubor a `fcntl.flock` mezi procesy,
- timeout místo neomezeného čekání,
- atomický text/JSON zápis přes dočasný soubor ve stejné složce,
- flush + `fsync` souboru, `os.replace` a best-effort `fsync` složky,
- zamčenou JSON read-modify-write transakci,
- zamčený JSONL append jednoho kompletního řádku.

První integrace je záměrně nízkoriziková:

1. `app/backup/activity_state.py` používá atomický zamčený JSON zápis.
2. Cockpit HTTP technický event log používá zamčený JSONL append s krátkým
   timeoutem; log zůstává best-effort a nikdy neobsahuje request payloady.
3. První VoiceBridge rollout převádí pouze čisté přepisy
   `adam_voice_mode_status.json` a `last_adam_response.json` na atomický zamčený
   JSON zápis. Pending stav, schvalování, historie JSONL a doručování se nemění.
4. Druhý VoiceBridge rollout převádí všechny přechody
   `pending_for_adam.json` na jednu zamčenou read-validate-modify-write
   transakci. Jiný aktivní pokyn vrací `pending_conflict`, stejná operace je
   idempotentní a historii zapisuje jen proces, který přechod skutečně provedl.
5. Třetí VoiceBridge rollout převádí oba zápisy
   `adam_voice_history.jsonl` na společný zamčený append. Seznam finálních a
   nefinálních rout zůstává beze změny; transportní mezistav proto nikdy
   neaktualizuje `last_adam_response.json`.
6. Hlavní `data/reminders/reminders.json` používá jednu zamčenou transakční
   funkci pro create-if-missing, změnu statusu, zrušení platební připomínky a
   doplnění dokumentových metadat. Duplicitní ID je idempotentní bez druhého
   replace.
7. Quick Notes `index.json` slučuje aktuálně pozorované soubory se stavem indexu
   uvnitř jednoho zamčeného read-modify-write cyklu. Dva refresh procesy proto
   neztratí záznam a nepřidělí stejné číslo různým poznámkám.

Existující soukromá data se nepřesouvají, nepřepisují dávkově ani nemigrují.

## Ověření

- Dva samostatné Python procesy provedou souběžně zamčené JSON
  read-modify-write operace bez ztracených aktualizací.
- Dva samostatné procesy appendují JSONL a každý očekávaný záznam zůstane právě
  jedním validním řádkem.
- Simulované selhání `os.replace` ponechá původní JSON beze změny a uklidí
  dočasný soubor.
- Integrační testy ověřují použití stabilního locku v backup state a Cockpit
  HTTP event logu.
- VoiceBridge testy ověřují lock i absenci temp souboru pro status a poslední
  odpověď; simulované selhání replace zachová předchozí status JSON.
- Po nasazení byl Voice Mode watcher bezpečně restartován bez pending pokynu,
  vrátil se do `listening`, zachoval terminálový bridge a živě vytvořil status
  lock. Relevantní sada má 413 testů OK.
- Dva procesy souběžně zakládající rozdílný pending mají právě jednoho vítěze;
  druhý aktivní pokyn nepřepíše. Dva procesy dokončující jeden pending vytvoří
  právě jednu finální historii a opakované stejné save/approval neprovede druhý
  replace.
- Živá idempotentní transakce nad skutečným zpracovaným pending stavem vytvořila
  stabilní lock a SHA-256 obsahu zůstal beze změny. Po tomto rolloutu prošlo 418
  relevantních testů, watcher `listening` a oba smoke checky.
- Dva skutečné procesy souběžně zapsaly 60 VoiceBridge history událostí jako 60
  samostatných validních řádků. Současná finální a transportní větev zachovala
  poslední odpověď z finální routy. Zamčení zajišťuje integritu řádků; samo o
  sobě není náhradou idempotentní pending transakce.
- Výslovný regresní test obou Cockpit vstupů potvrzuje invariant
  `watcher running => no inline delivery`. Po nasazení prošlo 420 relevantních
  testů, watcher se vrátil do `listening` a lokální i Tailscale smoke check byly
  kompletně zelené.
- Dva procesy současně přidaly 40 různých hlavních připomínek bez ztraceného
  záznamu. Při souběžném vytvoření stejného ID vyhrál právě jeden proces a druhý
  skončil idempotentně bez druhého replace.
- Dva procesy synchronizovaly dva Quick Notes inboxy do společného indexu:
  vzniklo 40 záznamů, 40 různých source cest a přesně čísla 1 až 40.
- Rozšířený quality gate má 445 testů. Po nasazení prošel lokální i Tailscale
  smoke check. Formát ani cesta existujících private JSON souborů se neměnily a
  jejich obsah nebyl dávkově migrován.
- GitHub Actions `Cockpit Quality Gate` běh číslo 4 pro commit `507734f` skončil
  úspěšně za 1 minutu 15 sekund.
- Míla ručně potvrdil, že nová Quick Note z iPhonu doputovala do Cockpitu právě
  jednou. Stejný test vytvořil i nové důležité připomenutí; jeho samostatný
  urgent index tehdy ještě nebyl touto dávkou měněn.

## Urgent reminders rollout

- Samostatný `urgent_reminders/index.json` nyní používá stejnou stabilní
  sidecar lock a atomickou read-modify-write vrstvu jako Quick Notes.
- Sken iCloud souborů probíhá mimo zámek. Sloučení, přidělení stabilního čísla,
  zachování stavu `done` a zápis indexu proběhnou v jedné transakci.
- Označení `done` je také jedna zamčená transakce; neexistující číslo index
  zbytečně nepřepisuje.
- Dva procesy sloučily 40 různých urgentních připomenutí bez ztráty a s
  unikátními čísly 1 až 40.
- Deterministický souběh pozastavil sync po načtení zdrojového souboru, mezitím
  označil existující položku jako `done` a potvrdil, že dokončený sync tento stav
  nepřepsal zpět na `open`.
- Simulované selhání `os.replace` zachovalo původní index a uklidilo dočasný
  soubor. Formát ani cesta JSON se nezměnily a private obsah se nemigroval.
- Cílených 25 urgent/reminders/Quick Notes/Cockpit testů a celý quality gate s
  463 testy prošly. Lokální i Tailscale smoke check jsou zelené; obě adresy
  ukazují stejný serverový PID a code stamp. Živý sidecar lock existuje.
- Implementace je pushnutá v commitu `6e6dc5c`. GitHub Actions Cockpit Quality
  Gate běh č. 7 skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29109790245`.

## Document persistence primitives rollout

- Tři existující helpery v `app/documents/vault.py` zachovávají stejné signatury
  a formáty, ale používají sdílenou persistence vrstvu:
  - `write_json` zapisuje manifesty atomickým zamčeným JSON replace,
  - `write_jsonl` zapisuje celý registry soubor atomickým zamčeným replace,
  - `append_jsonl` přidává každý event pod stabilním sidecar lockem a s `fsync`.
- Změna se automaticky vztahuje na stávající dokumentové/ScanDocu volající bez
  změny jejich doménové logiky, cest nebo payloadů.
- Dva procesy zapsaly 60 dokumentových eventů jako 60 samostatných validních
  řádků. Simulované selhání `os.replace` zachovalo původní celý JSONL registry
  soubor i JSON manifest a uklidilo temp soubory.
- Správně adresovaný cílený dokumentový balík má 81 zelených testů. Celý quality
  gate prošel 466 testy; lokální i Tailscale smoke check jsou zelené a obě
  adresy ukazují PID 10943 a code stamp `567cce4d18f9ea56`.
- Živý test nespouštěl import, reindex ani lifecycle akci a nečetl private obsah.
- Implementace je pushnutá v commitu `1196076`. GitHub Actions Cockpit Quality
  Gate běh č. 8 skončil úspěšně:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29110559953`.

Tato dávka chrání před částečným souborem a promíchaným appendem. **Neřeší ještě
ztracený read-modify-write update**, protože některé doménové funkce čtou index
před získáním write locku. Stejně tak index, manifest, backup a audit log ještě
nejsou jedna více-souborová transakce. Tyto dva invarianty musí dostat samostatný
návrh a consistency test; nesmí se vydávat za hotové jen proto, že jednotlivé
replace operace jsou atomické.

## Document index + manifest transaction rollout

- Nový `app/documents/transactions.py` drží primární sidecar lock
  `documents_index.jsonl` ještě před striktním načtením indexu.
- Metadata a reading status používají jeden protokol:
  1. dokončit nebo vrátit předchozí nedokončený marker,
  2. pod index lockem znovu načíst aktuální řádek a manifest,
  3. vytvořit unikátní pre-image zálohu indexu a existujícího manifestu,
  4. atomicky zapsat recovery marker ve fázi `prepared`,
  5. atomicky zapsat index a manifest s průběžnou změnou fáze,
  6. přidat audit s unikátním `transaction_id`,
  7. označit commit a uklidit marker.
- Pokud zápis manifestu nebo jiný krok před auditem selže, index i manifest se
  obnoví ze zálohy. Pokud proces skončí po auditu, další transakce auditní ID
  rozpozná a již dokončenou změnu nevrátí.
- Nezměněná metadata nevytvoří backup, audit ani marker.
- Dva procesy měnící různé dokumenty zachovaly oba update. Souběžná změna
  klasifikace a reading statusu stejného dokumentu zachovala obě pole v indexu
  i manifestu.
- Testy simulují selhání manifestu, pád po indexu před manifestem a pád po
  auditu před committed markerem. Rollback/recovery ve všech případech zachoval
  očekávaný index, manifest, audit a uklidil marker.
- Nových transakčních testů je 6; správně cílený dokumentový balík má 87 testů
  a celý quality gate 472 testů. Monolit zůstává pod baseline: 22 459 řádků,
  328 top-level funkcí.
- Read-only nasazení bez skutečné dokumentové mutace prošlo lokálním i Tailscale
  smoke checkem. Obě adresy mají PID 15800 a code stamp `e935ee8cf87c3168`;
  živý transaction marker neexistuje.

Hranice rolloutu: metadata a reading status jsou serializované mezi sebou.
ScanDocu review, reindex, lifecycle a některé importní writery zatím stejný
primární RMW protokol nepoužívají, takže globální ochrana celého document indexu
ještě není dokončená.

## Doporučené další pořadí rolloutů

1. Převést ScanDocu review na stejný transaction marker/lock protokol a zahrnout
   jeho candidate-status/audit invariant do failure testu.
2. Potom převést reindex, lifecycle a nové document-index append writery po
   samostatných dávkách.
3. E-mail activity/case/archive metadata; outbound a mazací workflow až nakonec.

Každý rollout má zachovat formát i cestu existujícího souboru, přidat cílený
regresní/concurrency test a nemigrovat obsah bez samostatného rozhodnutí.
