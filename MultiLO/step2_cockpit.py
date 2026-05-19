"""Step 2: MultiLO cockpit (dashboard) skeleton in CustomTkinter."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import time

from PIL import Image, ImageDraw, ImageOps
from app_paths import resolve_assets_root, resolve_cockpit_icon_dir, resolve_data_dir
from data_layer import DataBundle, load_data
from multilo_core import build_asset_index
from screen_frames import ColorsScreen, FlashcardsScreen, MonthsScreen, NumbersScreen, WeekdaysScreen
from storage import load_progress, save_progress, summarize_progress_by_okruh


try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    print("Missing dependency: customtkinter")
    print("Install with: python3 -m pip install customtkinter")
    raise SystemExit(1) from exc


APP_TITLE = "MultiLO - Cockpit (Step 2)"
DEBUG_TIMING = False
LANG_OPTIONS = ["FR", "IT", "ES", "EN"]
LANG_FLAGS = {
    "FR": "🇫🇷",
    "IT": "🇮🇹",
    "ES": "🇪🇸",
    "EN": "🇬🇧",
}
LANG_MENU_VALUES = [f"{LANG_FLAGS[code]}  {code}" for code in LANG_OPTIONS]
FLASHCARD_OKRUHY = {"Zelenina a ovoce", "Zvířata", "Ptáci", "Rostliny"}
COLORS_OKRUH = "Základní barvy"
WEEKDAYS_OKRUH = "Dny v týdnu"
MONTHS_OKRUH = "Měsíce v roce"
NUMBERS_OKRUH = "Číslovky"
NONCACHED_SCREEN_KEYS = {"flashcards", "colors", "numbers", "weekdays", "months"}
ICON_SIZE = (112, 112)
ICON_TOP_PADDING = 10
COCKPIT_ICON_DIR = resolve_cockpit_icon_dir()
COCKPIT_ICON_FILES = {
    "Číslovky": "Cockpi_Numbers.png",
    "Základní barvy": "Cockpit_Colors.png",
    "Dny v týdnu": "Cockpit_Week.png",
    "Měsíce v roce": "Cockpit_Months.png",
    "Zelenina a ovoce": "Cockpit_FruitVeget.png",
    "Zvířata": "Cockpit_Animals.png",
    "Ptáci": "Cockpit_Birds.png",
    "Rostliny": "Cockpit_Plants.png",
}
OKRUH_COLORS = {
    "Číslovky": ("#F59E0B", "#78350F"),
    "Základní barvy": ("#06B6D4", "#164E63"),
    "Dny v týdnu": ("#8B5CF6", "#4C1D95"),
    "Měsíce v roce": ("#F97316", "#7C2D12"),
    "Zelenina a ovoce": ("#22C55E", "#14532D"),
    "Zvířata": ("#EF4444", "#7F1D1D"),
    "Ptáci": ("#0EA5E9", "#0C4A6E"),
    "Rostliny": ("#10B981", "#064E3B"),
}


class CockpitApp(ctk.CTk):
    def __init__(self, bundle: DataBundle) -> None:
        super().__init__()
        self.bundle = bundle
        self.okruh_counts = Counter(item.okruh for item in bundle.vocab)
        self.item_okruh_map = {item.item_id: item.okruh for item in bundle.vocab}
        self.okruhy = sorted(self.okruh_counts.keys())
        self.selected_okruh: str | None = None
        self.okruh_buttons: dict[str, ctk.CTkButton] = {}
        self.start_btn: ctk.CTkButton | None = None
        self.user_menu: ctk.CTkOptionMenu | None = None
        self.progress_title_label: ctk.CTkLabel | None = None
        self.progress_body_label: ctk.CTkLabel | None = None
        self.progress_bar: ctk.CTkProgressBar | None = None
        self.progress_stats_label: ctk.CTkLabel | None = None
        self._has_usable_user = any(u.active for u in self.bundle.users)
        self.home_widgets: list[ctk.CTkBaseClass] = []
        self.active_screen: ctk.CTkFrame | None = None
        self.screen_cache: dict[str, ctk.CTkFrame] = {}
        self.tile_images: dict[str, ctk.CTkImage] = {}
        self.flash_asset_index = build_asset_index(resolve_assets_root())
        self.progress_data = load_progress()
        self.progress_dirty = False

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1060x720")
        self.minsize(980, 660)
        self.configure(fg_color=("#EEF2FF", "#0F172A"))

        self.stage = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.stage.pack(fill="both", expand=True)
        self.stage.grid_rowconfigure(0, weight=1)
        self.stage.grid_columnconfigure(0, weight=1)
        self.home_frame = ctk.CTkFrame(self.stage, corner_radius=0, fg_color="transparent")
        self.home_frame.grid(row=0, column=0, sticky="nsew")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._show_cockpit()
        self.after(120, self._bring_to_front)

    def _debug_timing(self, label: str, started_at: float) -> None:
        if not DEBUG_TIMING:
            return
        print(f"[DEBUG] {label}: {time.perf_counter() - started_at:.3f}s")

    def _debug(self, message: str) -> None:
        if DEBUG_TIMING:
            print(f"[DEBUG] {message}")

    def _defer_show_cockpit(self) -> None:
        started_at = time.perf_counter()
        old_screen = self.active_screen
        if old_screen is not None:
            cleanup = getattr(old_screen, "cleanup", None)
            if callable(cleanup):
                try:
                    cleanup()
                except Exception:
                    pass
            try:
                old_screen.grid_remove()
            except Exception:
                pass
        self.active_screen = None
        self.flush_progress_if_dirty()
        self._debug_timing("back_to_cockpit_prepare", started_at)
        self.after_idle(self._show_cockpit)

    def mark_progress_dirty(self) -> None:
        self.progress_dirty = True

    def flush_progress_if_dirty(self) -> None:
        if not self.progress_dirty:
            return
        started_at = time.perf_counter()
        save_progress(self.progress_data)
        self.progress_dirty = False
        self._debug_timing("flush_progress", started_at)

    def _on_close(self) -> None:
        try:
            self.flush_progress_if_dirty()
        finally:
            self.destroy()

    def _clear_home(self) -> None:
        while self.home_widgets:
            widget = self.home_widgets.pop()
            try:
                widget.destroy()
            except Exception:
                pass

    def _show_cockpit(self) -> None:
        started_at = time.perf_counter()
        self._clear_home()
        self._build_header()
        self._build_selectors()
        self._build_main_area()
        self._build_footer()
        if self.okruhy:
            self._set_selected_okruh(self.okruhy[0])
        self._refresh_progress_view()
        self.home_frame.tkraise()
        self._debug_timing("show_cockpit", started_at)

    def _open_screen(self, screen: ctk.CTkFrame) -> None:
        started_at = time.perf_counter()
        self.active_screen = screen
        self.active_screen.grid(row=0, column=0, sticky="nsew")
        self.active_screen.tkraise()
        self._debug_timing(f"open_screen:{type(screen).__name__}", started_at)

    def _show_cached_screen(self, key: str, factory, *context_args) -> None:
        started_at = time.perf_counter()
        if self.active_screen is not None and self.active_screen is not self.screen_cache.get(key):
            cleanup = getattr(self.active_screen, "cleanup", None)
            if callable(cleanup):
                try:
                    cleanup()
                except Exception:
                    pass
            try:
                self.active_screen.grid_remove()
            except Exception:
                pass
            self.active_screen = None

        screen = self.screen_cache.get(key)
        if key in NONCACHED_SCREEN_KEYS and screen is not None:
            cleanup = getattr(screen, "cleanup", None)
            if callable(cleanup):
                try:
                    cleanup()
                except Exception:
                    pass
            try:
                screen.destroy()
            except Exception:
                pass
            screen = None
            self.screen_cache.pop(key, None)
        if screen is None:
            factory_started = time.perf_counter()
            screen = factory()
            self._debug_timing(f"construct_screen:{key}", factory_started)
            self.screen_cache[key] = screen
        else:
            set_context = getattr(screen, "set_context", None)
            if callable(set_context):
                context_started = time.perf_counter()
                set_context(*context_args)
                self._debug_timing(f"set_context:{key}", context_started)
        self._open_screen(screen)
        self._debug_timing(f"show_screen_total:{key}", started_at)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.home_frame, corner_radius=18, fg_color=("#DCEAFE", "#172554"))
        header.pack(fill="x", padx=16, pady=(12, 8))
        self.home_widgets.append(header)

        title = ctk.CTkLabel(
            header,
            text="MultiLO - Jazykový trenér",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(anchor="w", padx=18, pady=(12, 2))

        subtitle = ctk.CTkLabel(
            header,
            text="Vyber uživatele, jazyk a okruh. Režim zvolíš uvnitř modulu. Pokrok se počítá průběžně.",
            font=ctk.CTkFont(size=14),
        )
        subtitle.pack(anchor="w", padx=18, pady=(0, 12))

    def _build_selectors(self) -> None:
        row = ctk.CTkFrame(self.home_frame, corner_radius=16, fg_color=("#E2E8F0", "#111827"))
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.home_widgets.append(row)

        row.grid_columnconfigure((0, 1), weight=1)

        user_values = [f"{u.user_id} - {u.display_name}" for u in self.bundle.users if u.active]
        if not user_values:
            user_values = ["<no active users>"]

        self.user_var = ctk.StringVar(value=user_values[0])
        self.lang_var = ctk.StringVar(value=self._lang_menu_value(LANG_OPTIONS[0]))

        self.user_menu = self._selector_block(
            row,
            0,
            "Uživatel",
            self.user_var,
            user_values,
            command=lambda _value: self._refresh_progress_view(),
        )
        self._selector_block(
            row,
            1,
            "Cílový jazyk",
            self.lang_var,
            LANG_MENU_VALUES,
            command=self._on_lang_changed,
        )

        if not self._has_usable_user and self.user_menu is not None:
            self.user_menu.configure(state="disabled")

    def _selector_block(
        self,
        parent: ctk.CTkFrame,
        col: int,
        label: str,
        variable: ctk.StringVar,
        values: list[str],
        command=None,
    ) -> ctk.CTkOptionMenu:
        block = ctk.CTkFrame(parent, corner_radius=14, fg_color=("#F8FAFC", "#1F2937"))
        block.grid(row=0, column=col, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(block, text=label, font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=10, pady=(6, 3)
        )
        menu = ctk.CTkOptionMenu(block, variable=variable, values=values, command=command)
        menu.pack(fill="x", padx=10, pady=(0, 8))
        return menu

    def _build_main_area(self) -> None:
        wrap = ctk.CTkFrame(self.home_frame, corner_radius=18, fg_color=("#E2E8F0", "#111827"))
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.home_widgets.append(wrap)
        wrap.grid_columnconfigure(0, weight=3)
        wrap.grid_columnconfigure(1, weight=2)
        wrap.grid_rowconfigure(0, weight=1)

        tiles_wrap = ctk.CTkFrame(wrap, corner_radius=18, fg_color=("#F8FAFC", "#0F172A"))
        tiles_wrap.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        ctk.CTkLabel(
            tiles_wrap,
            text="Okruhy",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 8))

        grid = ctk.CTkFrame(tiles_wrap, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = 4
        for col in range(cols):
            grid.grid_columnconfigure(col, weight=1)

        for idx, okruh in enumerate(self.okruhy):
            r = idx // cols
            c = idx % cols
            btn = ctk.CTkButton(
                grid,
                text=self._tile_text(okruh),
                image=self._tile_image(okruh),
                compound="top",
                height=168,
                corner_radius=18,
                anchor="center",
                font=ctk.CTkFont(size=15, weight="bold"),
                command=lambda o=okruh: self._set_selected_okruh(o),
            )
            btn.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            self.okruh_buttons[okruh] = btn

        progress_wrap = ctk.CTkFrame(wrap, corner_radius=18, fg_color=("#F8FAFC", "#0F172A"))
        progress_wrap.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        ctk.CTkLabel(
            progress_wrap,
            text="Pokrok",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 8))
        self.progress_title_label = ctk.CTkLabel(
            progress_wrap,
            text="Vyber okruh",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.progress_title_label.pack(anchor="w", padx=12, pady=(8, 6))
        self.progress_bar = ctk.CTkProgressBar(progress_wrap, height=18, corner_radius=999)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 10))
        self.progress_bar.set(0)
        self.progress_stats_label = ctk.CTkLabel(
            progress_wrap,
            text="",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.progress_stats_label.pack(fill="x", padx=12, pady=(0, 8))
        self.progress_body_label = ctk.CTkLabel(
            progress_wrap,
            text="",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14),
        )
        self.progress_body_label.pack(fill="x", padx=12, pady=(0, 12))

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self.home_frame, corner_radius=16, fg_color=("#DBEAFE", "#172554"))
        footer.pack(fill="x", padx=16, pady=(0, 12))
        self.home_widgets.append(footer)

        self.status_label = ctk.CTkLabel(
            footer,
            text="Připraveno. Vyber okruh a stiskni Start.",
            font=ctk.CTkFont(size=13),
        )
        self.status_label.pack(side="left", padx=12, pady=9)

        self.start_btn = ctk.CTkButton(
            footer,
            text="Start",
            width=120,
            command=self._on_start,
        )
        self.start_btn.pack(side="right", padx=12, pady=9)

        if not self._has_usable_user:
            self.status_label.configure(
                text="Chyba: nejsou dostupné aktivní uživatelské profily."
            )
            self.start_btn.configure(state="disabled")

    def _set_selected_okruh(self, okruh: str) -> None:
        self.selected_okruh = okruh
        for key, btn in self.okruh_buttons.items():
            if key == okruh:
                btn.configure(fg_color=("gray75", "gray30"))
            else:
                btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        self.status_label.configure(text=f"Vybraný okruh: {okruh}")
        self._refresh_progress_view()

    def _selected_user_id(self) -> str:
        return self.user_var.get().split(" - ", 1)[0]

    def _lang_menu_value(self, code: str) -> str:
        return f"{LANG_FLAGS[code]}  {code}"

    def _selected_lang_code(self) -> str:
        value = self.lang_var.get().strip()
        return value[-2:] if len(value) >= 2 else LANG_OPTIONS[0]

    def _on_lang_changed(self, value: str) -> None:
        code = value[-2:] if len(value) >= 2 else LANG_OPTIONS[0]
        self.status_label.configure(text=f"Vybraný jazyk: {code}")

    def _tile_text(self, okruh: str) -> str:
        count = self.okruh_counts[okruh]
        return f"{okruh}\n{count} položek"

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
        return slug.strip("_")

    def _generate_fallback_icon(self, okruh: str) -> Image.Image:
        primary, secondary = OKRUH_COLORS.get(okruh, ("#3B82F6", "#1E293B"))
        img = Image.new("RGB", ICON_SIZE, primary)
        draw = ImageDraw.Draw(img)
        for y in range(ICON_SIZE[1]):
            mix = y / max(ICON_SIZE[1] - 1, 1)
            r1, g1, b1 = tuple(int(primary[i : i + 2], 16) for i in (1, 3, 5))
            r2, g2, b2 = tuple(int(secondary[i : i + 2], 16) for i in (1, 3, 5))
            color = (
                int(r1 + (r2 - r1) * mix),
                int(g1 + (g2 - g1) * mix),
                int(b1 + (b2 - b1) * mix),
            )
            draw.line([(0, y), (ICON_SIZE[0], y)], fill=color)
        draw.rounded_rectangle((8, 8, 104, 104), radius=24, outline="#F8FAFC", width=3)
        initials = "".join(part[0] for part in okruh.split()[:2]).upper()
        if okruh == "Číslovky":
            initials = "12"
        elif okruh == "Základní barvy":
            initials = "C"
        elif okruh == "Zvířata":
            initials = "Z"
        elif okruh == "Ptáci":
            initials = "P"
        elif okruh == "Rostliny":
            initials = "R"
        elif okruh == "Měsíce v roce":
            initials = "M"
        elif okruh == "Dny v týdnu":
            initials = "D"
        elif okruh == "Zelenina a ovoce":
            initials = "OZ"
        draw.text((ICON_SIZE[0] / 2, ICON_SIZE[1] / 2), initials, anchor="mm", fill="#F8FAFC")
        return img

    def _tile_image(self, okruh: str) -> ctk.CTkImage:
        if okruh in self.tile_images:
            return self.tile_images[okruh]
        image_path = None
        mapped_name = COCKPIT_ICON_FILES.get(okruh)
        if mapped_name is not None:
            candidate = COCKPIT_ICON_DIR / mapped_name
            if candidate.exists():
                image_path = candidate
        if image_path is not None:
            with Image.open(image_path) as raw:
                image = raw.convert("RGBA")
        else:
            image = self._generate_fallback_icon(okruh).convert("RGBA")
        fitted = ImageOps.contain(image, (ICON_SIZE[0], ICON_SIZE[1] - ICON_TOP_PADDING), method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
        x = (ICON_SIZE[0] - fitted.size[0]) // 2
        y = ICON_TOP_PADDING + (ICON_SIZE[1] - ICON_TOP_PADDING - fitted.size[1]) // 2
        canvas.paste(fitted, (x, y), fitted)
        icon = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=ICON_SIZE)
        self.tile_images[okruh] = icon
        return icon

    def _progress_by_okruh(self) -> dict[str, dict[str, int]]:
        if not self._has_usable_user:
            return {}
        return summarize_progress_by_okruh(
            user_id=self._selected_user_id(),
            item_okruh_map=self.item_okruh_map,
            data=self.progress_data,
        )

    def _refresh_progress_view(self) -> None:
        if not self.okruh_buttons:
            return
        for okruh, btn in self.okruh_buttons.items():
            btn.configure(text=self._tile_text(okruh))
        if (
            self.progress_title_label is None
            or self.progress_body_label is None
            or self.progress_bar is None
            or self.progress_stats_label is None
        ):
            return
        if not self.selected_okruh:
            self.progress_title_label.configure(text="Vyber okruh")
            self.progress_body_label.configure(text="")
            self.progress_stats_label.configure(text="")
            self.progress_bar.set(0)
            return
        progress = self._progress_by_okruh().get(self.selected_okruh, {})
        total_items = int(progress.get("total_items", self.okruh_counts[self.selected_okruh]))
        seen_items = int(progress.get("seen_items", 0))
        correct_count = int(progress.get("correct_count", 0))
        wrong_count = int(progress.get("wrong_count", 0))
        attempts = correct_count + wrong_count
        seen_pct = int(round((seen_items / total_items) * 100)) if total_items else 0
        success_text = "-"
        if attempts > 0:
            success_text = f"{int(round((correct_count / attempts) * 100))}%"
        remaining_items = max(total_items - seen_items, 0)
        self.progress_bar.set(seen_pct / 100 if total_items else 0)
        self.progress_title_label.configure(
            text=f"{self.selected_okruh} · {self._selected_user_id()}"
        )
        self.progress_stats_label.configure(
            text=f"Procvičeno {seen_pct}%   |   Úspěšnost {success_text}"
        )
        self.progress_body_label.configure(
            text=(
                f"Položek celkem: {total_items}\n"
                f"Procvičené položky: {seen_items}\n"
                f"Zbývá procvičit: {remaining_items}\n"
                f"Procvičeno: {seen_pct}%\n\n"
                f"Správné odpovědi: {correct_count}\n"
                f"Chybné pokusy: {wrong_count}\n"
                f"Úspěšnost: {success_text}"
            )
        )

    def _bring_to_front(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(300, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _on_start(self) -> None:
        if not self._has_usable_user:
            self.status_label.configure(text="Nelze spustit: chybí aktivní uživatel.")
            return
        if not self.selected_okruh:
            self.status_label.configure(text="Nejprve vyber okruh.")
            return

        payload = {
            "user": self.user_var.get().split(" - ", 1)[0],
            "target_language": self._selected_lang_code(),
            "okruh": self.selected_okruh,
        }
        self._debug(f"start okruh={payload['okruh']} user={payload['user']} lang={payload['target_language']}")
        try:
            if payload["okruh"] in FLASHCARD_OKRUHY:
                self._show_cached_screen(
                    "flashcards",
                    lambda: FlashcardsScreen(
                        self.stage,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        payload["okruh"],
                        self._defer_show_cockpit,
                        progress_data=self.progress_data,
                        mark_progress_dirty=self.mark_progress_dirty,
                        asset_index=self.flash_asset_index,
                    ),
                    payload["user"],
                    payload["target_language"],
                    payload["okruh"],
                )
                return

            if payload["okruh"] == COLORS_OKRUH:
                self._show_cached_screen(
                    "colors",
                    lambda: ColorsScreen(
                        self.stage,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                        progress_data=self.progress_data,
                        mark_progress_dirty=self.mark_progress_dirty,
                    ),
                    payload["user"],
                    payload["target_language"],
                )
                return

            if payload["okruh"] == WEEKDAYS_OKRUH:
                self._show_cached_screen(
                    "weekdays",
                    lambda: WeekdaysScreen(
                        self.stage,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                        progress_data=self.progress_data,
                        mark_progress_dirty=self.mark_progress_dirty,
                    ),
                    payload["user"],
                    payload["target_language"],
                )
                return

            if payload["okruh"] == MONTHS_OKRUH:
                self._show_cached_screen(
                    "months",
                    lambda: MonthsScreen(
                        self.stage,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                        progress_data=self.progress_data,
                        mark_progress_dirty=self.mark_progress_dirty,
                    ),
                    payload["user"],
                    payload["target_language"],
                )
                return

            if payload["okruh"] == NUMBERS_OKRUH:
                self._show_cached_screen(
                    "numbers",
                    lambda: NumbersScreen(
                        self.stage,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                        progress_data=self.progress_data,
                        mark_progress_dirty=self.mark_progress_dirty,
                    ),
                    payload["user"],
                    payload["target_language"],
                )
                return

            self.status_label.configure(
                text=f"Okruh '{payload['okruh']}' bude napojen v dalším kroku."
            )
        except Exception as exc:
            print(f"Screen launch failed for {payload['okruh']}: {exc!r}")
            self.status_label.configure(text=f"Spuštění '{payload['okruh']}' selhalo: {exc}")


def main() -> int:
    base_dir = resolve_data_dir()
    bundle = load_data(base_dir)
    if not bundle.validation.is_valid:
        print("Data validation failed. Run: python3 step1_validate.py")
        for msg in bundle.validation.errors:
            print(f"  - {msg}")
        return 1

    app = CockpitApp(bundle)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
