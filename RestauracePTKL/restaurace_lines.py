import os
import re
import subprocess
import tkinter as tk
import zipfile
import traceback
from tkinter import messagebox
from xml.etree import ElementTree as ET
import sys

try:
    from PIL import Image, ImageTk  # type: ignore
except Exception:
    Image = None
    ImageTk = None


VOICE_CANDIDATES_BY_SPEAKER = {
    "Kate": ["Samantha", "Karen", "Moira"],
    "Lucy": ["Karen", "Samantha", "Tessa"],
    "Tom": ["Daniel", "Ralph", "Fred", "Reed", "Alex", "Bruce"],
    # Peter = mladší kluk, proto preferujeme jiný (a lehčí) hlas než Tom
    "Peter": ["Eddy", "Reed", "Fred", "Daniel", "Ralph", "Alex", "Bruce"],
    "Waiter": ["Reed", "Eddy", "Fred", "Ralph", "Daniel", "Alex", "Bruce"],
    "Woman": ["Moira", "Karen", "Samantha"],
}
_AVAILABLE_SAY_VOICES = None


def _get_available_say_voices():
    global _AVAILABLE_SAY_VOICES
    if _AVAILABLE_SAY_VOICES is not None:
        return _AVAILABLE_SAY_VOICES
    try:
        result = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True,
            text=True,
            check=False,
        )
        voices = set()
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if parts:
                voices.add(parts[0])
        _AVAILABLE_SAY_VOICES = voices
    except Exception:
        _AVAILABLE_SAY_VOICES = set()
    return _AVAILABLE_SAY_VOICES


def _choose_voice(preferred_voices):
    available = _get_available_say_voices()
    for voice in preferred_voices:
        if voice in available:
            return voice
    return "Samantha"


def speak_english(text: str, voice: str = "Samantha"):
    try:
        chosen_voice = _choose_voice([voice, "Samantha"])
        subprocess.Popen(["say", "-v", chosen_voice, text])
    except Exception:
        pass


def extract_speaker_and_spoken_text(line: str):
    english_part = line.split("/", 1)[0].strip()
    match = re.match(r"^([A-Za-z]+):\s*(.+)$", english_part)
    if not match:
        return None, english_part
    speaker = match.group(1)
    spoken_text = match.group(2).strip()
    return speaker, spoken_text


def normalize_text(raw: str) -> str:
    text = raw.replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    replacements = {
        "“": '"',
        "”": '"',
        "’": "'",
        "–": "-",
        "—": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def _load_text_lines_from_txt(path: str):
    with open(path, "rb") as f:
        raw_bytes = f.read()

    raw = None
    for enc in ("utf-8", "cp1250", "mac_roman", "cp1252", "latin-1"):
        try:
            raw = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raw = raw_bytes.decode("latin-1", errors="replace")

    text = normalize_text(raw)
    lines = [line.strip() for line in text.split("\n")]
    return [line for line in lines if line]


def _load_text_lines_from_docx(path: str):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")

    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    lines = []
    for p_el in root.findall(".//w:body/w:p", ns):
        parts = []
        for node in p_el.iter():
            if node.tag == f"{{{ns['w']}}}t":
                parts.append(node.text or "")
            elif node.tag == f"{{{ns['w']}}}tab":
                parts.append("\t")
            elif node.tag == f"{{{ns['w']}}}br":
                parts.append("\n")
        para = normalize_text("".join(parts))
        for line in para.split("\n"):
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def load_text_sections(path: str):
    base, _ = os.path.splitext(path)
    docx_path = base + ".docx"
    if os.path.exists(path):
        lines = _load_text_lines_from_txt(path)
    elif os.path.exists(docx_path):
        lines = _load_text_lines_from_docx(docx_path)
    else:
        raise FileNotFoundError(f"Missing file: {path}")

    sections = {i: [] for i in range(1, 8)}
    current = None
    for line in lines:
        match = re.match(r"^/?(\d)\)", line)
        if match:
            num = int(match.group(1))
            current = num if num in sections else None
            if current is not None:
                sections[current].append(line.lstrip("/"))
            continue
        if current in sections:
            sections[current].append(line)

    return sections


class RestaurantLinesApp:
    def __init__(self, master, base_dir):
        self.master = master
        self.base_dir = base_dir
        self.master.title("Navsteva Restaurace")
        self.normal_line_font = ("Helvetica", 22)
        self.focus_line_font = ("Helvetica", 44, "bold")
        self.read_focus_active = False
        self.read_focus_after_id = None
        self.directions_active = False
        self.directions_after_ids = []
        self._directions_saved_speaker = None

        screen_w = master.winfo_screenwidth()
        screen_h = master.winfo_screenheight()
        window_w = min(1100, screen_w - 80)
        window_h = min(700, screen_h - 120)
        self.master.geometry(f"{window_w}x{window_h}")

        self.sections = load_text_sections(
            os.path.join(base_dir, "NavstevaRestaurace.txt")
        )
        self.current_section = 1
        self.current_index = 0
        self.current_line = ""
        self.displayed_lines = []
        self.section_images = {}
        self.current_section_photo = None
        self.section_image_paths = {}
        self.speaker_images = {}
        self.speaker_image_paths = {}
        self.current_speaker_photo = None
        self.current_speaker_name = None

        self.top_frame = tk.Frame(master, bg="white")
        self.top_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.section_label = tk.Label(
            self.top_frame, text="Section 1", font=("Helvetica", 18, "bold"), bg="white"
        )
        self.section_label.pack(anchor="w")

        self.content_pane = tk.PanedWindow(
            master, orient="horizontal", sashwidth=8, sashrelief="raised", bg="white", bd=0
        )
        self.content_pane.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.text_frame = tk.Frame(self.content_pane, bg="white")
        self.image_frame = tk.Frame(self.content_pane, bg="white")
        self.content_pane.add(self.text_frame, minsize=420)
        self.content_pane.add(self.image_frame, minsize=220)

        self.line_label = tk.Label(
            self.text_frame,
            text="",
            font=self.normal_line_font,
            bg="white",
            justify="left",
            anchor="nw",
            wraplength=int(window_w * 0.6),
        )
        self.line_label.pack(fill="both", expand=True)

        self.speaker_panel = tk.Frame(self.text_frame, bg="white")
        self.speaker_panel.pack(fill="x", side="bottom", pady=(6, 0))
        self.speaker_image_label = tk.Label(self.speaker_panel, bg="white")
        self.speaker_image_label.pack(side="left", anchor="sw")
        self.speaker_name_label = tk.Label(
            self.speaker_panel,
            text="",
            font=("Helvetica", 16, "bold"),
            bg="white",
            fg="#333333",
            anchor="w",
            justify="left",
        )
        self.speaker_name_label.pack(side="left", padx=(10, 0), anchor="sw")
        self._hide_speaker_portrait()

        # Překryv pro krátkou animaci směrových pokynů přes levou část obrazovky.
        self.directions_overlay = tk.Frame(self.text_frame, bg="white")
        self.directions_arrow_label = tk.Label(
            self.directions_overlay,
            text="",
            font=("Helvetica", 120, "bold"),
            bg="white",
            fg="#1f3a93",
        )
        self.directions_arrow_label.pack(expand=True, pady=(30, 10))
        self.directions_text_label = tk.Label(
            self.directions_overlay,
            text="",
            font=("Helvetica", 40, "bold"),
            bg="white",
            fg="#000000",
            justify="center",
            wraplength=int(window_w * 0.5),
        )
        self.directions_text_label.pack(pady=(0, 40))

        self.section_image_label = tk.Label(
            self.image_frame,
            text="",
            bg="white",
            anchor="se",
            justify="right",
        )
        self.section_image_label.pack(fill="both", expand=True)

        self.buttons_frame = tk.Frame(master, bg="white")
        self.buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.section_buttons = []
        for i in range(1, 8):
            btn = tk.Button(
                self.buttons_frame,
                text=str(i),
                font=("Helvetica", 16, "bold"),
                width=3,
                command=lambda n=i: self.set_section(n),
            )
            btn.pack(side="left", padx=4)
            self.section_buttons.append(btn)

        self.next_button = tk.Button(
            self.buttons_frame,
            text="NEXT",
            font=("Helvetica", 16, "bold"),
            command=self.next_line,
        )
        self.next_button.pack(side="right")

        self.read_button = tk.Button(
            self.buttons_frame,
            text="READ",
            font=("Helvetica", 16, "bold"),
            command=self.read_line,
        )
        self.read_button.pack(side="right", padx=(0, 10))

        self.directions_button = tk.Button(
            self.buttons_frame,
            text="Directions",
            font=("Helvetica", 16, "bold"),
            command=self.play_directions_demo,
        )
        self.directions_button.pack(side="right", padx=(0, 10))

        self.master.configure(bg="white")
        self.master.bind("<Configure>", self.on_resize)

        self._load_section_images()
        self._load_speaker_images()

        self.set_section(1)

    def _find_section_image_path(self, section: int):
        candidates = [
            f"RestKPTL{section}.png",
            f"RestKPTL{section}.jpg",
            f"RestKPTL{section}.jpeg",
            f"RestKPTL{section}.gif",
            f"RestKPTL{section}.ppm",
            f"RestKPTL{section}.pgm",
        ]
        for filename in candidates:
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                return path
        return None

    def _load_section_images(self):
        for section in range(1, 8):
            path = self._find_section_image_path(section)
            self.section_image_paths[section] = path
            if not path:
                self.section_images[section] = None
                continue
            try:
                # PNG/GIF/PPM/PGM přes Tk; JPG/JPEG necháme rendrovat dynamicky přes Pillow.
                ext = os.path.splitext(path)[1].lower()
                if ext in (".jpg", ".jpeg"):
                    self.section_images[section] = path
                else:
                    self.section_images[section] = tk.PhotoImage(file=path)
            except Exception as exc:
                print(f"Cannot load image for section {section}: {path} ({exc})")
                self.section_images[section] = None

    def _find_person_image_path(self, speaker_name: str):
        # Tolerantní hledání podle jména postavy (case-insensitive) a více přípon.
        aliases = [speaker_name, speaker_name.lower(), speaker_name.capitalize()]
        for alias in aliases:
            for ext in (".png", ".jpg", ".jpeg", ".gif"):
                path = os.path.join(self.base_dir, alias + ext)
                if os.path.exists(path):
                    return path
        # fallback přes procházení adresáře (kdyby se lišil case)
        try:
            for fname in os.listdir(self.base_dir):
                low = fname.lower()
                stem, ext = os.path.splitext(low)
                if ext in (".png", ".jpg", ".jpeg", ".gif") and stem == speaker_name.lower():
                    return os.path.join(self.base_dir, fname)
        except Exception:
            pass
        return None

    def _load_image_any_format(self, path: str, max_size=(180, 180)):
        # 1) Tk PhotoImage (png/gif/ppm/pgm), 2) Pillow fallback (jpg/png/...)
        try:
            img = tk.PhotoImage(file=path)
            src_w, src_h = img.width(), img.height()
            if src_w > 0 and src_h > 0:
                scale = max(src_w / max_size[0], src_h / max_size[1], 1.0)
                subsample = max(1, int(scale + 0.999))
                if subsample > 1:
                    img = img.subsample(subsample, subsample)
            return img
        except Exception:
            pass

        if Image is not None and ImageTk is not None:
            try:
                pil = Image.open(path)
                pil.thumbnail(max_size)
                return ImageTk.PhotoImage(pil)
            except Exception:
                pass
        return None

    def _load_speaker_images(self):
        for speaker in VOICE_CANDIDATES_BY_SPEAKER.keys():
            path = self._find_person_image_path(speaker)
            self.speaker_image_paths[speaker] = path
            if not path:
                self.speaker_images[speaker] = None
                continue
            # Přednačteme malé preview; finální velikost se dopočítá dynamicky při zobrazení.
            self.speaker_images[speaker] = self._load_image_any_format(path, max_size=(220, 220))

    def _hide_speaker_portrait(self):
        self.current_speaker_name = None
        self.current_speaker_photo = None
        self.speaker_image_label.config(image="", text="")
        self.speaker_name_label.config(text="")

    def _render_speaker_portrait(self, speaker):
        if not speaker:
            self._hide_speaker_portrait()
            return
        path = self.speaker_image_paths.get(speaker)
        if not path:
            self._hide_speaker_portrait()
            return

        text_w = self.text_frame.winfo_width() or 480
        pane_h = self.content_pane.winfo_height() or self.master.winfo_height() or 700
        # Maximalizuj portrét pod textem vlevo, ale nech místo na jméno a řádky dialogu.
        max_w = max(180, min(520, int(text_w * 0.50)))
        max_h = max(180, min(360, int(pane_h * 0.38)))
        img = self._load_image_any_format(path, max_size=(max_w, max_h))
        if img is None:
            self._hide_speaker_portrait()
            return
        self.current_speaker_photo = img
        self.current_speaker_name = speaker
        self.speaker_image_label.config(image=img)
        self.speaker_name_label.config(text=speaker)

    def _show_speaker_portrait(self, speaker):
        if not speaker:
            self._hide_speaker_portrait()
            return
        self._render_speaker_portrait(speaker)

    def on_resize(self, event):
        if event.width > 200:
            text_width = max(self.text_frame.winfo_width() - 20, 220)
            self.line_label.config(wraplength=text_width)
            self.directions_text_label.config(wraplength=max(text_width - 20, 220))
            try:
                # Při resize nepřesouvej sash znovu (může vyvolat smyčku Configure událostí).
                self._render_section_image(adjust_sash=False)
            except Exception:
                pass
            if self.current_speaker_name:
                try:
                    self._render_speaker_portrait(self.current_speaker_name)
                except Exception:
                    pass

    def set_section(self, section: int):
        if self.directions_active:
            return
        self._cancel_read_focus_effect()
        self._hide_speaker_portrait()
        self.current_section = section
        self.current_index = 0
        self.displayed_lines = []
        self.section_label.config(text=f"Section {section}")
        self.directions_button.config(state=("normal" if section == 1 else "disabled"))
        self.show_current_line()

    def show_current_line(self):
        lines = self.sections.get(self.current_section, [])
        if not lines:
            self.current_line = ""
            self.line_label.config(text="(No lines in this section)")
            self._render_section_image()
            return

        if self.current_index < 0:
            self.current_index = 0
        if self.current_index >= len(lines):
            self.current_index = len(lines) - 1

        self.current_line = lines[self.current_index]
        if not self.displayed_lines:
            self.displayed_lines = [self.current_line]
        else:
            if self.displayed_lines[-1] != self.current_line:
                self.displayed_lines.append(self.current_line)
        if not self.read_focus_active:
            self.line_label.config(font=self.normal_line_font, fg="black")
        self.line_label.config(text="\n".join(self.displayed_lines))
        self._render_section_image()

    def _render_section_image(self, adjust_sash=True):
        source = self.section_images.get(self.current_section)
        if source is None:
            self.current_section_photo = None
            self.section_image_label.config(image="", text="(No image)")
            return

        pane_w = max(self.content_pane.winfo_width(), self.master.winfo_width())
        if adjust_sash and pane_w > 200:
            try:
                # Pravý panel drž přibližně jako pravou polovinu obrazovky.
                self.content_pane.sash_place(0, int(pane_w * 0.5), 0)
            except tk.TclError:
                pass

        frame_w = self.image_frame.winfo_width() or 280
        frame_h = self.image_frame.winfo_height() or 280
        target_w = max(160, int(frame_w - 8))
        target_h = max(160, int(frame_h - 8))

        if isinstance(source, str):
            rendered = self._load_image_any_format(source, max_size=(target_w, target_h))
            if rendered is None:
                self.current_section_photo = None
                self.section_image_label.config(image="", text="(No image)")
                return
        else:
            src_w = source.width()
            src_h = source.height()
            scale = max(src_w / target_w, src_h / target_h, 1.0)
            subsample = max(1, int(scale + 0.999))
            rendered = source.subsample(subsample, subsample)

        self.current_section_photo = rendered
        self.section_image_label.config(image=rendered, text="")

    def next_line(self):
        if self.directions_active:
            return
        lines = self.sections.get(self.current_section, [])
        if not lines:
            return
        self._cancel_read_focus_effect()
        self._hide_speaker_portrait()
        if self.current_index < len(lines) - 1:
            self.current_index += 1
            self.show_current_line()

    def _cancel_read_focus_effect(self):
        if self.read_focus_after_id is not None:
            try:
                self.master.after_cancel(self.read_focus_after_id)
            except Exception:
                pass
            self.read_focus_after_id = None
        self.read_focus_active = False
        self.line_label.config(font=self.normal_line_font, fg="black")

    def _start_read_focus_effect(self):
        self._cancel_read_focus_effect()
        if not self.current_line:
            return
        self.read_focus_active = True
        self.line_label.config(text=self.current_line, font=self.focus_line_font, fg="black")
        self.read_focus_after_id = self.master.after(10000, self._end_read_focus_effect)

    def _end_read_focus_effect(self):
        self.read_focus_after_id = None
        self.read_focus_active = False
        self.show_current_line()

    def read_line(self):
        if self.directions_active:
            return
        if not self.current_line:
            return
        self._start_read_focus_effect()
        speaker, spoken = extract_speaker_and_spoken_text(self.current_line)
        self._show_speaker_portrait(speaker)
        if spoken:
            preferred_voices = VOICE_CANDIDATES_BY_SPEAKER.get(speaker, ["Samantha"])
            speak_english(spoken, voice=_choose_voice(preferred_voices))

    def _set_main_controls_state(self, state: str):
        for btn in self.section_buttons:
            btn.config(state=state)
        self.next_button.config(state=state)
        self.read_button.config(state=state)
        self.directions_button.config(state=state)

    def _clear_directions_timers(self):
        for after_id in self.directions_after_ids:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
        self.directions_after_ids.clear()

    def play_directions_demo(self):
        if self.directions_active or self.current_section != 1:
            return

        self._cancel_read_focus_effect()
        self.directions_active = True
        self._clear_directions_timers()
        self._directions_saved_speaker = self.current_speaker_name
        self._hide_speaker_portrait()
        self._set_main_controls_state("disabled")

        self.directions_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.directions_overlay.lift()

        steps = [
            ("↑", "go straight"),
            ("←", "turn left"),
            ("→", "turn right"),
        ] * 2

        def show_step(index: int):
            if index >= len(steps):
                self._finish_directions_demo()
                return
            arrow, text = steps[index]
            self.directions_arrow_label.config(text=arrow)
            self.directions_text_label.config(text=text)
            speak_english(text, voice="Samantha")

            self.directions_after_ids.append(
                self.master.after(1700, lambda: clear_step(index))
            )

        def clear_step(index: int):
            self.directions_arrow_label.config(text="")
            self.directions_text_label.config(text="")
            self.directions_after_ids.append(
                self.master.after(500, lambda: show_step(index + 1))
            )

        show_step(0)

    def _finish_directions_demo(self):
        self._clear_directions_timers()
        self.directions_overlay.place_forget()
        self.directions_arrow_label.config(text="")
        self.directions_text_label.config(text="")
        self.directions_active = False
        self._set_main_controls_state("normal")
        if self.current_section != 1:
            self.directions_button.config(state="disabled")

        self.show_current_line()
        if self._directions_saved_speaker:
            try:
                self._show_speaker_portrait(self._directions_saved_speaker)
            except Exception:
                pass
        self._directions_saved_speaker = None


if __name__ == "__main__":
    root = tk.Tk()
    try:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        data_dir = base_dir
        txt_path = os.path.join(data_dir, "NavstevaRestaurace.txt")
        if not os.path.exists(txt_path):
            data_dir = os.path.join(base_dir, "RestauracePTKL")

        app = RestaurantLinesApp(root, data_dir)
    except FileNotFoundError as exc:
        messagebox.showerror("Missing file", str(exc))
        root.destroy()
    except Exception as exc:
        messagebox.showerror("Runtime error", f"{exc}\n\n{traceback.format_exc()}")
        root.destroy()
    else:
        root.mainloop()
