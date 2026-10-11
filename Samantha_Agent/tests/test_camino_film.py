"""P2-A contract failures and decoded-picture/sound integration evidence."""

import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.file_persistence import FilePersistenceError
from camino.film.media import FONT, binary, ffmpeg, probe, run
from camino.film.project import FilmError, digest, fingerprint, load_project, save_project, validate
from camino.film.render import directory_bytes, render
from camino.film.synthetic import SPEECH, create_fixture


class FilmWorkflowTests(unittest.TestCase):
    def test_disappearing_atomic_temp_does_not_kill_disk_measurement(self):
        from unittest.mock import Mock
        root, temporary = Mock(), Mock()
        root.rglob.return_value = [temporary]
        temporary.is_file.return_value = True
        temporary.is_symlink.return_value = False
        temporary.stat.side_effect = FileNotFoundError('atomic rename')
        self.assertEqual(directory_bytes(root), (0, 0))

    def test_registered_command_is_bounded_and_requires_confirmation(self):
        from app.workflows.commands import WORKFLOW_COMMANDS, run_workflow_command_text
        command = next(c for c in WORKFLOW_COMMANDS if c.command_id == 'camino_p2a_synthetic_film')
        self.assertEqual(command.argv[1:], ('-m', 'scripts.camino_p2a_film', '--execute'))
        self.assertTrue(command.requires_confirmation)
        with tempfile.TemporaryDirectory() as tmp, patch('subprocess.run') as runner:
            result = run_workflow_command_text(command_id=command.command_id,
                       pending_path=Path(tmp)/'pending.json', runner=runner)
        self.assertIn('chybi samostatne potvrzeni', result)
        runner.assert_not_called()


class FilmContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sources').mkdir()
        self.source = self.root / 'sources' / 'test.png'
        Image.new('RGB', (64, 64), 'red').save(self.source)
        self.project = {'schema': 1, 'scope': 'synthetic-p2a', 'id': 'test', 'revision': 1,
                        'sources': {'photo': {'file': 'test.png', 'kind': 'photo', 'revision': 1,
                                    'sha256': digest(self.source), 'duration_ms': 0,
                                    'privacy': 'diary', 'synthetic': True}},
                        'shots': [{'id': 'shot', 'source': 'photo', 'source_revision': 1,
                                   'at_ms': 0, 'in_ms': 0, 'out_ms': 1000, 'title': 'Žluťoučký kůň',
                                   'title_origin': 'synthetic', 'manual': True, 'gain': 0}], 'voices': []}

    def test_reopen_preserves_exact_timeline_and_no_overwrite(self):
        path = self.root / 'project.json'
        save_project(path, self.project)
        self.assertEqual(load_project(path), self.project)
        with self.assertRaises(FilePersistenceError):
            save_project(path, self.project)
        self.assertEqual(load_project(path)['shots'][0]['manual'], True)

    def test_corrupted_source_prevents_load(self):
        path = self.root / 'project.json'
        save_project(path, self.project)
        self.source.write_bytes(b'corruption')
        with self.assertRaises(FilmError):
            load_project(path)

    def test_private_unknown_and_non_synthetic_sources_are_rejected(self):
        for key, value in [('privacy', 'owner_only'), ('privacy', 'unknown'), ('synthetic', False)]:
            with self.subTest(key=key, value=value), self.assertRaises(FilmError):
                project = copy.deepcopy(self.project)
                project['sources']['photo'][key] = value
                validate(project, self.root)

    def test_version_revision_paths_and_unknown_fields_fail_closed(self):
        variants = []
        for key, value in [('schema', 2), ('schema', True), ('revision', True), ('scope', 'real-media')]:
            variants.append({**copy.deepcopy(self.project), key: value})
        p = copy.deepcopy(self.project); p['unexpected'] = True; variants.append(p)
        p = copy.deepcopy(self.project); p['sources']['photo']['file'] = '../test.png'; variants.append(p)
        p = copy.deepcopy(self.project); p['shots'][0]['source_revision'] = 2; variants.append(p)
        for project in variants:
            with self.subTest(project=project), self.assertRaises(FilmError):
                validate(project, self.root)

    def test_timing_duplicates_and_invalid_gain_are_rejected(self):
        for key, value in [('at_ms', 10), ('out_ms', 0), ('in_ms', -1), ('gain', float('nan')),
                           ('gain', True), ('manual', 1), ('title', 'line\nbreak')]:
            p = copy.deepcopy(self.project); p['shots'][0][key] = value
            with self.subTest(key=key), self.assertRaises(FilmError):
                validate(p, self.root)
        p = copy.deepcopy(self.project); p['shots'] *= 2
        with self.assertRaises(FilmError):
            validate(p, self.root)

    def test_symlink_is_not_a_source(self):
        link = self.root / 'sources' / 'link.png'; link.symlink_to(self.source)
        self.project['sources']['photo']['file'] = 'link.png'
        with self.assertRaises(FilmError):
            validate(self.project, self.root)

    def test_voice_overrun_and_source_trim_are_rejected(self):
        s = {**self.project['sources']['photo'], 'kind': 'audio', 'duration_ms': 1500}
        self.project['sources']['voice'] = s
        self.project['voices'] = [{'id': 'voice', 'source': 'voice', 'source_revision': 1,
                                  'at_ms': 0, 'in_ms': 0, 'out_ms': 1500, 'manual': False, 'gain': 1}]
        with self.assertRaisesRegex(FilmError, 'přesahuje'):
            validate(self.project, self.root)
        self.project['voices'][0]['out_ms'] = 1600
        with self.assertRaisesRegex(FilmError, 'překračuje'):
            validate(self.project, self.root)

    def test_full_disk_does_not_create_export(self):
        path = self.root / 'project.json'; save_project(path, self.project)
        with patch('camino.film.render._inspect_sources', return_value={}), \
                patch('camino.film.render.shutil.disk_usage', return_value=shutil._ntuple_diskusage(100, 100, 0)):
            with self.assertRaisesRegex(FilmError, 'místa'):
                render(path, 'preview')
        self.assertFalse(list(self.root.glob('preview-*')))

    def test_failed_render_has_no_published_film(self):
        path = self.root / 'project.json'; save_project(path, self.project)
        with patch('camino.film.render.ffmpeg', side_effect=FilmError('synthetic failure')):
            with self.assertRaises(FilmError):
                render(path, 'preview')
        self.assertFalse(list(self.root.glob('*/film.mp4')))
        self.assertFalse(list(self.root.glob('*/receipt.json')))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe') and FONT.is_file(), 'Local FFmpeg and Czech font required')
class FilmRenderTests(unittest.TestCase):
    setUp = FilmContractTests.setUp

    @unittest.skipUnless(Path('/usr/bin/say').is_file(), 'macOS speech fixture required')
    def test_synthetic_closing_sentence_is_near_film_end(self):
        root = self.root / 'fixture'
        root.mkdir()
        project = load_project(create_fixture(root))
        total_ms = validate(project, root)
        voice = project['voices'][0]
        voice_end_ms = voice['at_ms'] + voice['out_ms'] - voice['in_ms']
        self.assertEqual(total_ms - voice_end_ms, 1000)
        self.assertTrue(SPEECH.endswith('Šťastnou cestu.'))
        self.assertNotIn('musí být slyšet', SPEECH)

    def test_display_matrix_rotates_landscape_without_cropping(self):
        raw = self.root / 'raw.mp4'
        rotated = self.root / 'sources' / 'rotated.mp4'
        ffmpeg(['-f', 'lavfi', '-i', 'color=c=lime:s=160x90:r=30', '-t', '1',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(raw)])
        ffmpeg(['-display_rotation:v:0', '90', '-i', str(raw), '-c', 'copy', str(rotated)])
        self.assertTrue(any(abs(s.get('rotation', 0)) == 90 for s in
                            probe(rotated)['streams'][0].get('side_data_list', [])))
        p = self.project
        p['sources']['photo'].update(file='rotated.mp4', kind='video', duration_ms=1000,
                                      sha256=digest(rotated))
        p['shots'][0]['title'] = ''
        path = self.root / 'project.json'; save_project(path, p)
        with patch.dict('camino.film.render.PROFILES', {'preview': (320, 180, 25)}):
            result = render(path, 'preview')
        frame = run([binary('ffmpeg'), '-v', 'error', '-ss', '0.5', '-i', str(self.root/result['output']),
                     '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']).stdout
        image = Image.open(io.BytesIO(frame)).convert('RGB')
        self.assertLess(max(image.getpixel((5, 60))), 25)
        self.assertGreater(image.getpixel((160, 60))[1], 180)

    def test_source_change_during_export_prevents_publication(self):
        path = self.root / 'project.json'; save_project(path, self.project)
        def changing_source(args, **kwargs):
            ffmpeg(args, **kwargs)
            if args[-1].endswith('render.partial.mp4'):
                Image.new('RGB', (64, 64), 'blue').save(self.source)
        with patch.dict('camino.film.render.PROFILES', {'preview': (320, 180, 25)}), \
                patch('camino.film.render.ffmpeg', side_effect=changing_source):
            with self.assertRaisesRegex(FilmError, 'změnil'):
                render(path, 'preview')
        self.assertFalse(list(self.root.glob('*/film.mp4')))
    # Use a tiny deterministic fixture; real 720p/1080p experiment is separate.
    def test_render_decodes_preserves_full_clip_and_voice_tail(self):
        root = self.root
        ffmpeg(['-f', 'lavfi', '-i', 'color=c=lime:s=90x160:r=24', '-t', '1',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(root / 'sources' / 'clip.mp4')])
        ffmpeg(['-f', 'lavfi', '-i', 'sine=frequency=880:sample_rate=48000', '-t', '0.8',
                '-c:a', 'pcm_s16le', str(root / 'sources' / 'voice.wav')])
        p = self.project
        for sid, name, kind, duration in [('clip', 'clip.mp4', 'video', 1000), ('voice', 'voice.wav', 'audio', 800)]:
            p['sources'][sid] = {'file': name, 'kind': kind, 'revision': 1, 'sha256': digest(root/'sources'/name),
                                   'duration_ms': duration, 'privacy': 'diary', 'synthetic': True}
        shot = {**p['shots'][0], 'id': 'clip', 'source': 'clip', 'at_ms': 1000, 'title': ''}
        p['shots'].append(shot)
        p['voices'] = [{'id': 'voice', 'source': 'voice', 'source_revision': 1, 'at_ms': 1150,
                        'in_ms': 0, 'out_ms': 800, 'manual': False, 'gain': 1}]
        path = root / 'project.json'; save_project(path, p)
        with patch.dict('camino.film.render.PROFILES', {'preview': (320, 180, 25), 'final': (640, 360, 20)}):
            a, b = render(path, 'preview'), render(path, 'final')
        self.assertEqual(a['project_fingerprint'], b['project_fingerprint'])
        self.assertEqual(a['timeline_ms'], 2000)
        self.assertEqual(fingerprint(load_project(path)), a['project_fingerprint'])
        frame = run([binary('ffmpeg'), '-v', 'error', '-ss', '1.9', '-i', str(root/a['output']),
                     '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-']).stdout
        image = Image.open(io.BytesIO(frame)).convert('RGB')
        self.assertLess(max(image.getpixel((5, 60))), 25)  # black margin, portrait is not cropped
        self.assertGreater(image.getpixel((160, 60))[1], 180)
        audio = run([binary('ffmpeg'), '-v', 'error', '-ss', '1.85', '-i', str(root/a['output']),
                     '-t', '0.05', '-f', 's16le', '-ac', '1', '-']).stdout
        import array
        samples = array.array('h', audio)
        self.assertGreater(max(abs(v) for v in samples), 300)  # tail really decodes with sound
        self.assertEqual(digest(root/'sources'/'clip.mp4'), p['sources']['clip']['sha256'])
        again = render(path, 'preview')
        self.assertNotEqual(again['output'], a['output'])
        self.assertTrue((root/a['output']).is_file())

    def test_hdr_is_refused_before_render(self):
        path = self.root / 'project.json'; save_project(path, self.project)
        with patch('camino.film.render.probe', return_value={'streams': [
                {'codec_type': 'video', 'width': 64, 'height': 64, 'color_transfer': 'smpte2084'}]}):
            with self.assertRaisesRegex(FilmError, 'HDR'):
                render(path, 'preview')
        self.assertFalse(list(self.root.glob('preview-*')))
