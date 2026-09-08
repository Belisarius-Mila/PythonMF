"""Focused French verb practice window, separate from the editable verb library."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from verb_training import LessonPlayer, LocalSpeech, TrainingCorpus


class VerbTrainingScreen:
    def __init__(self, app, data_dir=None, speech=None):
        self.app = app
        self.data_dir = Path(data_dir or Path(__file__).resolve().parent)
        self.corpus = TrainingCorpus(self.data_dir)
        self.pictures = json.loads((self.data_dir / "verb_training_pictures.json").read_text(encoding="utf-8"))
        self.speech = speech or LocalSpeech()
        self.win = tk.Toplevel(app.master)
        self.win.title("Trénink francouzských sloves · Présent")
        self.win.geometry("1180x780")
        self.win.minsize(960, 650)
        self.win.configure(bg="#f5f3ee")
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.verb = None
        self.number = tk.StringVar(self.win, "S")
        self.person = tk.StringVar(self.win, "1")
        self.loop = tk.BooleanVar(self.win, False)
        self.recall = tk.BooleanVar(self.win, False)
        self.sound = tk.BooleanVar(self.win, bool(self.speech.command))
        self.interval = tk.StringVar(self.win, "2")
        self.search = tk.StringVar(self.win)
        self.translation = tk.StringVar(self.win)
        self.status = tk.StringVar(self.win, "Vyber sloveso ze seznamu.")
        self.translations = ["", "", ""]
        self.loop_job = None
        self.between_paused = False
        self.photo = None
        self._build()
        self.player = LessonPlayer(self.win, self.speech, self.show_event, self.finished, self.audio_error)
        self.search.trace_add("write", lambda *_: self.populate())
        self.populate()

    def _label(self, parent, text="", size=16, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg="#183a43",
                        font=("Helvetica", size), **kwargs)

    def _build(self):
        header = tk.Frame(self.win, bg="#183a43", padx=18, pady=12)
        header.pack(fill="x")
        ttk.Button(header, text="☰ Slovesa", command=self.toggle_list).pack(side="left")
        tk.Label(header, text="TRÉNINK SLOVES", bg="#183a43", fg="white",
                 font=("Helvetica", 17, "bold")).pack(side="left", padx=18)
        tk.Label(header, text="PRÉSENT", bg="#183a43", fg="#cfe5d7",
                 font=("Helvetica", 12)).pack(side="right")
        self.body = tk.Frame(self.win, bg="#f5f3ee")
        self.body.pack(fill="both", expand=True, padx=16, pady=14)
        self.sidebar = tk.Frame(self.body, bg="white", width=330)
        self.sidebar.pack(side="left", fill="y", padx=(0, 18))
        self._label(self.sidebar, f"{len(self.corpus.verbs)} sloves", 17).pack(anchor="w", pady=(0, 8))
        ttk.Entry(self.sidebar, textvariable=self.search).pack(fill="x", pady=(0, 8))
        tree_box = tk.Frame(self.sidebar, bg="white")
        tree_box.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_box, columns=("fr", "cz", "selected"), show="headings", selectmode="browse")
        for key, title, width in (("fr", "Français", 110), ("cz", "Česky", 150), ("selected", "✓", 35)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=width, stretch=key == "cz")
        scroll = ttk.Scrollbar(tree_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.choose_from_tree)
        self.tree.bind("<Return>", self.choose_from_tree)
        self.main = tk.Frame(self.body, bg="#f5f3ee")
        self.main.pack(side="left", fill="both", expand=True)
        self.title = self._label(self.main, "Jedno sloveso. Krok za krokem.", 28, anchor="w")
        self.title.pack(fill="x")
        self.meaning = self._label(self.main, "Poslech · věty · zapamatování", 15, anchor="w")
        self.meaning.pack(fill="x", pady=(3, 12))
        controls = tk.Frame(self.main, bg="#f5f3ee")
        controls.pack(fill="x", pady=(0, 8))
        self.number_buttons = {}
        for number, label in (("S", "S · jednotné"), ("P", "P · množné")):
            button = ttk.Radiobutton(controls, text=label, variable=self.number, value=number, command=self.change_selection)
            button.pack(side="left", padx=(0, 8))
            self.number_buttons[number] = button
        self.person_buttons = {}
        for person in ("1", "2", "3"):
            button = ttk.Radiobutton(controls, text=person, variable=self.person, value=person, command=self.change_selection)
            button.pack(side="left", padx=5)
            self.person_buttons[person] = button
        options = tk.Frame(self.main, bg="#f5f3ee")
        options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(options, text="Smyčka", variable=self.loop, command=self.loop_changed).pack(side="left", padx=(0, 10))
        self._label(options, "Pauza mezi větami (s):", 11).pack(side="left")
        ttk.Spinbox(options, from_=1, to=15, increment=1, textvariable=self.interval, width=3).pack(side="left", padx=5)
        ttk.Checkbutton(options, text="Zkus si vzpomenout", variable=self.recall, command=self.change_selection).pack(side="left", padx=10)
        ttk.Checkbutton(options, text="Zvuk", variable=self.sound, command=self.sound_changed).pack(side="left")
        self.content = tk.Frame(self.main, bg="#f5f3ee")
        self.content.pack(fill="both", expand=True)
        self.content.columnconfigure(0, weight=3)
        self.content.columnconfigure(1, weight=2)
        self.content.rowconfigure(0, weight=1)
        text_card = tk.Frame(self.content, bg="white", padx=18, pady=16)
        text_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.form_label = self._label(text_card, "", 29, anchor="w", justify="left", wraplength=490)
        self.form_label.pack(fill="x", pady=(0, 18))
        self.sentence_labels = []
        for _ in range(3):
            label = self._label(text_card, "", 20, justify="left", anchor="w", wraplength=490)
            label.pack(fill="x", pady=10)
            self.sentence_labels.append(label)
        self.recall_label = self._label(text_card, "", 17, anchor="w", justify="left", wraplength=490)
        self.recall_label.pack(fill="x", pady=8)
        text_card.bind("<Configure>", lambda e: self.resize_text(e.width))
        side = tk.Frame(self.content, bg="#f5f3ee")
        side.grid(row=0, column=1, sticky="nsew")
        self.picture = self._label(side, "", 15, wraplength=260)
        self.picture.pack(fill="x", pady=(0, 12))
        ttk.Button(side, text="Ukázat české věty", command=self.show_translation).pack(anchor="w")
        self.translation_label = self._label(side, "", 15, justify="left", anchor="nw", wraplength=300,
                                             textvariable=self.translation)
        self.translation_label.pack(fill="both", expand=True, pady=12)
        side.bind("<Configure>", lambda e: self.translation_label.configure(wraplength=max(180, e.width - 8)))
        self.answer = self._label(self.main, "", 40, height=2, anchor="w")
        self.answer.pack(fill="x", pady=(8, 0))
        footer = tk.Frame(self.main, bg="#f5f3ee")
        footer.pack(fill="x")
        ttk.Button(footer, text="▶ Přehrát", command=self.start).pack(side="left", padx=(0, 8))
        self.pause_button = ttk.Button(footer, text="Pauza", command=self.toggle_pause)
        self.pause_button.pack(side="left", padx=(0, 8))
        ttk.Button(footer, text="Zopakovat", command=self.repeat).pack(side="left", padx=(0, 8))
        ttk.Button(footer, text="Další osoba →", command=self.next_person).pack(side="left")
        self._label(self.main, "", 12, textvariable=self.status, anchor="w", wraplength=800).pack(fill="x", pady=(10, 0))
        if not self.speech.command:
            self.status.set("Bez zvuku. Pro francouzský hlas na Linuxu je potřeba eSpeak NG.")

    def resize_text(self, width):
        for label in (self.form_label, self.recall_label, *self.sentence_labels):
            label.configure(wraplength=max(160, width - 40))

    def populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.search.get().casefold().strip()
        for verb in self.corpus.verbs:
            if query and query not in (verb["InfFR"] + " " + verb["InfCZ"]).casefold():
                continue
            self.tree.insert("", "end", iid=verb["InfFR"], values=(verb["InfFR"], verb["InfCZ"], "☑" if self.verb == verb else "☐"))

    def choose_from_tree(self, event=None):
        if event is not None and getattr(event, "keysym", "") != "Return":
            if not self.tree.identify_row(event.y):
                return
        selection = self.tree.selection()
        if selection:
            self.select_verb(selection[0])

    def select_verb(self, infinitive):
        self.cancel()
        self.verb = next(v for v in self.corpus.verbs if v["InfFR"] == infinitive)
        self.title.configure(text=infinitive.upper())
        self.meaning.configure(text=self.verb["InfCZ"])
        if infinitive == "falloir":
            self.number.set("S")
            self.person.set("3")
        self.update_person_controls()
        self.populate()
        self.sidebar.pack_forget()
        self.load_picture()
        self.start(introduction=True)

    def toggle_list(self):
        if self.sidebar.winfo_manager():
            self.sidebar.pack_forget()
        else:
            self.cancel()
            self.status.set("Vyber sloveso, nebo pokračuj tlačítkem Přehrát.")
            self.sidebar.pack(side="left", fill="y", padx=(0, 18), before=self.main)

    def update_person_controls(self):
        if not self.verb:
            return
        impersonal = self.verb["InfFR"] == "falloir"
        self.number_buttons["P"].configure(state="disabled" if impersonal else "normal")
        for person, button in self.person_buttons.items():
            button.configure(state="disabled" if impersonal and person != "3" else "normal")

    def load_picture(self):
        stem = self.pictures.get(self.verb["InfFR"], "")
        local = self.data_dir / "training_images" / (stem + ".png")
        path = str(local) if stem and local.is_file() else (self.app._find_picture_path(stem) if stem else "")
        self.photo = None
        self.picture.configure(image="", text="Ilustraci tohoto slovesa ještě doplníme.")
        if path:
            try:
                with Image.open(path) as source:
                    image = source.convert("RGB")
                    image.thumbnail((300, 270), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(image, master=self.win)
                self.picture.configure(image=self.photo, text="")
            except (OSError, ValueError):
                self.picture.configure(text="Obrázek se nepodařilo načíst.")

    def interval_seconds(self):
        try:
            return max(1, min(15, int(self.interval.get())))
        except ValueError:
            self.interval.set("2")
            return 2

    def cancel(self):
        if self.loop_job is not None:
            self.win.after_cancel(self.loop_job)
            self.loop_job = None
        self.between_paused = False
        self.player.stop()
        self.pause_button.configure(text="Pauza")

    def start(self, introduction=False):
        if not self.verb:
            return
        self.cancel()
        self.translation.set("")
        self.translations = ["", "", ""]
        for label in (self.form_label, self.answer, self.recall_label, *self.sentence_labels):
            label.configure(text="")
        self.status.set("Poslouchej a sleduj tvar slovesa." if self.sound.get() else "Sleduj tvar slovesa · bez zvuku.")
        events = self.corpus.lesson(self.verb["InfFR"], self.number.get(), self.person.get(),
                                    recall=self.recall.get(), interval=self.interval_seconds(), introduction=introduction)
        self.player.start(events, sound=self.sound.get())

    def show_event(self, event):
        kind = event["kind"]
        if kind in ("intro", "form"):
            self.form_label.configure(text=event["text"])
        elif kind == "sentence":
            slot = event["slot"]
            self.sentence_labels[slot].configure(text=event["text"])
            self.translations[slot] = event["translation"]
            self.translation.set("")
        elif kind == "recall":
            for label in (self.form_label, *self.sentence_labels):
                label.configure(text="")
            self.translation.set("")
            self.translations = ["", "", ""]
            self.recall_label.configure(text="Jaký tvar patří k tomuto zájmenu?")
            self.answer.configure(text=event["text"])
        elif kind in ("reveal", "answer"):
            self.recall_label.configure(text="")
            self.answer.configure(text=event["text"])

    def show_translation(self):
        text = "\n\n".join(f"{i + 1}. {t}" for i, t in enumerate(self.translations) if t)
        self.translation.set(text or "Česká věta bude dostupná po francouzské ukázce.")

    def toggle_pause(self):
        if self.loop_job is not None:
            self.win.after_cancel(self.loop_job)
            self.loop_job = None
            self.between_paused = True
            self.pause_button.configure(text="Pokračovat")
            self.status.set("Pozastaveno mezi osobami.")
        elif self.between_paused:
            self.next_person()
        elif self.player.paused:
            self.player.resume()
            self.pause_button.configure(text="Pauza")
            self.status.set("Pokračujeme od začátku přerušené věty.")
        elif self.player.active:
            self.player.pause()
            self.pause_button.configure(text="Pokračovat")
            self.status.set("Pozastaveno. Pokračování zopakuje přerušenou větu.")

    def repeat(self):
        if self.loop_job is not None:
            self.win.after_cancel(self.loop_job)
            self.loop_job = None
        self.between_paused = False
        self.pause_button.configure(text="Pauza")
        self.player.repeat()

    def change_selection(self):
        self.start()

    def next_person(self):
        if self.verb:
            self.person.set(self.corpus.next_person(self.verb["InfFR"], self.number.get(), self.person.get()))
            self.start()

    def loop_changed(self):
        if not self.loop.get() and self.loop_job is not None:
            self.win.after_cancel(self.loop_job)
            self.loop_job = None

    def sound_changed(self):
        if self.sound.get() and not self.speech.command:
            self.sound.set(False)
            self.status.set("Hlas není dostupný. Na Linuxu nainstaluj eSpeak NG; trénink může běžet bez zvuku.")
            return
        self.start()

    def finished(self):
        self.status.set("Hotovo. Zopakuj si tvar nebo vyber další osobu.")
        if self.loop.get():
            self.status.set("Další osoba za chvíli…")
            self.loop_job = self.win.after(self.interval_seconds() * 1000, self.next_person)

    def audio_error(self, message):
        self.pause_button.configure(text="Pokračovat")
        self.status.set("Zvuk: " + message)

    def close(self):
        self.cancel()
        self.win.destroy()
        self.app.verb_training_window = None
