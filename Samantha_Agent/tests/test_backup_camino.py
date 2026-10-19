"""Synthetic archive, WAL, corruption, locks, and restoration of owned service state."""
import fcntl
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.backup import camino as backup


class Controller:
    SCHEMA_VERSION = 3

    def __init__(self, root, config, loaded=True):
        self.ROOT, self.config, self.loaded = root, config, loaded
        self.calls = []

    def load_config(self, _root):
        return self.config

    def control(self, action, _root):
        self.calls.append(action)
        if action == 'status':
            return {'owned_definition': True, 'loaded': self.loaded, 'running': self.loaded}
        self.loaded = action == 'start'

    @contextmanager
    def offline(self, _config):
        assert not self.loaded
        yield


class CaminoBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'Camino/Service'
        self.root.mkdir(parents=True)
        self.target = self.base / 'backup'
        self.target.mkdir()
        self.release = self.base / 'Camino/Releases/abc123/Samantha_Agent'
        (self.release / 'scripts').mkdir(parents=True)
        (self.release / 'scripts/camino_service_control.py').write_text('# synthetic release\n')
        self.trip, self.asset = str(uuid4()), str(uuid4())
        self.original = self.root / 'originals/objects' / (self.asset + '.bin')
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(b'synthetic immutable medium')
        (self.root / 'viewer-copies').mkdir()
        (self.root / 'film-projects').mkdir()
        (self.root / 'film-projects/edit-r000001.json').write_text('{"revision":1}')
        (self.root / 'owner-token.txt').write_text('synthetic-private-owner-credential')
        for name in ('metadata', 'media', 'auth', 'readers'):
            db = sqlite3.connect(self.root / (name + '.sqlite'))
            db.execute('CREATE TABLE fixture(value TEXT)')
            db.execute('INSERT INTO fixture VALUES (?)', (name,))
            if name == 'metadata':
                db.executescript('PRAGMA user_version=3; CREATE TABLE meta(singleton INTEGER, '
                    'server_id TEXT,epoch TEXT,cursor INTEGER,writer_device_id TEXT,'
                    'exports_blocked INTEGER,reconciliation_required INTEGER); '
                    'CREATE TABLE moments(trip_id TEXT); CREATE TABLE trips(id TEXT,body TEXT); '
                    'CREATE TABLE accepted_operations(id TEXT);')
                db.execute('INSERT INTO meta VALUES (1,?,?,7,?,0,0)',
                           (str(uuid4()), str(uuid4()), str(uuid4())))
                db.execute('INSERT INTO trips VALUES (?,?)', (self.trip, '{}'))
                db.execute('INSERT INTO moments VALUES (?)', (self.trip,))
                db.execute('INSERT INTO accepted_operations VALUES (?)', ('op',))
            if name == 'media':
                db.execute('CREATE TABLE verified_assets(asset_id TEXT,receipt TEXT)')
                db.execute('INSERT INTO verified_assets VALUES (?,?)', (self.asset, json.dumps({
                    'byte_count': self.original.stat().st_size, 'sha256': backup.digest(self.original)})))
            db.commit()
            db.close()
        self.config = {key: self.root / name for key, name in {
            'metadata_db': 'metadata.sqlite', 'media_db': 'media.sqlite', 'auth_db': 'auth.sqlite',
            'media_root': 'originals', 'viewer_media_root': 'viewer-copies'}.items()}
        self.config.update(code_root=self.release, trip_id=self.trip)
        (self.root / 'config.json').write_text(json.dumps({key: str(value) for key, value in self.config.items()}))
        self.controller = Controller(self.root, self.config)
        self.guard = patch.object(backup, 'encrypted_target')
        self.guard.start()
        self.addCleanup(self.guard.stop)
        self.health_calls = []

    def run_backup(self, mode='execute'):
        return backup.backup_camino(backup_root=self.target, mode=mode, root=self.root,
                                    controller=self.controller,
                                    health_check=lambda _root: self.health_calls.append(True))

    def bundle(self):
        return next((self.target / 'camino_snapshots').iterdir())

    def test_full_bundle_verifies_databases_originals_release_secrets_and_film(self):
        (self.root / 'venv').mkdir()
        (self.root / 'venv/excluded').write_text('rebuild')
        before = backup.digest(self.original)
        result = self.run_backup()
        bundle = self.bundle()
        self.assertTrue(result['verified'])
        self.assertEqual(result['databases'], 4)
        self.assertEqual(result['verified_assets'], 1)
        self.assertEqual(self.controller.calls, ['status', 'stop', 'status', 'status', 'start'])
        self.assertTrue(self.controller.loaded)
        self.assertEqual(self.health_calls, [True])
        self.assertFalse((bundle / 'Camino/Service/venv').exists())
        self.assertEqual((bundle / 'Camino/Service/owner-token.txt').read_bytes(),
                         (self.root / 'owner-token.txt').read_bytes())
        self.assertEqual(backup.digest(self.original), before)
        self.assertTrue((bundle / 'Camino/Service/viewer-copies').is_dir())
        self.assertTrue((bundle / 'Camino/Service/film-projects/edit-r000001.json').is_file())
        self.assertEqual(bundle.stat().st_mode & 0o777, 0o700)
        self.assertEqual((bundle / 'backup_manifest.json').stat().st_mode & 0o777, 0o600)
        # A separate restore location verifies without any live service or config rewriting.
        restored = self.base / 'restored'
        backup.shutil.copytree(bundle, restored)
        self.assertTrue(backup.verify_bundle(restored)['verified'])

    def test_dry_run_has_no_service_or_target_writes(self):
        before = list(self.target.iterdir())
        result = self.run_backup('dry-run')
        self.assertEqual(result['state'], 'preview')
        self.assertEqual(list(self.target.iterdir()), before)
        self.assertEqual(self.controller.calls, ['status'])

    def test_asynchronous_stop_waits_before_entering_offline_copy(self):
        original = self.controller.control
        draining = 0
        def delayed(action, root):
            nonlocal draining
            if action == 'stop':
                draining = 3
                self.controller.calls.append(action)
                return {'stop_requested': True, 'loaded': True}
            if action == 'status' and draining:
                draining -= 1
                self.controller.loaded = bool(draining)
            return original(action, root)
        self.controller.control = delayed
        with patch.object(backup.time, 'sleep'):
            result = self.run_backup()
        self.assertTrue(result['verified'])
        self.assertTrue(self.controller.loaded)
        self.assertEqual(self.health_calls, [True])

    def test_stop_timeout_does_not_claim_offline_state(self):
        with self.assertRaises(TimeoutError):
            backup.wait_stopped(self.controller, self.root, timeout=0)
        self.assertTrue(self.controller.loaded)

    def test_stop_error_with_delayed_unload_still_restores_original_service(self):
        original = self.controller.control
        draining = 0
        def failed_stop(action, root):
            nonlocal draining
            if action == 'stop':
                draining = 3
                self.controller.calls.append(action)
                raise TimeoutError('stop request response was lost')
            if action == 'status' and draining:
                draining -= 1
                self.controller.loaded = bool(draining)
            return original(action, root)
        self.controller.control = failed_stop
        with patch.object(backup.time, 'sleep'), self.assertRaises(TimeoutError):
            self.run_backup()
        self.assertTrue(self.controller.loaded)
        self.assertEqual(self.health_calls, [True])
        self.assertFalse((self.target / 'camino_snapshots').exists())

    def test_bootout_timeout_honors_owned_upload_drain_interval(self):
        with patch.object(backup.subprocess, 'run') as run:
            backup.service_command(['/bin/launchctl', 'bootout', 'synthetic-service'])
            self.assertEqual(run.call_args.kwargs['timeout'], 360)
            backup.service_command(['/bin/launchctl', 'print', 'synthetic-service'])
            self.assertEqual(run.call_args.kwargs['timeout'], 30)

    def test_stopped_service_is_left_stopped(self):
        self.controller.loaded = False
        self.run_backup()
        self.assertEqual(self.controller.calls, ['status'])
        self.assertFalse(self.health_calls)

    def test_copy_failure_restarts_service_without_completed_manifest(self):
        with patch.object(backup, 'copy_files', side_effect=OSError('simulated disk disconnect')):
            with self.assertRaises(OSError):
                self.run_backup()
        self.assertTrue(self.controller.loaded)
        self.assertEqual(self.health_calls, [True])
        self.assertFalse((self.bundle() / 'backup_manifest.json').exists())

    def test_failed_restart_is_not_reported_as_completed(self):
        with patch.object(backup, 'health', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                backup.backup_camino(backup_root=self.target, mode='execute', root=self.root,
                    controller=self.controller, health_check=lambda _: (_ for _ in ()).throw(RuntimeError()))
        self.assertFalse((self.bundle() / 'backup_manifest.json').exists())

    def test_corruption_is_detected_on_readback(self):
        self.run_backup()
        (self.bundle() / 'Camino/Service/owner-token.txt').write_text('damaged')
        with self.assertRaises(ValueError):
            backup.verify_bundle(self.bundle())

    def test_unsafe_source_symlink_is_rejected_before_stop(self):
        (self.root / 'untrusted').symlink_to(self.original)
        with self.assertRaises(ValueError):
            self.run_backup()
        self.assertNotIn('stop', self.controller.calls)

    def test_active_film_writer_is_rejected_without_stopping_service(self):
        path = self.root / 'film-projects/.closure-lock'
        with path.open('w') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                self.run_backup()
        self.assertNotIn('stop', self.controller.calls)

    def test_metadata_version_mismatch_refuses_any_service_mutation(self):
        self.controller.SCHEMA_VERSION = 99
        with self.assertRaises(ValueError):
            self.run_backup()
        self.assertFalse(self.controller.calls)

    def test_preexisting_backups_are_untouched_and_new_bundle_is_independent(self):
        self.run_backup()
        first = self.bundle()
        manifest_before = (first / 'backup_manifest.json').read_bytes()
        self.run_backup()
        self.assertEqual(len(list(first.parent.iterdir())), 2)
        self.assertEqual((first / 'backup_manifest.json').read_bytes(), manifest_before)
        self.assertTrue(backup.verify_bundle(first)['verified'])

    def test_backup_parent_symlink_cannot_redirect_credentials(self):
        elsewhere = self.base / 'elsewhere'
        elsewhere.mkdir()
        (self.target / 'camino_snapshots').symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_backup()
        self.assertTrue(self.controller.loaded)
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_failed_stop_still_restores_owned_service(self):
        original = self.controller.control
        def control(action, root):
            value = original(action, root)
            if action == 'stop':
                raise RuntimeError('stop failed after unloading')
            return value
        self.controller.control = control
        with self.assertRaises(RuntimeError):
            self.run_backup()
        self.assertTrue(self.controller.loaded)
        self.assertEqual(self.health_calls, [True])

    def test_sqlite_backup_captures_committed_wal(self):
        source = self.base / 'wal.sqlite'
        connection = sqlite3.connect(source)
        self.addCleanup(connection.close)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA wal_autocheckpoint=0')
        connection.execute('CREATE TABLE wal_data(value TEXT)')
        connection.execute("INSERT INTO wal_data VALUES ('committed')")
        connection.commit()
        self.assertTrue(source.with_name(source.name + '-wal').is_file())
        target = self.base / 'wal-copy.sqlite'
        backup.copy_database(source, target)
        with sqlite3.connect(target) as restored:
            self.assertEqual(restored.execute('SELECT value FROM wal_data').fetchone(), ('committed',))

    def test_unmounted_target_is_not_treated_as_a_backup_volume(self):
        self.guard.stop()
        with patch.object(backup.os.path, 'ismount', return_value=False):
            with self.assertRaises(ValueError):
                backup.encrypted_target(backup.BACKUP_ROOT)


if __name__ == '__main__':
    unittest.main()
