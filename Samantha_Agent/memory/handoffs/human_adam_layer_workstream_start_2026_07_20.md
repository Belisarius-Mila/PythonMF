<!-- SAMANTHA_CURRENT_STATUS_START -->
## Společné vydání všech dokončených commitů, 2026-11-12

Míla výslovně zadal p+n a úklid. E-mailové etapy3+4 a Datův HA-05 jsou
integrované;192 integračních PASS.39 starých plně převzatých větví uklizeno
se zálohou a zachováním všech souborů. Datův nezapsaný HA-06 ve vlastním
worktree zůstává nedotčený. Jediné registrované p+n, request `email-ha-all-finished-20261112-v1`;
přesný výsledek pouze v původní účtence job `b794e9f91e021059c97a7851827e6160` a
reports/all_finished_email_ha_release_20261112.md. Vývojový checkpoint není
doklad vydání. Další krok: dokončit zadané p+n a živou kontrolu. Hodinová
kopie7f47a41f/monitoroff zachované, upgrade/aktivace a skutečná přejímka zvlášť.


## Aktuální stav — HA-05, živá karta nad HA-04

- 2026-11-12: Na Mílův pokyn implementováno lokálně v Data. Dokončený HA-04
  72e1015c přijat fast-forwardem jen do data/parallel-20261104; Willův checkout
  a jeho publikace nedotčené. Veřejná projekce je napojená za scope/owner guardem.
- Hlavička ukazuje aktuální práci; Práce / Probíhá živý plán, veřejné komentáře,
  doloženou aktivitu, čas od přijetí, poslední změnu a poslední úspěšné čtení.
  Chybějící plán, zkrácení a gap jsou výslovné; žádné smyšlené procento.
- Automatický GET s cursorem, bounded history/backoff/deadline, resync a obnova
  stejné reference po načtení. Konečný/neověřený stav sledování ukončí.
  Jeden POST /work/start; ztracené ACK vyvolá pouze dohledání původní identity.
- Editor/fokus/selection, starší chat a běžící řeč zůstávají stabilní. Návrat
  z bfcache zachová rozepsaný text. Raw reasoning/tool args se nezobrazují.
- Veřejný filtr propouští jen typované kroky plánu a hotové commentary zprávy;
  nejvýše 32×1000 znaků / 16×2000 znaků. Staré terminalní veřejné detaily se
  kompaktně vyřazují, trvalá identita nadále brání opakovanému provedení.
- 417 finálních cílených testů OK / 17,214 s, včetně skutečného HA-04 producenta,
  observeru, wire scope a retence. 18 Node scénářů, 11 testů veřejné projekce;
  140 skutečných browser kontrol PASS na pěti velikostech. Viditelná změna
  v lokálních fixtures 723–733 ms; aktivní karta vizuálně zkontrolovaná.
- Plná regresní brána: 3648 testů OK / 534,548 s, 5 SKIP. Report reports/human_adam_ha05_live_ui_20261112.txt.
  Žádné skutečné App Server spojení, placené/modelové pokusy, služby/role
  ani p+n touto prací. Živá Mac/iPhone přejímka zůstává samostatná.
- Další krok: HA-06 na další zadání; případné společné vydání a živou přejímku
  řídit samostatně. HA-04 p+n má vlastní Willovu účtenku, není vydáním HA-05.
<!-- SAMANTHA_CURRENT_STATUS_END -->

Nazev: Human–Adam / vyvojove prostredi - zalozeni pracovniho proudu Layer
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-20

Co se resilo:
Krok 0 transformace r-Adama smerem k jednodussimu modelu pracovnich proudu.
Prvnim bodem bylo zalozit kanonicky pracovni proud typu Layer bez funkcni zmeny.

Co je hotove:
- V `WORKSTREAMS.md` je zalozen aktivni pracovni proud
  `layer-human-adam-development` typu `Layer` s kanonickym nazvem
  `Human–Adam / vyvojove prostredi`.
- Pracovni proud je dohledatelny z `MEMORY_INDEX.md`.
- Existujici oblast `App-server rozhrani / novy Adam` je vedena jako docasny
  kompatibilni zdroj, nikoli jako druhy projekt.
- Stavajici oddelene vlakno Human–Adam je zachovane; jeho soukromy identifikator
  se do Gitu neuklada.
- Stavajici `tvbcp/architektura_komunikace_samantha.txt` je potvrzen jako
  kanonicky TVBCP tohoto Layeru a je obousmerne propojen s registrem i handoffem.
- TVBCP obsahuje novy kanonicky jednoduchy model pracovnich proudu a presny
  seznam nahrazenych a zachovanych starsich pravidel.
- Read-only baseline bodu 0.4 potvrdil Cockpit smoke 5/5, dostupne hlavni UI,
  bezici app-server, zachovane vlakno Knihovny, dva ciste profilove workspaces a
  zdrave read-only Human–Adam API.
- Read-only baseline tehdy zachytil oba profilove workspaces pred beznou
  synchronizaci novych pametovych commitu ze zdrojoveho `main`.
- Regresni bod 0.5 prosel: Python kompilace, JavaScript hlavniho i Human–Adam UI,
  shell syntaxe, plna sada 856 testu za 198,475 sekundy a nasledny zivy Cockpit
  smoke test 5/5.
- Faze 1.1 pridala samostatny, zatim neaktivni backend jednoducheho checkpointu:
  preflight, plna brana, automaticky TVBCP + handoff, jeden commit na profilovem
  `main`, push stejneho objektu, fast-forward zdrojoveho `main` a zarovnani
  workspace bez nove vetve a bez persistentniho semaforu.
- Novych 7 integracnich testu proslo za 33,252 sekundy; plna Cockpit brana ma
  nyni 863 zelenych testu za 239,055 sekundy a nasledny zivy smoke je 5/5.
- Krok 0 nemenil kod ani runtime. Faze 1.1 meni pouze novy neaktivni backend,
  workspace path-policy helper, testy a quality gate; UI, API a bezici runtime
  zustavaji beze zmeny.
- Faze 1.2 napojila neaktivni backend na kanonickou konfiguraci aktivniho
  profilu. Profil Human–Adam vlastni ID `layer-human-adam-development`, typ
  `Layer`, nazev, handoff a TVBCP; klient tyto udaje nemuze volne zadat.
- Profilovy manager sklada checkpointovy request pouze z teto vazby, drzi
  aktivni profil po celou operaci a predava backendu ostatni profilove workspaces
  jako peer kontrolu. Vysledek nese potvrzenou identitu profilu a proudu.
- Knihovna nema pro novy tok vymyslenou implicitni vazbu: dokud jeji konkretni
  proud nezaregistrujeme v terminalu, novy checkpoint skonci fail-closed.
- Tri nove profilove testy zvysily plnou sadu na 866 testu. Cilena sada 34 testu
  i plna Cockpit brana prosly; plna sada bezela 235,895 sekundy a gate 240,1 s.
- Nasledny zivy read-only Cockpit smoke test prosel 5/5.
- Faze 1.2 nepridala API route, tlacitko ani zmenu UI a neaktivovala novy tok v
  bezicim Cockpitu.
- Faze 1.3 pridala samostatny neveřejny `HumanAdamWorkstreamCoordinator`.
  Koordinator vede validovany katalog, mapuje ID proudu na existujici izolovany
  profil a nikdy nevystavuje soukrome identifikatory vlaken.
- Human–Adam je v katalogu `Layer` `layer-human-adam-development`; Knihovna je
  zkušebne pripojena jako `Project` `project-knowledge-library` se svym
  stavajicim vlaknem, TVBCP, handoffem a workspace.
- Neveřejna metoda `select_workstream()` preklada vybrany proud na profil a
  deleguje na stavajici provereny prepinac. Tim zachovava ochranu aktivniho tahu,
  nejisteho doruceni a rozpracovane prace a automaticky fast-forwarduje cisty
  cil z commitnuteho lokalniho `main`.
- Zkušebni prechod Human–Adam -> Knihovna -> Human–Adam prosel vcetne
  automaticke synchronizace obou cilu. Neznamy proud a nečisty aktualni projekt
  zustavaji fail-closed.
- Cilena sada ma 38 zelenych testu. Plna Cockpit brana prosla 870 testy za
  179,167 sekundy; cela brana trvala 182,0 s a zivy smoke prosel 5/5.
- Faze 1.3 nezmenila API, UI, bezici profil, vlakno ani nasazeni.
- Faze 1.4 napojila stavajici vyberove menu na koordinator bez noveho prvku,
  tlacitka nebo CSS zmeny. Viditelne nazvy `Human–Adam` a `Knihovna`, popisek
  `Pracovni profil`, potvrzeni i rozlozeni zustaly zachovane.
- Status nyni vedle kompatibilnich `work_profile` / `work_profiles` poskytuje
  `workstream_selection`. UI bere polozky a aktivni proud prednostne odtud a pri
  starsim nebo nedostupnem katalogu umi zobrazit puvodni profilova data.
- Stavajici endpoint `/api/human-adam/profile` prijima `workstream_id` a vede jej
  pres `select_workstream()`. Puvodni `profile_id` zustava kompatibilnim
  fallbackem; pri novem payloadu ma kanonicky proud prednost.
- Interni `activeWorkstreamId` je oddeleny od `activeProfileId`, aby stare
  semaforove a nasazovaci vazby behem prechodu dal pracovaly s profilem.
- Cilena sada profilu, UI a checkpointu prosla 93 testy za 26,614 sekundy. Plna
  Cockpit brana prosla 871 testy za 170,754 sekundy; cela brana trvala 173,4 s.
- Prednasazovaci zivy Cockpit smoke prosel 5/5, ale nove menu jeste nebylo
  nasazeno ani rucne prokliknuto.
- Faze 1.4 byla commitnuta a pushnuta jako `6f17852`. Rizeny restart nahradil
  PID `94492` novym PID `37611` a code stamp se zmenil z `d25fa501fc5da9d5` na
  `7a4440b979d98690`; nasledny smoke prosel 5/5.
- Zivy endpointovy roundtrip pouzil nova kanonicka ID proudu. Vychozi aktivni
  Knihovna byla nejdrive bezpecne srovnana na Human–Adam, potom prosel presny
  sled Human–Adam -> Knihovna -> Human–Adam. Kazdy krok vratil spravny profil,
  proud, pripojenou relaci a cisty zarovnany workspace.
- Zaverecny audit potvrzuje oba profilove workspaces `aligned`, ciste, bez
  remote, lokalniho checkpointu, WIP a aktivniho tahu. Aktivni zustal Human–Adam.
- Mila nasledne rucne potvrdil i skutecne vizualni prepnuti Human–Adam ->
  Knihovna -> Human–Adam; faze 1.4 je tim provozne uzavrena.
- Faze 1.5 pridala private strukturovanou dokončovaci uctenku zapisovaciho tahu.
  Model ji smi pridat pouze po uspesne zmene souboru a zelenych relevantnich
  testech. Uctenka obsahuje jen nazev commitu, bezpecny souhrn a dalsi krok;
  pred zobrazenim Milovi se odstrani z odpovedi.
- Profilovy manager po platne uctence a skutecne necommitovane zmene automaticky
  spusti existujici direct-main backend: plnou branu, zapis do kanonickeho
  handoffu a TVBCP, jeden commit, push a zarovnani profilovych workspace.
- Ostatni ciste profily se po uspesnem commitu automaticky fast-forwarduji na
  stejny `main`. Pokud jejich dorovnani selze, commit zustava platny a vysledek
  poctive hlasi sync pending misto predstiraneho uplneho uspechu.
- Chybejici nebo neplatna uctenka, read-only tah, neuspesna brana, Git konflikt
  nebo opakovane doruceni stejne zpravy nevytvori zadny druhy commit. Puvodni
  zmeny nebo zachovany lokalni commit zustanou viditelne pro obnovu.
- Technicka uctenka se bezpecne odstrani i z persistovane odpovedi Session Hubu;
  pozdejsi idempotentni nacteni proto neukaze interní protokol ani jej nespusti
  znovu.
- Faze 1.5 nepridala novou API cestu, tlacitko ani zmenu HTML/CSS. Stary panel
  Prace zustava behem transformace kompatibilnim mostem.
- Cilena sada 59 testu prosla vcetne UTC runner regrese za 38,877 sekundy. Samostatna syntakticka brana
  prosla Pythonem, JavaScriptem obou UI, shellem a `git diff --check`.
- Finalni plna Cockpit brana po oprave UTC/CEST prosla 880 testy za 239,849
  sekundy; cela testova cast brany trvala 243,6 sekundy a vysledek je `OK`.

Co neni hotove:
- Faze 1.5 je commitnuta a pushnuta v `4bfd7fc`, ale zatim neni nasazena ani
  zive overena v Human–Adam tahu.
- Existujici checkpointove tlacitko a stary nasazovaci tok zatim zustavaji
  beze zmeny jako kompatibilni vratna cesta.
- Stary WIP/semafor/takeover tok zustava beze zmeny aktivniho runtime.
- Stary runtime nazev se zatim nesmi prejmenovat, protoze jej pouziva soucasna
  profilova konfigurace Cockpitu.

### GitHub Actions incident pred checkpointem faze 1.5

Mila upozornil na dva e-maily o neuspesne Cockpit Quality Gate. Read-only GitHub
API audit je priradil behum `99eb092` v 07:39 CEST a `bad3067` v 08:55 CEST.
Oba mely shodnou pricinu: dva testy checkpointu ocekavaly `07:00 CEST`, ale
macOS GitHub runner prevedl vlozeny cas na svou systemovou zonu `05:00 UTC`.
Logika checkpointu, commitu ani push nebyla pricinou.

Oprava nastavuje kanonickou projektovou zonu `Europe/Prague` pro vznik i format
checkpointoveho casu. Novy regresni test predava cas z UTC runneru a doklada
vystup `2026-07-20 07:00 CEST` nezavisle na zone hostitele. Cilena sada po oprave
prosla 59 testy za 38,877 sekundy. Finalni plna brana pote prosla 880 testy za
239,849 sekundy.

Dalsi krok:
Nasazeni, rizeny restart a prvni maly zivy zapisovaci tah proverit az
samostatnym potvrzenym krokem.

Navrhovane dalsi kroky:
- Pro dalsi proud nejdrive v terminalu zaregistrovat konkretni `Project`, `Tool`,
  `Layer` nebo `Misc`; nevymyslet vazbu pri kliknuti v r-Adamovi.
- Po nasazeni otestovat jeden maly zapisovaci tah nejdrive v Human–Adam; teprve
  potom stejnou cestu pouzit v Knihovne.
- Zachovat UI a zakladni funkce po celou dobu postupne transformace.

Zmenene nebo relevantni soubory:
- `memory/WORKSTREAMS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`
- `memory/ACTIVE_PROJECTS.md`
- `app/communication/human_adam_profiles.py`
- `app/communication/human_adam_turn_completion.py`
- `app/communication/session_hub.py`
- `app/communication/simple_main_checkpoint.py`
- `app/communication/human_adam_workspace.py`
- `tests/test_simple_main_checkpoint.py`
- `scripts/cockpit_quality_gate.py`

Bezpecnost / neukladat:
- Neukladat soukrome identifikatory vlaken, tokeny ani private obsah.
- Nemenit stary runtime nazev bez samostatne overene migrace.
- Mila autorizoval checkpoint, commit a push faze 1.5; nasazeni ani restart tim
  autorizovane nejsou.

### Checkpoint faze 1.5

Dne 2026-07-20 10:16 CEST byla faze 1.5 vcetne opravy UTC/CEST commitnuta jako
`4bfd7fc` (`Automate Human-Adam turn completion`) a pushnuta na `origin/main`.
Lokalni `main` a `origin/main` se po pushi shodovaly. Skutecna GitHub Cockpit
Quality Gate nad presnym commitem `4bfd7fc` skoncila `success`; tim je potvrzeno,
ze predchozi runnerova regrese casove zony je opravena i mimo lokalni Mac.

Tento checkpoint neautorizuje nasazeni ani restart. Dalsi krok je samostatne
nasazeni, rizeny restart, smoke test a jeden maly zivy zapisovaci tah.

### Zivy zapisovaci test automatickeho dokonceni faze 1.5

2026-07-20 10:29 CEST: Nasazeny Cockpit ma PID `58874` a kodovy otisk
`7c04aaa979f6dd9c`. Restart probehl rizene a smoke test prosel `5/5`. Jde o
zivy zapisovaci test automatickeho dokonceni faze 1.5.

### Automatický checkpoint 2026-07-20 10:34 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Živý zapisovací test fáze 1.5 prošel
- Ověření: plná Cockpit brána: 880 testů, 259.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (1): `Samantha_Agent/memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`
- Commit: `Verify Human-Adam automatic completion live`
- Další krok: Ověřit čistý main, synchronizaci profilů a uvolnit přechodný semafor

### Fáze 2.1 – neveřejné jednoduché nasazení z čistého main

Dne 2026-07-20 11:27 CEST vznikl samostatný backend jednoduchého nasazení z
přesného čistého `main`. Backend nemá API route, tlačítko ani automatické
spuštění a nemění současné UI nebo běžící Cockpit.

Před restartem backend vyžaduje výslovné potvrzení, přesný očekávaný commit,
zdrojovou větev `main`, čistý lokální `main`, shodný čerstvě načtený
`origin/main` a všechny profilové workspaces čisté, bez remote a zarovnané na
stejném commitu. Potom spustí plnou Cockpit bránu, znovu ověří Git i profily a
stálý očekávaný kódový otisk. Teprve pak uloží soukromou účtenku
`pending_restart`.

Po restartu druhá část backendu vyžaduje nový PID, přesný kódový otisk, stále
shodný `main` / `origin/main`, oba čisté profily a kanonický smoke test `5/5`.
Jedině úplný důkaz povýší soukromou účtenku na `deployed`. Chybný otisk, stejný
PID, neúplný smoke, nečistý profil, změna main nebo vzdálený závod ponechají
nasazení nedokončené.

Backend nevytváří větev, WIP checkpoint ani takeover a nečte ani nemění globální
vývojový semafor. Nový testovací modul má 7 zelených scénářů; společná cílená
sada s testy quality gate prošla 14 testy. Plná Cockpit brána prošla 887 testy
za 275,223 sekundy a skončila `OK` za 278,8 sekundy.

Změněné soubory fáze 2.1:

- `app/communication/simple_main_deploy.py`
- `tests/test_simple_main_deploy.py`
- `scripts/cockpit_quality_gate.py`

Fáze zatím není commitnutá, pushnutá, napojená na profilový manager ani
nasazená. Další krok: checkpoint + commit + push fáze 2.1; potom fáze 2.2 může
backend napojit na kanonický pracovní proud a existující bezpečný restart worker,
stále bez změny UI.

### Fáze 2.2 – napojení na kanonický profilový koordinátor

Dne 2026-07-20 11:59 CEST profilový manager převzal neveřejné napojení backendu
fáze 2.1. Aktivní pracovní proud, přesný commit zdrojového `main`, primární
workspace, všechny ostatní profilové workspaces a soukromá cesta účtenky se
odvozují výhradně ze serverové kanonické konfigurace; klient je nemůže zadat.

Příprava i dokončení nejdřív ověří, že žádný registrovaný profil nemá aktivní
tah nebo nevyřešené doručení. Příprava může po úplném zeleném důkazu zavolat
volitelný důvěryhodný callback existujícího řízeného restart workeru. Bez něj jen
pravdivě hlásí, že restart je připravený; při selhání naplánování zůstane
soukromá účtenka v obnovitelném stavu `pending_restart`.

Post-restartové ověření načte pracovní proud ze soukromé účtenky a přijme jej
jen tehdy, pokud je stále aktivní tentýž kanonický profil. Potom předá backendu
pozorovaný PID, kódový otisk a oba serverem vybrané workspaces. Semafor, WIP,
takeover ani klientský projektový výběr se této cesty neúčastní.

Šest nových manager testů pokrývá Human–Adam, Knihovnu, serverem odvozený commit
a peer workspace, volitelný restart worker, aktivní nebo nejistý tah v libovolném
profilu, selhání restart scheduleru, post-restartové ověření a odmítnutí jiného
aktivního proudu. Cílená sada `human_adam_profiles` + `simple_main_deploy` prošla
47 testy. Plná Cockpit brána prošla 893 testy za 223,196 sekundy a skončila
`OK` za 226,2 sekundy.

Fáze 2.2 nemá API route, HTML, CSS ani změnu současného UI a nebyla commitnutá,
pushnutá nebo nasazená. Změněné soubory jsou pouze
`human_adam_profiles.py`, `test_human_adam_profiles.py`, tento handoff a
kanonický TVBCP. Další krok: checkpoint + commit + push fáze 2.2; potom vytvořit
neveřejnou app-layer akci, která manager propojí s existujícím restart workerem,
stále bez přepnutí UI.

### Fáze 2.3 – neveřejná aplikační akce řízeného restartu

Dne 2026-07-20 12:20 CEST vznikla v aplikační vrstvě soukromá akce, která
propojuje profilový koordinátor fáze 2.2 s existujícím bezpečným restart workerem
Cockpitu. Aplikační vrstva sama odvozuje PID běžícího procesu, host a port;
manager nadále výhradně odvozuje aktivní pracovní proud, přesný `main`, profily
a cestu soukromé účtenky.

Restart callback se předá manageru, ale worker se zavolá až po úspěšném úplném
předrestartovém důkazu. Worker znovu ověří, že PID patří skutečnému Cockpit
serveru, a až potom spustí oddělený `restart_cockpit.py`. Chyba manageru nebo
restartu se vrací jako pravdivý bezpečný neúspěch; akce nevytváří větev, WIP,
takeover ani semafor.

Akce je záměrně neveřejná: nemá HTTP route, kartu v registru akcí, HTML, CSS ani
tlačítko. Tři nové přímé testy dokazují předání serverového PID a síťového
kontextu workeru, bezpečné vrácení chyby bez restartu a nepřítomnost API/UI
povrchu. Širší cílená sada prošla 303 testy. Plná Cockpit brána prošla syntaxí
a 896 testy za 210,122 sekundy; celá brána skončila `OK`.

Změněné soubory fáze 2.3 jsou `app/cockpit.py`, `tests/test_cockpit.py`, tento
handoff a kanonický TVBCP. Fáze zatím není commitnutá, pushnutá ani nasazená.
Další krok: checkpoint + commit + push fáze 2.3; potom neveřejně napojit
post-restartové ověření na serverem odvozený nový PID a `COCKPIT_CODE_STAMP`,
stále bez změny UI.

### Fáze 2.4 – neveřejné potvrzení dokončení po restartu

Dne 2026-07-20 12:56 CEST vznikla soukromá aplikační akce pro druhou polovinu
jednoduchého nasazení. Akce přijímá pouze serverem vytvořený profilový manager;
skutečný PID nového procesu bere z běžícího Cockpitu a kódový otisk z kanonické
konstanty `COCKPIT_CODE_STAMP`. Klient nemůže dodat ani změnit žádný důkaz.

Manager váže tyto údaje na čekající soukromou účtenku a stejný aktivní pracovní
proud. Dále používá již otestovaný kontrakt fáze 2.1: vyžaduje nový PID, přesný
otisk, stále čistý a synchronní `main`, oba profilové workspaces a kanonický
smoke test `5/5`. Teprve úplný důkaz změní účtenku z `pending_restart` na
`deployed`; chyba se vrátí pravdivě a účtenka se nepovýší.

Akce nemá HTTP route, kartu v registru, HTML, CSS ani tlačítko. Dva nové přímé
testy ověřují serverový PID a otisk i bezpečné vrácení chyby; rozšířený test
zároveň chrání nepřítomnost veřejného povrchu. Širší cílená sada prošla 305
testy. Plná Cockpit brána prošla syntaxí a 898 testy za 217,666 sekundy; celá
brána skončila `OK`.

Změněné soubory fáze 2.4 jsou `app/cockpit.py`, `tests/test_cockpit.py`, tento
handoff a kanonický TVBCP. Fáze zatím není commitnutá, pushnutá ani nasazená.
Další krok: checkpoint + commit + push fáze 2.4. Potom samostatně navrhnout
nejmenší řízené přepojení existujícího workflow na dokončenou soukromou cestu
2.1–2.4 při zachování současného vzhledu UI.

### Fáze 3.1 – přepojení stávajícího nasazovacího ovládání

Dne 2026-07-20 13:22 CEST bylo existující ovládání `Audit nasazení` a `Ověřit a
nasadit` přepojeno ze staré WIP/takeover cesty na jednoduchou cestu 2.1–2.4.
Rozložení okna, názvy tlačítek a potvrzovací textové pole zůstaly zachované.
Historické poznámky fází 2.3 a 2.4 o nepřítomnosti route popisují tehdejší stav;
fáze 3.1 je záměrně nahrazuje tímto řízeným veřejným napojením.

Read-only audit nyní serverově ověří aktivní kanonický pracovní proud, přesný
čistý `main`, shodu s `origin/main`, očekávaný kódový otisk a bezpečný stav obou
profilových workspaces. Vrací novou přesnou větu
`POTVRZUJI NASAZENI CISTEHO MAIN`. Klient neposílá commit, PID, otisk, workspace
ani cestu účtenky.

Potvrzené nasazení volá novou aplikační akci, spustí plnou bránu, uloží soukromou
účtenku a teprve potom řízený restart. Po návratu nového PID stejné frontendové
okno automaticky zavolá serverovou verifikaci. Ta znovu ověří PID, otisk, Git,
profily a smoke `5/5`; stránka se obnoví až po stavu `deployed`. Neúspěch zůstane
viditelný a nepředstírá dokončení.

Praktická synchronizace: čistý peer profil smí být při auditu bezpečně o commit
pozadu. Potvrzené nasazení jej před plnou branou automaticky dorovná na přesný
`main`. Dirty, lokálně napřed, rozvětvený nebo jinak nejistý profil zůstává
blokující. Samotná deploy cesta nepoužívá WIP větev, takeover ani globální
semafor. Starý backend zůstává v kódu, ale route jej již nevolá.

Nápověda `Práce` dostala nahoře krátký aktuální čtyřkrokový postup; ostatní
vizuální struktura zůstala zachovaná. Cílená sada backendu, profilů, UI a
Cockpitu prošla 363 testy. Plná Cockpit brána prošla Python, JavaScript i shell
syntaxí a 902 testy za 298,217 sekundy; celá brána skončila `OK`.

Změněné implementační a testovací soubory jsou `app/cockpit.py`,
`app/communication/human_adam_profiles.py`, `human_adam_ui.py`,
`simple_main_deploy.py` a jejich čtyři odpovídající testovací moduly, dále tento
handoff a TVBCP. Fáze zatím není commitnutá, pushnutá ani nasazená.

Další krok: checkpoint + commit + push fáze 3.1. Potom jednorázově nasadit nový
kód terminálovým řízeným restartem a smoke testem; teprve z nového Cockpitu lze
provést první plný živý roundtrip nové samoobslužné cesty.

### Fáze 3.1a – zachování potvrzení nasazení po reloadu

Dne 2026-07-20 14:18 CEST byl vyhodnocen první živý roundtrip fáze 3.1. Backend
uspěl úplně: účtenka `deployed`, commit `fca389d`, nový PID `27273`, správný
kódový otisk, 902 testů a smoke `5/5`; oba profily byly čisté a synchronní.
Frontend však po ověření okamžitě obnovil stránku, zavřel panel `Práce` a ukázal
poslední starší konverzační zprávu. Její čas `11:01:48` patřil starému tahu, ne
nasazení. Šlo o UX chybu, nikoli o selhání deploy cesty.

Oprava ukládá po úplné serverové verifikaci do `sessionStorage` pouze jednorázový
krátký záznam: zkrácený commit, počet testů, smoke `5/5`, čas dokončení a lokální
čas uložení. Neukládá text konverzace, profil, projekt, handoff, cestu, PID ani
jiná soukromá data. Záznam má schéma, přísnou validaci, maximální stáří 15 minut
a při prvním načtení se vždy odstraní.

Po reloadu frontend záznam jednorázově převezme, znovu otevře panel `Práce`,
načte jeho aktuální stav a teprve potom zobrazí jasnou hlášku ve tvaru
`Nasazeno a ověřeno · main … · … testů · smoke 5/5 · dokončeno …`. Když
`sessionStorage` není dostupný, reload se neprovede a stejná potvrzovací hláška
zůstane viditelná přímo v již otevřeném panelu.

Serverová verifikace nově vrací již ověřený počet testů, dobu brány a čas
dokončení z účtenky; klient si tyto hodnoty nevymýšlí. Cílená sada prošla 323
testy. Plná Cockpit brána prošla Python, JavaScript i shell syntaxí a 903 testy
za 227,723 sekundy; celá brána skončila `OK`.

Změněné soubory jsou `simple_main_deploy.py`, `human_adam_ui.py`, jejich dva
testovací moduly, tento handoff a TVBCP. Fáze zatím není commitnutá, pushnutá ani
nasazená. Další krok: checkpoint + commit + push fáze 3.1a. Potom synchronizovat
aktivní profil přes `Připojit` a novou samoobslužnou cestou nasadit právě tuto
opravu; úspěšný test musí po restartu znovu otevřít `Práci` a zachovat potvrzení.

### Fáze 3.1b – komunikační vrstva je zahrnutá v CI triggerech

Dne 2026-07-20 14:45 CEST byla opravena mezera ve spouštěcích filtrech GitHub
workflow `Cockpit Quality Gate`. Samotný lokální i CI skript brány již dlouho
kompiloval a testoval moduly `app/communication`, ale YAML trigger byl starší
ručně vyjmenovaný seznam konkrétních cest. Při přidávání nových modulů a testů
se rozšiřoval manifest brány, nikoli vždy paralelně i tento samostatný seznam.

Mezeru dočasně maskovalo, že větší fáze současně měnily `app/cockpit.py` nebo
`tests/test_cockpit.py`, které ve filtru byly a workflow tím nepřímo spustily.
Fáze 3.1a změnila jen `human_adam_ui.py`, `simple_main_deploy.py` a jejich testy;
žádná z těchto konkrétních cest starému filtru neodpovídala. GitHub proto přesně
podle konfigurace spustil Pages, ale ne Cockpit Quality Gate. Nešlo o chybu
testů, GitHubu ani commitu, nýbrž o drift dvou ručně udržovaných seznamů.

Oba triggery `pull_request` i `push` nyní obsahují široké pravidlo
`Samantha_Agent/app/communication/**` a vzory pro komunikační, Human–Adam,
simple-main a local-appserver testy. Nový regresní test čte skutečný workflow,
vyžaduje všechny tyto vzory a navíc vyžaduje, aby množiny cest pro push a pull
request byly shodné. Nový komunikační modul se tedy už nemusí jednotlivě
dopisovat a jednostranná změna triggeru test rozbije.

Cílená sada workflow testů prošla 8 testy. Plná Cockpit brána prošla Python,
JavaScript i shell syntaxí a 904 testy za 248,925 sekundy; celá brána skončila
`OK` za 260,1 sekundy.

Změněné soubory jsou `.github/workflows/cockpit-quality-gate.yml`,
`test_cockpit_quality_gate.py`, tento handoff a TVBCP. Fáze zatím není
commitnutá ani pushnutá. Další krok: checkpoint + commit + push fáze 3.1b; změna
workflow sama musí spustit vzdálený Cockpit Quality Gate a tím opravu potvrdit.

### Fáze 3.1c – odolnost účtenky, Git fetch a app-serveru

Dne 2026-07-20 16:30 CEST byly tři provozní mezery spojené do jedné úzké
odolnostní opravy bez změny vzhledu Human–Adam. Předchozí nasazení commitu
`38cb187` bylo serverově úplné: účtenka `deployed`, 904 testů, smoke `5/5`, nový
PID `50753` a oba profily zarovnané. Panel `Práce` se přesto neobnovil, protože
nasazení zahájil ještě starý JavaScript bez markeru fáze 3.1a; nový kód se načetl
až po restartu. Šlo o jednorázovou bootstrap mezeru, ne o selhání nasazení.

Server nyní z privátní jednoduché účtenky odvozuje maximálně 15 minut starý
bezpečný souhrn jen pro aktivní kanonický pracovní proud. Do klienta neposílá
PID, socket, cestu, kódový otisk ani soukromý obsah. Nové UI po startu nejdřív
použije jednorázový `sessionStorage` marker; pokud chybí, převezme tento serverový
důkaz, otevře `Práci`, načte její stav a zobrazí commit, počet testů, smoke a čas.
V jedné browserové relaci si pouze poznamená již zobrazený otisk účtenky.

Dva lokální fetch přenosy selhaly na macOS chybou `mmap failed: Resource deadlock
avoided`. Audit prokázal, že reverse-index hlavního Git packu byl v iCloudem
spravované Ploše označený `dataless`; následná hláška o chybějících objektech byla
jen důsledek přerušeného přenosu. Synchronizace nyní před fetchem kontroluje
packové soubory. Malé odložené indexy do 16 MiB bezpečně načte, velký odložený
pack odmítne se srozumitelným pokynem `Zachovat stažené` a přesnou přechodnou
chybu `mmap` opakuje nejvýše jednou. Míla zároveň ve Finderu zapnul `Zachovat
stažené` pro celý `PythonMF`; následná kontrola nenašla žádný `dataless` Git
objekt.

App-server používá soukromou vlastnickou účtenku vedle socketu. Obsahuje jen
schéma, PID, přesnou procesní identitu a socketovou cestu. Nový controller smí
převzít i starší dosažitelný proces pouze po úspěšném socketovém handshaku a
shodě příkazu a procesní skupiny. Neodpovídající proces smí ukončit a nahradit
jen při úplné shodě účtenky, PID, identity, skupiny a socketu a jen pokud profil
nemá aktivní tah ani nejisté doručení. Cizí nebo neověřitelný socket zůstává
fail-closed. Startovací limit byl zvýšen z 12 na 30 sekund.

Cílená sada prošla 159 testy. Plná Cockpit brána prošla kontrolou diffu, Python,
oběma JavaScript a shell syntaxemi a 913 testy za 298,271 sekundy; skončila
`OK`. Změněné aplikační soubory jsou `simple_main_deploy.py`,
`human_adam_profiles.py`, `human_adam_ui.py`, `human_adam_workspace.py`,
`human_adam_service.py` a `local_runtime.py` se šesti odpovídajícími testovacími
moduly, tento handoff a TVBCP. Fáze zatím není commitnutá, pushnutá ani nasazená.

Další krok: checkpoint + commit + push fáze 3.1c. Po zeleném vzdáleném Quality
Gate ji nasadit současnou samoobslužnou cestou. Běžný reload musí obnovit panel
z browserového markeru; nový samostatný tab otevřený do 15 minut musí totéž
dokázat pouze ze serverové účtenky.

### Fáze 3.2 – zjednodušení běžného okna Práce

Dne 2026-07-20 17:40 CEST byl po dokončení direct-main checkpointu a nasazovací
cesty odstraněn z běžného zobrazení historický přechodový workflow. Okno
`Práce` nyní ukazuje pouze stav workspace, případné změny, audit čistého `main`,
přesnou potvrzovací větu a akci `Ověřit a nasadit`.

Globální semafor a jeho stavový štítek, projektová vazba, audit WIP větví,
ruční lokální WIP checkpoint, takeover kontrola, návrh handoffu a stará
dokončovací karta jsou označené jako skrytá kompatibilní vrstva. Backend ani
API se v této fázi nemažou, takže případná obnova zůstává vratná. Samostatné
okno `Plán` a rotace vláken se nemění; jejich budoucí zjednodušení musí zachovat
funkční výměnu kontextu a bude řešeno odděleně.

Nápověda `Práce` má nový krátký postup: vybrat pracovní proud a připojit se,
zadat úkol přímo Adamovi, nechat automaticky dokončit handoff + TVBCP + commit +
push do `main` a panel otevřít až pro kontrolu nebo nasazení. Zachovává také
stručný fail-closed postup při nečistém repu nebo chybě auditu.

Cílená sada `test_human_adam_ui` prošla 56 testy. Plná Cockpit Quality Gate
prošla kontrolou diffu, Python, oběma JavaScript a shell syntaxemi a 914 testy
za 301,907 sekundy; celá testovací část trvala 305,8 sekundy a výsledek je `OK`.
Vizuální kontrola nebyla v této Codex relaci dostupná, protože nebyl připojený
ovladatelný prohlížeč.

Změněné soubory fáze jsou `human_adam_ui.py`, `test_human_adam_ui.py`, tento
handoff a kanonický TVBCP. Další krok: commit + push fáze 3.2, počkat na zelenou
vzdálenou Quality Gate a potom nasadit simple-main cestou. Míla následně ověří,
že okno `Práce` obsahuje jen nový jednoduchý workflow.

### Potvrzení fáze 3.2 a plán univerzálního katalogu

Dne 2026-07-20 18:12 CEST je fáze 3.2 provozně potvrzená. Commit `6442954` byl
pushnutý na `main`, vzdálená Cockpit Quality Gate doběhla zeleně za 2 minuty
7 sekund a simple-main nasazení skončilo účtenkou `Nasazeno a ověřeno`, 914
testy a smoke `5/5`. Míla v živém panelu viděl už jen čistý workspace, žádné
pracovní změny a potvrzení nasazení.

Následná kanonická dohoda nahrazuje záměr registrovat jednotlivé projekty ručně.
Human–Adam má dostat jednotný katalog všech smysluplných pracovních proudů typu
`Project`, `Tool`, `Layer` a `Misc`. Aktivní položky budou běžně viditelné,
pozastavené dostupné odděleně a archivní nebudou zahlcovat běžné menu.

Každý pracovní proud vlastní své samostatné Codex vlákno, kanonický handoff a
TVBCP. Vlákno se má soukromě založit až při prvním otevření a potom trvale
zachovat; nemají vzniknout desítky trvale běžících app-serverů ani samostatných
WIP workspace. Aktivní může být jen jeden proud. Přepnutí vyžaduje dokončený
tah a čistý synchronní `main`; čistý pracovní workspace lze mezi proudy
bezpečně znovu použít.

Typ `Misc` bude mít dvě výchozí samostatné položky:

- `Brainstorm / nápady` pro volné přemýšlení bez změny kódu ve výchozím stavu;
  do TVBCP patří jen potvrzená rozhodnutí, ne kopie každé myšlenky.
- `Miscellaneous / nezařazený vývoj` pro malé skutečné změny, které zatím
  nepatří pod projekt, tool ani layer a používají běžný direct-main checkpoint.

Když se brainstorm změní na skutečný projekt, má být možné pracovní proud
překlasifikovat na `Project` se zachováním vlákna a dosavadních rozhodnutí.

Potvrzený implementační plán:

1. Fáze 4.1 – vytvořit úplný validovaný katalog aktivních projektů, toolů,
   vrstev a obou výchozích `Misc` proudů, zatím bez změny UI a bez zakládání
   vláken.
2. Fáze 4.2 – oddělit pracovní proud od dvou pevných profilů a zavést soukromé
   lazy založení a pozdější obnovení vlastního vlákna.
3. Fáze 4.3 – zajistit jeden kanonický handoff a TVBCP každého proudu a jejich
   automatickou průběžnou aktualizaci při checkpointu.
4. Fáze 4.4 – napojit stávající menu na skupiny `Projekty`, `Tooly`, `Vrstvy` a
   `Ostatní`; přepnutí zároveň bezpečně synchronizuje a připojí cílový proud.
5. Fáze 4.5 – zachovat stávající vlákna Human–Adam a Knihovny, migrovat MMTX,
   provést malý živý MMTX vývoj a až po úspěchu odstranit pevnou dvouprofilovou
   konstrukci.

Další krok po nové Codex relaci: načíst paměť a zahájit fázi 4.1 read-only
inventurou kanonických zdrojů a návrhem úplného katalogu. Nezačínat registrací
samotného MMTX a nevytvářet vlákna ani měnit UI v této první fázi.

### 2026-07-20 19:42 CEST – Checkpoint fáze 4.1: úplný katalog

Fáze 4.1 je implementačně hotová. Nový git-safe kodový katalog obsahuje 29
pracovních proudů: 23 projektů, 4 tooly a 2 `Misc`; 26 proudů je `active` a
projekty iPhone Shortcuts / Mobile Input, Vocabulary FR a Vocabulary IT jsou
`paused`. Všech 28 živých řádků `ACTIVE_PROJECTS.md` zůstává pokryto, ale podle
Mílova schválení se příbuzné technické řádky slučují do lidských pracovních
celků.

Kanonická rozhodnutí: Human–Adam, Cockpit, Katalog projektů a schopností,
Samantha Infrastructure a ColorsAndNumbers jsou projekty. Recovery centrum a
legacy VoiceBridge patří pod Cockpit; platební SMS pod Správu dokumentů; Guard
proti mazání pod Samantha Infrastructure. Samostatné tooly jsou Záloha a
obnova, Zmenšování obrázků, PictNew a TTS. Human–Adam si do pozdější runtime
migrace ponechává historické ID, typ a název jako kompatibilní aliasy.

Fáze nemění UI, API, profily, workspace ani soukromá vlákna. Současný runtime
zůstává navázaný jen na Human–Adam a Knihovnu. Cílená sada prošla 107 testy,
plná Cockpit Quality Gate prošla všemi syntaxemi a 922 testy za 248,040 sekundy
a živý Cockpit smoke test skončil 5/5. `git diff --check` je čistý.

Změněné nebo nové soubory fáze: `human_adam_workstream_catalog.py`,
`human_adam_workstream_coordinator.py`, `test_human_adam_workstream_catalog.py`,
`test_human_adam_profiles.py`, `cockpit_quality_gate.py`, `WORKSTREAMS.md`,
`MEMORY_INDEX.md`, tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`.

Další krok: po tematickém commitu, pushi a zelené vzdálené Quality Gate zahájit
fázi 4.2 – oddělení pracovního proudu od dvou pevných profilů a bezpečné lazy
založení či obnovení soukromého vlákna. Fáze 4.1 se nenasazuje a živé menu se v
ní nemění.

### 2026-07-20 20:08 CEST – Checkpoint fáze 4.2: lazy soukromá vlákna

Fáze 4.2 je implementačně hotová jako neveřejný backend bez nové API route a
bez změny UI. `WorkstreamThreadRegistry` přebírá všech 29 validovaných identit
z katalogu, ale samotné načtení nevytvoří soukromý adresář, app-server klienta
ani Codex vlákno. Teprve výslovně potvrzené otevření jednoho proudu vytvoří nebo
obnoví jeho vlastní persistentní session stav.

Všechny lazy proudy znovu používají jeden app-server runtime a jeden sdílený
čistý workspace; nevzniká sada profilů, procesů, worktree ani WIP větví. V jednu
chvíli může být připojený nejvýše jeden lazy proud. Přepnutí skončí fail-closed,
pokud běží aktivní tah, existuje nejisté doručení nebo workspace není čistý a
synchronní s `main`. Redigovaný stav nevystavuje ID vlákna ani private cestu.

Human–Adam a Knihovna jsou z lazy otevření záměrně rezervované, protože jejich
existující soukromá vlákna se musí zachovat až při migraci fáze 4.5. Fáze 4.2
nezakládá jejich duplicitní session a nemění současný profilový přepínač.

Nový testovací modul ověřuje inertní načtení katalogu, vytvoření jediného
vyžádaného vlákna, obnovení stejného uloženého vlákna po novém registru,
odpojení předchozího proudu, blokaci aktivního tahu a nejistého doručení,
workspace guard, explicitní potvrzení a rezervované či archivované proudy.
Cílená sada 86 testů prošla. Plná Cockpit Quality Gate prošla kontrolou diffu,
Python, JavaScript i shell syntaxí a 930 testy za 242,097 sekundy; celá brána
skončila `OK`.

Změněné aplikační soubory fáze jsou `human_adam_workstream_threads.py`,
`human_adam_service.py`, `human_adam_profiles.py`, odpovídající nový test a
manifest quality gate. Tento checkpoint neautorizuje nasazení ani restart.

Další krok: fáze 4.3 – odvodit pro každý katalogový proud jedinou git-safe
kanonickou vazbu na handoff a TVBCP, bezpečně založit chybějící kostry a napojit
je na checkpointový backend. UI, menu a migrace legacy vláken zůstávají mimo
rozsah až do fází 4.4 a 4.5.

### 2026-07-20 20:32 CEST – Checkpoint fáze 4.3: kanonický handoff a TVBCP

Fáze 4.3 je implementačně hotová jako neveřejný backend. Nový
`WorkstreamMemoryRegistry` odvozuje pro všech 29 validovaných proudů právě jednu
git-safe dvojici handoff + TVBCP a odmítá neznámé proudy, nebezpečné cesty i
sdílení stejného dokumentu dvěma proudy.

Human–Adam a Knihovna zachovávají svoje dnešní potvrzené dokumenty. Zbývající
proudy mají stabilní cesty pod `memory/handoffs/workstreams/` a
`memory/tvbcp/workstreams/`. Katalog ani start Cockpitu je nevytváří. První
skutečný potvrzený checkpoint po zelené bráně založí obě git-safe kostry,
přidá časovaný handoff/TVBCP záznam a zahrne vše do stejného direct-main
commitu.

Zápis je transakční: selhání brány nevytvoří žádný dokument; selhání commitu
odstraní obě právě založené kostry a zachová původní pracovní změny. Chybějící
dokument bez serverem dodané kanonické kostry je odmítnut. Lazy checkpoint bere
ID a cesty jen ze serverových registrů a vyžaduje připojené vlákno bez aktivního
tahu a bez nejistého doručení.

Stávající profilové checkpointy Human–Adam/Knihovna i automatické dokončení
zapisovacího tahu používají stejný kanonický registr. Developer instrukce
lazy vlákna dostává přesné git-safe cesty, ale přímou změnu dokumentů bez
Mílova pokynu zakazuje; běžnou aktualizaci provádí potvrzený checkpoint.

Při integraci byla opravena chyba fáze 4.2 v názvu čistého workspace vztahu:
produkční `HumanAdamWorkspaceManager` používá `aligned`, nikoli testovací
`same`. Bez opravy by první skutečné lazy otevření skončilo falešným blokem.

Finální Cockpit Quality Gate prošla kontrolou diffu, Python, JavaScript i shell
syntaxí a 943 testy za 261,953 sekundy; celá testovací část skončila `OK` za
264,7 sekundy. Checkpoint 4.2 `efe5184` mezitím prošel i vzdálenou GitHub Quality
Gate. Fáze 4.3 nepřidala API route, UI, menu, živé vlákno, nasazení ani restart
a nevytvořila žádný nový proudový dokument mimo dva zachované legacy páry.

Změněné aplikační soubory jsou `human_adam_workstream_memory.py`,
`human_adam_workstream_threads.py`, `human_adam_profiles.py`,
`simple_main_checkpoint.py`, tři odpovídající testovací moduly, nový test
registru a manifest quality gate.

Další krok: fáze 4.4 – napojit stávající výběr na skupiny `Projekty`, `Tooly`,
`Vrstvy` a `Ostatní` a při potvrzeném přepnutí bezpečně synchronizovat sdílený
workspace, připojit cílové lazy vlákno a zachovat legacy proudy do migrace 4.5.
Tento checkpoint neautorizuje nasazení ani restart.

### 2026-07-21 08:03 CEST – Checkpoint fáze 4.5e: jednotný backend proudů

Nazev: Univerzální pracovní proudy – fáze 4.5e
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Pevné rozlišení `legacy_profile` / lazy backend bylo nahrazeno jedním
kanonickým backendovým registrem. Human–Adam a Knihovna jsou v této mezifázi
kompatibilní adaptéry, které odkazují přímo na své dosavadní služby a private
stav. Zbývajících 27 proudů používá existující lazy private-thread backend.

Co je hotove:
- `WorkstreamBackendRegistry` je jediná autorita typu backendu a služby pro
  všech 29 kanonických ID.
- Human–Adam i Knihovna zachovaly původní session, context anchor, hub,
  workspace, handoff a TVBCP; nic se nekopírovalo ani znovu nezakládalo.
- Menu, výběrový model, aktivní služba a atomický router rozhodují přes jednotný
  registr; thread registry už typ backendu neurčuje duplicitně.
- Commit `6c1a2da` byl pushnutý na `main`. Vzdálená Cockpit Quality Gate i
  Pages deployment jsou zelené.
- Simple-main nasazení prošlo serverovou branou 971 testů, novým procesem a
  smoke testem `5/5`.
- Live roundtrip `MMTX -> Human–Adam -> Knihovna -> MMTX` prošel na nasazeném
  kódu. Hashové porovnání potvrdilo stejné identity všech tří vláken; zachovány
  zůstaly také počty zpráv 2 / 102 / 28.
- `main`, `origin/main`, sdílený Human–Adam workspace i Knihovna workspace jsou
  čisté a zarovnané na `6c1a2da`. Aktivní zůstalo připojené MMTX bez aktivního
  tahu nebo nejistého doručení.

Co neni hotove:
- Perzistentní aktivní identita je uvnitř manageru stále kompatibilně složená z
  původního aktivního profilu a případného aktivního lazy proudu.
- Kompatibilní profilové API, `work_profiles` fallback a starý private soubor
  aktivního profilu zatím zůstávají; jejich odstranění nebylo součástí 4.5e.

Dalsi krok:
Fáze 4.5f – nejdřív navrhnout a otestovat jednu perzistentní autoritu
`active_workstream_id` pro všechny proudy. Migrace musí odkazovat na existující
služby a session beze změny; adaptéry, private stav ani fallback zatím nemazat.

Navrhovane dalsi kroky:
- Po zelené implementaci 4.5f zopakovat roundtrip přes oba adaptéry a MMTX.
- Teprve poté samostatně odstranit veřejný profilový fallback a mrtvou
  dvouprofilovou konstrukci.

Zmenene nebo relevantni soubory:
- `human_adam_workstream_backends.py`
- `human_adam_profiles.py`
- `human_adam_workstream_selection.py`
- `human_adam_workstream_threads.py`
- `human_adam_ui.py`
- `cockpit_quality_gate.py`
- odpovídající regresní testy

Bezpecnost / neukladat:
- Neukládat private thread ID, obsah zpráv, kotvy, tokeny ani private cesty.
- Nemazat ani nepřesouvat původní session Human–Adam/Knihovna během další
  migrace.

### 2026-07-21 09:09 CEST – Checkpoint fáze 4.5f: perzistentní aktivní proud

Nazev: Univerzální pracovní proudy – fáze 4.5f
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Dosavadní složená autorita aktivního legacy profilu a případného lazy proudu
byla nahrazena jediným perzistentním `active_workstream_id`. Stejný kanonický
identifikátor nyní používají lazy backendy i dočasné kompatibilní adaptéry
Human–Adam a Knihovna.

Co je hotove:
- Private stav má schéma 2 a zapisuje jen kanonický `active_workstream_id`;
  staré `active_profile_id` se do nového schématu nepřenáší.
- Schéma 1 zůstává čitelné jako migrační vstup. Pouhé načtení je inertní a
  migrace nastane až při potvrzeném výběru proudu.
- Obnovení lazy proudu po startu pouze připojí existující private session k
  manageru v odpojeném stavu. Nevytvoří nové vlákno, zprávu ani spojení.
- Atomický router při chybě persistence obnoví původní backend, session i stav;
  stale profilové pole nemůže přebít kanonické ID schématu 2.
- Commit `ccba6fe` byl pushnutý na `main` a vzdálená Cockpit Quality Gate
  skončila `success` za 2 minuty 32 sekund.
- Řízené nasazení prošlo plnou serverovou branou 980 testů, novým procesem a
  kanonickým smoke testem `5/5`. První pokus bezpečně skončil bez restartu při
  přechodném selhání závěrečného refreshu `origin/main`; nový audit prokázal
  přesnou shodu a opakovaný úplný průchod uspěl.
- Potvrzený výběr MMTX provedl migraci na schéma 2. Samostatný restart změnil
  PID, zachoval aktivní `project-mmtx` a obnovil je správně jako odpojené.
  Explicitní `Připojit` navázalo stejnou session se stejným počtem dvou zpráv,
  bez nové zprávy, vlákna nebo aktivního tahu.
- Finální stav: MMTX je aktivní a připojené, workspace je čistý a zarovnaný,
  `main` se shoduje s `origin/main` a živý smoke test je `5/5`.

Co neni hotove:
- Po schématu 2 ještě nebyl zopakován celý tříproudový roundtrip přes oba
  kompatibilní adaptéry.
- Veřejný profilový fallback, `work_profiles` kompatibilita a původní
  dvouprofilová konstrukce zatím zůstávají.

Dalsi krok:
Provést read-only ohraničený live roundtrip
`MMTX -> Human–Adam -> Knihovna -> MMTX` přes schéma 2 a ověřit, že se zachovaly
identity, počty zpráv, čisté workspaces a finálně aktivní připojené MMTX.

Navrhovane dalsi kroky:
- Po zeleném tříproudovém roundtripu zahájit fázi 4.5g.
- Ve fázi 4.5g odstranit veřejný profilový fallback a mrtvou dvouprofilovou
  konstrukci samostatně, bez mazání private session nebo kompatibilních dat.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `human_adam_workstream_threads.py`
- `test_human_adam_profiles.py`
- `test_human_adam_workstream_threads.py`
- `human_adam_active_profile.json` – private stav, necommitovat

Bezpecnost / neukladat:
- Neukládat private thread ID, jeho hash, obsah zpráv, kotvy, tokeny ani private
  cesty.
- Nemazat ani nepřesouvat legacy private session během odstranění fallbacku.

#### 2026-07-21 09:53 CEST – Post-roundtrip dodatek k checkpointu 4.5f

Finální live roundtrip `MMTX -> Human–Adam -> Knihovna -> MMTX` přes schéma 2
prošel bez nové zprávy nebo vlákna. Kontrolní porovnání potvrdilo zachované
identity a stejné počty uložených zpráv `2 / 102 / 28`. Všechny tři workspaces
skončily čisté a zarovnané na `e92ba02`; Cockpit smoke prošel `5/5` a aktivní
zůstalo připojené MMTX bez aktivního tahu. Jeden požadavek s nekanonickým ID
Knihovny byl fail-closed odmítnut bez změny aktivního proudu; následný krok
použil katalogové `project-knowledge-library`.

Další krok: read-only audit fáze 4.5g. Zatím nic neodstraňovat a neměnit
adaptery, veřejné fallbacky ani private session.

### 2026-07-21 10:19 CEST – Checkpoint fáze 4.5g-a: bez veřejného profilového fallbacku

Nazev: Univerzální pracovní proudy – fáze 4.5g-a
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Veřejný kontrakt výběru už nemá paralelní profilovou cestu. Endpoint na
stávající URL přijímá výhradně kanonické `workstream_id`; přítomnost legacy
`profile_id` je fail-closed chyba i při současně poslaném kanonickém ID.

Co je hotove:
- UI vždy vykresluje seskupený katalog a odesílá pouze `workstream_id`.
- Status nevrací `work_profile` ani `work_profiles`; selection model neobsahuje
  veřejná `profile_id`.
- Negativní testy ověřují odmítnutí legacy payloadu bez změny aktivního proudu.
- Interní adaptéry, jejich původní služby, schéma 1 a private session zůstaly
  beze změny.
- Cílená sada 130 testů, širší sada 336 testů a plná Cockpit Quality Gate s
  980 testy za 229,462 sekundy prošly včetně Python, JavaScript a shell syntaxe.
- Živé MMTX zůstalo připojené se dvěma zprávami, bez aktivního tahu a s čistým
  zarovnaným workspace; private ani autosave soubory se nezměnily.

Co neni hotove:
- Změna zatím není nasazená ani živě ověřená proti novému veřejnému kontraktu.
- Interní `HumanAdamWorkstreamCoordinator`, staré wrappery a profilově
  pojmenovaná bezpečnostní metadata zůstávají pro samostatnou fázi 4.5g-b.

Dalsi krok:
Po commitu, pushi a zelené vzdálené CI bezpečně nasadit fázi 4.5g-a. Live proof
musí ověřit, že `profile_id` payload nic nepřepne, kanonické `workstream_id`
funguje a finálně zůstane aktivní připojené MMTX se zachovanou session.

Navrhovane dalsi kroky:
- Po live proofu zahájit read-only hranici 4.5g-b pro odstranění mrtvého
  koordinátoru a wrapperů.
- Nemigrovat vývojový semafor ani deployment-completion účtenky ve stejném
  kroku; to je samostatná bezpečnostní migrace.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `human_adam_ui.py`
- `human_adam_workstream_selection.py`
- odpovídající tři testovací moduly

Bezpecnost / neukladat:
- Nemazat ani nepřesouvat private session, kotvy, workspaces nebo schéma 1.
- Neukládat private thread ID, hash identity, obsah zpráv, tokeny ani private
  cesty.

#### 2026-07-21 11:06 CEST – Post-deployment dodatek k checkpointu 4.5g-a

Commit `427f0a6` prošel vzdálenou Cockpit Quality Gate za 2 minuty 43 sekund a
Pages workflow. Řízené nasazení zopakovalo plnou bránu s 980 testy za 276,5
sekundy, spustilo nový Cockpit proces s očekávaným code stampem a dokončovací
smoke prošel `5/5`.

Live kontraktní proof potvrdil, že payload s `profile_id` skončí fail-closed a
nezmění aktivní Human–Adam, jeho spojení, historii ani schéma 2. Následný
kanonický payload `workstream_id=project-mmtx` uspěl a obnovil stejnou MMTX
session. MMTX zachovalo 2 zprávy, Human–Adam 102, status nezveřejňuje profilová
pole a všechny tři workspaces jsou čisté a zarovnané na `427f0a6`. Finálně je
aktivní připojené MMTX bez aktivního tahu.

Další krok: read-only hranice fáze 4.5g-b pro mrtvý koordinátor a wrappery.
Nemigrovat ve stejném kroku vývojový semafor, deployment-completion účtenky,
schéma 1 ani private session.

### 2026-07-21 11:45 CEST – Checkpoint fáze 4.5g-b: mrtvý koordinátor a wrappery odstraněny

Nazev: Univerzální pracovní proudy – fáze 4.5g-b
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Read-only audit prokázal, že `HumanAdamWorkstreamCoordinator` a čtyři staré
profilové wrappery už nemají živé call-site. Ve stejném modulu však zůstával
živý `CanonicalWorkstreamBinding`, který chrání kompatibilní adaptéry,
checkpointy a deployment. Implementace proto nejdřív oddělila tento kontrakt
a teprve potom odstranila mrtvou konstrukci.

Co je hotove:
- `CanonicalWorkstreamBinding` a jeho fail-closed validátor jsou v samostatném
  modulu `human_adam_workstream_binding.py`.
- Validace dál kontroluje katalogové ID, povolený alias názvu a typu, kanonické
  handoff/TVBCP cesty, identitu služby a shodu profilového TVBCP.
- Mrtvý `HumanAdamWorkstreamCoordinator`, jeho instance a wrappery
  `service_for_profile`, `simple_checkpoint_context`, `workstream_status` a
  `select_workstream` byly odstraněny.
- Živý grouped router, `WorkstreamBackendRegistry`, interní `switch`,
  kompatibilní adaptéry Human–Adam/Knihovna, schéma 1 a private session zůstaly
  zachované.
- Statická kontrola nenachází žádný zbylý import ani call-site koordinátoru a
  wrapperů. Cílených 78 testů a plná Cockpit Quality Gate s 979 testy za
  224,084 sekundy prošly; nový binding test je zahrnutý v kanonické CI sadě.
- `git diff --check` je čistý. Live Cockpit nebyl restartován ani nasazen.

Co neni hotove:
- Checkpoint ještě není commitnutý ani pushnutý a vzdálená CI jej zatím
  neověřila.
- Změna není nasazená; live Cockpit stále běží na předchozí potvrzené verzi.
- Vývojový semafor, deployment-completion účtenky, migrační schéma 1 a private
  session nebyly migrovány ani odstraněny.

Dalsi krok:
Vytvořit jeden tematický commit fáze 4.5g-b, pushnout `main` a počkat na zelenou
vzdálenou Cockpit Quality Gate. Teprve potom samostatně rozhodnout o bezpečném
nasazení a live regresním proofu se zachovaným aktivním MMTX.

Navrhovane dalsi kroky:
- Po nasazení ověřit grouped menu, kanonické `workstream_id`, zachovanou MMTX
  session a čisté workspaces bez nové zprávy nebo vlákna.
- Profilově pojmenovaná bezpečnostní metadata auditovat až v samostatné další
  fázi; nespojovat je s odstraněním koordinátoru.

Zmenene nebo relevantni soubory:
- `human_adam_workstream_binding.py`
- `human_adam_workstream_coordinator.py` – odstraněn
- `human_adam_profiles.py`
- `cockpit_quality_gate.py`
- `test_human_adam_workstream_binding.py`
- `test_human_adam_profiles.py`

Bezpecnost / neukladat:
- Nemazat ani nepřesouvat private session, kotvy, workspaces, schéma 1,
  semaforové nebo deployment-completion účtenky.
- Neukládat private thread ID, hash identity, obsah zpráv, tokeny ani private
  cesty.

#### 2026-07-21 12:25 CEST – Post-deployment dodatek k checkpointu 4.5g-b

Commit `c1b30df` prošel vzdálenou Cockpit Quality Gate s 979 testy a Pages
workflow. Protože auditovaný commit obsahoval schválené odstranění koordinátoru,
automatický synchronizační guard nejdřív fail-closed zastavil profilový update.
Po Mílově přesném potvrzení globální brzdy byly oba čisté izolované workspaces
ověřeně fast-forwardovány z `427f0a6` na `c1b30df`, bez remote, WIP nebo private
cest.

Řízené nasazení zopakovalo plnou serverovou bránu s 979 testy za 259,1 sekundy,
změnilo Cockpit PID `67271 -> 89177`, potvrdilo code stamp
`03cab696207b0c3f` a serverový i nezávislý smoke test prošly `5/5`. Live proof
vrátil stejnou private MMTX session se stejnými 2 zprávami; Human–Adam zachoval
102 zpráv. Finálně je aktivní připojené `project-mmtx` bez aktivního tahu nebo
nejistého doručení a main, Human–Adam i Knihovna jsou čisté a zarovnané na
`c1b30df`.

Další krok: samostatný read-only audit zbývajících profilově pojmenovaných
bezpečnostních metadat. Zatím nemigrovat schéma 1, vývojový semafor,
deployment-completion účtenky ani private session.

### 2026-07-21 13:21 CEST – Checkpoint fáze 4.5g-c: audit profilově pojmenovaných bezpečnostních metadat

Nazev: Univerzální pracovní proudy – fáze 4.5g-c
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Striktní read-only audit zbývajících profilově pojmenovaných metadat po
odstranění veřejného profilového fallbacku a mrtvého koordinátoru. Cílem bylo
oddělit skutečně zavádějící veřejná pole od interních identit, které stále
chrání kompatibilní služby, workspaces, rollback nebo obnovu starého stavu.

Co je hotove:
- `development_status()` veřejně vrací `active_profile_id` a
  `active_profile_label`. Při aktivním MMTX obsahují `project-mmtx` a `MMTX`,
  takže kanonický pracovní proud nesprávně vydávají za profil.
- Cockpit UI ani jeho JavaScript tato dvě pole nečtou. Jejich odstranění má
  malý lokální rozsah v normální i chybové větvi status payloadu.
- Generický semaforový `owner_id` je živá fail-closed identita vlastníka a musí
  zůstat. Stejně tak interní `active_profile_id`, `adapter.profile_id`,
  `work_profile_id`, `switch` a workspace řádky stále obsluhují skutečné
  kompatibilní backendy Human–Adam/Knihovna, ownership a rollback.
- Private stav používá schéma 2 a zapisuje jen `active_workstream_id`. Čtení
  schématu 1 je neaktivní pro současný stav, ale zůstává záměrnou migrační a
  recovery kompatibilitou.
- Aktuální simple-main deployment persistuje kanonické `workstream_id`.
- Starý deployment-completion endpoint a UI karta jsou proti aktuálnímu
  simple-main deploymentu osiřelé: jejich producent je v neroutovaném starém
  deployment handleru a živý completion záznam neexistuje. Tento subsystém má
  větší zapisovací a Git rozsah a nesmí se odstraňovat v malém kroku 4.5g-c1.
- Audit nic nezapsal do aplikačního ani private stavu, nic nenasadil a
  nerestartoval. `main` byl čistý a synchronní s `origin/main` na `4566fd0`.

Co neni hotove:
- Veřejná `active_profile_id` a `active_profile_label` pole zatím nebyla
  odstraněna a kontraktní testy nebyly změněny.
- Interní profilové identity ani schéma 1 nebyly přejmenovány nebo migrovány.
- Osiřelý deployment-completion endpoint, UI karta a starý action surface
  nebyly odstraněny; vyžadují samostatnou hranici 4.5g-c2.
- Neběžel deployment, restart ani live zapisovací proof.

Dalsi krok:
Ve fázi 4.5g-c1 odstranit pouze veřejná pole `active_profile_id` a
`active_profile_label` z obou větví `development_status()` a doplnit negativní
kontraktní testy pro samostatný semaphore endpoint i semaphore vložený ve
statusu. Interní ownership, schema 1, adaptéry a private data ponechat beze
změny; implementaci zatím nenasazovat.

Navrhovane dalsi kroky:
- Po samostatném ověření a nasazení 4.5g-c1 otevřít 4.5g-c2 jako read-only audit
  bezpečného odstranění osiřelého deployment-completion endpointu, UI karty a
  neroutovaného starého producenta.
- Případné přejmenování interního `work_profile_id` řešit až jako samostatnou
  migraci servisního ownership kontraktu, nikoli jako kosmetický cleanup.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `human_adam_workstream_backends.py`
- `development_semaphore.py`
- `human_adam_deploy.py`
- `simple_main_deploy.py`
- `human_adam_ui.py`
- `cockpit.py`
- `test_human_adam_profiles.py`
- `test_cockpit.py`
- `test_human_adam_ui.py`

Bezpecnost / neukladat:
- Nemigrovat ani nemazat schéma 1, private session, kotvy, workspaces,
  semaphore nebo deployment-completion stav bez samostatného auditu a výslovné
  dohody.
- Neukládat private thread ID, identity hash, obsah zpráv, tokeny ani private
  cesty.

### 2026-07-21 22:37 CEST – Dokumentační uzavření fází 4.5g-c1 až c2f1

Nazev: Univerzální pracovní proudy – uzavření legacy deployment subsystému
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-21

Co se resilo:
Po odstranění zavádějících veřejných profilových metadat byl po malých
auditovaných krocích odpojen a odstraněn osiřelý deployment-completion
subsystém. Závěrečný read-only audit a Mílův ruční test nyní dovolují
srovnat kanonickou projektovou paměť se skutečným stavem.

Co je hotove:
- Veřejný semaphore status už nevrací `active_profile_id` ani
  `active_profile_label`; interní ownership kontrakty zůstaly zachované.
- Starý deployment-completion endpoint, UI karta, action surface a legacy
  readery byly odstraněny. Deployment evidence patří pouze simple-main
  receiptu.
- Sdílená checkpoint quality gate a bezpečná read-only šablona TVBCP pro
  dosud neinicializovaný lazy proud zůstávají živé a samostatné.
- Servisní vazby starého deploymentu byly odpojeny bez zásahu do kompatibilních
  adaptérů, workspace ownership, rollbacku, schématu 1 nebo private session.
- `human_adam_deploy.py` a `test_human_adam_deploy.py` byly odstraněny.
- Checkpoint `23a219e` prošel vzdálenou Cockpit Quality Gate a řízené nasazení
  zopakovalo plnou bránu s 969 testy; nový proces a smoke `5/5` byly potvrzeny.
- Závěrečný audit nenašel žádný živý import, route, registraci ani reader
  starého subsystému. HTTP stránka i negativní kontrakty prošly a Míla
  potvrdil funkční panel `Práce`.
- Main, Human–Adam a Knihovna jsou čisté a zarovnané na `23a219e`.

Co neni hotove:
- Tento dokumentační checkpoint zatím není commitnutý ani pushnutý.
- Ignorované `.pyc` cache odstraněného modulu, šest osiřelých private JSON
  sad s locky a historicky pojmenovaný aktivní gate log nebyly smazány ani
  přejmenovány.
- Interní kompatibilní profilové identity a čtení migračního schématu 1
  nebyly měněny.

Dalsi krok:
Po samostatném commitu a pushi tohoto čtyřsouborového dokumentačního
checkpointu otevřít novou read-only hranici pro případnou další migraci.
Nespojovat ji s mazáním private artefaktů ani s přejmenováním gate logu.

Navrhovane dalsi kroky:
- Jako samostatnou fázi lze auditovat, zda je ještě potřebné čtení schématu 1
  a interní profilově pojmenované kompatibilní identity.
- Fyzický cleanup ignorovaných cache nebo private historických dat provést
  pouze po novém read-only auditu a Mílově výslovném souhlasu s mazáním.

Zmenene nebo relevantni soubory:
- `ACTIVE_PROJECTS.md`
- `MEMORY_INDEX.md`
- `human_adam_layer_workstream_start_2026_07_20.md`
- `architektura_komunikace_samantha.txt`

Bezpecnost / neukladat:
- Nemazat ani nemigrovat private data, session, workspaces nebo cache v tomto
  dokumentačním kroku.
- Neukládat private thread ID, identity hash, obsah zpráv, tokeny ani private
  cesty.

### 2026-07-24 09:37 CEST – Automatický sync čistého workspace při odeslání

Nazev: Human–Adam – odstranění zbytečného ručního připojení po čistém pushi
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Human–Adam po terminálovém commitu a pushi někdy odmítl další pokyn jen proto,
že jeho čistý izolovaný workspace zůstal za zdrojovým `main`. Ruční
`Připojit` stav dorovnalo, ale přidávalo zbytečný mezikrok.

Co je hotove:
- Odeslání nyní před samotným tahem kontroluje aktivní workspace.
- Čistý, nečinný a důvěryhodný workspace, který je pouze za zdrojovým `main`,
  se bezpečně fast-forwarduje stejnou cestou jako ruční připojení.
- Po synchronizaci se znovu ověří zarovnání a teprve potom se odešle původní
  pokyn.
- Špinavý workspace, aktivní tah, nejisté doručení, špinavý zdrojový `main`,
  divergence nebo nejednoznačný stav zůstávají fail-closed.
- Odpověď výslovně uvádí, zda synchronizace proběhla.
- Cílených 187 testů prošlo a celá Cockpit Quality Gate skončila 1189 testy
  bez chyby. `git diff --check` je čistý.

Co neni hotove:
- Implementace v okamžiku checkpointu ještě není commitnutá, pushnutá ani
  nasazená do běžícího Cockpitu.
- Oprava neumožňuje dva současné zapisující vývoje. Pokud je zdrojový `main`
  rozpracovaný, zapisovací pokyn Human–Adam je stále záměrně blokovaný.

Dalsi krok:
Dokončit přesný commit, push a potvrzované nasazení tohoto checkpointu.

Navrhovane dalsi kroky:
- Přednostně navrhnout a po malém auditu implementovat izolovanou souběžnou
  práci Human–Adam při terminálovém WIP.
- V takovém režimu povolit editaci a testy jen uvnitř vlastního izolovaného
  workspace; checkpoint, push a začlenění blokovat, dokud není zdrojový `main`
  čistý a neproběhne audit konfliktů.
- Nepřidávat automatický rebase, reset, merge, mazání ani skryté přepisování
  uživatelského WIP.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `test_human_adam_profiles.py`
- `ACTIVE_PROJECTS.md`
- `MEMORY_INDEX.md`
- `human_adam_layer_workstream_start_2026_07_20.md`
- `architektura_komunikace_samantha.txt`

Bezpecnost / neukladat:
- Do Git paměti nepatří obsah zpráv, private identity, session, cesty ani
  tajemství.
- Synchronizace nesmí obejít nečistý stav, nejisté doručení, aktivní tah nebo
  konflikt historie.

### 2026-07-24 10:09 CEST – Izolovaný vývoj při terminálovém WIP

Nazev: Human–Adam – souběžná izolovaná editace bez automatické integrace
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Běžící Human–Adam odmítal každý zapisovací pokyn, jakmile zdrojový `main`
obsahoval terminálové pracovní změny. Read-only pokyny přitom fungovaly.
Cílem bylo povolit užitečnou izolovanou editaci a testy, nikoli dva souběžné
zápisy do stejného `main`.

Co je hotove:
- Human–Adam může při terminálovém WIP zahájit zapisovací tah jen tehdy, když
  jeho workspace i všechny kompatibilní peery zůstávají čisté, bezpečné a
  zarovnané s posledním commitem.
- Tah je označen jako izolovaný s odloženou integrací a model dostane výslovný
  zákaz `git add`, commitu, checkpointu, push, merge, rebase, resetu a
  nasazení.
- Automatická dokončovací účtenka se modelu neposílá. I kdyby se v odpovědi
  objevila, checkpoint se nespustí a značka se nezobrazí uživateli.
- Úspěšné změny zůstanou viditelné a necommitnuté pro pozdější audit
  konfliktů.
- Výjimka platí pouze pro kanonický Human–Adam. Knihovna, dirty workspace,
  aktivní nebo nejistý tah a nezarovnaný peer zůstávají fail-closed.
- Cílená sada prošla 190 testy a celá Cockpit Quality Gate 1192 testy.
  `git diff --check` je čistý.

Co neni hotove:
- Checkpoint ještě není commitnutý, pushnutý ani nasazený.
- Neběžel živý test proti skutečnému Human–Adam workspace. Ten je smysluplný
  až po nasazení nové backendové logiky.
- Pozdější převzetí izolovaného WIP do `main` zatím záměrně není
  automatizované; vyžaduje čistý `main` a samostatný audit konfliktů.

Dalsi krok:
Commitnout, pushnout a potvrzovaně nasadit tento checkpoint. Potom připojit
Human–Adam a provést jeden malý živý zapisovací test při kontrolovaném
terminálovém WIP, bez checkpointu.

Navrhovane dalsi kroky:
- Po živém důkazu navrhnout read-only audit bezpečného převzetí izolovaného
  WIP po vyčištění `main`.
- Automatický merge, rebase, reset, mazání nebo přepis existující práce
  nepřidávat.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `test_human_adam_profiles.py`
- `ACTIVE_PROJECTS.md`
- `MEMORY_INDEX.md`
- `human_adam_layer_workstream_start_2026_07_20.md`
- `architektura_komunikace_samantha.txt`

Bezpecnost / neukladat:
- Neukládat obsah soukromých zpráv, private identity, session, cesty ani
  tajemství.
- Izolovaný režim nesmí sám vytvářet Git historii nebo měnit zdrojový `main`.

### Automatický checkpoint 2026-07-24 10:45 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Odstraněna skrytá zastaralá nápověda Human–Adam
- Ověření: plná Cockpit brána: 1192 testů, 220.5 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Remove obsolete Human-Adam work help`
- Další krok: Provést read-only audit skrytého UI auditu WIP větví

### 2026-07-24 10:57 CEST – Lepší TVBCP, fáze 1

Nazev: Nové TVBCP záznamy zaměřené na výsledek a další plán
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
TVBCP sice průběžně vznikal, ale automatické záznamy zvýrazňovaly hlavně
technický checkpoint, commit a push. Míla potřebuje rychle vidět, co je hotové,
co bylo rozhodnuto a kam může projekt dál pokračovat.

Co je hotove:
- Pravidla i checkpointový generátor používají pro nové záznamy pořadí
  `Hotovo`, `Rozhodnutí`, `Další krok`, `Navrhované další kroky` a nakonec
  stručný `Technický důkaz`.
- Neveřejná dokončovací účtenka zachová skutečné rozhodnutí a nejvýše čtyři
  budoucí plány z rozhovoru.
- Pokud rozhodnutí nebo další návrhy nevznikly, systém je nevymýšlí.
- Citlivé hodnoty jsou odmítnuty a staré třípolové účtenky zůstávají
  kompatibilní.
- Budoucí TVBCP šablony obsahují nový kontrakt od prvního checkpointu.
- Žádný dřívější TVBCP blok nebyl přepsán ani zpětně přeformátován.
- Cílených 108, širších 227 a úplných 1194 testů prošlo.

Co neni hotove:
- Změna ještě není commitnutá, pushnutá ani nasazená.
- Neběžel živý automatický checkpoint s novou pětipolovou účtenkou.
- Fáze 2 nebyla zahájena.

Dalsi krok:
Commitnout, pushnout a potvrzovaně nasadit fázi 1. Potom vytvořit jediný malý
živý checkpoint a zkontrolovat pouze jeho nový appendovaný TVBCP blok.

Navrhovane dalsi kroky:
- Po živém testu vyhodnotit, zda nový chronologický formát stačí pro rychlou
  orientaci Míly.
- Jen pokud nebude stačit, otevřít read-only návrh kompaktního aktuálního
  souhrnu bez přepisování historických záznamů.

Zmenene nebo relevantni soubory:
- `AGENTS.md`
- `human_adam_profiles.py`
- `human_adam_turn_completion.py`
- `human_adam_workstream_memory.py`
- `simple_main_checkpoint.py`
- `project_tvbcp_rules.md`
- příslušné cílené testy

Bezpecnost / neukladat:
- Nepřepisovat ani hromadně nepřeformátovávat starší TVBCP záznamy.
- Neukládat do rozhodnutí, plánů ani technických důkazů citlivý nebo private
  obsah.

### Automatický checkpoint 2026-07-24 11:26 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Odstraněn skrytý UI audit WIP větví při zachování terminálového auditu
- Ověření: plná Cockpit brána: 1194 testů, 207.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Remove hidden WIP branch audit UI`
- Další krok: Vytvořit potvrzený checkpoint a ověřit Human–Adam rozhraní po nasazení

### Automatický checkpoint 2026-07-24 11:37 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Rotace profilového vlákna již nevyžaduje připnutou kontextovou kotvu
- Ověření: plná Cockpit brána: 1194 testů, 210.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_service.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Make context anchor optional for thread rotation`
- Další krok: Po nasazení ručně ověřit rotaci bez kotvy a kontinuitu přes pracovní proud, handoff a TVBCP

### Automatický checkpoint 2026-07-24 12:16 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Kontrola rotace už nepředstírá, že připnutá kotva je povinná
- Ověření: plná Cockpit brána: 1194 testů, 213.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Upresnit stav rotace bez kotvy`
- Další krok: Po nasazení ručně ověřit text kontroly rotace bez kotvy

### 2026-07-24 13:56 CEST – Bezpečný návrat Human–Adam po nasazení

Nazev: Human–Adam – obnovení stránky a spojení po samoobslužném nasazení
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Po úspěšném nasazení se backend správně restartoval, ale stránka mohla zůstat
ve starém zakázaném stavu. Při selhání úložiště prohlížeče se vůbec neobnovila
a po běžném restartu nebylo spojení automaticky navázáno.

Co je hotove:
- Po serverově ověřeném nasazení se stránka obnoví bez ohledu na výsledek zápisu
  do `sessionStorage`.
- Obnovená stránka znovu připojí Human–Adam pouze po dohledání čerstvého
  ověřeného nasazení.
- Připojení zůstává fail-closed při aktivním tahu, vytížení, nejistém doručení
  nebo nedostupném runtime.
- Běžné otevření Human–Adam bez ověřeného nasazení se automaticky nepřipojuje.
- Cílená sada prošla 191 testy, JavaScript syntaktickou kontrolou a úplná
  Cockpit Quality Gate prošla 1195 testy.

Co neni hotove:
- Změna ještě není commitnutá, pushnutá ani nasazená.
- Neběžel živý test návratu stránky a dalšího pokynu po skutečném nasazení.

Dalsi krok:
Commitnout, pushnout a potvrzovaně nasadit tento checkpoint. Potom provést jeden
malý živý vývoj, nasazení z panelu `Práce` a ověřit, že Human–Adam přijme další
pokyn bez ručního obnovování nebo připojování.

Navrhovane dalsi kroky:
- Pokud živý test projde, uzavřít incident jako vyřešený.
- Pokud neprojde, zachytit pouze bezpečný stav UI a serveru bez obsahu zpráv.

Zmenene nebo relevantni soubory:
- `human_adam_ui.py`
- `test_human_adam_ui.py`
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat obsah soukromých zpráv, identity relace ani private stav.
- Automatické připojení nikdy nespouštět při aktivní nebo nejisté práci.

### 2026-07-24 18:01 CEST – Read-only audit čekající integrace

Nazev: Human–Adam – diagnostika odloženého WIP bez integračních zápisů
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Odložený izolovaný vývoj při terminálovém WIP bezpečně zachoval změny, ale po
vyčištění nebo posunu zdrojového `main` chyběla přesná samoobslužná diagnostika
dalšího kroku.

Co je hotove:
- Panel `Práce` obsahuje samostatný read-only audit čekající integrace.
- Audit rozliší čekání na čistý `main`, společný čistý základ, posunutý `main`
  a neověřenou nebo rozvětvenou historii.
- Při posunu `main` ukáže pouze počet a bezpečné názvy překrývajících se cest.
- Cizí WIP v jiném profilovém workspace přepne výsledek do fail-closed blokace.
- Audit ani UI nemají zapisovací akci a nespouštějí commit, push, merge, rebase,
  reset nebo nasazení.
- Cílených 168, širších 457 a úplných 1201 testů prošlo.

Co neni hotove:
- Neexistuje integrační brána ani samoobslužné začlenění změn do `main`.
- Neexistuje trvalý ownership marker, proto audit potvrzuje strukturální stav,
  nikoli původ nebo vlastnictví změn.
- Cestový překryv neověřuje sémantickou kompatibilitu obsahu.
- Změna ještě není commitnutá, pushnutá ani nasazená.

Dalsi krok:
Commitnout, pushnout a potvrzovaně nasadit read-only audit. Potom v panelu
`Práce` ověřit čistý stav bez čekající integrace.

Navrhovane dalsi kroky:
- Samostatně navrhnout potvrzovanou integrační bránu pouze pro ověřený společný
  základ.
- Pro posunutý `main` zachovat servisní rozhodnutí i při nulovém překryvu cest.
- Ownership marker případně řešit jako zvláštní předpoklad před automatizací.

Zmenene nebo relevantni soubory:
- `human_adam_workspace.py`
- `human_adam_profiles.py`
- `human_adam_ui.py`
- příslušné cílené testy
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat obsah změněných souborů ani soukromých zpráv.
- Nespouštět automatický merge, rebase, commit, push nebo přepis WIP.

### 2026-07-24 18:38 CEST – Recovery hranice automatického připojení

Nazev: Human–Adam – stará nejistota už neblokuje návrat po nasazení
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Živé ověření po nasazení ukázalo, že UI guard blokoval automatické připojení
kvůli každému historickému `delivery_unknown`, i když pozdější potvrzená
odpověď už tuto nejistotu podle backendového pravidla uzavřela.

Co je hotove:
- UI prochází technickou historii doručení odzadu stejně jako backend.
- Poslední `completed` uzavírá starší `pending`, `delivery_unknown` i recovery
  požadavky.
- Novější `pending`, `delivery_unknown` nebo `recovery_required=true` připojení
  nadále bezpečně blokují.
- Původní globální `messages.some(...)` kontrola byla odstraněna.
- UI testy prošly 62 testy, pět přímých JavaScriptových scénářů prošlo, širší
  sada prošla 457 testy a úplná Cockpit Quality Gate prošla 1201 testy.

Co neni hotove:
- Změna ještě není commitnutá, pushnutá ani nasazená.
- Neběžel živý restart s automatickým připojením nad existující historií.

Dalsi krok:
Commitnout, pushnout a potvrzovaně nasadit opravu. Po restartu ověřit, že
Human–Adam se automaticky připojí bez ručního zásahu.

Navrhovane dalsi kroky:
- Při zeleném živém testu uzavřít incident návratu po nasazení.
- Při selhání zachytit pouze technické stavy doručení bez textů zpráv.

Zmenene nebo relevantni soubory:
- `human_adam_ui.py`
- `test_human_adam_ui.py`
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat texty zpráv ani identity relace.
- Skutečně aktuální nejistotu vždy ponechat fail-closed.

### 2026-07-24 22:49 CEST – Ručně ověřená rotace bez kotvy a hranice handoffu

Nazev: Human–Adam – dokončení provozního testu rotace a zpřesnění aktuálního stavu
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Míla dokončil dříve otevřený ruční test rotace profilového vlákna bez připnuté
kontextové kotvy. Současně se ukázalo, že starší append-only záznamy mohou pro
rychlou orientaci působit jako aktuální stav, přestože je pozdější nasazení nebo
ruční důkaz již uzavřely.

Co je hotove:
- Kotva byla pozastavena a rotace bez připnuté kotvy proběhla.
- Míla ověřil zachování starého vlákna.
- Kontinuita nového vlákna z kanonického handoffu a TVBCP byla ověřena.
- Funkce je implementovaná, nasazená a provozně potvrzená.
- Automatický checkpoint Human–Adam zapisuje do handoffu bezpečný technický
  snapshot dokončeného vývojového kroku: souhrn, testovací důkaz, změněné cesty,
  commitovou zprávu a bezprostřední další krok.

Co neni hotove:
- Handoff nemá automatickou lifecycle finalizaci po pozdějším terminalovém
  pushi, nasazení nebo ručním retestu. Starší `čeká na nasazení` proto zůstává
  historicky pravdivým snapshotem, ale nesmí být čten jako dnešní stav.
- Potvrzovaná integrační brána odloženého Human–Adam WIP zatím neexistuje.
- Skutečný živý test izolovaného vývoje při současném terminálovém WIP ještě
  neproběhl.

Dalsi krok:
Po návratu od Rodinného kalendáře navrhnout úzkou potvrzovanou integrační bránu
pro odložený WIP na ověřeném společném základu.

Navrhovane dalsi kroky:
- Potom provést jeden úplný živý test: terminálový WIP, izolovaný vývoj
  Human–Adam, vyčištění `main`, audit a potvrzené začlenění.
- Zvážit kompaktní aktuální souhrn handoffu/TVBCP, který nebude přepisovat
  chronologickou historii.
- Lifecycle uzavření po nasazení řešit odděleně od správného append-only
  checkpointu; staré bloky hromadně nepřepisovat.

Zmenene nebo relevantni soubory:
- `human_adam_layer_workstream_start_2026_07_20.md`
- `architektura_komunikace_samantha.txt`
- `ACTIVE_PROJECTS.md`
- `MEMORY_INDEX.md`
- `simple_main_checkpoint.py`
- `human_adam_turn_completion.py`

Bezpecnost / neukladat:
- Neukládat ID vláken, texty soukromých zpráv, identity relace ani private stav.
- Historické bloky zachovat; aktuální stav zpřesňovat novým časovaným záznamem.

### 2026-07-24 23:23 CEST – Fáze 2 handoffu a potvrzovaná integrace

Nazev: Human–Adam – aktuální souhrn a bezpečné převzetí odloženého WIP
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-24

Co se resilo:
Navázala druhá fáze životního cyklu handoffu/TVBCP a úzká samoobslužná cesta
odloženého Human–Adam WIP zpět do `main`.

Co je hotove:
- Generátor checkpointu umí v handoffu i TVBCP vložit nebo nahradit právě jeden
  markerově ohraničený blok `Aktuální stav`; zbytek dokumentu zachová beze změny.
- Aktuální souhrn vzniká před jediným commitem z ověřeného
  `main == origin/main`, výsledku checkpointu a poslední bezpečné deployment
  účtenky. Nevytváří následný opravný commit po pushi.
- Nový chronologický blok výslovně říká, že popisuje stav při checkpointu a
  sám nepotvrzuje pozdější push ani nasazení.
- Chybějící, zdvojené nebo poškozené markery selžou uzavřeně.
- Odložený tah vytváří soukromý ownership marker mimo Git. Obsahuje jen ID
  pracovního proudu, base commit, počet a kryptografický otisk path-level změn
  a redigovanou dokončovací účtenku.
- Panel `Práce` nabídne integrační tlačítko jen při přesné shodě markeru,
  společného základu a aktuálního WIP. Akce vyžaduje přesnou samostatnou
  potvrzovací větu a používá existující kanonický jednoccommitový checkpoint a
  push backend.
- Při posunu `main`, cizím WIP, divergenci, chybějícím markeru nebo neshodě
  změn je brána fail-closed.

Co neni hotove:
- Změny nejsou commitnuté, pushnuté ani nasazené.
- Nový blok `Aktuální stav` se má poprvé vytvořit až uvnitř následujícího
  potvrzeného checkpointu.
- Neběžel úplný živý test: současný terminálový WIP, izolovaný Human–Adam tah,
  vyčištění `main`, audit markeru a potvrzené převzetí.

Dalsi krok:
Provést samostatný checkpoint a push; nasazení zůstává další samostatně
potvrzený krok.

Navrhovane dalsi kroky:
- Po nasazení provést úplný živý souběžný test na malém bezpečném vývoji.
- Teprve podle živého důkazu rozhodnout, zda rozšiřovat automatizaci; trvalý
  ownership marker zůstává předpokladem.
- Případ posunutého `main` neautomatizovat. Má zůstat servisním rozhodnutím i
  při nulovém překryvu cest.

Zmenene nebo relevantni soubory:
- `simple_main_checkpoint.py`
- `deferred_integration.py`
- `human_adam_turn_completion.py`
- `human_adam_profiles.py`
- `human_adam_ui.py`
- `cockpit.py`
- příslušné regresní testy
- tento handoff, kanonický TVBCP, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Ownership marker neukládá obsah souborů, chat, identity, hesla ani tajemství.
- Marker patří do private úložiště mimo Git a má práva pouze pro vlastníka.
- Automatický merge, rebase, reset ani řešení posunutého `main` nejsou součástí
  této brány.

Technicky dukaz:
- Cílených 446 testů prošlo.
- Úplná Cockpit Quality Gate, rozšířená výslovně o nový markerový modul a jeho
  testy, prošla 1216 testy.
- Python i JavaScript syntaxe a `git diff --check` jsou v pořádku.

### 2026-07-25 10:32 CEST – Obecné ruční dorovnání main s GitHubem

Nazev: Human–Adam – samoobslužný čistý fast-forward
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-25

Co se resilo:
Po automatickém vzdáleném commitu zůstal čistý lokální `main` o jeden commit za
`origin/main`. Audit nasazení rozdíl správně zablokoval, ale panel nenabídl
bezpečnou samoobslužnou cestu k nápravě.

Co je hotove:
- Vznikl obecný read-only audit lokálního `main` proti čerstvému
  `origin/main`; nejde o výjimku pro konkrétní automatizaci.
- Audit rozlišuje zarovnaný stav, lokální náskok, divergenci a jednoznačný
  fast-forward a při dostupném dorovnání ukáže cílový commit, počet commitů a
  změněné cesty.
- Potvrzená brána znovu načte GitHub a vyžaduje přesnou shodu lokálního i
  vzdáleného commitu s předchozím auditem.
- Po čistém `git merge --ff-only` synchronizuje oba ověřené profilové
  workspaces z lokálního `main`.
- Aktivní nebo nejistý tah, dirty stav, profilový WIP, lokální náskok,
  divergence nebo změna GitHubu zůstávají fail-closed.

Co neni hotove:
- Checkpoint ještě není commitnutý, pushnutý ani nasazený.
- Tlačítko zatím nebylo živě použito na přirozeném novém vzdáleném commitu.

Dalsi krok:
Commitnout a pushnout jeden tematický checkpoint a potom samostatně potvrzeně
nasadit čistý `main`.

Navrhovane dalsi kroky:
- Při příštím přirozeném bezpečném posunu `origin/main` projít audit, náhled,
  potvrzení a závěrečný zelený audit nasazení.
- Nevytvářet umělý vzdálený commit jen kvůli živému testu.

Zmenene nebo relevantni soubory:
- `main_remote_sync.py`
- `human_adam_profiles.py`
- `human_adam_ui.py`
- `cockpit.py`
- `cockpit_quality_gate.py`
- příslušné regresní testy
- tento handoff, kanonický TVBCP, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Audit ani účtenka nesmí ukládat obsah souborů, chat, tajemství nebo private
  runtime data.
- Brána nepoužívá pull, automatický merge, rebase, reset ani přepis historie.
- Pokud se stav od auditu změní, nic se nedorovná a je nutná nová kontrola.

Technicky dukaz:
- Cílená integrační sada prošla 426 testy.
- Úplná Cockpit Quality Gate prošla 1227 testy za 221,9 sekundy.
- Python, JavaScript a shell syntaxe i `git diff --check` jsou v pořádku.

### 2026-07-25 00:14 CEST – Servisní integrace rotace bez kotvy

Nazev: Human–Adam – převzetí zachovaného WIP po posunu main
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-25

Co se resilo:
Přednasazovací audit správně zablokoval nasazení, protože Human–Adam workspace
obsahoval čtyřsouborový WIP na starším základu, `main` mezitím postoupil a
ownership marker ještě neexistoval. Míla následně výslovně potvrdil servisní
začlenění tohoto přesného WIP.

Co je hotove:
- Plus/minus řádky ručně přenesené přes `apply_patch` přesně odpovídají
  zachovanému WIP; automatický merge ani rebase nebyl použit.
- Kontrola připravenosti rotace a výsledek rotace už nečtou ani nevracejí
  revizi kontextové kotvy.
- UI nezahazuje platný audit rotace jen kvůli změně, pozastavení nebo uložení
  volitelné kotvy.
- Změna auditovaného vlákna nadále audit správně zneplatní.
- Cílených 92 a úplných 1216 testů prošlo.

Co neni hotove:
- Servisní checkpoint ještě není commitnutý ani pushnutý.
- Starý Human–Adam workspace je stále bezpečně zachovaný a bude zarovnán až po
  důkazu, že commit na `main` obsahuje přesný WIP.
- Nasazení, restart, smoke test a ruční retest rotace ještě neproběhly.

Dalsi krok:
Commitnout a pushnout servisní checkpoint, ověřit jeho shodu, bezpečně zarovnat
profilové workspaces a spustit již potvrzené nasazení.

Navrhovane dalsi kroky:
- Po nasazení změnit nebo pozastavit kotvu a ověřit, že dříve provedený audit
  stejného vlákna zůstane použitelný.
- Potom provést celý živý scénář nové potvrzované integrace s ownership markerem.

Zmenene nebo relevantni soubory:
- `human_adam_service.py`
- `human_adam_ui.py`
- `test_human_adam_service.py`
- `test_human_adam_ui.py`
- tento handoff, kanonický TVBCP, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Neukládat identity vláken, texty zpráv ani private obsah kotvy.
- Starý WIP neuvolnit, dokud není prokazatelně obsažen v pushnutém `main`.

### Automatický checkpoint 2026-07-25 13:33 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Read-only stavy synchronizace main mají jednotný příznak úplnosti změn
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1227 testů, 224.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/main_remote_sync.py`, `Samantha_Agent/tests/test_main_remote_sync.py`
- Commit: `Unify main remote sync audit schema`
- Další krok: Po vyčištění zdrojového main provést audit konfliktů a potvrzené začlenění

### 2026-07-25 13:50 CEST – Aktuální nápověda odložené integrace a sovího dorovnání

Nazev: Human–Adam – aktualizace nápovědy Práce
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-25

Co se resilo:
Živý souběžný test odložené integrace byl úspěšně dokončen od terminálového WIP
přes ověřený private marker až po commit, push a nasazení. Nápověda pod
`Práce -> ?` ještě tento nový provozní postup nepopisovala přesně.

Co je hotove:
- Běžný automatický checkpoint je výslovně omezen na čistý zarovnaný `main`.
- Odložený tah bez commitu a pushnutí má popsaný read-only audit a samostatně
  potvrzované převzetí přesného WIP.
- Denní soví commit je uveden jako příklad bezpečného ručního fast-forwardu;
  dorovnání se nespouští automaticky.
- Posun `main`, cizí WIP, divergence a neshoda markeru nadále vyžadují servisní
  rozhodnutí.
- Cílených 64 UI testů prošlo a `git diff --check` je čistý.

Co neni hotove:
- Tento checkpoint ještě není commitnutý ani pushnutý.
- Aktualizovaná nápověda ještě není nasazená ani ručně vizuálně ověřená.

Dalsi krok:
Commitnout a pushnout tematický checkpoint a potom samostatně potvrzeně nasadit
čistý `main`.

Navrhovane dalsi kroky:
- Po nasazení jednou otevřít `Práce -> ?` a ověřit čitelnost nových bodů.
- Potom lze pokračovat projektem Rodinný kalendář.

Zmenene nebo relevantni soubory:
- `human_adam_ui.py`
- `test_human_adam_ui.py`
- tento handoff, kanonický TVBCP, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Nápověda ani checkpoint neobsahují chat, tajemství, private obsah nebo
  identifikátory vláken.
- Automatický merge, rebase, reset ani dorovnání při WIP se nepřidává.

### 2026-07-25 14:43 CEST – Kontextová capability nápověda soukromého archivu

Nazev: Human–Adam – obecná nápověda pracovních proudů
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-25

Co se resilo:
Obecná nápověda jmenovala Knihovnu jako zvláštní proud, přestože organizačně
patří mezi běžné kanonické pracovní proudy typu Project.

Co je hotove:
- Pevně pojmenovaný bod Knihovna byl z obecné nápovědy odstraněn.
- Obecné pravidlo soukromého archivu je ve výchozím stavu skryté.
- UI jej zobrazí pouze tehdy, když aktivní proud hlásí capability
  `private_archive_direct`.
- Backendová oprávnění, potvrzovací kategorie a private data se nezměnily.
- Cílených 66 UI a capability testů prošlo; `git diff --check` je čistý.

Co neni hotove:
- Checkpoint ještě není commitnutý, pushnutý ani nasazený.
- Hardcoded přiřazení knihovní capability v backendu zůstává případným
  samostatným budoucím refaktorem.

Dalsi krok:
Commitnout a pushnout checkpoint a samostatně potvrzeně nasadit čistý `main`.

Navrhovane dalsi kroky:
- Backendový capability refaktor neprovádět v tomto malém UI kroku.

Zmenene nebo relevantni soubory:
- `human_adam_ui.py`
- `test_human_adam_ui.py`
- tento handoff, kanonický TVBCP, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do nápovědy ani testů nepřidávat obsah soukromého archivu.
- Capability pouze řídí zobrazení existujícího pravidla; nerozšiřuje oprávnění.

### Automatický checkpoint 2026-07-25 15:07 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Schopnosti soukromého archivu se nyní načítají z deklarace kanonického pracovního proudu a výsledné chování zůstává stejné
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1229 testů, 222.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/app/communication/human_adam_workstream_catalog.py`, `Samantha_Agent/tests/test_human_adam_workstream_catalog.py`
- Commit: `Declare workstream private archive capabilities`
- Další krok: Provést běžný checkpoint a ověřit stejný capability výstup v Cockpitu

### Automatický checkpoint 2026-07-25 17:49 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Přístup k soukromému archivu nyní bezpečně řídí výhradně deklarativní metadata aktivního pracovního proudu
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1231 testů, 241.0 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/app/communication/human_adam_workstream_catalog.py`, `Samantha_Agent/tests/test_human_adam_profiles.py`, `Samantha_Agent/tests/test_human_adam_service.py`, `Samantha_Agent/tests/test_human_adam_workstream_catalog.py`
- Commit: `Drive private archive access from workstream capabilities`
- Další krok: Provést běžný checkpoint a po nasazení ověřit Knihovnu i proud bez private-archive capability

### Automatický checkpoint 2026-07-25 18:35 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Editor staré kontextové kotvy zmizel, rotace má vlastní panel a legacy stav zůstává viditelný pouze redigovaným upozorněním
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1221 testů, 238.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Vyřadit interaktivní UI kontextové kotvy`
- Další krok: Po checkpointu a nasazení ručně ověřit panel Vlákno, pasivní badge, běžný chat a přepnutí pracovního proudu

### Automatický checkpoint 2026-07-25 19:04 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Kontextovou kotvu už nelze číst ani měnit přes veřejné HTTP API; její private stav a dočasná modelová injekce zůstaly zachované
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1219 testů, 240.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_human_adam_service.py`
- Commit: `Vyřadit endpointy kontextové kotvy`
- Další krok: Po checkpointu a nasazení ověřit nepřístupnost starých endpointů a funkčnost chatu, statusu a rotace

### Automatický checkpoint 2026-07-25 19:34 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Kontextová kotva už neovlivňuje model, status, UI ani projektovou kontinuitu; její private data zůstala bezpečně zachovaná a neaktivní
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1218 testů, 235.0 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/app/project_continuity.py`, `Samantha_Agent/tests/test_human_adam_profiles.py`, `Samantha_Agent/tests/test_human_adam_service.py`, `Samantha_Agent/tests/test_human_adam_ui.py`, `Samantha_Agent/tests/test_project_continuity.py`
- Commit: `Odpojit modelovou injekci kontextové kotvy`
- Další krok: Po checkpointu a nasazení ručně ověřit běžný chat, přepnutí proudu, panel Vlákno a projektovou kontinuitu

### Automatický checkpoint 2026-07-25 22:50 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Nový kanonický Cockpit po automatickém restartu sám dokončí čekající deployment receipt; pozdější ověření z prohlížeče je idempotentní
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1221 testů, 320.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/simple_main_deploy.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_simple_main_deploy.py`
- Commit: `Dokončit důkaz nasazení po restartu`
- Další krok: Samostatně potvrzeně nasadit čistý main a bez otevřeného Human–Adam UI ověřit automatické uzavření receipt

### 2026-07-25 23:22 CEST – Read-only audit legacy kontextových kotev

Nazev: Human–Adam – uzavření obsahového rizika kontextové kotvy
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-25

Co se resilo:
Po záměrném vyřazení kontextové kotvy bylo potřeba ověřit, zda v zachovaných
soukromých souborech nezůstal unikátní aktuální plán, který chybí v handoffu
nebo TVBCP.

Co je hotove:
- Audit proběhl nad oběma profilovými legacy soubory bez vypsání jejich textu.
- Oba záznamy jsou krátké, starší testovací kotvy se strukturou
  `Cíl / Plán / Hotovo / Rozhodnutí / Další krok`.
- Human–Adam kotva je pozastavená. Knihovní soubor má historický příznak
  aktivity, ale současný runtime jej nečte ani nepřikládá modelu.
- Strukturální a tematické porovnání potvrdilo, že důležité obecné okruhy už
  pokrývají příslušné handoffy, TVBCP a provozní pravidla.
- Nebyl nalezen unikátní aktuální plán, který by bylo potřeba přenést.
- Žádný text kotvy nebyl zkopírován do Gitu, logů, chatu ani TVBCP.

Co neni hotove:
- Interní storage helpery, service metody, konstruktorové parametry a legacy
  testy kotvy stále zůstávají v kódu.
- Soukromé anchor soubory zůstávají zachované a nebyly změněny ani smazány.

Dalsi krok:
Odstranit mrtvý interní kód kotvy v jednom malém testovaném řezu bez mazání
private souborů.

Navrhovane dalsi kroky:
- Po změně ověřit běžný chat, přepnutí proudu a rotaci vlákna.
- O historických private souborech rozhodnout až samostatně; jejich odstranění
  není součástí cleanupu kódu.

Zmenene nebo relevantni soubory:
- `human_adam_service.py`
- `human_adam_profiles.py`
- odpovídající testy služby a profilů
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat ani necitovat obsah legacy kotev.
- Private soubory nemazat, nepřesouvat ani nemigrovat bez samostatného
  výslovného rozhodnutí.

### Automatický checkpoint 2026-07-25 23:47 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Kontextová kotva je definitivně odstraněná z produkčního kódu, konstruktorů a profilového sestavení; negativní testy brání jejímu návratu
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: plná Cockpit brána: 1216 testů, 320.2 s, výsledek OK
- Změněné cesty (8): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/app/communication/human_adam_service.py`, `Samantha_Agent/memory/ACTIVE_PROJECTS.md`, `Samantha_Agent/memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`, `Samantha_Agent/memory/tvbcp/architektura_komunikace_samantha.txt`, `Samantha_Agent/tests/test_communication_session_hub.py`, `Samantha_Agent/tests/test_human_adam_profiles.py`, `Samantha_Agent/tests/test_human_adam_service.py`
- Commit: `Dokončit odstranění kontextové kotvy`
- Další krok: Samostatně potvrzeně nasadit čistý main a ověřit běžný chat a přepnutí pracovního proudu

### Automatický checkpoint 2026-07-26 00:35 CEST

- Pracovní proud: `layer-human-adam-development`
- Souhrn: Společný read-only generátor skládá redigovaný živý stav main, deploymentu, profilových workspace a runtime bez I/O nebo změny chování
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: 9 nových regresních testů; širší sousední sada 115/115; Python syntaxe a whitespace OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/workstream_live_status.py`, `Samantha_Agent/tests/test_workstream_live_status.py`
- Commit: `Přidat generátor živého stavu pracovního proudu`
- Další krok: Napojit generátor na checkpointovou projekci; UI, model a runtime zatím neměnit

### 2026-07-26 07:57 CEST – Fáze 8.2: sémantická checkpointová projekce

Nazev: Human–Adam – živý stav v projektovém checkpointu
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-26

Co se resilo:
Checkpoint měl místo převahy technických údajů zachytit stručně, co je hotové,
co zůstává otevřené, jaká jsou rizika a jaký je skutečný další krok.

Co je hotove:
- Společný generátor z fáze 8.1 je napojený na potvrzovaný checkpoint.
- Handoff, TVBCP a jejich aktuální marker dostávají sémantické sekce Hotovo /
  Otevřeno / Rizika / Další krok.
- Předchozí serverově doložené nasazení se uzavře jako hotové, zatímco nový
  checkpoint zůstane otevřený do vlastního deployment důkazu.
- Pracovní proud bez deployment capability nedostane falešný blocker.
- Chybějící nebo neshodné důkazy selžou uzavřeně a zobrazí stručné riziko.
- Zápis zůstává součástí jediné checkpointové transakce; nevzniká následný
  dokumentační commit po pushi.
- Do dokumentů se nepropouštějí private cesty, texty zpráv, odpovědi ani PID.

Co neni hotove:
- Fáze 8.1 a 8.2 ještě nejsou nasazené v běžícím Cockpitu.
- První automaticky vytvořená projekce v reálném checkpointu bude ověřena až po
  nasazení této verze.
- UI a modelový vstup r-Adama zatím společný snapshot nekonzumují.

Dalsi krok:
Commitnout a pushnout checkpoint, čerstvě ověřit čistý shodný `main` a
samostatně potvrzeně nasadit fáze 8.1 a 8.2 společně.

Navrhovane dalsi kroky:
- Ve fázi 8.3 použít stejný snapshot v UI a modelovém vstupu bez duplikace
  rozhodovací logiky.
- V pozdější samostatné fázi přejmenovat aktuální marker na přesnější
  `Stav při posledním checkpointu`; historické bloky nepřepisovat.

Zmenene nebo relevantni soubory:
- `human_adam_profiles.py`
- `simple_main_checkpoint.py`
- `cockpit_quality_gate.py`
- odpovídající testy
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat transientní snapshot, private cesty, zprávy, odpovědi, PID ani
  citlivý obsah.
- Neodvozovat aktuální stav přepisem historických checkpointových bloků.

Technicky dukaz:
- Plná Cockpit Quality Gate prošla 1228 testy.
- Širší checkpointová a provozní sada prošla 404 testy; závěrečná cílená sada
  129 testy.
- `git diff --check`, Python kompilace, JavaScript, shell a Git safety byly
  zelené.

### 2026-07-26 09:07 CEST – Fáze 8.3a: živý stav v panelu Práce

Nazev: Human–Adam – read-only živý stav v UI
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-26

Co se resilo:
Společný redigovaný snapshot z fáze 8.1 měl dostat prvního přímého provozního
konzumenta v UI bez vzniku druhé klasifikační logiky.

Co je hotove:
- Panel `Práce` dostal samostatný box `Živý stav`.
- Box odděleně ukazuje main/GitHub, nasazení, profilové workspaces a runtime.
- Server předává právě běžící kódový otisk a používá existující read-only audit
  GitHubu, deployment účtenku, workspace statusy a session metadata.
- Neúplný, neshodný nebo cizí snapshot se zobrazí jako `Neověřeno`.
- UI ověřuje schéma, identitu aktivního proudu, `read_only=true` a
  `writes_performed=false`; text skládá pouze přes `textContent`.
- Načtení nic nesynchronizuje, nepřipojuje, nepřipravuje ani nezapisuje.

Co neni hotove:
- Fáze 8.3a ještě není nasazená v běžícím Cockpitu.
- Po nasazení zbývá ruční vizuální test panelu `Práce`.
- Modelový vstup r-Adama zatím snapshot nekonzumuje.
- První skutečný automatický checkpoint promítnutý backendem 8.2 zůstává
  provozně neověřený; tento terminálový checkpoint jej nenahrazuje.

Dalsi krok:
Commitnout a pushnout checkpoint, bezpečně zarovnat čisté profilové workspaces
a potom samostatně potvrzeně nasadit a vizuálně ověřit nový box.

Navrhovane dalsi kroky:
- Ve fázi 8.3b předat tentýž snapshot r-Adamovi bez druhé rozhodovací logiky.
- Později přejmenovat marker na `Stav při posledním checkpointu`; historické
  bloky nepřepisovat.

Zmenene nebo relevantni soubory:
- `cockpit.py`
- `human_adam_profiles.py`
- `human_adam_service.py`
- `human_adam_ui.py`
- odpovídající tři testovací soubory
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat ani zobrazovat private cesty, obsah změn, zprávy, odpovědi, PID nebo
  identifikátory vláken.
- Read-only status nesmí získat sync, reconnect ani jiný zapisovací vedlejší
  efekt.

Technicky dukaz:
- Plná Cockpit Quality Gate prošla 1232 testy za 215,1 s.
- Širší regrese prošla 487 testy; cílená sada 183 testy.
- Python, JavaScript, shell, whitespace a Git safety jsou zelené.

### 2026-07-26 10:09 CEST – Fáze 8.3b: živý stav v modelovém vstupu r-Adama

Nazev: Human–Adam – redigovaný živý stav pro r-Adama
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-26

Co se resilo:
Stejný redigovaný provozní snapshot z fáze 8.1 měl dostat druhého přímého
konzumenta v modelovém vstupu r-Adama, bez další klasifikační logiky.

Co je hotove:
- Cockpit předává serverový kódový otisk send routou profilovému manageru.
- Manager sestaví společný snapshot a vloží jeden kompaktní
  `[WORKSTREAM_LIVE_STATUS]` blok před existující `[DEVELOPMENT_CONTROL]`.
- Serializer propouští pouze schéma, identitu proudu, pevné stavové kódy,
  krátké Git otisky, počty a booleovské důkazy.
- Neplatný nebo neúplný snapshot končí jako `unverified`; selhání read-only
  GitHub auditu neblokuje odeslání zprávy.
- Jednorázové write oprávnění, izolovaná integrace, UI, persistence, reconnect
  a synchronizace zůstaly beze změny.

Co neni hotove:
- Fáze 8.3b ještě není nasazená v běžícím Cockpitu.
- Po nasazení zbývá jeden krátký živý read-only tah r-Adama a fail-closed test
  při neověřitelném vzdáleném stavu.
- První skutečná automatická projekce checkpointu z fáze 8.2 zůstává provozně
  neověřená.

Dalsi krok:
Samostatně potvrzeně nasadit čistý shodný `main` a potom ověřit jeden běžný
read-only tah r-Adama.

Navrhovane dalsi kroky:
- Později přejmenovat aktuální marker na `Stav při posledním checkpointu`;
  historické bloky nepřepisovat.
- Po živém testu uzavřít fázi 8.3 a vrátit se k dalšímu plánovanému projektu.

Zmenene nebo relevantni soubory:
- `cockpit.py`
- `human_adam_profiles.py`
- `human_adam_service.py`
- `workstream_live_status.py`
- odpovídající tři testovací soubory
- tento handoff, kanonický TVBCP a `ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Neukládat ani předávat private cesty, zprávy, odpovědi, PID nebo identifikátory
  vláken.
- Read-only audit nesmí získat sync, reconnect, prepare ani zapisovací vedlejší
  efekt.

Technicky dukaz:
- Plná Cockpit Quality Gate prošla 1237 testy za 324,1 s.
- Cílená sada 134 testů a širší Cockpit sada 329 testů prošly.
- Python, JavaScript, shell, whitespace a Git safety jsou zelené.

### Automatický checkpoint 2026-07-26 15:47 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Cockpit už neobsahuje starý oddíl Hlas ani jeho Voice Bridge JavaScript; Human–Adam mikrofon, předčítání a obecné ovládání zůstaly zachované; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1259 testů, 307.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_codex_approval_cockpit_contract.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`
- Commit: `Remove legacy Hlas frontend from Cockpit`
- Další krok: Provést checkpoint, push a nasazení ovládacími prvky Cockpitu a vizuálně ověřit hlavní obrazovku, předčítání, TVBCP a Human–Adam mikrofon

### Automatický checkpoint 2026-07-26 16:15 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Codex approval a TVBCP používají obecné API cesty a jejich staré voice aliasy už nejsou veřejně dostupné; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1261 testů, 305.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`, `Samantha_Agent/tests/test_codex_approval_cockpit_contract.py`
- Commit: `Move surviving APIs outside legacy voice namespaces`
- Další krok: Provést checkpoint, push a nasazení a živě ověřit otevření TVBCP, vyčištění Codex approval karty a nepřístupnost starých cest

### 2026-07-26 17:52 CEST – Fail-closed ochrana Git indexu

Co je hotové:
- Background statusy používají Git bez volitelných zámků a nezapisují index.
- Přerušený nebo chybějící index se nezobrazuje jako uživatelský WIP.
- Synchronizace, checkpoint i nasazení v tomto stavu zůstávají fail-closed.

Otevřeno:
- Commit a push tohoto checkpointu.
- Samostatně potvrzená obnova zachovaného recovery kandidáta.
- Společné nasazení opravy locku a hotfixu Důležitých připomenutí.

Technický důkaz:
- Cílená sada správce workspace: 24 testů.
- Navazující profilová a nasazovací sada: 183 testů.
- Plná Cockpit Quality Gate: 1267 testů.
- Živá read-only kontrola nezměnila obsah ani časy recovery kandidáta.

### Automatický checkpoint 2026-07-26 19:44 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Nepoužívané veřejné legacy Voice Bridge a Voice Mode endpointy byly odstraněny; obecné TTS, Human–Adam mikrofon, Codex approval a TVBCP zůstávají zachované.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1268 testů, 352.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit_http_security.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`
- Commit: `Retire unused legacy voice endpoints`
- Další krok: Samostatně potvrzeně nasadit čistý main a živě ověřit obecné TTS, Human–Adam mikrofon, TVBCP, Codex approval a nedostupnost odstraněných cest.

### 2026-07-26 20:36 CEST – Obnova vlastněného WIP bez dokončovací účtenky

Hotovo:
- Provizorní private ownership marker vzniká před každým zapisovacím tahem a
  po jeho dokončení bezpečně zachová původ změn i bez platné modelové účtenky.
- Panel `Práce` rozliší rozpracovaný tah, nejisté doručení, vlastněný WIP bez
  metadat a WIP připravený k potvrzené integraci.
- Samostatně potvrzovaná obnova doplní pouze git-safe metadata a znovu použije
  kanonickou plnou bránu, checkpoint, push a kontrolu zarovnání.

Rozhodnutí:
- Původ změn je provozní bezpečnostní důkaz a nesmí záviset pouze na textovém
  výstupu modelu.
- Automatický druhý modelový pokus se nyní nepřidává; obnova je deterministická
  a její zápisovací dokončení zůstává explicitně potvrzené.

Otevřeno:
- Commit a push tohoto checkpointu.
- Samostatně potvrzené nasazení a živý test jednoho záměrně chybějícího receiptu.

Rizika:
- Posun `main`, neshoda otisku změn, cizí WIP nebo nejisté doručení zůstávají
  fail-closed a nesmějí být automaticky sloučeny.

Technický důkaz:
- Cílená regresní sada prošla 429 testy.
- Plná Cockpit Quality Gate prošla 1275 testy za 335,3 s.
- Python, JavaScript, shell, whitespace a Git safety kontroly jsou zelené.

### Automatický checkpoint 2026-07-26 22:23 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Statusy Cockpitu už nenačítají ani nezveřejňují legacy Voice Mode a Voice Bridge stav; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1277 testů, 249.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/cockpit_status_service.py`, `Samantha_Agent/scripts/cockpit_smoke_check.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_status_service.py`
- Commit: `Retire legacy voice status sections`
- Další krok: Provést checkpoint, push a nasazení a ověřit pět smoke kontrol

### 2026-07-26 23:29 CEST – Git/main a běžící Cockpit jsou jednoznačně oddělené

Hotovo:
- Automatická účtenka nově říká `Git dokončen`, pojmenuje commit začleněný do
  `main` a pushnutý na GitHub a samostatně uvede serverově ověřený runtime
  commit.
- Stavový banner při rozdílu oranžově ukáže `Git/main`, běžící Cockpit a
  čekající nasazení; při shodě zobrazí jediný zelený stav.
- Nápověda i dynamické tlačítko říkají, že jeden nový runtime commit vyžaduje
  právě jeden audit a jedno potvrzené nasazení do Cockpitu.

Rozhodnutí:
- `Začlenit do main` označuje Git operaci; `nasadit do Cockpitu` označuje plnou
  bránu, řízený restart a serverové smoke ověření.
- Potvrzovací věta nově výslovně jmenuje nasazení aktuálního `main` do
  Cockpitu; bezpečnostní model a dvoukroková brána zůstávají stejné.

Otevřeno:
- Commit a push tohoto checkpointu.
- Přechodové nasazení větou z právě běžící starší UI a vizuální ověření
  oranžového i zeleného banneru.

Rizika:
- Automatický checkpoint nadále sám nerestartuje Cockpit.
- Souběžné spuštění stejného nasazení dvěma ovládacími cestami backend odmítne;
  nápověda nyní výslovně říká používat jen jednu cestu.

Technický důkaz:
- Cílená sada prošla 171 testy.
- Plná Cockpit Quality Gate prošla 1278 testy za 228,2 s.
- Python, oba JavaScripty, shell, whitespace a Git safety kontroly jsou zelené.

### Automatický checkpoint 2026-07-27 00:17 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Cockpit už neobsahuje osiřelé Voice Bridge handlery ani jejich glue kód; Janička, diagnostika, Human–Adam mikrofon a TTS zůstaly zachované; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1250 testů, 313.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`
- Commit: `Remove orphaned Cockpit voice handlers`
- Další krok: Provést checkpoint, push a nasazení a ověřit úplnou testovací bránu i pět smoke kontrol

### 2026-07-27 00:54 CEST – Pozdní úspěch nasazení už není falešný timeout

Hotovo:
- Serverová receipt zpětně prokázala, že nasazení `3df4410` uspělo: nový
  proces běžel, plná brána měla 1250 testů a smoke prošel 5/5.
- Browser nyní čeká až 120 sekund a přechodnou chybu ověřovacího endpointu
  ukládá jako průběžný stav místo okamžitého ukončení.
- Před závěrečným varováním načte stav a přijme pouze receipt odpovídající
  přesnému auditovanému commitu.

Rozhodnutí:
- Vypršení klientského čekání není důkaz neúspěchu.
- Neověřený výsledek se nesmí slepě opakovat; terminálový fallback se doporučí
  pouze při skutečně nedostupném serveru.

Otevřeno:
- Commit a push této opravy.
- Potvrzené nasazení a jeden živý restartovací test.

Rizika:
- Pokud se server nevrátí ani receipt není dostupná, stav zůstane správně
  nepotvrzený a vyžaduje read-only kontrolu.

Technický důkaz:
- Cílená UI a Cockpit sada prošla 294 testy.
- Plná Cockpit Quality Gate prošla 1251 testy za 321,9 s.
- Python, oba JavaScripty, shell, whitespace a Git safety jsou zelené.

### 2026-07-27 01:21 CEST – Banner bezpečně ověří aktuální Git/main

Hotovo:
- Redigovaný status poskytuje allowlistovaný 12znakový `source_head_short`,
  nikoli celý Git hash.
- Human–Adam porovná tento otisk s deployment receipt a při shodě zobrazí
  společný commit `Git/main` a běžícího Cockpitu.
- Neplatný nebo chybějící otisk zůstane jako neověřený stav.

Rozhodnutí:
- Oprava nerozšiřuje veřejný status o plný Git hash ani private metadata.
- Serverová deployment receipt zůstává autoritativním důkazem nasazení.

Otevřeno:
- Commit, push a samostatně potvrzené nasazení opravy.
- Vizuální kontrola zeleného banneru po restartu Cockpitu.

Rizika:
- Zkrácený otisk je pouze bezpečná porovnávací identita; při neplatném formátu
  musí UI dál selhat uzavřeně.

Technický důkaz:
- Cílených 83, širších 338 a úplných 1252 testů prošlo.
- Plná Cockpit Quality Gate doběhla za 326,1 s; syntaxe, JavaScript, shell,
  whitespace a Git safety jsou zelené.

### 2026-07-27 08:25 CEST – Fáze 9.3e a servisní převzetí po sovím commitu

Hotovo:
- Živé diagnostiky, přehled Codex relací a starý Adam fallback už nečtou Voice
  Bridge marker jako obecnou provozní autoritu.
- Janička orphan audit a cleanup používají vlastní registry spravovaných relací
  a při jejich nedostupnosti selžou uzavřeně.
- Automatická integrace zachovala devítisouborový WIP, když GitHub během tahu
  postoupil sovím commitem. Servisní kontrola potvrdila nulový překryv cest,
  vytvořila obnovitelný checkpoint a začlenila změny nad sovu.
- Před checkpointem bylo odhaleno a opraveno sedm regresí testovacího přechodu
  z odstraněného Cockpit wrapperu na přímý runtime modul.

Rozhodnutí:
- Voice Bridge marker není autoritou vlastnictví Janička ani obecných Codex
  relací.
- Posun `main` během odloženého WIP se dál řeší fail-closed a servisně podle
  přesného překryvu cest; tato kontrola se neobchází automatickým merge/rebase.

Otevřeno:
- Doplnit checkpointový commit, push a zarovnání profilů.
- Samostatně potvrzené nasazení a živý retest diagnostiky relací.

Rizika:
- Runtime VoiceBridge modul a private stav zůstávají zachované; jejich případné
  odstranění patří až do samostatné auditované fáze 9.4.

Technický důkaz:
- Cílená sada prošla 313 testy.
- Plná Cockpit Quality Gate prošla 1254 testy za 300,1 s.
- Soví commit měnil jen čtyři cesty mimo Samantha Agent a s WIP neměl překryv.

### 2026-07-27 11:19 CEST – Dávkový GitHub režim

Hotovo:
- Běžné dokončení ukládá přes den samostatné lokální commity bez pushnutí.
- Lokální nasazení není blokované starším nebo divergentním GitHubem.
- Panel Práce umí auditovat a potvrzeně odeslat všechny čekající commity jedním
  večerním pushem po jedné úplné bráně.

Rozhodnutí:
- Lokální `main` je přes den provozní autorita.
- Divergence blokuje jen večerní balíček, nikoli další lokální práci.
- Merge, rebase, squash a force push se automaticky nepoužívají.

Další krok:
- Pushnout bootstrap commit a samostatně potvrzeně nasadit nový `main`.

Navrhované další kroky:
- Po živém malém vývoji rozhodnout, zda zůstane balíček ruční, nebo dostane
  pevný večerní čas.

Technický důkaz:
- Úplná Cockpit Quality Gate prošla 1269 testy; syntaxe, oba JavaScripty, shell
  a whitespace kontrola jsou zelené.

### 2026-07-27 16:50 CEST – Malé verzované mazání už neblokuje dokončení vývoje

Hotovo:
- Schválený vývojový krok může automaticky checkpointovat, převzít do `main`
  a synchronizovat až deset smazaných verzovaných souborů.
- Stejné pravidlo používá modelový kontrakt, checkpoint, integrační převzetí
  i dorovnání čistých profilových workspace.
- Zastaralý approval kontraktní test po fázi 9.4b nyní ověřuje samostatný
  Codex approval stav bez závislosti na odstraněném Voice Mode importu.

Rozhodnutí:
- Jednotlivé smazání je běžná obnovitelná Git změna, pokud je výslovnou
  součástí Mílova zadání nebo schváleného vývojového plánu.
- Jedenáct a více smazaných cest zůstává hromadnou změnou se servisním
  potvrzením; blokované private, env a mediální cesty zůstávají nepovolené.

Další krok:
- Vytvořit lokální commit, dorovnat oba workspaces a samostatně potvrzeně
  nasadit aktuální `main` do Cockpitu.

Navrhované další kroky:
- Při příštím skutečném malém cleanupu ověřit, že automatické dokončení projde
  bez servisního převzetí.
- Limit měnit pouze podle doložené provozní potřeby.

Technický důkaz:
- Cílených 65 testů a úplných 1239 Cockpit testů prošlo.
- Python, JavaScript, shell a `git diff --check` jsou zelené.

### Automatický checkpoint 2026-07-27 17:15 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Start Samanthy ani aktivní pravidla už nevytvářejí a nepřebírají Voice Bridge marker; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/AGENTS.md`, `Samantha_Agent/memory/technical/session_recovery_rules.md`, `Samantha_Agent/scripts/mark_current_codex_tty.py`, `Samantha_Agent/scripts/samantha_screen_entry.sh`, `Samantha_Agent/tests/test_codex_session_report.py`
- Commit: `Retire Voice Bridge marker lifecycle`
- Další krok: Provést checkpoint a nasazení; potom pokračovat fází 9.4d odstraněním zbývajícího Voice Bridge runtime a spotřeby markeru

### Automatický checkpoint 2026-07-27 18:09 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Panel Práce nyní jasně ukazuje aktuální nasazení a nenabízí zbytečný opakovaný audit; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.3 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Clarify current Cockpit deployment status`
- Další krok: Provést checkpoint a nasazení hotfixu a živě ověřit zelený stav na mobilu i Macu

### Automatický checkpoint 2026-07-27 20:59 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Poslední mrtvé runtime jádro Voice Bridge je odstraněné a servisní runner je obecný; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1141 testů, 367.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (15): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/speech/adam_voice_mode.py`, `Samantha_Agent/app/speech/terminal_bridge.py`, `Samantha_Agent/app/speech/voice_inbox.py`, `Samantha_Agent/app/voice_bridge_state.py`, `Samantha_Agent/scripts/adam_voice_reply.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_adam_voice_mode.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`, `Samantha_Agent/tests/test_codex_approval_cockpit_contract.py`, `Samantha_Agent/tests/test_terminal_bridge.py`, `Samantha_Agent/tests/test_voice_bridge_state.py`, `Samantha_Agent/tests/test_voice_inbox.py`
- Commit: `Complete Voice Bridge runtime amputation`
- Další krok: Provést checkpoint a nasazení, potom zahájit závěrečný úklid 9.4e

### Automatický checkpoint 2026-07-27 22:05 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Přidána potvrzovaná bezeztrátová migrace starého private TVBCP do soukromého kontextu proudu Brainstorm včetně bezpečných instrukcí a testů.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/communication/human_adam_profiles.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/app/communication/legacy_tvbcp_migration.py`, `Samantha_Agent/scripts/migrate_legacy_tvbcp_to_brainstorm.py`, `Samantha_Agent/tests/test_legacy_tvbcp_migration.py`
- Commit: `Add legacy TVBCP migration to Brainstorm`
- Další krok: Nasadit aktuální main; samotnou private migraci spustit až samostatnou přesnou potvrzovací větou.

### 2026-07-27 22:50 CEST – Human–Adam má obecný přímý přístup ke kanonickým private datům

Hotovo:
- Human–Adam rozlišuje izolovaný workspace pro kód a Git od kanonické soukromé
  oblasti pro skutečná provozní data.
- V kanonické soukromé oblasti může přímo číst, diagnostikovat a na jasný
  Mílův pokyn provést jednu běžnou nedestruktivní úpravu.
- Knihovna si zachovává užší přístup pouze ke svému soukromému archivu.
- Dokončovací účtenka se řídí konečným stavem posledního relevantního opakování
  testů; opravený meziběh už sám o sobě dokončení neblokuje.

Rozhodnutí:
- Nevznikají nové operace ani další potvrzovací brány. Stávající zvláštní
  potvrzení zůstává jen pro mazání, hromadné změny, odesílání ven, práci s
  tajemstvím a systémové zásahy.
- Absence soukromého souboru v izolované kopii nesmí být vydávána za absenci
  kanonických dat.

Další krok:
- Po samostatně potvrzeném nasazení provést jeden malý živý Human–Adam test nad
  neškodnou soukromou operací bez opisování jejího obsahu.

Navrhované další kroky:
- Pokud živý test uspěje, nepřidávat další obecné brány a řešit už jen konkrétní
  doložené provozní chyby.

Rizika:
- Přístup k obecné soukromé oblasti je širší než dřívější profilová výjimka.
  Hranice rizikových akcí proto stojí na stávajícím modelovém a globálním
  bezpečnostním kontraktu; private texty nesmějí do Gitu, logů, handoffu,
  TVBCP ani odpovědi.

Technický důkaz:
- Prošlo 167 cílených testů.
- Úplná Cockpit Quality Gate prošla 1150 testy; Python, JavaScript, shell,
  whitespace a Git safety kontroly jsou zelené.

### Automatický checkpoint 2026-07-28 06:12 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Staré TVBCP tlačítko, modal, endpoint a výhradní obslužný kód jsou z Cockpitu odstraněné, zatímco Brainstorm kontext i projektový TVBCP Human–Adam zůstávají zachované.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1147 testů, 299.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/tvbcp.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/scripts/tvbcp.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`, `Samantha_Agent/tests/test_tvbcp.py`
- Commit: `Retire obsolete Cockpit TVBCP surface`
- Další krok: Provést checkpoint a nasazení, potom pokračovat fází 9.4e-b.

### Automatický checkpoint 2026-07-28 06:39 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Aktivní registry, návody a modelové instrukce už nesměřují ke starému VoiceBridge ani odstraněné komunikaci Janičky; historické důkazy zůstávají zachované.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.6 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (13): `Samantha_Agent/app/codex_approval_state.py`, `Samantha_Agent/app/communication/human_adam_workstream_catalog.py`, `Samantha_Agent/app/samantha_agent.py`, `Samantha_Agent/memory/ACTIVE_PROJECTS.md`, `Samantha_Agent/memory/MEMORY_INDEX.md`, `Samantha_Agent/memory/WORKSTREAMS.md`, `Samantha_Agent/memory/projects/email_readonly_oauth.md`, `Samantha_Agent/memory/projects/janicka_cockpit_kucharka.md`, `Samantha_Agent/memory/projects/janicka_cockpit_takeover.md`, `Samantha_Agent/memory/projects/tts_edge_audio_tools.md`, `Samantha_Agent/memory/technical/session_recovery_rules.md`, `Samantha_Agent/tests/test_cockpit_voice_frontend_retirement.py`, `Samantha_Agent/tests/test_human_adam_workstream_catalog.py`
- Commit: `Retire active legacy communication guidance`
- Další krok: Provést checkpoint a nasazení, potom spustit závěrečnou fázi 9.4e-c s úplnou Cockpit Quality Gate a smoke testem.

### 2026-08-01 13:01 CEST – Všechny zvolitelné proudy mají jednotný jednorázový vývoj

Hotovo:
- Historický allowlist `MMTX`, `Rodinný kalendář` a `R2-Adam` byl odstraněn.
- Každý zvolitelný aktivní i pozastavený proud nyní zveřejňuje schopnosti
  `development`, `checkpoint` a `one_turn_write`.
- Tah bez výslovného vývojového záměru zůstává nezapisovací. Při vývojovém
  záměru se dál ověřuje připojení, nečinný tah, čistota a shoda všech
  profilových workspaces a kanonická vazba handoffu/TVBCP.
- Čekající denní GitHub balíček není blokátorem dalšího vývoje.

Rozhodnutí:
- Pracovní proud určuje kontext, paměť, capability a bezpečnostní hranice;
  samotná zvolitelná identita proudu nesmí být důvodem k zákazu vývoje.
- Pozastavený proud lze zapisovat až po jeho výslovném zvolení. Archivované
  proudy zůstávají mimo výběr a nelze je otevřít pro jednorázový vývoj.
- Profilový semafor zůstává oddělenou kompatibilní cestou; lazy proudy používají
  jednorázové serverové oprávnění a automatický kanonický checkpoint.

Další krok:
- Vytvořit lokální commit do denního GitHub balíčku. Nasazení provést až
  samostatně potvrzeným krokem.

Navrhované další kroky:
- Po nasazení zvolit dříve nepovolený proud, například Samantha Agent/RAG, a
  živě ověřit, že `Zahájit vývoj` lze stisknout.
- Při živém testu provést jen jeden malý bezpečný krok a ověřit automatický
  checkpoint do správného handoffu a TVBCP.

Technický důkaz:
- Cílená sada `tests.test_human_adam_profiles` prošla 106 testy.
- Plná Cockpit Quality Gate prošla 1263 testy; Python, JavaScript, shell,
  whitespace a Git-safety kontroly jsou zelené.
- Běžící Cockpit tuto lokální změnu zatím neobsahuje.

### 2026-08-01 13:12 CEST – Jednotný zapisovací režim je živě nasazený

Hotovo:
- Commit `ef3526d` byl řízeně nasazen do Cockpitu a serverová účtenka potvrdila
  stav `deployed`.
- Aktivní proud Samantha Agent/RAG po restartu hlásí `development=true`,
  `checkpoint=true`, `one_turn_write=true` a `write_authorization=one_turn`.
- Human–Adam byl znovu připojený, tah není aktivní a samostatný smoke prošel 5/5.

Rozhodnutí:
- Funkční oprava je provozně uzavřená. GitHub push zůstává oddělený v denním
  balíčku a nebyl součástí nasazení.

Další krok:
- V Human–Adam lze stisknout `Zahájit vývoj` a pokračovat malým krokem P7 v
  proudu Samantha Agent/RAG.

Navrhované další kroky:
- Při prvním skutečném vývojovém tahu ověřit správný automatický checkpoint;
  nový obecný test zápisu není potřeba vynucovat před běžnou prací.

Technický důkaz:
- Nasazený kódový commit: `ef3526d`.
- Serverová verifikace: `deployed`, rychlá předrestartová brána, nový proces.
- Následný Cockpit smoke: 5/5.

### 2026-08-05 12:52 CEST – Serverová pojistka dokončení vývojového tahu

Hotovo:
- Výsledek účtenky se ukládá do samostatného redigovaného private registru jako
  stav tahu, checkpoint, GitHub čekání a úspěch uložení odpovědi.
- Další modelový tah dostává blok `LAST_STEP_COMPLETION`; Cockpit zobrazuje
  stejný serverový výsledek odděleně od textu modelu.
- Úspěšný checkpoint se znovu ověřuje proti historii `main` a čistému workspace.
  Neuzavřený nebo nejistý stav blokuje nový zapisovací tah.

Rozhodnutí:
- Modelová účtenka pouze žádá o dokončení. Autoritou pro skutečný výsledek je
  serverový stav ověřený proti Gitu a workspace.
- Registr neukládá chat, souhrn vývoje ani soukromý obsah.

Další krok:
- Vytvořit lokální commit. Nasazení do běžícího Cockpitu zůstává samostatné.

Navrhované další kroky:
- Po potvrzeném nasazení živě ověřit jeden malý zapisovací tah a následný dotaz
  Human–Adamovi, zda předchozí checkpoint uspěl.

Technický důkaz:
- Cílená rozšířená sada prošla 250 testy.
- Plná Cockpit Quality Gate prošla 1301 testy za 304,824 s.

### 2026-08-05 13:37 CEST – Samoobnovitelné serverové dokončení

Hotovo:
- Dokončení zapisovacího tahu je trvalá private úloha oddělená od životnosti
  chatového HTTP požadavku.
- Worker obnoví čekající úlohu po restartu, ověří přesný otisk WIP a pomocí
  commit traileru bezpečně naváže i po pádu mezi commitem a převzetím do main.
- Přechodné selhání procesu brány zopakuje nejvýše jednou; chybu testů nebo
  změněný workspace neopakuje.

Rozhodnutí:
- Úspěch se dál uznává jen podle serverového stavu, Gitu a workspace. Zařazení
  úlohy není totéž co dokončený checkpoint.
- File lease a idempotentní klíč brání souběžnému workeru a dvojímu commitu.

Další krok:
- Vytvořit lokální commit; nasazení zůstává samostatné.

Navrhované další kroky:
- Po nasazení provést malý živý tah a kontrolovaný restart v průběhu dokončení.

Technický důkaz:
- Cílený balík: 174 testů.
- Plná Cockpit Quality Gate: 1309 testů, 288,459 s, OK.

### 2026-08-07 13:59 CEST – Dokončení a poradní tah jsou provozně narovnané

Hotovo:
- Completion úloha úspěšně dokončila převzatý knihovní WIP po bezpečném
  dorovnání na `main`.
- Poradní tah bez souborových změn má vlastní neutrální stav.
- Všechny proudy mohou registrovaný read-only webový průzkum.

Rozhodnutí:
- Text odpovědi ani modelová účtenka nejsou důkazem dokončení; rozhoduje
  serverový stav, Git a workspace.

Další krok:
- Pokračovat běžným vývojem a zasahovat jen při novém doloženém selhání.

Navrhované další kroky:
- Doplnit automatickou synchronizaci `ACTIVE_PROJECTS.md` až jako samostatný
  malý workflow krok.

Technický důkaz:
- Pojistky jsou obsažené v živě nasazeném `91dc700`; smoke 5/5.

### 2026-08-07 16:03 CEST – Checkpoint synchronizuje tři vrstvy projektové paměti

Hotovo:
- Potvrzený checkpoint aktualizuje handoff, TVBCP a primární řádek proudu v
  `ACTIVE_PROJECTS.md` před vytvořením jediného checkpointového commitu.
- Při chybě zápisu nebo commitu obnoví všechny tři původní obsahy.
- Všech 30 proudů včetně Brainstorm a Misc má jednoznačný agregovaný řádek.

Rozhodnutí:
- Synchronizace je součástí stávajícího autoritativního checkpointu. Nevzniká
  druhý commit, watcher ani paralelní registr.
- U proudu s více zdrojovými řádky se mění pouze první kanonický zdroj.

Další krok:
- Po samostatně potvrzeném nasazení ověřit první přirozený checkpoint a
  následný audit s nulovým driftem.

Navrhované další kroky:
- Ponechat audit driftu jako nezávislou pojistku.
- Terminálové změny věcného stavu dál ručně promítat do projektové paměti.

Technický důkaz:
- 47 cílených checkpointových, katalogových a paměťových testů prošlo.
- 120 sousedních profilových a reportových testů prošlo.
- Plná Cockpit Quality Gate prošla 1329 testy.

### Automatický checkpoint 2026-08-11 15:08 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Adamovy dokončené odpovědi lze jedním tlačítkem zkopírovat bez doprovodných metadat; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Add copy button to Human-Adam replies`
- Další krok: Po checkpointu a nasazení živě ověřit kopírování na Macu nebo iPhonu

### Automatický checkpoint 2026-08-12 11:56 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Human–Adam připraví obrazový návrh, po samostatném potvrzení vytvoří private kandidáta a umožní jej schválit nebo zamítnout bez publikace; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1354 testů, 306.8 s, výsledek OK
- Změněné cesty před paměťovým zápisem (9): `Samantha_Agent/app/capabilities/registry.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_capability_registry.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_human_adam_ui.py`, `Samantha_Agent/app/communication/human_adam_images.py`, `Samantha_Agent/tests/test_human_adam_images.py`
- Commit: `Add confirmed Human-Adam image candidates`
- Další krok: Po checkpointu samostatně potvrdit nasazení a živě ověřit jeden neškodný obrázkový požadavek

### Automatický checkpoint 2026-08-12 13:54 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Generování obrázků je dostupné ve všech současných proudech a řídí je výhradně deklarativní capability konfigurace; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.7 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/communication/human_adam_images.py`, `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/app/communication/human_adam_workstream_catalog.py`, `Samantha_Agent/tests/test_human_adam_images.py`, `Samantha_Agent/tests/test_human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_workstream_catalog.py`
- Commit: `Enable image generation by workstream capability`
- Další krok: Samostatně potvrdit nasazení a živě ověřit generování ve dvou různých pracovních proudech

### Servisní dokončení 2026-08-12 22:33 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Globální, trvalý a odvolatelný souhlas s registrovaným externím
  generováním je oddělený od běžného externího odesílání a platí ve všech
  pracovních proudech pouze pro necitlivý obsah.
- Bezpečnost: Souhlas zůstává private, poškozený stav selže uzavřeně, zjevně
  citlivý prompt paušální souhlas nepoužije a publikování, Git push, nasazení,
  nákupy, přihlášení i destruktivní akce zůstávají mimo rozsah.
- Ověření: cílená sada 486/486; plná Cockpit Quality Gate 1403/1403.
- Další krok: Po samostatně potvrzeném nasazení ověřit stav v panelu Práce a
  jeden neškodný smyšlený obrazový požadavek.

### Servisní oprava 2026-08-13 18:51 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Klient privátního app-serveru bezpečně obnoví i vlákno obsahující
  generovaný obrázek; konečný lokální limit rámce je 32 MiB místo 8 MiB.
- Příčina: Původní MMTX `thread/resume` vrátil rámec přibližně 18 MiB a spojení
  skončilo kódem `MESSAGE_TOO_BIG`, přestože proces i socket byly zdravé.
- Ověření: cíleně 5/5, reálné obnovení původního vlákna prošlo a plná Cockpit
  Quality Gate prošla 1403/1403 za 425,2 s.
- Další krok: Samostatně potvrdit nasazení a živě ověřit Připojit v MMTX.

### Servisní vývoj 2026-08-13 20:26 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Více obrazových výstupů jednoho dokončeného tahu se idempotentně
  převádí do private kandidátů a UI je zobrazuje jako galerii.
- Bezpečnost: Nejvýše osm obrázků na tah a 25 MiB na soubor; žádné base64 ani
  lokální cesty v session JSON nebo veřejném API; jednotlivé verze zůstávají
  bez publikace a čekají na rozhodnutí.
- Obnova: Čtyři dříve nezobrazené MMTX obrázky jsou zachráněné jako čtyři
  samostatné kandidátní verze.
- Ověření: cílená a integrační sada 501/501; plná Cockpit Quality Gate
  1409/1409 za 442,1 s.
- Další krok: Vytvořit checkpoint a samostatně potvrzené nasazení; potom živě
  ověřit galerii čtyř obrázků.

### Automatický checkpoint 2026-08-16 16:47 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Checkpoint a informace o nasazení jsou na mobilu schované pod horními Podrobnostmi, takže chat má více prostoru; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Collapse technical receipts on mobile`
- Další krok: Samostatně potvrdit nasazení a vizuálně ověřit výšku chatu na iPhonu

### Terminálový vývoj 2026-08-29 19:52 CEST – Human–Adam získává samoobslužné MMTX p+n

- Pracovní proud: `layer-human-adam-development`
- Hotovo: MMTX má deklarovaný produkční cíl GitHub Pages. Přesný příkaz `p+n` nebo přímé „nasaď na produkci“ serverově zřetězí případný bezpečný GitHub balíček, Pages workflow, kontrolu deploymentu a HTTP smoke.
- Rozhodnutí: Model pouze předává záměr; Git, GitHub workflow a ověření vykonává registrovaný backend. Samotný push nadále není důkazem produkce.
- Rizika: Operace selže uzavřeně při nečistém nebo divergentním main, neshodě GitHubu, chybě workflow, chybějícím deploymentu nebo neúspěšném smoke; opakované nasazení stejného commitu se nespustí.
- Další krok: Úplná brána, commit, push, nasazení Cockpitu a živý test `p+n` v MMTX.
- Ověření: cílená sada 156/156 a úplná brána 1475/1475; současný MMTX commit `933834f` byl ručně publikován runem `33266361424` a veřejné vzorky scén 2 a 3 jsou hashově shodné.

### Živý retest a oprava 2026-08-29 20:25 CEST – Pages účtenka čeká na finální deployment

- Pracovní proud: `layer-human-adam-development`
- Hotovo: První živé `p+n` spustilo run `33267653174` a publikovalo přesný commit `a0ab509`. Serverová účtenka ale selhala, protože GitHub zobrazil úspěšný deployment `6158651157` až několik sekund po dokončení workflow. Publisher nyní čeká omezeně 30×1 s na úspěšný deployment stejného commitu.
- Rozhodnutí: Falešně záporný výsledek se nikdy neřeší slepým opakováním; nejprve se koreluje přesné workflow a deployment. Čekání je konečné a při chybě nebo cizím commitu dál selže uzavřeně.
- Další krok: Commit, push, řízené nasazení Cockpitu a jediný opakovaný živý test `p+n`.
- Ověření: cíleně 14/14; úplná Cockpit Quality Gate 1476/1476 za 442,2 s; GitHub Pages deployment `6158651157` má stav success pro `a0ab509` a veřejný kořen odpovídá HTTP 200.

### Živý retest a oprava 2026-08-29 20:32 CEST – HTTPS smoke používá systémové TLS

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Druhý živý `p+n` spustil run `33268409643` a deployment `6158799240` pro přesný commit `d0fb736`. GitHub část uspěla; falešně zápornou účtenku způsobilo až `CERTIFICATE_VERIFY_FAILED` v lokálním Python `urllib`. Smoke nyní volá pevný systémový `/usr/bin/curl` bez shellu.
- Rozhodnutí: Produkční důkaz nadále vyžaduje HTTP 200, ale používá systémové TLS úložiště Macu. Selhání HTTPS, nečíselný stav i stav odlišný od 200 dál zastaví operaci.
- Další krok: Commit, push, řízené nasazení Cockpitu a živé ověření již publikovaného commitu bez nového workflow.
- Ověření: cílená sada publisheru a provozní vrstvy 37/37; úplná Cockpit Quality Gate 1477/1477 za 445,1 s; GitHub run `33268409643` i deployment `6158799240` jsou success pro `d0fb736`; veřejná URL vrací přes systémový curl HTTP 200.

### Praktické dokončení 2026-08-29 20:44 CEST – Human–Adam nasadil MMTX s pravdivou účtenkou

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Oprava `72aedbf` je na GitHubu i v běžícím Cockpitu. Finální živý pokyn `p+n` v aktivním MMTX sám spustil Pages run `33269031345`, koreloval deployment `6158917594` se stejným commitem a vrátil `completed`, `deployed` a HTTP 200.
- Rozhodnutí: Samoobslužné nasazení MMTX je provozně dokončené. Přesný `p+n` zůstává jediným zkráceným pokynem, který může serverově zřetězit bezpečný push a ověřené Pages nasazení.
- Další krok: Při dalším hotovém vývoji MMTX použít `p+n`; při fail-closed výsledku příkaz automaticky neopakovat a nejprve auditovat přesné workflow/deployment ID.
- Ověření: cíleně 37/37, úplná brána 1477/1477 za 445,1 s, Cockpit quick gate 7,7 s a smoke 5/5; produkční účtenka obsahuje commit `72aedbfffc3f`, run `33269031345`, deployment `6158917594` a HTTP 200.

### Regresní oprava 2026-08-29 20:49 CEST – Přesný p+n nepodléhá modelové obálce

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Úklidový retest vrátil `invalid`, aniž spustil backend nebo workflow, protože model přidal vadnou provozní obálku. Server nyní při přesném autorizovaném MMTX `p+n` vždy vytvoří jediný kanonický požadavek `mmtx_pages_publish_current_main` a modelovou obálku nepoužije k autorizaci ani volbě operace.
- Rozhodnutí: Autorizaci dává výhradně přesný uživatelský text a deklarativní produkční cíl pracovního proudu; model smí dodat pouze viditelný doprovodný text.
- Další krok: Commit, push, nasazení Cockpitu a poslední živý `p+n`.
- Ověření: cíleně 16/16 včetně vadné modelové obálky a úplná Cockpit Quality Gate 1478/1478 za 446,9 s; neúspěšný retest měl `attempted=false` a nevytvořil žádný GitHub workflow.

### Praktické dokončení 2026-08-29 21:01 CEST – Kanonické p+n živě potvrzeno

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Oprava `0230cf5` je na GitHubu i v běžícím Cockpitu. Regresní živé `p+n` skončilo `completed`, spustilo run `33269734786`, ověřilo deployment `6159053676` stejného commitu a veřejný HTTP 200.
- Rozhodnutí: Přesný uživatelský `p+n` a deklarovaný cíl `github_pages` jsou jedinou autoritou; modelová obálka nemůže operaci změnit ani zablokovat.
- Další krok: Při dalším dokončeném MMTX vývoji použít `p+n`; při fail-closed výsledku nejprve auditovat přesná ID bez automatického opakování.
- Ověření: cíleně 16/16, úplná brána 1478/1478 za 446,9 s, Cockpit quick gate 7,8 s a smoke 5/5; produkční účtenka obsahuje commit `0230cf543ef4`, run `33269734786`, deployment `6159053676` a HTTP 200.

### Vývojový krok 2026-08-31 11:48 CEST – gpt-transcribe-migration

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Dokončené hlasové nahrávky Human–Adam nově používají `gpt-transcribe` na stávajícím `/v1/audio/transcriptions`. SDK i izolovaná systémová `curl` cesta posílají `response_format=json`, `languages=["cs"]` a úzkou sadu českých/doménových `keywords`; staré pole `language` ani ukončovaný výchozí model už aktivní kód a testy neobsahují. Editovatelný přepis, dočasné audio, limity velikosti a výslovné ruční odeslání zůstaly beze změny.
- Co není hotovo: Běžící Cockpit nebyl řízeně restartován ani nasazen. Skutečný uživatelský hlasový pokyn po migraci zatím nebyl ověřen.
- Rizika: `keywords` jsou nápověda, nikoli vynucený slovník; při živém retestu je třeba ověřit přesnost a nepřítomnost nevyslovených klíčových slov. Lokální OpenAI SDK 2.36.0 přijímá nová pole kompatibilně přes `extra_body`, protože je ještě nemá v běžném podpisu metody.
- Další krok: Samostatně potvrdit řízené nasazení Cockpitu a potom jednou nahrát krátký český pokyn, zkontrolovat přepis v editoru a teprve ručně odeslat.
- Navrhované další kroky: `gpt-live-transcribe` nepřidávat, dokud nebude samostatně požadovaný průběžný živý přepis; současný tok vždy nejprve dokončí nahrávku.
- Ověření: 23/23 cílených testů; syntetický český API smoke vrátil přesný text modelem `gpt-transcribe` za 2,6 s; úplná Cockpit Quality Gate prošla 1507/1507 za 458,4 s; `git diff --check` je čistý.
- Bezpečnost / neukládat: API smoke obsahoval jen syntetickou větu bez soukromých údajů. Audio vzniklo pouze v dočasném adresáři a po testu bylo odstraněno. Token ani API klíč se nevypsal a nepatří do Gitu.

### Nasazení 2026-08-31 12:04 CEST – gpt-transcribe-migration běží v Cockpitu

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Commit `bee5ad5` byl řízeně nasazen bez GitHub pushnutí. Před restartem prošla rychlá nasazovací brána, nový Cockpit nahradil PID 7920 procesem 36363 a běží s očekávaným kódovým otiskem `a254773e73d02854`. Serverová verifikace potvrdila nový proces, oba zarovnané workspaces a smoke 5/5.
- Rozhodnutí: Nasazovací účtenka patří kanonickému proudu Human–Adam; před nasazením byl proto čistý a nečinný Cockpit přepnut z MMTX na `layer-human-adam-development`. Tři tehdejší lokální commity zůstaly nepushnuté v denním GitHub balíčku.
- Rizika: Skutečný Mílův hlas zatím po migraci ověřen nebyl. `keywords` mohou ovlivnit přepis, proto je při ručním retestu třeba hlídat i nevyslovené termíny.
- Další krok: V Human–Adam jednou nahrát krátký český pokyn, zkontrolovat přepis v editoru a odeslat jej až ručně.
- Navrhované další kroky: Pokud bude přepis přesný, migraci provozně uzavřít bez zavádění `gpt-live-transcribe`.
- Ověření: Post-deploy syntetická věta prošla přes skutečný `/api/human-adam/transcribe` se stavem `transcribed_for_review` a přesným textem. Následný health potvrzuje PID 36363 a otisk `a254773e73d02854`.
- Bezpečnost / neukládat: Post-deploy test používal pouze syntetickou větu; dočasné audio bylo odstraněno a žádný klíč ani soukromý text se nezapsal do Gitu.

### Automatický checkpoint 2026-08-31 12:25 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Scéna 5 má zvolenou lehčí produkční kvalitu q90 a obecné pravidlo optimalizace obrazů je kanonicky zaznamenané
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `MatysekANJ/web_mmtx/scene05_log_bridge/webp_quality_pilot.html`, `Samantha_Agent/memory/handoffs/workstreams/project-mmtx.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-mmtx.md`, `Samantha_Agent/tests/test_mmtx_scene05_webp_pilot.py`, `docs/scene05_log_bridge/webp_quality_pilot.html`
- Commit: `Vybrat WebP q90 pro scénu 5`
- Další krok: Zapojit WebP q90 jako obrazový základ funkční scény 5

### Automatický checkpoint 2026-08-31 14:01 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Nově otevřený pracovní proud se spolehlivě zobrazí u poslední zprávy, aniž běžné obnovení rušilo čtení historie
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 6.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Opravit posun chatu po přepnutí proudu`
- Další krok: Samostatně nasadit změnu a ověřit přepnutí dlouhého proudu na Linux PC

### Servisní oprava 2026-09-02 07:40 CEST – obnovení dlouhého obrazového vlákna

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Privátní Unix-socket klient přijme při `thread/resume` rámec až 64 MiB, takže současné dlouhé MMTX vlákno s obrazovými výstupy už neblokuje vzdálené navázání. Limit zůstává konečný a týká se pouze lokálního socketu.
- Otevřeno: Opravu je třeba commitnout, pushnout, řízeně nasadit do Cockpitu a živě ověřit na témže vlákně.
- Rizika: Vlákno s rámcem nad 64 MiB zůstane správně odmítnuté. Další růst historie je signál k zachované rotaci vlákna, ne k neomezenému transportu.
- Další krok: Spustit úplnou bránu, vytvořit jeden lokální commit, uzavřít GitHub balíček, nasadit Cockpit a ověřit reconnect plus read-only tah.
- Ověření: Skutečná vnitřní příčina byla WebSocket `1009` pro rámec 46 323 050 B proti limitu 32 MiB; cílená sada prošla 176/176 a `git diff --check` je čistý.

### Automatický checkpoint 2026-10-19 13:00 CEST

- Pracovní proud: `layer-human-adam-development`
- Hotovo: Human–Adam upřednostňuje chat a aktuální stav; technické účtenky jsou dostupné v panelu Práce
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `Samantha_Agent/app/communication/human_adam_ui.py`, `Samantha_Agent/tests/luna_release_frontend.test.cjs`, `Samantha_Agent/tests/test_human_adam_ui.py`
- Commit: `Zjednodušit úvodní obrazovku Human–Adam`
- Další krok: Po samostatném nasazení vizuálně ověřit čitelnost chatu a panel Práce na Linuxu a iPhonu

### 2026-11-04 23:01 CET — 05/P1-B: lokální modernizace App Server klienta

Hotovo:
- Obnova vlákna žádá metadata bez historie; explicitní final_answer má přednost před commentary a partial textem. Strukturované RPC a turn chyby jsou přístupné bez zahrnutí soukromého obsahu do běžného textu výjimky.
- Před prací s vláknem se ověří stabilní verze připojeného serveru od 0.163.0. Zůstává přesný důkaz doručení i blokace opakování nejisté akce po restartu session hubu.

Rozhodnutí:
- Míla výslovně schválil 05/P1-B a nový zápis. Zachovat původního klienta bez adopce SDK, bez změn runtime, Cockpitu či e-mailů; vše pouze ve vlastní větvi.

Další krok:
- Will převezme diff a report; integrace do main a provozní přejímka vyžadují samostatné rozhodnutí. Přímé převzetí není potvrzené.

Navrhované další kroky:
- Po případné autorizované integraci a nasazení ověřit handshake a reconnect stejného vlákna se zachovanými oprávněními. Proxy a Mac/iPhone přejímka zůstávají samostatné.

Technický důkaz:
- 100 cílených testů PASS; úplná Cockpit brána PASS: 2 373 testů, 0 chyb a selhání, 5 skipů PDF exportů bez ReportLabu. Podrobnosti v `reports/codex_appserver_p1b_20261104.md`; pilotní commit `607fc538`.
- Žádný modelový tah, živá služba, sdílený provozní zápis, push, restart ani integrace do main. Kanonický TVBCP `tvbcp/architektura_komunikace_samantha.txt` aktualizován ve stejném kroku.


## 2026-11-05 00:53 CET — Převzetí Data a společný balíček

Hotovo: Will převzal oba Datovy commity do main po kontrole změn a jejich
slučitelnosti s e-mailovým proudem. Původní klient je modernizovaný; SDK
zůstává offline. Živý handshake a katalog potvrdily kompatibilní připojení.

Rozhodnutí: Míla před spaním výslovně zadal převzít Data, zkontrolovat a
provést p+n včetně oprav do čistého repozitáře. Systémová instalace nového
e-mailového LaunchAgentu dál vyžaduje přesnou globální větu.

Další krok: Dokončit společnou bránu a registrované p+n; konečný provozní
stav ověřit z přesné účtenky a živého auditu, nepředpokládat ho z indexu.

Navrhované další kroky: Potvrzená aktivace e-mailového agenta a první ostrý
cyklus; fyzická přejímka reconnectu. SDK proxy nebyla aktivována.

Technický důkaz: 192 cílených testů: 172 PASS, 20 volitelných SDK SKIP,
logs/data_email_integration_targeted_20261105.log; server 0.163.0 proti
lokální CLI 0.166.0. Plná integrační brána: 2462 testů, 2442 PASS, 20 SDK SKIP (377,0 s) v příslušném logu.


## 2026-11-05 08:55 CET — Potvrzené společné vydání a aktivace e-mailové služby

Hotovo: Předchozí společný balíček Data + instalátor b6375a33 je skutečně
vydaný; vzdálené CI úspěšné. E-mailový LaunchAgent byl po přesné globální
větě samostatně aktivován, první ostrý průchod i obnova ověřené. SDK se do
produkčního runtime nezavádí a přetrvávající session hub zůstává zachovaný.

Rozhodnutí: Míla přesnou větou schválil dříve připravený systémový krok.
Dále platí jeho noční pokyn dokončit záznamy a vydání do čistého repozitáře.

Další krok: Sledovat automatickou hodinovou kontrolu a běžné vyřizování karet.

Navrhované další kroky: Fyzická přejímka reconnectu; SDK proxy samostatně.

Technický důkaz: p+n 09e6c05f658a1ce16750dfd5cd15c514, push/deploy confirmed,
2462 testů (20 SDK skipů), smoke 5/5 a chráněné služby beze změny; CI
41938993126 success. E-mailová provozní přejímka: 6 zpráv, 3 důležité karty,
3 nedůležité v jednom řádku, 0 chyb, Pushcut API accepted=1; obnova bez
opakování posouzení. Viz kanonický continuous_personal_agent handoff.

### 2026-11-05 09:26 CET — Mobilní přejímka 05/P1-B a lokální oprava odesílání

Hotovo:
- Míla potvrdil nasazené 05/P1-B a úspěšný Mac test. iPhone viděl stejnou historii, ale opakovaně ztratil odeslaný dotaz bez práce či chyby; přejímka zůstává neuzavřená.
- Čtecí audit potvrdil soukromý HTTPS Serve do stejné instance. Aktivní serverový proud obsahoval pouze první dokončený přejímací dotaz; žádné nové odeslání se neprovádělo.
- Lokální UI připraví požadavek před vymazáním editoru, zachová text při chybě přípravy a zobrazí nejistý dotaz u editoru. Obecné selhání nepovolí opakování; stav uvolní jen přesná potvrzená účtenka.

Rozhodnutí:
- Žádná nová architektonická dohoda. SDK, session hub, runtime, modelové role a e-mailové moduly zůstávají v dosavadním režimu. Přesná chyba konkrétního iPhonu není prokázaná; syntetická reprodukce není fyzická přejímka.

Další krok:
- Předat ověřenou lokální opravu Willovi. Převzetí, push a nasazení nové opravy jsou samostatné; po nasazení načíst čerstvé UI a provést jediný neškodný retest na iPhonu.

Navrhované další kroky:
- Mobilní přejímku uzavřít až podle Mílova skutečného výsledku. Technický reconnect App Serveru a SDK pilot zůstávají samostatné.

Technický důkaz:
- Reprodukce FAIL→PASS nad skutečným JavaScriptem; 150 cílených testů PASS. Úplná Cockpit brána PASS: 2 374 testů, 0 chyb a selhání, 5 PDF skipů bez ReportLabu.
- Report reports/human_adam_iphone_send_failure_20261105.md. Bez nového modelového tahu, změny sdílených dat, restartu služby či automatického opakování.


## 2026-11-05 11:08 CET — Převzetí nové Datovy iPhone opravy po prvním p+n

Hotovo: Will zkontroloval a převzal zdrojový commit 5363238b. Konkrétní
reprodukovaná slabina vymazání textu před POST je ošetřená, nejistý dotaz
zůstane viditelný bez automatického opakování. V aktuálním main 250 cílených
PASS; konflikty společných paměťových souhrnů sloučené se zachováním historie.

Rozhodnutí: Míla výslovně zadal po mém dokončeném vydání samostatně vydat
Data. První balíček 3f3b5b25 má potvrzené p+n i CI, Data je druhý krok.

Další krok: Registrované druhé p+n přes centrální roli Terra a živé ověření
nasazeného zdroje; mobilní přejímku neprohlašovat za hotovou bez Míly.

Navrhované další kroky: Po čerstvém načtení UI jeden neškodný iPhone retest.

Technický důkaz: 250 PASS v data_iphone_integration_targeted_20261105.log,
bez placeného modelového tahu či POST send. Kanonický handoff a TVBCP
aktualizované společně; nový TVBCP nevzniká. E-mailový agent 167e629f je
aktivní; 11. hodina automaticky zpracovala dvě zprávy, oba providery OK.

### 2026-11-05 11:41 CET — iPhone přejímka bodu 2 po UI opravě PASS

Hotovo:
- Míla po úpravě potvrdil doručenou odpověď na iPhonu a správnou zkušební značku z předchozího tahu. Mac bod 1 i iPhone bod 2 jsou uživatelsky ověřené; původní selhání bodu 2 je po retestu uzavřené.
- Převzetí UI opravy do main je doložené commitem 6972ea5c (originál Data 5363238b).

Rozhodnutí:
- Žádná nová architektonická dohoda ani oprávnění k dalším akcím. Úspěšný dotaz sám nepotvrzuje obnovu během práce, nepřítomnost duplicit ani technický reconnect.

Další krok:
- Podle přejímacího postupu zkontrolovat návrat na Mac a jediné zobrazení zpráv (bod 3).

Navrhované další kroky:
- Samostatně ověřit obnovení stránky během rozpracované odpovědi (bod 4). Technický reconnect App Serveru a případný SDK pilot zůstávají oddělené.

Technický důkaz:
- Přímé uživatelské potvrzení výsledku po úpravě; žádný nový modelový tah ani nový runtime audit. Report reports/human_adam_iphone_send_failure_20261105.md.
- Jde o dokumentační zápis. Kód, služby, sdílená provozní data, push a nasazení se neměnily.

### 2026-11-05 11:58 CET — 05/P1-C: SDK proxy a přijetí bodu 3

Hotovo:
- Míla navazujícím „Funguje to!“ přijal bod 3 předchozího postupu; body 1–3 uživatelsky PASS. Bod 4 a skutečný technický reconnect zůstávají otevřené.
- Izolovaný pilot se skutečným SDK/CLI prokázal sdílení syntetického proudového socketu dvěma klienty, přežití posluchače po uzavření proxy a blokaci opakované akce po nejistotě. CLI proxy se současným WebSocket transportem nefunguje; současný transport proti téže fixture PASS.

Rozhodnutí:
- Nová architektonická dohoda nevznikla. Doporučení Data je ponechat modernizovaný původní klient; SDK se neadoptovalo.

Další krok:
- Předat Willovi lokální testy a závěry C; integrace se v této větvi neprovádí.

Navrhované další kroky:
- Dokončit bod 4 s Mílou a samostatně autorizovaný read-only reconnect současného transportu bez turn/start, náhradního vlákna či restartu.
- SDK migraci otevřít jen po konkrétním přínosu a samostatném rozhodnutí; vyžaduje skutečný WebSocket adaptér a zachování trvalého journalu.

Technický důkaz:
- 105 cílených testů PASS, včetně 12 nových; statická brána a pip check PASS. Report reports/codex_sdk_p1c_20261105.md a kontrolní environment JSON.
- Jen syntetické fixture, nula placených modelových tahů. Produkční klient/runtime/UI/e-mail, role, requirements a sdílená data beze změn; bez živého auditu, restartu, integrace, push a nasazení.


## Provozní předání — 2026-11-05 22:06 CET, Datův čtecí hlas v Cockpitu

### Hotovo
- Datova větev a5e401e6 je pravidelným merge zachovaná v main 11b4ce64; vlastní Datův worktree zůstává čistý na původním headu. Novější e-mail, Ateliér a původní App Server klient zůstaly zachované. 05/P1 je uzavřená 17/17; SDK neadoptované.
- Terra p+n kompatibilního kódu dokončeno: účtenka 6e9bbb2a6f7dbcd6f9e3f11cc2b88909, push/deploy confirmed, plná brána 2668 testů / 0 chyb / 31 SKIP, smoke 5/5 a protected_services_unchanged=true. Předtím 239 integračních kontrol PASS.
- Vlastní hodinový e-mailový LaunchAgent registrovaně upgradovaný 2fe0481e → 11b4ce64. Installed/owned/loaded/enabled; úplný business otisk, nastavení a Email politika před/po shodné, stará kopie i záloha zachované. První check already_completed, bez nového modelového posouzení či oznámení.
- Teprve po skutečném ověření instalovaného parseru přidaná přesná schválená read_only_voice role z Datova a5e401e6. GPT-Live 1 bez reasoning_effort, všechny předchozí bindingy nezměněné. 141 následných cílených kontrol PASS.
- Živé neplacené GET panelu HTTP 200: připravený existující proud, mikrofon vypnutý, cenový souhlas přítomný a žádná změna trvalých voice účtenek. Ateliér dál hlásí enabled/image_generation=true.

### Rozhodnutí
- Míla autorizoval samostatné Terra p+n Datova vedlejšího proudu i úklid. Závěrečný konfigurační checkpoint obsahuje jen schválenou hlasovou roli a provozní zápisy; konečný stav jeho p+n určuje účtenka logs/data_voice_role_release_20261105.log. Potvrzené vydání vyžaduje completed + push/deploy confirmed stejného headu.
- Žádný další placený hlasový start, mikrofon, mazání/reset, force push ani restart sdíleného App Serveru. Původní 47s probe je spotřebovaný; nikdy jej neopakovat.

### Další krok a otevřená přejímka
- Po návratu Míly praktický poslech a zvlášť cenově potvrzený rozhovor do 60 s. Mikrofon, iPhone/WebRTC, přerušování a subjektivní latence zůstávají otevřené; celý bod 15 tím není uzavřený. Hlas čte jen hrubý stav a neschvaluje ani nemění úlohy.
- Technický důkaz: logs/data_voice_code_release_20261105.log, data_voice_email_compat_upgrade_20261105.log, data_voice_role_activation_20261105.log, data_voice_role_targeted_20261105.log, data_voice_live_precommit_20261105.log. Závěrečný provozní audit: logs/data_voice_final_verified_20261105.log; GitHub CI obou přesných headů v data_voice_code_ci_20261105.log a data_voice_role_ci_20261105.log. Žádný nový TVBCP.

### Historický Datův lokální další krok před tehdejší integrací
Will převezme kód do aktuálního main a zachová své e-mailové změny i role;
nejdříve samostatně povolené nasazení kompatibilního parseru, pak hlasová role.

### Navrhované další kroky
Po nasazení neplacená kontrola panelu, poté Mílův zvlášť potvrzený iPhone
rozhovor do 60 s s kontrolou úlohy, vlákna, Stop a finální serverové spotřeby.

### Technický důkaz
120 cílených testů PASS, z toho 19 nových integračních kontraktů; statická
brána PASS, plná brána 2467 testů OK (skipped=5). Report voice_conversation_cockpit_20261105.md.
Žádná nová placená relace, mikrofon ani změna živých služeb/provozních dat.

## 2026-11-06 23:13 CET — 15/P2-E: iPhone blokuje hlas před mikrofonem

### Hotovo
Obecná hláška byla rozdělena na nezabezpečenou stránku, chybějící mikrofonní
API a chybějící WebRTC. Při HTTP vysvětluje nutnost privátní HTTPS adresy a to,
že Tailscale ani localhost jiného zařízení nenahradí secure context.

### Rozhodnutí
Míla hlásí nasazení, ale přejímka na iPhonu v Chromu selhala před žádostí
o mikrofon a vytvořením relace. Konkrétní HTTP/HTTPS zatím neověřené; nelze
označit Chrome za nepodporovaný. HTTPS kontrola se neobchází, síť se nemění.

### Další krok
Ověřit protokol adresy na iPhonu; při HTTP otevřít skutečný privátní HTTPS
vstup Cockpitu, případně připravit jeho samostatnou provozní konfiguraci.

### Navrhované další kroky
Po odstranění browserové blokace samostatná krátká hlasová přejímka a finální
serverová spotřeba. Nejasný placený požadavek neopakovat.

### Technický důkaz
77 cílených testů PASS (pilot, Cockpit adaptér, gateway a Node browserové
scénáře). Statická brána PASS. Žádný mikrofon, placený start,
restart, push nebo nasazení Datou. Síťová ani modelová konfigurace beze změny.

## 2026-11-06 23:24 CET — 15/P2-F: čekání na oprávnění mikrofonu

### Hotovo
Panel vysvětlí povolení mikrofonu a dosavadní timeout odliší od chyby spojení.
Zamítnutí, chybějící nebo nedostupný mikrofon mají vlastní bezpečné instrukce.

### Rozhodnutí
Míla se přes HTTPS dostal ke Start a hlásí čekání na mikrofon. To je před
placeným create, příčina na telefonu zůstává neověřená. Nastavení telefonu,
serverový backend, role a provozní síť se nemění; žádný automatický retry.

### Další krok
Nejprve ukončit původní čekání, pak ověřit oprávnění pro Chrome a konkrétní
HTTPS stránku. Teprve poté jeden nový ruční Start s cenovým souhlasem.

### Navrhované další kroky
Po získání mikrofonu pokračovat přejímkou hlasu, Stop a finální spotřeby.

### Technický důkaz
77 testů PASS včetně čekajícího/nepovoleného mikrofonu a opožděného povolení
po timeoutu bez create. Statická brána PASS; žádné placené volání ani nasazení.

## 2026-11-06 23:30 CET — 15/P2-G: časovač zablokoval žádost o mikrofon

### Hotovo
Opravená výchozí vazba setTimeout i clearTimeout na globální browserový objekt.
Nový kontrakt reprodukuje chybné this, které starší fake časovač nepodchytil.

### Rozhodnutí
Stejné chování Chromu/Safari nepřipisovat bez důkazu nastavení telefonu.
Čtecí audit potvrzuje původní nasazený controller. Výchozí timer může skončit
výjimkou ještě před getUserMedia; synteticky reprodukováno. Fyzický iPhone
stále není přijatý. Žádné obcházení oprávnění nebo automatický placený retry.

### Další krok
Will převezme E/F/G v pořadí, po samostatně povoleném nasazení ověří nový
asset a s Mílou jednou zkusí žádost o mikrofon přes HTTPS.

### Navrhované další kroky
Po získání mikrofonu ověřit rozhovor, Stop, zachování úlohy a finální usage.

### Technický důkaz
77 testů PASS. Před opravou receiver kontrakt: TypeError, 0 mic calls,
state connecting; po opravě bez výjimky, 1 mic call a čistý disconnected při
syntetickém zamítnutí, 0 paid calls. Statická brána PASS. Bez push či deploy.

## Provozní předání — 2026-11-07 00:18 CET, společná integrace Willa a Daty

### Hotovo
- Do novějšího main s Willovým čtecím EventKit pilotem c0963d6b jsou převzaté
  Datovy commity 4bf110fd, 73fdc08e a 975f0900. Browserové assety a Node kontrakt
  jsou byteově shodné s Datovým 975f0900; jeho vlastní worktree se nemění.
- Hlasový panel rozlišuje HTTP/API/WebRTC, bezpečně vysvětluje čekání a chyby
  mikrofonu a opravuje receiver výchozích setTimeout/clearTimeout přes globalThis.
- E-mailová zdvořilostní politika, Ateliér, modelové role a samostatná hodinová
  služba zůstávají zachované. Kalendářový pilot je nadále pouze čtecí.

### Rozhodnutí
- Míla výslovně autorizoval převzetí a Terra p+n Willových i Datových commitů.
  Společné vydání přes registrované submit_release(wait=True), připnuté k Terře
  a výslednému schválenému merge headu; bez dalšího mikrofonu či placeného probe.
- Původní 47s hlasový probe je spotřebovaný a neopakuje se. Žádný restart
  sdíleného App Serveru, změna sítí nebo update vlastní e-mailové kopie.

### Další krok
Dokončit registrované společné p+n; autoritou jsou přesná účtenka a následné
živé ověření v logs/calendar_voice_release_20261107.log a
calendar_voice_verified_20261107.log. Potom Mílův samostatný iPhone Start a
poslech; fyzická přejímka mikrofonu/WebRTC/ceny se tímto kódem nepředstírá.

### Navrhované další kroky
Kalendářový bod 2 (výběr kalendářů a čtecí přehled) až jako další vývojový krok.

### Technický důkaz
Node browserový kontrakt a 114 cílených testů PASS, statická brána PASS dle
logs/calendar_voice_integration_targeted_20261107.log a
calendar_voice_integration_static_20261107.log. Plnou publikační bránu provede
vykonavatel. Soukromá data, žádosti o oprávnění a původní e-mail nepatří do Gitu.

## 2026-11-07 08:55 CET — zrušení placeného hlasového rozhovoru

### Hotovo
Připravený přesný návrh vyřazení celého placeného pilotu 15/P2 včetně
frontendového panelu, brokeru/probe, role, API, capability a vlastních testů.

### Rozhodnutí
Míla projekt kompletně ruší: „není pro Agenta SDK Samantha relevantní“.
Starší kroky A–G jsou historické, nejsou pokynem pokračovat nebo je nasadit.

### Další krok
Po přesném potvrzení globální brzdy odstranit vymezené soubory a projít
skutečné cílené testy i plnou bránu. Zatím jde o ověřený návrh, ne hotové smazání.

### Navrhované další kroky
Později samostatně autorizované převzetí/nasazení odstranění do aktuálního
main; zachovat jeho novější role a Willovu práci. Bez další hlasové přejímky.

### Technický důkaz
14 verzovaných souborů a 10 generovaných souborů vymezených manifestem;
8 návazných souborů v návrhu upravených. 26 overlay testů a statické kontroly
návrhu PASS. Žádná změna živého runtime, placený start nebo mazání zdrojů.

## 2026-11-07 09:22 CET — placený hlasový rozhovor odstraněn po potvrzení

### Hotovo
Placený panel, jeho API, broker/probe, role a vlastní testy jsou odstraněné.
Odstraněno přesně 14 verzovaných a 10 generovaných souborů, prázdný adresář
panelu a osm navazujících úprav. Ostatní hlasové funkce a Camino zachované.

### Rozhodnutí
Placený hlasový rozhovor není pro Agenta SDK Samantha relevantní. Míla zrušil
projekt bez náhrady a přesnou globální brzdu pro tento rozsah potvrdil.
Historické A–G nejsou pokynem k pokračování, adopci nebo vydání.

### Další krok
Will převezme pouze rušící commit do aktuálního main se zachováním novějších
rolí a e-mailové práce; publikování/nasazení podléhá samostatnému oprávnění.

### Navrhované další kroky
Po povoleném nasazení neplaceně ověřit nedostupnost panelu/API a zachování
běžného Human–Adam, nahrávání pokynů a předčítání. Žádný další placený probe.

### Technický důkaz
113 cílených testů PASS, plná brána 2377 testů za 429,882 s OK (skipped=5).
Importy pěti modulů nedostupné; 5/5 bývalých GET/POST cest v Handler testu
vrací 404 bez akčního payloadu. Whitelist mazání shodný, App Server, lokální
runtime, e-mail, Camino a původní JSON důkazu P2-C beze změny. Bez push/deploy.

## 2026-11-07 — Will: společný balíček kalendáře 3 a zrušení hlasového pilotu

Míla výslovně schválil p+n včetně Datova rušícího `b4b72ab0`. Will jej
začlenil nad kalendářový `afb7c9cf`; starší hlasové opravy se samostatně
nenasazují. Bod 15/P2 je definitivně ukončen, historické přejímky E/F/G
ani iPhone Start již nejsou dalšími kroky. Data má dál vlastní worktree.

Při řešení konfliktů zůstaly všechny kalendářové a Ateliérové cesty i pět
ostatních rolí; odstraněná je pouze role read_only_voice a zapojení placeného
pilota. Na main se přebírá přesných 14 verzovaných odstranění; Datových deset
generovaných souborů se týkalo jen jeho worktree. Soukromé důkazy a audio se
nemažou. Běžné předčítání, nahrávání pokynů a audio Camina zůstávají zachované.
203 integračních testů PASS; po opravě zastaralého testu zakázané hlasové role
samostatně 10/10 PASS. Rychlá statická a plná publikační brána jsou podmínkou
vydání. Kalendářový vývoj před integrací: 2726 testů OK, 31 SKIP; jedno
syntetické živé modelové ověření PASS. Skutečný e-mail ani kalendář se neměnil.

P+n provede jediný registrovaný vykonavatel Terra pro project-email-cases
(společný Cockpit). Tento zápis vzniká před publikací; konečný provozní stav
určuje přesná účtenka a logs/calendar_draft_retirement_release_20261107.log,
čerstvé ověření logs/calendar_draft_retirement_verified_20261107.log.
Po dokončení ověřit 404 bývalého panelu/API, nové e-mailové UI a běžné audio.
Fyzická Mac/iPhone přejímka nového kalendářového editoru a oprávnění aktuálního
EventKit buildu zůstávají oddělené; bod 3 nevytváří kalendářové události.

### 2026-11-11 19:19 CET — čtení souborů a kompatibilita nástrojů Human–Adama

Hotovo: Zjištěna skutečná chyba nástrojového IPC místo předpokládaného zákazu
složky. Připravené přímé nástroje pro běžný profil, Knihovnu i lazy proudy.
V aktuálním nečinném vlákně infrastruktury server přijal oba přepínače;
bezplatný command/exec ověřil čtení, původní nastavení i session JSON shodné.

Rozhodnutí: Opravit nástroje uvnitř Human–Adama. Zachovat izolovaný vývoj,
DEVELOPMENT_CONTROL, sandbox i společný server. Instalace/restart, změna modelu,
rozšíření oprávnění ani opakování původního placeného požadavku nejsou součástí.
Míla následně výslovně schválil Terra p+n této hotové opravy.

Další krok: Vytvořit lokální commit a předat Terře schválené
p+n přes registrovaný submit_release(wait=True). Přesná účtenka jobu
444fe9352557c64a4082aed426d9dd0c a release_verification.json v soukromé složce
jsou autoritou vydání; tento zdrojový zápis úspěch vydání nepředjímá.

Navrhované další kroky: Po schváleném vydání ověřit čtení i po reconnectu.

Technický důkaz: 89 cílených testů PASS; plná brána 3485 testů OK (31 SKIP). Lifecycle testy
pokrývají zachování historie, nulový replay při reconnectu/rotaci, kopírování
konfigurace a nezměněný sandbox. Soukromá účtenka a gate log jsou v
`data/private/human_adam_tool_compat_20261111/`. Nula modelových tahů, žádný
dosavadní push/deploy této opravy, změna globální konfigurace ani zásah do Data. Modelová přejímka
přímých nástrojů zůstává otevřená; RPC čtení samo ji nenahrazuje.



## 2026-11-12 08:32 CET — Spolehlivý start závislosti hodinové pošty

**Hotovo:** Lokální oprava obnoví chybějící sdílený App Server před plánovanou kontrolou pošty i bez otevření Human–Adama. Souběžné starty používají jeden souborový zámek a jeden server.

**Rozhodnutí:** Spouštění patří do ověřeného modelového výběru již aktivované služby, až po kontrole role a platnosti běhu. Zachováváme stávající Unix socket, model, hodinový režim, limity, business stav a idempotenci. Cizí/neodpovídající socket se automaticky neodstraňuje ani server nerestartuje.

**Další krok:** Provést Mílou výslovně schválené p+n; vlastní hodinovou kopii přepnout až přesným upgradem po globální větě. Systémový plist bez ní neměnit.

**Navrhované další kroky:** Po upgradu ověřit přirozený hodinový běh a následně skutečný reboot/wake bez otevření chatu.

**Technický důkaz:** 166 cílených testů PASS; plná brána3520 testů OK /31 SKIP (585,445s). Skutečný izolovaný CLI bootstrap/reuse/catalog bez vlákna a modelového tahu. Dnešní registrovaný resume zachoval otisk business stavu, nastavení i roli a obnovil socket; instalovaná kopie zůstává8c83e93b. Dnešní přirozený slot08:00 completed v08:32:01 CET,4 nové zprávy. Report reports/email_runtime_boot_20261112.md rozlišuje místní důkaz, provozní obnovu a dosud neprovedený servisní upgrade.

Předání p+n: request `email-runtime-boot-20261112-v1`, job `cfc1c1b1375eb5c46143c98eed93bc38`; konečný výsledek ověřit z původní účtenky a `logs/email_runtime_boot_release_20261112.json`, nikoli z tohoto předávacího snapshotu.

### 2026-11-12 08:37 CET — HA-01: společná čtecí projekce stavu

Hotovo: Human–Adam má místní přídavný stavový kontrakt pro budoucí přehledné UI. Spojení, probíhající model, navazující kontrola, publikace a starší incidenty mají vlastní význam a rozsah. Starý nebo cizí doklad se nevydává za aktuální tah.

Rozhodnutí: Míla zadal HA-01 podle plánu z 11.11. Používá se nová čistá Python projekce nad existujícími zdroji, bez jejich nahrazení a bez nových mutací. ID jsou stabilní čtecí reference, revision je obsahový otisk, nikoli pořadový event cursor. Vlastníci provedení a doménové účtenky zůstávají autoritou.

Další krok: Po dokončení HA-01 navázat HA-02 — přehlednější rozhraní nad společnou projekcí.

Navrhované další kroky: HA-03 ažHA-05 pro skutečné události, serverově vlastněnou práci a živou kartu; poté doplnění/zastavení. Žádné p+n nebylo zadáno.

Technický důkaz: 29 nových HA-01 testů OK / 2,411 s. Závěrečná plná brána 3543 testů OK / 620,369 s, 5 SKIP; statické a syntaktické kontroly OK. Ověřené nezměněné bajty/mtime zdrojů, korelace a pozdní snímky, přesný head/target/smoke při dodatečném důkazu. Main a služby nedotčené. Report human_adam_ha01_work_state_20261112.txt.

## 2026-11-12 09:14 CET — Oprava nasazená i do vlastní hodinové služby

**Hotovo:** Hlídač nové pošty má ve vlastní běžící instalaci opravu automatického startu chybějícího sdíleného serveru. P+n nasadilo7f47a41f do Cockpitu; po přesné globální větě registrovaný upgrade přepnul také vlastní hodinovou kopii8c83e93b→7f47a41f.

**Rozhodnutí:** Míla výslovně schválil p+n a následně dodal přesnou větu pro připravený servisní upgrade. Model, hodinový režim, business stav a nastavení zůstávají stejné. Žádný nový testovací modelový tah, e-mailové odeslání ani kalendářový zápis.

**Další krok:** Běžný hodinový provoz; při příštím skutečném reboot/wake ověřit samostatné obnovení bez otevření chatu.

**Navrhované další kroky:** Pokračovat původní samostatnou etapou UI hlídání záležitostí; její automatický monitor se tímto neaktivoval.

**Technický důkaz:** P+n cfc1c1b1375eb5c46143c98eed93bc38 completed,25 commitů, publikační brána3520 PASS/642,8s, smoke5/5, code stamp bfe18afa86e45de4, chráněné služby při vydání shodné. Následný upgrade installed/owned/loaded/enabled, první check09:12:45 CET already_completed/0. Úplný business digest, všechny dosavadní položky, hodnoty nastavení a celý JSON rolí shodné.311 instalovaných souborů přesně podle manifestu; izolovaný test nové instalace skutečně spustil a znovu použil stejný server bez thread/start nebo turn/start. Report reports/email_runtime_boot_20261112.md; důkazy upgrade_result.json a installed_verification.json jen ve jmenované private složce. Fyzický reboot/wake po aktivaci nebyl proveden.

Doplňující ověření: start a převzetí stejného App Serveru prošly také v přesném
PATH a omezeném prostředí nainstalovaného LaunchAgentu. Instalovaná Terra/high,
0 thread/start a turn/start, produkční socket beze změny; důkaz
service_environment_verification.json ve stejné soukromé složce.

### 2026-11-12 09:36 CET — HA-02: čitelný chat a tři pohledy Práce

Stav: Lokálně implementováno na data/parallel-20261104 nad HA-01 5d9c1497; bez integrace, push nebo nasazení. Celková brána 3544 testů OK / 584,986 s, 5 SKIP; finální prezentační úpravy ověřené cíleně a v prohlížeči, statická brána OK.

Rozhodnutí: Míla zadal HA-02 podle auditního plánu. Společná projekce HA-01 je zdrojem aktuálního souhrnu; Práce odděluje probíhání, výsledky/publikaci a servis. Dosavadní mutační brány zůstaly. Nový stream, worker, App Server protokol, steer/interrupt a účtování celé úlohy se neimplementují v tomto kroku.

Další krok: Posoudit balíček HA-01/02 a fyzickou přejímku až po samostatném vydání; případně HA-03 na další zadání.

Rizika: Browser QA je syntetické a neprokazuje iPhone/Safari, reálnou klávesnici nebo živou relaci. UI používá dnešní snímky a dosavadní obnovu, ne nový event cursor. Omezený Markdown není úplný renderer.

Technický důkaz: 271 cílených testů OK / 9,976 s; 200 browser PASS na skutečných viewports 390x844, 430x932, 1280x900, 390x480 a 430x500. Vizuálně zkontrolované snímky hlavního okna i pohledů Práce. Čtecí generace/scopes, bezpečné odkazy, zachování DOM/fokusu/předčítání/scrollu, celý sbalený text a nulový POST v browser fixture. Rozpracované běhy ukončené před posledními opravami odolnosti; celková brána 3544 testů OK / 584,986 s, 5 SKIP. Následné prezentační úpravy návratu fokusu z Další a neověřených os zdrojů ověřené finální cílenou sadou (271 / 9,976 s), browser QA (200) a statickou bránou. Důkazy logs/ha02_*.log a data/private/ha02_ui_qa_20261112/. Report human_adam_ha02_ui_20261112.txt.

### 2026-11-12 10:36 CET — HA-03: oddělené RPC a události App Serveru

Stav: Lokálně implementováno na data/parallel-20261104 nad HA-02 7b77aba2. Finální cílená sada 287 testů OK / 4,783 s; statická brána OK. Plná regresní brána: 3587 testů OK / 532,005 s, 5 SKIP. Bez integrace, push, nasazení, skutečného App Server spojení či placeného pokusu.

Rozhodnutí: Míla zadal HA-03 podle plánu z 11.11. Jeden wire reader předává data bounded dispatcheru: RPC má vlastní slot podle ID, odběry samostatné fronty a scope/generation. Konkrétní validátory, explicitní kompatibilní plan/usage varianty, přesné vazby a close všech čekajících operací. Dosavadní receive guard zůstává v cestě včetně item/started a neznámých item payloadů. Chybné usage zneplatní staré měření, ne jinak potvrzené doručení. Read-only protocol diagnostika je mimo perzistentní session; sama nepřipojuje runtime ani neověřuje živou podporu features.

Další krok: HA-04 — trvalá serverová identita dlouhé práce, snímek/historie/cursor a obnova po reloadu, až na další zadání. UI živé karty je HA-05. Samostatně posoudit integraci/vydání balíčku a následnou živou Mac/iPhone přejímku.

Rizika: Testy jsou syntetické a nepřipojily skutečný sdílený App Server; historický 05/P1 není nové živé ověření změněného klienta. Validation pokrývá spotřebované core fields, nikoli všechna pole schématu. Již běžící callback nelze násilně zastavit; pozdější použití jeho výsledku musí ověřit generation. sequence je pořadí publikace a received_sequence původní wire pořadí, nikoli trvalý cursor. Nové odběry zatím nejsou napojené do živé UI karty. Main, služby, role a mutační oprávnění zachované.

Technický důkaz: Širší průběžná sada 475 testů OK / 62,471 s; finální jádro 287 OK / 4,783 s. Testy skutečného klienta nad vlastním Unix WebSocket listenerem a stdio Python fixture: RPC/event souběhy, plan před ACK, thread-only usage, cizí/stará generace, count/byte/callback limity, výpadek před/po ACK bez replay, jeden přijatý user item/start/final, CanonicalSessionHub delivery_unknown a ScienceNews guard. Offline CLI 0.167.0/schema; původní minimum serveru 0.163.0. Report human_adam_ha03_dispatcher_20261112.txt, logy ha03_* a ignorované otisky zdrojů; žádné soukromé payloady v Git-safe zápisu.


## 2026-11-12 10:55 CET — Will přebírá HA-01 až HA-03 do společného vydání

**Hotovo:** Lokálně převzaté Datovy tři hotové commity5d9c1497,7b77aba2 a045936f9
nad e-mailové UI aae687fb. Kód se spojil bez konfliktů; paměť zachovává obě
historie v časovém pořadí. Oprava startu pošty, její zámek i modelové role
jsou přesně zachované. Jedinou integrační úpravou je přenositelnost diagnostické
asertace hlubokého neobjektového JSON mezi Python3.11/3.12; obě cesty stále
odmítnou rámec, uzavřou spojení a probudí čekající RPC. Produkční dispatcher
zůstává Datovou verzí.

**Rozhodnutí:** Míla výslovně zadal společné p+n všech hotových Willových i
Datových commitů. Balíček zahrne také odložený hotový Ateliér4ea5b01e. Jediné
registrované vydání má request `combined-finished-work-20261112-v1`, job `4242cf7f5bdb6b88724e635cde31b443`,
project-email-cases→společný Cockpit. Vykonavatele určí centrální Terra role.
Nejde o aktivaci dalších služeb ani placený vývojový/modelový pilot.

**Další krok:** Převzít Ateliér, dokončit celkovou bránu a zmrazit přesný
commit pro jediné registrované p+n.

**Navrhované další kroky:** Po vydání fyzická přejímka Human–Adam na Macu/iPhonu;
HA-04 až po samostatném zadání. E-mailový automatický monitor zůstává další etapa.

**Technický důkaz:**201 cílených testů PASS, samostatný test také v Datově
Python3.11 PASS. Skutečný nový klient přes stávající Unix WebSocket: initialize
amodel/list,10 modelů, CLI/server0.167.0, žádný thread/start ani turn/start;
uzavřené jen vlastní spojení, sdílený socket zachovaný. Toto není důkaz
modelového tahu, reconnectu dlouhé práce ani fyzické přejímky. Plná brána
poběží nad finálním společným balíčkem; meziběh před rozšířením na Ateliér
se nevydává za úspěšnou závěrečnou kontrolu. Soukromé důkazy
`data/private/combined_release_20261112/`.


## 2026-11-12 10:58 CET — Finální společný balíček pro jedno Terra p+n

**Hotovo:** Funkčně nové ruční e-mailové UI aae687fb a Datovy HA-01/02/03
5d9c1497,7b77aba2,045936f9 jsou společně na main. Zbývající staré větve
jsou propojené pouze historicky: půdorys4ea5b01e má přesně stejný stable
patch-id jako již převzatý58a18e68 (c13a5067bd2855a44a068dc7e249c8981335f2d8).
Současné názvy návrhů, bezpečnostní úpravy a ostatní novější kód Ateliéru
zůstávají zachované. Přípravné commity8f64dca7/9d89446b mají dokončenou
náhradu v aae687fb: všechny kontrakty přešly do kanonického UI, které navíc
nemá nepotvrzený automatický výchozí termín. Historické propojení nepřenáší
žádný starší zdroj ani nepřepisuje dnešní implementaci.

**Rozhodnutí:** Výslovné Mílovo p+n všech hotových commitů se provede jednou
registrovaným submit_release(wait=True), v aktuálním project-email-cases,
společný cíl Cockpit Samanthy. Request combined-finished-work-20261112-v1,
job4242cf7f5bdb6b88724e635cde31b443. Schválený head se doplní až po finálním
lokálním merge commitu a zarovnání čistých profilů. Žádná změna modelové
politiky, automatického monitoru, systémové služby nebo placený vývojový pilot.

**Další krok:** Dokončit finální celkovou bránu, lokální checkpoint a jediné
p+n; výsledek jednou ověřit z původní účtenky a živého HTTP.

**Navrhované další kroky:** Lidská Mac/iPhone přejímka; e-mailová etapa3 a
Human–Adam HA-04 až jako další vývoj. Samostatný e-mailový TVBCP zůstává
nedohodnutý; aktualizují se existující správné handoffy a Cockpit/Layer TVBCP.

**Technický důkaz:**201 integračních testů PASS; zvlášť shodná bezpečnostní
regrese v Python3.11 PASS. Nový dispatcher ověřen skutečným initialize a
model/list na sdíleném serveru0.167.0 bez nového thread/start/turn/start.
Historické merge ponechávají app/scripts/tests bytewise stejné proti8d05aac2.
Finální plná lokální brána PASS: 3602 testů,31 SKIP, 507.039 s.
Výsledková autorita: reports/combined_finished_work_release_20261112.md a
původní privátní job/receipt. Zápis vzniká před publikací, není účtenkou
nasazení. Při nejistotě se původní job dohledá, nepodává se nový požadavek.


## 2026-11-12 12:07 CET — HA-04: trvalé serverové přijetí a návrat ke stejné práci

**Hotovo:** Backend ukládá přijetí a stejnou identitu práce před samostatným
prováděním. Nový start vrací rychle202, staré send zachovává čekající odpověď.
Práci lze dohledat i po ztraceném HTTP spojení; opakování stejného požadavku
nezakládá druhý modelový tah. Snímek a omezené události mají cursor/resync.
Po pádu backendu se obnovuje pouze původní důkaz, nikoli provedení.

**Rozhodnutí:** Míla výslovně zadal HA-04 a následně rovnou p+n. Kritickou
implementaci provedl Adam přímo. Původní oprávnění/dokončovací kód zůstávají
autoritou; model/hodnoty role se nemění. Ukládá se pouze již přijaté zadání
v private server cache, žádné nové browserové drafty. Živá karta je HA-05.

**Další krok:** Dokončit plnou lokální kontrolu, jeden commit a jediné Terra
p+n podle registrovaného postupu. Původní request/job viz report.

**Navrhované další kroky:** HA-05 — propojit živou kartu a automatické čtecí
sledování s tímto backendem. Pak skutečný omezený modelový pilot a fyzická
Mac/iPhone přejímka, až ve vlastním schváleném rozsahu.

**Technický důkaz:**325 cílených PASS: identity/fingerprint, dvojklik/dva klienti,
čtení/reload, cursor/gap/retence, generační a terminální ochrana, poškozený
zdroj, selhání zápisu/startu workeru, wake při shutdown, skutečný syntetický
process crash a legacy HTTP disconnect; RPC probe jen fake. Původní tělo
ProfileManager.send je po extrakci AST-shodné, včetně oprávnění/dokončení.
Pevná child-job vazba odmítne pozdější cizí doklad bez falešného Hotovo.
Finální plná lokální brána PASS: 3635 testů / 573,186 s, 31 SKIP; finální zdroj včetně child-job ochrany a oprav registrů.
Důkazy `data/private/ha04_20261112/`, bezpečný report
`reports/human_adam_ha04_server_work_20261112.md`. Bez skutečného modelového
tahu HA-04, živé UI přejímky nebo aktualizace vlastní hodinové poštovní kopie.

### 2026-11-12 12:29 CET — HA-05: živá karta a automatické čtecí sledování

Hotovo: Human–Adam lokálně zobrazuje aktuální práci v hlavičce a živý plán, veřejné komentáře, doloženou aktivitu a časy pod Práce / Probíhá. Čtecí sledování s cursorem obnoví stejnou práci po načtení, vypořádá gap/resync a zastaví se na konci. Editor, fokus/selection, starší chat i řeč zůstávají stabilní. Ztracené přijetí řeší pouze GET původní identity, nikoli další odeslání.

Rozhodnutí: Míla zadal HA-04 Willovi a Data pokračuje HA-05. Po stabilním 72e1015c byl jen Datův checkout fast-forwardován na HA-04, vlastní změny bezpečně uchované a vrácené. Veřejný filtr je nyní napojený za dosavadní thread/turn/owner/generation guard; důkaz doručení ani jednorázové oprávnění se nemění. Nové rozhraní nepřijímá raw reasoning ani tool args. Willovy soubory, procesy a jeho samostatné vydání nejsou měněné.

Další krok: HA-06 — doplnění pokynu do přesné práce na další zadání.

Navrhované další kroky: Případné vydání HA-05 a fyzickou Mac/iPhone/živou modelovou přejímku samostatně schválit. Pozdější HA-07/08 jsou zastavení a spotřeba celého průchodu; nejsou předstíranou součástí tohoto kroku.

Technický důkaz: 417 cílených testů OK / 17,214 s. Skutečný HA-04 public producer, observer a wire dispatcher ověřily plán před ACK, cizí turn/generaci, commentary-only a nezměněné doručení; retence kompaktního veřejného obsahu zachová trvalý ID soubor a idempotenci. 18 Node scénářů, 11 veřejných testů, 140 skutečných browser kontrol na pěti velikostech; ustálené popředí 723–733 ms ve fixtures, aktivní mobilní/desktop karta vizuálně zkontrolovaná. Plná brána 3648 testů OK / 534,548 s, 5 SKIP. Report human_adam_ha05_live_ui_20261112.txt. První plný UI běh ukončen při přijetí HA-04; závěrečná brána ověřuje celou spojenou verzi. Žádný skutečný App Server/model/služba ani p+n.

Doplnění ověření téhož kroku: po plné bráně už jen frontendová preflight blokace odeslání před připojením; 417 cílených / 17,214 s a finální statická brána OK, finální browser QA zopakované. Backend/payload/persistence proti plné bráně nezměněné.
