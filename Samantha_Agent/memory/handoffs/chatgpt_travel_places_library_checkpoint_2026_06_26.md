Nazev: ChatGPT export / Cestovani mista do knihovny
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-26

Co se resilo:
Z baliku ChatGPT exportu `nakupy_cestovani` se oddelily jen cestovatelske inspirace:
zajimave destinace, mista k navstiveni a verejne pouzitelne cestovni poznamky,
idealne mimo masovou turistiku. Nakupy, ubytovaci logistika, doklady, faktury,
pristupy a soukrome cestovni plany byly zamerne vynechane.

Co je hotove:
- V Knihovne vznikla nova git-safe kategorie `travel_places` s popiskem
  `Cestování / místa`.
- Kategorie je dostupna v Cockpitu pri ukladani URL, pri ukladani textu i jako
  samostatna zalozka Knihovny.
- Zmena kodu je commitnuta a pushnuta jako `ab1dd70 Add travel places library category`.
- Ze soukromeho ChatGPT exportu vznikl private kandidatni report:
  `data/private/knowledge_inbox/processed/chatgpt_export_travel_places_candidates_2026_06_26.md`
- Mila z rucni kontroly vybral polozky 1, 2, 5 a 6 z druhe devitky.
- Do private knihovny `data/private/article_archive/` byly vlozeny 4 ocistene
  cestovni karty v kategorii `travel_places`, vsechny se stavem `K precteni`:
  Egadske ostrovy, Rychlebske hory, prirodni vylety v Dominikanske republice
  a Erzherzog-Johann-Huette / Grossglockner.
- `git status` po importu soukromych karet zustal cisty, protoze article archive
  je ignorovany private prostor.

Co neni hotove:
- Neni rucne otestovana nova zalozka `Cestování / místa` primo v Cockpitu.
- Nebyly importovane dalsi cestovni kandidaty z ChatGPT exportu.
- U ulozenych karet nejsou definitivne proverene vsechny aktualni provozni udaje;
  pred cestou je nutne overit sezonu, dopravu, rezervace, oteviraci dobu a narocnost.

Dalsi krok:
Otevrit Cockpit -> Knihovna -> `Cestování / místa`, overit 4 karty, stav
`K přečtení`, fulltext a pripadne tlacitko `Otevřít na webu` jen u polozek,
ktere maji verejnou URL.

Navrhovane dalsi kroky:
- Okamzity: rucni UI retest nove knihovni zalozky.
- Volitelne: pokud Mila chce, projit zbylych 9 rucnich cestovnich kandidatu z
  private reportu a vybrat dalsi 1-3 karty.
- Navazujici: pro cestovni karty zvazit pozdeji jednotnou sablonu `Proc zaujalo`,
  `Co videt`, `Pro koho`, `Co overit pred cestou`, `Verejne zdroje`.

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `data/private/knowledge_inbox/processed/chatgpt_export_travel_places_candidates_2026_06_26.md`
- `data/private/knowledge_inbox/processed/chatgpt_export_travel_places_candidates_2026_06_26.json`
- `data/private/article_archive/`

Bezpecnost / neukladat:
- Do gitu nepatri raw ChatGPT export, cele texty konverzaci, soukrome cestovni
  plany, doklady, rezervace, objednavky, zdravotni ani rodinne detaily.
- Private knihovni karty zustavaji pouze v `data/private/article_archive/`.
- Pri dalsim importu cestovnich kandidatu nejdrive rucni vyber; automaticky
  neimportovat medium/high-risk polozky ani cokoli s private/secrets signaly.
