"""Real desktop smoke for personal experiments; all data stays in temporary folders."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import python_se_samanthou as app
from course_loader import load_course
from workshop_store import WorkshopError

GOOD = 'cislo = 7\nprint(cislo)\nkruh(250, 180, 40, "modra")\n'


def child(folder, phase):
    app.COURSE = load_course()
    app.LESSONS = app.COURSE['lessons']
    failures = []

    def ready(ui):
        deadline = time.monotonic() + 45
        def fail(exc):
            failures.append(repr(exc))
            ui.root.destroy()
        ui.root.report_callback_exception = lambda kind, exc, tb: fail(exc)

        def guarded(action):
            try:
                action()
            except BaseException as exc:
                fail(exc)

        def wait_for(w, continuation):
            if time.monotonic() > deadline:
                raise AssertionError('Workshop GUI timed out')
            if w.busy:
                w.window.after(50, lambda: guarded(lambda: wait_for(w, continuation)))
            else:
                continuation()

        def replace(w, code):
            w.editor.delete('1.0', 'end')
            w.editor.insert('1.0', code)

        def initial():
            ui.open_workshop()
            w = ui.workshop
            assert w is not None
            w.window.geometry('900x640')
            w.window.update_idletasks()
            assert w.editor.winfo_height() >= 100
            if phase == 'reopen':
                experiments = w.state['experiments']
                assert len(experiments) == 4
                assert w.editor.get('1.0', 'end-1c') == GOOD
                assert w.notes.get('1.0', 'end-1c') == 'Zkouším modrý kruh.'
                assert any(e['title'] == 'Můj obrázek' and e['source'] == GOOD for e in experiments.values())
                assert any(e['title'].endswith('kopie') for e in experiments.values())
                ui.close()
                return
            ui.load(3)
            course_source = ui.editor.get('1.0', 'end-1c')
            ui.save()
            course_bytes = ui.store.path.read_bytes()
            ui.open_workshop(copy_lesson=True)
            assert w is ui.workshop  # Only one workshop window.
            assert w.editor.get('1.0', 'end-1c') == course_source
            assert len(w.state['experiments']) == 2
            with patch('workshop.simpledialog.askstring', return_value='Můj obrázek'):
                w.rename()
            replace(w, GOOD)
            w.notes.delete('1.0', 'end')
            w.notes.insert('1.0', 'Zkouším modrý kruh.')
            key = w.current
            w.run()
            assert w.busy
            assert not w.create_experiment('Během běhu')
            # Editing during a worker run must label the old result accurately.
            w.editor.insert('end', '# změněno při běhu\n')

            def good_done():
                assert w.console.get('1.0', 'end-1c').startswith('7\n')
                assert 'cislo = 7' in w.variables.get('1.0', 'end-1c')
                assert len(w.drawing) == 1
                assert len([x for x in w.canvas.find_all() if w.canvas.type(x) == 'oval']) == 1
                assert 'před poslední úpravou' in w.feedback.cget('text')
                replace(w, 'if :\n')
                w.run()
                wait_for(w, error_done)

            def error_done():
                assert 'SyntaxError' in w.console.get('1.0', 'end-1c')
                assert w.editor.tag_ranges('error')
                replace(w, 'while True: pass')
                w.run()
                wait_for(w, timeout_done)

            def timeout_done():
                assert 'Časový limit' in w.console.get('1.0', 'end-1c')
                replace(w, GOOD)
                w.save()
                w.duplicate()
                assert w.current != key
                assert w.editor.get('1.0', 'end-1c') == GOOD
                assert w.notes.get('1.0', 'end-1c') == 'Zkouším modrý kruh.'
                marker = folder / 'must-not-exist'
                imported = folder / 'importovany.py'
                source = f'from pathlib import Path\nPath({str(marker)!r}).write_text("ran")\n'
                imported.write_text(source)
                with patch('workshop.filedialog.askopenfilename', return_value=str(imported)):
                    w.import_file()
                assert w.editor.get('1.0', 'end-1c') == source
                assert not marker.exists()
                exported = folder / 'exportovany.py'
                with patch('workshop.filedialog.asksaveasfilename', return_value=str(exported)):
                    w.export_file()
                assert exported.read_text() == source
                replace(w, '# nepřepsat export')
                with patch('workshop.filedialog.asksaveasfilename', return_value=str(exported)), patch('workshop.messagebox.showinfo'):
                    w.export_file()
                assert exported.read_text() == source
                w.load(key)
                assert w.editor.get('1.0', 'end-1c') == GOOD
                old_save = w.store.save
                def reject(state):
                    raise WorkshopError('simulated conflict')
                w.store.save = reject
                count = len(w.state['experiments'])
                assert not w.create_experiment('Nesmí přepsat původní')
                assert len(w.state['experiments']) == count
                with patch('workshop.messagebox.askyesno', return_value=False):
                    ui.close()
                assert w.window.winfo_exists()
                assert ui.root.winfo_exists()
                w.store.save = old_save
                assert ui.editor.get('1.0', 'end-1c') == course_source
                assert ui.store.path.read_bytes() == course_bytes
                ui.close()

            wait_for(w, good_done)

        guarded(initial)

    result = app.launch(folder, on_ready=ready)
    if result or failures:
        raise AssertionError(f'GUI failed: {result}, {failures}')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        child(Path(sys.argv[1]), sys.argv[2])
    else:
        with tempfile.TemporaryDirectory(prefix='samantha-workshop-gui-') as temp:
            for phase in ('exercise', 'reopen'):
                subprocess.run([sys.executable, str(Path(__file__).resolve()), temp, phase], check=True, timeout=60)
            state = json.loads((Path(temp) / 'dilna.json').read_text())
            assert len(state['experiments']) == 4
        print('Workshop GUI OK: lesson copy, names/notes, real drawing/error/timeout, import/export, conflict, close/reopen, course preservation.')
