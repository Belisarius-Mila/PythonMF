Nazev: Python se Samanthou — samostatný balíček Praktické úlohy
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 18:18 CEST

Co se resilo:
Míla potvrdil, že Codex přihlášení a dílna 1.5 na Linuxu fungují. Zadal další
balíček lekcí s přenosem pouze obsahu.

Co je hotove:
- Třetí kurz Python — praktické úlohy, sedm nových lekcí: textové metody,
  append, součty, filtrování, enumerate, ošetření převodu a nákupní rozpočet.
- Výklad, ukázka, úkol, nápověda, vzor a vlastní rozšíření do dílny u každé lekce.
- Samostatný obsahový ZIP s jedinou složkou python_prakticke_ulohy, 30 souborů.
- Všech 62 testů; GUI sedmi nových lekcí, zachování starých pokusů/dokončení
  a obnovení. Ověřeno přikopírování do původní distribuce 1.5 bez změny runtime.
- Existující 1.5 a oba původní kurzy zachované. Celkem jsou tři kurzy a 21 lekcí.

Co neni hotove:
- Přikopírování a uživatelské vyzkoušení nového balíčku na Mílově Linuxu.
- Přenos postupu mezi stroji, input(), skutečné krokování a trvalé AI rozhovory.

Dalsi krok:
Rozbalit PythonPraktickeUlohy_7lekci_20260906.zip. Zkopírovat pouze složku
python_prakticke_ulohy do kurzy běžně používané aplikace 1.5. Restartovat učebnu
a zvolit Python — praktické úlohy. Ověřit kurzy/python_prakticke_ulohy/kurz.json.
Aplikaci ani Codex není potřeba přeinstalovat; .python_se_samanthou zachovat.

Navrhovane dalsi kroky:
Podle průchodu lekcemi další balíček, přenos pokusů nebo krokování. TVBCP po dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/kurzy/python_prakticke_ulohy/, scripts/build_course_package.py,
testy balíčku, README, vývojový build_release.py, projektová paměť a registr.
Důkazy a kontrolní součet jsou v projects/python_se_samanthou.md.

Bezpecnost / neukladat:
ZIP neobsahuje program učebny, přihlášení, osobní pokusy ani postup. Lekce běží
offline; AI v dílně je volitelná a dál používá účet ChatGPT. Nová ID oddělují
postup kurzů. Vývoj/testy pracovaly jen s dočasnými daty. Nový push není zadán;
1.4 00c16689 a 1.5 e4a550b9 dosud čekají v místním balíčku spolu s tímto krokem.
