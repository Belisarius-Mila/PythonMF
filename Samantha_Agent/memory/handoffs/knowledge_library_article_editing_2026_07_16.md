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

Bezpecnost / neukladat:
- Do Gitu ani handoffu nepatří texty soukromých článků, přílohy, metadata
  konkrétních osob ani obsah soukromého koše.
- Při odebrání přílohy neobcházet přesnou potvrzovací bránu a nikdy nemaž soubory
  archivu ručně bez samostatného potvrzení.
