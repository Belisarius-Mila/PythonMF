from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workshop_store import WorkshopError, WorkshopStore, add_experiment, export_python, import_python


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.store = WorkshopStore(self.directory)

    def test_load_is_read_only_and_source_notes_round_trip(self):
        state = self.store.load()
        self.assertFalse(self.store.path.exists())
        key = add_experiment(state, 'První vlastní', 'print("Míla")\n', 'Co dělá print?')
        self.store.save(state)
        loaded = WorkshopStore(self.directory).load()
        self.assertEqual(loaded, state)
        self.assertEqual(loaded['current'], key)

    def test_same_title_gets_distinct_identity(self):
        state = self.store.load()
        first = add_experiment(state, 'Pokus', 'x = 1')
        second = add_experiment(state, 'Pokus', 'x = 2')
        self.assertNotEqual(first, second)
        self.assertEqual(state['experiments'][first]['source'], 'x = 1')

    def test_new_experiment_validation_does_not_mutate_existing_state(self):
        state = self.store.load()
        add_experiment(state, 'Původní', '# pokus')
        before = deepcopy(state)
        for title, source in [('', ''), ('a\nb', ''), ('a'*81, ''), ('Velký', 'a'*50001)]:
            with self.assertRaises(WorkshopError):
                add_experiment(state, title, source)
            self.assertEqual(state, before)

    def test_broken_python_is_a_valid_draft(self):
        state = self.store.load()
        add_experiment(state, 'Rozpracované', 'if :\n')
        self.store.save(state)
        self.assertEqual(WorkshopStore(self.directory).load(), state)

    def test_corrupt_future_and_invalid_data_cannot_be_overwritten(self):
        for raw in (b'{', b'[]', b'{"version":2}', b'{"version":1,"experiments":{},"current":"missing"}',
                    b'{"version":1,"experiments":{},"current":[]}'):
            self.store.path.write_bytes(raw)
            with self.assertRaises(WorkshopError):
                self.store.load()
            with self.assertRaises(WorkshopError):
                self.store.save({'version': 1, 'current': None, 'experiments': {}})
            self.assertEqual(self.store.path.read_bytes(), raw)

    def test_two_windows_cannot_overwrite_each_other(self):
        first = self.store.load()
        other = WorkshopStore(self.directory)
        second = other.load()
        add_experiment(first, 'Novější', 'x = 1')
        self.store.save(first)
        add_experiment(second, 'Starší', 'x = 2')
        with self.assertRaises(WorkshopError):
            other.save(second)
        self.assertEqual(WorkshopStore(self.directory).load(), first)

    def test_failed_atomic_replace_preserves_all_experiments(self):
        state = self.store.load()
        add_experiment(state, 'Původní', 'x = 1')
        self.store.save(state)
        raw = self.store.path.read_bytes()
        add_experiment(state, 'Nový', 'x = 2')
        with patch('workshop_store.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                self.store.save(state)
        self.assertEqual(self.store.path.read_bytes(), raw)
        self.assertFalse(list(self.directory.glob('.dilna-*.tmp')))
        self.store.save(state)
        self.assertEqual(WorkshopStore(self.directory).load(), state)

    def test_course_progress_is_untouched(self):
        progress = self.directory / 'prubeh_v2.json'
        progress.write_bytes(b'private course progress sentinel')
        state = self.store.load()
        add_experiment(state, 'Samostatný pokus')
        self.store.save(state)
        self.assertEqual(progress.read_bytes(), b'private course progress sentinel')

    def test_import_reads_without_executing_or_rewriting_source(self):
        marker = self.directory / 'must-not-exist'
        source = f'from pathlib import Path\nPath({str(marker)!r}).write_text("ran")\n'
        path = self.directory / 'priklad.py'
        raw = b'\xef\xbb\xbf' + source.encode('utf-8')
        path.write_bytes(raw)
        self.assertEqual(import_python(path), source)
        self.assertFalse(marker.exists())
        self.assertEqual(path.read_bytes(), raw)

    def test_import_rejects_large_binary_and_wrong_encoding(self):
        path = self.directory / 'priklad.py'
        for raw in (b'a'*50001, b'\x00', b'\xff'):
            path.write_bytes(raw)
            with self.assertRaises(WorkshopError):
                import_python(path)

    def test_export_never_overwrites_existing_file(self):
        path = self.directory / 'pokus.py'
        source = 'print("Pokus")\n'
        export_python(path, source)
        self.assertEqual(path.read_text(), source)
        with self.assertRaises(FileExistsError):
            export_python(path, 'different')
        self.assertEqual(path.read_text(), source)


if __name__ == '__main__':
    unittest.main()
