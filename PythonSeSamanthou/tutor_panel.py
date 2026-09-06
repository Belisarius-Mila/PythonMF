"""Tk tutor with per-experiment, session-only conversations and background requests."""
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import webbrowser

from ai_tutor import DEFAULT_MODEL, TutorError, ask_tutor, context_message, validate_settings


class TutorPanel(ttk.Frame):
    def __init__(self, parent, get_context, client=ask_tutor):
        super().__init__(parent)
        self.get_context, self.client = get_context, client
        self.key, self.model = os.environ.get('OPENAI_API_KEY', ''), DEFAULT_MODEL
        self.histories = {}
        self.pending = None
        self.queue = queue.Queue()
        self.dialog = None
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Button(top, text='Nastavení AI…', command=self.settings).pack(side='left')
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
        self.send_button = ttk.Button(self, text='Zeptat se AI', command=self.send)
        self.send_button.pack(fill='x', pady=3)
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
        ttk.Label(box, text='Potřebuješ vlastní OpenAI API klíč a kredit na API účtu.\n'
                  'Klíč zůstane jen v paměti do zavření dílny.\n'
                  'Uložení nastavení ještě nic neodesílá.', wraplength=430).pack(anchor='w')
        ttk.Button(box, text='Otevřít stránku pro vytvoření API klíče',
                   command=lambda: webbrowser.open('https://platform.openai.com/api-keys')).pack(anchor='w', pady=8)
        ttk.Label(box, text='API klíč (nepatří do rozhovoru ani poznámek):').pack(anchor='w')
        key = ttk.Entry(box, show='•', width=45)
        key.insert(0, self.key)
        key.pack(fill='x')
        ttk.Label(box, text='Model:').pack(anchor='w', pady=(8, 0))
        model = ttk.Entry(box, width=45)
        model.insert(0, self.model)
        model.pack(fill='x')
        def apply():
            try:
                new_key, new_model = validate_settings(key.get(), model.get())
            except TutorError as exc:
                messagebox.showerror('Nastavení AI', str(exc), parent=dialog)
                return
            self.key, self.model = new_key, new_model
            dialog.destroy()
            self.refresh()
            self.question.focus_set()
        ttk.Button(box, text='Použít pro tuto dílnu', command=apply).pack(fill='x', pady=(12, 0))
        key.focus_set()

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
            label = 'Připraveno. Otázka se odešle až tlačítkem.' if self.key else 'AI není připojená. Začni v Nastavení AI.'
        self.status.configure(text=label)
        self.send_button.configure(state='disabled' if self.pending else 'normal')

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
        if self.pending:
            return
        if not self.key:
            self.settings()
            return
        context = self.get_context()
        question = self.question.get('1.0', 'end-1c').strip() or self.mode.get()
        try:
            message = context_message(context, question)
            key, model = validate_settings(self.key, self.model)
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
        self.refresh()
        self.question.delete('1.0', 'end')
        def work():
            try:
                answer, failure = self.client(key, model, messages), None
            except TutorError as exc:
                answer, failure = None, str(exc)
            except Exception:
                answer, failure = None, 'AI se nepodařilo získat. Zkus to znovu.'
            self.queue.put((pending, answer, failure))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            pending, answer, failure = self.queue.get_nowait()
        except queue.Empty:
            return
        self.pending = None
        if not failure:
            turns = self.histories.setdefault(pending['key'], [])
            turns.append(dict(pending, answer=answer))
            del turns[:-6]
        self.refresh()
        if failure:
            self.status.configure(text=failure)
            if pending['key'] == self.get_context()['key'] and not self.question.get('1.0', 'end-1c'):
                self.question.insert('1.0', pending['question'])

    def clear_session(self):
        self.key = ''
        self.histories.clear()
