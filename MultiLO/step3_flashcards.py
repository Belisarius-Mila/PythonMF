"""Step 3: Flashcards for F/G/H (VegFruit, Animals, Plants)."""

from __future__ import annotations

import argparse
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageOps

from data_layer import DataBundle, load_data
from multilo_core import (
    FLASH_OKRUH_TO_FOLDER as OKRUH_TO_FOLDER,
    FlashcardItem as Flashcard,
    LANG_COL_MAP,
    build_asset_index as _build_asset_index,
    build_flashcards as _build_flashcards,
)
from nav_utils import replace_process
from tts_utils import SingleFlightTTS


try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    print("Missing dependency: customtkinter")
    print("Install with: python3 -m pip install customtkinter")
    raise SystemExit(1) from exc


APP_TITLE = "MultiLO - Flashcards"
IMAGE_SIZE = (400, 400)
ASSETS_ROOT = Path(__file__).resolve().parent / "Foto_normalized"
COCKPIT_PATH = Path(__file__).resolve().parent / "step2_cockpit.py"

def _placeholder_image(text: str) -> Image.Image:
    img = Image.new("RGB", IMAGE_SIZE, (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 392, 392), outline=(160, 160, 160), width=2)
    draw.text((22, 170), "Obrazek neni dostupny", fill=(80, 80, 80))
    draw.text((22, 210), text[:40], fill=(80, 80, 80))
    return img


class FlashcardApp(ctk.CTk):
    def __init__(
        self,
        bundle: DataBundle,
        initial_user_id: str | None = None,
        initial_lang: str | None = None,
        initial_okruh: str | None = None,
    ) -> None:
        super().__init__()
        self.bundle = bundle
        self.cards: list[Flashcard] = []
        self.order: list[int] = []
        self.asset_index = _build_asset_index(ASSETS_ROOT)
        self.index = 0
        self.revealed = False
        self.rated_current = False
        self.known_count = 0
        self.unknown_count = 0
        self.rated_item_ids: set[int] = set()
        self.unknown_item_ids: set[int] = set()
        self.current_photo: ctk.CTkImage | None = None
        self.tts = SingleFlightTTS()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.title(APP_TITLE)
        self.geometry("980x760")
        self.minsize(920, 700)

        self.user_var = ctk.StringVar(value=self._default_user())
        self.lang_var = ctk.StringVar(value="IT")
        self.okruh_var = ctk.StringVar(value=list(OKRUH_TO_FOLDER.keys())[0])

        self._apply_initial_selection(initial_user_id, initial_lang, initial_okruh)

        self._build_ui()
        self.bind("<space>", self._on_space)
        self.bind("<Right>", self._on_right)
        self.bind("<Left>", self._on_left)
        self._start_session()

    def _default_user(self) -> str:
        active = [u for u in self.bundle.users if u.active]
        if active:
            u = active[0]
            return f"{u.user_id} - {u.display_name}"
        if self.bundle.users:
            u = self.bundle.users[0]
            return f"{u.user_id} - {u.display_name}"
        return "guest - Guest"

    def _apply_initial_selection(
        self,
        initial_user_id: str | None,
        initial_lang: str | None,
        initial_okruh: str | None,
    ) -> None:
        if initial_user_id:
            for u in self.bundle.users:
                if u.user_id == initial_user_id:
                    self.user_var.set(f"{u.user_id} - {u.display_name}")
                    break
        if initial_lang in LANG_COL_MAP:
            self.lang_var.set(initial_lang)
        if initial_okruh in OKRUH_TO_FOLDER:
            self.okruh_var.set(initial_okruh)

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._add_selector(top, 0, "Uživatel", self.user_var, [f"{u.user_id} - {u.display_name}" for u in self.bundle.users] or ["guest - Guest"])
        self._add_selector(top, 1, "Jazyk", self.lang_var, list(LANG_COL_MAP))
        self._add_selector(top, 2, "Okruh", self.okruh_var, list(OKRUH_TO_FOLDER))

        ctk.CTkButton(top, text="Start / Restart", command=self._start_session).grid(
            row=1, column=3, padx=8, pady=(4, 10), sticky="ew"
        )

        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.progress_label = ctk.CTkLabel(main, text="Karta 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(12, 6))

        self.image_label = ctk.CTkLabel(main, text="")
        self.image_label.pack(pady=(4, 8))

        self.cz_label = ctk.CTkLabel(main, text="CZ: -", font=ctk.CTkFont(size=22, weight="bold"))
        self.cz_label.pack(pady=(4, 4))

        self.target_label = ctk.CTkLabel(main, text="?", font=ctk.CTkFont(size=24))
        self.target_label.pack(pady=(4, 10))

        bottom = ctk.CTkFrame(self, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(bottom, text="Zobrazit překlad", command=self._reveal).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Přehrát výslovnost", command=self._speak_current).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Znám ✓", command=self._mark_known).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Neznám ✗", command=self._mark_unknown).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Další", command=self._next_card).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Zamíchat znovu", command=self._reshuffle).pack(
            side="left", padx=10, pady=10
        )
        ctk.CTkButton(bottom, text="Zpět do kokpitu", command=self._back_to_cockpit).pack(
            side="left", padx=10, pady=10
        )

        self.status_label = ctk.CTkLabel(bottom, text="Připraveno.")
        self.status_label.pack(side="right", padx=12, pady=10)

    def _add_selector(
        self,
        parent: ctk.CTkFrame,
        col: int,
        label: str,
        variable: ctk.StringVar,
        values: list[str],
    ) -> None:
        wrap = ctk.CTkFrame(parent, corner_radius=8)
        wrap.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(wrap, text=label).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkOptionMenu(wrap, variable=variable, values=values).pack(fill="x", padx=8, pady=(0, 8))

    def _start_session(self) -> None:
        okruh = self.okruh_var.get()
        lang = self.lang_var.get()
        folder = OKRUH_TO_FOLDER[okruh]
        self.cards = _build_flashcards(
            self.bundle,
            lang,
            okruh,
            self.asset_index.get(folder, {}),
        )
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.rated_current = False
        self.known_count = 0
        self.unknown_count = 0
        self.rated_item_ids.clear()
        self.unknown_item_ids.clear()
        self._render()
        self.status_label.configure(text=f"Sezení start: {okruh} / {lang}")

    def _reshuffle(self) -> None:
        if not self.cards:
            return
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.rated_current = False
        self.known_count = 0
        self.unknown_count = 0
        self.rated_item_ids.clear()
        self.unknown_item_ids.clear()
        self._render()
        self.status_label.configure(text="Karty znovu zamíchány.")

    def _current_card(self) -> Flashcard | None:
        if not self.cards or self.index >= len(self.order):
            return None
        return self.cards[self.order[self.index]]

    def _build_display_image(self, card: Flashcard) -> Image.Image:
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

    def _render(self) -> None:
        card = self._current_card()
        if card is None:
            self.progress_label.configure(text=f"Hotovo ({len(self.cards)} karet)")
            self.cz_label.configure(text="CZ: -")
            self.target_label.configure(
                text=(
                    f"Kolo dokončeno. Znám: {self.known_count} | "
                    f"Neznám: {self.unknown_count}"
                )
            )
            self.image_label.configure(image=None, text="")
            self.current_photo = None
            self.status_label.configure(
                text=(
                    f"Shrnutí: znám={self.known_count}, neznám={self.unknown_count}, "
                    f"ohodnoceno={len(self.rated_item_ids)}/{len(self.cards)}"
                )
            )
            return

        self.progress_label.configure(text=f"Karta {self.index + 1}/{len(self.cards)}")
        self.cz_label.configure(text=f"CZ: {card.cz}")
        self.target_label.configure(text=card.target_text if self.revealed else "?")
        canvas = self._build_display_image(card)
        self.current_photo = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=IMAGE_SIZE)
        self.image_label.configure(image=self.current_photo, text="")

    def _reveal(self) -> None:
        if self._current_card() is None:
            return
        self.revealed = True
        self._render()

    def _mark_known(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if card.item_id not in self.rated_item_ids:
            self.rated_item_ids.add(card.item_id)
            self.known_count += 1
        self.rated_current = True
        self._next_card()

    def _mark_unknown(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if card.item_id not in self.rated_item_ids:
            self.rated_item_ids.add(card.item_id)
            self.unknown_count += 1
            self.unknown_item_ids.add(card.item_id)
        self.rated_current = True
        self._next_card()

    def _next_card(self) -> None:
        if self._current_card() is None:
            return
        self.index += 1
        self.revealed = False
        self.rated_current = False
        self._render()

    def _prev_card(self) -> None:
        if not self.cards:
            return
        self.index = max(0, self.index - 1)
        self.revealed = False
        self.rated_current = False
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

    def _on_left(self, _event) -> None:
        self._prev_card()

    def _speak_current(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.status_label.configure(text="TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text, self.lang_var.get(), rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _back_to_cockpit(self) -> None:
        try:
            replace_process(COCKPIT_PATH)
        except Exception as exc:
            self.status_label.configure(text=f"Návrat do kokpitu selhal: {exc}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MultiLO Flashcards")
    parser.add_argument("--user", dest="user_id", default=None)
    parser.add_argument("--lang", dest="lang", default=None)
    parser.add_argument("--okruh", dest="okruh", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = load_data(Path(__file__).resolve().parent)
    if not bundle.validation.is_valid:
        print("Data validation failed. Run: python3 step1_validate.py")
        for msg in bundle.validation.errors:
            print(f"  - {msg}")
        return 1

    app = FlashcardApp(
        bundle,
        initial_user_id=args.user_id,
        initial_lang=args.lang,
        initial_okruh=args.okruh,
    )
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
