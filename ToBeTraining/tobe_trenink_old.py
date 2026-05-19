import csv
import random
import tkinter as tk
from tkinter import messagebox
import subprocess
from pathlib import Path
import re

def speak_english(text: str):
    """
    Přečte nahlas anglický text pomocí macOS příkazu 'say'.
    """
    try:
        subprocess.Popen(["say", "-v", "Samantha", text])
    except Exception as e:
        print("TTS error:", e)
        
SCRIPT_DIR = Path(__file__).resolve().parent
CSV_BASENAME = "tobevety.csv"
VERB_CSV_BASENAME = "verb_conjugation.csv"
POSSIBLE_CSV = [
    SCRIPT_DIR / CSV_BASENAME,
    SCRIPT_DIR.parent / CSV_BASENAME,
    Path.cwd() / CSV_BASENAME,
]
POSSIBLE_VERB_CSV = [
    SCRIPT_DIR / VERB_CSV_BASENAME,
    SCRIPT_DIR.parent / VERB_CSV_BASENAME,
    Path.cwd() / VERB_CSV_BASENAME,
]

COLOR_MAP = {
    "red": "#e63946",
    "blue": "#3a86ff",
    "green": "#2a9d8f",
    "yellow": "#ffd166",
    "pink": "#f4a7b9",
    "black": "#222222",
    "white": "#f8f9fa",
    "grey": "#b0b0b0",
    "gray": "#b0b0b0",
}

CONTRACTIONS = {
    "aren't", "isn't", "i'm", "he's", "she's", "it's",
    "they're", "we're", "you're",
}

STOPWORDS = {
    "i", "you", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "a", "an", "the", "this", "that", "these", "those",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "at", "in", "on", "to", "from", "with", "for", "of", "by", "as",
    "and", "or", "but", "not",
}

# Názvy očekávaných sloupců v CSV
COLUMN_QUESTION = "Otázka"
COLUMN_POSITIVE = "Kladná odpověď"
COLUMN_NEGATIVE = "Záporná odpověď"
COLUMN_PRONOUN = "Pronoun"
COLUMN_VERB = "Verb"
COLUMN_ADVERBIAL = "Adverbial"
COLUMN_TRANSLATION = "Translation"


class ToBeTrainerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Trénink TO BE – věty z CSV")

        # Zvětšení okna
        self.master.geometry("1300x700")

        # Načtení dat z CSV
        csv_path = self.find_csv_path()
        if csv_path is None:
            self.master.destroy()
            return
        self.sentences = self.load_csv(csv_path)
        if not self.sentences:
            messagebox.showerror("Chyba", "V souboru nejsou žádné věty.")
            self.master.destroy()
            return
        self.verb_rows = []
        self.verconjug_available = self._try_load_verb_rows()

        # Seznam indexů vět v náhodném pořadí
        self.indices = list(range(len(self.sentences)))
        random.shuffle(self.indices)
        self.current_pos = -1  # zatím žádná věta
        self.verb_random_indices = list(range(len(self.verb_rows)))
        random.shuffle(self.verb_random_indices)
        self.verb_random_pos = -1
        self.verb_order_pos = -1

        # Velké fonty
        self.font_question = ("Arial", 40, "bold")
        self.font_answer = ("Arial", 36)
        self.font_button = ("Arial", 20, "bold")

        self.screen_stack = tk.Frame(self.master)
        self.screen_stack.pack(fill="both", expand=True)
        self.screen_stack.grid_rowconfigure(0, weight=1)
        self.screen_stack.grid_columnconfigure(0, weight=1)
        self.main_frame = tk.Frame(self.screen_stack)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.verconjug_frame = tk.Frame(self.screen_stack, bg="white")
        self.verconjug_frame.grid(row=0, column=0, sticky="nsew")

        # Rámec pro text
        text_frame = tk.Frame(self.main_frame)
        text_frame.pack(pady=40, padx=40, fill="both", expand=True)

        # Popisky pro otázku a odpovědi
        self.label_question = tk.Label(
            text_frame,
            text="",
            font=self.font_question,
            wraplength=1200,
            justify="center"
        )
        self.label_question.pack(pady=20)

        self.label_positive = tk.Label(
            text_frame,
            text="",
            font=self.font_answer,
            fg="darkgreen",
            wraplength=1200,
            justify="center"
        )
        self.label_positive.pack(pady=20)

        self.label_negative = tk.Label(
            text_frame,
            text="",
            font=self.font_answer,
            fg="darkred",
            wraplength=1200,
            justify="center"
        )
        self.label_negative.pack(pady=20)

        # Plátno pro jednoduché schématické obrázky (pod otázkou i odpověďmi)
        self.scene_canvas = tk.Canvas(
            text_frame, width=1200, height=220, bg="white", highlightthickness=0
        )
        self.scene_canvas.pack(pady=10)
        self.scene_canvas.bind("<Configure>", self.on_canvas_resize)
        self.current_scene_text = ""

        # Rámec pro tlačítka
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=20)

        self.btn_new = tk.Button(
            button_frame,
            text="Nová věta",
            font=self.font_button,
            command=self.show_new_sentence,
            width=12,
            height=2
        )
        self.btn_new.grid(row=0, column=0, padx=15)

        self.btn_begin = tk.Button(
            button_frame,
            text="Begin",
            font=self.font_button,
            command=self.begin_from_start,
            width=10,
            height=2
        )
        self.btn_begin.grid(row=0, column=1, padx=15)

        self.btn_positive = tk.Button(
            button_frame,
            text="Kladná odpověď",
            font=self.font_button,
            command=self.show_positive_answer,
            width=16,
            height=2
        )
        self.btn_positive.grid(row=0, column=2, padx=15)

        self.btn_negative = tk.Button(
            button_frame,
            text="Záporná odpověď",
            font=self.font_button,
            command=self.show_negative_answer,
            width=16,
            height=2
        )
        self.btn_negative.grid(row=0, column=3, padx=15)

        self.btn_verconjug = tk.Button(
            button_frame,
            text="VerConjug",
            font=self.font_button,
            command=self.show_verconjug_screen,
            width=12,
            height=2
        )
        self.btn_verconjug.grid(row=0, column=4, padx=15)
        if not self.verconjug_available:
            self.btn_verconjug.config(state="disabled")

        self.verconjug_after_ids = []
        self.verconjug_running = False
        self.verconjug_pending_step = None
        self.verconjug_pending_args = ()
        self.verconjug_pending_delay = 0
        self.verconjug_current = None
        self.verconjug_mode = "ordered"
        self.verconjug_question_requested = False
        self.verconjug_animating = False
        self.verconjug_floating_widgets = []
        self.verconjug_question_mark = None
        self._build_verconjug_screen()

        # Po startu hned zobrazíme první větu
        self.show_new_sentence()
        self.main_frame.tkraise()

    def load_csv(self, filename):
        """Načte CSV soubor do seznamu slovníků."""
        sentences = []
        try:
            with open(filename, "r", encoding="utf-8-sig", newline="") as f:
                # Pokus o automatickou detekci oddělovače
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                except csv.Error:
                    dialect = csv.excel
                    dialect.delimiter = ";"

                reader = csv.DictReader(f, dialect=dialect)
                # Kontrola, zda máme potřebné sloupce
                needed = {COLUMN_QUESTION, COLUMN_POSITIVE, COLUMN_NEGATIVE}
                if not needed.issubset(set(reader.fieldnames or [])):
                    msg = (
                        "V CSV souboru chybí některý z požadovaných sloupců:\n"
                        f"{COLUMN_QUESTION}, {COLUMN_POSITIVE}, {COLUMN_NEGATIVE}\n\n"
                        f"Nalezené sloupce: {reader.fieldnames}"
                    )
                    messagebox.showerror("Chyba struktury CSV", msg)
                    return []

                for row in reader:
                    # Ořízneme mezery
                    q = (row.get(COLUMN_QUESTION) or "").strip()
                    p = (row.get(COLUMN_POSITIVE) or "").strip()
                    n = (row.get(COLUMN_NEGATIVE) or "").strip()
                    if q:  # prázdné otázky ignorujeme
                        sentences.append(
                            {
                                COLUMN_QUESTION: q,
                                COLUMN_POSITIVE: p,
                                COLUMN_NEGATIVE: n,
                            }
                        )

        except FileNotFoundError:
            tried = "\n".join(str(p) for p in POSSIBLE_CSV)
            messagebox.showerror(
                "Soubor nenalezen",
                f"Soubor '{CSV_BASENAME}' nebyl nalezen.\n\nHledal jsem:\n{tried}",
            )
        except Exception as e:
            messagebox.showerror("Chyba při čtení CSV", str(e))

        return sentences

    def find_csv_path(self) -> Path | None:
        for p in POSSIBLE_CSV:
            if p.exists():
                return p
        tried = "\n".join(str(p) for p in POSSIBLE_CSV)
        messagebox.showerror(
            "Soubor nenalezen",
            f"Soubor '{CSV_BASENAME}' nebyl nalezen.\n\nHledal jsem:\n{tried}",
        )
        return None

    def load_verb_csv(self, filename):
        rows = []
        try:
            with open(filename, "r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                except csv.Error:
                    dialect = csv.excel
                    dialect.delimiter = ";"

                reader = csv.DictReader(f, dialect=dialect)
                needed = {COLUMN_PRONOUN, COLUMN_VERB, COLUMN_ADVERBIAL, COLUMN_TRANSLATION}
                if not needed.issubset(set(reader.fieldnames or [])):
                    msg = (
                        "V CSV souboru chybí některý z požadovaných sloupců:\n"
                        f"{COLUMN_PRONOUN}, {COLUMN_VERB}, {COLUMN_ADVERBIAL}, {COLUMN_TRANSLATION}\n\n"
                        f"Nalezené sloupce: {reader.fieldnames}"
                    )
                    messagebox.showerror("Chyba struktury CSV", msg)
                    return []

                for row in reader:
                    pronoun = (row.get(COLUMN_PRONOUN) or "").strip()
                    verb = (row.get(COLUMN_VERB) or "").strip()
                    adverbial = (row.get(COLUMN_ADVERBIAL) or "").strip()
                    translation = (row.get(COLUMN_TRANSLATION) or "").strip()
                    if pronoun and verb and adverbial and translation:
                        rows.append(
                            {
                                COLUMN_PRONOUN: pronoun,
                                COLUMN_VERB: verb,
                                COLUMN_ADVERBIAL: adverbial,
                                COLUMN_TRANSLATION: translation,
                            }
                        )
        except FileNotFoundError:
            tried = "\n".join(str(p) for p in POSSIBLE_VERB_CSV)
            messagebox.showerror(
                "Soubor nenalezen",
                f"Soubor '{VERB_CSV_BASENAME}' nebyl nalezen.\n\nHledal jsem:\n{tried}",
            )
        except Exception as e:
            messagebox.showerror("Chyba při čtení CSV", str(e))

        return rows

    def find_verb_csv_path(self) -> Path | None:
        for p in POSSIBLE_VERB_CSV:
            if p.exists():
                return p
        return None

    def _try_load_verb_rows(self) -> bool:
        verb_csv_path = self.find_verb_csv_path()
        if verb_csv_path is None:
            return False
        self.verb_rows = self.load_verb_csv(verb_csv_path)
        return bool(self.verb_rows)

    def _build_verconjug_screen(self):
        title = tk.Label(
            self.verconjug_frame,
            text="Verb Conjugation",
            font=("Arial", 34, "bold"),
            bg="white",
        )
        title.pack(pady=(22, 14))

        words_holder = tk.Frame(self.verconjug_frame, bg="white")
        words_holder.pack(fill="both", expand=True, padx=30, pady=(20, 10))
        words_row = tk.Frame(words_holder, bg="white")
        words_row.pack(expand=True)
        self.verconjug_words_row = words_row

        self.verconjug_pronoun_label = self._create_word_box(words_row, "#111111", width_chars=6)
        self.verconjug_verb_label = self._create_word_box(words_row, "#1f5eff", width_chars=7)
        self.verconjug_adverbial_label = self._create_word_box(words_row, "#7a2dbd", width_chars=17)
        self.verconjug_translation = tk.Label(
            self.verconjug_frame,
            text="",
            font=("Arial", 26),
            fg="#111111",
            bg="white",
            wraplength=1200,
            justify="center",
        )
        self.verconjug_translation.pack(pady=(0, 24))

        btns = tk.Frame(self.verconjug_frame, bg="white")
        btns.pack(pady=(0, 24))

        tk.Button(
            btns, text="Go", font=self.font_button, width=10, height=2,
            command=self.verconjug_go
        ).grid(row=0, column=0, padx=16)
        tk.Button(
            btns, text="Random", font=self.font_button, width=10, height=2,
            command=self.verconjug_random
        ).grid(row=0, column=1, padx=16)
        tk.Button(
            btns, text="Go Q", font=self.font_button, width=10, height=2,
            command=self.verconjug_go_question
        ).grid(row=0, column=2, padx=16)
        tk.Button(
            btns, text="Begin", font=self.font_button, width=10, height=2,
            command=self.verconjug_begin
        ).grid(row=0, column=3, padx=16)
        tk.Button(
            btns, text="Stop", font=self.font_button, width=10, height=2,
            command=self.verconjug_stop
        ).grid(row=0, column=4, padx=16)
        tk.Button(
            btns, text="Back", font=self.font_button, width=10, height=2,
            command=self.back_to_main_screen
        ).grid(row=0, column=5, padx=16)

        self._reset_verconjug_view()

    def _create_word_box(self, parent, fg_color: str, width_chars: int):
        outer = tk.Frame(parent, bg="black", padx=1, pady=1)
        outer.pack(side="left", padx=10, pady=12)
        label = tk.Label(
            outer,
            text="",
            font=("Arial", 42, "bold"),
            fg=fg_color,
            bg="white",
            anchor="center",
            justify="center",
            width=width_chars,
        )
        label.pack()
        label.outer_box = outer
        return label

    def _reset_verconjug_view(self):
        self._clear_verconjug_animation()
        self.verconjug_pronoun_label.config(text="")
        self.verconjug_verb_label.config(text="")
        self.verconjug_adverbial_label.config(text="")
        self.verconjug_translation.config(text="")

    def show_verconjug_screen(self):
        if not self.verconjug_available:
            messagebox.showinfo(
                "VerConjug není k dispozici",
                f"Soubor '{VERB_CSV_BASENAME}' chybí nebo neobsahuje validní data.",
            )
            return
        self.verconjug_stop()
        self._reset_verconjug_view()
        self.verconjug_frame.tkraise()

    def back_to_main_screen(self):
        self.verconjug_stop()
        self.main_frame.tkraise()

    def _clear_verconjug_animation(self):
        self.verconjug_animating = False
        if self.verconjug_question_mark is not None:
            try:
                self.verconjug_question_mark.destroy()
            except Exception:
                pass
            self.verconjug_question_mark = None
        while self.verconjug_floating_widgets:
            widget = self.verconjug_floating_widgets.pop()
            try:
                widget.destroy()
            except Exception:
                pass

    def _verconjug_box_bounds(self, label_widget):
        outer = getattr(label_widget, "outer_box", label_widget)
        self.master.update_idletasks()
        base_x = self.verconjug_frame.winfo_rootx()
        base_y = self.verconjug_frame.winfo_rooty()
        return (
            outer.winfo_rootx() - base_x,
            outer.winfo_rooty() - base_y,
            outer.winfo_width(),
            outer.winfo_height(),
        )

    def _create_floating_box(self, source_label, text):
        x, y, width, height = self._verconjug_box_bounds(source_label)
        outer = tk.Frame(self.verconjug_frame, bg="black", padx=1, pady=1)
        inner = tk.Label(
            outer,
            text=text,
            font=source_label.cget("font"),
            fg=source_label.cget("fg"),
            bg="white",
            anchor="center",
            justify="center",
            width=source_label.cget("width"),
        )
        inner.pack()
        outer.place(x=x, y=y, width=width, height=height)
        self.verconjug_floating_widgets.append(outer)
        return outer, (x, y, width, height)

    def _show_verconjug_question_mark(self):
        x, y, width, height = self._verconjug_box_bounds(self.verconjug_adverbial_label)
        mark = tk.Label(
            self.verconjug_frame,
            text="?",
            font=("Arial", 50, "bold"),
            fg="#111111",
            bg="white",
        )
        mark.place(x=x + width + 22, y=y + max(0, (height - 60) // 2))
        self.verconjug_question_mark = mark

    def _verconjug_all_words_visible(self):
        return all((
            self.verconjug_pronoun_label.cget("text"),
            self.verconjug_verb_label.cget("text"),
            self.verconjug_adverbial_label.cget("text"),
        ))

    def _next_verb_row_ordered(self):
        self.verb_order_pos += 1
        if self.verb_order_pos >= len(self.verb_rows):
            self.verb_order_pos = 0
        return self.verb_rows[self.verb_order_pos]

    def _next_verb_row_random(self):
        self.verb_random_pos += 1
        if self.verb_random_pos >= len(self.verb_random_indices):
            random.shuffle(self.verb_random_indices)
            self.verb_random_pos = 0
        idx = self.verb_random_indices[self.verb_random_pos]
        return self.verb_rows[idx]

    def _schedule_verconjug(self, delay_ms, callback, *args):
        self.verconjug_pending_step = callback
        self.verconjug_pending_args = args
        self.verconjug_pending_delay = int(delay_ms)

        def runner():
            try:
                self.verconjug_after_ids.remove(after_id)
            except Exception:
                pass
            if not self.verconjug_running:
                return
            self.verconjug_pending_step = None
            self.verconjug_pending_args = ()
            self.verconjug_pending_delay = 0
            callback(*args)

        after_id = self.master.after(delay_ms, runner)
        self.verconjug_after_ids.append(after_id)
        return after_id

    def _cancel_verconjug_timers(self):
        for after_id in self.verconjug_after_ids:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
        self.verconjug_after_ids.clear()

    def verconjug_go(self):
        self._start_verconjug_mode("ordered")

    def verconjug_random(self):
        self._start_verconjug_mode("random")

    def verconjug_go_question(self):
        self.verconjug_question_requested = True
        if self.verconjug_running and self._verconjug_all_words_visible() and not self.verconjug_animating:
            self._cancel_verconjug_timers()
            self.verconjug_pending_step = None
            self.verconjug_pending_args = ()
            self.verconjug_pending_delay = 0
            self._verconjug_run_question_mode()

    def verconjug_begin(self):
        """Reset ordered verb cycle to the first CSV row."""
        self.verconjug_mode = "ordered"
        self.verb_order_pos = -1
        self._cancel_verconjug_timers()
        self.verconjug_pending_step = None
        self.verconjug_pending_args = ()
        self.verconjug_pending_delay = 0
        self._reset_verconjug_view()

        if self.verconjug_running:
            self._verconjug_start_cycle()

    def _start_verconjug_mode(self, mode: str):
        mode_changed = self.verconjug_mode != mode
        self.verconjug_mode = mode

        if mode_changed:
            self._cancel_verconjug_timers()
            self.verconjug_pending_step = None
            self.verconjug_pending_args = ()
            self.verconjug_pending_delay = 0

        if self.verconjug_running and not mode_changed:
            return

        self.verconjug_running = True
        if self.verconjug_pending_step is not None and not mode_changed:
            self._schedule_verconjug(
                max(0, self.verconjug_pending_delay),
                self.verconjug_pending_step,
                *self.verconjug_pending_args,
            )
        else:
            self._verconjug_start_cycle()

    def verconjug_stop(self):
        self.verconjug_running = False
        self.verconjug_question_requested = False
        self._cancel_verconjug_timers()
        self._clear_verconjug_animation()

    def _verconjug_start_cycle(self):
        if not self.verconjug_running:
            return
        self._clear_verconjug_animation()
        if self.verconjug_mode == "random":
            self.verconjug_current = self._next_verb_row_random()
        else:
            self.verconjug_current = self._next_verb_row_ordered()
        self._reset_verconjug_view()
        self._schedule_verconjug(1000, self._verconjug_show_pronoun)

    def _verconjug_show_pronoun(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        self.verconjug_pronoun_label.config(text=self.verconjug_current[COLUMN_PRONOUN])
        self._schedule_verconjug(1000, self._verconjug_show_verb)

    def _verconjug_show_verb(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        self.verconjug_verb_label.config(text=self.verconjug_current[COLUMN_VERB])
        self._schedule_verconjug(1000, self._verconjug_show_adverbial)

    def _verconjug_show_adverbial(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        self.verconjug_adverbial_label.config(text=self.verconjug_current[COLUMN_ADVERBIAL])
        if self.verconjug_question_requested:
            self._schedule_verconjug(700, self._verconjug_run_question_mode)
        else:
            self._schedule_verconjug(1000, self._verconjug_speak_sentence)

    def _verconjug_speak_sentence(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        sentence = (
            f"{self.verconjug_current[COLUMN_PRONOUN]} "
            f"{self.verconjug_current[COLUMN_VERB]} "
            f"{self.verconjug_current[COLUMN_ADVERBIAL]}"
        )
        speak_english(sentence)
        self._schedule_verconjug(3000, self._verconjug_show_translation)

    def _verconjug_run_question_mode(self):
        if not self.verconjug_running or not self.verconjug_current or self.verconjug_animating:
            return

        self.verconjug_question_requested = False
        self.verconjug_animating = True

        pronoun_text = self.verconjug_current[COLUMN_PRONOUN]
        verb_text = self.verconjug_current[COLUMN_VERB]
        adverbial_text = self.verconjug_current[COLUMN_ADVERBIAL]

        self.verconjug_translation.config(text="")
        self.verconjug_pronoun_label.config(text="")
        self.verconjug_verb_label.config(text="")
        self.verconjug_adverbial_label.config(text=adverbial_text)

        pronoun_box, pronoun_start = self._create_floating_box(self.verconjug_pronoun_label, pronoun_text)
        verb_box, verb_start = self._create_floating_box(self.verconjug_verb_label, verb_text)
        pronoun_target = self._verconjug_box_bounds(self.verconjug_verb_label)
        verb_target = self._verconjug_box_bounds(self.verconjug_pronoun_label)

        duration_ms = 900
        step_ms = 25
        steps = max(1, duration_ms // step_ms)
        arc_height = 60

        def ease(progress):
            return 1 - (1 - progress) * (1 - progress)

        def move_widget(widget, start, target, progress):
            eased = ease(progress)
            sx, sy, sw, sh = start
            tx, ty, tw, th = target
            x = sx + (tx - sx) * eased
            y = sy + (ty - sy) * eased - arc_height * 4 * progress * (1 - progress)
            widget.place(x=x, y=y, width=sw + (tw - sw) * eased, height=sh + (th - sh) * eased)

        def animate(step=0):
            if not self.verconjug_running:
                self._clear_verconjug_animation()
                return
            progress = min(1.0, step / steps)
            move_widget(pronoun_box, pronoun_start, pronoun_target, progress)
            move_widget(verb_box, verb_start, verb_target, progress)
            if progress >= 1.0:
                self._clear_verconjug_animation()
                self.verconjug_pronoun_label.config(text=verb_text)
                self.verconjug_verb_label.config(text=pronoun_text)
                self.verconjug_adverbial_label.config(text=adverbial_text)
                self._show_verconjug_question_mark()
                self._schedule_verconjug(250, self._verconjug_speak_question_sentence)
                return

            def runner():
                try:
                    self.verconjug_after_ids.remove(after_id)
                except Exception:
                    pass
                animate(step + 1)

            after_id = self.master.after(step_ms, runner)
            self.verconjug_after_ids.append(after_id)

        animate()

    def _verconjug_speak_question_sentence(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        sentence = (
            f"{self.verconjug_current[COLUMN_VERB]} "
            f"{self.verconjug_current[COLUMN_PRONOUN]} "
            f"{self.verconjug_current[COLUMN_ADVERBIAL]}?"
        )
        speak_english(sentence)
        self._schedule_verconjug(2800, self._verconjug_start_cycle)

    def _verconjug_show_translation(self):
        if not self.verconjug_running or not self.verconjug_current:
            return
        self.verconjug_translation.config(text=self.verconjug_current[COLUMN_TRANSLATION])
        self._schedule_verconjug(2000, self._verconjug_start_cycle)

    def get_current_sentence(self):
        """Vrátí aktuální větu podle přepočteného náhodného pořadí."""
        if self.current_pos < 0 or self.current_pos >= len(self.indices):
            return None
        idx = self.indices[self.current_pos]
        return self.sentences[idx]

    def begin_from_start(self):
        """Vrátí cyklus na první větu aktuálního pořadí."""
        if not self.sentences or not self.indices:
            return

        self.current_pos = 0
        sentence = self.get_current_sentence()
        if not sentence:
            return

        question = sentence[COLUMN_QUESTION]
        self.label_question.config(text=question)
        self.label_positive.config(text="")
        self.label_negative.config(text="")
        self.draw_scene(question)
        speak_english(question)

    def show_new_sentence(self):
        """Vybere další větu v náhodném pořadí a zobrazí otázku."""
        if not self.sentences:
            return

        self.current_pos += 1
        if self.current_pos >= len(self.indices):
            # Došli jsme na konec – znovu zamícháme
            random.shuffle(self.indices)
            self.current_pos = 0

        sentence = self.get_current_sentence()
        if not sentence:
            return

        question = sentence[COLUMN_QUESTION]

        # Zobrazíme otázku, smažeme odpovědi
        self.label_question.config(text=sentence[COLUMN_QUESTION])
        self.label_positive.config(text="")
        self.label_negative.config(text="")
        self.draw_scene(sentence[COLUMN_QUESTION])

        # Přečti nahlas otázku
        speak_english(question)

    def draw_scene(self, text: str):
        self.current_scene_text = text
        c = self.scene_canvas
        c.delete("all")
        s = text.lower()
        words = set(re.findall(r"[a-z']+", s))
        words -= CONTRACTIONS
        words -= STOPWORDS
        used_words = set()

        cw = c.winfo_width() or int(c["width"])
        ch = c.winfo_height() or int(c["height"])
        scale = min(cw / 1200.0, ch / 220.0)
        y = (ch - 220 * scale) / 2
        # Virtuální scéna je centrovaná, aby objekty neutíkaly mimo plátno.
        scene_w = 1200 * scale
        scene_left = (cw - scene_w) / 2
        left_x = scene_left + 80 * scale
        mid_x = scene_left + 380 * scale
        right_x = scene_left + 640 * scale

        bg = "white"
        if "sky" in words:
            bg = "#bde7ff"
            used_words.add("sky")
        if "grey" in words or "gray" in words:
            bg = "#d9d9d9"
            used_words.update({"grey", "gray"})
        elif "blue" in words:
            bg = "#bde7ff"
            used_words.add("blue")
        elif "green" in words:
            bg = "#c8f2c3"
            used_words.add("green")
        elif "yellow" in words:
            bg = "#fff1a6"
            used_words.add("yellow")
        elif "pink" in words:
            bg = "#ffd1dc"
            used_words.add("pink")
        c.configure(bg=bg)

        accent = None
        for color_word in COLOR_MAP:
            if color_word in words:
                accent = COLOR_MAP[color_word]
                used_words.add(color_word)
                break

        size_factor = 1.0
        if "big" in words:
            size_factor = 1.15
            used_words.add("big")
        if "small" in words:
            size_factor = 0.85
            used_words.add("small")

        if "sun" in words:
            self._draw_sun(cw - 140 * scale, y + 10 * scale, scale)
            used_words.add("sun")

        color_words = [w for w in COLOR_MAP if w in words]
        if color_words:
            self._draw_color_swatches(left_x + 10 * scale, y + 170 * scale, scale, color_words)
            used_words.update(color_words)

        if "school" in words or "class" in words:
            self._draw_school(left_x, y + 10 * scale, scale)
            used_words.update({"school", "class"})
        elif "home" in words or "house" in words:
            self._draw_house(left_x, y + 20 * scale, scale)
            used_words.update({"home", "house"})
        elif "city" in words or "prague" in words:
            self._draw_city(left_x, y + 30 * scale, scale)
            used_words.update({"city", "prague"})
        elif "garden" in words:
            self._draw_tree(left_x, y + 40 * scale, scale)
            used_words.add("garden")

        if "dog" in words:
            self._draw_dog(mid_x, y + 80 * scale, scale)
            used_words.add("dog")
        if "cat" in words:
            self._draw_cat(mid_x + 160 * scale, y + 80 * scale, scale, accent)
            used_words.add("cat")
        if "bag" in words:
            self._draw_bag(mid_x + 320 * scale, y + 80 * scale, scale)
            used_words.add("bag")
        if "radio" in words:
            self._draw_radio(mid_x + 420 * scale, y + 70 * scale, scale, accent)
            used_words.add("radio")

        if "teacher" in words:
            self._draw_teacher(right_x, y + 20 * scale, scale * size_factor)
            used_words.add("teacher")
        elif "mom" in words or "sister" in words or "she" in words:
            self._draw_girl(right_x, y + 20 * scale, scale * size_factor, accent)
            used_words.update({"mom", "sister", "she"})
        elif "father" in words:
            self._draw_father(right_x, y + 20 * scale, scale * size_factor)
            used_words.add("father")
        elif "men" in words:
            self._draw_two_men(right_x, y + 20 * scale, scale * size_factor)
            used_words.add("men")
        elif "students" in words:
            self._draw_students(right_x, y + 20 * scale, scale * size_factor)
            used_words.add("students")
        elif "friends" in words:
            self._draw_friends(right_x, y + 20 * scale, scale * size_factor)
            used_words.add("friends")
        elif "brother" in words or "he" in words or "friend" in words or "student" in words:
            self._draw_boy(right_x, y + 20 * scale, scale * size_factor, accent)
            used_words.update({"brother", "he", "friend", "student"})
        if "window" in words:
            self._draw_window(right_x + 180 * scale, y + 30 * scale, scale)
            used_words.add("window")
        if "eyes" in words:
            self._draw_eyes(right_x + 260 * scale, y + 30 * scale, scale)
            used_words.add("eyes")
        if "dress" in words:
            self._draw_dress(right_x + 360 * scale, y + 20 * scale, scale, accent)
            used_words.add("dress")
        if "cake" in words:
            self._draw_cake(right_x + 480 * scale, y + 70 * scale, scale, accent)
            used_words.add("cake")

        if "open" in words and "window" in words:
            self._draw_open_mark(right_x + 180 * scale, y + 110 * scale, scale)
            used_words.add("open")

        if "happy" in words or "good" in words or "nice" in words:
            self._draw_smiley(cw * 0.5, y + 10 * scale, scale)
            used_words.update({"happy", "good", "nice"})
        if "tired" in words:
            self._draw_sleepy(cw * 0.5, y + 10 * scale, scale)
            used_words.add("tired")
        if "today" in words or "now" in words:
            self._draw_clock(cw * 0.5 + 120 * scale, y + 10 * scale, scale)
            used_words.update({"today", "now"})
        if "years" in words:
            self._draw_years_icon(cw * 0.5 + 220 * scale, y + 10 * scale, scale)
            used_words.add("years")
        if "tall" in words:
            self._draw_tall_icon(cw * 0.5 + 300 * scale, y + 10 * scale, scale)
            used_words.add("tall")
        if "small" in words:
            self._draw_small_icon(cw * 0.5 + 360 * scale, y + 10 * scale, scale)
            used_words.add("small")

        leftover = sorted(words - used_words)
        if leftover:
            self._draw_badges(leftover, 20 * scale, ch - 50 * scale, cw - 40 * scale, scale)

    def on_canvas_resize(self, _event):
        if self.current_scene_text:
            self.draw_scene(self.current_scene_text)

    def _draw_school(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y + 60 * scale, x + 180 * scale, y + 170 * scale,
            fill="#f2f2f2", outline="#444"
        )
        c.create_polygon(
            x, y + 60 * scale, x + 90 * scale, y, x + 180 * scale, y + 60 * scale,
            fill="#d36b6b", outline="#444"
        )
        c.create_rectangle(
            x + 75 * scale, y + 110 * scale, x + 105 * scale, y + 170 * scale,
            fill="#c59b6d", outline="#444"
        )
        c.create_rectangle(
            x + 20 * scale, y + 90 * scale, x + 55 * scale, y + 130 * scale,
            fill="#8ecae6", outline="#444"
        )
        c.create_rectangle(
            x + 125 * scale, y + 90 * scale, x + 160 * scale, y + 130 * scale,
            fill="#8ecae6", outline="#444"
        )
        c.create_text(x + 90 * scale, y + 80 * scale, text="SCHOOL", font=("Arial", 10, "bold"))

    def _draw_house(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y + 70 * scale, x + 170 * scale, y + 170 * scale,
            fill="#f7ede2", outline="#444"
        )
        c.create_polygon(
            x - 10 * scale, y + 70 * scale, x + 85 * scale, y + 10 * scale,
            x + 180 * scale, y + 70 * scale, fill="#c97c5d", outline="#444"
        )
        c.create_rectangle(
            x + 70 * scale, y + 110 * scale, x + 100 * scale, y + 170 * scale,
            fill="#c59b6d", outline="#444"
        )
        c.create_rectangle(
            x + 20 * scale, y + 95 * scale, x + 55 * scale, y + 125 * scale,
            fill="#8ecae6", outline="#444"
        )

    def _draw_city(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        widths = [50, 70, 40, 60, 50]
        heights = [120, 150, 90, 140, 110]
        offset = 0
        for w, h in zip(widths, heights):
            c.create_rectangle(
                x + offset * scale, y + (170 - h) * scale,
                x + (offset + w) * scale, y + 170 * scale,
                fill="#d9d9d9", outline="#666"
            )
            offset += w + 10

    def _draw_tree(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x + 50 * scale, y + 90 * scale, x + 70 * scale, y + 150 * scale,
            fill="#8d6e63", outline="#444"
        )
        c.create_oval(
            x + 20 * scale, y + 40 * scale, x + 100 * scale, y + 120 * scale,
            fill="#8bc34a", outline="#444"
        )

    def _draw_sun(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_oval(
            x, y, x + 60 * scale, y + 60 * scale, fill="#ffd166", outline="#e09f3e"
        )

    def _draw_boy(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        shirt = accent or "#6fa8dc"
        c.create_oval(
            x + 30 * scale, y, x + 70 * scale, y + 40 * scale,
            fill="#f2c9a0", outline="#333"
        )
        c.create_rectangle(
            x + 35 * scale, y + 40 * scale, x + 65 * scale, y + 90 * scale,
            fill=shirt, outline="#333"
        )
        c.create_line(x + 35 * scale, y + 55 * scale, x + 10 * scale, y + 75 * scale, width=3)
        c.create_line(x + 65 * scale, y + 55 * scale, x + 90 * scale, y + 75 * scale, width=3)
        c.create_line(x + 45 * scale, y + 90 * scale, x + 30 * scale, y + 130 * scale, width=3)
        c.create_line(x + 55 * scale, y + 90 * scale, x + 70 * scale, y + 130 * scale, width=3)

    def _draw_girl(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        dress = accent or "#f4a7b9"
        c.create_oval(
            x + 30 * scale, y, x + 70 * scale, y + 40 * scale,
            fill="#f2c9a0", outline="#333"
        )
        c.create_polygon(
            x + 50 * scale, y + 40 * scale, x + 20 * scale, y + 110 * scale,
            x + 80 * scale, y + 110 * scale,
            fill=dress, outline="#333"
        )
        c.create_line(x + 35 * scale, y + 60 * scale, x + 10 * scale, y + 80 * scale, width=3)
        c.create_line(x + 65 * scale, y + 60 * scale, x + 90 * scale, y + 80 * scale, width=3)
        c.create_line(x + 40 * scale, y + 110 * scale, x + 30 * scale, y + 140 * scale, width=3)
        c.create_line(x + 60 * scale, y + 110 * scale, x + 70 * scale, y + 140 * scale, width=3)

    def _draw_teacher(self, x: float, y: float, scale: float):
        self._draw_boy(x, y, scale)
        c = self.scene_canvas
        c.create_line(x + 30 * scale, y + 12 * scale, x + 70 * scale, y + 12 * scale, width=2)

    def _draw_dog(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y, x + 90 * scale, y + 40 * scale, fill="#c19a6b", outline="#444"
        )
        c.create_oval(
            x + 70 * scale, y - 10 * scale, x + 100 * scale, y + 20 * scale,
            fill="#c19a6b", outline="#444"
        )
        c.create_line(x + 15 * scale, y + 40 * scale, x + 15 * scale, y + 60 * scale, width=3)
        c.create_line(x + 35 * scale, y + 40 * scale, x + 35 * scale, y + 60 * scale, width=3)

    def _draw_cat(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        fur = accent or "#c0c0c0"
        c.create_oval(
            x, y, x + 60 * scale, y + 35 * scale, fill=fur, outline="#444"
        )
        c.create_polygon(
            x + 10 * scale, y, x + 20 * scale, y - 15 * scale, x + 30 * scale, y,
            fill=fur, outline="#444"
        )
        c.create_polygon(
            x + 30 * scale, y, x + 40 * scale, y - 15 * scale, x + 50 * scale, y,
            fill=fur, outline="#444"
        )

    def _draw_bag(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y, x + 60 * scale, y + 50 * scale, fill="#b08968", outline="#444"
        )
        c.create_arc(
            x + 10 * scale, y - 20 * scale, x + 50 * scale, y + 10 * scale,
            start=0, extent=180, style="arc", width=3
        )

    def _draw_window(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y, x + 70 * scale, y + 70 * scale, fill="#e0f7ff", outline="#444"
        )
        c.create_line(x + 35 * scale, y, x + 35 * scale, y + 70 * scale, width=2)
        c.create_line(x, y + 35 * scale, x + 70 * scale, y + 35 * scale, width=2)

    def _draw_eyes(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_oval(
            x, y, x + 30 * scale, y + 20 * scale, fill="white", outline="#444"
        )
        c.create_oval(
            x + 40 * scale, y, x + 70 * scale, y + 20 * scale, fill="white", outline="#444"
        )
        c.create_oval(
            x + 12 * scale, y + 6 * scale, x + 18 * scale, y + 12 * scale,
            fill="#333", outline="#333"
        )
        c.create_oval(
            x + 52 * scale, y + 6 * scale, x + 58 * scale, y + 12 * scale,
            fill="#333", outline="#333"
        )

    def _draw_radio(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        body = accent or "#adb5bd"
        c.create_rectangle(
            x, y, x + 80 * scale, y + 50 * scale, fill=body, outline="#444"
        )
        c.create_oval(
            x + 10 * scale, y + 15 * scale, x + 30 * scale, y + 35 * scale,
            fill="#333", outline="#333"
        )
        c.create_rectangle(
            x + 45 * scale, y + 15 * scale, x + 70 * scale, y + 25 * scale,
            fill="#f8f9fa", outline="#444"
        )

    def _draw_cake(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        icing = accent or "#f4a7b9"
        c.create_rectangle(
            x, y, x + 70 * scale, y + 35 * scale, fill="#f1c27d", outline="#444"
        )
        c.create_rectangle(
            x, y - 15 * scale, x + 70 * scale, y, fill=icing, outline="#444"
        )
        c.create_line(x + 35 * scale, y - 25 * scale, x + 35 * scale, y - 5 * scale, width=2)

    def _draw_dress(self, x: float, y: float, scale: float, accent: str | None = None):
        c = self.scene_canvas
        dress = accent or "#f4a7b9"
        c.create_polygon(
            x + 25 * scale, y, x, y + 60 * scale, x + 50 * scale, y + 60 * scale,
            fill=dress, outline="#444"
        )
        c.create_rectangle(
            x + 18 * scale, y - 20 * scale, x + 32 * scale, y, fill=dress, outline="#444"
        )

    def _draw_father(self, x: float, y: float, scale: float):
        self._draw_boy(x, y, scale)
        c = self.scene_canvas
        c.create_line(x + 35 * scale, y + 35 * scale, x + 65 * scale, y + 35 * scale, width=2)

    def _draw_two_men(self, x: float, y: float, scale: float):
        self._draw_boy(x, y, scale)
        self._draw_boy(x + 90 * scale, y, scale)

    def _draw_students(self, x: float, y: float, scale: float):
        self._draw_boy(x, y, scale)
        self._draw_girl(x + 90 * scale, y, scale)

    def _draw_friends(self, x: float, y: float, scale: float):
        self._draw_boy(x, y, scale)
        self._draw_girl(x + 90 * scale, y, scale)

    def _draw_open_mark(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_text(x, y, text="OPEN", font=("Arial", int(12 * scale), "bold"))

    def _draw_smiley(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_oval(
            x, y, x + 50 * scale, y + 50 * scale, fill="#ffe66d", outline="#444"
        )
        c.create_oval(x + 15 * scale, y + 18 * scale, x + 20 * scale, y + 23 * scale, fill="#333")
        c.create_oval(x + 30 * scale, y + 18 * scale, x + 35 * scale, y + 23 * scale, fill="#333")
        c.create_arc(
            x + 12 * scale, y + 20 * scale, x + 38 * scale, y + 40 * scale,
            start=200, extent=140, style="arc", width=2
        )

    def _draw_sleepy(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_text(x, y, text="ZzZ", font=("Arial", int(16 * scale), "bold"), fill="#666")

    def _draw_clock(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_oval(
            x, y, x + 50 * scale, y + 50 * scale, fill="#f8f9fa", outline="#444"
        )
        c.create_line(
            x + 25 * scale, y + 25 * scale, x + 25 * scale, y + 10 * scale, width=2
        )
        c.create_line(
            x + 25 * scale, y + 25 * scale, x + 35 * scale, y + 30 * scale, width=2
        )

    def _draw_color_swatches(self, x: float, y: float, scale: float, colors: list[str]):
        c = self.scene_canvas
        size = 18 * scale
        pad = 6 * scale
        cur_x = x
        for word in colors:
            c.create_rectangle(
                cur_x, y, cur_x + size, y + size, fill=COLOR_MAP[word], outline="#444"
            )
            c.create_text(
                cur_x + size + 6 * scale, y + size / 2,
                text=word.upper(), anchor="w", font=("Arial", int(11 * scale))
            )
            cur_x += size + 70 * scale + pad

    def _draw_years_icon(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_rectangle(
            x, y, x + 40 * scale, y + 35 * scale, fill="#fff3b0", outline="#444"
        )
        c.create_rectangle(
            x, y, x + 40 * scale, y + 8 * scale, fill="#ffcf33", outline="#444"
        )
        c.create_text(
            x + 20 * scale, y + 22 * scale, text="Y", font=("Arial", int(12 * scale), "bold")
        )

    def _draw_tall_icon(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_line(x + 15 * scale, y + 40 * scale, x + 15 * scale, y, width=3)
        c.create_polygon(
            x + 15 * scale, y - 8 * scale, x + 8 * scale, y + 4 * scale,
            x + 22 * scale, y + 4 * scale, fill="#333"
        )

    def _draw_small_icon(self, x: float, y: float, scale: float):
        c = self.scene_canvas
        c.create_line(x + 15 * scale, y + 40 * scale, x + 15 * scale, y + 20 * scale, width=3)
        c.create_polygon(
            x + 15 * scale, y + 14 * scale, x + 8 * scale, y + 26 * scale,
            x + 22 * scale, y + 26 * scale, fill="#333"
        )

    def _draw_badges(self, words: list[str], x: float, y: float, max_w: float, scale: float):
        c = self.scene_canvas
        cur_x = x
        cur_y = y
        pad = 6 * scale
        for w in words:
            text = w.upper()
            bbox = c.create_text(cur_x, cur_y, text=text, anchor="w", font=("Arial", int(14 * scale)))
            x1, y1, x2, y2 = c.bbox(bbox)
            c.delete(bbox)
            w_box = (x2 - x1) + 2 * pad
            h_box = (y2 - y1) + 2 * pad
            if cur_x + w_box > x + max_w:
                cur_x = x
                cur_y -= h_box + pad
            c.create_rectangle(cur_x, cur_y, cur_x + w_box, cur_y + h_box, fill="#fff4b0", outline="#e3d06a")
            c.create_text(cur_x + pad, cur_y + pad, text=text, anchor="nw", font=("Arial", int(14 * scale)))
            cur_x += w_box + pad

    def show_positive_answer(self):
        """Zobrazí kladnou odpověď k aktuální větě."""
        sentence = self.get_current_sentence()
        if not sentence:
            return

        positive = sentence[COLUMN_POSITIVE]
        self.label_positive.config(text=positive)

        # Přečti nahlas kladnou odpověď
        speak_english(positive)

    def show_negative_answer(self):
        """Zobrazí zápornou odpověď k aktuální větě."""
        sentence = self.get_current_sentence()
        if not sentence:
            return

        negative = sentence[COLUMN_NEGATIVE]
        self.label_negative.config(text=negative)

        # Přečti nahlas zápornou odpověď
        speak_english(negative)

def main():
    root = tk.Tk()
    app = ToBeTrainerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
