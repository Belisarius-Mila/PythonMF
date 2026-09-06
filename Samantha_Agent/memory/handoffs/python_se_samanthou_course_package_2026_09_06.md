Nazev: Python se Samanthou — AI průvodce a upravitelná dílna 1.4
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 15:17 CEST

Co se resilo:
Míla hlásil read-only dílnu 1.3 a zadal AI vysvětlování a vedení. Nemá na Linuxu
API klíč ani přihlášený Codex. Zvolen jednoduchý API klient s nastavením v okně.

Co je hotove:
- Zřetelně označený editor, Upravit kód, zaměření vstupu a nabídka pro vložení.
- AI vysvětlení, pomoc s chybou, další malý krok a navazující otázky.
- Rozhovory oddělené podle pokusu, pozdní odpovědi a změněný kód rozlišeny.
- API klíč z UI jen pro otevřenou dílnu; bez klíče vše ostatní funguje offline.
- 51 automatických testů a čtyři Tk GUI smoke na Macu, skutečné klávesy,
  oddělené API rozhovory, chyby a zachování osobní práce v testovacích datech.
- Živé API vysvětlení syntetického příkladu i doptání prošlo.
- Jediný kompletní ZIP 1.4 v LocalSendu. Kurzy a formát soukromých dat zachovány.

Co neni hotove:
- Potvrzení konkrétního read-only problému na Linux PC. Na Macu se nereprodukoval.
- Mílův vlastní API účet/klíč na Linuxu a uživatelský retest AI připojení.
- Trvalé ukládání AI rozhovorů, input(), skutečné krokování, přenos postupu.

Dalsi krok:
Na Linuxu rozbalit PythonSeSamanthou_1_4_20260906.zip, ve složce
PythonSeSamanthou_1_4 spustit python3 python_se_samanthou.py. Zkusit psaní
v MŮJ KÓD a poznámkách. AI průvodce → Nastavení AI otevře návod/stránku
pro klíč; vytvořený klíč vložit pouze do zakrytého pole aplikace.
Ponechat skrytou datovou složku .python_se_samanthou.

Navrhovane dalsi kroky:
Po Linux retestu pokračovat dle Mílovy volby: pohodlnější přihlášení,
přenos pokusů nebo krokování. TVBCP pouze po výslovné dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/, projects/python_se_samanthou.md, ACTIVE_PROJECTS.md, MEMORY_INDEX.md.
Podrobný důkaz a kontrolní součet ZIPu jsou v projektové paměti.

Bezpecnost / neukladat:
Klíče, pokusy, poznámky a postup nepatří do Gitu/ZIPu. AI tlačítko posílá
zobrazený kód, poznámky, odpovídající výpis a omezenou historii do OpenAI;
AI kód nemění ani nespouští. Klíč i rozhovory z UI platí do zavření dílny.
Předchozí 1.3 autorizovaně pushnuta jako 6fb2c215. Nová 1.4 jen lokální
checkpoint; nový push/deploy zatím není autorizovaný.
