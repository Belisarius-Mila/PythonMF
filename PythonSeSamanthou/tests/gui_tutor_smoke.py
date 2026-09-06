"""Real Tk typing and asynchronous tutor flow, with a fake Codex and temporary data."""
from pathlib import Path
import sys
import tempfile
import threading
import time
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workshop import WorkshopWindow
from ai_tutor import TutorError


def main():
    with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {}, clear=True):
        root = tk.Tk()
        failures = []
        root.report_callback_exception = lambda kind, exc, tb: failures.append(repr(exc))
        w = WorkshopWindow(root, folder, lambda source: {})
        w.window.geometry('900x640')
        root.update()
        def pump_until(condition):
            deadline = time.monotonic() + 8
            while not condition():
                assert time.monotonic() < deadline, 'GUI timeout'
                root.update()
                time.sleep(.01)
            root.update()
            assert not failures, failures
        def typing(widget):
            widget.focus_force()
            root.update()
            before = widget.get('1.0', 'end-1c')
            widget.mark_set('insert', 'end-1c')
            widget.event_generate('<KeyPress>', keysym='x')
            root.update()
            assert widget.get('1.0', 'end-1c') == before+'x'
            widget.event_generate('<KeyPress>', keysym='BackSpace')
            root.update()
            assert widget.get('1.0', 'end-1c') == before
            widget.event_generate('<KeyPress>', keysym='Return')
            root.update()
            assert widget.get('1.0', 'end-1c') == before+'\n'
            widget.event_generate('<Control-a>')
            root.update()
            assert widget.tag_ranges('sel')
            widget.event_generate('<KeyPress>', keysym='x')
            root.update()
            assert widget.get('1.0', 'end-1c') == 'x'
        typing(w.editor)
        typing(w.notes)
        assert w.save()
        w.open_tutor()
        root.update()
        typing(w.tutor.question)
        p = w.tutor
        assert p.question.winfo_height() >= 25
        assert p.transcript.winfo_height() >= 45
        assert p.disclosure.winfo_rooty()+p.disclosure.winfo_height() <= w.window.winfo_rooty()+w.window.winfo_height()
        calls = []
        released = threading.Event()
        def client(messages, cancel):
            calls.append(messages)
            assert released.wait(5)
            return 'Začneme příkazem print.'
        p.client = client
        p.settings()
        assert p.dialog.winfo_exists() and not calls
        with patch('tutor_panel.check_codex', side_effect=TutorError('Codex není nainstalovaný.')):
            p.connect('check')
            pump_until(lambda: not p.connecting)
            assert 'nainstalovaný' in p.connection_note
        with patch('tutor_panel.login_codex', return_value='Přihlášení přes ChatGPT ověřeno.'):
            p.connect('login')
            pump_until(lambda: not p.connecting)
            assert 'ChatGPT' in p.connection_note
        p.dialog.destroy()
        p.refresh()
        a = w.current
        original = w.editor.get('1.0', 'end-1c')
        p.question.delete('1.0', 'end')
        p.question.insert('1.0', 'Vysvětli tento kód.')
        p.send()
        assert p.pending and str(p.send_button['state']) == 'disabled'
        p.send()
        assert w.create_experiment('Druhý pokus', 'print(8)')
        b = w.current
        released.set()
        pump_until(lambda: p.pending is None)
        assert len(calls) == 1 and a in p.histories and b not in p.histories
        assert 'Začneme příkazem' not in p.transcript.get('1.0', 'end')
        w.load(a)
        assert 'Začneme příkazem' in p.transcript.get('1.0', 'end')
        assert w.editor.get('1.0', 'end-1c') == original
        w.last_results[a] = (original, {'output': 'old output', 'error': None})
        assert w.tutor_context()['result']
        w.editor.insert('end', '# změna')
        assert w.tutor_context()['result'] is None
        p.question.insert('1.0', 'Proč právě print?')
        p.send()
        w.editor.insert('end', '\n# při čekání')
        pump_until(lambda: p.pending is None)
        assert len(calls[-1]) == 3
        assert calls[-1][1]['role'] == 'assistant'
        assert '# změna' in calls[-1][-1]['content']
        assert 'old output' not in calls[-1][-1]['content']
        assert 'Kód jsi od poslední odpovědi změnil' in p.transcript.get('1.0', 'end')
        assert '# při čekání' in w.editor.get('1.0', 'end')
        w.load(b)
        p.send()
        pump_until(lambda: p.pending is None)
        assert len(calls[-1]) == 1
        def fail(*args):
            raise TutorError('Zkontroluj internet.')
        p.client = fail
        p.question.insert('1.0', 'Zopakuj to.')
        p.send()
        pump_until(lambda: p.pending is None)
        assert 'internet' in p.status['text']
        assert p.question.get('1.0', 'end-1c') == 'Zopakuj to.'
        assert len(p.histories[b]) == 1
        def cancelled(messages, cancel):
            assert cancel.wait(5)
            raise TutorError('Požadavek byl zastaven.')
        p.client = cancelled
        p.send()
        p.stop()
        pump_until(lambda: p.pending is None)
        assert 'zastaven' in p.status['text']
        assert p.question.get('1.0', 'end-1c') == 'Zopakuj to.'
        assert str(p.send_button['state']) == 'normal'
        p.reset()
        assert b not in p.histories and a in p.histories
        assert w.save()
        raw = (Path(folder)/'dilna.json').read_text()
        assert 'synthetic-secret' not in raw and 'Začneme příkazem' not in raw
        w.close()
        assert p.cancel.is_set() and not p.histories
        root.destroy()
        assert not failures, failures
    print('GUI tutor OK: keyboard, minimum layout, ChatGPT setup, follow-up, isolation, stale code, failure, no secret persistence.')


if __name__ == '__main__':
    main()
