Nazev: Cockpit knihovna clanku a soukromy webovy archiv
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-10

Co se resilo:
- Mila chtel jednoduchou databazi clanku, receptu a praktickych navodu: vlozit URL, ulozit zdrojovou adresu, precist clanek, ulozit prosty text a pozdeji hledat ve fulltextu.
- Navazujici pozadavek byl vstup primo v Cockpitu: vlozit URL, vybrat kategorii a nechat zbytek probehnout automaticky.

Co je hotove:
- Vznikl sdileny modul `app/article_archive.py` pro archivaci, seznam, fulltextove hledani a cteni ulozenych clanku.
- Archiv uklada metadata, zdrojove HTML a prosty text do soukrome ignorovane slozky `data/private/article_archive/`.
- Kategorie jsou `Recepty`, `Vědecké články` a `Ostatní`.
- V Cockpitu je tlacitko `Knihovna` s modalem pro seznam, vyhledavani, cteni a ulozeni nove URL.
- Pridany CLI skripty:
  - `scripts/archive_article_url.py`
  - `scripts/search_article_archive.py`
  - `scripts/read_article_archive.py`
- Opravena SSL chyba pri stahovani nekterych HTTPS stranek: Python `urllib` zkusi URL jako prvni, pri `CERTIFICATE_VERIFY_FAILED` se pouzije systemovy `curl` bez vypnuti TLS overeni.
- Prvni prakticky clanek o lepeni sparovky z Naradi Praha byl ulozen do soukromeho archivu mimo git.

Co neni hotove:
- Neni hotovy hezci editacni/detailni panel pro rucni opravu nazvu, kategorie nebo tagu.
- Neni hotove deduplikacni upozorneni v UI; stejna URL zatim bezpecne prepise stejne ID/metadatovy zaznam podle soucasne logiky.
- Neni hotove automaticke shrnuti clanku, jen ulozeni a fulltext.

Dalsi krok:
- Rucne v Cockpitu zkusit vlozit jeste jednu realnou URL do kazde kategorie: recept, vedecky/prakticky clanek a ostatni.

Navrhovane dalsi kroky:
- Okamzite: pridat v UI drobny stav "ulozeno do kategorie X" a pripadne tlacitko otevrit zdrojovou URL.
- Pozdeji: pridat editaci metadat, deduplikacni hlasku a jednoduchy export seznamu ulozenych clanku.
- Az bude vic obsahu: zvazit lokalni shrnuti nebo poznamku "proc je clanek dulezity".

Zmenene nebo relevantni soubory:
- `app/article_archive.py`
- `app/cockpit.py`
- `scripts/archive_article_url.py`
- `scripts/search_article_archive.py`
- `scripts/read_article_archive.py`
- `tests/test_article_archive.py`
- `tests/test_cockpit.py`
- `memory/projects/vedecke_clanky.md`

Bezpecnost / neukladat:
- Plne texty clanku, zdrojove HTML a metadata archivu jsou v `data/private/article_archive/` mimo git.
- Do handoffu ani gitu neukladat cele clanky, soukrome poznamky, placeny obsah, tokeny ani citlive rodinne informace.
