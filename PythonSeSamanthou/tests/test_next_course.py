import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import python_se_samanthou as app
from assessment import assess_lesson
from course_loader import DEFAULT_COURSE, discover_courses, load_course

NEXT = ROOT / 'kurzy/python_dalsi_kroky/kurz.json'


class NextCourseTests(unittest.TestCase):
    def test_all_seven_solutions_pass_and_starters_need_an_edit(self):
        course = load_course(NEXT)
        self.assertEqual(course['id'], 'python-dalsi-kroky')
        self.assertEqual(len(course['lessons']), 7)
        for lesson in course['lessons']:
            for field, passed in [('starter', False), ('solution', True)]:
                with self.subTest(lesson=lesson['id'], field=field):
                    result = app.run_code(lesson[field])
                    self.assertIsNone(result['error'])
                    self.assertEqual(assess_lesson(lesson, lesson[field], result)[0], passed)

    def test_incorrect_constructs_and_outputs_are_rejected(self):
        lessons = load_course(NEXT)['lessons']
        variants = [(0, lessons[0]['solution'].replace('len(jmeno)', '8')),
                    (1, lessons[1]['solution'].replace('barvy[3]', 'barvy[2]')),
                    (2, 'print("Ahoj, Míla!\\nAhoj, Jana!\\nAhoj, Samantha!")'),
                    (3, 'vysledek = 14\nprint(vysledek)'),
                    (4, 'zbyva = 0\nprint("3\\n2\\n1\\nStart!")'),
                    (5, lessons[5]['solution'].replace('"Brno"', '"Praha"')),
                    (6, lessons[6]['solution'].replace('>= 10', '>= 14'))]
        for index, source in variants:
            self.assertFalse(assess_lesson(lessons[index], source, app.execute_code(source))[0])

    def test_course_ids_do_not_overlap(self):
        first, second = load_course(DEFAULT_COURSE), load_course(NEXT)
        self.assertFalse({x['id'] for x in first['lessons']} & {x['id'] for x in second['lessons']})

    def test_catalog_reports_invalid_and_duplicate_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            shutil.copytree(DEFAULT_COURSE.parent, folder / 'first')
            shutil.copytree(NEXT.parent, folder / 'second')
            broken = folder / 'broken'
            broken.mkdir()
            (broken / 'kurz.json').write_text('{bad')
            courses, warnings = discover_courses(folder)
            self.assertEqual(len(courses), 2)
            self.assertEqual(len(warnings), 1)
            shutil.copytree(NEXT.parent, folder / 'duplicate')
            courses, warnings = discover_courses(folder)
            self.assertEqual([c['id'] for c in courses], ['python-zaklady'])
            self.assertEqual(len(warnings), 2)


if __name__ == '__main__':
    unittest.main()
