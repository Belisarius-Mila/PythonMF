#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python se Samanthou — offline učebna, verze 1.4.

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
~/.python_se_samanthou/prubeh_v2.json; aplikace nic neodesílá.
Původní prubeh.json se při prvním spuštění převede a zůstane zachovaný.
Balíček vyber vlevo nahoře. Každý má vlastní lekce a uložený postup.
Další balíček přidej jako složku do kurzy a učebnu znovu otevři.
Moje dílna nahoře otevírá vlastní pojmenované pokusy; ukládají se do
~/.python_se_samanthou/dilna.json. Kopii kódu z lekce přeneseš tlačítkem Do dílny.

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

import argparse
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

# The isolated Python worker (-I) also needs these bundled modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from assessment import assess_lesson
from course_loader import DEFAULT_COURSE, CourseError, discover_courses, load_course
from progress_store import ProgressError, ProgressStore
from drawing import draw_commands

COURSE = None
LESSONS = []


COLORS = {
    "modra": "#3287db", "zelena": "#2cb67d", "cervena": "#ef5b64",
    "zluta": "#f5c84c", "bila": "#ffffff", "cerna": "#202b3c",
    "oranzova": "#f69a48", "fialova": "#9b7ce0", "seda": "#7b8ba2",
}



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
            env={k: v for k, v in os.environ.items() if k not in {"OPENAI_API_KEY", "CODEX_API_KEY"}},
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
    return assess_lesson(LESSONS[index], source, result)


def launch(state_dir=None, on_ready=None):
    global COURSE, LESSONS
    if COURSE is None:
        COURSE = load_course()
        LESSONS = COURSE['lessons']
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
            self.root.title(f"Python se Samanthou · {COURSE['title']}")
            installed, package_warnings = discover_courses()
            self.courses = [COURSE] + [c for c in installed if c['id'] != COURSE['id']]
            self.course_index = 0
            self.workshop = None
            width = min(1220, max(900, root.winfo_screenwidth() - 60))
            height = min(870, max(640, root.winfo_screenheight() - 100))
            root.geometry(f"{width}x{height}")
            root.minsize(900, 640)
            root.configure(bg="#edf2f7")
            self.store = ProgressStore(state_dir)
            try:
                self.state, warning = self.store.load()
            except (OSError, ProgressError) as exc:
                self.state = {'version': 2, 'courses': {}}
                warning = f"Postup se nepodařilo načíst: {exc} Ukládání je zastavené."
            state = self.state['courses'].get(COURSE['id'], {})
            self.drafts = dict(state.get('drafts', {}))
            self.completed = set(state.get('completed', []))
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
            ttk.Label(header, text="Python se Samanthou · 1.4", font=(self.font.actual("family"), 22, "bold")).pack(side="left")
            ttk.Button(header, text="Moje dílna", command=self.open_workshop).pack(side="left", padx=16)
            ttk.Button(header, text="A+", width=3, command=lambda: self.resize_font(1)).pack(side="right")
            ttk.Button(header, text="A−", width=3, command=lambda: self.resize_font(-1)).pack(side="right", padx=5)
            ttk.Label(root, text="Odhadni výsledek → spusť ukázku → uprav kód → ověř úkol", padding=(20, 0, 20, 10)).pack(anchor="w")

            body = ttk.Frame(root, padding=(12, 0, 12, 8))
            body.pack(fill="both", expand=True)
            sidebar = ttk.Frame(body, width=200)
            sidebar.pack(side="left", fill="y", padx=(0, 12))
            ttk.Label(sidebar, text="BALÍČEK LEKCÍ", font=self.bold).pack(anchor="w", pady=(6, 4))
            self.course_picker = ttk.Combobox(sidebar, state="readonly", width=23,
                                               values=[c['title'] for c in self.courses])
            self.course_picker.current(0)
            self.course_picker.pack(fill="x", pady=(0, 8))
            self.course_picker.bind("<<ComboboxSelected>>", self.select_course)
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
            ttk.Button(actions, text="Do dílny", command=lambda: self.open_workshop(copy_lesson=True)).pack(side="left", padx=(0, 8))
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
            selected = next((i for i, lesson in enumerate(LESSONS) if lesson["id"] == state.get("current")), 0)
            self.refresh_list()
            self.load(selected if type(selected) is int and 0 <= selected < len(LESSONS) else 0)
            if warning:
                self.saved.configure(text=warning)
            if package_warnings:
                root.after(0, lambda: messagebox.showwarning("Některé balíčky nelze otevřít", "\n\n".join(package_warnings)))
            root.protocol("WM_DELETE_WINDOW", self.close)
            root.after(100, self.poll)

        def open_workshop(self, copy_lesson=False):
            from workshop import WorkshopWindow
            if copy_lesson and (self.busy or not self.save()):
                return
            if self.workshop is None or not self.workshop.window.winfo_exists():
                try:
                    self.workshop = WorkshopWindow(self.root, self.store.directory, run_code)
                except (OSError, ValueError) as exc:
                    messagebox.showerror("Dílnu nelze otevřít", str(exc))
                    return
            self.workshop.window.deiconify()
            self.workshop.window.lift()
            self.workshop.window.after_idle(self.workshop.edit_code)
            if copy_lesson:
                self.workshop.create_experiment(
                    (LESSONS[self.current]['title'] + ' — můj pokus')[:80],
                    self.editor.get('1.0', 'end-1c'),
                    'Kopie z lekce: ' + LESSONS[self.current]['title'])

        def select_course(self, event=None):
            global COURSE, LESSONS
            selected = self.course_picker.current()
            if selected < 0 or selected == self.course_index:
                return
            if self.busy or not self.save():
                self.course_picker.current(self.course_index)
                return
            if self.highlight_after is not None:
                self.root.after_cancel(self.highlight_after)
                self.highlight_after = None
            self.course_index = selected
            COURSE = self.courses[selected]
            LESSONS = COURSE['lessons']
            state = self.state['courses'].get(COURSE['id'], {})
            self.drafts = dict(state.get('drafts', {}))
            self.completed = set(state.get('completed', []))
            self.current = -1
            self.root.title(f"Python se Samanthou · {COURSE['title']}")
            index = next((i for i, lesson in enumerate(LESSONS) if lesson['id'] == state.get('current')), 0)
            self.load(index)

        def resize_font(self, delta):
            self.base_size = min(18, max(10, self.base_size + delta))
            self.font.configure(size=self.base_size)
            self.bold.configure(size=self.base_size)
            self.code_font.configure(size=self.base_size + 1)

        def refresh_list(self):
            self.listbox.delete(0, "end")
            for i, lesson in enumerate(LESSONS):
                self.listbox.insert("end", ("✓ " if lesson["id"] in self.completed else "  ") + f"{i + 1}  {lesson['short']}")
            if self.current >= 0:
                self.listbox.selection_set(self.current)
                self.listbox.see(self.current)
            done = sum(lesson["id"] in self.completed for lesson in LESSONS)
            self.progress.configure(text=f"Dokončeno {done} / {len(LESSONS)}")

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
                self.drafts[LESSONS[self.current]["id"]] = self.editor.get("1.0", "end-1c")
            self.current = index
            lesson = LESSONS[index]
            self.loading = True
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", self.drafts.get(lesson["id"], lesson["starter"]))
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
            if self.save_after is not None:
                self.root.after_cancel(self.save_after)
                self.save_after = None
            if self.current < 0:
                return True
            lesson_id = LESSONS[self.current]['id']
            self.drafts[lesson_id] = self.editor.get("1.0", "end-1c")
            state = self.state['courses'].setdefault(COURSE['id'], {})
            state.update(current=lesson_id, completed=sorted(self.completed), drafts=self.drafts)
            try:
                self.store.save(self.state)
                self.saved.configure(text="Rozepsané lekce a postup jsou uloženy na tomto počítači.")
                return True
            except (OSError, ValueError) as exc:
                self.saved.configure(text=f"Postup není uložen: {exc}")
                return False

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
                    self.completed.add(LESSONS[index]["id"])
                    self.refresh_list()
                    self.save()
            else:
                self.feedback.configure(text="Program doběhl. Porovnej výsledek se svým odhadem, uprav kód podle úkolu a klikni na Ověřit úkol.", bg="#e0ece9", fg="#1f4c47")

        def draw(self):
            draw_commands(self.canvas, self.drawing, self.font.actual("family"))

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
            if self.workshop is not None and self.workshop.window.winfo_exists():
                if not self.workshop.close():
                    return
            if not self.save() and not messagebox.askyesno(
                    "Postup není uložen", "Zavřít bez uložení? Nejdřív si zkopíruj rozepsaný kód."):
                return
            self.root.destroy()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Grafické okno se nepodařilo otevřít. Spusť program na počítači v grafické ploše.")
        print(str(exc))
        return 1
    classroom = Classroom(root)
    if on_ready is not None:
        root.after(0, lambda: on_ready(classroom))
    root.mainloop()
    return 0


def main(argv=None):
    global COURSE, LESSONS
    parser = argparse.ArgumentParser(description="Python se Samanthou — offline učebna")
    parser.add_argument('--course', type=Path, default=DEFAULT_COURSE, help="Soubor kurz.json")
    parser.add_argument('--state-dir', type=Path, help="Vlastní složka pro ukládání postupu")
    parser.add_argument('--check-course', action='store_true', help="Zkontrolovat balíček bez spuštění ukázek a GUI")
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        request = json.load(sys.stdin)
        print(json.dumps(execute_code(request['source']), ensure_ascii=False))
        return 0
    try:
        COURSE = load_course(args.course)
    except CourseError as exc:
        print(f"Kurz nelze otevřít: {exc}", file=sys.stderr)
        return 1
    LESSONS = COURSE['lessons']
    if args.check_course:
        print(f"Kurz v pořádku: {COURSE['title']} — {len(LESSONS)} lekcí.")
        return 0
    return launch(args.state_dir)


if __name__ == '__main__':
    raise SystemExit(main())
