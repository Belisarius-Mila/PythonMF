"""Run with python3 -m unittest discover -s tests -v. No display or real user data."""
import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import python_se_samanthou as app
from assessment import assess_lesson
from course_loader import CourseError, DEFAULT_COURSE, load_course
from progress_store import LEGACY_IDS, ProgressError, ProgressStore

spec = importlib.util.spec_from_file_location('original', ROOT / 'reference/python_se_samanthou_v1.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)


class CourseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'course'
        shutil.copytree(DEFAULT_COURSE.parent, self.folder)
        self.manifest = self.folder / 'kurz.json'
        self.course = load_course(self.manifest)

    def edit(self, path, change):
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def first_meta(self):
        return self.folder / json.loads(self.manifest.read_text())['lessons'][0]

    def test_original_texts_and_code_preserved(self):
        self.assertEqual(len(self.course['lessons']), 7)
        self.assertEqual(tuple(x['id'] for x in self.course['lessons']), LEGACY_IDS)
        for index, (old, new) in enumerate(zip(original.LESSONS, self.course['lessons'])):
            for key, value in old.items():
                self.assertEqual(f'{index + 1}  {new[key]}' if key == 'short' else new[key], value)

    def test_runner_implementation_preserved(self):
        trees = [ast.parse(p.read_text()) for p in
                 (ROOT / 'reference/python_se_samanthou_v1.py', ROOT / 'python_se_samanthou.py')]
        for name in ('execute_code',):
            self.assertEqual(*[ast.dump(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)) for tree in trees])

    def test_assessment_parity_solutions_starters_and_errors(self):
        for i, lesson in enumerate(self.course['lessons']):
            for source in (lesson['starter'], lesson['solution'], '', 'print("špatně")', 'x = 1 / 0', 'if :'):
                with self.subTest(lesson=lesson['id'], source=source):
                    result = app.execute_code(source)
                    self.assertEqual(result, original.execute_code(source))
                    self.assertEqual(assess_lesson(lesson, source, result), original.assess(i, source, result))
            self.assertTrue(assess_lesson(lesson, lesson['solution'], app.execute_code(lesson['solution']))[0])
            self.assertFalse(assess_lesson(lesson, lesson['starter'], app.execute_code(lesson['starter']))[0])

    def test_required_constructs_cannot_be_replaced_by_literal_result(self):
        cases = [(1, 'jmeno = "Samantha"\nprint("Ahoj, Samantha")'),
                 (2, 'pocet=5\ncena=20\ncelkem=100\nprint(celkem)'),
                 (4, '\n'.join(f'kruh({50+i*85},180,20,"zelena")' for i in range(5))),
                 (5, 'teplota=10\nprint("Vezmi si bundu.")\nkruh(250,180,65,"modra")')]
        for index, source in cases:
            result = app.execute_code(source)
            self.assertFalse(assess_lesson(self.course['lessons'][index], source, result)[0])
            self.assertEqual(assess_lesson(self.course['lessons'][index], source, result), original.assess(index, source, result))

    def test_eighth_lesson_requires_only_content_changes(self):
        src = self.first_meta().parent
        dest = self.folder / '08_opakovani'
        shutil.copytree(src, dest)
        self.edit(dest / 'lekce.json', lambda d: d.update(id='python-zaklady.opakovani'))
        self.edit(self.manifest, lambda d: d['lessons'].append('08_opakovani/lekce.json'))
        course = load_course(self.manifest)
        self.assertEqual(len(course['lessons']), 8)
        lesson = course['lessons'][-1]
        self.assertTrue(assess_lesson(lesson, lesson['solution'], app.execute_code(lesson['solution']))[0])

    def test_reordering_preserves_identity_and_checks(self):
        self.edit(self.manifest, lambda d: d['lessons'].reverse())
        reordered = load_course(self.manifest)
        self.assertEqual([x['id'] for x in reordered['lessons']], list(reversed(LEGACY_IDS)))
        for lesson in reordered['lessons']:
            self.assertTrue(assess_lesson(lesson, lesson['solution'], app.execute_code(lesson['solution']))[0])

    def test_loading_does_not_execute_example_or_solution(self):
        marker = Path(self.temp.name) / 'must-not-exist'
        code = f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n'
        for name in ('ukazka.py', 'reseni.py'):
            (self.first_meta().parent / name).write_text(code)
        load_course(self.manifest)
        self.assertFalse(marker.exists())

    def test_duplicate_ids_rejected(self):
        self.edit(self.manifest, lambda d: d['lessons'].append(d['lessons'][0]))
        with self.assertRaises(CourseError):
            load_course(self.manifest)

    def test_unknown_schema_rejected(self):
        self.edit(self.manifest, lambda d: d.update(schema_version=2))
        with self.assertRaises(CourseError):
            load_course(self.manifest)

    def test_invalid_check_rejected(self):
        for check in ({'kind': 'exec', 'value': 'pass'}, {'kind': 'ast_kind', 'value': 'Anything'},
                      {'kind': 'drawing_equals', 'value': [['circle', 1]]}):
            self.edit(self.first_meta(), lambda d: d.update(checks=[check]))
            with self.assertRaises(CourseError):
                load_course(self.manifest)

    def test_paths_cannot_escape_lesson(self):
        self.edit(self.first_meta(), lambda d: d.update(starter_file='../kurz.json'))
        with self.assertRaises(CourseError):
            load_course(self.manifest)

    def test_symlink_cannot_escape_course(self):
        outside = Path(self.temp.name) / 'outside.py'
        outside.write_text('print(1)')
        (self.first_meta().parent / 'linked.py').symlink_to(outside)
        self.edit(self.first_meta(), lambda d: d.update(starter_file='linked.py'))
        with self.assertRaises(CourseError):
            load_course(self.manifest)

    def test_missing_file_and_invalid_syntax_rejected(self):
        self.edit(self.first_meta(), lambda d: d.update(starter_file='missing.py'))
        with self.assertRaises(CourseError):
            load_course(self.manifest)
        (self.first_meta().parent / 'missing.py').write_text('if :')
        with self.assertRaises(CourseError):
            load_course(self.manifest)

    def test_cli_and_worker_from_unrelated_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / 'python_se_samanthou.py'), '--check-course'],
                                cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('7 lekcí', result.stdout)
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'python_se_samanthou.py'), '--worker'],
                                cwd=self.temp.name, input=json.dumps({'source': 'print("Míla")'}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['output'], 'Míla\n')

    def test_timeout_stops_infinite_loop(self):
        self.assertEqual(app.run_code('while True: pass', timeout=0.2)['error']['type'], 'Časový limit')


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'state'
        self.store = ProgressStore(self.folder)

    def legacy(self):
        data = {'version': 1, 'current': 4, 'completed': [0, 2],
                'drafts': {str(i): f'# vlastní kód {i}\nprint({i})' for i in range(7)}}
        self.folder.mkdir()
        raw = json.dumps(data, ensure_ascii=False, indent=3).encode()
        self.store.legacy_path.write_bytes(raw)
        return raw

    def test_new_state_load_does_not_write(self):
        data, warning = self.store.load()
        self.assertEqual(data, {'version': 2, 'courses': {}})
        self.assertFalse(self.folder.exists())
        self.store.save(data)
        self.assertEqual(ProgressStore(self.folder).load()[0], data)

    def test_migration_preserves_original_backup_drafts_and_completed(self):
        original_bytes = self.legacy()
        data, warning = self.store.load()
        self.assertFalse(self.store.path.exists())
        state = data['courses']['python-zaklady']
        self.assertEqual(state['current'], LEGACY_IDS[4])
        self.assertEqual(set(state['completed']), {LEGACY_IDS[0], LEGACY_IDS[2]})
        for i, lesson_id in enumerate(LEGACY_IDS):
            self.assertEqual(state['drafts'][lesson_id], f'# vlastní kód {i}\nprint({i})')
        self.store.save(data)
        self.assertEqual(self.store.legacy_path.read_bytes(), original_bytes)
        self.assertEqual(self.store.backup_path.read_bytes(), original_bytes)
        self.assertEqual(ProgressStore(self.folder).load()[0], data)

    def test_migration_is_idempotent(self):
        self.legacy()
        data, _ = self.store.load()
        self.store.save(data)
        data['courses']['python-zaklady']['drafts'][LEGACY_IDS[0]] = '# nový pokus'
        self.store.save(data)
        self.assertEqual(ProgressStore(self.folder).load()[0], data)

    def test_changed_legacy_after_migration_warns_without_reimport(self):
        self.legacy()
        data, _ = self.store.load()
        self.store.save(data)
        self.store.legacy_path.write_text('{}')
        loaded, warning = ProgressStore(self.folder).load()
        self.assertEqual(loaded, data)
        self.assertIn('mezitím', warning)

    def test_corrupt_legacy_cannot_be_overwritten(self):
        self.legacy()
        self.store.legacy_path.write_bytes(b'{broken')
        with self.assertRaises(ProgressError):
            self.store.load()
        with self.assertRaises(ProgressError):
            self.store.save({'version': 2, 'courses': {}})
        self.assertEqual(self.store.legacy_path.read_bytes(), b'{broken')
        self.assertFalse(self.store.path.exists())

    def test_invalid_or_future_v2_cannot_be_overwritten(self):
        self.folder.mkdir()
        for raw in (b'[]', b'{', b'{"version":3,"courses":{}}', b'{"version":2,"courses":{"bad":[]}}'):
            self.store.path.write_bytes(raw)
            with self.assertRaises(ProgressError):
                self.store.load()
            with self.assertRaises(ProgressError):
                self.store.save({'version': 2, 'courses': {}})
            self.assertEqual(self.store.path.read_bytes(), raw)

    def test_unknown_legacy_indices_do_not_silently_drop_work(self):
        self.legacy()
        for change in ({'drafts': {'7': '# future lesson'}}, {'completed': [7]}, {'current': True}, {'version': 5}):
            self.store.legacy_path.write_text(json.dumps({'version': 1, **change}))
            with self.assertRaises(ProgressError):
                self.store.load()

    def test_concurrent_copy_cannot_overwrite_newer_progress(self):
        first, _ = self.store.load()
        other = ProgressStore(self.folder)
        second, _ = other.load()
        first['note'] = 'newer'
        self.store.save(first)
        with self.assertRaises(ProgressError):
            other.save(second)
        self.assertEqual(ProgressStore(self.folder).load()[0], first)

    def test_changed_legacy_during_migration_blocks_save(self):
        self.legacy()
        data, _ = self.store.load()
        self.store.legacy_path.write_text('{}')
        with self.assertRaises(ProgressError):
            self.store.save(data)
        self.assertFalse(self.store.path.exists())

    def test_existing_different_backup_is_preserved(self):
        self.legacy()
        self.store.backup_path.write_bytes(b'older backup')
        data, _ = self.store.load()
        with self.assertRaises(ProgressError):
            self.store.save(data)
        self.assertEqual(self.store.backup_path.read_bytes(), b'older backup')
        self.assertFalse(self.store.path.exists())

    def test_failed_replace_keeps_previous_valid_state(self):
        data, _ = self.store.load()
        self.store.save(data)
        before = self.store.path.read_bytes()
        changed = deepcopy(data)
        changed['note'] = 'next'
        with patch('progress_store.os.replace', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                self.store.save(changed)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertFalse(list(self.folder.glob('.prubeh_v2-*.tmp')))
        self.store.save(changed)
        self.assertEqual(ProgressStore(self.folder).load()[0], changed)

    def test_other_courses_and_absent_lessons_survive(self):
        data, _ = self.store.load()
        data['courses']['jiny-kurz'] = {'current': 'jiny-kurz.a', 'completed': ['jiny-kurz.a'], 'drafts': {'jiny-kurz.a': '# jiné'}}
        data['courses']['python-zaklady'] = {'current': LEGACY_IDS[0], 'completed': ['python-zaklady.docasne-skryta'], 'drafts': {'python-zaklady.docasne-skryta': '# zachovat'}}
        self.store.save(data)
        self.assertEqual(ProgressStore(self.folder).load()[0], data)


if __name__ == '__main__':
    unittest.main()
