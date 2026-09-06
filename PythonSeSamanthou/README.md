# Python se Samanthou 1.3

Offline učebna Pythonu pro Mílu se dvěma balíčky po sedmi lekcích a Mojí dílnou pro vlastní pokusy. Původní lekce mají stejný výklad,
zadání, ukázky, řešení i hodnocení. Obsah je nyní samostatný balíček:
další lekce se přidává soubory, nikoli rozšiřováním seznamu v programu.

## Spuštění na Linuxu nebo Macu

1. Rozbal **celý ZIP**. Složky `kurzy` a ostatní soubory ponech vedle programu.
2. Otevři terminál v nově rozbalené složce `PythonSeSamanthou_1_3`.
3. Spusť `python3 python_se_samanthou.py`.
4. Vlevo v **Balíček lekcí** vyber **Python — první kroky** nebo **Python — další kroky**.
5. Tlačítko **Moje dílna** nahoře otevře prostor pro vlastní pokusy. V záhlaví učebny uvidíš číslo **1.3**.

Potřebuješ Python 3.9 nebo novější a Tkinter. Nejsou potřeba žádné balíčky
z pipu, účet ani internet. Pokud na Linux Mintu chybí Tkinter, nainstaluj
`python3-tk` ve Správci softwaru. Program pracuje také při spuštění z jiné
složky; soubory kurzu hledá vedle svého zdrojového souboru.

Kód v editoru je skutečný Python s přístupem k tvému počítači. Třísekundový
limit pomáhá s nekonečnou smyčkou, není bezpečnostním sandboxem.
Ukázky ani řešení se při pouhém načtení kurzu nespouštějí.

## Moje dílna

Dílna je samostatné okno pro vlastní kód, bez školního hodnocení. Otevřeš ji
z horního tlačítka **Moje dílna**. Můžeš přepínat mezi oknem učebny a dílny.

- **Nový pokus** vytvoří prázdný pojmenovaný pokus.
- **Přejmenovat** změní název; **Vytvořit kopii** založí samostatnou variantu.
- **Do dílny** v učebně zkopíruje právě rozepsaný kód lekce do nového pokusu.
  Změny v této kopii neovlivní lekci ani její dokončení.
- **Moje poznámky** uchovávají tvůj záměr, otázky a zjištění u konkrétního pokusu.
- **Spustit**, F5 nebo Ctrl+Enter spustí kód. Výpis, obrázek a konečné jednoduché
  proměnné fungují stejně jako v lekcích, včetně vysvětlení chyb a limitu tří sekund.
- **Otevřít .py…** načte kopii souboru v UTF-8 jako nový pokus. Soubor se tím
  nespustí ani nezmění; rozpracovaný kód může obsahovat i chyby.
- **Exportovat .py…** uloží kód do nového souboru. Existující soubor se nepřepíše.
  Poznámky zůstanou v dílně. Kód s kruh(), pozadi() a dalšími kreslicími pomocníky
  je potřeba spouštět v učebně; tyto funkce nejsou součástí běžného Pythonu.

Pokus i poznámky se automaticky ukládají po úpravě, před spuštěním, při změně
pokusu a zavření. Ručně lze uložit tlačítkem **Uložit** nebo Ctrl+S.
Dílna obnoví poslední pokus. Při neúspěšném uložení zobrazí zprávu a před zavřením
se zeptá; kód lze stále zkopírovat nebo exportovat. Při souběhu dvou aplikací
se novější uložená data nepřepisují. Během běhu nelze přepnout na jiný pokus.

Limity první verze: 50 000 znaků kódu, 10 000 znaků poznámek a název do 80 znaků.
Dílna zatím nemá AI vysvětlování, interaktivní input(), krokování ani automatický
přenos mezi počítači. Záložka Proměnné zobrazuje konečné jednoduché hodnoty,
ne obsah celých seznamů a slovníků. Uložení chybného Pythonu je v pořádku —
chybu zjistíš při spuštění.

Soukromé pokusy jsou v `~/.python_se_samanthou/dilna.json`, odděleně od lekcí.
Při použití `--state-dir` se i dílna uloží do této zvolené datové složky.
Pokusy, poznámky ani osobní postup nejsou součástí distribučního ZIPu nebo Gitu.
Při aktualizaci aplikace ponech tuto datovou složku zachovanou.

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

## Přidávání a přepínání balíčků

Balíček „Python — další kroky“ přidává text a f-string, seznamy, cyklus se
seznamem, return, while, slovníky a bodovací panel. Celkem je 14 lekcí.
Každý balíček má vlastní číslování od jedničky, pokusy i dokončení. Při přepnutí
se nejprve uloží otevřená lekce; během běhu programu nebo při chybě ukládání
učebna přepnutí nepovolí. Návrat do balíčku otevře jeho poslední vybranou lekci.
Po běžném spuštění aplikace se nabídne základní balíček.

Přídavný ZIP obsahuje složku `kurzy/python_dalsi_kroky`. Zkopíruj ji do `kurzy`
své učebny a aplikaci znovu spusť. Nové balíčky se vyhledávají při startu;
vadné a duplicitní balíčky učebna ohlásí. Kompletní ZIP verze 1.3 obsahuje oba balíčky i dílnu.
Samotný přídavný balíček funguje i ve verzi 1.1 přes argument `--course`;
přesný příkaz je v jeho README. Původní balíček se při připojení nemění.

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
python3 tests/gui_courses_smoke.py
python3 tests/gui_workshop_smoke.py
```

GUI příkazy potřebují grafickou plochu. Původní GUI test ve zkušebních datech otevře skutečné
okno, převede starý postup, projde sedm řešení, ověří kreslení, uložení a
znovuotevření se změněným pořadím lekcí. Testovací složku po sobě odstraní.

Na Macu prošlo 42 automatických testů a tři GUI smoke. Test dílny ověřuje kopii
z lekce, názvy a poznámky, kreslení, chyby, časový limit, import/export, konflikt
uložení i znovuotevření bez změny postupu lekcí. Míla potvrdil fungování verze 1.2.
Pro novou verzi 1.3 na Linux PC zbývá ověřit:

1. Číslo 1.3 v záhlaví a otevření Mojí dílny.
2. Nový pokus, jeho spuštění a kreslení.
3. Zachování názvu, kódu a poznámek po zavření a znovuotevření.
4. Kopii z lekce, import/export .py a zachování původního postupu obou balíčků.

## Původ a další kroky

Základem je soubor `python_se_samanthou.py` přijatý přes LocalSend od Samanthy
(ChatGPT), verze 1.0. Neupravená referenční kopie pro regresní testy je v
`reference/python_se_samanthou_v1.py`; běžná učebna ji nepoužívá.
SHA-256 původního souboru:
`94583742b6b192e9610c63fd9dca67f735a818ee47235d51fd63a6486f6c6013`.

Verze 1.2 přidala druhý balíček a přepínání. Verze 1.3 přidává Moji dílnu.
Otevřené další směry: vysvětlení kódu s doplňujícími otázkami, přenos pokusů
a postupu mezi Macem a Linuxem, kontextové nápovědy a skutečné krokování.
