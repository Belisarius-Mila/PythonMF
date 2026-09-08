"""Opt-in packaged GUI check, always using a fresh private copy of seed data."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import tkinter as tk

import vocab_trainer_fr as trainer
from verb_training_screen import VerbTrainingScreen


class SilentSpeech:
    command = None

    def start(self, text):
        pass

    def stop(self):
        pass

    def poll(self):
        return 0


def check_bundle(report):
    if report.exists():
        raise ValueError("Kontrolní protokol už existuje.")
    directory = Path(tempfile.mkdtemp(prefix="vocabularyfr-bundle-check-"))
    # Retain the isolated test directory for diagnostics; never use live CSVs.
    for name in trainer.RUNTIME_CSV_FILENAMES:
        # PyInstaller onedir links Frameworks data to Contents/Resources.
        source = (Path(trainer.__file__).parent / name).resolve()
        if not source.is_file():
            raise ValueError(f"Chybí přibalený {name}.")
        shutil.copyfile(source, directory / name)
    csv_path = directory / trainer.CSV_FILENAME
    before = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    trainer._app_support_dir = lambda: str(directory / "support")

    class QuietApp(trainer.VocabularyTrainerApp):
        def _speak_current(self):
            pass

        def _resolve_cz_voice(self):
            return "Zuzana"

    root = tk.Tk()
    app = QuietApp(root, str(csv_path))
    root.withdraw()
    screen = VerbTrainingScreen(app, speech=SilentSpeech())
    app.verb_training_window = screen
    try:
        for verb in screen.corpus.verbs:
            screen.select_verb(verb["InfFR"])
            screen.player.pause()
            if screen.photo is None:
                raise ValueError("Chybí tréninkový obrázek.")
        screen.select_verb("aller")
        screen.number.set("S")
        screen.person.set("1")
        screen.recall.set(True)
        screen.start()
        root.update()
        if not screen.player.waiting_for_answer:
            raise ValueError("Vzpomínání nečeká na odpověď.")
        screen.typed_form.set("vais")
        if screen.player.waiting_for_answer:
            raise ValueError("Správná odpověď nepokračuje.")
        screen.player.pause()
        result = {"rows": len(app.rows), "verbs": len(screen.corpus.verbs),
                  "images_loaded": len(screen.corpus.verbs), "recall_input": "OK",
                  "tk": root.tk.call("info", "patchlevel")}
    finally:
        screen.close()
        root.destroy()
    if hashlib.sha256(csv_path.read_bytes()).hexdigest() != before:
        raise ValueError("Kontrola změnila testovací slovník.")
    with report.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
