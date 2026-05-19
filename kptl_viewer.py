import tkinter as tk
import subprocess
from pathlib import Path
import csv
import random

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "KPTL_Introduction.txt"
VOCAB_FILE = SCRIPT_DIR / "SlovnikKPLT.csv"
IMAGE_FILES = {
    "Kate": SCRIPT_DIR / "Kate.png",
    "Peter": SCRIPT_DIR / "Peter.png",
    "Tom": SCRIPT_DIR / "Tom.png",
    "Lucy": SCRIPT_DIR / "Lucy.png",
}
JANE_LEO_IMAGE = SCRIPT_DIR / "JaneLeo.png"
LUCY_HOUSE_IMAGE = SCRIPT_DIR / "LucyHouse.PNG"
LUCY_MOLLY_IMAGE = SCRIPT_DIR / "LucyMolly.png"
KATE_GEORGE_IMAGE = SCRIPT_DIR / "GeorgeUniversity.PNG"
KATE_BIKE_IMAGE = SCRIPT_DIR / "KateBike.PNG"
PETER_MOTHER_IMAGE = SCRIPT_DIR / "PeterMother.PNG"
PETER_STARS_IMAGE = SCRIPT_DIR / "PeterStars.PNG"
TOM_AMELIA_IMAGE = SCRIPT_DIR / "TomAmelia.PNG"
TOM_CAT_IMAGE = SCRIPT_DIR / "TomCat.PNG"


def speak_english(text: str):
    try:
        subprocess.Popen(["say", "-v", "Samantha", text])
    except Exception:
        pass


def parse_introductions(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_name = None
    current_lines: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                if current_name and current_lines:
                    sections[current_name] = current_lines[:]
                current_name = None
                current_lines = []
                continue

            if current_name is None:
                current_name = line
                current_lines = []
            else:
                current_lines.append(line)

    if current_name and current_lines:
        sections[current_name] = current_lines

    return sections


def load_vocab(path: Path) -> dict[str, list[tuple[str, str, str]]]:
    vocab: dict[str, list[tuple[str, str, str]]] = {}
    if not path.exists():
        return vocab
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header_skipped = False
        for row in reader:
            if not row:
                continue
            if not header_skipped and row[0].strip().lower() == "person":
                header_skipped = True
                continue
            if len(row) < 4:
                continue
            person = row[0].strip()
            en = row[1].strip()
            pron = row[2].strip()
            cz = row[3].strip()
            vocab.setdefault(person, []).append((en, pron, cz))
    return vocab


def load_photo(path: Path, max_w: int = 420, max_h: int = 520) -> tk.PhotoImage | None:
    if not path.exists():
        return None
    try:
        img = tk.PhotoImage(file=str(path))
    except Exception:
        img = None

    if img is None:
        try:
            from PIL import Image, ImageTk
        except Exception:
            return None
        try:
            pil_img = Image.open(path)
        except Exception:
            return None
        w, h = pil_img.size
        scale = max(w / max_w, h / max_h, 1)
        if scale > 1:
            pil_img = pil_img.resize(
                (int(w / scale), int(h / scale)),
                Image.LANCZOS,
            )
        return ImageTk.PhotoImage(pil_img)

    w = img.width()
    h = img.height()
    scale = max(w / max_w, h / max_h, 1)
    scale_int = int(scale)
    if scale_int > 1:
        img = img.subsample(scale_int, scale_int)
    return img


def load_photo_fill(path: Path, target_w: int, target_h: int) -> tk.PhotoImage | None:
    if not path.exists():
        return None
    try:
        from PIL import Image, ImageTk
    except Exception:
        Image = None
        ImageTk = None

    if Image is not None and ImageTk is not None:
        try:
            pil_img = Image.open(path)
        except Exception:
            return None
        pil_img = pil_img.resize((target_w, target_h), Image.LANCZOS)
        return ImageTk.PhotoImage(pil_img)

    try:
        img = tk.PhotoImage(file=str(path))
    except Exception:
        return None

    w = img.width()
    h = img.height()
    if w == 0 or h == 0:
        return img
    zoom = max(int((target_w + w - 1) / w), int((target_h + h - 1) / h), 1)
    if zoom > 1:
        img = img.zoom(zoom, zoom)
    w = img.width()
    h = img.height()
    subsample = max(int((w + target_w - 1) / target_w), int((h + target_h - 1) / target_h), 1)
    if subsample > 1:
        img = img.subsample(subsample, subsample)
    return img


class KPTLApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KPTL Introduction")
        self.root.geometry("1100x250")

        self.data = parse_introductions(DATA_FILE)
        self.vocab = load_vocab(VOCAB_FILE)
        self.current_name: str | None = None
        self.current_index = 0
        self.vocab_mode = 0
        self.current_vocab: tuple[str, str, str] | None = None
        self.vocab_active = False
        self.saved_text = ""

        self.images: dict[str, tk.PhotoImage | None] = {
            name: load_photo(path) for name, path in IMAGE_FILES.items()
        }
        self.jane_leo_img = None
        self.jane_leo_size = (0, 0)
        self.right_image_path: Path | None = None
        self.right_image_loaded: Path | None = None
        self.jane_seen = False
        self.leo_seen = False
        self.jane_leo_shown = False

        main = tk.Frame(root)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=0, minsize=70)
        main.grid_columnconfigure(0, weight=1)

        top = tk.Frame(main)
        top.grid(row=0, column=0, sticky="nsew")
        bottom = tk.Frame(main)
        bottom.grid(row=1, column=0, sticky="nsew")

        # Top: image (left) + text + Jane/Leo (right)
        image_frame = tk.Frame(top, bg="white")
        image_frame.pack(side="left", padx=10, pady=10)
        self.image_label = tk.Label(image_frame, bg="white")
        self.image_label.pack(fill="both", expand=True)

        right_frame = tk.Frame(top)
        right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=2)
        right_frame.grid_columnconfigure(0, weight=1)

        text_frame = tk.Frame(right_frame)
        text_frame.grid(row=0, column=0, sticky="nsew")
        self.text_label = tk.Label(
            text_frame,
            text="",
            font=("Helvetica", 24),
            justify="left",
            wraplength=520,
            anchor="nw",
            padx=0,
            pady=25,
        )
        self.text_label.pack(fill="both", expand=True, padx=20, pady=10)

        # Jane/Leo image under the text
        self.jane_leo_frame = tk.Frame(right_frame)
        self.jane_leo_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.jane_leo_label = tk.Label(self.jane_leo_frame)
        self.jane_leo_label.pack(fill="both", expand=True)
        self.jane_leo_frame.bind("<Configure>", self.on_jane_leo_resize)

        # Bottom: buttons
        btn_left = tk.Frame(bottom)
        btn_left.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        for name in ["Tom", "Kate", "Peter", "Lucy"]:
            tk.Button(
                btn_left,
                text=name,
                font=("Helvetica", 18, "bold"),
                command=lambda n=name: self.select_person(n),
                width=10,
            ).pack(side="left", padx=8)

        tk.Button(
            btn_left,
            text="Next",
            font=("Helvetica", 18, "bold"),
            command=self.next_line,
            width=10,
        ).pack(side="right", padx=8)
        tk.Button(
            btn_left,
            text="VOC",
            font=("Helvetica", 18, "bold"),
            command=self.vocab_click,
            width=10,
        ).pack(side="right", padx=8)

    def select_person(self, name: str):
        self.current_name = name
        self.current_index = 0
        self.text_label.config(text="")
        self.vocab_mode = 0
        self.current_vocab = None
        self.vocab_active = False
        self.saved_text = ""
        self.jane_seen = False
        self.leo_seen = False
        self.jane_leo_shown = False
        self.jane_leo_size = (0, 0)
        self.right_image_path = None
        self.right_image_loaded = None
        self.jane_leo_label.config(image="", text="")

        img = self.images.get(name)
        if img is None:
            self.image_label.config(text=name, image="", font=("Helvetica", 24, "bold"))
        else:
            self.image_label.config(image=img, text="")
            self.image_label.image = img

    def next_line(self):
        if not self.current_name:
            return

        lines = self.data.get(self.current_name, [])
        if self.current_index >= len(lines):
            return

        if self.vocab_active:
            self.text_label.config(text=self.saved_text)
            self.vocab_active = False

        line = lines[self.current_index]
        current = self.text_label.cget("text")
        new_text = line if not current else f"{current}\n{line}"
        self.text_label.config(text=new_text)
        speak_english(line)
        self.current_index += 1

        if self.current_name == "Lucy":
            if "Jane" in line:
                self.jane_seen = True
            if "Leo" in line:
                self.leo_seen = True
            if self.jane_seen and self.leo_seen:
                self.show_right_image(JANE_LEO_IMAGE)
            if line == "Lucy lives in a big house with a big garden and a swimming pool.":
                self.show_right_image(LUCY_HOUSE_IMAGE)
            if line == "She loves her dog Molly.":
                self.show_right_image(LUCY_MOLLY_IMAGE)
            if line == "She likes her best friend Kate.":
                self.show_right_image(JANE_LEO_IMAGE)
        elif self.current_name == "Kate":
            if line == "Her older brother is George. He studies at university.":
                self.show_right_image(KATE_GEORGE_IMAGE)
            if "riding a bike" in line:
                self.show_right_image(KATE_BIKE_IMAGE)
        elif self.current_name == "Peter":
            if line == "His mother works at the post office.":
                self.show_right_image(PETER_MOTHER_IMAGE)
            if line == "Peter likes astronomy, maths, and technology.":
                self.show_right_image(PETER_STARS_IMAGE)
        elif self.current_name == "Tom":
            if line == "He has a younger sister. Her name is Amélia. She is 4 years old.":
                self.show_right_image(TOM_AMELIA_IMAGE)
            if line == "Tom lives in a small house. They have a British cat. Her name is Coco.":
                self.show_right_image(TOM_CAT_IMAGE)

    def vocab_click(self):
        if not self.current_name:
            return
        words = self.vocab.get(self.current_name, [])
        if not words:
            self.text_label.config(text="No vocabulary.")
            return

        if not self.vocab_active:
            self.saved_text = self.text_label.cget("text")
            self.vocab_active = True

        if self.vocab_mode == 0 or self.current_vocab is None:
            self.current_vocab = random.choice(words)
            en, _pron, _cz = self.current_vocab
            self.text_label.config(text=en)
            speak_english(en)
            self.vocab_mode = 1
        else:
            en, pron, cz = self.current_vocab
            self.text_label.config(text=f"{en}    {pron}    {cz}")
            self.vocab_mode = 0

    def on_jane_leo_resize(self, event: tk.Event):
        if not self.jane_leo_shown:
            return
        self.update_jane_leo_image(event.width, event.height)

    def update_jane_leo_image(self, width: int, height: int):
        if width <= 1 or height <= 1:
            return
        if (width, height) == self.jane_leo_size and self.right_image_loaded == self.right_image_path:
            return
        if self.right_image_path is None:
            self.jane_leo_label.config(image="", text="")
            return
        img = load_photo_fill(self.right_image_path, target_w=width, target_h=height)
        if img is None:
            self.jane_leo_label.config(text="Jane & Leo", font=("Helvetica", 14, "bold"))
            return
        self.jane_leo_label.config(image=img, text="")
        self.jane_leo_label.image = img
        self.jane_leo_size = (width, height)
        self.right_image_loaded = self.right_image_path

    def show_right_image(self, path: Path):
        self.right_image_path = path
        self.jane_leo_shown = True
        width = self.jane_leo_frame.winfo_width()
        height = self.jane_leo_frame.winfo_height()
        self.update_jane_leo_image(width, height)


def main():
    root = tk.Tk()
    app = KPTLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
