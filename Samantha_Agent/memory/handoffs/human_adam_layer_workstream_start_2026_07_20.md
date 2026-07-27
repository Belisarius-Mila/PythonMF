<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-07-27 22:05 CEST

### Hotovo
- Přidána potvrzovaná bezeztrátová migrace starého private TVBCP do soukromého kontextu proudu Brainstorm včetně bezpečných instrukcí a testů.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Nasadit aktuální main; samotnou private migraci spustit až samostatnou přesnou potvrzovací větou.

### Rozhodnutí
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

### Navrhované další kroky
- Žádné další návrhy nad rámec bezprostředního kroku.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `9976bd01b51a`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `9976bd01b51a` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-07-27T19:28:59+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
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
