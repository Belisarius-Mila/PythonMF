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
- Oba profilove workspaces cekaji na beznou synchronizaci novych pametovych
  commitu ze zdrojoveho `main`; proto souhrnny status docasne hlasi `ok=false`.
- Regresni bod 0.5 prosel: Python kompilace, JavaScript hlavniho i Human–Adam UI,
  shell syntaxe, plna sada 856 testu za 198,475 sekundy a nasledny zivy Cockpit
  smoke test 5/5.
- Nebyl zmenen kod, UI, API, runtime, Git workflow, nasazeni ani bezici relace.

Co neni hotove:
- Implementacni transformace jeste nezacala.
- Aktivni profil je po pametovych commitech stale potreba bezne synchronizovat
  pres `Pripojit`, ale az po cistem checkpointu zdrojoveho repa.
- Stary runtime nazev se zatim nesmi prejmenovat, protoze jej pouziva soucasna
  profilova konfigurace Cockpitu.

Dalsi krok:
Checkpointnout a pushnout dokonceni kroku 0. Potom nechat aktivni profil bezne
synchronizovat a prvni implementacni fazi zahajit z cisteho stavu podle dalsiho
potvrzeneho zadani.

Navrhovane dalsi kroky:
- Po cistem checkpointu nechat aktivni profil bezne synchronizovat pres
  `Pripojit`; synchronizaci neprovadet uprostred rozpracovaneho source repa.
- Zachovat vysledek 856 testu a smoke 5/5 jako porovnavaci baseline pro kazdou
  dalsi implementacni fazi.
- Zachovat UI a zakladni funkce po celou dobu postupne transformace.

Zmenene nebo relevantni soubory:
- `memory/WORKSTREAMS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md`
- `memory/ACTIVE_PROJECTS.md`
- `app/communication/human_adam_profiles.py`

Bezpecnost / neukladat:
- Neukladat soukrome identifikatory vlaken, tokeny ani private obsah.
- Nemenit stary runtime nazev bez samostatne overene migrace.
- Tento checkpoint neautorizuje funkcni zmenu ani nasazeni.
