import tkinter as tk
import random
import subprocess
import tempfile
import threading
import uuid
import shutil
from pathlib import Path

# ZÁKLADNÍ (nezvětšené) rozměry
BASE_BALL_DIAM = 40
BASE_SPACING = 10

# Konstanty rozložení
MARGIN_X = 40        # levý/pravý okraj
MIN_GAP = 40         # minimální mezera mezi skupinami
PLUS_WIDTH = 40
EQ_WIDTH = 60
NUMBERS_ICON_GRID_COLS = 4
NUMBERS_ICON_GRID_ROWS = 3
NUMBERS_ICON_GRID_MAX = NUMBERS_ICON_GRID_COLS * NUMBERS_ICON_GRID_ROWS
NUMBERS_OBJECTS_DIR = "assets/openmoji_numbers"

COLORS = [
    "red", "blue", "green", "yellow", "orange",
    "white", "black", "purple", "brown", "gray", "pink"
]
NUMBER_TEXT_COLORS = [
    "red", "blue", "green", "orange", "black", "purple", "brown", "gray", "pink"
]
TRAINING_COLORS = [
    ("white", "white"),
    ("black", "black"),
    ("purple", "purple"),
    ("gray", "gray"),
    ("yellow", "yellow"),
    ("red", "red"),
    ("blue", "blue"),
    ("green", "green"),
    ("brown", "brown"),
    ("pink", "pink"),
]

NUMBER_WORDS = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
}


def speak_english(text: str):
    try:
        subprocess.Popen(["say", "-v", "Samantha", text])
    except Exception:
        pass


def _find_edge_tts_bin() -> str | None:
    # 1) PATH, 2) typické uživatelské bin cesty na macOS, 3) Homebrew
    candidates = [
        shutil.which("edge-tts"),
        str(Path.home() / "Library/Python/3.11/bin/edge-tts"),
        str(Path.home() / "Library/Python/3.12/bin/edge-tts"),
        "/opt/homebrew/bin/edge-tts",
        "/usr/local/bin/edge-tts",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def _say_voice_exists(voice_name: str) -> bool:
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.DEVNULL)
        return any(line.startswith(voice_name + " ") for line in out.splitlines())
    except Exception:
        return False


def _speak_old_man_czech_fallback(text: str):
    # Preferuj mužský hlas, ale ověř, že na systému opravdu existuje.
    for voice in ("Alex", "Zuzana"):
        try:
            if voice == "Alex" and not _say_voice_exists("Alex"):
                continue
            if voice == "Zuzana" and not _say_voice_exists("Zuzana"):
                continue
            subprocess.Popen(["say", "-v", voice, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            continue


def _speak_czech_edge_tts_async(text: str) -> bool:
    """
    Pokus o externí TTS přes edge-tts (online, mužský CZ hlas).
    Vrací True, pokud se podařilo spustit job; jinak False.
    """
    edge_tts_bin = _find_edge_tts_bin()
    afplay_bin = shutil.which("afplay")
    if not edge_tts_bin or not afplay_bin:
        return False

    def worker():
        out_path = Path(tempfile.gettempdir()) / f"owl_tts_{uuid.uuid4().hex}.mp3"
        try:
            # Microsoft Edge TTS CLI (balík: edge-tts)
            subprocess.run(
                [
                    edge_tts_bin,
                    "--voice", "cs-CZ-AntoninNeural",
                    "--rate=-8%",
                    "--text", text,
                    "--write-media", str(out_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [afplay_bin, str(out_path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Když edge-tts selže (síť / voice / CLI), zkus systémový fallback
            _speak_old_man_czech_fallback(text)
        finally:
            try:
                out_path.unlink(missing_ok=True)
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()
    return True


def speak_old_man_czech(text: str):
    # 1) zkus externí TTS (mužský český hlas), 2) fallback na systémový say
    if _speak_czech_edge_tts_async(text):
        return
    _speak_old_man_czech_fallback(text)


def group_width(count: int, diam: float, spacing: float) -> float:
    if count <= 0:
        return 0.0
    return count * diam + (count - 1) * spacing


class ColorsAndNumbersApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Colors and Numbers")

        # šířka okna podle monitoru
        screen_w = master.winfo_screenwidth()
        canvas_w = max(800, screen_w - 100)   # minimálně 800

        self.screen_stack = tk.Frame(master, bg="white")
        self.screen_stack.pack(fill="both", expand=True)
        self.screen_stack.grid_rowconfigure(0, weight=1)
        self.screen_stack.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.screen_stack, bg="white")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.canvas = tk.Canvas(self.main_frame, width=canvas_w, height=420, bg="white")
        self.canvas.pack(padx=10, pady=10)

        status_frame = tk.Frame(self.main_frame, bg="white")
        status_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.number_label = tk.Label(
            status_frame, text="NUMBER", font=("Helvetica", 24, "bold"), bg="white"
        )
        self.number_label.pack(side="left")

        self.color_label = tk.Label(
            status_frame, text="COLOR", font=("Helvetica", 24, "bold"), bg="white"
        )
        self.color_label.pack(side="right")

        buttons_frame = tk.Frame(self.main_frame, bg="white")
        buttons_frame.pack(pady=(0, 10))

        self.new_button = tk.Button(
            buttons_frame, text="NEW", font=("Helvetica", 18, "bold"),
            command=self.new_example
        )
        self.new_button.pack(side="left", padx=20)

        self.numbers_mode_button = tk.Button(
            buttons_frame, text="Numbers", font=("Helvetica", 18, "bold"),
            command=self.show_numbers_screen
        )
        self.numbers_mode_button.pack(side="left", padx=20)

        self.turbo_button = tk.Button(
            buttons_frame, text="Turbo", font=("Helvetica", 18, "bold"),
            command=self.show_turbo_screen
        )
        self.turbo_button.pack(side="left", padx=20)

        self.colors_mode_button = tk.Button(
            buttons_frame, text="Colors", font=("Helvetica", 18, "bold"),
            command=self.show_colors_screen
        )
        self.colors_mode_button.pack(side="left", padx=20)

        # proměnné pro aktuální příklad
        self.left_count = 0
        self.right_count = 0
        self.left_colors = []
        self.right_colors = []
        self.result_drawn = False

        # aktuální (škálované) rozměry kuliček
        self.ball_diam = BASE_BALL_DIAM
        self.ball_spacing = BASE_SPACING

        # Numbers screen state
        self.numbers_after_ids = []
        self.numbers_seq_token = 0
        self.numbers_first = None
        self.numbers_second = None
        self.numbers_sum = None
        self.numbers_op = "+"
        self.numbers_result_drawn = False
        self.numbers_result_press_count = 0
        self.owl_special_shown = False
        self.owl_photo = None
        self.owl_photo_display = None
        self.owl_overlay_items = []
        self.owl_window = None
        self.owl_hide_after_id = None
        self.owl_prev_geometry = None
        self.owl_prev_state = None
        self.numbers_object_icon_paths = []
        self.numbers_object_base_photos = {}
        self.numbers_object_scaled_photos = {}
        self.numbers_slot_icon_paths = {"first": None, "second": None, "result": None}

        # Turbo numbers screen state
        self.turbo_after_ids = []
        self.turbo_running = False
        self.turbo_pending_step = None
        self.turbo_pending_args = ()
        self.turbo_pending_delay = 0
        self.turbo_current_number = None
        self.turbo_current_word = ""
        self.turbo_objects_render_refs = []

        # Colors screen state
        self.colors_after_ids = []
        self.colors_running = False
        self.colors_pending_step = None
        self.colors_pending_args = ()
        self.colors_pending_delay = 0
        self.colors_current_word = ""
        self.colors_cycle_pool = []

        self._load_numbers_object_pool()
        self._build_numbers_screen(canvas_w)
        self._build_turbo_screen(canvas_w)
        self._build_colors_screen(canvas_w)
        self.main_frame.tkraise()

        self.new_example()

    def _load_numbers_object_pool(self):
        icons_dir = Path(__file__).resolve().parent / NUMBERS_OBJECTS_DIR
        try:
            self.numbers_object_icon_paths = sorted(icons_dir.glob("*.png"))
        except Exception:
            self.numbers_object_icon_paths = []

    def _pick_numbers_slot_icons(self):
        if len(self.numbers_object_icon_paths) >= 3:
            chosen = random.sample(self.numbers_object_icon_paths, 3)
        elif self.numbers_object_icon_paths:
            chosen = [random.choice(self.numbers_object_icon_paths) for _ in range(3)]
        else:
            chosen = [None, None, None]
        self.numbers_slot_icon_paths = {
            "first": chosen[0],
            "second": chosen[1],
            "result": chosen[2],
        }

    def _get_scaled_numbers_icon(self, icon_path: Path, max_px: int):
        if icon_path is None:
            return None
        path_key = str(icon_path)
        if path_key not in self.numbers_object_base_photos:
            try:
                self.numbers_object_base_photos[path_key] = tk.PhotoImage(file=path_key)
            except Exception:
                return None

        base_photo = self.numbers_object_base_photos[path_key]
        base_w = max(1, int(base_photo.width()))
        base_h = max(1, int(base_photo.height()))
        target = max(8, int(max_px))
        factor = max(1, (max(base_w, base_h) + target - 1) // target)
        cache_key = (path_key, factor)

        if cache_key not in self.numbers_object_scaled_photos:
            if factor == 1:
                self.numbers_object_scaled_photos[cache_key] = base_photo
            else:
                self.numbers_object_scaled_photos[cache_key] = base_photo.subsample(factor, factor)

        return self.numbers_object_scaled_photos[cache_key]

    def _build_numbers_screen(self, canvas_w: int):
        self.numbers_frame = tk.Frame(self.screen_stack, bg="white")
        self.numbers_frame.grid(row=0, column=0, sticky="nsew")

        title = tk.Label(
            self.numbers_frame,
            text="Numbers",
            font=("Helvetica", 24, "bold"),
            bg="white",
        )
        title.pack(pady=(10, 5))

        self.numbers_canvas = tk.Canvas(
            self.numbers_frame, width=canvas_w, height=420, bg="white", highlightthickness=0
        )
        self.numbers_canvas.pack(padx=10, pady=(0, 10))

        btns = tk.Frame(self.numbers_frame, bg="white")
        btns.pack(pady=(0, 12))

        self.numbers_new_button = tk.Button(
            btns, text="New", font=("Helvetica", 18, "bold"),
            command=self.numbers_new_sequence
        )
        self.numbers_new_button.pack(side="left", padx=20)

        self.numbers_result_button = tk.Button(
            btns, text="Result", font=("Helvetica", 18, "bold"),
            command=self.numbers_show_result
        )
        self.numbers_result_button.pack(side="left", padx=20)

        self.numbers_back_button = tk.Button(
            btns, text="Back", font=("Helvetica", 18, "bold"),
            command=self.show_main_screen
        )
        self.numbers_back_button.pack(side="left", padx=20)

        self._numbers_prepare_canvas()

    def _numbers_prepare_canvas(self):
        c = self.numbers_canvas
        c.delete("all")
        w = int(c["width"])
        h = int(c["height"])
        number_font_size = max(96, min(128, int(h * 0.18)))
        word_font_size = max(26, min(42, int(h * 0.06)))
        op_font_size = max(72, min(96, int(h * 0.14)))
        mid_y = max(95, int(h * 0.20))
        word_y = h - max(52, int(h * 0.08))
        icons_top_y = mid_y + max(52, int(number_font_size * 0.42))
        icons_bottom_y = word_y - max(26, int(word_font_size * 0.75))
        if icons_bottom_y <= icons_top_y:
            icons_bottom_y = icons_top_y + 60

        x1 = int(w * 0.20)
        x_plus = int(w * 0.37)
        x2 = int(w * 0.52)
        x_eq = int(w * 0.68)
        x_res = int(w * 0.83)

        self.num_layout = {
            "mid_y": mid_y,
            "word_y": word_y,
            "icons_top_y": icons_top_y,
            "icons_bottom_y": icons_bottom_y,
            "x1": x1,
            "x_plus": x_plus,
            "x2": x2,
            "x_eq": x_eq,
            "x_res": x_res,
        }

        left_edge = 20
        right_edge = w - 20
        b1 = int((x1 + x_plus) / 2)
        b2 = int((x_plus + x2) / 2)
        b3 = int((x2 + x_eq) / 2)
        b4 = int((x_eq + x_res) / 2)
        self.num_layout["slot_boxes"] = {
            "first": (left_edge, b1 - 8, icons_top_y, icons_bottom_y),
            "second": (b2 + 8, b3 - 8, icons_top_y, icons_bottom_y),
            "result": (b4 + 8, right_edge, icons_top_y, icons_bottom_y),
        }

        self.numbers_items = {
            "first_num": c.create_text(x1, mid_y, text="", font=("Helvetica", number_font_size, "bold")),
            "first_word": c.create_text(x1, word_y, text="", font=("Helvetica", word_font_size, "bold")),
            "plus": c.create_text(x_plus, mid_y, text="", font=("Helvetica", op_font_size, "bold")),
            "second_num": c.create_text(x2, mid_y, text="", font=("Helvetica", number_font_size, "bold")),
            "second_word": c.create_text(x2, word_y, text="", font=("Helvetica", word_font_size, "bold")),
            "eq": c.create_text(x_eq, mid_y, text="", font=("Helvetica", op_font_size, "bold")),
            "result_num": c.create_text(x_res, mid_y, text="", font=("Helvetica", number_font_size, "bold")),
            "result_word": c.create_text(x_res, word_y, text="", font=("Helvetica", word_font_size, "bold")),
        }

    def _numbers_clear_objects(self, slot: str | None = None):
        if slot is None:
            self.numbers_canvas.delete("numbers_objects")
            return
        self.numbers_canvas.delete(f"numbers_objects_{slot}")

    def _numbers_draw_objects(self, slot: str, count: int):
        self._numbers_clear_objects(slot)
        if count is None or count <= 0:
            return

        count = min(NUMBERS_ICON_GRID_MAX, count)
        icon_path = self.numbers_slot_icon_paths.get(slot)
        if icon_path is None:
            return

        box = self.num_layout.get("slot_boxes", {}).get(slot)
        if not box:
            return
        left, right, top, bottom = box
        if right <= left or bottom <= top:
            return

        box_w = right - left
        box_h = bottom - top
        cell_w = box_w / NUMBERS_ICON_GRID_COLS
        cell_h = box_h / NUMBERS_ICON_GRID_ROWS
        # lehký padding v buňce; velikost se odvodí automaticky z dostupného prostoru
        max_px = int(min(cell_w * 0.86, cell_h * 0.86, 72))
        icon_img = self._get_scaled_numbers_icon(icon_path, max_px)
        if icon_img is None:
            return

        icon_w = max(1, int(icon_img.width()))
        icon_h = max(1, int(icon_img.height()))
        c = self.numbers_canvas

        rows_used = (count + NUMBERS_ICON_GRID_COLS - 1) // NUMBERS_ICON_GRID_COLS
        used_h = rows_used * cell_h
        top_offset = (box_h - used_h) / 2

        drawn = 0
        for row in range(rows_used):
            row_count = min(NUMBERS_ICON_GRID_COLS, count - drawn)
            used_w = row_count * cell_w
            left_offset = (box_w - used_w) / 2
            for col in range(row_count):
                cx = left + left_offset + col * cell_w + cell_w / 2
                cy = top + top_offset + row * cell_h + cell_h / 2
                c.create_image(
                    cx,
                    cy,
                    image=icon_img,
                    tags=("numbers_objects", f"numbers_objects_{slot}"),
                )
                drawn += 1

    def show_numbers_screen(self):
        self._cancel_numbers_sequence()
        self._pause_turbo_sequence()
        self._pause_colors_sequence()
        try:
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            self.master.geometry(f"{sw}x{sh}+0+0")
            self.master.update_idletasks()
        except Exception:
            pass
        try:
            canvas_w = max(900, self.master.winfo_width() - 40)
            canvas_h = max(480, self.master.winfo_height() - 180)
            self.numbers_canvas.config(width=canvas_w, height=canvas_h)
        except Exception:
            pass
        self._numbers_prepare_canvas()
        self.numbers_frame.tkraise()

    def show_main_screen(self):
        self._cancel_numbers_sequence()
        self._pause_turbo_sequence()
        self._pause_colors_sequence()
        self.main_frame.tkraise()

    def _build_turbo_screen(self, canvas_w: int):
        self.turbo_frame = tk.Frame(self.screen_stack, bg="white")
        self.turbo_frame.grid(row=0, column=0, sticky="nsew")

        title = tk.Label(
            self.turbo_frame,
            text="Turbo Numbers",
            font=("Helvetica", 24, "bold"),
            bg="white",
        )
        title.pack(pady=(10, 6))

        self.turbo_canvas = tk.Canvas(
            self.turbo_frame, width=canvas_w, height=520, bg="white", highlightthickness=0
        )
        self.turbo_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        btns = tk.Frame(self.turbo_frame, bg="white")
        btns.pack(pady=(0, 12))

        self.turbo_back_button = tk.Button(
            btns, text="Back", font=("Helvetica", 18, "bold"),
            command=self._turbo_back_to_main
        )
        self.turbo_back_button.pack(side="left", padx=20)

        self.turbo_go_button = tk.Button(
            btns, text="Go", font=("Helvetica", 18, "bold"),
            command=self.turbo_go
        )
        self.turbo_go_button.pack(side="left", padx=20)

        self.turbo_end_button = tk.Button(
            btns, text="End", font=("Helvetica", 18, "bold"),
            command=self.turbo_end
        )
        self.turbo_end_button.pack(side="left", padx=20)

        self._turbo_prepare_canvas()

    def _turbo_prepare_canvas(self):
        c = self.turbo_canvas
        c.delete("all")
        self.turbo_objects_render_refs = []

        w = int(c["width"])
        h = int(c["height"])
        title_y = max(70, int(h * 0.14))
        number_y = max(165, int(h * 0.34))
        objects_top = max(number_y + 80, int(h * 0.48))
        objects_bottom = h - 30

        word_font_size = max(34, min(58, int(h * 0.085)))
        number_font_size = max(120, min(180, int(h * 0.22)))

        self.turbo_layout = {
            "w": w,
            "h": h,
            "word_y": title_y,
            "number_y": number_y,
            "objects_top": objects_top,
            "objects_bottom": objects_bottom,
            "objects_left": 30,
            "objects_right": w - 30,
            "word_font_size": word_font_size,
            "number_font_size": number_font_size,
        }

        self.turbo_items = {
            "word": c.create_text(
                w / 2, title_y, text="", font=("Helvetica", word_font_size, "bold"), fill="#1f3a93"
            ),
            "number": c.create_text(
                w / 2, number_y, text="", font=("Helvetica", number_font_size, "bold"), fill="black"
            ),
            "hint": c.create_text(
                w / 2,
                h - 18,
                text="Go = start/continue, End = pause",
                font=("Helvetica", 14, "bold"),
                fill="#666666",
            ),
        }

    def show_turbo_screen(self):
        self._cancel_numbers_sequence()
        self._pause_colors_sequence()
        try:
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            self.master.geometry(f"{sw}x{sh}+0+0")
            self.master.update_idletasks()
        except Exception:
            pass
        try:
            canvas_w = max(900, self.master.winfo_width() - 40)
            canvas_h = max(520, self.master.winfo_height() - 180)
            self.turbo_canvas.config(width=canvas_w, height=canvas_h)
        except Exception:
            pass
        self._turbo_prepare_canvas()
        self._turbo_render_idle_state()
        self.turbo_frame.tkraise()

    def _turbo_render_idle_state(self):
        c = self.turbo_canvas
        c.itemconfig(self.turbo_items["word"], text="")
        c.itemconfig(self.turbo_items["number"], text="")
        self._turbo_clear_objects()
        c.itemconfig(
            self.turbo_items["hint"],
            text="Go = start/continue, End = pause, Back = main screen",
        )

    def _turbo_clear_objects(self):
        self.turbo_canvas.delete("turbo_objects")
        self.turbo_objects_render_refs = []

    def _turbo_draw_objects(self, count: int):
        self._turbo_clear_objects()
        if count <= 0:
            return

        c = self.turbo_canvas
        layout = self.turbo_layout
        left = layout["objects_left"]
        right = layout["objects_right"]
        top = layout["objects_top"]
        bottom = layout["objects_bottom"]
        box_w = max(1, right - left)
        box_h = max(1, bottom - top)

        cols = NUMBERS_ICON_GRID_COLS
        rows = NUMBERS_ICON_GRID_ROWS
        cell_w = box_w / cols
        cell_h = box_h / rows
        max_px = int(min(cell_w * 0.80, cell_h * 0.80, 100))
        rows_used = (count + cols - 1) // cols
        used_h = rows_used * cell_h
        top_offset = (box_h - used_h) / 2

        for idx in range(count):
            row = idx // cols
            col = idx % cols
            row_count = min(cols, count - row * cols)
            used_w = row_count * cell_w
            left_offset = (box_w - used_w) / 2
            cx = left + left_offset + (col * cell_w) + cell_w / 2
            cy = top + top_offset + (row * cell_h) + cell_h / 2

            icon_path = None
            if self.numbers_object_icon_paths:
                icon_path = random.choice(self.numbers_object_icon_paths)
            icon_img = self._get_scaled_numbers_icon(icon_path, max_px) if icon_path else None
            if icon_img is not None:
                self.turbo_objects_render_refs.append(icon_img)
                c.create_image(cx, cy, image=icon_img, tags=("turbo_objects",))
            else:
                r = max(8, int(min(cell_w, cell_h) * 0.22))
                fill = random.choice(COLORS)
                outline = "black" if fill == "white" else fill
                width = 2 if fill == "white" else 1
                c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=width, tags=("turbo_objects",))

    def _turbo_schedule(self, delay_ms, callback, *args):
        self.turbo_pending_step = callback
        self.turbo_pending_args = args
        self.turbo_pending_delay = int(delay_ms)

        def runner():
            try:
                self.turbo_after_ids.remove(after_id)
            except Exception:
                pass
            if not self.turbo_running:
                return
            self.turbo_pending_step = None
            self.turbo_pending_args = ()
            self.turbo_pending_delay = 0
            callback(*args)

        after_id = self.master.after(delay_ms, runner)
        self.turbo_after_ids.append(after_id)
        return after_id

    def _cancel_turbo_timers_only(self):
        for after_id in self.turbo_after_ids:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
        self.turbo_after_ids.clear()

    def _pause_turbo_sequence(self):
        self.turbo_running = False
        self._cancel_turbo_timers_only()

    def _reset_turbo_sequence(self):
        self._pause_turbo_sequence()
        self.turbo_pending_step = None
        self.turbo_pending_args = ()
        self.turbo_pending_delay = 0
        self.turbo_current_number = None
        self.turbo_current_word = ""

    def _turbo_back_to_main(self):
        self._reset_turbo_sequence()
        self.show_main_screen()

    def turbo_end(self):
        self._pause_turbo_sequence()

    def turbo_go(self):
        if self.turbo_running:
            return
        self.turbo_running = True
        if self.turbo_pending_step is not None:
            self._turbo_schedule(max(0, self.turbo_pending_delay), self.turbo_pending_step, *self.turbo_pending_args)
        else:
            self._turbo_start_cycle()

    def _turbo_start_cycle(self):
        if not self.turbo_running:
            return
        n = random.randint(0, 12)
        word = NUMBER_WORDS[n]
        self.turbo_current_number = n
        self.turbo_current_word = word

        c = self.turbo_canvas
        c.itemconfig(self.turbo_items["word"], text="")
        c.itemconfig(self.turbo_items["number"], text=str(n))
        c.itemconfig(self.turbo_items["hint"], text="")
        self._turbo_draw_objects(n)

        self._turbo_schedule(3000, self._turbo_show_word)

    def _turbo_show_word(self):
        if not self.turbo_running or self.turbo_current_number is None:
            return
        self.turbo_canvas.itemconfig(
            self.turbo_items["word"],
            text=self.turbo_current_word.upper(),
        )
        self._turbo_schedule(3000, self._turbo_speak_number)

    def _turbo_speak_number(self):
        if not self.turbo_running or self.turbo_current_number is None:
            return
        speak_english(self.turbo_current_word)
        self._turbo_schedule(2000, self._turbo_start_cycle)

    def _build_colors_screen(self, canvas_w: int):
        self.colors_frame = tk.Frame(self.screen_stack, bg="white")
        self.colors_frame.grid(row=0, column=0, sticky="nsew")

        title = tk.Label(
            self.colors_frame,
            text="Colors",
            font=("Helvetica", 24, "bold"),
            bg="white",
        )
        title.pack(pady=(10, 6))

        self.colors_canvas = tk.Canvas(
            self.colors_frame, width=canvas_w, height=520, bg="white", highlightthickness=0
        )
        self.colors_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        btns = tk.Frame(self.colors_frame, bg="white")
        btns.pack(pady=(0, 12))

        self.colors_go_button = tk.Button(
            btns, text="Go", font=("Helvetica", 18, "bold"),
            command=self.colors_go
        )
        self.colors_go_button.pack(side="left", padx=20)

        self.colors_stop_button = tk.Button(
            btns, text="Stop", font=("Helvetica", 18, "bold"),
            command=self.colors_stop
        )
        self.colors_stop_button.pack(side="left", padx=20)

        self.colors_back_button = tk.Button(
            btns, text="Back", font=("Helvetica", 18, "bold"),
            command=self._colors_back_to_main
        )
        self.colors_back_button.pack(side="left", padx=20)

        self._colors_prepare_canvas()

    def _next_training_color(self):
        if not self.colors_cycle_pool:
            self.colors_cycle_pool = list(TRAINING_COLORS)
            random.shuffle(self.colors_cycle_pool)
        return self.colors_cycle_pool.pop()

    def _colors_prepare_canvas(self):
        c = self.colors_canvas
        c.delete("all")
        w = int(c["width"])
        h = int(c["height"])
        center_x = w / 2
        object_y = max(180, int(h * 0.45))
        object_size = max(130, min(240, int(min(w, h) * 0.26)))
        word_y = h - max(78, int(h * 0.16))

        self.colors_layout = {
            "center_x": center_x,
            "object_y": object_y,
            "object_size": object_size,
            "word_y": word_y,
        }

        self.colors_items = {
            "word": c.create_text(
                center_x,
                word_y,
                text="",
                font=("Helvetica", 52, "bold"),
                fill="#1f3a93",
            ),
            "hint": c.create_text(
                center_x,
                h - 20,
                text="Go = start, Stop = pause, Back = main screen",
                font=("Helvetica", 14, "bold"),
                fill="#666666",
            ),
        }

    def show_colors_screen(self):
        self._cancel_numbers_sequence()
        self._pause_turbo_sequence()
        try:
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            self.master.geometry(f"{sw}x{sh}+0+0")
            self.master.update_idletasks()
        except Exception:
            pass
        try:
            canvas_w = max(900, self.master.winfo_width() - 40)
            canvas_h = max(520, self.master.winfo_height() - 180)
            self.colors_canvas.config(width=canvas_w, height=canvas_h)
        except Exception:
            pass
        self._colors_prepare_canvas()
        self.colors_frame.tkraise()

    def _draw_color_object(self, color_name: str, shape_name: str):
        c = self.colors_canvas
        c.delete("color_object")
        center_x = self.colors_layout["center_x"]
        object_y = self.colors_layout["object_y"]
        size = self.colors_layout["object_size"]
        half = size / 2
        left = center_x - half
        top = object_y - half
        right = center_x + half
        bottom = object_y + half

        outline = "#333333" if color_name == "white" else color_name
        width = 4 if color_name == "white" else 2

        if shape_name == "square":
            c.create_rectangle(
                left, top, right, bottom, fill=color_name, outline=outline, width=width, tags=("color_object",)
            )
        elif shape_name == "triangle":
            c.create_polygon(
                center_x, top, right, bottom, left, bottom,
                fill=color_name, outline=outline, width=width, tags=("color_object",)
            )
        else:
            c.create_oval(
                left, top, right, bottom, fill=color_name, outline=outline, width=width, tags=("color_object",)
            )

    def _colors_schedule(self, delay_ms, callback, *args):
        self.colors_pending_step = callback
        self.colors_pending_args = args
        self.colors_pending_delay = int(delay_ms)

        def runner():
            try:
                self.colors_after_ids.remove(after_id)
            except Exception:
                pass
            if not self.colors_running:
                return
            self.colors_pending_step = None
            self.colors_pending_args = ()
            self.colors_pending_delay = 0
            callback(*args)

        after_id = self.master.after(delay_ms, runner)
        self.colors_after_ids.append(after_id)
        return after_id

    def _cancel_colors_timers_only(self):
        for after_id in self.colors_after_ids:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
        self.colors_after_ids.clear()

    def _pause_colors_sequence(self):
        self.colors_running = False
        self._cancel_colors_timers_only()

    def _reset_colors_sequence(self):
        self._pause_colors_sequence()
        self.colors_pending_step = None
        self.colors_pending_args = ()
        self.colors_pending_delay = 0
        self.colors_current_word = ""

    def _colors_back_to_main(self):
        self._reset_colors_sequence()
        self.show_main_screen()

    def colors_go(self):
        if self.colors_running:
            return
        self.colors_running = True
        if self.colors_pending_step is not None:
            self._colors_schedule(
                max(0, self.colors_pending_delay),
                self.colors_pending_step,
                *self.colors_pending_args,
            )
        else:
            self._colors_start_cycle()

    def colors_stop(self):
        self._pause_colors_sequence()

    def _colors_start_cycle(self):
        if not self.colors_running:
            return
        word, tk_color = self._next_training_color()
        shape = random.choice(["circle", "square", "triangle"])
        self.colors_current_word = word
        self._draw_color_object(tk_color, shape)
        self.colors_canvas.itemconfig(self.colors_items["word"], text="")
        self.colors_canvas.itemconfig(self.colors_items["hint"], text="")
        self._colors_schedule(2000, self._colors_show_word)

    def _colors_show_word(self):
        if not self.colors_running or not self.colors_current_word:
            return
        self.colors_canvas.itemconfig(
            self.colors_items["word"],
            text=self.colors_current_word.upper(),
        )
        self._colors_schedule(2000, self._colors_speak_word)

    def _colors_speak_word(self):
        if not self.colors_running or not self.colors_current_word:
            return
        speak_english(self.colors_current_word)
        self._colors_schedule(2000, self._colors_start_cycle)

    def _random_number_color(self) -> str:
        return random.choice(NUMBER_TEXT_COLORS)

    def _schedule_numbers(self, delay_ms, callback, *args):
        after_id = self.master.after(delay_ms, callback, *args)
        self.numbers_after_ids.append(after_id)
        return after_id

    def _cancel_numbers_sequence(self):
        self.numbers_seq_token += 1
        for after_id in self.numbers_after_ids:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
        self.numbers_after_ids.clear()
        if self.owl_hide_after_id:
            try:
                self.master.after_cancel(self.owl_hide_after_id)
            except Exception:
                pass
            self.owl_hide_after_id = None

    def _maximize_main_window_for_owl(self):
        try:
            self.master.update_idletasks()
            self.owl_prev_geometry = self.master.winfo_geometry()
            try:
                self.owl_prev_state = self.master.state()
            except Exception:
                self.owl_prev_state = "normal"
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            self.master.geometry(f"{sw}x{sh}+0+0")
            self.master.update_idletasks()
        except Exception:
            pass

    def _restore_main_window_after_owl(self):
        try:
            if self.owl_prev_state and self.owl_prev_state not in ("normal", ""):
                try:
                    self.master.state(self.owl_prev_state)
                except Exception:
                    pass
            if self.owl_prev_geometry:
                self.master.geometry(self.owl_prev_geometry)
                self.master.update_idletasks()
        except Exception:
            pass

    def _hide_owl_overlay(self):
        if self.owl_window is not None:
            try:
                self.owl_window.destroy()
            except Exception:
                pass
            self.owl_window = None
        self.owl_photo = None
        self.owl_photo_display = None
        self.owl_overlay_items.clear()
        self.owl_hide_after_id = None
        self._restore_main_window_after_owl()

    def _show_owl_easter_egg_once(self):
        if self.owl_special_shown:
            return
        self.owl_special_shown = True

        self._hide_owl_overlay()
        self._maximize_main_window_for_owl()

        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        win = tk.Toplevel(self.master)
        self.owl_window = win
        win.title("Owl")
        win.configure(bg="white")
        win.geometry(f"{sw}x{sh}+0+0")
        try:
            win.transient(self.master)
        except Exception:
            pass
        try:
            win.lift()
            win.attributes("-topmost", True)
        except Exception:
            pass

        holder = tk.Frame(win, bg="white")
        holder.pack(fill="both", expand=True, padx=20, pady=20)

        script_dir = Path(__file__).resolve().parent
        candidate_paths = [
            script_dir / "oul.png",
            script_dir.parent / "oul.png",
            Path.cwd() / "oul.png",
        ]
        img_path = next((p for p in candidate_paths if p.exists()), candidate_paths[0])
        image_loaded = False
        if img_path.exists():
            try:
                self.owl_photo = tk.PhotoImage(file=str(img_path))
                disp = self.owl_photo
                iw = max(1, self.owl_photo.width())
                ih = max(1, self.owl_photo.height())
                avail_w = max(100, sw - 80)
                avail_h = max(100, sh - 140)
                factor_w = (iw + avail_w - 1) // avail_w
                factor_h = (ih + avail_h - 1) // avail_h
                factor = max(1, factor_w, factor_h)
                if factor > 1:
                    disp = self.owl_photo.subsample(factor, factor)
                self.owl_photo_display = disp
                lbl = tk.Label(holder, image=self.owl_photo_display, bg="white")
                lbl.pack(expand=True)
                image_loaded = True
            except Exception:
                self.owl_photo = None
                self.owl_photo_display = None

        if not image_loaded:
            txt = tk.Label(
                holder,
                text=f"OUL.PNG\nNenalezeno: {img_path}",
                font=("Helvetica", 36, "bold"),
                fg="#333333",
                bg="white"
            )
            txt.pack(expand=True)

        phrase = (
            "Hello Katka, Jana, Markéta, Simča! Jsem moudrá sova, která vás stále sleduje. "
            "Jsem ráda, že si opět opakujete čísla. To je velmi důležité. "
            "Vím, že jste dostaly vysvědčení, gratuluji. "
            "Také Janě gratuluji k dosažení třetí úrovně v duolingo. "
            "Pevně věřím, že vám radost z poznávání nového vydrží! "
            "Držím vám děvčata palce a příště se zase uslyšíme. Hůhůhůhů. "
        )
        speak_old_man_czech(phrase)

        # Jednorázově zobrazit a zase skrýt (do dalšího spuštění aplikace se už neukáže).
        # Delší čas, aby mužský hlas stihl doříct text.
        self.owl_hide_after_id = self.master.after(40000, self._hide_owl_overlay)

    def _speak_once_scheduled(self, word: str):
        speak_english(word)

    def _flash_number(self, item_key: str, flashes: int, done_callback, token: int):
        canvas = self.numbers_canvas
        item_id = self.numbers_items[item_key]
        interval_ms = 220
        total_toggles = flashes * 2

        def toggle(step=0):
            if token != self.numbers_seq_token:
                return
            if step >= total_toggles:
                canvas.itemconfig(item_id, state="normal")
                done_callback()
                return
            current_state = canvas.itemcget(item_id, "state")
            next_state = "hidden" if current_state != "hidden" else "normal"
            canvas.itemconfig(item_id, state=next_state)
            self._schedule_numbers(interval_ms, toggle, step + 1)

        canvas.itemconfig(item_id, state="normal")
        self._schedule_numbers(interval_ms, toggle, 0)

    def numbers_new_sequence(self):
        self._cancel_numbers_sequence()
        self._numbers_prepare_canvas()
        self.numbers_result_drawn = False

        self.numbers_op = random.choice(["+", "-"])

        if self.numbers_op == "+":
            a = random.randint(1, 11)
            b_max = min(11, 12 - a)
            b = random.randint(1, b_max)
            result = a + b
        else:
            a = random.randint(1, 11)
            b = random.randint(1, a)  # dovolíme výsledek 0, ale ne záporný
            result = a - b

        self.numbers_first = a
        self.numbers_second = b
        self.numbers_sum = result
        self.numbers_first_color = self._random_number_color()
        self.numbers_second_color = self._random_number_color()
        self.numbers_result_color = self._random_number_color()
        self._pick_numbers_slot_icons()
        token = self.numbers_seq_token

        self._numbers_step_first_number(token)

    def _numbers_step_first_number(self, token: int):
        if token != self.numbers_seq_token:
            return
        c = self.numbers_canvas
        c.itemconfig(
            self.numbers_items["first_num"],
            text=str(self.numbers_first),
            state="normal",
            fill=self.numbers_first_color,
        )
        c.itemconfig(
            self.numbers_items["first_word"],
            text="",
            state="normal",
            fill=self.numbers_first_color,
        )
        self._numbers_draw_objects("first", self.numbers_first)

        # Číslo už nebliká, jen se zobrazí a pokračuje se dál.
        self._schedule_numbers(500, self._numbers_step_first_word, token)

    def _numbers_step_first_word(self, token: int):
        if token != self.numbers_seq_token:
            return
        word = NUMBER_WORDS[self.numbers_first]
        self.numbers_canvas.itemconfig(
            self.numbers_items["first_word"],
            text=word.upper(),
            state="normal",
            fill=self.numbers_first_color,
        )
        self._speak_once_scheduled(word)
        self._schedule_numbers(2200, self._numbers_step_plus, token)

    def _numbers_step_plus(self, token: int):
        if token != self.numbers_seq_token:
            return
        spoken_op = "plus" if self.numbers_op == "+" else "minus"
        self.numbers_canvas.itemconfig(self.numbers_items["plus"], text=self.numbers_op, state="normal")
        speak_english(spoken_op)
        self._schedule_numbers(900, self._numbers_step_second_number, token)

    def _numbers_step_second_number(self, token: int):
        if token != self.numbers_seq_token:
            return
        self.numbers_canvas.itemconfig(
            self.numbers_items["second_num"],
            text=str(self.numbers_second),
            state="normal",
            fill=self.numbers_second_color,
        )
        self.numbers_canvas.itemconfig(
            self.numbers_items["second_word"],
            text="",
            state="normal",
            fill=self.numbers_second_color,
        )
        self._numbers_draw_objects("second", self.numbers_second)
        # Číslo už nebliká, jen se zobrazí a pokračuje se dál.
        self._schedule_numbers(500, self._numbers_step_second_word, token)

    def _numbers_step_second_word(self, token: int):
        if token != self.numbers_seq_token:
            return
        word = NUMBER_WORDS[self.numbers_second]
        self.numbers_canvas.itemconfig(
            self.numbers_items["second_word"],
            text=word.upper(),
            state="normal",
            fill=self.numbers_second_color,
        )
        self._speak_once_scheduled(word)
        self._schedule_numbers(2200, self._numbers_step_equal, token)

    def _numbers_step_equal(self, token: int):
        if token != self.numbers_seq_token:
            return
        self.numbers_canvas.itemconfig(self.numbers_items["eq"], text="=", state="normal")
        speak_english("is")

    def numbers_show_result(self):
        if self.numbers_sum is None:
            return
        self.numbers_result_press_count += 1
        self.numbers_result_drawn = True
        word = NUMBER_WORDS[self.numbers_sum]
        self.numbers_canvas.itemconfig(
            self.numbers_items["result_num"],
            text=str(self.numbers_sum),
            state="normal",
            fill=self.numbers_result_color,
        )
        self.numbers_canvas.itemconfig(
            self.numbers_items["result_word"],
            text=word.upper(),
            state="normal",
            fill=self.numbers_result_color,
        )
        self._numbers_draw_objects("result", self.numbers_sum)
        self._speak_once_scheduled(word)
        if self.numbers_result_press_count == 3 and not self.owl_special_shown:
            # Spusť sovu už po třetím zobrazení výsledku na numbers screenu.
            self._schedule_numbers(2500, self._show_owl_easter_egg_once)

    def new_example(self):
        self.canvas.delete("all")
        self.result_drawn = False
        self.number_label.config(text="NUMBER")
        self.color_label.config(text="COLOR", fg="black")

        # náhodná čísla tak, aby součet <= 12
        while True:
            a = random.randint(1, 11)
            b = random.randint(1, 11)
            if a + b <= 12:
                break

        self.left_count = a
        self.right_count = b
        total = a + b

        self.left_colors = [random.choice(COLORS) for _ in range(a)]
        self.right_colors = [random.choice(COLORS) for _ in range(b)]

        balls_y = 220
        number_y = 130
        word_y = 300

        canvas_w = int(self.canvas["width"])

        # spočítáme, kolik místa potřebujeme pro *největší možné* kuličky
        wl0 = group_width(a, BASE_BALL_DIAM, BASE_SPACING)
        wr0 = group_width(b, BASE_BALL_DIAM, BASE_SPACING)
        wres0 = group_width(total, BASE_BALL_DIAM, BASE_SPACING)

        # dostupná šířka pro kuličky (po odečtení okrajů, plus a rovná se)
        constant_part = PLUS_WIDTH + EQ_WIDTH + 4 * MIN_GAP
        available_for_balls = canvas_w - 2 * MARGIN_X - constant_part

        # měřítko – pokud není místo, kuličky se zmenší
        balls_total0 = wl0 + wr0 + wres0
        if balls_total0 <= 0:
            scale = 1.0
        else:
            scale = min(1.0, available_for_balls / balls_total0)
            if scale <= 0:
                scale = 1.0

        self.ball_diam = BASE_BALL_DIAM * scale
        self.ball_spacing = BASE_SPACING * scale

        wl = group_width(a, self.ball_diam, self.ball_spacing)
        wr = group_width(b, self.ball_diam, self.ball_spacing)
        wres = group_width(total, self.ball_diam, self.ball_spacing)

        # --- Rozložení skupin odleva doprava ---

        x = MARGIN_X

        # levý operand
        left_base_x = x
        x += wl + MIN_GAP

        # plus uprostřed malé oblasti
        plus_center_x = x + PLUS_WIDTH / 2
        self.canvas.create_text(
            plus_center_x, number_y,
            text="+", font=("Helvetica", 38, "bold")
        )
        x += PLUS_WIDTH + MIN_GAP

        # pravý operand
        right_base_x = x
        x += wr + MIN_GAP

        # "="
        eq_left = x
        eq_right = eq_left + EQ_WIDTH
        eq_center_x = (eq_left + eq_right) / 2
        eq_top = number_y - 25
        eq_bottom = number_y + 25

        eq_rect = self.canvas.create_rectangle(
            eq_left, eq_top, eq_right, eq_bottom, width=3
        )
        eq_text = self.canvas.create_text(
            eq_center_x, number_y,
            text="=", font=("Helvetica", 32, "bold")
        )
        self.canvas.itemconfig(eq_rect, tags=("equal_button",))
        self.canvas.itemconfig(eq_text, tags=("equal_button",))
        self.canvas.tag_bind("equal_button", "<Button-1>", self.on_equal_click)

        x = eq_right + MIN_GAP
        result_base_x = x

        # souřadnice pro další použití
        self.result_area_x = result_base_x
        self.balls_y = balls_y
        self.number_y = number_y
        self.word_y = word_y

        # vykreslíme skutečné kuličky a texty
        _, _ = self.draw_operand(
            base_x=left_base_x,
            balls_y=balls_y,
            number_y=number_y,
            word_y=word_y,
            count=self.left_count,
            colors_list=self.left_colors,
        )

        _, _ = self.draw_operand(
            base_x=right_base_x,
            balls_y=balls_y,
            number_y=number_y,
            word_y=word_y,
            count=self.right_count,
            colors_list=self.right_colors,
        )

    def draw_operand(self, base_x, balls_y, number_y, word_y, count, colors_list):
        last_x2 = base_x
        d = self.ball_diam
        s = self.ball_spacing

        # kuličky
        for i, col in enumerate(colors_list):
            x1 = base_x + i * (d + s)
            y1 = balls_y
            x2 = x1 + d
            y2 = y1 + d
            last_x2 = x2

            outline = "black" if col == "white" else col
            width = 2 if col == "white" else 1

            oval_id = self.canvas.create_oval(
                x1, y1, x2, y2, fill=col, outline=outline, width=width
            )
            tag = f"ball_{oval_id}"
            self.canvas.itemconfig(oval_id, tags=(tag,))
            self.canvas.tag_bind(
                tag, "<Button-1>",
                lambda event, color=col: self.on_ball_click(color)
            )

        total_w = group_width(count, d, s)
        center_x = base_x + total_w / 2

        # číslo
        number_text_id = self.canvas.create_text(
            center_x, number_y,
            text=str(count), font=("Helvetica", 30, "bold")
        )
        self.canvas.tag_bind(
            number_text_id, "<Button-1>",
            lambda event, n=count: self.on_number_click(n)
        )

        # slovo
        word = NUMBER_WORDS[count].upper()
        word_text_id = self.canvas.create_text(
            center_x, word_y,
            text=word, font=("Helvetica", 22, "bold")
        )
        self.canvas.tag_bind(
            word_text_id, "<Button-1>",
            lambda event, n=count: self.on_number_click(n)
        )

        return last_x2, center_x

    def on_ball_click(self, color_name: str):
        word = color_name.upper()
        self.color_label.config(text=word, fg=color_name)
        speak_english(color_name)

    def on_number_click(self, n: int):
        word = NUMBER_WORDS[n]
        self.number_label.config(text=word.upper())
        speak_english(word)

    def on_equal_click(self, event):
        if self.result_drawn:
            return

        self.result_drawn = True
        total = self.left_count + self.right_count
        colors_result = self.left_colors + self.right_colors

        base_x = self.result_area_x
        balls_y = self.balls_y
        number_y = self.number_y
        word_y = self.word_y
        d = self.ball_diam
        s = self.ball_spacing

        for i, col in enumerate(colors_result):
            x1 = base_x + i * (d + s)
            y1 = balls_y
            x2 = x1 + d
            y2 = y1 + d

            outline = "black" if col == "white" else col
            width = 2 if col == "white" else 1

            oval_id = self.canvas.create_oval(
                x1, y1, x2, y2, fill=col, outline=outline, width=width
            )
            tag = f"result_ball_{oval_id}"
            self.canvas.itemconfig(oval_id, tags=(tag,))
            self.canvas.tag_bind(
                tag, "<Button-1>",
                lambda event, color=col: self.on_ball_click(color)
            )

        total_w = group_width(total, d, s)
        center_x = base_x + total_w / 2

        # rámeček s číslem
        box_margin_x = 25
        box_margin_y = 15

        rect_left = center_x - box_margin_x
        rect_right = center_x + box_margin_x
        rect_top = number_y - box_margin_y
        rect_bottom = number_y + box_margin_y

        self.canvas.create_rectangle(
            rect_left, rect_top, rect_right, rect_bottom, width=3
        )

        number_id = self.canvas.create_text(
            center_x, number_y,
            text=str(total),
            font=("Helvetica", 30, "bold")
        )
        self.canvas.tag_bind(
            number_id, "<Button-1>",
            lambda event, n=total: self.on_number_click(n)
        )

        word = NUMBER_WORDS[total].upper()
        word_id = self.canvas.create_text(
            center_x, word_y,
            text=word,
            font=("Helvetica", 22, "bold")
        )
        self.canvas.tag_bind(
            word_id, "<Button-1>",
            lambda event, n=total: self.on_number_click(n)
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorsAndNumbersApp(root)
    root.mainloop()
