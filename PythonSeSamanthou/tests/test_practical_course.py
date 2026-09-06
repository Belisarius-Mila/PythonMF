"""Content and additive installation checks against the existing course contract."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import python_se_samanthou as app
from assessment import assess_lesson
from course_loader import discover_courses, load_course
from scripts.build_course_package import build

COURSE = ROOT / 'kurzy/python_prakticke_ulohy'


class PracticalCourseTests(unittest.TestCase):
    def test_seven_solutions_and_unfinished_starters(self):
        course = load_course(COURSE / 'kurz.json')
        self.assertEqual(len(course['lessons']), 7)
        for lesson in course['lessons']:
            for field, passed in [('starter', False), ('solution', True)]:
                with self.subTest(lesson=lesson['id'], field=field):
                    result = app.run_code(lesson[field])
                    self.assertIsNone(result['error'])
                    self.assertEqual(assess_lesson(lesson, lesson[field], result)[0], passed)
                    self.assertIn('DO DÍLNY', lesson['explain'])

    def test_typical_mistakes_and_boundary_errors(self):
        lessons = load_course(COURSE / 'kurz.json')['lessons']
        variants = [(0, '.strip()', ''), (0, '.lower()', ''),
                    (1, 'polozky.append("med")', ''),
                    (2, 'celkem = celkem + cena', 'celkem = cena'),
                    (3, '>= 20', '> 20'),
                    (4, ', start=1', ''), (5, 'int(hodnota)', '0'),
                    (6, 'celkem <= rozpocet', 'celkem < rozpocet'),
                    (6, 'celkem <= rozpocet', 'True'),
                    (6, 'celkem <= rozpocet', 'False'),
                    (6, 'celkem = celkem + polozka["cena"]', 'celkem = polozka["cena"]')]
        for index, old, new in variants:
            with self.subTest(index=index, old=old, new=new):
                source = lessons[index]['solution'].replace(old, new)
                self.assertFalse(assess_lesson(lessons[index], source, app.execute_code(source))[0])

    def test_workshop_extensions_in_the_explanations(self):
        lessons = load_course(COURSE / 'kurz.json')['lessons']
        def run(index, old, new):
            result = app.execute_code(lessons[index]['solution'].replace(old, new))
            self.assertIsNone(result['error'])
            return result
        self.assertIn('zelený  čaj', run(0, 'ZELENÝ ČAJ', 'ZELENÝ  ČAJ')['output'])
        self.assertEqual(run(1, 'pocet = len(polozky)', 'polozky.append("voda")\npocet = len(polozky)')['variables']['pocet'], 5)
        self.assertEqual(run(2, '[30, 20, 15]', '[]')['variables']['celkem'], 0)
        self.assertEqual(run(3, '[16, 20, 24, 19]', '[16, 20, 24, 19, 20]')['output'].splitlines(), ['20', '24', '20', 'Počet: 3'])
        self.assertEqual(run(3, '>= 20', '>= 100')['output'].strip(), 'Počet: 0')
        self.assertEqual(run(4, 'start=1', 'start=5')['variables']['cislo'], 7)
        self.assertEqual(run(5, '["12", "ahoj", "5"]', '["-3", " 8 ", "3.5"]')['output'].splitlines(), ['Číslo: -3', 'Číslo: 8', 'Neplatné číslo: 3.5'])
        self.assertIn('Nákup překročil rozpočet.', run(6, 'rozpocet = 100', 'rozpocet = 80')['output'])
        self.assertEqual(run(6, 'rozpocet = 100', 'rozpocet = 85')['variables']['zbyva'], 0)

    def test_three_distinct_courses_21_lessons(self):
        courses, warnings = discover_courses(ROOT / 'kurzy')
        self.assertFalse(warnings)
        self.assertEqual(len(courses), 3)
        ids = [l['id'] for c in courses for l in c['lessons']]
        self.assertEqual(len(ids), 21)
        self.assertEqual(len(set(ids)), 21)

    def test_package_only_referenced_content_and_safe_rebuild(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / 'python_prakticke_ulohy'
            shutil.copytree(COURSE, source)
            (source / '.env').write_text('NOT FOR DISTRIBUTION')
            (source / 'dilna.json').write_text('private')
            (source / 'extra.py').write_text('must not ship')
            output = folder / 'course.zip'
            with contextlib.redirect_stdout(io.StringIO()):
                build(source, output)
                first = output.read_bytes()
                build(source, output)
            self.assertEqual(first, output.read_bytes())
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(len(archive.namelist()), 30)
                self.assertTrue(all(n.startswith('python_prakticke_ulohy/') for n in archive.namelist()))
                self.assertFalse(any(Path(n).name in {'.env', 'dilna.json', 'extra.py', 'python_se_samanthou.py'} for n in archive.namelist()))
                installed = folder / 'installed/kurzy'
                installed.mkdir(parents=True)
                archive.extractall(installed)
                self.assertEqual(len(load_course(installed / 'python_prakticke_ulohy/kurz.json')['lessons']), 7)
            (source / 'README.md').write_text('changed')
            with self.assertRaises(FileExistsError):
                build(source, output)
            self.assertEqual(first, output.read_bytes())

    def test_packaging_does_not_run_code(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / 'python_prakticke_ulohy'
            shutil.copytree(COURSE, source)
            marker = folder / 'must-not-exist'
            manifest = json.loads((source / 'kurz.json').read_text())
            lesson_dir = (source / manifest['lessons'][0]).parent
            (lesson_dir / 'ukazka.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("bad")\n')
            with contextlib.redirect_stdout(io.StringIO()):
                build(source, folder / 'course.zip')
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
