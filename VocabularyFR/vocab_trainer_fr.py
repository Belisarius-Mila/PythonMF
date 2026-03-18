import csv
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

APP_NAME = "VocabularyFR"
CSV_FILENAME = "VocabularyFR.csv"
VERBE_CSV_FILENAME = "VerbeFR.csv"

# Keep Python defaults intentionally small; most mapping is loaded from Pict/mapping.json.
SYNONYM_IMAGE_MAP = {}
FEMALE_PRONOUNS = {"ona", "elle"}
MALE_PRONOUNS = {"on", "il", "lui"}
AMBIGUOUS_PRONOUNS = {"ja", "je", "moi", "vy", "vous"}
CONJUNCTION_WORDS = {"a", "ale", "nebo", "et", "ou", "mais"}
PREPOSITION_WORDS = {"na", "v", "ve", "do", "z", "u", "k", "sur", "dans", "de", "en"}
ADJ_ADV_WORDS = {"prislovce", "pridavnejmeno", "adverbe", "adjective", "adjectif"}


def _is_macos_app_runtime():
    # Some macOS app launchers don't reliably expose sys.frozen.
    exe = os.path.abspath(sys.executable or "")
    file_path = os.path.abspath(__file__)
    return (
        ".app/Contents/MacOS/" in exe
        or ".app/Contents/Resources/" in file_path
        or ".app/Contents/" in exe
    )


def _app_support_dir():
    return os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        APP_NAME,
    )


def _app_container_dir():
    exe_dir = os.path.dirname(sys.executable)
    # .../VocabularyFR.app/Contents/MacOS -> parent folder that contains VocabularyFR.app
    return os.path.abspath(os.path.join(exe_dir, "..", "..", ".."))


def _app_parent_dir():
    return os.path.dirname(_app_container_dir())


def resolve_csv_path():
    # Prefer "portable" data next to .app when possible, fallback to Application Support.
    if getattr(sys, "frozen", False) or _is_macos_app_runtime():
        exe_dir = os.path.dirname(sys.executable)
        app_container_dir = _app_container_dir()
        app_parent = _app_parent_dir()
        # "Portable" CSV should live in the folder that contains the .app bundle
        # (e.g. .../PythonMF/VocabularyFR), not inside the .app and not one level above.
        portable_csv = os.path.join(app_container_dir, CSV_FILENAME)

        if os.path.exists(portable_csv):
            return portable_csv

        support_dir = _app_support_dir()
        os.makedirs(support_dir, exist_ok=True)
        target_csv = os.path.join(support_dir, CSV_FILENAME)

        source_candidates = []
        # If user already has data in Application Support, migrate a copy next to .app first.
        if os.path.exists(target_csv):
            source_candidates.append(target_csv)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            source_candidates.append(os.path.join(meipass, CSV_FILENAME))

        source_candidates.append(os.path.join(app_container_dir, CSV_FILENAME))
        source_candidates.append(os.path.join(app_parent, CSV_FILENAME))
        source_candidates.append(os.path.join(exe_dir, CSV_FILENAME))

        # Try to initialize a portable CSV next to .app first.
        for source in source_candidates:
            if os.path.exists(source):
                try:
                    shutil.copy2(source, portable_csv)
                    return portable_csv
                except Exception:
                    continue

        # Then initialize Application Support CSV.
        if os.path.exists(target_csv):
            return target_csv
        for source in source_candidates:
            if os.path.exists(source):
                shutil.copy2(source, target_csv)
                return target_csv

        # First run without bundled CSV: create an empty valid file.
        with open(target_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_fr"]
            )
            writer.writeheader()
        return target_csv

    return os.path.join(os.path.dirname(__file__), CSV_FILENAME)


def resolve_verbe_csv_path(base_csv_path):
    # Keep verbs data aligned with the selected vocabulary CSV location.
    if base_csv_path:
        candidate = os.path.join(os.path.dirname(base_csv_path), VERBE_CSV_FILENAME)
        if os.path.exists(candidate):
            return candidate

    # Bundled app fallback: resolve in portable location first, then App Support.
    if getattr(sys, "frozen", False) or _is_macos_app_runtime():
        exe_dir = os.path.dirname(sys.executable)
        app_container_dir = _app_container_dir()
        app_parent = _app_parent_dir()
        portable_csv = os.path.join(app_container_dir, VERBE_CSV_FILENAME)
        if os.path.exists(portable_csv):
            return portable_csv

        support_dir = _app_support_dir()
        os.makedirs(support_dir, exist_ok=True)
        target_csv = os.path.join(support_dir, VERBE_CSV_FILENAME)

        source_candidates = []
        if os.path.exists(target_csv):
            source_candidates.append(target_csv)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            source_candidates.append(os.path.join(meipass, VERBE_CSV_FILENAME))

        source_candidates.append(os.path.join(app_container_dir, VERBE_CSV_FILENAME))
        source_candidates.append(os.path.join(app_parent, VERBE_CSV_FILENAME))
        source_candidates.append(os.path.join(exe_dir, VERBE_CSV_FILENAME))

        # Try to initialize portable verbs CSV next to .app first.
        for source in source_candidates:
            if os.path.exists(source):
                try:
                    shutil.copy2(source, portable_csv)
                    return portable_csv
                except Exception:
                    continue

        # Then initialize Application Support verbs CSV.
        if os.path.exists(target_csv):
            return target_csv
        for source in source_candidates:
            if os.path.exists(source):
                shutil.copy2(source, target_csv)
                return target_csv

        # No source found; return target path so caller can show clear missing-file error.
        return target_csv

    return os.path.join(os.path.dirname(__file__), VERBE_CSV_FILENAME)


class VocabularyTrainerApp:
    def __init__(self, master, csv_path):
        self.master = master
        self.csv_path = csv_path
        self.master.title("Vocabulary FR Trainer")
        self.master.configure(bg="white")
        self.master.geometry("1320x800")
        self.master.protocol("WM_DELETE_WINDOW", self._on_main_window_close)

        self.rows = self._load_csv()
        self.current_index = None
        self.hidden_side = None  # "FR" or "CZ"

        self.filter_var = tk.StringVar(value="all")
        self.lang_var = tk.StringVar(value="CZ")
        self.not_known_var = tk.BooleanVar(value=False)
        self.ht_only_var = tk.BooleanVar(value=False)
        self.learned_var = tk.BooleanVar(value=False)
        self.hard_training_var = tk.BooleanVar(value=False)
        self.no_voice_var = tk.BooleanVar(value=False)
        self.last_count_var = tk.StringVar(value="50")
        self.interval_start_var = tk.StringVar(value="1")
        self.interval_end_var = tk.StringVar(value="0")

        self.fr_var = tk.StringVar(value="")
        self.gender_var = tk.StringVar(value="")
        self.article_var = tk.StringVar(value="")
        self.cz_var = tk.StringVar(value="")
        self.sentence_var = tk.StringVar(value="")
        self.sentence_t_var = tk.StringVar(value="")
        self.input_var = tk.StringVar(value="")
        self.fr_hint_var = tk.StringVar(value="")
        self.thumb_var = tk.StringVar(value="")
        self.remaining_var = tk.StringVar(value="0")
        self.hint_blink_job = None
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.hint_blink_colors = ("blue", "white")
        self.hint_blink_color_index = 0
        self.turbo_mode = False
        self.turbo_running = False
        self.turbo_selection_signature = None
        self.turbo_shown_in_selection = set()
        self.turbo_after_job = None
        self.turbo_speech_generation = 0
        self.fr_voice = "Thomas"
        self.cz_voice = self._resolve_cz_voice()
        self.picture_photo = None
        self.picture_base_dirs = self._build_picture_base_dirs()
        self.synonym_image_map = dict(SYNONYM_IMAGE_MAP)
        self._load_external_mapping()
        self.picture_stems = self._discover_picture_stems()

        self._build_ui()
        last_order = len(self.rows)
        if self.interval_end_var.get() in ("0", "", None):
            self.interval_end_var.set(str(last_order))
        self._selection_signature = None
        self._shown_in_selection = set()
        self.load_new_word()
        self.input_window = None
        self.input_tree = None
        self.input_sort_mode = "order"
        self.edit_entry = None
        self.gender_popup_menu = None
        self.verbes_window = None
        self.verbes_tree = None
        self.verbe_rows = []
        self.verbe_csv_path = resolve_verbe_csv_path(self.csv_path)
        self._sync_portable_and_appsupport_on_startup()
        self.verbe_detail_vars = {}
        self.verbe_text_widgets = {}
        self.verbe_groups = []
        self.new_fr_entry = None
        self.new_cz_entry = None
        self.gender_popup_menu = None
        self.new_fr_var = tk.StringVar(value="")
        self.new_cz_var = tk.StringVar(value="")
        self.new_sentence_var = tk.StringVar(value="")
        self.new_sentence_t_var = tk.StringVar(value="")
        self.new_gender_fr_var = tk.StringVar(value="")

    def _portable_data_dir(self):
        if getattr(sys, "frozen", False) or _is_macos_app_runtime():
            return _app_container_dir()
        return os.path.dirname(__file__)

    def _copy_if_exists(self, src, dst):
        if not src or not dst or not os.path.exists(src):
            return False
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False

    def _sync_portable_and_appsupport_on_startup(self):
        # Goal: after unzip/install, keep Application Support in sync with CSVs
        # placed next to the .app in PythonMF/VocabularyFR.
        if not (getattr(sys, "frozen", False) or _is_macos_app_runtime()):
            return
        portable_dir = self._portable_data_dir()
        support_dir = _app_support_dir()
        os.makedirs(support_dir, exist_ok=True)
        for filename in (CSV_FILENAME, VERBE_CSV_FILENAME):
            src = os.path.join(portable_dir, filename)
            dst = os.path.join(support_dir, filename)
            self._copy_if_exists(src, dst)

    def _sync_csvs_to_portable_on_exit(self):
        # Goal: when app closes, mirror active CSV files back next to the app.
        if not (getattr(sys, "frozen", False) or _is_macos_app_runtime()):
            return
        portable_dir = self._portable_data_dir()
        os.makedirs(portable_dir, exist_ok=True)
        pairs = [
            (self.csv_path, os.path.join(portable_dir, CSV_FILENAME)),
            (self.verbe_csv_path, os.path.join(portable_dir, VERBE_CSV_FILENAME)),
        ]
        for src, dst in pairs:
            self._copy_if_exists(src, dst)

    def _on_main_window_close(self):
        try:
            self.stop_turbo()
        except Exception:
            pass
        try:
            self._persist_current_status_flags()
        except Exception:
            pass
        try:
            self._sync_csvs_to_portable_on_exit()
        except Exception:
            pass
        self.master.destroy()

    def _paste_into_entry(self, event):
        try:
            text = self.master.clipboard_get()
        except tk.TclError:
            return "break"
        # Entry is single-line; flatten multiline pasted content.
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
        widget = event.widget
        try:
            widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        widget.insert("insert", text)
        return "break"

    def _bind_entry_paste(self, entry):
        entry.bind("<Command-v>", self._paste_into_entry)
        entry.bind("<Control-v>", self._paste_into_entry)
        entry.bind("<Command-V>", self._paste_into_entry)
        entry.bind("<Control-V>", self._paste_into_entry)

    def _build_ui(self):
        top_bg = "#fff3b0"
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

        fr_row = tk.Frame(left, bg=top_bg)
        fr_row.pack(anchor="w", fill="x")
        tk.Label(
            fr_row,
            text="FR 🇫🇷",
            bg=top_bg,
            font=("Helvetica", 28, "bold"),
            width=6,
            anchor="w",
        ).pack(side="left", anchor="n", padx=(0, 12))
        tk.Label(
            fr_row, textvariable=self.fr_var, bg=top_bg, justify="left", wraplength=460, font=("Helvetica", 30)
        ).pack(side="left", anchor="w")

        article_row = tk.Frame(left, bg=top_bg, height=18)
        article_row.pack(anchor="w", fill="x", pady=(0, 2))
        article_row.pack_propagate(False)

        cz_row = tk.Frame(left, bg=top_bg)
        cz_row.pack(anchor="w", fill="x", pady=(0, 12))
        tk.Label(
            cz_row,
            text="CZ",
            bg=top_bg,
            font=("Helvetica", 28, "bold"),
            width=6,
            anchor="w",
        ).pack(side="left", anchor="n", padx=(0, 12))
        tk.Label(
            cz_row,
            textvariable=self.cz_var,
            bg=top_bg,
            justify="left",
            wraplength=460,
            font=("Helvetica", 30),
        ).pack(side="left", anchor="w")

        input_frame = tk.Frame(left, bg=top_bg)
        input_frame.pack(fill="x", pady=(8, 8))
        tk.Label(input_frame, text="Napiš slovíčko:", bg=top_bg, font=("Helvetica", 16)).pack(anchor="w")
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            width=24,
            font=("Helvetica", 16),
            fg="black",
        )
        self._bind_entry_paste(self.input_entry)
        self.input_entry.pack(anchor="w")
        tk.Checkbutton(
            input_frame,
            text="L, že to umím",
            variable=self.learned_var,
            bg=top_bg,
            command=self.on_learned_toggled,
        ).pack(anchor="w", pady=(8, 0))
        tk.Checkbutton(
            input_frame,
            text="HT neumím!!!",
            variable=self.hard_training_var,
            bg=top_bg,
            command=self.on_hard_training_toggled,
        ).pack(anchor="w")
        train_buttons = tk.Frame(input_frame, bg=top_bg)
        train_buttons.pack(anchor="w", pady=(8, 0))
        tk.Button(train_buttons, text="New", command=self.load_new_word, width=8).grid(
            row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w"
        )
        tk.Button(train_buttons, text="Read", command=self.show_translation, width=8).grid(
            row=1, column=0, padx=(0, 8), sticky="w"
        )
        tk.Button(train_buttons, text="Turbo", command=self.load_turbo_word, width=8).grid(
            row=0, column=1, pady=(0, 4), sticky="w"
        )
        tk.Button(train_buttons, text="End", command=self.stop_turbo, width=8).grid(
            row=1, column=1, sticky="w"
        )

        sentence_row = tk.Frame(right, bg=top_bg)
        sentence_row.pack(anchor="w", fill="x", pady=(5, 0))
        tk.Label(
            sentence_row,
            textvariable=self.sentence_var,
            bg=top_bg,
            justify="left",
            wraplength=520,
            font=("Helvetica", 24),
        ).pack(anchor="w")

        article_spacer = tk.Frame(right, bg=top_bg, height=24)
        article_spacer.pack(anchor="w", fill="x", pady=(0, 4))
        article_spacer.pack_propagate(False)

        sentence_t_row = tk.Frame(right, bg=top_bg)
        sentence_t_row.pack(anchor="w", fill="x", pady=(0, 12))
        tk.Label(
            sentence_t_row,
            textvariable=self.sentence_t_var,
            bg=top_bg,
            justify="left",
            wraplength=520,
            font=("Helvetica", 22, "italic"),
        ).pack(anchor="w")
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
        self.fr_hint_article_row = tk.Frame(hint_frame, bg=top_bg)
        self.fr_hint_article_row.pack(anchor="w", pady=(4, 0))
        self.fr_hint_gender_label = tk.Label(
            self.fr_hint_article_row,
            textvariable=self.gender_var,
            bg="white",
            fg="black",
            justify="left",
            font=("Helvetica", 18, "bold"),
            bd=1,
            relief="solid",
            padx=8,
            pady=2,
        )
        self.fr_hint_gender_label.pack(side="left", anchor="w", pady=(3, 0))
        self.fr_hint_article_label = tk.Label(
            self.fr_hint_article_row,
            textvariable=self.article_var,
            bg=top_bg,
            fg="black",
            justify="left",
            wraplength=520,
            font=("Helvetica", 26),
        )
        self.fr_hint_article_label.pack(side="left", anchor="w", padx=(10, 0))
        self.thumb_label = tk.Label(
            right,
            textvariable=self.thumb_var,
            bg=top_bg,
            fg="black",
            font=("Helvetica", 200),
        )
        self.thumb_label.pack(side="bottom", anchor="se", padx=(0, 16), pady=(0, 16))
        self.remaining_panel = tk.Frame(right, bg="#ffe680", bd=2, relief="ridge")
        self.remaining_panel.place(relx=0.98, rely=0.98, anchor="se")
        tk.Label(
            self.remaining_panel,
            text="Zbývá:",
            bg="#ffe680",
            fg="black",
            font=("Helvetica", 14, "bold"),
        ).pack(side="left", padx=(8, 4), pady=(4, 4))
        self.remaining_label = tk.Label(
            self.remaining_panel,
            textvariable=self.remaining_var,
            bg="#ffe680",
            fg="black",
            font=("Helvetica", 26, "bold"),
        )
        self.remaining_label.pack(side="left", padx=(0, 8), pady=(2, 4))
        self.remaining_panel.lift()

        params_bg = "#dff4dd"
        bottom_content = tk.Frame(bottom_row, bg="white")
        bottom_content.pack(fill="both", expand=True, padx=6, pady=(8, 0))

        settings_panel = tk.Frame(bottom_content, bg=params_bg, bd=2, relief="groove")
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
            text="FR",
            variable=self.lang_var,
            value="FR",
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
            text="HT (procvičování!!!)",
            variable=self.ht_only_var,
            bg=params_bg,
            command=self.load_new_word,
        ).pack(anchor="w")
        tk.Checkbutton(
            options_box,
            text="NoVoice",
            variable=self.no_voice_var,
            bg=params_bg,
        ).pack(anchor="w")

        picture_panel = tk.Frame(bottom_content, bg="white")
        picture_panel.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=(4, 8), anchor="nw")
        picture_card = tk.Frame(picture_panel, bg="white", bd=2, relief="groove")
        picture_card.place(relx=0.5, y=4, anchor="n")
        self.picture_label = tk.Label(
            picture_card,
            bg="white",
            width=240,
            height=240,
        )
        self.picture_label.pack(padx=10, pady=10)

        controls = tk.Frame(bottom_content, bg="white")
        controls.pack(side="right", anchor="se", padx=(20, 10), pady=(10, 12))
        tk.Button(controls, text="Verbes", command=self.open_verbes_window, width=10).pack(
            side="right", padx=(0, 8)
        )
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
            fr = (row.get("FR") or "").strip()
            cz = (row.get("CZ") or "").strip()
            sentence = (row.get("Sentence") or "").strip()
            sentence_t = (row.get("SentenceT") or "").strip()
            learned = (row.get("L") or "ne").strip().lower()
            hard_training = (row.get("HT") or "ne").strip().lower()
            gender_fr = (row.get("gender_fr") or "").strip().lower()

            if not fr and not cz and not sentence:
                continue

            if learned not in ("ano", "ne"):
                learned = "ne"
            if hard_training not in ("ano", "ne"):
                hard_training = "ne"
            # Contradiction safeguard: HT means "I still don't know it".
            if learned == "ano" and hard_training == "ano":
                learned = "ne"

            repaired.append(
                {
                    "FR": fr,
                    "CZ": cz,
                    "Order": "",  # recalc below
                    "Sentence": sentence,
                    "SentenceT": sentence_t,
                    "L": learned,
                    "HT": hard_training,
                    "gender_fr": gender_fr if gender_fr in ("m", "f") else "",
                }
            )

        for i, row in enumerate(repaired, start=1):
            row["Order"] = str(i)

        return repaired

    def _write_rows(self, rows):
        fieldnames = ["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_fr"]
        with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _save_csv(self):
        if not self.rows:
            return
        self._write_rows(self.rows)

    def _build_picture_base_dirs(self):
        dirs = []
        csv_dir = os.path.dirname(self.csv_path)
        code_dir = os.path.dirname(__file__)
        project_dir = os.path.dirname(code_dir)
        for d in (
            os.path.join(project_dir, "Pict"),
            os.path.join(csv_dir, "Pict"),
            os.path.join(code_dir, "Pict"),
        ):
            if d not in dirs:
                dirs.append(d)
        return dirs

    def _discover_picture_stems(self):
        stems = set()
        for base in self.picture_base_dirs:
            if not os.path.isdir(base):
                continue
            for name in os.listdir(base):
                stem, ext = os.path.splitext(name)
                if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                    continue
                stems.add(self._normalize_word(stem))
        return stems

    def _mapping_file_candidates(self):
        candidates = []
        for base in self.picture_base_dirs:
            candidates.append(os.path.join(base, "mapping.json"))
        csv_dir = os.path.dirname(self.csv_path)
        candidates.append(os.path.join(csv_dir, "mapping.json"))
        # keep order, remove duplicates
        dedup = []
        seen = set()
        for c in candidates:
            if c in seen:
                continue
            seen.add(c)
            dedup.append(c)
        return dedup

    def _load_external_mapping(self):
        for path in self._mapping_file_candidates():
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        key = self._normalize_word(str(k))
                        val = self._normalize_word(str(v))
                        if key and val:
                            self.synonym_image_map[key] = val
            except Exception:
                continue
            # first existing mapping file wins
            return

    def _normalize_word(self, text):
        val = (text or "").strip().casefold()
        if not val:
            return ""
        val = "".join(
            ch for ch in unicodedata.normalize("NFD", val) if unicodedata.category(ch) != "Mn"
        )
        return re.sub(r"[^a-z0-9]+", "", val)

    def _tokenize_words(self, text):
        raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", (text or "").casefold())
        return [self._normalize_word(tok) for tok in raw if self._normalize_word(tok)]

    def _is_probable_verb(self, fr_word):
        word = self._normalize_word(fr_word)
        if not word or " " in word:
            return False
        return word.endswith(("er", "ir", "re", "oir", "at", "it", "et", "yt"))

    def _pick_gender_for_ambiguous(self, fr_word, cz_word):
        key = f"{self._normalize_word(fr_word)}|{self._normalize_word(cz_word)}"
        if not key.strip("|"):
            return "man"
        score = sum(ord(ch) for ch in key)
        return "woman" if (score % 2) else "man"

    def _is_probable_adj_or_adv(self, fr_word, cz_word):
        cz = self._normalize_word(cz_word)
        fr = self._normalize_word(fr_word)
        if cz.endswith(
            (
                "e",
                "ne",
                "ove",
                "ova",
                "ovy",
                "ych",
                "ich",
                "y",
                "a",
                "i",
            )
        ):
            return True
        if fr.endswith(
            (
                "ment",  # adverbs
                "if",
                "ive",
                "eux",
                "euse",
                "al",
                "ale",
                "el",
                "elle",
                "ant",
                "ente",
            )
        ):
            return True
        return False

    def _choose_picture_stem(self, row):
        fr = (row.get("FR") or "").strip()
        cz = (row.get("CZ") or "").strip()
        fr_norm = self._normalize_word(fr)
        cz_norm = self._normalize_word(cz)
        tokens = self._tokenize_words(fr) + self._tokenize_words(cz)

        # 1) Exact filename match by whole words and tokens.
        for key in [fr_norm, cz_norm] + tokens:
            if key and key in self.picture_stems:
                return key

        # 2) Synonyms / aliases.
        for key in [fr_norm, cz_norm] + tokens:
            mapped = self.synonym_image_map.get(key)
            if mapped:
                return mapped

        # 3) Pronouns on/ona -> man/woman.
        token_set = set(tokens)
        if token_set & FEMALE_PRONOUNS:
            return "woman"
        if token_set & MALE_PRONOUNS:
            return "man"
        if token_set & AMBIGUOUS_PRONOUNS:
            return self._pick_gender_for_ambiguous(fr, cz)

        # 4) Category fallbacks requested by user.
        if token_set & CONJUNCTION_WORDS:
            return "conjuction"
        if token_set & PREPOSITION_WORDS:
            return "preposition"
        if token_set & ADJ_ADV_WORDS:
            return "proverbs"
        if self._is_probable_verb(fr):
            return "verb"
        if self._is_probable_adj_or_adv(fr, cz):
            return "proverbs"
        return "others"

    def _find_picture_path(self, stem):
        stem = self._normalize_word(stem)
        if not stem:
            return ""
        candidates = [f"{stem}.png", f"{stem}.jpg", f"{stem}.jpeg", f"{stem}.webp", f"{stem}.gif"]
        for base in self.picture_base_dirs:
            for name in candidates:
                path = os.path.join(base, name)
                if os.path.exists(path):
                    return path
        return ""

    def _update_picture_display(self, row):
        if not hasattr(self, "picture_label"):
            return
        stem = self._choose_picture_stem(row) if row else "others"
        path = self._find_picture_path(stem) or self._find_picture_path("others")
        if not path:
            self.picture_label.configure(image="", text="")
            self.picture_photo = None
            return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((240, 240), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (240, 240), (255, 255, 255, 255))
            x = (240 - img.width) // 2
            y = (240 - img.height) // 2
            canvas.paste(img, (x, y), img)
            self.picture_photo = ImageTk.PhotoImage(canvas)
            self.picture_label.configure(image=self.picture_photo, text="")
        except Exception:
            self.picture_label.configure(image="", text="")
            self.picture_photo = None

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
        if self.ht_only_var.get():
            indices = [i for i in indices if self.rows[i].get("HT", "").lower() == "ano"]

        return indices

    def _current_selection_signature(self, indices):
        # Signature is based on effective selection, not raw entry strings,
        # to avoid unnecessary reset of the "shown" cycle.
        return (
            tuple(indices),
            self.filter_var.get(),
            self.lang_var.get(),
            self.not_known_var.get(),
            self.ht_only_var.get(),
        )

    def _cz_meanings_for_fr(self, fr_word):
        key = (fr_word or "").strip().casefold()
        if not key:
            return []
        meanings = []
        seen = set()
        for row in self.rows:
            row_fr = (row.get("FR") or "").strip().casefold()
            row_cz = (row.get("CZ") or "").strip()
            if row_fr != key or not row_cz:
                continue
            marker = row_cz.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            meanings.append(row_cz)
        return meanings

    def _starts_with_elision_sound_fr(self, word):
        word = (word or "").strip().lower()
        if not word:
            return False
        first = word[:1]
        if first in "aàâæeéèêëiîïoôœuùûüh":
            return True
        return False

    def _format_fr_with_article(self, word, gender):
        word = (word or "").strip()
        gender = (gender or "").strip().lower()
        if not word or gender not in ("m", "f"):
            return ""
        if self._starts_with_elision_sound_fr(word):
            return f"l'{word}"
        if gender == "m":
            return f"le {word}"
        return f"la {word}"

    def _update_article_display(self, row, force_visible=False):
        if not row:
            self.gender_var.set("")
            self.article_var.set("")
            return
        if not force_visible and self.lang_var.get() == "CZ":
            self.gender_var.set("")
            self.article_var.set("")
            return
        self.gender_var.set((row.get("gender_fr") or "").strip().lower())
        self.article_var.set(
            self._format_fr_with_article(row.get("FR", ""), row.get("gender_fr", ""))
        )

    def load_new_word(self):
        self.stop_turbo()
        if self.current_index is not None:
            self._persist_current_status_flags()
        self.turbo_mode = False

        indices = self._filtered_indices()
        if not indices:
            self._selection_signature = None
            self._shown_in_selection.clear()
            self.remaining_var.set("0")
            self._update_picture_display(None)
            messagebox.showinfo("Info", "Žádná slovíčka pro aktuální filtr.")
            return

        signature = self._current_selection_signature(indices)
        if signature != self._selection_signature:
            self._selection_signature = signature
            self._shown_in_selection.clear()

        available = [i for i in indices if i not in self._shown_in_selection]
        if not available:
            self.remaining_var.set("0")
            self._shown_in_selection.clear()
            available = list(indices)

        self.current_index = random.choice(available)
        self._shown_in_selection.add(self.current_index)
        self._update_remaining_counter(indices)
        row = self.rows[self.current_index]

        fr = row.get("FR", "")
        cz = row.get("CZ", "")
        sentence = row.get("Sentence", "")
        learned = row.get("L", "").strip().lower() == "ano"
        hard_training = row.get("HT", "").strip().lower() == "ano"

        self.learned_var.set(learned)
        self.hard_training_var.set(hard_training)
        self.input_var.set("")
        self.sentence_var.set("")
        self.sentence_t_var.set("")
        self.fr_hint_var.set("")
        self.thumb_var.set("")
        self.gender_var.set("")
        self.article_var.set("")
        self.input_entry.configure(fg="black")
        self._stop_hint_blink()

        if self.lang_var.get() == "FR":
            self.fr_var.set(fr)
            self.cz_var.set("???")
            self.hidden_side = "CZ"
            self._update_article_display(row, force_visible=True)
        else:
            self.cz_var.set(cz)
            self.fr_var.set("???")
            self.hidden_side = "FR"
            self._update_article_display(row, force_visible=False)
        self._update_picture_display(row)

    def _update_remaining_counter(self, indices):
        total = len(indices)
        seen = len([i for i in self._shown_in_selection if i in indices])
        if total <= 0:
            self.remaining_var.set("0")
            if hasattr(self, "remaining_panel"):
                self.remaining_panel.lift()
            return
        # Count shown words as "in progress"; first shown word keeps full count.
        remaining = 0 if seen >= total else (total - seen + 1)
        self.remaining_var.set(str(max(0, remaining)))
        if hasattr(self, "remaining_panel"):
            self.remaining_panel.lift()

    def _indices_for_turbo(self):
        # Turbo respektuje stejné parametry výběru jako "New":
        # All / Last / Interval + případný filtr "Not known".
        indices = self._filtered_indices()
        if not indices:
            return []
        return [i for i in indices if (self.rows[i].get("FR") or "").strip()]

    def load_turbo_word(self):
        if self.turbo_running:
            return
        self.turbo_running = True
        self.turbo_mode = True
        self.turbo_speech_generation += 1
        self._run_turbo_cycle()

    def stop_turbo(self):
        self.turbo_running = False
        self.turbo_mode = False
        if self.turbo_after_job is not None:
            self.master.after_cancel(self.turbo_after_job)
            self.turbo_after_job = None
        self.turbo_speech_generation += 1

    def _run_turbo_cycle(self):
        if not self.turbo_running:
            return
        loaded = self._load_turbo_word_once()
        if not loaded:
            self.stop_turbo()

    def _load_turbo_word_once(self):
        if self.current_index is not None:
            self._persist_current_status_flags()

        indices = self._indices_for_turbo()
        if not indices:
            self.turbo_selection_signature = None
            self.turbo_shown_in_selection.clear()
            self.remaining_var.set("0")
            self._update_picture_display(None)
            messagebox.showinfo("Info", "Žádná FR slovíčka pro aktuální výběr.")
            return False

        signature = (
            tuple(indices),
            self.interval_start_var.get(),
            self.interval_end_var.get(),
        )
        if signature != self.turbo_selection_signature:
            self.turbo_selection_signature = signature
            self.turbo_shown_in_selection.clear()

        available = [i for i in indices if i not in self.turbo_shown_in_selection]
        if not available:
            self.remaining_var.set("0")
            self.turbo_shown_in_selection.clear()
            available = list(indices)

        self.current_index = random.choice(available)
        self.turbo_shown_in_selection.add(self.current_index)
        self._update_remaining_counter_turbo(indices)
        row = self.rows[self.current_index]

        fr = (row.get("FR") or "").strip()
        cz = (row.get("CZ") or "").strip()
        learned = row.get("L", "").strip().lower() == "ano"
        hard_training = row.get("HT", "").strip().lower() == "ano"

        self.learned_var.set(learned)
        self.hard_training_var.set(hard_training)
        self.input_var.set("")
        self.sentence_var.set("")
        self.sentence_t_var.set("")
        self.thumb_var.set("")
        self.gender_var.set("")
        self.article_var.set("")
        self.input_entry.configure(fg="black")

        # V turbo režimu vždy rovnou zobrazíme FR + CZ a pustíme audio/blikání.
        self.fr_var.set(fr)
        self.cz_var.set(cz)
        self._update_article_display(row, force_visible=True)
        self.fr_hint_var.set(fr)
        self.hidden_side = None
        self._update_picture_display(row)
        self._start_hint_blink(colors=("red", "blue", "white"), font_size=80, max_toggles=18)
        self._speak_turbo_current(row)
        return True

    def _update_remaining_counter_turbo(self, indices):
        total = len(indices)
        seen = len([i for i in self.turbo_shown_in_selection if i in indices])
        if total <= 0:
            self.remaining_var.set("0")
            if hasattr(self, "remaining_panel"):
                self.remaining_panel.lift()
            return
        remaining = 0 if seen >= total else (total - seen + 1)
        self.remaining_var.set(str(max(0, remaining)))
        if hasattr(self, "remaining_panel"):
            self.remaining_panel.lift()

    def show_translation(self):
        if self.current_index is None:
            return

        row = self.rows[self.current_index]
        fr = row.get("FR", "").strip()
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
            allowed_cz = self._cz_meanings_for_fr(row.get("FR", ""))
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

        self.fr_var.set(row.get("FR", ""))
        self._update_article_display(row, force_visible=True)
        if self.turbo_mode:
            self.cz_var.set(row.get("CZ", ""))
            self.sentence_var.set("")
            self.sentence_t_var.set("")
        else:
            all_meanings = self._cz_meanings_for_fr(row.get("FR", ""))
            self.cz_var.set("\n".join(all_meanings) if all_meanings else row.get("CZ", ""))
            self.sentence_var.set(row.get("Sentence", ""))
            self.sentence_t_var.set(row.get("SentenceT", ""))
        self.hidden_side = None
        if self.turbo_mode:
            self._start_hint_blink(colors=("red", "blue", "white"), font_size=80, max_toggles=18)
            self._speak_turbo_current(row)
        else:
            self._speak_current(row)

    def on_learned_toggled(self):
        if self.learned_var.get() and self.hard_training_var.get():
            self.hard_training_var.set(False)
        self._persist_current_status_flags()

    def on_hard_training_toggled(self):
        if self.hard_training_var.get() and self.learned_var.get():
            self.learned_var.set(False)
        self._persist_current_status_flags()

    def _start_hint_blink(self, colors=("blue", "white"), font_size=55, max_toggles=6):
        self._stop_hint_blink()
        self.hint_blink_colors = colors
        self.hint_blink_color_index = 0
        self.hint_blink_max_toggles = max_toggles
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.fr_hint_label.configure(fg=colors[0], font=("Helvetica", font_size, "bold"))
        self.hint_blink_job = self.master.after(350, self._toggle_hint_blink)

    def _stop_hint_blink(self):
        if self.hint_blink_job is not None:
            self.master.after_cancel(self.hint_blink_job)
            self.hint_blink_job = None
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.hint_blink_colors = ("blue", "white")
        self.hint_blink_color_index = 0
        self.hint_blink_max_toggles = 6
        if hasattr(self, "fr_hint_label"):
            self.fr_hint_label.configure(fg="blue", font=("Helvetica", 55, "bold"))

    def _toggle_hint_blink(self):
        if not self.fr_hint_var.get().strip():
            self._stop_hint_blink()
            return
        if self.hint_blink_toggles >= self.hint_blink_max_toggles:
            self._stop_hint_blink()
            return
        self.hint_blink_toggles += 1
        self.hint_blink_color_index = (self.hint_blink_color_index + 1) % len(
            self.hint_blink_colors
        )
        fg_color = self.hint_blink_colors[self.hint_blink_color_index]
        self.fr_hint_label.configure(fg=fg_color)
        self.hint_blink_job = self.master.after(350, self._toggle_hint_blink)

    def _persist_current_status_flags(self):
        if self.current_index is None:
            return
        new_l = "ano" if self.learned_var.get() else "ne"
        new_ht = "ano" if self.hard_training_var.get() else "ne"
        row = self.rows[self.current_index]
        if row.get("L") == new_l and row.get("HT", "ne") == new_ht:
            return
        row["L"] = new_l
        row["HT"] = new_ht
        self._save_csv()

    def _speak_current(self, row):
        if self.no_voice_var.get():
            return
        fr = row.get("FR", "").strip()
        sentence = row.get("Sentence", "").strip()
        text = ". ".join([t for t in (fr, sentence) if t])
        if not text:
            return
        try:
            subprocess.Popen(["say", "-v", self.fr_voice, text])
        except Exception:
            pass

    def _resolve_cz_voice(self):
        try:
            output = subprocess.check_output(
                ["say", "-v", "?"], text=True, stderr=subprocess.DEVNULL
            )
        except Exception:
            return self.fr_voice

        voices = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            voices.append((parts[0], parts[1]))

        for wanted_lang in ("cs_CZ", "cs", "sk_SK"):
            for voice, lang in voices:
                if lang.startswith(wanted_lang):
                    return voice
        return self.fr_voice

    def _say_blocking(self, voice, text, rate_wpm=None):
        text = (text or "").strip()
        if not text:
            return
        try:
            cmd = ["say", "-v", voice]
            if rate_wpm is not None:
                cmd.extend(["-r", str(rate_wpm)])
            cmd.append(text)
            subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _schedule_next_turbo_cycle(self, generation):
        self.turbo_after_job = None
        if not self.turbo_running or generation != self.turbo_speech_generation:
            return
        self.turbo_after_job = self.master.after(250, self._run_turbo_cycle)

    def _speak_turbo_current(self, row):
        generation = self.turbo_speech_generation
        if self.no_voice_var.get():
            if self.turbo_running:
                self._schedule_next_turbo_cycle(generation)
            return

        fr = (row.get("FR") or "").strip()
        cz = (row.get("CZ") or "").strip()
        sequence = [
            (self.fr_voice, fr),
            (self.cz_voice, cz),
            (self.fr_voice, fr),
            (self.cz_voice, cz),
        ]
        sequence = [(voice, text) for voice, text in sequence if text]
        if not sequence:
            if self.turbo_running:
                self._schedule_next_turbo_cycle(generation)
            return

        def worker():
            for voice, text in sequence:
                if generation != self.turbo_speech_generation:
                    return
                self._say_blocking(voice, text)

            if generation == self.turbo_speech_generation and self.turbo_running:
                try:
                    self.master.after(
                        200, lambda: self._schedule_next_turbo_cycle(generation)
                    )
                except Exception:
                    return

        threading.Thread(target=worker, daemon=True).start()

    def open_input_window(self):
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.lift()
            return

        win = tk.Toplevel(self.master)
        win.title("Input - VocabularyFR.csv")
        win.geometry("1320x800")
        win.minsize(1100, 700)
        win.configure(bg="white")
        self.input_window = win
        self.input_sort_mode = "order"
        self.new_fr_entry = None
        self.new_cz_entry = None

        def _on_input_window_close():
            self.new_fr_entry = None
            self.new_cz_entry = None
            self.input_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_input_window_close)

        list_frame = tk.Frame(win, bg="white")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(12, 8))

        toolbar = tk.Frame(list_frame, bg="white")
        toolbar.pack(fill="x", pady=(0, 6))
        self.input_sort_button = tk.Button(
            toolbar,
            text="Seřadit FR A-Z",
            command=self.toggle_input_sort_mode,
            width=16,
        )
        self.input_sort_button.pack(side="left")

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        columns = ("Order", "GenderFR", "FR", "CZ", "Sentence", "SentenceT", "L", "HT")
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
        tree.heading("GenderFR", text="Rod FR")
        tree.heading("FR", text="FR")
        tree.heading("CZ", text="CZ")
        tree.heading("Sentence", text="Sentence")
        tree.heading("SentenceT", text="SentenceT")
        tree.heading("L", text="L")
        tree.heading("HT", text="HT")

        tree.column("Order", width=80, anchor="center")
        tree.column("GenderFR", width=80, anchor="center")
        tree.column("FR", width=200, anchor="w")
        tree.column("CZ", width=220, anchor="w")
        tree.column("Sentence", width=340, anchor="w")
        tree.column("SentenceT", width=340, anchor="w")
        tree.column("L", width=60, anchor="center")
        tree.column("HT", width=60, anchor="center")

        style = ttk.Style(win)
        style.configure("Treeview", font=("Helvetica", 14), rowheight=24)
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))

        tree.bind("<Double-1>", self.on_tree_double_click)
        tree.bind("<Button-1>", self._on_input_tree_click, add="+")

        self._populate_input_list()

        form = tk.Frame(win, bg="white")
        form.pack(fill="x", padx=12, pady=(0, 12))

        tk.Label(form, text="FR:", bg="white").grid(row=0, column=0, sticky="w")
        fr_wrap = tk.Frame(form, bg="white")
        fr_wrap.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.new_fr_entry = tk.Entry(fr_wrap, textvariable=self.new_fr_var, width=30)
        self._bind_entry_paste(self.new_fr_entry)
        self.new_fr_entry.pack(side="left")
        tk.Button(
            fr_wrap, text="🔍", width=2, command=lambda: self.search_input_fr()
        ).pack(side="left", padx=(0, 0))

        tk.Label(form, text="CZ:", bg="white").grid(row=0, column=2, sticky="w")
        cz_wrap = tk.Frame(form, bg="white")
        cz_wrap.grid(row=0, column=3, sticky="w", padx=(6, 12))
        self.new_cz_entry = tk.Entry(cz_wrap, textvariable=self.new_cz_var, width=30)
        self._bind_entry_paste(self.new_cz_entry)
        self.new_cz_entry.pack(side="left")
        tk.Button(
            cz_wrap, text="🔍", width=2, command=lambda: self.search_input_cz()
        ).pack(side="left", padx=(0, 0))
        gender_wrap = tk.Frame(form, bg="white")
        gender_wrap.grid(row=0, column=4, columnspan=2, sticky="w", padx=(2, 8))
        tk.Label(gender_wrap, text="Rod FR:", bg="white").pack(side="left")
        gender_menu = tk.OptionMenu(gender_wrap, self.new_gender_fr_var, "", "m", "f")
        gender_menu.config(width=3)
        gender_menu.pack(side="left", padx=(2, 0))

        tk.Label(form, text="Sentence:", bg="white").grid(row=1, column=0, sticky="w")
        sentence_entry = tk.Entry(form, textvariable=self.new_sentence_var, width=34)
        self._bind_entry_paste(sentence_entry)
        sentence_entry.grid(
            row=1, column=1, sticky="w", padx=(6, 12), pady=(6, 0)
        )
        tk.Label(form, text="SentenceT:", bg="white").grid(row=1, column=2, sticky="w", pady=(6, 0))
        sentence_t_entry = tk.Entry(form, textvariable=self.new_sentence_t_var, width=34)
        self._bind_entry_paste(sentence_t_entry)
        sentence_t_entry.grid(
            row=1, column=3, sticky="w", padx=(6, 12), pady=(6, 0)
        )
        buttons_left = tk.Frame(form, bg="white")
        buttons_left.grid(row=1, column=4, columnspan=3, sticky="w", padx=(6, 0), pady=(6, 0))
        tk.Button(buttons_left, text="Add Row", command=self.add_new_row).pack(side="left")
        tk.Button(buttons_left, text="Insert Row", command=self.insert_row).pack(
            side="left", padx=(8, 0)
        )
        tk.Button(buttons_left, text="Delete", command=self.delete_selected_row).pack(
            side="left", padx=(8, 0)
        )
        tk.Button(buttons_left, text="Training", command=_on_input_window_close).pack(
            side="left", padx=(8, 0)
        )

    def _load_verbe_rows(self):
        if not os.path.exists(self.verbe_csv_path):
            raise FileNotFoundError(self.verbe_csv_path)
        with open(self.verbe_csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader]
        return self._repair_verbe_rows(rows)

    def _repair_verbe_rows(self, rows):
        fields = [
            "M",
            "Order",
            "InfFR",
            "InfCZ",
            "Ind1",
            "Ind2",
            "Ind3",
            "IndP1",
            "IndP2",
            "IndP3",
            "FS1",
            "FS2",
            "FS3",
            "FSP1",
            "FSP2",
            "FSP3",
            "Imp1",
            "Imp2",
            "Imp3",
            "ImpP1",
            "ImpP2",
            "ImpP3",
        ]
        repaired = []
        for raw in rows:
            row = {k: (raw.get(k) or "").strip() for k in fields}
            if not row["InfFR"] and not row["InfCZ"]:
                continue
            if row["M"] not in ("ano", "ne"):
                row["M"] = "ne"
            repaired.append(row)
        return repaired

    def _save_verbe_rows(self):
        if not self.verbe_rows:
            return
        fieldnames = [
            "M",
            "Order",
            "InfFR",
            "InfCZ",
            "Ind1",
            "Ind2",
            "Ind3",
            "IndP1",
            "IndP2",
            "IndP3",
            "FS1",
            "FS2",
            "FS3",
            "FSP1",
            "FSP2",
            "FSP3",
            "Imp1",
            "Imp2",
            "Imp3",
            "ImpP1",
            "ImpP2",
            "ImpP3",
        ]
        with open(self.verbe_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.verbe_rows)

    def open_verbes_window(self):
        if self.verbes_window and self.verbes_window.winfo_exists():
            self.verbes_window.lift()
            return

        try:
            self.verbe_rows = self._load_verbe_rows()
        except FileNotFoundError:
            messagebox.showerror("Chyba", f"Soubor nebyl nalezen: {self.verbe_csv_path}")
            return

        win = tk.Toplevel(self.master)
        win.title("Verbes - VerbeFR.csv")
        win.geometry("1320x800")
        win.minsize(1100, 700)
        win.configure(bg="white")
        self.verbes_window = win

        def _on_verbes_close():
            self.verbes_window = None
            self.verbes_tree = None
            self.verbe_detail_vars = {}
            self.verbe_text_widgets = {}
            self.verbe_groups = []
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_verbes_close)

        main = tk.Frame(win, bg="white")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left_panel = tk.Frame(main, bg="white")
        left_panel.pack(side="left", fill="both", expand=False)
        right_panel = tk.Frame(main, bg="white")
        right_panel.pack(side="right", fill="both", expand=True, padx=(16, 0))

        scrollbar = tk.Scrollbar(left_panel)
        scrollbar.pack(side="right", fill="y")

        columns = ("M", "Order", "InfFR", "InfCZ")
        tree = ttk.Treeview(
            left_panel,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            height=28,
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)
        self.verbes_tree = tree

        tree.heading("M", text="M")
        tree.heading("Order", text="Order")
        tree.heading("InfFR", text="InfFR")
        tree.heading("InfCZ", text="InfCZ")
        tree.column("M", width=32, anchor="center")
        tree.column("Order", width=50, anchor="center")
        tree.column("InfFR", width=122, anchor="w")
        tree.column("InfCZ", width=158, anchor="w")

        style = ttk.Style(win)
        style.configure("Treeview", font=("Helvetica", 14), rowheight=24)
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))

        tree.bind("<Button-1>", self._on_verbes_tree_click, add="+")
        tree.bind("<<TreeviewSelect>>", self._on_verbes_tree_select)

        self._populate_verbes_tree()

        self.verbe_detail_vars = {
            "Ind1": tk.StringVar(value=""),
            "Ind2": tk.StringVar(value=""),
            "Ind3": tk.StringVar(value=""),
            "IndP1": tk.StringVar(value=""),
            "IndP2": tk.StringVar(value=""),
            "IndP3": tk.StringVar(value=""),
            "FS1": tk.StringVar(value=""),
            "FS2": tk.StringVar(value=""),
            "FS3": tk.StringVar(value=""),
            "FSP1": tk.StringVar(value=""),
            "FSP2": tk.StringVar(value=""),
            "FSP3": tk.StringVar(value=""),
            "Imp1": tk.StringVar(value=""),
            "Imp2": tk.StringVar(value=""),
            "Imp3": tk.StringVar(value=""),
            "ImpP1": tk.StringVar(value=""),
            "ImpP2": tk.StringVar(value=""),
            "ImpP3": tk.StringVar(value=""),
        }
        self.verbe_text_widgets = {}

        forms = tk.Frame(right_panel, bg="white")
        forms.pack(anchor="nw", fill="both", expand=True)

        groups = [
            ("Ind", ["Ind1", "Ind2", "Ind3", "IndP1", "IndP2", "IndP3"], "#fff6a8"),
            ("FS", ["FS1", "FS2", "FS3", "FSP1", "FSP2", "FSP3"], "#dff6dd"),
            ("Imp", ["Imp1", "Imp2", "Imp3", "ImpP1", "ImpP2", "ImpP3"], "#dce9ff"),
        ]
        self.verbe_groups = groups
        for col, (title, keys, group_bg) in enumerate(groups):
            group = tk.LabelFrame(forms, text=title, bg=group_bg, padx=8, pady=8)
            group.grid(row=0, column=col, sticky="n", padx=(0, 12))
            for r, key in enumerate(keys):
                txt = tk.Text(
                    group,
                    width=17,
                    height=1,
                    bg=group_bg,
                    bd=0,
                    highlightthickness=0,
                    wrap="none",
                    font=("Helvetica", 28),
                )
                txt.tag_configure("stem", foreground="black")
                txt.tag_configure("ending", foreground="red")
                txt.grid(row=r, column=0, sticky="w", pady=(0, 6))
                txt.configure(state="disabled")
                self.verbe_text_widgets[key] = txt
            tk.Button(
                forms,
                text="🔊",
                width=4,
                command=lambda k=keys: self._speak_verbe_group(k),
            ).grid(row=1, column=col, sticky="n", padx=(0, 12), pady=(6, 0))

        bottom = tk.Frame(win, bg="white")
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(bottom, text="Training", command=_on_verbes_close).pack(side="right")

        self._refresh_verbe_details()

    def _populate_verbes_tree(self):
        if not self.verbes_tree:
            return
        for item in self.verbes_tree.get_children():
            self.verbes_tree.delete(item)
        for idx, row in enumerate(self.verbe_rows):
            mark = "☑" if row.get("M", "ne") == "ano" else "☐"
            self.verbes_tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(mark, row.get("Order", ""), row.get("InfFR", ""), row.get("InfCZ", "")),
            )

    def _checked_verbe_index(self):
        for idx, row in enumerate(self.verbe_rows):
            if row.get("M", "ne") == "ano":
                return idx
        return None

    def _set_checked_verbe(self, index):
        changed = False
        for i, row in enumerate(self.verbe_rows):
            new_value = "ano" if i == index else "ne"
            if row.get("M", "ne") != new_value:
                row["M"] = new_value
                changed = True
        if changed:
            self._save_verbe_rows()
        self._populate_verbes_tree()
        if self.verbes_tree is not None and index is not None:
            iid = str(index)
            self.verbes_tree.selection_set(iid)
            self.verbes_tree.focus(iid)
            self.verbes_tree.see(iid)
        self._refresh_verbe_details()

    def _on_verbes_tree_click(self, event):
        if not self.verbes_tree:
            return
        region = self.verbes_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.verbes_tree.identify_row(event.y)
        col_id = self.verbes_tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        if col_id != "#1":
            return
        try:
            idx = int(row_id)
        except ValueError:
            return "break"

        if self.verbe_rows[idx].get("M", "ne") == "ano":
            self.verbe_rows[idx]["M"] = "ne"
            self._save_verbe_rows()
            self._populate_verbes_tree()
            self._refresh_verbe_details()
        else:
            self._set_checked_verbe(idx)
        return "break"

    def _on_verbes_tree_select(self, event=None):
        if not self.verbes_tree:
            return
        selected = self.verbes_tree.selection()
        if not selected:
            self._refresh_verbe_details()
            return
        try:
            idx = int(selected[0])
        except ValueError:
            self._refresh_verbe_details()
            return
        if 0 <= idx < len(self.verbe_rows) and self.verbe_rows[idx].get("M", "ne") == "ano":
            self._refresh_verbe_details()

    def _refresh_verbe_details(self):
        if not self.verbe_detail_vars:
            return
        checked_idx = self._checked_verbe_index()
        if checked_idx is None:
            for var in self.verbe_detail_vars.values():
                var.set("")
            for key in self.verbe_text_widgets:
                self._set_verbe_widget_text(key, "")
            return
        row = self.verbe_rows[checked_idx]
        stems_by_group = {}
        for title, keys, _ in self.verbe_groups:
            stems_by_group[title] = self._compute_group_stem(row, keys)
        for key, var in self.verbe_detail_vars.items():
            value = row.get(key, "")
            var.set(value)
            group_name = "Ind" if key.startswith("Ind") else ("FS" if key.startswith("FS") else "Imp")
            self._set_verbe_widget_text(key, value, stems_by_group.get(group_name, ""))

    def _compute_group_stem(self, row, keys):
        tokens = []
        for key in keys:
            token = self._extract_verb_token((row.get(key) or "").strip())
            if token:
                tokens.append(token)
        if len(tokens) < 2:
            return ""
        lcp = tokens[0].lower()
        for tok in tokens[1:]:
            tok_l = tok.lower()
            i = 0
            limit = min(len(lcp), len(tok_l))
            while i < limit and lcp[i] == tok_l[i]:
                i += 1
            lcp = lcp[:i]
            if len(lcp) < 2:
                return ""
        return lcp if len(lcp) >= 2 else ""

    def _extract_verb_token(self, text):
        text = (text or "").strip()
        if not text:
            return ""
        return text.split()[-1]

    def _set_verbe_widget_text(self, key, text, stem_lower=""):
        widget = self.verbe_text_widgets.get(key)
        if widget is None:
            return
        text = (text or "").strip()
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        if not text:
            widget.configure(state="disabled")
            return

        token = self._extract_verb_token(text)
        if token and stem_lower and len(token) > len(stem_lower) and token.lower().startswith(stem_lower):
            head_len = len(text) - len(token)
            leading = text[:head_len]
            stem = token[: len(stem_lower)]
            ending = token[len(stem_lower) :]
            widget.insert("end", leading + stem, "stem")
            widget.insert("end", ending, "ending")
        else:
            widget.insert("end", text, "stem")
        widget.configure(state="disabled")

    def _speak_verbe_group(self, keys):
        if self.no_voice_var.get():
            return
        checked_idx = self._checked_verbe_index()
        if checked_idx is None:
            return
        row = self.verbe_rows[checked_idx]
        parts = [(row.get(k) or "").strip() for k in keys]
        parts = [p for p in parts if p]
        if not parts:
            return

        def worker():
            # Read each form separately with a short pause for clearer listening.
            for i, part in enumerate(parts):
                self._say_blocking(self.fr_voice, part, rate_wpm=155)
                if i < len(parts) - 1:
                    time.sleep(0.5)

        threading.Thread(target=worker, daemon=True).start()

    def _mark_search_entry(self, entry_widget, found):
        if entry_widget is None:
            return
        entry_widget.configure(fg="black" if found else "red")

    def _search_input_value(self, column_name, search_value, entry_widget):
        if not self.input_tree:
            return
        term = (search_value or "").strip().casefold()
        if not term:
            self._mark_search_entry(entry_widget, True)
            return

        found_iid = None
        for idx, row in enumerate(self.rows):
            value = (row.get(column_name) or "").strip().casefold()
            if value == term:
                found_iid = str(idx)
                break

        if found_iid is None:
            self._mark_search_entry(entry_widget, False)
            return

        self._mark_search_entry(entry_widget, True)
        self.input_tree.selection_set(found_iid)
        self.input_tree.focus(found_iid)
        self.input_tree.see(found_iid)

    def search_input_fr(self):
        self._search_input_value("FR", self.new_fr_var.get(), self.new_fr_entry)

    def search_input_cz(self):
        self._search_input_value("CZ", self.new_cz_var.get(), self.new_cz_entry)

    def _populate_input_list(self):
        if not self.input_tree:
            return
        for item in self.input_tree.get_children():
            self.input_tree.delete(item)
        display_rows = list(enumerate(self.rows))
        if self.input_sort_mode == "fr":
            display_rows.sort(
                key=lambda item: (
                    unicodedata.normalize("NFKD", (item[1].get("FR") or "").casefold()),
                    int(item[1].get("Order", "0") or 0),
                )
            )
        for idx, row in display_rows:
            self.input_tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    row.get("Order", ""),
                    row.get("gender_fr", ""),
                    row.get("FR", ""),
                    row.get("CZ", ""),
                    row.get("Sentence", ""),
                    row.get("SentenceT", ""),
                    self._checkbox_mark(row.get("L", "ne")),
                    self._checkbox_mark(row.get("HT", "ne")),
                ),
            )

    def toggle_input_sort_mode(self):
        self.input_sort_mode = "fr" if self.input_sort_mode == "order" else "order"
        if hasattr(self, "input_sort_button") and self.input_sort_button is not None:
            self.input_sort_button.configure(
                text="Zpět na pořadí" if self.input_sort_mode == "fr" else "Seřadit FR A-Z"
            )
        self._populate_input_list()

    def _checkbox_mark(self, value):
        return "☑" if (value or "").strip().lower() == "ano" else "☐"

    def _toggle_input_checkbox(self, idx, column_name):
        if idx < 0 or idx >= len(self.rows):
            return
        row = self.rows[idx]
        current = (row.get(column_name, "ne") or "ne").strip().lower()
        new_value = "ne" if current == "ano" else "ano"
        row[column_name] = new_value

        # Mutual exclusion: L and HT cannot be "ano" together.
        if column_name == "L" and new_value == "ano":
            row["HT"] = "ne"
        elif column_name == "HT" and new_value == "ano":
            row["L"] = "ne"

        self._save_csv()

        if self.input_tree:
            self.input_tree.item(
                str(idx),
                values=(
                    row.get("Order", ""),
                    row.get("gender_fr", ""),
                    row.get("FR", ""),
                    row.get("CZ", ""),
                    row.get("Sentence", ""),
                    row.get("SentenceT", ""),
                    self._checkbox_mark(row.get("L", "ne")),
                    self._checkbox_mark(row.get("HT", "ne")),
                ),
            )

    def _on_input_tree_click(self, event):
        if not self.input_tree:
            return
        region = self.input_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.input_tree.identify_row(event.y)
        col_id = self.input_tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        if col_id not in ("#7", "#8"):  # L, HT
            return

        try:
            idx = int(row_id)
        except ValueError:
            return "break"
        column_name = "L" if col_id == "#7" else "HT"
        self._toggle_input_checkbox(idx, column_name)
        self.input_tree.selection_set(row_id)
        self.input_tree.focus(row_id)
        return "break"

    def add_new_row(self):
        fr = self.new_fr_var.get().strip()
        cz = self.new_cz_var.get().strip()
        sentence = self.new_sentence_var.get().strip()
        sentence_t = self.new_sentence_t_var.get().strip()
        gender_fr = self.new_gender_fr_var.get().strip().lower()
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej FR i CZ.")
            return

        next_order = 1
        if self.rows:
            try:
                next_order = max(int(r.get("Order", "0") or 0) for r in self.rows) + 1
            except ValueError:
                next_order = len(self.rows) + 1

        new_row = {
            "FR": fr,
            "CZ": cz,
            "Order": str(next_order),
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
            "HT": "ne",
            "gender_fr": gender_fr if gender_fr in ("m", "f") else "",
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
                    new_row.get("gender_fr", ""),
                    new_row.get("FR", ""),
                    new_row.get("CZ", ""),
                    new_row.get("Sentence", ""),
                    new_row.get("SentenceT", ""),
                    self._checkbox_mark(new_row.get("L", "ne")),
                    self._checkbox_mark(new_row.get("HT", "ne")),
                ),
            )
            children = self.input_tree.get_children()
            if children:
                self.input_tree.see(children[-1])

        self.new_fr_var.set("")
        self.new_cz_var.set("")
        self.new_sentence_var.set("")
        self.new_sentence_t_var.set("")
        self.new_gender_fr_var.set("")
        self._mark_search_entry(self.new_fr_entry, True)
        self._mark_search_entry(self.new_cz_entry, True)

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
        gender_fr = self.new_gender_fr_var.get().strip().lower()
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej FR i CZ.")
            return

        try:
            selected_idx = int(selected[0])
        except ValueError:
            return
        if selected_idx < 0 or selected_idx >= len(self.rows):
            return

        new_row = {
            "FR": fr,
            "CZ": cz,
            "Order": "",
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
            "HT": "ne",
            "gender_fr": gender_fr if gender_fr in ("m", "f") else "",
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
        self.new_gender_fr_var.set("")
        self._mark_search_entry(self.new_fr_entry, True)
        self._mark_search_entry(self.new_cz_entry, True)

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

        # Columns: Order, GenderFR, FR, CZ, Sentence, SentenceT, L, HT
        fr = (values[2] if len(values) > 2 else "").strip()
        sentence = (values[4] if len(values) > 4 else "").strip()
        self._speak_current({"FR": fr, "Sentence": sentence})

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
        tree_columns = ("Order", "GenderFR", "FR", "CZ", "Sentence", "SentenceT", "L", "HT")
        data_keys = {
            "Order": "Order",
            "GenderFR": "gender_fr",
            "FR": "FR",
            "CZ": "CZ",
            "Sentence": "Sentence",
            "SentenceT": "SentenceT",
            "L": "L",
            "HT": "HT",
        }
        if col_index < 0 or col_index >= len(tree_columns):
            return
        tree_column = tree_columns[col_index]
        column_name = data_keys[tree_column]

        # prevent editing Order directly
        if column_name in ("Order", "L", "HT"):
            self.input_tree.selection_set(row_id)
            self.input_tree.focus(row_id)
            if column_name == "Order":
                self._read_tree_item(row_id)
            return

        x, y, width, height = self.input_tree.bbox(row_id, col_id)
        value = self.input_tree.set(row_id, tree_column)

        if self.edit_entry is not None:
            self.edit_entry.destroy()
            self.edit_entry = None

        if tree_column == "GenderFR":
            if self.gender_popup_menu is not None:
                try:
                    self.gender_popup_menu.destroy()
                except Exception:
                    pass
                self.gender_popup_menu = None

            def save_gender(new_value):
                self.input_tree.set(row_id, tree_column, new_value)
                try:
                    idx = int(row_id)
                except ValueError:
                    return
                if 0 <= idx < len(self.rows):
                    old_value = self.rows[idx].get(column_name, "")
                    if old_value != new_value:
                        self.rows[idx][column_name] = new_value
                        self._save_csv()
                if self.gender_popup_menu is not None:
                    try:
                        self.gender_popup_menu.destroy()
                    except Exception:
                        pass
                    self.gender_popup_menu = None

            menu = tk.Menu(self.input_tree, tearoff=0)
            menu.add_command(label="(prázdné)", command=lambda: save_gender(""))
            menu.add_command(label="m", command=lambda: save_gender("m"))
            menu.add_command(label="f", command=lambda: save_gender("f"))
            self.gender_popup_menu = menu
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return

        self.edit_entry = tk.Entry(self.input_tree, font=("Helvetica", 14))
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, value)
        self._bind_entry_paste(self.edit_entry)
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
                    if column_name == "gender_fr":
                        new_value = new_value.strip().lower()
                        if new_value not in ("", "m", "f"):
                            new_value = ""
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
