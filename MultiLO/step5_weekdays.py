"""Step 5: Weekdays module (D0 + D1 + D2)."""

from __future__ import annotations

import argparse
from pathlib import Path

from app_paths import resolve_data_dir, resolve_prefs_path
from data_layer import DataBundle, load_data
from multilo_core import (
    DAY_ORDER,
    DEFAULT_DAY_COLORS,
    LANG_COL_MAP,
    WEEKDAYS_OKRUH as OKRUH,
    WeekdayCardItem as WeekdayCard,
    build_weekdays as _build_weekdays,
    color_name_map as _color_name_map,
    edit_distance as _edit_distance,
    load_pref_map as _load_pref_map,
    load_pref_map_from_file as _load_pref_map_from_file,
    normalize_answer as _normalize_answer,
    write_user_color_prefs as _write_user_color_prefs,
)
from nav_utils import replace_process
from tts_utils import SingleFlightTTS


try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    print("Missing dependency: customtkinter")
    print("Install with: python3 -m pip install customtkinter")
    raise SystemExit(1) from exc


APP_TITLE = "MultiLO - Dny v týdnu"
PREFS_FILE = resolve_prefs_path()
COCKPIT_PATH = Path(__file__).resolve().parent / "step2_cockpit.py"
class WeekdaysApp(ctk.CTk):
    def __init__(
        self,
        bundle: DataBundle,
        initial_user_id: str | None = None,
        initial_lang: str | None = None,
    ) -> None:
        super().__init__()
        self.bundle = bundle
        self.cards = _build_weekdays(bundle)
        self.color_options = _color_name_map(bundle)
        self.tts = SingleFlightTTS()
        self.sequence_job: str | None = None
        self.sequence_running = False
        self.sequence_index = 0
        self.write_rows: dict[int, dict[str, object]] = {}
        self.write_after_ids: list[str] = []
        self.is_navigating = False

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.title(APP_TITLE)
        self.geometry("1080x820")
        self.minsize(980, 760)

        self.user_var = ctk.StringVar(value=self._default_user())
        self.lang_var = ctk.StringVar(value="IT")
        self.mode_var = ctk.StringVar(value="Barvy dnů")
        self._apply_initial(initial_user_id, initial_lang)

        self.current_user_id = self.user_var.get().split(" - ", 1)[0]
        self.color_choices: dict[int, ctk.StringVar] = {}
        self.day_colors = self._build_day_colors(self.current_user_id)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._bring_to_front)
        self._render_mode()

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

    def _build_day_colors(self, user_id: str) -> dict[int, str]:
        pref_map = _load_pref_map_from_file(PREFS_FILE, user_id, self.cards)
        if not pref_map:
            pref_map = _load_pref_map(self.bundle, user_id, self.cards)
        day_colors: dict[int, str] = {}
        for idx, card in enumerate(self.cards):
            pref = pref_map.get(card.item_id)
            color_hex = (pref.assoc_color_hex if pref else "").strip()
            day_colors[card.item_id] = color_hex or DEFAULT_DAY_COLORS[idx % len(DEFAULT_DAY_COLORS)]
        return day_colors

    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=12)
        top.pack(fill="x", padx=16, pady=(16, 10))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._add_selector(top, 0, "Uživatel", self.user_var, [f"{u.user_id} - {u.display_name}" for u in self.bundle.users], self._on_user_changed)
        self._add_selector(top, 1, "Jazyk", self.lang_var, list(LANG_COL_MAP), self._on_lang_changed)
        mode_wrap = ctk.CTkFrame(top, corner_radius=8)
        mode_wrap.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(mode_wrap, text="Režim").pack(anchor="w", padx=8, pady=(6, 2))
        self.mode_switch = ctk.CTkSegmentedButton(
            mode_wrap,
            values=["Barvy dnů", "Sekvence", "Psaní"],
            variable=self.mode_var,
            command=lambda _value: self._render_mode(),
        )
        self.mode_switch.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(top, text="Zpět do kokpitu", command=self._back_to_cockpit).grid(
            row=1, column=3, padx=8, pady=(4, 10), sticky="ew"
        )

        self.status_label = ctk.CTkLabel(
            self,
            text="Připraveno. Nastav barvy dnů nebo spusť sekvenci.",
            font=ctk.CTkFont(size=13),
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))

        self.content = ctk.CTkFrame(self, corner_radius=12)
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _add_selector(
        self,
        parent: ctk.CTkFrame,
        col: int,
        label: str,
        variable: ctk.StringVar,
        values: list[str],
        command,
    ) -> None:
        wrap = ctk.CTkFrame(parent, corner_radius=8)
        wrap.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
        ctk.CTkLabel(wrap, text=label).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkOptionMenu(wrap, variable=variable, values=values, command=command).pack(
            fill="x", padx=8, pady=(0, 8)
        )

    def _render_mode(self) -> None:
        if self.is_navigating:
            return
        self._cancel_pending_jobs()
        for child in self.content.winfo_children():
            child.destroy()
        mode = self.mode_var.get()
        if mode == "Barvy dnů":
            self._build_color_editor()
        elif mode == "Sekvence":
            self._build_sequence_mode()
        else:
            self._build_writing_mode()

    def _build_color_editor(self) -> None:
        frame = ctk.CTkFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text="Přiřazení barev k dnům",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            frame,
            text="Barvy se ukládají pro vybraného uživatele do user_item_prefs.csv.",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self.color_choices = {}
        options = list(self.color_options.keys())
        for card in self.cards:
            row = ctk.CTkFrame(frame, corner_radius=10)
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=card.cz, width=160, anchor="w", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=12, pady=10)
            swatch = ctk.CTkFrame(row, width=42, height=28, corner_radius=8, fg_color=self.day_colors[card.item_id])
            swatch.pack(side="left", padx=(0, 12), pady=10)
            var = ctk.StringVar(value=self._hex_to_color_name(self.day_colors[card.item_id]))
            self.color_choices[card.item_id] = var
            menu = ctk.CTkOptionMenu(
                row,
                variable=var,
                values=options,
                command=lambda choice, item_id=card.item_id, chip=swatch: self._on_color_selected(item_id, choice, chip),
            )
            menu.pack(side="left", padx=8, pady=10)
            target = card.target_text(self.lang_var.get())
            ctk.CTkLabel(row, text=target, width=180, anchor="w").pack(side="right", padx=12, pady=10)

        ctk.CTkButton(frame, text="Uložit barvy", command=self._save_day_colors).pack(anchor="e", padx=16, pady=14)

    def _build_sequence_mode(self) -> None:
        frame = ctk.CTkFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text="Sekvence Po–Ne",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))
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
        ctk.CTkButton(btns, text="Předchozí", command=self._prev_sequence).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(btns, text="Přehrát", command=self._speak_sequence).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(btns, text="Další", command=self._next_sequence).pack(side="left", padx=8, pady=10)
        self.seq_auto_btn = ctk.CTkButton(btns, text="Auto ON", command=self._toggle_sequence)
        self.seq_auto_btn.pack(side="left", padx=8, pady=10)

        self.sequence_index = 0
        self._render_sequence_card()

    def _build_writing_mode(self) -> None:
        frame = ctk.CTkScrollableFrame(self.content, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text="Psaní s kontrolou",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 10))

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
            self.write_rows[card.item_id] = {"entry": entry, "result": result, "row": row}

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
        user_id = self.user_var.get().split(" - ", 1)[0]
        try:
            _write_user_color_prefs(PREFS_FILE, self.bundle, user_id, self.day_colors)
        except Exception as exc:
            self.status_label.configure(text=f"Uložení selhalo: {exc}")
            return
        self.current_user_id = user_id
        self.day_colors = self._build_day_colors(user_id)
        self._render_mode()
        self.status_label.configure(text=f"Barvy dnů uloženy pro uživatele '{user_id}'.")

    def _render_sequence_card(self) -> None:
        if not self.cards:
            return
        card = self.cards[self.sequence_index]
        self.seq_progress.configure(text=f"Den {self.sequence_index + 1}/{len(self.cards)}")
        self.seq_card.configure(fg_color=self.day_colors.get(card.item_id, DEFAULT_DAY_COLORS[self.sequence_index]))
        self.seq_target_label.configure(text=card.target_text(self.lang_var.get()))
        self.seq_cz_label.configure(text=card.cz)

    def _prev_sequence(self) -> None:
        if not self.cards:
            return
        self.sequence_index = (self.sequence_index - 1) % len(self.cards)
        self._render_sequence_card()

    def _next_sequence(self) -> None:
        if not self.cards:
            return
        self.sequence_index = (self.sequence_index + 1) % len(self.cards)
        self._render_sequence_card()

    def _speak_sequence(self) -> None:
        if not self.cards:
            return
        self._speak_text(self.cards[self.sequence_index].target_text(self.lang_var.get()), self.lang_var.get())

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
        if not self.winfo_exists() or not self.sequence_running:
            return
        self._render_sequence_card()
        self._speak_sequence()
        self.sequence_index += 1
        if self.sequence_index >= len(self.cards):
            self.sequence_index = 0
        self.sequence_job = self.after(1800, self._run_sequence)

    def _stop_sequence(self) -> None:
        self.sequence_running = False
        if hasattr(self, "seq_auto_btn"):
            self.seq_auto_btn.configure(text="Auto ON")
        if self.sequence_job is not None:
            self.after_cancel(self.sequence_job)
            self.sequence_job = None

    def _check_write_answer(self, card: WeekdayCard) -> None:
        row = self.write_rows[card.item_id]
        entry = row["entry"]
        result = row["result"]
        assert isinstance(entry, ctk.CTkEntry)
        assert isinstance(result, ctk.CTkLabel)

        user_text = entry.get().strip()
        expected = card.target_text(self.lang_var.get())
        answer = _normalize_answer(user_text)
        target = _normalize_answer(expected)

        if answer == target:
            result.configure(text=f"Správně: {expected}", text_color="#16A34A")
            self._speak_text(expected, self.lang_var.get())
            return

        if user_text and _edit_distance(answer, target) <= 1:
            result.configure(text=f"Skoro! Správně: {expected}", text_color="#D97706")
            return

        result.configure(text=f"Chyba: {user_text} -> {expected}", text_color="#DC2626")

        def _show_correct() -> None:
            if not self.winfo_exists():
                return
            entry.delete(0, "end")
            entry.insert(0, expected)
            result.configure(text=f"Správně: {expected}", text_color="#16A34A")

        after_id = self.after(2000, _show_correct)
        self.write_after_ids.append(after_id)

    def _on_user_changed(self, _value: str) -> None:
        self.current_user_id = self.user_var.get().split(" - ", 1)[0]
        self.day_colors = self._build_day_colors(self.current_user_id)
        self._render_mode()
        self.status_label.configure(text=f"Uživatel přepnut na {self.current_user_id}.")

    def _on_lang_changed(self, _value: str) -> None:
        self._render_mode()
        self.status_label.configure(text=f"Jazyk přepnut na {self.lang_var.get()}.")

    def _speak_text(self, text: str, lang: str) -> None:
        if not text or self.tts.backend == "none":
            return
        if not self.tts.speak(text, lang, rate=165):
            self.status_label.configure(text="TTS právě mluví, nový požadavek přeskočen.")

    def _bring_to_front(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(300, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _back_to_cockpit(self) -> None:
        if self.is_navigating:
            return
        self.is_navigating = True
        self._cancel_pending_jobs()
        try:
            self.focus_set()
            self.update_idletasks()
        except Exception:
            pass
        try:
            for widget in self.winfo_children():
                try:
                    widget.configure(state="disabled")
                except Exception:
                    pass
        except Exception:
            pass
        self.status_label.configure(text="Návrat do kokpitu...")
        self.after_idle(self._exec_back_to_cockpit)

    def _exec_back_to_cockpit(self) -> None:
        try:
            replace_process(COCKPIT_PATH)
        except Exception as exc:
            self.is_navigating = False
            self.status_label.configure(text=f"Návrat do kokpitu selhal: {exc}")
            return

    def _on_close(self) -> None:
        self._cancel_pending_jobs()
        self._finalize_close()

    def _cancel_pending_jobs(self) -> None:
        self._stop_sequence()
        if self.write_after_ids:
            for after_id in self.write_after_ids:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
            self.write_after_ids.clear()

    def _finalize_close(self) -> None:
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MultiLO Weekdays")
    parser.add_argument("--user", dest="user_id", default=None)
    parser.add_argument("--lang", dest="lang", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = load_data(resolve_data_dir())
    if not bundle.validation.is_valid:
        print("Data validation failed. Run: python3 step1_validate.py")
        for msg in bundle.validation.errors:
            print(f"  - {msg}")
        return 1

    app = WeekdaysApp(bundle, initial_user_id=args.user_id, initial_lang=args.lang)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
