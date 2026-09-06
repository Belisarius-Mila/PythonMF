Nazev: Python se Samanthou — Moje dílna a dva balíčky lekcí
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 14:08 CEST

Co se resilo:
Míla potvrdil fungování verze 1.2 a zadal vývoj Mojí dílny. Nynější verze 1.3
má offline prostor pro vlastní pokusy; AI vysvětlování přijde jako další etapa.

Co je hotove:
- Pojmenované pokusy, poznámky, kopie, automatické ukládání a znovuotevření.
- Kopie z lekce, import .py bez spuštění a export do nového .py souboru.
- Stejný běh kódu, kreslení a chyby jako v učebně. Dílna má vlastní dilna.json;
  kurzy a prubeh_v2.json zůstávají zachované. Konflikty a vadná data se nepřepíší.
- 42 testů a tři skutečné GUI smoke na Macu prošly; ověřena i rozbalená distribuce.
- Jeden kompletní ZIP 1.3 v LocalSendu; číslo verze je vidět v obou oknech.
- Plná brána 1518 testů, rychlá statika i všech 28 testů katalogu/registru prošly.

Co neni hotove:
- Uživatelský retest dílny na Linux PC.
- AI vysvětlování, doptávání, krokování, input() a automatický přenos postupu.

Dalsi krok:
Na Linuxu rozbalit jediný PythonSeSamanthou_1_3_20260906.zip, otevřít novou
složku PythonSeSamanthou_1_3 a spustit python3 python_se_samanthou.py.
Nahoře otevřít Moji dílnu, zkusit pokus a poznámky, kopii z lekce a obnovení
po zavření. Ponechat skrytou datovou složku .python_se_samanthou.

Navrhovane dalsi kroky:
Po potvrzení nové verze navázat AI vysvětlením kódu s možností doptání nebo
přenosem pokusů mezi Macem a Linuxem. TVBCP pouze po výslovné dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/, projects/python_se_samanthou.md, ACTIVE_PROJECTS.md, MEMORY_INDEX.md.
Podrobné důkazy a kontrolní součet ZIPu jsou v projektové paměti.

Bezpecnost / neukladat:
Osobní pokusy, poznámky ani postup nesmí do Gitu nebo distribučního ZIPu.
Původní programy a datové soubory zachovat. Commit fa329883 byl dříve autorizovaně
pushnut; pro 1.2 ani 1.3 zatím další push/deploy autorizace není.
