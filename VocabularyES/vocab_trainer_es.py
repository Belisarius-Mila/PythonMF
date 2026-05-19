import csv
import os
import random
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

APP_NAME = "VocabularyES"
CSV_FILENAME = "VocabularyES.csv"


def resolve_spanish_voice():
    preferred = ["Jorge", "Monica", "Paulina", "Diego", "Marisol"]
    try:
        output = subprocess.check_output(["say", "-v", "?"], text=True)
    except Exception:
        return None

    available = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if not parts:
            continue
        available.append(parts[0])

    for voice in preferred:
        if voice in available:
            return voice
    return None


def resolve_csv_path():
    # Keep user data in a stable writable location when running as a bundled app.
    if getattr(sys, "frozen", False):
        support_dir = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            APP_NAME,
        )
        os.makedirs(support_dir, exist_ok=True)
        target_csv = os.path.join(support_dir, CSV_FILENAME)
        if os.path.exists(target_csv):
            return target_csv

        source_candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            source_candidates.append(os.path.join(meipass, CSV_FILENAME))

        exe_dir = os.path.dirname(sys.executable)
        app_dir = os.path.abspath(os.path.join(exe_dir, "..", "..", ".."))
        app_parent = os.path.dirname(app_dir)
        source_candidates.append(os.path.join(app_parent, CSV_FILENAME))
        source_candidates.append(os.path.join(exe_dir, CSV_FILENAME))

        for source in source_candidates:
            if os.path.exists(source):
                shutil.copy2(source, target_csv)
                return target_csv

        # First run without bundled CSV: create an empty valid file.
        with open(target_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["ES", "CZ", "Order", "Sentence", "SentenceT", "L"]
            )
            writer.writeheader()
        return target_csv

    return os.path.join(os.path.dirname(__file__), CSV_FILENAME)


class VocabularyTrainerApp:
    def __init__(self, master, csv_path):
        self.master = master
        self.csv_path = csv_path
        self.master.title("Vocabulary ES Trainer")
        self.master.configure(bg="white")
        self.master.geometry("1320x800")
        self.voice_name = resolve_spanish_voice()

        self.rows = self._load_csv()
        self.current_index = None
        self.hidden_side = None  # "ES" or "CZ"

        self.filter_var = tk.StringVar(value="all")
        self.lang_var = tk.StringVar(value="CZ")
        self.not_known_var = tk.BooleanVar(value=False)
        self.learned_var = tk.BooleanVar(value=False)
        self.no_voice_var = tk.BooleanVar(value=False)
        self.last_count_var = tk.StringVar(value="50")
        self.interval_start_var = tk.StringVar(value="1")
        self.interval_end_var = tk.StringVar(value="0")

        self.fr_var = tk.StringVar(value="")
        self.cz_var = tk.StringVar(value="")
        self.sentence_var = tk.StringVar(value="")
        self.sentence_t_var = tk.StringVar(value="")
        self.input_var = tk.StringVar(value="")
        self.fr_hint_var = tk.StringVar(value="")
        self.thumb_var = tk.StringVar(value="")
        self.hint_blink_job = None
        self.hint_blink_on = True
        self.hint_blink_toggles = 0

        self._build_ui()
        last_order = len(self.rows)
        if self.interval_end_var.get() in ("0", "", None):
            self.interval_end_var.set(str(last_order))
        self._selection_signature = None
        self._shown_in_selection = set()
        self.load_new_word()
        self.input_window = None
        self.input_tree = None
        self.edit_entry = None
        self.new_fr_var = tk.StringVar(value="")
        self.new_cz_var = tk.StringVar(value="")
        self.new_sentence_var = tk.StringVar(value="")
        self.new_sentence_t_var = tk.StringVar(value="")

    def _build_ui(self):
        top_bg = "#fff3b0"
        params_bg = "#dff4dd"
        content = tk.Frame(self.master, bg="white")
        content.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        split = tk.PanedWindow(content, orient="vertical", sashwidth=6, bd=0, bg="white")
        split.pack(fill="both", expand=True)

        top_row = tk.Frame(split, bg=top_bg)
        bottom_row = tk.Frame(split, bg="white")
        split.add(top_row, stretch="always")
        split.add(bottom_row, stretch="always")
        split.update_idletasks()
        split.sash_place(0, 0, max(1, int(content.winfo_height() * 0.5)))

        left = tk.Frame(top_row, bg=top_bg)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(top_row, bg=top_bg)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="ES", bg=top_bg, font=("Helvetica", 28, "bold")).pack(
            anchor="w"
        )
        tk.Label(left, textvariable=self.fr_var, bg=top_bg, font=("Helvetica", 30)).pack(
            anchor="w", pady=(0, 12)
        )

        tk.Label(left, text="CZ", bg=top_bg, font=("Helvetica", 28, "bold")).pack(
            anchor="w"
        )
        tk.Label(
            left,
            textvariable=self.cz_var,
            bg=top_bg,
            justify="left",
            wraplength=520,
            font=("Helvetica", 30),
        ).pack(
            anchor="w", pady=(0, 12)
        )

        input_frame = tk.Frame(left, bg=top_bg)
        input_frame.pack(fill="x", pady=(8, 8))
        tk.Label(input_frame, text="Napiš slovíčko:", bg=top_bg, font=("Helvetica", 16)).pack(anchor="w")
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            width=32,
            font=("Helvetica", 16),
            fg="black",
        )
        self.input_entry.pack(anchor="w")
        tk.Checkbutton(
            input_frame,
            text="L, že to umím",
            variable=self.learned_var,
            bg=top_bg,
            command=self.on_learned_toggled,
        ).pack(anchor="w", pady=(8, 0))
        train_buttons = tk.Frame(input_frame, bg=top_bg)
        train_buttons.pack(anchor="w", pady=(8, 0))
        tk.Button(train_buttons, text="New", command=self.load_new_word).pack(side="left")
        tk.Button(train_buttons, text="Show", command=self.show_translation).pack(
            side="left", padx=(8, 0)
        )

        tk.Label(right, text="Sentence", bg=top_bg, font=("Helvetica", 20, "bold")).pack(
            anchor="w"
        )
        tk.Label(
            right,
            textvariable=self.sentence_var,
            bg=top_bg,
            justify="left",
            wraplength=520,
            font=("Helvetica", 22),
        ).pack(anchor="w", pady=(0, 12))
        tk.Label(right, text="SentenceT", bg=top_bg, font=("Helvetica", 20, "bold")).pack(
            anchor="w"
        )
        tk.Label(
            right,
            textvariable=self.sentence_t_var,
            bg=top_bg,
            justify="left",
            wraplength=520,
            font=("Helvetica", 22),
        ).pack(anchor="w", pady=(0, 12))
        hint_frame = tk.Frame(right, bg=top_bg)
        hint_frame.pack(fill="x", pady=(8, 8))
        self.fr_hint_label = tk.Label(
            hint_frame,
            textvariable=self.fr_hint_var,
            bg=top_bg,
            fg="blue",
            justify="left",
            wraplength=520,
            font=("Helvetica", 55, "bold"),
        )
        self.fr_hint_label.pack(anchor="w")
        self.thumb_label = tk.Label(
            right,
            textvariable=self.thumb_var,
            bg=top_bg,
            fg="black",
            font=("Helvetica", 200),
        )
        self.thumb_label.pack(side="bottom", anchor="se", padx=(0, 16), pady=(0, 16))

        bottom_content = tk.Frame(bottom_row, bg="white")
        bottom_content.pack(fill="both", expand=True, padx=6, pady=(8, 0))

        settings_panel = tk.Frame(bottom_content, bg=params_bg)
        settings_panel.pack(side="left", anchor="nw", padx=(0, 20), pady=(4, 4))

        filter_box = tk.LabelFrame(settings_panel, text="Výběr slovíček", bg=params_bg)
        filter_box.pack(anchor="w", pady=(0, 8))

        all_row = tk.Frame(filter_box, bg=params_bg)
        all_row.pack(anchor="w", pady=(0, 4))
        tk.Radiobutton(
            all_row,
            text="All",
            variable=self.filter_var,
            value="all",
            bg=params_bg,
            command=self.load_new_word,
        ).pack(side="left")

        last_row = tk.Frame(filter_box, bg=params_bg)
        last_row.pack(anchor="w", pady=(0, 4))
        tk.Radiobutton(
            last_row,
            text="Last",
            variable=self.filter_var,
            value="last",
            bg=params_bg,
            command=self.load_new_word,
        ).pack(side="left")
        tk.Entry(last_row, textvariable=self.last_count_var, width=6).pack(
            side="left", padx=(6, 0)
        )
        tk.Label(last_row, text="(count)", bg=params_bg).pack(side="left", padx=(6, 0))

        interval_row = tk.Frame(filter_box, bg=params_bg)
        interval_row.pack(anchor="w")
        tk.Radiobutton(
            interval_row,
            text="Interval",
            variable=self.filter_var,
            value="interval",
            bg=params_bg,
            command=self.load_new_word,
        ).pack(side="left")
        tk.Label(interval_row, text="Start", bg=params_bg).pack(side="left", padx=(6, 0))
        tk.Entry(interval_row, textvariable=self.interval_start_var, width=6).pack(
            side="left", padx=(4, 0)
        )
        tk.Label(interval_row, text="End", bg=params_bg).pack(side="left", padx=(8, 0))
        tk.Entry(interval_row, textvariable=self.interval_end_var, width=6).pack(
            side="left", padx=(4, 0)
        )

        lang_box = tk.LabelFrame(settings_panel, text="Jazyk nabídky", bg=params_bg)
        lang_box.pack(anchor="w", pady=(0, 8))

        tk.Radiobutton(
            lang_box,
            text="ES",
            variable=self.lang_var,
            value="ES",
            bg=params_bg,
            command=self.load_new_word,
        ).pack(anchor="w")
        tk.Radiobutton(
            lang_box,
            text="CZ",
            variable=self.lang_var,
            value="CZ",
            bg=params_bg,
            command=self.load_new_word,
        ).pack(anchor="w")

        options_box = tk.LabelFrame(settings_panel, text="Filtry", bg=params_bg)
        options_box.pack(anchor="w")

        tk.Checkbutton(
            options_box,
            text="Not known (L = ne)",
            variable=self.not_known_var,
            bg=params_bg,
            command=self.load_new_word,
        ).pack(anchor="w")
        tk.Checkbutton(
            options_box,
            text="NoVoice",
            variable=self.no_voice_var,
            bg=params_bg,
        ).pack(anchor="w")
        controls = tk.Frame(bottom_content, bg="white")
        controls.pack(side="right", anchor="se", padx=(20, 10), pady=(10, 12))
        tk.Button(controls, text="Input", command=self.open_input_window, width=10).pack(
            side="right"
        )

    def _load_csv(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(self.csv_path)
        with open(self.csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader]
        rows = self._repair_rows(rows)
        return rows

    def _repair_rows(self, rows):
        repaired = []
        for row in rows:
            fr = ((row.get("ES") or row.get("IT") or row.get("FR") or "").strip())
            cz = (row.get("CZ") or "").strip()
            sentence = (row.get("Sentence") or "").strip()
            sentence_t = (row.get("SentenceT") or "").strip()
            learned = (row.get("L") or "ne").strip().lower()

            if not fr and not cz and not sentence:
                continue

            if learned not in ("ano", "ne"):
                learned = "ne"

            repaired.append(
                {
                    "ES": fr,
                    "CZ": cz,
                    "Order": "",  # recalc below
                    "Sentence": sentence,
                    "SentenceT": sentence_t,
                    "L": learned,
                }
            )

        for i, row in enumerate(repaired, start=1):
            row["Order"] = str(i)

        return repaired

    def _write_rows(self, rows):
        fieldnames = ["ES", "CZ", "Order", "Sentence", "SentenceT", "L"]
        with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _save_csv(self):
        if not self.rows:
            return
        self._write_rows(self.rows)

    def _filtered_indices(self):
        indices = list(range(len(self.rows)))
        if self.filter_var.get() == "last":
            try:
                count = int(self.last_count_var.get())
            except ValueError:
                count = 50
            if count <= 0:
                count = 50
            indices = indices[-count:]
        elif self.filter_var.get() == "interval":
            last_order = len(self.rows)
            try:
                start = int(self.interval_start_var.get())
            except ValueError:
                start = 1
            try:
                end = int(self.interval_end_var.get())
            except ValueError:
                end = last_order
            if end <= 0 or end > last_order:
                end = last_order
            if start < 1:
                start = 1
            if end <= start:
                messagebox.showwarning("Interval", "End musí být větší než Start.")
                return []
            indices = [i for i in indices if start <= (i + 1) <= end]

        if self.not_known_var.get():
            indices = [i for i in indices if self.rows[i].get("L", "").lower() != "ano"]

        return indices

    def _current_selection_signature(self, indices):
        return (
            tuple(indices),
            self.filter_var.get(),
            self.lang_var.get(),
            self.not_known_var.get(),
            self.last_count_var.get(),
            self.interval_start_var.get(),
            self.interval_end_var.get(),
        )

    def _cz_meanings_for_es(self, es_word):
        key = (es_word or "").strip().casefold()
        if not key:
            return []
        meanings = []
        seen = set()
        for row in self.rows:
            row_es = (row.get("ES") or "").strip().casefold()
            row_cz = (row.get("CZ") or "").strip()
            if row_es != key or not row_cz:
                continue
            marker = row_cz.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            meanings.append(row_cz)
        return meanings

    def load_new_word(self):
        if self.current_index is not None:
            self._persist_current_learned()

        indices = self._filtered_indices()
        if not indices:
            self._selection_signature = None
            self._shown_in_selection.clear()
            messagebox.showinfo("Info", "Žádná slovíčka pro aktuální filtr.")
            return

        signature = self._current_selection_signature(indices)
        if signature != self._selection_signature:
            self._selection_signature = signature
            self._shown_in_selection.clear()

        available = [i for i in indices if i not in self._shown_in_selection]
        if not available:
            self._shown_in_selection.clear()
            available = list(indices)

        self.current_index = random.choice(available)
        self._shown_in_selection.add(self.current_index)
        row = self.rows[self.current_index]

        fr = row.get("ES", "")
        cz = row.get("CZ", "")
        sentence = row.get("Sentence", "")
        learned = row.get("L", "").strip().lower() == "ano"

        self.learned_var.set(learned)
        self.input_var.set("")
        self.sentence_var.set("")
        self.sentence_t_var.set("")
        self.fr_hint_var.set("")
        self.thumb_var.set("")
        self.input_entry.configure(fg="black")
        self._stop_hint_blink()

        if self.lang_var.get() == "ES":
            self.fr_var.set(fr)
            self.cz_var.set("???")
            self.hidden_side = "CZ"
        else:
            self.cz_var.set(cz)
            self.fr_var.set("???")
            self.hidden_side = "ES"

    def show_translation(self):
        if self.current_index is None:
            return

        row = self.rows[self.current_index]
        fr = row.get("ES", "").strip()
        typed = self.input_var.get().strip()
        self.thumb_var.set("👍" if typed and typed.casefold() == fr.casefold() else "")

        if self.lang_var.get() == "CZ":
            if typed and typed.casefold() != fr.casefold():
                self.fr_hint_var.set(fr)
                self.input_entry.configure(fg="red")
            else:
                self.input_entry.configure(fg="black")
        else:
            typed = self.input_var.get().strip()
            allowed_cz = self._cz_meanings_for_es(row.get("ES", ""))
            if not allowed_cz:
                allowed_cz = [row.get("CZ", "").strip()]
            allowed_normalized = {value.casefold() for value in allowed_cz if value}
            if typed and typed.casefold() not in allowed_normalized:
                self.input_entry.configure(fg="red")
            else:
                self.input_entry.configure(fg="black")

        # V obou režimech vždy zobraz a rozblikej FR nápovědu.
        self.fr_hint_var.set(fr)
        self._start_hint_blink()

        self.fr_var.set(row.get("ES", ""))
        all_meanings = self._cz_meanings_for_es(row.get("ES", ""))
        self.cz_var.set("\n".join(all_meanings) if all_meanings else row.get("CZ", ""))
        self.sentence_var.set(row.get("Sentence", ""))
        self.sentence_t_var.set(row.get("SentenceT", ""))
        self.hidden_side = None
        self._speak_current(row)

    def on_learned_toggled(self):
        self._persist_current_learned()

    def _start_hint_blink(self):
        self._stop_hint_blink()
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.fr_hint_label.configure(fg="blue")
        self.hint_blink_job = self.master.after(350, self._toggle_hint_blink)

    def _stop_hint_blink(self):
        if self.hint_blink_job is not None:
            self.master.after_cancel(self.hint_blink_job)
            self.hint_blink_job = None
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        if hasattr(self, "fr_hint_label"):
            self.fr_hint_label.configure(fg="blue")

    def _toggle_hint_blink(self):
        if not self.fr_hint_var.get().strip():
            self._stop_hint_blink()
            return
        if self.hint_blink_toggles >= 6:
            self._stop_hint_blink()
            return
        self.hint_blink_on = not self.hint_blink_on
        self.hint_blink_toggles += 1
        self.fr_hint_label.configure(fg="blue" if self.hint_blink_on else "white")
        self.hint_blink_job = self.master.after(350, self._toggle_hint_blink)

    def _persist_current_learned(self):
        if self.current_index is None:
            return
        new_value = "ano" if self.learned_var.get() else "ne"
        if self.rows[self.current_index].get("L") == new_value:
            return
        self.rows[self.current_index]["L"] = new_value
        self._save_csv()

    def _speak_current(self, row):
        if self.no_voice_var.get():
            return
        fr = row.get("ES", "").strip()
        sentence = row.get("Sentence", "").strip()
        text = ". ".join([t for t in (fr, sentence) if t])
        if not text:
            return
        try:
            if self.voice_name:
                subprocess.Popen(["say", "-v", self.voice_name, text])
            else:
                subprocess.Popen(["say", text])
        except Exception:
            pass

    def open_input_window(self):
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.lift()
            return

        win = tk.Toplevel(self.master)
        win.title("Input - VocabularyES.csv")
        win.geometry("1320x800")
        win.minsize(1100, 700)
        win.configure(bg="white")
        self.input_window = win

        list_frame = tk.Frame(win, bg="white")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(12, 8))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        columns = ("Order", "ES", "CZ", "Sentence", "SentenceT", "L")
        tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)
        self.input_tree = tree

        tree.heading("Order", text="Order")
        tree.heading("ES", text="ES")
        tree.heading("CZ", text="CZ")
        tree.heading("Sentence", text="Sentence")
        tree.heading("SentenceT", text="SentenceT")
        tree.heading("L", text="L")

        tree.column("Order", width=80, anchor="center")
        tree.column("ES", width=200, anchor="w")
        tree.column("CZ", width=220, anchor="w")
        tree.column("Sentence", width=340, anchor="w")
        tree.column("SentenceT", width=340, anchor="w")
        tree.column("L", width=60, anchor="center")

        style = ttk.Style(win)
        style.configure("Treeview", font=("Helvetica", 14), rowheight=24)
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))

        tree.bind("<Double-1>", self.on_tree_double_click)

        self._populate_input_list()

        form = tk.Frame(win, bg="white")
        form.pack(fill="x", padx=12, pady=(0, 12))

        tk.Label(form, text="ES:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(form, textvariable=self.new_fr_var, width=30).grid(
            row=0, column=1, sticky="w", padx=(6, 12)
        )

        tk.Label(form, text="CZ:", bg="white").grid(row=0, column=2, sticky="w")
        tk.Entry(form, textvariable=self.new_cz_var, width=30).grid(
            row=0, column=3, sticky="w", padx=(6, 12)
        )

        tk.Label(form, text="Sentence:", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(form, textvariable=self.new_sentence_var, width=34).grid(
            row=1, column=1, sticky="w", padx=(6, 12), pady=(6, 0)
        )
        tk.Label(form, text="SentenceT:", bg="white").grid(row=1, column=2, sticky="w", pady=(6, 0))
        tk.Entry(form, textvariable=self.new_sentence_t_var, width=34).grid(
            row=1, column=3, sticky="w", padx=(6, 12), pady=(6, 0)
        )

        buttons_left = tk.Frame(form, bg="white")
        buttons_left.grid(row=0, column=4, rowspan=2, sticky="w", padx=(6, 0))
        tk.Button(buttons_left, text="Add Row", command=self.add_new_row).pack(side="left")
        tk.Button(buttons_left, text="Insert Row", command=self.insert_row).pack(
            side="left", padx=(8, 0)
        )
        tk.Button(buttons_left, text="Delete", command=self.delete_selected_row).pack(
            side="left", padx=(8, 0)
        )

        form.grid_columnconfigure(5, weight=1)
        tk.Button(form, text="Training", command=win.destroy).grid(
            row=0, column=6, rowspan=2, sticky="e", padx=(8, 0)
        )

    def _populate_input_list(self):
        if not self.input_tree:
            return
        for item in self.input_tree.get_children():
            self.input_tree.delete(item)
        for idx, row in enumerate(self.rows):
            self.input_tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    row.get("Order", ""),
                    row.get("ES", ""),
                    row.get("CZ", ""),
                    row.get("Sentence", ""),
                    row.get("SentenceT", ""),
                    row.get("L", ""),
                ),
            )

    def add_new_row(self):
        fr = self.new_fr_var.get().strip()
        cz = self.new_cz_var.get().strip()
        sentence = self.new_sentence_var.get().strip()
        sentence_t = self.new_sentence_t_var.get().strip()
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej ES i CZ.")
            return

        next_order = 1
        if self.rows:
            try:
                next_order = max(int(r.get("Order", "0") or 0) for r in self.rows) + 1
            except ValueError:
                next_order = len(self.rows) + 1

        new_row = {
            "ES": fr,
            "CZ": cz,
            "Order": str(next_order),
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
        }
        self.rows.append(new_row)
        self._save_csv()

        if self.input_tree:
            self.input_tree.insert(
                "",
                tk.END,
                iid=str(len(self.rows) - 1),
                values=(
                    new_row.get("Order", ""),
                    new_row.get("ES", ""),
                    new_row.get("CZ", ""),
                    new_row.get("Sentence", ""),
                    new_row.get("SentenceT", ""),
                    new_row.get("L", ""),
                ),
            )
            children = self.input_tree.get_children()
            if children:
                self.input_tree.see(children[-1])

        self.new_fr_var.set("")
        self.new_cz_var.set("")
        self.new_sentence_var.set("")
        self.new_sentence_t_var.set("")

    def insert_row(self):
        if not self.input_tree:
            return

        selected = self.input_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Nejdřív vyber řádek, za který chceš vložit nový.")
            return

        fr = self.new_fr_var.get().strip()
        cz = self.new_cz_var.get().strip()
        sentence = self.new_sentence_var.get().strip()
        sentence_t = self.new_sentence_t_var.get().strip()
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej ES i CZ.")
            return

        try:
            selected_idx = int(selected[0])
        except ValueError:
            return
        if selected_idx < 0 or selected_idx >= len(self.rows):
            return

        new_row = {
            "ES": fr,
            "CZ": cz,
            "Order": "",
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
        }
        insert_idx = selected_idx + 1
        self.rows.insert(insert_idx, new_row)
        for i, row in enumerate(self.rows, start=1):
            row["Order"] = str(i)
        self._save_csv()
        self._populate_input_list()

        if self.input_tree:
            new_iid = str(insert_idx)
            self.input_tree.selection_set(new_iid)
            self.input_tree.focus(new_iid)
            self.input_tree.see(new_iid)

        self.new_fr_var.set("")
        self.new_cz_var.set("")
        self.new_sentence_var.set("")
        self.new_sentence_t_var.set("")

    def delete_selected_row(self):
        if not self.input_tree:
            return
        selected = self.input_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Nejdřív vyber řádek.")
            return

        item_id = selected[0]
        if not messagebox.askyesno("Smazat", "Opravdu chceš smazat vybraný řádek?"):
            return

        try:
            idx = int(item_id)
        except ValueError:
            return

        if 0 <= idx < len(self.rows):
            del self.rows[idx]
            # recompute Order
            for i, row in enumerate(self.rows, start=1):
                row["Order"] = str(i)
            self._save_csv()
            self._populate_input_list()
    def _read_tree_item(self, item_id):
        if not self.input_tree:
            return
        values = self.input_tree.item(item_id, "values")
        if not values:
            return

        # Columns: Order, ES, CZ, Sentence, SentenceT, L
        fr = (values[1] if len(values) > 1 else "").strip()
        sentence = (values[3] if len(values) > 3 else "").strip()
        self._speak_current({"ES": fr, "Sentence": sentence})

    def on_tree_double_click(self, event):
        if not self.input_tree:
            return
        region = self.input_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.input_tree.identify_row(event.y)
        col_id = self.input_tree.identify_column(event.x)
        if not row_id or not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        columns = ("Order", "ES", "CZ", "Sentence", "SentenceT", "L")
        if col_index < 0 or col_index >= len(columns):
            return
        column_name = columns[col_index]

        # prevent editing Order directly
        if column_name == "Order":
            self.input_tree.selection_set(row_id)
            self.input_tree.focus(row_id)
            self._read_tree_item(row_id)
            return

        x, y, width, height = self.input_tree.bbox(row_id, col_id)
        value = self.input_tree.set(row_id, column_name)

        if self.edit_entry is not None:
            self.edit_entry.destroy()

        self.edit_entry = tk.Entry(self.input_tree, font=("Helvetica", 14))
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, value)
        self.edit_entry.focus()

        def save_edit(event=None):
            new_value = self.edit_entry.get()
            self.input_tree.set(row_id, column_name, new_value)
            self.edit_entry.destroy()
            self.edit_entry = None

            try:
                idx = int(row_id)
            except ValueError:
                return
            if 0 <= idx < len(self.rows):
                old_value = self.rows[idx].get(column_name, "")
                if old_value != new_value:
                    self.rows[idx][column_name] = new_value
                    self._save_csv()

        def cancel_edit(event=None):
            if self.edit_entry is not None:
                self.edit_entry.destroy()
                self.edit_entry = None

        self.edit_entry.bind("<Return>", save_edit)
        self.edit_entry.bind("<Escape>", cancel_edit)
        self.edit_entry.bind("<FocusOut>", save_edit)


if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyTrainerApp(root, resolve_csv_path())
    root.mainloop()
