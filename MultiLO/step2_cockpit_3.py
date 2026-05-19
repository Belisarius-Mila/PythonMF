"""Step 2: MultiLO cockpit (dashboard) skeleton in CustomTkinter."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from data_layer import DataBundle, load_data
from screen_frames import ColorsScreen, FlashcardsScreen, MonthsScreen, NumbersScreen, WeekdaysScreen


try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    print("Missing dependency: customtkinter")
    print("Install with: python3 -m pip install customtkinter")
    raise SystemExit(1) from exc


APP_TITLE = "MultiLO - Cockpit (Step 2)"
LANG_OPTIONS = ["FR", "IT", "ES", "EN"]
FLASHCARD_OKRUHY = {"Zelenina a ovoce", "Zvířata", "Rostliny"}
COLORS_OKRUH = "Základní barvy"
WEEKDAYS_OKRUH = "Dny v týdnu"
MONTHS_OKRUH = "Měsíce v roce"
NUMBERS_OKRUH = "Číslovky"


class CockpitApp(ctk.CTk):
    def __init__(self, bundle: DataBundle) -> None:
        super().__init__()
        self.bundle = bundle
        self.okruh_counts = Counter(item.okruh for item in bundle.vocab)
        self.okruhy = sorted(self.okruh_counts.keys())
        self.selected_okruh: str | None = None
        self.okruh_buttons: dict[str, ctk.CTkButton] = {}
        self.start_btn: ctk.CTkButton | None = None
        self.user_menu: ctk.CTkOptionMenu | None = None
        self._has_usable_user = any(u.active for u in self.bundle.users)
        self.home_widgets: list[ctk.CTkBaseClass] = []
        self.active_screen: ctk.CTkFrame | None = None

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1060x720")
        self.minsize(980, 660)

        self._show_cockpit()
        self.after(120, self._bring_to_front)

    def _defer_show_cockpit(self) -> None:
        old_screen = self.active_screen
        if old_screen is not None:
            try:
                old_screen.pack_forget()
            except Exception:
                pass
        self.active_screen = None
        self.after_idle(lambda: self._show_cockpit_with_cleanup(old_screen))

    def _show_cockpit_with_cleanup(self, old_screen: ctk.CTkFrame | None) -> None:
        self._show_cockpit()
        if old_screen is not None:
            self.after_idle(lambda: self._destroy_old_screen(old_screen))

    def _destroy_old_screen(self, screen: ctk.CTkFrame) -> None:
        try:
            screen.destroy()
        except Exception:
            pass

    def _clear_root(self) -> None:
        if self.active_screen is not None:
            try:
                self.active_screen.destroy()
            except Exception:
                pass
            self.active_screen = None
        while self.home_widgets:
            widget = self.home_widgets.pop()
            try:
                widget.destroy()
            except Exception:
                pass

    def _show_cockpit(self) -> None:
        self._clear_root()
        self._build_header()
        self._build_selectors()
        self._build_okruh_tiles()
        self._build_footer()
        if self.okruhy:
            self._set_selected_okruh(self.okruhy[0])

    def _open_screen(self, screen: ctk.CTkFrame) -> None:
        self._clear_root()
        self.active_screen = screen
        self.active_screen.pack(fill="both", expand=True)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=16, pady=(16, 10))
        self.home_widgets.append(header)

        title = ctk.CTkLabel(
            header,
            text="MultiLO Kokpit",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(anchor="w", padx=16, pady=(12, 2))

        subtitle = ctk.CTkLabel(
            header,
            text="Vyber uživatele, jazyk a okruh. Režim zvolíš uvnitř modulu.",
            font=ctk.CTkFont(size=14),
        )
        subtitle.pack(anchor="w", padx=16, pady=(0, 12))

    def _build_selectors(self) -> None:
        row = ctk.CTkFrame(self, corner_radius=12)
        row.pack(fill="x", padx=16, pady=(0, 10))
        self.home_widgets.append(row)

        row.grid_columnconfigure((0, 1), weight=1)

        user_values = [f"{u.user_id} - {u.display_name}" for u in self.bundle.users if u.active]
        if not user_values:
            user_values = ["<no active users>"]

        self.user_var = ctk.StringVar(value=user_values[0])
        self.lang_var = ctk.StringVar(value=LANG_OPTIONS[0])

        self.user_menu = self._selector_block(row, 0, "Uživatel", self.user_var, user_values)
        self._selector_block(row, 1, "Cílový jazyk", self.lang_var, LANG_OPTIONS)

        if not self._has_usable_user and self.user_menu is not None:
            self.user_menu.configure(state="disabled")

    def _selector_block(
        self,
        parent: ctk.CTkFrame,
        col: int,
        label: str,
        variable: ctk.StringVar,
        values: list[str],
    ) -> ctk.CTkOptionMenu:
        block = ctk.CTkFrame(parent, corner_radius=10)
        block.grid(row=0, column=col, padx=8, pady=10, sticky="ew")

        ctk.CTkLabel(block, text=label, font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=10, pady=(8, 4)
        )
        menu = ctk.CTkOptionMenu(block, variable=variable, values=values)
        menu.pack(fill="x", padx=10, pady=(0, 10))
        return menu

    def _build_okruh_tiles(self) -> None:
        tiles_wrap = ctk.CTkFrame(self, corner_radius=12)
        tiles_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.home_widgets.append(tiles_wrap)

        ctk.CTkLabel(
            tiles_wrap,
            text="Okruhy",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 8))

        grid = ctk.CTkFrame(tiles_wrap, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = 4
        for col in range(cols):
            grid.grid_columnconfigure(col, weight=1)

        for idx, okruh in enumerate(self.okruhy):
            r = idx // cols
            c = idx % cols
            count = self.okruh_counts[okruh]
            tile_text = f"{okruh}\n{count} položek"
            btn = ctk.CTkButton(
                grid,
                text=tile_text,
                height=88,
                corner_radius=10,
                command=lambda o=okruh: self._set_selected_okruh(o),
            )
            btn.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            self.okruh_buttons[okruh] = btn

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, corner_radius=12)
        footer.pack(fill="x", padx=16, pady=(0, 16))
        self.home_widgets.append(footer)

        self.status_label = ctk.CTkLabel(
            footer,
            text="Připraveno. Vyber okruh a stiskni Start.",
            font=ctk.CTkFont(size=13),
        )
        self.status_label.pack(side="left", padx=12, pady=12)

        self.start_btn = ctk.CTkButton(
            footer,
            text="Start",
            width=120,
            command=self._on_start,
        )
        self.start_btn.pack(side="right", padx=12, pady=12)

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
            "target_language": self.lang_var.get(),
            "okruh": self.selected_okruh,
        }
        try:
            if payload["okruh"] in FLASHCARD_OKRUHY:
                self._open_screen(
                    FlashcardsScreen(
                        self,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        payload["okruh"],
                        self._defer_show_cockpit,
                    )
                )
                return

            if payload["okruh"] == COLORS_OKRUH:
                self._open_screen(
                    ColorsScreen(
                        self,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                    )
                )
                return

            if payload["okruh"] == WEEKDAYS_OKRUH:
                self._open_screen(
                    WeekdaysScreen(
                        self,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                    )
                )
                return

            if payload["okruh"] == MONTHS_OKRUH:
                self._open_screen(
                    MonthsScreen(
                        self,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                    )
                )
                return

            if payload["okruh"] == NUMBERS_OKRUH:
                self._open_screen(
                    NumbersScreen(
                        self,
                        self.bundle,
                        payload["user"],
                        payload["target_language"],
                        self._defer_show_cockpit,
                    )
                )
                return

            self.status_label.configure(
                text=f"Okruh '{payload['okruh']}' bude napojen v dalším kroku."
            )
        except Exception as exc:
            print(f"Screen launch failed for {payload['okruh']}: {exc!r}")
            self.status_label.configure(text=f"Spuštění '{payload['okruh']}' selhalo: {exc}")


def main() -> int:
    base_dir = Path(__file__).resolve().parent
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
