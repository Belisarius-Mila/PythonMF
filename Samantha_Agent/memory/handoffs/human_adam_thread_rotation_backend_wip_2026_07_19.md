Nazev: Human-Adam - bezpecna rotace dlouheho profiloveho vlakna
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Ochrana dlouhych profilovych Codex vlaken pred postupnym zahlcenim kontextu.
- Bezpecna rucni rotace na nove vlakno bez smazani nebo archivace puvodniho.
- Navazani kontinuity pres existujici soukromou profilovou kontextovou kotvu.

Co je hotove:

- Session Hub umi auditovat pripravenost rotace a zalozit nove persistovane vlakno.
- Puvodni vlakno, jeho technicka identita a lokalni historie zustavaji zachovane.
- Rotace je fail-closed pri aktivnim tahu, nejistem doruceni nebo zmene ocekavaneho vlakna.
- Sluzba vyzaduje pripojeny profil, aktivni neprázdnou kontextovou kotvu a presnou
  potvrzovaci vetu `POTVRZUJI ROTACI PROFILOVEHO VLAKNA`.
- Opraven je restart prazdneho noveho vlakna: lze je bezpecne nahradit, i kdyz
  lokalni historie obsahuje zpravy predchoziho zachovaneho vlakna.
- Doplnene profilove audit/apply API drzi audit i rotaci pod stejnym zamkem
  aktivniho profilu; druhy profil zustava nedotceny.
- V panelu `Plan` je rucni kontrola pripravenosti, viditelne zadani presne
  potvrzovaci vety a samostatne tlacitko pro prechod do noveho vlakna.
- UI zneplatni audit pri zmene vlakna nebo revize kotvy a rotaci blokuje pri
  aktivnim tahu, odpojenem profilu nebo rozpracovane kotve.
- Cela Cockpit quality gate se 804 testy prosla spolu se syntaxemi,
  JavaScript/shell kontrolami a `git diff --check`.
- Lokalni testovaci server potvrdil nacteni ovladacich prvku a read-only API;
  audit spravne vratil fail-closed blokery pro nepripojeny prazdny testovaci
  profil.

Co neni hotove:

- Nebyl proveden zivy test nad skutecnym Human-Adam nebo Knihovna vlaknem.
- Nebyl dostupny pripojeny prohlizec pro obrazovy klikaci test rozlozeni.
- WIP v `wip/thread-rotation-api-20260719` neni nasazeny do `main`; zivy Cockpit
  pouziva predchozi stabilni verzi.

Dalsi krok:

- Po samostatnem potvrzeni prevzit WIP do `main` a nasadit. Potom vizualne overit
  panel `Plan` a provest zivy test pouze na zvolenem profilu s kratkou aktivni
  kotvou; pri rotaci neposilat zadny pokyn.

Navrhovane dalsi kroky:

- Po zivem testu overit, ze nove vlakno pouzilo pripnutou kotvu a stare zustalo
  dohledatelne bez archivace.
- Automatickou rotaci nezapinat; pripadny prah nejdrive jen informacne zobrazit.

Zmenene nebo relevantni soubory:

- `app/communication/session_hub.py`
- `app/communication/human_adam_service.py`
- `app/communication/human_adam_profiles.py`
- `app/communication/human_adam_ui.py`
- `app/cockpit.py`
- `tests/test_communication_session_hub.py`
- `tests/test_human_adam_service.py`
- `tests/test_human_adam_profiles.py`
- `tests/test_human_adam_ui.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:

- Neukladat obsah profilovych konverzaci, plna ID vlaken, tokeny, soukrome cesty
  ani obsah kontextovych kotev do Gitu, handoffu nebo TVBCP.
- Stare vlakno automaticky nemazat ani nearchivovat.
- Rotaci neprovadet pri aktivnim nebo nejistem doruceni.
