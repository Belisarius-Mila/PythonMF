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
