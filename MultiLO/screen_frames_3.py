"""Internal frame-based screens for MultiLO cockpit navigation."""

from __future__ import annotations

from pathlib import Path
import random
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk

from data_layer import DataBundle
from multilo_core import (
    DAY_ORDER,
    DEFAULT_DAY_COLORS,
    FLASH_OKRUH_TO_FOLDER,
    LANG_COL_MAP,
    MONTHS_OKRUH,
    NUMBERS_OKRUH,
    WEEKDAYS_OKRUH,
    MonthCardItem,
    NumberCardItem,
    WeekdayCardItem as WeekdayCard,
    build_asset_index,
    build_assets,
    build_color_cards,
    build_flashcards,
    build_months,
    build_numbers,
    build_weekdays,
    color_name_map,
    edit_distance,
    load_pref_map,
    load_pref_map_from_file,
    normalize_answer,
    write_user_color_prefs,
)
from step3_flashcards import (
    IMAGE_SIZE as FLASH_IMAGE_SIZE,
    _placeholder_image as flash_placeholder_image,
)
from step4_colors import (
    COLOR_HEX_BY_CZ,
    IMAGE_SIZE as COLORS_IMAGE_SIZE,
    OKRUH as COLORS_OKRUH,
    _placeholder_image as color_placeholder_image,
)
from step5_weekdays import (
    PREFS_FILE,
)
from tts_utils import SingleFlightTTS


MONTHS_IMAGE_SIZE = (260, 360)
MONTHS_ASSETS_DIR = Path(__file__).resolve().parent / "Foto_normalized" / "Months"


def _poll_tts_idle(widget, tts: SingleFlightTTS, callback, poll_ms: int = 120):
    if not widget.winfo_exists():
        return None
    if tts.is_busy():
        return widget.after(poll_ms, lambda: _poll_tts_idle(widget, tts, callback, poll_ms))
    return widget.after(poll_ms, callback)


class FlashcardsScreen(ctk.CTkFrame):
    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        okruh: str,
        on_back,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.on_back = on_back
        self.asset_index = build_asset_index(Path(__file__).resolve().parent / "Foto_normalized")
        self.cards = build_flashcards(bundle, lang, okruh, self.asset_index[FLASH_OKRUH_TO_FOLDER[okruh]])
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.known_count = 0
        self.unknown_count = 0
        self.rated_item_ids: set[int] = set()
        self.current_photo: ctk.CTkImage | None = None
        self.tts = SingleFlightTTS()

        self.user_id = user_id
        self.lang = lang
        self.okruh = okruh

        self._build_ui()
        self._render()

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(
            top,
            text=f"Flashcards · {self.okruh} · {self.lang} · {self.user_id}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(top, text="Zpět do kokpitu", command=self.on_back).pack(side="right", padx=12, pady=12)

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
        ctk.CTkButton(bottom, text="Zobrazit překlad", command=self._reveal).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Přehrát výslovnost", command=self._speak_current).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Znám ✓", command=self._mark_known).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Neznám ✗", command=self._mark_unknown).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Další", command=self._next_card).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(bottom, text="Zamíchat znovu", command=self._reshuffle).pack(side="left", padx=8, pady=10)
        self.status_label = ctk.CTkLabel(bottom, text="Připraveno.")
        self.status_label.pack(side="right", padx=12, pady=10)

    def _current_card(self):
        if not self.cards or self.index >= len(self.order):
            return None
        return self.cards[self.order[self.index]]

    def _build_display_image(self, card) -> Image.Image:
        if card.image_path and card.image_path.exists():
            with Image.open(card.image_path) as raw:
                img = raw.convert("RGB")
        else:
            img = flash_placeholder_image(card.en)
        img = ImageOps.contain(img, FLASH_IMAGE_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", FLASH_IMAGE_SIZE, (240, 240, 240))
        x = (FLASH_IMAGE_SIZE[0] - img.size[0]) // 2
        y = (FLASH_IMAGE_SIZE[1] - img.size[1]) // 2
        canvas.paste(img, (x, y))
        return canvas

    def _render(self) -> None:
        card = self._current_card()
        if card is None:
            self.progress_label.configure(text=f"Hotovo ({len(self.cards)} karet)")
            self.cz_label.configure(text="CZ: -")
            self.target_label.configure(text=f"Znám: {self.known_count} | Neznám: {self.unknown_count}")
            self.image_label.configure(image=None, text="")
            self.current_photo = None
            return
        self.progress_label.configure(text=f"Karta {self.index + 1}/{len(self.cards)}")
        self.cz_label.configure(text=f"CZ: {card.cz}")
        self.target_label.configure(text=card.target_text if self.revealed else "?")
        canvas = self._build_display_image(card)
        self.current_photo = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=FLASH_IMAGE_SIZE)
        self.image_label.configure(image=self.current_photo, text="")

    def _reveal(self) -> None:
        if self._current_card() is None:
            return
        self.revealed = True
        self._render()

    def _speak_current(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.status_label.configure(text="TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text, self.lang, rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _mark_known(self) -> None:
        card = self._current_card()
        if card and card.item_id not in self.rated_item_ids:
            self.rated_item_ids.add(card.item_id)
            self.known_count += 1
        self._next_card()

    def _mark_unknown(self) -> None:
        card = self._current_card()
        if card and card.item_id not in self.rated_item_ids:
            self.rated_item_ids.add(card.item_id)
            self.unknown_count += 1
        self._next_card()

    def _next_card(self) -> None:
        if self._current_card() is None:
            return
        self.index += 1
        self.revealed = False
        self._render()

    def _reshuffle(self) -> None:
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.rated_item_ids.clear()
        self.known_count = 0
        self.unknown_count = 0
        self._render()


class ColorsScreen(ctk.CTkFrame):
    def __init__(self, master, bundle: DataBundle, user_id: str, lang: str, on_back) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.assets = build_assets(Path(__file__).resolve().parent / "Foto_normalized" / "Colors")
        self.cards = build_color_cards(bundle, lang, self.assets)
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.current_photo: ImageTk.PhotoImage | None = None
        self.tts = SingleFlightTTS()
        self.autoplay_job: str | None = None
        self.autoplay_on = False

        self._build_ui()
        self._render()

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(top, text=f"Barvy · {self.lang} · {self.user_id}", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(top, text="Zpět do kokpitu", command=self._back).pack(side="right", padx=12, pady=12)

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
        self.status_label = ctk.CTkLabel(bottom, text=f"Připraveno. TTS: {self.tts.backend}")
        self.status_label.pack(side="right", padx=8, pady=10)

    def _current_card(self):
        if not self.cards or self.index >= len(self.order):
            return None
        return self.cards[self.order[self.index]]

    def _build_display_image(self, card) -> Image.Image:
        if card.image_path and card.image_path.exists():
            with Image.open(card.image_path) as raw:
                img = raw.convert("RGB")
        else:
            img = color_placeholder_image(card.en)
        img = ImageOps.contain(img, COLORS_IMAGE_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", COLORS_IMAGE_SIZE, (240, 240, 240))
        x = (COLORS_IMAGE_SIZE[0] - img.size[0]) // 2
        y = (COLORS_IMAGE_SIZE[1] - img.size[1]) // 2
        canvas.paste(img, (x, y))
        return canvas

    def _safe_set_image(self, photo: ImageTk.PhotoImage | None) -> None:
        try:
            if photo is None:
                self.image_label.configure(image="")
                self.image_label.image = None
            else:
                self.image_label.configure(image=photo)
                self.image_label.image = photo
        except tk.TclError:
            pass

    def _render(self) -> None:
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
        if self._current_card():
            self.revealed = True
            self._render()

    def _speak_current(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.status_label.configure(text="TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text, self.lang, rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _next_card(self) -> None:
        if not self._current_card():
            return
        self.index += 1
        self.revealed = False
        self._render()

    def _reshuffle(self) -> None:
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self._render()

    def _toggle_autoplay(self) -> None:
        if self.autoplay_on:
            self._stop_autoplay()
        else:
            self.autoplay_on = True
            self.auto_btn.configure(text="Auto OFF")
            self._run_autoplay()

    def _stop_autoplay(self) -> None:
        self.autoplay_on = False
        if hasattr(self, "auto_btn"):
            self.auto_btn.configure(text="Auto ON")
        if self.autoplay_job is not None:
            try:
                self.after_cancel(self.autoplay_job)
            except Exception:
                pass
            self.autoplay_job = None

    def _run_autoplay(self) -> None:
        if not self.autoplay_on:
            return
        if self._current_card() is None:
            self._stop_autoplay()
            return
        if not self.revealed:
            self._reveal()
            self._speak_current()
            self.autoplay_job = _poll_tts_idle(self, self.tts, self._autoplay_advance)
            return
        self.autoplay_job = self.after(300, self._autoplay_advance)

    def _autoplay_advance(self) -> None:
        if not self.autoplay_on:
            return
        self._next_card()
        self.autoplay_job = self.after(300, self._run_autoplay)

    def _back(self) -> None:
        self._stop_autoplay()
        self.on_back()

    def destroy(self) -> None:
        self._stop_autoplay()
        super().destroy()


class MonthsSlideshowPane(ctk.CTkFrame):
    def __init__(self, master: "MonthsScreen") -> None:
        super().__init__(master.content, corner_radius=12)
        self.master_screen = master
        self.current_photo: ImageTk.PhotoImage | None = None
        self.autoplay_on = False
        self.autoplay_job: str | None = None

        self.pack(fill="both", expand=True, padx=12, pady=12)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.progress_label = ctk.CTkLabel(self, text="Měsíc 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(10, 6))

        self.image_wrap = tk.Frame(self, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_wrap.pack(pady=(2, 6))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_label.pack()

        self.cz_label = ctk.CTkLabel(self, text="CZ: -", font=ctk.CTkFont(size=20, weight="bold"))
        self.cz_label.pack(pady=(4, 2))
        self.target_label = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=28))
        self.target_label.pack(pady=(2, 6))

        btns = ctk.CTkFrame(self, corner_radius=10)
        btns.pack(fill="x", padx=24, pady=6)
        ctk.CTkButton(btns, text="Předchozí", command=self._prev).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(btns, text="Přehrát", command=self._speak).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(btns, text="Další", command=self._next).pack(side="left", padx=8, pady=10)
        self.auto_btn = ctk.CTkButton(btns, text="Auto ON", command=self._toggle_autoplay)
        self.auto_btn.pack(side="left", padx=8, pady=10)

    def _set_image(self, card: MonthCardItem) -> None:
        canvas = self.master_screen.build_display_image(card)
        self.current_photo = ImageTk.PhotoImage(canvas)
        self.image_label.configure(image=self.current_photo)
        self.image_label.image = self.current_photo

    def refresh(self) -> None:
        card = self.master_screen.current_card()
        if card is None:
            self.progress_label.configure(text="Měsíc 0/0")
            self.cz_label.configure(text="CZ: -")
            self.target_label.configure(text="-")
            return
        self.progress_label.configure(text=f"Měsíc {self.master_screen.index + 1}/{len(self.master_screen.cards)}")
        self.cz_label.configure(text=f"CZ: {card.cz}")
        self.target_label.configure(text=card.target_text(self.master_screen.lang))
        self._set_image(card)

    def _prev(self) -> None:
        self.stop()
        self.master_screen.shift_month(-1)

    def _next(self) -> None:
        self.stop()
        self.master_screen.shift_month(1)

    def _speak(self) -> None:
        self.master_screen.speak_current_month()

    def _toggle_autoplay(self) -> None:
        if self.autoplay_on:
            self.stop()
            self.master_screen.set_status("Slideshow vypnuto.")
            return
        self.autoplay_on = True
        self.auto_btn.configure(text="Auto OFF")
        self.master_screen.set_status("Slideshow běží automaticky.")
        self._tick()

    def _tick(self) -> None:
        if not self.autoplay_on:
            return
        self.refresh()
        self.master_screen.speak_current_month()
        self.autoplay_job = _poll_tts_idle(self, self.master_screen.tts, self._advance_then_tick)

    def _advance_then_tick(self) -> None:
        if not self.autoplay_on:
            return
        self.master_screen.shift_month(1, update_status=False)
        self._tick()

    def stop(self) -> None:
        self.autoplay_on = False
        if hasattr(self, "auto_btn"):
            self.auto_btn.configure(text="Auto ON")
        if self.autoplay_job is not None:
            try:
                self.after_cancel(self.autoplay_job)
            except Exception:
                pass
            self.autoplay_job = None

    def cleanup(self) -> None:
        self.stop()


class MonthsWritingPane(ctk.CTkFrame):
    def __init__(self, master: "MonthsScreen") -> None:
        super().__init__(master.content, corner_radius=12)
        self.master_screen = master
        self.current_photo: ImageTk.PhotoImage | None = None
        self.after_ids: list[str] = []

        self.pack(fill="both", expand=True, padx=12, pady=12)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.progress_label = ctk.CTkLabel(self, text="Měsíc 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(10, 6))

        self.image_wrap = tk.Frame(self, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_wrap.pack(pady=(2, 6))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_label.pack()

        self.cz_label = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=22, weight="bold"))
        self.cz_label.pack(pady=(6, 4))

        entry_wrap = ctk.CTkFrame(self, corner_radius=10)
        entry_wrap.pack(fill="x", padx=24, pady=6)
        self.entry = ctk.CTkEntry(entry_wrap, width=320)
        self.entry.pack(side="left", padx=12, pady=12)
        ctk.CTkButton(entry_wrap, text="Kontrola", command=self.check_answer).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(entry_wrap, text="Přehrát", command=self.master_screen.speak_current_month).pack(side="left", padx=8, pady=12)

        self.result_label = ctk.CTkLabel(entry_wrap, text="", font=ctk.CTkFont(size=16, weight="bold"), width=300, anchor="w")
        self.result_label.pack(side="left", padx=10, pady=12)

        nav = ctk.CTkFrame(self, corner_radius=10)
        nav.pack(fill="x", padx=24, pady=6)
        ctk.CTkButton(nav, text="Předchozí", command=lambda: self.master_screen.shift_month(-1)).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(nav, text="Další", command=lambda: self.master_screen.shift_month(1)).pack(side="left", padx=8, pady=12)

    def _set_image(self, card: MonthCardItem) -> None:
        canvas = self.master_screen.build_display_image(card)
        self.current_photo = ImageTk.PhotoImage(canvas)
        self.image_label.configure(image=self.current_photo)
        self.image_label.image = self.current_photo

    def refresh(self) -> None:
        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.after_ids.clear()

        card = self.master_screen.current_card()
        if card is None:
            self.progress_label.configure(text="Měsíc 0/0")
            self.cz_label.configure(text="-")
            self.result_label.configure(text="")
            return
        self.progress_label.configure(text=f"Měsíc {self.master_screen.index + 1}/{len(self.master_screen.cards)}")
        self.cz_label.configure(text=card.cz)
        self._set_image(card)
        self.entry.delete(0, "end")
        self.result_label.configure(text="")

    def check_answer(self) -> None:
        card = self.master_screen.current_card()
        if card is None:
            return
        user_text = self.entry.get().strip()
        expected = card.target_text(self.master_screen.lang)
        answer = normalize_answer(user_text)
        target = normalize_answer(expected)

        if not user_text:
            self.result_label.configure(text="Napiš název měsíce.", text_color="#DC2626")
            self.master_screen.set_status("Kontrola: pole je prázdné.")
            return
        if answer == target:
            self.result_label.configure(text=f"Správně: {expected}", text_color="#16A34A")
            self.master_screen.set_status(f"Správně: {card.cz} -> {expected}")
            self.master_screen.speak_current_month()
            return
        if edit_distance(answer, target) <= 1:
            self.result_label.configure(text=f"Skoro! Správně: {expected}", text_color="#D97706")
            self.master_screen.set_status(f"Skoro správně: {card.cz} -> {expected}")
            return

        self.result_label.configure(text=f"Chyba: {user_text} -> {expected}", text_color="#DC2626")
        self.master_screen.set_status(f"Chyba: {card.cz} -> {expected}")

        def _show_correct() -> None:
            try:
                self.entry.delete(0, "end")
                self.entry.insert(0, expected)
                self.result_label.configure(text=f"Správně: {expected}", text_color="#16A34A")
                self.master_screen.speak_current_month()
            except Exception:
                pass

        self.after_ids.append(self.after(2000, _show_correct))

    def cleanup(self) -> None:
        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.after_ids.clear()
        try:
            self.entry.configure(state="disabled")
        except Exception:
            pass


class MonthsScreen(ctk.CTkFrame):
    def __init__(self, master, bundle: DataBundle, user_id: str, lang: str, on_back) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.cards = build_months(bundle)
        self.assets = build_assets(MONTHS_ASSETS_DIR)
        self.index = 0
        self.mode_var = ctk.StringVar(value="Slideshow")
        self.tts = SingleFlightTTS()
        self.is_leaving = False
        self.active_pane: MonthsSlideshowPane | MonthsWritingPane | None = None

        self._build_ui()
        self._switch_mode()

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        top.grid_columnconfigure((0, 1, 2), weight=1)

        self.title_label = ctk.CTkLabel(
            top,
            text=f"Měsíce · {self.lang} · {self.user_id}",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        mode_wrap = ctk.CTkFrame(top, corner_radius=8)
        mode_wrap.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(mode_wrap, text="Režim").pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkSegmentedButton(
            mode_wrap,
            values=["Slideshow", "Psaní"],
            variable=self.mode_var,
            command=lambda _value: self._switch_mode(),
        ).pack(fill="x", padx=8, pady=(0, 8))

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, padx=8, pady=8, sticky="e")
        self.lang_menu = ctk.CTkOptionMenu(right, values=list(LANG_COL_MAP), command=self._on_lang_changed)
        self.lang_menu.set(self.lang)
        self.lang_menu.pack(side="left", padx=(0, 8))
        ctk.CTkButton(right, text="Zpět do kokpitu", command=self._back).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="Připraveno. Vyber režim pro měsíce.", font=ctk.CTkFont(size=13))
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))

        self.content = ctk.CTkFrame(self, corner_radius=12)
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def current_card(self) -> MonthCardItem | None:
        if not self.cards:
            return None
        return self.cards[self.index % len(self.cards)]

    def build_display_image(self, card: MonthCardItem) -> Image.Image:
        asset = self.assets.get(card.en.lower())
        if asset and asset.exists():
            with Image.open(asset) as raw:
                img = raw.convert("RGB")
        else:
            img = Image.new("RGB", MONTHS_IMAGE_SIZE, (230, 230, 230))
            draw = ImageDraw.Draw(img)
            draw.rectangle((8, 8, MONTHS_IMAGE_SIZE[0] - 8, MONTHS_IMAGE_SIZE[1] - 8), outline=(160, 160, 160), width=2)
            draw.text((18, MONTHS_IMAGE_SIZE[1] // 2 - 10), f"Missing image: {card.en}", fill=(80, 80, 80))
            return img
        img = ImageOps.contain(img, MONTHS_IMAGE_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", MONTHS_IMAGE_SIZE, (240, 240, 240))
        x = (MONTHS_IMAGE_SIZE[0] - img.size[0]) // 2
        y = (MONTHS_IMAGE_SIZE[1] - img.size[1]) // 2
        canvas.paste(img, (x, y))
        return canvas

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def speak_current_month(self) -> None:
        card = self.current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.set_status("TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text(self.lang), self.lang, rate=165):
            self.set_status("TTS právě mluví, nový požadavek přeskočen.")

    def shift_month(self, delta: int, update_status: bool = True) -> None:
        if not self.cards:
            return
        self.index = (self.index + delta) % len(self.cards)
        if self.active_pane is not None:
            self.active_pane.refresh()
        if update_status:
            self.set_status(f"Aktuální měsíc: {self.cards[self.index].cz}")

    def _switch_mode(self) -> None:
        if self.active_pane is not None:
            self.active_pane.cleanup()
            self.active_pane.destroy()
            self.active_pane = None
        if self.mode_var.get() == "Slideshow":
            self.active_pane = MonthsSlideshowPane(self)
        else:
            self.active_pane = MonthsWritingPane(self)

    def _on_lang_changed(self, value: str) -> None:
        self.lang = value
        self.title_label.configure(text=f"Měsíce · {self.lang} · {self.user_id}")
        if self.active_pane is not None:
            self.active_pane.refresh()
        self.set_status(f"Jazyk přepnut na {self.lang}.")

    def _back(self) -> None:
        if self.is_leaving:
            return
        self.is_leaving = True
        if self.active_pane is not None:
            self.active_pane.cleanup()
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass
        self.after(1, self._do_back)

    def _do_back(self) -> None:
        self.is_leaving = False
        self.on_back()

    def destroy(self) -> None:
        if self.active_pane is not None:
            self.active_pane.cleanup()
        super().destroy()


class NumbersScreen(ctk.CTkFrame):
    def __init__(self, master, bundle: DataBundle, user_id: str, lang: str, on_back) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.cards = build_numbers(bundle)
        self.order_mode = ctk.StringVar(value="Náhodně")
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.tts = SingleFlightTTS()
        self.autoplay_on = False
        self.autoplay_job: str | None = None

        self._build_ui()
        self._render()

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(
            top,
            text=f"Číslovky · {self.lang} · {self.user_id}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=12, pady=12)

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)
        self.order_menu = ctk.CTkOptionMenu(right, values=["Náhodně", "Vzestupně"], command=self._on_order_changed)
        self.order_menu.set(self.order_mode.get())
        self.order_menu.pack(side="left", padx=(0, 8))
        self.lang_menu = ctk.CTkOptionMenu(right, values=list(LANG_COL_MAP), command=self._on_lang_changed)
        self.lang_menu.set(self.lang)
        self.lang_menu.pack(side="left", padx=(0, 8))
        ctk.CTkButton(right, text="Zpět do kokpitu", command=self._back).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="Připraveno. Procvičuj číslovky.", font=ctk.CTkFont(size=13))
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))

        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.progress_label = ctk.CTkLabel(main, text="Číslo 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(16, 10))

        self.number_panel = ctk.CTkFrame(main, corner_radius=22, fg_color="#E5E7EB")
        self.number_panel.pack(fill="x", padx=32, pady=(6, 14))
        self.number_label = ctk.CTkLabel(self.number_panel, text="-", font=ctk.CTkFont(size=64, weight="bold"))
        self.number_label.pack(pady=(28, 8))
        self.target_label = ctk.CTkLabel(self.number_panel, text="-", font=ctk.CTkFont(size=28))
        self.target_label.pack(pady=(0, 28))

        self.cz_label = ctk.CTkLabel(main, text="CZ: -", font=ctk.CTkFont(size=18, weight="bold"))
        self.cz_label.pack(pady=(4, 12))

        btns = ctk.CTkFrame(main, corner_radius=10)
        btns.pack(fill="x", padx=24, pady=10)
        ctk.CTkButton(btns, text="Předchozí", command=lambda: self._shift(-1)).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(btns, text="Zobrazit název", command=self._reveal).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(btns, text="Přehrát", command=self._speak_current).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(btns, text="Další", command=lambda: self._shift(1)).pack(side="left", padx=8, pady=12)
        self.auto_btn = ctk.CTkButton(btns, text="Auto ON", command=self._toggle_autoplay)
        self.auto_btn.pack(side="left", padx=8, pady=12)

    def _current_card(self) -> NumberCardItem | None:
        if not self.cards or self.index >= len(self.order):
            return None
        return self.cards[self.order[self.index]]

    def _render(self) -> None:
        card = self._current_card()
        if card is None:
            self.progress_label.configure(text="Číslo 0/0")
            self.number_label.configure(text="-")
            self.target_label.configure(text="-")
            self.cz_label.configure(text="CZ: -")
            return
        self.progress_label.configure(text=f"Číslo {self.index + 1}/{len(self.cards)}")
        self.number_label.configure(text=self._display_number(card))
        self.target_label.configure(text=card.target_text(self.lang) if self.revealed else "?")
        self.cz_label.configure(text=f"CZ: {card.cz}")

    def _display_number(self, card: NumberCardItem) -> str:
        if card.numeric_value is None:
            return card.cz
        return f"{card.numeric_value:,}".replace(",", " ")

    def _reveal(self) -> None:
        if self._current_card() is None:
            return
        self.revealed = True
        self._render()

    def _shift(self, delta: int) -> None:
        self._stop_autoplay()
        if not self.cards:
            return
        self.index = (self.index + delta) % len(self.order)
        self.revealed = False
        self._render()
        current = self._current_card()
        if current is not None:
            self.status_label.configure(text=f"Aktuální číslo: {current.cz}")

    def _speak_current(self) -> None:
        card = self._current_card()
        if card is None:
            return
        if self.tts.backend == "none":
            self.status_label.configure(text="TTS není dostupné.")
            return
        if not self.tts.speak(card.target_text(self.lang), self.lang, rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _toggle_autoplay(self) -> None:
        if self.autoplay_on:
            self._stop_autoplay()
            self.status_label.configure(text="Auto režim vypnut.")
            return
        self.autoplay_on = True
        self.auto_btn.configure(text="Auto OFF")
        self.status_label.configure(text="Auto režim běží.")
        self._tick()

    def _tick(self) -> None:
        if not self.autoplay_on:
            return
        self._render()
        if not self.revealed:
            self.revealed = True
            self._render()
            self._speak_current()
            self.autoplay_job = _poll_tts_idle(self, self.tts, self._advance_then_tick)
            return
        self.autoplay_job = self.after(300, self._advance_then_tick)

    def _advance_then_tick(self) -> None:
        if not self.autoplay_on:
            return
        self.index = (self.index + 1) % len(self.order)
        self.revealed = False
        self._tick()

    def _stop_autoplay(self) -> None:
        self.autoplay_on = False
        if hasattr(self, "auto_btn"):
            self.auto_btn.configure(text="Auto ON")
        if self.autoplay_job is not None:
            try:
                self.after_cancel(self.autoplay_job)
            except Exception:
                pass
            self.autoplay_job = None

    def _on_lang_changed(self, value: str) -> None:
        self.lang = value
        self._render()
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang}.")

    def _on_order_changed(self, value: str) -> None:
        self.order_mode.set(value)
        if value == "Vzestupně":
            self.order = sorted(
                range(len(self.cards)),
                key=lambda idx: (
                    self.cards[idx].numeric_value is None,
                    self.cards[idx].numeric_value if self.cards[idx].numeric_value is not None else 10**12,
                    self.cards[idx].cz,
                ),
            )
        else:
            self.order = list(range(len(self.cards)))
            random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self._render()
        self.status_label.configure(text=f"Pořadí přepnuto na: {value}.")

    def _back(self) -> None:
        self._stop_autoplay()
        self.on_back()

    def destroy(self) -> None:
        self._stop_autoplay()
        super().destroy()


class WeekdaysScreen(ctk.CTkFrame):
    def __init__(self, master, bundle: DataBundle, user_id: str, lang: str, on_back) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.on_back = on_back
        self.cards = build_weekdays(bundle)
        self.color_options = color_name_map(bundle)
        self.tts = SingleFlightTTS()
        self.sequence_job: str | None = None
        self.sequence_running = False
        self.sequence_index = 0
        self.sequence_controls_job: str | None = None
        self.sequence_controls_locked = False
        self.write_rows: dict[int, dict[str, object]] = {}
        self.write_after_ids: list[str] = []
        self.write_frame: ctk.CTkScrollableFrame | None = None
        self.is_leaving = False
        self.current_user_id = user_id
        self.lang = lang
        self.mode_var = ctk.StringVar(value="Barvy dnů")
        self.day_colors = self._build_day_colors(user_id)

        self._build_ui()
        self._render_mode()

    def _build_day_colors(self, user_id: str) -> dict[int, str]:
        pref_map = load_pref_map_from_file(PREFS_FILE, user_id, self.cards)
        if not pref_map:
            pref_map = load_pref_map(self.bundle, user_id, self.cards)
        out: dict[int, str] = {}
        for idx, card in enumerate(self.cards):
            pref = pref_map.get(card.item_id)
            color_hex = (pref.assoc_color_hex if pref else "").strip()
            out[card.item_id] = color_hex or DEFAULT_DAY_COLORS[idx % len(DEFAULT_DAY_COLORS)]
        return out

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.user_var = ctk.StringVar(value=self.current_user_id)
        self.lang_var = ctk.StringVar(value=self.lang)
        self._add_selector(top, 0, "Uživatel", self.user_var, [u.user_id for u in self.bundle.users if u.active], self._on_user_changed)
        self._add_selector(top, 1, "Jazyk", self.lang_var, list(LANG_COL_MAP), self._on_lang_changed)

        mode_wrap = ctk.CTkFrame(top, corner_radius=8)
        mode_wrap.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(mode_wrap, text="Režim").pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkSegmentedButton(
            mode_wrap,
            values=["Barvy dnů", "Sekvence", "Psaní"],
            variable=self.mode_var,
            command=lambda _value: self._render_mode(),
        ).pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(top, text="Zpět do kokpitu", command=self._back).grid(row=1, column=3, padx=8, pady=(4, 10), sticky="ew")

        self.status_label = ctk.CTkLabel(self, text="Připraveno. Nastav barvy dnů nebo spusť sekvenci.", font=ctk.CTkFont(size=13))
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))
        self.content = ctk.CTkFrame(self, corner_radius=12)
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _add_selector(self, parent, col, label, variable, values, command) -> None:
        wrap = ctk.CTkFrame(parent, corner_radius=8)
        wrap.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(wrap, text=label).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkOptionMenu(wrap, variable=variable, values=values, command=command).pack(fill="x", padx=8, pady=(0, 8))

    def _cancel_pending_jobs(self) -> None:
        self._stop_sequence()
        for after_id in self.write_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.write_after_ids.clear()

    def _render_mode(self) -> None:
        self._cancel_pending_jobs()
        for child in self.content.winfo_children():
            child.destroy()
        if self.mode_var.get() == "Barvy dnů":
            self._build_color_editor()
        elif self.mode_var.get() == "Sekvence":
            self._build_sequence_mode()
        else:
            self._build_writing_mode()

    def _build_color_editor(self) -> None:
        frame = ctk.CTkFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(frame, text="Přiřazení barev k dnům", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkLabel(frame, text="Barvy se ukládají pro vybraného uživatele do user_item_prefs.csv.").pack(anchor="w", padx=16, pady=(0, 12))
        options = list(self.color_options.keys())
        for card in self.cards:
            row = ctk.CTkFrame(frame, corner_radius=10)
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=card.cz, width=160, anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=12, pady=10)
            swatch = ctk.CTkFrame(row, width=42, height=28, corner_radius=8, fg_color=self.day_colors[card.item_id])
            swatch.pack(side="left", padx=(0, 12), pady=10)
            var = ctk.StringVar(value=self._hex_to_color_name(self.day_colors[card.item_id]))
            menu = ctk.CTkOptionMenu(
                row,
                variable=var,
                values=options,
                command=lambda choice, item_id=card.item_id, chip=swatch: self._on_color_selected(item_id, choice, chip),
            )
            menu.pack(side="left", padx=8, pady=10)
            ctk.CTkLabel(row, text=card.target_text(self.lang_var.get()), width=180, anchor="w").pack(side="right", padx=12, pady=10)
        ctk.CTkButton(frame, text="Uložit barvy", command=self._save_day_colors).pack(anchor="e", padx=16, pady=14)

    def _build_sequence_mode(self) -> None:
        frame = ctk.CTkFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(frame, text="Sekvence Po–Ne", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=16, pady=(14, 8))
        self.seq_progress = ctk.CTkLabel(frame, text="Den 1/7", font=ctk.CTkFont(size=14, weight="bold"))
        self.seq_progress.pack(anchor="w", padx=16, pady=(0, 10))
        self.seq_card = ctk.CTkFrame(frame, width=760, height=220, corner_radius=18, fg_color="#4F46E5")
        self.seq_card.pack(fill="x", padx=40, pady=14)
        self.seq_card.pack_propagate(False)
        self.seq_target_label = ctk.CTkLabel(self.seq_card, text="-", font=ctk.CTkFont(size=34, weight="bold"), text_color="white")
        self.seq_target_label.pack(pady=(48, 8))
        self.seq_cz_label = ctk.CTkLabel(self.seq_card, text="-", font=ctk.CTkFont(size=18), text_color="white")
        self.seq_cz_label.pack()
        btns = ctk.CTkFrame(frame, corner_radius=10)
        btns.pack(fill="x", padx=24, pady=10)
        self.seq_prev_btn = ctk.CTkButton(btns, text="Předchozí", command=self._prev_sequence)
        self.seq_prev_btn.pack(side="left", padx=8, pady=10)
        self.seq_play_btn = ctk.CTkButton(btns, text="Přehrát", command=self._speak_sequence)
        self.seq_play_btn.pack(side="left", padx=8, pady=10)
        self.seq_next_btn = ctk.CTkButton(btns, text="Další", command=self._next_sequence)
        self.seq_next_btn.pack(side="left", padx=8, pady=10)
        self.seq_auto_btn = ctk.CTkButton(btns, text="Auto ON", command=self._toggle_sequence)
        self.seq_auto_btn.pack(side="left", padx=8, pady=10)
        self.sequence_index = 0
        self._render_sequence_card()

    def _build_writing_mode(self) -> None:
        frame = ctk.CTkScrollableFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.write_frame = frame
        ctk.CTkLabel(frame, text="Psaní s kontrolou", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=8, pady=(8, 10))
        self.write_rows = {}
        for card in self.cards:
            row = ctk.CTkFrame(frame, corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)
            color_hex = self.day_colors[card.item_id]
            swatch = ctk.CTkFrame(row, width=18, height=44, corner_radius=6, fg_color=color_hex)
            swatch.pack(side="left", padx=(10, 8), pady=10)
            ctk.CTkLabel(row, text=card.cz, width=120, anchor="w", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=(0, 8), pady=10)
            entry = ctk.CTkEntry(row, width=240)
            entry.pack(side="left", padx=8, pady=10)
            ctk.CTkButton(row, text="Kontrola", width=92, command=lambda c=card: self._check_write_answer(c)).pack(side="left", padx=8, pady=10)
            result = ctk.CTkLabel(row, text="", width=360, anchor="w")
            result.pack(side="left", padx=8, pady=10)
            self.write_rows[card.item_id] = {"entry": entry, "result": result}

    def _hex_to_color_name(self, color_hex: str) -> str:
        for name, hex_value in self.color_options.items():
            if hex_value.lower() == color_hex.lower():
                return name
        return next(iter(self.color_options.keys()))

    def _on_color_selected(self, item_id: int, choice: str, chip: ctk.CTkFrame) -> None:
        color_hex = self.color_options[choice]
        self.day_colors[item_id] = color_hex
        chip.configure(fg_color=color_hex)

    def _save_day_colors(self) -> None:
        try:
            write_user_color_prefs(PREFS_FILE, self.bundle, self.current_user_id, self.day_colors)
        except Exception as exc:
            self.status_label.configure(text=f"Uložení barev selhalo: {exc}")
            return
        self.day_colors = self._build_day_colors(self.current_user_id)
        self._render_mode()
        self.status_label.configure(text=f"Barvy dnů uloženy pro uživatele '{self.current_user_id}'.")

    def _render_sequence_card(self) -> None:
        card = self.cards[self.sequence_index]
        self.seq_progress.configure(text=f"Den {self.sequence_index + 1}/{len(self.cards)}")
        self.seq_card.configure(fg_color=self.day_colors.get(card.item_id, DEFAULT_DAY_COLORS[self.sequence_index]))
        self.seq_target_label.configure(text=card.target_text(self.lang_var.get()))
        self.seq_cz_label.configure(text=card.cz)

    def _prev_sequence(self) -> None:
        if self.sequence_controls_locked or self.tts.is_busy():
            self.status_label.configure(text="Počkej, až doběhne hlas.")
            return
        self.sequence_index = (self.sequence_index - 1) % len(self.cards)
        self._render_sequence_card()

    def _next_sequence(self) -> None:
        if self.sequence_controls_locked or self.tts.is_busy():
            self.status_label.configure(text="Počkej, až doběhne hlas.")
            return
        self.sequence_index = (self.sequence_index + 1) % len(self.cards)
        self._render_sequence_card()

    def _speak_sequence(self) -> None:
        if self.sequence_controls_locked or self.tts.is_busy():
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")
            return
        self._lock_sequence_controls()
        self._speak_text(self.cards[self.sequence_index].target_text(self.lang_var.get()))

    def _toggle_sequence(self) -> None:
        if self.sequence_running:
            self._stop_sequence()
            self.status_label.configure(text="Sekvence vypnuta.")
            return
        self.sequence_running = True
        self.seq_auto_btn.configure(text="Auto OFF")
        self.status_label.configure(text="Sekvence běží automaticky.")
        self._run_sequence()

    def _run_sequence(self) -> None:
        if not self.sequence_running:
            return
        self._render_sequence_card()
        self._speak_sequence()
        self.sequence_job = _poll_tts_idle(self, self.tts, self._advance_sequence)

    def _advance_sequence(self) -> None:
        if not self.sequence_running:
            return
        self.sequence_index = (self.sequence_index + 1) % len(self.cards)
        self.sequence_job = self.after(300, self._run_sequence)

    def _stop_sequence(self) -> None:
        self.sequence_running = False
        if hasattr(self, "seq_auto_btn"):
            self.seq_auto_btn.configure(text="Auto ON")
        if self.sequence_job is not None:
            try:
                self.after_cancel(self.sequence_job)
            except Exception:
                pass
            self.sequence_job = None
        if self.sequence_controls_job is not None:
            try:
                self.after_cancel(self.sequence_controls_job)
            except Exception:
                pass
            self.sequence_controls_job = None
        self._unlock_sequence_controls()

    def _check_write_answer(self, card: WeekdayCard) -> None:
        row = self.write_rows[card.item_id]
        entry = row["entry"]
        result = row["result"]
        user_text = entry.get().strip()
        expected = card.target_text(self.lang_var.get())
        answer = normalize_answer(user_text)
        target = normalize_answer(expected)
        if answer == target:
            result.configure(text=f"Správně: {expected}", text_color="#16A34A")
            self._speak_text(expected)
            return
        if user_text and edit_distance(answer, target) <= 1:
            result.configure(text=f"Skoro! Správně: {expected}", text_color="#D97706")
            return
        result.configure(text=f"Chyba: {user_text} -> {expected}", text_color="#DC2626")
        def _show_correct() -> None:
            try:
                entry.delete(0, "end")
                entry.insert(0, expected)
                result.configure(text=f"Správně: {expected}", text_color="#16A34A")
            except Exception:
                pass
        self.write_after_ids.append(self.after(2000, _show_correct))

    def _on_user_changed(self, value: str) -> None:
        self.current_user_id = value
        self.day_colors = self._build_day_colors(self.current_user_id)
        self._render_mode()
        self.status_label.configure(text=f"Uživatel přepnut na {self.current_user_id}.")

    def _on_lang_changed(self, value: str) -> None:
        self.lang = value
        self._render_mode()
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang}.")

    def _speak_text(self, text: str) -> None:
        if self.tts.backend == "none":
            return
        if not self.tts.speak(text, self.lang, rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _lock_sequence_controls(self) -> None:
        self.sequence_controls_locked = True
        for btn_name in ("seq_prev_btn", "seq_play_btn", "seq_next_btn"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                try:
                    btn.configure(state="disabled")
                except Exception:
                    pass
        self._poll_sequence_controls()

    def _unlock_sequence_controls(self) -> None:
        self.sequence_controls_locked = False
        for btn_name in ("seq_prev_btn", "seq_play_btn", "seq_next_btn"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                try:
                    btn.configure(state="normal")
                except Exception:
                    pass

    def _poll_sequence_controls(self) -> None:
        if self.mode_var.get() != "Sekvence":
            self._unlock_sequence_controls()
            return
        if self.tts.is_busy():
            self.sequence_controls_job = self.after(120, self._poll_sequence_controls)
            return
        self.sequence_controls_job = None
        self._unlock_sequence_controls()

    def _back(self) -> None:
        if self.is_leaving:
            return
        self.is_leaving = True
        self._cancel_pending_jobs()
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass
        self.after(1, self._do_back)

    def _do_back(self) -> None:
        if self.write_frame is not None:
            try:
                self.write_frame.destroy()
            except Exception:
                pass
        self.write_frame = None
        self.write_rows = {}
        self.is_leaving = False
        self.on_back()

    def destroy(self) -> None:
        self._cancel_pending_jobs()
        super().destroy()
