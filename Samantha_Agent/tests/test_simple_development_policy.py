"""Scope and mutation-boundary regression tests for function delegation."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from app.simple_development_policy import (
    build_updated_source, prepare_function_task, validate_function_answer,
)


ORIGINAL = 'def label(text: str) -> str:\n    return text.strip()\n'
REPLACEMENT = 'def label(text: str) -> str:\n    return text.upper()\n'


class SimpleDevelopmentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'app').mkdir()
        (self.root / 'tests').mkdir()
        self.file = self.root / 'app/text_helpers.py'
        self.file.write_text('# before\n' + ORIGINAL + '\n# after\nVALUE = 1\n', encoding='utf-8')
        (self.root / 'tests/test_text_helpers.py').write_text('import unittest\n', encoding='utf-8')
        self.git('init', '-q')
        self.git('add', 'app/text_helpers.py', 'tests/test_text_helpers.py')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        self.request = {'goal': 'Uprav velikost písmen.', 'path': 'app/text_helpers.py', 'function': 'label', 'test_modules': ['tests.test_text_helpers']}

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def task(self):
        return prepare_function_task(self.root, self.request)

    def answer(self, source=REPLACEMENT):
        return {'function_source': source, 'summary': 'Upravena velikost písmen.'}

    def test_formatting_change_preserves_surroundings_and_does_not_write(self):
        before = self.file.read_bytes()
        task = self.task()
        self.assertEqual(task['source_sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(task['original_function'], ORIGINAL)
        replacement = validate_function_answer(task, self.answer())
        updated = build_updated_source(self.root, task, replacement)
        self.assertEqual(updated, before.decode().replace(ORIGINAL, REPLACEMENT))
        self.assertEqual(self.file.read_bytes(), before)

    def test_crlf_and_final_newline_preserved(self):
        for ending in ('', '\r\n'):
            with self.subTest(ending=ending):
                before = ('# before\r\n' + ORIGINAL.replace('\n', '\r\n').rstrip('\r\n') + ending).encode()
                self.file.write_bytes(before)
                updated = build_updated_source(self.root, self.task(), REPLACEMENT)
                self.assertEqual(updated.encode(), before.replace(b'text.strip()', b'text.upper()'))

    def test_blocked_paths(self):
        for path in ('app/cockpit.py', 'app/samantha_agent.py', 'app/routine_tasks.py', 'app/simple_development_policy.py', 'app/communication/helpers.py', 'app/capabilities/helpers.py', 'app/workflows/helpers.py', 'app/camino_helpers.py', 'app/codex_helpers.py', 'app/helpers_backup.py', 'app/email/helpers.py', 'app/git_helpers.py', 'app/storage_helpers.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare_function_task(self.root, dict(self.request, path=path))

    def test_traversal_and_absolute_paths(self):
        for path in ('app/../app/text_helpers.py', 'app//text_helpers.py', str(self.file), 'app/./text_helpers.py', 'app\\text_helpers.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare_function_task(self.root, dict(self.request, path=path))

    def test_symlink_source_and_test(self):
        (self.root / 'app/link.py').symlink_to(self.file)
        self.git('add', 'app/link.py')
        with self.assertRaises(ValueError):
            prepare_function_task(self.root, dict(self.request, path='app/link.py'))
        (self.root / 'tests/test_link.py').symlink_to(self.root / 'tests/test_text_helpers.py')
        self.git('add', 'tests/test_link.py')
        with self.assertRaises(ValueError):
            prepare_function_task(self.root, dict(self.request, test_modules=['tests.test_link']))

    def test_untracked_source_and_test(self):
        (self.root / 'app/new.py').write_text(ORIGINAL)
        (self.root / 'tests/test_new.py').write_text('')
        with self.assertRaises(ValueError):
            prepare_function_task(self.root, dict(self.request, path='app/new.py'))
        with self.assertRaises(ValueError):
            prepare_function_task(self.root, dict(self.request, test_modules=['tests.test_new']))

    def test_strict_request(self):
        for changes in ({'extra': True}, {'goal': ''}, {'goal': 'x' * 1201}, {'test_modules': []}, {'test_modules': ['os']}, {'test_modules': ['tests.test_text_helpers'] * 2}, {'function': 'other.name'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                prepare_function_task(self.root, dict(self.request, **changes))

    def test_unsafe_original_or_replacement(self):
        bodies = ['import os\n    return text', 'return helper(text)', 'return GLOBAL', 'return text.__class__', 'text[0] = "x"\n    return text', 'text.append("x")\n    return text', 'alias = text\n    alias.extend(["x"])\n    return text', 'global state\n    return text', 'return (lambda: text)()', 'with text:\n        return text', 'try:\n        return text\n    except ValueError:\n        return ""', 'yield text', 'return open(text)', 'return text.strip().upper()', 'text += "x"\n    return text', 'len = text\n    return len()', 'def inner():\n        return text\n    return text']
        task = self.task()
        for body in bodies:
            source = 'def label(text: str) -> str:\n    ' + body + '\n'
            with self.subTest(body=body):
                with self.assertRaises(ValueError):
                    validate_function_answer(task, self.answer(source))
                self.file.write_text(source)
                with self.assertRaises(ValueError):
                    self.task()
        self.file.write_text(ORIGINAL)

    def test_signature_and_decorators_cannot_change(self):
        task = self.task()
        for replacement in ('def label(text, extra=0) -> str:\n    return text\n', 'def label(text: str) -> int:\n    return 1\n', '@property\n' + REPLACEMENT, REPLACEMENT.replace('label', 'other'), 'async ' + REPLACEMENT):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                validate_function_answer(task, self.answer(replacement))

    def test_changes_outside_function_rejected(self):
        task = self.task()
        for replacement in (REPLACEMENT + 'VALUE = 2\n', 'VALUE = 2\n' + REPLACEMENT, REPLACEMENT + '# outside\n', '# outside\n' + REPLACEMENT):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                validate_function_answer(task, self.answer(replacement))

    def test_source_drift_rejected(self):
        task = self.task()
        self.file.write_text(self.file.read_text() + '# drift\n')
        with self.assertRaises(ValueError):
            build_updated_source(self.root, task, REPLACEMENT)

    def test_oversized_inputs(self):
        task = self.task()
        for source in ('def label(text: str) -> str:\n    return "' + 'x' * 12000 + '"\n', 'def label(text: str) -> str:\n' + '    # line\n' * 100 + '    return text\n'):
            with self.subTest(source=source[:50]):
                with self.assertRaises(ValueError):
                    validate_function_answer(task, self.answer(source))
                self.file.write_text(source)
                with self.assertRaises(ValueError):
                    self.task()
        self.file.write_text('#' + 'x' * (400 * 1024) + '\n' + ORIGINAL)
        with self.assertRaises(ValueError):
            self.task()

    def test_strict_answer(self):
        task = self.task()
        for answer in ({'function_source': REPLACEMENT}, dict(self.answer(), extra=True), self.answer(''), dict(self.answer(), summary='x' * 401)):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                validate_function_answer(task, answer)

    def test_decorated_original_and_duplicate_functions_rejected(self):
        for source in ('@property\n' + ORIGINAL, ORIGINAL + '\n' + ORIGINAL):
            self.file.write_text(source)
            with self.assertRaises(ValueError):
                self.task()

    def test_fresh_local_collections_are_supported_but_aliases_are_not(self):
        source = ('def label(text: str) -> str:\n    parts = []\n    for item in text.split():\n        parts.append(item.lower())\n    return \" \".join(parts)\n')
        self.file.write_text(source)
        task = self.task()
        replacement = source.replace('item.lower()', 'item.upper()')
        self.assertEqual(validate_function_answer(task, self.answer(replacement)), replacement)
        for assignment in ('parts = text', 'parts = []\n    parts = text'):
            unsafe = source.replace('parts = []', assignment)
            self.file.write_text(unsafe)
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                self.task()

    def test_unsafe_annotations_and_defaults_rejected(self):
        for source in ('def label(text: helper()) -> str:\n    return text\n', 'def label(text: Secret) -> str:\n    return text\n', 'def label(text=helper()):\n    return text\n'):
            self.file.write_text(source)
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.task()

    def test_large_diff_rejected(self):
        self.file.write_text('def label(text: str) -> str:\n' + ''.join(f'    a{i} = {i}\n' for i in range(60)) + '    return text\n')
        task = self.task()
        source = 'def label(text: str) -> str:\n' + ''.join(f'    b{i} = {i}\n' for i in range(60)) + '    return text\n'
        with self.assertRaises(ValueError):
            validate_function_answer(task, self.answer(source))


if __name__ == '__main__':
    unittest.main()
