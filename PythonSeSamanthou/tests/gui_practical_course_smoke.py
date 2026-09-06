"""Three-course GUI test; can run unmodified inside the preserved 1.5 distribution."""
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

NEW_ID = 'python-prakticke-ulohy'
OLD_IDS = ('python-zaklady', 'python-dalsi-kroky')


def child(folder, phase):
    app.COURSE = load_course()
    app.LESSONS = app.COURSE['lessons']
    failures = []
    def ready(ui):
        deadline = time.monotonic()+50
        def guard(action):
            try:
                action()
            except BaseException as exc:
                failures.append(repr(exc))
                ui.root.destroy()
        ui.root.report_callback_exception = lambda kind, exc, tb: (failures.append(repr(exc)), ui.root.destroy())
        def switch(course_id):
            ui.course_picker.current(next(i for i,c in enumerate(ui.courses) if c['id']==course_id))
            ui.course_picker.event_generate('<<ComboboxSelected>>')
            assert app.COURSE['id']==course_id
        def verify():
            for course_id in OLD_IDS:
                switch(course_id)
                assert ui.current==0
                assert ui.editor.get('1.0','end-1c')=='# Zachovaný pokus '+course_id+'\n'
                assert ui.completed=={app.LESSONS[0]['id']}
            switch(NEW_ID)
            assert ui.current==6
            assert ui.completed=={l['id'] for l in app.LESSONS}
            assert ui.progress['text']=='Dokončeno 7 / 7'
            for lesson in app.LESSONS:
                assert ui.drafts[lesson['id']]==lesson['solution']
            ui.close()
        def advance():
            assert time.monotonic()<deadline,'GUI timeout'
            if ui.busy:
                ui.root.after(50,lambda:guard(advance))
                return
            assert app.LESSONS[ui.current]['id'] in ui.completed,ui.feedback['text']
            if ui.current==6:
                verify()
            else:
                ui.next_lesson()
                start()
        def start():
            ui.editor.delete('1.0','end')
            ui.editor.insert('1.0',app.LESSONS[ui.current]['solution'])
            ui.run(True)
            ui.root.after(50,lambda:guard(advance))
        def initial():
            assert len(ui.courses)==3
            if phase=='reopen':
                verify()
                return
            for course_id in OLD_IDS:
                switch(course_id)
                ui.editor.delete('1.0','end')
                ui.editor.insert('1.0','# Zachovaný pokus '+course_id+'\n')
                ui.completed.add(app.LESSONS[0]['id'])
            switch(NEW_ID)
            assert not ui.completed
            start()
        guard(initial)
    result=app.launch(folder,on_ready=ready)
    assert not result and not failures,(result,failures)


if __name__=='__main__':
    if len(sys.argv)>1:
        child(Path(sys.argv[1]),sys.argv[2])
    else:
        with tempfile.TemporaryDirectory(prefix='samantha-practical-gui-') as temp:
            for phase in ('exercise','reopen'):
                subprocess.run([sys.executable,str(Path(__file__).resolve()),temp,phase],check=True,timeout=65)
            state=json.loads((Path(temp)/'prubeh_v2.json').read_text())
            assert set(state['courses'])=={NEW_ID,*OLD_IDS}
        print('GUI practical OK: three courses, seven runs/checks, previous drafts/progress preserved, reopen.')
