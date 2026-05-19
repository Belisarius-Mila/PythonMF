#!/usr/bin/env python3
"""Small Tkinter GUI for generating Czech MP3 speech with edge-tts."""

from __future__ import annotations

import asyncio
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import edge_tts
except ImportError:  # pragma: no cover - depends on local environment
    edge_tts = None


DEFAULT_OUT = Path("assets") / "audio" / "cs"
DEFAULT_VOICE = "cs-CZ-AntoninNeural"
DEFAULT_RATE = "-10%"
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def normalize_filename(name: str) -> str:
    filename = name.strip()
    if filename.lower().endswith(".mp3"):
        filename = filename[:-4]
    return filename.strip()


def validate_filename(name: str) -> str:
    filename = normalize_filename(name)
    if not filename:
        raise ValueError("Zadejte název souboru.")
    if filename in {".", ".."} or INVALID_FILENAME_CHARS.search(filename):
        raise ValueError(
            'Název souboru nesmí obsahovat znaky: < > : " / \\ | ? *'
        )
    return filename


async def save_tts(text: str, output_path: Path, voice: str) -> None:
    if edge_tts is None:
        raise RuntimeError(
            "Chybí knihovna edge-tts. Nainstalujte ji příkazem: python -m pip install edge-tts"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=DEFAULT_RATE)
    await communicate.save(str(output_path))


class TtsApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=16)
        self.root = root
        self.worker: threading.Thread | None = None

        self.text = tk.Text(self, height=8, width=70, wrap="word")
        self.filename_var = tk.StringVar(value="novy_text")
        self.out_dir_var = tk.StringVar(value=str(DEFAULT_OUT))
        self.voice_var = tk.StringVar(value=DEFAULT_VOICE)
        self.status_var = tk.StringVar(value="Připraveno.")

        self.generate_button = ttk.Button(
            self,
            text="Namluvit a uložit MP3",
            command=self.start_generation,
        )

        self.build_ui()

    def build_ui(self) -> None:
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Text k namluvení").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.text.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(4, 12))

        ttk.Label(self, text="Název souboru").grid(row=2, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.filename_var).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(12, 0)
        )

        ttk.Label(self, text="Složka pro uložení").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Entry(self, textvariable=self.out_dir_var).grid(
            row=3, column=1, sticky="ew", padx=(12, 8), pady=(10, 0)
        )
        ttk.Button(self, text="Vybrat...", command=self.choose_directory).grid(
            row=3, column=2, sticky="ew", pady=(10, 0)
        )

        ttk.Label(self, text="Hlas").grid(row=4, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(self, textvariable=self.voice_var).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=(12, 0), pady=(10, 0)
        )

        self.generate_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=16)
        ttk.Label(self, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=3, sticky="w"
        )

    def choose_directory(self) -> None:
        selected = filedialog.askdirectory(
            title="Vyberte složku pro MP3",
            initialdir=self.out_dir_var.get() or str(DEFAULT_OUT),
        )
        if selected:
            self.out_dir_var.set(selected)

    def start_generation(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return

        try:
            text = self.text.get("1.0", "end").strip()
            if not text:
                raise ValueError("Zadejte text k namluvení.")

            filename = validate_filename(self.filename_var.get())
            out_dir = Path(self.out_dir_var.get()).expanduser()
            voice = self.voice_var.get().strip() or DEFAULT_VOICE
            output_path = out_dir / f"{filename}.mp3"
        except ValueError as exc:
            messagebox.showerror("Chyba", str(exc))
            return

        if output_path.exists() and not messagebox.askyesno(
            "Soubor už existuje",
            f"Soubor už existuje:\n{output_path}\n\nChcete ho přepsat?",
        ):
            self.status_var.set("Uložení zrušeno.")
            return

        self.generate_button.configure(state="disabled")
        self.status_var.set("Generuji MP3...")

        self.worker = threading.Thread(
            target=self.run_generation,
            args=(text, output_path, voice),
            daemon=True,
        )
        self.worker.start()

    def run_generation(self, text: str, output_path: Path, voice: str) -> None:
        try:
            asyncio.run(save_tts(text, output_path, voice))
        except Exception as exc:
            self.root.after(0, self.finish_with_error, str(exc))
            return

        self.root.after(0, self.finish_success, output_path)

    def finish_success(self, output_path: Path) -> None:
        self.generate_button.configure(state="normal")
        self.status_var.set(f"Hotovo: {output_path}")
        messagebox.showinfo("Hotovo", f"MP3 bylo uloženo:\n{output_path}")

    def finish_with_error(self, error: str) -> None:
        self.generate_button.configure(state="normal")
        self.status_var.set("Generování selhalo.")
        messagebox.showerror("Chyba", error)


def main() -> None:
    root = tk.Tk()
    root.title("České TTS do MP3")
    root.minsize(620, 420)
    TtsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
