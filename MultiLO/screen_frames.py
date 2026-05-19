"""Internal frame-based screens for MultiLO cockpit navigation."""

from __future__ import annotations

from pathlib import Path
import random
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk

from app_paths import resolve_assets_root
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
from storage import (
    rank_item_ids_by_weakness,
    record_progress_event,
    record_progress_seen,
    reset_progress_for_okruh,
    reset_progress_for_okruh_in_memory,
    update_progress_event_in_memory,
    update_progress_seen_in_memory,
)
from tts_utils import SingleFlightTTS


MONTHS_IMAGE_SIZE = (220, 300)
COLORS_DISPLAY_SIZE = (280, 280)
ASSETS_ROOT = resolve_assets_root()
MONTHS_ASSETS_DIR = ASSETS_ROOT / "Months"
LANG_FLAGS = {
    "FR": "🇫🇷",
    "IT": "🇮🇹",
    "ES": "🇪🇸",
    "EN": "🇬🇧",
}
LANG_MENU_VALUES = [f"{LANG_FLAGS[code]}  {code}" for code in LANG_COL_MAP]
LANG_DIACRITICS = {
    "FR": ["é", "è", "ê", "à", "ç", "ù", "û", "î", "ï", "ë", "ô"],
    "IT": ["à", "è", "é", "ì", "ò", "ù"],
    "ES": ["á", "é", "í", "ó", "ú", "ñ", "ü", "¿", "¡"],
    "EN": [],
}


def _lang_menu_value(code: str) -> str:
    return f"{LANG_FLAGS[code]}  {code}"


def _lang_code_from_menu(value: str) -> str:
    value = value.strip()
    return value[-2:] if len(value) >= 2 else "FR"


def _poll_tts_idle(widget, tts: SingleFlightTTS, callback, poll_ms: int = 120):
    if not widget.winfo_exists():
        return None
    if tts.is_busy():
        return widget.after(poll_ms, lambda: _poll_tts_idle(widget, tts, callback, poll_ms))
    return widget.after(poll_ms, callback)


def _record_event(
    progress_data: dict | None,
    mark_progress_dirty,
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
    correct: bool,
) -> None:
    if progress_data is None:
        record_progress_event(
            user_id=user_id,
            item_id=item_id,
            mode=mode,
            okruh=okruh,
            lang=lang,
            correct=correct,
        )
        return
    update_progress_event_in_memory(
        progress_data,
        user_id=user_id,
        item_id=item_id,
        mode=mode,
        okruh=okruh,
        lang=lang,
        correct=correct,
    )
    if callable(mark_progress_dirty):
        mark_progress_dirty()


def _record_seen(
    progress_data: dict | None,
    mark_progress_dirty,
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
) -> None:
    if progress_data is None:
        record_progress_seen(
            user_id=user_id,
            item_id=item_id,
            mode=mode,
            okruh=okruh,
            lang=lang,
        )
        return
    update_progress_seen_in_memory(
        progress_data,
        user_id=user_id,
        item_id=item_id,
        mode=mode,
        okruh=okruh,
        lang=lang,
    )
    if callable(mark_progress_dirty):
        mark_progress_dirty()


def _reset_okruh_progress(
    progress_data: dict | None,
    mark_progress_dirty,
    *,
    user_id: str,
    okruh: str,
) -> None:
    if progress_data is None:
        reset_progress_for_okruh(user_id=user_id, okruh=okruh)
        return
    reset_progress_for_okruh_in_memory(progress_data, user_id=user_id, okruh=okruh)
    if callable(mark_progress_dirty):
        mark_progress_dirty()


def _widget_alive(widget) -> bool:
    if widget is None:
        return False
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False


def _insert_special_char(entry: tk.Entry, char: str) -> None:
    if not _widget_alive(entry):
        return
    try:
        entry.focus_set()
        start = entry.index("sel.first")
        end = entry.index("sel.last")
        entry.delete(start, end)
        entry.insert(start, char)
        entry.icursor(start + len(char))
        return
    except Exception:
        pass
    try:
        pos = entry.index("insert")
    except Exception:
        pos = "end"
    entry.insert(pos, char)
    try:
        if isinstance(pos, int):
            entry.icursor(pos + len(char))
    except Exception:
        pass


def _build_diacritic_bar(parent, lang: str, entry: tk.Entry, columns: int = 0) -> ctk.CTkFrame | None:
    chars = LANG_DIACRITICS.get(lang, [])
    if not chars:
        return None
    wrap = ctk.CTkFrame(parent, corner_radius=10, fg_color="transparent")
    if columns and columns > 0:
        for col in range(columns):
            wrap.grid_columnconfigure(col, weight=1)
        for idx, char in enumerate(chars):
            ctk.CTkButton(
                wrap,
                text=char,
                width=30,
                height=28,
                command=lambda ch=char: _insert_special_char(entry, ch),
            ).grid(row=idx // columns, column=idx % columns, padx=3, pady=3, sticky="ew")
    else:
        for char in chars:
            ctk.CTkButton(
                wrap,
                text=char,
                width=28,
                height=26,
                command=lambda ch=char: _insert_special_char(entry, ch),
            ).pack(side="left", padx=2, pady=2)
    return wrap


class FlashcardsScreen(ctk.CTkFrame):
    FLASH_MODE_KEY = "flashcards"
    QUIZ_MODE_KEY = "quiz_1_of_3"
    QUIZ_ERROR_TEXT = {
        "FR": "Mauvais choix, reessaie !",
        "IT": "Scelta sbagliata, riprova!",
        "ES": "Eleccion incorrecta, intentalo de nuevo!",
        "EN": "Wrong choice, try again!",
    }

    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        okruh: str,
        on_back,
        progress_data: dict | None = None,
        mark_progress_dirty=None,
        asset_index: dict[str, dict[str, Path]] | None = None,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.on_back = on_back
        self.asset_index = asset_index or build_asset_index(ASSETS_ROOT)
        self.cards = build_flashcards(bundle, lang, okruh, self.asset_index[FLASH_OKRUH_TO_FOLDER[okruh]])
        self.order = list(range(len(self.cards)))
        self.index = 0
        self.revealed = False
        self.mode_var = ctk.StringVar(value="Flashcards")
        self.order_mode_var = ctk.StringVar(value="Slabé první")
        self.known_count = 0
        self.unknown_count = 0
        self.rated_item_ids: set[int] = set()
        self.current_photo: ctk.CTkImage | None = None
        self.quiz_choices: list[str] = []
        self.quiz_answered = False
        self.quiz_advance_job: str | None = None
        self.quiz_correct_count = 0
        self.quiz_wrong_attempts = 0
        self.quiz_incorrect_item_ids: set[int] = set()
        self.tts = SingleFlightTTS()

        self.user_id = user_id
        self.lang = lang
        self.okruh = okruh
        self.progress_data = progress_data
        self.mark_progress_dirty = mark_progress_dirty
        self.lang_menu_var = ctk.StringVar(value=_lang_menu_value(self.lang))

        self._build_ui()
        self.order = self._make_order()
        self._render()

    def set_context(self, user_id: str, lang: str, okruh: str) -> None:
        self.cleanup()
        self.user_id = user_id
        self.lang = lang
        self.okruh = okruh
        self.lang_menu_var.set(_lang_menu_value(self.lang))
        self.title_label.configure(text=f"{self.okruh} · {self.lang} · {self.user_id}")
        self.cards = build_flashcards(
            self.bundle,
            self.lang,
            self.okruh,
            self.asset_index[FLASH_OKRUH_TO_FOLDER[self.okruh]],
        )
        self._rebuild_order(reset_scores=True)

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        self.title_label = ctk.CTkLabel(
            top,
            text=f"{self.okruh} · {self.lang} · {self.user_id}",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.pack(side="left", padx=12, pady=12)
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)
        self.lang_menu = ctk.CTkOptionMenu(right, variable=self.lang_menu_var, values=LANG_MENU_VALUES, command=self._on_lang_changed)
        self.lang_menu.pack(side="left", padx=(0, 8))
        ctk.CTkSegmentedButton(
            right,
            values=["Slabé první", "Náhodně"],
            variable=self.order_mode_var,
            command=lambda _value: self._rebuild_order(reset_scores=False),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkSegmentedButton(
            right,
            values=["Flashcards", "Vyber 1 ze 3"],
            variable=self.mode_var,
            command=lambda _value: self._switch_mode(),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(right, text="Zpět do kokpitu", command=self._back).pack(side="left")

        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.progress_label = ctk.CTkLabel(main, text="Karta 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(12, 6))
        self.quiz_score_label = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.quiz_score_label.pack(anchor="w", padx=16, pady=(0, 6))
        self.image_label = ctk.CTkLabel(main, text="")
        self.image_label.pack(pady=(4, 8))
        self.cz_label = ctk.CTkLabel(main, text="CZ: -", font=ctk.CTkFont(size=22, weight="bold"))
        self.cz_label.pack(pady=(4, 4))
        self.target_label = ctk.CTkLabel(main, text="?", font=ctk.CTkFont(size=24))
        self.target_label.pack(pady=(4, 10))
        self.quiz_options_frame = ctk.CTkFrame(main, corner_radius=10, fg_color="transparent")
        self.quiz_options_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.quiz_buttons: list[ctk.CTkButton] = []
        self.quiz_button_font = ctk.CTkFont(size=24, weight="bold")
        for _ in range(3):
            btn = ctk.CTkButton(
                self.quiz_options_frame,
                text="-",
                command=lambda: None,
                height=64,
                font=self.quiz_button_font,
            )
            self.quiz_buttons.append(btn)
        self.quiz_summary_frame = ctk.CTkFrame(main, corner_radius=10)
        self.quiz_summary_title = ctk.CTkLabel(self.quiz_summary_frame, text="Shrnutí kola", font=ctk.CTkFont(size=18, weight="bold"))
        self.quiz_summary_title.pack(anchor="w", padx=12, pady=(10, 4))
        self.quiz_summary_body = ctk.CTkLabel(self.quiz_summary_frame, text="", justify="left", anchor="w")
        self.quiz_summary_body.pack(fill="x", padx=12, pady=(0, 12))

        self.flash_bottom = ctk.CTkFrame(self, corner_radius=12)
        self.flash_bottom.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(self.flash_bottom, text="Zobrazit překlad", command=self._reveal).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.flash_bottom, text="Přehrát výslovnost", command=self._speak_current).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.flash_bottom, text="Znám ✓", command=self._mark_known).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.flash_bottom, text="Neznám ✗", command=self._mark_unknown).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.flash_bottom, text="Další", command=self._next_card).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.flash_bottom, text="Zamíchat znovu", command=self._reshuffle).pack(side="left", padx=8, pady=10)
        self.quiz_bottom = ctk.CTkFrame(self, corner_radius=12)
        ctk.CTkButton(self.quiz_bottom, text="Přehrát výslovnost", command=self._speak_current).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(self.quiz_bottom, text="Zamíchat znovu", command=self._reshuffle).pack(side="left", padx=8, pady=10)
        self.quiz_repeat_btn = ctk.CTkButton(self.quiz_bottom, text="Opakovat chybné", command=self._repeat_incorrect_quiz)
        self.quiz_repeat_btn.pack(side="left", padx=8, pady=10)
        self.status_label = ctk.CTkLabel(self.flash_bottom, text="Připraveno.")
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
            if self.mode_var.get() == "Flashcards":
                self.target_label.configure(text=f"Znám: {self.known_count} | Neznám: {self.unknown_count}")
                self.quiz_score_label.configure(text="")
            else:
                self.target_label.configure(
                    text=f"Kolo dokončeno. Správně: {self.quiz_correct_count}/{len(self.order)}"
                )
                self.quiz_score_label.configure(
                    text=f"Průběžné skóre · Správně: {self.quiz_correct_count} · Chybné pokusy: {self.quiz_wrong_attempts}"
                )
                self.status_label.configure(
                    text=f"Chybné položky: {len(self.quiz_incorrect_item_ids)} | Chybné pokusy: {self.quiz_wrong_attempts}"
                )
                self.quiz_repeat_btn.configure(
                    state="normal" if self.quiz_incorrect_item_ids else "disabled"
                )
                self.quiz_summary_body.configure(
                    text=(
                        f"Správné odpovědi: {self.quiz_correct_count}/{len(self.order)}\n"
                        f"Chybné pokusy: {self.quiz_wrong_attempts}\n"
                        f"Chybné položky: {len(self.quiz_incorrect_item_ids)}"
                    )
                )
                self.quiz_summary_frame.pack(fill="x", padx=16, pady=(8, 10))
            self.image_label.configure(image=None, text="")
            self.current_photo = None
            self.quiz_options_frame.pack_forget()
            return
        self.progress_label.configure(text=f"Karta {self.index + 1}/{len(self.cards)}")
        self.cz_label.configure(text=f"CZ: {card.cz}")
        if self.mode_var.get() == "Flashcards":
            self.target_label.configure(text=card.target_text if self.revealed else "?")
            self.quiz_score_label.configure(text="")
            self.quiz_options_frame.pack_forget()
            self.quiz_summary_frame.pack_forget()
        else:
            self.target_label.configure(text="Vyber správný název")
            self.quiz_score_label.configure(
                text=f"Průběžné skóre · Správně: {self.quiz_correct_count} · Chybné pokusy: {self.quiz_wrong_attempts}"
            )
            self._render_quiz_options(card)
            self.quiz_summary_frame.pack_forget()
        canvas = self._build_display_image(card)
        self.current_photo = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=FLASH_IMAGE_SIZE)
        self.image_label.configure(image=self.current_photo, text="")

    def _make_order(self, item_ids: list[int] | None = None) -> list[int]:
        card_by_item_id = {card.item_id: idx for idx, card in enumerate(self.cards)}
        if item_ids is None:
            item_ids = [card.item_id for card in self.cards]
        item_ids = [item_id for item_id in item_ids if item_id in card_by_item_id]

        if self.order_mode_var.get() == "Slabé první":
            ordered_item_ids = rank_item_ids_by_weakness(
                user_id=self.user_id,
                item_ids=item_ids,
                data=self.progress_data,
            )
            return [card_by_item_id[item_id] for item_id in ordered_item_ids]

        order = [card_by_item_id[item_id] for item_id in item_ids]
        random.shuffle(order)
        return order

    def _rebuild_order(self, reset_scores: bool = True) -> None:
        self.order = self._make_order()
        self.index = 0
        self.revealed = False
        self.quiz_answered = False
        self.quiz_choices = []
        if reset_scores:
            self.rated_item_ids.clear()
            self.known_count = 0
            self.unknown_count = 0
            self.quiz_correct_count = 0
            self.quiz_wrong_attempts = 0
            self.quiz_incorrect_item_ids.clear()
        self._render()
        if self.order_mode_var.get() == "Slabé první":
            self.status_label.configure(text="Pořadí: slabé položky první.")
        else:
            self.status_label.configure(text="Pořadí: náhodně.")

    def _render_quiz_options(self, card) -> None:
        self.quiz_options_frame.pack(fill="x", padx=16, pady=(0, 10))
        for btn in self.quiz_buttons:
            btn.grid_forget()
            btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"], state="normal")
        if not self.quiz_choices:
            self.quiz_choices = self._build_quiz_choices(card)
        for idx, (btn, choice) in enumerate(zip(self.quiz_buttons, self.quiz_choices)):
            btn.configure(text=choice, command=lambda value=choice: self._answer_quiz(value))
            btn.grid(row=0, column=idx, padx=8, pady=6, sticky="ew")

    def _build_quiz_choices(self, card) -> list[str]:
        distractors = [c.target_text for c in self.cards if c.item_id != card.item_id and c.target_text != card.target_text]
        picked = random.sample(distractors, k=min(2, len(distractors)))
        choices = picked + [card.target_text]
        random.shuffle(choices)
        while len(choices) < 3:
            choices.append(card.target_text)
        return choices

    def _answer_quiz(self, choice: str) -> None:
        card = self._current_card()
        if card is None or self.quiz_answered:
            return
        if choice == card.target_text:
            self.quiz_answered = True
            self.quiz_correct_count += 1
            _record_event(
                self.progress_data,
                self.mark_progress_dirty,
                user_id=self.user_id,
                item_id=card.item_id,
                mode=self.QUIZ_MODE_KEY,
                okruh=self.okruh,
                lang=self.lang,
                correct=True,
            )
            for btn in self.quiz_buttons:
                if btn.cget("text") == choice:
                    btn.configure(fg_color="#16A34A", hover_color="#16A34A")
                else:
                    btn.configure(state="disabled")
            self.status_label.configure(text=f"Správně: {card.target_text}")
            self._speak_current()
            self.quiz_advance_job = self.after(1200, self._next_card)
            return
        self.quiz_wrong_attempts += 1
        self.quiz_incorrect_item_ids.add(card.item_id)
        _record_event(
            self.progress_data,
            self.mark_progress_dirty,
            user_id=self.user_id,
            item_id=card.item_id,
            mode=self.QUIZ_MODE_KEY,
            okruh=self.okruh,
            lang=self.lang,
            correct=False,
        )
        for btn in self.quiz_buttons:
            if btn.cget("text") == choice:
                btn.configure(fg_color="#DC2626", hover_color="#DC2626")
                break
        self.status_label.configure(
            text=f"{self.QUIZ_ERROR_TEXT.get(self.lang, 'Wrong choice, try again!')} ({self.quiz_wrong_attempts})"
        )

    def _reveal(self) -> None:
        if self.mode_var.get() != "Flashcards":
            return
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
            _record_event(
                self.progress_data,
                self.mark_progress_dirty,
                user_id=self.user_id,
                item_id=card.item_id,
                mode=self.FLASH_MODE_KEY,
                okruh=self.okruh,
                lang=self.lang,
                correct=True,
            )
        self._next_card()

    def _mark_unknown(self) -> None:
        card = self._current_card()
        if card and card.item_id not in self.rated_item_ids:
            self.rated_item_ids.add(card.item_id)
            self.unknown_count += 1
            _record_event(
                self.progress_data,
                self.mark_progress_dirty,
                user_id=self.user_id,
                item_id=card.item_id,
                mode=self.FLASH_MODE_KEY,
                okruh=self.okruh,
                lang=self.lang,
                correct=False,
            )
        self._next_card()

    def _next_card(self) -> None:
        if self.quiz_advance_job is not None:
            try:
                self.after_cancel(self.quiz_advance_job)
            except Exception:
                pass
            self.quiz_advance_job = None
        if self._current_card() is None:
            return
        self.index += 1
        self.revealed = False
        self.quiz_answered = False
        self.quiz_choices = []
        self._render()

    def _reshuffle(self) -> None:
        if self.quiz_advance_job is not None:
            try:
                self.after_cancel(self.quiz_advance_job)
            except Exception:
                pass
            self.quiz_advance_job = None
        self._rebuild_order(reset_scores=True)

    def _switch_mode(self) -> None:
        self.cleanup()
        self.revealed = False
        self.quiz_answered = False
        self.quiz_choices = []
        self.quiz_correct_count = 0
        self.quiz_wrong_attempts = 0
        self.quiz_incorrect_item_ids.clear()
        if self.mode_var.get() == "Flashcards":
            self.quiz_bottom.pack_forget()
            self.flash_bottom.pack(fill="x", padx=16, pady=(0, 16))
            self.status_label.pack_forget()
            self.status_label = ctk.CTkLabel(self.flash_bottom, text="Připraveno.")
            self.status_label.pack(side="right", padx=12, pady=10)
        else:
            self.flash_bottom.pack_forget()
            self.quiz_bottom.pack(fill="x", padx=16, pady=(0, 16))
            self.status_label.pack_forget()
            self.status_label = ctk.CTkLabel(self.quiz_bottom, text="Vyber správnou možnost.")
            self.status_label.pack(side="right", padx=12, pady=10)
            self.quiz_repeat_btn.configure(state="disabled")
        self._render()

    def _back(self) -> None:
        self.cleanup()
        self.on_back()

    def cleanup(self) -> None:
        if self.quiz_advance_job is not None:
            try:
                self.after_cancel(self.quiz_advance_job)
            except Exception:
                pass
            self.quiz_advance_job = None

    def destroy(self) -> None:
        self.cleanup()
        super().destroy()

    def _on_lang_changed(self, value: str) -> None:
        self.lang = _lang_code_from_menu(value)
        self.cards = build_flashcards(
            self.bundle,
            self.lang,
            self.okruh,
            self.asset_index[FLASH_OKRUH_TO_FOLDER[self.okruh]],
        )
        self._rebuild_order(reset_scores=True)
        self.title_label.configure(text=f"{self.okruh} · {self.lang} · {self.user_id}")
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang}.")

    def _repeat_incorrect_quiz(self) -> None:
        if not self.quiz_incorrect_item_ids:
            return
        incorrect_order = [
            idx for idx, card in enumerate(self.cards)
            if card.item_id in self.quiz_incorrect_item_ids
        ]
        if not incorrect_order:
            self.status_label.configure(text="Žádné chybné položky k opakování.")
            return
        incorrect_item_ids = [self.cards[idx].item_id for idx in incorrect_order]
        self.order = self._make_order(incorrect_item_ids)
        self.index = 0
        self.revealed = False
        self.quiz_answered = False
        self.quiz_choices = []
        self.quiz_correct_count = 0
        self.quiz_wrong_attempts = 0
        self.quiz_incorrect_item_ids.clear()
        self.quiz_repeat_btn.configure(state="disabled")
        self.status_label.configure(text="Opakování chybných položek.")
        self._render()


class ColorsScreen(ctk.CTkFrame):
    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        on_back,
        progress_data: dict | None = None,
        mark_progress_dirty=None,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.progress_data = progress_data
        self.mark_progress_dirty = mark_progress_dirty
        self.assets = build_assets(ASSETS_ROOT / "Colors")
        self.cards = build_color_cards(bundle, lang, self.assets)
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.current_photo: ImageTk.PhotoImage | None = None
        self.tts = SingleFlightTTS()
        self.autoplay_job: str | None = None
        self.autoplay_on = False
        self.lang_menu_var = ctk.StringVar(value=_lang_menu_value(self.lang))

        self._build_ui()
        self._render()

    def set_context(self, user_id: str, lang: str) -> None:
        self.cleanup()
        self.user_id = user_id
        self.lang = lang
        self.lang_menu_var.set(_lang_menu_value(self.lang))
        self.cards = build_color_cards(self.bundle, self.lang, self.assets)
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.title_label.configure(text=f"Barvy · {self.lang} · {self.user_id}")
        self._render()
        self.status_label.configure(text=f"Připraveno. TTS: {self.tts.backend}")

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        self.title_label = ctk.CTkLabel(top, text=f"Barvy · {self.lang} · {self.user_id}", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(side="left", padx=12, pady=12)
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)
        self.lang_menu = ctk.CTkOptionMenu(right, variable=self.lang_menu_var, values=LANG_MENU_VALUES, command=self._on_lang_changed)
        self.lang_menu.pack(side="left", padx=(0, 8))
        ctk.CTkButton(right, text="Zpět do kokpitu", command=self._back).pack(side="left")

        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.progress_label = ctk.CTkLabel(main, text="Barva 0/0", font=ctk.CTkFont(size=14, weight="bold"))
        self.progress_label.pack(anchor="w", padx=16, pady=(12, 6))
        self.image_wrap = tk.Frame(main, bd=0, highlightthickness=0, bg="#2b2b2b")
        self.image_wrap.pack(pady=(2, 4))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#2b2b2b")
        self.image_label.pack(pady=(2, 4))
        self.cz_label = ctk.CTkLabel(main, text="CZ: -", font=ctk.CTkFont(size=20, weight="bold"))
        self.cz_label.pack(pady=(2, 2))
        self.color_band = ctk.CTkFrame(main, width=320, height=28, corner_radius=8, fg_color="#d1d5db")
        self.color_band.pack(pady=(2, 4))
        self.target_label = ctk.CTkLabel(main, text="?", font=ctk.CTkFont(size=26))
        self.target_label.pack(pady=(2, 6))

        bottom = ctk.CTkFrame(self, corner_radius=12)
        bottom.pack(fill="x", padx=16, pady=(0, 12))
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
        img = ImageOps.contain(img, COLORS_DISPLAY_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", COLORS_DISPLAY_SIZE, (240, 240, 240))
        x = (COLORS_DISPLAY_SIZE[0] - img.size[0]) // 2
        y = (COLORS_DISPLAY_SIZE[1] - img.size[1]) // 2
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

    def cleanup(self) -> None:
        self._stop_autoplay()

    def _on_lang_changed(self, value: str) -> None:
        self.lang = _lang_code_from_menu(value)
        self.cards = build_color_cards(self.bundle, self.lang, self.assets)
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.title_label.configure(text=f"Barvy · {self.lang} · {self.user_id}")
        self._render()
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang}. TTS: {self.tts.backend}")

    def destroy(self) -> None:
        self.cleanup()
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
        self.progress_label.pack(anchor="w", padx=16, pady=(8, 4))

        self.image_wrap = tk.Frame(self, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_wrap.pack(pady=(2, 4))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_label.pack()

        self.cz_label = ctk.CTkLabel(self, text="CZ: -", font=ctk.CTkFont(size=20, weight="bold"))
        self.cz_label.pack(pady=(3, 1))
        self.target_label = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=28))
        self.target_label.pack(pady=(1, 4))

        btns = ctk.CTkFrame(self, corner_radius=10)
        btns.pack(fill="x", padx=24, pady=4)
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
        self.progress_label.pack(anchor="w", padx=16, pady=(8, 4))

        self.image_wrap = tk.Frame(self, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_wrap.pack(pady=(2, 4))
        self.image_label = tk.Label(self.image_wrap, bd=0, highlightthickness=0, bg="#d1d5db")
        self.image_label.pack()

        self.cz_label = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=22, weight="bold"))
        self.cz_label.pack(pady=(4, 2))

        entry_wrap = ctk.CTkFrame(self, corner_radius=10)
        entry_wrap.pack(fill="x", padx=24, pady=4)
        self.entry = tk.Entry(entry_wrap, width=28, relief="flat", highlightthickness=1, bd=0)
        self.entry.pack(side="left", padx=12, pady=12)
        ctk.CTkButton(entry_wrap, text="Kontrola", command=self.check_answer).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(entry_wrap, text="Přehrát", command=self.master_screen.speak_current_month).pack(side="left", padx=8, pady=12)

        self.result_label = ctk.CTkLabel(entry_wrap, text="", font=ctk.CTkFont(size=16, weight="bold"), width=300, anchor="w")
        self.result_label.pack(side="left", padx=10, pady=12)

        self.diacritic_bar = _build_diacritic_bar(self, self.master_screen.lang, self.entry)
        if self.diacritic_bar is not None:
            self.diacritic_bar.pack(anchor="w", padx=24, pady=(0, 4))

        nav = ctk.CTkFrame(self, corner_radius=10)
        nav.pack(fill="x", padx=24, pady=4)
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
        if self.diacritic_bar is not None:
            self.diacritic_bar.destroy()
        self.diacritic_bar = _build_diacritic_bar(self, self.master_screen.lang, self.entry)
        if self.diacritic_bar is not None:
            self.diacritic_bar.pack(anchor="w", padx=24, pady=(0, 4))

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
            _record_event(
                self.master_screen.progress_data,
                self.master_screen.mark_progress_dirty,
                user_id=self.master_screen.user_id,
                item_id=card.item_id,
                mode=self.master_screen.WRITING_MODE_KEY,
                okruh=MONTHS_OKRUH,
                lang=self.master_screen.lang,
                correct=True,
            )
            return
        if edit_distance(answer, target) <= 1:
            self.result_label.configure(text=f"Skoro! Správně: {expected}", text_color="#D97706")
            self.master_screen.set_status(f"Skoro správně: {card.cz} -> {expected}")
            return

        self.result_label.configure(text=f"Chyba: {user_text} -> {expected}", text_color="#DC2626")
        self.master_screen.set_status(f"Chyba: {card.cz} -> {expected}")
        _record_event(
            self.master_screen.progress_data,
            self.master_screen.mark_progress_dirty,
            user_id=self.master_screen.user_id,
            item_id=card.item_id,
            mode=self.master_screen.WRITING_MODE_KEY,
            okruh=MONTHS_OKRUH,
            lang=self.master_screen.lang,
            correct=False,
        )

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
    SLIDESHOW_MODE_KEY = "months_slideshow"
    WRITING_MODE_KEY = "months_writing"

    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        on_back,
        progress_data: dict | None = None,
        mark_progress_dirty=None,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.progress_data = progress_data
        self.mark_progress_dirty = mark_progress_dirty
        self.cards = build_months(bundle)
        self.assets = build_assets(MONTHS_ASSETS_DIR)
        self.index = 0
        self.mode_var = ctk.StringVar(value="Slideshow")
        self.lang_menu_var = ctk.StringVar(value=_lang_menu_value(self.lang))
        self.tts = SingleFlightTTS()
        self.is_leaving = False
        self.active_pane: MonthsSlideshowPane | MonthsWritingPane | None = None

        self._build_ui()
        self._switch_mode()

    def set_context(self, user_id: str, lang: str) -> None:
        self.cleanup()
        self.user_id = user_id
        self.lang = lang
        self.index = 0
        self.lang_menu_var.set(_lang_menu_value(self.lang))
        self.title_label.configure(text=f"Měsíce · {self.lang} · {self.user_id}")
        if self.active_pane is not None:
            self.active_pane.refresh()
        self.set_status(f"Připraveno. Jazyk: {self.lang}.")

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
        self.lang_menu = ctk.CTkOptionMenu(right, variable=self.lang_menu_var, values=LANG_MENU_VALUES, command=self._on_lang_changed)
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
            return
        _record_seen(
            self.progress_data,
            self.mark_progress_dirty,
            user_id=self.user_id,
            item_id=card.item_id,
            mode=self.SLIDESHOW_MODE_KEY,
            okruh=MONTHS_OKRUH,
            lang=self.lang,
        )

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
        self.lang = _lang_code_from_menu(value)
        self.title_label.configure(text=f"Měsíce · {self.lang} · {self.user_id}")
        if self.active_pane is not None:
            self.active_pane.refresh()
        self.set_status(f"Jazyk přepnut na {self.lang}.")

    def _back(self) -> None:
        if self.is_leaving:
            return
        self.is_leaving = True
        self.cleanup()
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass
        self.is_leaving = False
        self.on_back()

    def cleanup(self) -> None:
        if self.active_pane is not None:
            self.active_pane.cleanup()
        self.is_leaving = False

    def destroy(self) -> None:
        self.cleanup()
        super().destroy()


class NumbersScreen(ctk.CTkFrame):
    NUMBERS_MODE_KEY = "numbers_reading"

    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        on_back,
        progress_data: dict | None = None,
        mark_progress_dirty=None,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.user_id = user_id
        self.lang = lang
        self.on_back = on_back
        self.progress_data = progress_data
        self.mark_progress_dirty = mark_progress_dirty
        self.cards = build_numbers(bundle)
        self.order_mode = ctk.StringVar(value="Náhodně")
        self.order = list(range(len(self.cards)))
        random.shuffle(self.order)
        self.index = 0
        self.revealed = False
        self.tts = SingleFlightTTS()
        self.autoplay_on = False
        self.autoplay_job: str | None = None
        self.lang_menu_var = ctk.StringVar(value=_lang_menu_value(self.lang))

        self._build_ui()
        self._render()

    def set_context(self, user_id: str, lang: str) -> None:
        self.cleanup()
        self.user_id = user_id
        self.lang = lang
        self.index = 0
        self.revealed = False
        self.lang_menu_var.set(_lang_menu_value(self.lang))
        self.title_label.configure(text=f"Číslovky · {self.lang} · {self.user_id}")
        self._render()
        self.status_label.configure(text=f"Připraveno. Jazyk: {self.lang}.")

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        self.title_label = ctk.CTkLabel(
            top,
            text=f"Číslovky · {self.lang} · {self.user_id}",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.pack(side="left", padx=12, pady=12)

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)
        self.order_menu = ctk.CTkOptionMenu(right, values=["Náhodně", "Vzestupně"], command=self._on_order_changed)
        self.order_menu.set(self.order_mode.get())
        self.order_menu.pack(side="left", padx=(0, 8))
        self.lang_menu = ctk.CTkOptionMenu(right, variable=self.lang_menu_var, values=LANG_MENU_VALUES, command=self._on_lang_changed)
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
        card = self._current_card()
        if card is None:
            return
        self.revealed = True
        _record_seen(
            self.progress_data,
            self.mark_progress_dirty,
            user_id=self.user_id,
            item_id=card.item_id,
            mode=self.NUMBERS_MODE_KEY,
            okruh=NUMBERS_OKRUH,
            lang=self.lang,
        )
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
        self.lang = _lang_code_from_menu(value)
        self.title_label.configure(text=f"Číslovky · {self.lang} · {self.user_id}")
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

    def cleanup(self) -> None:
        self._stop_autoplay()

    def destroy(self) -> None:
        self.cleanup()
        super().destroy()


class WeekdaysScreen(ctk.CTkFrame):
    SEQUENCE_MODE_KEY = "weekdays_sequence"
    WRITING_MODE_KEY = "weekdays_writing"

    def __init__(
        self,
        master,
        bundle: DataBundle,
        user_id: str,
        lang: str,
        on_back,
        progress_data: dict | None = None,
        mark_progress_dirty=None,
    ) -> None:
        super().__init__(master, corner_radius=0)
        self.bundle = bundle
        self.on_back = on_back
        self.progress_data = progress_data
        self.mark_progress_dirty = mark_progress_dirty
        self.cards = build_weekdays(bundle)
        self.color_options = color_name_map(bundle)
        self.tts = SingleFlightTTS()
        self.sequence_job: str | None = None
        self.sequence_running = False
        self.sequence_index = 0
        self.sequence_controls_job: str | None = None
        self.sequence_controls_locked = False
        self.seq_prev_btn = None
        self.seq_play_btn = None
        self.seq_next_btn = None
        self.seq_auto_btn = None
        self.write_rows: dict[int, dict[str, object]] = {}
        self.write_after_ids: list[str] = []
        self.write_frame: ctk.CTkFrame | None = None
        self.is_leaving = False
        self.current_user_id = user_id
        self.lang = lang
        self.mode_var = ctk.StringVar(value="Barvy dnů")
        self.lang_var = ctk.StringVar(value=_lang_menu_value(self.lang))
        self.day_colors = self._build_day_colors(user_id)

        self._build_ui()
        self._render_mode()

    def set_context(self, user_id: str, lang: str) -> None:
        self.cleanup()
        self.current_user_id = user_id
        self.lang = lang
        self.user_var.set(self.current_user_id)
        self.lang_var.set(_lang_menu_value(self.lang))
        self.mode_var.set("Barvy dnů")
        self.day_colors = self._build_day_colors(self.current_user_id)
        self._render_mode()
        self.status_label.configure(text="Připraveno. Nastav barvy dnů nebo spusť sekvenci.")

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
        top.pack(fill="x", padx=16, pady=(8, 6))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.user_var = ctk.StringVar(value=self.current_user_id)
        self._add_selector(top, 0, "Uživatel", self.user_var, [u.user_id for u in self.bundle.users if u.active], self._on_user_changed)
        self._add_selector(top, 1, "Jazyk", self.lang_var, LANG_MENU_VALUES, self._on_lang_changed)

        mode_wrap = ctk.CTkFrame(top, corner_radius=8)
        mode_wrap.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(mode_wrap, text="Režim").pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkSegmentedButton(
            mode_wrap,
            values=["Barvy dnů", "Sekvence", "Psaní"],
            variable=self.mode_var,
            command=lambda _value: self._render_mode(),
        ).pack(fill="x", padx=8, pady=(0, 8))

        nav_wrap = ctk.CTkFrame(top, corner_radius=8)
        nav_wrap.grid(row=0, column=3, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(nav_wrap, text=" ").pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkButton(nav_wrap, text="Null", width=88, command=self._reset_weekdays_progress).pack(
            fill="x", padx=8, pady=(0, 6)
        )
        ctk.CTkButton(nav_wrap, text="Zpět do kokpitu", command=self._back).pack(fill="x", padx=8, pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="Připraveno. Nastav barvy dnů nebo spusť sekvenci.", font=ctk.CTkFont(size=13))
        self.status_label.pack(fill="x", padx=20, pady=(0, 4))
        self.content = ctk.CTkFrame(self, corner_radius=12)
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 8))

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
        self.seq_prev_btn = None
        self.seq_play_btn = None
        self.seq_next_btn = None
        self.seq_auto_btn = None
        self.write_frame = None
        self.write_rows = {}
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
            ctk.CTkLabel(row, text=card.target_text(_lang_code_from_menu(self.lang_var.get())), width=180, anchor="w").pack(side="right", padx=12, pady=10)
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
        frame = ctk.CTkFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.write_frame = frame
        ctk.CTkLabel(frame, text="Psaní s kontrolou", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=8, pady=(2, 4))
        self.write_rows = {}
        for card in self.cards:
            row = ctk.CTkFrame(frame, corner_radius=10)
            row.pack(fill="x", padx=8, pady=2)
            color_hex = self.day_colors[card.item_id]
            swatch = ctk.CTkFrame(row, width=18, height=38, corner_radius=6, fg_color=color_hex)
            swatch.pack(side="left", padx=(10, 8), pady=4)
            ctk.CTkLabel(row, text=card.cz, width=105, anchor="w", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=(0, 6), pady=4)
            actions = ctk.CTkFrame(row, corner_radius=8, fg_color="transparent")
            actions.pack(side="right", padx=(6, 10), pady=4, fill="y")
            ctk.CTkButton(actions, text="Kontrola", width=84, command=lambda c=card: self._check_write_answer(c)).pack(anchor="center", expand=True)
            result = ctk.CTkLabel(actions, text="", width=160, anchor="e", justify="right")
            result.pack(anchor="e")
            input_wrap = ctk.CTkFrame(row, corner_radius=8, fg_color="transparent")
            input_wrap.pack(side="left", fill="x", expand=True, padx=4, pady=2)
            entry = tk.Entry(input_wrap, width=18, relief="flat", highlightthickness=1, bd=0)
            entry.pack(side="left", padx=(2, 6), pady=1)
            diacritic_bar = _build_diacritic_bar(input_wrap, self.lang, entry)
            if diacritic_bar is not None:
                diacritic_bar.pack(side="left", padx=0, pady=0)
            self.write_rows[card.item_id] = {"entry": entry, "result": result, "diacritic_bar": diacritic_bar}

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

    def _reset_weekdays_progress(self) -> None:
        try:
            _reset_okruh_progress(
                self.progress_data,
                self.mark_progress_dirty,
                user_id=self.current_user_id,
                okruh=WEEKDAYS_OKRUH,
            )
        except Exception as exc:
            self.status_label.configure(text=f"Vynulování progresu selhalo: {exc}")
            return
        self.status_label.configure(text=f"Progres okruhu 'Dny v týdnu' byl vynulován pro '{self.current_user_id}'.")

    def _render_sequence_card(self) -> None:
        card = self.cards[self.sequence_index]
        self.seq_progress.configure(text=f"Den {self.sequence_index + 1}/{len(self.cards)}")
        self.seq_card.configure(fg_color=self.day_colors.get(card.item_id, DEFAULT_DAY_COLORS[self.sequence_index]))
        self.seq_target_label.configure(text=card.target_text(_lang_code_from_menu(self.lang_var.get())))
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
        card = self.cards[self.sequence_index]
        self._speak_text(card.target_text(_lang_code_from_menu(self.lang_var.get())))
        _record_seen(
            self.progress_data,
            self.mark_progress_dirty,
            user_id=self.current_user_id,
            item_id=card.item_id,
            mode=self.SEQUENCE_MODE_KEY,
            okruh=WEEKDAYS_OKRUH,
            lang=_lang_code_from_menu(self.lang_var.get()),
        )

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
        if self.mode_var.get() == "Sekvence" and _widget_alive(self.seq_auto_btn):
            try:
                self.seq_auto_btn.configure(text="Auto ON")
            except Exception:
                pass
            self._unlock_sequence_controls()
        else:
            self.sequence_controls_locked = False

    def _check_write_answer(self, card: WeekdayCard) -> None:
        row = self.write_rows[card.item_id]
        entry = row["entry"]
        result = row["result"]
        user_text = entry.get().strip()
        expected = card.target_text(_lang_code_from_menu(self.lang_var.get()))
        answer = normalize_answer(user_text)
        target = normalize_answer(expected)
        if answer == target:
            result.configure(text=f"Správně: {expected}", text_color="#16A34A")
            self._speak_text(expected)
            _record_event(
                self.progress_data,
                self.mark_progress_dirty,
                user_id=self.current_user_id,
                item_id=card.item_id,
                mode=self.WRITING_MODE_KEY,
                okruh=WEEKDAYS_OKRUH,
                lang=_lang_code_from_menu(self.lang_var.get()),
                correct=True,
            )
            return
        if user_text and edit_distance(answer, target) <= 1:
            result.configure(text=f"Skoro! Správně: {expected}", text_color="#D97706")
            return
        result.configure(text=f"Chyba: {user_text} -> {expected}", text_color="#DC2626")
        _record_event(
            self.progress_data,
            self.mark_progress_dirty,
            user_id=self.current_user_id,
            item_id=card.item_id,
            mode=self.WRITING_MODE_KEY,
            okruh=WEEKDAYS_OKRUH,
            lang=_lang_code_from_menu(self.lang_var.get()),
            correct=False,
        )
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
        self.lang = _lang_code_from_menu(value)
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
                    if btn.winfo_exists():
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
        if self.mode_var.get() != "Barvy dnů":
            self._cancel_pending_jobs()
            try:
                self.content.focus_set()
            except Exception:
                pass
            try:
                self.winfo_toplevel().focus_set()
            except Exception:
                pass
            self.mode_var.set("Barvy dnů")
            self.status_label.configure(text="Aktivní režim ukončen. Pro návrat do kokpitu klikni znovu.")
            return
        self.is_leaving = True
        self._cancel_pending_jobs()
        try:
            self.content.focus_set()
        except Exception:
            pass
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass
        self.after(75, self._finish_back)

    def _finish_back(self) -> None:
        self.is_leaving = False
        self.on_back()

    def cleanup(self) -> None:
        self._cancel_pending_jobs()
        self.is_leaving = False

    def destroy(self) -> None:
        self.cleanup()
        super().destroy()
