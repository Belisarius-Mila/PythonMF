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
