# Python se Samanthou 1.1

Offline učebna Pythonu pro Mílu. Sedm původních lekcí má stejný výklad,
zadání, ukázky, řešení i hodnocení. Obsah je nyní samostatný balíček:
další lekce se přidává soubory, nikoli rozšiřováním seznamu v programu.

## Spuštění na Linuxu nebo Macu

1. Rozbal **celý ZIP**. Složky `kurzy` a ostatní soubory ponech vedle programu.
2. Otevři terminál ve složce `PythonSeSamanthou`.
3. Spusť `python3 python_se_samanthou.py`.

Potřebuješ Python 3.9 nebo novější a Tkinter. Nejsou potřeba žádné balíčky
z pipu, účet ani internet. Pokud na Linux Mintu chybí Tkinter, nainstaluj
`python3-tk` ve Správci softwaru. Program pracuje také při spuštění z jiné
složky; soubory kurzu hledá vedle svého zdrojového souboru.

Kód v editoru je skutečný Python s přístupem k tvému počítači. Třísekundový
limit pomáhá s nekonečnou smyčkou, není bezpečnostním sandboxem.
Ukázky ani řešení se při pouhém načtení kurzu nespouštějí.

## Uložený postup

Před prvním spuštěním zavři starou učebnu. Nová verze na stejném počítači
načte `~/.python_se_samanthou/prubeh.json` a převede sedm číselných pozic
na trvalá ID lekcí. Rozepsaný kód, dokončení a poslední otevřená lekce se zachovají.

- Původní `prubeh.json` zůstane beze změny.
- Vznikne přesná kopie `prubeh_v1_pred_prevodem.json`.
- Nová učebna ukládá do `prubeh_v2.json` ve stejné složce.
- Chybný nebo novější neznámý formát se automaticky nepřepíše; učebna oznámí
  zastavené ukládání. Před zavřením si případný nový pokus zkopíruj.
- Dvě současně otevřené kopie si nepřepíší novější postup bez upozornění.

Starou aplikaci lze nadále spustit, ale používá svůj starý postup. Pokusy
z nové verze se do staré zpět nepřenášejí. Stejně tak se zatím automaticky
nesynchronizuje Mac a Linux. ZIP neobsahuje žádný osobní postup.

## Balíček lekcí

`kurzy/python_zaklady/kurz.json` určuje název, ID kurzu a pořadí lekcí.
Každá lekce má svou složku se čtyřmi soubory:

| Soubor | Obsah |
| --- | --- |
| `lekce.json` | Trvalé ID, název, úkol, nápověda, zprávy a pravidla kontroly |
| `vyklad.md` | Výklad zobrazovaný jako prostý text |
| `ukazka.py` | Počáteční kód pro editor |
| `reseni.py` | Vzorové řešení |

Pro další lekci zkopíruj podobnou složku, uprav obsah, přiděl nové unikátní ID
začínající `python-zaklady.` a připoj cestu k `lekce.json` do seznamu `lessons`
v `kurz.json`. Existující ID neměň při přejmenování nebo přesunu lekce:
právě podle ID se pozná tvůj uložený pokus. Čísla v seznamu se vytvoří podle pořadí.

Pravidla v `checks` musí být splněna všechna:

| `kind` | `value` |
| --- | --- |
| `output_lines` | Seznam přesných řádků výpisu |
| `variables_equal` | Slovník očekávaných konečných hodnot proměnných |
| `uses_name` | Jméno proměnné, které se v kódu čte |
| `ast_kind` | Konstrukce: `Mult`, `For`, `If`, `FunctionDef`, `Add`, `Sub`, `Div`, `Return`, `While` |
| `drawing_equals` | Přesný seznam kreslicích příkazů; příklad je v lekci 4 |

Jde o předem připravené kontroly, nikoli AI. Stejně jako původní verze mohou
odmítnout variantu mimo přesné zadání. Lekce využívající tyto kontroly lze
přidávat bez změny aplikace; zcela nový způsob hodnocení vyžaduje rozšířit
společný hodnoticí modul. Balíček nenačítá spustitelné pluginy.

Kontrola struktury bez GUI, spouštění kódu a zápisu postupu:

```sh
python3 python_se_samanthou.py --check-course
```

Jiný balíček stejného formátu lze otevřít pomocí `--course cesta/kurz.json`.
Samostatnou zkušební složku pro postup lze zvolit pomocí `--state-dir cesta`.

## Ověření a zkouška na Linuxu

Automatické testy nepracují s tvým skutečným postupem:

```sh
python3 -m unittest discover -s tests -v
python3 tests/gui_smoke.py
```

Druhý příkaz potřebuje grafickou plochu. Ve zkušebních datech otevře skutečné
okno, převede starý postup, projde sedm řešení, ověří kreslení, uložení a
znovuotevření se změněným pořadím lekcí. Testovací složku po sobě odstraní.

Na Macu oba testy prošly. Na tvém Linux PC zbývá ověřit:

1. Zobrazení diakritiky a čitelnost okna.
2. Spuštění a ověření úlohy; kruhy v lekci 4 a semafory v lekci 7.
3. Zachování rozepsaného pokusu a dokončení po zavření a znovuotevření.
4. Pokud jsi používal původní aplikaci na tomto Linuxu, převzetí jejího postupu.

## Původ a další kroky

Základem je soubor `python_se_samanthou.py` přijatý přes LocalSend od Samanthy
(ChatGPT), verze 1.0. Neupravená referenční kopie pro regresní testy je v
`reference/python_se_samanthou_v1.py`; běžná učebna ji nepoužívá.
SHA-256 původního souboru:
`94583742b6b192e9610c63fd9dca67f735a818ee47235d51fd63a6486f6c6013`.

Dohodnuté pořadí dalšího vývoje: ověření na Linuxu → přenos kurzů a postupu →
Moje dílna → vysvětlení kódu s doplňujícími otázkami → kontextové nápovědy →
skutečné krokování → další lekce. V této verzi je dokončené oddělení sedmi lekcí.
