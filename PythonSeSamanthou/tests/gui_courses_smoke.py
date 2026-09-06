"""Real GUI test: switch courses, preserve drafts, run next seven, reopen. Temporary data only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import python_se_samanthou as app
from course_loader import load_course
from progress_store import ProgressError


def child(folder, phase):
    app.COURSE = load_course()
    app.LESSONS = app.COURSE['lessons']
    failures = []

    def ready(ui):
        deadline = time.monotonic() + 45
        first_id = app.LESSONS[0]['id']
        second_index = next(i for i, c in enumerate(ui.courses) if c['id'] == 'python-dalsi-kroky')

        def guarded(action):
            try:
                action()
            except BaseException as exc:
                failures.append(repr(exc))
                ui.root.destroy()

        def switch(index):
            ui.course_picker.current(index)
            ui.course_picker.event_generate('<<ComboboxSelected>>')

        def verify_saved_courses():
            switch(0)
            assert app.COURSE['id'] == 'python-zaklady'
            assert ui.current == 0
            assert ui.editor.get('1.0', 'end-1c') == '# můj původní pokus\n'
            assert ui.completed == {first_id}
            switch(second_index)
            assert ui.current == 6
            assert ui.completed == {x['id'] for x in app.LESSONS}
            for lesson in app.LESSONS:
                assert ui.drafts[lesson['id']] == lesson['solution']
            assert ui.progress.cget('text') == 'Dokončeno 7 / 7'
            # Running work and a failed save must keep the current course selected.
            ui.busy = True
            switch(0)
            assert ui.course_index == second_index
            assert ui.course_picker.current() == second_index
            ui.busy = False
            saved_method = ui.store.save
            def fail_save(state):
                raise ProgressError('simulated save failure')
            ui.store.save = fail_save
            switch(0)
            assert ui.course_index == second_index
            assert app.COURSE['id'] == 'python-dalsi-kroky'
            ui.store.save = saved_method
            ui.close()

        def advance():
            if time.monotonic() > deadline:
                raise AssertionError('GUI worker timed out')
            if ui.busy:
                ui.root.after(50, lambda: guarded(advance))
                return
            lesson = app.LESSONS[ui.current]
            assert lesson['id'] in ui.completed, ui.feedback.cget('text')
            assert ui.drawing == app.execute_code(lesson['solution'])['commands']
            if ui.current == 6:
                verify_saved_courses()
                return
            ui.next_lesson()
            start()

        def start():
            ui.editor.delete('1.0', 'end')
            ui.editor.insert('1.0', app.LESSONS[ui.current]['solution'])
            ui.run(True)
            ui.root.after(50, lambda: guarded(advance))

        def initial():
            if phase == 'reopen':
                verify_saved_courses()
                return
            ui.editor.delete('1.0', 'end')
            ui.editor.insert('1.0', '# můj původní pokus\n')
            ui.completed.add(first_id)
            switch(second_index)
            assert app.COURSE['id'] == 'python-dalsi-kroky'
            assert not ui.completed
            assert ui.current == 0
            start()

        guarded(initial)

    result = app.launch(folder, on_ready=ready)
    if result or failures:
        raise AssertionError(f'GUI failed: {result}, {failures}')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        child(Path(sys.argv[1]), sys.argv[2])
    else:
        with tempfile.TemporaryDirectory(prefix='samantha-courses-gui-') as temp:
            for phase in ('exercise', 'reopen'):
                subprocess.run([sys.executable, str(Path(__file__).resolve()), temp, phase], check=True, timeout=60)
            state = json.loads((Path(temp) / 'prubeh_v2.json').read_text())
            assert set(state['courses']) == {'python-zaklady', 'python-dalsi-kroky'}
        print('GUI courses OK: picker, seven new worker runs, independent drafts/progress, reopen, busy/save-failure guards.')
