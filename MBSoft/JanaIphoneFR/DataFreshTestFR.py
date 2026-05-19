import json
import os
import shutil
import time
from pathlib import Path

import ui
from datafresh_sync import refresh_files_from_icloud

try:
    import console
except Exception:
    console = None

try:
    import dialogs
except Exception:
    dialogs = None


BASE_DIR = Path(__file__).parent
SOURCES_FILE = BASE_DIR / 'datafresh_sources.json'
LOG_FILE = BASE_DIR / 'datafresh_test.log'
FILES = ['VocabularyFR.csv', 'VerbeFR.csv']


def log(event, **meta):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    payload = ' | '.join(f'{k}={repr(v)}' for k, v in meta.items())
    line = f'{ts} | {event}'
    if payload:
        line += ' | ' + payload
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def load_sources():
    if not SOURCES_FILE.exists():
        return {}
    try:
        with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if v}
    except Exception as exc:
        log('load_sources.error', error=repr(exc))
    return {}


def save_sources(sources):
    with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


def describe_path(path):
    if not path:
        return 'neni vybrano'
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    return f'{path}\nexists={exists}, size={size}'


class DataFreshTest(ui.View):
    def __init__(self):
        self.name = 'DataFresh FR test'
        self.background_color = '#f2f2f7'
        self.sources = load_sources()
        self.setup_ui()
        self.refresh_labels()

    def setup_ui(self):
        self.status = ui.TextView(
            frame=(10, 10, 380, 210),
            editable=False,
            font=('<system>', 13),
            background_color='white',
        )
        self.add_subview(self.status)

        y = 235

        self.btn_copy = ui.Button(
            frame=(10, y, 380, 44),
            title='Rychly test DataFresh bez vyberu',
            background_color='#34c759',
            tint_color='white',
            corner_radius=8,
        )
        self.btn_copy.action = self.copy_action
        self.add_subview(self.btn_copy)

        self.btn_reload = ui.Button(
            frame=(10, y + 54, 380, 44),
            title='Znovu nacist JSON',
            background_color='#8e8e93',
            tint_color='white',
            corner_radius=8,
        )
        self.btn_reload.action = self.reload_action
        self.add_subview(self.btn_reload)

    def set_status(self, text):
        self.status.text = text
        log('status', text=text)

    def refresh_labels(self):
        lines = ['Mapovani DataFresh:', '']
        for filename in FILES:
            lines.append(filename + ':')
            lines.append(describe_path(self.sources.get(filename)))
            lines.append('')
        self.status.text = '\n'.join(lines)

    def copy_action(self, sender):
        result = refresh_files_from_icloud(
            local_dir=str(BASE_DIR),
            filenames=FILES,
            app_dir_hints=('PythonMF/VocabularyFR', 'PythonMF', 'VocabularyFR'),
            source_overrides=self.sources,
            strict=True,
            allow_recursive=False,
            fast=True,
            max_attempts=1,
        )
        lines = ['Rychly test hotov.', '']
        if result.get('updated'):
            lines.append('Aktualizovano: ' + ', '.join(result['updated']))
        if result.get('unchanged'):
            lines.append('Uz aktualni: ' + ', '.join(result['unchanged']))
        if result.get('missing'):
            lines.append('Nenalezeno: ' + ', '.join(result['missing']))
        if result.get('failed'):
            lines.append('Chyby: ' + ' | '.join(result['failed']))
        sources = result.get('sources') or {}
        if sources:
            lines.append('')
            lines.append('Zdroje:')
            for name, path in sources.items():
                lines.append(f'{name}: {path}')
        diagnostics = result.get('diagnostics') or {}
        if diagnostics:
            lines.append('')
            lines.append('Kontrolovane koreny:')
            seen = []
            for roots in diagnostics.values():
                for root in roots:
                    if root not in seen:
                        seen.append(root)
            for root in seen[:8]:
                lines.append(root)
        self.set_status('\n'.join(lines))

    def reload_action(self, sender):
        self.sources = load_sources()
        self.refresh_labels()


if __name__ == '__main__':
    view = DataFreshTest()
    view.present('sheet')
