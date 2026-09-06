"""A separate Tk window for personal experiments, using the classroom's worker."""
import io
import keyword
from pathlib import Path
import queue
import re
import threading
import tokenize
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from drawing import draw_commands
from tutor_panel import TutorPanel
from workshop_store import WorkshopError, WorkshopStore, add_experiment, export_python, import_python


class WorkshopWindow:
    def __init__(self, parent, directory, runner):
        self.store = WorkshopStore(directory)
        self.state = self.store.load()  # Fail before creating a window if data is invalid.
        self.runner = runner
        self.current = None
        self.busy = False
        self.loading = False
        self.save_after = None
        self.poll_after = None
        self.queue = queue.Queue()
        self.drawing = []
        self.last_results = {}
        self.window = tk.Toplevel(parent)
        self.window.title('Moje dílna · Python se Samanthou 1.4')
        self.window.geometry(f'{min(1100, parent.winfo_screenwidth()-60)}x{min(780, parent.winfo_screenheight()-100)}')
        self.window.minsize(900, 640)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        header = ttk.Frame(self.window, padding=12)
        header.pack(fill='x')
        ttk.Label(header, text='Moje dílna', font=('Arial', 20, 'bold')).pack(side='left')
        ttk.Label(header, text='Vlastní pokusy · ukládají se automaticky', padding=(18, 0)).pack(side='left')
        body = ttk.Frame(self.window, padding=(12, 0, 12, 8))
        body.pack(fill='both', expand=True)
        sidebar = ttk.Frame(body)
        sidebar.pack(side='left', fill='y', padx=(0, 12))
        ttk.Label(sidebar, text='MOJE POKUSY').pack(anchor='w', pady=(0, 6))
        list_frame = ttk.Frame(sidebar)
        list_frame.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(list_frame, width=23, height=9, exportselection=False)
        scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.select)
        for label, command in [('Nový pokus', self.new), ('Přejmenovat', self.rename),
                               ('Vytvořit kopii', self.duplicate), ('Otevřít .py…', self.import_file),
                               ('Exportovat .py…', self.export_file)]:
            ttk.Button(sidebar, text=label, command=command).pack(fill='x', pady=3)
        ttk.Label(sidebar, text='Kód z lekce sem přeneseš\ntlačítkem Do dílny v učebně.',
                  wraplength=190).pack(anchor='w', pady=8)

        main = ttk.Frame(body)
        main.pack(fill='both', expand=True)
        self.title = ttk.Label(main, text='', font=('Arial', 14, 'bold'), wraplength=650)
        self.title.pack(anchor='w', pady=(0, 6))
        actions = ttk.Frame(main)
        actions.pack(fill='x', pady=(0, 6))
        self.run_button = ttk.Button(actions, text='Spustit (F5)', command=self.run)
        self.run_button.pack(side='left')
        ttk.Button(actions, text='Uložit', command=self.save).pack(side='left', padx=6)
        ttk.Button(actions, text='Upravit kód', command=self.edit_code).pack(side='left')
        ttk.Button(actions, text='AI průvodce', command=self.open_tutor).pack(side='left', padx=6)
        self.feedback = ttk.Label(main, text='Napiš vlastní kód nebo otevři soubor .py.', wraplength=640)
        self.feedback.pack(fill='x', pady=(0, 8))
        split = ttk.Panedwindow(main, orient='horizontal')
        split.pack(fill='both', expand=True)
        code_frame = ttk.Frame(split)
        ttk.Label(code_frame, text='MŮJ KÓD — sem piš nebo vlož Python').pack(anchor='w', pady=(0, 4))
        self.editor = ScrolledText(code_frame, wrap='none', undo=True, state='normal', takefocus=True, width=32, height=13,
                                   font=('Courier', 13), bg='#152238', fg='#e4edf7', insertbackground='white')
        self.editor.pack(fill='both', expand=True)
        self.enable_editing(self.editor)
        for name, color in [('keyword', '#c7abff'), ('string', '#90d6ac'), ('number', '#f8ce75'), ('comment', '#9cacc4')]:
            self.editor.tag_configure(name, foreground=color)
        self.editor.tag_configure('error', background='#733744')
        self.editor.bind('<<Modified>>', self.modified)
        self.editor.bind('<Tab>', self.tab)
        self.editor.bind('<Return>', self.newline)
        self.editor.bind('<Control-Return>', self.run_key)
        self.window.bind('<F5>', self.run_key)
        self.window.bind('<Control-s>', self.save_key)
        split.add(code_frame, weight=1)
        self.tabs = ttk.Notebook(split)
        self.console = ScrolledText(self.tabs, width=30, wrap='word', state='disabled', font=('Courier', 12))
        self.canvas = tk.Canvas(self.tabs, width=320, height=240, highlightthickness=0)
        self.variables = ScrolledText(self.tabs, width=30, wrap='word', state='disabled', font=('Courier', 12))
        self.tabs.add(self.console, text='Výpis')
        self.tabs.add(self.canvas, text='Obrázek')
        self.tabs.add(self.variables, text='Proměnné')
        self.tutor = TutorPanel(self.tabs, self.tutor_context)
        self.tabs.add(self.tutor, text='AI průvodce')
        self.canvas.bind('<Configure>', lambda event: self.draw())
        split.add(self.tabs, weight=1)
        ttk.Label(main, text='MOJE POZNÁMKY — co chci zkusit, co jsem zjistil').pack(anchor='w', pady=(8, 4))
        self.notes = ScrolledText(main, height=3, wrap='word', font=('Arial', 12))
        self.notes.pack(fill='x')
        self.enable_editing(self.notes)
        self.enable_editing(self.tutor.question)
        self.notes.bind('<<Modified>>', self.modified)
        self.saved = ttk.Label(self.window, text='', padding=(12, 5), wraplength=850)
        self.saved.pack(fill='x')
        self.window.bind('<Configure>', lambda event: self.saved.configure(wraplength=max(400, self.window.winfo_width()-24)))
        if not self.state['experiments']:
            add_experiment(self.state, 'První pokus', 'print("Moje dílna!")\n')
        selected = self.state.get('current') or next(iter(self.state['experiments']))
        self.load(selected)
        self.window.after_idle(self.edit_code)
        self.poll_after = self.window.after(100, self.poll)

    @staticmethod
    def enable_editing(widget):
        widget.configure(state='normal', takefocus=True)
        widget.bind('<Button-1>', lambda event: widget.focus_set(), add='+')
        menu = tk.Menu(widget, tearoff=False)
        for label, action in [('Vyjmout', '<<Cut>>'), ('Kopírovat', '<<Copy>>'), ('Vložit', '<<Paste>>')]:
            menu.add_command(label=label, command=lambda action=action: widget.event_generate(action))
        def select_all(event=None):
            widget.tag_add('sel', '1.0', 'end-1c')
            return 'break'
        menu.add_command(label='Vybrat vše', command=select_all)
        widget.bind('<Control-a>', select_all)
        def popup(event):
            widget.focus_set()
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return 'break'
        widget.bind('<Button-3>', popup)
        if widget.tk.call('tk', 'windowingsystem') == 'aqua':
            widget.bind('<Button-2>', popup)

    def edit_code(self):
        self.editor.configure(state='normal')
        self.editor.focus_set()

    def open_tutor(self):
        self.tutor.refresh()
        self.tabs.select(self.tutor)
        self.tutor.question.focus_set()

    def tutor_context(self):
        item = self.state['experiments'].get(self.current, {})
        source = self.editor.get('1.0', 'end-1c')
        previous = self.last_results.get(self.current)
        return {'key': self.current, 'title': item.get('title', ''), 'source': source,
                'notes': self.notes.get('1.0', 'end-1c') if hasattr(self, 'notes') else '',
                'result': previous[1] if previous and previous[0] == source else None}

    @staticmethod
    def set_text(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')

    def refresh_list(self):
        self.ids = list(self.state['experiments'])
        self.listbox.delete(0, 'end')
        for key in self.ids:
            self.listbox.insert('end', self.state['experiments'][key]['title'])
        if self.current in self.ids:
            index = self.ids.index(self.current)
            self.listbox.selection_set(index)
            self.listbox.see(index)

    def load(self, key):
        if self.busy or (self.current is not None and not self.save()):
            self.refresh_list()
            return False
        self.current = key
        self.state['current'] = key
        item = self.state['experiments'][key]
        self.loading = True
        for widget, text in [(self.editor, item['source']), (self.notes, item['notes'])]:
            widget.configure(state='normal')
            widget.delete('1.0', 'end')
            widget.insert('1.0', text)
            widget.edit_modified(False)
        self.editor.edit_reset()
        self.loading = False
        self.title.configure(text=item['title'])
        self.feedback.configure(text='Uprav kód a spusť ho. Tento pokus nemá školní hodnocení.')
        self.set_text(self.console, 'Tady se objeví výpis programu.')
        self.set_text(self.variables, 'Po běhu uvidíš konečné hodnoty čísel, textů a ano/ne.')
        self.drawing = []
        self.draw()
        self.tabs.select(0)
        self.highlight()
        self.refresh_list()
        self.tutor.refresh()
        return self.save()

    def select(self, event=None):
        selection = self.listbox.curselection()
        if selection and self.ids[selection[0]] != self.current:
            self.load(self.ids[selection[0]])

    def save(self):
        if self.save_after is not None:
            self.window.after_cancel(self.save_after)
            self.save_after = None
        if self.current is None:
            return True
        item = self.state['experiments'][self.current]
        item.update(source=self.editor.get('1.0', 'end-1c'), notes=self.notes.get('1.0', 'end-1c'))
        try:
            self.store.save(self.state)
        except (OSError, ValueError) as exc:
            self.saved.configure(text=f'Pokus není uložen: {exc} Můžeš si kód zkopírovat nebo exportovat.')
            return False
        self.saved.configure(text='Pokus i poznámky jsou uložené na tomto počítači.')
        return True

    def modified(self, event):
        widget = event.widget
        if not widget.edit_modified():
            return
        widget.edit_modified(False)
        if self.loading:
            return
        if widget is self.editor:
            self.editor.tag_remove('error', '1.0', 'end')
            self.highlight()
        if self.save_after is not None:
            self.window.after_cancel(self.save_after)
        self.saved.configure(text='Ukládám pokus…')
        self.save_after = self.window.after(700, self.save)

    def highlight(self):
        for tag in ('keyword', 'string', 'number', 'comment'):
            self.editor.tag_remove(tag, '1.0', 'end')
        try:
            for token in tokenize.generate_tokens(io.StringIO(self.editor.get('1.0', 'end-1c')).readline):
                tag = {tokenize.STRING: 'string', tokenize.NUMBER: 'number', tokenize.COMMENT: 'comment'}.get(token.type)
                if token.type == tokenize.NAME and keyword.iskeyword(token.string):
                    tag = 'keyword'
                if tag:
                    self.editor.tag_add(tag, f'{token.start[0]}.{token.start[1]}', f'{token.end[0]}.{token.end[1]}')
        except (tokenize.TokenError, SyntaxError):
            pass

    def create_experiment(self, title, source='', notes=''):
        if self.busy or not self.save():
            return False
        try:
            key = add_experiment(self.state, title, source, notes)
        except WorkshopError as exc:
            messagebox.showerror('Pokus nelze vytvořit', str(exc), parent=self.window)
            return False
        return self.load(key)

    def new(self):
        if self.busy:
            return
        title = simpledialog.askstring('Nový pokus', 'Jak se bude pokus jmenovat?', parent=self.window)
        if title is not None:
            self.create_experiment(title)

    def rename(self):
        if self.busy:
            return
        item = self.state['experiments'][self.current]
        title = simpledialog.askstring('Přejmenovat pokus', 'Nový název:', initialvalue=item['title'], parent=self.window)
        if title is None:
            return
        title = title.strip()
        if not title or len(title) > 80 or '\n' in title or '\r' in title:
            messagebox.showerror('Neplatný název', 'Použij název na jednom řádku, nejvýše 80 znaků.', parent=self.window)
            return
        item['title'] = title
        self.title.configure(text=title)
        self.refresh_list()
        self.save()

    def duplicate(self):
        item = self.state['experiments'][self.current]
        self.create_experiment((item['title'][:72] + ' — kopie')[:80],
                               self.editor.get('1.0', 'end-1c'), self.notes.get('1.0', 'end-1c'))

    def import_file(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(parent=self.window, title='Otevřít kopii Python souboru', filetypes=[('Python', '*.py')])
        if path:
            try:
                source = import_python(path)
            except (OSError, WorkshopError) as exc:
                messagebox.showerror('Soubor nelze otevřít', str(exc), parent=self.window)
                return
            self.create_experiment(Path(path).stem[:80] or 'Otevřený pokus', source)

    def export_file(self):
        path = filedialog.asksaveasfilename(parent=self.window, title='Exportovat jako nový soubor',
                                           defaultextension='.py', initialfile='muj_pokus.py', filetypes=[('Python', '*.py')])
        if path:
            try:
                export_python(path, self.editor.get('1.0', 'end-1c'))
            except FileExistsError:
                messagebox.showinfo('Soubor už existuje', 'Zvol jiné jméno; existující soubor zůstává zachovaný.', parent=self.window)
            except OSError as exc:
                messagebox.showerror('Export se nepodařil', str(exc), parent=self.window)
            else:
                self.feedback.configure(text='Kód je exportovaný. Kreslicí pomocníci vyžadují spuštění v učebně; poznámky zůstávají v dílně.')

    def run_key(self, event=None):
        self.run()
        return 'break'

    def save_key(self, event=None):
        self.save()
        return 'break'

    def tab(self, event):
        if self.editor.tag_ranges('sel'):
            self.editor.delete('sel.first', 'sel.last')
        self.editor.insert('insert', '    ')
        return 'break'

    def newline(self, event):
        if self.editor.tag_ranges('sel'):
            self.editor.delete('sel.first', 'sel.last')
        prefix = self.editor.get('insert linestart', 'insert')
        indent = re.match(r' *', prefix).group()
        self.editor.insert('insert', '\n' + indent + ('    ' if prefix.rstrip().endswith(':') else ''))
        return 'break'

    def run(self):
        if self.busy or not self.save():
            return
        source = self.editor.get('1.0', 'end-1c')
        key = self.current
        self.busy = True
        self.run_button.configure(state='disabled')
        self.feedback.configure(text='Program běží…')
        self.editor.tag_remove('error', '1.0', 'end')
        def work():
            self.queue.put((key, source, self.runner(source)))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        self.tutor.poll()
        try:
            key, source, result = self.queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.run_button.configure(state='normal')
            self.show_result(key, source, result)
        self.poll_after = self.window.after(100, self.poll)

    def show_result(self, key, source, result):
        self.last_results[key] = (source, result)
        error = result['error']
        unchanged = key == self.current and source == self.editor.get('1.0', 'end-1c')
        output = result['output'] or 'Program nic nevypsal. Výpis vzniká příkazem print().'
        if error:
            output += f"\n\n{error['type']}\n{error['tip']}\n{error['detail']}"
            if error['line'] and unchanged:
                self.editor.tag_add('error', f"{error['line']}.0", f"{error['line']}.end")
                self.editor.see(f"{error['line']}.0")
        self.set_text(self.console, output)
        self.set_text(self.variables, '\n\n'.join(f'{k} = {v!r}' for k, v in result['variables'].items()) or 'Žádné jednoduché konečné proměnné.')
        self.drawing = result['commands']
        self.draw()
        self.tabs.select(1 if self.drawing and not error else 0)
        text = 'Program doběhl. Porovnej výsledek se svým očekáváním.'
        if not unchanged:
            text = 'Výsledek patří ke kódu před poslední úpravou. Spusť upravený kód znovu.'
        elif error:
            text = 'V záložce Výpis najdeš vysvětlení chyby.'
        self.feedback.configure(text=text)

    def draw(self):
        draw_commands(self.canvas, self.drawing)

    def close(self):
        if not self.save() and not messagebox.askyesno('Pokus není uložen',
                'Zavřít bez uložení? Nejdřív si zkopíruj nebo exportuj svůj kód.', parent=self.window):
            return False
        if self.poll_after is not None:
            self.window.after_cancel(self.poll_after)
        self.tutor.clear_session()
        self.window.destroy()
        return True
