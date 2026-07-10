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

Co neni hotove:

- Zakladni stabilizace, HTTP hranice a iPhone hlas jsou funkcne potvrzene; PDF
  browser retest Mila vedome odlozil a neni blokujici pro dalsi architekturu.
- Sdilena persistence vrstva a prvni nizkorizikova integrace jsou hotove, ale
  prime JSON/JSONL zapisy VoiceBridge, reminders, dokumentu a e-mailu na ni
  jeste nejsou prevedene.
- `app/cockpit.py` zustava monolit s backendem, HTML, CSS a JavaScriptem.
- VoiceBridge nema jeden explicitni stavovy model prikazu.
- Dokumentove a e-mailove workflow nemaji jednotnou repository/transakcni
  vrstvu.

Dalsi krok:

Po potvrzeni prvniho persistence rezu pokracovat dalsi malou davkou ve
VoiceBridge: nejdrive prevest pouze samostatne JSON stavove prepisy, ktere
neprovadeji read-modify-write. Zachovat cesty i format, pridat cilene regresni
testy a test selhani zapisu. Pending workflow, historie JSONL a vlastnictvi
doruceni nemenit ve stejne davce. PDF browser retest zustava odlozeny.

Navrhovane dalsi kroky:

1. Prevest samostatne VoiceBridge JSON stavove prepisy na sdilenou vrstvu.
2. Samostatne resit pending read-modify-write a hlasovou JSONL historii.
3. Po malych davkach prejit na reminders, dokumenty a nakonec e-mail metadata.
4. Postupne rozdelit monolit pri zachovani endpointu:
   status/health -> voice -> documents -> email -> staticky frontend.
5. Zavadet explicitni stavove modely a repository vrstvy po oblastech, ne
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
- `app/file_persistence.py`
- `app/backup/activity_state.py`
- `scripts/cockpit_smoke_check.py`
- `tests/test_cockpit.py`
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
