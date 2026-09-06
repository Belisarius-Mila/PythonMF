"""Load a local course package. Reading a course never runs its Python examples."""
import ast
import json
from pathlib import Path
import re

from assessment import validate_checks


DEFAULT_COURSE = Path(__file__).resolve().parent / 'kurzy' / 'python_zaklady' / 'kurz.json'
ID_RE = re.compile(r'[a-z][a-z0-9_.-]{0,79}\Z')


class CourseError(ValueError):
    pass


def read_text(path):
    try:
        if path.stat().st_size > 1_000_000:
            raise CourseError(f'Soubor kurzu je příliš velký: {path.name}.')
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        raise CourseError(f'Nelze načíst soubor kurzu {path.name}: {exc}') from exc


def read_json(path):
    try:
        data = json.loads(read_text(path))
    except ValueError as exc:
        raise CourseError(f'Neplatný JSON v {path.name}: {exc}') from exc
    if not isinstance(data, dict):
        raise CourseError(f'{path.name} musí obsahovat objekt.')
    return data


def local_file(base, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise CourseError('Kurz musí odkazovat na místní soubory relativní cestou.')
    base = base.resolve()
    path = (base / relative).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise CourseError('Odkaz na soubor opouští složku kurzu nebo lekce.') from exc
    if not path.is_file():
        raise CourseError(f'V balíčku chybí soubor {relative}.')
    return path


def valid_id(value):
    return isinstance(value, str) and ID_RE.fullmatch(value) is not None


def load_course(manifest_path=DEFAULT_COURSE):
    manifest_path = Path(manifest_path).resolve()
    course = read_json(manifest_path)
    if type(course.get('schema_version')) is not int or course['schema_version'] != 1:
        raise CourseError('Tato verze učebny nepodporuje formát kurzu.')
    if not valid_id(course.get('id')) or not isinstance(course.get('title'), str) or not course['title'].strip():
        raise CourseError('Kurzu chybí platné ID nebo název.')
    entries = course.get('lessons')
    if not isinstance(entries, list) or not 1 <= len(entries) <= 1000:
        raise CourseError('Kurz musí obsahovat 1 až 1000 lekcí.')
    lessons, seen = [], set()
    for relative in entries:
        meta_path = local_file(manifest_path.parent, relative)
        lesson = read_json(meta_path)
        lesson_id = lesson.get('id')
        if not valid_id(lesson_id) or not lesson_id.startswith(course['id'] + '.') or lesson_id in seen:
            raise CourseError(f'Neplatné nebo duplicitní ID lekce: {lesson_id!r}.')
        seen.add(lesson_id)
        for field in ('title', 'short', 'time', 'predict', 'task', 'hint', 'success', 'feedback'):
            if not isinstance(lesson.get(field), str) or not lesson[field].strip():
                raise CourseError(f'Lekci {lesson_id} chybí text {field}.')
        for field, ref in [('explain', 'explanation_file'), ('starter', 'starter_file'), ('solution', 'solution_file')]:
            lesson[field] = read_text(local_file(meta_path.parent, lesson.get(ref)))
            if not lesson[field].strip():
                raise CourseError(f'Lekce {lesson_id} má prázdný soubor {ref}.')
        try:
            ast.parse(lesson['starter'])
            ast.parse(lesson['solution'])
            validate_checks(lesson.get('checks'))
        except (SyntaxError, ValueError, TypeError) as exc:
            raise CourseError(f'Chyba lekce {lesson_id}: {exc}') from exc
        lessons.append(lesson)
    return {'id': course['id'], 'title': course['title'], 'lessons': lessons}
