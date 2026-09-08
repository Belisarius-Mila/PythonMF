"""Portable Jana edition: one explicit writable directory beside the app."""

import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from vocab_trainer_fr import RUNTIME_CSV_FILENAMES, main


def portable_arguments(executable, argv):
    """An explicit CLI directory wins; never silently migrate user data."""
    if any(arg == "--data-dir" or arg.startswith("--data-dir=") for arg in argv):
        return list(argv)
    executable = Path(executable).absolute()
    if executable.parent.name != "MacOS" or executable.parent.parent.name != "Contents":
        raise ValueError("Tento spouštěč patří do VocabularyFR.app.")
    directory = executable.parents[3]
    missing = [name for name in RUNTIME_CSV_FILENAMES
               if not (directory / name).is_file() or (directory / name).is_symlink()]
    if missing:
        raise ValueError(
            "Otevři VocabularyFR.app ve sdílené složce PythonMF/VocabularyFR. "
            "Vedle aplikace musí zůstat datové soubory. Chybí: " + ", ".join(missing)
        )
    return ["--data-dir", str(directory), *argv]


def launch():
    if len(sys.argv) == 3 and sys.argv[1] == "--check-bundle":
        from bundle_check import check_bundle
        check_bundle(Path(sys.argv[2]))
        return 0
    try:
        arguments = portable_arguments(sys.executable, sys.argv[1:])
    except ValueError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("VocabularyFR – umístění slovníku", str(exc))
        root.destroy()
        return 1
    return main(arguments)


if __name__ == "__main__":
    raise SystemExit(launch())
