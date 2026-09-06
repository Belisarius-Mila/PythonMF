"""Tk tutor with per-experiment, session-only conversations and background requests."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import webbrowser

from ai_tutor import TutorError, ask_tutor, context_message, check_codex, login_codex


class TutorPanel(ttk.Frame):
    def __init__(self, parent, get_context, client=ask_tutor):
        super().__init__(parent)
        self.get_context, self.client = get_context, client
        self.cancel = threading.Event()
        self.connecting = False
        self.connection_queue = queue.Queue()
        self.connection_note = 'Přihlášení přes ChatGPT ověříme před dotazem.'
        self.histories = {}
        self.pending = None
        self.queue = queue.Queue()
        self.dialog = None
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Button(top, text='Připojení AI…', command=self.settings).pack(side='left')
        ttk.Button(top, text='Nový rozhovor', command=self.reset).pack(side='left', padx=3)
        self.transcript = ScrolledText(self, state='disabled', width=28, height=7, wrap='word', font=('Arial', 12))
        self.transcript.pack(fill='both', expand=True, pady=4)
        self.status = ttk.Label(self, text='', wraplength=280)
        self.status.pack(fill='x')
        # A combobox keeps all three modes usable at the minimum window width.
        self.mode = ttk.Combobox(self, state='readonly', values=(
            'Vysvětli krok za krokem', 'Pomoz mi s chybou', 'Veď mě dalším krokem'))
        self.mode.current(0)
        self.mode.pack(fill='x', pady=(4, 2))
        ttk.Label(self, text='Otázka / doptání (může zůstat prázdné):').pack(anchor='w')
        self.question = ScrolledText(self, height=2, width=28, wrap='word', undo=True, state='normal')
        self.question.pack(fill='x')
        self.question.bind('<Control-Return>', self.send_key)
        send_row = ttk.Frame(self)
        send_row.pack(fill='x', pady=3)
        self.send_button = ttk.Button(send_row, text='Zeptat se AI', command=self.send)
        self.send_button.pack(side='left', fill='x', expand=True)
        self.stop_button = ttk.Button(send_row, text='Zastavit', command=self.stop, state='disabled')
        self.stop_button.pack(side='left')
        self.disclosure = ttk.Label(self, text='Tlačítko odešle kód, poznámky, aktuální výpis a rozhovor do OpenAI. AI může chybovat.', wraplength=280)
        self.disclosure.pack(fill='x')
        self.bind('<Configure>', self.resize)
        self.refresh()

    def resize(self, event):
        for label in (self.status, self.disclosure):
            label.configure(wraplength=max(180, event.width-8))

    def settings(self):
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        dialog = self.dialog = tk.Toplevel(self)
        dialog.title('Připojit AI průvodce')
        dialog.transient(self.winfo_toplevel())
        box = ttk.Frame(dialog, padding=16)
        box.pack(fill='both', expand=True)
        ttk.Label(box, text='AI používá Codex přihlášený přes tvůj účet ChatGPT.\n'
                  'Čerpá limit Codexu tvého tarifu; API klíč se nepoužívá.\n'
                  'Přihlášení proběhne v prohlížeči, rozhovor pak zůstane v dílně.', wraplength=440).pack(anchor='w')
        ttk.Button(box, text='1. Návod k instalaci Codexu (Linux / Mac)',
                   command=lambda: webbrowser.open('https://learn.chatgpt.com/docs/cli')).pack(fill='x', pady=8)
        self.login_button = ttk.Button(box, text='2. Přihlásit přes ChatGPT', command=lambda: self.connect('login'))
        self.login_button.pack(fill='x')
        self.check_button = ttk.Button(box, text='3. Ověřit připojení', command=lambda: self.connect('check'))
        self.check_button.pack(fill='x', pady=8)
        self.connection_label = ttk.Label(box, text=self.connection_note, wraplength=440)
        self.connection_label.pack(fill='x')
        ttk.Label(box, text='Pokud se prohlížeč neotevře, spusť v terminálu: codex login\n'
                  'Potom zde ověř připojení. Vyžaduje Codex 0.153.0 nebo novější.', wraplength=440).pack(fill='x', pady=8)
        ttk.Button(box, text='Zpět do dílny', command=dialog.destroy).pack(fill='x')
        self.update_connection()

    def update_connection(self):
        if self.dialog is not None and self.dialog.winfo_exists():
            self.connection_label.configure(text=self.connection_note)
            state = 'disabled' if self.connecting or self.pending else 'normal'
            self.login_button.configure(state=state)
            self.check_button.configure(state=state)

    def connect(self, action):
        if self.pending or self.connecting:
            return
        self.connecting = True
        self.cancel.clear()
        self.connection_note = ('Dokonči přihlášení v prohlížeči…' if action == 'login' else 'Ověřuji instalaci a přihlášení…')
        self.refresh()
        def work():
            try:
                if action == 'login':
                    note = login_codex(self.cancel)
                else:
                    check_codex(self.cancel)
                    note = 'Připojení přes ChatGPT ověřeno. Můžeš se ptát v dílně.'
            except TutorError as exc:
                note = str(exc)
            except Exception:
                note = 'Připojení se nepodařilo ověřit. Zkus codex login v terminálu.'
            self.connection_queue.put(note)
        threading.Thread(target=work, daemon=True).start()

    def stop(self):
        self.cancel.set()
        self.status.configure(text='Zastavuji požadavek…')

    def refresh(self):
        context = self.get_context()
        turns = self.histories.get(context['key'], [])
        text = 'Samantha ti vysvětlí kód a nabídne malé kroky.\nRozhovory jsou oddělené podle pokusu a platí do zavření dílny.\n'
        for turn in turns:
            text += '\nTy: ' + turn['question'] + '\n\nSamantha: ' + turn['answer'] + '\n'
        if turns and turns[-1]['source'] != context['source']:
            text += '\n[Kód jsi od poslední odpovědi změnil. Další otázka pošle novou podobu.]\n'
        self.transcript.configure(state='normal')
        self.transcript.delete('1.0', 'end')
        self.transcript.insert('1.0', text)
        self.transcript.configure(state='disabled')
        self.transcript.see('end')
        if self.pending:
            label = 'AI přemýšlí…' if self.pending['key'] == context['key'] else 'AI ještě odpovídá u jiného pokusu…'
        else:
            label = self.connection_note
        self.status.configure(text=label)
        self.send_button.configure(state='disabled' if self.pending or self.connecting else 'normal')
        self.stop_button.configure(state='normal' if self.pending or self.connecting else 'disabled')
        self.update_connection()

    def reset(self):
        if self.pending:
            self.status.configure(text='Nejprve počkej na rozepsanou odpověď.')
            return
        self.histories.pop(self.get_context()['key'], None)
        self.refresh()

    def send_key(self, event=None):
        self.send()
        return 'break'

    def send(self):
        if self.pending or self.connecting:
            return
        context = self.get_context()
        question = self.question.get('1.0', 'end-1c').strip() or self.mode.get()
        try:
            message = context_message(context, question)
        except TutorError as exc:
            self.status.configure(text=str(exc))
            return
        # Bound history to five complete prior turns; never mix experiment identities.
        history = self.histories.get(context['key'], [])[-5:]
        messages = []
        for turn in history:
            messages.extend((turn['message'], {'role': 'assistant', 'content': turn['answer']}))
        messages.append(message)
        pending = dict(key=context['key'], source=context['source'], question=question, message=message)
        self.pending = pending
        self.cancel.clear()
        self.refresh()
        self.question.delete('1.0', 'end')
        def work():
            try:
                answer, failure = self.client(messages, self.cancel), None
            except TutorError as exc:
                answer, failure = None, str(exc)
            except Exception:
                answer, failure = None, 'AI se nepodařilo získat. Zkus to znovu.'
            self.queue.put((pending, answer, failure))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            self.connection_note = self.connection_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.connecting = False
            self.refresh()
        try:
            pending, answer, failure = self.queue.get_nowait()
        except queue.Empty:
            return
        self.pending = None
        if not failure:
            self.connection_note = 'Připojeno přes ChatGPT. Můžeš položit další otázku.'
            turns = self.histories.setdefault(pending['key'], [])
            turns.append(dict(pending, answer=answer))
            del turns[:-6]
        self.refresh()
        if failure:
            self.status.configure(text=failure)
            if pending['key'] == self.get_context()['key'] and not self.question.get('1.0', 'end-1c'):
                self.question.insert('1.0', pending['question'])

    def clear_session(self):
        self.cancel.set()
        self.histories.clear()
