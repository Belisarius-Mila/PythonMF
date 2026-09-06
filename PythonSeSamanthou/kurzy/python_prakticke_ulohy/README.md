# Python — praktické úlohy

Třetí balíček pro Python se Samanthou: sedm offline lekcí navazujících na
„Python — první kroky“ a „Python — další kroky“. Celkem budeš mít 21 lekcí.
Aktualizace aplikace ani nové přihlašování do Codexu nejsou potřeba.

## Co se naučíš

1. **Čistý text** — strip(), lower() a zachování původního vstupu.
2. **Doplň seznam** — append(), počet položek a rozdíl proti textovým metodám.
3. **Průběžný součet** — postupné sčítání a sledování mezivýsledků.
4. **Vyber hodnoty** — filtrování do nového seznamu, >= a odsazení.
5. **Číslovaný výpis** — enumerate(), dvojice číslo/položka, pořadí versus index.
6. **Ošetři chybu** — int(), try a except ValueError, pokračování po chybném vstupu.
7. **Můj nákupní rozpočet** — seznam slovníků, funkce, součet a hraniční případy.

V každé lekci nejdřív odhadni výsledek a spusť ukázku. Potom udělej malou
úpravu podle zadání a stiskni **Ověřit úkol**. Výklad vysvětluje nový pojem,
častou chybu a nabízí navazující vlastní pokus. Na úpravy mimo přesné zadání
použij **Do dílny**. Tam se můžeš doptat AI; samotné lekce internet nepotřebují.
Odhady času jsou orientační — postupuj vlastním tempem.

## Připojení k tvojí aplikaci 1.5 — kopíruješ jen jednu složku

1. Zavři učebnu, aby se při příštím startu načetl seznam balíčků.
2. Rozbal `PythonPraktickeUlohy_7lekci_20260906.zip`.
3. Uvnitř najdi složku **python_prakticke_ulohy**. V ní musí být `kurz.json`,
   tento README a sedm složek lekcí. Některé rozbalovací programy kolem vytvoří
   ještě složku se jménem ZIPu; tu do kurzů nepřidávej.
4. Zkopíruj pouze **python_prakticke_ulohy** do složky **kurzy** aplikace,
   ze které opravdu spouštíš `python_se_samanthou.py`.
5. Znovu spusť učebnu. Vlevo v **Balíček lekcí** vyber **Python — praktické úlohy**.

Výsledná struktura má být:

```text
PythonSeSamanthou_1_5/
├── python_se_samanthou.py
└── kurzy/
    ├── python_zaklady/
    ├── python_dalsi_kroky/
    └── python_prakticke_ulohy/
        ├── kurz.json
        ├── README.md
        ├── 01_cisty_text/
        ├── 02_dopln_seznam/
        ├── 03_prubezny_soucet/
        ├── 04_vyber_hodnot/
        ├── 05_cislovany_vypis/
        ├── 06_osetri_chybu/
        └── 07_nakupni_rozpocet/
```

Pokud balíček ve výběru chybí, zkontroluj zejména cestu
`kurzy/python_prakticke_ulohy/kurz.json`. Nesmí vzniknout další vložená složka
`kurzy/kurzy` ani `python_prakticke_ulohy/python_prakticke_ulohy`.
Kopíruj do správné verze učebny a po kopírování ji úplně zavři a znovu spusť.

Původní balíčky ponech. Složku `~/.python_se_samanthou` s osobním postupem
neměň; nový kurz má vlastní ID a vlastní dokončení. ZIP neobsahuje aplikaci,
autentizaci, tvé pokusy ani osobní postup. Obsah lekcí používá stejný formát
jako verze 1.1; výběr v okně funguje od verze 1.2.

## Jaké kontroly můžeš očekávat

Kontroly běží offline ve stávající aplikaci. Porovnávají výpis, vybrané
jednoduché proměnné a dostupné kontroly konstrukcí/jmen. Nejsou obecným
hodnotitelem všech správných řešení a neumějí vynutit každou konkrétní metodu.
Například přesné použití strip(), lower(), append() nebo struktury try/except
si porovnej s výkladem a vzorem; odpovídající výsledky jsou automaticky ověřené.
Seznamy a slovníky zobrazuj přes print(), záložka Proměnné ukazuje jednoduché hodnoty.
