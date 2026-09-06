Nazev: Python se Samanthou — balíček sedmi offline lekcí
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 10:57 CEST

Co se resilo:
První schválený vývojový krok učebny: oddělit obsah od programu a zachovat
chování sedmi lekcí i rozepsaný postup. Mac a Linux jsou cílové platformy.

Co je hotove:
- Projekt PythonSeSamanthou, sedm samostatných lekcí, loader a společné kontroly.
- Trvalá ID, nedestruktivní migrace v1, atomické ukládání a detekce konfliktu.
- 27 cílených testů a skutečné GUI na Macu prošly; ověřeno i z rozbaleného ZIPu.
- ZIP v LocalSendu a README pro Mílovu zkoušku; původní soubor nezměněn.
- Plná brána 1518 testů, rychlá statická brána a pět testů registru prošly.
- Podrobné důkazy a kontrolní součty v projects/python_se_samanthou.md.

Co neni hotove:
- Ruční retest na skutečném Linux PC.
- Přenos postupu Mac–Linux, Moje dílna ani AI vysvětlování nejsou součástí této verze.

Dalsi krok:
Na Linuxu rozbalit celý PythonSeSamanthou_1_1_20260906.zip, zavřít starou učebnu,
spustit python3 python_se_samanthou.py a ověřit kreslení, převzetí postupu a
znovuotevření. Kontrolní postup je v README.md.

Navrhovane dalsi kroky:
Po potvrzení Linuxu navázat druhou etapou — jednoduchým přenosem kurzů a postupu,
poté Mojí dílnou. Nový TVBCP zakládat pouze po výslovné dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/, projects/python_se_samanthou.md, ACTIVE_PROJECTS.md, MEMORY_INDEX.md.

Bezpecnost / neukladat:
Neukládat osobní rozepsaný kód do Gitu ani distribučního ZIPu. Původní program
i původní prubeh.json zachovat. Bez push/deploy autorizace pro tuto novou etapu.
