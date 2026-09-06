Nazev: Python se Samanthou — dva balíčky po sedmi lekcích
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 12:40 CEST

Co se resilo:
Po oddělení původních sedmi lekcí Míla potvrdil stejné chování rozbalené verze
a požádal o připojení dalšího balíčku sedmi lekcí. Mac a Linux jsou cílové platformy.

Co je hotove:
- Projekt PythonSeSamanthou 1.2, dva balíčky po sedmi lekcích, přepínač v GUI.
- Trvalá ID, nedestruktivní migrace v1, atomické ukládání a detekce konfliktu.
- 31 cílených testů a oba skutečné GUI smoke na Macu prošly; i z rozbaleného ZIPu.
- Přídavný balíček ověřen také nad nezměněnou 1.1: sedm řešení prošlo.
- Kompletní ZIP 1.2 i samostatný přídavný ZIP v LocalSendu; původní kurz nezměněn.
- Plný běh: 1517/1518 prošlo; chybná katalogová vazba záznamu učebny v registru
  opravena. Následně všech 28 testů katalogu a registru i rychlá statika prošly.
  Celý běh se po čistě dokumentační opravě neopakoval; důkaz je v projektové paměti.
- Podrobné důkazy a kontrolní součty v projects/python_se_samanthou.md.

Co neni hotove:
- Ruční retest na skutečném Linux PC.
- Přenos postupu Mac–Linux, Moje dílna ani AI vysvětlování nejsou součástí této verze.

Dalsi krok:
Na Linuxu rozbalit celý PythonSeSamanthou_1_2_20260906.zip, zavřít starou učebnu,
spustit python3 python_se_samanthou.py a vlevo vybrat Python — další kroky.
Ověřit přepínání, nové úlohy, původní pokusy a znovuotevření. Návod je v README.md.

Navrhovane dalsi kroky:
Po potvrzení nové verze zvolit přenos postupu mezi počítači nebo Moji dílnu. Nový TVBCP zakládat pouze po výslovné dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/, projects/python_se_samanthou.md, ACTIVE_PROJECTS.md, MEMORY_INDEX.md.

Bezpecnost / neukladat:
Neukládat osobní rozepsaný kód do Gitu ani distribučního ZIPu. Původní program
i původní prubeh.json zachovat. První commit fa329883 byl autorizovaně pushnut. Pro etapu 1.2 zatím push/deploy
autorizace není.
