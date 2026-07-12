Nazev: Samantha Cockpit - hlavni architektura a postupna modernizace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-10

Co se resilo:

- Probehl hluboky read-only audit hlavni architektury Samantha Cockpitu se
  zamerenim na Cockpit, VoiceBridge, dokumenty, e-maily, provozni bezpecnost,
  vykon a testovani.
- Zamerne byly vynechany jednotlive rodinne, jazykove, lekarnicke a dalsi
  samostatne projekty.
- Mila schvalil smer postupne modernizace bez prepisu od nuly a s malymi,
  overitelnymi implementacnimi baliky.
- Tento soubor je prubezny aktivni handoff. Behem aktualni faze se ma
  aktualizovat, ne zakladat novy handoff po kazde male uprave.

Co je hotove:

- Hlavni audit je ulozen v koreni projektu jako `AuditCockpit56.txt`.
- Prvni vykonovy krok je implementovany a pushnuty v commitu `23abbaa`:
  - novy lehky GET `/api/live-status`,
  - trisekundovy frontend monitor uz nevola plny `/api/status`,
  - plny status se automaticky obnovuje jednou za pet minut,
  - draha VoiceBridge procesni diagnostika ma patnactisekundovou cache,
  - smoke check kontroluje take live status.
- Po zmene proslo 374 relevantnich testu.
- Lokalni i Tailscale Cockpit po nasazeni prosly smoke checkem.
- Kontrolni mereni ukazalo priblizne 2-6 ms pro cachovany live status oproti
  priblizne 1,07 s pro kontrolni plny status.
- Vychozi handoff checkpoint byl pushnuty v `25cc522` a jedna instance v
  `d65fa23`; aktualni HTTP zmeny cekaji na novy tematicky commit.

Rucni retest po prvnim vykonovem kroku:

- Mac cast rucniho testu Mila provedl 2026-07-10.
- Cockpit se uspesne otevrel pres globalni klavesovou zkratku.
- `Restart Cockpitu` funkcne prosel; restart trval priblizne 20-30 sekund.
- Behem ocekavaneho preruseni spojeni se ve stavovem radku objevilo `Load failed`,
  ale po obnoveni serveru vse zmizelo a nezustala zadna cervena chyba.
- VoiceBridge z Macu prosel end-to-end a odpoved se vratila do Cockpitu.
- Rucni `Obnovit` z horni listy prosel; plny status se nacital priblizne dve
  sekundy.
- Funkcne je Mac retest uspesny. Neprivetive `Load failed` pri zamerne provadenem
  restartu je neblokujici UX nalez pro pozdejsi zlepseni stavove hlasky.
- Tailscale/iPhone klient se nacetl funkcne a hlasovy pokyn z iPhonu dorazil
  end-to-end do Codexu; odpoved byla zapsana zpet do Cockpitu.
- Prvni vykonovy krok je tim rucne potvrzeny na Macu i iPhonu.
- Druhy P0 krok je implementovany: lokalni i Tailscale adresa jsou obsluhovane
  jedinym `cockpit_server.py` procesem na `127.0.0.1:8770`.
- Tailscale Serve TCP proxy zachovava dosavadni vzdalenou IP adresu a port, ale
  pouze predava spojeni do lokalni instance.
- Puvodni Tailscale launchd plist zustal zachovany a neni nacteny; slouzi jako
  rychly rollback bez mazani puvodni konfigurace.
- `scripts/migrate_cockpit_single_instance.py` umi read-only status, `--apply`
  a `--rollback`; neuspesna migrace se pokusi automaticky obnovit puvodni sluzbu.
- Po migraci lokalni i vzdaleny health vratily stejny PID a code stamp.
- Lokalni i vzdaleny smoke check prosly pred i po restartu vyvolanem pres
  vzdalenou adresu. Proxy po restartu ukazala novy lokalni PID na obou adresach.
- Po doplneni migracnich testu proslo 378 relevantnich testu.
- Mila po migraci rucne poslal hlasovy pokyn z iPhonu na dosavadni adrese;
  pokyn dorazil a odpoved se vratila do Cockpitu. Jedna instance je tim rucne
  potvrzena end-to-end.
- Treti P0 krok je implementovany a nasazeny: centralni HTTP ochranna vrstva.
- JSON tela maji limit 10 MiB, ktery zachovava rezervu pro sestimegabajtove
  hlasove audio po base64 prevodu.
- Chybny JSON, prilis velke telo a nespravny Content-Type vraceji rizene
  400/413/415 odpovedi; cizi webovy Origin/Referer vraci 403.
- Host kontrola povoluje pouze loopback a Tailscale adresy/jmena.
- Neocekavana vyjimka vraci obecnou 500 bez textu vnitrni vyjimky.
- Vsechny odpovedi maji CSP, nosniff, SAMEORIGIN, Referrer-Policy,
  Cross-Origin-Resource-Policy a Permissions-Policy. SAMEORIGIN zachovava
  vestavenou PDF ctecku.
- Private HTTP event log uklada jen cas, udalost, metodu, cestu bez query,
  status a tridu chyby; neuklada payloady, hlavicky ani soukrome texty.
- Po HTTP zmene proslo 388 relevantnich testu, lokalni i vzdaleny smoke check,
  zivy invalid-JSON test a Tailscale same-origin POST.
- Pri rucnim Mac testu Mila odhalil frontendovou regresi: horni `Obnovit`
  problikavalo v trisekundovem live intervalu.
- Pricina byla potvrzena: `refreshLiveStatus()` po lehkem fetchi stale volal
  cely `renderDashboard(...)`.
- Oprava vyjmula hlasove vykresleni do `renderVoiceStatus(...)`; live interval
  nyni meni jen hlas, bridge a potvrzovaci karty. Plny dashboard se neprekresluje.
- JavaScript syntax check, novy regresni test, 389 relevantnich testu a lokalni
  i vzdaleny smoke check prosly. Nasazena HTML obsahuje pouze
  `renderVoiceStatus(latestMainStatusData)` v live refreshi.
- Pri navazujicim hlasovem testu z iPhonu se na otevrenem Mac Cockpitu sama
  objevila browserova hlaska o nepovolenem pozadavku. Doruceni pokynu,
  VoiceBridge i server zustaly funkcni; pricina byla ve vystupni audio vrstve:
  Mac prohlizec zablokoval automaticke `audio.play()` bez cerstveho kliknuti a
  Cockpit ocekavany autoplay blok chybne zapsal jako cervenou frontendovou chybu.
- Oprava rozlisuje ocekavany autoplay `NotAllowedError` pouze uvnitr prehravaci
  vetve. Na Macu tise pokracuje k systemovemu hlasovemu fallbacku, na vzdalenem
  mobilu ponecha tlacitko pro rucni prehrani; jine chyby audia, mikrofonu a
  VoiceBridge zustavaji viditelne.
- Po oprave prosla JavaScript syntax kontrola, novy regresni test a 390
  relevantnich testu. Nasazena verze prosla lokalnim i Tailscale smoke checkem
  a obe adresy dal obsluhuje stejny novy serverovy PID.
- Navazujici iPhone retest ukazal, ze odpoved se zapisovala, ale iPhone zustal
  tichy. Po reloadu byl webovy audiokanal znovu zamceny a bez samostatneho
  klepnuti na `Otevrit audiokanal` nevznikl ani pokus o prehrani.
- Tlacitko `Odeslat Adamovi` proto na vzdalenem mobilnim klientu nyni v ramci
  stejneho uzivatelskeho gesta automaticky otevira tichy Web Audio kanal jeste
  pred odeslanim pokynu. Samostatne tlacitko zustava jako rucni fallback.
  Doruceni pokynu, mikrofonni vetev ani VoiceBridge se nezmenily.
- Po iPhone audio oprave prosla JavaScript kontrola a 391 relevantnich testu.
  Nasazena verze prosla lokalnim i Tailscale smoke checkem; prvni vzdaleny plny
  status po restartu jednou vyprsel na timeoutu, opakovani s rezervou proslo.
- Rucni retest potvrdil stav `Audiokanal otevreny`, ale dalsi odpoved se presto
  neprehrala. Server, zapis odpovedi i zobrazeni na iPhonu byly funkcni.
- Druha pricina byla v rozhodovani o automatickem cteni: prvni nova odpoved po
  reloadu se mohla zobrazit pres lehky live status, ktery automaticke cteni
  podminoval existenci starsiho response klice. Pokud presne pollingove
  sparovani nasledne neprobehlo, prehravac nebyl vubec zavolan.
- Otevreni audiokanalu nyni oznaci prave zobrazenou starou odpoved jako vyrizenou
  a live status muze automaticky precist kazdou skutecne novou odpoved i jako
  prvni odpoved po reloadu. Bezpecna frontend diagnostika navic uklada pouze
  technicke udalosti `voice_autospeak_requested` a `audio_play_succeeded` bez
  textu odpovedi.
- Po teto oprave prosla JavaScript kontrola a 392 relevantnich testu. Lokalni i
  Tailscale smoke check po nasazeni prosly kompletne.
- Rucni iPhone test 3785 nasledne potvrdil automaticke cteni. Bezpecna technicka
  stopa zaznamenala `voice_autospeak_requested` a dokoncene
  `audio_play_succeeded`; puvodni ticho bylo v poslednim pokusu zpusobene
  tichym rezimem telefonu, ne dalsi chybou Cockpitu.
- Pozdejsi telefonni hovor prerusil iPhone Web AudioContext: text zaverecneho
  shrnuti dorazil, ale chybel `audio_play_succeeded` a rucni prehrani nedokazalo
  obnovit kontext, prestoze UI stale hlasilo otevreny kanal. Oprava obnovuje
  stavy `suspended` i iOS `interrupted`, zahazuje `closed` kontext, overuje
  skutecny stav `running` a drzi rucni recovery uvnitr diagnosticke obalky.
- Po audio recovery oprave proslo 410 relevantnich testu a lokalni i Tailscale
  smoke check. Rucni retest po realnem telefonatu muze probehnout pozdeji.
- Zapisova mista runtime casti `app/` jsou zmapovana v git-safe reportu
  `reports/cockpit_persistence_write_map_2026_07_10.md`. Inventura necetla
  private obsahy a potvrzuje roztristene prime JSON/JSONL zapisy ve VoiceBridge,
  dokumentech, e-mailech, pripominkach a provoznich stavech.
- Nova sdilena vrstva `app/file_persistence.py` poskytuje stabilni sidecar
  `.lock`, `fcntl.flock` s timeoutem, atomicky zapis pres temp soubor ve stejne
  slozce, `fsync`, `os.replace`, zamcenou read-modify-write JSON transakci a
  zamceny JSONL append.
- Prvni nizkorizikova integrace je nasazena do backup activity state a Cockpit
  HTTP technickeho event logu. HTTP log ma kratky timeout a zustava best-effort,
  aby diagnostika nikdy nezdrzela odpoved serveru. Cesty ani formaty dat se
  nemenily a zadna private data se nemigrovala.
- Testy spousteji dva skutecne Python procesy: 60 soubeznych JSON aktualizaci
  probehlo bez ztraty a 60 JSONL udalosti zustalo samostatnymi validnimi radky.
  Simulovane selhani `os.replace` zachovalo puvodni soubor a uklidilo temp.
- Cely relevantni balicek Cockpit, VoiceBridge, dokumenty, e-maily a backup
  prosel: 409 testu OK.
- Prvni cista VoiceBridge persistence davka prevadi pouze
  `adam_voice_mode_status.json` a `last_adam_response.json` na sdileny atomicky
  zamceny JSON zapis. Pending stav, approval karty, historie JSONL a doruceni
  zustaly beze zmeny.
- Integracni testy overuji lock a uklid temp souboru u obou VoiceBridge souboru;
  simulovane selhani `os.replace` zachova predchozi status JSON.
- Po nasazeni byl Voice Mode watcher restartovan bez cekajiciho pokynu, vratil
  se do `listening`, terminalovy bridge zustal zapnuty a zivy statusovy lock
  vznikl. Lokalni i Tailscale smoke check a 413 relevantnich testu prosly.
- Vsechny prechody `pending_for_adam.json` nyni pouzivaji jeden zamceny
  read-validate-modify-write cyklus. Dva ruzne aktivni pokyny se neprepisou:
  prvni vyhraje a druhy dostane `pending_conflict`; stejny save, approval,
  processing nebo finalni odpoved jsou idempotentni.
- Watcher pri pending konfliktu vrati pravdivou zpravu a historii oznaci routou
  `pending_conflict`, misto aby tvrdil, ze novy pokyn ulozil. Pri soubeznem
  dokonceni historie vznikne jen procesu, ktery zmenu skutecne provedl.
- Nove dvouprocesove testy potvrdily jednoho viteze pri zalozeni i dokonceni.
  Cely relevantni balicek ma 418 testu OK.
- Po nasazeni se watcher vratil do `listening`, terminalovy bridge zustal
  zapnuty a idempotentni ziva transakce vytvorila pending lock bez zmeny SHA-256
  obsahu. Lokalni i Tailscale smoke check prosly.
- Oba zapisy `adam_voice_history.jsonl` nyni pouzivaji sdileny zamceny JSONL
  append. Format ani cesty se nezmenily a seznam finalnich/nefinalnich rout
  zustal stejny, takze transportni mezistav neprepisuje posledni finalni odpoved.
- Dvouprocesovy test zapsal 60 soubeznych history udalosti jako 60 validnich
  samostatnych radku a potvrdil, ze posledni odpoved zustala z finalni routy.
  Lock chrani integritu radku; exactly-once dokonceni dale zajistuje predchozi
  idempotentni pending transakce.
- Novy souhrnny regresni test pro textovy i nahravany vstup tvrde hlida invariant
  `watcher running => no inline delivery` a absenci delivery attempts.
- Po nasazeni proslo 420 relevantnich testu, watcher se vratil do `listening`,
  nic neceka a lokalni i Tailscale smoke check prosly kompletne.
- Pred rozdelenim monolitu vznikl kanonicky
  `scripts/cockpit_quality_gate.py`: kontroluje whitespace, striktni syntax bez
  `SyntaxWarning`, 424 relevantnich testu a vypisuje informativni metriku
  monolitu. Vychozi `app/cockpit.py` ma 22 465 radku, 332 top-level funkci a
  2 tridy; dalsi rust vyvola varovani, ne krehky hard fail.
- Korenovy GitHub Actions workflow `.github/workflows/cockpit-quality-gate.yml`
  bezi na `macos-14`, ma pouze read-only contents opravneni, zadna tajemstvi ani
  private data a path filtry pro relevantni Cockpit zmeny.
- Prvni vzdaleny beh odhalil osm VoiceBridge CLI testu vazanych na lokalni
  `.venv/bin/python`. Nyni pouzivaji `sys.executable`; gate navic pri chybe
  publikuje bezpecnou anotaci s koncem tracebacku. Treti GitHub beh pro commit
  `3ba9d59` skoncil uspesne za 1 minutu 19 sekund.
- Prvni striktni syntax beh odhalil tri JavaScript regex escape zapisy uvnitr
  Python HTML retezce. Byly ekvivalentne opraveny bez zmeny runtime JavaScriptu.
- Hlavni `reminders.json` nyni pouziva jednu zamcenou transakcni funkci pro
  vytvoreni bez duplicit, zmenu statusu, zruseni platebni pripominky a doplneni
  dokumentovych metadat. Dva procesy pridaly 40 ruznych pripominek bez ztraty;
  pri stejnem ID vznikl prave jeden zaznam bez druheho replace.
- Quick Notes sync nyni scanuje vstupy mimo lock, ale slouceni, prideleni cisla
  a zapis indexu provede v jednom zamcenem read-modify-write cyklu. Dva procesy
  sloucily 40 poznamek s jedinecnymi cisly 1 az 40 a bez ztracenych cest.
- Quality gate byl rozsiren o samostatne reminders/Quick Notes moduly a ma 445
  testu. Transparentne ukazuje 7 prechodovych radku navic v `app/cockpit.py`;
  transakcni logika je v reminders modulu, ne v monolitu.
- Po nasazeni prosly lokalni i Tailscale smoke check. Private obsahy se necetly,
  format/cesty dat se nemenily a zadna davkova migrace neprobehla.
- GitHub Actions quality gate beh cislo 4 pro commit `507734f` skoncil uspesne
  za 1 minutu 15 sekund.
- Mila rucne potvrdil novou Quick Note z iPhonu v Cockpitu. Nove dulezite
  pripomenuti take doputovalo; pouziva vsak samostatny urgent index, ktery tato
  davka nemenila.
- Pri rucnim otevreni pres `Ctrl+Option+Command+C` se Cockpit oteviral neobvykle
  dlouho. Pricina byla potvrzena: launcher a server pocitaly code stamp z jineho
  seznamu souboru, takze zdravy server byl falesne restartovan.
- `app/cockpit_code_stamp.py` je nyni jediny zdroj manifestu pro server i
  launcher a automaticky zahrnuje `app/**/*.py` plus `cockpit_server.py`.
  Regresni test hlida shodu obou stran a quality gate ma 458 testu.
- Prvni opravny beh provedl ocekavany jednorazovy restart za 42,47 s; druhy
  bezny `--no-open` beh trval 0,89 s a stampy se shodovaly. Oba smoke checky
  prosly. Monolit klesl na 22 454 radku a 331 funkci, tedy pod baseline.
- GitHub Actions quality gate beh cislo 5 pro commit `17729ec` skoncil uspesne
  za 1 minutu 29 sekund.
- Read-only inventura mrtveho a legacy kodu je hotova v
  `reports/cockpit_dead_legacy_code_inventory_2026_07_10.md`; necetla private
  obsahy a nemenila aplikacni kod.
- Vsech 67 POST cest ma presnou registry kartu a spravny handler. Ve trech
  hlavnich HTML dokumentech nebyla nalezena duplicitni nebo definition-only
  JavaScript funkce, duplicitni ID ani chybejici DOM cil.
- Z 331 top-level funkci monolitu je 323 staticky dosazitelnych z produkcnich
  vstupu. Osm nedosazitelnych funkci tvori stary e-mailovy Markdown prehled,
  nahrazeny PDF resolver a starou lokalni Janicka vetev.
- Spolu s nepouzitym launcher helperem a full-replacement reminders wrapperem
  tvori silni kandidati 255 radku funkci. Nic nebylo odstraneno.
- Pet API cest bez aktivni UI vazby potrebuje pred pripadnym odstranenim
  kontrolu externich Shortcuts, bookmarku a servisnich klientu.
- Opatrny Cleanup R1 odstranil pouze dva nepouzivane importy z Cockpit monolitu,
  nasledne osirely `atomic_write_json` import z reminders store, nahrazeny PDF
  resolver, launcher `wait_until_ok` a nepouzivany full-replacement reminders
  wrapper. Endpointy, Janicka, e-mailovy parser, VoiceBridge a private data se
  nemenily.
- Aplikacni diff ma 2 upravene importni radky a 39 odstraneni. Primy scan
  nepotvrdil zadnou zbyvajici referenci; zamerne zustal testovany launcher alias
  `CODE_STAMP_PATHS`.
- Cilenych 20 launcher/reminders testu a cely quality gate s 458 testy prosly.
  Po kontrolovanem restartu maji lokalni i Tailscale adresa stejny PID 5700 a
  code stamp `4035402f842a33dc`; oba petibodove smoke checky prosly.
- Cleanup R1 je pushnuty v commitu `9192e53`. GitHub Actions Cockpit Quality
  Gate beh cislo 6 pro tento commit skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29107547605`.
- `app/cockpit.py` ma po R1 22 439 radku a 330 top-level funkci. Ze 255 radku
  puvodnich funkcnich kandidatu zbyva 227 radku starych e-mailovych a Janicka
  vetvi, ktere vyzaduji samostatne rozhodnuti nebo rucni overeni.
- Samostatny urgent-reminders index nyni skenuje iCloud soubory mimo lock, ale
  slouceni, stabilni cislovani, zachovani `done` a zapis provadi v jedne
  `update_json_file` transakci. Oznaceni `done` pouziva stejnou zamcenou cestu.
- Dva procesy sloucily 40 ruznych urgentnich pripomenuti s jedinecnymi cisly
  1 az 40. Deterministicky sync-vs-done test potvrdil, ze soubezny sync nevrati
  hotovou polozku na `open`; selhani `os.replace` zachovalo puvodni index.
- Cilenych 25 testu a cely quality gate se samostatnym urgent modulem prosly:
  463 testu OK. Lokalni i Tailscale smoke check jsou zelene, obe adresy maji
  PID 9179 a code stamp `7898101b0363b08f`; zivy sidecar lock existuje.
- Cesta ani JSON format se nemenily, private obsah se nemigroval ani nevypisoval.
- Implementace je pushnuta v commitu `6e6dc5c`. GitHub Actions Cockpit Quality
  Gate beh cislo 7 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29109790245`.
- Prvni dokumentova persistence davka zamerne nezamykala napul vice-souborovou
  operaci. Tri existujici helpery v `app/documents/vault.py` nyni pouzivaji
  sdilenou vrstvu: JSON a cely JSONL atomicky replace pod lockem, JSONL append
  zamceny append s fsync. Signatury, cesty a payload formaty zustaly stejne.
- Dva procesy zapsaly 60 dokumentovych eventu bez promichani nebo ztraty radku.
  Simulovane selhani replace zachovalo puvodni JSONL registry i JSON manifest a
  uklidilo temp soubory. Spravne adresovany dokumentovy balicek ma 81 testu OK;
  kanonicky quality gate ma 466 testu OK.
- Po read-only nasazeni bez importu/reindexu/lifecycle akce prosly lokalni i
  Tailscale smoke checky. Obe adresy maji PID 10943 a code stamp
  `567cce4d18f9ea56`; private dokumentovy obsah se necetl ani nemigroval.
- Implementace je pushnuta v commitu `1196076`. GitHub Actions Cockpit Quality
  Gate beh cislo 8 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29110559953`.
- Hranice: jednotlive zapisy jsou crash-safe a append-safe, ale domenovy
  read-modify-write muze stale ztratit soubeznou zmenu, protoze cteni nekterych
  funkci probiha pred lockem. Index, manifest, backup a audit log zatim nejsou
  jedna vice-souborova transakce.
- `app/documents/transactions.py` nyni poskytuje fazovou recovery transakci pro
  metadata a reading status: primarni index lock pred strict readem, pre-image
  backup indexu/manifestu, atomicky marker, index + manifest, auditni
  `transaction_id`, committed faze a uklid markeru.
- Selhani pred auditem vrati index i manifest. Pri padu po auditu dalsi vstup
  rozpozna transaction ID a zachova uz commitnutou zmenu. Nezmenena metadata
  nevytvori backup, audit ani marker.
- Dva procesy nad ruznymi dokumenty zachovaly oba update; metadata a reading
  status stejneho dokumentu zachovaly obe pole v indexu i manifestu. Sest novych
  testu kryje concurrency, manifest failure, dve crash faze a no-change.
- Cileny dokumentovy balicek ma 87 testu OK a cely quality gate 472 testu OK.
  Monolit ma 22 459 radku / 328 top-level funkci, stale pod baseline.
- Read-only nasazeni bez skutecne mutace proslo obema smoke checky. Lokalni i
  Tailscale adresa maji PID 15800 a code stamp `e935ee8cf87c3168`; v zivem
  vaultu neni transaction marker a private obsah se necetl ani nemigroval.
- Implementace je pushnuta v commitu `64ce395`. GitHub Actions Cockpit Quality
  Gate beh cislo 9 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29115015113`.
- ScanDocu review nyni pod stejnym primarnim index lockem zapisuje index,
  manifest, candidate status a `scandocu_actions.jsonl` jako jednu obnovitelnou
  transakci. Action audit je commit point a obsahuje `transaction_id`.
- Audit failure vrati vsechny tri JSON/JSONL pre-images; simulovany pad pred
  auditem zanecha marker a dalsi dokumentova transakce vrati i candidate status.
  Deterministicky dvouprocesovy test potvrdil, ze Cockpit metadata update ceka
  na ScanDocu lock a oba dokumenty zustanou zachovane.
- Ctyri nove ScanDocu testy zvedly cely quality gate na 476 testu OK;
  dokumentove moduly maji 87 testu OK. `app/cockpit.py` zustal beze zmeny na
  22 459 radcich / 328 top-level funkcich. Skutecny vault se nemutoval.
- Read-only nasazeni proslo lokalnim i Tailscale smoke checkem. Obe adresy maji
  PID 19613 a code stamp `8b947c4304e2cd95`; live marker neexistuje a na portu
  8771 nebezi zalozni instance.
- Implementace je pushnuta v commitu `a11e263`. GitHub Actions Cockpit Quality
  Gate beh cislo 10 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29117003749`.
- Hranice: reindex, lifecycle a nektere importni writery jeste nepouzivaji
  primarni RMW protokol a mohou se se soubeznou transakci krizit.
- Oprava prehledu relaci nyni ukazuje celkem / bezne / spravovane; zivy stav je
  dve Codex relace, z toho jedna bezna Milova a jedna spravovana Janička light.
  Managed relace zustava chranena pred cleanupem, ale je viditelna a ma vlastni
  ovladani Start/Stop.
- Stop Janičky po `screen quit` overuje, ze screen opravdu zmizel. Pokud ne,
  vrati `stop_incomplete` misto falesneho uspechu.
- Dva autosave watchery byly skutecny provozni problem: Janička i hlavni relace
  spoustely globalni kopirovani a watcher mohl po ukonceni screen zustat ve
  `sleep`. Managed relace nyni watcher nespousteji, watcher ma singleton lock a
  signal prerusi i cekajici sleep.
- Zivy nadbytecny Janička watcher byl ukoncen bez zastaveni Janičky. Autosave
  status, Recovery centrum i cleanup panel potvrzuji jeden watcher; zadny
  autosave snapshot se pri oprave nemazal.
- Autosave backend je vyjmuty do `app/autosave_service.py`. Kanonicky gate ma
  532 testu a kontroluje i shell syntax; `app/cockpit.py` klesl na 22 369 radku
  / 325 top-level funkci, tedy 96 radku pod baseline.
- Nasazeny Cockpit prosly lokalnim i Tailscale smoke checkem; obe adresy vidi
  PID 24877 a code stamp `8f5b6b65b7426805`.
- Implementace je pushnuta v commitu `67ba77e`. GitHub Actions Cockpit Quality
  Gate beh cislo 11 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29119991977`.
- Mila rucne overil lifecycle Janičky: spustil ji na nove managed TTY a znovu
  zastavil. Managed screen i TTY zmizely, hlavni relace a jediny autosave
  watcher zustaly zachovane; Janička je nyni zastavena.
- Faze 1.1 je implementovana: novy `app/cockpit_status_service.py` prevzal
  sestaveni `/api/server/health`, `/api/live-status` a `/api/status`, mereni
  sekci i zamcenou patnactisekundovou live cache. `app/cockpit.py` zustal
  kompatibilnim adapterem, takze routy, nazvy funkci a JSON payloady se
  nezmenily.
- Prime kontraktni testy nove sluzby overuji health identitu, poradi a vazby
  plnych statusovych sekci i live cache. Kanonicky gate ma 535 testu OK a
  `app/cockpit.py` klesl na 22 293 radku / 325 top-level funkci, tedy 172 radku
  pod baseline.
- Po jednorazovem nasazovacim restartu prosly lokalni i Tailscale smoke checky
  vsech peti cest. Obe adresy obsluhuje jedina serverova instance PID 27653.
- Implementace Faze 1.1 je pushnuta v commitu `a8857f0`. GitHub Actions Cockpit
  Quality Gate beh cislo 12 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29121176082`.
- Faze 1.2 ma implementovany prvni a hlavni bezpecny rez: novy
  `app/voice_bridge_coordinator.py` rozhoduje, zda ma ulozeny textovy nebo
  prepsany hlasovy pokyn vlastnit bezici watcher, nebo explicitni inline
  fallback. Pri bezicim watcheru coordinator inline doruceni vubec nezavola.
- HTTP routy, prepis audia, TTY/screen transporty, `pending_for_adam.json`,
  historie, approval pravidla a potvrzovaci bezpecnost zustaly ve stavajicich
  vrstvach. `app/cockpit.py` je pro obe vstupni akce kompatibilni adapter.
- Ctyri prime kontraktni testy hlidaji shodny ownership pro text i nahravku,
  explicitni inline adapter, chybu prepisu bez doruceni a prazdny vstup bez
  persistence. Kanonicky gate ma 539 testu OK; `app/cockpit.py` klesl na
  22 230 radku / 324 top-level funkci, tedy 235 radku pod baseline.
- Nova verze prosla lokalnim i Tailscale smoke checkem vsech peti cest. Obe
  adresy obsluhuje jedina instance PID 32168 a na nouzovem portu 8771 nic
  neposloucha.
- Rucni iPhone test potvrdil command ownership: pokyn dorazil do chatu prave
  jednou, watcher byl jedinym vlastnikem a `delivery_attempts.jsonl` zustal od
  drivejska beze zmeny. GitHub Actions gate pro commit `0beebbc` s 539 testy
  skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29122979483`.
- Prvni odpoved dorazila jako text, ale se sluchatky se neprehrala. Technicka
  stopa ukazala obnovu iOS AudioContextu bez uspechu nebo chyby prehrani;
  backend Edge TTS samostatne i ve trech soubeznych pozadavcich vracel MP3 za
  1-2 sekundy. Problem byl omezeny na posledni Web Audio vrstvu.
- iPhone prehravac ma nyni petisekundovy timeout dekodovani, casove omezeny
  playback, automaticky fallback na HTML Audio a lokalni zamek proti
  soubeznemu spusteni. JavaScript syntax, 225 Cockpit testu a cely gate s 539
  testy prosly; `app/cockpit.py` ma 22 263 radku / 324 top-level funkci, tedy
  202 radku pod baseline.
- Po nasazeni opravy prosly lokalni i Tailscale smoke checky na jedine instanci
  PID 35158. Mila po znovuotevreni Cockpitu rucne potvrdil prehrani do sluchatek
  a technicka stopa zaznamenala `audio_play_succeeded` bez obsahu odpovedi.
- Zaverecna audio oprava je pushnuta v commitu `18b9f63`. GitHub Actions
  Cockpit Quality Gate beh cislo 14 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29123726588`.
- Po Milove korekci rozsahu nebyla Faze 1.2 uzavrena po pouhem 30radkovem
  cistem poklesu. Navazujici tri rezy vyjmuly inbox/delivery persistence,
  transportni coordinator, runtime status, marker a start/stop watcheru do
  `app/voice_bridge_coordinator.py` a `app/voice_bridge_runtime.py`.
- `app/cockpit.py` klesl z 22 263 na 21 786 radku, tedy o 477 radku. Z
  VoiceBridge backendu v nem zustaly tenke kompatibilni adaptery a frontend,
  nikoli vlastni transportni nebo provozni orchestrace.
- Prime testy coordinatoru/runtime hlidaji ownership, transport, managed screen,
  rozdeleni relaci, marker a watcher lifecycle. Kanonicky gate ma 547 testu.
- Implementacni commity jsou `b663589`, `9279fc0` a `561034a`. GitHub Actions
  Cockpit Quality Gate finalniho kodu skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29125107857`.
- Finalni iPhone test potvrdil jeden pokyn, watcher jako jedineho vlastnika,
  zadny inline pokus, jednu odpoved a uspesne prehrani do sluchatek. Faze 1.2
  je tim skutecne uzavrena.
- Faze 1.3 zacala prvnim read-only rezem: `app/documents/search_service.py`
  prevzal dokumentove a nakupni hledani, intent scoring, redigovane vysledky a
  metadata-only reading status. GET `/api/documents/search` zustal beze zmeny.
- Tri prime service testy a sest existujicich Cockpit search scenaru prosly;
  kanonicky gate ma 550 testu. `app/cockpit.py` klesl z 21 786 na 21 517 radku,
  tedy o dalsich 269 radku.
- Nasazena verze prosla lokalnim i Tailscale smoke checkem na jedine instanci
  PID 44394. Zivy private vault se pri rezu necetl ani nemenil.
- Druhy read-only rez Faze 1.3 pridal `app/documents/case_service.py`. Sluzba
  prevzala seskupeni dokumentu do cases, detail case, vazbu na otevrene
  pripominky a terminy, redigovani internich ID a vypocet `case_health`.
  Verejne funkce v `app/cockpit.py` zustaly tenke kompatibilni adaptery a
  endpointy se nezmenily.
- Tri prime testy nove sluzby rozsiruji kanonicky gate na 553 testu.
  `app/cockpit.py` klesl z 21 517 na 21 060 radku, tedy o dalsich 457 radku;
  od zacatku Faze 1.3 celkem o 726 radku.
- Lokalni i Tailscale smoke check po nasazeni prosly na jedine instanci PID
  47655 se shodnym code stampem `72bd182745b34cc5`. Restart mel kratke
  prechodove okno, ve kterem launchd jeste nezacal odpovidat, ale sam obnovil
  jednu standardni instanci; zadny druhy server nezustal bezet.
- Treti read-only dokumentovy rez, pracovne oznaceny jako 1.4, pridal
  `app/documents/review_service.py`. Sluzba prevzala klasifikacni prehled a
  automaticke navrhy, frontu dokumentu k revizi, strukturovany review report a
  souhrn document work. Potvrzene zapisovaci transakce metadat a reading statusu
  zustaly v Cockpitu beze zmeny.
- Ctyri prime testy nove sluzby rozsiruji gate na 557 testu. `app/cockpit.py`
  klesl z 21 060 na 20 519 radku, tedy o dalsich 541 radku; od zacatku Faze 1.3
  celkem o 1 267 radku.
- Lokalni i Tailscale smoke check po nasazeni prosly na jedine instanci PID
  50626 se shodnym code stampem `e2a2b6fed6cd6ff6`.
- Ctvrty read-only dokumentovy rez, pracovne 1.5, pridal
  `app/documents/due_date_service.py`. Sluzba prevzala kandidaty terminu z
  vaultu i ulozenych e-mailu, filtrovani starych terminu, rozpoznani stejneho
  e-mailu a PDF prilohy, pravdepodobne duplicity a verejne redigovane vysledky.
  Potvrzena tvorba pripominky zustala v Cockpitu jako samostatna zapisovaci
  hranice.
- Ctyri prime testy nove sluzby rozsiruji gate na 561 testu. `app/cockpit.py`
  klesl z 20 519 na 19 915 radku, tedy o dalsich 604 radku; od zacatku Faze 1.3
  celkem o 1 871 radku.
- Lokalni i Tailscale smoke check po nasazeni prosly na jedine instanci PID
  51970 se shodnym code stampem `28394cc55992a99b`.
- Paty read-only dokumentovy rez 1.6 pridal
  `app/documents/intake_service.py`. Sluzba sjednocuje cekajici PDF z Downloads,
  oznacene polozky e-mailove fronty, mobilni scan batch a lokalni inbox do
  jednoho prehledu a stabilniho poradi akci. Sama neskenuje e-mailova tela,
  nestahuje prilohy a nic neimportuje ani nezapisuje.
- Tri prime testy nove sluzby rozsiruji gate na 564 testu. `app/cockpit.py`
  klesl z 19 915 na 19 703 radku, tedy o dalsich 212 radku; od zacatku Faze 1.3
  celkem o 2 083 radku.
- Lokalni i Tailscale smoke check po nasazeni prosly na jedine instanci PID
  53444 se shodnym code stampem `eeba05331cde14eb`.
- Faze 2.1 pridala `app/voice_bridge_state.py`: explicitni stavy prijeti,
  prepisu, persistence, volby vlastnika, watcher fronty/zpracovani, cekani na
  Adama nebo potvrzeni a finalnich vysledku. Coordinator i watcher pouzivaji
  stejny model; prechod na jineho vlastnika po volbe je zakazany.
- Stavova stopa je technicka a neobsahuje text pokynu. Watcher ji uklada do
  existujiciho private status JSON; heartbeat zachovava posledni `command_state`
  misto jeho prepsani. Stara UI pole zustala kompatibilni.
- Gate ma 573 testu. Implementacni commity jsou `9417056` a `46ca297`.
  `app/speech/adam_voice_mode.py` zustal na baseline 1 105 radku a stavovy model
  je samostatny modul.
- Finalni zivy test po restartu watcheru PID 60230 potvrdil prave jeden history
  zaznam, nula inline pokusu a zachovanou stopu
  `watcher_queued -> watcher_processing -> awaiting_adam`. Text pokynu ani
  private logy se do checkpointu neukladaji.
- Faze 2.2 pridala `app/documents/intake_models.py`: jednotne enumy zdroje,
  stavu a akce, `DocumentIntakeItem` a `DocumentIntakeSourceSnapshot`.
  Downloads, e-mailova fronta, mobilni scan i lokalni inbox jsou adaptovane do
  stejneho kontraktu pod stavajicim API.
- Kazda polozka ma stabilni hashovanou `intake_ref`; filename/UID/batch klic se
  pouzije jen pro hash a neni soucasti verejneho modelu. Invarianty zakazuji
  polozku pod nespravnym zdrojem a nesouhlas viditelneho a celkoveho poctu.
- Gate ma 578 testu. Zive overeni bez vypisu obsahu potvrdilo 4 zdroje, 5
  aktualnich sjednocenych polozek, vsechny reference platne a unikatni.
  Lokalni i Tailscale smoke check prosly na jedine instanci PID 63621 se
  shodnym code stampem `b960ddd3a4e6552f`.
- Faze 2.3 pridala `app/email/work_models.py`: jednotnou stabilni identitu,
  stav a akci pro nove e-mailove hlavicky i polozky pracovni fronty. Zachovava
  puvodni `id`, `legacy_id` a `source_key`, takze stare decision zaznamy zustaly
  kompatibilni. Do modulu se z monolitu presunula take klasifikace a batch
  skupiny; provider, archivace, odesilani a potvrzovaci brany se nezmenily.
- Gate ma 583 testu a `app/cockpit.py` klesl na 19 547 radku. Zivy read-only
  test bez vypisu obsahu vratil dve nove polozky od dvou provideru; obe mely
  platnou `emailworkref-...` referenci a stav `new`. Pracovni fronta byla
  prazdna. Lokalni i Tailscale smoke check prosly na jedine instanci PID 65307.
- Prvni rez Faze 2.4 pridal `app/work_repository.py` s atomickou repository
  mutaci, `operation_id` ledgerem a volitelnym outbox zaznamem v jednom JSON
  commitu. `app/email/work_repository.py` je prvni adapter pro pracovni
  e-mailova rozhodnuti; save i clear uz nemaji read pred ziskanim locku.
- Dva procesy ulozily dve ruzna rozhodnuti bez lost update. Stejny request nebo
  stejny semanticky stav se neprepise podruhe. Frontend posila `operation_id`,
  stary `decisions` format i nezname top-level hodnoty zustavaji kompatibilni.
- Zivy adapter outbox udalosti zatim negeneruje. E-mailove providery, archiv,
  prilohy, kos, purge a odesilani se nezmenily. Gate ma 593 testu; oba smoke
  checky prosly na jedine instanci PID 67447.
- Druhy rez Faze 2.4 doplnil `lease -> retry -> ack`: atomicky vyber dostupne
  udalosti, expiraci, pocitadlo pokusu a fencing token. Dva procesy nemohou
  ziskat stejnou udalost; po prevzeti expirovaneho lease novym workerem je stary
  token odmitnut pro ack i retry.
- Ack i retry jsou idempotentni pri opakovani se stejnym aktualnim tokenem.
  Retry ma odlozene `available_at` a uklada jen kratky technicky error code.
  Simulovany pad replace pri lease/ack zachoval predchozi soubor.
- Gate ma 599 testu. Outbox testy pouzily pouze `/private/tmp`; zivy producent
  ani konzument nevznikl. Oba smoke checky prosly na PID 69869.
- Finalni pilot Faze 2.4 pridal redigovanou e-mailovou decision udalost a
  idempotentni technicky auditni konzument. Udalost obsahuje pouze hashovanou
  referenci a akci. Pad po auditu pred ACK nevytvoril pri replayi duplicitu.
- Realny provoz overil 22 udalosti, 22 auditu, 22 delivered a 0 pending. Ve
  stejne rucni davce proslo 5 presunu do kose, 1 archivace a 1 import prilohy
  bez chyby; providerove akce nebyly soucasti auditniho konzumenta.
- Test odhalil transientni purge seznam v browseru. Soucasnych 5 polozek po
  zavreni okna nelze bezpecne identifikovat pro trvaly purge a zustavaji v
  kosi. Budouci trash log persistuje kosove UID/Message-ID a Work Queue umi po
  otevreni obnovit jen bezpecne identifikovatelne nepurgovane polozky. Stare
  nekompletni zaznamy se nikdy nehádají ani automaticky nemazou.
- Gate ma 606 testu, monolit 19 602 radku a oba smoke checky prosly na jedine
  instanci PID 85842. Faze 2.4 je uzavrena.
- Navazujici e-mailovy UI fix prejmenoval hlavni navigaci na `Zpet do Cockpitu`
  a pridal do Work Queue samostatne `Zpet na e-maily` i `Zpet do Cockpitu`.
  Vsechny cesty maji fallback na primou URL, kdyz prohlizec odmitne zavrit nebo
  fokusovat popup. Gate ma 607 testu; oba smoke checky prosly na PID 87379.

Co neni hotove:

- Zakladni stabilizace, HTTP hranice a iPhone hlas jsou funkcne potvrzene; PDF
  browser retest Mila vedome odlozil a post-call audio recovery ceka na pozdejsi
  rucni retest; ani jedno neni blokujici pro dalsi architekturu.
- Sdilena persistence, zakladni VoiceBridge persistence, hlavni reminders store
  a Quick Notes i urgent-reminders index jsou zamcene. Dokumenty a e-maily
  jeste nejsou globalne transakcni; metadata, reading status a ScanDocu review
  uz maji recovery transakci, ale dalsi document-index writery na ni nejsou
  prevedene.
- `app/cockpit.py` zustava monolit s backendem, HTML, CSS a JavaScriptem;
  status/health a VoiceBridge command ownership jsou uz vyjmuty, dalsi hranice
  jsou dokumentove routy a service vrstva.
- Cleanup R1 je hotovy. Stary e-mailovy parser, lokalni Janicka vetev a pet
  podezrelych API cest zustavaji beze zmeny; u API cest chybi registr externich
  klientu.
- Python zavislosti zatim nejsou pripnute na konkretni verze.
- VoiceBridge ma explicitni stavovy model pro coordinator i watcher. Dalsi
  budouci rozsireni ma smysl jen pokud bude potreba outbox/idempotency pres
  restart procesu, ne jako dalsi ad-hoc sada status stringu.
- Dokumentove a e-mailove workflow maji jednotne read-only pracovni modely.
  Repository zaklad, prvni e-mailovy decision adapter, delivery protokol i
  nedestruktivni runtime pilot jsou hotove. Ostatni zapisovaci workflow nejsou
  plosne prevedena.

Dalsi krok:

Faze 2.1 az 2.4 jsou uzavrene a overene. Pred Fazi 3 je doporuceny navrat k
Fazi 1.4: vyjmout e-mailove routy a service vrstvu z Cockpit monolitu s vyuzitim
hotoveho work modelu a repository adapteru. Dokumentovy reindex a dalsi writery
zustavaji oddelenou persistence roadmapou.
Dokumentovy reindex zustava vedlejsi persistence roadmapou. Stary e-mailovy
parser, lokalni Janicka vetev a pet podezrelych API cest zatim nemenit. PDF
browser a post-call audio retest jsou odlozene.

Vedle roadmapy vznikl 2026-07-12 maly TVBCP nastroj pro docasny VoiceBridge
brainstorming. Soukromy `data/private/voice_bridge/TVBCP_current.txt` je mimo
git, Cockpit jej pouze cte v panelu uvnitr hlavni stranky a
`scripts/tvbcp.py append` pridava zamcene zaznamy. Uchovava plne vecne zneni
podstatnych navrhu a myslenek Mily i Adama, ale vynechava technicke mezistavy,
testy, prikazy a provozni hlaseni. Nic automaticky nemaze nebo nepresouva.
Gate ma 611 testu; lokalni i Tailscale smoke check prosly na jedine instanci
PID 94652. Panel se po otevreni nebo rucnim obnoveni posune na nejcerstvejsi
konec protokolu.

Navrhovane dalsi kroky:

1. Faze 1.3: vyjmout dokumentove routy a service vrstvu po malych balicich.
2. Janicka a stary e-mailovy parser mazat az po popsanem rucnim/recovery overeni.
3. Podezrele API cesty proverit proti Shortcuts a servisnim klientum.
4. Ve vedlejsi persistence roadmapě pozdeji prevest reindex a potom e-mail metadata.
5. Postupne rozdelit monolit pri zachovani endpointu:
   status/health -> voice -> documents -> email -> staticky frontend.
6. Zavadet explicitni stavove modely a repository vrstvy po oblastech, ne
   jednim velkym prepisem.

Handoff strategie pro tento program:

- `AuditCockpit56.txt` je hlavni roadmapa a zdroj architektonickych zaveru.
- Tento soubor je jediny prubezny aktivni handoff.
- Novy handoff nevytvaret po kazdem pracovnim dni ani drobne oprave.
- Pri dokonceni velke faze vytvorit jeden finalni checkpoint a tento current
  handoff prepnout na dalsi fazi.
- Pocitat nejvyse s peti finalnimi fazovymi checkpointy:
  1. stabilizace a HTTP bezpecnost,
  2. jedna instance a bezpecne ukladani,
  3. rozdeleni monolitu,
  4. VoiceBridge stavovy model,
  5. dokumenty, e-maily a zaverecne UI/testy.

Zmenene nebo relevantni soubory:

- `AuditCockpit56.txt`
- `app/cockpit.py`
- `app/cockpit_status_service.py`
- `app/documents/case_service.py`
- `app/documents/due_date_service.py`
- `app/documents/intake_service.py`
- `app/documents/intake_models.py`
- `app/documents/review_service.py`
- `app/documents/search_service.py`
- `app/email/work_models.py`
- `app/email/work_repository.py`
- `app/email/work_outbox.py`
- `app/work_repository.py`
- `app/voice_bridge_coordinator.py`
- `app/voice_bridge_state.py`
- `app/tvbcp.py`
- `app/file_persistence.py`
- `app/backup/activity_state.py`
- `scripts/cockpit_smoke_check.py`
- `scripts/tvbcp.py`
- `tests/test_cockpit.py`
- `tests/test_cockpit_status_service.py`
- `tests/test_document_case_service.py`
- `tests/test_document_due_date_service.py`
- `tests/test_document_intake_service.py`
- `tests/test_document_intake_models.py`
- `tests/test_document_review_service.py`
- `tests/test_document_search_service.py`
- `tests/test_email_work_models.py`
- `tests/test_email_work_repository.py`
- `tests/test_email_work_outbox.py`
- `tests/test_work_repository.py`
- `scripts/email_work_outbox_pilot.py`
- `tests/test_voice_bridge_coordinator.py`
- `tests/test_voice_bridge_state.py`
- `tests/test_tvbcp.py`
- `tests/test_file_persistence.py`
- `scripts/install_cockpit_local_launchd.sh`
- `scripts/install_cockpit_tailscale_launchd.sh`
- `scripts/migrate_cockpit_single_instance.py`
- `tests/test_migrate_cockpit_single_instance.py`
- `tests/test_cockpit_http_security.py`
- `reports/cockpit_persistence_write_map_2026_07_10.md`
- `reports/cockpit_function_inventory_audit_2026_06_27.md`
- `reports/cockpit_post_action_risk_matrix_2026_06_27.md`
- `handoffs/voicebridge_operational_contract_2026_06_30.md`

Bezpecnost / neukladat:

- Neukladat obsahy soukromych dokumentu, e-mailu ani hlasovych pokynu.
- Neukladat tokeny, hesla, API klice, cele e-mailove adresy ani private vault data.
- Pred zasahem do VoiceBridge znovu precist jeho provozni kontrakt a zachovat
  pravidlo jedineho vlastnika doruceni.
- Prechod na jednu instanci nesmi prerusit lokalni ani iPhone pristup; musi mit
  predem popsany rollback a smoke check.
- Aktualni rollback prikaz je
  `.venv/bin/python scripts/migrate_cockpit_single_instance.py --rollback`;
  nepouzivat ho bez duvodu, pokud jedna instance a Tailscale proxy funguji.
- Existujici dokumenty pri budouci migraci nepresouvat ani nemazat bez
  samostatneho potvrzeni.
- HTTP event log je private provozni diagnostika; nikdy do nej nepridavat JSON
  payloady, query parametry, request hlavicky ani texty hlasu/e-mailu/dokumentu.
