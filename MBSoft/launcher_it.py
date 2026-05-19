import os
import runpy
import traceback

try:
    import console
except Exception:
    console = None


TARGET_SCRIPT = "AppIT.py"


def _alert(title, message):
    if console is None:
        print(f"{title}: {message}")
        return
    try:
        console.alert(title, message, "OK", hide_cancel_button=True)
    except Exception:
        print(f"{title}: {message}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(base_dir, TARGET_SCRIPT)

    if not os.path.exists(target):
        _alert("Launcher IT", f"Soubor nebyl nalezen:\n{target}")
        return

    try:
        runpy.run_path(target, run_name="__main__")
    except SystemExit:
        pass
    except Exception:
        _alert("Chyba v AppIT.py", traceback.format_exc(limit=8))


if __name__ == "__main__":
    main()
