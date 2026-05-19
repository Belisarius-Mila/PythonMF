import os
import runpy
import traceback

try:
    import console
except Exception:
    console = None


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
    target = os.path.join(base_dir, "AppFR.py")

    if not os.path.exists(target):
        _alert("Launcher", f"Soubor nebyl nalezen:\n{target}")
        return

    try:
        runpy.run_path(target, run_name="__main__")
    except SystemExit:
        # AppFR can call sys.exit() intentionally.
        pass
    except Exception:
        _alert("Chyba v AppFR.py", traceback.format_exc(limit=8))


if __name__ == "__main__":
    main()
