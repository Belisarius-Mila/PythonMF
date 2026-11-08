from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app.recovery_guide_revision import collect_revision
from app.recovery_guide_sources import digest


class RevisionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.top = Path(tmp.name).resolve()
        self.root = self.top / 'Samantha_Agent'
        (self.root / 'memory').mkdir(parents=True)
        self.original = self.top / 'original.txt'
        self.original.write_text('1. OBNOVA\nPůvodní celý návod.\n')
        self.write('Samantha_Agent/memory/current.md', 'Současná dokumentace.\n')
        self.write('Samantha_Agent/memory/handoffs/old.md', 'Historický doklad.\n')
        self.write('Samantha_Agent/docs/readme.md', 'Celý dokument.\n')
        self.write('Samantha_Agent/data/private/README.md', 'Not part of corpus.')
        self.write('MatysekANJ/docs/setup.md', 'Nastavení výukové aplikace.\n')
        self.write('unrelated/notes.md', 'Outside proposed scope.')
        self.git('init', '-q')
        self.head = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.top), *args], stderr=subprocess.PIPE)

    def write(self, path, text):
        p = self.top / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def commit(self):
        self.git('add', 'Samantha_Agent', 'MatysekANJ', 'unrelated')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'Synthetic document checkpoint')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def collect(self, head=None, **kwargs):
        return collect_revision(self.original, head or self.head, self.root, **kwargs)

    def test_complete_sorted_public_documents_and_provenance(self):
        s = self.collect()
        self.assertEqual(s.head, self.head)
        self.assertEqual(s.original.text, self.original.read_text())
        self.assertEqual(len(s.sources), 4)
        names = [r.path for r in s.sources]
        self.assertEqual(names, sorted(names))
        self.assertNotIn('Samantha_Agent/data/private/README.md', names)
        self.assertNotIn('unrelated/notes.md', names)
        self.assertTrue(any(r.authority == 'historical_or_mixed' for r in s.sources))
        for r in s.sources:
            self.assertEqual(r.sha256, digest(r.text))

    def test_dirty_working_copy_and_new_head_do_not_replace_frozen_sources(self):
        self.write('Samantha_Agent/memory/current.md', 'Novější obsah.\n')
        later = self.commit()
        self.write('Samantha_Agent/memory/current.md', 'Necommitovaná práce.\n')
        s = self.collect()
        self.assertEqual(next(r.text for r in s.sources if r.path.endswith('current.md')), 'Současná dokumentace.\n')
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), later)
        self.assertIn('Necommitovaná', (self.root / 'memory/current.md').read_text())

    def test_untracked_private_and_excluded_invalid_utf8_never_enter_input(self):
        (self.top / 'unrelated/notes.md').write_bytes(b'\xff')
        head = self.commit()
        self.write('Samantha_Agent/memory/untracked.md', 'Not committed.')
        s = self.collect(head)
        self.assertFalse(any('untracked' in r.path for r in s.sources))

    def test_explicit_project_only_scope_excludes_companions(self):
        self.write('unrelated/README.md', 'Another project.')
        head = self.commit()
        s = self.collect(head, project_only=True)
        self.assertEqual(len(s.sources), 3)
        self.assertTrue(all(r.path.startswith('Samantha_Agent/') for r in s.sources))

    def test_selected_symlink_is_rejected_from_git_mode(self):
        (self.root / 'docs/link.md').symlink_to('readme.md')
        head = self.commit()
        with self.assertRaisesRegex(ValueError, 'non_regular'):
            self.collect(head)

    def test_invalid_utf8_or_secret_in_selected_blob_fails_without_content(self):
        p = self.root / 'docs/readme.md'
        for value in (b'\xff', ('sk-' + 'X' * 30).encode()):
            p.write_bytes(value)
            head = self.commit()
            with self.assertRaises((UnicodeError, ValueError)) as error:
                self.collect(head)
            self.assertNotIn('X' * 30, str(error.exception))

    def test_only_full_commit_identity_is_accepted(self):
        for revision in ('main', self.head[:12], '--all', '0' * 40):
            with self.subTest(revision=revision), self.assertRaises((ValueError, subprocess.CalledProcessError)):
                self.collect(revision)

    def test_no_model_ref_checkout_or_writes_are_needed(self):
        before = self.git('status', '--porcelain')
        self.collect()
        self.assertEqual(before, self.git('status', '--porcelain'))
        self.assertEqual(self.head, self.git('rev-parse', 'HEAD').decode().strip())

    def test_original_alias_and_invalid_companion_scope_fail(self):
        link = self.top / 'alias.txt'
        link.symlink_to(self.original)
        with self.assertRaises(ValueError):
            collect_revision(link, self.head, self.root)
        for scope in ('../docs/', '/tmp/docs/', 'docs'):
            with self.assertRaises(ValueError):
                self.collect(companion_scopes=(scope,))

    def test_changed_original_during_git_reads_fails(self):
        actual = subprocess.run
        def change(*args, **kwargs):
            result = actual(*args, **kwargs)
            self.original.write_text('Original was changed concurrently.')
            return result
        with patch('app.recovery_guide_revision.subprocess.run', side_effect=change):
            with self.assertRaisesRegex(ValueError, 'input_changed'):
                self.collect()


if __name__ == '__main__':
    unittest.main()
