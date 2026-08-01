<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-01 15:49 CEST

### Hotovo
- Obrázky se otevírají v Knihovně s jasným tlačítkem pro návrat

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

### Další krok
- Převzít a nasadit změnu, potom ověřit návrat z obrázku na iPhonu

### Rozhodnutí
- Obrázkové přílohy se otevírají uvnitř Knihovny místo v nové kartě

### Navrhované další kroky
- Žádné další návrhy nad rámec bezprostředního kroku.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `f4092fb481b4`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `d1ffd4c0bc56` · je starší než ověřený main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-01T12:25:16+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

Nazev: Knihovna v Cockpitu – editace článku a příloh
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-16

Co se resilo:
- Human–Adam doplnil přímou editaci existující znalostní karty v Cockpitu.
- Součástí stejného celku je úprava popisku a poznámky přílohy a bezpečné
  odebrání přílohy do soukromého koše.
- Kanonický commit je `2597e14` (`Knihovna - editace`) z 2026-07-16.

Co je hotove:
- Editor načte celý text vybrané karty a umožní změnit název, text, kategorii,
  tagy, označení zdroje a poznámku ke zdroji.
- Uložení aktualizuje text, metadata i registr; při chybě vrací původní stav.
- Existující přílohy zůstanou při editaci článku zachované a obrazová karta si
  zachová technický tag `ma-obrazek`.
- U přílohy lze změnit pouze popisek a poznámku, bez přepisu obrazových souborů.
- Odebrání přílohy vyžaduje přesnou potvrzovací větu, přesune její soubory do
  soukromého koše s manifestem a upraví metadata i registr.
- Přílohy mimo recepty používají obecný popisek a tagy; nedostávají automaticky
  receptové nebo rukopisné značky.
- Změna je v `app/article_archive.py`, `app/cockpit.py`,
  `test_article_archive.py` a `test_cockpit.py`.

Co neni hotove:
- Terminálový Adam samostatně neopakoval ruční editaci skutečného soukromého
  článku v UI; soukromý obsah nebyl kvůli handoffu čten ani vypisován.
- Obnova jednotlivé přílohy přímo z koše nemá samostatné tlačítko v Cockpitu;
  odebrání je vratné technicky uloženými soubory a manifestem.

Dalsi krok:
- Bez okamžité vývojové akce. Při příští běžné editaci zkontrolovat, že se po
  uložení znovu otevře stejná karta se zachovanými přílohami.

Navrhovane dalsi kroky:
- Na necitlivé nebo testovací kartě lze samostatně ověřit změnu popisku přílohy
  a potvrzované odebrání do koše.
- Samostatné uživatelské obnovení přílohy z koše řešit pouze podle reálné potřeby.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `memory/projects/vedecke_clanky.md`

Overeni:
- Commit `2597e14` mění pouze čtyři kódové a testovací soubory; soukromý archiv
  článků není součástí commitu.
- Dne 2026-07-16 terminálově znovu prošlo 6 cílených regresních testů, Python
  kompilace obou aplikačních modulů a `git diff --check`.

Infrastrukturni registrace 2026-07-20:
- Knihovna je ve fazi 1.3 transformace Human–Adam zkušebne zaregistrovana jako
  `Project` `project-knowledge-library`.
- Vazba pouziva stavajici oddelene vlakno Knihovny, `knihovna_cockpit.txt`, tento
  handoff a existujici izolovany workspace; zadny soukromy identifikator vlakna
  se do Gitu neuklada.
- Neveřejny koordinator umi prechod Human–Adam -> Knihovna -> Human–Adam a pri
  aktivaci automaticky fast-forwarduje cisty cil z commitnuteho lokalniho
  `main`. API ani UI zatim nejsou prepnute.
- Cilena sada 38 testu, plna sada 870 testu a zivy Cockpit smoke 5/5 prosly.
- Faze 1.4 dne 2026-07-20 zachovala stejny vyber a jeho vzhled, ale zdroj polozek
  prepojila na koordinator. Knihovna se nyni v payloadu voli kanonickym ID
  `project-knowledge-library`; puvodni profilove ID zustava vratnym fallbackem.
- Automatizovana sada 93 cilenych a 871 plnych testu prosla. Zmena jeste neni
  nasazena ani rucne prokliknuta v zivem Cockpitu.
- Commit `6f17852` byl nasazen a Cockpit rizene restartovan na code stamp
  `7a4440b979d98690`. Zivy endpointovy prechod Human–Adam -> Knihovna ->
  Human–Adam prosel a oba workspaces skoncily ciste a zarovnane.
- Vizualni kliknuti pres menu zatim chybi pouze proto, ze vestaveny prohlizec
  nebyl v terminalove relaci dostupny; soukromy obsah Knihovny se necetl.

Bezpecnost / neukladat:
- Do Gitu ani handoffu nepatří texty soukromých článků, přílohy, metadata
  konkrétních osob ani obsah soukromého koše.
- Při odebrání přílohy neobcházet přesnou potvrzovací bránu a nikdy nemaž soubory
  archivu ručně bez samostatného potvrzení.

### 2026-07-20 11:01 CEST – Živý zapisovací test fáze 1.6

- Knihovna ověřila automatické dokončení jednoho zapisovacího tahu přímo do
  `main`.

### Automatický checkpoint 2026-07-20 11:06 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Živý zapisovací test Knihovny fáze 1.6 prošel
- Ověření: plná Cockpit brána: 880 testů, 265.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (1): `Samantha_Agent/memory/handoffs/knowledge_library_article_editing_2026_07_16.md`
- Commit: `Verify Knihovna automatic completion live`
- Další krok: Ověřit čistý main, synchronizaci obou profilů a uvolnit přechodný semafor.

### Automatický checkpoint 2026-07-23 10:57 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Import URL nyní respektuje HTTP charset včetně ISO-8859-2
- Ověření: plná Cockpit brána: 1123 testů, 216.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`
- Commit: `Fix URL article HTTP charset decoding`
- Další krok: Nasadit opravu a samostatně obnovit dnešní kartu z uloženého source.html.

### Automatický checkpoint 2026-07-23 13:12 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Read-only náhled nové extrakce ISO-8859-2 je připraven bez změny karty
- Ověření: plná Cockpit brána: 1132 testů, 234.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (4): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_article_archive.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add read-only article re-extraction preview`
- Další krok: Nasadit změnu a spustit náhled nad dnešní kartou; samotnou opravu potvrdit samostatně.

### Automatický checkpoint 2026-07-23 22:11 CEST

- Pracovní proud: `project-knowledge-library`
- Souhrn: Import URL bezpečně rozbaluje gzip před dekódováním a regresní testy prošly
- Ověření: plná Cockpit brána: 1159 testů, 230.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/article_archive.py`, `Samantha_Agent/tests/test_article_archive.py`
- Commit: `Handle gzip-compressed article responses`
- Další krok: Nasadit změnu a samostatným výslovným pokynem opravit dnešní kartu z uloženého zdroje.

### Automatický checkpoint 2026-08-01 15:49 CEST

- Pracovní proud: `project-knowledge-library`
- Hotovo: Obrázky se otevírají v Knihovně s jasným tlačítkem pro návrat
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 9.1 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Add in-app library attachment viewer`
- Další krok: Převzít a nasadit změnu, potom ověřit návrat z obrázku na iPhonu
