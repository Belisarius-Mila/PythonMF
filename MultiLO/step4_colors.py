"""Step 4: Colors module (C1-lite) for 'Základní barvy'."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import tkinter as tk

from PIL import Image, ImageDraw, ImageOps, ImageTk

from data_layer import DataBundle, load_data
from multilo_core import (
    COLORS_OKRUH as OKRUH,
    ColorCardItem as ColorCard,
    LANG_COL_MAP,
    build_assets as _build_assets,
    build_color_cards as _build_cards,
)
from nav_utils import replace_process
from tts_utils import SingleFlightTTS


try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    print("Missing dependency: customtkinter")
    print("Install with: python3 -m pip install customtkinter")
    raise SystemExit(1) from exc


APP_TITLE = "MultiLO - Barvy"
IMAGE_SIZE = (400, 400)
ASSETS_DIR = Path(__file__).resolve().parent / "Foto_normalized" / "Colors"
COCKPIT_PATH = Path(__file__).resolve().parent / "step2_cockpit.py"
COLOR_HEX_BY_CZ = {
    "Červená": "#ef4444",
    "Modrá": "#3b82f6",
    "Žlutá": "#facc15",
    "Zelená": "#22c55e",
    "Oranžová": "#f97316",
    "Fialová": "#8b5cf6",
    "Růžová": "#ec4899",
    "Hnědá": "#92400e",
    "Černá": "#111827",
    "Bílá": "#f9fafb",
    "Šedá": "#9ca3af",
}
def _placeholder_image(text: str) -> Image.Image:
    img = Image.new("RGB", IMAGE_SIZE, (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 392, 392), outline=(160, 160, 160), width=2)
    draw.text((18, 170), "Color image missing", fill=(80, 80, 80))
    draw.text((18, 206), text[:40], fill=(80, 80, 80))
    return img


class ColorsApp(ctk.CTk):
    def __init__(
        self,
        bundle: DataBundle,
        initial_user_id: str | None = None,
        initial_lang: str | None = None,
    ) -> None:
        super().__init__()
        self.bundle = bundle
        self.assets = _build_assets(ASSETS_DIR)
        self.cards: list[ColorCard] = []
        self.order: list[int] = []
        self.index = 0
        self.revealed = False
        self.current_photo: ImageTk.PhotoImage | None = None
        self.tts = SingleFlightTTS()
        self.autoplay_job: str | None = None
        self.autoplay_on = False

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.title(APP_TITLE)
        self.geometry("920x740")
        self.minsize(880, 680)

        self.user_var = ctk.StringVar(value=self._default_user())
        self.lang_var = ctk.StringVar(value="IT")
        self._apply_initial(initial_user_id, initial_lang)

        self._build_ui()
        self.bind("<space>", self._on_space)
        self.bind("<Right>", self._on_right)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_session()
        self.after(120, self._bring_to_front)

    def _default_user(self) -> str:
        active = [u for u in self.bundle.users if u.active]
        if active:
            u = active[0]
            return f"{u.user_id} - {u.display_name}"
        if self.bundle.users:
            u = self.bundle.users[0]
            return f"{u.user_id} - {u.display_name}"
        return "guest - Guest"

    def _apply_initial(self, user_id: str | None, lang: str | None) -> None:
        if user_id:
            for u in self.bundle.users:
                if u.user_id == user_id:
                    self.user_var.set(f"{u.user_id} - {u.display_name}")
                    break
        if lang in LANG_COL_MAP:
            self.lang_var.set(lang)

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        top.grid_columnconfigure((0, 1, 2), weight=1)

        self._add_selector(top, 0, "Uživatel", self.user_var, [f"{u.user_id} - {u.display_name}" for u in self.bundle.users] or ["guest - Guest"])
        self._add_selector(top, 1, "Jazyk", self.lang_var, list(LANG_COL_MAP), command=self._on_lang_changed)
        ctk.CTkButton(top, text="Start / Restart", command=self._start_session).grid(
            row=1, column=2, padx=8, pady=(4, 10), sticky="ew"
        )

        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.progress_label = ctk.CTkLabel(main, text="Barva 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(12, 6))

        self.image_wrap = tk.Frame(main, bd=0, highlightthickness=0, bg="#2b2b2b")
        self.image_wrap.pack(pady=(4, 8))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#2b2b2b")
        self.image_label.pack(pady=(4, 8))

        self.cz_label = ctk.CTkLabel(main, text="CZ: -", font=ctk.CTkFont(size=20, weight="bold"))
        self.cz_label.pack(pady=(2, 4))

        self.color_band = ctk.CTkFrame(main, width=420, height=36, corner_radius=8, fg_color="#d1d5db")
        self.color_band.pack(pady=(4, 6))

        self.target_label = ctk.CTkLabel(main, text="?", font=ctk.CTkFont(size=26))
        self.target_label.pack(pady=(2, 10))

        bottom = ctk.CTkFrame(self, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(bottom, text="Zobrazit název", command=self._reveal).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Přehrát výslovnost", command=self._speak_current).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Další", command=self._next_card).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Zamíchat znovu", command=self._reshuffle).pack(side="left", padx=8, pady=10)
        self.auto_btn = ctk.CTkButton(bottom, text="Auto ON", command=self._toggle_autoplay)
        self.auto_btn.pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Zpět do kokpitu", command=self._back_to_cockpit).pack(
            side="right", padx=8, pady=10
        )
        self.status_label = ctk.CTkLabel(bottom, text="Připraveno.")
        self.status_label.pack(side="right", padx=8, pady=10)

    def _add_selector(
        self,
        parent: ctk.CTkFrame,
        col: int,
        label: str,
        variable: ctk.StringVar,
        values: list[str],
        command=None,
    ) -> None:
        wrap = ctk.CTkFrame(parent, corner_radius=8)
        wrap.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(wrap, text=label).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkOptionMenu(wrap, variable=variable, values=values, command=command).pack(
            fill="x", padx=8, pady=(0, 8)
        )

    def _start_session(self) -> None:
        self._stop_autoplay()
        self.cards = _build_cards(self.bundle, self.lang_var.get(), self.assets)
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self._render()
        self.status_label.configure(
            text=(
                f"Sezení start: {OKRUH} / {self.lang_var.get()} "
                f"(TTS: {self.tts.backend})"
            )
        )

    def _reshuffle(self) -> None:
        if not self.cards:
            return
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self._render()
        self.status_label.configure(text="Barvy znovu zamíchány.")

    def _current_card(self) -> ColorCard | None:
        if not self.cards or self.index >= len(self.order):
            return None
        return self.cards[self.order[self.index]]

    def _build_display_image(self, card: ColorCard) -> Image.Image:
        if card.image_path and card.image_path.exists():
            with Image.open(card.image_path) as raw:
                img = raw.convert("RGB")
        else:
            img = _placeholder_image(card.en)
        img = ImageOps.contain(img, IMAGE_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", IMAGE_SIZE, (240, 240, 240))
        x = (IMAGE_SIZE[0] - img.size[0]) // 2
        y = (IMAGE_SIZE[1] - img.size[1]) // 2
        canvas.paste(img, (x, y))
        return canvas

    def _safe_set_image(self, photo: ImageTk.PhotoImage | None) -> None:
        if not self.winfo_exists():
            return
        try:
            if photo is None:
                self.image_label.configure(image="")
                self.image_label.image = None
            else:
                self.image_label.configure(image=photo)
                self.image_label.image = photo
        except tk.TclError:
            # If Tk image handle was invalidated, clear the widget image.
            try:
                self.image_label.configure(image="")
                self.image_label.image = None
            except Exception:
                pass

    def _render(self) -> None:
        if not self.winfo_exists():
            return
        card = self._current_card()
        if card is None:
            self.progress_label.configure(text=f"Hotovo ({len(self.cards)} barev)")
            self.cz_label.configure(text="CZ: -")
            self.target_label.configure(text="Kolo dokončeno.")
            self.color_band.configure(fg_color="#d1d5db")
            self._safe_set_image(None)
            self.current_photo = None
            return
        self.progress_label.configure(text=f"Barva {self.index + 1}/{len(self.cards)}")
        self.cz_label.configure(text=f"CZ: {card.cz}")
        self.color_band.configure(fg_color=COLOR_HEX_BY_CZ.get(card.cz, "#d1d5db"))
        self.target_label.configure(text=card.target_text if self.revealed else "?")
        canvas = self._build_display_image(card)
        self.current_photo = ImageTk.PhotoImage(canvas)
        self._safe_set_image(self.current_photo)

    def _reveal(self) -> None:
        if self._current_card() is None:
            return
        self.revealed = True
        self._render()

    def _next_card(self) -> None:
        if self._current_card() is None:
            return
        self.index += 1
        self.revealed = False
        self._render()

    def _on_space(self, _event) -> None:
        if self._current_card() is None:
            return
        if not self.revealed:
            self._reveal()
        else:
            self._next_card()

    def _on_right(self, _event) -> None:
        self._next_card()

    def _speak_current(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.status_label.configure(text="TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text, self.lang_var.get(), rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _on_lang_changed(self, _value) -> None:
        self._start_session()
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang_var.get()}.")

    def _toggle_autoplay(self) -> None:
        if self.autoplay_on:
            self._stop_autoplay()
            self.status_label.configure(text="Auto režim vypnut.")
        else:
            self.autoplay_on = True
            self.auto_btn.configure(text="Auto OFF")
            self.status_label.configure(text="Auto režim zapnut (odhalit + další).")
            self._run_autoplay()

    def _stop_autoplay(self) -> None:
        self.autoplay_on = False
        self.auto_btn.configure(text="Auto ON")
        if self.autoplay_job is not None:
            self.after_cancel(self.autoplay_job)
            self.autoplay_job = None

    def _run_autoplay(self) -> None:
        if not self.winfo_exists():
            return
        if not self.autoplay_on:
            return
        if self._current_card() is None:
            self._stop_autoplay()
            return
        if not self.revealed:
            self._reveal()
            self._speak_current()
            self.autoplay_job = self.after(1300, self._run_autoplay)
            return
        self._next_card()
        self.autoplay_job = self.after(1000, self._run_autoplay)

    def _bring_to_front(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(300, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _back_to_cockpit(self) -> None:
        self._stop_autoplay()
        try:
            replace_process(COCKPIT_PATH)
        except Exception as exc:
            self.status_label.configure(text=f"Návrat do kokpitu selhal: {exc}")
            return

    def _on_close(self) -> None:
        self._stop_autoplay()
        self.destroy()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MultiLO Colors")
    parser.add_argument("--user", dest="user_id", default=None)
    parser.add_argument("--lang", dest="lang", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = load_data(Path(__file__).resolve().parent)
    if not bundle.validation.is_valid:
        print("Data validation failed. Run: python3 step1_validate.py")
        for msg in bundle.validation.errors:
            print(f"  - {msg}")
        return 1
    app = ColorsApp(bundle, initial_user_id=args.user_id, initial_lang=args.lang)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
