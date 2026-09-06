"""Optional real Tk smoke on a graphical Mac/Linux desktop, using temporary data only."""
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
from progress_store import LEGACY_IDS


def child(folder, phase):
    app.COURSE = load_course()
    app.LESSONS = app.COURSE['lessons']
    if phase == 'reopen':
        app.LESSONS.reverse()
    failures = []

    def ready(classroom):
        deadline = time.monotonic() + 45

        def protect(action):
            try:
                action()
            except BaseException as exc:
                failures.append(repr(exc))
                classroom.root.destroy()

        def advance():
            if time.monotonic() > deadline:
                raise AssertionError('GUI worker timed out')
            if classroom.busy:
                classroom.root.after(50, lambda: protect(advance))
                return
            lesson = app.LESSONS[classroom.current]
            assert lesson['id'] in classroom.completed, classroom.feedback.cget('text')
            assert classroom.drawing == app.execute_code(lesson['solution'])['commands']
            if classroom.current == 6:
                classroom.close()
                return
            classroom.load(classroom.current + 1)
            start()

        def start():
            lesson = app.LESSONS[classroom.current]
            classroom.editor.delete('1.0', 'end')
            classroom.editor.insert('1.0', lesson['solution'])
            classroom.run(True)
            classroom.root.after(50, lambda: protect(advance))

        def check_initial():
            if phase == 'reopen':
                # Reordering keeps the same selected lesson, drafts and completion.
                assert classroom.current == 0
                assert classroom.completed == set(LEGACY_IDS)
                for lesson in app.LESSONS:
                    assert classroom.drafts[lesson['id']] == lesson['solution']
                assert classroom.progress.cget('text') == 'Dokončeno 7 / 7'
                classroom.close()
                return
            assert classroom.current == 2
            assert classroom.editor.get('1.0', 'end-1c') == '# rozepsané počítání\n'
            assert classroom.completed == {LEGACY_IDS[0]}
            classroom.load(0)
            start()

        protect(check_initial)

    result = app.launch(folder, on_ready=ready)
    if result or failures:
        raise AssertionError(f'GUI failed: {result}, {failures}')


def main():
    if len(sys.argv) > 1:
        child(Path(sys.argv[1]), sys.argv[2])
        return
    with tempfile.TemporaryDirectory(prefix='samantha-classroom-gui-') as temp:
        folder = Path(temp)
        legacy = json.dumps({'version': 1, 'current': 2, 'completed': [0],
                             'drafts': {'2': '# rozepsané počítání\n'}}, ensure_ascii=False).encode()
        (folder / 'prubeh.json').write_bytes(legacy)
        for phase in ('exercise', 'reopen'):
            subprocess.run([sys.executable, str(Path(__file__).resolve()), str(folder), phase], check=True, timeout=60)
        assert (folder / 'prubeh.json').read_bytes() == legacy
        assert (folder / 'prubeh_v1_pred_prevodem.json').read_bytes() == legacy
        state = json.loads((folder / 'prubeh_v2.json').read_text())
        assert set(state['courses']['python-zaklady']['completed']) == set(LEGACY_IDS)
    print('GUI OK: v1 migration, seven real worker runs/checks/drawings, save, reopen, reordered lessons.')


if __name__ == '__main__':
    main()
