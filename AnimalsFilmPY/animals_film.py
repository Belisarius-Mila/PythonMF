import os
import re
import tkinter as tk
from tkinter import messagebox
import subprocess

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - runtime dependency
    Image = None
    ImageTk = None


SCREEN_HEADINGS = [
    "FIRST SCREEN",
    "SECOND SCREEN",
    "THIRD SCREEN",
    "FOURTH SCREEN",
    "FIFTH SCREEN",
    "SIXTH SCREEN",
]

IMAGE_FILES = [
    "A1.png",
    "A2.jpg",
    "A3.png",
    "A4.png",
    "A5.png",
    "A6.png",
]


def speak_english(text: str):
    try:
        subprocess.Popen(["say", "-v", "Samantha", text])
    except Exception:
        pass


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
    text = re.sub(r"([.!?])([A-Za-z])", r"\1 \2", text)
    return text


def split_into_screens(text: str):
    positions = []
    for heading in SCREEN_HEADINGS:
        match = re.search(rf"\b{re.escape(heading)}\b", text)
        if not match:
            raise ValueError(f"Missing heading: {heading}")
        positions.append((match.start(), match.end(), heading))

    positions.sort()
    screens = []
    for idx, (start, end, heading) in enumerate(positions):
        next_start = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        content = text[end:next_start].strip()
        screens.append(content)
    return screens


def split_lines(text: str):
    lines = [line.strip() for line in text.split("\n")]
    return [line for line in lines if line]


class AnimalsFilmApp:
    def __init__(self, master, base_dir):
        self.master = master
        self.base_dir = base_dir
        self.master.title("Our Life with Animals")

        screen_w = master.winfo_screenwidth()
        screen_h = master.winfo_screenheight()
        window_w = min(1200, screen_w - 80)
        window_h = min(720, screen_h - 120)
        self.master.geometry(f"{window_w}x{window_h}")
        self.left_ratio = 0.6

        self.main_frame = tk.Frame(master, bg="white")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.left_frame = tk.Frame(self.main_frame, bg="white")
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.left_frame.config(width=int(window_w * self.left_ratio))
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.main_frame, bg="white")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))
        self.right_frame.config(width=int(window_w * (1 - self.left_ratio)))
        self.right_frame.pack_propagate(False)

        self.image_label = tk.Label(self.left_frame, bg="white")
        self.image_label.pack(fill="both", expand=True)
        self.image_label.bind("<Button-1>", self.on_image_click)

        self.text_title = tk.Label(
            self.right_frame, text="", font=("Helvetica", 22, "bold"), bg="white"
        )
        self.text_title.pack(anchor="w")

        self.text_box = tk.Text(
            self.right_frame,
            wrap="word",
            font=("Helvetica", 22),
            bg="white",
            bd=0,
            highlightthickness=0,
        )
        self.text_box.pack(fill="both", expand=True, pady=(10, 0))
        self.text_box.config(state="disabled")

        self.buttons_frame = tk.Frame(master, bg="white")
        self.buttons_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.back_button = tk.Button(
            self.buttons_frame, text="BACK", font=("Helvetica", 16, "bold"),
            command=self.prev_screen
        )
        self.back_button.pack(side="left")

        self.next_button = tk.Button(
            self.buttons_frame, text="NEXT", font=("Helvetica", 16, "bold"),
            command=self.next_screen
        )
        self.next_button.pack(side="right")

        self.screens = []
        self.sentences = []
        self.current_screen = 0
        self.current_sentence_index = 0
        self.photo = None

        self.load_content()
        self.show_screen(0)

        self.master.bind("<Left>", lambda event: self.prev_screen())
        self.master.bind("<Right>", lambda event: self.next_screen())

    def load_content(self):
        text_path = os.path.join(self.base_dir, "Our Life with Animals KPTL_Program.txt")
        if not os.path.exists(text_path):
            messagebox.showerror("Missing file", f"Text file not found: {text_path}")
            self.master.destroy()
            return

        with open(text_path, "rb") as f:
            raw_bytes = f.read()
        raw = None
        for enc in ("utf-8", "mac_roman", "cp1252", "latin-1"):
            try:
                raw = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if raw is None:
            raw = raw_bytes.decode("latin-1", errors="replace")

        normalized = normalize_text(raw)
        try:
            screens = split_into_screens(normalized)
        except ValueError as exc:
            messagebox.showerror("Format error", str(exc))
            self.master.destroy()
            return

        self.screens = [split_lines(s) for s in screens]

    def set_text(self, text: str):
        self.text_box.config(state="normal")
        self.text_box.delete("1.0", "end")
        if text:
            self.text_box.insert("end", text)
        self.text_box.config(state="disabled")

    def append_text(self, text: str):
        self.text_box.config(state="normal")
        if self.text_box.get("1.0", "end").strip():
            self.text_box.insert("end", "\n")
        self.text_box.insert("end", text)
        self.text_box.config(state="disabled")
        self.text_box.see("end")

    def show_screen(self, index: int):
        self.current_screen = index
        self.current_sentence_index = 0
        self.set_text("")
        self.text_title.config(text=SCREEN_HEADINGS[index].title())

        self.master.update_idletasks()

        image_path = os.path.join(self.base_dir, IMAGE_FILES[index])
        if not os.path.exists(image_path):
            messagebox.showerror("Missing file", f"Image not found: {image_path}")
            return

        if Image is None or ImageTk is None:
            messagebox.showerror(
                "Missing dependency",
                "Pillow is required to display JPG/PNG images. Install with: pip install pillow",
            )
            self.master.destroy()
            return

        max_w = self.left_frame.winfo_width() or 500
        max_h = self.left_frame.winfo_height() or 500
        img = Image.open(image_path)
        img.thumbnail((max_w, max_h))
        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)

        self.update_buttons()

    def update_buttons(self):
        self.back_button.config(state="normal" if self.current_screen > 0 else "disabled")
        self.next_button.config(
            state="normal" if self.current_screen < len(self.screens) - 1 else "disabled"
        )

    def on_image_click(self, event=None):
        sentences = self.screens[self.current_screen]
        if self.current_sentence_index >= len(sentences):
            return
        sentence = sentences[self.current_sentence_index]
        self.current_sentence_index += 1
        self.append_text(sentence)
        speak_english(sentence)

    def next_screen(self):
        if self.current_screen < len(self.screens) - 1:
            self.show_screen(self.current_screen + 1)

    def prev_screen(self):
        if self.current_screen > 0:
            self.show_screen(self.current_screen - 1)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimalsFilmApp(root, os.path.dirname(__file__))
    root.mainloop()
