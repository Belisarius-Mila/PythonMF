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

Co neni hotove:
- Novy checkpoint backend stale neni napojeny na existujici checkpointove
  tlacitko. Vyber proudu je napojeny, ale zatim neni nasazeny.
- Stary WIP/semafor/takeover tok zustava beze zmeny aktivniho runtime.
- Faze 1.4 je pripravena pro tento checkpoint a push; nasazeni a rucni UI
  roundtrip nasleduji az nad timto presnym commitem.
- Stary runtime nazev se zatim nesmi prejmenovat, protoze jej pouziva soucasna
  profilova konfigurace Cockpitu.

Dalsi krok:
Po tomto checkpointu a pushi fazi 1.4 nasadit, rizene restartovat Cockpit a
rucne overit Human–Adam -> Knihovna -> Human–Adam pres stejne menu.

Navrhovane dalsi kroky:
- Pro dalsi proud nejdrive v terminalu zaregistrovat konkretni `Project`, `Tool`,
  `Layer` nebo `Misc`; nevymyslet vazbu pri kliknuti v r-Adamovi.
- Po rucnim overeni teprve rozhodnout o fazi automatickeho dokončeni vyvojoveho
  kroku; stary profilovy fallback zatim ponechat jako vratny most.
- Zachovat UI a zakladni funkce po celou dobu postupne transformace.

Zmenene nebo relevantni soubory:
- `memory/WORKSTREAMS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`
- `memory/ACTIVE_PROJECTS.md`
- `app/communication/human_adam_profiles.py`
- `app/communication/simple_main_checkpoint.py`
- `app/communication/human_adam_workspace.py`
- `tests/test_simple_main_checkpoint.py`
- `scripts/cockpit_quality_gate.py`

Bezpecnost / neukladat:
- Neukladat soukrome identifikatory vlaken, tokeny ani private obsah.
- Nemenit stary runtime nazev bez samostatne overene migrace.
- Tento checkpoint neaktivuje novy backend v API/UI a neautorizuje nasazeni.
