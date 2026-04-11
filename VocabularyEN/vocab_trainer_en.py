import csv
from datetime import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import ttk
from tkinter import messagebox

APP_NAME = "VocabularyEN"
CSV_FILENAME = "VocabularyEN.csv"

# Keep Python defaults intentionally small; most mapping is loaded from Pict/mapping.json.
SYNONYM_IMAGE_MAP = {}
FEMALE_PRONOUNS = {"she", "her", "hers", "ona", "ji", "její"}
MALE_PRONOUNS = {"he", "him", "his", "on", "ho", "jeho"}
AMBIGUOUS_PRONOUNS = {"i", "you", "we", "they", "it", "me", "us", "them", "ja", "ty", "my", "vy", "oni", "ono"}
CONJUNCTION_WORDS = {"and", "or", "but", "nor", "so", "yet", "a", "nebo", "ale"}
PREPOSITION_WORDS = {
    "in", "on", "at", "to", "for", "from", "with", "by", "about", "under", "over", "between",
    "into", "through", "during", "before", "after", "without", "against", "among",
    "na", "v", "ve", "do", "z", "u", "k", "od", "po", "pro", "s", "bez", "mezi",
}
ADJ_ADV_WORDS = {"adjective", "adverb", "pridavnejmeno", "prislovce"}


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
                f, fieldnames=["EN", "CZ", "Order", "Sentence", "SentenceT", "L", "HT"]
            )
            writer.writeheader()
        return target_csv

    return os.path.join(os.path.dirname(__file__), CSV_FILENAME)


class VocabularyTrainerApp:
    def __init__(self, master, csv_path):
        self.master = master
        self.csv_path = csv_path
        self.master.title("Vocabulary EN Trainer")
        self.master.configure(bg="white")
        self.master.geometry("1320x800")

        self.rows = self._load_csv()
        self.current_index = None
        self.hidden_side = None  # "EN" or "CZ"

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
        self.hint_blink_colors = ("green", "white")
        self.hint_blink_color_index = 0
        self.turbo_mode = False
        self.turbo_running = False
        self.turbo_selection_signature = None
        self.turbo_shown_in_selection = set()
        self.turbo_after_job = None
        self.turbo_speech_generation = 0
        self.fr_voice = "Samantha"
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
        self.edit_entry = None
        self.new_fr_entry = None
        self.new_cz_entry = None
        self.new_fr_var = tk.StringVar(value="")
        self.new_cz_var = tk.StringVar(value="")
        self.new_sentence_var = tk.StringVar(value="")
        self.new_sentence_t_var = tk.StringVar(value="")

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
            text="EN 🇬🇧",
            bg=top_bg,
            font=("Helvetica", 28, "bold"),
            width=6,
            anchor="w",
        ).pack(side="left", anchor="n", padx=(0, 12))
        tk.Label(
            fr_row, textvariable=self.fr_var, bg=top_bg, justify="left", wraplength=460, font=("Helvetica", 30)
        ).pack(side="left", anchor="w")

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
            width=32,
            font=("Helvetica", 16),
            fg="black",
        )
        self._bind_entry_paste(self.input_entry)
        self.input_entry.pack(anchor="w")
        tk.Checkbutton(
            input_frame,
            text="L pro vnuka / web",
            variable=self.learned_var,
            bg=top_bg,
            command=self.on_learned_toggled,
        ).pack(anchor="w", pady=(8, 0))
        tk.Checkbutton(
            input_frame,
            text="HT těžké",
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
            fg="green",
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
            text="EN",
            variable=self.lang_var,
            value="EN",
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
            text="Jen L (pro vnuka / web)",
            variable=self.not_known_var,
            bg=params_bg,
            command=self.load_new_word,
        ).pack(anchor="w")
        tk.Checkbutton(
            options_box,
            text="Jen HT",
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
        tk.Button(
            controls, text="WebUpdate", command=self.run_web_update, width=10
        ).pack(side="right", padx=(0, 8))
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
            fr = ((row.get("EN") or row.get("FR") or "").strip())
            cz = (row.get("CZ") or "").strip()
            sentence = (row.get("Sentence") or "").strip()
            sentence_t = (row.get("SentenceT") or "").strip()
            learned = (row.get("L") or "ne").strip().lower()
            hard_training = (row.get("HT") or "ne").strip().lower()

            if not fr and not cz and not sentence:
                continue

            if learned not in ("ano", "ne"):
                learned = "ne"
            if hard_training not in ("ano", "ne"):
                hard_training = "ne"

            repaired.append(
                {
                    "EN": fr,
                    "CZ": cz,
                    "Order": "",  # recalc below
                    "Sentence": sentence,
                    "SentenceT": sentence_t,
                    "L": learned,
                    "HT": hard_training,
                }
            )

        for i, row in enumerate(repaired, start=1):
            row["Order"] = str(i)

        return repaired

    def _write_rows(self, rows):
        fieldnames = ["EN", "CZ", "Order", "Sentence", "SentenceT", "L", "HT"]
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

    def _is_probable_verb(self, word):
        w = self._normalize_word(word)
        if not w or " " in w:
            return False
        if w.startswith("to") and len(w) > 4:
            return True
        return w.endswith(("ing", "ed", "en", "fy", "ise", "ize"))

    def _is_probable_adj_or_adv(self, it_word, cz_word):
        cz = self._normalize_word(cz_word)
        it = self._normalize_word(it_word)
        if cz.endswith(("e", "ne", "ove", "ova", "ovy", "ych", "ich", "y", "a", "i")):
            return True
        if it.endswith(("ly", "ous", "ful", "less", "able", "ible", "ive", "al", "ic", "ish")):
            return True
        return False

    def _pick_gender_for_ambiguous(self, it_word, cz_word):
        key = f"{self._normalize_word(it_word)}|{self._normalize_word(cz_word)}"
        if not key.strip("|"):
            return "man"
        score = sum(ord(ch) for ch in key)
        return "woman" if (score % 2) else "man"

    def _choose_picture_stem(self, row):
        it = (row.get("EN") or "").strip()
        cz = (row.get("CZ") or "").strip()
        it_norm = self._normalize_word(it)
        cz_norm = self._normalize_word(cz)
        tokens = self._tokenize_words(it) + self._tokenize_words(cz)

        for key in [it_norm, cz_norm] + tokens:
            if key and key in self.picture_stems:
                return key

        for key in [it_norm, cz_norm] + tokens:
            mapped = self.synonym_image_map.get(key)
            if mapped:
                return mapped

        token_set = set(tokens)
        if token_set & FEMALE_PRONOUNS:
            return "woman"
        if token_set & MALE_PRONOUNS:
            return "man"
        if token_set & AMBIGUOUS_PRONOUNS:
            return self._pick_gender_for_ambiguous(it, cz)
        if token_set & CONJUNCTION_WORDS:
            return "conjuction"
        if token_set & PREPOSITION_WORDS:
            return "preposition"
        if token_set & ADJ_ADV_WORDS:
            return "proverbs"
        if self._is_probable_verb(it):
            return "verb"
        if self._is_probable_adj_or_adv(it, cz):
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
            indices = [i for i in indices if self.rows[i].get("L", "").lower() == "ano"]
        elif self.ht_only_var.get():
            indices = [
                i
                for i in indices
                if self.rows[i].get("HT", "").lower() == "ano"
            ]

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

    def _cz_meanings_for_en(self, fr_word):
        key = (fr_word or "").strip().casefold()
        if not key:
            return []
        meanings = []
        seen = set()
        for row in self.rows:
            row_fr = ((row.get("EN") or row.get("FR") or "").strip()).casefold()
            row_cz = (row.get("CZ") or "").strip()
            if row_fr != key or not row_cz:
                continue
            marker = row_cz.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            meanings.append(row_cz)
        return meanings

    def _load_export_font(self, size):
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size=size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _wrap_text_for_image(self, draw, text, font, max_width):
        value = (text or "").strip()
        if not value:
            return [""]
        wrapped = []
        for paragraph in value.splitlines():
            paragraph = paragraph.strip()
            if not paragraph:
                wrapped.append("")
                continue
            words = paragraph.split()
            line = words[0]
            for word in words[1:]:
                probe = f"{line} {word}"
                box = draw.textbbox((0, 0), probe, font=font)
                if (box[2] - box[0]) <= max_width:
                    line = probe
                else:
                    wrapped.append(line)
                    line = word
            wrapped.append(line)
        return wrapped or [""]

    def _import_image_to_photos(self, image_path):
        if sys.platform != "darwin":
            return False, "Import do Fotek je podporovaný jen na macOS."
        escaped_path = image_path.replace("\\", "\\\\").replace('"', '\\"')
        script = (
            'set imgPath to POSIX file "' + escaped_path + '"\n'
            'tell application "Photos"\n'
            "  activate\n"
            "  import imgPath skip check duplicates yes\n"
            "end tell\n"
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                return True, ""
            err = (result.stderr or "").strip() or "Neznámá chyba při importu."
            return False, err
        except Exception as e:
            return False, str(e)

    def export_actual_words_image(self):
        indices = self._filtered_indices()
        if not indices:
            messagebox.showinfo("Image", "Žádná slovíčka pro aktuální filtr.")
            return

        data_rows = []
        for i in indices:
            row = self.rows[i]
            it = (row.get("EN") or "").strip()
            cz = (row.get("CZ") or "").strip()
            if not it and not cz:
                continue
            data_rows.append((it, cz))

        if not data_rows:
            messagebox.showinfo("Image", "Žádná slovíčka k exportu.")
            return

        title_font = self._load_export_font(46)
        body_font = self._load_export_font(34)

        margin = 50
        gutter = 40
        col_w = 300
        row_pad_y = 12
        header_h = 88
        line_h = 44
        width = margin * 2 + col_w * 2 + gutter

        probe_img = Image.new("RGB", (width, 200), "white")
        probe_draw = ImageDraw.Draw(probe_img)
        prepared = []
        content_h = 0
        for it, cz in data_rows:
            it_lines = self._wrap_text_for_image(probe_draw, it, body_font, col_w)
            cz_lines = self._wrap_text_for_image(probe_draw, cz, body_font, col_w)
            row_lines = max(len(it_lines), len(cz_lines))
            row_h = row_lines * line_h + row_pad_y * 2
            prepared.append((it_lines, cz_lines, row_h))
            content_h += row_h

        height = margin * 2 + header_h + content_h + 20
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        x_it = margin
        x_cz = margin + col_w + gutter
        y = margin

        draw.text((x_it, y), "EN", font=title_font, fill="black")
        draw.text((x_cz, y), "CZ", font=title_font, fill="black")
        y += header_h

        for it_lines, cz_lines, row_h in prepared:
            for li, line in enumerate(it_lines):
                draw.text((x_it, y + row_pad_y + li * line_h), line, font=body_font, fill="black")
            for li, line in enumerate(cz_lines):
                draw.text((x_cz, y + row_pad_y + li * line_h), line, font=body_font, fill="black")
            draw.line((margin, y + row_h, width - margin, y + row_h), fill="#e0e0e0", width=1)
            y += row_h

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop, exist_ok=True)
        output_path = os.path.join(desktop, "ActualWordsToLearn.png")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            img.save(output_path, "PNG")
        except Exception as e:
            messagebox.showerror("Image", f"Nepodařilo se uložit obrázek:\n{e}")
            return

        imported, import_msg = self._import_image_to_photos(output_path)
        if imported:
            messagebox.showinfo("Image", f"Uloženo na plochu a importováno do Fotek:\n{output_path}")
        else:
            messagebox.showinfo(
                "Image",
                f"Uloženo na plochu:\n{output_path}\n\nImport do Fotek se nepodařil:\n{import_msg}",
            )

    def run_web_update(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(repo_root, "VocabularyEN", "sync_vocabulary_en_to_docs.py")
        if not os.path.exists(script_path):
            messagebox.showerror("WebUpdate", f"Chybí skript:\n{script_path}")
            return

        self._persist_current_status_flags()

        try:
            sync_result = subprocess.run(
                [sys.executable, script_path],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            messagebox.showerror("WebUpdate", f"Nepodařilo se spustit synchronizaci:\n{e}")
            return

        sync_parts = []
        if sync_result.stdout.strip():
            sync_parts.append(sync_result.stdout.strip())
        if sync_result.stderr.strip():
            sync_parts.append(sync_result.stderr.strip())
        sync_output = "\n\n".join(sync_parts) if sync_parts else "Bez výstupu."

        if sync_result.returncode != 0:
            messagebox.showerror("WebUpdate", f"Synchronizace selhala.\n\n{sync_output}")
            return

        csv_rel = os.path.join("VocabularyEN", "VocabularyEN.csv")
        json_rel = os.path.join("docs", "data", "vocabulary-en.json")
        asset_dir_rel = os.path.join("docs", "assets", "vocabulary-en")
        deploy_targets = [csv_rel, json_rel]

        try:
            staged_status = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            asset_status = subprocess.run(
                ["git", "status", "--short", "--", asset_dir_rel],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            target_status = subprocess.run(
                ["git", "status", "--short", "--", *deploy_targets],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            messagebox.showerror("WebUpdate", f"Synchronizace proběhla, ale git kontrola selhala:\n{e}")
            return

        if staged_status.returncode != 0:
            messagebox.showerror(
                "WebUpdate",
                "Synchronizace proběhla, ale nepodařilo se zkontrolovat staged změny.\n\n"
                f"{staged_status.stderr.strip() or staged_status.stdout.strip() or 'Bez výstupu.'}",
            )
            return

        staged_files = [line.strip() for line in staged_status.stdout.splitlines() if line.strip()]
        if staged_files:
            messagebox.showwarning(
                "WebUpdate",
                "V repu už jsou staged jiné změny.\n\n"
                "Nejdřív je commitni nebo odstageuj ručně, pak zkus WebUpdate znovu.\n\n"
                + "\n".join(staged_files),
            )
            return

        if asset_status.returncode != 0:
            messagebox.showerror(
                "WebUpdate",
                "Synchronizace proběhla, ale nepodařilo se zkontrolovat assety.\n\n"
                f"{asset_status.stderr.strip() or asset_status.stdout.strip() or 'Bez výstupu.'}",
            )
            return

        if asset_status.stdout.strip():
            messagebox.showwarning(
                "WebUpdate",
                "Synchronizace proběhla, ale změnily se i obrázkové assety.\n\n"
                "Automatický deploy přes tlačítko je povolen jen pro CSV a JSON.\n"
                "Obrázky prosím commitni a pushni ručně.\n\n"
                + asset_status.stdout.strip(),
            )
            return

        if target_status.returncode != 0:
            messagebox.showerror(
                "WebUpdate",
                "Synchronizace proběhla, ale nepodařilo se zkontrolovat deploy soubory.\n\n"
                f"{target_status.stderr.strip() or target_status.stdout.strip() or 'Bez výstupu.'}",
            )
            return

        if not target_status.stdout.strip():
            messagebox.showinfo("WebUpdate", f"Webová data jsou už aktuální.\n\n{sync_output}")
            return

        commit_message = f"VocabularyEN web update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            add_result = subprocess.run(
                ["git", "add", "--", *deploy_targets],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if add_result.returncode != 0:
                raise RuntimeError(add_result.stderr.strip() or add_result.stdout.strip() or "git add selhal.")

            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if commit_result.returncode != 0:
                raise RuntimeError(commit_result.stderr.strip() or commit_result.stdout.strip() or "git commit selhal.")

            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo_root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if push_result.returncode != 0:
                raise RuntimeError(push_result.stderr.strip() or push_result.stdout.strip() or "git push selhal.")
        except Exception as e:
            messagebox.showerror(
                "WebUpdate",
                "Synchronizace proběhla, ale automatický deploy selhal.\n\n"
                f"{e}\n\nSync výstup:\n{sync_output}",
            )
            return

        deploy_parts = [sync_output]
        if commit_result.stdout.strip():
            deploy_parts.append(commit_result.stdout.strip())
        if push_result.stderr.strip():
            deploy_parts.append(push_result.stderr.strip())
        if push_result.stdout.strip():
            deploy_parts.append(push_result.stdout.strip())
        deploy_output = "\n\n".join(part for part in deploy_parts if part)
        messagebox.showinfo(
            "WebUpdate",
            "Webová data byla synchronizována, commitnuta a pushnuta na GitHub.\n\n"
            f"{deploy_output}",
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

        fr = row.get("EN", "")
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
        self.input_entry.configure(fg="black")
        self._stop_hint_blink()

        if self.lang_var.get() == "EN":
            self.fr_var.set(fr)
            self.cz_var.set("???")
            self.hidden_side = "CZ"
        else:
            self.cz_var.set(cz)
            self.fr_var.set("???")
            self.hidden_side = "EN"
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
        return [i for i in indices if (self.rows[i].get("EN") or "").strip()]

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
            messagebox.showinfo("Info", "Žádná EN slovíčka pro aktuální výběr.")
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

        fr = ((row.get("EN") or row.get("FR") or "").strip())
        cz = (row.get("CZ") or "").strip()
        learned = row.get("L", "").strip().lower() == "ano"
        hard_training = row.get("HT", "").strip().lower() == "ano"

        self.learned_var.set(learned)
        self.hard_training_var.set(hard_training)
        self.input_var.set("")
        self.sentence_var.set("")
        self.sentence_t_var.set("")
        self.thumb_var.set("")
        self.input_entry.configure(fg="black")

        # V turbo režimu vždy rovnou zobrazíme FR + CZ a pustíme audio/blikání.
        self.fr_var.set(fr)
        self.cz_var.set(cz)
        self.fr_hint_var.set(fr)
        self.hidden_side = None
        self._update_picture_display(row)
        self._start_hint_blink(colors=("red", "green", "white"), font_size=80, max_toggles=18)
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
        fr = row.get("EN", "").strip()
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
            allowed_cz = self._cz_meanings_for_en(row.get("EN", ""))
            if not allowed_cz:
                allowed_cz = [row.get("CZ", "").strip()]
            allowed_normalized = {value.casefold() for value in allowed_cz if value}
            if typed and typed.casefold() not in allowed_normalized:
                self.input_entry.configure(fg="red")
            else:
                self.input_entry.configure(fg="black")

        # V režimu Read zobraz FR nápovědu staticky (bez blikání).
        self.fr_hint_var.set(fr)
        self._stop_hint_blink()

        self.fr_var.set(row.get("EN", ""))
        if self.turbo_mode:
            self.cz_var.set(row.get("CZ", ""))
            self.sentence_var.set("")
            self.sentence_t_var.set("")
        else:
            all_meanings = self._cz_meanings_for_en(row.get("EN", ""))
            self.cz_var.set("\n".join(all_meanings) if all_meanings else row.get("CZ", ""))
            self.sentence_var.set(row.get("Sentence", ""))
            self.sentence_t_var.set(row.get("SentenceT", ""))
        self.hidden_side = None
        if self.turbo_mode:
            self.fr_hint_label.configure(fg="red", font=("Helvetica", 80, "bold"))
            self._speak_turbo_current(row)
        else:
            self.fr_hint_label.configure(fg="green", font=("Helvetica", 55, "bold"))
            self._speak_current(row)

    def on_learned_toggled(self):
        self._persist_current_status_flags()

    def on_hard_training_toggled(self):
        self._persist_current_status_flags()

    def _start_hint_blink(self, colors=("green", "white"), font_size=55, max_toggles=6):
        self._stop_hint_blink()
        self.hint_blink_colors = colors
        self.hint_blink_color_index = 0
        self.hint_blink_max_toggles = max_toggles
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.fr_hint_label.configure(fg=colors[0], font=("Helvetica", font_size, "bold"))
        # Bezpečnost: v Turbo režimu hint nebliká (epilepsie / citlivost na blikání).
        if self.turbo_mode:
            return
        self.hint_blink_job = self.master.after(350, self._toggle_hint_blink)

    def _stop_hint_blink(self):
        if self.hint_blink_job is not None:
            self.master.after_cancel(self.hint_blink_job)
            self.hint_blink_job = None
        self.hint_blink_on = True
        self.hint_blink_toggles = 0
        self.hint_blink_colors = ("green", "white")
        self.hint_blink_color_index = 0
        self.hint_blink_max_toggles = 6
        if hasattr(self, "fr_hint_label"):
            self.fr_hint_label.configure(fg="green", font=("Helvetica", 55, "bold"))

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
        fr = row.get("EN", "").strip()
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

    def _say_blocking(self, voice, text):
        text = (text or "").strip()
        if not text:
            return
        try:
            subprocess.run(
                ["say", "-v", voice, text],
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

        fr = ((row.get("EN") or row.get("FR") or "").strip())
        cz = (row.get("CZ") or "").strip()
        sequence = [
            (self.fr_voice, fr),
            (self.cz_voice, cz),
            (self.fr_voice, fr),
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
        win.title("Input - VocabularyEN.csv")
        win.geometry("1320x800")
        win.minsize(1100, 700)
        win.configure(bg="white")
        self.input_window = win
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

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        columns = ("Order", "EN", "CZ", "Sentence", "SentenceT", "L", "HT")
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
        tree.heading("EN", text="EN")
        tree.heading("CZ", text="CZ")
        tree.heading("Sentence", text="Sentence")
        tree.heading("SentenceT", text="SentenceT")
        tree.heading("L", text="L")
        tree.heading("HT", text="HT")

        tree.column("Order", width=80, anchor="center")
        tree.column("EN", width=200, anchor="w")
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

        tk.Label(form, text="EN:", bg="white").grid(row=0, column=0, sticky="w")
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
        buttons_left.grid(row=0, column=4, rowspan=2, sticky="w", padx=(6, 0))
        tk.Button(buttons_left, text="Add Row", command=self.add_new_row).pack(side="left")
        tk.Button(buttons_left, text="Insert Row", command=self.insert_row).pack(
            side="left", padx=(8, 0)
        )
        tk.Button(buttons_left, text="Delete", command=self.delete_selected_row).pack(
            side="left", padx=(8, 0)
        )

        form.grid_columnconfigure(5, weight=1)
        tk.Button(form, text="Training", command=_on_input_window_close).grid(
            row=0, column=6, rowspan=2, sticky="e", padx=(8, 0)
        )

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
        self._search_input_value("EN", self.new_fr_var.get(), self.new_fr_entry)

    def search_input_cz(self):
        self._search_input_value("CZ", self.new_cz_var.get(), self.new_cz_entry)

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
                    row.get("EN", ""),
                    row.get("CZ", ""),
                    row.get("Sentence", ""),
                    row.get("SentenceT", ""),
                    self._checkbox_mark(row.get("L", "ne")),
                    self._checkbox_mark(row.get("HT", "ne")),
                ),
            )

    def _checkbox_mark(self, value):
        return "☑" if (value or "").strip().lower() == "ano" else "☐"

    def _toggle_input_checkbox(self, idx, column_name):
        if idx < 0 or idx >= len(self.rows):
            return
        row = self.rows[idx]
        current = (row.get(column_name, "ne") or "ne").strip().lower()
        new_value = "ne" if current == "ano" else "ano"
        row[column_name] = new_value
        self._save_csv()
        if self.input_tree:
            self.input_tree.item(
                str(idx),
                values=(
                    row.get("Order", ""),
                    row.get("EN", ""),
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
        if col_id not in ("#6", "#7"):  # L, HT
            return
        try:
            idx = int(row_id)
        except ValueError:
            return "break"
        column_name = "L" if col_id == "#6" else "HT"
        self._toggle_input_checkbox(idx, column_name)
        self.input_tree.selection_set(row_id)
        self.input_tree.focus(row_id)
        return "break"

    def add_new_row(self):
        fr = self.new_fr_var.get().strip()
        cz = self.new_cz_var.get().strip()
        sentence = self.new_sentence_var.get().strip()
        sentence_t = self.new_sentence_t_var.get().strip()
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej EN i CZ.")
            return

        next_order = 1
        if self.rows:
            try:
                next_order = max(int(r.get("Order", "0") or 0) for r in self.rows) + 1
            except ValueError:
                next_order = len(self.rows) + 1

        new_row = {
            "EN": fr,
            "CZ": cz,
            "Order": str(next_order),
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
            "HT": "ne",
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
                    new_row.get("EN", ""),
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
        if not fr or not cz:
            messagebox.showwarning("Chybí data", "Zadej EN i CZ.")
            return

        try:
            selected_idx = int(selected[0])
        except ValueError:
            return
        if selected_idx < 0 or selected_idx >= len(self.rows):
            return

        new_row = {
            "EN": fr,
            "CZ": cz,
            "Order": "",
            "Sentence": sentence,
            "SentenceT": sentence_t,
            "L": "ne",
            "HT": "ne",
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

        # Columns: Order, EN, CZ, Sentence, SentenceT, L, HT
        fr = (values[1] if len(values) > 1 else "").strip()
        sentence = (values[3] if len(values) > 3 else "").strip()
        self._speak_current({"EN": fr, "Sentence": sentence})

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
        columns = ("Order", "EN", "CZ", "Sentence", "SentenceT", "L", "HT")
        if col_index < 0 or col_index >= len(columns):
            return
        column_name = columns[col_index]

        # prevent editing Order directly
        if column_name in ("Order", "L", "HT"):
            self.input_tree.selection_set(row_id)
            self.input_tree.focus(row_id)
            if column_name == "Order":
                self._read_tree_item(row_id)
            return

        x, y, width, height = self.input_tree.bbox(row_id, col_id)
        value = self.input_tree.set(row_id, column_name)

        if self.edit_entry is not None:
            self.edit_entry.destroy()

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
