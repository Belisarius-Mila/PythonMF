Nazev: Python se Samanthou — Codex s účtem ChatGPT v dílně 1.5
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-09-06 15:37 CEST

Co se resilo:
Míla zadal nahradit placené API přihlášeným Codexem, aby nemusel přepínat okna.

Co je hotove:
- AI vysvětlení, malý další krok a doptání přes Codex na pozadí přímo v dílně.
- Připojení AI: instalační návod, browser přihlášení přes ChatGPT, kontrola.
- Povinné ChatGPT přihlášení před dotazem, API backend/fallback odstraněn.
- Zastavení požadavku, časový limit, přehledné chyby; zachování rozepsané otázky.
- Oddělené rozhovory pokusů, rozlišení upraveného kódu a pozdních odpovědí.
- 56 testů a čtyři Mac Tk GUI smoke; skutečné Codex vysvětlení i doptání,
  včetně odpovědi přímo v Tk panelu. Vše nad syntetickými/dočasnými daty.
- Jeden kompletní ZIP 1.5 v LocalSendu, oba kurzy i persistence zachovány.

Co neni hotove:
- Instalace Codexu a přihlášení na Mílově Linuxu, retest kompletního toku.
- Potvrzení původního problému read-only na Linuxu; na Macu psaní funguje.
- Trvalé rozhovory, input(), skutečné krokování a přenos postupu mezi stroji.

Dalsi krok:
Rozbalit PythonSeSamanthou_1_5_20260906.zip, spustit aplikaci z nové složky
PythonSeSamanthou_1_5. Moje dílna → AI průvodce → Připojení AI.
Nainstalovat aktuální Codex (nejméně 0.153.0), přihlásit se přes ChatGPT a ověřit
připojení. Potom otázky i odpovědi zůstávají v dílně. Zachovat .python_se_samanthou.

Navrhovane dalsi kroky:
Po retestu přenos pokusů nebo krokování dle Mílova výběru. TVBCP po dohodě.

Zmenene nebo relevantni soubory:
PythonSeSamanthou/, projects/python_se_samanthou.md, ACTIVE_PROJECTS.md, MEMORY_INDEX.md.
Podrobný důkaz a kontrolní součet ZIPu jsou v projektové paměti.

Bezpecnost / neukladat:
Autentizaci spravuje Codex, aplikace tokeny nečte a neexportuje. Přihlášení sdílí
s místním Codexem. Odeslání pouze tlačítkem; kód/poznámky/výpis a omezená historie
jdou přes Codex do OpenAI. Čerpají se oprávnění a limity účtu, žádný API fallback.
Běh má read-only, vypnuté shellové nástroje, pluginy, hooks a paměť. Učební kód
sám uživatel dál spouští běžným workerem, který není bezpečnostní sandbox.
1.3 byla pushnuta jako 6fb2c215; 1.4 00c16689 a nová 1.5 pouze místní checkpointy.
Nový push ani deploy nyní není autorizovaný.
