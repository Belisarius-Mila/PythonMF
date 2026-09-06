#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python se Samanthou — první učebna, verze 1.0.

Spuštění: python3 python_se_samanthou.py
Linux Mint: pokud chybí tkinter, nainstaluj balíček python3-tk
(ve Správci softwaru, nebo příkazem sudo apt install python3-tk).
Vyžaduje Python 3.9+ a Tkinter. Jinak žádné další balíčky ani internet.
Na iPhonu se tato desktopová aplikace přímo nespouští.

Začni lekcí 1. Přečti vysvětlení, odhadni výsledek, spusť ukázku,
uprav ji podle úkolu a klikni na Ověřit úkol. Stačí jedna lekce najednou.
Nápověda a vzorové řešení jsou vlevo. A− / A+ mění velikost písma.
F5 nebo Ctrl+Enter spouští kód, Tab vloží čtyři mezery.
Rozepsané lekce a dokončení se ukládají místně do
~/.python_se_samanthou/prubeh.json; aplikace nic neodesílá.

Kód v editoru je skutečný Python, spouštěný na tvém počítači.
Kreslicí funkce kruh(), obdelnik(), cara(), napis() a pozadi()
jsou pomocníci této učebny, nikoli vestavěné příkazy Pythonu.
Podrobný přehled je v tlačítku Jak začít / kreslení.
Učebna neobsahuje připojení k AI: kontroly a nápovědy jsou předem napsané.
Složitější vysvětlení prober se Samanthou v chatu.

Proces má časový limit kvůli omylem nekonečným smyčkám; nejde o bezpečnostní
sandbox. Spouštěj vlastní kód a kód, kterému důvěřuješ. input() zde není
interaktivní; údaje pro cvičení zadávej do proměnných v editoru.

Technický základ GUI: https://docs.python.org/3/library/tkinter.html
"""

import ast
import io
import json
import keyword
import math
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import tokenize
import traceback


COLORS = {
    "modra": "#3287db", "zelena": "#2cb67d", "cervena": "#ef5b64",
    "zluta": "#f5c84c", "bila": "#ffffff", "cerna": "#202b3c",
    "oranzova": "#f69a48", "fialova": "#9b7ce0", "seda": "#7b8ba2",
}

LESSONS = [
    {
        "title": "První příkaz", "short": "1  První příkaz", "time": "5–10 minut",
        "explain": "Program je seznam pokynů, které počítač vykonává. Python čte tento kód shora dolů.\n\nprint() vypíše obsah závorek. Text uzavři do rovných uvozovek: \"text\". Uvozovky určují začátek a konec textu; ve výsledku se neukážou. Každý print() tady začne nový řádek.",
        "predict": "Co se objeví po spuštění? Budou ve výpisu i uvozovky?",
        "task": "Ponech první řádek a přidej druhý příkaz, který vypíše přesně: Učím se Python.",
        "starter": 'print("Ahoj, Mílo!")\n',
        "solution": 'print("Ahoj, Mílo!")\nprint("Učím se Python.")\n',
        "hint": 'Na nový řádek napiš další print(). Do závorek vlož text v uvozovkách. Nezapomeň tečku za slovem Python.',
        "success": "Umíš napsat a spustit první program! Každý ze dvou příkazů vypsal jeden řádek.",
    },
    {
        "title": "Proměnná má jméno", "short": "2  Proměnné", "time": "5–10 minut",
        "explain": 'Proměnná je pojmenování hodnoty, se kterou chceš pracovat. Řádek jmeno = "Míla" přiřadí text jménu jmeno. Znak = zde znamená přiřazení.\n\nprint("Ahoj,", jmeno) vypíše text a hodnotu proměnné; čárka je oddělí a print mezi ně vloží mezeru. jmeno bez uvozovek znamená proměnnou, "jmeno" v uvozovkách je doslovný text.',
        "predict": "Co vypíše ukázka? Co by se změnilo, kdybys v print() napsal místo jmeno výraz \"jmeno\"?",
        "task": 'Změň hodnotu proměnné jmeno na "Samantha". Příkaz print ponech tak, aby používal proměnnou.',
        "starter": 'jmeno = "Míla"\nprint("Ahoj,", jmeno)\n',
        "solution": 'jmeno = "Samantha"\nprint("Ahoj,", jmeno)\n',
        "hint": 'Uprav text napravo od =. Druhý řádek už proměnnou správně používá.',
        "success": "Změna uložené hodnoty změnila výpis. Podívej se také na záložku Proměnné.",
    },
    {
        "title": "Python počítá", "short": "3  Počítání", "time": "5–10 minut",
        "explain": "Čísla piš bez uvozovek, aby s nimi Python počítal. + sčítá, - odčítá, * násobí a / dělí.\n\ncelkem = pocet * cena spočítá součin aktuálních hodnot a výsledek uloží do celkem. Pokud později změníš pocet, musíš výpočet spustit znovu. Hodnota celkem se sama nepřepočítává jako vzorec v tabulce.",
        "predict": "Ukázka počítá tři vstupenky po 20 korunách. Jaký výsledek čekáš?",
        "task": "Změň počet vstupenek na 5, cenu ponech 20. Nech Python vypočítat a vypsat celkovou cenu.",
        "starter": "pocet = 3\ncena = 20\ncelkem = pocet * cena\nprint(celkem)\n",
        "solution": "pocet = 5\ncena = 20\ncelkem = pocet * cena\nprint(celkem)\n",
        "hint": "Stačí změnit hodnotu na prvním řádku. Výpočet ve třetím řádku použije nový počet.",
        "success": "Python vypočítal 5 × 20 = 100. Číslo celkem vzniklo výpočtem z proměnných.",
    },
    {
        "title": "Kód se mění v obrázek", "short": "4  První obrázek", "time": "10 minut",
        "explain": 'Pomocník kruh(x, y, polomer, barva) vykreslí kruh. Pořadí hodnot v závorkách je důležité. Barvu zadáváme jako text, například "modra".\n\nObrázek má souřadnice 500 × 360. Bod (0, 0) leží vlevo nahoře. x roste doprava, y dolů. Poloměr je vzdálenost od středu k okraji.\n\nkruh() jsem do učebny doplnila; není to vestavěný příkaz Pythonu. Vlastní pomocné funkce se naučíš tvořit v lekci 7.',
        "predict": "Kde bude střed kruhu? Co by se stalo při zvětšení x?",
        "task": 'Zvětši poloměr na 70 a změň barvu na "modra". Střed ponech na x = 250, y = 180.',
        "starter": 'polomer = 40\nkruh(250, 180, polomer, "oranzova")\n',
        "solution": 'polomer = 70\nkruh(250, 180, polomer, "modra")\n',
        "hint": 'Změň 40 na 70. Pak změň text "oranzova" na "modra". Názvy barev v kódu jsou bez diakritiky.',
        "success": "Dvě drobné změny kódu změnily velikost a barvu obrázku. Zkus pak posunout jeho střed.",
    },
    {
        "title": "Cyklus: opakování", "short": "5  Cykly", "time": "10–15 minut",
        "explain": "for opakuje odsazené řádky. range(3) postupně poskytne čísla 0, 1 a 2; každé se na chvíli přiřadí proměnné i.\n\nŘádek x = 50 + i * 85 tak postupně spočítá 50, 135 a 220. Kruh se pokaždé objeví o kus dál. Řádek s for končí dvojtečkou. Oba řádky uvnitř cyklu musí být odsazené stejně — používáme čtyři mezery.",
        "predict": "Kolik kruhů ukázka nakreslí? Jaká bude poslední hodnota i?",
        "task": "Uprav cyklus, aby nakreslil pět zelených kruhů místo tří. Ostatní hodnoty ponech.",
        "starter": 'for i in range(3):\n    x = 50 + i * 85\n    kruh(x, 180, 20, "zelena")\n',
        "solution": 'for i in range(5):\n    x = 50 + i * 85\n    kruh(x, 180, 20, "zelena")\n',
        "hint": "Změň číslo uvnitř range(). range(5) poskytne pět hodnot: 0, 1, 2, 3, 4.",
        "success": "Jeden cyklus nakreslil pět kruhů. Stejný postup využiješ při práci s mnoha soubory nebo záznamy.",
    },
    {
        "title": "Podmínka: rozhodování", "short": "6  Podmínky", "time": "10–15 minut",
        "explain": "if znamená „pokud“. Výraz teplota >= 20 ověří, zda je teplota alespoň 20. Je-li podmínka splněna, provede se první odsazený blok; jinak blok po else („jinak“).\n\nZa if i else patří dvojtečka. Odsazení určuje, které řádky patří do které větve. Další porovnání: > větší, < menší, == rovná se. Pozor: = přiřazuje, == porovnává.",
        "predict": "Která barva se objeví při teplotě 25? A která přesně při 20?",
        "task": "Nastav teplotu na 10 a ponech rozhodování pomocí if a else. Program má nakreslit modrý kruh a vypsat: Vezmi si bundu.",
        "starter": 'teplota = 25\nif teplota >= 20:\n    kruh(250, 180, 65, "zluta")\n    print("Je teplo.")\nelse:\n    kruh(250, 180, 65, "modra")\n    print("Vezmi si bundu.")\n',
        "solution": 'teplota = 10\nif teplota >= 20:\n    kruh(250, 180, 65, "zluta")\n    print("Je teplo.")\nelse:\n    kruh(250, 180, 65, "modra")\n    print("Vezmi si bundu.")\n',
        "hint": "Uprav pouze hodnotu proměnné teplota. Při 10 není podmínka >= 20 splněna, provede se tedy else.",
        "success": "Podmínka zvolila druhou větev. Vyzkoušej také hodnoty 19 a 20 a porovnej výsledky.",
    },
    {
        "title": "Vlastní funkce: semafory", "short": "7  Vlastní funkce", "time": "10–15 minut",
        "explain": 'def definuje vlastní funkci: pojmenuje postup, který lze opakovaně zavolat. Samotná definice ještě nic nenakreslí.\n\nParametr x je vstup funkce. Při volání semafor(150) uvnitř funkce používáme x = 150. obdelnik(x1, y1, x2, y2, barva) dostane levý horní a pravý dolní roh. Tři volání kruh() přidají světla.\n\nTady svítí všechny barvy jako názorný obrázek. Řízení skutečné signalizace by byl další úkol.',
        "predict": "Kolik semaforů vznikne při jediném volání semafor(150)? Co určuje číslo 150?",
        "task": "Zachovej funkci i první volání. Na konec přidej volání, které nakreslí druhý semafor se středem x = 350.",
        "starter": 'def semafor(x):\n    obdelnik(x - 40, 50, x + 40, 305, "cerna")\n    kruh(x, 100, 27, "cervena")\n    kruh(x, 180, 27, "zluta")\n    kruh(x, 260, 27, "zelena")\n\nsemafor(150)\n',
        "solution": 'def semafor(x):\n    obdelnik(x - 40, 50, x + 40, 305, "cerna")\n    kruh(x, 100, 27, "cervena")\n    kruh(x, 180, 27, "zluta")\n    kruh(x, 260, 27, "zelena")\n\nsemafor(150)\nsemafor(350)\n',
        "hint": "Na poslední řádek, bez odsazení, napiš semafor(350). Tím zavoláš stejný postup s jiným vstupem.",
        "success": "Máš vlastní funkci a použil jsi ji dvakrát! Příště můžeme přidat seznamy, tlačítka nebo malou hru. Zkus nejdřív vlastními slovy vysvětlit, co dělá parametr x.",
    },
]


def execute_code(source):
    """Spustí jeden studentský program. Volat v samostatném procesu."""
    commands = []

    class ShortOutput(io.StringIO):
        def write(self, value):
            if self.tell() + len(value) > 20000:
                raise ValueError("Výpis je příliš dlouhý. Zkus méně opakování.")
            return super().write(value)

    def color(value):
        if isinstance(value, str) and value in COLORS:
            return COLORS[value]
        if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            return value
        raise ValueError('Neznámá barva. Zkus "modra", "zelena", "cervena", "zluta" nebo "cerna".')

    def number(value):
        if not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 10000:
            raise ValueError("Souřadnice musí být konečné číslo mezi −10000 a 10000.")
        return value

    def add(kind, *values):
        if len(commands) >= 1000:
            raise ValueError("Najednou kreslíme nejvýše 1000 tvarů. Zmenši počet opakování.")
        commands.append([kind, *values])

    def kruh(x, y, polomer, barva="modra"):
        number(polomer)
        if not 0 < polomer <= 2000:
            raise ValueError("Poloměr musí být větší než 0 a nejvýše 2000.")
        add("circle", number(x), number(y), polomer, color(barva))

    def obdelnik(x1, y1, x2, y2, barva="modra"):
        add("rect", number(x1), number(y1), number(x2), number(y2), color(barva))

    def cara(x1, y1, x2, y2, barva="cerna"):
        add("line", number(x1), number(y1), number(x2), number(y2), color(barva))

    def napis(x, y, text, barva="cerna"):
        add("text", number(x), number(y), str(text)[:300], color(barva))

    def pozadi(barva="bila"):
        add("background", color(barva))

    def input_unavailable(*args):
        raise ValueError("input() tato učebna zatím nepodporuje. Napiš hodnotu přímo do proměnné v editoru.")

    env = {"__name__": "__main__", "kruh": kruh, "obdelnik": obdelnik,
           "cara": cara, "napis": napis, "pozadi": pozadi, "input": input_unavailable}
    output = ShortOutput()
    error = None
    original_out, original_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = output
    try:
        exec(compile(source, "<tvoje lekce>", "exec"), env, env)
    except BaseException as exc:
        frames = traceback.extract_tb(exc.__traceback__)
        line = getattr(exc, "lineno", None)
        for frame in frames:
            if frame.filename == "<tvoje lekce>":
                line = frame.lineno
        tips = {
            "SyntaxError": "Zkontroluj uvozovky, závorky a dvojtečky. Python nerozumí zápisu tohoto řádku.",
            "IndentationError": "Zkontroluj odsazení. Uvnitř if, for nebo def používej čtyři mezery.",
            "TabError": "Nemíchej tabulátory s mezerami. Odsazuj čtyřmi mezerami.",
            "NameError": "Python nezná toto jméno. Zkontroluj překlep a zda proměnná dostala hodnotu před použitím.",
            "TypeError": "Některá hodnota má nevhodný typ nebo funkce dostala nesprávný počet vstupů. Zkontroluj čísla, texty a argumenty.",
            "ZeroDivisionError": "Nulou nelze dělit. Zkontroluj hodnotu za lomítkem.",
            "ValueError": "Zkontroluj hodnoty, které předáváš příkazu. Podrobnost je níže.",
            "SystemExit": "Program se ukončil příkazem exit() nebo sys.exit().",
        }
        name = type(exc).__name__
        error = {"type": name, "line": line,
                 "tip": tips.get(name, "Podívej se na označený řádek a podrobnost chyby."),
                 "detail": str(exc)[:600]}
    finally:
        sys.stdout, sys.stderr = original_out, original_err
    variables = {}
    for name, value in list(env.items()):
        if name.startswith("_") or name in ("kruh", "obdelnik", "cara", "napis", "pozadi", "input"):
            continue
        if value is None or type(value) in (str, int, float, bool):
            try:
                if isinstance(value, str):
                    variables[name] = value[:1000]
                elif type(value) is int and value.bit_length() > 3000:
                    variables[name] = "(velmi velké celé číslo)"
                elif type(value) is float and not math.isfinite(value):
                    variables[name] = str(value)
                else:
                    variables[name] = value
            except Exception:
                pass
    return {"output": output.getvalue(), "commands": commands, "variables": variables, "error": error}


def run_code(source, timeout=3):
    """Timeout se týká vlastního běhu v odděleném procesu, GUI zůstává aktivní."""
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--worker"],
            input=json.dumps({"source": source}, ensure_ascii=False),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
            timeout=timeout, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Proces skončil před dokončením výsledku.")
        data = json.loads(result.stdout)
        if not isinstance(data, dict) or not all(k in data for k in ("error", "output", "commands", "variables")):
            raise ValueError("Neplatný výsledek programu.")
        return data
    except subprocess.TimeoutExpired:
        return {"output": "", "commands": [], "variables": {},
                "error": {"type": "Časový limit", "line": None,
                          "tip": "Program běžel déle než 3 sekundy a zastavila jsem ho. Zkontroluj, zda se cyklus může ukončit.", "detail": ""}}
    except (OSError, ValueError, RuntimeError) as exc:
        return {"output": "", "commands": [], "variables": {},
                "error": {"type": "Spuštění", "line": None,
                          "tip": "Program se nepodařilo dokončit. Zkus vrátit zadání a spustit ukázku.", "detail": str(exc)[:600]}}


def assess(index, source, result):
    """Kontrola výsledku a probíraného konstruktu; nejde o obecného AI hodnotitele."""
    if result["error"]:
        return False, "Nejdřív oprav chybu, kterou najdeš v záložce Výpis."
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    has = lambda kind: any(isinstance(n, kind) for n in nodes)
    uses = lambda name: any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id == name for n in nodes)
    variables, commands = result["variables"], result["commands"]
    lines = result["output"].strip().splitlines()
    expected_circles = [["circle", 50 + i * 85, 180, 20, COLORS["zelena"]] for i in range(5)]
    checks = [
        lambda: lines == ["Ahoj, Mílo!", "Učím se Python."],
        lambda: variables.get("jmeno") == "Samantha" and uses("jmeno") and lines == ["Ahoj, Samantha"],
        lambda: variables.get("pocet") == 5 and variables.get("cena") == 20 and variables.get("celkem") == 100 and has(ast.Mult) and uses("pocet") and uses("cena") and lines == ["100"],
        lambda: commands == [["circle", 250, 180, 70, COLORS["modra"]]],
        lambda: has(ast.For) and commands == expected_circles,
        lambda: variables.get("teplota") == 10 and has(ast.If) and lines == ["Vezmi si bundu."] and commands == [["circle", 250, 180, 65, COLORS["modra"]]],
        lambda: has(ast.FunctionDef) and commands == execute_code(LESSONS[6]["solution"])["commands"],
    ]
    if checks[index]():
        return True, LESSONS[index]["success"]
    feedback = [
        "Očekávám dva řádky: Ahoj, Mílo! a Učím se Python. Zkontroluj i tečku a diakritiku.",
        'Proměnná jmeno má obsahovat "Samantha" a výpis má být Ahoj, Samantha. Použij jmeno v příkazu print().',
        "Zkontroluj pocet = 5, cena = 20 a výpočet celkem pomocí násobení proměnných. Výpis má být 100.",
        'Očekávám jeden kruh se středem (250, 180), poloměrem 70 a barvou "modra".',
        "Použij cyklus for pro pět zelených kruhů. Ponech x = 50 + i * 85, y = 180 a poloměr 20.",
        "Nastav teplota = 10 a ponech if/else. Očekávám modrý kruh a výpis Vezmi si bundu.",
        "Očekávám původní funkci a dva semafory: semafor(150) a semafor(350). Volání piš bez odsazení.",
    ]
    return False, feedback[index]


def read_state(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}, "Soubor s postupem měl neplatný obsah; otevírám nové zadání."
        return data, ""
    except FileNotFoundError:
        return {}, ""
    except (OSError, ValueError):
        return {}, "Postup se nepodařilo načíst; otevírám nové zadání."


def save_state(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def launch():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        from tkinter.scrolledtext import ScrolledText
        import tkinter.font as tkfont
    except ImportError:
        print("Chybí Tkinter. V Linux Mintu nainstaluj balíček python3-tk:")
        print("sudo apt install python3-tk")
        return 1

    class Classroom:
        def __init__(self, root):
            self.root = root
            self.root.title("Python se Samanthou · první kroky")
            width = min(1220, max(900, root.winfo_screenwidth() - 60))
            height = min(870, max(640, root.winfo_screenheight() - 100))
            root.geometry(f"{width}x{height}")
            root.minsize(900, 640)
            root.configure(bg="#edf2f7")
            self.path = Path.home() / ".python_se_samanthou" / "prubeh.json"
            state, warning = read_state(self.path)
            drafts = state.get("drafts", {})
            self.drafts = {k: v for k, v in drafts.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(drafts, dict) else {}
            completed = state.get("completed", [])
            self.completed = {x for x in completed if type(x) is int and 0 <= x < len(LESSONS)} if isinstance(completed, list) else set()
            self.current = -1
            self.loading = False
            self.busy = False
            self.queue = queue.Queue()
            self.save_after = None
            self.highlight_after = None
            self.drawing = []
            self.check_pending = False
            self.base_size = 12
            families = set(tkfont.families())
            mono = "DejaVu Sans Mono" if "DejaVu Sans Mono" in families else "Courier"
            self.font = tkfont.Font(family="DejaVu Sans" if "DejaVu Sans" in families else "Arial", size=12)
            self.bold = self.font.copy()
            self.bold.configure(weight="bold")
            self.code_font = tkfont.Font(family=mono, size=13)
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")
            style.configure("TFrame", background="#edf2f7")
            style.configure("TLabel", background="#edf2f7", foreground="#25334b", font=self.font)
            style.configure("TButton", font=self.font, padding=(10, 7))
            style.configure("Accent.TButton", background="#1d776e", foreground="white")
            style.map("Accent.TButton", background=[("active", "#24665f"), ("disabled", "#a7b4bd")])
            style.configure("TNotebook.Tab", font=self.font, padding=(12, 6))

            header = ttk.Frame(root, padding=(18, 10))
            header.pack(fill="x")
            ttk.Label(header, text="Python se Samanthou", font=(self.font.actual("family"), 22, "bold")).pack(side="left")
            ttk.Button(header, text="A+", width=3, command=lambda: self.resize_font(1)).pack(side="right")
            ttk.Button(header, text="A−", width=3, command=lambda: self.resize_font(-1)).pack(side="right", padx=5)
            ttk.Label(root, text="Odhadni výsledek → spusť ukázku → uprav kód → ověř úkol", padding=(20, 0, 20, 10)).pack(anchor="w")

            body = ttk.Frame(root, padding=(12, 0, 12, 8))
            body.pack(fill="both", expand=True)
            sidebar = ttk.Frame(body, width=200)
            sidebar.pack(side="left", fill="y", padx=(0, 12))
            ttk.Label(sidebar, text="TVÉ LEKCE", font=self.bold).pack(anchor="w", pady=(6, 8))
            self.listbox = tk.Listbox(sidebar, font=self.font, width=21, height=9, bd=0, highlightthickness=0,
                                      activestyle="none", exportselection=False, bg="#f8fafc", fg="#25334b",
                                      selectbackground="#1d776e", selectforeground="white")
            self.listbox.pack(fill="x")
            self.listbox.bind("<<ListboxSelect>>", self.select_lesson)
            self.progress = ttk.Label(sidebar, text="", padding=(0, 8))
            self.progress.pack(anchor="w")
            self.next_button = ttk.Button(sidebar, text="Další lekce →", command=self.next_lesson)
            self.next_button.pack(fill="x", pady=(4, 15))
            ttk.Button(sidebar, text="Nápověda", command=self.show_hint).pack(fill="x", pady=3)
            ttk.Button(sidebar, text="Ukázat řešení", command=self.show_solution).pack(fill="x", pady=3)
            ttk.Button(sidebar, text="Vrátit zadání", command=self.reset).pack(fill="x", pady=3)
            ttk.Button(sidebar, text="Jak začít / kreslení", command=self.help).pack(fill="x", pady=3)
            ttk.Label(sidebar, text="Stačí jedna lekce.\n\nChyba je informace.\nUprav jeden detail\na zkus to znovu.", wraplength=190).pack(anchor="w", pady=18)

            main = ttk.Panedwindow(body, orient="vertical")
            main.pack(fill="both", expand=True)
            info_frame = ttk.Frame(main)
            self.info = ScrolledText(info_frame, height=11, wrap="word", font=self.font,
                                     bg="#ffffff", fg="#26354d", relief="flat", padx=15, pady=12)
            self.info.pack(fill="both", expand=True)
            self.info.tag_configure("heading", font=self.bold, foreground="#17675f", spacing1=7, spacing3=4)
            main.add(info_frame, weight=2)

            lower = ttk.Frame(main)
            main.add(lower, weight=3)
            actions = ttk.Frame(lower, padding=(0, 8))
            actions.pack(fill="x")
            self.run_button = ttk.Button(actions, text="Spustit (F5)", command=self.run)
            self.run_button.pack(side="left")
            self.check_button = ttk.Button(actions, text="Ověřit úkol", style="Accent.TButton", command=lambda: self.run(True))
            self.check_button.pack(side="left", padx=8)
            self.running_label = ttk.Label(actions, text="")
            self.running_label.pack(side="left")

            split = ttk.Panedwindow(lower, orient="horizontal")
            split.pack(fill="both", expand=True)
            left = ttk.Frame(split)
            ttk.Label(left, text="TVŮJ KÓD", font=self.bold, padding=(0, 0, 0, 5)).pack(anchor="w")
            self.editor = ScrolledText(left, wrap="none", font=self.code_font, undo=True, width=32,
                                       height=11, bg="#152238", fg="#e4edf7", insertbackground="white",
                                       selectbackground="#365570", padx=12, pady=12, relief="flat")
            self.editor.pack(fill="both", expand=True)
            self.editor.tag_configure("keyword", foreground="#c7abff")
            self.editor.tag_configure("string", foreground="#90d6ac")
            self.editor.tag_configure("number", foreground="#f8ce75")
            self.editor.tag_configure("comment", foreground="#9cacc4")
            self.editor.tag_configure("error", background="#733744")
            self.editor.bind("<<Modified>>", self.modified)
            self.editor.bind("<Tab>", self.tab)
            self.editor.bind("<Return>", self.newline)
            self.editor.bind("<Control-Return>", lambda event: self.run_key())
            root.bind("<F5>", lambda event: self.run_key())
            split.add(left, weight=1)

            self.tabs = ttk.Notebook(split)
            self.console = ScrolledText(self.tabs, font=self.code_font, wrap="word", width=31, height=10,
                                       bg="#ffffff", fg="#26354d", relief="flat", padx=12, pady=12, state="disabled")
            graphic_frame = ttk.Frame(self.tabs)
            self.canvas = tk.Canvas(graphic_frame, bg="#f8fafc", width=360, height=260, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.bind("<Configure>", lambda event: self.draw())
            self.variables = ScrolledText(self.tabs, font=self.code_font, wrap="word", width=31, height=10,
                                         bg="#ffffff", relief="flat", padx=12, pady=12, state="disabled")
            self.tabs.add(self.console, text="Výpis")
            self.tabs.add(graphic_frame, text="Obrázek")
            self.tabs.add(self.variables, text="Proměnné")
            split.add(self.tabs, weight=1)

            self.feedback = tk.Label(root, text="", bg="#e0ece9", fg="#1f4c47", font=self.font,
                                     anchor="w", justify="left", padx=16, pady=10)
            self.feedback.pack(fill="x", padx=12, pady=(2, 0))
            self.feedback.bind("<Configure>", lambda event: self.feedback.configure(wraplength=max(300, event.width - 32)))
            self.saved = ttk.Label(root, text="Postup se ukládá automaticky.", padding=(16, 4))
            self.saved.pack(anchor="w")
            selected = state.get("current", 0)
            self.refresh_list()
            self.load(selected if type(selected) is int and 0 <= selected < len(LESSONS) else 0)
            if warning:
                self.saved.configure(text=warning)
            root.protocol("WM_DELETE_WINDOW", self.close)
            root.after(100, self.poll)

        def resize_font(self, delta):
            self.base_size = min(18, max(10, self.base_size + delta))
            self.font.configure(size=self.base_size)
            self.bold.configure(size=self.base_size)
            self.code_font.configure(size=self.base_size + 1)

        def refresh_list(self):
            self.listbox.delete(0, "end")
            for i, lesson in enumerate(LESSONS):
                self.listbox.insert("end", ("✓ " if i in self.completed else "  ") + lesson["short"])
            if self.current >= 0:
                self.listbox.selection_set(self.current)
            self.progress.configure(text=f"Dokončeno {len(self.completed)} / {len(LESSONS)}")

        def select_lesson(self, event=None):
            selection = self.listbox.curselection()
            if selection and selection[0] != self.current:
                if self.busy:
                    self.listbox.selection_clear(0, "end")
                    self.listbox.selection_set(self.current)
                    return
                self.load(selection[0])

        def load(self, index):
            if self.current >= 0:
                self.drafts[str(self.current)] = self.editor.get("1.0", "end-1c")
            self.current = index
            lesson = LESSONS[index]
            self.loading = True
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", self.drafts.get(str(index), lesson["starter"]))
            self.editor.edit_reset()
            self.editor.edit_modified(False)
            self.loading = False
            self.highlight()
            self.info.configure(state="normal")
            self.info.delete("1.0", "end")
            for title, paragraph in [
                (f"{index + 1}. {lesson['title']} · {lesson['time']}", lesson["explain"]),
                ("NEJDŘÍV ODHADNI", lesson["predict"]), ("TVŮJ ÚKOL", lesson["task"]),
            ]:
                self.info.insert("end", title + "\n", "heading")
                self.info.insert("end", paragraph + "\n\n")
            self.info.configure(state="disabled")
            self.info.yview_moveto(0)
            self.set_text(self.console, "Tady se objeví výpis programu.\n\nNejprve odhadni výsledek, pak klikni na Spustit.")
            self.set_text(self.variables, "Po spuštění uvidíš konečné hodnoty jednoduchých proměnných (čísla, texty, ano/ne).")
            self.drawing = []
            self.draw()
            self.tabs.select(0)
            self.feedback.configure(text="Přečti vysvětlení a úkol nahoře. Text lze posouvat kolečkem myši.", bg="#e0ece9", fg="#1f4c47")
            self.next_button.configure(state="normal" if index < len(LESSONS) - 1 else "disabled")
            self.refresh_list()
            self.save()

        @staticmethod
        def set_text(widget, text):
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", text)
            widget.configure(state="disabled")

        def modified(self, event=None):
            if not self.editor.edit_modified():
                return
            self.editor.edit_modified(False)
            if self.loading:
                return
            self.editor.tag_remove("error", "1.0", "end")
            if self.highlight_after:
                self.root.after_cancel(self.highlight_after)
            self.highlight_after = self.root.after(180, self.highlight)
            if self.save_after:
                self.root.after_cancel(self.save_after)
            self.saved.configure(text="Ukládám rozepsaný kód…")
            self.save_after = self.root.after(700, self.save)

        def highlight(self):
            self.highlight_after = None
            for tag in ("keyword", "string", "number", "comment"):
                self.editor.tag_remove(tag, "1.0", "end")
            try:
                for token in tokenize.generate_tokens(io.StringIO(self.editor.get("1.0", "end-1c")).readline):
                    tag = {tokenize.STRING: "string", tokenize.NUMBER: "number", tokenize.COMMENT: "comment"}.get(token.type)
                    if token.type == tokenize.NAME and keyword.iskeyword(token.string):
                        tag = "keyword"
                    if tag:
                        self.editor.tag_add(tag, f"{token.start[0]}.{token.start[1]}", f"{token.end[0]}.{token.end[1]}")
            except (tokenize.TokenError, SyntaxError):
                pass

        def tab(self, event):
            try:
                self.editor.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            self.editor.insert("insert", "    ")
            return "break"

        def newline(self, event):
            try:
                self.editor.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            prefix = self.editor.get("insert linestart", "insert")
            indent = re.match(r" *", prefix).group()
            if prefix.rstrip().endswith(":"):
                indent += "    "
            self.editor.insert("insert", "\n" + indent)
            self.editor.see("insert")
            return "break"

        def save(self):
            self.save_after = None
            if self.current < 0:
                return
            self.drafts[str(self.current)] = self.editor.get("1.0", "end-1c")
            try:
                save_state(self.path, {"version": 1, "current": self.current, "completed": sorted(self.completed), "drafts": self.drafts})
                self.saved.configure(text="Rozepsané lekce a postup jsou uloženy na tomto počítači.")
            except OSError:
                self.saved.configure(text="Postup se nepodařilo uložit. Před zavřením si zkopíruj rozepsaný kód.")

        def run_key(self):
            self.run()
            return "break"

        def run(self, check=False):
            if self.busy:
                return
            source = self.editor.get("1.0", "end-1c")
            if len(source) > 50000:
                messagebox.showinfo("Příliš dlouhý kód", "Pro začátek používej programy do 50 000 znaků.")
                return
            self.busy = True
            self.run_button.configure(state="disabled")
            self.check_button.configure(state="disabled")
            self.running_label.configure(text="Běží…")
            self.editor.tag_remove("error", "1.0", "end")
            self.save()
            def work():
                self.queue.put((self.current, source, check, run_code(source)))
            threading.Thread(target=work, daemon=True).start()

        def poll(self):
            try:
                index, source, check, result = self.queue.get_nowait()
            except queue.Empty:
                pass
            else:
                self.busy = False
                self.run_button.configure(state="normal")
                self.check_button.configure(state="normal")
                self.running_label.configure(text="")
                self.show_result(index, source, check, result)
            self.root.after(100, self.poll)

        def show_result(self, index, source, check, result):
            error = result["error"]
            text = result["output"] or "Program nic nevypsal. Výpis vzniká příkazem print().\n"
            unchanged = source == self.editor.get("1.0", "end-1c") and index == self.current
            if error:
                line = f" na řádku {error['line']}" if error["line"] else ""
                text += f"\n\n{error['type']}{line}\n{error['tip']}\n\nPodrobnost: {error['detail']}"
                if error["line"] and unchanged:
                    self.editor.tag_add("error", f"{error['line']}.0", f"{error['line']}.end")
                    self.editor.see(f"{error['line']}.0")
            self.set_text(self.console, text)
            variable_text = "\n\n".join(f"{key} = {value!r}" for key, value in result["variables"].items())
            self.set_text(self.variables, variable_text or "Zatím žádné jednoduché proměnné.\n\nZde se ukazují konečné hodnoty čísel, textů a logických hodnot; funkce a seznamy se v této verzi nezobrazují.")
            self.drawing = result["commands"]
            self.draw()
            self.tabs.select(0 if error or not self.drawing else 1)
            if not unchanged:
                self.feedback.configure(text="Výsledek patří ke kódu před poslední úpravou. Spusť upravený kód znovu.", bg="#fff0d7", fg="#694918")
            elif error:
                self.feedback.configure(text="Podívej se na vysvětlení chyby v záložce Výpis. Oprav jednu věc a zkus Spustit znovu.", bg="#fff0d7", fg="#694918")
            elif check:
                passed, feedback = assess(index, source, result)
                self.feedback.configure(text=("Splněno! " if passed else "Ještě drobná úprava: ") + feedback,
                                        bg="#dcefe6" if passed else "#fff0d7", fg="#1f5542" if passed else "#694918")
                if passed:
                    self.completed.add(index)
                    self.refresh_list()
                    self.save()
            else:
                self.feedback.configure(text="Program doběhl. Porovnej výsledek se svým odhadem, uprav kód podle úkolu a klikni na Ověřit úkol.", bg="#e0ece9", fg="#1f4c47")

        def draw(self):
            canvas = self.canvas
            canvas.delete("all")
            w, h = max(canvas.winfo_width(), 10), max(canvas.winfo_height(), 10)
            scale = max(0.01, min((w - 24) / 500, (h - 24) / 360))
            ox, oy = (w - 500 * scale) / 2, (h - 360 * scale) / 2
            point = lambda x, y: (ox + x * scale, oy + y * scale)
            canvas.create_rectangle(*point(0, 0), *point(500, 360), fill="white", outline="#cdd7e2", tags="page")
            for x in range(0, 501, 50):
                canvas.create_line(*point(x, 0), *point(x, 360), fill="#edf1f5", tags="grid")
            for y in range(0, 361, 50):
                canvas.create_line(*point(0, y), *point(500, y), fill="#edf1f5", tags="grid")
            canvas.create_text(*point(8, 8), text="(0, 0)", anchor="nw", fill="#7b8ba2", font=(self.font.actual("family"), 9), tags="grid")
            canvas.create_text(*point(492, 352), text="(500, 360)", anchor="se", fill="#7b8ba2", font=(self.font.actual("family"), 9), tags="grid")
            for item in self.drawing:
                kind, *a = item
                if kind == "background":
                    canvas.itemconfigure("page", fill=a[0])
                    canvas.delete("grid")
                elif kind == "circle":
                    x, y, radius, color = a
                    canvas.create_oval(*point(x - radius, y - radius), *point(x + radius, y + radius), fill=color, outline="")
                elif kind == "rect":
                    x1, y1, x2, y2, color = a
                    canvas.create_rectangle(*point(x1, y1), *point(x2, y2), fill=color, outline="")
                elif kind == "line":
                    x1, y1, x2, y2, color = a
                    canvas.create_line(*point(x1, y1), *point(x2, y2), fill=color, width=max(1, 3 * scale))
                elif kind == "text":
                    x, y, text, color = a
                    canvas.create_text(*point(x, y), text=text, fill=color, font=(self.font.actual("family"), max(8, int(16 * scale))))

        def next_lesson(self):
            if not self.busy and self.current < len(LESSONS) - 1:
                self.load(self.current + 1)

        def show_hint(self):
            messagebox.showinfo("Malá nápověda", LESSONS[self.current]["hint"])

        def show_solution(self):
            dialog = tk.Toplevel(self.root)
            dialog.title("Vzorové řešení")
            dialog.geometry("650x450")
            ttk.Label(dialog, text="Přečti si řešení. Potom okno zavři a zkus ho napsat vlastními silami.", wraplength=600, padding=14).pack(fill="x")
            view = ScrolledText(dialog, font=self.code_font, wrap="none", padx=12, pady=12)
            view.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            self.set_text(view, LESSONS[self.current]["solution"])
            ttk.Button(dialog, text="Zavřít", command=dialog.destroy).pack(pady=(0, 12))

        def reset(self):
            if self.busy:
                return
            if messagebox.askyesno("Vrátit zadání", "Nahradit rozepsaný kód této lekce původní ukázkou?"):
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", LESSONS[self.current]["starter"])
                self.save()

        def help(self):
            dialog = tk.Toplevel(self.root)
            dialog.title("Jak začít a jak kreslit")
            dialog.geometry("720x560")
            text = ScrolledText(dialog, wrap="word", font=self.font, padx=18, pady=18)
            text.pack(fill="both", expand=True)
            self.set_text(text, __doc__ + '\n\nKRESLENÍ\n\n'
                          'kruh(x, y, polomer, barva)\nStřed, poloměr a barva kruhu.\n\n'
                          'obdelnik(x1, y1, x2, y2, barva)\nSouřadnice dvou protilehlých rohů.\n\n'
                          'cara(x1, y1, x2, y2, barva)\nÚsečka mezi dvěma body.\n\n'
                          'napis(x, y, "text", barva)\nText se středem v bodě (x, y).\n\n'
                          'pozadi(barva)\nZmění barvu podkladu a skryje mřížku; už nakreslené tvary ponechá.\n\n'
                          'Barvy: ' + ', '.join(COLORS) + '. Názvy jsou v kódu v uvozovkách a bez diakritiky. Lze použít také hexadecimální barvu, například "#ff8800".\n\n'
                          'Souřadnice: x = 0 až 500 zleva doprava, y = 0 až 360 shora dolů. Obrázek se automaticky přizpůsobí velikosti okna.\n\n'
                          'Každé spuštění začíná znovu: čisté proměnné, čistý obrázek. Záložka Proměnné ukazuje stav po skončení programu, ne průběh jednotlivých kroků.\n\n'
                          'Kontrola úkolu ověřuje vybrané výsledky a konstrukce. Další správné varianty mimo přesné zadání nemusí rozpoznat. Učení pokračuje i experimentováním mimo zadání.\n')

        def close(self):
            self.save()
            self.root.destroy()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Grafické okno se nepodařilo otevřít. Spusť program na počítači v grafické ploše.")
        print(str(exc))
        return 1
    Classroom(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    if "--worker" in sys.argv:
        request = json.load(sys.stdin)
        print(json.dumps(execute_code(request["source"]), ensure_ascii=False))
    else:
        raise SystemExit(launch())
